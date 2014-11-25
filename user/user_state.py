from random import Random

from engine.utils.dictutils import MappingView
from engine.user.user_stash import Stash

__author__ = 'kollad'


class UserStash(Stash):
    def __init__(self, state, **kwargs):
        self.state = state
        data = state['resources']
        super(UserStash, self).__init__(data, **kwargs)
        self._data = data

    def copy(self):
        return UserStash(self.state)


class UserState(MappingView):
    def __init__(self, data, *args, random, **kwargs):
        super(UserState, self).__init__(*args, **kwargs)
        self._data = data or {}
        self._content_manager = None
        if random is None:
            self.random = Random(0)
        else:
            self.random = random

    @property
    def content_manager(self):
        if self._content_manager is None:
            raise ValueError("Content manager is not set")
        return self._content_manager

    def set_content_manager(self, manager):
        self._content_manager = manager

    def __setitem__(self, item, value):
        self._data[item] = value

    def __delitem__(self, key):
        del self._data[key]

    def __getitem__(self, item):
        return self._data[item]

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]

    def increase_id_counter(self):
        count = self.get('_id_counter', 0)
        self['_id_counter'] = count + 1
        return count

    def make_stash(self, data):
        return Stash(data, random=self.random)

    @property
    def stash(self):
        """
        :return: User stash
        :rtype: UserStash
        """
        return UserStash(self._data, random=self.random)

    @stash.setter
    def stash(self, stash):
        """
        :type stash: UserStash
        :param stash: Stash
        """
        self._stash = stash

    @property
    def map(self):
        return self.setdefault('map', {})

    @property
    def tilegrid(self):
        """
        Information about cells that are not passable

        :return:
        """
        return self.map.setdefault('tilegrid', [])

    @property
    def layers(self):
        """
        Map layers

        :return:
        """
        return self.map.setdefault('layers', {})

    @property
    def objects(self):
        """
        Map placed objects

        :return:
        """
        return self.map.setdefault('objects', {})

    @property
    def open_cells(self):
        """
        Opened cells

        :return:
        """
        return self.map.setdefault('open_cells', [])

    @property
    def areas(self):
        """
        Map 3x3 areas

        :return:
        """
        return self.map.setdefault('areas', [])

    @property
    def active_processes(self):
        """
        Active interaction processes

        :return:
        """
        return self.setdefault('active_processes', {})

