from logging import getLogger

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
import tornado.netutil

from engine.apps.game.environment import setup_game_server
from engine.apps.game.handlers.game import GameServerHandler
from engine.apps.game.handlers.static import StaticDataHandler
from engine.common.development import DevelopmentStaticHandler
from engine.common.log import setup_logger
from engine.utils.pathutils import norm_path
from engine.utils.handlers import CrossDomainHandler
from engine.apps.game import GameProcess


# Do not remove!!!
game_server_process = None

_shutdown_mode = False
_loop = IOLoop.instance()


def _init(index, crc, settings_path, server_id):
    global log, game_server_process, _loop
    game_server_process = GameProcess(index, crc, settings_path, server_id, loop=_loop)
    settings = game_server_process.settings

    setup_logger(settings)
    log = game_server_process.logger = getLogger('process')

    tornado_port = game_server_process.ports['tornado']
    unix_socket = game_server_process.sockets['tornado']
    environment_variables = setup_game_server(settings, tornado_port)
    environment_variables['data_format'] = settings['data_format']
    environment_variables['game_settings'] = settings
    environment_variables['logger'] = log
    environment_variables['server_process'] = game_server_process

    handlers = [
        (r'/crossdomain.xml', CrossDomainHandler),
        (r'/data/(.*)', StaticDataHandler, environment_variables),
        (r'/', GameServerHandler, environment_variables),

    ]
    app_settings = {}
    if settings['development_mode']:
        log.info('Development mode on')
        development_handlers = [
            (r'/static/(.+)', DevelopmentStaticHandler, {
                'path': [
                    norm_path('engine', 'social', 'static'),
                    norm_path('..', 'static'),
                    norm_path('..', 'data')
                ]
            }),
            # THIS IS TEMPORARY
            (r'/(.+)', DevelopmentStaticHandler, {
                'path': [
                    norm_path('engine', 'social', 'static'),
                    norm_path('..', 'static')
                ]
            })
        ]
        handlers += development_handlers
        app_settings['debug'] = True

    game_server_application = Application(handlers, app_settings)

    if unix_socket:
        server = HTTPServer(game_server_application)
        log.info('Tornado running through socket {0}'.format(unix_socket))
        socket = tornado.netutil.bind_unix_socket(unix_socket, mode=0o757)
        server.add_socket(socket)
    else:
        log.info('Tornado listening to {0}'.format(tornado_port))
        game_server_application.listen(tornado_port, address=settings['machine_address'])
    log.info('game.{} : Game server started.'.format(server_id))
    game_server_process.start()


if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-i', '--process-index', action='store',
                      type='int', dest='index', default=0, help='Process index')
    parser.add_option('-c', '--crc', action='store',
                      type='str', dest='crc', default=None, help='Process crc')
    parser.add_option('-s', '--settings-path', action='store', dest='settings_path', help='Path to settings.yaml')
    parser.add_option('-n', '--server-id', action='store', dest='server_id', help='Server ID, must exist in settings')
    options, arguments = parser.parse_args()
    if not options.settings_path:
        parser.error('--settings-path should be set')
    if not options.server_id:
        parser.error('--server-id should be set')
    _init(options.index, options.crc, options.settings_path, options.server_id)
