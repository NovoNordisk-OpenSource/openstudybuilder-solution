from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query, Request

from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.syntax_pre_instances.criteria_pre_instance import (
    CriteriaPreInstance,
    CriteriaPreInstanceEditInput,
    CriteriaPreInstanceIndexingsInput,
    CriteriaPreInstanceVersion,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.syntax_pre_instances.criteria_pre_instances import (
    CriteriaPreInstanceService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

CriteriaPreInstanceUID = Path(description="The unique id of the Criteria Pre-Instance.")

# Prefixed with "/criteria-pre-instances"
router = APIRouter()

Service = CriteriaPreInstanceService


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns all Syntax Pre-Instances in their latest/newest version.",
    description="Allowed parameters include : filter on fields, sort by field name with sort direction, pagination",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "library=library.name",
            "uid",
            "sequence_id",
            "template_name",
            "name",
            "guidance_text",
            "indications",
            "categories",
            "sub_categories",
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
def criteria_pre_instances(
    request: Request,  # request is actually required by the allow_exports decorator
    status: Annotated[
        LibraryItemStatus | None,
        Query(
            description="If specified, only those Syntax Pre-Instances will be returned that are currently in the specified status. "
            "This may be particularly useful if the Criteria Pre-Instance has "
            "a 'Draft' and a 'Final' status or and you are interested in the 'Final' status.\n"
            "Valid values are: 'Final' or 'Draft'.",
        ),
    ] = None,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.SYNTAX_FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[CriteriaPreInstance]:
    results = CriteriaPreInstanceService().get_all(
        status=status,
        return_study_count=True,
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
            description="If specified, only those Syntax Pre-Instances will be returned that are currently in the specified status. "
            "This may be particularly useful if the Criteria Pre-Instance has "
            "a 'Draft' and a 'Final' status or and you are interested in the 'Final' status.\n"
            "Valid values are: 'Final' or 'Draft'.",
        ),
    ] = None,
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.SYNTAX_FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
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
) -> CustomPage[CriteriaPreInstance]:
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
    "/{criteria_pre_instance_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of a specific criteria pre-instance identified by 'criteria_pre_instance_uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria pre-instance with the specified 'criteria_pre_instance_uid' (and the specified date/time and/or status) wasn't found.",
        },
    },
)
def get(
    criteria_pre_instance_uid: Annotated[str, CriteriaPreInstanceUID],
) -> CriteriaPreInstance:
    return CriteriaPreInstanceService().get_by_uid(uid=criteria_pre_instance_uid)


@router.patch(
    "/{criteria_pre_instance_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Updates the Criteria Pre-Instance identified by 'criteria_pre_instance_uid'.",
    description="""This request is only valid if the Criteria Pre-Instance
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
* The link to the criteria will remain as is.
""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The Criteria Pre-Instance is not in draft status.\n"
            "- The Criteria Pre-Instance had been in 'Final' status before.\n"
            "- The provided list of parameters is invalid.\n"
            "- The library doesn't allow to edit draft versions.\n"
            "- The Criteria Pre-Instance does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Criteria Pre-Instance with the specified 'criteria_pre_instance_uid' wasn't found.",
        },
    },
)
def edit(
    criteria_pre_instance_uid: Annotated[str, CriteriaPreInstanceUID],
    criteria_pre_instance: Annotated[
        CriteriaPreInstanceEditInput,
        Body(
            description="The new parameter terms for the Criteria Pre-Instance, its indexings and the change description.",
        ),
    ],
) -> CriteriaPreInstance:
    return Service().edit_draft(
        uid=criteria_pre_instance_uid, template=criteria_pre_instance
    )


@router.patch(
    "/{criteria_pre_instance_uid}/indexings",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Updates the indexings of the Criteria Pre-Instance identified by 'criteria_pre_instance_uid'.",
    description="""This request is only valid if the Pre-Instance
    * belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).
    
    This is version independent : it won't trigger a status or a version change.
    """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {
            "description": "No content - The indexings for this Pre-Instance were successfully updated."
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Pre-Instance with the specified 'criteria_pre_instance_uid' could not be found.",
        },
    },
)
def patch_indexings(
    criteria_pre_instance_uid: Annotated[str, CriteriaPreInstanceUID],
    indexings: Annotated[
        CriteriaPreInstanceIndexingsInput,
        Body(
            description="The lists of UIDs for the new indexings to be set, grouped by indexings to be updated.",
        ),
    ],
) -> CriteriaPreInstance:
    return Service().patch_indexings(uid=criteria_pre_instance_uid, indexings=indexings)


@router.get(
    "/{criteria_pre_instance_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns the version history of a specific Criteria Pre-Instance identified by 'criteria_pre_instance_uid'.",
    description=f"""
