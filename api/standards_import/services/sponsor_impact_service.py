"""What a release would mean for the sponsor-defined content already in MDR.

The preview answers "what does this release change in CDISC terms?". This answers the
question it cannot: the sponsor has been coining codelists and terms of their own, and a
CDISC release can land on top of one. Three ways it can:

* a term this release adds to a codelist means the same as a sponsor term already in it;
* a codelist this release introduces covers the same ground as a sponsor codelist;
* CDISC changes a term whose sponsor name is no longer what the naming rules would give.

The first is the one with teeth. The main API requires a term's name to be unique among
the terms of the codelists it belongs to, and nothing in this app's Cypher enforces
that — so an exact collision imports quietly and leaves a codelist the main API will
then refuse to edit. Those findings are left open until somebody settles them, which is
the whole reason this step exists as a gate rather than a report.

**Why this is a separate run and not part of `analyse`.** Analysis is run over and over
around the review loop; this reads MDR heavily and, in time, will ask a language model.
The two also answer different questions — analysis says what the release *says*, this
says what it *means here* — and it can only run once analysis has settled everything,
because the name it compares is the name the review items settled, not the one CDISC
shipped.

Findings land in the same store as analysis's and are settled through the same endpoints
and the same rules. What is new is a producer of findings, not a second review system.
The two passes prune only their own kinds; see `ANALYSIS_TYPES` and
`SPONSOR_IMPACT_TYPES`.
"""

import logging
import uuid
from datetime import date
from typing import Any

from common.auth.user import user
from common.exceptions import NotFoundException, ValidationException
from standards_import.config import settings
from standards_import.models.inconsistencies import (
    ANALYSIS_TYPES,
    FROM_LANGUAGE_MODEL,
    FROM_MDR_HEAD,
    FROM_NAMING_RULES,
    FROM_THIS_RELEASE,
    HELD_IN_MDR,
    SPONSOR_IMPACT_TYPES,
    EntityType,
    InconsistencyStatus,
    InconsistencyType,
    MatchTier,
    ResolutionStrategy,
    build_inconsistency_uid,
    is_informational,
)
from standards_import.models.jobs import Job, JobKind, JobStatus
from standards_import.models.packages import (
    EffectiveDateStatus,
    InconsistencyCount,
    SponsorImpactSummary,
)
from standards_import.repositories import (
    analysis_repository,
    inconsistency_repository,
    job_repository,
    mdr_repository,
    rules_repository,
    semantic_repository,
    staging_repository,
)
from standards_import.repositories.staging_db import staging_session, to_native
from standards_import.services import (
    import_service,
    job_service,
    resolution_service,
    semantic_matching,
    semantic_provider,
    sponsor_matching,
)

log = logging.getLogger(__name__)

PRUNE_TYPES = sorted(SPONSOR_IMPACT_TYPES)


# Statuses a release must not be in to be assessed. `FILES_STAGED` because there is
# nothing grouped to compare yet; `IMPORTING`/`IMPORTED` because the answer would be
# about a release already on its way into MDR, where no decision taken now could still
# apply.
UNASSESSABLE = (
    EffectiveDateStatus.FILES_STAGED.value,
    EffectiveDateStatus.IMPORTING.value,
    EffectiveDateStatus.IMPORTED.value,
)

# `ANALYZING` because it would be reading the grouped layer mid-rewrite; `ASSESSING`
# because a second assessment of the same release is just this one again. Kept apart
# from `UNASSESSABLE` for a message that says what to do about it: wait, not "this
# release isn't ready".
BUSY_WITH_ANOTHER_STEP = (
    EffectiveDateStatus.ANALYZING.value,
    EffectiveDateStatus.ASSESSING.value,
)


def start_assessment(effective_date: date) -> Job:
    """Checks the release may be assessed and records a job to carry it out.

    A misconfigured semantic provider is checked here rather than left to fail inside
    the background job, so it is reported immediately instead of only on the next
    `GET /jobs/{uid}` — the same reasoning as `staging_service.start_discovery`'s
    `cdisc_client.require_configured()` call.
    """

    semantic_provider.load_provider()
    package_date = effective_date.isoformat()
    author_id = user().id()

    with staging_session() as session:
        release = require_release(session, package_date)
        guard_assessable(session, release, package_date)

        job_uid = uuid.uuid4().hex
        record = job_repository.start_job(
            session,
            job_uid,
            JobKind.SPONSOR_IMPACT.value,
            package_date,
            author_id,
            status_while_running=EffectiveDateStatus.ASSESSING.value,
            # Null: `perform_assessment` already sets ANALYZED/BLOCKED itself on
            # success, via the same `set_assessment_outcome` call the old synchronous
            # path made.
            status_on_success=None,
            # Whatever it was before starting: assessment only adds findings and never
            # rewrites the grouped layer, so a failed run invalidates nothing analysis
            # had already settled — unlike analysis's own failure, which does.
            status_on_failure=release["status"],
        )

    ValidationException.raise_if(
        record is None,
        msg=f"Effective date '{package_date}' cannot start now because another step is already running against it.",
    )
    assert record is not None
    return job_service.job_to_model(record)


