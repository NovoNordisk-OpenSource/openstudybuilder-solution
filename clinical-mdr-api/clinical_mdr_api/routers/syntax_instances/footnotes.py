from typing import Annotated, Any

from fastapi import APIRouter, Path, Query, Request, Response
from fastapi import status as fast_api_status
from fastapi.param_functions import Body
from pydantic.types import Json

from clinical_mdr_api.domain_repositories.models.syntax import FootnoteValue
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyComponentEnum,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.syntax_instances.footnote import (
    Footnote,
    FootnoteCreateInput,
    FootnoteEditInput,
    FootnoteVersion,
    FootnoteWithType,
)
from clinical_mdr_api.models.syntax_templates.template_parameter import (
    TemplateParameter,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers._generic_descriptions import study_section_description
from clinical_mdr_api.services.syntax_instances.footnotes import FootnoteService
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with /footnotes
router = APIRouter()

Service = FootnoteService

# Argument definitions
FootnoteUID = Path(description="The unique id of the footnote.")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all final versions of footnotes referenced by any study.",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[FootnoteWithType],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library","uid","objective","template","footnote","start_date","end_date","status","version","change_description","author_username"
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
            <template type="str">Footnote using [Activity] and [Indication]</template>
            <footnote type="str">Footnote using [body weight] and [type 2 diabetes]</footnote>
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
            "template=template.name",
            "footnote=name",
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
    all_items = FootnoteService().get_all(
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
    )

    return CustomPage.create(
        items=all_items.items,
        total=all_items.total,
        page=page_number,
        size=page_size,
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
    return FootnoteService().get_distinct_values_for_header(
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
    response_model=CustomPage[Footnote],
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
    "/{footnote_uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of a specific footnote identified by 'footnote_uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=FootnoteWithType | None,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote with the specified 'footnote_uid' (and the specified date/time and/or status) wasn't found.",
        },
    },
)
def get(
    footnote_uid: Annotated[str, FootnoteUID],
):
    return FootnoteService().get_by_uid(uid=footnote_uid)


@router.get(
    "/{footnote_uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the version history of a specific footnote identified by 'footnote_uid'.",
    description="The returned versions are ordered by\n"
    "0. start_date descending (newest entries first)",
    response_model=list[FootnoteVersion],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote with the specified 'footnote_uid' wasn't found.",
        },
    },
)
def get_versions(footnote_uid: Annotated[str, FootnoteUID]):
    return Service().get_version_history(uid=footnote_uid)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Creates a new footnote in 'Draft' status.",
    description="""This request is only valid if
* the specified footnote template is in 'Final' status and
* the specified objective is in 'Final' status and
* the specified library allows creating footnote (the 'is_editable' property of the library needs to be true) and
* the footnote doesn't yet exist (no footnote with the same content in 'Final' or 'Draft' status).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'change_description' property will be set automatically.
* The 'version' property will be set to '0.1'.
""",
    response_model=Footnote,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The footnote was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The provided list of parameters is invalid.\n"
            "- The objective wasn't found or it is not in 'Final' status.\n"
            "- The library doesn't allow to create footnote.\n"
            "- The footnote does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The library with the specified 'library_name' could not be found.\n"
            "- The footnote template with the specified 'template_uid' could not be found.",
        },
    },
)
def create(
    footnote: Annotated[
        FootnoteCreateInput,
        Body(description="Related parameters of the footnote that shall be created."),
    ],
):
    return FootnoteService().create(footnote)


@router.post(
    "/preview",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Previews the creation of a new footnote.",
    description="""This request is only valid if
* the specified footnote template is in 'Final' status and
* the specified library allows creating footnote (the 'is_editable' property of the library needs to be true) and
* the footnote doesn't yet exist (no footnote with the same content in 'Final' or 'Draft' status).

If the request succeeds:
* No footnote will be created, but the result of the request will show what the footnote will look like.
""",
    response_model=Footnote,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "Success - The footnote is able to be created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The provided list of parameters is invalid.\n"
            "- The library doesn't allow to create footnote.\n"
            "- The footnote does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The library with the specified 'library_name' could not be found.\n"
            "- The footnote template with the specified 'template_uid' could not be found.",
        },
    },
)
def preview(
    footnote: Annotated[
        FootnoteCreateInput,
        Body(description="Related parameters of the footnote that shall be previewed."),
    ],
):
    return FootnoteService().create(footnote, preview=True)


