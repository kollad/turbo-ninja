import json
import re

from tornado.httputil import format_timestamp
from tornado.web import RequestHandler

from engine.common.settings import load_settings
from engine.tornado_messages import FlashMessageMixin
from engine.user.user_manager import UserManager


user_manager = UserManager(load_settings('settings.yaml'))

_user_manager = None


def get_user_manager():
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager(load_settings('settings.yaml'))
    return _user_manager


class BackdoorGateway(RequestHandler, FlashMessageMixin):
    def get(self, *args, **kwargs):
        message = None
        level = None
        if self.has_message('danger'):
            level = 'danger'
            message = self.get_message(level)
        if self.has_message('success'):
            level = 'success'
            message = self.get_message(level)
        self.render('gateway.html', message=message, level=level, active_url=lambda x: x, user_id=None)


class AbstractBackdoorHandler(RequestHandler, FlashMessageMixin):
    def get_user(self):
        self.user_id = self.get_argument('user_id')
        user_manager = get_user_manager()
        user = user_manager.get(self.user_id, auto_create=False)
        if user is None:
            message = {'message': 'User does not exists', 'data': {'user_id': self.user_id}}
            self.set_message(message, 'danger')
            self.redirect('/')
            return
        return user

    def render(self, template_name, **kwargs):
        user_id = self.get_argument('user_id')
        user = self.get_user()
        kwargs['user_id'] = user_id
        kwargs['message'] = kwargs.get('message', None)
        kwargs['active_processes_count'] = len(user.active_processes)
        kwargs['active_url'] = self._check_active_url
        kwargs['format_timestamp'] = format_timestamp
        super(AbstractBackdoorHandler, self).render(template_name, **kwargs)

    def _check_active_url(self, url):
        request_uri = self.request.uri
        controller = re.match('/(.*)/', request_uri).group()
        return 'active' if url in controller else ''


class BackdoorUserHandler(AbstractBackdoorHandler):
    def get(self, *args, **kwargs):
        self.user_id = self.get_argument('user_id')
        arguments = self.request.arguments
        if 'panel' in arguments:
            user = self.get_user()
            self.render(
                'user.html',
                user=user,
            )

        if 'play' in arguments:
            self.redirect('http://local.wysegames.com:8081/?action=authenticate&user_id={}'.format(self.user_id))


class BackdoorActiveProcessesHandler(AbstractBackdoorHandler):
    def get(self, *args, **kwargs):
        user = self.get_user()
        self.render(
            'active_processes.html',
            user=user,
            active_processes=user.active_processes)


class BackdoorWipeHandler(RequestHandler, FlashMessageMixin):
    def get(self, *args, **kwargs):
        self.user_id = self.get_argument('user_id')
        user_manager = get_user_manager()
        user = user_manager.get(self.user_id, auto_create=False)
        if user is None:
            message = {'message': 'User does not exists', 'data': {'user_id': self.user_id}}
            self.set_message(message, 'danger')
            self.redirect('/')
        else:
            user_manager.delete(self.user_id)
            message = {'message': 'User successfully wiped', 'data': {'user_id': self.user_id}}
            self.set_message(message, 'success')
            self.redirect('/')


class MapHandler(AbstractBackdoorHandler, FlashMessageMixin):
    def get(self, *args, **kwargs):
        user = self.get_user()
        self.render(
            'map.html',
            map_data=json.dumps(user.map),
        )


class CommandsLogHandler(AbstractBackdoorHandler, FlashMessageMixin):
    def get(self, user_id, *args, **kwargs):
        user_manager = get_user_manager()
        log = user_manager.get_commands_log(user_id)
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(log, indent=4))
