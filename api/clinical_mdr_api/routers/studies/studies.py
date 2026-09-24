from typing import Annotated, Any, cast

from dict2xml import DataSorter, dict2xml
from fastapi import APIRouter, BackgroundTasks, Body, Path, Query
from fastapi.responses import Response
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyCompactComponentEnum,
    StudyComponentEnum,
    StudyCopyComponentEnum,
    StudyStatus,
)
from clinical_mdr_api.models.complexity_score import ComplexityScoreDetails
from clinical_mdr_api.models.jobs.job import JobResponse
from clinical_mdr_api.models.study_selections.study import (
    CompactStudy,
    LockReleaseInput,
    Study,
    StudyCloneInput,
    StudyCreateInput,
    StudyFieldAuditTrailEntry,
    StudyIntegrityCheckResponse,
    StudyMinimal,
    StudyOtherAttribute,
    StudyOtherAttributeBatchInput,
    StudyOtherAttributeBatchOutput,
    StudyOtherAttributeInput,
    StudyOtherAttributePatchInput,
    StudyPatchRequestJsonModel,
    StudyPreferredTimeUnit,
    StudyPreferredTimeUnitInput,
    StudyProtocolHeaderVersion,
    StudyProtocolTitle,
    StudySelectionContainmentResult,
    StudySimple,
    StudySoaPreferences,
    StudySoaPreferencesInput,
    StudySoaSplit,
    StudySoaSplitInput,
    StudyStructureOverview,
    StudyStructureStatistics,
    StudySubpartAuditTrail,
    StudySubpartCreateInput,
    StudySubpartReorderingInput,
    StudyTemplate,
    StudyTemplateInput,
    StudyTemplatePatchInput,
    StudyVersionHistory,
    UnlockInput,
)
from clinical_mdr_api.models.study_selections.study_pharma_cm import StudyPharmaCM
from clinical_mdr_api.models.utils import CustomPage, EditInputModel
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers._generic_descriptions import (
    study_fields_audit_trail_section_description,
    study_section_description,
)
from clinical_mdr_api.services.studies.complexity_score import ComplexityScoreService
from clinical_mdr_api.services.studies.study import (
    StudyService,
    validate_if_study_is_not_locked,
)
from clinical_mdr_api.services.studies.study_pharma_cm import StudyPharmaCMService
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.exceptions import NotFoundException, ValidationException
from common.models.error import ErrorResponse

# Prefixed with "/studies"
router = APIRouter()

StudyUID = Path(description="The unique id of the study.")
TargetStudyUID = Path(
    description="The unique id of the target study (e.g. a clone). "
    "Only selection labels that appear on this study are included in the comparison."
)


