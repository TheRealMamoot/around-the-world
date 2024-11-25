import datetime

DATE_FORMAT = '%Y-%m-%d'


def date_range(start, end=None, days=None, day_step=1, include_end=True):
    assert end or days, 'one of "end" and "days" should be given'
    assert not (end and days), 'at most one of "end" and "days" could be given'

    start = datetime.datetime.strptime(start, DATE_FORMAT).date()
    if end:  # and not days
        end = datetime.datetime.strptime(end, DATE_FORMAT).date()
        days = (end - start).days
        if include_end:
            days += 1

    return [start + datetime.timedelta(days=x) for x in range(0, days, day_step)]


def test():
    print(date_range('2018-07-02', days=5, day_step=1))

    print(date_range('2018-07-02', end='2018-08-24', day_step=1))

    print(date_range('2018-07-02', end='2018-08-23', day_step=3))
    print(date_range('2018-07-02', end='2018-08-24', day_step=3))
    print(date_range('2018-07-02', end='2018-08-25', day_step=3))

    # bad
    # print(range_date('2018-07-02', end='2018-08-24', days=4, day_step=1))
    # print(range_date('2018-07-02', day_step=1))
