from abc import ABCMeta, abstractproperty, abstractmethod

__author__ = 'lopalo'


class AbstractGameApp(metaclass=ABCMeta):

    @abstractproperty
    def name(self):
        pass

    @abstractmethod
    def get_command_processor_class(self, application_settings):
        pass

    @abstractmethod
    def get_user_manager(self, application_settings):
        pass

    @abstractmethod
    def get_content_manager(self, application_settings):
        pass

