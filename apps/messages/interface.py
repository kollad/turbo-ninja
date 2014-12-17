from abc import ABCMeta, abstractmethod
from uuid import uuid4
import six
from utils.timeutils import milliseconds

__author__ = 'kollad'

STATE_NEW = 'new'
STATE_ACCEPTED = 'accepted'
STATE_DELETED = 'deleted'
STATE_PENDING = 'pending'


class MessagesInterfaceAbstract(metaclass=ABCMeta):
    @abstractmethod
    def count(self, receiver):
        """

        :param receiver:
        :return:
        """

    @abstractmethod
    def fetch(self, receiver, offset=None):
        """

        :param receiver:
        :param offset:
        :return:
        """

    @staticmethod
    def create(sender, receiver, message_type, body=None):
        """

        :param sender:
        :param receiver:
        :param body:
        :param message_type:
        :return:
        """
        return Message({'sender': sender, 'receiver': receiver, 'type': message_type, 'body': body or {}})

    @abstractmethod
    def send(self, messages):
        """

        :param messages:
        :return:
        """


    @abstractmethod
    def remove(self, user_id, messages_ids):
        """

        :param user_id:
        :param messages:
        :return:
        """

    @abstractmethod
    def accept(self, user_id, messages_ids, remove=False):
        """

        :param user_id:
        :param messages:
        :return:
        """


class Message(dict, metaclass=ABCMeta):
    _required_fields = {'sender', 'receiver', 'type'}

    def __init__(self, iterable, **kwargs):
        super().__init__(iterable, **kwargs)
        if not self._required_fields.issubset(self.keys()):
            raise AttributeError('Not all required fields present: {}'.format(self._required_fields - set(self.keys())))
        self.setdefault('id', uuid4().hex)
        self.setdefault('ts', milliseconds())
        self.setdefault('state', STATE_NEW)