from .date import to_date_object, to_date_str, get_date_range_list


def filter_date_by_date_range(date_list, start=None, end=None):
    """
    :param date_list: date string/object list in 2018-07-07 format, string or datetime.date instance
    :param start: start date, include it
    :param end: end date, include it
    :return: date string list
    """
    if not date_list:
        return []

    # sort date string/object
    date_list.sort()

    # default start, end
    if not start:
        start = date_list[0]
    if not end:
        end = date_list[-1]

    # parse string to date
    date_list = [to_date_object(x) for x in date_list]

    wanted_date_list = get_date_range_list(start, end)
    rv = filter(lambda x: to_date_str(x) in wanted_date_list, date_list)

    return [to_date_str(x) for x in rv]