def run_assessment(job_uid: str, effective_date: date, refresh: bool = False) -> None:
    """Assesses sponsor impact. Runs in the background; failures land on the job.

    No `author_id`: like analysis, nothing this does is attributed to a person.
    """

    package_date = effective_date.isoformat()
    try:
        summary = perform_assessment(effective_date, refresh=refresh)
        with staging_session() as session:
            job_repository.finish_job(
                session,
                job_uid,
                JobStatus.SUCCEEDED.value,
                stats={
                    "open_finding_count": summary.open_finding_count,
                    "checked_codelists": summary.checked_codelists,
                    "checked_memberships": summary.checked_memberships,
                    "checked_semantically": summary.checked_semantically,
                    "checked_updated_terms": summary.checked_updated_terms,
                    "checked_removed_or_changed_terms": summary.checked_removed_or_changed_terms,
                },
            )
        log.info(
            "Assessment %s of %s finished: %s", job_uid, package_date, summary.status
        )
    except Exception as exc:  # pylint: disable=broad-except
        log.exception("Assessment %s of %s failed", job_uid, package_date)
        with staging_session() as session:
            job_repository.finish_job(
                session, job_uid, JobStatus.FAILED.value, error=str(exc)
            )


def perform_assessment(
    effective_date: date, refresh: bool = False
) -> SponsorImpactSummary:
    """Compares one release against the sponsor side of MDR. Writes nothing to MDR.

    `refresh` puts every question to the language model again instead of reusing the
    answers on file. The inputs decide that on their own — a codelist whose settled names
    have not moved is not asked again — so this is for when the *answers* are what changed:
    a new model, or a provider pointed somewhere else.

    Assumes the caller already checked the release can be assessed — see
    `start_assessment`/`guard_assessable`. Not called directly from a route: reached
    through `run_assessment`, the background job's own work.
    """

    package_date = effective_date.isoformat()
    run_id = uuid.uuid4().hex

    with staging_session() as session:
        rules_repository.ensure_seed_data(session)
        rules = rules_repository.get_rules(session, enabled_only=True)

        log.info("Assessing sponsor impact of %s (run %s)", package_date, run_id)
        delta = import_service.compute_delta(session, package_date)
        findings, checked = collect_findings(
            session, package_date, delta, rules, refresh
        )

        inconsistency_repository.upsert_findings(
            session, package_date, run_id, findings
        )
        pruned = inconsistency_repository.prune_findings(
            session, package_date, run_id, PRUNE_TYPES
        )
        if pruned:
            log.info(
                "%s sponsor impact findings no longer apply and were dropped", pruned
            )

        settled = auto_resolve(session, package_date, findings, rules)
        inconsistency_repository.link_findings_to_concepts(session, package_date)

        counts = inconsistency_repository.count_by_type_tier_and_status(
            session, package_date, PRUNE_TYPES
        )
        # Across every kind, not only this pass's: the release's own count is what the
        # import reads, and analysis's findings are still on it.
        open_count = open_findings(
            inconsistency_repository.count_by_type_and_status(session, package_date)
        )
        status = (
            EffectiveDateStatus.BLOCKED if open_count else EffectiveDateStatus.ANALYZED
        )
        outcome = staging_repository.set_assessment_outcome(
            session, package_date, status.value, open_count
        )

    log.info(
        "Assessed %s: %s findings (%s settled automatically), %s open across the release",
        package_date,
        len(findings),
        settled,
        open_count,
    )

    return build_summary(effective_date, status, outcome, counts, checked)


def get_summary(effective_date: date) -> SponsorImpactSummary:
    """The last assessment of a release, rebuilt from what it stored."""

    package_date = effective_date.isoformat()
    with staging_session() as session:
        release = require_release(session, package_date)
        NotFoundException.raise_if(
            release.get("assessed_at") is None,
            msg=f"Effective date '{package_date}' has not been assessed for sponsor "
            "impact yet. Run POST /effective-dates/{effective_date}/sponsor-impact.",
        )
        counts = inconsistency_repository.count_by_type_tier_and_status(
            session, package_date, PRUNE_TYPES
        )

    # The counts a stored assessment can answer for. What it compared is not stored,
    # because it is derived from the release and would go stale on its own.
    return build_summary(
        effective_date,
        EffectiveDateStatus(release["status"]),
        release,
        counts,
        {},
    )


