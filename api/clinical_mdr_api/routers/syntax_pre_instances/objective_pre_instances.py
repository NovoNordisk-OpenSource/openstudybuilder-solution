from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query, Request

from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.syntax_pre_instances.objective_pre_instance import (
    ObjectivePreInstance,
    ObjectivePreInstanceEditInput,
    ObjectivePreInstanceIndexingsInput,
    ObjectivePreInstanceVersion,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.syntax_pre_instances.objective_pre_instances import (
    ObjectivePreInstanceService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

ObjectivePreInstanceUID = Path(
    description="The unique id of the Objective Pre-Instance."
)

# Prefixed with "/objective-pre-instances"
router = APIRouter()

Service = ObjectivePreInstanceService


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
            "objective_template=template_name",
            "name",
            "indications",
            "categories",
            "is_confirmatory_testing",
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
def objective_pre_instances(
    request: Request,  # request is actually required by the allow_exports decorator
    status: Annotated[
        LibraryItemStatus | None,
        Query(
            description="If specified, only those Syntax Pre-Instances will be returned that are currently in the specified status. "
            "This may be particularly useful if the Objective Pre-Instance has "
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
) -> CustomPage[ObjectivePreInstance]:
    results = ObjectivePreInstanceService().get_all(
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
            "This may be particularly useful if the Objective Pre-Instance has "
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
) -> CustomPage[ObjectivePreInstance]:
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
    "/{objective_pre_instance_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of a specific objective pre-instance identified by 'objective_pre_instance_uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": (
                "Not Found - The objective pre-instance with the specified 'objective_pre_instance_uid' (and the specified date/time and/or status) wasn't found."
            ),
        },
    },
)
def get(
    objective_pre_instance_uid: Annotated[str, ObjectivePreInstanceUID],
) -> ObjectivePreInstance:
    return ObjectivePreInstanceService().get_by_uid(uid=objective_pre_instance_uid)


@router.patch(
    "/{objective_pre_instance_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Updates the Objective Pre-Instance identified by 'objective_pre_instance_uid'.",
    description="""This request is only valid if the Objective Pre-Instance
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
* The link to the objective will remain as is.
""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The Objective Pre-Instance is not in draft status.\n"
            "- The Objective Pre-Instance had been in 'Final' status before.\n"
            "- The provided list of parameters is invalid.\n"
            "- The library doesn't allow to edit draft versions.\n"
            "- The Objective Pre-Instance does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Objective Pre-Instance with the specified 'objective_pre_instance_uid' wasn't found.",
        },
    },
)
def edit(
    objective_pre_instance_uid: Annotated[str, ObjectivePreInstanceUID],
    objective_pre_instance: Annotated[
        ObjectivePreInstanceEditInput,
        Body(
            description="The new parameter terms for the Objective Pre-Instance, its indexings and the change description.",
        ),
    ],
) -> ObjectivePreInstance:
    return Service().edit_draft(
        uid=objective_pre_instance_uid, template=objective_pre_instance
    )


@router.patch(
    "/{objective_pre_instance_uid}/indexings",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Updates the indexings of the Objective Pre-Instance identified by 'objective_pre_instance_uid'.",
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
            "description": "Not Found - The Pre-Instance with the specified 'objective_pre_instance_uid' could not be found.",
        },
    },
)
def patch_indexings(
    objective_pre_instance_uid: Annotated[str, ObjectivePreInstanceUID],
    indexings: Annotated[
        ObjectivePreInstanceIndexingsInput,
        Body(
            description="The lists of UIDs for the new indexings to be set, grouped by indexings to be updated.",
        ),
    ],
) -> ObjectivePreInstance:
    return Service().patch_indexings(
        uid=objective_pre_instance_uid, indexings=indexings
    )


@router.get(
    "/{objective_pre_instance_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns the version history of a specific Objective Pre-Instance identified by 'objective_pre_instance_uid'.",
    description=f"""
The returned versions are ordered by `start_date` descending (newest entries first).

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {
            "content": {
                "text/csv": {"example": """
"library","objective_template","objective","uid","objective","start_date","end_date","status","version","change_description","author_username"
"Sponsor","First [ComparatorIntervention]","Objective","826d80a7-0b6a-419d-8ef1-80aa241d7ac7","First Intervention","2020-10-22T10:19:29+00:00",,"Draft","0.1","Initial version","NdSJ"
"""},
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
                "text/xml": {"example": """
<?xml version="1.0" encoding="UTF-8" ?>
<root>
    <data type="list">
        <item type="dict">
            <library type="str">Sponsor</library>
            <objective_template type="str">Objective using [Activity] and [Indication]</objective_template>
            <objective type="str">Test template new [glucose metabolism] [MACE+] totot</objective>
            <uid type="str">682d7003-8dcc-480d-b07b-878e659b8697</uid>
            <objective type="str">Objective using [body weight] and [type 2 diabetes]</objective>
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
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Objective Pre-Instance with the specified 'objective_pre_instance_uid' wasn't found.",
        },
    },
)
@decorators.allow_exports(
    {
        "text/csv": [
            "library=library.name",
            "objective_template=objective_template.uid",
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
            "objective_template=objective_template.name",
            "objective=objective.name",
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
            "objective_template=objective_template.uid",
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
    objective_pre_instance_uid: Annotated[str, ObjectivePreInstanceUID],
) -> list[ObjectivePreInstanceVersion]:
    return Service().get_version_history(objective_pre_instance_uid)


@router.post(
    "/{objective_pre_instance_uid}/versions",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates a new version of the Objective Pre-Instance identified by 'objective_pre_instance_uid'.",
    description="""This request is only valid if the Objective Pre-Instance
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
            "- The Objective Pre-Instance is not in final or retired status or has a draft status.\n"
            "- The Objective Pre-Instance name is not valid.\n"
            "- The library doesn't allow to create a new version.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Objective Pre-Instance with the specified 'objective_pre_instance_uid' could not be found.",
        },
    },
)
def create_new_version(
    objective_pre_instance_uid: Annotated[str, ObjectivePreInstanceUID],
) -> ObjectivePreInstance:
    return Service().create_new_version(uid=objective_pre_instance_uid)


@router.delete(
    "/{objective_pre_instance_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Inactivates/deactivates the objective pre-instance identified by 'objective_pre_instance_uid'.",
    description="""This request is only valid if the objective pre-instance
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
            "- The objective pre-instance is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The objective pre-instance with the specified 'objective_pre_instance_uid' wasn't found.",
        },
    },
)
def inactivate(
    objective_pre_instance_uid: Annotated[str, ObjectivePreInstanceUID],
) -> ObjectivePreInstance:
    return ObjectivePreInstanceService().inactivate_final(objective_pre_instance_uid)


@router.post(
    "/{objective_pre_instance_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivates the objective pre-instance identified by 'objective_pre_instance_uid'.",
    description="""This request is only valid if the objective pre-instance
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
            "- The objective pre-instance is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The objective pre-instance with the specified 'objective_pre_instance_uid' wasn't found.",
        },
    },
)
def reactivate(
    objective_pre_instance_uid: Annotated[str, ObjectivePreInstanceUID],
) -> ObjectivePreInstance:
    return ObjectivePreInstanceService().reactivate_retired(objective_pre_instance_uid)


