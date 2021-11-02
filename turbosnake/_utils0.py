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
