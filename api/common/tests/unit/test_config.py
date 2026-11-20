import pytest
from pydantic import ValidationError

from common.config import Settings

ENV_VAR = "STUDIES_STUDY_NUMBER_REGEX"


def load_settings(monkeypatch, value: str | None) -> Settings:
    # _env_file=None keeps a developer's api/.env from leaking into the result,
    # so the one required setting it would supply is set here instead.
    monkeypatch.setenv("NEO4J_DSN", "bolt://neo4j:password@localhost:7687/neo4j")
    if value is None:
        monkeypatch.delenv(ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(ENV_VAR, value)
    # Same ignore as `settings = Settings()` in common/config.py: the pydantic
    # mypy plugin knows neither env-supplied fields nor the _env_file kwarg.
    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.mark.parametrize("value", [None, "", "   "])
def test_studies_study_number_regex_default(monkeypatch, value):
    setting = load_settings(monkeypatch, value).studies_study_number_regex

    assert setting == {
        "regex": r"^\d{1,4}$",
        "message": "Study number must be a string of up to 4 digits.",
    }


def test_studies_study_number_regex_custom(monkeypatch):
    setting = load_settings(
        monkeypatch, r'{"regex": "[A-Z]{2}-\\d{3}", "message": "Use AB-123."}'
    ).studies_study_number_regex

    assert setting == {"regex": r"[A-Z]{2}-\d{3}", "message": "Use AB-123."}


@pytest.mark.parametrize(
    "value", [r'{"regex": "\\d+"}', r'{"regex": "\\d+", "message": ""}']
)
def test_studies_study_number_regex_message_defaults(monkeypatch, value):
    setting = load_settings(monkeypatch, value).studies_study_number_regex

    assert setting == {
        "regex": r"\d+",
        "message": r"Study number must match regex '\d+'.",
    }


def test_studies_study_number_regex_drops_unknown_keys(monkeypatch):
    setting = load_settings(
        monkeypatch, r'{"regex": "\\d+", "message": "Digits.", "extra": 1}'
    ).studies_study_number_regex

    assert setting == {"regex": r"\d+", "message": "Digits."}


@pytest.mark.parametrize(
    ("value", "error"),
    [
        ('"abc"', "must be a JSON object with a 'regex' key"),
        ("[]", "must be a JSON object with a 'regex' key"),
        ('{"message": "Digits."}', "'regex' must be a non-empty string"),
        ('{"regex": ""}', "'regex' must be a non-empty string"),
        ('{"regex": 5}', "'regex' must be a non-empty string"),
        ('{"regex": "("}', "Invalid regex pattern"),
        (r'{"regex": "\\d+", "message": 5}', "'message' must be a string"),
    ],
)
def test_studies_study_number_regex_invalid(monkeypatch, value, error):
    with pytest.raises(ValidationError) as exc_info:
        load_settings(monkeypatch, value)

    assert error in str(exc_info.value)
