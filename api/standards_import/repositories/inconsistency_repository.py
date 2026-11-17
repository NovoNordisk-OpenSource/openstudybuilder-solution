"""Review items and the decisions attached to them.

Findings hang off the `EffectiveDateImport`, not off the grouped concepts, because the
grouped layer is torn down and rebuilt by every analysis run and the decisions attached
to a finding must not go with it. The `ON` relationship to the grouped concept is a
convenience for traversal and is re-established after each run.
"""

import logging
from typing import Any

from standards_import.repositories.staging_db import StagingSession, run_query

log = logging.getLogger(__name__)

INCONSISTENCY_RETURN = """
    inc.uid AS uid,
    inc.effective_date AS effective_date,
    inc.type AS type,
    inc.entity_type AS entity_type,
    inc.concept_id AS concept_id,
    inc.related_concept_id AS related_concept_id,
    inc.property AS property,
    inc.match_tier AS match_tier,
    inc.usage_count AS usage_count,
    inc.codelist_ids AS codelist_ids,
    inc.submission_values AS submission_values,
    inc.status AS status,
    inc.detected_at AS detected_at,
    [(inc)-[:HAS_CANDIDATE]->(cand) | {value: cand.value, catalogues: cand.catalogues, source: cand.source}] AS candidates,
    head([(inc)-[:RESOLVED_BY]->(dec) |
        dec{.*, rule_uid: head([(dec)-[:APPLIES_RULE]->(rule) | rule.uid])}
    ]) AS resolution
"""


def upsert_findings(
    session: StagingSession,
    package_date: str,
    run_id: str,
    findings: list[dict[str, Any]],
) -> None:
    """Records this run's findings, keeping any decision still made against the same values.

    A finding's uid is deterministic, so re-analysis lands on the node a reviewer
    already decided about. What must not carry over is a decision taken against values
    that have since changed — a re-uploaded file can turn "SDTM says X, ADAM says Y"
    into an entirely different choice — so a changed candidate fingerprint drops the
    decision and reopens the item rather than silently applying a stale answer.
    See resolution_service for more info on candidate fingerprint.
    """

    if not findings:
        return

    run_query(
        session,
        """
        MATCH (import:EffectiveDateImport {effective_date: $package_date})
        UNWIND $findings AS finding
        MERGE (import)-[:HAS_INCONSISTENCY]->(inc:Inconsistency:CDISCStaging {uid: finding.uid})
        ON CREATE SET inc.detected_at = datetime(),
            inc.status = coalesce(finding.initial_status, 'OPEN')
        SET inc.effective_date = $package_date,
            inc.type = finding.type,
            inc.entity_type = finding.entity_type,
            inc.concept_id = finding.concept_id,
            inc.related_concept_id = finding.related_concept_id,
            inc.property = finding.property,
            inc.match_tier = finding.match_tier,
            inc.usage_count = finding.usage_count,
            inc.codelist_ids = finding.codelist_ids,
            inc.submission_values = finding.submission_values,
            inc.analysis_run_id = $run_id
        WITH inc, finding
        CALL (inc, finding) {
            MATCH (inc)-[resolved:RESOLVED_BY]->(decision:ResolutionDecision)
            WHERE inc.candidate_fingerprint IS NOT NULL
              AND inc.candidate_fingerprint <> finding.fingerprint
            DELETE resolved
            DETACH DELETE decision
            // A fingerprint change means the values changed since the decision was
            // made — the item reopens to whichever status it was raised at this run,
            // not unconditionally OPEN: an informational finding reopening should stay
            // informational, not be promoted to a blocker.
            SET inc.status = coalesce(finding.initial_status, 'OPEN')
        }
        WITH inc, finding
        CALL (inc) {
            MATCH (inc)-[:HAS_CANDIDATE]->(stale:CandidateValue)
            DETACH DELETE stale
        }
        SET inc.candidate_fingerprint = finding.fingerprint
        FOREACH (candidate IN finding.candidates |
            CREATE (inc)-[:HAS_CANDIDATE]->(:CandidateValue:CDISCStaging {
                value: candidate.value, catalogues: candidate.catalogues,
                source: candidate.source
            })
        )
        """,
        parameters={
            "package_date": package_date,
            "run_id": run_id,
            "findings": findings,
        },
    )


