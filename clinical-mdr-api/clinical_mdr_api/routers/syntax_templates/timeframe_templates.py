"""Timeframe templates router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query, Request, Response
from fastapi import status as fast_api_status
from pydantic.types import Json

from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.syntax_templates.template_parameter import (
    ComplexTemplateParameter,
)
from clinical_mdr_api.models.syntax_templates.timeframe_template import (
    TimeframeTemplate,
    TimeframeTemplateCreateInput,
    TimeframeTemplateEditInput,
    TimeframeTemplatePreValidateInput,
    TimeframeTemplateVersion,
    TimeframeTemplateWithCount,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.syntax_templates.timeframe_templates import (
    TimeframeTemplateService,
)
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/timeframe-templates"
router = APIRouter()

Service = TimeframeTemplateService

# Argument definitions
TimeframeTemplateUID = Path(description="The unique id of the timeframe template.")

PARAMETERS_NOTE = """**Parameters in the 'name' property**:

The 'name' of an timeframe template may contain parameters, that can - and usually will - be replaced with concrete values once an timeframe is created out of the timeframe template.

Parameters are referenced by simple strings in square brackets [] that match existing parameters defined in the MDR repository.

The timeframe template will be linked to those parameters defined in the 'name' property.

You may use an arbitrary number of parameters and you may use the same parameter multiple times within the same timeframe template 'name'.

*Example*:

name='MORE TESTING of the superiority in the efficacy of [Intervention] with [Activity] and [Activity] in [Timeframe].'

