"""The one place this app reads from the CDISC Library, and the seam for replacing it.

Discovery asks CDISC one question — *which controlled terminology releases exist?* — and
nothing else crosses this module. What comes back is the name and the link of each
release, never its content: package content still arrives by upload, so that the bytes
staged are the bytes somebody looked at.

Kept to a single function for the same reason `semantic_provider` is: an organisation that
reaches the library through a gateway of its own changes a base URL and a token, and
nothing about how the answer is diffed against staging can drift while it does.
"""

import logging

from common.exceptions import ValidationException
from standards_import.config import settings

log = logging.getLogger(__name__)

PACKAGE_LIST_PATH = "mdr/ct/packages"


def require_configured() -> None:
    ValidationException.raise_if_not(
        settings.cdisc_api_base_url,
        msg="Reaching the CDISC Library needs STANDARDS_IMPORT_CDISC_API_BASE_URL, "
        "which is not set.",
    )


def _headers(api_key: str) -> dict[str, str]:
    # The CDISC Library API authenticates via this header, not a bearer token.
    return {"Accept": "application/json", "api-key": api_key}


def fetch_package_list(api_key: str) -> list[dict[str, str]]:
    """The controlled terminology releases CDISC has published, as `{title, href}` rows.

    The library returns them under `_links.packages`, one entry per catalogue at one
    effective date — the same granularity as an uploaded package file, so a title read
    here and a `name` read out of an uploaded document mean the same thing.

    Entries are handed back exactly as CDISC named them. Deriving a catalogue and an
    effective date from a title is the caller's job, because that convention is shared
    with the upload path and must not have a second definition here.

    The key is the caller's own, supplied for this one call: it is deliberately not a
    setting, so it is never stored, and never outlives the request that carried it.

    Imported here rather than at module scope, as in `semantic_provider.http_chat_provider`:
    `httpx` is only needed by the paths that actually leave the process, and an
    installation that never calls discovery should not pay for it.
    """

    import httpx  # pylint: disable=import-outside-toplevel

    require_configured()

    with httpx.Client(
        base_url=settings.cdisc_api_base_url,
        headers=_headers(api_key),
        timeout=settings.cdisc_api_timeout_seconds,
    ) as client:
        response = client.get(PACKAGE_LIST_PATH)
        response.raise_for_status()
        payload = response.json()

    links = payload.get("_links") if isinstance(payload, dict) else None
    packages = (links or {}).get("packages") or []

    if not packages:
        # Not an error — but it is the shape of the answer changing under us, and the
        # release nobody discovered would look exactly like a release nobody published.
        log.warning(
            "The CDISC package list came back with no entries under `_links.packages`"
        )

    entries = [
        {
            "title": str(package.get("title") or ""),
            "href": str(package.get("href") or ""),
        }
        for package in packages
        if isinstance(package, dict) and package.get("title")
    ]
    log.info("Fetched %s published releases from the CDISC Library", len(entries))
    return entries


def fetch_package_content(href: str, api_key: str) -> bytes:
    """Fetches one CDISC package document, given the `href` `fetch_package_list` returned.

    Returned as raw bytes rather than parsed JSON: this is exactly the payload
    `staging_service.stage_package_file` accepts for a manual upload, and its digest has
    to be taken over the bytes CDISC actually served, not a lossy round-trip through a
    JSON parser and back. The caller decides whether and how to stage it.
    """

    import httpx  # pylint: disable=import-outside-toplevel

    require_configured()

    with httpx.Client(
        base_url=settings.cdisc_api_base_url,
        headers=_headers(api_key),
        timeout=settings.cdisc_api_timeout_seconds,
    ) as client:
        response = client.get(href)
        response.raise_for_status()
        return response.content