# --- guards ---------------------------------------------------------------------


def require_release(session, package_date: str) -> dict[str, Any]:
    record = staging_repository.find_effective_date(session, package_date)
    if record is None:
        raise NotFoundException(
            msg=f"No files have been staged for effective date '{package_date}'."
        )
    return record


def guard_assessable(session, release: dict[str, Any], package_date: str) -> None:
    """Refuses a release whose settled values are not the ones this would compare.

    Every check here is about the same thing: the name a term will be called in MDR is
    what the review items settled, so an unsettled or unapplied review item means the
    comparison would be made against a value that is not going to be the one written.
    """

    ValidationException.raise_if(
        release["status"] in UNASSESSABLE,
        msg=f"Effective date '{package_date}' has status '{release['status']}'. Sponsor "
        "impact is assessed on an analysed release that has not been imported.",
    )
    ValidationException.raise_if(
        release["status"] in BUSY_WITH_ANOTHER_STEP,
        msg=f"Effective date '{package_date}' has status '{release['status']}'. Another "
        "step is already running against it. Wait for it to finish and try again.",
    )

    open_elsewhere = open_findings(
        inconsistency_repository.count_by_type_and_status(session, package_date),
        excluding=SPONSOR_IMPACT_TYPES,
    )
    ValidationException.raise_if(
        open_elsewhere,
        msg=f"{open_elsewhere} review items are still open. Settle them and re-analyse "
        "first: what a term collides with depends on the name it will be given, and an "
        "open item means that name has not been chosen.",
    )

    pending = inconsistency_repository.count_decisions_since_analysis(
        session, package_date, sorted(ANALYSIS_TYPES)
    )
    ValidationException.raise_if(
        pending,
        msg=f"{pending} decisions have been made since the last analysis. Re-run the "
        "analysis so the staged values reflect them, then assess.",
    )


def open_findings(
    counts: list[dict[str, Any]], excluding: frozenset[str] | None = None
) -> int:
    return sum(
        row["count"]
        for row in counts
        if row["status"] == InconsistencyStatus.OPEN.value
        and not (excluding and row["type"] in excluding)
    )


# --- findings -------------------------------------------------------------------


