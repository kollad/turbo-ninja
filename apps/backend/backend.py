from logging import getLogger

from tornado.ioloop import IOLoop

from engine.apps.backend import BackendProcess
from engine.common.log import setup_logger


_loop = IOLoop.instance()
backend_process = None


def _init(crc, settings_path):
    global backend_process, _loop
    backend_process = BackendProcess(crc, settings_path, loop=_loop)
    setup_logger(backend_process.settings)
    backend_process.logger = getLogger('backend')
    backend_process.start()


if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-i', '--process-index', action='store', type='int', dest='index', default=0,
                      help='Process index')
    parser.add_option('-c', '--crc', action='store', type='str', dest='crc', default=None, help='Process crc')
    parser.add_option('-s', '--settings-path', action='store', dest='settings_path', help='Path to settings.yaml')
    options, args = parser.parse_args()

    if not options.settings_path:
        parser.error('--settings-path should be set')
    _init(options.crc, options.settings_path)
