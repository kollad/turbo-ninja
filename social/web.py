from tornado.gen import coroutine
from engine.utils.mathutils import random_id

__author__ = 'kollad'


class WebSocialInterfaceMixin(object):
    iframe_template = 'static/templates/iframe.html'

    @coroutine
    def render_iframe(self, handler):
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