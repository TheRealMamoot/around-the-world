import json
import pandas as pd
from functools import reduce


def sum_without_text_fields(df, exclude=None):
    fields = df.dtypes.index
    rv = df[list(set(fields) - set(exclude or []))].sum()
    return rv


def new_blank_data_frame(fields):
    return pd.DataFrame(columns=fields)


def concat_list_of_df(df_list, default_fields):
    if len(df_list) == 0:
        return new_blank_data_frame(default_fields)
    return pd.concat(df_list, ignore_index=True, sort=False)


def df_to_list_of_dict(df):
    # to_dict() got an unexpected keyword argument 'orient'
    if isinstance(df, pd.DataFrame):
        rv = df.to_json(orient='records')
    else:
        raise Exception('do not use this for {}'.format(type(df)))

    rv = json.loads(rv)

    return rv


def as_float(df, fields):
    for f in fields:
        if f in df:
            df[f] = df[f].astype(float)


def aggregate_by_group(df, key, set_fields=None):
    def column_set(series):
        def set_reduce(x, y):
            if isinstance(x, list):
                return sorted(list(set(x + [y])))
            return sorted([x, y])

        return reduce(set_reduce, series)

    rv = df.groupby(key).sum()
    if set_fields:
        set_df = df.groupby(key).agg({k: column_set for k in set_fields})
        rv = pd.concat([rv, set_df], axis=1)

    rv = rv.reset_index(level=[key])
    return rv


def is_empty_df(df):
    if isinstance(df, pd.DataFrame) and len(df.index) == 0:
        return True
    return False
