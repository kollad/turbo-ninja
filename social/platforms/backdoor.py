import json
from tornado import gen
from engine.social import SocialInterface

__author__ = 'kollad'


class BackdoorSocialInterface(SocialInterface):
    def authenticate(self, handler):
        user_id = handler.get_argument('user_id')

        response = {
            'user_id': 'backdoor.{}'.format(user_id)
        }

        return response

    @gen.coroutine
    def get_social_data(self, social_data):
        user_id = social_data['user_id']
        response = {
            'first_name': 'Backdoor User #{}'.format(user_id),
            'last_name': '',
            'avatar': '',
            'social_id': user_id,
        }
        return response

    def get_profile_fields(self, social_data):
        return {
            'name': u'{first_name} {last_name}'.format(**social_data),
            'avatar': social_data['avatar'],
            'social_id': social_data['social_id']
        }
