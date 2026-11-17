"""Applying releases to MDR: versions, memberships, and repeating the run.

Several of these cover things no unit test can see, because they are properties of the
Cypher itself — what `MERGE` matches, what a closed relationship does to a later run.
"""

import pytest
from neomodel import db as neomodel_db

from common.exceptions import ValidationException
from standards_import.repositories import mdr_repository
from standards_import.tests.integration.packages import codelist, package, term

FIRST = "2025-09-26"
SECOND = "2026-03-27"


def mdr(query, **params):
    rows, _ = neomodel_db.cypher_query(query, params)
    return rows


def one(query, **params):
    rows = mdr(query, **params)
    return rows[0][0] if rows else None


def release_with(effective_date, definition, terms, catalogue="SDTM CT"):
    return package(
        catalogue,
        effective_date,
        [codelist("C1", "Test Codelist", "TESTCL", definition=definition, terms=terms)],
    )


def import_clean(release, effective_date, payload):
    """Upload, analyse, assess and import one single-catalogue release.

    The assessment is not optional bookkeeping: the import refuses a release nobody has
    checked against the sponsor side of MDR. These fixtures have no sponsor content, so
    it raises nothing, but it still has to have run.
    """

    release.upload(payload)
    summary = release.analyse(effective_date)
    assert summary.open_inconsistency_count == 0, "fixture was meant to be uncontested"
    release.assess(effective_date)
    job = release.import_now(effective_date)
    assert job.status.value == "SUCCEEDED", job.error
    return job


def test_a_first_import_creates_the_concepts_and_their_first_versions(release):
    import_clean(
        release,
        FIRST,
        release_with(FIRST, "First.", [term("T1", "A"), term("T2", "B")]),
    )

    assert one("MATCH (c:CTCodelistRoot {uid:'C1'}) RETURN count(c)") == 1
    assert one("MATCH (t:CTTermRoot) RETURN count(t)") == 2

    version, definition = mdr(
        """MATCH (:CTCodelistRoot {uid:'C1'})-[:HAS_ATTRIBUTES_ROOT]->()-[hv:HAS_VERSION]->(v)
           WHERE hv.end_date IS NULL RETURN hv.version, v.definition"""
    )[0]
    assert (version, definition) == ("1.0", "First.")

    assert (
        one(
            """MATCH (:CTCodelistRoot {uid:'C1'})-[:HAS_ATTRIBUTES_ROOT]->()-[hv:HAS_VERSION]->()
           RETURN hv.change_description"""
        )
        == "Initial CDISC import"
    )


def test_the_name_half_is_created_once_with_the_sponsor_name(release):
    import_clean(release, FIRST, release_with(FIRST, "First.", [term("T1", "A")]))

    name, is_ordinal = mdr(
        """MATCH (:CTCodelistRoot {uid:'C1'})-[:HAS_NAME_ROOT]->()-[hv:HAS_VERSION]->(v)
           WHERE hv.end_date IS NULL RETURN v.name, v.is_ordinal"""
    )[0]

    assert (name, is_ordinal) == ("Test Codelist", False)


def test_memberships_open_with_the_settled_submission_value(release):
    import_clean(
        release,
        FIRST,
        release_with(FIRST, "First.", [term("T1", "A"), term("T2", "B")]),
    )

    rows = mdr("""MATCH (:CTCodelistRoot {uid:'C1'})-[ht:HAS_TERM]->(ct:CTCodelistTerm)
                 -[:HAS_TERM_ROOT]->(t:CTTermRoot)
           WHERE ht.end_date IS NULL
           RETURN t.uid, ct.submission_value ORDER BY t.uid""")

    assert rows == [["T1", "A"], ["T2", "B"]]


def test_importing_the_same_release_twice_is_refused(release):
    import_clean(release, FIRST, release_with(FIRST, "First.", [term("T1", "A")]))

    with pytest.raises(ValidationException, match="already been imported"):
        release.import_now(FIRST)


def test_a_later_release_versions_what_changed_and_leaves_the_rest_alone(release):
    import_clean(
        release,
        FIRST,
        release_with(FIRST, "First.", [term("T1", "A"), term("T2", "B")]),
    )

    import_clean(
        release,
        SECOND,
        release_with(SECOND, "Second.", [term("T1", "A"), term("T2", "B")]),
    )

    versions = mdr(
        """MATCH (:CTCodelistRoot {uid:'C1'})-[:HAS_ATTRIBUTES_ROOT]->()-[hv:HAS_VERSION]->(v)
           RETURN hv.version, v.definition, hv.end_date IS NULL ORDER BY hv.version"""
    )
    assert versions == [["1.0", "First.", False], ["2.0", "Second.", True]]

    # The terms did not change, so they were not versioned again.
    assert (
        one(
            "MATCH (:CTTermRoot {uid:'T1'})-[:HAS_ATTRIBUTES_ROOT]->()-[hv:HAS_VERSION]->() RETURN count(hv)"
        )
        == 1
    )


