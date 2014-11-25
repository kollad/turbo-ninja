from abc import abstractmethod, ABCMeta
from tornado.web import HTTPError
from engine.utils.handlers import DataHandler

__author__ = 'kollad'


class GameServerHandlerAbstract(DataHandler, metaclass=ABCMeta):
    def initialize(self, *args, **kwargs):
        """
        Initialize game server handler with all required managers, social interfaces and other stuff.

        :param args:
        :param kwargs: User manager, content manager, social interface are required to pass
        :return:
        """
        self.logger = kwargs.pop('logger')
        self.server_process = kwargs.pop('server_process')
        if not self.server_process.state == 'active':
            self.logger.error('Game Server process inactive')
            raise HTTPError(503)
        self.command_processor_maker = kwargs.pop('command_processor_maker')
        self.user_manager = kwargs.pop('user_manager')
        self.content_manager = kwargs.pop('content_manager')
        self.game_settings = kwargs.pop('game_settings')
        self.social_interface = kwargs.pop('social')
        if self.game_settings['development_mode']:
            # This will reload game data on each request, even if game data file haven't changed
            self.content_manager.reload_game_data()
        super(GameServerHandlerAbstract, self).initialize(*args, **kwargs)

    @abstractmethod
    def get(self, *args, **kwargs):
        pass

    @abstractmethod
    def post(self, *args, **kwargs):
        pass
