"""API endpoints to study_design_classes"""

from typing import Annotated

from fastapi import Body

from clinical_mdr_api.models.study_selections.study_selection import (
    StudyDesignClass,
    StudyDesignClassInput,
)
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.routers.studies import utils
from clinical_mdr_api.services.studies.study_design_class import StudyDesignClassService
from common.auth import rbac
from common.auth.dependencies import security


@router.get(
    "/studies/{study_uid}/study-design-classes",
    dependencies=[security, rbac.STUDY_READ],
    summary="Return study_design_class currently selected for the study.",
    description="""
State before:
 - Study must exist.
 
Business logic:
 - Returns one study design class if it exists for a specific Study.

State after:
 - no change.
 
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
def get(
    study_uid: Annotated[str, utils.studyUID],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> StudyDesignClass:
    study_design_class_service = StudyDesignClassService()
    study_design_class = study_design_class_service.get_study_design_class(
        study_uid=study_uid,
        study_value_version=study_value_version,
    )
    return study_design_class


@router.get(
    "/studies/{study_uid}/study-design-classes/editions-allowed",
    dependencies=[security, rbac.STUDY_READ],
    summary="Return boolean indication whether StudyDesignClass can be edited.",
    description="""
State before:
 - Study must exist.
 
Business logic:
 - If there exist some StudyArms or StudyCohorts in a given Study, the endpoint will return false otherwise it returns true.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.
""",
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def check_if_study_design_class_can_be_edited(
    study_uid: Annotated[str, utils.studyUID],
) -> bool:
    study_design_class_service = StudyDesignClassService()
    return study_design_class_service.is_study_design_class_edition_allowed(
        study_uid=study_uid,
    )


@router.post(
    "/studies/{study_uid}/study-design-classes",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Add a study design class to a study",
    description="""
State before:
 - Study must exist and study status must be in draft.

Business logic:
 - Add a study design class to a study if it does not exist already.

State after:
 - study design classes is added to the study.
 
Possible errors:
 - Invalid study-uid or study design class already exists.
    """,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: _generic_descriptions.ERROR_400,
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
        409: _generic_descriptions.ERROR_409,
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
def post_new_design_class(
    study_uid: Annotated[str, utils.studyUID],
    study_design_class_input: Annotated[
        StudyDesignClassInput,
        Body(description="Related parameters of the selection that shall be created."),
    ],
) -> StudyDesignClass:
    service = StudyDesignClassService()
    return service.create(
        study_uid=study_uid, study_design_class_input=study_design_class_input
    )


@router.put(
    "/studies/{study_uid}/study-design-classes",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Edit a study design class",
    description="""
State before:
 - Study must exist and study status must be in draft.

Business logic:
 - study design class node is found and updated with the data passed in the body

State after:
 - study design class is edited in the study.
 - Added new entry in the audit trail for the update of the study-design-class.

Possible errors:
 - Invalid study-uid or study_design_class_uid .
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
def put_update_design_class(
    study_uid: Annotated[str, utils.studyUID],
    study_design_class_input: Annotated[
        StudyDesignClassInput,
        Body(description="Related parameters of the selection that shall be created."),
    ],
) -> StudyDesignClass:
    service = StudyDesignClassService()
    return service.edit(
        study_uid=study_uid,
        study_design_class_input=study_design_class_input,
    )