def prune_findings(
    session: StagingSession, package_date: str, run_id: str, types: list[str]
) -> int:
    """Removes findings this run did not re-raise, because the data no longer disagrees.

    Returns how many were dropped, which is the only way a reviewer learns that an item
    they were about to decide has gone away on its own.

    `types` is required, because two passes raise findings onto the same release —
    analysis and the sponsor impact assessment — and each runs on its own schedule, so a
    prune that matched every kind would have analysis silently delete the assessment's
    findings, decisions and all, every time it ran.
    """

    records = run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})-[:HAS_INCONSISTENCY]->(inc:Inconsistency)
        WHERE inc.type IN $types
          AND (inc.analysis_run_id IS NULL OR inc.analysis_run_id <> $run_id)
        OPTIONAL MATCH (inc)-[:HAS_CANDIDATE]->(cand:CandidateValue)
        OPTIONAL MATCH (inc)-[:RESOLVED_BY]->(dec:ResolutionDecision)
        WITH collect(DISTINCT inc) AS findings, collect(DISTINCT cand) AS cands, collect(DISTINCT dec) AS decs
        FOREACH (n IN findings | DETACH DELETE n)
        FOREACH (n IN cands | DETACH DELETE n)
        FOREACH (n IN decs | DETACH DELETE n)
        RETURN size(findings) AS pruned
        """,
        parameters={"package_date": package_date, "run_id": run_id, "types": types},
    )
    return records[0]["pruned"] if records else 0


def link_findings_to_concepts(session: StagingSession, package_date: str) -> None:
    """Points each finding at the grouped concept it is about.

    Rebuilt after grouping, since the grouped nodes are new objects on every run.
    """

    for label, group_rel in (
        ("GroupedCodelist", "HAS_GROUPED_CODELIST"),
        ("GroupedTerm", "HAS_GROUPED_TERM"),
    ):
        run_query(
            session,
            f"""
            MATCH (:EffectiveDateImport {{effective_date: $package_date}})-[:HAS_INCONSISTENCY]->(inc:Inconsistency)
            MATCH (:RawPackage {{effectiveDate: $package_date}})-[:{group_rel}]->(concept:{label} {{conceptId: inc.concept_id}})
            MERGE (inc)-[:ON]->(concept)
            """,
            parameters={"package_date": package_date},
        )


def get_findings(
    session: StagingSession,
    effective_date: str | None = None,
    status: str | None = None,
    inconsistency_type: str | None = None,
    entity_type: str | None = None,
    concept_id: str | None = None,
) -> list[dict[str, Any]]:
    filters = []
    if effective_date:
        filters.append("inc.effective_date = $effective_date")
    if status:
        filters.append("inc.status = $status")
    if inconsistency_type:
        filters.append("inc.type = $inconsistency_type")
    if entity_type:
        filters.append("inc.entity_type = $entity_type")
    if concept_id:
        filters.append("inc.concept_id = $concept_id")
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    return run_query(
        session,
        f"""
        MATCH (inc:Inconsistency)
        {where_clause}
        RETURN {INCONSISTENCY_RETURN}
        ORDER BY inc.effective_date DESC, inc.entity_type, inc.concept_id, inc.uid
        """,
        parameters={
            "effective_date": effective_date,
            "status": status,
            "inconsistency_type": inconsistency_type,
            "entity_type": entity_type,
            "concept_id": concept_id,
        },
    )


def get_finding_counts_by_codelist(
    session: StagingSession, package_date: str
) -> dict[str, dict[str, int]]:
    """Every finding of this release, grouped by status and the codelist it belongs to.

    Which field names the codelist varies by kind — see "What `concept_id` refers to,
    per kind" in the README. The 8 `CODELIST`-entity kinds carry it directly in
    `concept_id`; `SPONSOR_NAME` and `SPONSOR_NAME_DIVERGED` carry it in `codelist_ids`;
    the remaining two `TERM`-entity kinds (`CONFLICTING_VALUES`, `UNWANTED_QUOTES` on a
    term's own properties) name no codelist at all, so those are attributed through the
    term's current membership in the grouped layer instead.
    """

    records = run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})-[:HAS_INCONSISTENCY]->(inc:Inconsistency)
        OPTIONAL MATCH (:RawPackage {effectiveDate: $package_date})-[:HAS_GROUPED_CODELIST]->(gc:GroupedCodelist)-[:HAS_GROUPED_TERM_MEMBER]->(:GroupedTerm {conceptId: inc.concept_id})
          WHERE inc.entity_type = 'TERM' AND (inc.codelist_ids IS NULL OR size(inc.codelist_ids) = 0)
        WITH inc,
             CASE
               WHEN inc.entity_type = 'CODELIST' THEN [inc.concept_id]
               WHEN inc.codelist_ids IS NOT NULL AND size(inc.codelist_ids) > 0 THEN inc.codelist_ids
               WHEN gc IS NOT NULL THEN [gc.conceptId]
               ELSE []
             END AS codelist_ids
        UNWIND codelist_ids AS codelist_id
        RETURN codelist_id, inc.status AS status, count(*) AS count
        """,
        parameters={"package_date": package_date},
    )
    counts: dict[str, dict[str, int]] = {}
    for record in records:
        counts.setdefault(record["codelist_id"], {})[record["status"]] = record["count"]
    return counts


