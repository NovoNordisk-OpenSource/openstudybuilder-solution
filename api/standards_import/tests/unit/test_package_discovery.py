"""Noticing a new CDISC release, without talking to CDISC or to a database.

Three things are worth holding still here. The `/mdr/ct/packages` list titles a release
differently from the `name` field inside its own package document — "SDTM Controlled
Terminology Package 61 Effective 2026-03-27" versus "SDTM CT 2026-03-27" — so discovery
needs its own parser, `derive_catalogue_from_title`, and that parser must still land on
the same catalogue name `derive_catalogue` would, or a release already staged by hand
would never be recognised as the one CDISC just published. And "new" means strictly
newer than the head of the MDR database — a release is one effective date, not a
catalogue — which is the same append-only-at-the-head rule the import enforces.
"""

import contextlib
from typing import Any

import httpx
import pytest

from common.exceptions import ValidationException
from standards_import.config import settings
from standards_import.repositories import (
    mdr_repository,
    rules_repository,
    staging_repository,
)
from standards_import.services import cdisc_client, staging_service
from standards_import.services.staging_service import (
    derive_catalogue,
    derive_catalogue_from_title,
    discover_new_releases,
    is_newer_than_head,
)

BASE_URL = "https://library.example.com/api"

PACKAGE_LIST = {
    "_links": {
        "packages": [
            {
                "href": "/mdr/ct/packages/sdtmct-2026-03-27",
                "title": "SDTM CT 2026-03-27",
            },
            {
                "href": "/mdr/ct/packages/adamct-2025-06-27",
                "title": "ADaM CT 2025-06-27",
            },
        ]
    }
}


# --- the split shared with the upload path -----------------------------------------


def test_derive_catalogue_splits_a_published_name():
    assert derive_catalogue("SDTM CT 2026-03-27") == ("SDTM CT", "2026-03-27")


def test_derive_catalogue_keeps_a_multi_word_catalogue_whole():
    assert derive_catalogue("DEFINE-XML CT 2025-12-19") == (
        "DEFINE-XML CT",
        "2025-12-19",
    )


def test_derive_catalogue_refuses_a_name_without_a_trailing_date():
    """The same message the upload path has always given, because it is the same rule."""

    with pytest.raises(
        ValidationException, match="does not end with its effective date"
    ):
        derive_catalogue("SDTM CT")


def test_derive_catalogue_refuses_a_trailing_date_that_is_not_a_date():
    with pytest.raises(ValidationException, match="not a YYYY-MM-DD date"):
        derive_catalogue("SDTM CT 2024-13-45")


# --- the split against CDISC's own list title --------------------------------------


def test_derive_catalogue_from_title_reads_the_published_shape():
    assert derive_catalogue_from_title(
        "SDTM Controlled Terminology Package 61 Effective 2026-03-27"
    ) == ("SDTM CT", "2026-03-27")


def test_derive_catalogue_from_title_keeps_a_multi_word_catalogue_whole():
    assert derive_catalogue_from_title(
        "Define-XML Controlled Terminology Package 45 Effective 2021-03-26"
    ) == ("DEFINE-XML CT", "2021-03-26")


def test_derive_catalogue_from_title_agrees_with_the_upload_paths_catalogue_name():
    """Otherwise a release already staged by hand is never recognised as this one."""

    catalogue, effective_date = derive_catalogue_from_title(
        "ADaM Controlled Terminology Package 61 Effective 2026-03-27"
    )
    assert (catalogue, effective_date) == derive_catalogue("ADAM CT 2026-03-27")


def test_derive_catalogue_from_title_refuses_a_title_of_a_different_shape():
    with pytest.raises(
        ValidationException, match=r"does not match the .*Controlled Terminology"
    ):
        derive_catalogue_from_title("Protocol Templates")


def test_an_empty_mdr_database_makes_every_date_new():
    assert is_newer_than_head("2025-06-27", None)


