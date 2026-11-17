"""Reading review items, settling them, and managing the standing decisions."""

import logging
from datetime import date
from typing import Any

from common.auth.user import user
from common.exceptions import NotFoundException, ValidationException
from standards_import.models.inconsistencies import (
    INFORMATIONAL_TYPES,
    TIER_DEPENDENT_TYPES,
    CandidateValue,
    CataloguePriorityEntry,
    CataloguePriorityInput,
    EntityType,
    ExpectedWorkbooksInput,
    ImportEnabled,
    Inconsistency,
    InconsistencyStatus,
    InconsistencyType,
    MandatoryCataloguesInput,
    MatchTier,
    ResolutionDecision,
    ResolutionInput,
    ResolutionOptions,
    ResolutionRule,
    ResolutionRuleInput,
    ResolutionRuleUpdate,
    ResolutionStrategy,
    RewriteStep,
    RuleScope,
    StrategyDescription,
    review_pass_of,
)
from standards_import.models.packages import EffectiveDateStatus
from standards_import.repositories import (
    inconsistency_repository,
    mdr_repository,
    rules_repository,
    staging_repository,
)
from standards_import.repositories.staging_db import staging_session, to_native
from standards_import.services import resolution_service

log = logging.getLogger(__name__)

# Which of a finding's fields a saved rule pins down, per scope. Anything not listed is
# left unset, and a rule ignores what it does not set.
#
# `match_tier` is pinned at every scope, including GLOBAL. It is null on every finding
# analysis raises, so for those it pins nothing — but on a sponsor impact finding it is
# what separates a collision that breaks a uniqueness rule from one that does not, and a
# rule saved from an exact one must not go on to wave through the near ones as well.
RULE_DISCRIMINATORS_BY_SCOPE: dict[RuleScope, tuple[str, ...]] = {
    RuleScope.OCCURRENCE: (
        "entity_type",
        "concept_id",
        "related_concept_id",
        "property",
        "effective_date",
        "inconsistency_type",
        "match_tier",
    ),
    RuleScope.CONCEPT: (
        "entity_type",
        "concept_id",
        "inconsistency_type",
        "match_tier",
    ),
    RuleScope.PROPERTY: ("entity_type", "property", "inconsistency_type", "match_tier"),
    RuleScope.GLOBAL: ("inconsistency_type", "match_tier"),
}


def list_findings(
    effective_date: date | None = None,
    status: InconsistencyStatus | None = None,
    inconsistency_type: InconsistencyType | None = None,
    entity_type: EntityType | None = None,
    concept_id: str | None = None,
) -> list[Inconsistency]:
    with staging_session() as session:
        records = inconsistency_repository.get_findings(
            session,
            effective_date=effective_date.isoformat() if effective_date else None,
            status=status.value if status else None,
            inconsistency_type=inconsistency_type.value if inconsistency_type else None,
            entity_type=entity_type.value if entity_type else None,
            concept_id=concept_id,
        )
    return [to_model(record) for record in records]


def get_finding(uid: str) -> Inconsistency:
    with staging_session() as session:
        record = require_finding(session, uid)
    return to_model(record)


def resolve(uid: str, resolution: ResolutionInput) -> Inconsistency:
    """Settles one review item, optionally remembering the choice as a rule."""

    with staging_session() as session:
        record = require_finding(session, uid)
        guard_release_not_imported(session, record["effective_date"])

        status, decision = resolution_service.decide(
            record,
            resolution.strategy,
            author_id=user().id(),
            value=resolution.value,
            catalogue=resolution.catalogue,
            pattern=resolution.pattern,
            steps=tuple((s.pattern, s.replacement) for s in resolution.steps),
            title_case=resolution.title_case,
            note=resolution.note,
        )
        guard_sponsor_term_is_free(resolution.strategy, decision)

        # Built and checked before anything is written. Each repository call commits on
        # its own, so validating after recording the decision would leave the item
        # settled, its release's open count stale, and the caller holding a 400 that
        # says none of it happened.
        rule = (
            rule_from_resolution(record, resolution)
            if resolution.save_as_rule
            else None
        )
        if rule is not None:
            resolution_service.validate_rule(rule)

        updated = require_updated(
            inconsistency_repository.record_decision(
                session, uid, status.value, decision
            ),
            uid,
        )

        if rule is not None:
            rules_repository.upsert_rule(session, rule)
            log.info("Stored rule %s from resolution of %s", rule["uid"], uid)

        refresh_open_count(session, record["effective_date"])

    return to_model(updated)


