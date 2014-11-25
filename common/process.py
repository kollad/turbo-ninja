from engine.utils.process import IOLoopProcess

__author__ = 'kollad'


class Process(IOLoopProcess):
    def __init__(self, process_type, process_index=0, crc=None, log=True,
                 ports=None, sockets=None, external_address=None, loop=None, settings=None):
        self.settings = settings

        super(Process, self).__init__(
            process_type, process_index=process_index, machine_id=self.settings['machine_id'],
            crc=crc, log=log, ports=ports, sockets=sockets,
            external_address=external_address, loop=loop)

        self.logger.info('Pid: {}'.format(self.info.pid))
        self.logger.info('Process started: {}'.format(self.crc))