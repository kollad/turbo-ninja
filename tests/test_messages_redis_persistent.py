import unittest
from apps.messages.backends.redis_persistent import RedisPersistentMessagesInterface
from tests.test_messages import RedisMessagesTestCaseAbstract

__author__ = 'kollad'


class RedisPersistentMessagesTestCase(RedisMessagesTestCaseAbstract):
    @classmethod
    def setUpClass(cls):
        cls.messages_interface = RedisPersistentMessagesInterface(None)


if __name__ == '__main__':
    unittest.main(warnings='ignore')