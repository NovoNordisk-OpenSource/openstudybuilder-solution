"""One codelist or term as it stood in each of the last releases of a catalogue.

The package diff answers "what changed in this release"; this answers "how did this
concept get here" — the same attributes laid side by side across the releases leading up
to the one under review, so an edit can be read against what it replaced. Computed on
demand from the staged raw layer, like the diff; nothing is stored.
"""

from datetime import date
from itertools import pairwise
from typing import Any

from common.exceptions import NotFoundException
from standards_import.models.packages import (
    ConceptHistory,
    ConceptHistoryAttribute,
    ConceptHistoryCodelist,
    ConceptHistoryMembershipChange,
    ConceptHistoryRelease,
    ConceptType,
)
from standards_import.repositories import release_repository
from standards_import.repositories.staging_db import staging_session

DEFAULT_RELEASES = 5

# `ct_diff.CODELIST_FIELDS` and `TERM_FIELDS`, in the order a reviewer reads them. A
# term's submission value is not a property of the term but of its place in a codelist,
# so it is listed for terms too, as the values it has across the codelists holding it.
CODELIST_FIELDS = (
    "name",
    "preferredTerm",
    "submissionValue",
    "definition",
    "extensible",
    "synonyms",
)
TERM_FIELDS = ("preferredTerm", "submissionValue", "definition", "synonyms")


def _value(props: dict[str, Any], field: str) -> Any:
    raw = props.get(field)
    if field == "synonyms":
        return sorted(raw or [])
    if field == "extensible":
        return raw == "true"
    return raw


def _term_values(memberships: list[dict[str, Any]]) -> dict[str, Any]:
    """A term's attributes in one release; the term is the same under every codelist."""

    props = memberships[0]["term"]
    values = {field: _value(props, field) for field in TERM_FIELDS}
    submission_values = sorted(
        {
            row["term"].get("submissionValue")
            for row in memberships
            if row["term"].get("submissionValue")
        }
    )
    values["submissionValue"] = ", ".join(submission_values) or None
    return values


def _membership_changes(
    held: list[dict[str, str | None]],
) -> list[ConceptHistoryMembershipChange]:
    """Per release, the codelists entered and left since the one before it.

    `held[i]` maps the id of each codelist holding the term in release i to that
    codelist's submission value; empty for a release that does not hold the term.
    """

    changes = [ConceptHistoryMembershipChange()]
    for before, after in pairwise(held):
        changes.append(
            ConceptHistoryMembershipChange(
                entered=[
                    ConceptHistoryCodelist(concept_id=cid, submission_value=after[cid])
                    for cid in sorted(after.keys() - before.keys())
                ],
                left=[
                    ConceptHistoryCodelist(concept_id=cid, submission_value=before[cid])
                    for cid in sorted(before.keys() - after.keys())
                ],
            )
        )
    return changes


def get_concept_history(
    catalogue: str,
    effective_date: date,
    concept_type: ConceptType,
    concept_id: str,
    releases: int = DEFAULT_RELEASES,
) -> ConceptHistory:
    """The last `releases` releases of a catalogue, ending at `effective_date`.

    A release that does not hold the concept is kept, with null values, so a concept that
    was absent, removed or only just added shows as such rather than as a shorter list.
    The chain follows `HAS_PRIOR_VERSION`, so it is shorter where an earlier release was
    never staged. Raises when none of them holds the concept.
    """

    package_name = f"{catalogue} {effective_date}"
    is_term = concept_type == ConceptType.TERM

    with staging_session() as session:
        rows = (
            release_repository.get_term_history
            if is_term
            else release_repository.get_codelist_history
        )(session, package_name, concept_id, releases)

    if not rows or rows[-1]["package_name"] != package_name:
        raise NotFoundException(
            msg=f"No catalogue '{package_name}' is staged, so it has no history."
        )

    per_release: list[dict[str, Any] | None] = []
    held: list[dict[str, str | None]] = []
    for row in rows:
        if is_term:
            memberships = row["memberships"]
            per_release.append(_term_values(memberships) if memberships else None)
            held.append(
                {m["codelist_id"]: m["codelist_submission_value"] for m in memberships}
            )
        else:
            per_release.append(
                {field: _value(row["codelists"][0], field) for field in CODELIST_FIELDS}
                if row["codelists"]
                else None
            )

    if not any(per_release):
        raise NotFoundException(
            msg=f"{concept_type.value.capitalize()} '{concept_id}' is in none of the "
            f"last {len(rows)} releases of {catalogue} up to {effective_date}."
        )

    return ConceptHistory(
        catalogue=catalogue,
        concept_id=concept_id,
        concept_type=concept_type,
        releases=[
            ConceptHistoryRelease(
                package_name=row["package_name"],
                effective_date=row["effective_date"],
                present=values is not None,
                is_current=row["package_name"] == package_name,
                is_earliest_staged=not row["has_prior"],
            )
            for row, values in zip(rows, per_release)
        ],
        attributes=[
            ConceptHistoryAttribute(
                field=field,
                values=[values[field] if values else None for values in per_release],
            )
            for field in (TERM_FIELDS if is_term else CODELIST_FIELDS)
        ],
        membership_changes=_membership_changes(held) if is_term else None,
    )
