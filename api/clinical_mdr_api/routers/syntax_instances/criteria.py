from typing import Annotated, Any

from fastapi import APIRouter, Path, Query, Request
from fastapi.param_functions import Body

from clinical_mdr_api.domain_repositories.models.syntax import CriteriaValue
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyComponentEnum,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.syntax_instances.criteria import (
    Criteria,
    CriteriaCreateInput,
    CriteriaEditInput,
    CriteriaVersion,
    CriteriaWithType,
)
from clinical_mdr_api.models.syntax_templates.template_parameter import (
    TemplateParameter,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers._generic_descriptions import study_section_description
from clinical_mdr_api.services.syntax_instances.criteria import CriteriaService
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/criteria"
router = APIRouter()

Service = CriteriaService

# Argument definitions
CriteriaUID = Path(description="The unique id of the criteria.")


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns all final versions of criteria referenced by any study.",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {
            "content": {
                "text/csv": {"example": """
"library","uid","objective","template","criteria","start_date","end_date","status","version","change_description","author_username"
"Sponsor","826d80a7-0b6a-419d-8ef1-80aa241d7ac7","Objective","First [ComparatorIntervention]","First Intervention","2020-10-22T10:19:29+00:00",,"Draft","0.1","Initial version","NdSJ"
"""},
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
                "text/xml": {"example": """
<?xml version="1.0" encoding="UTF-8" ?>
<root>
    <data type="list">
        <item type="dict">
            <library type="str">Sponsor</library>
            <uid type="str">682d7003-8dcc-480d-b07b-878e659b8697</uid>
            <objective type="str">Test template new [glucose metabolism] [MACE+] totot</objective>
            <template type="str">Criteria using [Activity] and [Indication]</template>
            <criteria type="str">Criteria using [body weight] and [type 2 diabetes]</criteria>
            <start_date type="str">2020-11-26T13:43:23.000Z</start_date>
            <end_date type="str"></end_date>
            <status type="str">Draft</status>
            <version type="str">0.2</version>
            <change_description type="str">Changed indication</change_description>
            <author_username type="str">someone@example.com</author_username>
        </item>
    </data>
</root>
"""},
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
            "criteria=name",
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
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.SYNTAX_FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[CriteriaWithType]:
    all_items = CriteriaService().get_all(
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
    )

    return CustomPage(
        items=all_items.items,
        total=all_items.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/headers",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
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
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.SYNTAX_FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    return CriteriaService().get_distinct_values_for_header(
        status=status,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/audit-trail",
    dependencies=[security, rbac.LIBRARY_READ],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def retrieve_audit_trail(
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.SYNTAX_FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[Criteria]:
    results = Service().get_all(
        page_number=page_number,
        page_size=page_size,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        total_count=total_count,
        for_audit_trail=True,
    )

    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/{criteria_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of a specific criteria identified by 'criteria_uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria with the specified 'criteria_uid' (and the specified date/time and/or status) wasn't found.",
        },
    },
)
def get(
    criteria_uid: Annotated[str, CriteriaUID],
) -> CriteriaWithType:
    return CriteriaService().get_by_uid(uid=criteria_uid)


@router.get(
    "/{criteria_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns the version history of a specific criteria identified by 'criteria_uid'.",
    description="The returned versions are ordered by\n"
    "0. start_date descending (newest entries first)",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria with the specified 'criteria_uid' wasn't found.",
        },
    },
)
def get_versions(criteria_uid: Annotated[str, CriteriaUID]) -> list[CriteriaVersion]:
    return Service().get_version_history(uid=criteria_uid)


@router.post(
    "",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates a new criteria in 'Draft' status.",
    description="""This request is only valid if
* the specified criteria template is in 'Final' status and
* the specified objective is in 'Final' status and
* the specified library allows creating criteria (the 'is_editable' property of the library needs to be true) and
* the criteria doesn't yet exist (no criteria with the same content in 'Final' or 'Draft' status).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'change_description' property will be set automatically.
* The 'version' property will be set to '0.1'.
""",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The criteria was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The provided list of parameters is invalid.\n"
            "- The objective wasn't found or it is not in 'Final' status.\n"
            "- The library doesn't allow to create criteria.\n"
            "- The criteria does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The library with the specified 'library_name' could not be found.\n"
            "- The criteria template with the specified 'template_uid' could not be found.",
        },
    },
)
def create(
    criteria: Annotated[
        CriteriaCreateInput,
        Body(description="Related parameters of the criteria that shall be created."),
    ],
) -> Criteria:
    return CriteriaService().create(criteria)