def get_finding_counts_by_term(
    session: StagingSession, package_date: str
) -> dict[str, dict[str, int]]:
    """Every finding of this release that names a term, grouped by status and that term.

    The mirror of `get_finding_counts_by_codelist`, and simpler: which field names the
    term varies by kind — see "What `concept_id` refers to, per kind" in the README — but
    going term-first, a finding either names its term or names none, so there is no
    grouped-layer fallback to make. The `TERM`-entity kinds carry it in `concept_id`; the
    four kinds about a term inside a particular codelist key on the codelist and name the
    term in `related_concept_id`.

    Findings that name no term are dropped, `INCONSISTENT_TERM_SETS` among them — it is
    about which terms a codelist contains rather than about any one of them, so it
    belongs on no term's row.
    """

    records = run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})-[:HAS_INCONSISTENCY]->(inc:Inconsistency)
        WITH inc,
             CASE
               WHEN inc.entity_type = 'TERM' THEN inc.concept_id
               WHEN inc.related_concept_id IS NOT NULL THEN inc.related_concept_id
               ELSE null
             END AS term_id
        WHERE term_id IS NOT NULL
        RETURN term_id, inc.status AS status, count(*) AS count
        """,
        parameters={"package_date": package_date},
    )
    counts: dict[str, dict[str, int]] = {}
    for record in records:
        counts.setdefault(record["term_id"], {})[record["status"]] = record["count"]
    return counts


def get_findings_for_codelist(
    session: StagingSession, package_date: str, codelist_id: str, term_ids: list[str]
) -> list[dict[str, Any]]:
    """Every finding relevant to one codelist: about the codelist itself, a collision
    keyed on the pair, or about one of the terms given (its current members, plus any
    whose membership just ended — both are worth showing here).

    Mirrors the three sources `get_finding_counts_by_codelist` tallies, but for one
    codelist and returning full rows rather than counts.
    """

    return run_query(
        session,
        f"""
        MATCH (:EffectiveDateImport {{effective_date: $package_date}})-[:HAS_INCONSISTENCY]->(inc:Inconsistency)
        WHERE (inc.entity_type = 'CODELIST' AND inc.concept_id = $codelist_id)
           OR ($codelist_id IN inc.codelist_ids)
           OR (inc.entity_type = 'TERM' AND inc.concept_id IN $term_ids)
        RETURN {INCONSISTENCY_RETURN}
        ORDER BY inc.entity_type, inc.concept_id, inc.uid
        """,
        parameters={
            "package_date": package_date,
            "codelist_id": codelist_id,
            "term_ids": term_ids,
        },
    )


def get_findings_for_term(
    session: StagingSession, package_date: str, term_id: str
) -> list[dict[str, Any]]:
    """Every finding that names one term: about the term itself, or about it inside one
    of its codelists.

    The same two sources `get_finding_counts_by_term` tallies, for one term and
    returning full rows rather than counts.
    """

    return run_query(
        session,
        f"""
        MATCH (:EffectiveDateImport {{effective_date: $package_date}})-[:HAS_INCONSISTENCY]->(inc:Inconsistency)
        WHERE (inc.entity_type = 'TERM' AND inc.concept_id = $term_id)
           OR (inc.entity_type <> 'TERM' AND inc.related_concept_id = $term_id)
        RETURN {INCONSISTENCY_RETURN}
        ORDER BY inc.entity_type, inc.concept_id, inc.uid
        """,
        parameters={"package_date": package_date, "term_id": term_id},
    )


def statuses_of(session: StagingSession, uids: list[str]) -> dict[str, str]:
    """Returns the current status of each of these findings, for whichever exist.

    A bulk lookup for a guard that has to ask "has this one already been acknowledged?"
    about several findings at once, without pulling the rest of each one back.
    """

    if not uids:
        return {}

    records = run_query(
        session,
        """
        MATCH (inc:Inconsistency)
        WHERE inc.uid IN $uids
        RETURN inc.uid AS uid, inc.status AS status
        """,
        parameters={"uids": uids},
    )
    return {record["uid"]: record["status"] for record in records}


def find_finding(session: StagingSession, uid: str) -> dict[str, Any] | None:
    records = run_query(
        session,
        f"""
        MATCH (inc:Inconsistency {{uid: $uid}})
        RETURN {INCONSISTENCY_RETURN}
        """,
        parameters={"uid": uid},
    )
    return records[0] if records else None


def record_decision(
    session: StagingSession, uid: str, status: str, decision: dict[str, Any]
) -> dict[str, Any] | None:
    """Attaches a decision, replacing whatever was there before."""

    records = run_query(
        session,
        f"""
        MATCH (inc:Inconsistency {{uid: $uid}})
        OPTIONAL MATCH (inc)-[old_link:RESOLVED_BY]->(old:ResolutionDecision)
        DELETE old_link
        DETACH DELETE old
        WITH inc
        CREATE (inc)-[:RESOLVED_BY]->(dec:ResolutionDecision:CDISCStaging {{
            strategy: $decision.strategy,
            resolved_value: $decision.resolved_value,
            chosen_catalogue: $decision.chosen_catalogue,
            author_id: $decision.author_id,
            note: $decision.note,
            decided_at: datetime()
        }})
        SET inc.status = $status
        WITH inc, dec
        CALL (dec) {{
            MATCH (rule:ResolutionRule {{uid: $rule_uid}})
            MERGE (dec)-[:APPLIES_RULE]->(rule)
        }}
        RETURN {INCONSISTENCY_RETURN}
        """,
        parameters={
            "uid": uid,
            "status": status,
            "decision": decision,
            "rule_uid": decision.get("rule_uid"),
        },
    )
    return records[0] if records else None


def record_decisions(session: StagingSession, decisions: list[dict[str, Any]]) -> None:
    """Attaches many decisions at once, for the auto-resolution pass.

    Each row is `{uid, status, decision}`. A conflict-heavy release can raise thousands
    of findings, and one round trip apiece would dominate the run.
    """

    if not decisions:
        return

    run_query(
        session,
        """
        UNWIND $decisions AS row
        MATCH (inc:Inconsistency {uid: row.uid})
        CALL (inc) {
            MATCH (inc)-[old_link:RESOLVED_BY]->(old:ResolutionDecision)
            DELETE old_link
            DETACH DELETE old
        }
        CREATE (inc)-[:RESOLVED_BY]->(dec:ResolutionDecision:CDISCStaging {
            strategy: row.decision.strategy,
            resolved_value: row.decision.resolved_value,
            chosen_catalogue: row.decision.chosen_catalogue,
            author_id: row.decision.author_id,
            note: row.decision.note,
            decided_at: datetime()
        })
        SET inc.status = row.status
        WITH inc, dec, row
        CALL (dec, row) {
            MATCH (rule:ResolutionRule {uid: row.decision.rule_uid})
            MERGE (dec)-[:APPLIES_RULE]->(rule)
        }
        """,
        parameters={"decisions": decisions},
    )


def get_undecided(
    session: StagingSession, package_date: str, types: list[str]
) -> list[str]:
    """Returns the uids of this release's findings that nothing has settled yet.

    Scoped to the kinds the calling pass raises, for the same reason the prune is: the
    two passes must not reach into each other's findings.
    """

    records = run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})-[:HAS_INCONSISTENCY]->(inc:Inconsistency)
        WHERE inc.type IN $types AND inc.status = 'OPEN' AND NOT (inc)-[:RESOLVED_BY]->()
        RETURN inc.uid AS uid
        """,
        parameters={"package_date": package_date, "types": types},
    )
    return [record["uid"] for record in records]


