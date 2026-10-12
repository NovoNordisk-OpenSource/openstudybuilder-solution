from typing import Annotated, Any

from fastapi import Body, Request

from clinical_mdr_api.models.study_selections.study_selection import (
    StudyCompoundDosing,
    StudyCompoundDosingInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import (
    _generic_descriptions,
    decorators,
    study_router as router,
)
from clinical_mdr_api.routers.studies import utils
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_compound_dosing_selection import (
    StudyCompoundDosingSelectionService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse


@router.get(
    "/studies/{study_uid}/study-compound-dosings",
    dependencies=[security, rbac.STUDY_READ],
    summary="List all study compound dosings currently defined for the study",
    description=_generic_descriptions.DATA_EXPORTS_HEADER + """

A dose value is either a library one in `dose_value` or a study level free text in
`free_text_dose_value`, and a dose frequency likewise either `dose_frequency` or
`free_text_dose_frequency` — never both in each pair. `dose_value_label` and
`dose_frequency_label` collapse each pair into the single rendered string, and are the
fields to sort and filter on when the source does not matter.""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there is no study with the given uid.",
        },
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid=study_compound_dosing_uid",
            "order",
            "element=study_element.name",
            "compound=study_compound.compound.name",
            "compound_alias=study_compound.compound_alias.name",
            "dose_value_value=dose_value.value",
            "dose_value_unit=dose_value.unit_label",
            "free_text_dose_value",
            # The *_label columns are what the UI displays and filters on, so the
            # export carries them too rather than only the two underlying sources.
            "dose_value_label",
            "dose_frequency=dose_frequency.term_name",
            "free_text_dose_frequency",
            "dose_frequency_label",
            "dose_collection_activity_instance=study_activity_instance.activity_instance.name|study_activity_instance.activity.name",
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
def get_all_selected_compound_dosings(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: Annotated[str, utils.studyUID],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[StudyCompoundDosing]:
    service = StudyCompoundDosingSelectionService()
    all_items = service.get_all_compound_dosings(
        study_uid=study_uid,
        study_value_version=study_value_version,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
    )

    return CustomPage(
        items=all_items.items,
        total=all_items.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/studies/{study_uid}/study-compound-dosings/headers",
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
    study_uid: Annotated[str, utils.studyUID],
    field_name: _generic_descriptions.HEADER_FIELD_NAME_QUERY,
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    service = StudyCompoundDosingSelectionService()
    return service.get_distinct_values_for_header(
        study_uid=study_uid,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/study-compound-dosings/headers",
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
def get_distinct_compound_dosings_values_for_header(
    field_name: _generic_descriptions.HEADER_FIELD_NAME_QUERY,
    search_string: _generic_descriptions.HEADER_SEARCH_STRING_QUERY = "",
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    page_size: _generic_descriptions.HEADER_PAGE_SIZE_QUERY = settings.default_header_page_size,
) -> list[Any]:
    service = StudyCompoundDosingSelectionService()
    return service.get_distinct_values_for_header(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/studies/{study_uid}/study-compound-dosings/audit-trail",
    dependencies=[security, rbac.STUDY_READ],
    summary="List full audit trail related to definition of all study compound dosings.",
    description="""
Parameters:
 - uid as study-uid (required)
 - [NOT YET IMPLEMENTED] study status (optional)
 - [NOT YET IMPLEMENTED] study version (required when study status is locked)

State before:
 - Study must exist.

Business logic:
 - List all entries in the audit trail related to study compound dosings for specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.
 - Each entry reports the dose value and dose frequency as they stood, whether taken from the
   library (`dose_value`, `dose_frequency`) or given as study level free text
   (`free_text_dose_value`, `free_text_dose_frequency`). Switching between the two shows up as
   one field becoming null and the other being set.

State after:
 - no change.

Possible errors:
 - Invalid study-uid.

Returned data:
 - List of actions and changes related to study compounds.
    """,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_compound_dosings_audit_trail(
    study_uid: Annotated[str, utils.studyUID],
) -> list[StudyCompoundDosing]:
    service = StudyCompoundDosingSelectionService()
    return service.get_all_selection_audit_trail(study_uid=study_uid)


@router.get(
    "/studies/{study_uid}/study-compound-dosings/{study_compound_dosing_uid}/audit-trail",
    dependencies=[security, rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study compound dosing.",
    description="""
Parameters:
 - uid as study-uid (required)
 - study-compound-dosing-uid (required)
 - [NOT YET IMPLEMENTED] study status (optional)
 - [NOT YET IMPLEMENTED] study version (required when study status is locked)

State before:
 - Study and study compound dosing must exist.

Business logic:
 - List a specific entry in the audit trail related to the specified study compound dosing for the specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.
 - Each entry reports the dose value and dose frequency as they stood, whether taken from the
   library (`dose_value`, `dose_frequency`) or given as study level free text
   (`free_text_dose_value`, `free_text_dose_frequency`).

State after:
 - no change.

Possible errors:
 - Invalid study-uid.

Returned data:
 - List of actions and changes related to the specified study compound dosing.
    """,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the compound dosing for the study provided.",
        },
    },
)
def get_compound_dosing_audit_trail(
    study_uid: Annotated[str, utils.studyUID],
    study_compound_dosing_uid: Annotated[str, utils.study_compound_dosing_uid],
) -> list[StudyCompoundDosing]:
    service = StudyCompoundDosingSelectionService()
    return service.get_compound_dosing_audit_trail(
        study_uid=study_uid, compound_dosing_uid=study_compound_dosing_uid
    )


@router.post(
    "/studies/{study_uid}/study-compound-dosings",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Add a study compound dosing to a study",
    description="""
Business logic:
 - The dose value is either selected from the library through `dose_value_uid`, or given
   as a study level free text through `free_text_dose_value`. The two are mutually
   exclusive, and providing both is rejected.
 - The dose frequency works the same way: either `dose_frequency_uid` from the library,
   or a study level free text through `free_text_dose_frequency`, never both.
 - The two choices are independent — a library dose value may be combined with a free
   text dose frequency, and the reverse.
 - A library `dose_value_uid` must be one of the dose values defined on the medicinal product.
 - A library `dose_frequency_uid` may be **any** term of the dose frequency codelist, not only
   one of those the medicinal product defines — a medicinal product lists a handful of
   frequencies while studies need the rest of the codelist. A uid outside that codelist is
   rejected.
 - The free text fields exist to express a value that is not in the library at all.
 - A dose value or dose frequency given as free text is not added to the library.""",
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: {
            "model": ErrorResponse,
            "description": "Bad Request - both 'dose_value_uid' and 'free_text_dose_value' were provided, "
            "or both 'dose_frequency_uid' and 'free_text_dose_frequency' were provided, "
            "or 'dose_frequency_uid' is not a term of the dose frequency codelist",
        },
        409: {
            "model": ErrorResponse,
            "description": "Conflict - a study compound dosing already exists for the selected study compound and dose configuration.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study, study compound, study element or study activity instance is not found with the passed 'study_uid'.",
        },
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
def create_study_compound_dosing(
    study_uid: Annotated[str, utils.studyUID],
    selection: Annotated[
        StudyCompoundDosingInput,
        Body(
            description="Related parameters of the compound dosing that shall be created.",
        ),
    ],
) -> StudyCompoundDosing:
    service = StudyCompoundDosingSelectionService()
    return service.make_selection(study_uid=study_uid, selection_create_input=selection)


@router.delete(
    "/studies/{study_uid}/study-compound-dosings/{study_compound_dosing_uid}",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Delete a study compound dosing",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the compound dosing and the study provided.",
        },
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
def delete_compound_dosing(
    study_uid: Annotated[str, utils.studyUID],
    study_compound_dosing_uid: Annotated[str, utils.study_compound_dosing_uid],
):
    StudyService().check_if_study_exists(study_uid)
    service = StudyCompoundDosingSelectionService()
    service.delete_selection(
        study_uid=study_uid, study_selection_uid=study_compound_dosing_uid
    )


@router.patch(
    "/studies/{study_uid}/study-compound-dosings/{study_compound_dosing_uid}",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Edit or replace a study compound dosing",
    description="""
State before:
 - Study must exist and be in status draft

Business logic:
 - Update specified study-compound-dosing with selection of existing study compound and study element items.
 - A single relationships can be defined for a study compound dosing to each of the following code list terms:
   - Dose frequency
 - An optional link can be defined to the study activity instance collecting the dose.
   Send `study_activity_instance_uid` explicitly as `null` to clear it.
 - The dose value is either selected from the library through `dose_value_uid`, or given
   as a study level free text through `free_text_dose_value`. The two are mutually
   exclusive, and providing both is rejected. The dose frequency works the same way,
   through `dose_frequency_uid` or `free_text_dose_frequency`. The two choices are
   independent of one another.
 - `dose_value_uid` must be one of the dose values defined on the medicinal product, while
   `dose_frequency_uid` may be any term of the dose frequency codelist.
 - Omitted fields are filled in from the current state of the study compound dosing.
   Switching either the dose value or the dose frequency from one mode to the other
   therefore requires sending the field being switched away from explicitly as `null`.
 - Order number for the study compound cannot be changed by this API endpoint.

State after:
 - related parameters are updated for the study compound dosing.
 - Added new entry in the audit trail for the update of the study-compound-dosing.""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: {
            "model": ErrorResponse,
            "description": "Bad Request - The study is locked, or both 'dose_value_uid' and 'free_text_dose_value' were provided, "
            "or both 'dose_frequency_uid' and 'free_text_dose_frequency' were provided, "
            "or 'dose_frequency_uid' is not a term of the dose frequency codelist",
        },
        409: {
            "model": ErrorResponse,
            "description": "Conflict - a study compound dosing already exists for the selected study compound and dose configuration.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection with the given uid, or the study activity instance is not found with the passed 'study_uid'.",
        },
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
def update_compound_dosing(
    study_uid: Annotated[str, utils.studyUID],
    study_compound_dosing_uid: Annotated[str, utils.study_compound_dosing_uid],
    selection: Annotated[
        StudyCompoundDosingInput,
        Body(description="Related parameters of the selection that shall be updated."),
    ],
) -> StudyCompoundDosing:
    service = StudyCompoundDosingSelectionService()
    return service.patch_selection(
        study_uid=study_uid,
        study_selection_uid=study_compound_dosing_uid,
        selection_update_input=selection,
    )
