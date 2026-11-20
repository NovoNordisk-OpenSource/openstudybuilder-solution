from datetime import datetime
from typing import Any

import pytest
from pydantic import ValidationError as PydanticValidationError

from common.exceptions import ValidationException
from standards_import.models.inconsistencies import (
    FROM_NAMING_RULES,
    HELD_IN_MDR,
    InconsistencyStatus,
    InconsistencyType,
    MatchTier,
    ResolutionRuleInput,
    ResolutionStrategy,
    ReviewPass,
    RuleScope,
    is_informational,
    review_pass_of,
)
from standards_import.services import inconsistency_service, resolution_service
from standards_import.services.resolution_service import (
    STRATEGIES_BY_TYPE,
    STRATEGY_INPUTS,
    auto_resolve,
    build_rule_uid,
    candidate_fingerprint,
    decide,
    find_matching_rule,
    preferred_by_catalogue,
    resolve_value,
    rule_matches,
    strategies_for,
    validate_rule,
)

PRIORITY = ["SDTM CT", "ADAM CT", "SEND CT"]


def finding(**overrides):
    base = {
        "uid": "2025-09-26_CODELIST_C1_CONFLICTING_VALUES_definition_-",
        "effective_date": "2025-09-26",
        "type": InconsistencyType.CONFLICTING_VALUES.value,
        "entity_type": "CODELIST",
        "concept_id": "C1",
        "related_concept_id": None,
        "property": "definition",
        "candidates": [
            {"value": "from sdtm", "catalogues": ["SDTM CT 2025-09-26"]},
            {"value": "from adam", "catalogues": ["ADAM CT 2025-09-26"]},
        ],
    }
    base.update(overrides)
    return base


def rule(**overrides):
    base = {
        "uid": "rule_test",
        "scope": RuleScope.GLOBAL.value,
        "strategy": ResolutionStrategy.PREFER_CATALOGUE.value,
        "entity_type": None,
        "concept_id": None,
        "property": None,
        "effective_date": None,
        "inconsistency_type": None,
        "value": None,
        "catalogue": "SDTM CT 2025-09-26",
        "enabled": True,
        "author_id": "someone",
        "note": None,
    }
    base.update(overrides)
    return base


# --- fingerprinting -------------------------------------------------------------


def test_fingerprint_is_stable_regardless_of_candidate_order():
    one = [
        {"value": "a", "catalogues": ["SDTM CT"]},
        {"value": "b", "catalogues": ["ADAM CT"]},
    ]
    two = list(reversed(one))

    assert candidate_fingerprint(one) == candidate_fingerprint(two)


def test_fingerprint_changes_when_a_catalogue_moves_between_values():
    """The values persist but the question is different, so a decision must not stand."""

    before = [
        {"value": "a", "catalogues": ["SDTM CT"]},
        {"value": "b", "catalogues": ["ADAM CT", "SEND CT"]},
    ]
    after = [
        {"value": "a", "catalogues": ["SDTM CT", "ADAM CT"]},
        {"value": "b", "catalogues": ["SEND CT"]},
    ]

    assert candidate_fingerprint(before) != candidate_fingerprint(after)


# --- rule matching --------------------------------------------------------------


def test_a_rule_constrains_only_the_fields_it_sets():
    assert rule_matches(rule(), finding()) is True


def test_a_rule_does_not_match_a_different_concept():
    assert rule_matches(rule(concept_id="C999"), finding()) is False


def test_a_rule_does_not_match_a_different_property():
    assert rule_matches(rule(property="synonyms"), finding()) is False


def test_a_rule_does_not_match_a_different_release():
    assert rule_matches(rule(effective_date="2024-03-29"), finding()) is False


def test_a_rule_matches_on_inconsistency_type():
    quotes = rule(inconsistency_type=InconsistencyType.UNWANTED_QUOTES.value)

    assert rule_matches(quotes, finding()) is False
    assert (
        rule_matches(quotes, finding(type=InconsistencyType.UNWANTED_QUOTES.value))
        is True
    )


def test_a_disabled_rule_never_matches():
    assert rule_matches(rule(enabled=False), finding()) is False


def test_the_first_matching_rule_wins():
    narrow = rule(uid="narrow", concept_id="C1")
    broad = rule(uid="broad")

    matched = find_matching_rule(finding(), [narrow, broad])
    assert matched is not None
    assert matched["uid"] == "narrow"


def test_no_rule_matching_returns_none():
    assert find_matching_rule(finding(), [rule(concept_id="C999")]) is None


# --- strategies -----------------------------------------------------------------


def test_prefer_catalogue_takes_that_catalogues_value():
    assert (
        resolve_value(
            ResolutionStrategy.PREFER_CATALOGUE,
            finding(),
            catalogue="ADAM CT 2025-09-26",
        )
        == "from adam"
    )


