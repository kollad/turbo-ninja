from uuid import uuid4

from redis import StrictRedis
from tornado.ioloop import IOLoop

from engine.utils.asyncutils import sleep

__author__ = "lopalo"


class LockError(Exception):
    pass


class RedisLock(object):
    _key_prefix = 'lock'
    validity_time = 60  # seconds

    def __init__(self, redis, key, ioloop=None, *args, **kwargs):
        self._ioloop = ioloop or IOLoop.instance()
        self._redis = redis
        self._acquire_time = None
        self._lock_value = None
        self._key = key

    @property
    def key(self):
        return '{}:{}'.format(self._key_prefix, self._key)

    def acquire(self, blocking=True, timeout=10, check_period=0.005):
        if self._lock_value is not None:
            raise LockError("Lock already acquired")

        key = self.key
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
        result = self._redis.release_lock_script(keys=[self.key, lock_value])
        if not result:
            raise LockError('Try to release unlocked lock')


class LockRedisMixin(object):
    RELEASE_LOCK_SCRIPT = """
        if redis.call("GET", KEYS[1]) == KEYS[2]
        then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
    """

    release_lock_script = None

    def init_lock_script(self):
        reg = self.register_script
        self.release_lock_script = reg(self.RELEASE_LOCK_SCRIPT)


