from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query, Request, Response
from fastapi import status as fast_api_status
from pydantic.types import Json

from clinical_mdr_api.domain_repositories.models.syntax import TimeframeValue
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyComponentEnum,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.syntax_instances.timeframe import (
    Timeframe,
    TimeframeCreateInput,
    TimeframeEditInput,
    TimeframeVersion,
)
from clinical_mdr_api.models.syntax_templates.template_parameter import (
    ComplexTemplateParameter,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers._generic_descriptions import study_section_description
from clinical_mdr_api.services.syntax_instances.timeframes import TimeframeService
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/timeframes"
router = APIRouter()

Service = TimeframeService

# Argument definitions
TimeframeUID = Path(description="The unique id of the timeframe.")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all timeframes in their latest/newest version.",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[Timeframe],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library","template","uid","timeframe","start_date","end_date","status","version","change_description","author_username"
"Sponsor","First  [ComparatorIntervention]","826d80a7-0b6a-419d-8ef1-80aa241d7ac7",First Intervention,"2020-10-22T10:19:29+00:00",,"Draft","0.1","Initial version","NdSJ"
"""
                },
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
            }
        },
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "library=library.name",
            "template=template_name",
            "uid",
            "timeframe=name",
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "author_username",
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
    status: Annotated[
        LibraryItemStatus | None,
        Query(
            description="If specified, only those timeframes will be returned that are currently in the specified status. "
            "This may be particularly useful if the timeframe has "
            "a) a 'Draft' and a 'Final' status or "
            "b) a 'Draft' and a 'Retired' status at the same time "
            "and you are interested in the 'Final' or 'Retired' status.\n"
            "Valid values are: 'Final', 'Draft' or 'Retired'.",
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
            description=_generic_descriptions.SYNTAX_FILTERS,
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
    data = Service().get_all(
        status=status,
        return_study_count=True,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
    )
    return CustomPage.create(
        items=data.items, total=data.total, page=page_number, size=page_size
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
    status: Annotated[
        LibraryItemStatus | None,
        Query(
            description="If specified, only those objective templates will be returned that are currently in the specified status. "
            "This may be particularly useful if the objective template has "
            "a) a 'Draft' and a 'Final' status or "
            "b) a 'Draft' and a 'Retired' status at the same time "
            "and you are interested in the 'Final' or 'Retired' status.\n"
            "Valid values are: 'Final', 'Draft' or 'Retired'.",
        ),
    ] = None,
    search_string: Annotated[
        str | None, Query(description=_generic_descriptions.HEADER_SEARCH_STRING)
    ] = "",
    filters: Annotated[
        Json | None,
        Query(
            description=_generic_descriptions.SYNTAX_FILTERS,
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
    return Service().get_distinct_values_for_header(
        status=status,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/audit-trail",
    dependencies=[rbac.LIBRARY_READ],
    response_model=CustomPage[Timeframe],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def retrieve_audit_trail(
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
            description=_generic_descriptions.SYNTAX_FILTERS,
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
    results = Service().get_all(
        page_number=page_number,
        page_size=page_size,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        total_count=total_count,
        for_audit_trail=True,
    )

    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/{timeframe_uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of a specific timeframe identified by 'timeframe_uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=Timeframe | None,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe with the specified 'timeframe_uid' (and the specified date/time and/or status) wasn't found.",
        },
    },
)
def get(
    timeframe_uid: Annotated[str, TimeframeUID],
    status: Annotated[
        LibraryItemStatus | None,
        Query(
            description="If specified, the representation of the timeframe in that status is returned (if existent). "
            "This may be particularly useful if the timeframe has "
            "a) a 'Draft' and a 'Final' status or "
            "b) a 'Draft' and a 'Retired' status at the same time "
            "and you are interested in the 'Final' or 'Retired' status.\n"
            "Valid values are: 'Final', 'Draft' or 'Retired'.",
        ),
    ] = None,
    version: Annotated[
        str | None,
        Query(
            description=r"If specified, the latest/newest representation of the timeframe in that version is returned. "
            r"Only exact matches are considered. "
            r"The version is specified in the following format: \<major\>.\<minor\> where \<major\> and \<minor\> are digits. "
            r"E.g. '0.1', '0.2', '1.0', ...",
        ),
    ] = None,
):
    return Service().get_by_uid(uid=timeframe_uid, version=version, status=status)


@router.get(
    "/{timeframe_uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the version history of a specific timeframe identified by 'timeframe_uid'.",
    description="The returned versions are ordered by\n"
    "0. start_date descending (newest entries first)",
    response_model=list[TimeframeVersion],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe with the specified 'timeframe_uid' wasn't found.",
        },
    },
)
def get_versions(timeframe_uid: Annotated[str, TimeframeUID]):
    return Service().get_version_history(timeframe_uid)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Creates a new timeframe in 'Draft' status.",
    description="""This request is only valid if
* the specified timeframe template is in 'Final' status and
* the specified library allows creating timeframes (the 'is_editable' property of the library needs to be true) and
* the timeframe doesn't yet exist (no timeframe with the same content in 'Final' or 'Draft' status).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'change_description' property will be set automatically.
* The 'version' property will be set to '0.1'.
""",
    response_model=Timeframe,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The timeframe was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The provided list of parameters is invalid.\n"
            "- The library doesn't allow to create timeframes.\n"
            "- The timeframe does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The library with the specified 'library_name' could not be found.\n"
            "- The timeframe template with the specified 'timeframe_template_uid' could not be found.",
        },
    },
)
def create(
    timeframe: Annotated[
        TimeframeCreateInput,
        Body(description="Related parameters of the timeframe that shall be created."),
    ],
):
    return Service().create(timeframe)


@router.post(
    "/preview",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Previews the creation of a new timeframe.",
    description="""This request is only valid if
* the specified timeframe template is in 'Final' status and
* the specified library allows creating timeframe (the 'is_editable' property of the library needs to be true) and
* the timeframe doesn't yet exist (no timeframe with the same content in 'Final' or 'Draft' status).

If the request succeeds:
* No timeframe will be created, but the result of the request will show what the timeframe will look like.
""",
    response_model=Timeframe,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "Success - The timeframe is able to be created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The provided list of parameters is invalid.\n"
            "- The library doesn't allow to create timeframes.\n"
            "- The timeframe does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The library with the specified 'library_name' could not be found.\n"
            "- The timeframe template with the specified 'timeframe_template_uid' could not be found.",
        },
    },
)
def preview(
    timeframe: Annotated[
        TimeframeCreateInput,
        Body(
            description="Related parameters of the timeframe that shall be previewed."
        ),
    ],
):
    return Service().create(timeframe, preview=True)


@router.patch(
    "/{timeframe_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Updates the timeframe identified by 'timeframe_uid'.",
    description="""This request is only valid if the timeframe
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
""",
    response_model=Timeframe,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe is not in draft status.\n"
            "- The timeframe had been in 'Final' status before.\n"
            "- The provided list of parameters is invalid.\n"
            "- The library doesn't allow to edit draft versions.\n"
            "- The timeframe does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe with the specified 'timeframe_uid' wasn't found.",
        },
    },
)
def edit(
    timeframe_uid: Annotated[str, TimeframeUID],
    timeframe: Annotated[
        TimeframeEditInput,
        Body(
            description="The new parameter terms for the timeframe including the change description.",
        ),
    ],
):
    return Service().edit_draft(timeframe_uid, timeframe)


@router.post(
    "/{timeframe_uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Approves the timeframe identified by 'timeframe_uid'.",
    description="""This request is only valid if the timeframe
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=Timeframe,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe is not in draft status.\n"
            "- The library doesn't allow to approve timeframe.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe with the specified 'timeframe_uid' wasn't found.",
        },
    },
)
def approve(timeframe_uid: Annotated[str, TimeframeUID]):
    return Service().approve(timeframe_uid)


