from collections import defaultdict


def replace_dict_keys(data, new_key_fn):  # type: (dict, (str -> str)) -> dict
    return {new_key_fn(k): data[k] for k in data}


def rename_dict(data, mapping):  # type: (dict, dict) -> dict
    return {v: data[k] for k, v in mapping.items() if v}


def infinite_default_dict():
    return defaultdict(infinite_default_dict)


def filter_dict_by_keys(data, required_keys, get_default=None):
    def get_value(k):
        if get_default:
            return data.get(k, get_default(k))
        else:
            return data[k]

    return {k: get_value(k) for k in required_keys}


def get_dict_value_by_path(data, path, default=None):
    """
    :param default: function to get the default value
    """
    paths = path.split(".")
    rv = data
    for p in paths:
        try:
            rv = data[p]
        except KeyError:
            if default:
                return default(p)
            else:
                raise
    return rv