def test_prefer_catalogue_rejects_a_catalogue_that_supplied_nothing():
    with pytest.raises(ValidationException, match="supplied no value"):
        resolve_value(
            ResolutionStrategy.PREFER_CATALOGUE,
            finding(),
            catalogue="SEND CT 2025-09-26",
        )


def test_pick_value_must_name_a_competing_value():
    assert (
        resolve_value(ResolutionStrategy.PICK_VALUE, finding(), value="from sdtm")
        == "from sdtm"
    )
    with pytest.raises(ValidationException, match="must name one of the competing"):
        resolve_value(ResolutionStrategy.PICK_VALUE, finding(), value="invented")


def test_custom_value_accepts_a_value_nobody_offered():
    assert (
        resolve_value(ResolutionStrategy.CUSTOM_VALUE, finding(), value="invented")
        == "invented"
    )


def test_union_values_merges_lists_without_duplicates():
    synonyms = finding(
        property="synonyms",
        candidates=[
            {"value": ["A", "B"], "catalogues": ["SDTM CT 2025-09-26"]},
            {"value": ["B", "C"], "catalogues": ["ADAM CT 2025-09-26"]},
        ],
    )

    assert resolve_value(ResolutionStrategy.UNION_VALUES, synonyms) == ["A", "B", "C"]


def test_union_values_rejects_non_list_values():
    with pytest.raises(ValidationException, match="every value is a list"):
        resolve_value(ResolutionStrategy.UNION_VALUES, finding())


def test_strip_quotes_collapses_a_quoted_and_unquoted_pair():
    quoted = finding(
        type=InconsistencyType.UNWANTED_QUOTES.value,
        candidates=[
            {"value": '"same"', "catalogues": ["SDTM CT 2025-09-26"]},
            {"value": "same", "catalogues": ["ADAM CT 2025-09-26"]},
        ],
    )

    assert resolve_value(ResolutionStrategy.STRIP_QUOTES, quoted) == "same"


def test_strip_quotes_refuses_when_it_does_not_settle_the_question():
    with pytest.raises(ValidationException, match="more than one distinct value"):
        resolve_value(ResolutionStrategy.STRIP_QUOTES, finding())


def test_ignore_is_accepted_on_anything():
    """Accepting the data as-is is a meaningful choice for any finding."""

    assert resolve_value(ResolutionStrategy.IGNORE, finding()) is None


def term_sets(**overrides):
    """A membership disagreement: about the codelist as a whole, naming no term."""

    base = {
        "type": InconsistencyType.INCONSISTENT_TERM_SETS.value,
        "concept_id": "C66736",
        "related_concept_id": None,
        "property": None,
        "candidates": [{"value": ["C48262:SCRN"], "catalogues": ["SDTM CT"]}],
    }
    base.update(overrides)
    return finding(**base)


def test_dropping_a_term_resolves_to_the_term_the_finding_names():
    about_a_term = finding(
        type=InconsistencyType.CONFLICTING_SUBMISSION_VALUES.value,
        related_concept_id="C25301",
    )

    assert (
        resolve_value(ResolutionStrategy.DROP_TERM_FROM_CODELIST, about_a_term)
        == "C25301"
    )


def test_a_membership_disagreement_takes_the_term_to_drop_from_the_rule():
    """It names no term of its own, which is why the 2017-09-29 seed supplies one."""

    assert (
        resolve_value(
            ResolutionStrategy.DROP_TERM_FROM_CODELIST, term_sets(), value="C48262"
        )
        == "C48262"
    )


def test_dropping_a_term_needs_one_named_somewhere():
    with pytest.raises(ValidationException, match="neither this finding nor the rule"):
        resolve_value(ResolutionStrategy.DROP_TERM_FROM_CODELIST, term_sets())


def test_a_membership_disagreement_can_be_accepted_as_it_stands():
    assert resolve_value(ResolutionStrategy.IGNORE, term_sets()) is None


# Every strategy except the two a membership disagreement can actually use. Derived
# from the enum rather than listed, so a strategy added later is refused here until
# someone decides it belongs — the previous hand-written list covered four of ten.
REFUSED_ON_TERM_SETS = [
    strategy
    for strategy in ResolutionStrategy
    if strategy not in STRATEGIES_BY_TYPE[InconsistencyType.INCONSISTENT_TERM_SETS]
]

# Arguments that would otherwise satisfy each strategy, so the refusal is the only
# reason it can fail — a missing `pattern` would raise for the wrong reason.
SATISFYING_ARGUMENTS: dict[ResolutionStrategy, dict[str, Any]] = {
    ResolutionStrategy.PREFER_CATALOGUE: {"catalogue": "SDTM CT"},
    ResolutionStrategy.PICK_VALUE: {"value": ["C48262:SCRN"]},
    ResolutionStrategy.CUSTOM_VALUE: {"value": ["anything"]},
    ResolutionStrategy.REGEX_REPLACE: {"pattern": ".*", "value": "x"},
    ResolutionStrategy.REWRITE: {"steps": ((".*", "x"),)},
}


