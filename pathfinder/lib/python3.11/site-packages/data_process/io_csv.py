import csv
import sys
import os
import json
from typing import Iterable
from contextlib import contextmanager

from . import is_py2
from .io_files import prepare_dir

# https://stackoverflow.com/a/15063941/5281824
import csv

maxInt = sys.maxsize
while True:
    # decrease the maxInt value by factor 10
    # as long as the OverflowError occurs.
    try:
        csv.field_size_limit(maxInt)
        break
    except OverflowError:
        maxInt = int(maxInt / 10)

CSV_FORMAT_PARAMS = dict(delimiter=",", quotechar='"')


@contextmanager
def new_csv_writer(path, fields, csv_format=None, keep_open=False, is_excel=False):
    f = None
    try:
        if path is None:
            f = sys.stdout
        elif hasattr(path, "write") or hasattr(path, "read"):
            f = path
        else:
            path = os.path.expanduser(os.path.expandvars(path))
            prepare_dir(path)
            f = open(path, "w")

        if is_excel:
            f.write('\ufeff')

        yv = csv.DictWriter(f, fieldnames=fields, **(csv_format or CSV_FORMAT_PARAMS))
        yv.writeheader()
        yield yv
    finally:
        if f and hasattr(f, 'close') and not keep_open:
            f.close()


@contextmanager
def new_csv_reader(path, fields=None, csv_format=None):
    f = None
    try:
        if hasattr(path, "read"):
            f = path
        else:
            f = open(path)
        yield csv.DictReader(f, fieldnames=fields, **(csv_format or CSV_FORMAT_PARAMS))
    finally:
        f and f.close()


def _process_row(writer, row):
    writer.writerow(row)


def process_row_generator(
    fields, generator, output, process_row=_process_row, **kwargs
):
    c = 0

    with new_csv_writer(output, fields, **kwargs) as writer:
        for row in generator:
            process_row(writer, row)
            c += 1

    return c


def merge_csv_list(file_path_list, fields=None, csv_format=None):
    """
    merge data in some csv list to one list

    :return: list of ordereddict
    """
    rv = []

    def _process_row(row):
        rv.append(row)

    for fp in file_path_list:
        if not os.path.exists(fp):
            raise Exception("file {} does not exist".format(fp))
        with new_csv_reader(fp, fields=fields, csv_format=csv_format) as reader:
            for row in reader:
                _process_row(row)

    return rv


def write_csv(
    data: Iterable[dict], out_path, sort=is_py2, fields=None, writer_kwargs=None
):
    data = list(data)
    # serialize csv values
    for x in data:
        for k, v in x.items():
            if isinstance(v, (list, tuple, dict)):
                x[k] = json.dumps(v, ensure_ascii=False)
            elif v is None:
                x[k] = ''

    if not fields:
        fields = set()
        for x in data:
            for k, v in x.items():
                fields.add(k)
        fields = sorted(fields)

    if sort:
        fields = sorted(fields)
    with new_csv_writer(out_path, fields, **writer_kwargs or {}) as writer:
        for row in data:
            writer.writerow(row)
    return len(data)


def read_csv(path):
    with new_csv_reader(path) as reader:
        return list(reader)