'Intervention', 'Activity' and 'Timeframe' are parameters."""


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all timeframe templates in their latest/newest version.",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[TimeframeTemplate],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library","uid","name","start_date","end_date","status","version","change_description","author_username"
"Sponsor","826d80a7-0b6a-419d-8ef1-80aa241d7ac7","First  [ComparatorIntervention]","2020-10-22T10:19:29+00:00",,"Draft","0.1","Initial version","NdSJ"
"""
                },
                "text/xml": {
                    "example": """
                    <?xml version="1.0" encoding="UTF-8" ?><root><data type="list"><item type="dict"><uid type="str">e9117175-918f-489e-9a6e-65e0025233a6</uid><name type="str">Alamakota</name><start_date type="str">2020-11-19T11:51:43.000Z</start_date><status type="str">Draft</status><version type="str">0.2</version><change_description type="str">Test</change_description><author_username type="str">someone@example.com</author_username></item></data></root>
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
            "uid",
            "sequence_id",
            "name_plain",
            "name",
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
def get_timeframe_templates(
    request: Request,  # request is actually required by the allow_exports decorator
    status: Annotated[
        LibraryItemStatus | None,
        Query(
            description="If specified, only those timeframe templates will be returned that are currently in the specified status. "
            "This may be particularly useful if the timeframe template has "
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
) -> CustomPage[TimeframeTemplate]:
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
            description="If specified, only those timeframe templates will be returned that are currently in the specified status. "
            "This may be particularly useful if the timeframe template has "
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
    response_model=CustomPage[TimeframeTemplate],
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
    "/{timeframe_template_uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of a specific timeframe template identified by 'timeframe_template_uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=TimeframeTemplateWithCount,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'timeframe_template_uid' (and the specified date/time and/or status) wasn't found.",
        },
    },
)
def get_timeframe_template(
    timeframe_template_uid: Annotated[str, TimeframeTemplateUID],
) -> TimeframeTemplate:
    return Service().get_by_uid(timeframe_template_uid)


@router.get(
    "/{timeframe_template_uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the version history of a specific timeframe template identified by 'timeframe_template_uid'.",
    description=f"""
The returned versions are ordered by `start_date` descending (newest entries first).

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=list[TimeframeTemplateVersion],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library";"uid";"name";"start_date";"end_date";"status";"version";"change_description";"author_username"
"Sponsor";"826d80a7-0b6a-419d-8ef1-80aa241d7ac7";"First  [ComparatorIntervention]";"2020-10-22T10:19:29+00:00";;"Draft";"0.1";"Initial version";"NdSJ"
"""
                },
                "text/xml": {
                    "example": """
                    <?xml version="1.0" encoding="UTF-8" ?><root><data type="list"><item type="dict"><name type="str">Alamakota</name><start_date type="str">2020-11-19 11:51:43+00:00</start_date><end_date type="str">None</end_date><status type="str">Draft</status><version type="str">0.2</version><change_description type="str">Test</change_description><author_username type="str">someone@example.com</author_username></item><item type="dict"><name type="str">Alamakota</name><start_date type="str">2020-11-19 11:51:07+00:00</start_date><end_date type="str">2020-11-19 11:51:43+00:00</end_date><status type="str">Draft</status><version type="str">0.1</version><change_description type="str">Initial version</change_description><author_username type="str">someone@example.com</author_username></item></data></root>
"""
                },
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
            }
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'timeframe_template_uid' wasn't found.",
        },
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "library=library.name",
            "name",
            "change_description",
            "status",
            "version",
            "start_date",
            "end_date",
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
def get_timeframe_template_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    timeframe_template_uid: Annotated[str, TimeframeTemplateUID],
) -> list[TimeframeTemplateVersion]:
    return Service().get_version_history(timeframe_template_uid)


@router.get(
    "/{timeframe_template_uid}/versions/{version}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns a specific version of a specific timeframe template identified by 'timeframe_template_uid' and 'version'.",
    description="**Multiple versions**:\n\n"
    "Technically, there can be multiple versions of the timeframe template with the same version number. "
    "This is due to the fact, that the version number remains the same when inactivating or reactivating an timeframe template "
    "(switching between 'Final' and 'Retired' status). \n\n"
    "In that case the latest/newest representation is returned.",
    response_model=TimeframeTemplate,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'timeframe_template_uid' and 'version' wasn't found.",
        },
    },
)
def get_timeframe_template_version(
    timeframe_template_uid: Annotated[str, TimeframeTemplateUID],
    version: Annotated[
        str,
        Path(
            description="A specific version number of the timeframe template. "
            "The version number is specified in the following format: \\<major\\>.\\<minor\\> where \\<major\\> and \\<minor\\> are digits.\n"
            "E.g. '0.1', '0.2', '1.0', ...",
        ),
    ],
) -> TimeframeTemplate:
    return Service().get_specific_version(timeframe_template_uid, version)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new timeframe template in 'Draft' status or returns the timeframe template if it already exists.",
    description="""This request is only valid if the timeframe template
* belongs to a library that allows creating (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'change_description' property will be set automatically.
* The 'version' property will be set to '0.1'.
* The timeframe template will be linked to a library.

"""
    + PARAMETERS_NOTE,
    response_model=TimeframeTemplate,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The timeframe template was successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe template name is not valid.\n"
            "- The library doesn't allow to create timeframe templates.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The library with the specified 'library_name' could not be found.",
        },
        409: _generic_descriptions.ERROR_409,
    },
)
def create_timeframe_template(
    timeframe_template: TimeframeTemplateCreateInput = (
        Body(description="The timeframe template that shall be created.")
    ),
) -> TimeframeTemplate:
    return Service().create(timeframe_template)


@router.patch(
    "/{timeframe_template_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Updates the timeframe template identified by 'timeframe_template_uid'.",
    description="""This request is only valid if the timeframe template
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.

Parameters in the 'name' property can only be changed if the timeframe template has never been approved.
Once the timeframe template has been approved, only the surrounding text (excluding the parameters) can be changed.

"""
    + PARAMETERS_NOTE,
    response_model=TimeframeTemplate,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe template is not in draft status.\n"
            "- The timeframe template name is not valid.\n"
            "- The library doesn't allow to edit draft versions.\n"
            "- The change of parameters of previously approved timeframe templates.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'timeframe_template_uid' could not be found.",
        },
    },
)
def edit(
    timeframe_template_uid: Annotated[str, TimeframeTemplateUID],
    timeframe_template: Annotated[
        TimeframeTemplateEditInput,
        Body(
            description="The new content of the timeframe template including the change description.",
        ),
    ],
) -> TimeframeTemplate:
    return Service().edit_draft(timeframe_template_uid, timeframe_template)


@router.post(
    "/{timeframe_template_uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new version of the timeframe template identified by 'timeframe_template_uid'.",
    description="""This request is only valid if the timeframe template
* is in 'Final' or 'Retired' status only (so no latest 'Draft' status exists) and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The latest 'Final' or 'Retired' version will remain the same as before.
* The status of the new version will be automatically set to 'Draft'.
* The 'version' property of the new version will be automatically set to the version of the latest 'Final' or 'Retired' version increased by +0.1.

Parameters in the 'name' property cannot be changed with this request.
Only the surrounding text (excluding the parameters) can be changed.
""",
    response_model=TimeframeTemplate,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe template is not in final or retired status or has a draft status.\n"
            "- The timeframe template name is not valid.\n"
            "- The library doesn't allow to create a new version.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'timeframe_template_uid' could not be found.",
        },
    },
)
def create_new_version(
    timeframe_template_uid: Annotated[str, TimeframeTemplateUID],
    timeframe_template: Annotated[
        TimeframeTemplateEditInput,
        Body(
            description="The content of the timeframe template for the new 'Draft' version including the change description.",
        ),
    ],
) -> TimeframeTemplate:
    return Service().create_new_version(timeframe_template_uid, timeframe_template)


@router.post(
    "/{timeframe_template_uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approves the timeframe template identified by 'timeframe_template_uid'.",
    description="""This request is only valid if the timeframe template
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).
If timeframe template has any related objects status will not be updated but item will be extended with 
related item counts.
If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=TimeframeTemplate,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe template is not in draft status.\n"
            "- The library doesn't allow to approve drafts.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'timeframe_template_uid' could not be found.",
        },
        409: {
            "model": ErrorResponse,
            "description": "Conflict - there are timeframes created from template and cascade is false",
        },
    },
)
def approve(
    timeframe_template_uid: Annotated[str, TimeframeTemplateUID],
    cascade: bool = False,
) -> TimeframeTemplate:
    """
    Approves timeframe template. Fails with 409 if there is some timeframes created
    from this template and cascade is false
    """
    if not cascade:
        return Service().approve(uid=timeframe_template_uid)
    return Service().approve_cascade(uid=timeframe_template_uid)