@router.get(
    "",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns all studies in their latest/newest version.",
    description=f"""
Allowed parameters include : filter on fields, sort by field name with sort direction, pagination

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "current_metadata.identification_metadata.clinical_programme_name",
            "current_metadata.identification_metadata.project_number",
            "current_metadata.identification_metadata.project_name",
            "current_metadata.identification_metadata.study_number",
            "current_metadata.identification_metadata.study_id",
            "current_metadata.identification_metadata.study_acronym",
            "current_metadata.identification_metadata.study_subpart_acronym",
            "current_metadata.study_description.study_title",
            "current_metadata.version_metadata.study_status",
            "current_metadata.version_metadata.version_timestamp",
            "current_metadata.version_metadata.version_author",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_all(
    request: Request,  # request is actually required by the allow_exports decorator
    include_sections: Annotated[
        list[StudyCompactComponentEnum] | None,
        Query(
            description="""Optionally specify a list of sections to include from the StudyDefinition.

        Valid values are:

        - identification_metadata
        - version_metadata
        - study_description

        If no filters are specified, the default sections are returned.""",
        ),
    ] = None,
    exclude_sections: Annotated[
        list[StudyCompactComponentEnum] | None,
        Query(
            description="""Optionally specify a list of sections to exclude from the StudyDefinition.

        Valid values are:

        - identification_metadata
        - version_metadata
        - study_description

        If no filters are specified, the default sections are returned.""",
        ),
    ] = None,
    has_study_objective: Annotated[
        bool | None,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Optionally, filter studies based on the existence of related Study Objectives or not",
        ),
    ] = None,
    has_study_footnote: Annotated[
        bool | None,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Optionally, filter studies based on the existence of related Study SoA Footnotes or not",
        ),
    ] = None,
    has_study_endpoint: Annotated[
        bool | None,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Optionally, filter studies based on the existence of related Study Endpoints or not",
        ),
    ] = None,
    has_study_criteria: Annotated[
        bool | None,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Optionally, filter studies based on the existence of related Study Criteria or not",
        ),
    ] = None,
    has_study_activity: Annotated[
        bool | None,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Optionally, filter studies based on the existence of related Study Activities or not",
        ),
    ] = None,
    has_study_activity_instruction: Annotated[
        bool | None,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Optionally, filter studies based on the existence of related sTudy Activity Instruction or not",
        ),
    ] = None,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    deleted: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Indicates whether to return 'Active' Studies or 'Deleted' ones.",
        ),
    ] = False,
) -> CustomPage[CompactStudy]:
    study_service = StudyService()
    results = study_service.get_all(
        include_sections=include_sections,
        exclude_sections=exclude_sections,
        has_study_footnote=has_study_footnote,
        has_study_objective=has_study_objective,
        has_study_endpoint=has_study_endpoint,
        has_study_criteria=has_study_criteria,
        has_study_activity=has_study_activity,
        has_study_activity_instruction=has_study_activity_instruction,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
        deleted=deleted,
    )

    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/list",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns a list of studies with their ids and acronyms.",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "id",
            "acronym",
            "number",
            "title",
            "description",
            "subpart_id",
            "subpart_acronym",
            "clinical_programme=clinical_programme_name",
            "project_number",
            "project_name",
            "status=version_status",
            "modified=version_start_date",
            "modified_by=version_author",
            "latest_version_number=version_number",
            "latest_locked_version_number=latest_locked_version.version_number",
            "latest_locked_version_description=latest_locked_version.change_description",
            "latest_released_version_number=latest_released_version.version_number",
            "latest_released_version_description=latest_released_version.change_description",
            "data_completeness_tags",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_studies_list(
    request: Request,  # request is actually required by the allow_exports decorator
    minimal_response: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Indicates whether to return minimal response with only `uid`, `id` and `acronym`."
        ),
    ] = True,
    has_study_objective: Annotated[
        bool | None,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Filter studies by Study Objectives presence: `true` (has objectives), `false` (no objectives), or omit (all studies).",
        ),
    ] = None,
    has_study_footnote: Annotated[
        bool | None,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Filter studies by Study Objectives presence: `true` (has objectives), `false` (no objectives), or omit (all studies).",
        ),
    ] = None,
    has_study_endpoint: Annotated[
        bool | None,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Filter studies by Study Endpoints presence: `true` (has endpoints), `false` (no endpoints), or omit (all studies).",
        ),
    ] = None,
    has_study_criteria: Annotated[
        bool | None,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Filter studies by Study Criteria presence: `true` (has criteria), `false` (no criteria), or omit (all studies).",
        ),
    ] = None,
    has_study_activity: Annotated[
        bool | None,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Filter studies by Study Activities presence: `true` (has activities), `false` (no activities), or omit (all studies).",
        ),
    ] = None,
    has_study_activity_instruction: Annotated[
        bool | None,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Filter studies by Study Activity Instructions presence: `true` (has activity instructions), `false` (no activity instructions), or omit (all studies).",
        ),
    ] = None,
    deleted: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Indicates whether to return 'Active' Studies or 'Deleted' ones.",
        ),
    ] = False,
) -> list[StudySimple | StudyMinimal]:
    """
    Returns a list of studies
    """
    study_service = StudyService()
    return study_service.get_studies_list(
        minimal_response=minimal_response,
        has_study_objective=has_study_objective,
        has_study_footnote=has_study_footnote,
        has_study_endpoint=has_study_endpoint,
        has_study_criteria=has_study_criteria,
        has_study_activity=has_study_activity,
        has_study_activity_instruction=has_study_activity_instruction,
        deleted=deleted,
    )


@router.get(
    "/template",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns the active study template, if any.",
    status_code=200,
    responses={403: _generic_descriptions.ERROR_403},
)
def get_study_template() -> StudyTemplate | None:
    return StudyService().get_study_template()


@router.post(
    "/template",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Creates the study template configuration.",
    status_code=201,
    responses={
        400: _generic_descriptions.ERROR_400,
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def create_study_template(
    study_template_input: Annotated[
        StudyTemplateInput, Body(description="Study template target study reference.")
    ],
) -> StudyTemplate:
    return StudyService().create_study_template(study_template_input)


@router.patch(
    "/template",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Updates the study template with a new version.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: _generic_descriptions.ERROR_400,
        404: _generic_descriptions.ERROR_404,
    },
)
def patch_study_template(
    patch_input: Annotated[
        StudyTemplatePatchInput, Body(description="Updated study template target.")
    ],
) -> StudyTemplate:
    return StudyService().patch_study_template(patch_input)


@router.delete(
    "/template/activations",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Retires the current study template.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def retire_study_template(
    _: Annotated[
        EditInputModel | None,
        Body(description="Optional change description payload.", embed=False),
    ] = None,
) -> StudyTemplate:
    return StudyService().retire_study_template()


@router.post(
    "/template/activations",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Reactivates a retired study template.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def reactivate_study_template(
    _: Annotated[
        EditInputModel | None,
        Body(description="Optional change description payload.", embed=False),
    ] = None,
) -> StudyTemplate:
    return StudyService().reactivate_study_template()


@router.get(
    "/structure-overview",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns an overview of study structure of all studies.",
    description=f"""
Allowed parameters include : filter on fields, sort by field name with sort direction, pagination

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "study_id",
            "arms",
            "pre_treatment_epochs",
            "treatment_epochs",
            "no_treatment_epochs",
            "post_treatment_epochs",
            "treatment_elements",
            "no_treatment_elements",
            "cohorts_in_study",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_study_structure_overview(
    request: Request,  # request is actually required by the allow_exports decorator
    sort_by: Annotated[Json, _generic_descriptions.SORT_BY_QUERY] = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[StudyStructureOverview]:
    study_service = StudyService()
    results = study_service.get_study_structure_overview(
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
    )

    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/structure-overview/headers",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns possibles values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
    },
)
def get_study_structure_overview_header(
    field_name: _generic_descriptions.HEADER_FIELD_NAME_QUERY,
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    study_service = StudyService()
    return study_service.get_study_structure_overview_header(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/headers",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns possibles values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
    },
)
def get_distinct_values_for_header(
    field_name: _generic_descriptions.HEADER_FIELD_NAME_QUERY,
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    study_service = StudyService()
    return study_service.get_distinct_values_for_header(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.post(
    "/{study_uid}/locks",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Locks a Study with specified uid",
    description="The Study is locked, which means that the LATEST_LOCKED relationship in the database is created."
    "The first locked version obtains number '1' and each next locked version "
    "is incremented number of the last locked version. "
    "The Study exists in the LOCKED state after successful lock",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: {
            "model": ErrorResponse,
            "description": "ValidationException - The business rules were not met",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid'.",
        },
    },
)
def lock(
    study_uid: Annotated[str, StudyUID],
    lock_description: Annotated[
        LockReleaseInput,
        Body(
            description="The data (reason_for_lock and description) needed for locked version."
        ),
    ],
) -> Study:
    study_service = StudyService()
    return study_service.lock(
        uid=study_uid,
        change_description=lock_description.change_description,
        other_reason_for_locking=lock_description.other_reason_for_locking_releasing,
        reason_for_lock_term_uid=lock_description.reason_for_change_uid,
        protocol_header_major_version=lock_description.protocol_header_major_version,
        protocol_header_minor_version=lock_description.protocol_header_minor_version,
    )


@router.post(
    "/{study_uid}/unlocks",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Unlocks a Study with specified uid",
    description="The Study is unlocked, which means that the new DRAFT version of a Study is created"
    " and the Study exists in the DRAFT state.",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: {
            "model": ErrorResponse,
            "description": "ValidationException - The business rules were not met",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid'.",
        },
    },
)
def unlock(
    study_uid: Annotated[str, StudyUID],
    lock_description: Annotated[
        UnlockInput,
        Body(
            description="The data (reason_for_unlock and description) needed for unlocked version."
        ),
    ],
) -> Study:
    study_service = StudyService()
    return study_service.unlock(
        uid=study_uid,
        reason_for_unlock_term_uid=lock_description.reason_for_change_uid,
        other_reason_for_unlocking=lock_description.other_reason_for_unlocking,
    )