@pytest.mark.parametrize(
    "effective_date, expected",
    [("2025-12-20", True), ("2025-12-19", False), ("2025-09-26", False)],
)
def test_only_a_date_strictly_after_the_mdr_head_is_new(effective_date, expected):
    assert is_newer_than_head(effective_date, "2025-12-19") is expected


# --- the one call that leaves the process ------------------------------------------


def stub_transport(monkeypatch, handler):
    """Points `httpx.Client` at a handler, leaving the request building under test.

    Patched at the transport rather than around `fetch_package_list`: the URL the path is
    joined onto the base URL to make, and the header the token turns into, are the whole of
    what this function does.
    """

    original_client = httpx.Client

    def client(**kwargs):
        return original_client(**kwargs, transport=httpx.MockTransport(handler))

    monkeypatch.setattr(httpx, "Client", client)


def given_library(monkeypatch):
    monkeypatch.setattr(settings, "cdisc_api_base_url", BASE_URL)


def test_fetch_package_list_reads_titles_and_hrefs(monkeypatch):
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["api_key"] = request.headers.get("api-key")
        return httpx.Response(200, json=PACKAGE_LIST)

    given_library(monkeypatch)
    stub_transport(monkeypatch, handler)

    entries = cdisc_client.fetch_package_list("a-token")

    assert entries == [
        {"title": "SDTM CT 2026-03-27", "href": "/mdr/ct/packages/sdtmct-2026-03-27"},
        {"title": "ADaM CT 2025-06-27", "href": "/mdr/ct/packages/adamct-2025-06-27"},
    ]
    assert seen["url"] == f"{BASE_URL}/mdr/ct/packages"
    assert seen["api_key"] == "a-token"


def test_fetch_package_list_needs_a_base_url(monkeypatch):
    monkeypatch.setattr(settings, "cdisc_api_base_url", "")

    with pytest.raises(ValidationException, match="CDISC_API_BASE_URL"):
        cdisc_client.fetch_package_list("a-token")


def test_fetch_package_list_raises_on_an_error_response(monkeypatch):
    given_library(monkeypatch)
    stub_transport(monkeypatch, lambda request: httpx.Response(503))

    with pytest.raises(httpx.HTTPStatusError):
        cdisc_client.fetch_package_list("a-token")


def test_fetch_package_list_tolerates_a_list_with_no_packages(monkeypatch):
    """An answer whose shape changed is not a release list nobody published."""

    given_library(monkeypatch)
    stub_transport(
        monkeypatch, lambda request: httpx.Response(200, json={"_links": {}})
    )

    assert cdisc_client.fetch_package_list("a-token") == []


# --- the diff against staging ------------------------------------------------------


def given_mandatory(monkeypatch, *catalogues):
    """The catalogues the organisation has configured as mandatory — what discovery stages."""

    monkeypatch.setattr(rules_repository, "ensure_seed_data", lambda _session: None)
    monkeypatch.setattr(
        rules_repository, "get_mandatory_catalogues", lambda _session: list(catalogues)
    )


def stub_staging(monkeypatch):
    """Discovery against a staging database that records the writes instead of making them.

    Returns the list of `record_known_releases` calls, so a test can assert on what would
    have been written as well as on what came back.
    """

    written: list[list[dict[str, Any]]] = []

    given_mandatory(monkeypatch, "SDTM CT")
    monkeypatch.setattr(
        staging_service, "staging_session", lambda: contextlib.nullcontext(None)
    )

    def record_known_releases(_session, releases):
        written.append(releases)
        return [
            {**release, "discovered_at": "2026-04-01T00:00:00"} for release in releases
        ]

    monkeypatch.setattr(
        staging_repository, "record_known_releases", record_known_releases
    )
    monkeypatch.setattr(
        staging_repository, "get_unstaged_known_releases", lambda *_: []
    )
    return written