@router.delete(
    "/{timeframe_template_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Inactivates/deactivates the timeframe template identified by 'timeframe_template_uid'.",
    description="""This request is only valid if the timeframe template
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'change_description' property will be set automatically.
* The 'version' property will remain the same as before.
    """,
    response_model=TimeframeTemplate,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe template is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'timeframe_template_uid' could not be found.",
        },
    },
)
def inactivate(
    timeframe_template_uid: Annotated[str, TimeframeTemplateUID]
) -> TimeframeTemplate:
    return Service().inactivate_final(timeframe_template_uid)


@router.post(
    "/{timeframe_template_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivates the timeframe template identified by 'timeframe_template_uid'.",
    description="""This request is only valid if the timeframe template
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically.
* The 'version' property will remain the same as before.
    """,
    response_model=TimeframeTemplate,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe template is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'timeframe_template_uid' could not be found.",
        },
    },
)
def reactivate(
    timeframe_template_uid: Annotated[str, TimeframeTemplateUID]
) -> TimeframeTemplate:
    return Service().reactivate_retired(timeframe_template_uid)


@router.delete(
    "/{timeframe_template_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Deletes the timeframe template identified by 'timeframe_template_uid'.",
    description="""This request is only valid if \n
* the timeframe template is in 'Draft' status and
* the timeframe template has never been in 'Final' status and
* the timeframe template has no references to any timeframes and
* the timeframe template belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The timeframe template was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe template is not in draft status.\n"
            "- The timeframe template was already in final state or is in use.\n"
            "- The library doesn't allow to delete timeframe templates.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An timeframe template with the specified uid could not be found.",
        },
    },
)
def delete_timeframe_template(
    timeframe_template_uid: Annotated[str, TimeframeTemplateUID],
) -> Response:
    Service().soft_delete(timeframe_template_uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)


# TODO this endpoint potentially returns duplicated entries (by intention, currently).
#       however: check if that is ok with regard to the data volume we expect in the future. is paging needed?
@router.get(
    "/{timeframe_template_uid}/parameters",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all parameters used in the timeframe template identified by 'timeframe_template_uid'. Includes the available values per parameter.",
    description="""The returned parameters are ordered
0. as they occur in the timeframe template

Per parameter, the parameter.values are ordered by
0. value.name ascending

Note that parameters may be used multiple times in templates.
In that case, the same parameter (with the same values) is included multiple times in the response.
    """,
    response_model=list[ComplexTemplateParameter],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_parameters(
    timeframe_template_uid: Annotated[str, TimeframeTemplateUID],
    study_uid: Annotated[
        str | None,
        Query(
            description="if specified only valid parameters for a given study will be returned.",
        ),
    ] = None,
):
    return Service().get_parameters(timeframe_template_uid, study_uid=study_uid)


@router.post(
    "/pre-validate",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Validates the content of an timeframe template without actually processing it.",
    description="""Be aware that - even if this request is accepted - there is no guarantee that
a following request to e.g. *[POST] /timeframe-templates* or *[PATCH] /timeframe-templates/{timeframe_template_uid}*
with the same content will succeed.

"""
    + PARAMETERS_NOTE,
    status_code=202,
    responses={
        403: _generic_descriptions.ERROR_403,
        202: {
            "description": "Accepted. The content is valid and may be submitted in another request."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden. The content is invalid - Reasons include e.g.: \n"
            "- The syntax of the 'name' is not valid.\n"
            "- One of the parameters wasn't found.",
        },
    },
)
def pre_validate(
    timeframe_template: Annotated[
        TimeframeTemplatePreValidateInput,
        Body(
            description="The content of the timeframe template that shall be validated.",
        ),
    ],
):
    Service().validate_template_syntax(timeframe_template.name)