@router.post(
    "/{study_uid}/release",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Releases a Study with specified uid",
    description="The Study is released, which means that 'snapshot' of the Study is created in the database"
    "and the LATEST_RELEASED relationship is created that points to the created snapshot."
    "What's more the new LATEST_DRAFT node is created that describes the new Draft Study after releasing.",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: {
            "model": ErrorResponse,
            "description": "ValidationException - The business rules were not met",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid'.",
        },
    },
)
def release(
    study_uid: Annotated[str, StudyUID],
    release_description: Annotated[
        LockReleaseInput,
        Body(
            description="The data (reason_for_release and description) needed for released version."
        ),
    ],
) -> Study:
    study_service = StudyService()
    return study_service.release(
        uid=study_uid,
        other_reason_for_releasing=release_description.other_reason_for_locking_releasing,
        change_description=release_description.change_description,
        reason_for_release_uid=release_description.reason_for_change_uid,
        protocol_header_major_version=release_description.protocol_header_major_version,
        protocol_header_minor_version=release_description.protocol_header_minor_version,
    )


@router.delete(
    "/{study_uid}",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Deletes a Study",
    description="""
State before:
 - uid must exist
 - The Study must be in status Draft and it couldn't be locked before.

Business logic:
 - The draft Study is deleted.

State after:
 - Study is successfully deleted.

Possible errors:
 - Invalid uid or status not Draft or Study was previously locked.
    """,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The Study was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "ValidationException - The business rules were not met",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid'.",
        },
    },
)
def delete_study(study_uid: Annotated[str, StudyUID]):
    study_service = StudyService()
    study_service.soft_delete(uid=study_uid)


