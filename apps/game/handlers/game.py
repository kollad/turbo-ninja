from copy import deepcopy

from tornado.gen import coroutine

from engine.apps.game.handlers.base import GameServerHandlerAbstract
from engine.commands import CommandProcessor
from engine.utils.dictutils import dump_value
from engine.utils.pathutils import norm_path
from engine.utils.timeutils import milliseconds


__author__ = 'kollad'


class GameServerHandler(GameServerHandlerAbstract):
    @coroutine
    def get(self, *args, **kwargs):
        yield from self.process()

    @coroutine
    def post(self, *args, **kwargs):
        yield from self.process()

    def process(self):
        """
        Game server entry point. All the processing for commands and authentication starts from here

        :return:
        """
        action = self.get_argument('action', 'authenticate')
        if action == 'authenticate':
            yield self.authenticate_user()
        else:
            self.user_id = self.get_argument('user_id')
            self.sid = self.get_argument('sid', None)
            if action == 'fetch_player':
                self.logger.debug('Fetch player. User:{}. Sid:{}'.format(self.user_id, self.sid))
                yield from self.fetch_player()
            elif action == 'run_commands':
                commands = self.get_argument('commands')
                testing = self.get_argument('testing', True)
                if not testing:
                    self.verify_session(self.user_id, self.sid)
                response = yield from self.run_commands(commands, self.user_id, log=True)
                self.finish(self.respond({'response': response}))
            else:
                raise NotImplementedError('Action {} not implemented'.format(action))

    def verify_session(self, user_id, sid):
        """

        :param user_id:
        :param sid:
        :return:
        """
        user = self.user_manager.get(self.user_id)
        if user['social_data']['sid'] != sid:
            raise AttributeError("Invalid session id {} != {}".format(user['social_data']['sid'], sid))

    _create_user_commands = [
        {'name': 'CreateUserState'},
        {'name': 'CreateStartingLocation'},
    ]

    _fetch_player_commands = [
        {'name': 'CheckActiveProcesses'}
    ]

    def fetch_player(self):
        """
        Fetch player from database and run preparation commands if required

        :return:
        """
        response_events = []
        user = self.user_manager.get(self.user_id)
        user.set_content_manager(self.content_manager)
        if user['new_user']:
            create_user_events = yield from self.run_commands(self._create_user_commands, self.user_id)
            response_events.append(create_user_events)

        if self._fetch_player_commands:
            fetch_player_events = yield from self.run_commands(self._fetch_player_commands, self.user_id)
            response_events.append(fetch_player_events)

        game_data = deepcopy(user.content_manager.game_data)
        del game_data['location']
        self.finish(
            self.respond({
                'user': dump_value(self.user_manager.get(self.user_id)),
                'game_data': dump_value(game_data),
                'response': response_events
            })
        )

    def run_commands(self, commands, user_id, log=False):
        """
        Run commands

        :param commands: List of commands
        :type commands: list
        :return: Response or nothing
        """
        with (yield from self.user_manager.transaction(user_id)) as writable_state:
            command_processor = self.command_processor_maker(
                writable_state,
                self.content_manager,
                commands)
            response = command_processor.run()
        if log:
            self.user_manager.log_commands(user_id, commands, response)
        return response

    @coroutine
    def authenticate_user(self):
        """
        Authenticate user and render iframe

        :return:
        """
        iframe_data = yield self.social_interface.prepare_iframe_data(self)
        if iframe_data:
            # TODO: Probably this part should be refactored, because it looks weird.
            social_data = iframe_data.pop('social_data', {})
            yield from self.update_social_data(social_data)

            template_name = iframe_data.pop('template', None)
            template_name = norm_path('engine', 'social', template_name)
            iframe_data['swf_name'] = self.static_url(self.game_settings['swf']['name'])
            self.render(template_name, **iframe_data)

    def update_social_data(self, social_data):
        """
        Update user profile with new data from social platform

        :param social_data:
        :return:
        """
        command = {
            'name': 'UpdateSocialData',
            'arguments': {
                'social_data': social_data
            }
        }
        yield from self.run_commands([command], user_id=social_data['social_id'])

    def respond(self, data=None):
        """
        Respond to client or whatever requests game server and append current server time

        :param data: Response data
        :type data: dict
        :return:
        """
        data = data or {}
        data['time'] = milliseconds()
        super(GameServerHandler, self).respond(data)

    def static_url(self, path, include_host=False, **kwargs):
        """
        Static url for templates

        :param path: Path to static file
        :type path: str
        :param include_host: Absolute url or relative
        :type include_host: bool
        :param kwargs: Additional keyword arguments
        :return: CDN url for static file or relative url in development mode
        :rtype: str
        """
        static_data = self.content_manager.static_data.get(path)
        if not static_data:
            return '/static/{}'.format(path)
        else:
            return static_data['url']
