from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.models.concepts.odms.odm_common_models import (
    OdmElementWithParentUid,
    OdmVendorElementRelationPostInput,
    OdmVendorRelationPostInput,
    OdmVendorsPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_item_group import (
    OdmItemGroup,
    OdmItemGroupActivitySubGroupPostInput,
    OdmItemGroupItemPostInput,
    OdmItemGroupPatchInput,
    OdmItemGroupPostInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.concepts.odms.odm_item_groups import OdmItemGroupService
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/concepts/odms/item-groups"
router = APIRouter()

# Argument definitions
OdmItemGroupUID = Path(description="The unique id of the ODM Item Group.")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Return every variable related to the selected status and version of the ODM Item Groups",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[OdmItemGroup],
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
            "aliases",
            "descriptions=descriptions.description",
            "instructions=descriptions.instruction",
            "languages=descriptions.language",
            "instructions=descriptions.instruction",
            "sponsor_instructions=descriptions.sponsor_instruction",
            "repeating",
            "start_date",
            "end_date",
            "effective_date",
            "retired_date",
            "end_date",
            "status",
            "version",
            "sas_dataset_name",
            "sdtm_domains",
            "activity_subgroups",
            "vendor_attributes",
            "vendor_attributes",
            "vendor_element_attributes",
            "vendor_elements",
        ],
        "text/xml": [
            "uid",
            "oid",
            "library_name",
            "name",
            "aliases",
            "descriptions",
            "repeating",
            "start_date",
            "end_date",
            "effective_date",
            "retired_date",
            "end_date",
            "status",
            "version",
            "sas_dataset_name",
            "sdtm_domains",
            "activity_subgroups",
            "vendor_attributes",
            "vendor_attributes",
            "vendor_element_attributes",
            "vendor_elements",
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
def get_all_odm_item_groups(
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
    odm_item_group_service = OdmItemGroupService()
    results = odm_item_group_service.get_all_concepts(
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
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/forms",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get all ODM Item Groups that belongs to an ODM Form",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=list[OdmElementWithParentUid],
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
            "end_date",
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
def get_odm_item_group_that_belongs_to_form(
    request: Request,  # request is actually required by the allow_exports decorator
):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.get_item_groups_that_belongs_to_form()


@router.get(
    "/{odm_item_group_uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific ODM Item Group (in a specific version)",
    response_model=OdmItemGroup,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_odm_item_group(odm_item_group_uid: Annotated[str, OdmItemGroupUID]):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.get_by_uid(uid=odm_item_group_uid)


@router.get(
    "/{odm_item_group_uid}/relationships",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get UIDs of a specific ODM Item Group's relationships",
    response_model=dict,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_active_relationships(odm_item_group_uid: Annotated[str, OdmItemGroupUID]):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.get_active_relationships(uid=odm_item_group_uid)


@router.get(
    "/{odm_item_group_uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List version history for ODM Item Group",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Item Groups.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=list[OdmItemGroup],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item Group with the specified 'odm_item_group_uid' wasn't found.",
        },
    },
)
def get_odm_item_group_versions(odm_item_group_uid: Annotated[str, OdmItemGroupUID]):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.get_version_history(uid=odm_item_group_uid)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new Item Group in 'Draft' status with version 0.1",
    response_model=OdmItemGroup,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The ODM Item Group was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
        409: _generic_descriptions.ERROR_409,
    },
)
def create_odm_item_group(
    odm_item_group_create_input: Annotated[OdmItemGroupPostInput, Body()],
):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.create_with_relations(
        concept_input=odm_item_group_create_input
    )


@router.patch(
    "/{odm_item_group_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Update ODM Item Group",
    response_model=OdmItemGroup,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item Group is not in draft status.\n"
            "- The ODM Item Group had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item Group with the specified 'odm_item_group_uid' wasn't found.",
        },
    },
)
def edit_odm_item_group(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
    odm_item_group_edit_input: Annotated[OdmItemGroupPatchInput, Body()],
):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.update_with_relations(
        uid=odm_item_group_uid, concept_edit_input=odm_item_group_edit_input
    )