@router.get(
    "/{study_uid}/integrity-check",
    dependencies=[security, rbac.STUDY_READ],
    summary="Run integrity checks for a specific study",
    description="Executes database integrity checks for the specified study and returns detailed results including all checks and non-compliant entities.",
    response_model=StudyIntegrityCheckResponse,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def run_integrity_check_for_study(
    study_uid: Annotated[str, StudyUID],
) -> StudyIntegrityCheckResponse:
    """Run integrity checks for a specific study and return detailed results."""
    study_service = StudyService()
    return study_service.run_integrity_check_for_study(study_uid=study_uid)


@router.get(
    "/{study_uid}",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns the current state of a specific study definition identified by 'study_uid'.",
    description="If multiple request query parameters are used, then they need to match all at the same time"
    " (they are combined with the AND operation).",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid'"
            " (and the specified date/time and/or status) wasn't found.",
        },
    },
)
def get(
    study_uid: Annotated[str, StudyUID],
    include_sections: Annotated[
        list[StudyComponentEnum] | None,
        Query(description=study_section_description("include")),
    ] = None,
    exclude_sections: Annotated[
        list[StudyComponentEnum] | None,
        Query(description=study_section_description("exclude")),
    ] = None,
    status: Annotated[
        StudyStatus | None,
        Query(
            description="If specified, the last representation of the study in that status is returned (if existent)."
            "Valid values are: 'Released', 'Draft' or 'Locked'.",
        ),
    ] = None,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> Study:
    study_service = StudyService()
    study_definition = study_service.get_by_uid(
        uid=study_uid,
        include_sections=include_sections,
        exclude_sections=exclude_sections,
        at_specified_date_time=None,
        status=status,
        study_value_version=study_value_version,
    )
    return study_definition


@router.get(
    "/{study_uid}/structure-statistics",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns various statistics about the structure of the study identified by 'study_uid'.",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid'.",
        },
    },
)
def get_structure_statistics(
    study_uid: Annotated[str, StudyUID],
) -> StudyStructureStatistics:
    study_service = StudyService()
    return study_service.get_study_structure_statistics(study_uid)


@router.get(
    "/{study_uid}/study-selection-containment/{target_study_uid}",
    dependencies=[security, rbac.STUDY_READ],
    summary=(
        "Whether target study selection statistics are contained in the source study."
    ),
    description=(
        "Compares selection counts (and distinct CT term roots) for each concrete "
        "selection label that appears on **target_study_uid** against **study_uid** "
        "(source). Returns whether target counts are <= source for every such label, "
        "plus per-label figures. **StudySoAFootnote** is excluded (conditional clone "
        "rules make footnote counts incomparable)."
    ),
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - source or target study uid.",
        },
    },
)
def get_study_selection_containment(
    study_uid: Annotated[str, StudyUID],
    target_study_uid: Annotated[str, TargetStudyUID],
) -> StudySelectionContainmentResult:
    study_service = StudyService()
    return study_service.get_study_selection_containment(
        source_study_uid=study_uid,
        target_study_uid=target_study_uid,
    )


@router.get(
    "/{study_uid}/pharma-cm",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns the pharma-cm represention of study identified by 'study_uid'.",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid'"
            " (and the specified date/time and/or status) wasn't found.",
        },
    },
)
def get_pharma_cm_representation(
    study_uid: Annotated[str, StudyUID],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> StudyPharmaCM:
    StudyService().check_if_study_uid_and_version_exists(
        study_uid=study_uid, study_value_version=study_value_version
    )
    study_pharma_service = StudyPharmaCMService()
    study_pharma = study_pharma_service.get_pharma_cm_representation(
        study_uid=study_uid,
        study_value_version=study_value_version,
    )
    return study_pharma


@router.get(
    "/{study_uid}/pharma-cm.xml",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns the pharma-cm represention of study identified by 'study_uid' in the xml format.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"content": {"text/xml": {}}},
        404: _generic_descriptions.ERROR_404,
    },
)
def get_pharma_cm_xml_representation(
    study_uid: Annotated[str, StudyUID],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> Response:
    StudyService().check_if_study_uid_and_version_exists(
        study_uid=study_uid, study_value_version=study_value_version
    )
    study_pharma_service = StudyPharmaCMService()
    study_pharma: dict[str, Any] = study_pharma_service.get_pharma_cm_xml(
        study_uid=study_uid,
        study_value_version=study_value_version,
    )
    response = Response(
        dict2xml(
            study_pharma,
            indent="  ",
            closed_tags_for=[None],
            data_sorter=cast(DataSorter | None, DataSorter.never()),
        ),
        media_type="text/xml",
        headers={
            "Content-Disposition": "attachment; filename=export.xml",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'",
        },
    )
    return response


@router.patch(
    "/{study_uid}",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Request to change some aspects (parts) of a specific study definition identified by 'study_uid'.",
    description="The request to change (some aspect) of the state of current aggregate. "
    "There are some special cases and considerations:\n"
    "* patching study_status in current_metadata.version_metadata is considered as the request for"
    "  locking/unlocking/releasing the study definition and should not be combined with any other"
    "  changes\n"
    "* there are many business rules that apply in different patching scenario or state of the"
    "  study definition. If request is not compliant it will fail with 403 and response body"
    "  will (hopefully) explain what is wrong.\n"
    "* the method may be invoked with dry=true query param. if that's the case it wokrs the same"
    "  except that any change made to the resource are not persisted (however all validations are"
    "  performed.\n",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid to process the request. Expect more detailed"
            " information in response body.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid'.",
        },
    },
)
def patch(
    study_uid: Annotated[str, StudyUID],
    study_patch_request: Annotated[
        StudyPatchRequestJsonModel,
        Body(
            description="The request with the structure similar to the GET /{study_uid} response. Carrying only those"
            "fields requested to change.",
        ),
    ],
    dry: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="If specified the operation does full validation and returns either 200 or 403 but"
            "nothing is persisted.",
        ),
    ] = False,
) -> Study:
    study_service = StudyService()

    ValidationException.raise_if(
        study_patch_request is None, msg="No data to patch was provided."
    )

    response = study_service.patch(study_uid, dry, study_patch_request)
    return response