def test_the_refused_set_is_every_strategy_but_two():
    """Guards the derivation above: if this shrinks, the tests below stop covering."""

    assert len(REFUSED_ON_TERM_SETS) == len(ResolutionStrategy) - 2
    assert ResolutionStrategy.IGNORE not in REFUSED_ON_TERM_SETS
    assert ResolutionStrategy.DROP_TERM_FROM_CODELIST not in REFUSED_ON_TERM_SETS


@pytest.mark.parametrize(
    "strategy", REFUSED_ON_TERM_SETS, ids=lambda s: s.value.lower()
)
def test_a_membership_disagreement_refuses_strategies_that_change_nothing(strategy):
    """There is no property to write the chosen value to, so it would go nowhere — and
    the refusal names the two that do apply, so nobody has to try the rest."""

    with pytest.raises(ValidationException, match=r"IGNORE.*DROP_TERM_FROM_CODELIST"):
        resolve_value(strategy, term_sets(), **SATISFYING_ARGUMENTS.get(strategy, {}))


# --- deciding -------------------------------------------------------------------


def test_a_person_deciding_gives_resolved_status():
    status, decision = decide(
        finding(),
        ResolutionStrategy.PREFER_CATALOGUE,
        author_id="someone",
        catalogue="SDTM CT 2025-09-26",
    )

    assert status is InconsistencyStatus.RESOLVED
    assert decision["resolved_value"] == "from sdtm"
    assert decision["author_id"] == "someone"


def test_deciding_automatically_gives_auto_resolved_status():
    status, _ = decide(
        finding(),
        ResolutionStrategy.PREFER_CATALOGUE,
        author_id="a-rule",
        catalogue="SDTM CT 2025-09-26",
        automatic=True,
    )

    assert status is InconsistencyStatus.AUTO_RESOLVED


def test_ignoring_gives_ignored_status_however_it_was_decided():
    status, _ = decide(
        finding(), ResolutionStrategy.IGNORE, author_id="someone", automatic=True
    )

    assert status is InconsistencyStatus.IGNORED


# --- automatic resolution -------------------------------------------------------


def test_catalogue_priority_settles_a_plain_disagreement():
    outcome = auto_resolve(finding(), [], PRIORITY)

    assert outcome is not None
    status, decision = outcome
    assert status is InconsistencyStatus.AUTO_RESOLVED
    assert decision["resolved_value"] == "from sdtm"
    assert decision["rule_uid"] is None


def test_catalogue_priority_matches_on_catalogue_not_release():
    """Catalogue names carry the effective date; the pecking order does not."""

    assert preferred_by_catalogue(finding(), PRIORITY) == "SDTM CT 2025-09-26"


def test_a_rule_beats_the_catalogue_pecking_order():
    outcome = auto_resolve(finding(), [rule(catalogue="ADAM CT 2025-09-26")], PRIORITY)

    assert outcome is not None
    status, decision = outcome
    assert status is InconsistencyStatus.AUTO_RESOLVED
    assert decision["resolved_value"] == "from adam"
    assert decision["rule_uid"] == "rule_test"


def test_quotes_are_left_open_when_no_rule_covers_them():
    """The pecking order settles disagreements, not quoting."""

    quoted = finding(
        type=InconsistencyType.UNWANTED_QUOTES.value,
        candidates=[{"value": '"x"', "catalogues": ["SDTM CT 2025-09-26"]}],
    )

    assert auto_resolve(quoted, [], PRIORITY) is None


def test_term_set_disagreements_are_left_open():
    assert auto_resolve(term_sets(), [], PRIORITY) is None


def test_a_rule_that_cannot_apply_leaves_the_item_open(caplog):
    unusable = rule(catalogue="NOWHERE CT 2025-09-26", inconsistency_type=None)
    quoted = finding(
        type=InconsistencyType.UNWANTED_QUOTES.value,
        candidates=[{"value": '"x"', "catalogues": ["SDTM CT 2025-09-26"]}],
    )

    assert auto_resolve(quoted, [unusable], PRIORITY) is None
    assert "could not be applied" in caplog.text


# --- rule validation ------------------------------------------------------------


@pytest.mark.parametrize(
    "scope,missing",
    [
        (RuleScope.OCCURRENCE, "concept_id"),
        (RuleScope.CONCEPT, "concept_id"),
        (RuleScope.PROPERTY, "property"),
    ],
)
def test_a_scope_must_pin_down_what_it_claims_to(scope, missing):
    with pytest.raises(ValidationException, match=f"needs `{missing}`"):
        validate_rule(rule(scope=scope.value, concept_id=None, property=None))


def test_a_global_rule_needs_no_discriminators():
    validate_rule(rule(scope=RuleScope.GLOBAL.value))


def test_pick_value_rule_needs_a_value():
    with pytest.raises(ValidationException, match="needs `value`"):
        validate_rule(
            rule(
                scope=RuleScope.GLOBAL.value,
                strategy=ResolutionStrategy.PICK_VALUE.value,
            )
        )


