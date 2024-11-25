from collections import defaultdict
from itertools import chain
from .group_by import group_by
from .dict_helper import replace_dict_keys


def get_count_in_list(lst, k):
    return sum(map(lambda x: 1 if x == k else 0, lst))


def get_unique_key(lst, key, prefix, force=False):
    if force or get_count_in_list(lst, key) > 1:
        return prefix + key
    return key


def _join(
    data_list_a,
    data_list_b,
    a_get_key,
    b_get_key,
    left=True,
    right=True,
    a_prefix="a.",
    b_prefix="b.",
    force=False,
):
    """
    :param data_list_a:
    :param data_list_b:
    :param a_get_key:
    :param b_get_key:
    :param left:
    :param right:
    :return:
    """
    a_keys = data_list_a[0].keys()
    b_keys = data_list_b[0].keys()
    all_origin_fields = list(chain(a_keys, b_keys))

    a_groups = group_by(data_list_a, a_get_key)
    b_groups = group_by(data_list_b, b_get_key)

    # replace keys of dict in groups
    a_groups = {
        k: [
            replace_dict_keys(
                item, lambda k: get_unique_key(all_origin_fields, k, a_prefix, force)
            )
            for item in a_groups[k]
        ]
        for k in a_groups.keys()
    }
    b_groups = {
        k: [
            replace_dict_keys(
                item, lambda k: get_unique_key(all_origin_fields, k, b_prefix, force)
            )
            for item in b_groups[k]
        ]
        for k in b_groups.keys()
    }

    all_group_names = chain(a_groups.keys(), b_groups.keys())

    # loop on all groups
    rv = []
    for g in all_group_names:
        a_list = a_groups.get(g)
        b_list = b_groups.get(g)

        # three join types
        # inner join
        if not left and not right and a_list and b_list:
            for a in a_list:
                for b in b_list:
                    data = defaultdict(lambda: None)
                    rv.append(data)

                    data.update(a)
                    data.update(b)
        # left join
        elif left and a_list:
            for a in a_list:
                for b in b_list or [
                    {
                        get_unique_key(all_origin_fields, k, b_prefix, force): None
                        for k in b_keys
                    }
                ]:
                    data = defaultdict(lambda: None)
                    rv.append(data)

                    data.update(a)
                    data.update(b)
        # right join
        elif right and b_list:
            for b in b_list:
                for a in a_list or [
                    {
                        get_unique_key(all_origin_fields, k, a_prefix, force): None
                        for k in a_keys
                    }
                ]:
                    data = defaultdict(lambda: None)
                    rv.append(data)

                    data.update(a)
                    data.update(b)
        # outer join
        elif left and right:
            for a in a_list or [
                {
                    get_unique_key(all_origin_fields, k, a_prefix, force): None
                    for k in a_keys
                }
            ]:
                for b in b_list or [
                    {
                        get_unique_key(all_origin_fields, k, b_prefix, force): None
                        for k in b_keys
                    }
                ]:
                    data = defaultdict(lambda: None)
                    rv.append(data)

                    data.update(a)
                    data.update(b)

    return rv


def left_join(a, b, a_get_key, b_get_key, **kwargs):
    return _join(a, b, a_get_key, b_get_key, left=True, right=False, **kwargs)


def right_join(a, b, a_get_key, b_get_key, **kwargs):
    return _join(a, b, a_get_key, b_get_key, left=False, right=True, **kwargs)


def inner_join(a, b, a_get_key, b_get_key, **kwargs):
    return _join(a, b, a_get_key, b_get_key, left=False, right=False, **kwargs)


def outer_join(a, b, a_get_key, b_get_key, **kwargs):
    return _join(a, b, a_get_key, b_get_key, left=True, right=True, **kwargs)
