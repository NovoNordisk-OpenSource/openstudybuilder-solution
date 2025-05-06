from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query, Request, Response
from fastapi import status as fast_api_status
from pydantic.types import Json

from clinical_mdr_api.domain_repositories.models.syntax import EndpointValue
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyComponentEnum,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.syntax_instances.endpoint import (
    Endpoint,
    EndpointCreateInput,
    EndpointEditInput,
    EndpointVersion,
)
from clinical_mdr_api.models.syntax_templates.template_parameter import (
    TemplateParameter,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers._generic_descriptions import study_section_description
from clinical_mdr_api.services.syntax_instances.endpoints import EndpointService
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/endpoints"
router = APIRouter()

Service = EndpointService

# Argument definitions
EndpointUID = Path(description="The unique id of the endpoint.")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all final versions of endpoints referenced by any study.",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[Endpoint],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library","uid","objective","template","endpoint","start_date","end_date","status","version","change_description","author_username"
"Sponsor","826d80a7-0b6a-419d-8ef1-80aa241d7ac7","Objective","First [ComparatorIntervention]","First Intervention","2020-10-22T10:19:29+00:00",,"Draft","0.1","Initial version","NdSJ"
"""
                },
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
                "text/xml": {
                    "example": """
<?xml version="1.0" encoding="UTF-8" ?>
<root>
    <data type="list">
        <item type="dict">
            <library type="str">Sponsor</library>
            <uid type="str">682d7003-8dcc-480d-b07b-878e659b8697</uid>
            <objective type="str">Test template new [glucose metabolism] [MACE+] totot</objective>
            <template type="str">Endpoint using [Activity] and [Indication]</template>
            <endpoint type="str">Endpoint using [body weight] and [type 2 diabetes]</endpoint>
            <start_date type="str">2020-11-26T13:43:23.000Z</start_date>
            <end_date type="str"></end_date>
            <status type="str">Draft</status>
            <version type="str">0.2</version>
            <change_description type="str">Changed indication</change_description>
            <author_username type="str">someone@example.com</author_username>
        </item>
    </data>
</root>
"""
                },
            }
        },
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "library=library.name",
            "uid",
            "objective=objective.name",
            "template=template_name",
            "endpoint=name",
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
    all_items = EndpointService().get_all(
        status=LibraryItemStatus.FINAL.value,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
    )

    return CustomPage.create(
        items=all_items.items, total=all_items.total, page=page_number, size=page_size
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
    response_model=CustomPage[Endpoint],
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
    "/{endpoint_uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of a specific endpoint identified by 'endpoint_uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=Endpoint | None,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The endpoint with the specified 'endpoint_uid' (and the specified date/time and/or status) wasn't found.",
        },
    },
)
def get(
    endpoint_uid: Annotated[str, EndpointUID],
):
    return EndpointService().get_by_uid(uid=endpoint_uid)


@router.get(
    "/{endpoint_uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the version history of a specific endpoint identified by 'endpoint_uid'.",
    description=f"""
The returned versions are ordered by `start_date` descending (newest entries first).

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=list[EndpointVersion],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library","template","objective","uid","endpoint","start_date","end_date","status","version","change_description","author_username"
"Sponsor","First [ComparatorIntervention]","Objective","826d80a7-0b6a-419d-8ef1-80aa241d7ac7","First Intervention","2020-10-22T10:19:29+00:00",,"Draft","0.1","Initial version","NdSJ"
"""
                },
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
                "text/xml": {
                    "example": """
<?xml version="1.0" encoding="UTF-8" ?>
<root>
    <data type="list">
        <item type="dict">
            <library type="str">Sponsor</library>
            <template type="str">Endpoint using [Activity] and [Indication]</template>
            <objective type="str">Test template new [glucose metabolism] [MACE+] totot</objective>
            <uid type="str">682d7003-8dcc-480d-b07b-878e659b8697</uid>
            <endpoint type="str">Endpoint using [body weight] and [type 2 diabetes]</endpoint>
            <start_date type="str">2020-11-26T13:43:23.000Z</start_date>
            <end_date type="str"></end_date>
            <status type="str">Draft</status>
            <version type="str">0.2</version>
            <change_description type="str">Changed indication</change_description>
            <author_username type="str">someone@example.com</author_username>
        </item>
    </data>
</root>
"""
                },
            }
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The endpoint with the specified 'endpoint_uid' wasn't found.",
        },
    },
)
@decorators.allow_exports(
    {
        "text/csv": [
            "library=library.name",
            "template=template_name",
            "objective=objective.name",
            "uid",
            "endpoint=name",
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "author_username",
        ],
        "text/xml": [
            "library=library.name",
            "template=template_name",
            "objective=objective.name",
            "uid",
            "endpoint=name",
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "author_username",
        ],
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
            "library=library.name",
            "template=template_name",
            "objective=objective.name",
            "uid",
            "endpoint=name",
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "author_username",
        ],
    }
)
# pylint: disable=unused-argument
def get_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    endpoint_uid: Annotated[str, EndpointUID],
):
    return EndpointService().get_version_history(endpoint_uid)


@router.get(
    "/{endpoint_uid}/studies",
    dependencies=[rbac.STUDY_READ],
    response_model=list[Study],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The endpoint with the specified 'endpoint_uid' wasn't found.",
        },
    },
)
def get_studies(
    endpoint_uid: Annotated[str, EndpointUID],
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
        uid=endpoint_uid,
        node_type=EndpointValue,
        include_sections=include_sections,
        exclude_sections=exclude_sections,
    )


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Creates a new endpoint in 'Draft' status.",
    description="""This request is only valid if
* the specified endpoint template is in 'Final' status and
* the specified objective is in 'Final' status and
* the specified library allows creating endpoints (the 'is_editable' property of the library needs to be true) and
* the endpoint doesn't yet exist (no endpoint with the same content in 'Final' or 'Draft' status).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'change_description' property will be set automatically.
* The 'version' property will be set to '0.1'.
""",
    response_model=Endpoint,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The endpoint was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The provided list of parameters is invalid.\n"
            "- The objective wasn't found or it is not in 'Final' status.\n"
            "- The library doesn't allow to create endpoints.\n"
            "- The endpoint does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The library with the specified 'library_name' could not be found.\n"
            "- The endpoint template with the specified 'template_uid' could not be found.",
        },
    },
)
def create(
    endpoint: Annotated[
        EndpointCreateInput,
        Body(description="Related parameters of the endpoint that shall be created."),
    ],
):
    return EndpointService().create(endpoint)


@router.post(
    "/preview",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Previews the creation of a new endpoint.",
    description="""This request is only valid if
* the specified endpoint template is in 'Final' status and
* the specified library allows creating endpoints (the 'is_editable' property of the library needs to be true) and
* the endpoint doesn't yet exist (no endpoint with the same content in 'Final' or 'Draft' status).

If the request succeeds:
* No endpoint will be created, but the result of the request will show what the endpoint will look like.
""",
    response_model=Endpoint,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "Success - The endpoint is able to be created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The provided list of parameters is invalid.\n"
            "- The library doesn't allow to create endpoints.\n"
            "- The endpoint does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The library with the specified 'library_name' could not be found.\n"
            "- The endpoint template with the specified 'template_uid' could not be found.",
        },
    },
)
def preview(
    endpoint: Annotated[
        EndpointCreateInput,
        Body(description="Related parameters of the endpoint that shall be previewed."),
    ],
):
    return EndpointService().create(endpoint, preview=True)


@router.patch(
    "/{endpoint_uid}",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Updates the endpoint identified by 'endpoint_uid'.",
    description="""This request is only valid if the endpoint
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
* The link to the objective will remain as is.
""",
    response_model=Endpoint,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The endpoint is not in draft status.\n"
            "- The endpoint had been in 'Final' status before.\n"
            "- The provided list of parameters is invalid.\n"
            "- The library doesn't allow to edit draft versions.\n"
            "- The endpoint does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The endpoint with the specified 'endpoint_uid' wasn't found.",
        },
    },
)
def edit(
    endpoint_uid: Annotated[str, EndpointUID],
    endpoint: Annotated[
        EndpointEditInput,
        Body(
            description="The new parameter terms for the endpoint including the change description.",
        ),
    ],
):
    return EndpointService().edit_draft(uid=endpoint_uid, template=endpoint)


@router.post(
    "/{endpoint_uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Approves the endpoint identified by 'endpoint_uid'.",
    description="""This request is only valid if the endpoint
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=Endpoint,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The endpoint is not in draft status.\n"
            "- The library doesn't allow to approve endpoints.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The endpoint with the specified 'endpoint_uid' wasn't found.",
        },
    },
)
def approve(endpoint_uid: Annotated[str, EndpointUID]):
    return EndpointService().approve(endpoint_uid)


