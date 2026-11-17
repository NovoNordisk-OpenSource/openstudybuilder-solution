"""Groups one CDISC release, raises review items, and settles what it can.

Ported from the grouping and inconsistency steps of
`import_standards/cdisc_staging.py`, with the resolution half turned from code into
data — see `resolution_service`. Three detection differences from that script are
deliberate, each because the original loses information:

* a value quoted in *any* catalogue is reported. The original only ever inspected the
  first catalogue's values, so a quoted value elsewhere surfaced, if at all, as a plain
  disagreement.
* `name` and `extensible` take part in building the conflict detail. The original
  compared them when deciding a codelist was inconsistent but left them out of the
  detail, so a codelist differing only in those produced an empty finding — and, being
  neither consistent nor recorded, ended up with no grouped properties at all.
* every concept gets its properties written. The original wrote properties only for
  concepts that never disagreed, which left every conflicted codelist with nothing for
  the MDR import to read. Staging is a working area: it is filled in regardless, with
  settled values where there are any and the pecking order's pick where there are not.
  Open items hold up promotion to MDR, not staging.
"""

import json
import logging
import uuid
from datetime import date
from typing import Any

from common.auth.user import user
from common.exceptions import NotFoundException, ValidationException
from standards_import.models.inconsistencies import (
    ANALYSIS_TYPES,
    EntityType,
    InconsistencyStatus,
    InconsistencyType,
    ResolutionStrategy,
    build_inconsistency_uid,
)
from standards_import.models.jobs import Job, JobKind, JobStatus
from standards_import.models.packages import (
    AnalysisSummary,
    EffectiveDateStatus,
    InconsistencyCount,
)
from standards_import.repositories import (
    analysis_repository,
    inconsistency_repository,
    job_repository,
    mdr_repository,
    pairing_repository,
    rules_repository,
    staging_repository,
)
from standards_import.repositories.staging_db import staging_session, to_native
from standards_import.services import (
    job_service,
    resolution_service,
    review_snapshot_service,
)

log = logging.getLogger(__name__)

TERM_BATCH_SIZE = 1000
# A term-set disagreement needs at least two catalogues listing the codelist.
MIN_CATALOGUES_TO_COMPARE = 2

CODELIST_PROPERTIES = [
    "definition",
    "name",
    "preferredTerm",
    "synonyms",
    "submissionValue",
    "extensible",
]
TERM_PROPERTIES = ["definition", "preferredTerm", "synonyms"]
QUOTE_CHECKED_PROPERTIES = ["definition", "preferredTerm", "synonyms"]


def start_analysis(effective_date: date) -> Job:
    """Checks the release may be analysed and records a job to carry it out."""

    package_date = effective_date.isoformat()
    author_id = user().id()

    with staging_session() as session:
        release = staging_repository.find_effective_date(session, package_date)
        if release is None:
            raise NotFoundException(
                msg=f"No files have been staged for effective date '{package_date}'."
            )
        guard_analysable(release, package_date)
        # The mandatory-catalogues check reads seeded config, which `perform_analysis`
        # would otherwise only guarantee once the background job actually runs — too
        # late for a guard that has to raise before the job is even recorded.
        rules_repository.ensure_seed_data(session)
        guard_mandatory_catalogues_present(session, package_date)

        job_uid = uuid.uuid4().hex
        record = job_repository.start_job(
            session,
            job_uid,
            JobKind.ANALYSIS.value,
            package_date,
            author_id,
            status_while_running=EffectiveDateStatus.ANALYZING.value,
            # Null: `perform_analysis` already sets ANALYZED/BLOCKED itself on success,
            # via the same `set_analysis_outcome` call the old synchronous path made.
            status_on_success=None,
            # Not `previous_status`: the derived layer is cleared before anything else
            # runs, so a failed analysis has already invalidated whatever was there —
            # a full re-analysis is the only honest way back, the same as a release
            # that has only ever had files staged for it.
            status_on_failure=EffectiveDateStatus.FILES_STAGED.value,
        )

    ValidationException.raise_if(
        record is None,
        msg=f"Effective date '{package_date}' cannot start now because another step is already running against it.",
    )
    assert record is not None
    return job_service.job_to_model(record)


