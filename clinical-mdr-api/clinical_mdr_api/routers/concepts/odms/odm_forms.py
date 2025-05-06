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
from clinical_mdr_api.models.concepts.odms.odm_form import (
    OdmForm,
    OdmFormActivityGroupPostInput,
    OdmFormItemGroupPostInput,
    OdmFormPatchInput,
    OdmFormPostInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.concepts.odms.odm_forms import OdmFormService
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/concepts/odms/forms"
router = APIRouter()

# Argument definitions
OdmFormUID = Path(description="The unique id of the ODM Form.")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Return every variable related to the selected status and version of the ODM Forms",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[OdmForm],
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
            "descriptions=descriptions.description",
            "instructions=descriptions.instruction",
            "languages=descriptions.language",
            "instructions=descriptions.instruction",
            "sponsor_instructions=descriptions.sponsor_instruction",
            "forms",
            "start_date",
            "end_date",
            "effective_date",
            "retired_date",
            "end_date",
            "item_groups",
            "aliases",
            "activity_groups",
            "status",
            "version",
            "repeating",
            "scope",
            "sdtm_version",
            "vendor_attributes",
            "vendor_element_attributes",
            "vendor_elements",
        ],
        "text/xml": [
            "uid",
            "oid",
            "library_name",
            "name",
            "descriptions",
            "forms",
            "start_date",
            "end_date",
            "effective_date",
            "retired_date",
            "end_date",
            "item_groups",
            "aliases",
            "activity_groups",
            "status",
            "version",
            "repeating",
            "scope",
            "sdtm_version",
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
def get_all_odm_forms(
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
    odm_form_service = OdmFormService()
    results = odm_form_service.get_all_concepts(
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
    odm_form_service = OdmFormService()
    return odm_form_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/study-events",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get all ODM Forms that belongs to an ODM Study Event",
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
def get_odm_form_that_belongs_to_study_event(
    request: Request,  # request is actually required by the allow_exports decorator
):
    odm_form_service = OdmFormService()
    return odm_form_service.get_forms_that_belongs_to_study_event()


@router.get(
    "/{odm_form_uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get details on a specific ODM Form (in a specific version)",
    response_model=OdmForm,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_odm_form(odm_form_uid: Annotated[str, OdmFormUID]):
    odm_form_service = OdmFormService()
    return odm_form_service.get_by_uid(uid=odm_form_uid)


@router.get(
    "/{odm_form_uid}/relationships",
    dependencies=[rbac.LIBRARY_READ],
    summary="Get UIDs of a specific ODM Form's relationships",
    response_model=dict,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_active_relationships(odm_form_uid: Annotated[str, OdmFormUID]):
    odm_form_service = OdmFormService()
    return odm_form_service.get_active_relationships(uid=odm_form_uid)


@router.get(
    "/{odm_form_uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List version history for ODM Form",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Forms.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=list[OdmForm],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'odm_form_uid' wasn't found.",
        },
    },
)
def get_odm_form_versions(odm_form_uid: Annotated[str, OdmFormUID]):
    odm_form_service = OdmFormService()
    return odm_form_service.get_version_history(uid=odm_form_uid)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new Form in 'Draft' status with version 0.1",
    response_model=OdmForm,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The ODM Form was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
        409: _generic_descriptions.ERROR_409,
    },
)
def create_odm_form(
    odm_form_create_input: Annotated[OdmFormPostInput, Body()],
):
    odm_form_service = OdmFormService()

    return odm_form_service.create_with_relations(concept_input=odm_form_create_input)


@router.patch(
    "/{odm_form_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Update ODM Form",
    response_model=OdmForm,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in draft status.\n"
            "- The ODM Form had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'odm_form_uid' wasn't found.",
        },
    },
)
def edit_odm_form(
    odm_form_uid: Annotated[str, OdmFormUID],
    odm_form_edit_input: Annotated[OdmFormPatchInput, Body()],
):
    odm_form_service = OdmFormService()
    return odm_form_service.update_with_relations(
        uid=odm_form_uid, concept_edit_input=odm_form_edit_input
    )


