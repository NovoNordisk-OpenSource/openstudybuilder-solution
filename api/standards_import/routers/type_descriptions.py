"""Endpoint explaining the enums shown throughout the review workflow."""

from fastapi import APIRouter, status

from common.auth import rbac
from common.auth.dependencies import security
from standards_import.common import ERROR_RESPONSES
from standards_import.models.type_descriptions import EnumDescription
from standards_import.services import type_descriptions_service

router = APIRouter(tags=["Type descriptions"])


@router.get(
    "/type-descriptions",
    dependencies=[security, rbac.LIBRARY_IMPORT_READ],
    status_code=status.HTTP_200_OK,
    responses=ERROR_RESPONSES,
    summary="Explain the enums shown throughout the review workflow",
    description="""What each `InconsistencyType`, `ResolutionStrategy`, `MatchTier`,
`InconsistencyStatus`, `RuleScope` and `EffectiveDateStatus` value means, for tooltips
and help text around the review screens — `SPONSOR_TERM_SEMANTIC_DUPLICATE` is no
clearer to a reviewer than it is to a newcomer to this codebase.

A `null` against a value means it never had an explanation to give, not that one was
missed — a plain lifecycle step like `EffectiveDateStatus.IMPORTING` speaks for itself.
""",
)
def get_type_descriptions() -> dict[str, EnumDescription]:
    return type_descriptions_service.get_type_descriptions()
