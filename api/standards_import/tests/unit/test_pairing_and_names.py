import pytest

from common.exceptions import ValidationException
from standards_import.models.inconsistencies import (
    InconsistencyType,
    ResolutionStrategy,
    RuleScope,
)
from standards_import.services.resolution_service import (
    resolve_value,
    rule_matches,
    validate_rule,
)


def pairing_finding(*partners):
    return {
        "uid": "u",
        "type": InconsistencyType.CODELIST_PAIRING.value,
        "entity_type": "CODELIST",
        "concept_id": "C1",
        "property": None,
        "effective_date": "2025-09-26",
        "codelist_ids": [],
        "candidates": [{"value": p, "catalogues": []} for p in partners],
    }


def sponsor_finding(preferred_term, codelist_ids=()):
    return {
        "uid": "u",
        "type": InconsistencyType.SPONSOR_NAME.value,
        "entity_type": "TERM",
        "concept_id": "C48262",
        "property": None,
        "effective_date": "2025-09-26",
        "codelist_ids": list(codelist_ids),
        "candidates": [{"value": preferred_term, "catalogues": []}],
    }


def test_accept_as_is_takes_the_only_partner_on_offer():
    assert resolve_value(ResolutionStrategy.ACCEPT_AS_IS, pairing_finding("C2")) == "C2"


def test_accept_as_is_refuses_when_the_pairing_is_ambiguous():
    """Two plausible partners is exactly the case a person should look at."""

    with pytest.raises(ValidationException, match="ambiguous"):
        resolve_value(ResolutionStrategy.ACCEPT_AS_IS, pairing_finding("C2", "C3"))


def test_accept_as_is_refuses_when_there_is_nothing_to_accept():
    with pytest.raises(ValidationException, match="no value to accept"):
        resolve_value(ResolutionStrategy.ACCEPT_AS_IS, pairing_finding())


def test_a_sponsor_name_defaults_to_the_cdisc_preferred_term():
    assert (
        resolve_value(ResolutionStrategy.ACCEPT_AS_IS, sponsor_finding("Adverse Event"))
        == "Adverse Event"
    )


def test_regex_replace_rewrites_the_name():
    """This is what makes the bootstrap's naming transforms expressible as data."""

    resolved = resolve_value(
        ResolutionStrategy.REGEX_REPLACE,
        sponsor_finding("Trial Screening Epoch"),
        value="",
        pattern=r"^Trial | Epoch$",
    )

    assert resolved == "Screening"


def test_regex_replace_needs_a_pattern():
    with pytest.raises(ValidationException, match="needs a pattern"):
        resolve_value(ResolutionStrategy.REGEX_REPLACE, sponsor_finding("X"), value="")


def test_regex_replace_rejects_an_invalid_pattern():
    with pytest.raises(ValidationException, match="not a valid regular expression"):
        resolve_value(
            ResolutionStrategy.REGEX_REPLACE,
            sponsor_finding("X"),
            value="",
            pattern="(unclosed",
        )


def test_regex_replace_caps_the_pattern_length():
    with pytest.raises(ValidationException, match="longer than"):
        resolve_value(
            ResolutionStrategy.REGEX_REPLACE,
            sponsor_finding("X"),
            value="",
            pattern="a" * 500,
        )


def test_a_rule_can_reach_every_term_of_a_codelist():
    """`in_codelist_id` is a membership test, not an equality one."""

    rule = {
        "uid": "r",
        "scope": "CONCEPT",
        "strategy": "ACCEPT_AS_IS",
        "enabled": True,
        "in_codelist_id": "C66736",
        "author_id": "someone",
    }

    assert rule_matches(rule, sponsor_finding("X", ["C66736", "C1"])) is True
    assert rule_matches(rule, sponsor_finding("X", ["C1"])) is False
    assert rule_matches(rule, sponsor_finding("X")) is False


def test_a_regex_rule_needs_its_pattern():
    with pytest.raises(ValidationException, match="needs `pattern`"):
        validate_rule(
            {
                "scope": RuleScope.GLOBAL.value,
                "strategy": ResolutionStrategy.REGEX_REPLACE.value,
                "value": "",
            }
        )
