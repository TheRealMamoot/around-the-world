import copy
from decimal import Decimal
from . import is_py2


def is_float(value):
    if isinstance(value, (float, Decimal)):
        return True
    if isinstance(value, str):
        if all(x in "0123456789." for x in (value[1:] if value[0] == '-' else value)):
            return True
    return False


class DictIterator(object):
    def __init__(self, data):  # type: (dict) -> None
        self.data = copy.deepcopy(data)
        if hasattr(self, "init") and callable(self.init):
            self.init()

    def transfer(self):
        return self._transfer_dict(self.data)

    def _transfer_dict(self, data):  # type: (dict) -> dict
        for k, v in data.items():
            data[k] = self._transfer_value(v)
        return self.value_dict(data)

    def _transfer_value(self, v):
        if is_float(v):
            return self.value_float(v)
        if isinstance(v, int):
            return self.value_int(v)
        elif isinstance(v, str):
            # str(bytes) in python2 and str(unicode) in python3
            return self.value_str(v)
        elif isinstance(v, bytes):
            # exactly bytes
            return self.value_bytes(v)
        elif is_py2 and isinstance(v, unicode):
            # exactly unicode, only in python2
            return self.value_unicode(v)
        elif isinstance(v, list):
            rv = [self._transfer_value(x) for x in v]
            return self.value_list(rv)
        elif isinstance(v, dict):
            rv = self._transfer_dict(v)
            return self.value_dict(rv)
        else:
            raise Exception("unprocessed value: {}, type: {}".format(v, type(v)))

    def value_list(self, v):
        return v

    def value_dict(self, v):
        return v

    def value_str(self, value):
        return value

    def value_bytes(self, value):
        return value

    def value_unicode(self, value):
        return value

    def value_float(self, value):
        return value

    def value_int(self, value):
        return value


class ObjectifyDict(dict):
    def __getattr__(self, item):
        if item in self:
            return self[item]


def get_fn_float(ndigit=2, decimal=True):
    def value_float(value):
        rv = ("{:.%sf}" % ndigit).format(Decimal(value))
        if decimal:
            return Decimal(rv)
        return rv

    return value_float


def get_fixed_float_dict_iterator(ndigit=3):
    class FixFloatDictIterator(DictIterator):
        def init(self):
            self.value_float = get_fn_float(ndigit=ndigit, decimal=True)

        def value_dict(self, v):
            return ObjectifyDict(v)

    return FixFloatDictIterator


def test():
    data = {
        "a": "3.0000000001",
        "b": ["4.243420004"],
        "c": {"cc": "34.00003", "cd": "32.23423423"},
    }

    iterator = get_fixed_float_dict_iterator()(data)
    print(iterator.transfer())
    print(data)
