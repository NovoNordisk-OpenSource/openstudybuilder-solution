"""Matching a release's changelog entries onto the changes a package diff found."""

from standards_import.domain import changelog_match


def entry(**overrides):
    base = {
        "uid": "e1",
        "change_type": "UPDATE",
        "change_summary": "Update CDISC Definition",
        "request_codes": ["CDISC-1"],
        "implementation_instructions": None,
        "nci_code": "C1000",
        "codelist_short_name": "UNIT",
        "codelist_long_name": "Unit",
        "catalogue": "SDTM CT",
        "source_file": "sdtmct-2025-09-26.xls",
    }
    base.update(overrides)
    return base


def record(target_labels, target_concept_id=None, parent=None, **overrides):
    return {
        "entry": entry(**overrides),
        "target_labels": [target_labels],
        "target_concept_id": target_concept_id,
        "target_submission_value": None,
        "parent_codelist_id": parent,
    }


def uids(entries):
    return [item["uid"] for item in entries]


# --- field detection -------------------------------------------------------------


def test_the_field_comes_out_of_the_summary_since_term_type_is_not_stored():
    assert changelog_match.field_of(
        entry(change_summary="Update CDISC Definition")
    ) == ("definition")
    assert changelog_match.field_of(entry(change_summary="Add new CDISC Synonym")) == (
        "synonyms"
    )
    assert changelog_match.field_of(entry(change_summary="Remove CDISC Synonym")) == (
        "synonyms"
    )
    assert changelog_match.field_of(
        entry(change_summary="Update NCI Preferred Term")
    ) == ("preferredTerm")


def test_codelist_name_wins_over_a_bare_name_match():
    assert changelog_match.field_of(entry(change_summary="Update Codelist Name")) == (
        "name"
    )


def test_a_summary_naming_no_field_yields_none():
    assert changelog_match.field_of(entry(change_summary="Add new term")) is None


# --- indexing --------------------------------------------------------------------


def test_a_term_is_indexed_under_its_own_codelist_and_catalogue_wide():
    index = changelog_match.index_entries(
        [record("RawTerm", target_concept_id="C2000", parent="C1000")]
    )

    assert uids(index["term"][("C1000", "C2000")]) == ["e1"]
    assert uids(index["term_any"]["C2000"]) == ["e1"]


def test_an_entry_whose_nci_code_is_the_codelists_own_is_about_the_codelist():
    index = changelog_match.index_entries(
        [record("RawCodelist", target_concept_id="C1000", nci_code="C1000")]
    )

    assert uids(index["codelist"]["C1000"]) == ["e1"]


def test_a_collapsed_rename_carrying_no_nci_code_is_about_the_codelist():
    index = changelog_match.index_entries(
        [record("RawCodelist", target_concept_id="C1000", nci_code=None)]
    )

    assert uids(index["codelist"]["C1000"]) == ["e1"]


def test_an_entry_on_a_codelist_naming_another_code_is_about_a_removed_term():
    """The `RESOLVE_TARGET` fallback for a term that left a surviving codelist."""

    index = changelog_match.index_entries(
        [record("RawCodelist", target_concept_id="C1000", nci_code="C2000")]
    )

    assert uids(index["removed_term"][("C1000", "C2000")]) == ["e1"]
    assert uids(index["removed_term_any"]["C2000"]) == ["e1"]
    assert not index["codelist"]["C1000"]


def test_an_entry_on_the_catalogue_is_about_a_retired_codelist():
    index = changelog_match.index_entries(
        [record("RawCatalogue", codelist_short_name="FREQ")]
    )

    assert uids(index["retired_codelist"]["FREQ"]) == ["e1"]


# --- matching --------------------------------------------------------------------


def test_a_retired_codelist_is_matched_through_the_catalogue_fallback():
    """Band 1 is only reachable this way - the codelist has no node left in the release."""

    index = changelog_match.index_entries(
        [record("RawCatalogue", change_type="REMOVE", codelist_short_name="FREQ")]
    )

    matched = changelog_match.match_entries(
        index,
        {
            "kind": "codelist_removed",
            "codelist": {"conceptId": "C1001", "submissionValue": "FREQ"},
        },
    )

    assert uids(matched) == ["e1"]


