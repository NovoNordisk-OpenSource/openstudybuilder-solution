import pytest

from standards_import.models.inconsistencies import MatchTier
from standards_import.services.sponsor_matching import (
    build_index,
    describe_match,
    find_matches,
    match_tier,
    normalize_key,
    sponsor_uid_from_candidate,
    strongest_tier,
)


def sponsor(uid, name=None, submission_value=None):
    return {"uid": uid, "name": name, "submission_value": submission_value}


def matches_for(entities, **cdisc_values):
    return find_matches(build_index(entities), **cdisc_values)


# --- normalization --------------------------------------------------------------


def test_the_same_concept_typed_three_ways_normalizes_to_one_key():
    assert (
        normalize_key("AE Severity")
        == normalize_key("ae_severity")
        == normalize_key("AESEVERITY")
    )


def test_an_accented_letter_survives_normalization():
    """`[^a-z0-9]` would truncate `Café` to `caf` and match it against `Caffeine`."""

    assert normalize_key("Café") == normalize_key("CAFÉ")
    assert normalize_key("Café") != normalize_key("Caf")


def test_a_value_with_nothing_alphanumeric_in_it_yields_no_key():
    assert normalize_key("---") == ""
    assert normalize_key(None) == ""


# --- tiers ----------------------------------------------------------------------


def test_identical_values_are_an_exact_match():
    assert match_tier("SEVERE", "SEVERE") is MatchTier.EXACT


def test_values_differing_only_in_case_are_not_exact():
    """`SEV` and `sev` are distinct submission values; calling that exact would report a
    broken invariant where none is broken."""

    assert match_tier("SEV", "sev") is MatchTier.CASE_INSENSITIVE


def test_values_differing_in_punctuation_are_normalized_matches():
    assert match_tier("AE Severity", "ae_severity") is MatchTier.NORMALIZED


# --- finding matches ------------------------------------------------------------


def test_a_concept_nobody_shares_a_value_with_matches_nothing():
    assert matches_for([sponsor("S1", "Mild", "MILD")], name="Severe") == []


def test_a_shared_name_is_a_match_naming_both_sides():
    found = matches_for([sponsor("S1", "Severe", "SEV")], name="Severe")

    assert len(found) == 1
    assert found[0]["sponsor_uid"] == "S1"
    assert found[0]["field"] == "name"
    assert found[0]["sponsor_field"] == "name"
    assert found[0]["tier"] is MatchTier.EXACT


def test_a_shared_submission_value_is_a_match_on_its_own():
    """Colliding on the submission value alone is as much of a problem as on the name."""

    found = matches_for(
        [sponsor("S1", "Mild", "SEV")], name="Severe", submission_value="SEV"
    )

    assert len(found) == 1
    assert found[0]["field"] == "submission_value"
    assert found[0]["sponsor_field"] == "submission_value"


def test_one_sponsor_value_hit_by_both_cdisc_fields_is_reported_once():
    """The name and the submission value both land on the sponsor's *name*. That is one
    problem, and reporting it twice trains a reviewer to stop reading the column."""

    found = matches_for(
        [sponsor("S1", "SEV", "SOMETHING-ELSE")], name="SEV", submission_value="SEV"
    )

    assert len(found) == 1
    assert found[0]["sponsor_field"] == "name"


def test_two_sponsor_values_hit_separately_are_two_matches():
    """Same sponsor term, but its name and its submission value are each taken. Unlike
    the case above these are two distinct facts, and collapsing them would hide one."""

    found = matches_for(
        [sponsor("S1", "Severe", "SEV")], name="Severe", submission_value="SEV"
    )

    assert [match["sponsor_field"] for match in found] == ["name", "submission_value"]


def test_the_pairing_that_reads_best_wins_a_tie():
    """Both CDISC fields land on the same sponsor field equally well, and the pairing
    whose field names agree is the one worth showing. Checked in both arrival orders: a
    comparison that never replaces what it is already holding looks right until the
    better pairing happens to come second."""

    reached_by_name = matches_for(
        [sponsor("S1", "AESEV", "OTHER")], name="AESEV", submission_value="AESEV"
    )
    assert [match["field"] for match in reached_by_name] == ["name"]
    assert reached_by_name[0]["sponsor_field"] == "name"

    reached_by_submission_value = matches_for(
        [sponsor("S1", "OTHER", "AESEV")], name="AESEV", submission_value="AESEV"
    )
    assert [match["field"] for match in reached_by_submission_value] == [
        "submission_value"
    ]
    assert reached_by_submission_value[0]["sponsor_field"] == "submission_value"


