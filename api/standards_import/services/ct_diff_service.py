"""Diffs one staged catalogue against the previous release of the same catalogue.

Computed on demand from the raw layer already in staging — nothing here is persisted.
A diff is a pure function of two already-stored snapshots, so there is nothing to keep
in sync and no versioning-model question to answer.

Where a terminology-changes spreadsheet has been uploaded for the release, each change
also carries the changelog entries explaining it (`domain.changelog_match`). That is
annotation only: it cannot change which changes are found or how they are banded, and a
missing, partial or unmatched changelog costs the diff nothing.
"""

import logging
from collections import defaultdict
from datetime import date
from typing import Any

from common.exceptions import NotFoundException
from standards_import.domain import changelog_match, ct_diff
from standards_import.models.packages import (
    PackageDiffBand,
    PackageDiffBandCount,
    PackageDiffReport,
    PackageDiffSummary,
    PreviousReleaseInfo,
)
from standards_import.repositories import (
    changelog_repository,
    release_repository,
    staging_repository,
)
from standards_import.repositories.staging_db import StagingSession, staging_session
from standards_import.services.changelog_service import to_models

log = logging.getLogger(__name__)


# `ct_diff.SEVERITIES`: "Terms removed from the catalogue".
REMOVED_TERMS_LEVEL = 2


def _normalize_codelist(props: dict[str, Any]) -> dict[str, Any]:
    return {
        "conceptId": props["conceptId"],
        "name": props.get("name"),
        "definition": props.get("definition"),
        "preferredTerm": props.get("preferredTerm"),
        "submissionValue": props.get("submissionValue"),
        "extensible": props.get("extensible") == "true",
        "synonyms": frozenset(props.get("synonyms") or []),
    }


def _normalize_term(props: dict[str, Any]) -> dict[str, Any]:
    return {
        "conceptId": props["conceptId"],
        "definition": props.get("definition"),
        "preferredTerm": props.get("preferredTerm"),
        "synonyms": frozenset(props.get("synonyms") or []),
    }


def _normalize_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    """Turns one `get_raw_catalogue_snapshot` record into the shape `ct_diff` expects.

    Mirrors `import_standards`' `normalize_package`: terms are deduplicated
    catalogue-wide by conceptId, and each (codelist, term) pair becomes one
    membership carrying that term's submission value in this codelist.
    """

    codelists = {}
    terms = {}
    memberships = {}

    for props in record["codelists"]:
        codelist = _normalize_codelist(props)
        codelists[codelist["conceptId"]] = codelist

    for row in record["terms"]:
        term_props = row["term"]
        term = _normalize_term(term_props)
        terms[term["conceptId"]] = term
        memberships[(row["codelist_id"], term["conceptId"])] = term_props.get(
            "submissionValue"
        )

    return {"codelists": codelists, "terms": terms, "memberships": memberships}


