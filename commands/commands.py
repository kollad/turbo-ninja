from collections import Counter
from copy import deepcopy
import json
from logging import getLogger


__author__ = 'kollad'

log = getLogger('process')


class CommandProcessor(object):
    command_class = None #must be implemented in a subclass

    def __init__(self, writable_state, content_manager, commands_list):
        assert issubclass(self.command_class, BaseCommand), self.command_class
        self.writable_state = writable_state
        self.content_manager = content_manager

        if isinstance(commands_list, str):
            commands_list = json.loads(commands_list)

        self.commands_list = deepcopy(commands_list)

    def run(self):
        response_events = []
        processed_commands = []
        for data in self.commands_list:
            command = self.command_class.create(
                self.writable_state, self.content_manager,
                data['name'], data.get('arguments', {}),
            )
            command.run()
            response_events.extend(command.response_events)
            processed_commands.append(data['name'])

        self.log(processed_commands, response_events)

        return [event.dump() for event in response_events]

    @staticmethod
    def log_commands(commands):
        return ', '.join(commands)

    @staticmethod
    def log_responses(events):
        events = [e.event_id for e in events]
        counter = Counter(events)
        s = ', '.join(['%s x %s' % (k, v) for k, v in counter.items()])
        return s

    def log(self, processed_commands, response_events):
        commands = self.log_commands(processed_commands)
        responses = self.log_responses(response_events)

        log.info('Commands: [%s]. Responses: [%s]' % (commands, responses))


class CommandMeta(type):

    def __init__(self, name, bases, command):
        super(CommandMeta, self).__init__(name, bases, command)
        if command.get('disabled', False):
            return
        self.registry[name] = self


class BaseCommand(metaclass=CommandMeta):
    registry = None #must be implemented in a subclass
    disabled = True

    def __init__(self, user_state, content_manager, arguments):
        self.user_state = user_state
        self.content_manager = content_manager
        self.arguments = arguments

        self.response_events = []

    def add_response_event(self, *events, merge=False):
        """

        :param events: Events
        :type events: tuple, list, set
        :param merge: Merge same type events into single event
        :type merge: bool
        :return:
        """
        if merge:
            # TODO: Merge events
            pass
        for event in events:
            self.response_events.append(event)

    def run(self):
        raise NotImplementedError()

    @classmethod
    def create(cls, user_state, content_manager, name, arguments):
        command = cls.registry[name]
        instance = command(user_state, content_manager, arguments)
        return instance


class BaseResponseEvent(object):
    pass