def clear_decision(
    session: StagingSession,
    uid: str,
    informational_types: list[str],
    tier_dependent_types: list[str],
) -> dict[str, Any] | None:
    """Removes the decision and reopens the item.

    Reopens to `INFORMATIONAL`, not `OPEN`, where that is what the finding was raised
    at — an item that never blocked before a decision was taken must not start
    blocking just because the decision was taken back.

    Type alone is not enough for every kind: `SPONSOR_TERM_DUPLICATE` is informational
    away from the `EXACT` tier and `OPEN` at it, so for the types named in
    `tier_dependent_types` the stored `match_tier` decides too, on top of `type` being
    in `informational_types`. Every other informational kind reopens to
    `INFORMATIONAL` regardless of tier — `SPONSOR_CODELIST_DUPLICATE` carries a tier of
    its own, but nothing about this kind is ever actionable at any tier, so the tier
    changes nothing about its status. This restates `is_informational` in the models.
    """

    records = run_query(
        session,
        f"""
        MATCH (inc:Inconsistency {{uid: $uid}})
        OPTIONAL MATCH (inc)-[link:RESOLVED_BY]->(dec:ResolutionDecision)
        DELETE link
        DETACH DELETE dec
        SET inc.status = CASE
            WHEN NOT inc.type IN $informational_types THEN 'OPEN'
            WHEN inc.type IN $tier_dependent_types
                 AND coalesce(inc.match_tier, 'EXACT') = 'EXACT'
                THEN 'OPEN'
            ELSE 'INFORMATIONAL'
        END
        WITH inc
        RETURN {INCONSISTENCY_RETURN}
        """,
        parameters={
            "uid": uid,
            "informational_types": informational_types,
            "tier_dependent_types": tier_dependent_types,
        },
    )
    return records[0] if records else None


