from engine.common.process import Process
from engine.common.settings import load_settings


class NotifierProcess(Process):
    def __init__(self, crc=None, settings_path=None, loop=None):
        self.settings = load_settings(settings_path)
        address = self.settings['server']['notifier']['address']
        port = self.settings['server']['notifier']['port']
        super().__init__(
            'notifier', crc=crc, ports={'tornado': port},
            external_address=address, loop=loop, settings=self.settings
        )