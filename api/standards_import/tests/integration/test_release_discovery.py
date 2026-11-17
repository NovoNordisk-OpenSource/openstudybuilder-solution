"""Discovery against a real staging database, so the Cypher of the diff is under test.

The CDISC call is stubbed — it is one function behind a seam and has no database in it —
but everything after it is real: the UNION over uploads and earlier discoveries, and the
`MERGE` that makes a second run report nothing.
"""

from common.exceptions import ValidationException
from standards_import.repositories import mdr_repository, rules_repository, staging_db
from standards_import.services import cdisc_client, staging_service
from standards_import.tests.integration.packages import codelist, package, term

DATE = "2025-09-26"

SDTM = package(
    "SDTM CT",
    DATE,
    [codelist("C1", "Test Codelist", "TESTCL", terms=[term("T1", "A")])],
)


def published_title(catalogue: str, effective_date: str) -> str:
    """A title in the shape CDISC's `/mdr/ct/packages` list actually publishes them in."""

    return f"{catalogue} Controlled Terminology Package 61 Effective {effective_date}"


PUBLISHED = [
    {
        "title": published_title("SDTM", "2026-03-27"),
        "href": "/mdr/ct/packages/sdtmct-2026-03-27",
    },
    {
        "title": published_title("SDTM", "2025-09-26"),
        "href": "/mdr/ct/packages/sdtmct-2025-09-26",
    },
    {
        "title": published_title("ADaM", "2025-06-27"),
        "href": "/mdr/ct/packages/adamct-2025-06-27",
    },
    {"title": "Protocol Templates", "href": "/mdr/protocol-templates"},
]


def stub_no_content(monkeypatch):
    """Fails any attempt to fetch package content, without reaching the real CDISC Library.

    Any test not specifically exercising auto-staging must stub this rather than let
    discovery reach out to the real Library. Raising the same exception type `auto_stage_release` already
    handles keeps this indistinguishable from CDISC being genuinely unreachable: the
    release is still reported, just not staged.
    """

    def unavailable(href, api_key):
        raise ValidationException(msg=f"content not stubbed for {href!r}")

    monkeypatch.setattr(cdisc_client, "fetch_package_content", unavailable)


def given_mdr_head(effective_date: str):
    """Puts a package in the MDR database, which is what makes its date the head."""

    mdr_repository.mdr_query(
        "CREATE (:CTPackage {uid: $uid, effective_date: date($effective_date)})",
        {"uid": f"head-{effective_date}", "effective_date": effective_date},
    )


def known_releases():
    with staging_db.staging_session() as session:
        return staging_db.run_query(
            session,
            """
            MATCH (known:KnownRelease)
            RETURN known.package_name AS package_name,
                   known.catalogue AS catalogue,
                   known.effective_date AS effective_date,
                   known.href AS href
            ORDER BY known.package_name
            """,
        )


def test_discovery_records_only_what_is_newer_than_the_mdr_head(databases, monkeypatch):
    del databases  # depended on for the clean pair it creates, not for a value
    stub_no_content(monkeypatch)
    monkeypatch.setattr(cdisc_client, "fetch_package_list", lambda api_key: PUBLISHED)
    # ADaM CT 2025-06-27 is older than the head, even though MDR has never seen its
    # catalogue before — a release is one effective date, not a catalogue.
    given_mdr_head(DATE)

    result = staging_service.discover_new_releases("a-token")

    assert [release.package_name for release in result.new_releases] == [
        "SDTM CT 2026-03-27",
    ]
    assert result.skipped_count == 1
    assert [record["package_name"] for record in known_releases()] == [
        "SDTM CT 2026-03-27",
    ]


def test_a_datetime_typed_mdr_package_is_read_as_a_plain_date(databases):
    """Packages loaded by `import_standards` store a datetime, not a date."""

    del databases  # depended on for the clean pair it creates, not for a value
    mdr_repository.mdr_query(
        "CREATE (:CTPackage {uid: 'p', effective_date: datetime('2025-03-28T00:00:00Z')})"
    )

    assert mdr_repository.get_head_effective_date() == "2025-03-28"
    assert mdr_repository.get_head_effective_date(excluding="2025-03-28") is None


def test_the_release_at_the_mdr_head_is_not_reported_as_new(databases, monkeypatch):
    del databases  # depended on for the clean pair it creates, not for a value
    stub_no_content(monkeypatch)
    monkeypatch.setattr(cdisc_client, "fetch_package_list", lambda api_key: PUBLISHED)
    given_mdr_head(DATE)

    staging_service.discover_new_releases("a-token")

    assert "SDTM CT 2025-09-26" not in [
        record["package_name"] for record in known_releases()
    ]


