# pylint: disable=redefined-outer-name
"""How a review decision becomes a standing rule."""

import contextlib

import pytest

from common.exceptions import ValidationException
from standards_import.models.inconsistencies import (
    ResolutionInput,
    ResolutionStrategy,
    RuleScope,
)
from standards_import.repositories import inconsistency_repository, rules_repository
from standards_import.services import inconsistency_service
from standards_import.services.inconsistency_service import rule_from_resolution
from standards_import.services.resolution_service import validate_rule

SUBMISSION_VALUE_FINDING = {
    "uid": "f",
    "effective_date": "2026-03-27",
    "type": "CONFLICTING_SUBMISSION_VALUES",
    "entity_type": "CODELIST",
    "concept_id": "C177908",
    "related_concept_id": "C25564",
    "property": None,
    # Enough for USE_SUBMISSION_VALUE to resolve, so the rule validation is what fails.
    "codelist_ids": ["C177908"],
    "submission_values": ["MAXIMUM"],
    "candidates": [{"value": "MAXIMUM", "catalogues": ["SDTM CT"]}],
}

# A term new to MDR being named. The one kind `USE_SUBMISSION_VALUE` applies to, with
# enough for it to resolve, so that the rule validation is what fails.
NAMING_FINDING = {
    "uid": "2026-03-27_TERM_C25564_SPONSOR_NAME_-_-",
    "effective_date": "2026-03-27",
    "type": "SPONSOR_NAME",
    "entity_type": "TERM",
    "concept_id": "C25564",
    "related_concept_id": None,
    "property": None,
    "codelist_ids": ["C177908"],
    "submission_values": ["MAXIMUM"],
    "candidates": [{"value": "Maximum", "catalogues": []}],
}


@pytest.fixture(autouse=True)
def _a_signed_in_reviewer(monkeypatch):
    """`rule_from_resolution` stamps the author, which needs a request context."""

    class Reviewer:
        def id(self):
            return "someone"

    monkeypatch.setattr(inconsistency_service, "user", Reviewer)


def saved_at(scope):
    return rule_from_resolution(
        SUBMISSION_VALUE_FINDING,
        ResolutionInput(
            strategy=ResolutionStrategy.CUSTOM_VALUE,
            value="MAX",
            save_as_rule=True,
            rule_scope=scope,
        ),
    )


def test_occurrence_scope_pins_the_term_the_finding_is_about():
    """Otherwise the rule would reach every term of the codelist."""

    assert saved_at(RuleScope.OCCURRENCE)["related_concept_id"] == "C25564"


def test_concept_scope_deliberately_does_not_pin_the_term():
    """`CONCEPT` means the whole codelist here, because that is the finding\'s concept."""

    assert saved_at(RuleScope.CONCEPT)["related_concept_id"] is None


def test_the_term_is_part_of_the_uid_so_sibling_rules_do_not_collide():
    assert "C25564" in saved_at(RuleScope.OCCURRENCE)["uid"]


# --- nothing is written when the rule cannot be stored ---------------------------


class _Writes:
    """Records which repository writes were attempted, in order."""

    def __init__(self):
        self.calls = []

    def record_decision(self, _session, uid, status, _decision):
        self.calls.append(("record_decision", uid, status))
        return {**SUBMISSION_VALUE_FINDING, "status": status, "resolution": None}

    def upsert_rule(self, _session, rule):
        self.calls.append(("upsert_rule", rule["uid"]))

    def refresh_open_count(self, _session, _date):
        self.calls.append(("refresh_open_count",))


@pytest.fixture
def writes(monkeypatch):
    recorder = _Writes()
    monkeypatch.setattr(
        inconsistency_service, "staging_session", lambda: contextlib.nullcontext(None)
    )
    monkeypatch.setattr(
        inconsistency_service, "require_finding", lambda *_: SUBMISSION_VALUE_FINDING
    )
    monkeypatch.setattr(
        inconsistency_service, "guard_release_not_imported", lambda *_: None
    )
    monkeypatch.setattr(inconsistency_service, "to_model", lambda record: record)
    monkeypatch.setattr(
        inconsistency_repository, "record_decision", recorder.record_decision
    )
    monkeypatch.setattr(rules_repository, "upsert_rule", recorder.upsert_rule)
    monkeypatch.setattr(
        inconsistency_service, "refresh_open_count", recorder.refresh_open_count
    )
    return recorder


def test_an_unstorable_rule_leaves_the_item_untouched(writes):
    """`PROPERTY` scope on a finding with no property cannot produce a valid rule.

    The decision must not be recorded: each repository call commits on its own, so a
    write here would settle the item, skip the open-count refresh, and still hand the
    caller a 400.
    """

    with pytest.raises(ValidationException, match="needs `property`"):
        inconsistency_service.resolve(
            "f",
            ResolutionInput(
                strategy=ResolutionStrategy.CUSTOM_VALUE,
                value="MAX",
                save_as_rule=True,
                rule_scope=RuleScope.PROPERTY,
            ),
        )

    assert writes.calls == []


def test_use_submission_value_cannot_be_saved_as_a_rule_from_a_review(
    writes, monkeypatch
):
    """A rule using it needs `in_codelist_id`, which `ResolutionInput` cannot set."""

    monkeypatch.setattr(
        inconsistency_service, "require_finding", lambda *_: NAMING_FINDING
    )

    with pytest.raises(ValidationException, match="needs `in_codelist_id`"):
        inconsistency_service.resolve(
            "f",
            ResolutionInput(
                strategy=ResolutionStrategy.USE_SUBMISSION_VALUE,
                save_as_rule=True,
                rule_scope=RuleScope.CONCEPT,
            ),
        )

    assert writes.calls == []


def test_a_valid_rule_is_written_after_the_decision_and_the_count_refreshed(writes):
    inconsistency_service.resolve(
        "f",
        ResolutionInput(
            strategy=ResolutionStrategy.CUSTOM_VALUE,
            value="MAX",
            save_as_rule=True,
            rule_scope=RuleScope.OCCURRENCE,
        ),
    )

    assert [call[0] for call in writes.calls] == [
        "record_decision",
        "upsert_rule",
        "refresh_open_count",
    ]


@pytest.mark.parametrize(
    "strategy",
    [
        option.strategy
        for option in inconsistency_service.get_resolution_options().strategies
        if not option.can_save_as_rule
    ],
    ids=lambda s: s.value.lower(),
)
def test_a_strategy_the_menu_says_cannot_be_saved_as_a_rule_is_refused_when_tried(
    strategy, writes
):
    """`can_save_as_rule` is a promise about `save_as_rule`, and this is what makes it
    one: the rule a resolution would produce from any of these has to fail the same
    validation `resolve()` runs before it writes anything.
    """

    rule = rule_from_resolution(
        SUBMISSION_VALUE_FINDING,
        ResolutionInput(
            strategy=strategy, save_as_rule=True, rule_scope=RuleScope.GLOBAL
        ),
    )

    with pytest.raises(ValidationException):
        validate_rule(rule)

    assert writes.calls == []
