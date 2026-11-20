import pytest

from common.exceptions import ValidationException
from standards_import.models.inconsistencies import (
    InconsistencyType,
    ResolutionStrategy,
    RuleScope,
)
from standards_import.repositories.rules_repository import SEED_RULES
from standards_import.services.resolution_service import (
    find_matching_rule,
    resolve_value,
    validate_rule,
)


def sponsor_finding(preferred_term, codelist_ids=(), submission_values=()):
    return {
        "uid": "u",
        "type": InconsistencyType.SPONSOR_NAME.value,
        "entity_type": "TERM",
        "concept_id": "C1",
        "property": None,
        "effective_date": "2025-09-26",
        "codelist_ids": list(codelist_ids),
        "submission_values": list(submission_values),
        "candidates": [{"value": preferred_term, "catalogues": []}],
    }


def seeded(uid):
    return dict(
        next(r for r in SEED_RULES if r["uid"] == uid), enabled=True, author_id="seed"
    )


def apply(rule, finding):
    return resolve_value(
        ResolutionStrategy(rule["strategy"]),
        finding,
        value=rule.get("value"),
        pattern=rule.get("pattern"),
        in_codelist_id=rule.get("in_codelist_id"),
        steps=tuple(
            (step["pattern"], step.get("replacement", ""))
            for step in rule.get("steps") or []
        ),
        title_case=bool(rule.get("title_case")),
    )


# --- Trial Phase: roman numerals to digits, trailing " Trial" removed ------------


@pytest.mark.parametrize(
    "preferred_term,expected",
    [
        # what the bootstrap script spells out term by term
        ("Phase I Trial", "Phase 1"),
        ("Phase II Trial", "Phase 2"),
        ("Phase III Trial", "Phase 3"),
        ("Phase IV Trial", "Phase 4"),
        ("Phase I/II Trial", "Phase 1/Phase 2"),
        ("Phase I/III Trial", "Phase 1/Phase 3"),
        ("Phase II/III Trial", "Phase 2/Phase 3"),
        ("Phase I/II/III Trial", "Phase 1/Phase 2/Phase 3"),
        ("Early Phase 1 Trial", "Early Phase 1"),
        ("Not Applicable", "Not Applicable"),
        # the seven the script leaves with their Roman numerals and their " Trial"
        ("Phase Ia Trial", "Phase 1a"),
        ("Phase Ib Trial", "Phase 1b"),
        ("Phase IIa Trial", "Phase 2a"),
        ("Phase IIb Trial", "Phase 2b"),
        ("Phase IIIa Trial", "Phase 3a"),
        ("Phase IIIb Trial", "Phase 3b"),
        ("Phase V Trial", "Phase 5"),
        # the one exception: not a conversion at all
        ("Phase 0 Trial", "Early Phase 1"),
        ("Phase 0", "Early Phase 1"),
    ],
)
def test_the_seeded_phase_rule_renames_every_trial_phase_term(preferred_term, expected):
    """A compound phase repeats the word: `Phase I/II` is written `Phase 1/Phase 2`."""

    assert (
        apply(
            seeded("seed_sponsor_name_C66737_trial_phase"),
            sponsor_finding(preferred_term),
        )
        == expected
    )


def test_iv_is_not_read_as_i_followed_by_v():
    assert (
        resolve_value(ResolutionStrategy.TRIAL_PHASE_NAME, sponsor_finding("Phase IV"))
        == "Phase 4"
    )


def test_the_phase_rule_leaves_words_alone():
    """Only standalone numerals are converted, not letters inside words."""

    assert (
        resolve_value(
            ResolutionStrategy.TRIAL_PHASE_NAME, sponsor_finding("Vital Signs")
        )
        == "Vital Signs"
    )


def test_the_phase_rule_needs_a_single_text_value():
    with pytest.raises(ValidationException, match="only applies to text"):
        resolve_value(ResolutionStrategy.TRIAL_PHASE_NAME, sponsor_finding(["a", "b"]))


# --- Study Type: drop the trailing word -----------------------------------------


@pytest.mark.parametrize(
    "preferred_term,expected",
    [
        ("Patient Registry Study", "Patient Registry"),
        ("Observational Study", "Observational"),
        ("Interventional Study", "Interventional"),
        ("Expanded Access Study", "Expanded Access"),
    ],
)
def test_the_seeded_study_type_rule_drops_the_trailing_word(preferred_term, expected):
    """The four terms CDISC ships in C99077."""

    assert (
        apply(
            seeded("seed_sponsor_name_C99077_drop_study"),
            sponsor_finding(preferred_term),
        )
        == expected
    )