@pytest.mark.parametrize("value", ["", []])
def test_value_strategies_reject_an_empty_value(value):
    with pytest.raises(ValidationException, match="needs `value`"):
        validate_rule(rule(strategy=ResolutionStrategy.CUSTOM_VALUE.value, value=value))


@pytest.mark.parametrize(
    "overrides",
    [
        {"when": "(["},
        {"strategy": ResolutionStrategy.REGEX_REPLACE.value, "pattern": "(["},
        {
            "strategy": ResolutionStrategy.REWRITE.value,
            "steps": [{"pattern": "([", "replacement": ""}],
        },
        {"when": "a" * 201},
    ],
)
def test_rule_rejects_an_invalid_or_overlong_regex(overrides):
    with pytest.raises(ValidationException, match=r"regular expression|longer than"):
        validate_rule(rule(**overrides))


@pytest.mark.parametrize(
    "fields",
    [
        {"priority": -1},
        {"priority": 10**30},
        {"priority": False},
        {"title_case": 1},
        {"effective_date": 0},
        {"effective_date": "0"},
        {"concept_id": "x" * 256},
        {"steps": [{"pattern": ""}]},
    ],
)
def test_rule_input_rejects_malformed_fields(fields):
    with pytest.raises(PydanticValidationError):
        ResolutionRuleInput(
            scope=RuleScope.GLOBAL, strategy=ResolutionStrategy.IGNORE, **fields
        )


def test_prefer_catalogue_rule_needs_a_catalogue():
    with pytest.raises(ValidationException, match="needs `catalogue`"):
        validate_rule(rule(scope=RuleScope.GLOBAL.value, catalogue=None))


def test_rule_uid_is_composed_from_what_the_rule_discriminates_on():
    first = build_rule_uid(rule(scope="CONCEPT", concept_id="C1"))
    same = build_rule_uid(rule(scope="CONCEPT", concept_id="C1"))
    other = build_rule_uid(rule(scope="CONCEPT", concept_id="C2"))

    assert first == same
    assert first != other


# --- quoted lists ---------------------------------------------------------------


def quoted_synonyms(**overrides):
    """A quoted block of synonyms, which `is_quoted` detects by design."""

    base = {
        "type": InconsistencyType.UNWANTED_QUOTES.value,
        "property": "synonyms",
        "candidates": [
            {
                "value": ['"Alpha', "Beta", 'Gamma"'],
                "catalogues": ["SEND CT 2018-12-21"],
            }
        ],
    }
    base.update(overrides)
    return finding(**base)


def test_strip_quotes_handles_a_quoted_list():
    """Synonyms are lists, and a list cannot be a set element."""

    assert resolve_value(ResolutionStrategy.STRIP_QUOTES, quoted_synonyms()) == [
        "Alpha",
        "Beta",
        "Gamma",
    ]


def test_strip_quotes_collapses_two_lists_that_differ_only_by_quoting():
    both = quoted_synonyms(
        candidates=[
            {"value": ['"A', 'B"'], "catalogues": ["SEND CT 2018-12-21"]},
            {"value": ["A", "B"], "catalogues": ["SDTM CT 2018-12-21"]},
        ]
    )

    assert resolve_value(ResolutionStrategy.STRIP_QUOTES, both) == ["A", "B"]


def test_strip_quotes_still_refuses_lists_that_stay_different():
    different = quoted_synonyms(
        candidates=[
            {"value": ['"A', 'B"'], "catalogues": ["SEND CT 2018-12-21"]},
            {"value": ["A", "C"], "catalogues": ["SDTM CT 2018-12-21"]},
        ]
    )

    with pytest.raises(ValidationException, match="more than one distinct value"):
        resolve_value(ResolutionStrategy.STRIP_QUOTES, different)


def test_strip_quotes_survives_candidates_of_mixed_shape():
    """A text value against a list one: they differ, but comparing must not blow up.

    Stripping returns a list for a list, and a list cannot be a set element — the
    crash this guards was a `TypeError` escaping as a 500, not a refusal.
    """

    mixed = quoted_synonyms(
        candidates=[
            {"value": '"Alpha"', "catalogues": ["SDTM CT"]},
            {"value": ["Alpha"], "catalogues": ["ADAM CT"]},
        ]
    )

    with pytest.raises(ValidationException, match="more than one distinct value"):
        resolve_value(ResolutionStrategy.STRIP_QUOTES, mixed)


def test_strip_quotes_handles_a_list_of_things_that_are_not_strings():
    """Synonym lists are text in practice, but nothing enforces that here."""

    odd = quoted_synonyms(
        candidates=[{"value": [1, None, "x"], "catalogues": ["SDTM CT"]}]
    )

    assert resolve_value(ResolutionStrategy.STRIP_QUOTES, odd) == [1, None, "x"]


def test_strip_quotes_on_a_finding_with_no_candidates_yields_nothing():
    assert (
        resolve_value(ResolutionStrategy.STRIP_QUOTES, quoted_synonyms(candidates=[]))
        is None
    )