def collect_findings(
    session,
    package_date: str,
    delta: dict[str, Any],
    rules: list[dict[str, Any]],
    refresh: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Raises a finding for each way this release lands on sponsor-defined content.

    Also returns what was actually compared. "Checked" and "clean" are different answers
    and a summary that could not tell them apart would read a release nobody compared as
    a release with nothing wrong with it.
    """

    findings: list[dict[str, Any]] = []
    checked: dict[str, int] = {}

    plan = build_comparison_plan(session, package_date, delta)
    checked["checked_memberships"] = sum(len(entry["added"]) for entry in plan.values())

    term_findings, string_matched = collect_term_duplicates(package_date, plan)
    findings.extend(term_findings)

    semantic_findings, checked["checked_semantically"] = collect_semantic_duplicates(
        session, package_date, plan, string_matched, refresh
    )
    findings.extend(semantic_findings)

    codelist_findings, checked["checked_codelists"] = collect_codelist_duplicates(
        package_date, delta
    )
    findings.extend(codelist_findings)

    name_findings, checked["checked_updated_terms"] = collect_diverged_names(
        session, package_date, delta, rules
    )
    findings.extend(name_findings)

    usage_findings, checked["checked_removed_or_changed_terms"] = (
        collect_used_term_changes(package_date, delta)
    )
    findings.extend(usage_findings)

    return findings, checked


def build_comparison_plan(
    session, package_date: str, delta: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Per codelist, the terms this release adds to it and the sponsor terms already in it.

    Built once and handed to both comparisons. They ask the same question of the same two
    lists — one by comparing strings, one by asking a model — and the reads behind those
    lists are the expensive part.

    Codelists this release introduces are left out: nothing can have been sitting in a
    codelist that did not exist, so there is nothing there to collide with. Codelists with
    no sponsor terms drop out too, which is what keeps the model side cheap.

    Extensibility is deliberately not consulted. Whether the sponsor was *allowed* to
    extend a codelist is a worse question than whether they *did* — a codelist that was
    extensible once and is not any more still holds whatever was added back then, and
    asking MDR directly answers both cases without a rule about either.
    """

    new_codelists = {row["concept_id"] for row in delta["codelists"]["new"]}
    additions = [
        membership
        for membership in delta["memberships_added"]
        if membership["codelist_uid"] not in new_codelists
    ]
    if not additions:
        return {}

    sponsor_terms = mdr_repository.get_sponsor_terms_in_codelists(
        sorted({membership["codelist_uid"] for membership in additions})
    )
    if not sponsor_terms:
        return {}

    by_codelist: dict[str, list[dict[str, Any]]] = {}
    for sponsor_term in sponsor_terms:
        by_codelist.setdefault(sponsor_term["codelist_uid"], []).append(sponsor_term)

    comparable = [
        membership
        for membership in additions
        if membership["codelist_uid"] in by_codelist
    ]
    names = settled_term_names(
        session, package_date, {membership["term_uid"] for membership in comparable}
    )
    definitions = {
        row["concept_id"]: (row["props"] or {}).get("definition")
        for row in delta["terms"]["all"]
    }
    codelist_names = {
        row["concept_id"]: row["attributes"].get("name")
        for row in delta["codelists"]["all"]
    }

    plan: dict[str, dict[str, Any]] = {}
    for membership in comparable:
        codelist_uid = membership["codelist_uid"]
        entry = plan.setdefault(
            codelist_uid,
            {
                "codelist_name": codelist_names.get(codelist_uid) or codelist_uid,
                "sponsor": by_codelist[codelist_uid],
                "added": [],
            },
        )
        entry["added"].append(
            {
                "concept_id": membership["term_uid"],
                "name": names.get(membership["term_uid"]),
                "submission_value": membership["submission_value"],
                "definition": definitions.get(membership["term_uid"]),
            }
        )
    return plan


def collect_term_duplicates(
    package_date: str, plan: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], set[tuple[str, str]]]:
    """Terms this release adds that a sponsor term in the same codelist already covers.

    Also returns the (codelist, CDISC term) pairs it found anything for, so the model is
    never asked to give a second opinion on a collision the strings already settled.
    """

    collisions = []
    for codelist_uid, entry in plan.items():
        index = sponsor_matching.build_index(entry["sponsor"])
        for added in entry["added"]:
            matches = sponsor_matching.find_matches(
                index,
                name=added["name"],
                submission_value=added["submission_value"],
            )
            if matches:
                collisions.append(
                    (
                        {
                            "codelist_uid": codelist_uid,
                            "term_uid": added["concept_id"],
                        },
                        matches,
                    )
                )

    # One read for every sponsor term implicated, rather than one per finding. The count
    # is a signal for the queue — whether this collision is one anybody can act on — and
    # not the authority: what is actually in use is checked again when a decision is
    # taken and again before the import writes anything.
    usage = mdr_repository.get_term_usage(
        sorted(
            {
                uid
                for _, matches in collisions
                for uid in sponsor_uids_of(matches)
                if uid
            }
        )
    )

    findings = []
    for membership, matches in collisions:
        tier = sponsor_matching.strongest_tier(matches)
        findings.append(
            build_finding(
                package_date,
                InconsistencyType.SPONSOR_TERM_DUPLICATE,
                EntityType.CODELIST,
                membership["codelist_uid"],
                [
                    {"value": sponsor_matching.describe_match(match), "catalogues": []}
                    for match in matches
                ],
                related_concept_id=membership["term_uid"],
                match_tier=tier,
                usage_count=sum(
                    entry["count"]
                    for uid in sponsor_uids_of(matches)
                    for entry in usage.get(uid, ())
                ),
                # EXACT breaks the main API's uniqueness rule and stays OPEN — somebody
                # has to say what to do about it. Anything looser is informational: two
                # distinct values that merely read alike, not a broken invariant.
                status=(
                    InconsistencyStatus.INFORMATIONAL
                    if is_informational(
                        InconsistencyType.SPONSOR_TERM_DUPLICATE.value,
                        tier.value if tier else None,
                    )
                    else InconsistencyStatus.OPEN
                ),
            )
        )
    return findings, {
        (membership["codelist_uid"], membership["term_uid"])
        for membership, _ in collisions
    }


def sponsor_uids_of(matches: list[dict[str, Any]]) -> set[str]:
    return {match["sponsor_uid"] for match in matches if match["sponsor_uid"]}


