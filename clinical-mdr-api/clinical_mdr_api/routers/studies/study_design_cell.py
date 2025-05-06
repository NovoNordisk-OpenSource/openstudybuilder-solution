from typing import Annotated

from fastapi import Body, Response, status

from clinical_mdr_api.models.study_selections.study_selection import (
    StudyDesignCell,
    StudyDesignCellBatchInput,
    StudyDesignCellBatchOutput,
    StudyDesignCellCreateInput,
    StudyDesignCellEditInput,
    StudyDesignCellVersion,
    StudySelectionActivity,
)
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.routers.studies import utils
from clinical_mdr_api.services.studies.study_design_cell import StudyDesignCellService
from common.auth import rbac
from common.models.error import ErrorResponse


@router.get(
    "/studies/{study_uid}/study-design-cells",
    dependencies=[rbac.STUDY_READ],
    summary="List all study design cells currently defined for the study",
    response_model=list[StudyDesignCell],
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
def get_all_design_cells(
    study_uid: Annotated[str, utils.studyUID],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> list[StudyDesignCell]:
    service = StudyDesignCellService()
    cells = service.get_all_design_cells(
        study_uid=study_uid, study_value_version=study_value_version
    )
    return cells


@router.post(
    "/studies/{study_uid}/study-design-cells",
    dependencies=[rbac.STUDY_WRITE],
    summary="Add a study design cell to a study",
    response_model=StudyDesignCell,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - A study design cell already exists for selected study arm and epoch",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study, study arm or study epoch is not found with the passed 'study_uid'.",
        },
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
def post_new_design_cell_create(
    study_uid: Annotated[str, utils.studyUID],
    selection: Annotated[
        StudyDesignCellCreateInput,
        Body(
            description="Related parameters of the design cell that shall be created."
        ),
    ],
) -> StudyDesignCell:
    service = StudyDesignCellService()
    return service.create(study_uid=study_uid, design_cell_input=selection)


@router.patch(
    "/studies/{study_uid}/study-design-cells/{study_design_cell_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Update a study design cell",
    description="""
    The StudyDesignCell has the following properties:
        -StudyArm 
        -StudyBranchArm 
        -StudyEpoch 
        -StudyElement
        -Transition_rule
    Patching properties has different dependencies, to patch:
        -StudyArm
            -StudyArm has to exists
            -if the StudyDesignCell already has a StudyBranchArm then the StudyBranchArm has to be set as null on the payload.
        -StudyBranchArm
            -StudyBranchArm has to exists
            -if the StudyDesignCell already has a StudyArm then it will be disconnected from PREVIOUS StudyArm and switched to the NEW StudyBranchArm
        -StudyElement
            -StudyElement has to exists
        -StudyEpoch
            -StudyEpoch has to exists
        -Transition_rule
            -no dependencies, is just a string field
     """,
    response_model=None,
    response_model_exclude_unset=True,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {
            "description": "No content - The study design cell was successfully updated."
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study design cell with the specified 'study_design_cell_uid' could not be found.",
        },
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
#  pylint: disable=unused-argument
def edit_design_cell(
    study_uid: Annotated[str, utils.studyUID],
    study_design_cell_uid: Annotated[str, utils.study_design_cell_uid],
    selection: Annotated[
        StudyDesignCellEditInput,
        Body(description="Related parameters of the selection that shall be updated."),
    ],
) -> StudySelectionActivity:
    service = StudyDesignCellService()
    service.patch(
        study_uid=study_uid,
        design_cell_update_input=selection,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/studies/{study_uid}/study-design-cells/{study_design_cell_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study design cell",
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the design cell and the study provided.",
        },
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
def delete_design_cell(
    study_uid: Annotated[str, utils.studyUID],
    study_design_cell_uid: Annotated[str, utils.study_design_cell_uid],
):
    service = StudyDesignCellService()
    service.delete(study_uid=study_uid, design_cell_uid=study_design_cell_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/studies/{study_uid}/study-design-cells/audit-trail/",
    dependencies=[rbac.STUDY_READ],
    summary="List full audit trail related to definition of all study design cells.",
    description="""
The following values should be returned for all study design cells:
- date_time
- author_username
- action
- activity
- order
    """,
    response_model=list[StudyDesignCellVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_design_cells_audit_trail(
    study_uid: Annotated[str, utils.studyUID],
) -> list[StudyDesignCellVersion]:
    service = StudyDesignCellService()
    return service.get_all_design_cells_audit_trail(study_uid=study_uid)


@router.get(
    "/studies/{study_uid}/study-design-cells/{study_design_cell_uid}/audit-trail/",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study design cell.",
    response_model=list[StudyDesignCellVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the design cell for the study provided.",
        },
    },
)
def get_specific_schedule_audit_trail(
    study_uid: Annotated[str, utils.studyUID],
    study_design_cell_uid: Annotated[str, utils.study_design_cell_uid],
) -> StudyDesignCellVersion:
    service = StudyDesignCellService()
    return service.get_specific_selection_audit_trail(
        study_uid=study_uid, design_cell_uid=study_design_cell_uid
    )


@router.post(
    "/studies/{study_uid}/study-design-cells/batch",
    dependencies=[rbac.STUDY_WRITE],
    summary="Batch operations (create, delete) for study design cells",
    response_model=list[StudyDesignCellBatchOutput],
    status_code=207,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
def design_cell_batch_operations(
    study_uid: Annotated[str, utils.studyUID],
    operations: Annotated[
        list[StudyDesignCellBatchInput],
        Body(description="List of operations to perform"),
    ],
) -> list[StudyDesignCellBatchOutput]:
    service = StudyDesignCellService()
    return service.handle_batch_operations(study_uid, operations)


@router.get(
    "/studies/{study_uid}/study-design-cells/arm/{arm_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="""List all study design-cells currently selected for study with provided uid that are connected to an StudyArm with arm_uid""",
    description="""
    State before:
    - Study must exist.
     
    Business logic:
     - By default (no study status is provided) list all study design-cells for the study uid in status draft. If the study not exist in status draft then return the study design-cells for the study in status released. If the study uid only exist as deleted then this is returned.
     - If a specific study status parameter is provided then return study design-cell for this study status.
    - If the locked study status parameter is requested then a study version should also be provided, and then the study design-cells for the specific locked study version is returned.
    - Indicate by a boolean variable if the study design-cell can be updated (if the selected study is in status draft).  
    - Indicate by a boolean variable if all expected selections have been made for each study design-cells, or some are missing.


    State after:
    - no change.
     
    Possible errors:
    - Invalid study-uid.
""",
    response_model=list[StudyDesignCell],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_selected_design_cells_connected_arm(
    study_uid: str,
    arm_uid: str,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> list[StudyDesignCell]:
    service = StudyDesignCellService()
    return service.get_all_selection_within_arm(
        study_uid=study_uid,
        study_arm_uid=arm_uid,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{study_uid}/study-design-cells/branch-arm/{branch_arm_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="""List all study design-cells currently selected for study with provided
    uid that are connected to an StudyBranchArm with branch_arm_uid""",
    description="""
    State before:
    - Study must exist.
     
    Business logic:
     - By default (no study status is provided) list all study design-cells for the
     study uid in status draft. If the study not exist in status draft then return
     the study design-cells for the study in status released. If the study uid only exist as deleted then this is returned.
     - If a specific study status parameter is provided then return study design-cell for this study status.
    - If the locked study status parameter is requested then a study version should
    also be provided, and then the study design-cells for the specific locked study version is returned.
    - Indicate by a boolean variable if the study design-cell can be updated (if the selected study is in status draft).  
    - Indicate by a boolean variable if all expected selections have been made for each study design-cells, or some are missing.


    State after:
    - no change.
     
    Possible errors:
    - Invalid study-uid.
""",
    response_model=list[StudyDesignCell],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_selected_design_cells_connected_branch_arm(
    study_uid: str,
    branch_arm_uid: str,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> list[StudyDesignCell]:
    service = StudyDesignCellService()
    return service.get_all_selection_within_branch_arm(
        study_uid=study_uid,
        study_branch_arm_uid=branch_arm_uid,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{study_uid}/study-design-cells/study-epochs/{study_epoch_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="""List all study design-cells currently selected for study with provided uid that are connected to an StudyEpoch with study_epoch_uid""",
    description="""
    State before:
    - Study must exist.
     
    Business logic:
     - By default (no study status is provided) list all study design-cells for the study uid in status draft. If the study not exist in status draft then return the study design-cells for the study in status released. If the study uid only exist as deleted then this is returned.
     - If a specific study status parameter is provided then return study design-cell for this study status.
    - If the locked study status parameter is requested then a study version should also be provided, and then the study design-cells for the specific locked study version is returned.
    - Indicate by a boolean variable if the study design-cell can be updated (if the selected study is in status draft).  
    - Indicate by a boolean variable if all expected selections have been made for each study design-cells, or some are missing.


    State after:
    - no change.
     
    Possible errors:
    - Invalid study-uid.
""",
    response_model=list[StudyDesignCell],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_selected_design_cells_connected_epoch(
    study_uid: str,
    study_epoch_uid: str,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> list[StudyDesignCell]:
    service = StudyDesignCellService()
    return service.get_all_selection_within_epoch(
        study_uid=study_uid,
        study_epoch_uid=study_epoch_uid,
        study_value_version=study_value_version,
    )
