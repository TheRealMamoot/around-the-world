import os
from yaml import load, dump
from .io_files import prepare_dir

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def to_yaml(data, sort_keys=None):
    if sort_keys is None:
        sort_keys = bool(os.getenv("SORT_KEYS"))
    return dump(
        data,
        Dumper=Dumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=sort_keys,
    )


def from_yaml(stream):
    return load(stream, Loader=Loader)


def read_yaml(path):
    with open(path) as f:
        return from_yaml(f.read())


def write_yaml(data, out_path):
    prepare_dir(out_path)
    with open(out_path, "w") as f:
        f.write(to_yaml(data))
