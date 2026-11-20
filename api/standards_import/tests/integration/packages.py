"""Small, readable CDISC packages built in the test rather than loaded from disk.

The real files run to megabytes; these carry exactly the shapes under test — an agreed
codelist, a disputed property, a term set the catalogues differ on, a quoted value.
"""

import json
from typing import Any


def term(
    concept_id: str,
    submission_value: str,
    preferred_term: str | None = None,
    definition: str = "A term.",
    synonyms: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "conceptId": concept_id,
        "submissionValue": submission_value,
        "preferredTerm": preferred_term or f"Term {concept_id}",
        "definition": definition,
        "synonyms": synonyms if synonyms is not None else [],
    }


def codelist(
    concept_id: str,
    name: str,
    submission_value: str,
    terms: list[dict[str, Any]],
    definition: str = "A codelist.",
    extensible: str = "false",
    synonyms: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "conceptId": concept_id,
        "name": name,
        "submissionValue": submission_value,
        "definition": definition,
        "extensible": extensible,
        "preferredTerm": f"{name} Terminology",
        "synonyms": synonyms if synonyms is not None else [],
        "terms": terms,
    }


def package_href(catalogue: str, effective_date: str) -> str:
    """CDISC's own package URL, as `_links.self.href` carries it."""

    return f"/mdr/ct/packages/{catalogue.lower().replace(' ', '')}-{effective_date}"


def package(
    catalogue: str,
    effective_date: str,
    codelists: list[dict[str, Any]],
    prior_effective_date: str | None = None,
) -> bytes:
    """One catalogue file, as uploaded. The name must carry the effective date.

    `prior_effective_date` adds the `priorVersion` link CDISC uses to chain releases,
    which is what `raw_load_repository.link_prior_version` matches on — a test needing
    a diff has to supply it, because the predecessor is found through these links and
    not by comparing dates. It is off by default so that a test uninterested in the
    chain cannot accidentally acquire a predecessor.

    `self` is always written, since it is the other half of that match: the release
    being pointed *at* needs one even though it names no predecessor of its own. On its
    own it links nothing.
    """

    document: dict[str, Any] = {
        "name": f"{catalogue} {effective_date}",
        "effectiveDate": effective_date,
        "codelists": codelists,
        "_links": {"self": {"href": package_href(catalogue, effective_date)}},
    }
    if prior_effective_date:
        document["_links"]["priorVersion"] = {
            "href": package_href(catalogue, prior_effective_date)
        }
    return json.dumps(document).encode()
