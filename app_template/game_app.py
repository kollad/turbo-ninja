from engine import AbstractGameApp
from engine.user.user_manager import UserManager

# NOTE: registers all commands
from game_logic.commands import *
from game_logic.commands.base import GameCommandProcessor
from game_logic.content_manager import ContentManager


class GameApp(AbstractGameApp):
    name = None

    def get_command_processor_class(self, application_settings):
        """
        This one should return Application CommandProcessor class

        :param application_settings:
        :return:
        """
        return GameCommandProcessor

    def get_user_manager(self, application_settings):
        """
        This one should return application UserManager instance with application_settings

        :param application_settings:
        :return:
        """
        return UserManager(application_settings)

    def get_content_manager(self, application_settings):
        """
        This one should return application ContentManager instance with application_settings

        :param application_settings:
        :return:
        """
        return ContentManager(application_settings)