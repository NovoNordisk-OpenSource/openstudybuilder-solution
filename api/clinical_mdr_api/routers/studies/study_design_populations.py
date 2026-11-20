"""API endpoints for study_design_populations"""

from typing import Annotated

from fastapi import Body

from clinical_mdr_api.models.study_selections.study_design_population import (
    StudyDesignPopulation,
    StudyDesignPopulationInput,
    StudyDesignPopulationPatchInput,
    StudyDesignPopulationVersion,
    StudySelectionDesignPopulationNewOrder,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import (
    _generic_descriptions,
    decorators,
    study_router as router,
)
from clinical_mdr_api.routers.studies import utils
from clinical_mdr_api.services.studies.study_design_population import (
    StudyDesignPopulationService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse


@router.get(
    "/studies/{study_uid}/study-design-populations",
    dependencies=[security, rbac.STUDY_READ],
    summary="Return study design populations currently selected for the study.",
    description="""
State before:
 - Study must exist.

Business logic:
 - Returns all study design populations for a specific Study.

State after:
 - No change.

Possible errors:
 - Invalid study-uid.
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        400: _generic_descriptions.ERROR_400,
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_study_design_populations(
    study_uid: Annotated[str, utils.studyUID],
    sort_by: _generic_descriptions.SORT_BY_QUERY = None,
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    filters: _generic_descriptions.FILTERS_QUERY = None,
    operator: _generic_descriptions.FILTER_OPERATOR_QUERY = settings.default_filter_operator,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> CustomPage[StudyDesignPopulation]:
    service = StudyDesignPopulationService()
    all_items = service.get_all_study_design_populations(
        study_uid=study_uid,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        total_count=total_count,
        study_value_version=study_value_version,
    )
    return CustomPage(
        items=all_items.items,
        total=all_items.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/studies/{study_uid}/study-design-populations/audit-trail",
    dependencies=[security, rbac.STUDY_READ],
    summary="List audit trail related to all study design populations within the specified study-uid.",
    description="""
State before:
 - Study must exist.

Business logic:
 - List the audit trail of all study design populations within the specified study-uid.

State after:
 - No change.

Possible errors:
 - Invalid study-uid.

Returned data:
 - List of actions and changes related to all study design populations.
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the provided study.",
        },
    },
)
def get_study_design_populations_all_audit_trail(
    study_uid: Annotated[str, utils.studyUID],
) -> list[StudyDesignPopulationVersion]:
    service = StudyDesignPopulationService()
    return service.get_all_population_audit_trail(
        study_uid=study_uid,
    )


