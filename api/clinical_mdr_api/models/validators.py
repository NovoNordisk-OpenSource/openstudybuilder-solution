"""Reusable pydantic validator functions"""

import re
from datetime import date, datetime, timezone
from typing import Any

from pydantic import ValidationInfo

from clinical_mdr_api.domains._utils import get_iso_lang_data
from clinical_mdr_api.domains.enums import OdmTranslatedTextTypeEnum
from clinical_mdr_api.domains.odms.utils import EN_LANGUAGE, ENG_LANGUAGE
from common.exceptions import ValidationException

FLOAT_REGEX = "^[0-9]+\\.?[0-9]*$"

# Non-empty strings accepted by ``validate_string_represents_boolean`` (case
# insensitive). Applied as a ``pattern=`` constraint on the same fields so the
# OpenAPI schema advertises the exact set of values the runtime accepts and
# contract testers (Schemathesis v4) stop generating strings the validator
# would reject with HTTP 422.
BOOLEAN_STRING_PATTERN = r"^(?i:y|yes|t|true|on|1|n|no|f|false|off|0)$"


def validate_string_represents_boolean(value, info: ValidationInfo):
    """
    Validates whether a string value represents a boolean value.

    Args:
        cls: The class to which the field belongs.
        value: The value to validate.
        info: ValidationInfo

    Returns:
        str: The validated value.

    Raises:
        ValidationException: If the value does not represent a boolean value.
    """
    # Only treat missing values (``None``) as "false". An empty string is
    # explicitly rejected so it does not bypass the ``BOOLEAN_STRING_PATTERN``
    # declared on the Input-model fields that use this validator.
    # Other falsy types (0, False, {}, []) are type violations against a
    # string-typed field and must be rejected explicitly.
    if value is None:
        return "false"

    truthy = ("y", "yes", "t", "true", "on", "1")
    falsy = ("n", "no", "f", "false", "off", "0")

    ValidationException.raise_if(
        not isinstance(value, str),
        msg=f"Unsupported boolean value '{value}' for field '{info.field_name}'. Must be a string, got {type(value).__name__}.",
    )

    ValidationException.raise_if(
        value.lower() not in (truthy + falsy),
        msg=f"Unsupported boolean value '{value}' for field '{info.field_name}'. Allowed values are: {truthy + falsy}.",
    )

    return value


def validate_name_only_contains_letters(value, info: ValidationInfo):
    """
    Validates whether a string value contains only letters.

    Args:
        cls: The class to which the field belongs.
        value: The value to validate.
        info: ValidationInfo

    Returns:
        str: The validated value.

    Raises:
        ValueError: If the value contains characters other than letters.
    """
    if value is None:
        return value
    if not isinstance(value, str):
        raise ValueError(
            f"Provided value '{value}' for '{info.field_name}' is invalid. Must only contain letters."
        )
    if re.search("[^a-zA-Z]", value):
        raise ValueError(
            f"Provided value '{value}' for '{info.field_name}' is invalid. Must only contain letters."
        )
    return value


def validate_regex(value, info: ValidationInfo):
    """
    Validates whether a string value is a valid regular expression.

    Args:
        cls: The class to which the field belongs.
        value: The value to validate.
        info: ValidationInfo

    Returns:
        str: The validated regular expression.

    Raises:
        ValueError: If the value is not a valid regular expression.
    """
    if value:
        if not isinstance(value, str):
            raise ValueError(
                f"Provided regex value '{value}' for field '{info.field_name}' is invalid. Must be a string, got {type(value).__name__}."
            )
        try:
            re.compile(value)
            return value
        except re.error as exc:
            raise ValueError(
                f"Provided regex value '{value}' for field '{info.field_name}' is invalid."
            ) from exc
    return value


def validate_first_character_is_uppercase(value, info: ValidationInfo):
    """
    Validates whether the first character of a string value is uppercase.

    Args:
        cls: The class to which the field belongs.
        value: The value to validate.
        info: ValidationInfo

    Returns:
        str: The validated value.
    """
    if value and isinstance(value, str) and not value[0].isupper():
        raise ValueError(
            f"Provided value '{value}' for '{info.field_name}' is invalid. The first character must be uppercase."
        )
    return value


def validate_first_character_is_lowercase(value, info: ValidationInfo):
    """
    Validates whether the first character of a string value is lowercase.

    Args:
        cls: The class to which the field belongs.
        value: The value to validate.
        info: ValidationInfo

    Returns:
        str: The validated value.
    """
    if value and isinstance(value, str) and not value[0].islower():
        raise ValueError(
            f"Provided value '{value}' for '{info.field_name}' is invalid. The first character must be lowercase."
        )
    return value


def to_uppercase(value, _info: ValidationInfo):
    """Transforms a string value to uppercase."""
    if value:
        return value.upper()
    return value


def transform_to_utc(value: datetime | None, info: ValidationInfo):
    if not value:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    try:
        return value.astimezone(timezone.utc)
    except OverflowError as exc:
        raise ValueError(
            f"Provided value '{value}' for '{info.field_name}' is invalid. {exc}"
        ) from exc


def reject_non_string_datetime(value: Any, info: ValidationInfo):
    """Reject non-string payloads for date/datetime fields.

    Pydantic's default coercion accepts ints (epoch seconds) and bools for
    date/datetime fields, which schemathesis exploits to find schema
    mismatches. ``Field(strict=True)`` rejects those but also rejects ISO
    strings - the only representation JSON can carry - so it cannot be used.

    This ``mode='before'`` validator keeps ISO strings (and real ``date``/
    ``datetime`` objects) and rejects everything else.
    """
    if value is None or isinstance(value, (str, datetime, date)):
        return value
    raise ValueError(
        f"Provided value for '{info.field_name}' must be an ISO-formatted "
        "date/datetime string."
    )


def is_language_supported(value: str):
    if not value:
        return None

    keys = ["639-3", "639-2/B", "639-2/T", "639-1"]

    for key in keys:
        try:
            # This function will throw an exception if the language isn't found
            get_iso_lang_data(query=value, return_key=key)  # type: ignore[call-overload]
            return value
        except ValidationException:
            if key == keys[-1]:
                raise

    return None


def has_english_description(translated_texts: list[Any]):
    """
    Ensures that there is at least one Translated Text with language English ('eng' or 'en') if Description(s) have been provided.

    Args:
        translated_texts (list[Any]): List of translated_texts.

    Returns:
        list[Any]: The original list if valid.

    Raises:
        ValidationException: If no English Description is found.
    """

    if not translated_texts:
        return []

    descriptions = [
        tt
        for tt in translated_texts
        if tt.text_type == OdmTranslatedTextTypeEnum.DESCRIPTION
    ]
    if not descriptions or any(
        d.language in {ENG_LANGUAGE, EN_LANGUAGE} for d in descriptions
    ):
        return translated_texts

    raise ValidationException(
        msg="A Translated Text with text_type Description and language English ('eng' or 'en') must be provided."
    )


def translated_text_uniqueness_check(translated_texts: list[Any]):
    """
    Ensures that there are no duplicate Translated Texts for the same language and text_type.

    Args:
        translated_texts (list[Any]): List of translated_texts.

    Returns:
        list[Any]: The original list if valid.

    Raises:
        ValidationException: If duplicate Translated Texts are found.
    """
    seen = set()

    for translated_text in translated_texts:
        identifier = (translated_text.text_type, translated_text.language)
        if identifier in seen:
            raise ValidationException(
                msg=f"Duplicate Translated Text found for text_type '{translated_text.text_type.value}' and language '{translated_text.language}'."
            )
        seen.add(identifier)

    return translated_texts