@router.delete(
    "/{timeframe_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Inactivates/deactivates the timeframe identified by 'timeframe_uid'.",
    description="""This request is only valid if the timeframe
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=Timeframe,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe with the specified 'timeframe_uid' wasn't found.",
        },
    },
)
def inactivate(timeframe_uid: Annotated[str, TimeframeUID]):
    return Service().inactivate_final(timeframe_uid)


# TODO check if * there is no other timeframe with the same name (it may be that one had been created after inactivating this one here)
@router.post(
    "/{timeframe_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivates the timeframe identified by 'timeframe_uid'.",
    description="""This request is only valid if the timeframe
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=Timeframe,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe with the specified 'timeframe_uid' wasn't found.",
        },
    },
)
def reactivate(timeframe_uid: Annotated[str, TimeframeUID]):
    return Service().reactivate_retired(timeframe_uid)


@router.delete(
    "/{timeframe_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Deletes the timeframe identified by 'timeframe_uid'.",
    description="""This request is only valid if \n
* the timeframe is in 'Draft' status and
* the timeframe has never been in 'Final' status and
* the timeframe belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The timeframe was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe is not in draft status.\n"
            "- The timeframe was already in final state or is in use.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An timeframe with the specified uid could not be found.",
        },
    },
)
def delete(timeframe_uid: Annotated[str, TimeframeUID]):
    Service().soft_delete(timeframe_uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)


@router.get(
    "/{timeframe_uid}/studies",
    dependencies=[rbac.STUDY_READ],
    response_model=list[Study],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe with the specified 'timeframe_uid' wasn't found.",
        },
    },
)
def get_studies(
    timeframe_uid: Annotated[str, TimeframeUID],
    include_sections: Annotated[
        list[StudyComponentEnum] | None,
        Query(description=study_section_description("include")),
    ] = None,
    exclude_sections: Annotated[
        list[StudyComponentEnum] | None,
        Query(description=study_section_description("exclude")),
    ] = None,
):
    return Service().get_referencing_studies(
        uid=timeframe_uid,
        node_type=TimeframeValue,
        include_sections=include_sections,
        exclude_sections=exclude_sections,
    )


@router.get(
    "/{timeframe_uid}/parameters",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all template parameters available for the timeframe identified by 'timeframe_uid'. Includes the available values per parameter.",
    description="Returns all template parameters used in the timeframe template "
    "that is the basis for the timeframe identified by 'timeframe_uid'. "
    "Includes the available values per parameter.",
    response_model=list[ComplexTemplateParameter],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_parameters(
    timeframe_uid: Annotated[str, TimeframeUID],
    study_uid: Annotated[
        str | None,
        Query(
            description="if specified only valid parameters for a given study will be returned.",
        ),
    ] = None,
):
    return Service().get_parameters(timeframe_uid, study_uid=study_uid)