def collect_semantic_duplicates(
    session,
    package_date: str,
    plan: dict[str, dict[str, Any]],
    string_matched: set[tuple[str, str]],
    refresh: bool = False,
) -> tuple[list[dict[str, Any]], int]:
    """Asks a language model what the string comparison could not see.

    Off unless a provider is configured, and the whole assessment works without it —
    `checked_semantically` of zero says the question was never put, which is a different
    answer from nobody finding anything.

    Three things keep this cheap enough to run as often as a release needs assessing. The
    plan already excludes codelists with no sponsor terms, which on a real release is most
    of them; pairs the strings already matched are skipped, so the model is only ever
    asked about what is genuinely outstanding; and an answer already on file for the same
    question is reused rather than bought again.

    That last one is what makes re-assessing affordable. A release is assessed once per
    analysis run, and analysis is re-run every time a review item is settled — so without
    it, settling one naming item would mean paying for every codelist in the release a
    second time. The prompt is the key, so a codelist whose settled names have not moved
    since the last assessment is free, and one where a single term was renamed is asked
    again. `refresh` puts every question again regardless, for when the answers rather
    than the inputs are what changed.

    A failure against one codelist is logged and costs that codelist's answer, not the
    assessment — the string comparison is the part with teeth, and losing it because a
    gateway timed out would be a poor trade. Nothing is filed for a failed call, so the
    next assessment tries again.
    """

    provider = semantic_provider.load_provider()
    if provider is None:
        log.info(
            "No semantic provider configured, so this release is not checked for sponsor "
            "terms that mean the same thing under a different name."
        )
        return [], 0

    prompts = {}
    for codelist_uid, entry in plan.items():
        outstanding = [
            added
            for added in entry["added"]
            if (codelist_uid, added["concept_id"]) not in string_matched
        ]
        if outstanding:
            prompts[codelist_uid] = (
                outstanding,
                semantic_matching.build_prompt(
                    entry["codelist_name"], outstanding, entry["sponsor"]
                ),
            )
    if not prompts:
        return [], 0

    keys = {
        codelist_uid: semantic_repository.answer_key(
            settings.semantic_provider, settings.semantic_model, prompt
        )
        for codelist_uid, (_, prompt) in prompts.items()
    }
    on_file = (
        {}
        if refresh
        else semantic_repository.get_answers(session, sorted(set(keys.values())))
    )
    log.info(
        "%s codelist(s) to ask about, %s already answered",
        len(prompts),
        sum(1 for key in keys.values() if key in on_file),
    )

    findings: list[dict[str, Any]] = []
    checked = 0
    to_file: list[dict[str, Any]] = []

    for codelist_uid, (outstanding, prompt) in prompts.items():
        reply = on_file.get(keys[codelist_uid])
        if reply is None:
            log.info(
                "Asking about %s: %s added against %s sponsor term(s)",
                codelist_uid,
                len(outstanding),
                len(plan[codelist_uid]["sponsor"]),
            )
            try:
                reply = provider(prompt)
            except Exception:  # pylint: disable=broad-except
                log.exception(
                    "The semantic provider failed for codelist %s; its terms are "
                    "reported by the string comparison only",
                    codelist_uid,
                )
                continue
            to_file.append(
                {
                    "uid": keys[codelist_uid],
                    "reply": reply,
                    "model": settings.semantic_model,
                    "provider": settings.semantic_provider,
                    "codelist_id": codelist_uid,
                }
            )

        checked += len(outstanding)
        candidates_by_term = semantic_matching.resolve_pairs(
            semantic_matching.extract_pairs(reply),
            outstanding,
            plan[codelist_uid]["sponsor"],
        )
        for term_id, candidates in sorted(candidates_by_term.items()):
            findings.append(
                build_finding(
                    package_date,
                    InconsistencyType.SPONSOR_TERM_SEMANTIC_DUPLICATE,
                    EntityType.CODELIST,
                    codelist_uid,
                    [
                        {
                            "value": semantic_matching.describe_candidate(candidate),
                            "catalogues": [],
                            "source": (
                                f"{FROM_LANGUAGE_MODEL} {settings.semantic_model}"
                                if settings.semantic_model
                                else FROM_LANGUAGE_MODEL
                            ),
                        }
                        for candidate in candidates
                    ],
                    related_concept_id=term_id,
                    # A model's opinion, never a fact about a broken rule — there is no
                    # EXACT tier here, so this is always informational.
                    status=InconsistencyStatus.INFORMATIONAL,
                )
            )

    # Filed after the loop, and only for calls that came back: a question the gateway
    # never answered must be asked again next time, not remembered as unanswerable.
    semantic_repository.save_answers(session, to_file)
    return findings, checked


def collect_codelist_duplicates(
    package_date: str, delta: dict[str, Any]
) -> tuple[list[dict[str, Any]], int]:
    """Codelists this release introduces that a sponsor codelist already covers.

    Compared against every sponsor codelist rather than a narrowed set, because the main
    API's name and submission-value uniqueness for codelists is global — there is no
    scope to narrow to.
    """

    new_codelists = delta["codelists"]["new"]
    if not new_codelists:
        return [], 0

    index = sponsor_matching.build_index(mdr_repository.get_sponsor_codelists())

    findings = []
    for row in new_codelists:
        attributes = row["attributes"]
        matches = sponsor_matching.find_matches(
            index,
            name=attributes.get("name"),
            submission_value=attributes.get("submission_value"),
        )
        if not matches:
            continue
        findings.append(
            build_finding(
                package_date,
                InconsistencyType.SPONSOR_CODELIST_DUPLICATE,
                EntityType.CODELIST,
                row["concept_id"],
                [
                    {"value": sponsor_matching.describe_match(match), "catalogues": []}
                    for match in matches
                ],
                match_tier=sponsor_matching.strongest_tier(matches),
                # Always informational, at every tier: there is no strategy that acts
                # on this kind either way, so the tier changes nothing about the status.
                status=InconsistencyStatus.INFORMATIONAL,
            )
        )
    return findings, len(new_codelists)