@router.delete(
    "/{objective_pre_instance_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Deletes the Objective Pre-Instance identified by 'objective_pre_instance_uid'.",
    description="""This request is only valid if \n
* the Objective Pre-Instance is in 'Draft' status and
* the Objective Pre-Instance has never been in 'Final' status and
* the Objective Pre-Instance belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).""",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The Objective Pre-Instance was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The Objective Pre-Instance is not in draft status.\n"
            "- The Objective Pre-Instance was already in final state or is in use.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An Objective Pre-Instance with the specified uid could not be found.",
        },
    },
)
def delete(
    objective_pre_instance_uid: Annotated[str, ObjectivePreInstanceUID],
):
    Service().soft_delete(objective_pre_instance_uid)


@router.post(
    "/{objective_pre_instance_uid}/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Approves the Objective Pre-Instance identified by 'objective_pre_instance_uid'.",
    description="""This request is only valid if the Objective Pre-Instance
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
            "- The Objective Pre-Instance is not in draft status.\n"
            "- The library doesn't allow to approve Objective Pre-Instances.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The Objective Pre-Instance with the specified 'objective_pre_instance_uid' wasn't found.",
        },
    },
)
def approve(
    objective_pre_instance_uid: Annotated[str, ObjectivePreInstanceUID],
) -> ObjectivePreInstance:
    return Service().approve(objective_pre_instance_uid)
