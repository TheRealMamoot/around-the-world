from decimal import Decimal


def to_decimal(value, ndigits=3):
    return Decimal(("{:0.%sf}" % ndigits).format(float(value or 0)))
