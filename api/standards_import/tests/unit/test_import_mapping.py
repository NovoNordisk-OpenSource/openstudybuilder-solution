import inspect
from datetime import datetime, timedelta
from typing import Any

import pytest

from standards_import.repositories import (
    inconsistency_repository,
    job_repository,
    mdr_repository,
    release_repository,
    rules_repository,
)
from standards_import.repositories.analysis_repository import catalogue_name
from standards_import.services import import_service
from standards_import.services.import_service import (
    as_bool,
    as_membership,
    codelist_attributes,
    codelist_name,
    next_version,
    ordinal_codelists,
    ordinal_value,
    package_uid,
    sentence_case,
    term_attributes,
    term_name,
    values_differ,
)


def test_package_uid_and_catalogue_name():
    assert package_uid("SDTM CT 2025-09-26") == "SDTM__CT__2025-09-26"
    assert catalogue_name("SDTM CT 2025-09-26") == "SDTM CT"
    assert catalogue_name("DEFINE-XML CT 2021-06-25") == "DEFINE-XML CT"


@pytest.mark.parametrize(
    "current,expected",
    [("1.0", "2.0"), ("2.0", "3.0"), ("12.3", "13.0"), (None, "1.0"), ("odd", "1.0")],
)
def test_next_version_bumps_the_major(current, expected):
    assert next_version(current) == expected


def test_codelist_preferred_term_follows_the_bootstrap_import():
    """`preferred_term` takes the codelist name, not its CDISC `preferredTerm`.

    Diverging would make every codelist look changed the first time this runs against a
    database the bootstrap script populated.
    """
    attributes = codelist_attributes(
        "C66742",
        {
            "name": "No Yes Response",
            "preferredTerm": "CDISC SDTM Yes No Response Terminology",
            "submissionValue": "NY",
            "definition": "A response.",
            "extensible": "false",
            "synonyms": ["NY"],
        },
    )

    assert attributes["preferred_term"] == "No Yes Response"
    assert attributes["name"] == "No Yes Response"
    assert attributes["concept_id"] == "C66742"
    assert attributes["extensible"] is False


def test_term_attributes_use_the_cdisc_preferred_term():
    attributes = term_attributes(
        "C49488", {"preferredTerm": "Yes", "definition": "Yes.", "synonyms": []}
    )

    assert attributes == {
        "preferred_term": "Yes",
        "definition": "Yes.",
        "concept_id": "C49488",
        "synonyms": [],
    }


def test_missing_synonyms_become_an_empty_list():
    assert codelist_attributes("C1", {})["synonyms"] == []
    assert term_attributes("C1", {})["synonyms"] == []


@pytest.mark.parametrize(
    "value,expected",
    [("true", True), ("false", False), ("TRUE", True), (True, True), (None, False)],
)
def test_as_bool(value, expected):
    assert as_bool(value) is expected


def test_extensible_is_normalised_before_comparing():
    """CDISC ships `extensible` as a string; the bootstrap import stores that string.

    Comparing it raw against a proper boolean would version every codelist for nothing.
    """
    wanted = codelist_attributes("C1", {"name": "n", "extensible": "false"})
    stored_by_bootstrap = dict(wanted, extensible="false")

    assert values_differ(wanted, stored_by_bootstrap) is False


def test_synonym_order_is_not_a_change():
    wanted = codelist_attributes("C1", {"name": "n", "synonyms": ["A", "B"]})
    stored = dict(wanted, synonyms=["B", "A"])

    assert values_differ(wanted, stored) is False


def test_a_real_change_is_detected():
    wanted = codelist_attributes("C1", {"name": "n", "definition": "new"})
    stored = dict(wanted, definition="old")

    assert values_differ(wanted, stored) is True


def test_a_value_missing_from_mdr_is_a_change():
    wanted = codelist_attributes("C1", {"name": "n", "definition": "something"})

    assert values_differ(wanted, {}) is True


def test_sentence_case_keeps_acronyms_and_roman_numerals():
    assert sentence_case("Prolonged ST Segment by ECG Finding") == (
        "prolonged ST segment by ECG finding"
    )
    assert sentence_case("Phase II Trial") == "phase II trial"


def test_names_are_case_variants_of_themselves():
    """The main API requires the sentence case to be a case-variant of the name."""

    props = codelist_name({"name": "No Yes Response"})

    assert props["name_sentence_case"].lower() == props["name"].lower()
    assert props["codelist_type"] == "Standard"
    assert props["is_ordinal"] is False


def test_a_new_term_takes_the_cdisc_preferred_term_as_its_sponsor_name():
    props = term_name({"preferredTerm": "Adverse Event"})

    assert props["name"] == "Adverse Event"
    assert props["name_sentence_case"].lower() == "adverse event"


