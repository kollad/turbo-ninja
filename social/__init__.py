from abc import ABCMeta, abstractmethod
import json
from tornado.gen import coroutine
from engine.factory import Factory
from engine.utils.mathutils import random_id

__author__ = 'kollad'


def connect_social_interface(settings, *args, **kwargs):
    platform = settings['social']['platform']
    if platform == 'fb':
        return SocialInterfaceFactory.FacebookSocialInterface(settings, *args, **kwargs)
    elif platform == 'sixwaves_fb':
        return SocialInterfaceFactory.SixWavesFacebookSocialInterface(settings, *args, **kwargs)
    elif platform == 'backdoor':
        return SocialInterfaceFactory.BackdoorSocialInterface(settings, *args, **kwargs)


class SocialInterface(object):
    __metaclass__ = ABCMeta

    iframe_template = 'static/templates/iframe.html'

    def __init__(self, settings):
        """
        Initialize social interface for current platform

        :param settings: Application settings
        :return:
        """
        self.settings = settings

    @abstractmethod
    def authenticate(self, handler):
        """
        Authenticate with social platform

        :param handler: Handler instance
        :type handler: RequestHandler
        :return: Social Data
        :rtype: dict
        """

    @abstractmethod
    def get_profile_fields(self, social_data):
        """
        Prepare profile fields for social profile

        :param social_data: Social data that comes from platform
        :type social_data: dict
        :return: Should contain 'name', 'avatar', 'social_id' fields in data
        :rtype: dict
        """

    @abstractmethod
    def get_social_data(self, social_id):
        """
        Get user social data

        :param social_id:
        :return:
        """

    @staticmethod
    def parse_response(response):
        """

        :param response: Social platform response
        :type response: str
        :return:
        """
        return json.loads(response)

    def update_social_data_command(self, social_data):
        """

        :param social_data: User social data
        :type social_data: dict
        :return:
        """
        return {
            'name': 'UpdateSocialData',
            'arguments': {'social_data': social_data}
        }

    @coroutine
    def prepare_iframe_data(self, handler):
        """
        Prepare and render iframe

        :param handler: Handler instance
        :type handler: GameServerHandler
        :return:
        """
        auth_data = self.authenticate(handler)
        if auth_data is None:
            return None
        social_data = yield self.get_social_data(auth_data)
        if not isinstance(social_data, dict):
            social_data = self.parse_response(social_data.decode('utf-8'))
        if social_data is None:
            return None

        profile_fields = self.get_profile_fields(social_data)
        social_data.update(profile_fields)
        social_data['sid'] = random_id()

        flash_vars = {
            'game_server_url': self.settings['external_address'],
            'game_data_url': self.settings['client_load_urls']['game_data'],
            'static_data_url': self.settings['client_load_urls']['static_data'],
            'time_sync_url': '{}/sync'.format(self.settings['server']['timesync']['url']),
            'user_id': auth_data['user_id'],
        }

        return {
            'template': self.iframe_template,
            'settings': self.settings,
            'flashvars': flash_vars,
            'user_id': auth_data['user_id'],
            'social_data': social_data
        }


class SocialInterfaceFactoryBase(Factory):
    pass


SocialInterfaceFactory = SocialInterfaceFactoryBase()

SocialInterfaceFactory.register('FacebookSocialInterface', module='engine.social.platforms.fb')
SocialInterfaceFactory.register('SixWavesFacebookSocialInterface', module='engine.social.platforms.sixwaves_fb')
SocialInterfaceFactory.register('BackdoorSocialInterface', module='engine.social.platforms.backdoor')