def test_the_seeded_quote_rule_settles_a_quoted_synonym_list():
    """`seed_send-ct-2018-12-21_strip_quotes` is GLOBAL and matches this finding."""

    seed = rule(
        uid="seed_send-ct-2018-12-21_strip_quotes",
        strategy=ResolutionStrategy.STRIP_QUOTES.value,
        catalogue=None,
        effective_date="2018-12-21",
        inconsistency_type=InconsistencyType.UNWANTED_QUOTES.value,
    )
    outcome = auto_resolve(
        quoted_synonyms(effective_date="2018-12-21"), [seed], PRIORITY
    )

    assert outcome is not None
    status, decision = outcome
    assert status is InconsistencyStatus.AUTO_RESOLVED
    assert decision["resolved_value"] == ["Alpha", "Beta", "Gamma"]


def test_an_unexpected_failure_leaves_the_item_open_instead_of_ending_the_run(
    monkeypatch, caplog
):
    """Analysis walks tens of thousands of findings; one bad one must not kill it."""

    def explode(_request):
        raise TypeError("unhashable type: 'list'")

    monkeypatch.setitem(
        resolution_service.STRATEGY_HANDLERS,
        ResolutionStrategy.STRIP_QUOTES,
        explode,
    )
    quotes_rule = rule(
        strategy=ResolutionStrategy.STRIP_QUOTES.value,
        catalogue=None,
        inconsistency_type=InconsistencyType.UNWANTED_QUOTES.value,
    )

    # Quoting has no pecking-order fallback, so the item is simply left open.
    assert auto_resolve(quoted_synonyms(), [quotes_rule], PRIORITY) is None
    assert "failed unexpectedly" in caplog.text


# --- targeting one term ---------------------------------------------------------


def submission_value_finding(term="C25564"):
    """A submission value belongs to the membership, so the codelist is the concept."""

    return finding(
        type=InconsistencyType.CONFLICTING_SUBMISSION_VALUES.value,
        entity_type="CODELIST",
        concept_id="C177908",
        related_concept_id=term,
        property=None,
        candidates=[
            {"value": "MAXIMUM", "catalogues": ["SDTM CT"]},
            {"value": "DIFFERENT_SV", "catalogues": ["SEND CT"]},
        ],
    )


def test_a_rule_can_name_the_term_where_the_term_is_not_the_concept():
    one_term = rule(
        concept_id="C177908",
        related_concept_id="C25564",
        strategy=ResolutionStrategy.CUSTOM_VALUE.value,
        value="MAX",
        catalogue=None,
    )

    assert rule_matches(one_term, submission_value_finding("C25564")) is True
    assert rule_matches(one_term, submission_value_finding("C28007")) is False


def test_a_rule_naming_no_term_still_reaches_every_term_of_the_codelist():
    """The discriminator constrains only when set, as all the others do."""

    codelist_wide = rule(concept_id="C177908", catalogue="SDTM CT")

    assert rule_matches(codelist_wide, submission_value_finding("C25564")) is True
    assert rule_matches(codelist_wide, submission_value_finding("C28007")) is True


def test_the_term_makes_two_otherwise_identical_rules_distinct():
    """Otherwise one would overwrite the other on upsert."""

    maximum = build_rule_uid(rule(concept_id="C177908", related_concept_id="C25564"))
    median = build_rule_uid(rule(concept_id="C177908", related_concept_id="C28007"))
    whole = build_rule_uid(rule(concept_id="C177908"))

    assert len({maximum, median, whole}) == 3


def test_a_targeted_rule_leaves_the_other_terms_open():
    """The point of the discriminator: no silent collateral on a sibling term."""

    targeted = rule(
        concept_id="C177908",
        related_concept_id="C25564",
        strategy=ResolutionStrategy.CUSTOM_VALUE.value,
        value="MAX",
        catalogue=None,
    )

    settled = auto_resolve(submission_value_finding("C25564"), [targeted], PRIORITY)
    assert settled is not None and settled[1]["resolved_value"] == "MAX"

    # A submission-value disagreement has no catalogue-priority fallback.
    assert (
        auto_resolve(submission_value_finding("C28007"), [targeted], PRIORITY) is None
    )


# --- the `when` guard -----------------------------------------------------------


def guarded(pattern):
    return rule(when=pattern, catalogue="SDTM CT 2025-09-26")


def test_a_guard_matches_a_single_value_finding():
    """The shape every seeded guard was written against."""

    one = finding(
        candidates=[{"value": "Administration via Stoma", "catalogues": ["SDTM CT"]}]
    )

    assert rule_matches(guarded("^Administration via"), one) is True
    assert rule_matches(guarded("^Nothing like it"), one) is False


