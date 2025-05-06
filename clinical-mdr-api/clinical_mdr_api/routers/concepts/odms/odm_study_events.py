from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.models.concepts.odms.odm_study_event import (
    OdmStudyEvent,
    OdmStudyEventFormPostInput,
    OdmStudyEventPatchInput,
    OdmStudyEventPostInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.concepts.odms.odm_study_events import (
    OdmStudyEventService,
)
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/concepts/odms/templates"
router = APIRouter()

# Argument definitions
OdmStudyEventUID = Path(description="The unique id of the ODM Study Event.")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Return every variable related to the selected status and version of the ODM Study Events",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[OdmStudyEvent],
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
            "oid",
            "library_name",
            "name",
            "description",
            "forms",
            "start_date",
            "end_date",
            "effective_date",
            "retired_date",
            "status",
            "version",
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
def get_all_odm_study_events(
    request: Request,  # request is actually required by the allow_exports decorator
    library_name: Annotated[str | None, Query()] = None,
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
    odm_study_event_service = OdmStudyEventService()
    results = odm_study_event_service.get_all_concepts(
        library=library_name,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
    )
    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/headers",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
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
    library_name: Annotated[str | None, Query()] = None,
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
    odm_study_event_service = OdmStudyEventService()
    return odm_study_event_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/{odm_study_event_uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific ODM Study Event (in a specific version)",
    response_model=OdmStudyEvent,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_odm_study_event(odm_study_event_uid: Annotated[str, OdmStudyEventUID]):
    odm_study_event_service = OdmStudyEventService()
    return odm_study_event_service.get_by_uid(uid=odm_study_event_uid)


@router.get(
    "/{odm_study_event_uid}/relationships",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get UIDs of a specific ODM Study Event's relationships",
    response_model=dict,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_active_relationships(odm_study_event_uid: Annotated[str, OdmStudyEventUID]):
    odm_study_event_service = OdmStudyEventService()
    return odm_study_event_service.get_active_relationships(uid=odm_study_event_uid)


@router.get(
    "/{odm_study_event_uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List version history for ODM Study Event",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Study Events.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=list[OdmStudyEvent],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Study Event with the specified 'odm_study_event_uid' wasn't found.",
        },
    },
)
def get_odm_study_event_versions(odm_study_event_uid: Annotated[str, OdmStudyEventUID]):
    odm_study_event_service = OdmStudyEventService()
    return odm_study_event_service.get_version_history(uid=odm_study_event_uid)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new Study Event in 'Draft' status with version 0.1",
    response_model=OdmStudyEvent,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The ODM Study Event was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
        409: _generic_descriptions.ERROR_409,
    },
)
def create_odm_study_event(
    odm_study_event_create_input: Annotated[OdmStudyEventPostInput, Body()],
):
    odm_study_event_service = OdmStudyEventService()
    return odm_study_event_service.create(concept_input=odm_study_event_create_input)


@router.patch(
    "/{odm_study_event_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Update ODM Study Event",
    response_model=OdmStudyEvent,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Study Event is not in draft status.\n"
            "- The ODM Study Event had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Study Event with the specified 'odm_study_event_uid' wasn't found.",
        },
    },
)
def edit_odm_study_event(
    odm_study_event_uid: Annotated[str, OdmStudyEventUID],
    odm_study_event_edit_input: Annotated[OdmStudyEventPatchInput, Body()],
):
    odm_study_event_service = OdmStudyEventService()
    return odm_study_event_service.edit_draft(
        uid=odm_study_event_uid, concept_edit_input=odm_study_event_edit_input
    )


@router.post(
    "/{odm_study_event_uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Create a new version of ODM Study Event",
    description="""
State before:
 - uid must exist and the ODM Study Event must be in status Final.

Business logic:
- The ODM Study Event is changed to a draft state.

State after:
 - ODM Study Event changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=OdmStudyEvent,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't allow to create ODM Study Events.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Study Event is not in final status.\n"
            "- The ODM Study Event with the specified 'odm_study_event_uid' could not be found.",
        },
    },
)
def create_odm_study_event_version(
    odm_study_event_uid: Annotated[str, OdmStudyEventUID]
):
    odm_study_event_service = OdmStudyEventService()
    return odm_study_event_service.create_new_version(uid=odm_study_event_uid)


@router.post(
    "/{odm_study_event_uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve draft version of ODM Study Event",
    response_model=OdmStudyEvent,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Study Event is not in draft status.\n"
            "- The library doesn't allow to approve ODM Study Event.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Study Event with the specified 'odm_study_event_uid' wasn't found.",
        },
    },
)
def approve_odm_study_event(odm_study_event_uid: Annotated[str, OdmStudyEventUID]):
    odm_study_event_service = OdmStudyEventService()
    return odm_study_event_service.approve(uid=odm_study_event_uid)


@router.delete(
    "/{odm_study_event_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of ODM Study Event",
    response_model=OdmStudyEvent,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Study Event is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Study Event with the specified 'odm_study_event_uid' could not be found.",
        },
    },
)
def inactivate_odm_study_event(odm_study_event_uid: Annotated[str, OdmStudyEventUID]):
    odm_study_event_service = OdmStudyEventService()
    return odm_study_event_service.inactivate_final(uid=odm_study_event_uid)


@router.post(
    "/{odm_study_event_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a ODM Study Event",
    response_model=OdmStudyEvent,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Study Event is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Study Event with the specified 'odm_study_event_uid' could not be found.",
        },
    },
)
def reactivate_odm_study_event(odm_study_event_uid: Annotated[str, OdmStudyEventUID]):
    odm_study_event_service = OdmStudyEventService()
    return odm_study_event_service.reactivate_retired(uid=odm_study_event_uid)


@router.post(
    "/{odm_study_event_uid}/forms",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds forms to the ODM Study Event.",
    response_model=OdmStudyEvent,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The forms were successfully added to the ODM Study Event."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The forms with the specified 'odm_study_event_uid' wasn't found.",
        },
    },
)
def add_forms_to_odm_study_event(
    odm_study_event_uid: Annotated[str, OdmStudyEventUID],
    odm_study_event_form_post_input: Annotated[
        list[OdmStudyEventFormPostInput], Body()
    ],
    override: Annotated[
        bool,
        Query(
            description="If true, all existing form relationships will be replaced with the provided form relationships.",
        ),
    ] = False,
):
    odm_study_event_service = OdmStudyEventService()
    return odm_study_event_service.add_forms(
        uid=odm_study_event_uid,
        odm_study_event_form_post_input=odm_study_event_form_post_input,
        override=override,
    )


@router.delete(
    "/{odm_study_event_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Delete draft version of ODM Study Event",
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The ODM Study Event was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Study Event is not in draft status.\n"
            "- The ODM Study Event was already in final state or is in use.\n"
            "- The library doesn't allow to delete ODM Study Event.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Study Event with the specified 'odm_study_event_uid' could not be found.",
        },
    },
)
def delete_odm_study_event(odm_study_event_uid: Annotated[str, OdmStudyEventUID]):
    odm_study_event_service = OdmStudyEventService()
    odm_study_event_service.soft_delete(uid=odm_study_event_uid)