@router.get(
    "/{study_uid}/snapshot-history",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns the history of study snapshot definitions",
    description="It returns the history of changes made to the specified Study Definition Snapshot."
    "The returned history should reflect HAS_VERSION relationships in the database between StudyRoot and StudyValue nodes",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid'"
            " (and the specified date/time and/or status) wasn't found.",
        },
    },
)
def get_snapshot_history(
    study_uid: Annotated[str, StudyUID],  # ,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    only_latest_major_protocol_version: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Indicates whether Study snapshots without protocol header version should be returned",
        ),
    ] = False,
) -> CustomPage[StudyVersionHistory]:
    study_service = StudyService()
    snapshot_history = study_service.get_study_snapshot_history(
        study_uid=study_uid,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        only_latest_major_protocol_version=only_latest_major_protocol_version,
    )
    return CustomPage(
        items=snapshot_history.items,
        total=snapshot_history.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/{study_uid}/protocol-header-versions",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns the latest available protocol header version and whether the study contains a 'Final Protocol' locked version.",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid'",
        },
    },
)
def get_protocol_header_version(
    study_uid: Annotated[str, StudyUID],
) -> StudyProtocolHeaderVersion:
    return StudyService().get_protocol_header_version(study_uid=study_uid)


@router.get(
    "/{study_uid}/fields-audit-trail",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns the audit trail for the fields of a specific study definition identified by 'study_uid'.",
    description="Actions on the study are grouped by date of edit."
    "Optionally select which subset of fields should be reflected in the audit trail.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid'"
            " wasn't found.",
        },
    },
)
def get_fields_audit_trail(
    study_uid: Annotated[str, StudyUID],  # ,
    include_sections: Annotated[
        list[StudyComponentEnum] | None,
        Query(description=study_fields_audit_trail_section_description("include")),
    ] = None,
    exclude_sections: Annotated[
        list[StudyComponentEnum] | None,
        Query(description=study_fields_audit_trail_section_description("exclude")),
    ] = None,
) -> list[StudyFieldAuditTrailEntry]:
    study_service = StudyService()
    study_fields_audit_trail = study_service.get_fields_audit_trail_by_uid(
        uid=study_uid,
        include_sections=include_sections,
        exclude_sections=exclude_sections,
    )
    return study_fields_audit_trail


@router.get(
    "/{study_uid}/audit-trail",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns the audit trail for the subparts of a specific study definition identified by 'study_uid'.",
    description="Actions on the study are grouped by date of edit. Optionally select which subset of fields should be reflected in the audit trail.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid'"
            " wasn't found.",
        },
    },
)
def get_study_subpart_audit_trail(
    study_uid: Annotated[str, StudyUID],
    is_subpart: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(),
    ] = False,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[StudySubpartAuditTrail]:
    study_service = StudyService()
    result = study_service.get_subpart_audit_trail_by_uid(
        uid=study_uid,
        is_subpart=is_subpart,
        study_value_version=study_value_version,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
    )
    return CustomPage.create(
        items=result.items,
        total=result.total,
        page=page_number,
        size=page_size,
    )


@router.post(
    "",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Creates a new Study Definition.",
    description="""
If the request succeeds new DRAFT Study Definition will be with initial identification data as provided in 
request body with new unique uid generated and returned in response body.
        """,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The study was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid to process the request. Expect more detailed"
            " information in response body.",
        },
    },
)
def create(
    study_create_input: Annotated[
        StudySubpartCreateInput | StudyCreateInput,
        Body(description="Related parameters of the objective that shall be created."),
    ],
) -> Study:
    study_service = StudyService()
    return study_service.create(study_create_input)


@router.post(
    "/{study_uid}/clone",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Creates a cloned Study Definition with selective copying.",
    description="""
Creates a new DRAFT Study Definition by cloning an existing study. 
The client can specify which parts of the study should be copied using the request body.
""",
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The study was successfully cloned."},
        400: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid processing the request.",
        },
    },
)
def clone_study(
    study_uid: str,
    clone_input: StudyCloneInput,
) -> Study:
    study_service = StudyService()
    new_study = study_service.clone_study(
        study_src_uid=study_uid,
        study_clone_input=clone_input,
    )
    return new_study