def test_a_guard_matches_on_any_competing_value_not_just_the_first():
    """Testing whichever value happened to be listed first is arbitrary."""

    second_one_matches = finding(
        candidates=[
            {"value": "Buccal Route of Administration", "catalogues": ["SDTM CT"]},
            {"value": "Administration via Stoma", "catalogues": ["ADAM CT"]},
        ]
    )

    assert rule_matches(guarded("^Administration via"), second_one_matches) is True


def test_a_guard_ignores_values_that_are_not_text():
    """Synonym lists cannot be pattern-matched; they simply do not match."""

    synonyms = finding(candidates=[{"value": ["A", "B"], "catalogues": ["SDTM CT"]}])

    assert rule_matches(guarded("A"), synonyms) is False


# --- sponsor impact ---------------------------------------------------------------


def collision(**overrides):
    """A SPONSOR_TERM_DUPLICATE finding: one CDISC term, one sponsor term it lands on."""

    base = {
        "uid": "2026-03-27_CODELIST_C1_SPONSOR_TERM_DUPLICATE_-_T2",
        "effective_date": "2026-03-27",
        "type": InconsistencyType.SPONSOR_TERM_DUPLICATE.value,
        "entity_type": "CODELIST",
        "concept_id": "C1",
        "related_concept_id": "T2",
        "property": None,
        "match_tier": "EXACT",
        "candidates": [
            {
                "value": "EXACT:CTTerm_000042:sponsor name 'Severe' matches",
                "catalogues": [],
            }
        ],
    }
    base.update(overrides)
    return base


def diverged(**overrides):
    base = {
        "uid": "2026-03-27_TERM_T1_SPONSOR_NAME_DIVERGED_-_-",
        "effective_date": "2026-03-27",
        "type": InconsistencyType.SPONSOR_NAME_DIVERGED.value,
        "entity_type": "TERM",
        "concept_id": "T1",
        "related_concept_id": None,
        "property": None,
        "match_tier": None,
        "candidates": [
            {"value": "Held Locally", "catalogues": [], "source": HELD_IN_MDR},
            {
                "value": "What CDISC Says Now",
                "catalogues": ["SDTM CT 2026-03-27"],
                "source": FROM_NAMING_RULES,
            },
        ],
    }
    base.update(overrides)
    return base


def test_retiring_a_sponsor_term_resolves_to_the_one_the_finding_names():
    assert (
        resolve_value(ResolutionStrategy.RETIRE_SPONSOR_TERM, collision())
        == "CTTerm_000042"
    )


def test_a_collision_with_several_sponsor_terms_will_not_guess():
    """Retiring the wrong one is not a thing to do quietly."""

    two = collision(
        candidates=[
            {"value": "EXACT:CTTerm_1:matches", "catalogues": []},
            {"value": "EXACT:CTTerm_2:matches", "catalogues": []},
        ]
    )

    with pytest.raises(ValidationException, match="more than one sponsor term"):
        resolve_value(ResolutionStrategy.RETIRE_SPONSOR_TERM, two)

    assert (
        resolve_value(ResolutionStrategy.RETIRE_SPONSOR_TERM, two, value="CTTerm_2")
        == "CTTerm_2"
    )


def test_naming_a_sponsor_term_the_finding_does_not_collide_with_is_refused():
    with pytest.raises(ValidationException, match="not one of the sponsor terms"):
        resolve_value(
            ResolutionStrategy.RETIRE_SPONSOR_TERM, collision(), value="CTTerm_999"
        )


def test_adopting_the_cdisc_name_takes_the_one_from_the_rules_not_the_held_one():
    """Taking the held name would be IGNORE — except that it would also write a new name
    version saying nothing had changed."""

    assert (
        resolve_value(ResolutionStrategy.ADOPT_CDISC_NAME, diverged())
        == "What CDISC Says Now"
    )


def test_adopting_reads_the_label_not_the_position():
    """Which candidate is which is said in `source`, and a strategy that counted
    positions instead would rename a term to the name it already has the moment the
    order changed."""

    reversed_order = diverged(candidates=list(reversed(diverged()["candidates"])))

    assert (
        resolve_value(ResolutionStrategy.ADOPT_CDISC_NAME, reversed_order)
        == "What CDISC Says Now"
    )


def test_a_finding_from_before_candidates_had_a_source_is_read_by_position():
    """Held first, proposed second, was the whole contract once."""

    unlabelled = diverged(
        candidates=[
            {"value": "Held Locally", "catalogues": []},
            {"value": "What CDISC Says Now", "catalogues": []},
        ]
    )

    assert (
        resolve_value(ResolutionStrategy.ADOPT_CDISC_NAME, unlabelled)
        == "What CDISC Says Now"
    )


def test_a_value_producing_strategy_is_refused_on_a_collision():
    """There is nowhere to write it: the disagreement is with the MDR database, not
    between two catalogues."""

    with pytest.raises(ValidationException, match="does not apply"):
        resolve_value(ResolutionStrategy.CUSTOM_VALUE, collision(), value="anything")