The returned versions are ordered by `start_date` descending (newest entries first).

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Criteria Pre-Instance with the specified 'criteria_pre_instance_uid' wasn't found.",
        },
    },
)
@decorators.allow_exports(
    {
        "text/csv": [
            "library=library.name",
            "template_uid",
            "uid",
            "name_plain",
            "name",
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "author_username",
        ],
        "text/xml": [
            "library=library.name",
            "template_name",
            "criteria=criteria.name",
            "uid",
            "name_plain",
            "name",
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "author_username",
        ],
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
            "library=library.name",
            "template_uid",
            "uid",
            "name_plain",
            "name",
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
    criteria_pre_instance_uid: Annotated[str, CriteriaPreInstanceUID],
) -> list[CriteriaPreInstanceVersion]:
    return Service().get_version_history(criteria_pre_instance_uid)


@router.post(
    "/{criteria_pre_instance_uid}/versions",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates a new version of the Criteria Pre-Instance identified by 'criteria_pre_instance_uid'.",
    description="""This request is only valid if the Criteria Pre-Instance
* is in 'Final' or 'Retired' status only (so no latest 'Draft' status exists) and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The latest 'Final' or 'Retired' version will remain the same as before.
* The status of the new version will be automatically set to 'Draft'.
* The 'version' property of the new version will be automatically set to the version of the latest 'Final' or 'Retired' version increased by +0.1.

Parameters in the 'name' property cannot be changed with this request.
Only the surrounding text (excluding the parameters) can be changed.
""",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The Criteria Pre-Instance is not in final or retired status or has a draft status.\n"
            "- The Criteria Pre-Instance name is not valid.\n"
            "- The library doesn't allow to create a new version.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Criteria Pre-Instance with the specified 'criteria_pre_instance_uid' could not be found.",
        },
    },
)
def create_new_version(
    criteria_pre_instance_uid: Annotated[str, CriteriaPreInstanceUID],
) -> CriteriaPreInstance:
    return Service().create_new_version(uid=criteria_pre_instance_uid)


@router.delete(
    "/{criteria_pre_instance_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Inactivates/deactivates the criteria pre-instance identified by 'criteria_pre_instance_uid'.",
    description="""This request is only valid if the criteria pre-instance
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
            "- The criteria pre-instance is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria pre-instance with the specified 'criteria_pre_instance_uid' wasn't found.",
        },
    },
)
def inactivate(
    criteria_pre_instance_uid: Annotated[str, CriteriaPreInstanceUID],
) -> CriteriaPreInstance:
    return CriteriaPreInstanceService().inactivate_final(criteria_pre_instance_uid)


@router.post(
    "/{criteria_pre_instance_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivates the criteria pre-instance identified by 'criteria_pre_instance_uid'.",
    description="""This request is only valid if the criteria pre-instance
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
            "- The criteria pre-instance is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria pre-instance with the specified 'criteria_pre_instance_uid' wasn't found.",
        },
    },
)
def reactivate(
    criteria_pre_instance_uid: Annotated[str, CriteriaPreInstanceUID],
) -> CriteriaPreInstance:
    return CriteriaPreInstanceService().reactivate_retired(criteria_pre_instance_uid)


@router.delete(
    "/{criteria_pre_instance_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Deletes the Criteria Pre-Instance identified by 'criteria_pre_instance_uid'.",
    description="""This request is only valid if \n
* the Criteria Pre-Instance is in 'Draft' status and
* the Criteria Pre-Instance has never been in 'Final' status and
* the Criteria Pre-Instance belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).""",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The Criteria Pre-Instance was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The Criteria Pre-Instance is not in draft status.\n"
            "- The Criteria Pre-Instance was already in final state or is in use.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - A Criteria Pre-Instance with the specified uid could not be found.",
        },
    },
)
def delete(
    criteria_pre_instance_uid: Annotated[str, CriteriaPreInstanceUID],
):
    Service().soft_delete(criteria_pre_instance_uid)


@router.post(
    "/{criteria_pre_instance_uid}/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Approves the Criteria Pre-Instance identified by 'criteria_pre_instance_uid'.",
    description="""This request is only valid if the Criteria Pre-Instance
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
            "- The Criteria Pre-Instance is not in draft status.\n"
            "- The library doesn't allow to approve Criteria Pre-Instances.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Criteria Pre-Instance with the specified 'criteria_pre_instance_uid' wasn't found.",
        },
    },
)
def approve(
    criteria_pre_instance_uid: Annotated[str, CriteriaPreInstanceUID],
) -> CriteriaPreInstance:
    return Service().approve(criteria_pre_instance_uid)
