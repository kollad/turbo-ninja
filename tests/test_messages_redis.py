import json
import unittest
import time
from uuid import uuid4
from apps.messages.backends.redis import RedisMessagesInterface
from apps.messages.interface import Message, STATE_NEW
from tests.test_messages import MessagesTestCaseMixin

__author__ = 'kollad'


class RedisMessagesTestCase(MessagesTestCaseMixin, unittest.TestCase):
    def setUp(self):
        self.messages_interface.connection.flushall()

    def tearDown(self):
        self.messages_interface.connection.flushall()

    @classmethod
    def setUpClass(cls):
        cls.messages_interface = RedisMessagesInterface(None)

    def test_01_create(self):
        super()._test_01_create()

    def test_02_send(self):
        super()._test_02_send()

    def test_03_send_multiple(self):
        super()._test_03_send_multiple()

    def test_04_send_and_accept(self):
        super()._test_04_send_and_accept()


if __name__ == '__main__':
    unittest.main(warnings='ignore')