@pytest.mark.parametrize(
    "rule_uid,preferred_term,expected",
    [
        # Epoch: a leading word and three possible trailing ones, in one alternation
        ("seed_sponsor_name_C99079_epoch", "Treatment Epoch", "Treatment"),
        ("seed_sponsor_name_C99079_epoch", "Run-in Period", "Run-in"),
        ("seed_sponsor_name_C99079_epoch", "Screening Study Epoch", "Screening"),
        (
            "seed_sponsor_name_C99079_epoch",
            "Investigational Treatment Epoch",
            "Treatment",
        ),
        # Trial Type takes either trailing word
        ("seed_sponsor_name_C66736_trial_type", "Safety Study", "Safety"),
        ("seed_sponsor_name_C66736_trial_type", "Efficacy Trial", "Efficacy"),
        ("seed_sponsor_name_C66785_control_type", "Placebo Control", "Placebo"),
        (
            "seed_sponsor_name_C66735_blinding_schema",
            "Double Blind Study",
            "Double Blind",
        ),
        ("seed_sponsor_name_C99076_intervention_model", "Crossover Study", "Crossover"),
        # Objective Level strips from the front instead
        (
            "seed_sponsor_name_C188725_objective_level",
            "Trial Primary Objective",
            "Primary Objective",
        ),
    ],
)
def test_the_remaining_codelists_drop_their_boilerplate(
    rule_uid, preferred_term, expected
):
    assert apply(seeded(rule_uid), sponsor_finding(preferred_term)) == expected


def test_every_unit_subset_codelist_has_a_rule():
    """The Unit codelist and its fifteen subsets each need their own rule."""

    from standards_import.repositories.rules_repository import UNIT_CODELIST_IDS

    seeded_units = {
        r["in_codelist_id"]
        for r in SEED_RULES
        if r["uid"].endswith("_unit_submission_value")
    }

    assert len(UNIT_CODELIST_IDS) == 16
    assert seeded_units == set(UNIT_CODELIST_IDS)


def test_dropping_a_trailing_word_leaves_a_term_without_it_alone():
    rule = seeded("seed_sponsor_name_C99077_drop_study")

    assert apply(rule, sponsor_finding("Study Design")) == "Study Design"


# --- Units: name the term after its submission value -----------------------------


def test_use_submission_value_takes_the_one_from_the_named_codelist():
    finding = sponsor_finding(
        "Kilogram",
        codelist_ids=["C71620", "C66770"],
        submission_values=["kg", "KILOGRAM"],
    )

    assert (
        apply(seeded("seed_sponsor_name_C71620_unit_submission_value"), finding) == "kg"
    )


def test_use_submission_value_refuses_when_the_term_is_not_in_that_codelist():
    finding = sponsor_finding(
        "Kilogram", codelist_ids=["C66770"], submission_values=["KILOGRAM"]
    )

    with pytest.raises(ValidationException, match="no submission value in codelist"):
        apply(seeded("seed_sponsor_name_C71620_unit_submission_value"), finding)


def test_use_submission_value_without_a_codelist_needs_them_to_agree():
    """Over half of all terms carry a different submission value per codelist."""

    agreeing = sponsor_finding("Kilogram", ["C1", "C2"], ["kg", "kg"])
    differing = sponsor_finding("Kilogram", ["C1", "C2"], ["kg", "KILOGRAM"])

    assert resolve_value(ResolutionStrategy.USE_SUBMISSION_VALUE, agreeing) == "kg"
    with pytest.raises(ValidationException, match="name the codelist to take it from"):
        resolve_value(ResolutionStrategy.USE_SUBMISSION_VALUE, differing)


def test_use_submission_value_needs_some_to_use():
    with pytest.raises(ValidationException, match="no submission values"):
        resolve_value(ResolutionStrategy.USE_SUBMISSION_VALUE, sponsor_finding("X"))


def test_a_use_submission_value_rule_must_name_a_codelist():
    with pytest.raises(ValidationException, match="needs `in_codelist_id`"):
        validate_rule(
            {
                "scope": RuleScope.GLOBAL.value,
                "strategy": ResolutionStrategy.USE_SUBMISSION_VALUE.value,
            }
        )


# --- scope and matching ----------------------------------------------------------


def test_a_codelist_satisfies_concept_scope():
    """A rule reaching every term of a codelist names one concept: the codelist."""

    validate_rule(
        {
            "scope": RuleScope.CONCEPT.value,
            "strategy": ResolutionStrategy.ACCEPT_AS_IS.value,
            "in_codelist_id": "C66737",
        }
    )


def test_a_concept_rule_still_needs_one_or_the_other():
    with pytest.raises(ValidationException, match="`concept_id` or `in_codelist_id`"):
        validate_rule(
            {
                "scope": RuleScope.CONCEPT.value,
                "strategy": ResolutionStrategy.ACCEPT_AS_IS.value,
            }
        )


