import unittest
from apps.messages.backends.mongo import MongoMessagesInterface
from tests.test_messages import MessagesTestCaseMixin

__author__ = 'kollad'


class MongoMessagesTestCase(MessagesTestCaseMixin, unittest.TestCase):
    def setUp(self):
        self.messages_interface.connection.drop_database('turbo_ninja')

    @classmethod
    def setUpClass(cls):
        cls.messages_interface = MongoMessagesInterface(None)

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