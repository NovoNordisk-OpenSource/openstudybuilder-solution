from typing import Annotated, Any

from dict2xml import DataSorter, dict2xml
from fastapi import APIRouter, Body, Path, Query, Response
from fastapi import status as response_status
from fastapi.responses import StreamingResponse
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyCompactComponentEnum,
    StudyComponentEnum,
    StudyCopyComponentEnum,
    StudyStatus,
)
from clinical_mdr_api.models.study_selections.study import (
    CompactStudy,
    StatusChangeDescription,
    Study,
    StudyCloneInput,
    StudyCreateInput,
    StudyFieldAuditTrailEntry,
    StudyPatchRequestJsonModel,
    StudyPreferredTimeUnit,
    StudyPreferredTimeUnitInput,
    StudyProtocolTitle,
    StudySoaPreferences,
    StudySoaPreferencesInput,
    StudyStructureOverview,
    StudyStructureStatistics,
    StudySubpartAuditTrail,
    StudySubpartCreateInput,
    StudySubpartReorderingInput,
)
from clinical_mdr_api.models.study_selections.study_pharma_cm import StudyPharmaCM
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers._generic_descriptions import (
    study_fields_audit_trail_section_description,
    study_section_description,
)
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_pharma_cm import StudyPharmaCMService
from common import config
from common.auth import rbac
from common.exceptions import ValidationException
from common.models.error import ErrorResponse

# Prefixed with "/studies"
router = APIRouter()

StudyUID = Path(description="The unique id of the study.")


