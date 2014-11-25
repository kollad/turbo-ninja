from engine.apps.game.performance import PerformanceInfo
from engine.common.process import Process
from engine.common.settings import load_settings


class GameProcess(Process):
    def __init__(self, process_index, crc, settings_path, server_id, loop=None):
        self.settings = load_settings(settings_path)
        self.server_id = server_id
        server_configuration = self.settings['server']['game'][self.server_id]
        tornado_port = server_configuration['port']
        external_address = server_configuration['address']

        unix_socket = server_configuration.get('unix_socket')

        super(GameProcess, self).__init__(
            'game', process_index, crc,
            ports={'tornado': tornado_port},
            sockets={'tornado': unix_socket},
            external_address=external_address, loop=loop, settings=self.settings)

        self.state = 'active'

    def start(self):
        super(GameProcess, self).start()