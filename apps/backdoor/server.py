from logging import getLogger

from zmq.eventloop.ioloop import install, IOLoop

from engine.apps.backdoor.handlers import (
    BackdoorGateway, BackdoorUserHandler, MapHandler,
    BackdoorWipeHandler, BackdoorActiveProcessesHandler,
    CommandsLogHandler)
from engine.common.development import DevelopmentStaticHandler
from engine.common.log import setup_logger
from engine.utils.pathutils import norm_path


install()

from tornado.web import Application

from engine.utils.handlers import CrossDomainHandler

from engine.apps.backdoor import BackdoorProcess

_loop = IOLoop.instance()
backdoor_process = None


def _init(crc, settings_path):
    global backdoor_process
    backdoor_process = BackdoorProcess(crc, settings_path, loop=_loop)
    setup_logger(backdoor_process.settings)
    backdoor_process.logger = getLogger('backdoor')
    tornado_port = backdoor_process.ports['tornado']

    handlers = [
        (r'/crossdomain.xml', CrossDomainHandler),
        (r'/', BackdoorGateway),
        (r'/user/', BackdoorUserHandler),
        (r'/processes/', BackdoorActiveProcessesHandler),
        (r'/wipe/', BackdoorWipeHandler),
        (r'/map/', MapHandler),
        (r'/commands_log_(.*)\.json', CommandsLogHandler),

        (r'/static/(.+)', DevelopmentStaticHandler, {
            'path': [
                norm_path('engine', 'apps', 'backdoor', 'static'),
            ]
        }),
    ]

    tornado_settings = {
        'template_path': norm_path('engine', 'apps', 'backdoor', 'templates'),
        'xheaders': True,
        'debug': True
    }

    application = Application(handlers, **tornado_settings)
    application.listen(tornado_port, address=backdoor_process.settings['server']['backdoor']['address'])
    getLogger('process').info('Tornado listening to port {0}'.format(tornado_port))

    backdoor_process.start()


if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-i', '--process-index', action='store',
                      type='int', dest='index', default=0, help='Process index')
    parser.add_option('-c', '--crc', action='store',
                      type='str', dest='crc', default=None, help='Process crc')
    parser.add_option('-s', '--settings-path', action='store', dest='settings_path', help='Path to settings.yaml')

    options, args = parser.parse_args()
    if not options.settings_path:
        parser.error('--settings-path should be set')
    _init(options.crc, options.settings_path)
