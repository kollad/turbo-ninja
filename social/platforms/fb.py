import base64
import hashlib
import hmac
import json
from logging import getLogger
from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from tornado.web import HTTPError

from engine.social.interface import SocialInterface
from engine.social.mobile import MobileSocialInterfaceMixin
from engine.social.web import WebSocialInterfaceMixin


__author__ = 'kollad'

log = getLogger('social')


def parse_signed_request(signed_request, app_secret):
    """ Return dictionary with signed request data.

    We return a dictionary containing the information in the
    signed_request. This includes a user_id if the user has authorised
    your application, as well as any information requested.

    If the signed_request is malformed or corrupted, False is returned.

    """
    try:
        encoded_sig, payload = map(str, signed_request.split('.', 1))

        sig = base64.urlsafe_b64decode(encoded_sig + "=" *
                                       ((4 - len(encoded_sig) % 4) % 4))
        data = base64.urlsafe_b64decode(payload + "=" *
                                        ((4 - len(payload) % 4) % 4))
    except IndexError:
        # Signed request was malformed.
        return False
    except TypeError:
        # Signed request had a corrupted payload.
        return False
    data = json.loads(data.decode('utf-8'))
    if data.get('algorithm', '').upper() != 'HMAC-SHA256':
        return False

    # HMAC can only handle ascii (byte) strings
    # http://bugs.python.org/issue5285
    app_secret = app_secret.encode('ascii')
    payload = payload.encode('ascii')

    expected_sig = hmac.new(app_secret,
                            msg=payload,
                            digestmod=hashlib.sha256).digest()
    if sig != expected_sig:
        return False

    return data


locale_language_map = {
    'en_GB': 'en',
    'en_PI': 'en',
    'en_UD': 'en',
    'en_US': 'en',
    'ru_RU': 'ru',
    'uk_UA': 'ru',
    'be_BY': 'ru'
}


class FacebookSocialInterface(SocialInterface, WebSocialInterfaceMixin, MobileSocialInterfaceMixin):
    OAUTH_REDIRECT_TEMPLATE = """
    <script type="text/javascript">
        var oauth_url = 'https://www.facebook.com/v2.0/dialog/oauth/';
        oauth_url += '?client_id={{ app_id }}';
        oauth_url += '&redirect_uri=' + '{{ app_url }}' + encodeURIComponent(document.location.search);
        oauth_url += '&scope={{ scope }}';
        window.top.location = oauth_url;
    </script>
    """
    GRAPH_API_URL = 'https://graph.facebook.com/v2.0/'

    def authenticate(self, handler):
        signed_request = handler.get_argument('signed_request')
        if not signed_request:
            log.error('Unable to get "signed_request" from request')
            raise HTTPError(500)
        decoded_signed_request = parse_signed_request(signed_request, self.settings['social']['app_secret'])
        if not decoded_signed_request:
            log.error('Unable to decode "signed_request"')
            raise HTTPError(500)

        if not 'user_id' in decoded_signed_request or not 'oauth_token' in decoded_signed_request:
            return self._oauth_redirect(handler)
        user_locale = decoded_signed_request['user']['locale']
        language_code = locale_language_map.get(user_locale, 'en')

        response = {
            'user_id': decoded_signed_request['user_id'],
            'access_token': decoded_signed_request['oauth_token'],
            'locale': user_locale,
            'signed_request': signed_request,
            'language': language_code
        }

        return response

    def _oauth_redirect(self, handler):
        handler.render(
            self.OAUTH_REDIRECT_TEMPLATE,
            app_id=self.settings['social']['app_id'],
            scope=self.settings['social']['facebook_oauth_scope'],
            app_url=self.settings['social']['app_url']
        )

    @gen.coroutine
    def get_social_data(self, social_data):
        request = HTTPRequest(
            '{}me?fields=id,birthday,first_name,last_name,picture,locale,gender&access_token={}'.format(
                self.GRAPH_API_URL, social_data['access_token']
            ))
        http_client = AsyncHTTPClient()
        response = yield http_client.fetch(request)
        return response.body

    def get_profile_fields(self, social_data):
        if 'first_name' not in social_data:
            social_data['first_name'] = ''
        if 'last_name' not in social_data:
            social_data['last_name'] = ''
        return {
            'name': u'{first_name} {last_name}'.format(**social_data).strip(),
            'avatar': social_data['picture']['data']['url'],
            'social_id': social_data['id']
        }
