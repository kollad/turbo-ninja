from uuid import uuid4

from redis import StrictRedis
from tornado.ioloop import IOLoop

from engine.utils.asyncutils import sleep

__author__ = "lopalo"


class LockError(Exception):
    pass


class RedisLock(object):
    key_prefix = 'redis_lock:'
    validity_time = 60  # seconds

    def __init__(self, redis, key, ioloop=None, *args, **kwargs):
        self._ioloop = ioloop or IOLoop.instance()
        self._redis = redis
        self._acquire_time = None
        self._lock_value = None
        self._key = key

    def acquire(self, blocking=True, timeout=10, check_period=0.005):
        if self._lock_value is not None:
            raise LockError("Lock already acquired")

        key = '{}{}'.format(self.key_prefix, self._key)
        value = self._lock_value = uuid4().hex

        result = None
        start = self._ioloop.time()
        while not result:
            now = self._ioloop.time()
            result = self._redis.set(key, value, nx=True,
                                     ex=self.validity_time)
            if result:
                self._acquire_time = now
                self._lock_value = value
                return True
            if not blocking:
                return False
            if now - start >= timeout:
                raise LockError('Timeout expired')
            yield from sleep(check_period, self._ioloop)

    def check_validity_time(self):
        if self._ioloop.time() - self._acquire_time >= self.validity_time:
            raise LockError("Validity time expired")

    def release(self):
        lock_value = self._lock_value
        self._acquire_time = None
        self._lock_value = None
        key = '{}{}'.format(self.key_prefix, self._key)
        result = self._redis.release_script(keys=[key, lock_value])
        if not result:
            raise LockError('Try to release unlocked lock')


class LockRedis(StrictRedis):
    RELEASE_SCRIPT = """
        if redis.call("GET", KEYS[1]) == KEYS[2]
        then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
    """

    release_script = None

    def init_scripts(self):
        self.release_script = self.register_script(self.RELEASE_SCRIPT)