def guard_analysable(release: dict[str, Any], package_date: str) -> None:
    status = release["status"]
    ValidationException.raise_if(
        status
        in (EffectiveDateStatus.IMPORTING.value, EffectiveDateStatus.IMPORTED.value),
        msg=f"Effective date '{package_date}' has status '{status}'. "
        "Re-analysing it would discard the grouped properties that its imported "
        "version history refers to.",
    )
    ValidationException.raise_if(
        status
        in (EffectiveDateStatus.ANALYZING.value, EffectiveDateStatus.ASSESSING.value),
        msg=f"Effective date '{package_date}' has status '{status}'. Another step is "
        "already running against it — analysis would rebuild the same grouped layer "
        "that step is reading or writing. Wait for it to finish and try again.",
    )


def guard_mandatory_catalogues_present(session: Any, package_date: str) -> None:
    """Refuses to start analysis while a catalogue the organisation requires is missing.

    Presence-only, not an exact match — extra catalogues beyond the mandatory set are
    fine. This is a different check from `expected_catalogues` on the import request:
    that one is opt-in, per-call, and exact; this one is a standing, admin-configured
    default enforced on every analysis.
    """

    mandatory = set(rules_repository.get_mandatory_catalogues(session))
    if not mandatory:
        return
    staged = {
        analysis_repository.catalogue_name(name)
        for name in analysis_repository.get_catalogues(session, package_date)
    }
    missing = mandatory - staged
    ValidationException.raise_if(
        missing,
        msg=f"Effective date '{package_date}' is missing mandatory catalogues: "
        f"{sorted(missing)}. Upload the remaining package files before running "
        "analysis.",
    )


def run_analysis(job_uid: str, effective_date: date) -> None:
    """Analyses a release. Runs in the background; failures land on the job.

    No `author_id`: unlike an import or a decision, nothing analysis does is
    attributed to a person — it is a system pass over what was uploaded.
    """

    package_date = effective_date.isoformat()
    try:
        summary = perform_analysis(effective_date)
        with staging_session() as session:
            job_repository.finish_job(
                session,
                job_uid,
                JobStatus.SUCCEEDED.value,
                stats={
                    "grouped_codelist_count": summary.grouped_codelist_count,
                    "grouped_term_count": summary.grouped_term_count,
                    "open_inconsistency_count": summary.open_inconsistency_count,
                },
            )
        log.info(
            "Analysis %s of %s finished: %s", job_uid, package_date, summary.status
        )
    except Exception as exc:  # pylint: disable=broad-except
        log.exception("Analysis %s of %s failed", job_uid, package_date)
        with staging_session() as session:
            job_repository.finish_job(
                session, job_uid, JobStatus.FAILED.value, error=str(exc)
            )


def get_summary(effective_date: date) -> AnalysisSummary:
    """The last analysis of a release, rebuilt from what it stored."""

    package_date = effective_date.isoformat()
    with staging_session() as session:
        release = staging_repository.find_effective_date(session, package_date)
        if release is None:
            raise NotFoundException(
                msg=f"No files have been staged for effective date '{package_date}'."
            )
        NotFoundException.raise_if(
            release.get("analyzed_at") is None,
            msg=f"Effective date '{package_date}' has not been analysed yet. Run "
            f"POST /effective-dates/{package_date}/analysis.",
        )
        catalogues = analysis_repository.get_catalogues(session, package_date)
        concept_counts = analysis_repository.count_grouped_concepts(
            session, package_date
        )
        inconsistencies = summarise(
            inconsistency_repository.count_by_type_and_status(session, package_date)
        )

    return AnalysisSummary(
        effective_date=effective_date,
        status=EffectiveDateStatus(release["status"]),
        analyzed_at=to_native(release["analyzed_at"]),
        catalogues=catalogues,
        grouped_codelist_count=concept_counts["codelist_count"],
        grouped_term_count=concept_counts["term_count"],
        inconsistencies=inconsistencies,
        open_inconsistency_count=release.get("open_inconsistency_count") or 0,
    )


