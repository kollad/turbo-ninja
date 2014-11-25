from tornado.ioloop import IOLoop
from tornado.web import Application

from engine.common.settings import load_settings
from engine.utils.handlers import CrossDomainHandler
from engine.utils.handlers import DataHandler
from engine.utils.timeutils import milliseconds


class TimeSyncHandler(DataHandler):
    def respond(self, data=None):
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        super(TimeSyncHandler, self).respond({'time': milliseconds()})

    def get(self, *args, **kwargs):
        return self.respond()

    def post(self, *args, **kwargs):
        return self.respond()


def _init(settings_path):
    settings = load_settings(settings_path)
    time_sync_handlers = (
        (r'/sync', TimeSyncHandler, {'data_format': settings['data_format']}),
        (r'/crossdomain.xml', CrossDomainHandler)
    )

    app = Application(time_sync_handlers)
    app.listen(port=settings['server']['timesync']['port'], address=settings['server']['timesync']['address'])
    # Check if fork available
    # if hasattr(os, 'fork'):
    #    server.start(0)
    #else:
    #    server.start()
    IOLoop.instance().start()


if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option('-s', '--settings-path', action='store', dest='settings_path', help='Path to settings.yaml')
    options, arguments = parser.parse_args()
    if not options.settings_path:
        parser.error('--settings-path should be set')
    _init(options.settings_path)
