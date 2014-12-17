import json
from redis import StrictRedis
from apps.messages.interface import MessagesInterfaceAbstract

__author__ = 'kollad'

# TODO: this should be set in settings
HOST = 'localhost'
PORT = 6379
DB = 5
TTL = 60 * 60 * 24


class RedisMessagesInterface(MessagesInterfaceAbstract):
    _connection = None

    def __init__(self, settings):
        # TODO: provide settings which should contain redis connection information
        self.settings = settings

    @property
    def connection(self):
        if self._connection is None:
            self._connection = StrictRedis(host=HOST, port=PORT, db=DB)
        return self._connection

    @staticmethod
    def format_user_messages_key(user_id):
        return 'messages:{}'.format(user_id)

    @staticmethod
    def format_message_key(message_id):
        return 'message:{}'.format(message_id)

    @staticmethod
    def decode_response(response):
        return response.decode('utf-8')

    @staticmethod
    def encode(value):
        return json.dumps(value)

    @staticmethod
    def decode(value):
        if isinstance(value, bytes):
            value = value.decode()
        return json.loads(value)

    def remove(self, user_id, messages_ids):
        """

        :param user_id: User ID
        :param messages_ids:
        :return:
        """
        pipe = self.connection.pipeline(transaction=True)
        for message_id in messages_ids:
            _message_key = self.format_message_key(message_id)
            pipe.delete(_message_key)
            pipe.srem()

    def accept(self, user_id, messages_ids, remove=True):
        """

        :param user_id:
        :param messages_ids: Messages IDs list
        :type messages_ids: list
        :param remove: Remove from storage
        :type remove: bool
        :return:
        """
        pipe = self.connection.pipeline(transaction=True)
        _message_keys = [self.format_message_key(message_id) for message_id in messages_ids]
        if remove:
            pipe.delete(*_message_keys)
            pipe.srem(self.format_user_messages_key(user_id), *messages_ids)
            result = pipe.execute()[0]
            return result
        return True

    def count(self, receiver):
        """

        :param receiver:
        :return:
        """
        key = self.format_user_messages_key(receiver)
        if self.connection.exists(key):
            return self.connection.scard(key)
        return 0

    def send(self, messages):
        """

        :param messages:
        :return:
        """
        if not isinstance(messages, (list, set)):
            messages = [messages]
        pipe = self.connection.pipeline(transaction=True)
        for message in messages:
            pipe.set(self.format_message_key(message['id']), self.encode(message))
            pipe.expire(message['id'], TTL)
            pipe.sadd(self.format_user_messages_key(message['receiver']), message['id'])
        result = pipe.execute()[0]
        return result

    def fetch(self, receiver, offset=None):
        """

        :param receiver:
        :param offset:
        :return:
        """
        key = self.format_user_messages_key(receiver)
        if self.connection.exists(key):
            messages_ids = self.connection.smembers(key)
            if messages_ids:
                pipe = self.connection.pipeline()
                for message_id in messages_ids:
                    _message_key = self.format_message_key(message_id.decode('utf-8'))
                    pipe.get(_message_key)
                result = pipe.execute()
                return [self.decode(r) for r in result]
        return []