@router.post(
    "/{study_uid}/clone/async",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Schedules a Study clone as a background job and returns immediately.",
    description="""
Schedules a clone of the specified Study Definition as a background job, then
returns HTTP 207 with a `Job` describing the in-flight work. Clients should poll
`GET /jobs/{uid}` to observe completion. On success, the job's `response` field
contains the same `Study` payload that the synchronous `/clone` endpoint would
have returned.

Use this endpoint when the synchronous `/clone` is likely to exceed the API
gateway's request timeout.
""",
    status_code=202,
    responses={
        202: {
            "description": "The clone job has been started in the background. "
            "Poll GET /jobs/{uid} for status and result.",
        },
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
        400: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid processing the request.",
        },
    },
)
def clone_study_async(
    study_uid: str,
    clone_input: StudyCloneInput,
    background_tasks: BackgroundTasks,
) -> JobResponse:
    # pylint: disable=unexpected-keyword-arg
    # `background_tasks` is consumed by the @background_job decorator on the
    # service method; pylint can't see through functools.wraps.
    #
    # Building a human-readable job name up front requires knowing the source
    # study's id/acronym. Look it up here so a bad `study_uid` fails fast with
    # a clean 404 rather than crashing the background worker later.
    service = StudyService()
    existing_studies = service.get_studies_list()
    src_study = next((s for s in existing_studies if s.uid == study_uid), None)
    NotFoundException.raise_if(src_study is None, "Study Definition", study_uid)
    # mypy: NotFoundException.raise_if guarantees `src_study` is not None below
    assert src_study is not None

    src_study_id = src_study.id or src_study.acronym or src_study.uid
    target_study_id = (
        f"{clone_input.project_number}-{clone_input.study_number}"
        if clone_input.project_number and clone_input.study_number
        else clone_input.study_acronym
    )

    return service.clone_study_async(
        study_src_uid=study_uid,
        study_clone_input=clone_input,
        background_tasks=background_tasks,  # type: ignore[call-arg]
        job_name=f"Clone study {src_study_id} to {target_study_id}",
    )


@router.get(
    "/{study_uid}/protocol-title",
    dependencies=[security, rbac.STUDY_READ],
    summary="Retrieve all information related to Protocol Title",
    description="""
State before:
 - Study-uid must exist

Business logic:
 - Retrieve Study title, Universal Trial Number, EudraCT number, IND number, Study phase fields
 - Retrieve all names of study compounds associated to {study_uid} and where type of treatment is equal to Investigational Product

State after:
 - No change
""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid'"
            " wasn't found.",
        },
    },
)
def get_protocol_title(
    study_uid: Annotated[str, StudyUID],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> StudyProtocolTitle:
    study_service = StudyService()
    return study_service.get_protocol_title(
        uid=study_uid, study_value_version=study_value_version
    )


@router.get(
    "/{study_uid}/copy-component",
    dependencies=[security, rbac.STUDY_READ],
    summary="Creates a project of a specific component copy from another study",
    description="""
State before:
 - uid must exist
 - reference_study_uid must exist

Business logic:
 - if overwrite is set to false, then only properties that are not set are copied over to the target Study.
 - if overwrite is set to true, then all the properties from the reference_study_uid Study are copied over to the target Study.

State after:
 - The specific form is copied or projected into a study referenced by uid 'study_uid'.
""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid'"
            " wasn't found.",
        },
    },
)
def copy_simple_form_from_another_study(
    study_uid: Annotated[str, StudyUID],
    reference_study_uid: Annotated[
        str, Query(description="The uid of the study to copy component from")
    ],
    component_to_copy: Annotated[
        StudyCopyComponentEnum,
        Query(description="The uid of the study to copy component from"),
    ],
    overwrite: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Indicates whether to overwrite the component of the study referenced by the uid"
            "or return a projection",
        ),
    ] = False,
) -> Study:
    study_service = StudyService()
    return study_service.copy_component_from_another_study(
        uid=study_uid,
        reference_study_uid=reference_study_uid,
        component_to_copy=component_to_copy,
        overwrite=overwrite,
    )


@router.get(
    "/{study_uid}/time-units",
    dependencies=[security, rbac.STUDY_READ],
    summary="Gets a study preferred time unit",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study or unit definition with the specified 'study_uid'"
            " wasn't found.",
        },
    },
)
def get_preferred_time_unit(
    study_uid: Annotated[str, StudyUID],
    for_protocol_soa: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Whether the preferred time unit is associated with Protocol SoA or not.",
        ),
    ] = False,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> StudyPreferredTimeUnit:
    study_service = StudyService()
    return study_service.get_study_preferred_time_unit(
        study_uid=study_uid,
        for_protocol_soa=for_protocol_soa,
        study_value_version=study_value_version,
    )


@router.patch(
    "/{study_uid}/time-units",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Edits a study preferred time unit",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study or unit definition with the specified 'study_uid'"
            " wasn't found.",
        },
    },
)
def patch_preferred_time_unit(
    study_uid: Annotated[str, StudyUID],
    preferred_time_unit_input: Annotated[
        StudyPreferredTimeUnitInput,
        Body(description="Data needed to create a study preferred time unit"),
    ],
    for_protocol_soa: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="Whether the preferred time unit is associated with Protocol Soa or not.",
        ),
    ] = False,
) -> StudyPreferredTimeUnit:
    study_service = StudyService()
    return study_service.patch_study_preferred_time_unit(
        study_uid=study_uid,
        unit_definition_uid=preferred_time_unit_input.unit_definition_uid,
        for_protocol_soa=for_protocol_soa,
    )