def test_retiring_is_refused_on_a_codelist_duplicate():
    """The API has no way to retire a codelist at all, so offering it here would be a
    promise this app cannot keep."""

    codelist_finding = collision(
        type=InconsistencyType.SPONSOR_CODELIST_DUPLICATE.value,
        related_concept_id=None,
    )

    with pytest.raises(ValidationException, match="does not apply"):
        resolve_value(ResolutionStrategy.RETIRE_SPONSOR_TERM, codelist_finding)


@pytest.mark.parametrize("tier", ["CASE_INSENSITIVE", "NORMALIZED"])
def test_a_looser_collision_can_be_acknowledged(tier):
    assert (
        resolve_value(ResolutionStrategy.ACKNOWLEDGE, collision(match_tier=tier))
        is None
    )


def test_an_exact_collision_cannot_be_acknowledged():
    """It is OPEN and blocks import; ACKNOWLEDGE produces no value, so it would wave a
    broken uniqueness rule through."""

    with pytest.raises(ValidationException, match="does not apply"):
        resolve_value(ResolutionStrategy.ACKNOWLEDGE, collision(match_tier="EXACT"))
    with pytest.raises(ValidationException, match="does not apply"):
        resolve_value(ResolutionStrategy.ACKNOWLEDGE, collision(match_tier=None))


def test_an_exact_collision_keeps_every_other_strategy():
    for strategy in (
        ResolutionStrategy.REMOVE_SPONSOR_FROM_CODELIST,
        ResolutionStrategy.RETIRE_SPONSOR_TERM,
    ):
        assert strategy in strategies_for(
            InconsistencyType.SPONSOR_TERM_DUPLICATE, "EXACT"
        )


def test_acknowledging_is_unaffected_for_tier_independent_kinds():
    assert resolve_value(ResolutionStrategy.ACKNOWLEDGE, diverged()) is None
    for kind in InconsistencyType:
        if kind is InconsistencyType.SPONSOR_TERM_DUPLICATE:
            continue
        assert strategies_for(kind, "EXACT") == STRATEGIES_BY_TYPE[kind]


def test_the_served_menu_narrows_by_tier():
    options = inconsistency_service.get_resolution_options()
    kind = InconsistencyType.SPONSOR_TERM_DUPLICATE

    assert ResolutionStrategy.ACKNOWLEDGE not in options.by_type[kind]
    assert (
        ResolutionStrategy.ACKNOWLEDGE
        not in options.by_type_and_tier[kind][MatchTier.EXACT]
    )
    assert (
        ResolutionStrategy.ACKNOWLEDGE
        in options.by_type_and_tier[kind][MatchTier.NORMALIZED]
    )
    assert set(options.by_type_and_tier) == {kind}


def test_a_served_candidate_names_the_sponsor_term_it_collides_with():
    """So a reviewer picks the term to displace instead of typing its uid; a plain value
    from any other kind of finding names none."""

    served = inconsistency_service.to_model(
        collision(status="OPEN", detected_at=datetime(2026, 3, 27))
    )
    plain = inconsistency_service.to_model(
        finding(status="OPEN", detected_at=datetime(2026, 3, 27))
    )

    assert [c.sponsor_term_uid for c in served.candidates] == ["CTTerm_000042"]
    assert [c.sponsor_term_uid for c in plain.candidates] == [None, None]


@pytest.mark.parametrize(
    "strategy",
    [
        ResolutionStrategy.RETIRE_SPONSOR_TERM,
        ResolutionStrategy.REMOVE_SPONSOR_FROM_CODELIST,
        ResolutionStrategy.ADOPT_CDISC_NAME,
    ],
)
def test_a_strategy_that_changes_mdr_can_never_become_a_standing_rule(strategy):
    """A rule doing this would retire sponsor content unattended, quarter after quarter.
    These are decisions about one finding, not conventions."""

    with pytest.raises(ValidationException, match="never stands for every release"):
        validate_rule({"scope": RuleScope.GLOBAL.value, "strategy": strategy.value})


# --- the one table ------------------------------------------------------------------


def test_every_kind_of_finding_has_a_menu_and_can_always_be_accepted():
    """A kind added to the enum and left out of the table would refuse every strategy,
    and one that cannot be settled at all would hold a release forever.

    `ACKNOWLEDGE` is the other universal "accept it as-is" strategy, alongside `IGNORE`
    — the two CDISC-usage kinds take it instead, because settling a live reference is
    not the same thing as waving through a disagreement."""

    for kind in InconsistencyType:
        assert kind in STRATEGIES_BY_TYPE, f"{kind.value} has no strategies"
        menu = STRATEGIES_BY_TYPE[kind]
        assert (
            ResolutionStrategy.IGNORE in menu or ResolutionStrategy.ACKNOWLEDGE in menu
        ), kind.value


def test_every_strategy_settles_something():
    """A strategy nothing admits is dead code with an endpoint."""

    admitted = {strategy for menu in STRATEGIES_BY_TYPE.values() for strategy in menu}

    assert admitted == set(ResolutionStrategy)


