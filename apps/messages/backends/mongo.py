from pymongo import MongoClient
import pymongo
from apps.messages.backends.redis import RedisMessagesInterface
from apps.messages.interface import MessagesInterfaceAbstract

__author__ = 'kollad'

HOST = 'localhost'
PORT = 27017
DB = 'turbo_ninja'
COLLECTION = 'messages'


class MongoMessagesInterface(MessagesInterfaceAbstract):
    """
    Much the same as RedisMessageInterface except message would be stored in persistent storage,
    like MongoDB, MySQL, PostgreSQL etc.
    """
    _connection = None
    _db = None
    _collection = None

    def __init__(self, settings):
        self.settings = settings
        self.collection.ensure_index([
            ('id', pymongo.ASCENDING),
            ('sender', pymongo.ASCENDING),
            ('receiver', pymongo.ASCENDING)
        ])

    @property
    def connection(self):
        if self._connection is None:
            self._connection = MongoClient(host=HOST, port=PORT)
        return self._connection

    @property
    def db(self):
        if self._db is None:
            self._db = self.connection[DB]
        return self._db

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.db[COLLECTION]
        return self._collection

    def remove(self, user_id, messages_ids):
        return self.collection.remove({'id': {'$in': messages_ids}, 'receiver': user_id})

    def send(self, messages):
        if not isinstance(messages, (list, set)):
            messages = [messages]
        bulk = self.collection.initialize_ordered_bulk_op()
        for message in messages:
            bulk.insert(message)
        result = bulk.execute()
        return result

    def accept(self, user_id, messages_ids, remove=True):
        if remove:
            return self.remove(user_id, messages_ids)
        else:
            return self.collection.find_and_modify(
                {'id': {'$in': messages_ids}, 'receiver': user_id},
                {'$set': {'accepted': True}})

    def fetch(self, receiver, offset=None):
        return list(self.collection.find({'receiver': receiver}))

    def count(self, receiver):
        return self.collection.find({'receiver': receiver}).count()