@router.patch(
    "/{footnote_uid}",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Updates the footnote identified by 'footnote_uid'.",
    description="""This request is only valid if the footnote
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
""",
    response_model=FootnoteWithType,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote is not in draft status.\n"
            "- The footnote had been in 'Final' status before.\n"
            "- The provided list of parameters is invalid.\n"
            "- The library doesn't allow to edit draft versions.\n"
            "- The footnote does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote with the specified 'footnote_uid' wasn't found.",
        },
    },
)
def edit(
    footnote_uid: Annotated[str, FootnoteUID],
    footnote: Annotated[
        FootnoteEditInput,
        Body(
            description="The new parameter terms for the footnote including the change description.",
        ),
    ],
):
    return Service().edit_draft(footnote_uid, footnote)


@router.post(
    "/{footnote_uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE_OR_STUDY_WRITE],
    summary="Approves the footnote identified by 'footnote_uid'.",
    description="""This request is only valid if the footnote
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=FootnoteWithType,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote is not in draft status.\n"
            "- The library doesn't allow to approve footnote.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote with the specified 'footnote_uid' wasn't found.",
        },
    },
)
def approve(footnote_uid: Annotated[str, FootnoteUID]):
    return Service().approve(footnote_uid)


@router.delete(
    "/{footnote_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Inactivates/deactivates the footnote identified by 'footnote_uid'.",
    description="""This request is only valid if the footnote
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=FootnoteWithType,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote with the specified 'footnote_uid' wasn't found.",
        },
    },
)
def inactivate(footnote_uid: Annotated[str, FootnoteUID]):
    return Service().inactivate_final(uid=footnote_uid)


@router.post(
    "/{footnote_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivates the footnote identified by 'footnote_uid'.",
    description="""This request is only valid if the footnote
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=FootnoteWithType,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote with the specified 'footnote_uid' wasn't found.",
        },
    },
)
def reactivate(footnote_uid: Annotated[str, FootnoteUID]):
    return Service().reactivate_retired(footnote_uid)


@router.delete(
    "/{footnote_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Deletes the footnote identified by 'footnote_uid'.",
    description="""This request is only valid if \n
* the footnote is in 'Draft' status and
* the footnote has never been in 'Final' status and
* the footnote belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The footnote was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The footnote is not in draft status.\n"
            "- The footnote was already in final state or is in use.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An footnote with the specified uid could not be found.",
        },
    },
)
def delete(footnote_uid: Annotated[str, FootnoteUID]):
    Service().soft_delete(footnote_uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)


@router.get(
    "/{footnote_uid}/studies",
    dependencies=[rbac.STUDY_READ],
    response_model=list[Study],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The footnote with the specified 'footnote_uid' wasn't found.",
        },
    },
)
def get_studies(
    footnote_uid: Annotated[str, FootnoteUID],
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
        uid=footnote_uid,
        node_type=FootnoteValue,
        include_sections=include_sections,
        exclude_sections=exclude_sections,
    )


@router.get(
    "/{footnote_uid}/parameters",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all template parameters available for the footnote identified by 'footnote_uid'. Includes the available values per parameter.",
    description="""Returns all template parameters used in the footnote template
that is the basis for the footnote identified by 'footnote_uid'. 
Includes the available values per parameter.

The returned parameters are ordered
0. as they occur in the footnote template

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
def get_parameters(footnote_uid: Annotated[str, FootnoteUID]):
    return FootnoteService().get_parameters(footnote_uid)
