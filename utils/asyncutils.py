from tornado.gen import Task
from tornado.ioloop import IOLoop


def sleep(seconds, ioloop=None):
    ioloop = ioloop or IOLoop.instance()
    time = ioloop.time() + seconds
    yield Task(ioloop.add_timeout, time)