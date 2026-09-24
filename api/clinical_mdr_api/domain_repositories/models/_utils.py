import datetime
from typing import Any

import neo4j.time

from common.utils import convert_to_datetime


def convert_to_tz_aware_datetime(value: datetime.datetime):
    """
    Converts a datetime object to a timezone-aware datetime object with UTC timezone.

    Args:
        value (datetime.datetime): The datetime object to convert.

    Returns:
        datetime.datetime: The timezone-aware datetime object with UTC timezone.
    """
    return value.astimezone(tz=datetime.timezone.utc)


def format_generic_header_values(values: list[Any]):
    """
    Formats a list of values to match the expected format for generic headers.

    Args:
        values (list[Any]): The list of values to format.

    Returns:
        list: The formatted list of values, with any DateTime objects converted to Python datetime objects.
    """
    if len(values) > 0 and isinstance(values[0], neo4j.time.DateTime):
        return [convert_to_datetime(_val) for _val in values]
    return values


class ListDistinct(list):
    def distinct(self):
        return list(dict.fromkeys(self))
