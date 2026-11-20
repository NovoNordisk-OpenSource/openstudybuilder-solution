"""What CDISC said it changed, attached to the codelists and terms it is about.

Two things are being tested here, and neither is the spreadsheet reader — that is
`test_changelog_parsing`, which needs no database.

**Where an entry lands.** The `NCI Code` column means different things on different
rows, and the sheet's own `CDISC Term Type` is not a reliable guide to which. What the
code actually matches in the staged catalogue is, including the two cases where the
subject is no longer there to point at.

**That none of it blocks anything.** This is commentary hung alongside a release. It
must not move the release's status, change what the import would do, or appear among
the blockers.
"""

import pytest

from common.exceptions import NotFoundException
from standards_import.models.packages import EffectiveDateStatus
from standards_import.tests.integration.packages import codelist, package, term

DATE = "2025-09-26"


def entry(
    nci_code="C001",
    short_name="LBTEST",
    change_type="UPDATE",
    summary="Update CDISC Definition",
    uid=None,
    request_codes=None,
    instructions=None,
):
    """One row as the parser hands it over: no term type, no before-and-after."""

    return {
        "uid": uid or f"uid-{nci_code}-{short_name}-{summary}",
        "change_type": change_type,
        "change_summary": summary,
        "request_codes": request_codes if request_codes is not None else ["CDISC-1"],
        "implementation_instructions": instructions,
        "nci_code": nci_code,
        "codelist_short_name": short_name,
        "codelist_long_name": "Laboratory Test Name",
    }


def sdtm_package(terms=("C001", "C002")):
    return package(
        "SDTM CT",
        DATE,
        [
            codelist(
                "CL1",
                "Laboratory Test Name",
                "LBTEST",
                [term(code, f"SV{code}") for code in terms],
            )
        ],
    )


def target_labels(session, date=DATE):
    """What each entry ended up attached to, by the subject's node label.

    `RESOLVE_TARGET` only ever points an entry at a `RawCatalogue`, `RawCodelist`, or
    `RawTerm` — but every one of those also carries `:CDISCStaging`, and Neo4j does
    not guarantee a node's labels come back in write order, so `head(labels(t))` picks
    whichever of the two it feels like. Filtering the marker label out first makes this
    deterministic.
    """

    return {
        (record["nci_code"], record["label"]): record["n"]
        for record in session.run(
            """
            MATCH (:EffectiveDateImport {effective_date: $date})
                  -[:HAS_CHANGELOG_ENTRY]->(e:ChangelogEntry)
            OPTIONAL MATCH (e)-[:ABOUT]->(t)
            RETURN e.nci_code AS nci_code,
                   head([label IN labels(t) WHERE label <> "CDISCStaging"]) AS label,
                   count(*) AS n
            """,
            date=date,
        ).data()
    }


# --- where an entry lands ---------------------------------------------------------


def test_an_entry_about_a_term_attaches_to_that_term(release, staging_session):
    release.upload(sdtm_package())

    release.load_changelog(DATE, "SDTM CT", [entry(nci_code="C001")])

    assert target_labels(staging_session)[("C001", "RawTerm")] == 1


def test_an_entry_carrying_the_codelists_own_code_attaches_to_the_codelist(
    release, staging_session
):
    """Codelists have definitions and synonyms too, so a row typed `CDISC Definition`
    is not always about a term. The code is what settles it."""

    release.upload(sdtm_package())

    release.load_changelog(DATE, "SDTM CT", [entry(nci_code="CL1")])

    assert target_labels(staging_session)[("CL1", "RawCodelist")] == 1


def test_an_entry_with_no_code_attaches_to_the_codelist(release, staging_session):
    """How a collapsed codelist rename arrives: the fan-out's copies each carried a
    member term's code, and the entry that survives carries none."""

    release.upload(sdtm_package())

    release.load_changelog(DATE, "SDTM CT", [entry(nci_code=None)])

    assert target_labels(staging_session)[(None, "RawCodelist")] == 1


def test_a_removed_term_falls_back_to_its_surviving_codelist(release, staging_session):
    """The real case: terms dropped from `LBTEST`, which CDISC kept. There is no term
    node left to attach to, but the codelist is still the right place to show it."""

    release.upload(sdtm_package(terms=("C001",)))

    release.load_changelog(
        DATE,
        "SDTM CT",
        [entry(nci_code="C002", change_type="REMOVE", summary="Remove term")],
    )

    assert target_labels(staging_session)[("C002", "RawCodelist")] == 1


def test_an_entry_whose_codelist_is_gone_falls_back_to_the_catalogue(
    release, staging_session
):
    """The `CCRCLS` case: CDISC retired the codelist and every term in it, so nothing
    the row names was staged at all."""

    release.upload(sdtm_package())

    release.load_changelog(
        DATE,
        "SDTM CT",
        [entry(nci_code="C900", short_name="CCRCLS", change_type="REMOVE")],
    )

    assert target_labels(staging_session)[("C900", "RawCatalogue")] == 1