@router.get(
    "/{study_uid}/study-other-attributes",
    dependencies=[security, rbac.STUDY_READ],
    summary="Lists Other Study Attributes (TS parameters) that have a value assigned for the study.",
    description=(
        "Returns one row per Trial Summary parameter CT term (codelists "
        "`C66738` / `C67152`) whose `osb_page_reference` matches "
        "`/study_properties/other_attributes` and that has a "
        "`parameter_value` or `null_flavor` assigned. "
        "Only attributes with an existing selection are returned."
    ),
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study with the specified 'study_uid' wasn't found.",
        },
    },
)
def get_study_other_attributes(
    study_uid: Annotated[str, StudyUID],
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[StudyOtherAttribute]:
    results = StudyService().get_study_other_attributes(
        study_uid=study_uid,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        total_count=total_count,
    )
    return CustomPage(
        items=results.items,
        total=results.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/{study_uid}/study-other-attributes/headers",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns possible values from the database for a given header",
    description="Allowed parameters include : field name for which to get possible "
    "values, search string to provide filtering for the field name, additional filters to apply on other fields",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified or study not found.",
        },
    },
)
def get_distinct_study_other_attribute_values_for_header(
    study_uid: Annotated[str, StudyUID],
    field_name: _generic_descriptions.HEADER_FIELD_NAME_QUERY,
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    return StudyService().get_distinct_other_attribute_values_for_header(
        study_uid=study_uid,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.post(
    "/{study_uid}/study-other-attributes",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Creates a Study Other Attribute selection for a TS parameter CT term.",
    description=(
        "Sets the parameter value (or null flavor) for the given TS parameter "
        "CT term. The CT term must belong to codelists `C66738` / `C67152` and "
        "be configured for the Other Study Attributes page."
    ),
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: {
            "model": ErrorResponse,
            "description": "Bad Request - A selection for this TS parameter already exists.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or TS parameter CT term wasn't found.",
        },
    },
)
def post_study_other_attribute(
    study_uid: Annotated[str, StudyUID],
    attribute_input: Annotated[
        StudyOtherAttributeInput,
        Body(description="TS parameter UID and value/null-flavor to persist."),
    ],
) -> StudyOtherAttribute:
    return StudyService().post_study_other_attribute(
        study_uid=study_uid, attribute_input=attribute_input
    )


@router.patch(
    "/{study_uid}/study-other-attributes/{ts_parameter_term_uid}",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Updates a Study Other Attribute selection.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study, TS parameter CT term, or existing selection wasn't found.",
        },
    },
)
def patch_study_other_attribute(
    study_uid: Annotated[str, StudyUID],
    ts_parameter_term_uid: Annotated[
        str,
        Path(description="UID of the TS parameter CTTermRoot."),
    ],
    attribute_input: Annotated[
        StudyOtherAttributePatchInput,
        Body(description="New value/null-flavor to persist."),
    ],
) -> StudyOtherAttribute:
    return StudyService().patch_study_other_attribute(
        study_uid=study_uid,
        ts_parameter_term_uid=ts_parameter_term_uid,
        attribute_input=attribute_input,
    )


@router.delete(
    "/{study_uid}/study-other-attributes/{ts_parameter_term_uid}",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Deletes a Study Other Attribute selection.",
    description=(
        "Removes the parameter value (and null flavor if set) for the given "
        "TS parameter CT term. The CT term configuration itself is not affected."
    ),
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study, TS parameter CT term, or existing selection wasn't found.",
        },
    },
)
def delete_study_other_attribute(
    study_uid: Annotated[str, StudyUID],
    ts_parameter_term_uid: Annotated[
        str,
        Path(description="UID of the TS parameter CTTermRoot."),
    ],
) -> None:
    StudyService().delete_study_other_attribute(
        study_uid=study_uid,
        ts_parameter_term_uid=ts_parameter_term_uid,
    )


@router.post(
    "/{study_uid}/study-other-attributes/batch",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Batch create/edit/delete of Study Other Attributes.",
    description=(
        "Processes a list of operations (POST, PATCH, DELETE) on Study Other "
        "Attributes in a single transaction. Returns one result per operation."
    ),
    status_code=207,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study wasn't found.",
        },
    },
)
def batch_study_other_attributes(
    study_uid: Annotated[str, StudyUID],
    operations: Annotated[list[StudyOtherAttributeBatchInput], Body()],
) -> list[StudyOtherAttributeBatchOutput]:
    return StudyService().batch_study_other_attributes(
        study_uid=study_uid,
        operations=operations,
    )


@router.patch(
    "/{study_uid}/order",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Reorder Study Subparts within a Study Parent Part",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'study_uid'"
            " wasn't found.",
        },
    },
)
def reorder_study_subparts(
    study_uid: Annotated[str, StudyUID],
    study_subpart_reordering_input: Annotated[
        StudySubpartReorderingInput | None,
        Body(
            description="Specify the Study Subpart to be reordered. "
            "If provided, the specified Study Subpart will be reordered; otherwise, any gaps in the order will be filled.",
        ),
    ] = None,
) -> list[Study]:
    study_service = StudyService()
    return study_service.reorder_study_subparts(
        study_parent_part_uid=study_uid,
        study_subpart_reordering_input=study_subpart_reordering_input,
    )