@router.get(
    "/studies/{study_uid}/study-design-populations/{study_design_population_uid}/audit-trail",
    dependencies=[security, rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study design population.",
    description="""
State before:
 - Study and study design population must exist.

Business logic:
 - List a specific entry in the audit trail related to the specified study design population for the specified study-uid.

State after:
 - No change.

Possible errors:
 - Invalid study-uid.
 - Invalid study-design-population-uid.

Returned data:
 - List of actions and changes related to the specified study design population.
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the design population provided for the study provided.",
        },
    },
)
def get_study_design_population_audit_trail(
    study_uid: Annotated[str, utils.studyUID],
    study_design_population_uid: Annotated[str, utils.study_design_population_uid],
) -> list[StudyDesignPopulationVersion]:
    service = StudyDesignPopulationService()
    return service.get_population_audit_trail(
        study_uid=study_uid,
        population_uid=study_design_population_uid,
    )


@router.get(
    "/studies/{study_uid}/study-design-populations/{study_design_population_uid}",
    dependencies=[security, rbac.STUDY_READ],
    summary="Return a specific study design population.",
    description="""
State before:
 - Study and study design population must exist.

Business logic:
 - Returns the specified study design population for a specific Study.

State after:
 - No change.

Possible errors:
 - Invalid study-uid or study-design-population-uid.
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exists no study design population for the study provided.",
        },
    },
)
def get_study_design_population(
    study_uid: Annotated[str, utils.studyUID],
    study_design_population_uid: Annotated[str, utils.study_design_population_uid],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> StudyDesignPopulation:
    service = StudyDesignPopulationService()
    return service.get_specific_selection(
        study_uid=study_uid,
        population_uid=study_design_population_uid,
        study_value_version=study_value_version,
    )


@router.post(
    "/studies/{study_uid}/study-design-populations",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Add a study design population to a study.",
    description="""
State before:
 - Study must exist and study status must be in draft.

Business logic:
 - Creates a new StudyDesignPopulation node and links it to the study.

State after:
 - StudyDesignPopulation is added to the study.
 - A new entry is added to the audit trail.

Possible errors:
 - Invalid study-uid.
""",
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: _generic_descriptions.ERROR_400,
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
def post_study_design_population(
    study_uid: Annotated[str, utils.studyUID],
    population_input: Annotated[
        StudyDesignPopulationInput,
        Body(description="Properties of the study design population to create."),
    ],
) -> StudyDesignPopulation:
    service = StudyDesignPopulationService()
    return service.create(
        study_uid=study_uid,
        population_input=population_input,
    )


@router.patch(
    "/studies/{study_uid}/study-design-populations/{study_design_population_uid}",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Update a study design population.",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - Study design population must exist.

Business logic:
 - Updates the specified study design population with new property values.

State after:
 - Study design population is updated.
 - A new entry is added to the audit trail.

Possible errors:
 - Invalid study-uid or study-design-population-uid.
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        400: _generic_descriptions.ERROR_400,
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
def patch_study_design_population(
    study_uid: Annotated[str, utils.studyUID],
    study_design_population_uid: Annotated[str, utils.study_design_population_uid],
    population_input: Annotated[
        StudyDesignPopulationPatchInput,
        Body(description="Properties of the study design population to update."),
    ],
) -> StudyDesignPopulation:
    service = StudyDesignPopulationService()
    return service.update(
        study_uid=study_uid,
        population_uid=study_design_population_uid,
        population_input=population_input,
    )


@router.patch(
    "/studies/{study_uid}/study-design-populations/{study_design_population_uid}/order",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Change display order of a study design population.",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - Study design population must exist.

Business logic:
 - Moves the specified study design population to the new order position.
 - Shifts the order of the study design populations between the old and new position by one to keep the order consecutive.

State after:
 - Order number for specified study design population is updated to the new order number.
 - Note this will change the order of other study design populations in between the old and new position as well.
 - A new entry is added to the audit trail for the re-ordering of the study design population.

Possible errors:
 - Invalid study-uid or study-design-population-uid.
 - New order number is out of range.
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        400: _generic_descriptions.ERROR_400,
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or study design population not found.",
        },
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
def patch_study_design_population_order(
    study_uid: Annotated[str, utils.studyUID],
    study_design_population_uid: Annotated[str, utils.study_design_population_uid],
    new_order_input: Annotated[
        StudySelectionDesignPopulationNewOrder,
        Body(description="New value to set for the order property of the selection"),
    ],
) -> StudyDesignPopulation:
    service = StudyDesignPopulationService()
    return service.reorder(
        study_uid=study_uid,
        population_uid=study_design_population_uid,
        new_order=new_order_input.new_order,
    )


@router.delete(
    "/studies/{study_uid}/study-design-populations/{study_design_population_uid}",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Delete a study design population.",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - Study design population must exist.

Business logic:
 - Removes the specified study design population from the study.
 - The population node remains in the database but is marked as deleted via audit trail.

State after:
 - Study design population is deleted from the study.
 - A new entry is added to the audit trail.

Possible errors:
 - Invalid study-uid or study-design-population-uid.
""",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or study design population not found.",
        },
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
def delete_study_design_population(
    study_uid: Annotated[str, utils.studyUID],
    study_design_population_uid: Annotated[str, utils.study_design_population_uid],
) -> None:
    service = StudyDesignPopulationService()
    service.delete(
        study_uid=study_uid,
        population_uid=study_design_population_uid,
    )
