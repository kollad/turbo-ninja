from copy import deepcopy

from tornado.gen import coroutine
from tornado.web import asynchronous

from engine.apps.game.handlers.base import GameServerHandlerAbstract


__author__ = 'kollad'


class StaticDataHandler(GameServerHandlerAbstract):
    @asynchronous
    @coroutine
    def get(self, *args, **kwargs):
        self.process()

    @asynchronous
    @coroutine
    def post(self, *args, **kwargs):
        self.process()

    def process(self):
        request_uri = self.request.uri
        if request_uri == '/data/game_data':
            game_data = deepcopy(self.content_manager.game_data)
            del game_data['location']
            self.respond(game_data)
        elif request_uri == '/data/static_data':
            self.respond(self.content_manager.static_data)
        else:
            raise NotImplementedError('Request uri {} not found'.format(request_uri))

    def get_game_data(self):
        self.respond(self.content_manager.game_data)

    def get_static_data(self):
        self.respond(self.content_manager.static_data)