@router.post(
    "/{odm_form_uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Create a new version of ODM Form",
    description="""
State before:
 - uid must exist and the ODM Form must be in status Final.

Business logic:
- The ODM Form is changed to a draft state.

State after:
 - ODM Form changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=OdmForm,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't allow to create ODM Forms.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Form is not in final status.\n"
            "- The ODM Form with the specified 'odm_form_uid' could not be found.",
        },
    },
)
def create_odm_form_version(odm_form_uid: Annotated[str, OdmFormUID]):
    odm_form_service = OdmFormService()
    return odm_form_service.create_new_version(
        uid=odm_form_uid, cascade_new_version=True
    )


@router.post(
    "/{odm_form_uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve draft version of ODM Form",
    response_model=OdmForm,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in draft status.\n"
            "- The library doesn't allow to approve ODM Form.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'odm_form_uid' wasn't found.",
        },
    },
)
def approve_odm_form(odm_form_uid: Annotated[str, OdmFormUID]):
    odm_form_service = OdmFormService()
    return odm_form_service.approve(uid=odm_form_uid, cascade_edit_and_approve=True)


@router.delete(
    "/{odm_form_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Inactivate final version of ODM Form",
    response_model=OdmForm,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'odm_form_uid' could not be found.",
        },
    },
)
def inactivate_odm_form(odm_form_uid: Annotated[str, OdmFormUID]):
    odm_form_service = OdmFormService()
    return odm_form_service.inactivate_final(uid=odm_form_uid, cascade_inactivate=True)


@router.post(
    "/{odm_form_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivate retired version of a ODM Form",
    response_model=OdmForm,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'odm_form_uid' could not be found.",
        },
    },
)
def reactivate_odm_form(odm_form_uid: Annotated[str, OdmFormUID]):
    odm_form_service = OdmFormService()
    return odm_form_service.reactivate_retired(
        uid=odm_form_uid, cascade_reactivate=True
    )


@router.post(
    "/{odm_form_uid}/activity-groups",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds activity groups to the ODM Form.",
    response_model=OdmForm,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The activity groups were successfully added to the ODM Form."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity groups with the specified 'odm_form_uid' wasn't found.",
        },
    },
)
def add_activity_groups_to_odm_form(
    odm_form_activity_group_post_input: Annotated[
        list[OdmFormActivityGroupPostInput], Body()
    ],
    odm_form_uid: Annotated[str, OdmFormUID],
    override: Annotated[
        bool,
        Query(
            description="If true, all existing activity group relationships will be replaced with the provided activity group relationships.",
        ),
    ] = False,
):
    odm_form_service = OdmFormService()
    return odm_form_service.add_activity_groups(
        uid=odm_form_uid,
        odm_form_activity_group_post_input=odm_form_activity_group_post_input,
        override=override,
    )


@router.post(
    "/{odm_form_uid}/item-groups",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds item groups to the ODM Form.",
    response_model=OdmForm,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The item groups were successfully added to the ODM Form."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The item groups with the specified 'odm_form_uid' wasn't found.",
        },
    },
)
def add_item_groups_to_odm_form(
    odm_form_uid: Annotated[str, OdmFormUID],
    odm_form_item_group_post_input: Annotated[list[OdmFormItemGroupPostInput], Body()],
    override: Annotated[
        bool,
        Query(
            description="If true, all existing item group relationships will be replaced with the provided item group relationships.",
        ),
    ] = False,
):
    odm_form_service = OdmFormService()
    return odm_form_service.add_item_groups(
        uid=odm_form_uid,
        odm_form_item_group_post_input=odm_form_item_group_post_input,
        override=override,
    )


@router.post(
    "/{odm_form_uid}/vendor-elements",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds ODM Vendor Elements to the ODM Form.",
    response_model=OdmForm,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The ODM Vendor Elements were successfully added to the ODM Form."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendor Elements with the specified 'odm_form_uid' wasn't found.",
        },
    },
)
def add_vendor_elements_to_odm_form(
    odm_vendor_relation_post_input: Annotated[
        list[OdmVendorElementRelationPostInput], Body()
    ],
    odm_form_uid: Annotated[str, OdmFormUID],
    override: Annotated[
        bool,
        Query(
            description="If true, all existing ODM Vendor Element relationships will be replaced with the provided ODM Vendor Element relationships.",
        ),
    ] = False,
):
    odm_form_service = OdmFormService()
    return odm_form_service.add_vendor_elements(
        uid=odm_form_uid,
        odm_vendor_relation_post_input=odm_vendor_relation_post_input,
        override=override,
    )


@router.post(
    "/{odm_form_uid}/vendor-attributes",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds ODM Vendor Attributes to the ODM Form.",
    response_model=OdmForm,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The ODM Vendor Attributes were successfully added to the ODM Form."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendor Attributes with the specified 'odm_form_uid' wasn't found.",
        },
    },
)
def add_vendor_attributes_to_odm_form(
    odm_form_uid: Annotated[str, OdmFormUID],
    odm_vendor_relation_post_input: Annotated[list[OdmVendorRelationPostInput], Body()],
    override: Annotated[
        bool,
        Query(
            description="""If true, all existing ODM Vendor Attribute relationships will
        be replaced with the provided ODM Vendor Attribute relationships.""",
        ),
    ] = False,
):
    odm_form_service = OdmFormService()
    return odm_form_service.add_vendor_attributes(
        uid=odm_form_uid,
        odm_vendor_relation_post_input=odm_vendor_relation_post_input,
        override=override,
    )


@router.post(
    "/{odm_form_uid}/vendor-element-attributes",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Adds ODM Vendor Element attributes to the ODM Form.",
    response_model=OdmForm,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The ODM Vendor Element attributes were successfully added to the ODM Form."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendor Element attributes with the specified 'odm_form_uid' wasn't found.",
        },
    },
)
def add_vendor_element_attributes_to_odm_form(
    odm_form_uid: Annotated[str, OdmFormUID],
    odm_vendor_relation_post_input: Annotated[list[OdmVendorRelationPostInput], Body()],
    override: Annotated[
        bool,
        Query(
            description="""If true, all existing ODM Vendor Element attribute relationships
        will be replaced with the provided ODM Vendor Element attribute relationships.""",
        ),
    ] = False,
):
    odm_form_service = OdmFormService()
    return odm_form_service.add_vendor_element_attributes(
        uid=odm_form_uid,
        odm_vendor_relation_post_input=odm_vendor_relation_post_input,
        override=override,
    )


@router.post(
    "/{odm_form_uid}/vendors",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Manages all ODM Vendors by replacing existing ODM Vendors by provided ODM Vendors.",
    response_model=OdmForm,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The ODM Vendors were successfully added to the ODM Form."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendors with the specified 'odm_form_uid' wasn't found.",
        },
    },
)
def manage_vendors_of_odm_form(
    odm_form_uid: Annotated[str, OdmFormUID],
    odm_vendors_post_input: Annotated[OdmVendorsPostInput, Body()],
):
    odm_form_service = OdmFormService()
    return odm_form_service.manage_vendors(
        uid=odm_form_uid, odm_vendors_post_input=odm_vendors_post_input
    )


@router.delete(
    "/{odm_form_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Delete draft version of ODM Form",
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The ODM Form was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in draft status.\n"
            "- The ODM Form was already in final state or is in use.\n"
            "- The library doesn't allow to delete ODM Form.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Form with the specified 'odm_form_uid' could not be found.",
        },
    },
)
def delete_odm_form(odm_form_uid: Annotated[str, OdmFormUID]):
    odm_form_service = OdmFormService()
    odm_form_service.soft_delete(uid=odm_form_uid, cascade_delete=True)
