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
from engine.user.lock import RedisLock, LockRedis


__author__ = 'kollad'


def encoder_function(data):
    return data_to_json(data)


def decoder_function(data):
    return json_to_data(data)


log = getLogger('process')


class UserManager(object):
    _user_key_pattern = 'user:{}'

    _lock_key_pattern = 'user_lock:{}'


    def __init__(self, settings):
        """
        Initialize player manager

        :param settings: Settings
        :type settings: dict
        :return:
        """
        self.settings = settings
        self.users_redis = None
        self.locks_redis = None
        self.lock_release_script = None
        self.mongo = None
        self.random = Random()

        self.init_redis()
        self.init_mongo()


    def init_redis(self):
        """
        Initialize redis clients

        :return:
        """
        settings = self.settings['user_manager']['redis']
        host = settings['host']
        port = settings['port']
        password = settings['password']
        dbs = settings['dbs']
        self.users_redis = UserRedis(host, port, dbs['users'], password)
        self.locks_redis = LockRedis(host, port, dbs['locks'], password)
        self.log_cmd_redis = StrictRedis(host, port,
                                         dbs['commands_log'], password)
        self.users_redis.init_scripts()
        self.locks_redis.init_scripts()


    def init_mongo(self):
        """
        Initialize mongo client

        :return:
        """
        host = self.settings['user_manager']['mongo']['host']
        port = self.settings['user_manager']['mongo']['port']
        self.mongo = MongoClient(host=host, port=port)


    def get_lock(self, key):
        """
        :return: RedisLock object
        """
        return RedisLock(self.locks_redis, key)


    def format_user_id(self, user_id):
        """
        Format user_id key that would be saved in redis database

        :param user_id: User ID
        :type user_id: str

        :return: Formatted user id key
        :rtype: str
        """
        return self._user_key_pattern.format(user_id)

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
        user_key = self.format_user_id(user_id)
        if self.settings['user_manager']['fixed_random_seed']:
            random = None
        else:
            random = self.random
        if self.users_redis.exists(user_key):
            data = self.decode_data(self.users_redis.get(user_key))
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
        db = self.mongo[self.settings['user_manager']['mongo']['db_name']]
        collection = db[self.settings['user_manager']['mongo']['collection']]
        user_state = collection.find_one({'_id': user_id})

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
        db = self.mongo[self.settings['user_manager']['mongo']['db_name']]
        collection = db[self.settings['user_manager']['mongo']['collection']]
        collection.remove({'_id': user_id})
        pipe = self.users_redis.pipeline(transaction=True)
        pipe.delete(self.format_user_id(user_id))
        pipe.srem('modified_users', self.format_user_id(user_id))
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
        pipe = self.users_redis.pipeline(transaction=True)
        data['user_id'] = user_id
        # the set command cancels a user's ttl
        pipe.set(self.format_user_id(user_id), self.encode_data(data))
        pipe.sadd('modified_users', self.format_user_id(user_id))
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
        return self.users_redis.dbsize() - 1  # minus "modified_users"

    def transaction(self, user_id):
        """
        Context manager helper for opening user state. Provides lock for user get/set operations.

        :param user_id: User ID
        :type user_id: str
        :return: context manager
        """
        key = self._lock_key_pattern.format(user_id)
        lock = self.get_lock(key)
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
        return self.users_redis.scard('modified_users')


    def dump_users(self, all=False):
        db = self.users_redis
        expire = self.settings['user']['session_ttl']
        if all:
            users = db.get_all_script(keys=[expire])
        else:
            users = db.get_modified_script(keys=[expire])
        for user_data in users:
            self._dump_user_to_mongo(self.decode_data(user_data))
        return len(users)

    def remove_user_ttls(self):
        # TODO: a script that calls this method
        self.users_redis.remove_ttls_script()

    def _dump_user_to_mongo(self, user_data):
        """
        Dump player to MongoDB

        :param player_data: User state
        :type player_data: dict or UserState
        :return:
        """
        db = self.mongo[self.settings['user_manager']['mongo']['db_name']]
        collection = db[self.settings['user_manager']['mongo']['collection']]
        collection.ensure_index('user_id')
        collection.find_and_modify({'_id': user_data['user_id']},
                                   dump_value(user_data), upsert=True)

    def log_commands(self, user_id, commands, response):
        settings = self.settings['user_manager']['redis']['log_commands']
        if not settings['enable']:
            return
        if isinstance(commands, str):
            commands = json.loads(commands)
        key = self.format_user_id(user_id)
        data = {"ts": milliseconds(),
                "commands": commands,
                "response": response}
        pipe = self.log_cmd_redis.pipeline(transaction=True)
        pipe.rpush(key, json.dumps(data))
        pipe.ltrim(key, -settings['size'], -1)
        pipe.expire(key, settings['ttl'])
        pipe.execute()

    def get_commands_log(self, user_id):
        key = self.format_user_id(user_id)
        data = self.log_cmd_redis.lrange(key, 0, -1)
        return [json.loads(i.decode("utf-8")) for i in data]


class UserRedis(StrictRedis):
    GET_ALL_SCRIPT = """
        local ids = redis.call("KEYS", "user:*")
        local objects = {}
        for n, id in ipairs(ids) do
            table.insert(objects, redis.call("GET", id))
            redis.call("EXPIRE", id, KEYS[1])
        end
        return objects
    """

    GET_MODIFIED_SCRIPT = """
        local ids = redis.call("SMEMBERS", "modified_users")
        redis.call("DEL", "modified_users")
        local objects = {}
        for n, id in ipairs(ids) do
            table.insert(objects, redis.call("GET", id))
            redis.call("EXPIRE", id, KEYS[1])
        end
        return objects
    """

    REMOVE_TTLS_SCRIPT = """
        local ids = redis.call("KEYS", "user:*")
        for n, id in ipairs(ids) do
            redis.call("PERSIST", id)
        end
        return redis.status_reply("OK")
    """

    get_all_script = None
    get_modified_script = None
    remove_ttls_script = None

    def init_scripts(self):
        register = self.register_script
        self.get_all_script = register(self.GET_ALL_SCRIPT)
        self.get_modified_script = register(self.GET_MODIFIED_SCRIPT)
        self.remove_ttls_script = register(self.REMOVE_TTLS_SCRIPT)




