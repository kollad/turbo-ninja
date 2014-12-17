from apps.messages.backends.redis import RedisMessagesInterface

__author__ = 'kollad'


class RedisPersistentMessagesInterface(RedisMessagesInterface):
    """
    Much the same as RedisMessageInterface except message would be stored in persistent storage,
    like MongoDB, MySQL, PostgreSQL etc.
    """

    def __init__(self, settings):
        super().__init__(settings)

        # TODO: override required methods to provide persistent storage for messages