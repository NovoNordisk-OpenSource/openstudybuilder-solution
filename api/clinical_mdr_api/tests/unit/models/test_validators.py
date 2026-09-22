"""Unit tests for clinical_mdr_api.models.validators."""

from types import SimpleNamespace

import pytest

from clinical_mdr_api.models.validators import (
    validate_regex,
    validate_string_represents_boolean,
)
from common.exceptions import ValidationException


def _info(field_name: str = "test_field") -> SimpleNamespace:
    return SimpleNamespace(field_name=field_name)


class TestValidateRegex:
    def test_accepts_valid_regex(self):
        assert validate_regex("^[a-z]+$", _info()) == "^[a-z]+$"

    def test_accepts_none_and_empty(self):
        assert validate_regex(None, _info()) is None
        assert validate_regex("", _info()) == ""

    def test_rejects_invalid_regex_with_valueerror(self):
        with pytest.raises(ValueError, match="invalid"):
            validate_regex("[unclosed", _info())

    @pytest.mark.parametrize(
        "non_string",
        [["list"], {"k": "v"}, 42, True],
    )
    def test_rejects_non_string_with_valueerror(self, non_string):
        # Schemathesis-style fuzzing passes lists/dicts/ints as field values;
        # re.compile() used to crash with TypeError, surfacing as a 500.
        with pytest.raises(ValueError, match="Must be a string"):
            validate_regex(non_string, _info())


class TestValidateStringRepresentsBoolean:
    @pytest.mark.parametrize(
        "truthy",
        ["y", "yes", "t", "true", "on", "1", "YES", "True"],
    )
    def test_accepts_truthy(self, truthy):
        assert validate_string_represents_boolean(truthy, _info()) == truthy

    @pytest.mark.parametrize(
        "falsy",
        ["n", "no", "f", "false", "off", "0", "NO", "False"],
    )
    def test_accepts_falsy(self, falsy):
        assert validate_string_represents_boolean(falsy, _info()) == falsy

    def test_none_coerces_to_false(self):
        assert validate_string_represents_boolean(None, _info()) == "false"

    def test_rejects_empty_string(self):
        # ``""`` is a type violation against the BOOLEAN_STRING_PATTERN declared
        # on Input-model fields; it must not silently coerce to "false".
        with pytest.raises(ValidationException, match="Unsupported boolean value"):
            validate_string_represents_boolean("", _info())

    def test_rejects_non_boolean_string(self):
        with pytest.raises(ValidationException, match="Unsupported boolean value"):
            validate_string_represents_boolean("maybe", _info())

    @pytest.mark.parametrize(
        "non_string",
        [["list"], {"k": "v"}, 42],
    )
    def test_rejects_non_string_with_validationexception(self, non_string):
        # Schemathesis-style fuzzing passes lists/dicts/ints as field values;
        # value.lower() used to crash with AttributeError, surfacing as a 500.
        with pytest.raises(ValidationException, match="Must be a string"):
            validate_string_represents_boolean(non_string, _info())
