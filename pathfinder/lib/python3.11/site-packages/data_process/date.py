import datetime
import calendar

from .date_range import date_range
from . import is_py2


DATE_FORMAT_DAY = "%Y-%m-%d"
DATE_FORMAT_MONTH = "%Y-%m"
DATE_FORMAT_YEAR = "%Y"
DATE_FORMAT_MONTH_ABBR = "%b %Y"

default_formats = (DATE_FORMAT_DAY, DATE_FORMAT_MONTH, DATE_FORMAT_YEAR)


class DateProcessException(Exception):
    pass


def is_string(x):
    if is_py2:
        return isinstance(x, (str, unicode))
    else:
        return isinstance(x, str)


def to_date_object(date, allowed_date_format_list=None, raise_if_fail=True):
    allowed_date_format_list = allowed_date_format_list or default_formats
    if is_string(date):
        for fmt in allowed_date_format_list:
            try:
                return datetime.datetime.strptime(date, fmt).date()
            except ValueError as e:
                if not raise_if_fail:
                    print("ignore parse date exception: {}".format(e))
        if raise_if_fail:
            exc_text = "{} is not a valid date format [{}]".format(
                date, ", ".join(allowed_date_format_list)
            )
            raise DateProcessException(exc_text)
    return date


def to_date_str(date):
    if isinstance(date, datetime.date):
        return date.strftime(DATE_FORMAT_DAY)
    elif isinstance(date, datetime.datetime):
        return date.date().strftime(DATE_FORMAT_DAY)
    return date


def get_date_range_list(start, end, include_end=True):
    start = to_date_str(start)
    end = to_date_str(end)
    return [to_date_str(x) for x in date_range(start, end=end, include_end=include_end)]


def get_first_day_of_month(date, raise_if_fail=True):
    date = to_date_object(date, raise_if_fail=raise_if_fail)
    day = 1
    return date.replace(day=day)


def get_last_day_of_month(date, raise_if_fail=True):
    date = to_date_object(date, raise_if_fail=raise_if_fail)
    day = calendar.monthrange(date.year, date.month)[1]
    return date.replace(day=day)


def get_days_of_month(date):
    first = get_first_day_of_month(date)
    last = get_last_day_of_month(date)
    return get_date_range_list(first, last, include_end=True)


def today(with_tz=False):
    n = now(with_tz=with_tz)
    return n.date()


def now(with_tz=False):
    if with_tz:
        try:
            from django.utils import timezone

            return timezone.now()
        except Exception:
            import pytz

            u = datetime.datetime.utcnow()
            u = u.replace(tzinfo=pytz.utc)
            return u
    else:
        return datetime.datetime.now()


def get_days_of_year(year):
    first = datetime.date(int(year), 1, 1)
    last = get_last_day_of_month(first.replace(month=12, day=31))
    return get_date_range_list(first, last, include_end=True)


def get_start_end_daily(date):
    date = to_date_object(
        date, raise_if_fail=True, allowed_date_format_list=[DATE_FORMAT_DAY]
    )
    return date, date


def get_start_end_monthly(date):
    date = to_date_object(
        date, raise_if_fail=True, allowed_date_format_list=[DATE_FORMAT_MONTH]
    )

    start = get_first_day_of_month(date)
    end = get_last_day_of_month(date)
    return start, end


def get_start_end_yearly(date):
    date = to_date_object(
        date, raise_if_fail=True, allowed_date_format_list=[DATE_FORMAT_YEAR]
    )

    days_of_year = get_days_of_year(date.year)
    return days_of_year[0], days_of_year[-1]


def to_month_abbreviated_format(date_str):
    return datetime.datetime.strptime(date_str, DATE_FORMAT_MONTH).strftime(
        DATE_FORMAT_MONTH_ABBR
    )


def convert_date_format(date_str, in_format, out_format):
    return datetime.datetime.strptime(date_str, in_format).strftime(out_format)