ANALYSED_AT = datetime(2026, 3, 1, 9, 0)
ASSESSED_AT = datetime(2026, 3, 1, 10, 0)


def assessed(status="ANALYZED", **overrides):
    """A release that has been through everything the import asks of it."""

    release = {
        "status": status,
        "open_inconsistency_count": 0,
        "analyzed_at": ANALYSED_AT,
        "assessed_at": ASSESSED_AT,
    }
    release.update(overrides)
    return release


EMPTY_DELTA: dict[str, list[Any]] = {"memberships_added": [], "memberships_ended": []}


@pytest.fixture
def nothing_in_the_way(monkeypatch):
    """Every question `import_blockers` puts to a database, answered as "all clear".

    Each test below then patches back the one thing it is about. Kept as a fixture rather
    than repeated inline so that a blocker added later fails the test that owns it,
    instead of every test in this section at once.
    """

    monkeypatch.setattr(
        mdr_repository, "get_head_effective_date", lambda excluding=None: None
    )
    monkeypatch.setattr(job_repository, "find_running_job", lambda *_: None)
    monkeypatch.setattr(rules_repository, "get_import_enabled", lambda *_: True)
    monkeypatch.setattr(
        inconsistency_repository, "count_decisions_since_analysis", lambda *_: 0
    )
    monkeypatch.setattr(inconsistency_repository, "get_sponsor_actions", lambda *_: [])
    monkeypatch.setattr(mdr_repository, "get_term_usage", lambda uids: {})
    monkeypatch.setattr(mdr_repository, "get_membership_usage", lambda pairs: {})


@pytest.mark.usefixtures("nothing_in_the_way")
def test_a_failed_run_is_not_blocked_by_its_own_half_written_packages(monkeypatch):
    """`apply_delta` creates the packages first, so a run that dies after that would
    otherwise see its own package as the head and refuse to be retried."""

    seen = {}

    def fake_head(excluding=None):
        seen["excluding"] = excluding
        # the failed run already created this release's package
        return "2025-09-26" if excluding != "2025-09-26" else "2025-03-28"

    monkeypatch.setattr(mdr_repository, "get_head_effective_date", fake_head)

    blockers = import_service.import_blockers(
        None, assessed("READY"), "2025-09-26", EMPTY_DELTA
    )

    assert seen["excluding"] == "2025-09-26"
    assert not blockers


@pytest.mark.usefixtures("nothing_in_the_way")
def test_a_genuinely_older_release_is_still_refused(monkeypatch):
    """Excluding the release under import must not weaken the append-only rule."""

    monkeypatch.setattr(
        mdr_repository, "get_head_effective_date", lambda excluding=None: "2025-09-26"
    )

    blockers = import_service.import_blockers(
        None, assessed(), "2025-03-28", EMPTY_DELTA
    )

    assert any("only ever appends" in b for b in blockers)


@pytest.mark.usefixtures("nothing_in_the_way")
def test_decisions_made_since_the_last_analysis_block_the_import(monkeypatch):
    """Resolving the last open item flips the release to ANALYZED by itself.

    Without this check the import would run against staged values the decisions were
    never applied to, because analysis is what applies them.
    """

    monkeypatch.setattr(
        inconsistency_repository, "count_decisions_since_analysis", lambda *_: 3
    )

    blockers = import_service.import_blockers(
        None, assessed(), "2025-09-26", EMPTY_DELTA
    )

    assert any("since the last analysis" in b for b in blockers)


@pytest.mark.usefixtures("nothing_in_the_way")
def test_a_release_nobody_assessed_for_sponsor_impact_is_refused():
    """The assessment is the only pass that looks at what the release lands on. Skipped,
    an exact name collision imports quietly and leaves a codelist the main API refuses to
    edit — so an unassessed release must not be importable at all."""

    blockers = import_service.import_blockers(
        None, assessed(assessed_at=None), "2025-09-26", EMPTY_DELTA
    )

    assert any("has not been assessed" in b for b in blockers)


@pytest.mark.usefixtures("nothing_in_the_way")
def test_a_disabled_import_blocks_a_release_that_is_otherwise_ready(monkeypatch):
    """The switch only gates the promotion into OSB; the release itself is fine."""

    monkeypatch.setattr(rules_repository, "get_import_enabled", lambda *_: False)

    blockers = import_service.import_blockers(
        None, assessed(), "2025-09-26", EMPTY_DELTA
    )

    assert len(blockers) == 1
    assert "disabled" in blockers[0]


@pytest.mark.usefixtures("nothing_in_the_way")
def test_an_assessment_older_than_the_last_analysis_is_refused():
    """Analysis rebuilds the settled values the assessment compared against, so an
    analysis run that is newer means the answer is stale even though both have run."""

    stale = assessed(analyzed_at=ASSESSED_AT + timedelta(hours=1))
    blockers = import_service.import_blockers(None, stale, "2025-09-26", EMPTY_DELTA)

    assert any("analysed since sponsor impact" in b for b in blockers)