@router.get(
    "",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all studies in their latest/newest version.",
    description=f"""
Allowed parameters include : filter on fields, sort by field name with sort direction, pagination

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[CompactStudy],
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
        Query(
            description="Optionally, filter studies based on the existence of related Study Objectives or not",
        ),
    ] = None,
    has_study_footnote: Annotated[
        bool | None,
        Query(
            description="Optionally, filter studies based on the existence of related Study SoA Footnotes or not",
        ),
    ] = None,
    has_study_endpoint: Annotated[
        bool | None,
        Query(
            description="Optionally, filter studies based on the existence of related Study Endpoints or not",
        ),
    ] = None,
    has_study_criteria: Annotated[
        bool | None,
        Query(
            description="Optionally, filter studies based on the existence of related Study Criteria or not",
        ),
    ] = None,
    has_study_activity: Annotated[
        bool | None,
        Query(
            description="Optionally, filter studies based on the existence of related Study Activities or not",
        ),
    ] = None,
    has_study_activity_instruction: Annotated[
        bool | None,
        Query(
            description="Optionally, filter studies based on the existence of related sTudy Activity Instruction or not",
        ),
    ] = None,
    sort_by: Annotated[
        Json | None, Query(description=_generic_descriptions.SORT_BY)
    ] = None,
    page_number: Annotated[
        int | None, Query(ge=1, description=_generic_descriptions.PAGE_NUMBER)
    ] = config.DEFAULT_PAGE_NUMBER,
    page_size: Annotated[
        int | None,
        Query(
            ge=0,
            le=config.MAX_PAGE_SIZE,
            description=_generic_descriptions.PAGE_SIZE,
        ),
    ] = config.DEFAULT_PAGE_SIZE,
    filters: Annotated[
        Json | None,
        Query(
            description=_generic_descriptions.FILTERS,
            openapi_examples=_generic_descriptions.FILTERS_EXAMPLE,
        ),
    ] = None,
    operator: Annotated[
        str | None, Query(description=_generic_descriptions.FILTER_OPERATOR)
    ] = config.DEFAULT_FILTER_OPERATOR,
    total_count: Annotated[
        bool | None, Query(description=_generic_descriptions.TOTAL_COUNT)
    ] = False,
    deleted: Annotated[
        bool,
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

    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/structure-overview",
    dependencies=[rbac.STUDY_READ],
    summary="Returns an overview of study structure of all studies.",
    description=f"""
Allowed parameters include : filter on fields, sort by field name with sort direction, pagination

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[StudyStructureOverview],
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
    sort_by: Annotated[Json, Query(description=_generic_descriptions.SORT_BY)] = None,
    page_number: Annotated[
        int | None, Query(ge=1, description=_generic_descriptions.PAGE_NUMBER)
    ] = config.DEFAULT_PAGE_NUMBER,
    page_size: Annotated[
        int | None,
        Query(
            ge=0,
            le=config.MAX_PAGE_SIZE,
            description=_generic_descriptions.PAGE_SIZE,
        ),
    ] = config.DEFAULT_PAGE_SIZE,
    filters: Annotated[
        Json | None,
        Query(
            description=_generic_descriptions.FILTERS,
            openapi_examples=_generic_descriptions.FILTERS_EXAMPLE,
        ),
    ] = None,
    operator: Annotated[
        str | None, Query(description=_generic_descriptions.FILTER_OPERATOR)
    ] = config.DEFAULT_FILTER_OPERATOR,
    total_count: Annotated[
        bool | None, Query(description=_generic_descriptions.TOTAL_COUNT)
    ] = False,
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

    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/structure-overview/headers",
    dependencies=[rbac.STUDY_READ],
    summary="Returns possibles values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=list[Any],
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
    field_name: Annotated[
        str, Query(description=_generic_descriptions.HEADER_FIELD_NAME)
    ],
    search_string: Annotated[
        str | None, Query(description=_generic_descriptions.HEADER_SEARCH_STRING)
    ] = "",
    filters: Annotated[
        Json | None,
        Query(
            description=_generic_descriptions.FILTERS,
            openapi_examples=_generic_descriptions.FILTERS_EXAMPLE,
        ),
    ] = None,
    operator: Annotated[
        str | None, Query(description=_generic_descriptions.FILTER_OPERATOR)
    ] = config.DEFAULT_FILTER_OPERATOR,
    page_size: Annotated[
        int | None, Query(description=_generic_descriptions.HEADER_PAGE_SIZE)
    ] = config.DEFAULT_HEADER_PAGE_SIZE,
):
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
    dependencies=[rbac.STUDY_READ],
    summary="Returns possibles values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=list[Any],
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
    field_name: Annotated[
        str, Query(description=_generic_descriptions.HEADER_FIELD_NAME)
    ],
    search_string: Annotated[
        str | None, Query(description=_generic_descriptions.HEADER_SEARCH_STRING)
    ] = "",
    filters: Annotated[
        Json | None,
        Query(
            description=_generic_descriptions.FILTERS,
            openapi_examples=_generic_descriptions.FILTERS_EXAMPLE,
        ),
    ] = None,
    operator: Annotated[
        str | None, Query(description=_generic_descriptions.FILTER_OPERATOR)
    ] = config.DEFAULT_FILTER_OPERATOR,
    page_size: Annotated[
        int | None, Query(description=_generic_descriptions.HEADER_PAGE_SIZE)
    ] = config.DEFAULT_HEADER_PAGE_SIZE,
):
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
    dependencies=[rbac.STUDY_WRITE],
    summary="Locks a Study with specified uid",
    description="The Study is locked, which means that the LATEST_LOCKED relationship in the database is created."
    "The first locked version obtains number '1' and each next locked version "
    "is incremented number of the last locked version. "
    "The Study exists in the LOCKED state after successful lock",
    response_model=Study,
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
        StatusChangeDescription,
        Body(description="The description of the locked version."),
    ],
):
    study_service = StudyService()
    return study_service.lock(
        uid=study_uid, change_description=lock_description.change_description
    )


@router.delete(
    "/{study_uid}/locks",
    dependencies=[rbac.STUDY_WRITE],
    summary="Unlocks a Study with specified uid",
    description="The Study is unlocked, which means that the new DRAFT version of a Study is created"
    " and the Study exists in the DRAFT state.",
    response_model=Study,
    status_code=200,
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
):
    study_service = StudyService()
    return study_service.unlock(uid=study_uid)


@router.post(
    "/{study_uid}/release",
    dependencies=[rbac.STUDY_WRITE],
    summary="Releases a Study with specified uid",
    description="The Study is released, which means that 'snapshot' of the Study is created in the database"
    "and the LATEST_RELEASED relationship is created that points to the created snapshot."
    "What's more the new LATEST_DRAFT node is created that describes the new Draft Study after releasing.",
    response_model=Study,
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
        StatusChangeDescription,
        Body(description="The description of the release version."),
    ],
):
    study_service = StudyService()
    return study_service.release(
        uid=study_uid, change_description=release_description.change_description
    )


