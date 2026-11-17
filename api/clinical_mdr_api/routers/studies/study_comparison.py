from typing import Annotated

from fastapi import Path, Query

from clinical_mdr_api.models.study_selections.study_comparison import StudyComparison
from clinical_mdr_api.models.validators import FLOAT_REGEX
from clinical_mdr_api.routers import _generic_descriptions, study_router as router
from clinical_mdr_api.services.studies.study_comparison import (
    StudyComparisonService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.models.error import ErrorResponse

_VERSION_DESCRIPTION = (
    "Locked or released study version as listed by the study snapshot history (e.g. 1, 2.1), "
    "or 'draft' for the current draft."
)
_VERSION_PATTERN = f"^(draft|{FLOAT_REGEX[1:-1]})$"


@router.get(
    "/studies/{study_uid}/comparison",
    dependencies=[security, rbac.STUDY_READ],
    summary="Compares two versions of the same study",
    description="""
State before:
 - Study must exist and both requested versions must exist.

Business logic:
 - Loads every study component (definition, design, visits, objectives, endpoints, criteria, 
   compounds, activities, schedules, footnotes, ...) for both versions.
 - Items are matched across versions by their identifier and reported as ADDED, REMOVED or MODIFIED.
 - MODIFIED items list every changed field with its old and new value.
 - With include_unchanged=true identical items and fields are returned as well (changed=false / UNCHANGED).
 - Audit properties (start/end dates, author) are ignored, as are fields listed in ignore_fields.

State after:
 - no change.

Possible errors:
 - Invalid study-uid or version.
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study or one of the versions was not found.",
        },
    },
)
def compare_study_versions(
    study_uid: Annotated[str, Path(description="The unique id of the study.")],
    version_a: Annotated[
        str,
        Query(description=_VERSION_DESCRIPTION, pattern=_VERSION_PATTERN),
    ],
    version_b: Annotated[
        str,
        Query(description=_VERSION_DESCRIPTION, pattern=_VERSION_PATTERN),
    ],
    include_unchanged: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="If true, items and fields that are identical in both versions are returned too, "
            "so the complete study can be shown with the differences highlighted."
        ),
    ] = False,
    ignore_fields: Annotated[
        list[str] | None,
        Query(
            description="Field names to leave out of the comparison, e.g. 'uid'. Matches the full dotted "
            "field path or its last segment; '*' wildcards are supported (e.g. '*_uid')."
        ),
    ] = None,
) -> StudyComparison:
    return StudyComparisonService().compare(
        study_uid=study_uid,
        version_a=version_a,
        version_b=version_b,
        include_unchanged=include_unchanged,
        ignore_fields=tuple(ignore_fields or ()),
    )
