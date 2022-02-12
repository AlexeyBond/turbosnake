import random
import string
from typing import Iterable


def have_differences_by_keys(dict1: dict, dict2: dict, keys: Iterable):
    """Check if two given dictionaries have differences in values of given keys."""
    for name in keys:
        try:
            value1 = dict1[name]
        except KeyError:
            if name in dict2:
                return True
        else:
            try:
                value2 = dict2[name]
            except KeyError:
                return True
            else:
                if value1 != value2:
                    return True

    return False


def random_id(
        length=10,
        first_character_choices=string.ascii_lowercase,
        rest_character_choices=string.ascii_lowercase + string.digits
):
    """Generates a random id string."""

    assert length >= 1

    return ''.join((
        random.choice(first_character_choices),
        *random.choices(rest_character_choices, k=length - 1)
    ))


class RandomIdSet:
    def __init__(self, **settings):
        self._settings = settings
        self._used = set()

    def generate(self):
        while True:
            i = random_id(**self._settings)
            if i in self._used:
                continue
            self._used.add(i)
            return i