def published_title(catalogue: str, effective_date: str) -> str:
    """A title in the shape CDISC's `/mdr/ct/packages` list actually publishes them in."""

    return f"{catalogue} Controlled Terminology Package 61 Effective {effective_date}"


def given_published(monkeypatch, *titles):
    monkeypatch.setattr(
        cdisc_client,
        "fetch_package_list",
        lambda api_key: [{"title": title, "href": f"/p/{title}"} for title in titles],
    )


def given_head(monkeypatch, head, known_names=()):
    """The MDR head, and the package names staging already holds or has been told of."""

    monkeypatch.setattr(
        mdr_repository, "get_head_effective_date", lambda excluding=None: head
    )
    monkeypatch.setattr(
        staging_repository,
        "get_known_package_names",
        lambda _session: set(known_names),
    )


def test_only_releases_newer_than_the_mdr_head_are_reported(monkeypatch):
    stub_staging(monkeypatch)
    given_published(
        monkeypatch,
        published_title("SDTM", "2026-03-27"),  # newer than the MDR head
        published_title("SDTM", "2025-09-26"),  # older
        published_title("SDTM", "2025-12-19"),  # exactly the MDR head
        published_title(
            "ADaM", "2025-06-27"
        ),  # older still, even though its catalogue is new to MDR
    )
    given_head(monkeypatch, "2025-12-19")

    result = discover_new_releases("a-token")

    assert [release.package_name for release in result.new_releases] == [
        "SDTM CT 2026-03-27",
    ]
    assert result.skipped_count == 0


def test_a_release_spanning_several_catalogues_reports_every_one_of_them(monkeypatch):
    """A release is one effective date; discovery must not drop the catalogues under it."""

    stub_staging(monkeypatch)
    given_published(
        monkeypatch,
        published_title("SDTM", "2026-03-27"),
        published_title("ADaM", "2026-03-27"),
        published_title("SEND", "2026-03-27"),
    )
    given_head(monkeypatch, "2025-12-19")

    result = discover_new_releases("a-token")

    assert [release.package_name for release in result.new_releases] == [
        "SDTM CT 2026-03-27",
        "ADAM CT 2026-03-27",
        "SEND CT 2026-03-27",
    ]


def test_the_reported_releases_are_the_ones_recorded(monkeypatch):
    recorded = stub_staging(monkeypatch)
    title = published_title("SDTM", "2026-03-27")
    given_published(monkeypatch, title)
    given_head(monkeypatch, None)

    discover_new_releases("a-token")

    assert recorded == [
        [
            {
                "catalogue": "SDTM CT",
                "package_name": "SDTM CT 2026-03-27",
                "effective_date": "2026-03-27",
                "href": f"/p/{title}",
            }
        ]
    ]


def test_nothing_is_written_when_there_is_nothing_new(monkeypatch):
    recorded = stub_staging(monkeypatch)
    given_published(monkeypatch, published_title("SDTM", "2025-12-19"))
    given_head(monkeypatch, "2025-12-19")

    result = discover_new_releases("a-token")

    assert not result.new_releases
    assert not recorded


def test_a_name_that_cannot_be_placed_is_counted_not_raised(monkeypatch):
    """One oddly named package must not cost the release next to it in the list."""

    stub_staging(monkeypatch)
    given_published(
        monkeypatch,
        "SDTM CT 2025-12-19",  # the upload shape, not the list shape — still unparseable here
        "Protocol Templates",
        published_title("SDTM", "2026-03-27"),
    )
    given_head(monkeypatch, None)

    result = discover_new_releases("a-token")

    assert [release.package_name for release in result.new_releases] == [
        "SDTM CT 2026-03-27"
    ]
    assert result.skipped_count == 2


