from datetime import timedelta, datetime
from typing import Tuple

import pytz
from dateutil import parser

SG_TIMEZONE = 'Asia/Singapore'


def get_curr_dt_str(dt_format: str, timezone_val: str = None) -> str:
    """
    Get the
    """
    tz = pytz.timezone(timezone_val) if timezone_val else pytz.UTC
    return datetime.now(tz=tz).strftime(dt_format)


def to_utc_dt_str(datetime_str: str, dt_format: str, local_tz=SG_TIMEZONE) -> str:
    """
    Convert a datetime string to an UTC datetime string.
    If the input datetime string has no timezone, it is assumed to be in SG timezone.
    """
    timezone = pytz.timezone(local_tz)
    dt = parser.parse(datetime_str)
    if dt.tzinfo is None:
        dt = dt.astimezone(timezone)

    return dt.astimezone(pytz.UTC).strftime(dt_format)


def get_utc_datetime_start_end_str(datetime_str: str, dt_format: str, local_tz='Asia/Singapore') -> Tuple[str, str]:
    """
    Get UTC datetime string for the 0000 and 2359 hours of a given local datetime.
    """
    timezone = pytz.timezone(local_tz)
    dt = parser.parse(datetime_str)
    if dt.tzinfo is None:
        dt = dt.astimezone(timezone)

    dt0 = dt.replace(hour=0, minute=0)
    dt1 = dt0 + timedelta(days=1)

    dt0_str = dt0.astimezone(pytz.UTC).strftime(dt_format)
    dt1_str = dt1.astimezone(pytz.UTC).strftime(dt_format)
    return dt0_str, dt1_str