@pytest.mark.parametrize(
    "kind,expected",
    [
        (InconsistencyType.CONFLICTING_VALUES, ReviewPass.ANALYSIS),
        (InconsistencyType.UNWANTED_QUOTES, ReviewPass.ANALYSIS),
        (InconsistencyType.INCONSISTENT_TERM_SETS, ReviewPass.ANALYSIS),
        (InconsistencyType.CONFLICTING_SUBMISSION_VALUES, ReviewPass.ANALYSIS),
        (InconsistencyType.CODELIST_PAIRING, ReviewPass.ANALYSIS),
        (InconsistencyType.SPONSOR_NAME, ReviewPass.ANALYSIS),
        (InconsistencyType.SPONSOR_TERM_DUPLICATE, ReviewPass.SPONSOR_IMPACT),
        (InconsistencyType.SPONSOR_TERM_SEMANTIC_DUPLICATE, ReviewPass.SPONSOR_IMPACT),
        (InconsistencyType.SPONSOR_CODELIST_DUPLICATE, ReviewPass.SPONSOR_IMPACT),
        (InconsistencyType.SPONSOR_NAME_DIVERGED, ReviewPass.SPONSOR_IMPACT),
        (
            InconsistencyType.CDISC_TERM_SUBMISSION_VALUE_CHANGED,
            ReviewPass.SPONSOR_IMPACT,
        ),
        (InconsistencyType.CDISC_TERM_REMOVED_FROM_CODELIST, ReviewPass.SPONSOR_IMPACT),
    ],
)
def test_review_pass_of_matches_which_pass_actually_raises_the_kind(kind, expected):
    """This is the fact a frontend needs to split its queue in two before fetching
    anything — it has to agree with `ANALYSIS_TYPES`/`SPONSOR_IMPACT_TYPES`, which is
    what `prune_findings`/`get_undecided` actually key on."""

    assert review_pass_of(kind) is expected


def test_review_pass_of_covers_every_kind():
    """A kind added to the enum and left out of either frozenset would silently answer
    ANALYSIS for it — this is the same "nothing left out" guarantee `ANALYSIS_TYPES`
    itself is built to provide, checked from the other side."""

    for kind in InconsistencyType:
        assert review_pass_of(kind) in (ReviewPass.ANALYSIS, ReviewPass.SPONSOR_IMPACT)


def test_get_resolution_options_reports_raised_by_for_every_kind():
    options = inconsistency_service.get_resolution_options()

    assert set(options.raised_by) == set(InconsistencyType)
    assert options.raised_by[InconsistencyType.SPONSOR_NAME] == ReviewPass.ANALYSIS
    assert (
        options.raised_by[InconsistencyType.SPONSOR_TERM_DUPLICATE]
        == ReviewPass.SPONSOR_IMPACT
    )


@pytest.mark.parametrize(
    "strategy,missing",
    [
        (strategy, field)
        for strategy, fields in STRATEGY_INPUTS.items()
        for field in fields
    ],
)
def test_what_a_strategy_says_it_needs_is_what_a_rule_is_refused_without(
    strategy, missing
):
    """The inputs served to a client and the ones `validate_rule` insists on are two
    statements of one fact, and this is what keeps them the same statement."""

    complete = {
        "scope": RuleScope.GLOBAL.value,
        "strategy": strategy.value,
        "value": "x",
        "catalogue": "SDTM CT",
        "pattern": ".*",
        "steps": [{"pattern": ".*", "replacement": ""}],
    }
    validate_rule(dict(complete))

    del complete[missing]
    with pytest.raises(ValidationException):
        validate_rule(complete)


def test_a_strategy_outside_the_menu_is_refused_by_the_type_alone():
    """Before any handler runs, so the message names the whole menu rather than one
    precondition that happened to fail first."""

    with pytest.raises(
        ValidationException, match="does not apply to a CODELIST_PAIRING"
    ):
        resolve_value(
            ResolutionStrategy.UNION_VALUES,
            finding(type=InconsistencyType.CODELIST_PAIRING.value),
        )


@pytest.mark.parametrize(
    "kind,tier,expected",
    [
        (InconsistencyType.SPONSOR_TERM_DUPLICATE, "EXACT", False),
        (InconsistencyType.SPONSOR_TERM_DUPLICATE, None, False),
        (InconsistencyType.SPONSOR_TERM_DUPLICATE, "CASE_INSENSITIVE", True),
        (InconsistencyType.SPONSOR_TERM_DUPLICATE, "NORMALIZED", True),
        (InconsistencyType.SPONSOR_TERM_SEMANTIC_DUPLICATE, None, True),
        (InconsistencyType.SPONSOR_CODELIST_DUPLICATE, "EXACT", True),
        (InconsistencyType.SPONSOR_NAME_DIVERGED, None, True),
        (InconsistencyType.CONFLICTING_VALUES, None, False),
    ],
)
def test_is_informational(kind, tier, expected):
    assert is_informational(kind.value, tier) is expected