def _convert(value: Any) -> Any:
    """Makes `band_changes`' output JSON-safe (frozensets, tuples) for the response model."""

    if isinstance(value, frozenset | set):
        return sorted(value)
    if isinstance(value, tuple):
        return [_convert(item) for item in value]
    if isinstance(value, dict):
        return {key: _convert(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_convert(item) for item in value]
    return value


def get_previous_release(catalogue: str, effective_date: date) -> PreviousReleaseInfo:
    """Resolves which release a diff would compare against, without computing it.

    A single relationship lookup, unlike `get_package_diff` which also walks every
    codelist and term of both catalogues — meant to let the frontend show what it is
    about to compare against before that heavier call returns.
    """

    package_name = f"{catalogue} {effective_date}"

    with staging_session() as session:
        prior = release_repository.find_prior_catalogue(session, package_name)

    if prior is None:
        return PreviousReleaseInfo(previous_available=False)

    return PreviousReleaseInfo(
        previous_available=True,
        previous_package_name=prior["package_name"],
        previous_effective_date=prior["effective_date"],
    )


def _band_changes(
    session: StagingSession, current: dict[str, Any], previous_package_name: str
) -> dict[int, list[dict[str, Any]]]:
    """Every change between a staged catalogue and its predecessor, by severity band."""

    previous = release_repository.get_raw_catalogue_snapshot(
        session, previous_package_name
    )
    if previous is None:
        raise NotFoundException(
            msg=f"No catalogue '{previous_package_name}' is staged, so it cannot be diffed."
        )

    old_snapshot = _normalize_snapshot(previous)
    new_snapshot = _normalize_snapshot(current)

    pair_diff = ct_diff.diff_package_pair(old_snapshot, new_snapshot)
    bands = ct_diff.band_changes(pair_diff, ct_diff.extensible_codelists(old_snapshot))
    _merge_removed_term_memberships(bands)
    _add_submission_values(bands, old_snapshot, new_snapshot)
    return bands


def _merge_removed_term_memberships(bands: dict[int, list[dict[str, Any]]]) -> None:
    """Folds, in place, the memberships a removed term leaves into the term's own row.

    `ct_diff` bands a term removed from the catalogue twice over: once as the term, and
    once per codelist that held it. Both are in the same band, so the band listed the
    term without a codelist and then again with each — the same event several times,
    counted as many. Here it is one change per term, carrying `codelists`: the concept
    ids of every codelist it left.

    A membership whose term was not itself removed cannot be in this band, but is kept
    as it was rather than dropped should that ever stop being so.
    """

    band = bands[REMOVED_TERMS_LEVEL]
    left_by_term: dict[str, list[dict[str, Any]]] = defaultdict(list)
    kept = []
    for change in band:
        if change["kind"] == "membership_removed":
            left_by_term[change["key"][1]].append(change)
        else:
            kept.append(change)

    for change in kept:
        if change["kind"] == "term_removed":
            memberships = left_by_term.pop(change["term"]["conceptId"], [])
            change["codelists"] = sorted(m["key"][0] for m in memberships)

    bands[REMOVED_TERMS_LEVEL] = kept + [
        membership
        for memberships in left_by_term.values()
        for membership in memberships
    ]


def _values_by_term(
    memberships: dict[tuple[str, str], Any],
) -> dict[str, dict[str, Any]]:
    by_term: dict[str, dict[str, Any]] = defaultdict(dict)
    for (codelist_id, term_id), submission_value in memberships.items():
        by_term[term_id][codelist_id] = submission_value
    return by_term


def _stays_in(
    old_by_term: dict[str, dict[str, Any]],
    new_by_term: dict[str, dict[str, Any]],
    term_id: str,
) -> list[str]:
    """Concept ids of the codelists holding a term in both releases."""

    return sorted(
        old_by_term.get(term_id, {}).keys() & new_by_term.get(term_id, {}).keys()
    )


def _add_submission_values(
    bands: dict[int, list[dict[str, Any]]],
    old_snapshot: dict[str, Any],
    new_snapshot: dict[str, Any],
) -> None:
    """Names, in submission values, the terms and codelists a change is about.

    A codelist carries its own submission value, but a term's exists only inside a
    codelist, so a change that names a term or a membership by concept id alone says
    little to a reviewer. Adds, in place:

    - `term_submission_values` to every term and membership change: the term's value in
      the codelist concerned, or every distinct value it has when the change is about the
      term as a whole. Read from the release the change leaves the term in — the previous
      one for a removal.
    - `codelist_submission_values` (`{codelist concept id: value}`) to every change that
      names codelists other than the one it embeds: membership changes and moves.
    - `term_name` to every membership change and move, which name the term by its
      concept id alone: the term's preferred term, from the later release holding it.
    - `stays_in` to every membership addition or removal and every move: the codelists
      holding the term both before and after, so a reviewer sees what it leaves or enters
      against where it remains. Their submission values are in `codelist_submission_values`
      too.
    """

    codelist_values = {
        codelist_id: codelist["submissionValue"]
        for snapshot in (old_snapshot, new_snapshot)
        for codelist_id, codelist in snapshot["codelists"].items()
    }
    term_names = {
        term_id: term["preferredTerm"]
        for snapshot in (old_snapshot, new_snapshot)
        for term_id, term in snapshot["terms"].items()
    }
    old_by_term = _values_by_term(old_snapshot["memberships"])
    new_by_term = _values_by_term(new_snapshot["memberships"])

    def distinct(values):
        return sorted({value for value in values if value})

    for changes in bands.values():
        for change in changes:
            kind = change["kind"]
            if kind in ("term_added", "term_changed"):
                term_id = change["term"]["conceptId"]
                change["term_submission_values"] = distinct(
                    new_by_term[term_id].values()
                )
            elif kind == "term_removed":
                term_id = change["term"]["conceptId"]
                change["term_submission_values"] = distinct(
                    old_by_term[term_id].values()
                )
                change["codelist_submission_values"] = {
                    codelist_id: codelist_values.get(codelist_id)
                    for codelist_id in change.get("codelists", [])
                }
            elif kind in (
                "membership_added",
                "membership_removed",
                "membership_changed",
            ):
                memberships = (
                    old_snapshot["memberships"]
                    if kind == "membership_removed"
                    else new_snapshot["memberships"]
                )
                codelist_id, term_id = change["key"]
                change["term_name"] = term_names.get(term_id)
                change["term_submission_values"] = distinct(
                    [memberships.get(tuple(change["key"]))]
                )
                involved = [codelist_id]
                if kind != "membership_changed":
                    change["stays_in"] = _stays_in(old_by_term, new_by_term, term_id)
                    involved += change["stays_in"]
                change["codelist_submission_values"] = {
                    involved_id: codelist_values.get(involved_id)
                    for involved_id in involved
                }
            elif kind == "term_moved":
                move = change["move"]
                change["term_name"] = term_names.get(move["conceptId"])
                entered = new_by_term[move["conceptId"]]
                change["term_submission_values"] = distinct(
                    entered.get(codelist_id) for codelist_id in move["entered"]
                )
                change["stays_in"] = _stays_in(
                    old_by_term, new_by_term, move["conceptId"]
                )
                change["codelist_submission_values"] = {
                    codelist_id: codelist_values.get(codelist_id)
                    for codelist_id in [
                        *move["left"],
                        *move["entered"],
                        *change["stays_in"],
                    ]
                }


def get_diff_summaries(effective_date: date) -> list[PackageDiffSummary]:
    """Counts per severity band for every catalogue staged under one effective date.

    The same bands `get_package_diff` returns, counted rather than listed, for all of a
    release's catalogues in one call. That is what a reviewer needs to decide which
    catalogue to look at: a release spans several, and each full diff is both a large
    response and a separate round trip.

    Cheaper to send and to consume, not cheaper to compute — the graph work is the same
    walk of both releases per catalogue, and the changes are still all built before being
    counted. What it does save is carrying them back, matching a changelog onto them, and
    holding them all in a browser at once.

    A catalogue with nothing to compare against is reported with `previous_available`
    false and no bands rather than left out, so the caller can say so per card instead of
    silently showing fewer catalogues than were uploaded.
    """

    summaries = []

    with staging_session() as session:
        files = staging_repository.get_staged_files(
            session, effective_date=effective_date.isoformat()
        )

        for file in files:
            catalogue = file["catalogue"]
            package_name = file["package_name"]

            current = release_repository.get_raw_catalogue_snapshot(
                session, package_name
            )
            prior = (
                release_repository.find_prior_catalogue(session, package_name)
                if current is not None
                else None
            )

            if current is None or prior is None:
                summaries.append(
                    PackageDiffSummary(
                        catalogue=catalogue,
                        effective_date=effective_date,
                        previous_available=False,
                    )
                )
                continue

            bands = _band_changes(session, current, prior["package_name"])
            changelog_entries = changelog_repository.count_changelog_for_catalogue(
                session, str(effective_date), package_name
            )

            summaries.append(
                PackageDiffSummary(
                    catalogue=catalogue,
                    effective_date=effective_date,
                    previous_available=True,
                    previous_package_name=prior["package_name"],
                    previous_effective_date=prior["effective_date"],
                    changelog_available=changelog_entries > 0,
                    total_changes=sum(len(changes) for changes in bands.values()),
                    bands=[
                        PackageDiffBandCount(
                            level=level,
                            label=ct_diff.SEVERITIES[level],
                            count=len(changes),
                        )
                        for level, changes in bands.items()
                        if changes
                    ],
                )
            )

    return summaries


def _annotate(change: dict[str, Any], index: dict[str, Any] | None) -> dict[str, Any]:
    """One change, JSON-safe, carrying the changelog entries that explain it.

    The `changelog` key is left off entirely rather than set empty when nothing matches,
    so a consumer can tell "CDISC said nothing about this change" from "a changelog was
    never uploaded" — the latter is `changelog_available: false` on the report.
    """

    converted = _convert(change)
    if index is None:
        return converted

    entries = changelog_match.match_entries(index, change)
    if change["kind"] == "term_removed":
        # The row stands for the term leaving each of its codelists too, and the sheet
        # may describe it against any one of them.
        term_id = change["term"]["conceptId"]
        for codelist_id in change.get("codelists", []):
            entries += changelog_match.match_entries(
                index, {"kind": "membership_removed", "key": (codelist_id, term_id)}
            )
        entries = list({entry.get("uid"): entry for entry in entries}.values())
    if entries:
        converted["changelog"] = to_models(entries)
    return converted


def get_package_diff(
    catalogue: str, effective_date: date, include_changelog: bool = True
) -> PackageDiffReport:
    package_name = f"{catalogue} {effective_date}"

    with staging_session() as session:
        current = release_repository.get_raw_catalogue_snapshot(session, package_name)
        if current is None:
            raise NotFoundException(
                msg=f"No catalogue '{package_name}' is staged, so it cannot be diffed."
            )

        prior = release_repository.find_prior_catalogue(session, package_name)
        if prior is None:
            return PackageDiffReport(
                catalogue=catalogue,
                effective_date=effective_date,
                previous_available=False,
            )

        bands = _band_changes(session, current, prior["package_name"])

        # The changelog for release D describes the step D-1 -> D, which is exactly the
        # step being diffed, so it is the current release's entries that are wanted —
        # never the predecessor's.
        changelog_records = (
            changelog_repository.get_changelog_for_catalogue(
                session, str(effective_date), package_name
            )
            if include_changelog
            else []
        )

    index = (
        changelog_match.index_entries(changelog_records) if changelog_records else None
    )

    return PackageDiffReport(
        catalogue=catalogue,
        effective_date=effective_date,
        previous_available=True,
        previous_package_name=prior["package_name"],
        previous_effective_date=prior["effective_date"],
        changelog_available=bool(changelog_records),
        counts={level: len(changes) for level, changes in bands.items()},
        bands=[
            PackageDiffBand(
                level=level,
                label=ct_diff.SEVERITIES[level],
                changes=[_annotate(change, index) for change in changes],
            )
            for level, changes in bands.items()
            if changes
        ],
    )