@pytest.mark.usefixtures("nothing_in_the_way")
def test_a_sponsor_term_settled_for_removal_that_is_now_in_use_blocks(monkeypatch):
    """Deciding and importing are separate moments, and a study can be built on the
    sponsor term in between. Retiring it then would break that study, so the check the
    resolution endpoint made is made again here — before the run writes anything."""

    monkeypatch.setattr(
        inconsistency_repository,
        "get_sponsor_actions",
        lambda *_: [
            {
                "uid": "item",
                "type": "SPONSOR_TERM_DUPLICATE",
                "concept_id": "C1",
                "related_concept_id": "T2",
                "strategy": "RETIRE_SPONSOR_TERM",
                "resolved_value": "CTTerm_000042",
            }
        ],
    )
    monkeypatch.setattr(
        mdr_repository,
        "get_term_usage",
        lambda uids: {"CTTerm_000042": [{"count": 3, "relationship": "HAS_CT_TERM"}]},
    )

    blockers = import_service.import_blockers(
        None, assessed(), "2025-09-26", EMPTY_DELTA
    )

    assert any("CTTerm_000042" in b for b in blockers)


@pytest.mark.usefixtures("nothing_in_the_way")
def test_a_sponsor_term_settled_for_removal_that_nothing_uses_does_not_block(
    monkeypatch,
):
    monkeypatch.setattr(
        inconsistency_repository,
        "get_sponsor_actions",
        lambda *_: [
            {
                "uid": "item",
                "type": "SPONSOR_TERM_DUPLICATE",
                "concept_id": "C1",
                "related_concept_id": "T2",
                "strategy": "RETIRE_SPONSOR_TERM",
                "resolved_value": "CTTerm_000042",
            }
        ],
    )
    monkeypatch.setattr(
        mdr_repository, "get_term_usage", lambda uids: {"CTTerm_000042": []}
    )

    assert not import_service.import_blockers(
        None, assessed(), "2025-09-26", EMPTY_DELTA
    )


@pytest.mark.usefixtures("nothing_in_the_way")
def test_assessing_after_analysing_clears_the_way():
    """The order that matters is assess-last, and the check must not fire on it."""

    assert not import_service.import_blockers(
        None, assessed(), "2025-09-26", EMPTY_DELTA
    )


# --- changed and removed memberships ---------------------------------------------


def membership(codelist_uid, term_uid, submission_value):
    return {
        "codelist_uid": codelist_uid,
        "term_uid": term_uid,
        "submission_value": submission_value,
    }


def test_a_pair_in_both_added_and_ended_is_a_value_change():
    """A submission-value change closes the old triple and opens a new one for the same
    (codelist, term) pair — indistinguishable from a removal-plus-arrival until paired.
    """

    delta = {
        "memberships_added": [membership("C1", "T1", "NEW")],
        "memberships_ended": [membership("C1", "T1", "OLD")],
    }

    changed, removed = import_service.changed_and_removed_memberships(delta)

    assert not removed
    assert len(changed) == 1
    assert changed[0]["codelist_uid"] == "C1"
    assert changed[0]["term_uid"] == "T1"
    assert changed[0]["old"]["submission_value"] == "OLD"
    assert changed[0]["new"]["submission_value"] == "NEW"


def test_a_pair_only_in_ended_is_a_removal():
    delta = {
        "memberships_added": [],
        "memberships_ended": [membership("C1", "T1", "OLD")],
    }

    changed, removed = import_service.changed_and_removed_memberships(delta)

    assert not changed
    assert removed == [membership("C1", "T1", "OLD")]


def test_a_pair_only_in_added_is_neither():
    """An ordinary new membership — nothing about it changed or was removed."""

    delta = {
        "memberships_added": [membership("C1", "T1", "NEW")],
        "memberships_ended": [],
    }

    changed, removed = import_service.changed_and_removed_memberships(delta)

    assert not changed
    assert not removed


def test_a_term_moved_between_codelists_is_a_removal_from_one_and_an_addition_to_the_other():
    """Same term, different codelist: the pair key is (codelist, term), so this does not
    collide with a same-codelist value change."""

    delta = {
        "memberships_added": [membership("C2", "T1", "A")],
        "memberships_ended": [membership("C1", "T1", "A")],
    }

    changed, removed = import_service.changed_and_removed_memberships(delta)

    assert not changed
    assert removed == [membership("C1", "T1", "A")]


# --- ordinal codelists ----------------------------------------------------------

AIMS = "Abnormal Involuntary Movement Scale Clinical Classification STRESC for AIMS0101"
KURTZKE = "Kurtzke Functional System Scores Clinical Classification STRESC for KFSS0101"
TANNER = "Tanner Scale Girl Clinical Classification STRESC for TANNER01 TN/TC"
LAB = "Laboratory Test Standard Character Result"