def collect_used_term_changes(
    package_date: str, delta: dict[str, Any]
) -> tuple[list[dict[str, Any]], int]:
    """CDISC terms this release changes or removes from a codelist that MDR still refers to.

    Not a collision with sponsor content — a routine CDISC change, reported only where
    it lands on something already built on the term. CDISC drops and re-values terms
    every release, almost always harmlessly, so a changed or removed term with nothing
    referring to it raises nothing here at all: not an auto-resolved finding, no node,
    no trace. Only a term MDR still points at is worth a reviewer's attention.

    Detection is a pure recompute from `compute_delta` every run, gated on a usage count
    queried fresh rather than trusted from a prior assessment. That is what makes both
    directions of usage moving work without any special-casing: a term whose usage goes
    from zero to nonzero is new to this run's candidate set and gets created by
    `upsert_findings` like any other finding; one that drops back to zero is simply
    absent from this run's set and gets pruned by `prune_findings`, the same as a
    disagreement the data no longer supports.
    """

    changed, removed = import_service.changed_and_removed_memberships(delta)
    if not changed and not removed:
        return [], 0

    pairs = sorted(
        {(row["codelist_uid"], row["term_uid"]) for row in changed + removed}
    )
    usage = mdr_repository.get_membership_usage(pairs)

    findings = []
    for row in changed:
        count = sum(
            entry["count"]
            for entry in usage.get((row["codelist_uid"], row["term_uid"]), ())
        )
        if count <= 0:
            continue
        findings.append(
            build_finding(
                package_date,
                InconsistencyType.CDISC_TERM_SUBMISSION_VALUE_CHANGED,
                EntityType.CODELIST,
                row["codelist_uid"],
                [
                    {
                        "value": row["old"]["submission_value"],
                        "catalogues": [],
                        "source": FROM_MDR_HEAD,
                    },
                    {
                        "value": row["new"]["submission_value"],
                        "catalogues": [],
                        "source": FROM_THIS_RELEASE,
                    },
                ],
                related_concept_id=row["term_uid"],
                usage_count=count,
            )
        )
    for row in removed:
        count = sum(
            entry["count"]
            for entry in usage.get((row["codelist_uid"], row["term_uid"]), ())
        )
        if count <= 0:
            continue
        findings.append(
            build_finding(
                package_date,
                InconsistencyType.CDISC_TERM_REMOVED_FROM_CODELIST,
                EntityType.CODELIST,
                row["codelist_uid"],
                [
                    {
                        "value": row["submission_value"],
                        "catalogues": [],
                        "source": FROM_MDR_HEAD,
                    }
                ],
                related_concept_id=row["term_uid"],
                usage_count=count,
            )
        )
    return findings, len(changed) + len(removed)


def collect_diverged_names(
    session, package_date: str, delta: dict[str, Any], rules: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], int]:
    """Terms CDISC has changed whose sponsor name the rules would no longer produce.

    The obvious test — the name in MDR differs from the CDISC preferred term — is
    useless, because that is the *normal* state wherever a naming rule applies: the
    shipped rules turn `Interventional Study` into `Interventional` across dozens of
    codelists, and every one of those would be reported forever.

    So the rules are re-run instead. A `SPONSOR_NAME` finding is built from the preferred
    term this release now ships, put through the same matching and the same strategy the
    import would use for a new term, and the answer compared with what MDR holds. That
    separates "the rules still agree with the name" from "the rules would now say
    something else", which is the only version of this worth a reviewer's attention.
    """

    updated = delta["terms"]["updated"]
    if not updated:
        return [], 0

    held = mdr_repository.get_term_names([row["concept_id"] for row in updated])
    if not held:
        return [], 0

    codelists_by_term = analysis_repository.get_codelists_by_term(session, package_date)

    findings = []
    checked = 0
    for row in updated:
        current = held.get(row["concept_id"])
        if not current:
            continue
        checked += 1
        memberships = sorted(
            codelists_by_term.get(row["concept_id"], []),
            key=lambda membership: membership["codelist_id"],
        )
        preferred_term = (row["props"] or {}).get("preferredTerm")
        proposed = name_the_rules_would_give(
            package_date, row["concept_id"], preferred_term, memberships, rules
        )
        if proposed is None or proposed == current:
            continue

        # The question is whether *this release* moved the name, not whether the name in
        # MDR happens to differ from what the rules say. Those are wildly different
        # populations: on a database the bootstrap script populated, thousands of terms
        # carry a name no rule would produce today, and reporting each one CDISC touches
        # would bury the handful where a rename actually happened.
        was = ((row.get("head") or {}).get("props") or {}).get("preferred_term")
        previously = name_the_rules_would_give(
            package_date, row["concept_id"], was, memberships, rules
        )
        if previously == proposed:
            continue
        findings.append(
            build_finding(
                package_date,
                InconsistencyType.SPONSOR_NAME_DIVERGED,
                EntityType.TERM,
                row["concept_id"],
                # Two names competing for one term. Each says where it came from, and
                # the one the rules produced also names the catalogues that shipped the
                # preferred term it was produced from — that is real provenance, and it
                # is what tells a reviewer which CDISC package moved the name.
                [
                    {"value": current, "catalogues": [], "source": HELD_IN_MDR},
                    {
                        "value": proposed,
                        "catalogues": sorted(set(row.get("packages") or [])),
                        "source": FROM_NAMING_RULES,
                    },
                ],
                codelist_ids=[m["codelist_id"] for m in memberships],
                submission_values=[m["submission_value"] for m in memberships],
                # The sponsor name is left alone either way; this is a fact worth
                # noting, not a value in dispute — never blocking.
                status=InconsistencyStatus.INFORMATIONAL,
            )
        )
    return findings, checked