@router.post(
    "/{odm_item_group_uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Create a new version of ODM Item Group",
    description="""
State before:
 - uid must exist and the ODM Item Group must be in status Final.

Business logic:
- The ODM Item Group is changed to a draft state.

State after:
 - ODM Item Group changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=OdmItemGroup,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't allow to create ODM Item Groups.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Item Group is not in final status.\n"
            "- The ODM Item Group with the specified 'odm_item_group_uid' could not be found.",
        },
    },
)
def create_odm_item_group_version(odm_item_group_uid: Annotated[str, OdmItemGroupUID]):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.create_new_version(
        uid=odm_item_group_uid, cascade_new_version=True
    )


@router.post(
    "/{odm_item_group_uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve draft version of ODM Item Group",
    response_model=OdmItemGroup,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item Group is not in draft status.\n"
            "- The library doesn't allow to approve ODM Item Group.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item Group with the specified 'odm_item_group_uid' wasn't found.",
        },
    },
)
def approve_odm_item_group(odm_item_group_uid: Annotated[str, OdmItemGroupUID]):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.approve(
        uid=odm_item_group_uid, cascade_edit_and_approve=True
    )


@router.delete(
    "/{odm_item_group_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of ODM Item Group",
    response_model=OdmItemGroup,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item Group is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item Group with the specified 'odm_item_group_uid' could not be found.",
        },
    },
)
def inactivate_odm_item_group(odm_item_group_uid: Annotated[str, OdmItemGroupUID]):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.inactivate_final(
        uid=odm_item_group_uid, cascade_inactivate=True
    )


@router.post(
    "/{odm_item_group_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a ODM Item Group",
    response_model=OdmItemGroup,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item Group is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item Group with the specified 'odm_item_group_uid' could not be found.",
        },
    },
)
def reactivate_odm_item_group(odm_item_group_uid: Annotated[str, OdmItemGroupUID]):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.reactivate_retired(
        uid=odm_item_group_uid, cascade_reactivate=True
    )


@router.post(
    "/{odm_item_group_uid}/activity-sub-groups",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds activity sub groups to the ODM Item Group.",
    response_model=OdmItemGroup,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The activity sub groups were successfully added to the ODM Item Group."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity sub groups with the specified 'odm_item_group_uid' wasn't found.",
        },
    },
)
def add_activity_subgroups_to_odm_item_group(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
    odm_item_group_activity_subgroup_post_input: Annotated[
        list[OdmItemGroupActivitySubGroupPostInput], Body()
    ],
    override: Annotated[
        bool,
        Query(
            description="If true, all existing activity sub group relationships will be replaced with the provided activity sub group relationships.",
        ),
    ] = False,
):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.add_activity_subgroups(
        uid=odm_item_group_uid,
        odm_item_group_activity_subgroup_post_input=odm_item_group_activity_subgroup_post_input,
        override=override,
    )


@router.post(
    "/{odm_item_group_uid}/items",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds items to the ODM Item Group.",
    response_model=OdmItemGroup,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The items were successfully added to the ODM Item Group."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The items with the specified 'odm_item_group_uid' wasn't found.",
        },
    },
)
def add_item_to_odm_item_group(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
    odm_item_group_item_post_input: Annotated[list[OdmItemGroupItemPostInput], Body()],
    override: Annotated[
        bool,
        Query(
            description="If true, all existing item relationships will be replaced with the provided item relationships.",
        ),
    ] = False,
):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.add_items(
        uid=odm_item_group_uid,
        odm_item_group_item_post_input=odm_item_group_item_post_input,
        override=override,
    )


@router.post(
    "/{odm_item_group_uid}/vendor-elements",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds ODM Vendor Elements to the ODM Item Group.",
    response_model=OdmItemGroup,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The ODM Vendor Elements were successfully added to the ODM Item Group."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendor Elements with the specified 'odm_item_group_uid' wasn't found.",
        },
    },
)
def add_vendor_elements_to_odm_item_group(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
    odm_vendor_relation_post_input: Annotated[
        list[OdmVendorElementRelationPostInput], Body()
    ],
    override: Annotated[
        bool,
        Query(
            description="If true, all existing ODM Vendor Element relationships will be replaced with the provided ODM Vendor Element relationships.",
        ),
    ] = False,
):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.add_vendor_elements(
        uid=odm_item_group_uid,
        odm_vendor_relation_post_input=odm_vendor_relation_post_input,
        override=override,
    )


@router.post(
    "/{odm_item_group_uid}/vendor-attributes",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds ODM Vendor Attributes to the ODM Item Group.",
    response_model=OdmItemGroup,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The ODM Vendor Attributes were successfully added to the ODM Item Group."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendor Attributes with the specified 'odm_item_group_uid' wasn't found.",
        },
    },
)
def add_vendor_attributes_to_odm_item_group(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
    odm_vendor_relation_post_input: Annotated[list[OdmVendorRelationPostInput], Body()],
    override: Annotated[
        bool,
        Query(
            description="""If true, all existing ODM Vendor Attribute relationships will be replaced with the provided ODM Vendor Attribute relationships.""",
        ),
    ] = False,
):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.add_vendor_attributes(
        uid=odm_item_group_uid,
        odm_vendor_relation_post_input=odm_vendor_relation_post_input,
        override=override,
    )


@router.post(
    "/{odm_item_group_uid}/vendor-element-attributes",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds ODM Vendor Element attributes to the ODM Item Group.",
    response_model=OdmItemGroup,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The ODM Vendor Element attributes were successfully added to the ODM Item Group."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendor Element attributes with the specified 'odm_item_group_uid' wasn't found.",
        },
    },
)
def add_vendor_element_attributes_to_odm_item_group(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
    odm_vendor_relation_post_input: Annotated[list[OdmVendorRelationPostInput], Body()],
    override: Annotated[
        bool,
        Query(
            description="""If true, all existing ODM Vendor Element attribute relationships will be replaced with the provided ODM Vendor Element attribute relationships.""",
        ),
    ] = False,
):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.add_vendor_element_attributes(
        uid=odm_item_group_uid,
        odm_vendor_relation_post_input=odm_vendor_relation_post_input,
        override=override,
    )


@router.post(
    "/{odm_item_group_uid}/vendors",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Manages all ODM Vendors by replacing existing ODM Vendors by provided ODM Vendors.",
    response_model=OdmItemGroup,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The ODM Vendors were successfully added to the ODM Item Group."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendors with the specified 'odm_item_group_uid' wasn't found.",
        },
    },
)
def manage_vendors_of_odm_item_group(
    odm_item_group_uid: Annotated[str, OdmItemGroupUID],
    odm_vendors_post_input: Annotated[OdmVendorsPostInput, Body()],
):
    odm_item_group_service = OdmItemGroupService()
    return odm_item_group_service.manage_vendors(
        uid=odm_item_group_uid, odm_vendors_post_input=odm_vendors_post_input
    )


@router.delete(
    "/{odm_item_group_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Delete draft version of ODM Item Group",
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {
            "description": "No Content - The ODM Item Group was successfully deleted."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item Group is not in draft status.\n"
            "- The ODM Item Group was already in final state or is in use.\n"
            "- The library doesn't allow to delete ODM Item Group.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Item Group with the specified 'odm_item_group_uid' could not be found.",
        },
    },
)
def delete_odm_item_group(odm_item_group_uid: Annotated[str, OdmItemGroupUID]):
    odm_item_group_service = OdmItemGroupService()
    odm_item_group_service.soft_delete(uid=odm_item_group_uid, cascade_delete=True)