def test_a_removed_term_is_matched_through_the_codelist_fallback():
    index = changelog_match.index_entries(
        [
            record(
                "RawCodelist",
                target_concept_id="C1000",
                nci_code="C2000",
                change_type="REMOVE",
                change_summary="Remove term from codelist",
            )
        ]
    )

    matched = changelog_match.match_entries(
        index, {"kind": "term_removed", "term": {"conceptId": "C2000"}}
    )

    assert uids(matched) == ["e1"]


def test_a_membership_change_is_not_annotated_from_a_different_codelist():
    index = changelog_match.index_entries(
        [
            record(
                "RawTerm",
                target_concept_id="C2000",
                parent="C1000",
                change_type="ADD",
                uid="under-1000",
            ),
            record(
                "RawTerm",
                target_concept_id="C2000",
                parent="C9999",
                change_type="ADD",
                uid="under-9999",
            ),
        ]
    )

    matched = changelog_match.match_entries(
        index, {"kind": "membership_added", "key": ("C1000", "C2000")}
    )

    assert uids(matched) == ["under-1000"]


def test_the_matching_field_is_preferred_where_several_entries_share_a_subject():
    index = changelog_match.index_entries(
        [
            record(
                "RawCodelist",
                target_concept_id="C1000",
                nci_code="C1000",
                change_summary="Update CDISC Definition",
                uid="def",
            ),
            record(
                "RawCodelist",
                target_concept_id="C1000",
                nci_code="C1000",
                change_summary="Update NCI Preferred Term",
                uid="pt",
            ),
        ]
    )

    matched = changelog_match.match_entries(
        index,
        {"kind": "codelist_changed", "conceptId": "C1000", "field": "definition"},
    )

    assert uids(matched) == ["def"]


def test_narrowing_never_returns_nothing():
    """A change annotated with several plausible entries beats one annotated with none."""

    index = changelog_match.index_entries(
        [
            record(
                "RawCodelist",
                target_concept_id="C1000",
                nci_code="C1000",
                change_summary="Update CDISC Definition",
            )
        ]
    )

    matched = changelog_match.match_entries(
        index,
        {"kind": "codelist_changed", "conceptId": "C1000", "field": "submissionValue"},
    )

    assert uids(matched) == ["e1"]


def test_the_change_type_is_preferred_over_a_contradicting_one():
    index = changelog_match.index_entries(
        [
            record("RawTerm", target_concept_id="C2000", parent="C1000", uid="updated"),
            record(
                "RawTerm",
                target_concept_id="C2000",
                parent="C1000",
                change_type="ADD",
                uid="added",
            ),
        ]
    )

    matched = changelog_match.match_entries(
        index, {"kind": "term_added", "term": {"conceptId": "C2000"}}
    )

    assert uids(matched) == ["added"]


def test_a_moved_term_collects_its_entries_across_codelists():
    index = changelog_match.index_entries(
        [
            record(
                "RawTerm",
                target_concept_id="C2000",
                parent="C1000",
                change_type="ADD",
                uid="entered",
            ),
            record(
                "RawCodelist",
                target_concept_id="C1001",
                nci_code="C2000",
                change_type="REMOVE",
                uid="left",
            ),
        ]
    )

    matched = changelog_match.match_entries(
        index, {"kind": "term_moved", "move": {"conceptId": "C2000"}}
    )

    assert sorted(uids(matched)) == ["entered", "left"]


def test_an_entry_reached_by_two_indexes_is_returned_once():
    index = changelog_match.index_entries(
        [
            record(
                "RawCodelist",
                target_concept_id="C1000",
                nci_code="C2000",
                change_type="REMOVE",
            )
        ]
    )

    matched = changelog_match.match_entries(
        index, {"kind": "membership_removed", "key": ("C1000", "C2000")}
    )

    assert uids(matched) == ["e1"]


def test_an_unmatched_change_yields_nothing():
    index = changelog_match.index_entries(
        [record("RawTerm", target_concept_id="C2000", parent="C1000")]
    )

    assert not changelog_match.match_entries(
        index, {"kind": "term_added", "term": {"conceptId": "C7777"}}
    )


def test_an_unknown_kind_returns_nothing_rather_than_raising():
    assert not changelog_match.match_entries(
        changelog_match.index_entries([]), {"kind": "?"}
    )


def test_an_empty_index_annotates_nothing_without_raising():
    index = changelog_match.index_entries([])

    assert not changelog_match.match_entries(
        index,
        {
            "kind": "codelist_removed",
            "codelist": {"conceptId": "C1", "submissionValue": "X"},
        },
    )