def perform_analysis(effective_date: date) -> AnalysisSummary:
    """Groups and checks one release, keeping decisions already made about it.

    Assumes the caller already checked the release can be analysed — see
    `start_analysis`/`guard_analysable`. Not called directly from a route: reached
    through `run_analysis`, the background job's own work.
    """

    package_date = effective_date.isoformat()
    run_id = uuid.uuid4().hex

    with staging_session() as session:
        rules_repository.ensure_seed_data(session)

        rules = rules_repository.get_rules(session, enabled_only=True)
        catalogue_priority = [
            row["catalogue_name"]
            for row in rules_repository.get_catalogue_priority(session)
        ]

        log.info("Analysing effective date %s (run %s)", package_date, run_id)
        analysis_repository.clear_derived_layer(session, package_date)
        group_release(session, package_date)

        findings, baselines = collect_findings(
            session, package_date, catalogue_priority
        )
        inconsistency_repository.upsert_findings(
            session, package_date, run_id, findings
        )
        pruned = inconsistency_repository.prune_findings(
            session, package_date, run_id, sorted(ANALYSIS_TYPES)
        )
        if pruned:
            log.info("%s review items no longer apply and were dropped", pruned)

        auto_resolve(session, package_date, findings, rules, catalogue_priority)
        inconsistency_repository.link_findings_to_concepts(session, package_date)
        apply_resolutions(session, package_date, baselines)
        # After the resolutions, which write the grouped properties the delta reads, and
        # before the outcome, so a release reads as analysed only once it is there.
        review_snapshot_service.rebuild(session, package_date)

        catalogues = analysis_repository.get_catalogues(session, package_date)
        concept_counts = analysis_repository.count_grouped_concepts(
            session, package_date
        )
        inconsistencies = summarise(
            inconsistency_repository.count_by_type_and_status(session, package_date)
        )
        open_count = sum(item.open for item in inconsistencies)

        status = (
            EffectiveDateStatus.BLOCKED if open_count else EffectiveDateStatus.ANALYZED
        )
        outcome = staging_repository.set_analysis_outcome(
            session, package_date, status.value, open_count
        )

    log.info(
        "Analysed %s: %s codelists, %s terms, %s review items (%s open)",
        package_date,
        concept_counts["codelist_count"],
        concept_counts["term_count"],
        sum(item.total for item in inconsistencies),
        open_count,
    )

    return AnalysisSummary(
        effective_date=effective_date,
        status=status,
        analyzed_at=to_native(outcome["analyzed_at"]),
        catalogues=catalogues,
        grouped_codelist_count=concept_counts["codelist_count"],
        grouped_term_count=concept_counts["term_count"],
        inconsistencies=inconsistencies,
        open_inconsistency_count=open_count,
    )


def group_release(session, package_date: str) -> None:
    """Collapses the per-catalogue definitions of this release into grouped nodes."""

    codelist_cids = analysis_repository.get_codelist_cids(session, package_date)
    analysis_repository.create_grouped_codelists(session, package_date, codelist_cids)

    start = 0
    while True:
        term_cids = analysis_repository.get_term_cids(
            session, package_date, start, TERM_BATCH_SIZE
        )
        start += len(term_cids)
        if term_cids:
            analysis_repository.create_grouped_terms(session, package_date, term_cids)
        if len(term_cids) < TERM_BATCH_SIZE:
            break

    for codelist_cid in codelist_cids:
        analysis_repository.add_grouped_codelist_terms(
            session, package_date, codelist_cid
        )