def test_a_stronger_tier_beats_the_better_reading_pairing():
    """An exact hit says an invariant breaks. That has to survive, even when the tidier
    same-named pairing is only a case-insensitive one."""

    found = matches_for(
        [sponsor("S1", "AESEV", "OTHER")], name="aesev", submission_value="AESEV"
    )

    assert found[0]["tier"] is MatchTier.EXACT
    assert found[0]["field"] == "submission_value"


def test_exact_matches_are_listed_before_near_ones():
    """A long tail of cosmetic near-matches must never bury the one hit that blocks."""

    found = matches_for(
        [sponsor("S1", "ae_severity"), sponsor("S2", "AESEV")],
        name="AESEV",
        submission_value="AESEVERITY",
    )

    assert [match["tier"] for match in found] == [
        MatchTier.EXACT,
        MatchTier.NORMALIZED,
    ]


def test_values_with_no_alphanumeric_content_never_match_each_other():
    """An empty normalized key would otherwise bucket every punctuation-only value
    together and report them all as colliding."""

    assert matches_for([sponsor("S1", "---")], name="???") == []


def test_a_sponsor_entity_with_neither_field_set_is_not_indexed():
    assert matches_for([sponsor("S1")], name="Severe", submission_value="SEV") == []


def test_the_same_inputs_always_produce_the_same_order():
    """Findings are fingerprinted over what they carry, so an order that drifted between
    runs would discard a decision and reopen the item for no reason."""

    entities = [sponsor("S2", "AESEV"), sponsor("S1", "AESEV"), sponsor("S3", "AESEV")]

    first = matches_for(entities, name="AESEV")
    second = matches_for(list(reversed(entities)), name="AESEV")

    assert [match["sponsor_uid"] for match in first] == ["S1", "S2", "S3"]
    assert [match["sponsor_uid"] for match in second] == ["S1", "S2", "S3"]


def test_two_sponsor_entities_without_uids_stay_two_matches():
    found = matches_for([sponsor(None, "AESEV"), sponsor(None, "aesev")], name="AESEV")

    assert len(found) == 2


# --- reading a candidate back -----------------------------------------------------


def test_a_described_match_names_the_sponsor_term_it_is_about():
    """The contract between the two halves: a decision has nothing but the candidate
    value to say which sponsor term it was made about."""

    found = matches_for([sponsor("CTTerm_000042", "Severe", "SEV")], name="Severe")

    described = describe_match(found[0])
    assert sponsor_uid_from_candidate(described) == "CTTerm_000042"
    assert described.startswith("EXACT:CTTerm_000042:")


def test_a_sponsor_value_full_of_colons_still_reads_back():
    """Only the first two separators are structural; the rest of the line is prose, and
    a sponsor is free to have punctuated their term however they liked."""

    found = matches_for([sponsor("CTTerm_1", "A:B:C:D")], name="A:B:C:D")

    assert sponsor_uid_from_candidate(describe_match(found[0])) == "CTTerm_1"


@pytest.mark.parametrize(
    "value",
    ["", "not a candidate", "NOPE:CTTerm_1:something", "EXACT::something", None, 42],
)
def test_a_value_from_some_other_kind_of_finding_names_nobody(value):
    """Candidates on the other finding kinds are plain values, and one of those must not
    be read as naming a sponsor term — the caller can then refuse in its own words."""

    assert sponsor_uid_from_candidate(value) is None


# --- the tier that decides ------------------------------------------------------


def test_nothing_matched_has_no_tier():
    assert strongest_tier([]) is None


def test_one_exact_hit_among_near_ones_decides_the_tier():
    """All three spellings collide with the same CDISC value, and the exact one is what
    says an invariant breaks — so it has to decide, wherever it sits in the list."""

    found = matches_for(
        [
            sponsor("S1", "AESEV"),
            sponsor("S2", "aesev"),
            sponsor("S3", "A-E-S-E-V"),
        ],
        name="AESEV",
    )

    assert [match["tier"] for match in found] == [
        MatchTier.EXACT,
        MatchTier.CASE_INSENSITIVE,
        MatchTier.NORMALIZED,
    ]
    assert strongest_tier(found) is MatchTier.EXACT