def unresolve(uid: str) -> Inconsistency:
    """Takes back a decision, putting the item back in the queue."""

    with staging_session() as session:
        record = require_finding(session, uid)
        guard_release_not_imported(session, record["effective_date"])
        updated = require_updated(
            inconsistency_repository.clear_decision(
                session,
                uid,
                sorted(INFORMATIONAL_TYPES),
                sorted(TIER_DEPENDENT_TYPES),
            ),
            uid,
        )
        refresh_open_count(session, record["effective_date"])

    return to_model(updated)


def list_rules() -> list[ResolutionRule]:
    with staging_session() as session:
        rules_repository.ensure_seed_data(session)
        records = rules_repository.get_rules(session)
    return [rule_to_model(record) for record in records]


def create_rule(rule_input: ResolutionRuleInput) -> ResolutionRule:
    rule = rule_input.model_dump()
    rule["entity_type"] = _enum_value(rule_input.entity_type)
    rule["inconsistency_type"] = _enum_value(rule_input.inconsistency_type)
    rule["match_tier"] = _enum_value(rule_input.match_tier)
    rule["scope"] = rule_input.scope.value
    rule["strategy"] = rule_input.strategy.value
    rule["effective_date"] = (
        rule_input.effective_date.isoformat() if rule_input.effective_date else None
    )
    rule["author_id"] = user().id()
    rule["steps"] = [
        step if isinstance(step, dict) else step.model_dump()
        for step in rule.get("steps") or []
    ]
    rule["uid"] = resolution_service.build_rule_uid(rule)
    resolution_service.validate_rule(rule)

    with staging_session() as session:
        record = rules_repository.upsert_rule(session, rule)
    return rule_to_model(record)


def update_rule(uid: str, update: ResolutionRuleUpdate) -> ResolutionRule:
    """Changes what a rule does, leaving what it matches on alone."""

    with staging_session() as session:
        record = rules_repository.find_rule(session, uid)
        if record is None:
            raise NotFoundException(msg=f"No resolution rule with uid '{uid}'.")

        rule = dict(record)
        for field, value in update.model_dump(exclude_unset=True).items():
            rule[field] = (
                value.value if isinstance(value, ResolutionStrategy) else value
            )
        resolution_service.validate_rule(rule)

        updated = rules_repository.upsert_rule(session, rule)
    return rule_to_model(updated)


def get_rule(uid: str) -> ResolutionRule:
    with staging_session() as session:
        record = rules_repository.find_rule(session, uid)
        if record is None:
            raise NotFoundException(msg=f"No resolution rule with uid '{uid}'.")
    return rule_to_model(record)


def delete_rule(uid: str) -> None:
    with staging_session() as session:
        if rules_repository.find_rule(session, uid) is None:
            raise NotFoundException(msg=f"No resolution rule with uid '{uid}'.")
        rules_repository.delete_rule(session, uid)


def get_resolution_options() -> ResolutionOptions:
    """The strategy menu per kind of finding, as the resolution endpoint enforces it."""

    return ResolutionOptions(
        strategies=[
            StrategyDescription(
                strategy=strategy,
                description=resolution_service.STRATEGY_DESCRIPTIONS[strategy],
                needs=list(resolution_service.STRATEGY_INPUTS.get(strategy, ())),
                can_save_as_rule=(
                    strategy not in resolution_service.NOT_SAVEABLE_FROM_A_RESOLUTION
                ),
            )
            for strategy in ResolutionStrategy
        ],
        by_type={
            kind: list(resolution_service.strategies_for(kind))
            for kind in resolution_service.STRATEGIES_BY_TYPE
        },
        by_type_and_tier={
            kind: {
                tier: list(resolution_service.strategies_for(kind, tier.value))
                for tier in MatchTier
            }
            for kind in InconsistencyType
            if kind.value in TIER_DEPENDENT_TYPES
        },
        raised_by={kind: review_pass_of(kind) for kind in InconsistencyType},
    )


def get_catalogue_priority() -> list[CataloguePriorityEntry]:
    with staging_session() as session:
        rules_repository.ensure_seed_data(session)
        records = rules_repository.get_catalogue_priority(session)
    return [CataloguePriorityEntry(**record) for record in records]


def set_catalogue_priority(
    priority: CataloguePriorityInput,
) -> list[CataloguePriorityEntry]:
    duplicates = {
        name for name in priority.catalogues if priority.catalogues.count(name) > 1
    }
    ValidationException.raise_if(
        duplicates,
        msg=f"Each catalogue may appear once; repeated: {sorted(duplicates)}.",
    )

    with staging_session() as session:
        records = rules_repository.set_catalogue_priority(session, priority.catalogues)
    return [CataloguePriorityEntry(**record) for record in records]