def test_a_release_already_staged_or_known_is_not_rediscovered(monkeypatch):
    """Staged-but-not-imported releases are invisible to the MDR head; staging remembers them."""

    recorded = stub_staging(monkeypatch)
    given_published(
        monkeypatch,
        published_title("SDTM", "2026-03-27"),
        published_title("ADaM", "2026-03-27"),
    )
    given_head(monkeypatch, "2025-12-19", known_names={"SDTM CT 2026-03-27"})

    result = discover_new_releases("a-token")

    assert [release.package_name for release in result.new_releases] == [
        "ADAM CT 2026-03-27"
    ]
    assert [r["package_name"] for r in recorded[0]] == ["ADAM CT 2026-03-27"]


def test_a_release_known_but_older_than_the_mdr_head_is_not_retried(monkeypatch):
    """Once MDR has moved past a release it can no longer be imported; do not fetch it."""

    stub_staging(monkeypatch)
    given_published(monkeypatch)
    given_head(monkeypatch, "2026-06-26", known_names={"SDTM CT 2026-03-27"})
    monkeypatch.setattr(
        staging_repository,
        "get_unstaged_known_releases",
        lambda _session, _catalogues: [
            {
                "catalogue": "SDTM CT",
                "package_name": "SDTM CT 2026-03-27",
                "effective_date": "2026-03-27",
                "href": "/p/sdtmct-2026-03-27",
                "discovered_at": "2026-04-01T00:00:00",
            }
        ],
    )

    def unexpected_fetch(href, api_key):
        raise AssertionError("a release behind the MDR head must not be fetched")

    monkeypatch.setattr(cdisc_client, "fetch_package_content", unexpected_fetch)

    assert not discover_new_releases("a-token").new_releases


# --- auto-staging SDTM CT -----------------------------------------------------------


def test_a_new_sdtm_release_is_fetched_and_staged(monkeypatch):
    stub_staging(monkeypatch)
    given_published(monkeypatch, published_title("SDTM", "2026-03-27"))
    given_head(monkeypatch, None)
    monkeypatch.setattr(
        cdisc_client,
        "fetch_package_content",
        lambda href, api_key: b"the package bytes",
    )
    staged: list[bytes] = []
    monkeypatch.setattr(staging_service, "stage_package_file", staged.append)

    result = discover_new_releases("a-token")

    assert staged == [b"the package bytes"]
    assert len(result.new_releases) == 1
    release = result.new_releases[0]
    assert release.auto_staged is True
    assert release.stage_error is None


def test_a_new_release_of_another_catalogue_is_not_fetched(monkeypatch):
    """Only the mandatory catalogues are auto-staged; every other one is upload-by-hand."""

    stub_staging(monkeypatch)
    given_published(monkeypatch, published_title("ADaM", "2026-03-27"))
    given_head(monkeypatch, None)

    def unexpected_fetch(href, api_key):
        raise AssertionError("ADaM CT must not be auto-staged")

    monkeypatch.setattr(cdisc_client, "fetch_package_content", unexpected_fetch)

    result = discover_new_releases("a-token")

    assert len(result.new_releases) == 1
    release = result.new_releases[0]
    assert release.auto_staged is False
    assert release.stage_error is None


def test_every_mandatory_catalogue_is_fetched_and_staged(monkeypatch):
    stub_staging(monkeypatch)
    given_mandatory(monkeypatch, "SDTM CT", "ADAM CT")
    given_published(
        monkeypatch,
        published_title("SDTM", "2026-03-27"),
        published_title("ADaM", "2026-03-27"),
        published_title("SEND", "2026-03-27"),
    )
    given_head(monkeypatch, None)
    fetched: list[str] = []

    def fetch(href, api_key):
        fetched.append(href)
        return b"bytes"

    monkeypatch.setattr(cdisc_client, "fetch_package_content", fetch)
    monkeypatch.setattr(staging_service, "stage_package_file", lambda payload: None)

    result = discover_new_releases("a-token")

    staged = {r.catalogue: r.auto_staged for r in result.new_releases}
    assert staged == {"SDTM CT": True, "ADAM CT": True, "SEND CT": False}
    assert len(fetched) == 2