def count_by_type_and_status(
    session: StagingSession, package_date: str
) -> list[dict[str, Any]]:
    return run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})-[:HAS_INCONSISTENCY]->(inc:Inconsistency)
        RETURN inc.type AS type, inc.status AS status, count(*) AS count
        """,
        parameters={"package_date": package_date},
    )


def count_by_type_tier_and_status(
    session: StagingSession, package_date: str, types: list[str]
) -> list[dict[str, Any]]:
    """Counts of one pass's findings, split by how closely the values collided as well.

    The tier is what decides whether a finding blocks, so a summary that reported only
    kinds and statuses could not say why a release is held up.
    """

    return run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})-[:HAS_INCONSISTENCY]->(inc:Inconsistency)
        WHERE inc.type IN $types
        RETURN inc.type AS type, inc.match_tier AS match_tier,
               inc.status AS status, count(*) AS count
        """,
        parameters={"package_date": package_date, "types": types},
    )


def count_decisions_since_analysis(
    session: StagingSession, package_date: str, types: list[str]
) -> int:
    """How many decisions were made after the last analysis run.

    Deciding stores the choice but does not touch the staged values — analysis is what
    applies them. Any count above zero means staging does not yet reflect the decisions.

    `types` must name only the kinds analysis actually applies. A sponsor impact decision
    is never written to the staged values, so counting one here would demand a re-analysis
    that could not change anything — and, because analysing invalidates the assessment,
    the release would then need assessing again, which would decide again, forever.
    """

    records = run_query(
        session,
        """
        MATCH (import:EffectiveDateImport {effective_date: $package_date})
        MATCH (import)-[:HAS_INCONSISTENCY]->(inc:Inconsistency)
              -[:RESOLVED_BY]->(dec:ResolutionDecision)
        WHERE inc.type IN $types
          AND (import.analyzed_at IS NULL OR dec.decided_at > import.analyzed_at)
        RETURN count(dec) AS count
        """,
        parameters={"package_date": package_date, "types": types},
    )
    return records[0]["count"] if records else 0


