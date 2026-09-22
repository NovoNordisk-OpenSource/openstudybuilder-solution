"""Decorators that can be used on routers"""

import functools

# pylint: disable=unused-import
from clinical_mdr_api.routers.export import allow_exports

# pylint: disable=unused-import
from clinical_mdr_api.services.decorators import validate_if_study_is_not_locked
from common.config import settings
from common.exceptions import ValidationException


def validate_serial_number_against_neo4j_max_and_min_int():
    """Decorator ensures the provided Serial Number is not bigger than max_int_neo4j, else raises ValidationException."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            ValidationException.raise_if(
                kwargs["serial_number"] > settings.max_int_neo4j
                or kwargs["serial_number"] < -settings.max_int_neo4j,
                msg=f"Serial Number must not be greater than '{settings.max_int_neo4j}' and less than '-{settings.max_int_neo4j}'.",
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator
