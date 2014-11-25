from random import Random
from copy import copy
from collections import MutableMapping
from logging import getLogger
import re
import operator

from engine.utils.dictutils import DictView
from engine.utils.mathutils import Weights


log = getLogger('process')


class StashError(Exception):
    def __init__(self, description=None, *args, **kwargs):
        super(StashError, self).__init__(*args, **kwargs)
        self.description = description

    def __str__(self):
        return 'Stash operation error: {description}'.format(**self.__dict__)


class StashValue(object):
    __slots__ = ('value', 'random', 'plain', 'min', 'max',
                 'probability', 'weighted', 'sampled')

    PATTERN = re.compile(
        r"(?P<min>\d+)(:(?P<max>\d+))?(%(?P<probability>\d+))?(?P<weighted>\*)?(#(?P<sampled>\d+))?")

    def __init__(self, value, *, random):
        self.random = random
        self.weighted = False
        if isinstance(value, (int, float)):
            self.value = value
            self.plain = True
            return

        try:
            self.value = int(float(value))
        except ValueError:
            pass
        else:
            self.plain = True
            return

        match = self.PATTERN.match(value)
        if not match:
            raise StashError('Unable to parse {}'.format(value))

        self.value = value
        self.plain = False
        match = match.groupdict()

        self.min = int(self._float(match['min'], 0))
        self.max = int(self._float(match['max'], self.min))
        self.probability = self._float(match['probability'], 100) / 100
        try:
            sampled = int(match['sampled'])
        except TypeError:
            self.weighted = bool(match['weighted'])
            self.sampled = False
        else:
            self.sampled = sampled

    @staticmethod
    def _float(value, default):
        if value is None:
            return default
        else:
            return float(value)

    def roll(self, dice=None):
        if self.plain:
            return self.value
        else:
            if self.probability < 1:
                if dice is None:
                    dice = self.random.random()
                if self.probability <= dice:
                    return 0
                elif self.weighted:
                    self.probability -= 0.01
                    self.probability = max(self.probability, 0)
            if self.min < self.max:
                return self.random.choice(list(range(self.min, self.max + 1)))
            else:
                return self.min

    def format_value(self):
        """Formats changed value"""

        if self.plain:
            return str(self.value)
        if self.min != self.max:
            t = "{}:{}".format(self.min, self.max)
        else:
            t = str(self.min)
        if self.probability < 1:
            t += "%{}".format(int(round(self.probability * 100, 3)))
        if self.weighted:
            t += '*'
        elif self.sampled:
            t += "#{}".format(self.sampled)
        return t

    def __str__(self):
        return '<StashValue: {}>'.format(self.value)

    def __unicode__(self):
        return str(self)

    def __repr__(self):
        return str(self)


class Stash(DictView, MutableMapping):
    def __init__(self, src=None, *, random, **kwargs):
        self.random = random
        self._stash_values = {}
        if src:
            self._stash_values.update(self.init_stash_values(src))
        if kwargs:
            self._stash_values.update(self.init_stash_values(kwargs))
        super(Stash, self).__init__({})
        if self._stash_values:
            self.roll()

    def init_stash_values(self, src):
        for k, v in dict(src).items():
            yield k, StashValue(v, random=self.random)

    @property
    def stash_values(self):
        return self._stash_values

    def format_stash_values(self):
        return {k: v.format_value() for k, v in list(self.stash_values.items())}

    @property
    def weighted_empty(self):
        for value in list(self._stash_values.values()):
            if value.weighted and value.probability:
                return False
        return True

    def copy(self):
        out = self.__class__()
        out._stash_values = copy(self._stash_values)
        out.roll()

    def is_plain(self):
        for value in self._stash_values.values():
            if not value.plain:
                return False
        return True

    def roll(self):
        self._data.clear()
        roll_values = {}
        weighted_values = {}
        sampled_values = {}
        sample_count = 0

        for key, value in self._stash_values.items():
            if value.plain:
                roll_values[key] = value
            elif value.sampled:
                sampled_values[key] = value
                sample_count = value.sampled
            elif value.probability and value.weighted:
                weighted_values[key] = value
            else:
                roll_values[key] = value

        for key, value in roll_values.items():
            self._data[key] = value.roll()

        if len(weighted_values) > 1:
            self._data.update(dict.fromkeys(weighted_values, 0))
            weights = Weights(**dict((key, value.probability) for key, value in weighted_values.items()))
            key = weights.choice()
            value = weighted_values[key]
            self._data[key] = value.roll(0)
        elif len(weighted_values) == 1:
            key, value = next(iter(list(weighted_values.items())))
            self._data[key] = value.roll(0)

        if len(sampled_values) > 1 and sample_count:
            sampled_keys = self.sample(sampled_values, sample_count)
            for key, value in sampled_values.items():
                if key in sampled_keys:
                    self._data[key] = value.roll()
                else:
                    self._data[key] = 0

        return self._data

    def __getitem__(self, item):
        try:
            return self._data[item]
        except KeyError:
            return 0

    def get(self, key, default=None):
        try:
            return self._data[key]
        except KeyError:
            return default

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def __str__(self):
        return ", ".join(["{0}:{1}".format(key, value) for key, value in list(self.items())])

    def __contains__(self, item):
        if isinstance(item, (dict, DictView, list, tuple)):
            item = Stash(item, random=self.random)
        if isinstance(item, Stash):
            for item_key, item_value in list(item.items()):
                if item_key not in list(self.keys()):
                    return False
                if item_value > self[item_key]:
                    return False
            return True
        else:
            return item in self._data

    def parse_value(self, value):
        return StashValue(value, random=self.random).roll()

    def _apply_operator(self, key, value, op):
        current_value = self.get(key, 0)
        value = op(current_value, value)
        if value or current_value:
            self[key] = value

    def _generic_operation_with_dict(self, other, op):
        other = Stash(other, random=self.random)
        for key, value in other.items():
            self._apply_operator(key, value, op)
        return self

    def _generic_operation_with_key_value(self, key_value, op):
        key, value = key_value
        self._apply_operator(key, value, op)
        return self

    def _generic_operation_with_number(self, number, op):
        value = self.parse_value(number)
        for key in list(self.keys()):
            self._apply_operator(key, value, op)
        return self

    def _generic_operation(self, other, op):
        if isinstance(other, (dict, DictView)):
            return self._generic_operation_with_dict(other, op)
        elif isinstance(other, (list, tuple)):
            return self._generic_operation_with_key_value(other, op)
        else:
            return self._generic_operation_with_number(other, op)

    def __add__(self, other):
        return self._generic_operation(other, operator.add)

    def __sub__(self, other):
        return self._generic_operation(other, operator.sub)

    def __mul__(self, other):
        return self._generic_operation(other, operator.mul)

    def __div__(self, other):
        return self._generic_operation(other, operator.div)

    def __bool__(self):
        if not len(self):
            return False
        for key, value in self.items():
            if value:
                return True
        return False

    def __neg__(self):
        negative = Stash(random=self.random)
        for key in list(self._data.keys()):
            try:
                negative[key] = -self._data[key]
            except TypeError:
                negative[key] = self._data[key]
        return negative

    def is_positive(self):
        for value in list(self.keys()):
            if value < 0:
                return False
        return True