def test_only_one_version_and_one_latest_pointer_stays_open(release):
    import_clean(release, FIRST, release_with(FIRST, "First.", [term("T1", "A")]))
    import_clean(release, SECOND, release_with(SECOND, "Second.", [term("T1", "A")]))

    assert (
        one(
            """MATCH (:CTCodelistRoot {uid:'C1'})-[:HAS_ATTRIBUTES_ROOT]->()-[hv:HAS_VERSION]->()
           WHERE hv.end_date IS NULL RETURN count(hv)"""
        )
        == 1
    )
    for pointer in ("LATEST", "LATEST_FINAL"):
        assert (
            one(
                f"MATCH (:CTCodelistRoot {{uid:'C1'}})-[:HAS_ATTRIBUTES_ROOT]->()-[:{pointer}]->() RETURN count(*)"
            )
            == 1
        ), pointer


def test_a_term_that_leaves_a_codelist_has_its_membership_closed(release):
    import_clean(
        release,
        FIRST,
        release_with(FIRST, "First.", [term("T1", "A"), term("T2", "B")]),
    )

    import_clean(release, SECOND, release_with(SECOND, "First.", [term("T1", "A")]))

    rows = mdr(
        """MATCH (:CTCodelistRoot {uid:'C1'})-[ht:HAS_TERM]->()-[:HAS_TERM_ROOT]->(t:CTTermRoot)
           RETURN t.uid, ht.end_date IS NULL ORDER BY t.uid"""
    )

    assert rows == [["T1", True], ["T2", False]]
    # Closed, not deleted: the term itself is still there for older packages to resolve.
    assert one("MATCH (t:CTTermRoot {uid:'T2'}) RETURN count(t)") == 1


def test_a_term_that_comes_back_is_a_member_again(release):
    """`MERGE` on the relationship would match the closed one and never reopen it.

    The term would silently stay out of the codelist while the job counted it as added.
    """

    import_clean(
        release,
        FIRST,
        release_with(FIRST, "First.", [term("T1", "A"), term("T2", "B")]),
    )
    import_clean(release, SECOND, release_with(SECOND, "First.", [term("T1", "A")]))

    import_clean(
        release,
        "2026-09-25",
        release_with("2026-09-25", "First.", [term("T1", "A"), term("T2", "B")]),
    )

    open_members = mdr(
        """MATCH (:CTCodelistRoot {uid:'C1'})-[ht:HAS_TERM]->()-[:HAS_TERM_ROOT]->(t:CTTermRoot)
           WHERE ht.end_date IS NULL RETURN t.uid ORDER BY t.uid"""
    )
    assert open_members == [["T1"], ["T2"]]

    # The gap stays visible: a new relationship, not the old one reopened.
    spells = mdr(
        """MATCH (:CTCodelistRoot {uid:'C1'})-[ht:HAS_TERM]->()-[:HAS_TERM_ROOT]->(:CTTermRoot {uid:'T2'})
           RETURN toString(ht.start_date), ht.end_date IS NULL ORDER BY ht.start_date"""
    )
    assert len(spells) == 2
    assert spells[0][1] is False and spells[1][1] is True


def test_a_run_that_dies_between_closing_and_creating_can_be_retried(
    monkeypatch, release
):
    """The window where a concept has no open version at all.

    A retry that took the concept for a new one would stack a version 1.0 described as
    "Initial CDISC import" on top of a closed 1.0.
    """

    import_clean(release, FIRST, release_with(FIRST, "First.", [term("T1", "A")]))

    release.upload(release_with(SECOND, "Second.", [term("T1", "A")]))
    release.analyse(SECOND)
    release.assess(SECOND)

    # Fail only the first call, rather than undoing the patch later: `monkeypatch.undo`
    # would also undo the autouse fixture that supplies the author.
    real = mdr_repository.create_attribute_versions
    attempts = {"n": 0}

    def die_once(*args, **kwargs):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RuntimeError("killed between closing and creating")
        return real(*args, **kwargs)

    monkeypatch.setattr(mdr_repository, "create_attribute_versions", die_once)
    failed = release.import_now(SECOND)
    assert failed.status.value == "FAILED"

    # Exactly the state the fix is about: closed, with nothing open.
    assert (
        one(
            """MATCH (:CTCodelistRoot {uid:'C1'})-[:HAS_ATTRIBUTES_ROOT]->()-[hv:HAS_VERSION]->()
           WHERE hv.end_date IS NULL RETURN count(hv)"""
        )
        == 0
    )

    retried = release.import_now(SECOND)
    assert retried.status.value == "SUCCEEDED", retried.error

    versions = mdr(
        """MATCH (:CTCodelistRoot {uid:'C1'})-[:HAS_ATTRIBUTES_ROOT]->()-[hv:HAS_VERSION]->(v)
           RETURN hv.version, hv.change_description, hv.end_date IS NULL
           ORDER BY hv.version"""
    )
    assert versions == [
        ["1.0", "Initial CDISC import", False],
        ["2.0", f"CDISC release {SECOND}", True],
    ]
