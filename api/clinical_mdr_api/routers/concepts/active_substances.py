"""active_substances router"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from starlette.requests import Request

from clinical_mdr_api.models.concepts.active_substance import (
    ActiveSubstance,
    ActiveSubstanceCreateInput,
    ActiveSubstanceEditInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.concepts.active_substances_service import (
    ActiveSubstanceService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/concepts"
router = APIRouter()

ActiveSubstanceUID = Path(description="The unique id of the active substance")


@router.get(
    "/active-substances",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all active substances (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List all active substances in their latest version, including properties derived from linked control terminology.

State after:
 - No change

Possible errors:
 - Invalid library name specified.
 
{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
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
            "analyte_number",
            "short_number",
            "long_number",
            "inn",
            "external_id",
            "unii=unii.substance_unii",
            "pclass_name=unii.pclass_name",
            "pclass_id=unii.pclass_id",
            "start_date",
            "version",
            "status",
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
def get_active_substances(
    request: Request,  # request is actually required by the allow_exports decorator
    library_name: Annotated[str | None, Query()] = None,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[ActiveSubstance]:
    active_substance_service = ActiveSubstanceService()
    results = active_substance_service.get_all_concepts(
        library=library_name,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/active-substances/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all versions of active substances",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List version history of active substances.
 - The returned versions are ordered by version start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid library name specified.

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
            "analyte_number",
            "short_number",
            "long_number",
            "inn",
            "unii=unii.substance_unii",
            "pclass_id=unii.pclass_id",
            "pclass_name=unii.pclass_name",
            "external_id",
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
def get_active_substances_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    library_name: Annotated[str | None, Query()] = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[ActiveSubstance]:
    service = ActiveSubstanceService()
    results = service.get_all_concept_versions(
        library=library_name,
        sort_by={"start_date": False},
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/active-substances/headers",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
    description="Allowed parameters include : field name for which to get possible values, "
    "search string to provide filtering for the field name, additional filters to apply on other fields",
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
    library_name: Annotated[str | None, Query()] = None,
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/active-substances/{active_substance_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific active substance (in a specific version)",
    description="""
Possible errors:
 - Invalid uid, at_specified_date_time, status or version.
 """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_activity(
    active_substance_uid: Annotated[str, ActiveSubstanceUID],
) -> ActiveSubstance:
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.get_by_uid(uid=active_substance_uid)


@router.get(
    "/active-substances/{active_substance_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List version history for active substances",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for active substances.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The active substance with the specified 'active_substance_uid' wasn't found.",
        },
    },
)
def get_versions(
    active_substance_uid: Annotated[str, ActiveSubstanceUID],
) -> list[ActiveSubstance]:
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.get_version_history(uid=active_substance_uid)


@router.post(
    "/active-substances",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates new active substance.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).
 - The specified CT term uids must exist, and the term names are in a final state.

Business logic:
 - New node is created for the active substance with the set properties.
 - relationships to specified control terminology are created (as in the model).
 - relationships to specified activity parent are created (as in the model)
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - Active substance is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The active substance was successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
    },
)
def create(
    active_substance_create_input: Annotated[ActiveSubstanceCreateInput, Body()],
) -> ActiveSubstance:
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.create(concept_input=active_substance_create_input)


@router.patch(
    "/active-substances/{active_substance_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Update active_substance",
    description="""
State before:
 - uid must exist and active substance must exist in status draft.
 - The active substance must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If active substance exist in status draft then attributes are updated.
 - If links to CT are selected or updated then relationships are made to CTTermRoots.
- If the linked active substance is updated, the relationships are updated to point to the active substance value node.

State after:
 - attributes are updated for the active_substance.
 - Audit trail entry must be made with update of attributes.

Possible errors:
 - Invalid uid.

""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The active substance is not in draft status.\n"
            "- The active substance had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The active substance with the specified 'active_substance_uid' wasn't found.",
        },
    },
)
def edit(
    active_substance_uid: Annotated[str, ActiveSubstanceUID],
    active_substance_edit_input: Annotated[ActiveSubstanceEditInput, Body()],
) -> ActiveSubstance:
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.edit_draft(
        uid=active_substance_uid, concept_edit_input=active_substance_edit_input
    )


