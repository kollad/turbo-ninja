import unittest

__author__ = 'kollad'


class RedisMessagesTestCaseAbstract(unittest.TestCase):
    SENDER = 'sender_id'
    RECEIVER = 'receiver_id'
    MESSAGE_TYPE = 'message'

    def setUp(self):
        self.messages_interface.connection.flushall()

    def _create_message(self, sender=None, receiver=None, message_type=None, body=None):
        sender = sender or self.SENDER
        receiver = receiver or self.RECEIVER
        message_type = message_type or self.MESSAGE_TYPE
        body = body or {}
        return self.messages_interface.create(sender, receiver, message_type, body)