def collect_findings(
    session, package_date: str, catalogue_priority: list[str]
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Compares the catalogues and returns the findings plus each concept's baseline.

    The baseline is the value set a concept would get if nothing were disputed. Where
    catalogues disagree it holds the pecking order's pick, so a concept always has a
    complete set of values even if a reviewer ends up choosing IGNORE.
    """

    findings: list[dict[str, Any]] = []
    baselines: dict[str, dict[str, Any]] = {"CODELIST": {}, "TERM": {}}

    for codelist in analysis_repository.get_codelist_properties(session, package_date):
        raw_defs, catalogues = codelist["raw_defs"], codelist["raw_cats"]
        if not raw_defs:
            continue

        concept_findings, baseline = compare_concept(
            package_date,
            EntityType.CODELIST,
            codelist["cid"],
            raw_defs,
            catalogues,
            CODELIST_PROPERTIES,
            catalogue_priority,
        )
        findings.extend(concept_findings)
        baselines["CODELIST"][codelist["cid"]] = baseline

        term_set_finding = compare_term_sets(
            package_date, codelist["cid"], codelist["cl_terms"], catalogues
        )
        if term_set_finding:
            findings.append(term_set_finding)

    start = 0
    while True:
        terms = analysis_repository.get_term_properties(
            session, package_date, start, TERM_BATCH_SIZE
        )
        start += len(terms)
        for term in terms:
            raw_defs, catalogues = term["raw_defs"], term["raw_cats"]
            if not raw_defs:
                continue
            concept_findings, baseline = compare_concept(
                package_date,
                EntityType.TERM,
                term["cid"],
                raw_defs,
                catalogues,
                TERM_PROPERTIES,
                catalogue_priority,
            )
            findings.extend(concept_findings)
            baselines["TERM"][term["cid"]] = baseline
        if len(terms) < TERM_BATCH_SIZE:
            break

    findings.extend(collect_submission_value_findings(session, package_date))
    findings.extend(collect_pairing_findings(session, package_date, baselines))
    findings.extend(collect_sponsor_name_findings(session, package_date, baselines))
    return findings, baselines


def collect_pairing_findings(
    session, package_date: str, baselines: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Proposes which code codelist each name codelist pairs with.

    Taken from the paired-view spreadsheets uploaded with the release, not guessed from
    the data: the submission values usually imply the pairing but not reliably enough to
    depend on. A release with no spreadsheet simply gets no pairing items, and its
    codelists stay unpaired.

    Only codelists MDR has not already paired are considered, so a pairing decided once
    does not come back every quarter. Where the spreadsheets name more than one partner
    for the same codelist the ambiguity is left for a reviewer.
    """

    pairings = pairing_repository.get_pairings(session, package_date)
    if not pairings:
        log.info("No codelist pairings uploaded for %s", package_date)
        return []

    in_release = set(baselines["CODELIST"])
    already_paired = mdr_repository.get_paired_codelists(sorted(in_release))

    partners: dict[str, list[str]] = {}
    for pairing in pairings:
        name_id, code_id = pairing["name_concept_id"], pairing["code_concept_id"]
        if name_id not in in_release or code_id not in in_release:
            continue
        if name_id in already_paired:
            continue
        if code_id not in partners.setdefault(name_id, []):
            partners[name_id].append(code_id)

    return [
        build_finding(
            package_date,
            InconsistencyType.CODELIST_PAIRING,
            EntityType.CODELIST,
            name_id,
            [{"value": code_id, "catalogues": []} for code_id in codes],
        )
        for name_id, codes in sorted(partners.items())
    ]


def collect_sponsor_name_findings(
    session, package_date: str, baselines: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Proposes what each term new to MDR should be called.

    A term's sponsor preferred name is sponsors' to choose, not CDISC's. The bootstrap script
    decides it with a hand-written cascade; here it is a review item settled by rules,
    defaulting to the CDISC preferred term.

    Raised only for terms MDR does not already hold: the name of an existing term is the
    sponsor's to edit, and the import never overwrites it.

    This is the one place analysis consults MDR. Sponsor naming is an MDR-facing
    question, and asking here keeps every review item in one queue.
    """

    term_ids = list(baselines["TERM"])
    if not term_ids:
        return []

    known = mdr_repository.get_existing_term_uids(term_ids)
    codelists_by_term = analysis_repository.get_codelists_by_term(session, package_date)

    findings = []
    for term_id in sorted(set(term_ids) - known):
        preferred_term = (baselines["TERM"].get(term_id) or {}).get("preferredTerm")
        if not preferred_term:
            continue
        finding = build_finding(
            package_date,
            InconsistencyType.SPONSOR_NAME,
            EntityType.TERM,
            term_id,
            [{"value": preferred_term, "catalogues": []}],
        )
        memberships = sorted(
            codelists_by_term.get(term_id, []), key=lambda m: m["codelist_id"]
        )
        # Kept as two aligned lists rather than a map: Neo4j cannot hold a map as a
        # node property, and zipping them back together is a one-liner where needed.
        finding["codelist_ids"] = [m["codelist_id"] for m in memberships]
        finding["submission_values"] = [m["submission_value"] for m in memberships]
        findings.append(finding)
    return findings


def compare_concept(
    package_date: str,
    entity_type: EntityType,
    concept_id: str,
    raw_defs: list[dict[str, Any]],
    catalogues: list[dict[str, Any]],
    properties: list[str],
    catalogue_priority: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Compares every catalogue's take on one concept, property by property."""

    findings = []
    baseline: dict[str, Any] = {}

    for prop in properties:
        candidates = build_candidates(raw_defs, catalogues, prop)
        baseline[prop] = choose_baseline(candidates, catalogue_priority)

        if len(candidates) > 1:
            findings.append(
                build_finding(
                    package_date,
                    InconsistencyType.CONFLICTING_VALUES,
                    entity_type,
                    concept_id,
                    candidates,
                    property_name=prop,
                )
            )

        if prop in QUOTE_CHECKED_PROPERTIES and any(
            is_quoted(candidate["value"]) for candidate in candidates
        ):
            findings.append(
                build_finding(
                    package_date,
                    InconsistencyType.UNWANTED_QUOTES,
                    entity_type,
                    concept_id,
                    candidates,
                    property_name=prop,
                )
            )

    return findings, baseline


def compare_term_sets(
    package_date: str,
    codelist_cid: str,
    codelist_terms: list[dict[str, str]],
    catalogues: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Reports catalogues that disagree on which terms a codelist contains.

    Submission values are compared with quotes stripped, so a merely quoted value is
    left to the submission-value check rather than counted as a different term set.
    """

    if len(codelist_terms) < MIN_CATALOGUES_TO_COMPARE:
        return None

    signatures = [
        {f"{cid}:{strip_unwanted_quotes(submval)}" for cid, submval in terms.items()}
        for terms in codelist_terms
    ]
    if all(signature == signatures[0] for signature in signatures[1:]):
        return None

    shared = set.intersection(*signatures)
    candidates = []
    for signature, catalogue in zip(signatures, catalogues):
        candidates.append(
            {
                "value": sorted(signature - shared),
                "catalogues": [catalogue["name"]],
            }
        )

    return build_finding(
        package_date,
        InconsistencyType.INCONSISTENT_TERM_SETS,
        EntityType.CODELIST,
        codelist_cid,
        merge_candidates(candidates),
    )


def collect_submission_value_findings(
    session, package_date: str
) -> list[dict[str, Any]]:
    """Reports term submission values that are disputed between catalogues, or quoted."""

    findings = []
    for row in analysis_repository.get_submission_value_conflicts(
        session, package_date
    ):
        candidates = merge_candidates(
            [
                {
                    "value": entry["submission_value"],
                    "catalogues": [entry["catalogue"]],
                }
                for entry in row["entries"]
            ]
        )
        values = [candidate["value"] for candidate in candidates]
        finding_type = (
            InconsistencyType.CONFLICTING_SUBMISSION_VALUES
            if len(candidates) > 1
            else InconsistencyType.UNWANTED_QUOTES
        )
        if len(candidates) == 1 and not is_quoted(values[0]):
            continue
        findings.append(
            build_finding(
                package_date,
                finding_type,
                EntityType.CODELIST,
                row["codelist_cid"],
                candidates,
                related_concept_id=row["term_cid"],
            )
        )
    return findings


def build_finding(
    package_date: str,
    finding_type: InconsistencyType,
    entity_type: EntityType,
    concept_id: str,
    candidates: list[dict[str, Any]],
    property_name: str | None = None,
    related_concept_id: str | None = None,
) -> dict[str, Any]:
    return {
        "uid": build_inconsistency_uid(
            package_date,
            entity_type,
            concept_id,
            finding_type,
            property_name=property_name,
            related_concept_id=related_concept_id,
        ),
        "effective_date": package_date,
        "type": finding_type.value,
        "entity_type": entity_type.value,
        "concept_id": concept_id,
        "related_concept_id": related_concept_id,
        "property": property_name,
        "match_tier": None,
        "usage_count": None,
        "candidates": candidates,
        "codelist_ids": [],
        "submission_values": [],
        "fingerprint": resolution_service.candidate_fingerprint(candidates),
        "initial_status": InconsistencyStatus.OPEN.value,
    }


def build_candidates(
    raw_defs: list[dict[str, Any]],
    catalogues: list[dict[str, Any]],
    prop: str,
) -> list[dict[str, Any]]:
    """Groups the catalogues by the value each gave for one property."""

    return merge_candidates(
        [
            {"value": raw_def.get(prop), "catalogues": [catalogue["name"]]}
            for raw_def, catalogue in zip(raw_defs, catalogues)
        ]
    )


def merge_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapses candidates that carry the same value, keeping first-seen order."""

    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for candidate in candidates:
        key = json.dumps(candidate["value"], sort_keys=True)
        if key not in merged:
            merged[key] = {"value": candidate["value"], "catalogues": []}
            order.append(key)
        merged[key]["catalogues"].extend(candidate["catalogues"])
    return [merged[key] for key in order]


def choose_baseline(
    candidates: list[dict[str, Any]], catalogue_priority: list[str]
) -> Any:
    """Picks the value a concept gets before any decision is applied."""

    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]["value"]

    winner = resolution_service.preferred_by_catalogue(
        {"candidates": candidates}, catalogue_priority
    )
    if winner:
        for candidate in candidates:
            if winner in candidate["catalogues"]:
                return candidate["value"]
    return candidates[0]["value"]


def auto_resolve(
    session,
    package_date: str,
    findings: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    catalogue_priority: list[str],
) -> None:
    """Settles every undecided finding that a rule or the pecking order can settle."""

    undecided = set(
        inconsistency_repository.get_undecided(
            session, package_date, sorted(ANALYSIS_TYPES)
        )
    )
    if not undecided:
        return

    decisions = []
    for finding in findings:
        if finding["uid"] not in undecided:
            continue
        outcome = resolution_service.auto_resolve(finding, rules, catalogue_priority)
        if outcome is None:
            continue
        status, decision = outcome
        decisions.append(
            {"uid": finding["uid"], "status": status.value, "decision": decision}
        )

    inconsistency_repository.record_decisions(session, decisions)
    log.info(
        "%s of %s undecided review items settled automatically",
        len(decisions),
        len(undecided),
    )


def apply_resolutions(
    session, package_date: str, baselines: dict[str, dict[str, Any]]
) -> None:
    """Writes every concept's properties, and applies structural decisions.

    Staging is written in full, including concepts whose disagreements are still open —
    those simply keep the pecking order's pick until somebody decides otherwise. What
    open items hold up is promotion to MDR, not staging itself: the release stays
    `BLOCKED`, and the findings say exactly which concepts are provisional.
    """

    resolutions = inconsistency_repository.get_resolutions_for_date(
        session, package_date
    )

    overrides: dict[tuple[str, str, str], Any] = {}
    submission_values: list[dict[str, Any]] = []
    dropped_terms: list[dict[str, Any]] = []

    for resolution in resolutions:
        strategy = resolution.get("strategy")
        if strategy == ResolutionStrategy.DROP_TERM_FROM_CODELIST.value:
            # The strategy resolves to the term id: the one the finding names, or the
            # one the rule supplied where the finding is about the codelist as a whole.
            term_cid = resolution.get("resolved_value") or resolution.get(
                "related_concept_id"
            )
            if term_cid:
                dropped_terms.append(
                    {
                        "codelist_cid": resolution["concept_id"],
                        "term_cid": term_cid,
                    }
                )
            continue

        resolved = resolution.get("resolved_value")
        if resolved is None:
            continue

        if resolution["type"] in (
            InconsistencyType.CONFLICTING_SUBMISSION_VALUES.value,
            InconsistencyType.UNWANTED_QUOTES.value,
        ) and resolution.get("related_concept_id"):
            submission_values.append(
                {
                    "codelist_cid": resolution["concept_id"],
                    "term_cid": resolution["related_concept_id"],
                    "submission_value": resolved,
                }
            )
            continue

        if resolution.get("property"):
            cell = (
                resolution["entity_type"],
                resolution["concept_id"],
                resolution["property"],
            )
            # A property can be both disputed and quoted, so two findings can settle the
            # same value. The order is stable (by finding uid), but only one wins, and
            # which one is not obvious from either decision — so say so.
            if cell in overrides and overrides[cell] != resolved:
                log.warning(
                    "Two resolutions set %s of %s %s to different values; keeping the "
                    "later one (%r over %r). Settle both the same way to be sure.",
                    cell[2],
                    cell[0],
                    cell[1],
                    resolved,
                    overrides[cell],
                )
            overrides[cell] = resolved

    codelist_rows = build_property_rows(
        package_date, EntityType.CODELIST, baselines["CODELIST"], overrides
    )
    term_rows = build_property_rows(
        package_date, EntityType.TERM, baselines["TERM"], overrides
    )

    analysis_repository.save_codelist_properties(session, codelist_rows)
    analysis_repository.save_term_properties(session, term_rows)
    analysis_repository.set_grouped_submission_value(
        session, package_date, submission_values
    )
    analysis_repository.drop_terms_from_codelists(session, package_date, dropped_terms)


def build_property_rows(
    package_date: str,
    entity_type: EntityType,
    baselines: dict[str, dict[str, Any]],
    overrides: dict[tuple[str, str, str], Any],
) -> list[dict[str, Any]]:
    """Builds the property rows to write, one per concept.

    Settled values replace the baseline; anything still open keeps the baseline, which
    is the pecking order's pick rather than an arbitrary catalogue's.
    """

    key = "cl_props" if entity_type is EntityType.CODELIST else "term_props"
    cid_key = "codelist_cid" if entity_type is EntityType.CODELIST else "term_cid"

    rows = []
    for concept_id, baseline in baselines.items():
        properties = dict(baseline)
        for prop in list(properties):
            override = overrides.get((entity_type.value, concept_id, prop))
            if override is not None:
                properties[prop] = override
        rows.append(
            {"package_date": package_date, cid_key: concept_id, key: properties}
        )
    return rows


def strip_unwanted_quotes(value: str) -> str:
    return value.strip('"').replace('""', '"')


def is_quoted(value: Any) -> bool:
    """Reports whether a property value arrived wrapped in double quotes.

    A list is quoted when its first entry opens and its last entry closes, which is how
    a quoted block of synonyms shows up once split.
    """

    if isinstance(value, str):
        return value.startswith('"') and value.endswith('"')
    if isinstance(value, list) and value:
        first, last = value[0], value[-1]
        return (
            isinstance(first, str)
            and isinstance(last, str)
            and first.startswith('"')
            and last.endswith('"')
        )
    return False


def summarise(records: list[dict[str, Any]]) -> list[InconsistencyCount]:
    """Folds the stored findings into per-type counts for the response."""

    status_fields = {
        InconsistencyStatus.OPEN.value: "open",
        InconsistencyStatus.AUTO_RESOLVED.value: "auto_resolved",
        InconsistencyStatus.RESOLVED.value: "resolved",
        InconsistencyStatus.IGNORED.value: "ignored",
        InconsistencyStatus.INFORMATIONAL.value: "informational",
        InconsistencyStatus.ACKNOWLEDGED.value: "acknowledged",
    }

    counts: dict[str, dict[str, int]] = {}
    for record in records:
        bucket = counts.setdefault(
            record["type"],
            {
                "total": 0,
                "open": 0,
                "auto_resolved": 0,
                "resolved": 0,
                "ignored": 0,
                "informational": 0,
                "acknowledged": 0,
            },
        )
        bucket["total"] += record["count"]
        field = status_fields.get(record["status"])
        if field:
            bucket[field] += record["count"]

    return [
        InconsistencyCount(type=InconsistencyType(finding_type), **bucket)
        for finding_type, bucket in sorted(counts.items())
    ]