@router.post(
    "/active-substances/{active_substance_uid}/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Approve draft version of an active substance",
    description="""
State before:
 - uid must exist and active substance must be in status Draft.
 
Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically to 'Approved version'.
 
State after:
 - ActiveSubstance changed status to Final and assigned a new major version number.
 - Audit trail entry must be made with action of approving to new Final version.
 
Possible errors:
 - Invalid uid or status not Draft.
    """,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The active substance is not in draft status.\n"
            "- The library doesn't allow active substance approval.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The active substance with the specified 'active_substance_uid' wasn't found.",
        },
    },
)
def approve(
    active_substance_uid: Annotated[str, ActiveSubstanceUID],
) -> ActiveSubstance:
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.approve(uid=active_substance_uid)


@router.post(
    "/active-substances/{active_substance_uid}/versions",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Create a new version of an active substance",
    description="""
State before:
 - uid must exist and the active substance must be in status Final.
 
Business logic:
- The active substance is changed to a draft state.

State after:
 - ActiveSubstance changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.
 
Possible errors:
 - Invalid uid or status not Final.
""",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't allow to create active_substances.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The active substance is not in final status.\n"
            "- The active substance with the specified 'active_substance_uid' could not be found.",
        },
    },
)
def create_new_version(
    active_substance_uid: Annotated[str, ActiveSubstanceUID],
) -> ActiveSubstance:
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.create_new_version(uid=active_substance_uid)


@router.delete(
    "/active-substances/{active_substance_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of an active substance",
    description="""
State before:
 - uid must exist and active substance must be in status Final.
 
Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.
 
State after:
 - ActiveSubstance changed status to Retired.
 - Audit trail entry must be made with action of inactivating to retired version.
 
Possible errors:
 - Invalid uid or status not Final.
    """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The active substance is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The active substance with the specified 'active_substance_uid' could not be found.",
        },
    },
)
def inactivate(
    active_substance_uid: Annotated[str, ActiveSubstanceUID],
) -> ActiveSubstance:
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.inactivate_final(uid=active_substance_uid)


@router.post(
    "/active-substances/{active_substance_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of an active substance",
    description="""
State before:
 - uid must exist and active substance must be in status Retired.
 
Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - ActiveSubstance changed status to Final.
 - An audit trail entry must be made with action of reactivating to final version.
 
Possible errors:
 - Invalid uid or status not Retired.
    """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The active substance is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The active substance with the specified 'active_substance_uid' could not be found.",
        },
    },
)
def reactivate(
    active_substance_uid: Annotated[str, ActiveSubstanceUID],
) -> ActiveSubstance:
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.reactivate_retired(uid=active_substance_uid)


@router.delete(
    "/active-substances/{active_substance_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Delete draft version of an active substance",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).
 
Business logic:
 - The draft concept is deleted.
 
State after:
 - ActiveSubstance is successfully deleted.
 
Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The active substance was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The active substance is not in draft status.\n"
            "- The active substance was already in final state or is in use.\n"
            "- The library doesn't allow to delete active_substance.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An active substance with the specified 'active_substance_uid' could not be found.",
        },
    },
)
def delete(active_substance_uid: Annotated[str, ActiveSubstanceUID]):
    active_substance_service = ActiveSubstanceService()
    active_substance_service.soft_delete(uid=active_substance_uid)


@router.post(
    "/active-substances/{active_substance_uid}/archive",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=f"Move active substance to {settings.archived_library_name} library",
    description="Moves an existing active substance to the target library if not yet in it. Returns new state of ActiveSubstance.",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: _generic_descriptions.ERROR_400,
        404: _generic_descriptions.ERROR_404,
    },
)
def archive(
    active_substance_uid: Annotated[str, ActiveSubstanceUID],
) -> ActiveSubstance:
    active_substance_service = ActiveSubstanceService()
    return active_substance_service.archive(uid=active_substance_uid)