@pytest.mark.parametrize(
    "submission_value,expected",
    [
        ("0", 0.0),
        ("4", 4.0),
        ("-1", -1.0),
        ("Unknown", None),
        ("i0", None),
        ("Stage 1", None),
        ("2.5", None),
        ("", None),
        (None, None),
    ],
)
def test_ordinal_value_takes_only_whole_numbers(submission_value, expected):
    assert ordinal_value(submission_value) == expected


def test_a_scored_scale_is_ordinal():
    memberships = {("C1", "T0", "0"), ("C1", "T1", "1"), ("C1", "T2", "2")}

    assert ordinal_codelists(memberships, {"C1": AIMS}) == {"C1"}


def test_a_scale_is_still_ordinal_when_some_terms_are_not_scored():
    """Real Kurtzke codelists grade 0-6 and also carry `Unknown`."""

    memberships = {("C1", "T0", "0"), ("C1", "T1", "1"), ("C1", "TU", "Unknown")}

    assert ordinal_codelists(memberships, {"C1": KURTZKE}) == {"C1"}


def test_a_stresc_codelist_with_no_scored_term_is_not_ordinal():
    """Tanner grades `Stage 1`-`Stage 5` and Rutgeerts `i0`-`i4`: named, not scored."""

    memberships = {("C1", "T1", "Stage 1"), ("C1", "T2", "Stage 2")}

    assert ordinal_codelists(memberships, {"C1": TANNER}) == set()


def test_a_scored_codelist_not_marked_stresc_is_not_ordinal():
    memberships = {("C1", "T1", "1"), ("C1", "T2", "2")}

    assert ordinal_codelists(memberships, {"C1": LAB}) == set()


def test_the_name_flag_follows_the_scored_set():
    assert codelist_name({"name": AIMS}, True)["is_ordinal"] is True
    assert codelist_name({"name": AIMS})["is_ordinal"] is False


def test_a_membership_of_a_scored_scale_carries_its_rank():
    row = as_membership(("C1", "T3", "3"), "2025-09-26", {"C1"})

    assert row["ordinal"] == 3.0


def test_an_unscored_member_of_a_scored_scale_carries_no_rank():
    """`Unknown` belongs to the codelist but has no place in the ordering."""

    row = as_membership(("C1", "TU", "Unknown"), "2025-09-26", {"C1"})

    assert row["ordinal"] is None


def test_memberships_of_an_unscored_codelist_carry_no_rank():
    """A numeric submission value elsewhere is not a rank."""

    row = as_membership(("C9", "T1", "1"), "2025-09-26", {"C1"})

    assert row["ordinal"] is None


def test_opening_a_membership_does_not_merge_on_the_relationship():
    """A regression guard on the Cypher, since `MERGE` here is quietly wrong.

    `MERGE (root)-[:HAS_TERM]->(ct)` matches a *closed* membership as well as an open
    one, so `ON CREATE` never fires for a term that left the codelist and came back —
    it stays out while the job reports it as added. Behaviour is verified against a
    real database; this only stops the shape being reintroduced.
    """

    source = inspect.getsource(mdr_repository.add_memberships)
    # The comment in that query says the words too, so judge the Cypher alone.
    query = "\n".join(
        line for line in source.splitlines() if not line.strip().startswith("//")
    )

    assert "MERGE (root)-[" not in query
    assert "open.end_date IS NULL" in query
    assert "CREATE (root)-[:HAS_TERM {" in query


def test_the_head_lookup_is_scoped_to_the_release_being_imported(monkeypatch):
    """The diff must pass the date, or the crash window cannot be recognised."""

    seen = {}

    def fake_heads(uids, package_date):
        seen["uids"], seen["package_date"] = uids, package_date
        return {}

    monkeypatch.setattr(mdr_repository, "get_codelist_heads", fake_heads)
    monkeypatch.setattr(
        release_repository,
        "get_codelists",
        lambda *_: [{"concept_id": "C1", "props": {"name": "n"}}],
    )

    import_service.diff_codelists(None, "2025-09-26")

    assert seen == {"uids": ["C1"], "package_date": "2025-09-26"}


def test_the_head_lookup_accepts_a_version_closed_at_this_release():
    """A regression guard on the Cypher; behaviour is verified against a database.

    Closing the old version and creating the new one are separate steps, so a run that
    dies between them leaves no open version. Matching only `end_date IS NULL` would
    make the retry treat the concept as new.
    """

    for query in (
        inspect.getsource(mdr_repository.get_codelist_heads),
        inspect.getsource(mdr_repository.get_term_heads),
    ):
        assert "hv.end_date = datetime($package_date)" in query
        assert "ORDER BY CASE WHEN hv.end_date IS NULL THEN 0 ELSE 1 END" in query