@router.post(
    "/preview",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Previews the creation of a new criteria.",
    description="""This request is only valid if
* the specified criteria template is in 'Final' status and
* the specified library allows creating criteria (the 'is_editable' property of the library needs to be true) and
* the criteria doesn't yet exist (no criteria with the same content in 'Final' or 'Draft' status).

If the request succeeds:
* No criteria will be created, but the result of the request will show what the criteria will look like.
""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "Success - The criteria is able to be created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The provided list of parameters is invalid.\n"
            "- The library doesn't allow to create criteria.\n"
            "- The criteria does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The library with the specified 'library_name' could not be found.\n"
            "- The criteria template with the specified 'template_uid' could not be found.",
        },
    },
)
def preview(
    criteria: Annotated[
        CriteriaCreateInput,
        Body(description="Related parameters of the criteria that shall be previewed."),
    ],
) -> Criteria:
    return CriteriaService().create(criteria, preview=True)


@router.patch(
    "/{criteria_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Updates the criteria identified by 'criteria_uid'.",
    description="""This request is only valid if the criteria
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The criteria is not in draft status.\n"
            "- The criteria had been in 'Final' status before.\n"
            "- The provided list of parameters is invalid.\n"
            "- The library doesn't allow to edit draft versions.\n"
            "- The criteria does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria with the specified 'criteria_uid' wasn't found.",
        },
    },
)
def edit(
    criteria_uid: Annotated[str, CriteriaUID],
    criteria: Annotated[
        CriteriaEditInput,
        Body(
            description="The new parameter terms for the criteria including the change description.",
        ),
    ],
) -> CriteriaWithType:
    return Service().edit_draft(criteria_uid, criteria)


@router.post(
    "/{criteria_uid}/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Approves the criteria identified by 'criteria_uid'.",
    description="""This request is only valid if the criteria
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The criteria is not in draft status.\n"
            "- The library doesn't allow to approve criteria.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria with the specified 'criteria_uid' wasn't found.",
        },
    },
)
def approve(criteria_uid: Annotated[str, CriteriaUID]) -> CriteriaWithType:
    return Service().approve(criteria_uid)


@router.delete(
    "/{criteria_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Inactivates/deactivates the criteria identified by 'criteria_uid'.",
    description="""This request is only valid if the criteria
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The criteria is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria with the specified 'criteria_uid' wasn't found.",
        },
    },
)
def inactivate(criteria_uid: Annotated[str, CriteriaUID]) -> CriteriaWithType:
    return Service().inactivate_final(uid=criteria_uid)


@router.post(
    "/{criteria_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivates the criteria identified by 'criteria_uid'.",
    description="""This request is only valid if the criteria
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The criteria is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria with the specified 'criteria_uid' wasn't found.",
        },
    },
)
def reactivate(criteria_uid: Annotated[str, CriteriaUID]) -> CriteriaWithType:
    return Service().reactivate_retired(criteria_uid)


@router.delete(
    "/{criteria_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Deletes the criteria identified by 'criteria_uid'.",
    description="""This request is only valid if \n
* the criteria is in 'Draft' status and
* the criteria has never been in 'Final' status and
* the criteria belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).""",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The criteria was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The criteria is not in draft status.\n"
            "- The criteria was already in final state or is in use.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An criteria with the specified uid could not be found.",
        },
    },
)
def delete(criteria_uid: Annotated[str, CriteriaUID]):
    Service().soft_delete(criteria_uid)


@router.get(
    "/{criteria_uid}/studies",
    dependencies=[security, rbac.STUDY_READ],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria with the specified 'criteria_uid' wasn't found.",
        },
    },
)
def get_studies(
    criteria_uid: Annotated[str, CriteriaUID],
    include_sections: Annotated[
        list[StudyComponentEnum] | None,
        Query(description=study_section_description("include")),
    ] = None,
    exclude_sections: Annotated[
        list[StudyComponentEnum] | None,
        Query(description=study_section_description("exclude")),
    ] = None,
) -> list[Study]:
    return Service().get_referencing_studies(
        uid=criteria_uid,
        node_type=CriteriaValue,
        include_sections=include_sections,
        exclude_sections=exclude_sections,
    )


# TODO this criteria potentially returns duplicated entries (by intention, currently).
#       however: check if that is ok with regard to the data volume we expect in the future. is paging needed?
@router.get(
    "/{criteria_uid}/parameters",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns all template parameters available for the criteria identified by 'criteria_uid'. Includes the available values per parameter.",
    description="""Returns all template parameters used in the criteria template
that is the basis for the criteria identified by 'criteria_uid'. 
Includes the available values per parameter.

The returned parameters are ordered
0. as they occur in the criteria template

Per parameter, the parameter.values are ordered by
0. value.name ascending

Note that parameters may be used multiple times in templates.
In that case, the same parameter (with the same values) is included multiple times in the response.
    """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_parameters(
    criteria_uid: Annotated[str, CriteriaUID],
) -> list[TemplateParameter]:
    return CriteriaService().get_parameters(criteria_uid)