@router.delete(
    "/{study_uid}",
    dependencies=[rbac.STUDY_WRITE],
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
    response_model=None,
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
def delete_activity(study_uid: Annotated[str, StudyUID]):
    study_service = StudyService()
    study_service.soft_delete(uid=study_uid)
    return Response(status_code=response_status.HTTP_204_NO_CONTENT)


@router.get(
    "/{study_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="Returns the current state of a specific study definition identified by 'study_uid'.",
    description="If multiple request query parameters are used, then they need to match all at the same time"
    " (they are combined with the AND operation).",
    response_model=Study,
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
):
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
    dependencies=[rbac.STUDY_READ],
    summary="Returns various statistics about the structure of the study identified by 'study_uid'.",
    response_model=StudyStructureStatistics,
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
):
    study_service = StudyService()
    return study_service.get_study_structure_statistics(study_uid)


@router.get(
    "/{study_uid}/pharma-cm",
    dependencies=[rbac.STUDY_READ],
    summary="Returns the pharma-cm represention of study identified by 'study_uid'.",
    response_model=StudyPharmaCM,
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
):
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
    dependencies=[rbac.STUDY_READ],
    summary="Returns the pharma-cm represention of study identified by 'study_uid' in the xml format.",
    response_model_exclude_unset=True,
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
) -> StreamingResponse:
    StudyService().check_if_study_uid_and_version_exists(
        study_uid=study_uid, study_value_version=study_value_version
    )
    study_pharma_service = StudyPharmaCMService()
    study_pharma = study_pharma_service.get_pharma_cm_xml(
        study_uid=study_uid,
        study_value_version=study_value_version,
    )
    response = StreamingResponse(
        iter(
            [
                dict2xml(
                    study_pharma,
                    indent="  ",
                    closed_tags_for=[None],
                    data_sorter=DataSorter.never(),
                )
            ]
        ),
        media_type="text/xml",
    )
    response.headers["Content-Disposition"] = "attachment; filename=export"
    return response


@router.patch(
    "/{study_uid}",
    dependencies=[rbac.STUDY_WRITE],
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
    response_model=Study,
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
    dependencies=[rbac.STUDY_READ],
    summary="Returns the history of study snapshot definitions",
    description="It returns the history of changes made to the specified Study Definition Snapshot."
    "The returned history should reflect HAS_VERSION relationships in the database between StudyRoot and StudyValue nodes",
    response_model=CustomPage[CompactStudy],
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
    sort_by: Annotated[
        Json | None, Query(description=_generic_descriptions.SORT_BY)
    ] = None,
    page_number: Annotated[
        int | None, Query(ge=1, description=_generic_descriptions.PAGE_NUMBER)
    ] = config.DEFAULT_PAGE_NUMBER,
    page_size: Annotated[
        int | None,
        Query(
            ge=0,
            le=config.MAX_PAGE_SIZE,
            description=_generic_descriptions.PAGE_SIZE,
        ),
    ] = config.DEFAULT_PAGE_SIZE,
    filters: Annotated[
        Json | None,
        Query(
            description=_generic_descriptions.FILTERS,
            openapi_examples=_generic_descriptions.FILTERS_EXAMPLE,
        ),
    ] = None,
    operator: Annotated[
        str | None, Query(description=_generic_descriptions.FILTER_OPERATOR)
    ] = config.DEFAULT_FILTER_OPERATOR,
    total_count: Annotated[
        bool | None, Query(description=_generic_descriptions.TOTAL_COUNT)
    ] = False,
):
    study_service = StudyService()
    snapshot_history = study_service.get_study_snapshot_history(
        study_uid=study_uid,
        page_number=page_number,
        page_size=page_size,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
        total_count=total_count,
    )
    return CustomPage.create(
        items=snapshot_history.items,
        total=snapshot_history.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/{study_uid}/fields-audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="Returns the audit trail for the fields of a specific study definition identified by 'study_uid'.",
    description="Actions on the study are grouped by date of edit."
    "Optionally select which subset of fields should be reflected in the audit trail.",
    response_model=list[StudyFieldAuditTrailEntry],
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
):
    study_service = StudyService()
    study_fields_audit_trail = study_service.get_fields_audit_trail_by_uid(
        uid=study_uid,
        include_sections=include_sections,
        exclude_sections=exclude_sections,
    )
    return study_fields_audit_trail