def test_nothing_is_fetched_when_no_catalogue_is_mandatory(monkeypatch):
    stub_staging(monkeypatch)
    given_mandatory(monkeypatch)
    given_published(monkeypatch, published_title("SDTM", "2026-03-27"))
    given_head(monkeypatch, None)

    def unexpected_fetch(href, api_key):
        raise AssertionError("no catalogue is mandatory, so nothing is auto-staged")

    monkeypatch.setattr(cdisc_client, "fetch_package_content", unexpected_fetch)

    result = discover_new_releases("a-token")

    assert result.new_releases[0].auto_staged is False


def test_a_failed_auto_stage_is_reported_not_raised(monkeypatch):
    """One SDTM fetch failing must not hide the other releases discovery found."""

    stub_staging(monkeypatch)
    given_published(
        monkeypatch,
        published_title("SDTM", "2026-03-27"),
        published_title("ADaM", "2026-03-27"),
    )
    given_head(monkeypatch, None)

    def broken_fetch(href, api_key):
        raise httpx.ConnectError("no route to host")

    monkeypatch.setattr(cdisc_client, "fetch_package_content", broken_fetch)

    result = discover_new_releases("a-token")

    by_catalogue = {release.catalogue: release for release in result.new_releases}
    assert by_catalogue["SDTM CT"].auto_staged is False
    assert by_catalogue["SDTM CT"].stage_error is not None
    assert "no route to host" in by_catalogue["SDTM CT"].stage_error
    assert by_catalogue["ADAM CT"].auto_staged is False
    assert by_catalogue["ADAM CT"].stage_error is None


def test_a_release_known_but_never_staged_is_retried(monkeypatch):
    """A release that failed to auto-stage on an earlier call must not wait forever."""

    stub_staging(monkeypatch)
    given_published(monkeypatch)  # nothing new published this time
    given_head(monkeypatch, "2025-12-19", known_names={"SDTM CT 2026-03-27"})
    monkeypatch.setattr(
        staging_repository,
        "get_unstaged_known_releases",
        lambda _session, catalogues: (
            [
                {
                    "catalogue": "SDTM CT",
                    "package_name": "SDTM CT 2026-03-27",
                    "effective_date": "2026-03-27",
                    "href": "/p/sdtmct-2026-03-27",
                    "discovered_at": "2026-04-01T00:00:00",
                }
            ]
            if "SDTM CT" in catalogues
            else []
        ),
    )
    monkeypatch.setattr(
        cdisc_client,
        "fetch_package_content",
        lambda href, api_key: b"the package bytes",
    )
    staged: list[bytes] = []
    monkeypatch.setattr(staging_service, "stage_package_file", staged.append)

    result = discover_new_releases("a-token")

    assert not result.new_releases
    assert staged == [b"the package bytes"]


def test_a_release_just_auto_staged_is_not_retried_a_second_time(monkeypatch):
    """A release this same call just staged must not be fetched from CDISC twice."""

    stub_staging(monkeypatch)
    given_published(monkeypatch, published_title("SDTM", "2026-03-27"))
    given_head(monkeypatch, None)
    calls: list[str] = []
    monkeypatch.setattr(
        cdisc_client, "fetch_package_content", lambda href, api_key: calls.append(href)
    )
    monkeypatch.setattr(staging_service, "stage_package_file", lambda _payload: None)
    monkeypatch.setattr(
        staging_repository,
        "get_unstaged_known_releases",
        lambda _session, _catalogues: [
            {
                "catalogue": "SDTM CT",
                "package_name": "SDTM CT 2026-03-27",
                "effective_date": "2026-03-27",
                "href": "/p/SDTM Controlled Terminology Package 61 Effective 2026-03-27",
                "discovered_at": "2026-04-01T00:00:00",
            }
        ],
    )

    discover_new_releases("a-token")

    assert len(calls) == 1
