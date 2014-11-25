import json
import pickle
import tornado.escape

__author__ = 'kollad'


class FlashMessageMixin(object):
    def _cookie_name(self, key):
        return '{}_message_cookie'.format(key)

    def _get_message_cookie(self, key):
        return self.get_cookie(self._cookie_name(key))

    def has_message(self, key):
        return self._get_message_cookie(key) is not None

    def get_message(self, key):
        if not self.has_message(key):
            return None
        message = tornado.escape.url_unescape(self._get_message_cookie(key))
        try:
            message_data = json.loads(message)
            self.clear_cookie(self._cookie_name(key))
            return message_data
        except Exception as e:
            return None

    def set_message(self, message, key='error'):
        message = json.dumps(message)
        self.set_cookie(self._cookie_name(key), tornado.escape.url_escape(message))