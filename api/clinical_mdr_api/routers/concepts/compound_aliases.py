"""Compound aliases router"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from starlette.requests import Request

from clinical_mdr_api.models.concepts.compound_alias import (
    CompoundAlias,
    CompoundAliasCreateInput,
    CompoundAliasEditInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.concepts.compound_alias_service import (
    CompoundAliasService,
)
from clinical_mdr_api.services.concepts.compound_service import CompoundService
from common import exceptions
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/concepts"
router = APIRouter()

CompoundAliasUID = Path(description="The unique id of the compound alias")


@router.get(
    "/compound-aliases",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all compound aliases (for a given library)",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List all compound aliases in their latest version, including properties derived from linked control terminology.

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
            "compound=compound.name",
            "name",
            "name_sentence_case",
            "is_preferred_synonym",
            "definition",
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
def get_all(
    request: Request,  # request is actually required by the allow_exports decorator
    library_name: Annotated[str | None, Query()] = None,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[CompoundAlias]:
    service = CompoundAliasService()
    results = service.get_all_concepts(
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
    "/compound-aliases/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all versions of compound aliases",
    description=f"""
State before:
 - The library must exist (if specified)

Business logic:
 - List version history of compound aliases.
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
            "compound=compound.name",
            "name",
            "is_preferred_synonym",
            "definition",
            "start_date",
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
def get_compounds_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    library_name: Annotated[str | None, Query()] = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[CompoundAlias]:
    service = CompoundAliasService()
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
    "/compound-aliases/headers",
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
    service = CompoundAliasService()
    return service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/compound-aliases/{compound_alias_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific compound aliases (in a specific version)",
    description="""
State before:
 - a compound alias with uid must exist.

Business logic:
 - If parameter at_specified_date_time is specified then the latest/newest representation of the concept at this point in time is returned. The point in time needs to be specified in ISO 8601 format including the timezone, e.g.: '2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. If the timezone is omitted, UTC�0 is assumed.
 - If parameter status is specified then the representation of the concept in that status is returned (if existent). This is useful if the concept has a status 'Draft' and a status 'Final'.
 - If parameter version is specified then the latest/newest representation of the concept in that version is returned. Only exact matches are considered. The version is specified in the following format: <major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0', ...

State after:
 - No change

Possible errors:
 - Invalid uid, at_specified_date_time, status or version.
 """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get(compound_alias_uid: Annotated[str, CompoundAliasUID]) -> CompoundAlias:
    service = CompoundAliasService()
    return service.get_by_uid(uid=compound_alias_uid)


@router.get(
    "/compound-aliases/{compound_alias_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List version history for compound aliases",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for compound aliases.
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
            "description": "Not Found - The compound alias with the specified 'compound_uid' wasn't found.",
        },
    },
)
def get_versions(
    compound_alias_uid: Annotated[str, CompoundAliasUID],
) -> list[CompoundAlias]:
    service = CompoundAliasService()
    return service.get_version_history(uid=compound_alias_uid)


@router.post(
    "/compound-aliases",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates new compound alias.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'is_editable' property of the library needs to be true).
 - The specified CT term uids must exist, and the term names are in a final state.

Business logic:
 - New node is created for the compound alias with the set properties.
 - relationships to specified control terminology are created (as in the model).
 - relationships to specified activity parent are created (as in the model)
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'change_description' property will be set automatically to 'Initial version'.

State after:
 - compound aliases is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The compound alias was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
    },
)
def create(
    compound_create_input: Annotated[CompoundAliasCreateInput, Body()],
) -> CompoundAlias:
    service = CompoundAliasService()
    return service.create(concept_input=compound_create_input)


