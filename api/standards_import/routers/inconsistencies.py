"""Endpoints for reviewing and settling the disagreements analysis found."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from common.auth import rbac
from common.auth.dependencies import security
from standards_import.common import ERROR_RESPONSES, NOT_FOUND_RESPONSES
from standards_import.models.inconsistencies import (
    EntityType,
    Inconsistency,
    InconsistencyStatus,
    InconsistencyType,
    ResolutionInput,
    ResolutionOptions,
)
from standards_import.services import inconsistency_service

router = APIRouter(prefix="/inconsistencies", tags=["Review items"])

# Not under `/inconsistencies`: it is about no item in particular, and a client wants it
# before it has one in front of it.
options_router = APIRouter(tags=["Review items"])


@options_router.get(
    "/resolution-strategies",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=ERROR_RESPONSES,
    summary="Which strategies settle which kind of review item",
    description="""The menu behind `POST /inconsistencies/{uid}/resolution`: for every kind
of review item, the strategies that can settle it, and for every strategy what it needs
to be given and whether a decision using it may be saved as a rule.

This is the same table the resolution endpoint enforces, so a client that offers exactly
what is listed here will never be refused on the kind of finding alone. It is the first
gate, not the last: a listed strategy can still refuse a particular finding — one value
to accept where there are two, a catalogue that supplied nothing — and says why.

Each kind's list has the usual choice first. That is the only opinion it carries.

`raised_by` says which step raises each kind: `ANALYSIS`
(`POST /effective-dates/{date}/analysis`) or `SPONSOR_IMPACT`
(`POST /effective-dates/{date}/sponsor-impact`). Every `ANALYSIS` kind has to be settled,
and the release re-analysed, before sponsor impact can even be assessed — this is a fixed
property of the kind, not something that varies finding to finding, so it is safe to use
for splitting a queue into two lists before any of it is fetched.""",
)
def get_resolution_strategies() -> ResolutionOptions:
    return inconsistency_service.get_resolution_options()


UID_PATH = Path(description="Uid of the review item")


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=ERROR_RESPONSES,
    summary="List review items",
    description="""Lists what analysis found, across releases or within one.

Filter by `status=OPEN` for the queue that is actually holding a release back —
everything else has already been settled, either by a stored rule or by a person.""",
)
def get_inconsistencies(
    effective_date: Annotated[
        date | None, Query(description="Only items raised for this release")
    ] = None,
    inconsistency_status: Annotated[
        InconsistencyStatus | None,
        Query(alias="status", description="Only items in this state"),
    ] = None,
    inconsistency_type: Annotated[
        InconsistencyType | None,
        Query(alias="type", description="Only items of this kind"),
    ] = None,
    entity_type: Annotated[
        EntityType | None,
        Query(description="Only items about codelists, or about terms"),
    ] = None,
    concept_id: Annotated[
        str | None, Query(description="Only items about this concept")
    ] = None,
) -> list[Inconsistency]:
    return inconsistency_service.list_findings(
        effective_date=effective_date,
        status=inconsistency_status,
        inconsistency_type=inconsistency_type,
        entity_type=entity_type,
        concept_id=concept_id,
    )


@router.get(
    "/{uid}",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="Get one review item",
)
def get_inconsistency(uid: Annotated[str, UID_PATH]) -> Inconsistency:
    return inconsistency_service.get_finding(uid)


@router.post(
    "/{uid}/resolution",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="Settle one review item",
    description="""Records how this disagreement should be settled, and what value that
produces. The value is applied to the grouped concept by the next analysis run.

Set `save_as_rule` to also store the choice as a standing rule, so the same
disagreement is settled automatically next quarter instead of coming back. `rule_scope`
decides how widely that rule reaches — from this one concept and property at this one
release, up to every finding of this kind.

Re-analysis keeps the decision, unless the competing values themselves have changed:
a decision made about different values is discarded rather than silently reapplied.""",
)
def resolve_inconsistency(
    uid: Annotated[str, UID_PATH], resolution: ResolutionInput
) -> Inconsistency:
    return inconsistency_service.resolve(uid, resolution)


@router.delete(
    "/{uid}/resolution",
    dependencies=[security, rbac.LIBRARY_IMPORT_WRITE],
    status_code=status.HTTP_200_OK,
    responses=NOT_FOUND_RESPONSES,
    summary="Take back a decision",
    description="""Removes the decision and puts the item back in the queue.

Any rule saved alongside the original decision is left alone — delete it separately if
the whole standing choice was a mistake, otherwise the next analysis run will simply
settle this item the same way again.""",
)
def unresolve_inconsistency(uid: Annotated[str, UID_PATH]) -> Inconsistency:
    return inconsistency_service.unresolve(uid)