@router.delete(
    "/{endpoint_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Inactivates/deactivates the endpoint identified by 'endpoint_uid'.",
    description="""This request is only valid if the endpoint
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=Endpoint,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The endpoint is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The endpoint with the specified 'endpoint_uid' wasn't found.",
        },
    },
)
def inactivate(endpoint_uid: Annotated[str, EndpointUID]):
    return EndpointService().inactivate_final(endpoint_uid)


# TODO check if * there is no other endpoint with the same name (it may be that one had been created after inactivating this one here)
@router.post(
    "/{endpoint_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivates the endpoint identified by 'endpoint_uid'.",
    description="""This request is only valid if the endpoint
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=Endpoint,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The endpoint is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The endpoint with the specified 'endpoint_uid' wasn't found.",
        },
    },
)
def reactivate(endpoint_uid: Annotated[str, EndpointUID]):
    return EndpointService().reactivate_retired(endpoint_uid)


@router.delete(
    "/{endpoint_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Deletes the endpoint identified by 'endpoint_uid'.",
    description="""This request is only valid if \n
* the endpoint is in 'Draft' status and
* the endpoint has never been in 'Final' status and
* the endpoint belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The endpoint was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The endpoint is not in draft status.\n"
            "- The endpoint was already in final state or is in use.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An endpoint with the specified uid could not be found.",
        },
    },
)
def delete(endpoint_uid: Annotated[str, EndpointUID]):
    EndpointService().soft_delete(endpoint_uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)


# TODO this endpoint potentially returns duplicated entries (by intention, currently).
#       however: check if that is ok with regard to the data volume we expect in the future. is paging needed?
@router.get(
    "/{endpoint_uid}/parameters",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all template parameters available for the endpoint identified by 'endpoint_uid'. Includes the available values per parameter.",
    description="""Returns all template parameters used in the endpoint template
that is the basis for the endpoint identified by 'endpoint_uid'. 
Includes the available values per parameter.

The returned parameters are ordered
0. as they occur in the endpoint template

Per parameter, the parameter.values are ordered by
0. value.name ascending

Note that parameters may be used multiple times in templates.
In that case, the same parameter (with the same values) is included multiple times in the response.
    """,
    response_model=list[TemplateParameter],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_parameters(endpoint_uid: Annotated[str, EndpointUID]):
    return EndpointService().get_parameters(endpoint_uid)
