from .io_csv import merge_csv_list
from .io_files import file_list_in
from .filter_date import filter_date_by_date_range


def collect_csv_data_in_dir(data_dir, pattern, get_date_fn, start=None, end=None, fields=None, csv_format=None):
    """
    :param data_dir: in which directory to search files
    :param pattern: pattern to search files
    :param get_date_fn: get date str from file path
    :param start:
    :param end:
    :param fields: needed if csv data miss headers
    :param csv_format: e.g. {delimiter=',', quotechar='"'}

    :return: files, data
    """
    import os
    files = file_list_in(data_dir, pattern)
    files.sort()
    # no file found
    if not files:
        return None, None

    date_list = [get_date_fn(x) for x in files]
    wanted_date_list = filter_date_by_date_range(
        date_list,
        start=start,
        end=end,
    )
    files = [x for x in files if get_date_fn(x) in wanted_date_list]
    # no file matched the date range
    if not files:
        return None, None

    data = merge_csv_list([os.path.join(data_dir, l) for l in files], fields=fields, csv_format=csv_format)

    return files, data
