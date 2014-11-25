from logging import getLogger

from engine.common.process import Process
from engine.common.settings import load_settings


log = getLogger('process')


class BackdoorProcess(Process):
    process_filter = 'game@'

    def __init__(self, crc=None, settings_path=None, loop=None):
        self.settings = load_settings(settings_path)
        address = self.settings['server']['backdoor']['address']
        port = self.settings['server']['backdoor']['port']
        super(BackdoorProcess, self).__init__(
            'backdoor', crc=crc, ports={'tornado': port},
            external_address=address, settings=self.settings, loop=loop)