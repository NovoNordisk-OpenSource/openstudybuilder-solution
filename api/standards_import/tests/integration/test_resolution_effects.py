"""Decisions taken in review, followed through to what they change.

A resolution that is accepted but changes nothing looks identical to one that worked,
until you look at the data — which is what these do.
"""

from neomodel import db as neomodel_db

from standards_import.tests.integration.packages import codelist, package, term

DATE = "2025-09-26"


def mdr(query, **params):
    rows, _ = neomodel_db.cypher_query(query, params)
    return rows


def two_catalogues_differing_on_terms():
    """SDTM holds T1 and T2; SEND holds T1 only. A membership disagreement."""

    return (
        package(
            "SDTM CT",
            DATE,
            [
                codelist(
                    "C1",
                    "Test Codelist",
                    "TESTCL",
                    terms=[term("T1", "A"), term("T2", "B")],
                )
            ],
        ),
        package(
            "SEND CT",
            DATE,
            [codelist("C1", "Test Codelist", "TESTCL", terms=[term("T1", "A")])],
        ),
    )


def open_item(release, kind):
    return next(
        item
        for item in release.findings(DATE, status="OPEN")
        if item.type.value == kind
    )


def test_ignoring_a_membership_disagreement_keeps_the_union(release):
    release.upload(*two_catalogues_differing_on_terms())
    release.analyse(DATE)

    release.resolve(open_item(release, "INCONSISTENT_TERM_SETS").uid, strategy="IGNORE")
    release.analyse(DATE)
    release.assess(DATE)
    job = release.import_now(DATE)
    assert job.status.value == "SUCCEEDED", job.error

    members = mdr(
        """MATCH (:CTCodelistRoot {uid:'C1'})-[ht:HAS_TERM]->()-[:HAS_TERM_ROOT]->(t:CTTermRoot)
           WHERE ht.end_date IS NULL RETURN t.uid ORDER BY t.uid"""
    )
    assert members == [["T1"], ["T2"]]


def test_dropping_a_term_actually_removes_it_from_the_codelist(release):
    """The strategy was accepted for a year while doing nothing at all.

    It settled the item, unblocked the import, and left the term in place.
    """

    release.upload(*two_catalogues_differing_on_terms())
    release.analyse(DATE)

    release.resolve(
        open_item(release, "INCONSISTENT_TERM_SETS").uid,
        strategy="DROP_TERM_FROM_CODELIST",
        value="T2",
    )
    release.analyse(DATE)
    release.assess(DATE)
    job = release.import_now(DATE)
    assert job.status.value == "SUCCEEDED", job.error

    members = mdr(
        """MATCH (:CTCodelistRoot {uid:'C1'})-[ht:HAS_TERM]->()-[:HAS_TERM_ROOT]->(t:CTTermRoot)
           WHERE ht.end_date IS NULL RETURN t.uid ORDER BY t.uid"""
    )

    assert members == [["T1"]], "the dropped term is still a member"


def test_quoted_synonym_lists_can_be_settled(release):
    """Stripping quotes returns a list, and a list cannot go in a set.

    The crash escaped as a 500 through the endpoint, and took down a whole analysis run
    when the seeded rule met it.
    """

    quoted = package(
        "SDTM CT",
        DATE,
        [
            codelist(
                "C1",
                "Test Codelist",
                "TESTCL",
                synonyms=['"Alpha', "Beta", 'Gamma"'],
                terms=[term("T1", "A")],
            )
        ],
    )
    release.upload(quoted)
    summary = release.analyse(DATE)

    quotes = [f for f in release.findings(DATE) if f.type.value == "UNWANTED_QUOTES"]
    assert quotes, "expected the quoted synonym list to be noticed"

    release.resolve(quotes[0].uid, strategy="STRIP_QUOTES")
    release.analyse(DATE)
    release.assess(DATE)
    job = release.import_now(DATE)
    assert job.status.value == "SUCCEEDED", job.error

    synonyms = mdr(
        """MATCH (:CTCodelistRoot {uid:'C1'})-[:HAS_ATTRIBUTES_ROOT]->()-[hv:HAS_VERSION]->(v)
           WHERE hv.end_date IS NULL RETURN v.synonyms"""
    )[0][0]

    assert synonyms == ["Alpha", "Beta", "Gamma"]
    assert summary is not None
