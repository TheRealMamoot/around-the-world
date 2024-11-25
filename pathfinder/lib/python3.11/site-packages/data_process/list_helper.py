from . import is_py2

iter_types = [tuple, list]
if not is_py2:
    iter_types.append(range)
# isinstance() arg 2 must be a type or tuple of types
iter_types = tuple(iter_types)


def flat_list(data):
    if not isinstance(data, iter_types):
        return data

    rv = []
    for x in data:
        if isinstance(x, iter_types):
            rv += flat_list(x)
        else:
            rv.append(x)
    return rv


def test_flat():
    a = [1, 2, range(3), 3, range(2, 5), [[3, [2, 4]], 4, 5]]
    assert flat_list(a) == [1, 2, 0, 1, 2, 3, 2, 3, 4, 3, 2, 4, 4, 5]