def test_a_staged_release_not_yet_in_mdr_is_not_reported_again(databases, monkeypatch):
    """The MDR head cannot see an upload waiting for import; staging has to remember it."""

    del databases  # depended on for the clean pair it creates, not for a value
    stub_no_content(monkeypatch)
    monkeypatch.setattr(cdisc_client, "fetch_package_list", lambda api_key: PUBLISHED)
    staging_service.stage_package_file(SDTM)

    result = staging_service.discover_new_releases("a-token")

    assert "SDTM CT 2025-09-26" not in [
        release.package_name for release in result.new_releases
    ]
    assert "SDTM CT 2026-03-27" in [
        release.package_name for release in result.new_releases
    ]


def test_a_second_run_of_the_same_list_finds_nothing_further(databases, monkeypatch):
    """What one run recorded is what the next one measures against."""

    del databases  # depended on for the clean pair it creates, not for a value
    stub_no_content(monkeypatch)
    monkeypatch.setattr(cdisc_client, "fetch_package_list", lambda api_key: PUBLISHED)
    first = staging_service.discover_new_releases("a-token")
    after_first = known_releases()

    second = staging_service.discover_new_releases("a-token")

    # Nothing was staged, so every entry that can be placed is new on the first run.
    assert len(first.new_releases) == 3
    assert not second.new_releases
    assert known_releases() == after_first


def test_discovery_records_the_catalogue_and_the_link_it_was_published_under(
    databases, monkeypatch
):
    del databases  # depended on for the clean pair it creates, not for a value
    stub_no_content(monkeypatch)
    monkeypatch.setattr(
        cdisc_client, "fetch_package_list", lambda api_key: [PUBLISHED[2]]
    )

    staging_service.discover_new_releases("a-token")

    assert known_releases() == [
        {
            "package_name": "ADAM CT 2025-06-27",
            "catalogue": "ADAM CT",
            "effective_date": "2025-06-27",
            "href": "/mdr/ct/packages/adamct-2025-06-27",
        }
    ]


def test_a_new_sdtm_release_is_fetched_and_staged(databases, monkeypatch):
    """SDTM CT is the one catalogue discovery does not just report — it stages it too."""

    del databases  # depended on for the clean pair it creates, not for a value
    monkeypatch.setattr(rules_repository, "DEFAULT_MANDATORY_CATALOGUES", {"SDTM CT"})
    monkeypatch.setattr(
        cdisc_client, "fetch_package_list", lambda api_key: [PUBLISHED[0]]
    )
    monkeypatch.setattr(
        cdisc_client,
        "fetch_package_content",
        lambda href, api_key: package(
            "SDTM CT",
            "2026-03-27",
            [codelist("C1", "Test Codelist", "TESTCL", terms=[term("T1", "A")])],
        ),
    )

    result = staging_service.discover_new_releases("a-token")

    assert len(result.new_releases) == 1
    release = result.new_releases[0]
    assert release.auto_staged is True
    assert release.stage_error is None
    staged = staging_service.get_staged_files()
    assert [file.package_name for file in staged] == ["SDTM CT 2026-03-27"]


def test_a_failed_auto_stage_does_not_hide_the_release_or_its_peers(
    databases, monkeypatch
):
    """A fetch failure for SDTM CT must not cost ADaM CT its place in the same run."""

    del databases  # depended on for the clean pair it creates, not for a value
    monkeypatch.setattr(rules_repository, "DEFAULT_MANDATORY_CATALOGUES", {"SDTM CT"})
    monkeypatch.setattr(
        cdisc_client, "fetch_package_list", lambda api_key: [PUBLISHED[0], PUBLISHED[2]]
    )

    def broken_fetch(href, api_key):
        raise ValidationException(msg="CDISC Library did not answer")

    monkeypatch.setattr(cdisc_client, "fetch_package_content", broken_fetch)

    result = staging_service.discover_new_releases("a-token")

    by_catalogue = {release.catalogue: release for release in result.new_releases}
    assert by_catalogue["SDTM CT"].auto_staged is False
    assert by_catalogue["SDTM CT"].stage_error == "CDISC Library did not answer"
    assert by_catalogue["ADAM CT"].auto_staged is False
    assert by_catalogue["ADAM CT"].stage_error is None
    assert not staging_service.get_staged_files()