def get_resolutions_for_date(
    session: StagingSession, package_date: str
) -> list[dict[str, Any]]:
    """Returns every settled item of a release, for applying to the grouped concepts."""

    return run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})-[:HAS_INCONSISTENCY]->(inc:Inconsistency)
        WHERE NOT inc.status IN ['OPEN', 'INFORMATIONAL']
        OPTIONAL MATCH (inc)-[:RESOLVED_BY]->(dec:ResolutionDecision)
        RETURN inc.uid AS uid, inc.entity_type AS entity_type, inc.concept_id AS concept_id,
               inc.related_concept_id AS related_concept_id, inc.property AS property,
               inc.status AS status, inc.type AS type, inc.codelist_ids AS codelist_ids,
               dec.strategy AS strategy, dec.resolved_value AS resolved_value
        // Stable order: a property can carry two findings — disputed *and* quoted, say —
        // and both settle the same value. Which one lands must not vary between runs.
        ORDER BY inc.uid
        """,
        parameters={"package_date": package_date},
    )


def get_sponsor_actions(
    session: StagingSession, package_date: str, strategies: list[str]
) -> list[dict[str, Any]]:
    """Returns the settled sponsor impact items that will change what MDR already holds.

    Narrow on purpose. `get_resolutions_for_date` answers a different question and returns
    every decision of the release, which on a quarterly one is tens of thousands of rows;
    this is asked before the import is even accepted, and the answer is a handful.
    """

    return run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})-[:HAS_INCONSISTENCY]->(inc:Inconsistency)
              -[:RESOLVED_BY]->(dec:ResolutionDecision)
        WHERE dec.strategy IN $strategies AND dec.resolved_value IS NOT NULL
        RETURN inc.uid AS uid, inc.type AS type, inc.concept_id AS concept_id,
               inc.related_concept_id AS related_concept_id,
               dec.strategy AS strategy, dec.resolved_value AS resolved_value
        ORDER BY inc.uid
        """,
        parameters={"package_date": package_date, "strategies": strategies},
    )


def get_provisional_concepts(
    session: StagingSession, package_date: str
) -> list[dict[str, Any]]:
    """Returns the concepts whose staged values are not settled yet.

    Their properties are written to staging like any other concept's — what open items
    hold up is promotion to MDR. This is how a caller tells which of those staged values
    are still the pecking order's guess rather than a decision.
    """

    return run_query(
        session,
        """
        MATCH (:EffectiveDateImport {effective_date: $package_date})-[:HAS_INCONSISTENCY]->(inc:Inconsistency)
        WHERE inc.status = 'OPEN'
        RETURN inc.entity_type AS entity_type,
               inc.concept_id AS concept_id,
               collect(DISTINCT inc.type) AS types
        ORDER BY entity_type, concept_id
        """,
        parameters={"package_date": package_date},
    )
