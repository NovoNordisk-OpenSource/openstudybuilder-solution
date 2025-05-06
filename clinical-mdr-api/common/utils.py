import datetime
import logging
import os
from datetime import datetime
from types import GenericAlias, NoneType, UnionType
from typing import Any, Type, get_args, get_origin

import neo4j
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from common import config
from common.exceptions import ValidationException

log = logging.getLogger(__name__)


def strtobool(value: str) -> int:
    """Convert a string representation of truth to integer 1 (true) or 0 (false).

    Returns 1 for True values: 'y', 'yes', 't', 'true', 'on', '1'.
    Returns 0 for False values: 'n', 'no', 'f', 'false', 'off', '0'.
    Otherwise raises ValueError.

    Reimplemented because of deprecation https://peps.python.org/pep-0632/#migration-advice

    Returns int to remain compatible with Python 3.7 distutils.util.strtobool().
    """

    val = value.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return 1
    if val in ("n", "no", "f", "false", "off", "0"):
        return 0
    raise ValueError(f"invalid truth value: {value:s}")


def booltostr(value: bool | str | int, true_format: str = "Yes") -> str:
    """
    Converts a boolean value to a string representation.
    True values are 'y', 'Y', 'Yes', 'yes', 't', 'true', 'on', and '1';
    False values are 'n', 'N', 'No', 'no', 'f', 'false', 'off', and '0'.

    Args:
        value (bool | str | int): The boolean value to convert. If a string is passed, it will be converted to a boolean.
        true_format (str, optional): The string representation of the True value. Defaults to "Yes".

    Returns:
        str: The string representation of the boolean value.

    Raises:
        ValueError: If the true_format argument is invalid.
    """
    if isinstance(value, str):
        value = bool(strtobool(value))

    mapping = {
        "y": "n",
        "Y": "N",
        "Yes": "No",
        "yes": "no",
        "t": "f",
        "true": "false",
        "on": "off",
        "1": "0",
    }

    if true_format in mapping:
        if value:
            return true_format
        return mapping[true_format]
    raise ValueError(f"Invalid true format {true_format}")


def convert_to_datetime(value: "neo4j.time.DateTime") -> datetime | None:
    """
    Converts a neo4j.time.DateTime object from the database to a Python datetime object.

    Args:
        value (neo4j.time.DateTime): The DateTime object to convert.

    Returns:
        datetime.datetime: The Python datetime object.
    """
    return value.to_native() if value is not None else None


def validate_page_number_and_page_size(page_number: int, page_size: int):
    validate_max_skip_clause(page_number=page_number, page_size=page_size)


def validate_max_skip_clause(page_number: int, page_size: int) -> None:
    # neo4j supports `SKIP {val}` values which fall within unsigned 64-bit integer range
    ValidationException.raise_if(
        max(1, page_number) * max(1, page_size) > config.MAX_INT_NEO4J,
        msg=f"(page_number * page_size) value cannot be bigger than {config.MAX_INT_NEO4J}",
    )


def load_env(key: str, default: str | None = None):
    value = os.environ.get(key)
    log.info("ENV variable fetched: %s=%s", key, value)
    if value is None and default is None:
        log.error("%s is not set and no default was provided", key)
        raise EnvironmentError(f"Failed because {key} is not set.")
    if value is not None:
        return value
    log.warning("%s is not set, using default value: %s", key, default)
    return default


def get_field_type(tp: Type[Any]) -> Type[Any]:
    """
    Determines the actual type of a given type hint, handling generic types and nested types.

    Args:
        tp (Type[Any]): The type hint to analyze.

    Returns:
        Type[Any]: The resolved type. If the type hint is a generic type, it returns the type of the contained elements.
        If the type hint is a dictionary, it returns the type of the values.
        Otherwise, it returns the type itself.
    """
    origin = get_origin(tp)
    if not origin or not hasattr(tp, "__args__"):
        return tp

    args = get_args(tp)

    args = tuple(arg for arg in args if arg is not NoneType)

    if len(args) > 1:
        if origin is dict:
            return args[1]
        return tp

    if isinstance(args[0], GenericAlias):
        return get_field_type(args[0])

    return args[0]


def get_sub_fields(field_info: FieldInfo):
    """
    Extracts sub-fields from the given field information.

    This function examines the annotation of the provided FieldInfo object and
    returns a list of sub-fields if the annotation is a list or a union type
    containing a list. If the annotation is not a list or does not contain a list,
    the function returns None.

    Args:
        field_info (FieldInfo): The field information containing the annotation to be examined.

    Returns:
        list | None: A list of sub-fields if the annotation is a list or a union type containing a list, otherwise None.
    """
    if (
        isinstance(field_info.annotation, GenericAlias)
        and get_origin(field_info.annotation) is list
    ):
        return list(get_args(field_info.annotation))

    if isinstance(field_info.annotation, UnionType):
        fields = tuple(
            field for field in get_args(field_info.annotation) if field is not NoneType
        )
        for field in fields:
            if isinstance(field, GenericAlias) and get_origin(field) is list:
                return list(get_args(field))

    return None


def version_string_to_tuple(version: str) -> tuple[int, int]:
    major, minor = version.split(".", 1)
    return (int(major), int(minor))


def get_edit_input_or_previous_value(
    edit_input: BaseModel,
    existing_vo: object,
    field_name: str,
    field_name_in_vo: str | None = None,
):
    """
    Get the value of a field from the edit input if it was provided,
    or return the value from the existing VO if not.
    The ``field_name_in_vo`` parameter allows specifying a different field name in the VO.
    If not provided, it defaults to the same name as in the edit input.
    """
    if field_name_in_vo is None:
        field_name_in_vo = field_name
    if field_name in edit_input.model_fields_set:
        return getattr(edit_input, field_name)
    return getattr(existing_vo, field_name_in_vo)