def name_the_rules_would_give(
    package_date: str,
    concept_id: str,
    preferred_term: Any,
    memberships: list[dict[str, Any]],
    rules: list[dict[str, Any]],
) -> str | None:
    """What the naming rules would call this term today, or None where they cannot say.

    The probe is shaped exactly like the `SPONSOR_NAME` finding analysis raises for a
    term new to MDR, because it has to be matched by the same rules — a probe that
    differed in any discriminator would be answered by a different rule than the import
    would actually apply.
    """

    if not preferred_term:
        return None

    probe = {
        "uid": build_inconsistency_uid(
            package_date,
            EntityType.TERM,
            concept_id,
            InconsistencyType.SPONSOR_NAME,
        ),
        "effective_date": package_date,
        "type": InconsistencyType.SPONSOR_NAME.value,
        "entity_type": EntityType.TERM.value,
        "concept_id": concept_id,
        "related_concept_id": None,
        "property": None,
        "match_tier": None,
        "candidates": [{"value": preferred_term, "catalogues": []}],
        "codelist_ids": [m["codelist_id"] for m in memberships],
        "submission_values": [m["submission_value"] for m in memberships],
    }

    rule = resolution_service.find_matching_rule(probe, rules)
    if rule is None:
        return None

    try:
        proposed = resolution_service.resolve_value(
            ResolutionStrategy(rule["strategy"]),
            probe,
            value=rule.get("value"),
            catalogue=rule.get("catalogue"),
            pattern=rule.get("pattern"),
            in_codelist_id=rule.get("in_codelist_id"),
            steps=tuple(
                (step["pattern"], step["replacement"])
                for step in rule.get("steps") or []
            ),
            title_case=bool(rule.get("title_case")),
        )
    except ValidationException as exc:
        # The same contract auto-resolution holds to: a rule that cannot apply here is a
        # configuration problem, visible in the log and not a reason to fail the run.
        log.warning(
            "Rule %s matched term %s but could not be applied: %s",
            rule["uid"],
            concept_id,
            exc.msg,
        )
        return None
    except Exception:  # pylint: disable=broad-except
        log.exception(
            "Rule %s matched term %s but failed unexpectedly",
            rule["uid"],
            concept_id,
        )
        return None

    # A strategy can produce a list; a name is text, and anything else means the rule was
    # never meant for this question.
    return proposed if isinstance(proposed, str) else None


