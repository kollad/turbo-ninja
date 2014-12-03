from abc import ABCMeta, abstractmethod

__author__ = 'kollad'


class DataObjectAbstract(metaclass=ABCMeta):
    @abstractmethod
    def reload_cache(self, key):
        pass

    @abstractmethod
    def drop_cache(self):
        pass