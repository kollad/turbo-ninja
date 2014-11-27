import contextlib
import json
from random import Random
from copy import deepcopy
from logging import getLogger

from pymongo import MongoClient
from redis import StrictRedis

from engine.common.serializers import data_to_json, json_to_data
from engine.utils.dictutils import dump_value
from engine.utils.timeutils import milliseconds
from engine.user.user_state import UserState
from engine.user.lock import RedisLock, LockRedisMixin


__author__ = 'kollad'


def encoder_function(data):
    return data_to_json(data)


def decoder_function(data):
    return json_to_data(data)


def key_maker(key_prefix):
    def make_key(ident):
        prefix = key_prefix + ":"
        if ident.startswith(prefix):
            return ident
        return prefix + ident
    return staticmethod(make_key)


log = getLogger('process')


class UserManager(object):
    _key_prefix = 'user'
    _log_key_prefix = 'user-log'


    def __init__(self, settings):
        """
        Initialize player manager

        :param settings: Settings
        :type settings: dict
        :return:
        """
        self.settings = settings
        self.redis = None
        self.mongo = None
        self.random = Random()

        self.init_redis()
        self.init_mongo()


    def init_redis(self):
        """
        Initialize redis client

        :return:
        """
        settings = self.settings['user_manager']['redis']
        host = settings['host']
        port = settings['port']
        password = settings['password']
        db = settings['db']
        self.redis = UserRedis(host, port, db, password)
        self.redis.init_scripts()


    def init_mongo(self):
        """
        Initialize mongo client

        :return:
        """
        settings = self.settings['user_manager']['mongo']
        host = settings['host']
        port = settings['port']
        db_name = settings['db_name']
        collection = settings['collection']
        self.mongo = MongoClient(host=host, port=port)[db_name][collection]


    def get_lock(self, key):
        """
        :return: RedisLock object
        """
        return RedisLock(self.redis, key)


    user_key = key_maker(_key_prefix)

    def decode_user_id(self, user_key):
        """
        Decode user_id key that would
        :param user_key:
        :type user_key:
        :return: User ID
        :rtype: str
        """
        if isinstance(user_key, bytes):
            user_key = user_key.decode('utf-8')
        return user_key.split(':')[1]

    def get(self, user_id, auto_create=True):
        """
        Get user from redis if exists, otherwise fetch it from storage and put it into redis

        :param user_id: User ID or Social ID
        :type user_id: str
        :param auto_create: Auto create user if not exists
        :type auto_create: bool
        :return: User state object
        :rtype: UserState
        """
        user_id = str(user_id)
        user_key = self.user_key(user_id)
        if self.settings['user_manager']['fixed_random_seed']:
            random = None
        else:
            random = self.random
        if self.redis.exists(user_key):
            data = self.decode_data(self.redis.get(user_key))
            return UserState(data, random=random)
        else:
            data = self.fetch_or_create(user_id, auto_create=auto_create)
            if data:
                return UserState(data, random=random)
            return None

    def create_user_state(self, user_id):
        """
        Create initial user state

        :param user_id: User ID
        :type user_id: str
        :return: User state
        :rtype: dict
        """
        state = deepcopy(self.settings['user']['starting_state'])
        state['_id'] = user_id
        state['user_id'] = user_id
        state['registration_time'] = milliseconds()
        state['new_user'] = True
        return state

    def fetch_or_create(self, user_id, auto_create=True):
        """
        Fetch player from database or create new one, if not exists

        :param user_id: User ID
        :type user_id: str
        :param auto_create: Auto create user if not exists
        :type auto_create: bool
        :return: User state
        :rtype: dict
        """
        user_state = self.mongo.find_one({'_id': user_id})

        if not user_state and auto_create:
            user_state = self.create_user_state(user_id)

        if user_state:
            result = self.save(user_id, user_state)
            if result:
                log.debug('User {} saved to redis'.format(user_id))
            else:
                raise ValueError('Cannot save user to redis : {}'.format(user_id))
            return user_state
        return None

    def delete(self, user_id):
        self.mongo.remove({'_id': user_id})
        pipe = self.redis.pipeline(transaction=True)
        pipe.delete(self.user_key(user_id))
        pipe.srem('modified_users', self.user_key(user_id))
        result = pipe.execute()[0]
        return result

    def save(self, user_id, data):
        """
        Save user data into redis

        :param user_id: User ID
        :type user_id: str
        :param data: User state
        :type data: dict
        :return: indicates if player was saved in redis
        :rtype: bool
        """
        pipe = self.redis.pipeline(transaction=True)
        data['user_id'] = user_id
        # the set command cancels a user's ttl
        pipe.set(self.user_key(user_id), self.encode_data(data))
        pipe.sadd('modified_users', self.user_key(user_id))
        result = pipe.execute()[0]
        return result

    def encode_data(self, data):
        """
        Encode data to store in redis

        :param data: Decoded user state
        :type data: dict
        :return: Encoded data
        :rtype:
        """

        return encoder_function(data)

    def decode_data(self, data):
        """
        Decode data came from redis

        :param data: User state encoded
        :type data:
        :return: Decoded data
        :rtype: dict
        """
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return decoder_function(data)

    @property
    def online_users_count(self):
        """
        Count online players in redis
        :return: Database size (players in database)
        :rtype: int
        """
        return self.redis.keys(self.user_key("*"))

    def transaction(self, user_id):
        """
        Context manager helper for opening user state. Provides lock for user get/set operations.

        :param user_id: User ID
        :type user_id: str
        :return: context manager
        """
        lock = self.get_lock(user_id)
        yield from lock.acquire()
        writable_state = self.get(user_id)
        return self._transaction_context(user_id, writable_state, lock)

    @contextlib.contextmanager
    def _transaction_context(self, user_id, writable_state, lock):
        """
        User state transaction context manager

        :param user_id: User ID
        :type user_id: str
        :param writable_state: User state
        :type writable_state: UserState
        :param key: Lock key
        :type key: str
        """
        try:
            yield writable_state
            lock.check_validity_time()
            self.save(user_id, dump_value(writable_state))
        finally:
            lock.release()

    @property
    def unsaved_users_count(self):
        """
        Get unsaved players count

        :return: Unsaved players count
        :rtype: int
        """
        return self.redis.scard('modified_users')


    def dump_users(self, all=False):
        db = self.redis
        expire = self.settings['user']['session_ttl']
        if all:
            users = db.get_all_users_script(keys=[expire])
        else:
            users = db.get_modified_users_script(keys=[expire])
        for user_data in users:
            self._dump_user_to_mongo(self.decode_data(user_data))
        return len(users)

    def remove_user_ttls(self):
        # TODO: a script that calls this method
        self.redis.remove_user_ttls_script()

    def _dump_user_to_mongo(self, user_data):
        """
        Dump player to MongoDB

        :param player_data: User state
        :type player_data: dict or UserState
        :return:
        """
        self.mongo.ensure_index('user_id')
        self.mongo.find_and_modify({'_id': user_data['user_id']},
                                   dump_value(user_data), upsert=True)

    log_key = key_maker(_log_key_prefix)

    def log_commands(self, user_id, commands, response):
        settings = self.settings['user_manager']['redis']['log_commands']
        if not settings['enable']:
            return
        if isinstance(commands, str):
            commands = json.loads(commands)
        key = self.log_key(user_id)
        data = {"ts": milliseconds(),
                "commands": commands,
                "response": response}
        pipe = self.redis.pipeline(transaction=True)
        pipe.rpush(key, json.dumps(data))
        pipe.ltrim(key, -settings['size'], -1)
        pipe.expire(key, settings['ttl'])
        pipe.execute()

    def get_commands_log(self, user_id):
        key = self.log_key(user_id)
        data = self.redis.lrange(key, 0, -1)
        return [json.loads(i.decode("utf-8")) for i in data]


