"""Endpoints for the standing decisions analysis applies without asking."""

from typing import Annotated

from fastapi import APIRouter, Path, status

from common.auth import rbac
from common.auth.dependencies import security
from standards_import.common import ERROR_RESPONSES, NOT_FOUND_RESPONSES
from standards_import.models.inconsistencies import (
    CataloguePriorityEntry,
    CataloguePriorityInput,
    ExpectedWorkbooksInput,
    ImportEnabled,
    MandatoryCataloguesInput,
    ResolutionRule,
    ResolutionRuleInput,
    ResolutionRuleUpdate,
)
from standards_import.services import inconsistency_service

router = APIRouter(tags=["Resolution rules"])

UID_PATH = Path(description="Uid of the rule")


@router.get(
    "/resolution-rules",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=ERROR_RESPONSES,
    summary="List resolution rules",
    description="""Returns the standing decisions, narrowest first — which is the order
analysis matches them in, so the first rule that applies to a finding is the one that
settles it.
""",
)
def get_resolution_rules() -> list[ResolutionRule]:
    return inconsistency_service.list_rules()


@router.post(
    "/resolution-rules",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
    summary="Add a resolution rule",
    description="""Stores a standing decision.

A rule constrains only the fields it sets and ignores the rest, so `scope` has to pin
down what it claims to — a `CONCEPT` rule without a `concept_id` would quietly apply
everywhere, and is rejected.

The uid is composed from what the rule discriminates on, so saving the same rule twice
updates it rather than stacking a duplicate that would compete with itself.""",
)
def create_resolution_rule(rule: ResolutionRuleInput) -> ResolutionRule:
    return inconsistency_service.create_rule(rule)


@router.get(
    "/resolution-rules/{uid}",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="Get one resolution rule",
)
def get_resolution_rule(uid: Annotated[str, UID_PATH]) -> ResolutionRule:
    return inconsistency_service.get_rule(uid)


@router.patch(
    "/resolution-rules/{uid}",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="Update a resolution rule",
    description="""Changes what a rule does, most usefully `enabled`.

Disabling a rule is how you take a standing decision out of service without losing the
record of it — the seeded rule that names every new term after its CDISC preferred term,
for instance, can be switched off so each one is reviewed by hand instead.

What the rule *matches on* is fixed: those fields compose its uid, so changing them
would be a different rule. Create that one instead.

Takes effect at the next analysis run; decisions already made are not revisited.""",
)
def update_resolution_rule(
    uid: Annotated[str, UID_PATH], update: ResolutionRuleUpdate
) -> ResolutionRule:
    return inconsistency_service.update_rule(uid, update)


@router.delete(
    "/resolution-rules/{uid}",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND_RESPONSES,
    summary="Delete a resolution rule",
    description="""Removes a standing decision.

Items it already settled keep their decisions — those are recorded separately. They are
only re-opened if a later analysis run finds the underlying values have changed.""",
)
def delete_resolution_rule(uid: Annotated[str, UID_PATH]) -> None:
    inconsistency_service.delete_rule(uid)


@router.get(
    "/config/catalogue-priority",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=ERROR_RESPONSES,
    summary="Get the catalogue pecking order",
    description="""The fallback used when catalogues disagree over a value and no rule
applies: the most authoritative catalogue that supplied a value wins.

This is what settles the great majority of disagreements, and matches what the bootstrap
import script does — the difference being that here the order is data you can read and
change rather than a list in Python.""",
)
def get_catalogue_priority() -> list[CataloguePriorityEntry]:
    return inconsistency_service.get_catalogue_priority()


@router.put(
    "/config/catalogue-priority",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_200_OK,
    responses=ERROR_RESPONSES,
    summary="Replace the catalogue pecking order",
    description="""Replaces the order wholesale, so a catalogue left out of the list is
genuinely removed from it.

Takes effect at the next analysis run. Decisions already made are not revisited.""",
)
def set_catalogue_priority(
    priority: CataloguePriorityInput,
) -> list[CataloguePriorityEntry]:
    return inconsistency_service.set_catalogue_priority(priority)


@router.put(
    "/config/mandatory-catalogues",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_200_OK,
    responses=ERROR_RESPONSES,
    summary="Replace the mandatory catalogues",
    description="""Sets which catalogues a release must hold before it can be
analysed — read together with the rest of the pecking order on
`GET /config/catalogue-priority`, under `mandatory`.

Replaces the set wholesale, so a catalogue left out is no longer mandatory. Every name
must already appear in the catalogue pecking order; add it there first.

Takes effect on the next `POST /effective-dates/{date}/analysis` — a release missing
one of these is refused, naming what is missing.""",
)
def set_mandatory_catalogues(
    catalogues: MandatoryCataloguesInput,
) -> list[CataloguePriorityEntry]:
    return inconsistency_service.set_mandatory_catalogues(catalogues)


@router.put(
    "/config/expected-workbooks",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_200_OK,
    responses=ERROR_RESPONSES,
    summary="Replace the catalogues expected to ship a workbook",
    description="""Sets which catalogues usually ship a paired-view workbook alongside
their package files — read together with the rest of the pecking order on
`GET /config/catalogue-priority`, under `expects_workbook`.

Informational only: a workbook is not always published, so this never gates analysis
or import. It exists to be shown to whoever is uploading a release, alongside the
pairing-workbook table.

Replaces the set wholesale. Every name must already appear in the catalogue pecking
order; add it there first.""",
)
def set_expected_workbook_catalogues(
    catalogues: ExpectedWorkbooksInput,
) -> list[CataloguePriorityEntry]:
    return inconsistency_service.set_expected_workbook_catalogues(catalogues)


@router.get(
    "/config/import-enabled",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=ERROR_RESPONSES,
    summary="Is the final import into OSB enabled?",
    description="""Whether a reviewed release may be promoted from staging into the OSB
database. Disabled by default.""",
)
def get_import_enabled() -> ImportEnabled:
    return inconsistency_service.get_import_enabled()


@router.put(
    "/config/import-enabled",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_200_OK,
    responses=ERROR_RESPONSES,
    summary="Enable or disable the final import into OSB",
    description="""Only the promotion from staging to the OSB database is affected: while
disabled, `POST /effective-dates/{date}/import` is refused and the release reports it as
a blocker. Uploading, analysis, sponsor impact assessment and review all remain possible.

Takes effect immediately, including for releases already analysed and reviewed.""",
)
def set_import_enabled(setting: ImportEnabled) -> ImportEnabled:
    return inconsistency_service.set_import_enabled(setting)
