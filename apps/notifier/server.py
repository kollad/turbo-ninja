from logging import getLogger

from tornado.ioloop import IOLoop
from tornado.web import Application

from modules.cherrycommon.handlers import CrossDomainHandler
from engine.apps.notifier import NotifierProcess
from engine.common.log import setup_logger


_loop = IOLoop.instance()


def _init(crc, settings_path):
    notifier_process = NotifierProcess(crc=crc, settings_path=settings_path, loop=_loop)
    settings = notifier_process.settings
    setup_logger(settings)
    log = notifier_process.logger = getLogger('notifier')
    tornado_port = notifier_process.ports['tornado']

    tornado_application = Application((
        (r'/crossdomain.xml', CrossDomainHandler),
    ))

    log.info('Tornado listening to {0}'.format(tornado_port))
    tornado_application.listen(tornado_port, address=settings['machine_address'])
    log.info('Notifier started.')
    notifier_process.start()


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-i', '--process-index', action='store', type=int, dest='index', default=0,
                        help='Process index')
    parser.add_argument('-c', '--crc', action='store', dest='crc', default=None, help='Process crc')
    parser.add_argument('-s', '--settings-path', action='store', dest='settings_path', help='Path to settings.yaml')
    args = parser.parse_args()
    if not args.settings_path:
        parser.error('--settings-path should be set')
    _init(args.crc, args.settings_path)