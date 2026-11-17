from typing import Annotated, Any

from fastapi import Body, Path, Request

from clinical_mdr_api.models.study_selections import study_auxiliary_device as models
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import (
    _generic_descriptions,
    decorators,
    study_router as router,
)
from clinical_mdr_api.services.studies.study_auxiliary_device import (
    StudyAuxiliaryDeviceService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

studyUID = Path(description="The unique id of the study.")
study_auxiliary_device_uid_description = Path(
    description="The unique id of the study auxiliary device."
)
BASE = "/studies/{study_uid}/study-auxiliary-devices"


@router.get(
    BASE,
    dependencies=[security, rbac.STUDY_READ],
    summary="List all study auxiliary devices selected for the study.",
    description=f"""
State before:
 - Study must exist.

Business logic:
 - List the auxiliary devices of the latest study value, or of the given `study_value_version`.
 - Device name, NCI preferred name, submission value, definition and algorithm come from the selected CT term.

State after:
 - no change.

Possible errors:
 - Invalid study-uid.

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
            "order",
            "auxiliary_device_name",
            "auxiliary_device_submission_value",
            "auxiliary_device_nci_preferred_name",
            "auxiliary_device_definition",
            "auxiliary_device_algorithm",
            "study_uid",
            "study_version",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
def get_all(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: Annotated[str, studyUID],
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> CustomPage[models.StudyAuxiliaryDevice]:
    all_items = StudyAuxiliaryDeviceService().get_all(
        study_uid=study_uid,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
        study_value_version=study_value_version,
    )
    return CustomPage(
        items=all_items.items,
        total=all_items.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    f"{BASE}/headers",
    dependencies=[security, rbac.STUDY_READ],
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
    study_uid: Annotated[str, studyUID],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    return StudyAuxiliaryDeviceService().get_distinct_values_for_header(
        study_uid=study_uid,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
        study_value_version=study_value_version,
    )


@router.get(
    f"{BASE}/audit-trail",
    dependencies=[security, rbac.STUDY_READ],
    summary="List audit trail of all study auxiliary devices within the study",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_audit_trail(
    study_uid: Annotated[str, studyUID],
) -> list[models.StudyAuxiliaryDeviceVersion]:
    return StudyAuxiliaryDeviceService().audit_trail_all(study_uid)


@router.get(
    BASE + "/{study_auxiliary_device_uid}",
    dependencies=[security, rbac.STUDY_READ],
    summary="Get a specific study auxiliary device",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_study_auxiliary_device(
    study_uid: Annotated[str, studyUID],
    study_auxiliary_device_uid: Annotated[str, study_auxiliary_device_uid_description],
) -> models.StudyAuxiliaryDevice:
    return StudyAuxiliaryDeviceService().find_by_uid(
        study_uid=study_uid, uid=study_auxiliary_device_uid
    )


@router.get(
    BASE + "/{study_auxiliary_device_uid}/audit-trail",
    dependencies=[security, rbac.STUDY_READ],
    summary="List audit trail of a specific study auxiliary device",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_study_auxiliary_device_audit_trail(
    study_uid: Annotated[str, studyUID],
    study_auxiliary_device_uid: Annotated[str, study_auxiliary_device_uid_description],
) -> list[models.StudyAuxiliaryDeviceVersion]:
    return StudyAuxiliaryDeviceService().audit_trail(
        study_uid=study_uid, uid=study_auxiliary_device_uid
    )


@router.post(
    BASE,
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Add an auxiliary device to a study",
    description="""
State before:
 - Study must exist and be in draft.

Business logic:
 - Select an existing CT term of the auxiliary device codelist (`DEVICE_DEF`).
 - The same device can only be selected once per study.
 - Orders of the following devices are shifted to stay consecutive.

Possible errors:
 - Invalid study-uid, unknown term, term not in the auxiliary device codelist, device already selected.
    """,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: {
            "model": ErrorResponse,
            "description": "The device is already selected or the term is not in the auxiliary device codelist",
        },
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
def post_study_auxiliary_device(
    study_uid: Annotated[str, studyUID],
    selection: Annotated[
        models.StudyAuxiliaryDeviceCreateInput,
        Body(description="Related parameters of the selection that shall be created."),
    ],
) -> models.StudyAuxiliaryDevice:
    return StudyAuxiliaryDeviceService().create(
        study_uid=study_uid, item_input=selection
    )


@router.delete(
    BASE + "/{study_auxiliary_device_uid}",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Remove an auxiliary device from a study",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The selection was successfully deleted."},
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
def delete_study_auxiliary_device(
    study_uid: Annotated[str, studyUID],
    study_auxiliary_device_uid: Annotated[str, study_auxiliary_device_uid_description],
):
    StudyAuxiliaryDeviceService().delete(
        study_uid=study_uid, uid=study_auxiliary_device_uid
    )


@router.patch(
    BASE + "/{study_auxiliary_device_uid}/order",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Change display order of a study auxiliary device",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
def patch_reorder(
    study_uid: Annotated[str, studyUID],
    study_auxiliary_device_uid: Annotated[str, study_auxiliary_device_uid_description],
    new_order_input: Annotated[
        models.StudyAuxiliaryDeviceNewOrder,
        Body(description="New value to set for the order property of the selection"),
    ],
) -> models.StudyAuxiliaryDevice:
    return StudyAuxiliaryDeviceService().reorder(
        study_uid=study_uid,
        uid=study_auxiliary_device_uid,
        new_order=new_order_input.new_order,
    )