def test_every_entry_is_attached_to_something(release, staging_session):
    """Each way a subject can be missing has a fallback, so none is left dangling."""

    release.upload(sdtm_package())
    release.load_changelog(
        DATE,
        "SDTM CT",
        [
            entry(nci_code="C001"),
            entry(nci_code="CL1"),
            entry(nci_code=None),
            entry(nci_code="C404"),
            entry(nci_code="C900", short_name="NOSUCHCL"),
        ],
    )

    dangling = staging_session.run(
        """
        MATCH (:EffectiveDateImport {effective_date: $date})-[:HAS_CHANGELOG_ENTRY]->(e)
        WHERE NOT (e)-[:ABOUT]->() RETURN count(e) AS n
        """,
        date=DATE,
    ).single()["n"]

    assert dangling == 0


def test_a_term_is_resolved_under_its_own_codelist_only(release, staging_session):
    """`RawTerm` nodes are not unique by concept id — a term in two codelists has one
    node under each — so a bare match would attach the entry to either."""

    release.upload(
        package(
            "SDTM CT",
            DATE,
            [
                codelist("CL1", "Name", "LBTEST", [term("C001", "SV1")]),
                codelist("CL2", "Code", "LBTESTCD", [term("C001", "SV2")]),
            ],
        )
    )

    release.load_changelog(
        DATE, "SDTM CT", [entry(nci_code="C001", short_name="LBTESTCD")]
    )

    attached_to = staging_session.run("""
        MATCH (:ChangelogEntry)-[:ABOUT]->(t:RawTerm)<-[:HAS_RAW_TERM]-(cl:RawCodelist)
        RETURN cl.submissionValue AS codelist
        """).data()

    assert [record["codelist"] for record in attached_to] == ["LBTESTCD"]


# --- replacing an upload ----------------------------------------------------------


def test_re_uploading_a_catalogue_replaces_its_entries(release):
    release.upload(sdtm_package())
    release.load_changelog(DATE, "SDTM CT", [entry(), entry(nci_code="C002")])

    release.load_changelog(DATE, "SDTM CT", [entry()])

    assert len(release.changelog(DATE)) == 1


def test_a_different_filename_does_not_double_the_entries(release):
    """Why replacement is scoped by catalogue rather than by `source_file`, unlike the
    pairing workbooks: this payload says which catalogue it is, so the filename is not
    its identity, and scoping by one would let a rename duplicate every row."""

    release.upload(sdtm_package())
    release.load_changelog(DATE, "SDTM CT", [entry()], source_file="first.xls")

    release.load_changelog(DATE, "SDTM CT", [entry()], source_file="renamed.xls")

    assert len(release.changelog(DATE)) == 1


def test_another_catalogues_entries_are_left_alone(release):
    release.upload(sdtm_package())
    release.upload(
        package(
            "SEND CT",
            DATE,
            [codelist("CL1", "Laboratory Test Name", "LBTEST", [term("C001", "SV1")])],
        )
    )
    release.load_changelog(DATE, "SEND CT", [entry()])

    release.load_changelog(DATE, "SDTM CT", [entry()])

    assert {c for e in release.changelog(DATE) for c in e.catalogues} == {
        "SDTM CT",
        "SEND CT",
    }


def test_replacing_a_package_file_keeps_the_entries_attached(release, staging_session):
    """Replacing a package deletes and rebuilds its whole raw subtree, taking every
    `ABOUT` relationship with it. The entries carry what they need to be resolved
    again, so the spreadsheet does not have to be uploaded a second time."""

    release.upload(sdtm_package())
    release.load_changelog(DATE, "SDTM CT", [entry(nci_code="C001")])

    release.upload(sdtm_package(terms=("C001", "C002", "C003")))

    assert target_labels(staging_session)[("C001", "RawTerm")] == 1


# --- reading it back --------------------------------------------------------------


def test_the_codelist_detail_carries_the_codelists_own_entries(release):
    release.upload(sdtm_package())
    release.analyse(DATE)
    release.load_changelog(DATE, "SDTM CT", [entry(nci_code=None)])

    detail = release.codelist(DATE, "CL1")

    assert [e.change_summary for e in detail.changelog] == ["Update CDISC Definition"]


def test_an_entry_about_a_term_lands_on_that_terms_row(release):
    release.upload(sdtm_package())
    release.analyse(DATE)
    release.load_changelog(DATE, "SDTM CT", [entry(nci_code="C001")])

    detail = release.codelist(DATE, "CL1")
    rows = {t.concept_id: t for t in detail.terms}

    assert [e.change_summary for e in rows["C001"].changelog] == [
        "Update CDISC Definition"
    ]
    assert rows["C002"].changelog == []