@router.patch(
    "/compound-aliases/{compound_alias_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Update compound alias",
    description="""
State before:
 - uid must exist and compound alias must exist in status draft.
 - The compound alias must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).

Business logic:
 - If compound alias exist in status draft then attributes are updated.
 - If links to CT are selected or updated then relationships are made to CTTermRoots.
- If the linked compound alias is updated, the relationships are updated to point to the compound alias value node.

State after:
 - attributes are updated for the compound alias.
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
            "- The compound alias is not in draft status.\n"
            "- The compound alias had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The compound alias with the specified 'compound_uid' wasn't found.",
        },
    },
)
def edit(
    compound_alias_uid: Annotated[str, CompoundAliasUID],
    compound_edit_input: Annotated[CompoundAliasEditInput, Body()],
) -> CompoundAlias:
    service = CompoundAliasService()
    return service.edit_draft(
        uid=compound_alias_uid, concept_edit_input=compound_edit_input
    )


@router.post(
    "/compound-aliases/{compound_alias_uid}/approvals",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Approve draft version of a compound alias",
    description="""
State before:
 - uid must exist and compound alias must be in status Draft.
 
Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically to 'Approved version'.
 
State after:
 - Compound changed status to Final and assigned a new major version number.
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
            "- The compound alias is not in draft status.\n"
            "- The library doesn't allow compound alias approval.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The compound alias with the specified 'compound_uid' wasn't found.",
        },
    },
)
def approve(compound_alias_uid: Annotated[str, CompoundAliasUID]) -> CompoundAlias:
    service = CompoundAliasService()
    compound_alias = service.get_by_uid(uid=compound_alias_uid)

    compound_versions = CompoundService().get_version_history(
        uid=compound_alias.compound.uid
    )

    # Do not allow approving an alias unless the linked compound has at least one final version
    if not any(version.status == "Final" for version in compound_versions):
        raise exceptions.BusinessLogicException(
            msg=f"The linked compound '{compound_alias.compound.name}' must have at least one approved version before alias can be approved.",
        )

    return service.approve(uid=compound_alias_uid)


@router.post(
    "/compound-aliases/{compound_alias_uid}/versions",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Create a new version of a compound alias",
    description="""
State before:
 - uid must exist and the compound alias must be in status Final.
 
Business logic:
- The compound alias is changed to a draft state.

State after:
 - Compound changed status to Draft and assigned a new minor version number.
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
            "- The library doesn't allow to create compound aliases.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The compound alias is not in final status.\n"
            "- The compound alias with the specified 'compound_uid' could not be found.",
        },
    },
)
def create_new_version(
    compound_alias_uid: Annotated[str, CompoundAliasUID],
) -> CompoundAlias:
    service = CompoundAliasService()
    return service.create_new_version(uid=compound_alias_uid)


@router.delete(
    "/compound-aliases/{compound_alias_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of an compound alias",
    description="""
State before:
 - uid must exist and compound alias must be in status Final.
 
Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.
 
State after:
 - Compound changed status to Retired.
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
            "- The compound alias is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The compound alias with the specified 'compound_uid' could not be found.",
        },
    },
)
def inactivate(compound_alias_uid: Annotated[str, CompoundAliasUID]) -> CompoundAlias:
    service = CompoundAliasService()
    return service.inactivate_final(uid=compound_alias_uid)


@router.post(
    "/compound-aliases/{compound_alias_uid}/activations",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of an compound alias",
    description="""
State before:
 - uid must exist and compound alias must be in status Retired.
 
Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'change_description' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Compound changed status to Final.
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
            "- The compound alias is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The compound alias with the specified 'compound_uid' could not be found.",
        },
    },
)
def reactivate(compound_alias_uid: Annotated[str, CompoundAliasUID]) -> CompoundAlias:
    service = CompoundAliasService()
    return service.reactivate_retired(uid=compound_alias_uid)


@router.delete(
    "/compound-aliases/{compound_alias_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Delete draft version of an compound alias",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).
 
Business logic:
 - The draft concept is deleted.
 
State after:
 - Compound is successfully deleted.
 
Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The compound alias was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The compound alias is not in draft status.\n"
            "- The compound alias was already in final state or is in use.\n"
            "- The library doesn't allow to delete compound alias.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An compound alias with the specified 'compound_uid' could not be found.",
        },
    },
)
def delete(compound_alias_uid: Annotated[str, CompoundAliasUID]):
    service = CompoundAliasService()
    service.soft_delete(uid=compound_alias_uid)


@router.post(
    "/compound-aliases/{compound_alias_uid}/archive",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary=f"Move compound alias to {settings.archived_library_name} library",
    description="Moves an existing compound alias to the target library if not yet in it. Returns new state of CompoundAlias.",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: _generic_descriptions.ERROR_400,
        404: _generic_descriptions.ERROR_404,
    },
)
def archive(
    compound_alias_uid: Annotated[str, CompoundAliasUID],
) -> CompoundAlias:
    service = CompoundAliasService()
    return service.archive(uid=compound_alias_uid)