def test_the_narrow_naming_rules_beat_the_global_fallback():
    """Seeded rules are matched narrowest first, so the fallback is the last resort."""

    rules = [
        seeded(uid)
        for uid in (
            "seed_sponsor_name_C66737_trial_phase",
            "seed_sponsor_name_C99077_drop_study",
            "seed_sponsor_name_from_preferred_term",
        )
    ]
    phase = sponsor_finding("Phase II Trial", codelist_ids=["C66737"])
    other = sponsor_finding("Adverse Event", codelist_ids=["C99999"])

    matched_phase = find_matching_rule(phase, rules)
    matched_other = find_matching_rule(other, rules)

    assert matched_phase is not None and matched_other is not None
    assert matched_phase["uid"] == "seed_sponsor_name_C66737_trial_phase"
    assert matched_other["uid"] == "seed_sponsor_name_from_preferred_term"


# --- the three families that need ordered steps ----------------------------------


@pytest.mark.parametrize(
    "preferred_term,expected",
    [
        ("Dosage Form for Injection", "For Injection"),
        ("Tablet Dosage Form", "Tablet"),
        ("Dosage Form Tablet", "Tablet"),
        ("Injectable Dosage Form Solution", "Injectable Solution"),
        ("Tablet", "Tablet"),
    ],
)
def test_dosage_form_needs_two_steps_with_different_replacements(
    preferred_term, expected
):
    """A single pattern cannot both rewrite a prefix and delete the phrase elsewhere."""

    assert (
        apply(
            seeded("seed_sponsor_name_C66726_dosage_form"),
            sponsor_finding(preferred_term),
        )
        == expected
    )


@pytest.mark.parametrize(
    "preferred_term,expected",
    [
        ("Two Times Per Day", "Two Times Daily"),
        ("Once Per Month", "Once Monthly"),
        ("Every Night.", "Every Night"),
        ("Every Night", "Every Night"),
    ],
)
def test_frequency_strips_a_stray_stop_then_rewrites(preferred_term, expected):
    assert (
        apply(
            seeded("seed_sponsor_name_C71113_frequency"),
            sponsor_finding(preferred_term),
        )
        == expected
    )


def test_frequency_special_cases_are_term_rules_that_win():
    """Named on the term, so they beat the rule covering the rest of the codelist."""

    rules = [
        seeded(uid)
        for uid in (
            "seed_sponsor_name_C64954_occasional",
            "seed_sponsor_name_C64596_every_day",
            "seed_sponsor_name_C71113_frequency",
        )
    ]
    infrequent = sponsor_finding("Infrequent", codelist_ids=["C71113"])
    infrequent["concept_id"] = "C64954"
    every_evening = sponsor_finding("QPM", codelist_ids=["C71113"])
    every_evening["concept_id"] = "C64596"

    assert apply(find_matching_rule(infrequent, rules), infrequent) == "Occasional"
    assert apply(find_matching_rule(every_evening, rules), every_evening) == "Every Day"


@pytest.mark.parametrize(
    "preferred_term,expected",
    [
        ("Intravenous Route of Administration", "Intravenous"),
        ("Oral-Route of Administration", "Oral"),
        ("Route of Administration Unknown", "Unknown"),
    ],
)
def test_route_of_administration_strips_the_phrase(preferred_term, expected):
    finding = sponsor_finding(preferred_term, codelist_ids=["C66729"])
    rules = [
        seeded("seed_sponsor_name_C66729_route_via"),
        seeded("seed_sponsor_name_C66729_route_strip"),
    ]

    assert apply(find_matching_rule(finding, rules), finding) == expected


def test_administration_via_terms_take_the_submission_value_instead():
    """The `when` guard puts the narrow rule in front of the broad one."""

    finding = sponsor_finding(
        "Administration via Hemodialysis",
        codelist_ids=["C66729"],
        submission_values=["HEMODIALYSIS"],
    )
    rules = [
        seeded("seed_sponsor_name_C66729_route_via"),
        seeded("seed_sponsor_name_C66729_route_strip"),
    ]
    matched = find_matching_rule(finding, rules)

    assert matched is not None and matched["uid"].endswith("_route_via")
    assert apply(matched, finding) == "Hemodialysis"


def test_a_guarded_rule_is_skipped_when_the_value_does_not_match():
    finding = sponsor_finding(
        "Intravenous Route of Administration", codelist_ids=["C66729"]
    )
    matched = find_matching_rule(
        finding, [seeded("seed_sponsor_name_C66729_route_via")]
    )

    assert matched is None


def test_a_rewrite_rule_needs_at_least_one_step():
    with pytest.raises(ValidationException, match="at least one step"):
        validate_rule(
            {
                "scope": RuleScope.GLOBAL.value,
                "strategy": ResolutionStrategy.REWRITE.value,
            }
        )
