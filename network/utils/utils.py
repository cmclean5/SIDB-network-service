# Patrik Hlobil
# nested_iterator.py
# https://gist.github.com/PatrikHlobil/9d045e43fe44df2d5fd8b570f9fd78cc

from itertools import chain

def iterate_all(iterable, returned="key"):
    """Returns an iterator that returns all keys or values
       of a (nested) iterable.

       Arguments:
           - iterable: <list> or <dictionary>
           - returned: <string> "key" or "value"

       Returns:
           - <iterator>
    """

    if isinstance(iterable, dict):
        for key, value in iterable.items():
            if returned == "key":
                yield key
            elif returned == "value":
                if not (isinstance(value, dict) or isinstance(value, list)):
                    yield value
            else:
                raise ValueError("'returned' keyword only accepts 'key' or 'value'.")
            for ret in iterate_all(value, returned=returned):
                yield ret
    elif isinstance(iterable, list):
        for el in iterable:
            for ret in iterate_all(el, returned=returned):
                yield ret

def unlist(values):

    res = ''
    if not isinstance(values, dict):

        if isinstance(values, str):
            return values

        if isinstance(values, list) and len(values) > 0:

            if not isinstance(values[0], str):

                if isinstance(values[0], dict):
                    return ''
                else:
                    while isinstance(values[0], list):
                        values = values[0]

                    if isinstance(values, dict):
                        return ''

            if len(values) == 1:
                res = values[0]
            else:
                res = values

    return res

def check_dict(values):

    res = ''

    if isinstance(values, str):
        res = values

    if isinstance(values, dict):
        res = ''

    if isinstance(values, list):
        values = unlist(values)
        if isinstance(values, dict):
            res = ''
        else:
            res = values

    return res

def check_None(values, replacement='Missing'):

    if isinstance(values, str):
        if values is None:
            values = replacement

    if isinstance(values, list):
        values = [replacement for x in values if x is None]

    return values

def undict(key, values):

    temp = {'%s_%s'%(key, k): v for k,v in values.item()}

    return(temp)

def set_values(values, sep=';'):

    res = ''
    if not isinstance(values, dict):

        if isinstance(values, str):
            res = values

        if isinstance(values, list):
            res = unlist(values)
            if isinstance(res, list):
                res = sep.join(map(str, res))

    return res

def get_values(values, sep=';'):

    res = ''

    if isinstance(values, str) and not (sep in values):
        return values

    elif not isinstance(values, dict):

        if (isinstance(values, str)) and (sep in values):
            res = str.split(values, sep)

        if isinstance(values, list):
            res = unlist(values)
            if isinstance(res, str):
                res = str.split(res, sep)
            if len(res) == 1:
                res = res[0]

    return res


def append_values(key, values, _map, sep, dict_append=False):

    if isinstance(values, dict) or isinstance(values, list) or isinstance(values, str):
        if isinstance(values, dict) and (dict_append is True):
         for k,v in undict(key, values).items():
            _map[k] = v
        if isinstance(values, str):
            _map[key] = values
        if isinstance(values, list):
            values = unlist(values)
            if isinstance(values, str):
                values = str.split(values, sep)
            _map[key] = values

    return(_map)