@router.get(
    "/{study_uid}/soa-preferences",
    dependencies=[security, rbac.STUDY_READ],
    summary="Get study SoA preferences",
    response_model_by_alias=False,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - study with the specified 'study_uid' doesn't exist or has no SoA preferences set",
        },
    },
)
def get_soa_preferences(
    study_uid: Annotated[str, StudyUID],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> StudySoaPreferences:
    study_service = StudyService()
    return study_service.get_study_soa_preferences(
        study_uid=study_uid,
        study_value_version=study_value_version,
    )


@router.patch(
    "/{study_uid}/soa-preferences",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Update study SoA preferences",
    response_model_by_alias=False,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - study with the specified 'study_uid' doesn't exist",
        },
    },
)
def patch_soa_preferences(
    study_uid: Annotated[str, StudyUID],
    soa_preferences: Annotated[
        StudySoaPreferencesInput, Body(description="SoA preferences data")
    ],
) -> StudySoaPreferences:
    study_service = StudyService()
    return study_service.patch_study_soa_preferences(
        study_uid=study_uid,
        soa_preferences=soa_preferences,
    )


@router.get(
    "/{study_uid}/soa-splits",
    dependencies=[security, rbac.STUDY_READ],
    summary="Get SoA split uids",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - study with the specified 'study_uid' doesn't exist or has no SoA splits configured",
        },
    },
)
def get_soa_splits(
    study_uid: Annotated[str, StudyUID],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> list[StudySoaSplit]:
    study_service = StudyService()
    return study_service.get_study_soa_splits(
        study_uid=study_uid,
        study_value_version=study_value_version,
    )


@router.put(
    "/{study_uid}/soa-splits",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Add a uid to SoA splits",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - study with the specified 'study_uid' doesn't exist",
        },
        409: {
            "model": ErrorResponse,
            "description": "Conflict - The uid to add is already in the SoA splits",
        },
    },
)
@validate_if_study_is_not_locked("study_uid", 1)
def put_soa_split(
    study_uid: Annotated[str, StudyUID],
    soa_splits_input: Annotated[
        StudySoaSplitInput, Body(description="SoA split input")
    ],
) -> list[StudySoaSplit]:
    study_service = StudyService()
    return study_service.add_study_soa_split(
        study_uid=study_uid,
        soa_split_input=soa_splits_input,
    )


@router.delete(
    "/{study_uid}/soa-splits/{study_visit_uid}",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Remove a uid from SoA splits",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - study with the specified 'study_uid' doesn't exist",
        },
    },
)
@validate_if_study_is_not_locked("study_uid", 1)
def remove_soa_split(
    study_uid: Annotated[str, StudyUID],
    study_visit_uid: Annotated[str, Path(description="SoA split uid")],
) -> list[StudySoaSplit]:
    study_service = StudyService()
    return study_service.remove_study_soa_split(
        study_uid=study_uid,
        uid=study_visit_uid,
    )


@router.delete(
    "/{study_uid}/soa-splits",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Remove all SoA splits",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - study with the specified 'study_uid' doesn't exist",
        },
    },
)
@validate_if_study_is_not_locked("study_uid", 1)
def remove_soa_splits(
    study_uid: Annotated[str, StudyUID],
) -> None:
    study_service = StudyService()
    study_service.remove_study_soa_splits(
        study_uid=study_uid,
    )


@router.get(
    "/{study_uid}/complexity-score",
    dependencies=[security, rbac.STUDY_READ],
    summary="Get study complexity score",
    response_model_by_alias=False,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - study with the specified 'study_uid' doesn't exist",
        },
    },
)
def get_complexity_score(
    study_uid: Annotated[str, StudyUID],
    study_version_number: Annotated[
        str | None,
        Query(
            description="Study Version Number",
            openapi_examples={"2.1": {"value": "2.1"}},
            alias="study_value_version",
        ),
    ] = None,
) -> float:
    service = ComplexityScoreService()
    return service.calculate_site_complexity_score(
        study_uid=study_uid,
        study_version_number=study_version_number,
    )


@router.get(
    "/{study_uid}/complexity-score-details",
    dependencies=[security, rbac.STUDY_READ],
    summary="Get detailed study complexity score breakdown",
    response_model=ComplexityScoreDetails,
    response_model_by_alias=False,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - study with the specified 'study_uid' doesn't exist",
        },
    },
)
def get_complexity_score_details(
    study_uid: Annotated[str, StudyUID],
    study_version_number: Annotated[
        str | None,
        Query(
            description="Study Version Number",
            openapi_examples={"2.1": {"value": "2.1"}},
            alias="study_value_version",
        ),
    ] = None,
) -> ComplexityScoreDetails:
    service = ComplexityScoreService()
    return service.get_complexity_score_details(
        study_uid=study_uid,
        study_version_number=study_version_number,
    )
