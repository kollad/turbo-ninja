from functools import partial
from logging import getLogger
from threading import Thread
import os
import zlib
import signal

from zmq.eventloop.ioloop import IOLoop, install

from engine.utils.mathutils import random_id
from engine.utils.timeutils import milliseconds


class ProcessException(Exception):
    def __init__(self, process, description):
        Exception.__init__(self, description)
        self.process_id = str(process.info)
        self.description = description

    PATTERN = '{process_id} - {description}'

    def __str__(self):
        return self.PATTERN.format(process_id=self.process_id, description=self.description)


class ProcessInfo(object):
    def __init__(self, process_type='', process_index=0, machine_id=None,
                 ports=None, sockets=None, external_address=None, pid=None, crc=None):
        self.process_type = process_type
        self.process_index = process_index
        self.machine_id = machine_id
        self.pid = pid or os.getpid()
        self.ports = ports or {}
        self.sockets = sockets or {}
        self._crc = crc
        if external_address:
            self.external_address = external_address

    _process_name_pattern = '{process_type}@{machine_id}.{index:03d}'

    @classmethod
    def get_process_name(cls, process_type, machine_id, index):
        return cls._process_name_pattern.format(process_type=process_type, machine_id=machine_id, index=int(index))

    _process_crc_pattern = '{name}.{time:.0f}'

    @classmethod
    def get_process_crc(cls, process_name):
        return zlib.crc32(
            bytes(cls._process_crc_pattern.format(name=process_name, time=milliseconds()), 'utf-8')) & 0xfff

    _name = None

    @property
    def name(self):
        if self._name is None:
            self._name = self.get_process_name(self.process_type, self.machine_id, self.process_index)
        return self._name

    def init_crc(self):
        self._crc = self.get_process_crc(self.name)
        return self._crc

    _crc = None

    @property
    def crc(self):
        if self._crc is None:
            self.init_crc()
        return self._crc

    _id = None

    @property
    def id(self):
        if self._id is None:
            self._id = '{name}.{hash}'.format(name=self.name, hash=self.crc)
        return self._id

    def __str__(self):
        return self.id

    def __repr__(self):
        return '<ProcessInfo: {}>'.format(self.id)


DEFAULT_MACHINE_ID = 'cherry'
_process_instance = None


class BasicProcess(object):
    @classmethod
    def get_instance(cls, *args, **kwargs):
        """Just singleton implementation.

        :return: Process instance for current application.
        :rtype: BasicProcess
        """
        global _process_instance
        if _process_instance is None:
            _process_instance = cls.__new__(cls)
            _process_instance.__init__(*args, **kwargs)
        return _process_instance

    @classmethod
    def _init_instance(cls, instance):
        cls._instance = instance

    def __init__(self, process_type, process_index=0, machine_id=DEFAULT_MACHINE_ID, crc=None, log=True,
                 ports=None, sockets=None, external_address=None):
        global _process_instance
        _process_instance = self
        self.ports = ports or {}
        self.sockets = sockets or {}
        self.info = ProcessInfo(process_type, process_index=process_index, machine_id=machine_id,
                                ports=self.ports, sockets=self.sockets,
                                external_address=external_address, crc=crc)
        if not crc:
            self.info.init_crc()

        if log:
            self.configure_logger()

    def configure_logger(self):
        self.logger = getLogger('process')

    @property
    def crc(self):
        return self.info.crc

    @property
    def name(self):
        return self.info.name

    @property
    def external_address(self):
        return self.info.external_address

    @property
    def process_index(self):
        return self.info.process_index

    def start(self):
        self.logger.info('Process started: {!s}'.format(self.info))

    def stop(self):
        self.logger.info('Process stopped: {!s}'.format(self.info))


class IOLoopProcess(BasicProcess):
    """
    Run process with zmq eventloop. Please, implement loop initialization in ther start method if you about to run this
    process as daemon.
    """

    def __init__(self, process_type, process_index=0, machine_id=DEFAULT_MACHINE_ID, crc=None, log=True,
                 ports=None, sockets=None, external_address=None, loop=None):
        super(IOLoopProcess, self).__init__(process_type, process_index=process_index, machine_id=machine_id,
                                            crc=crc, log=log, ports=ports, sockets=sockets,
                                            external_address=external_address)
        self._loop = loop

    @property
    def loop(self):
        if self._loop is None:
            install()
            self._loop = IOLoop.instance()
        return self._loop

    def start(self):
        super(IOLoopProcess, self).start()
        try:
            self.loop.start()
        except KeyboardInterrupt:
            self.stop()
            self.logger.error('Exited via Ctrl-C: {}'.format(self.name))

    def stop(self):
        self.loop.stop()
        super(IOLoopProcess, self).stop()


class IOLoopMixin():
    """Add IOLoop getter to object. Use it if you need separate instance of zmq eventloop in subprocess or thread.
    """
    _loop = None

    @property
    def loop(self):
        if self._loop is None:
            install()
            self._loop = IOLoop()
        return self._loop

    def loop_start(self):
        try:
            self.loop.start()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.loop.stop()

    def init_signal_handler(self, signals=(signal.SIGINT, signal.SIGTERM)):
        self._handle_signals = True
        try:
            for s in signals:
                signal.signal(s, self.signal_handler)
        except (ValueError, AttributeError):
            # Windows?
            pass

    def signal_handler(self, signum, frame):
        if not self._handle_signals:
            return
        if signum in {signal.SIGKILL, signal.SIGTERM, signal.SIGINT}:
            self._handle_signals = False
            self.stop()


class IOLoopThread(Thread, IOLoopMixin):
    pass


class CallbackWrapper(object):
    """Something similar to functools.partial, but also added a property to mark callback as executed.
    Note, that if you've provided args to both callback and wrapper, wrapper's args will be added at
    the end of callback args.
    """

    def __init__(self, handler, *args, **kwargs):
        self.done = False
        self.args = args
        self.kwargs = kwargs
        self.handler = handler
        self._callee = partial(handler, *args, **kwargs)
        self._hash = random_id()

    def __call__(self, *args, **kwargs):
        self.done = True
        self._callee(*args, **kwargs)

    def __hash__(self):
        return self._hash


def wrap_callback(handler, *args, **kwargs):
    """Decorate handler with this function to turn function or method to CallbackWrapper
    """
    return CallbackWrapper(handler, *args, **kwargs)


def make_lazy(fun, *args, **kwargs):
    sentinel = object()
    cell = [sentinel]

    def evaluate():
        if cell[0] is sentinel:
            cell[0] = fun(*args, **kwargs)
        return cell[0]

    return evaluate