class UserRedis(StrictRedis, LockRedisMixin):
    GET_ALL_USERS_SCRIPT = """
        local ids = redis.call("KEYS", "user:*")
        local objects = {}
        for n, id in ipairs(ids) do
            table.insert(objects, redis.call("GET", id))
            redis.call("EXPIRE", id, KEYS[1])
        end
        return objects
    """

    GET_MODIFIED_USERS_SCRIPT = """
        local ids = redis.call("SMEMBERS", "modified_users")
        redis.call("DEL", "modified_users")
        local objects = {}
        for n, id in ipairs(ids) do
            table.insert(objects, redis.call("GET", id))
            redis.call("EXPIRE", id, KEYS[1])
        end
        return objects
    """

    REMOVE_USER_TTLS_SCRIPT = """
        local ids = redis.call("KEYS", "user:*")
        for n, id in ipairs(ids) do
            redis.call("PERSIST", id)
        end
        return redis.status_reply("OK")
    """

    get_all_users_script = None
    get_modified_users_script = None
    remove_user_ttls_script = None

    def init_scripts(self):
        reg = self.register_script
        self.get_all_users_script = reg(self.GET_ALL_USERS_SCRIPT)
        self.get_modified_users_script = reg(self.GET_MODIFIED_USERS_SCRIPT)
        self.remove_user_ttls_script = reg(self.REMOVE_USER_TTLS_SCRIPT)
        self.init_lock_script()