def build_finding(
    package_date: str,
    finding_type: InconsistencyType,
    entity_type: EntityType,
    concept_id: str,
    candidates: list[dict[str, Any]],
    related_concept_id: str | None = None,
    match_tier: MatchTier | None = None,
    usage_count: int | None = None,
    codelist_ids: list[str] | None = None,
    submission_values: list[str] | None = None,
    status: InconsistencyStatus = InconsistencyStatus.OPEN,
) -> dict[str, Any]:
    """One finding, with the deterministic uid that lets a decision survive a re-run.

    The fingerprint covers the candidates, and every candidate of a collision finding
    leads with its tier and the sponsor uid — so a decision is discarded and the item
    reopened when the sponsor edits what it was made about, and stands when they do not.

    `status` is most often `OPEN`, the default — the exception is a collector raising
    a kind that is informational rather than blocking, which passes
    `InconsistencyStatus.INFORMATIONAL` explicitly. `upsert_findings` reads it under
    `initial_status` to decide what a *new* finding — or one reopened after its
    candidates changed — is created as.
    """

    return {
        "uid": build_inconsistency_uid(
            package_date,
            entity_type,
            concept_id,
            finding_type,
            related_concept_id=related_concept_id,
        ),
        "effective_date": package_date,
        "type": finding_type.value,
        "entity_type": entity_type.value,
        "concept_id": concept_id,
        "related_concept_id": related_concept_id,
        "property": None,
        "match_tier": match_tier.value if match_tier else None,
        # Left out of the fingerprint on purpose: usage moves all the time and on its
        # own says nothing about whether the decision was the right one, or whether the
        # finding should still exist at all. What stops a stale retirement is the check
        # made when the import runs, not a reopened item — and what makes a usage
        # finding come and go with the count crossing zero is that it is not part of
        # the candidate set to begin with when the count is zero, not fingerprinting.
        "usage_count": usage_count,
        "candidates": candidates,
        "codelist_ids": codelist_ids or [],
        "submission_values": submission_values or [],
        "fingerprint": resolution_service.candidate_fingerprint(candidates),
        "initial_status": status.value,
    }


def settled_term_names(
    session, package_date: str, term_ids: set[str]
) -> dict[str, str]:
    """What each of these terms will be called in MDR once this release is imported.

    Not the CDISC preferred term. For a term new to MDR that is whatever the
    `SPONSOR_NAME` review item settled, and for one MDR already holds it is the name
    already there, which the import never overwrites. Comparing anything else would both
    miss collisions and invent ones that could never happen.
    """

    if not term_ids:
        return {}

    decided = {
        resolution["concept_id"]: resolution["resolved_value"]
        for resolution in inconsistency_repository.get_resolutions_for_date(
            session, package_date
        )
        if resolution["type"] == InconsistencyType.SPONSOR_NAME.value
        and resolution["concept_id"] in term_ids
        and isinstance(resolution.get("resolved_value"), str)
    }

    names = mdr_repository.get_term_names(sorted(term_ids - set(decided)))
    names.update(decided)
    return names


def auto_resolve(
    session,
    package_date: str,
    findings: list[dict[str, Any]],
    rules: list[dict[str, Any]],
) -> int:
    """Settles what the rules cover, leaving the rest to be looked at.

    No catalogue pecking order is offered: that settles a disagreement between two
    catalogues of one release, and none of these findings is one.
    """

    undecided = set(
        inconsistency_repository.get_undecided(session, package_date, PRUNE_TYPES)
    )
    if not undecided:
        return 0

    decisions = []
    for finding in findings:
        if finding["uid"] not in undecided:
            continue
        outcome = resolution_service.auto_resolve(finding, rules, [])
        if outcome is None:
            continue
        status, decision = outcome
        decisions.append(
            {"uid": finding["uid"], "status": status.value, "decision": decision}
        )

    inconsistency_repository.record_decisions(session, decisions)
    return len(decisions)


# --- reporting ------------------------------------------------------------------


def build_summary(
    effective_date: date,
    status: EffectiveDateStatus,
    outcome: dict[str, Any],
    counts: list[dict[str, Any]],
    checked: dict[str, int],
) -> SponsorImpactSummary:
    status_fields = {
        InconsistencyStatus.OPEN.value: "open",
        InconsistencyStatus.AUTO_RESOLVED.value: "auto_resolved",
        InconsistencyStatus.RESOLVED.value: "resolved",
        InconsistencyStatus.IGNORED.value: "ignored",
        InconsistencyStatus.INFORMATIONAL.value: "informational",
        InconsistencyStatus.ACKNOWLEDGED.value: "acknowledged",
    }

    per_type: dict[str, dict[str, int]] = {}
    per_tier: dict[str, int] = {}
    for record in counts:
        bucket = per_type.setdefault(
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
        if record["match_tier"]:
            per_tier[record["match_tier"]] = (
                per_tier.get(record["match_tier"], 0) + record["count"]
            )

    return SponsorImpactSummary(
        effective_date=effective_date,
        status=status,
        assessed_at=to_native(outcome["assessed_at"]),
        findings=[
            InconsistencyCount(type=InconsistencyType(finding_type), **bucket)
            for finding_type, bucket in sorted(per_type.items())
        ],
        open_finding_count=sum(bucket["open"] for bucket in per_type.values()),
        by_match_tier=dict(sorted(per_tier.items())),
        checked_codelists=checked.get("checked_codelists", 0),
        checked_memberships=checked.get("checked_memberships", 0),
        checked_semantically=checked.get("checked_semantically", 0),
        checked_updated_terms=checked.get("checked_updated_terms", 0),
        checked_removed_or_changed_terms=checked.get(
            "checked_removed_or_changed_terms", 0
        ),
    )
