"""API endpoints to study_source_variables"""

from typing import Annotated

from fastapi import Body

from clinical_mdr_api.models.study_selections.study_selection import (
    StudySourceVariable,
    StudySourceVariableInput,
)
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.routers.studies import utils
from clinical_mdr_api.services.studies.study_source_variable import (
    StudySourceVariableService,
)
from common.auth import rbac
from common.auth.dependencies import security


@router.get(
    "/studies/{study_uid}/study-source-variables",
    dependencies=[security, rbac.STUDY_READ],
    summary="Return study_source_variable currently selected for the study.",
    description="""
State before:
 - Study must exist.
 
Business logic:
 - Returns one study source variable if it exists for a specific Study.

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
) -> StudySourceVariable | None:
    study_source_variable_service = StudySourceVariableService()
    study_source_variable = study_source_variable_service.get_study_source_variable(
        study_uid=study_uid,
        study_value_version=study_value_version,
    )
    return study_source_variable


@router.post(
    "/studies/{study_uid}/study-source-variables",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Add a study source variable to a study",
    description="""
State before:
 - Study must exist and study status must be in draft.

Business logic:
 - Add a study source_variable to a study if it does not exist already.

State after:
 - study source variables is added to the study.
 
Possible errors:
 - Invalid study-uid or study source variable already exists.
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
def post_new_source_variable(
    study_uid: Annotated[str, utils.studyUID],
    study_source_variable_input: Annotated[
        StudySourceVariableInput,
        Body(description="Related parameters of the selection that shall be created."),
    ],
) -> StudySourceVariable:
    service = StudySourceVariableService()
    return service.create(
        study_uid=study_uid, study_source_variable_input=study_source_variable_input
    )


@router.put(
    "/studies/{study_uid}/study-source-variables",
    dependencies=[security, rbac.STUDY_WRITE],
    summary="Edit a study source variable",
    description="""
State before:
 - Study must exist and study status must be in draft.

Business logic:
 - study source variable node is found and updated with the data passed in the body

State after:
 - study source variable is edited in the study.
 - Added new entry in the audit trail for the update of the study-source-variable.

Possible errors:
 - Invalid study-uid or study_source_variable_uid .
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
def put_update_source_variable(
    study_uid: Annotated[str, utils.studyUID],
    study_source_variable_input: Annotated[
        StudySourceVariableInput,
        Body(description="Related parameters of the selection that shall be created."),
    ],
) -> StudySourceVariable:
    service = StudySourceVariableService()
    return service.edit(
        study_uid=study_uid,
        study_source_variable_input=study_source_variable_input,
    )
