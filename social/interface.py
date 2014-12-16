__author__ = 'kollad'

from abc import ABCMeta, abstractmethod
import json
from engine.factory import Factory


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


class SocialInterfaceFactoryBase(Factory):
    pass


SocialInterfaceFactory = SocialInterfaceFactoryBase()

SocialInterfaceFactory.register('FacebookSocialInterface', module='engine.social.platforms.fb')
SocialInterfaceFactory.register('SixWavesFacebookSocialInterface', module='engine.social.platforms.sixwaves_fb')
SocialInterfaceFactory.register('BackdoorSocialInterface', module='engine.social.platforms.backdoor')