@router.get(
    "/{study_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="Returns the audit trail for the subparts of a specific study definition identified by 'study_uid'.",
    description="Actions on the study are grouped by date of edit. Optionally select which subset of fields should be reflected in the audit trail.",
    response_model=list[StudySubpartAuditTrail],
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
    is_subpart: bool = False,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
):
    study_service = StudyService()
    return study_service.get_subpart_audit_trail_by_uid(
        uid=study_uid, is_subpart=is_subpart, study_value_version=study_value_version
    )


@router.post(
    "",
    dependencies=[rbac.STUDY_WRITE],
    summary="Creates a new Study Definition.",
    description="""
If the request succeeds new DRAFT Study Definition will be with initial identification data as provided in 
request body with new unique uid generated and returned in response body.
        """,
    response_model=Study,
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
    dependencies=[rbac.STUDY_WRITE],
    summary="Creates a cloned Study Definition with selective copying.",
    description="""
Creates a new DRAFT Study Definition by cloning an existing study. 
The client can specify which parts of the study should be copied using the request body.
""",
    response_model=Study,
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


@router.get(
    "/{study_uid}/protocol-title",
    dependencies=[rbac.STUDY_READ],
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
    response_model=StudyProtocolTitle,
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
):
    study_service = StudyService()
    return study_service.get_protocol_title(
        uid=study_uid, study_value_version=study_value_version
    )


@router.get(
    "/{study_uid}/copy-component",
    dependencies=[rbac.STUDY_READ],
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
    response_model=Study,
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
        Query(
            description="Indicates whether to overwrite the component of the study referenced by the uid"
            "or return a projection",
        ),
    ] = False,
):
    study_service = StudyService()
    return study_service.copy_component_from_another_study(
        uid=study_uid,
        reference_study_uid=reference_study_uid,
        component_to_copy=component_to_copy,
        overwrite=overwrite,
    )


@router.get(
    "/{study_uid}/time-units",
    dependencies=[rbac.STUDY_READ],
    summary="Gets a study preferred time unit",
    response_model=StudyPreferredTimeUnit,
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
        Query(
            description="Whether the preferred time unit is associated with Protocol SoA or not.",
        ),
    ] = False,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
):
    study_service = StudyService()
    return study_service.get_study_preferred_time_unit(
        study_uid=study_uid,
        for_protocol_soa=for_protocol_soa,
        study_value_version=study_value_version,
    )


@router.patch(
    "/{study_uid}/time-units",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edits a study preferred time unit",
    response_model=StudyPreferredTimeUnit,
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
        Query(
            description="Whether the preferred time unit is associated with Protocol Soa or not.",
        ),
    ] = False,
):
    study_service = StudyService()
    return study_service.patch_study_preferred_time_unit(
        study_uid=study_uid,
        unit_definition_uid=preferred_time_unit_input.unit_definition_uid,
        for_protocol_soa=for_protocol_soa,
    )


@router.patch(
    "/{study_uid}/order",
    dependencies=[rbac.STUDY_WRITE],
    summary="Reorder Study Subparts within a Study Parent Part",
    response_model=list[Study],
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
):
    study_service = StudyService()
    return study_service.reorder_study_subparts(
        study_parent_part_uid=study_uid,
        study_subpart_reordering_input=study_subpart_reordering_input,
    )


@router.get(
    "/{study_uid}/soa-preferences",
    dependencies=[rbac.STUDY_READ],
    summary="Get study SoA preferences",
    response_model_by_alias=False,
    response_model=StudySoaPreferences,
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
    dependencies=[rbac.STUDY_WRITE],
    summary="Update study SoA preferences",
    response_model=StudySoaPreferences,
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
):
    study_service = StudyService()
    return study_service.patch_study_soa_preferences(
        study_uid=study_uid,
        soa_preferences=soa_preferences,
    )
