import atexit

from tornado.ioloop import PeriodicCallback

from engine.common.settings import load_settings
from engine.utils.timeutils import milliseconds, seconds
from engine.common.process import Process
from engine.user.user_manager import UserManager


class BackendProcess(Process):
    def __init__(self, crc=None, settings_path=None, loop=None):
        self.initial_save = True
        self.settings = load_settings(settings_path)
        self.user_manager = UserManager(self.settings)
        self.save_players_time = self.settings['server']['backend']['save_players_time']
        super().__init__('backend', crc=crc, loop=loop, settings=self.settings)
        self._save_players_callback = PeriodicCallback(
            self.save_players, milliseconds(self.save_players_time)
        )

    def start(self):
        self._save_players_callback.start()
        self.logger.info('Save players callback started. Callback time: {}s'.format(self.save_players_time))
        atexit.register(self.atexit)
        super().start()

    def save_players(self):
        """
        Save players from Redis replica to persistent storage, like MySQL, MongoDB etc.

        :return:
        """

        self.logger.info('Saving started.')
        initial_save, self.initial_save = self.initial_save, False
        start = seconds()
        count = self.user_manager.dump_users(all=initial_save)
        end = seconds()
        period = self.save_players_time
        self.logger.info('Saving done. Count: %s. Time: %.3fs. Period: %ss',
                         count, end - start, period)

    def atexit(self):
        # NOTE: do not call this method if multiple backends are used
        self.user_manager.remove_user_ttls()
        self.logger.info("User's ttls have been removed")
