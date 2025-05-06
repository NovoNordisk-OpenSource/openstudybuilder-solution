from typing import Annotated

from fastapi import Body, Query, Response, status
from pydantic.types import Json

from clinical_mdr_api.models.study_selections.study_selection import (
    StudyActivityInstruction,
    StudyActivityInstructionBatchInput,
    StudyActivityInstructionBatchOutput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.routers.studies import utils
from clinical_mdr_api.services.studies.study_activity_instruction import (
    StudyActivityInstructionService,
)
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse


@router.get(
    "/study-activity-instructions",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all study activity instructions currently selected",
    response_model=CustomPage[StudyActivityInstruction],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_activity_instructions_for_all_studies(
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
) -> CustomPage[StudyActivityInstruction]:
    service = StudyActivityInstructionService()
    all_selections = service.get_all_instructions_for_all_studies(
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
    )
    return CustomPage.create(
        items=all_selections.items,
        total=all_selections.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/studies/{study_uid}/study-activity-instructions",
    dependencies=[rbac.STUDY_READ],
    summary="List all study activity instructions currently defined for the study",
    response_model=list[StudyActivityInstruction],
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
def get_all_selected_instructions(
    study_uid: Annotated[str, utils.studyUID],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> list[StudyActivityInstruction]:
    service = StudyActivityInstructionService()
    return service.get_all_instructions(
        study_uid=study_uid, study_value_version=study_value_version
    )


@router.delete(
    "/studies/{study_uid}/study-activity-instructions/{study_activity_instruction_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study activity instruction",
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity instruction and the study provided.",
        },
    },
)
def delete_activity_instruction(
    study_uid: Annotated[str, utils.studyUID],
    study_activity_instruction_uid: Annotated[
        str, utils.study_activity_instruction_uid
    ],
):
    service = StudyActivityInstructionService()
    service.delete(study_uid=study_uid, instruction_uid=study_activity_instruction_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/studies/{study_uid}/study-activity-instructions/batch",
    dependencies=[rbac.STUDY_WRITE],
    summary="Batch operations (create, delete) for study activity instructions",
    response_model=list[StudyActivityInstructionBatchOutput],
    status_code=207,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def activity_instruction_batch_operations(
    study_uid: Annotated[str, utils.studyUID],
    operations: Annotated[
        list[StudyActivityInstructionBatchInput],
        Body(description="List of operation to perform"),
    ],
) -> list[StudyActivityInstructionBatchOutput]:
    service = StudyActivityInstructionService()
    return service.handle_batch_operations(study_uid, operations)
