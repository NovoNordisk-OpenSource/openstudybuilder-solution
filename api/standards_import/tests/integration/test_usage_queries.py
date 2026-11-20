"""What counts as a term being *used*: only a consumer that is still live.

A consumer is live while one of its `HAS_VERSION` relationships is open. A study
selection, syntax instance or the like whose versions have all been closed is history,
and must not stand in the way of retiring or displacing the term.

These go straight at `mdr_repository` rather than through a release, because the thing
under test is two hand-written Cypher shapes and nothing about them needs an import.
"""

import pytest
from neomodel import db as neomodel_db

from standards_import.repositories import mdr_repository
from standards_import.tests.integration.sponsor_data import (
    add_sponsor_codelist,
    add_sponsor_term,
    use_term_in_a_study,
    use_term_in_a_syntax_instance,
    use_term_name_value_in_a_syntax_instance,
)

TERM = "SPONSOR_1"
CODELIST = "C1"

# One entry per way a consumer can reach a term: how to plant it, and what it is reported
# as. `get_term_usage` has an arm for each; `get_membership_usage` only the first.
ARMS = {
    "selected in context": lambda version: use_term_in_a_study(CODELIST, TERM, version),
    "used by name root": lambda version: use_term_in_a_syntax_instance(TERM, version),
    "used by name value": lambda version: use_term_name_value_in_a_syntax_instance(
        TERM, version
    ),
}
REPORTED_AS = {
    "selected in context": "selected in context",
    "used by name root": "used by name",
    "used by name value": "used by name",
}
MEMBERSHIP_ARMS = ["selected in context"]


@pytest.fixture
def sponsor_term(databases):
    del databases  # depended on for the clean pair it creates, not for a value
    add_sponsor_codelist(CODELIST, "Test Codelist", "TESTCL")
    add_sponsor_term(CODELIST, TERM, "Sponsor term", "SPONSORSV")


def term_usage():
    return mdr_repository.get_term_usage([TERM])[TERM]


def membership_usage(codelist=CODELIST):
    return mdr_repository.get_membership_usage([(codelist, TERM)])[(codelist, TERM)]


def total(usage):
    return sum(entry["count"] for entry in usage)


@pytest.mark.parametrize("arm", ARMS)
def test_a_live_consumer_is_reported(sponsor_term, arm):
    del sponsor_term
    ARMS[arm]("live")

    usage = term_usage()

    assert total(usage) == 1
    assert usage[0]["through"] == REPORTED_AS[arm]


@pytest.mark.parametrize("arm", ARMS)
def test_a_consumer_whose_versions_are_all_closed_is_not_reported(sponsor_term, arm):
    del sponsor_term
    ARMS[arm]("closed")

    assert term_usage() == []


@pytest.mark.parametrize("arm", ARMS)
def test_a_consumer_with_no_versions_at_all_is_not_reported(sponsor_term, arm):
    """No open version means no live version, whatever the reason."""

    del sponsor_term
    ARMS[arm]("unversioned")

    assert term_usage() == []


@pytest.mark.parametrize("arm", ARMS)
def test_a_consumer_that_was_reopened_is_reported_once(sponsor_term, arm):
    """Version 1.0 closed, version 2.0 open: still live, and still one consumer. The
    liveness test must not multiply the row by the number of versions it looked at."""

    del sponsor_term
    ARMS[arm]("reopened")

    assert total(term_usage()) == 1


def test_an_open_version_has_no_end_date_property_at_all(sponsor_term):
    """The case that slipped past `{end_date: null}`: the property is absent rather than
    holding a null, because Neo4j does not store nulls. If the fixture ever started
    writing one, the tests above would stop covering it."""

    del sponsor_term
    use_term_in_a_study(CODELIST, TERM, "live")

    rows, _ = neomodel_db.cypher_query(
        "MATCH ()-[hv:HAS_VERSION]->(:StudyVisit) RETURN keys(hv)"
    )

    assert len(rows) == 1
    assert "end_date" not in rows[0][0]


def test_only_the_live_consumers_among_several_are_counted(sponsor_term):
    del sponsor_term
    use_term_in_a_study(CODELIST, TERM, "live")
    use_term_in_a_study(CODELIST, TERM, "closed")
    use_term_in_a_syntax_instance(TERM, "live")
    use_term_in_a_syntax_instance(TERM, "closed")

    usage = {entry["through"]: entry["count"] for entry in term_usage()}

    assert usage == {"selected in context": 1, "used by name": 1}


@pytest.mark.parametrize("arm", MEMBERSHIP_ARMS)
def test_membership_usage_reports_a_live_consumer(sponsor_term, arm):
    del sponsor_term
    ARMS[arm]("live")

    assert total(membership_usage()) == 1


@pytest.mark.parametrize("arm", MEMBERSHIP_ARMS)
def test_membership_usage_ignores_a_closed_consumer(sponsor_term, arm):
    del sponsor_term
    ARMS[arm]("closed")

    assert membership_usage() == []


def test_a_live_consumer_through_another_codelist_is_not_this_memberships(
    sponsor_term,
):
    """The codelist condition and the liveness condition are ANDed, not ORed: a live
    consumer that picked the term through another codelist must not leak in because it
    happens to be live."""

    del sponsor_term
    add_sponsor_codelist("C2", "Other Codelist", "OTHERCL")
    use_term_in_a_study("C2", TERM, "live")

    assert membership_usage("C1") == []
    assert total(membership_usage("C2")) == 1