def test_the_term_detail_carries_the_terms_entries(release):
    release.upload(sdtm_package())
    release.analyse(DATE)
    release.load_changelog(
        DATE, "SDTM CT", [entry(nci_code="C001"), entry(nci_code=None)]
    )

    assert [e.change_summary for e in release.term(DATE, "C001").changelog] == [
        "Update CDISC Definition"
    ]
    assert release.term(DATE, "C002").changelog == []


def test_the_same_change_from_two_catalogues_is_shown_once(release):
    """Catalogues overlap, and each ships its own sheet saying the same thing."""

    release.upload(sdtm_package(terms=("C001",)))
    release.upload(
        package(
            "SEND CT",
            DATE,
            [codelist("CL1", "Laboratory Test Name", "LBTEST", [term("C001", "SV1")])],
        )
    )
    release.analyse(DATE)
    release.load_changelog(DATE, "SDTM CT", [entry(nci_code="C001")])
    release.load_changelog(DATE, "SEND CT", [entry(nci_code="C001")])

    rows = {t.concept_id: t for t in release.codelist(DATE, "CL1").terms}

    assert len(rows["C001"].changelog) == 1
    assert rows["C001"].changelog[0].catalogues == ["SDTM CT", "SEND CT"]


def test_a_release_with_no_changelog_reads_the_same_as_before(release):
    release.upload(sdtm_package())
    release.analyse(DATE)

    detail = release.codelist(DATE, "CL1")

    assert detail.changelog == []
    assert all(t.changelog == [] for t in detail.terms)


def test_entries_about_a_retired_codelist_are_still_listable(release):
    """Nothing in the codelist-by-codelist view has a row for a codelist that is not
    in the release, so the release-wide list is the only way to reach these."""

    release.upload(sdtm_package())
    release.load_changelog(
        DATE, "SDTM CT", [entry(nci_code="C900", short_name="CCRCLS")]
    )

    assert [e.codelist_short_name for e in release.changelog(DATE)] == ["CCRCLS"]


def test_the_listing_can_be_narrowed_to_one_catalogue(release):
    release.upload(sdtm_package())
    release.upload(
        package(
            "SEND CT",
            DATE,
            [codelist("CL9", "Other", "OTHER", [term("C009", "SV9")])],
        )
    )
    release.load_changelog(DATE, "SDTM CT", [entry()])
    release.load_changelog(DATE, "SEND CT", [entry(short_name="OTHER")])

    assert [e.codelist_short_name for e in release.changelog(DATE, "SEND CT")] == [
        "OTHER"
    ]


# --- it blocks nothing ------------------------------------------------------------


def test_uploading_a_changelog_does_not_reset_an_analysed_release(release):
    """A package or pairing upload sends the release back to `FILES_STAGED`, because
    both change what the import would do. This one does not, and must not: it would
    turn commentary into something that holds up an import."""

    release.upload(sdtm_package())
    release.analyse(DATE)
    before = release.dashboard(DATE).release_status

    release.load_changelog(DATE, "SDTM CT", [entry()])

    assert before != EffectiveDateStatus.FILES_STAGED
    assert release.dashboard(DATE).release_status == before


def test_a_changelog_raises_no_findings_and_no_blockers(release):
    release.upload(sdtm_package())
    release.analyse(DATE)
    before = release.dashboard(DATE)

    release.load_changelog(DATE, "SDTM CT", [entry(), entry(nci_code="C404")])
    after = release.dashboard(DATE)

    assert after.blockers == before.blockers
    assert after.can_import == before.can_import


def test_the_preview_is_unchanged_by_a_changelog(release):
    """It says what the import would do, and this changes nothing about that."""

    release.upload(sdtm_package())
    release.analyse(DATE)
    before = release.preview(DATE)

    release.load_changelog(DATE, "SDTM CT", [entry()])

    assert release.preview(DATE) == before


def test_a_changelog_needs_its_catalogue_to_be_staged_first(release):
    """The one thing this upload does insist on. Entries are stored attached to the
    codelist or term they are about, so arriving before the package would leave every
    one of them pointing at nothing."""

    release.upload(sdtm_package())

    with pytest.raises(NotFoundException, match="SEND CT"):
        release.load_changelog(DATE, "SEND CT", [entry()])


def test_a_changelog_for_an_unknown_release_is_refused(release):
    with pytest.raises(NotFoundException, match="2099-01-01"):
        release.load_changelog("2099-01-01", "SDTM CT", [entry()])


@pytest.mark.parametrize("show", ["changed", "all"])
def test_the_term_list_is_filtered_the_same_way_as_before(release, show):
    """An entry is not a finding, so it does not pull an otherwise unchanged term into
    the `show=changed` view. Whether it should is a product question; quietly widening
    a documented filter is not the way to answer it."""

    release.upload(sdtm_package())
    release.analyse(DATE)
    before = {t.concept_id for t in release.codelist(DATE, "CL1", show=show).terms}

    release.load_changelog(DATE, "SDTM CT", [entry(nci_code="C001")])

    assert {
        t.concept_id for t in release.codelist(DATE, "CL1", show=show).terms
    } == before
