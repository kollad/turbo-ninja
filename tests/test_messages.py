import json
import unittest
import time
from uuid import uuid4
from apps.messages.interface import Message
from apps.messages.interface import STATE_NEW

__author__ = 'kollad'


class MessagesTestCaseMixin(object):
    SENDER = 'sender_id'
    RECEIVER = 'receiver_id'
    MESSAGE_TYPE = 'message'

    def _create_message(self, sender=None, receiver=None, message_type=None, body=None):
        sender = sender or self.SENDER
        receiver = receiver or self.RECEIVER
        message_type = message_type or self.MESSAGE_TYPE
        body = body or {}
        return self.messages_interface.create(sender, receiver, message_type, body)

    def _test_01_create(self):
        message = self._create_message()

        self.assertIsInstance(message, Message)
        self.assertEqual(self.SENDER, message['sender'])
        self.assertEqual(self.RECEIVER, message['receiver'])
        self.assertEqual(self.MESSAGE_TYPE, message['type'])
        self.assertEqual(message['state'], STATE_NEW)
        ts = time.time() * 1000
        _d = json.dumps(message)
        print('dumps time: %.4fms' % (time.time() * 1000 - ts))
        _l = json.loads(_d)
        ts2 = time.time() * 1000
        print('loads time: %.4fms' % (time.time() * 1000 - ts2))
        print('total time: %.4fms' % (time.time() * 1000 - ts))

    def _test_02_send(self):
        body = {'resource': 1}
        message = self._create_message(body=body)

        sent = self.messages_interface.send(message)
        self.assertTrue(sent)

        count = self.messages_interface.count(self.RECEIVER)
        fetched_messages = self.messages_interface.fetch(self.RECEIVER)
        self.assertEqual(count, 1)
        self.assertEqual(len(fetched_messages), 1)
        self.assertIn('resource', fetched_messages[0]['body'])
        self.assertEqual(fetched_messages[0]['body']['resource'], 1)

    def _test_03_send_multiple(self):
        senders_count = 10
        random_senders = [uuid4().hex for _ in range(senders_count)]
        for sender in random_senders:
            body = {'resource': 1}
            message = self._create_message(sender=sender, body=body)
            sent = self.messages_interface.send(message)
            self.assertTrue(sent)

        count = self.messages_interface.count(self.RECEIVER)
        self.assertEqual(count, senders_count)
        fetched_messages = self.messages_interface.fetch(self.RECEIVER)

        resources = {'resource': 0}
        for message in fetched_messages:
            for key, value in message['body'].items():
                resources[key] += value
        self.assertEqual(resources['resource'], senders_count)

    def _test_04_send_and_accept(self):
        senders_count = 10
        random_senders = [uuid4().hex for _ in range(senders_count)]
        for sender in random_senders:
            body = {'resource': 1}
            message = self._create_message(sender=sender, body=body)
            sent = self.messages_interface.send(message)
            self.assertTrue(sent)

        count = self.messages_interface.count(self.RECEIVER)
        self.assertEqual(count, senders_count)
        fetched_messages = self.messages_interface.fetch(self.RECEIVER)

        resources = {'resource': 0}
        for message in fetched_messages:
            for key, value in message['body'].items():
                resources[key] += value
        self.messages_interface.accept(self.RECEIVER, [message['id'] for message in fetched_messages])
        self.assertEqual(resources['resource'], senders_count)
        after_accepted_count = self.messages_interface.count(self.RECEIVER)
        self.assertEqual(after_accepted_count, 0)