def guard_known_catalogues(session: Any, catalogues: list[str]) -> None:
    """Refuses a name that names no catalogue in the pecking order.

    A flag on an unknown catalogue would silently match nothing — visible here, rather
    than discovered later as a mandatory or expected-workbook setting that never took
    effect.
    """

    known = {
        row["catalogue_name"]
        for row in rules_repository.get_catalogue_priority(session)
    }
    unknown = set(catalogues) - known
    ValidationException.raise_if(
        unknown,
        msg=f"Unknown catalogues: {sorted(unknown)}. Add them to the catalogue "
        "pecking order first (PUT /config/catalogue-priority).",
    )


def set_mandatory_catalogues(
    catalogues: MandatoryCataloguesInput,
) -> list[CataloguePriorityEntry]:
    with staging_session() as session:
        rules_repository.ensure_seed_data(session)
        guard_known_catalogues(session, catalogues.catalogues)
        records = rules_repository.set_mandatory_catalogues(
            session, catalogues.catalogues
        )
    return [CataloguePriorityEntry(**record) for record in records]


def set_expected_workbook_catalogues(
    catalogues: ExpectedWorkbooksInput,
) -> list[CataloguePriorityEntry]:
    with staging_session() as session:
        rules_repository.ensure_seed_data(session)
        guard_known_catalogues(session, catalogues.catalogues)
        records = rules_repository.set_expected_workbook_catalogues(
            session, catalogues.catalogues
        )
    return [CataloguePriorityEntry(**record) for record in records]


def get_import_enabled() -> ImportEnabled:
    with staging_session() as session:
        return ImportEnabled(enabled=rules_repository.get_import_enabled(session))


def set_import_enabled(setting: ImportEnabled) -> ImportEnabled:
    with staging_session() as session:
        return ImportEnabled(
            enabled=rules_repository.set_import_enabled(session, setting.enabled)
        )


def rule_from_resolution(
    finding: dict[str, Any], resolution: ResolutionInput
) -> dict[str, Any]:
    """Turns a one-off decision into a standing one at the requested breadth."""

    available = {
        "entity_type": finding["entity_type"],
        "concept_id": finding["concept_id"],
        "related_concept_id": finding.get("related_concept_id"),
        "property": finding.get("property"),
        "effective_date": finding["effective_date"],
        "inconsistency_type": finding["type"],
        "match_tier": finding.get("match_tier"),
    }
    rule: dict[str, Any] = {
        "scope": resolution.rule_scope.value,
        "strategy": resolution.strategy.value,
        "value": resolution.value,
        "pattern": resolution.pattern,
        "steps": [step.model_dump() for step in resolution.steps],
        "title_case": resolution.title_case,
        "when": None,
        "priority": 100,
        "in_codelist_id": None,
        "catalogue": resolution.catalogue,
        "enabled": True,
        "note": resolution.note,
        "author_id": user().id(),
        "entity_type": None,
        "concept_id": None,
        "related_concept_id": None,
        "property": None,
        "effective_date": None,
        "inconsistency_type": None,
    }
    for field in RULE_DISCRIMINATORS_BY_SCOPE[resolution.rule_scope]:
        rule[field] = available[field]

    rule["uid"] = resolution_service.build_rule_uid(rule)
    return rule


def require_finding(session, uid: str) -> dict[str, Any]:
    record = inconsistency_repository.find_finding(session, uid)
    if record is None:
        raise NotFoundException(msg=f"No review item with uid '{uid}'.")
    return record


def require_updated(record: dict[str, Any] | None, uid: str) -> dict[str, Any]:
    """Guards the write-then-read-back of a review item.

    The item was there a moment ago, so an empty result means it was removed
    concurrently — worth saying plainly rather than failing on a None later.
    """

    if record is None:
        raise NotFoundException(
            msg=f"Review item '{uid}' disappeared while it was being updated."
        )
    return record


def describe_usage(usage: list[dict[str, Any]]) -> str:
    """The references to a term, as something a person can go and act on."""

    return "; ".join(
        f"{entry['count']}x {entry['relationship']} from "
        f"{'/'.join(entry['consumer_labels'])}"
        for entry in sorted(usage, key=lambda entry: -entry["count"])
    )


def guard_sponsor_term_is_free(
    strategy: ResolutionStrategy, decision: dict[str, Any]
) -> None:
    """Refuses to displace a sponsor term that anything in the database still refers to.

    Checked here rather than trusted from the assessment's `usage_count`, which
    was true whenever that last ran. It is checked again before the import writes
    anything, because it can become false in between.
    """

    if strategy not in resolution_service.NEEDS_AN_UNUSED_TERM:
        return

    term_uid = decision.get("resolved_value")
    if not isinstance(term_uid, str):
        return

    usage = mdr_repository.get_term_usage([term_uid]).get(term_uid) or []
    ValidationException.raise_if(
        usage,
        msg=f"Sponsor term '{term_uid}' is still referred to by {describe_usage(usage)}. "
        "Move that onto the CDISC term through the main API first — taking it out from "
        "under them here would leave those references pointing at something retired.",
    )


