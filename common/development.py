import datetime
import hashlib
import mimetypes
import stat
import time
from tornado.web import StaticFileHandler, HTTPError, os, email
from engine.utils.pathutils import norm_path, file_path


class StaticHandler(StaticFileHandler):
    """This slightly modified static file handler can host files from multiple locations
    """

    def initialize(self, path=(), default_filename=None):
        if isinstance(path, str):
            path = path,
        self.path = map(norm_path, path)

    def get(self, path, include_body=True):
        try:
            path = file_path(path, self.path)
        except OSError:
            raise HTTPError(404)

        stat_result = os.stat(path)
        modified = datetime.datetime.fromtimestamp(stat_result[stat.ST_MTIME])

        self.set_header("Last-Modified", modified)

        mime_type, encoding = mimetypes.guess_type(path)
        if mime_type:
            self.set_header("Content-Type", mime_type)

        cache_time = self.get_cache_time(path, modified, mime_type)
        if cache_time > 0:
            self.set_header("Expires", datetime.datetime.utcnow() + datetime.timedelta(seconds=cache_time))
            self.set_header("Cache-Control", "max-age=" + str(cache_time))
        else:
            self.set_header("Cache-Control", "public")

        self.set_extra_headers(path)

        # Check the If-Modified-Since, and don't send the result if the
        # content has not been modified
        ims_value = self.request.headers.get("If-Modified-Since")
        if ims_value is not None:
            date_tuple = email.utils.parsedate(ims_value)
            if_since = datetime.datetime.fromtimestamp(time.mktime(date_tuple))
            if if_since >= modified:
                self.set_status(304)
                return

        with open(path, "rb") as f:
            data = f.read()
            hasher = hashlib.sha1()
            hasher.update(data)
            self.set_header("Etag", '"%s"' % hasher.hexdigest())
            if include_body:
                self.write(data)
            else:
                assert self.request.method == "HEAD"
                self.set_header("Content-Length", len(data))


class DevelopmentStaticHandler(StaticHandler):
    def initialize(self, path=(), default_filename=None):
        super(DevelopmentStaticHandler, self).initialize(path, default_filename)