def guard_release_not_imported(session, effective_date: str) -> None:
    """Refuses to change a decision once its release has reached MDR."""

    release = staging_repository.find_effective_date(session, effective_date)
    if release is None:
        return
    status = release["status"]
    ValidationException.raise_if(
        status in (EffectiveDateStatus.IMPORTING, EffectiveDateStatus.IMPORTED),
        msg=f"Effective date '{effective_date}' has status '{status}'. "
        "Its review items can no longer be changed; the values they settled are "
        "already in the MDR database.",
    )
    ValidationException.raise_if(
        status in (EffectiveDateStatus.ANALYZING, EffectiveDateStatus.ASSESSING),
        msg=f"Effective date '{effective_date}' has status '{status}'. Another step "
        "is already running against it; wait for that job to finish and try again.",
    )


def refresh_open_count(session, effective_date: str) -> None:
    """Keeps the release's open count and status in step with its review items."""

    counts = inconsistency_repository.count_by_type_and_status(session, effective_date)
    open_count = sum(
        row["count"]
        for row in counts
        if row["status"] == InconsistencyStatus.OPEN.value
    )
    release = staging_repository.find_effective_date(session, effective_date)
    if release is None or release["status"] == EffectiveDateStatus.FILES_STAGED.value:
        # Not analysed yet: leave the release alone, analysis will set both.
        return

    status = EffectiveDateStatus.BLOCKED if open_count else EffectiveDateStatus.ANALYZED
    staging_repository.set_open_inconsistency_count(
        session, effective_date, status.value, open_count
    )


def to_model(record: dict[str, Any]) -> Inconsistency:
    resolution = record.get("resolution")
    return Inconsistency(
        uid=record["uid"],
        effective_date=record["effective_date"],
        type=InconsistencyType(record["type"]),
        entity_type=EntityType(record["entity_type"]),
        concept_id=record["concept_id"],
        related_concept_id=record.get("related_concept_id"),
        property=record.get("property"),
        match_tier=(
            MatchTier(record["match_tier"]) if record.get("match_tier") else None
        ),
        usage_count=record.get("usage_count"),
        status=InconsistencyStatus(record["status"]),
        detected_at=to_native(record["detected_at"]),
        candidates=[
            CandidateValue(
                value=c.get("value"),
                catalogues=c.get("catalogues") or [],
                source=c.get("source"),
                # Read with the resolver's own parser, so it offers exactly what it accepts.
                sponsor_term_uid=resolution_service.sponsor_uid(c.get("value")),
            )
            for c in record.get("candidates") or []
        ],
        codelist_ids=record.get("codelist_ids") or [],
        submission_values=dict(
            zip(record.get("codelist_ids") or [], record.get("submission_values") or [])
        ),
        resolution=(
            ResolutionDecision(
                strategy=ResolutionStrategy(resolution["strategy"]),
                resolved_value=resolution.get("resolved_value"),
                chosen_catalogue=resolution.get("chosen_catalogue"),
                author_id=resolution["author_id"],
                decided_at=to_native(resolution["decided_at"]),
                note=resolution.get("note"),
                rule_uid=resolution.get("rule_uid"),
            )
            if resolution
            else None
        ),
    )


def rule_to_model(record: dict[str, Any]) -> ResolutionRule:
    return ResolutionRule(
        uid=record["uid"],
        scope=RuleScope(record["scope"]),
        strategy=ResolutionStrategy(record["strategy"]),
        entity_type=(
            EntityType(record["entity_type"]) if record.get("entity_type") else None
        ),
        concept_id=record.get("concept_id"),
        property=record.get("property"),
        effective_date=record.get("effective_date"),
        inconsistency_type=(
            InconsistencyType(record["inconsistency_type"])
            if record.get("inconsistency_type")
            else None
        ),
        match_tier=(
            MatchTier(record["match_tier"]) if record.get("match_tier") else None
        ),
        related_concept_id=record.get("related_concept_id"),
        in_codelist_id=record.get("in_codelist_id"),
        value=record.get("value"),
        pattern=record.get("pattern"),
        steps=[RewriteStep(**step) for step in record.get("steps") or []],
        when=record.get("when"),
        title_case=bool(record.get("title_case")),
        priority=int(record["priority"]) if record.get("priority") is not None else 100,
        catalogue=record.get("catalogue"),
        enabled=record.get("enabled", True),
        author_id=record["author_id"],
        created_at=to_native(record["created_at"]),
        note=record.get("note"),
    )


def _enum_value(value: Any) -> Any:
    return value.value if value is not None else None
