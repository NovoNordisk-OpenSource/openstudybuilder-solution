"""Study Protocol Interventions router"""

import os
from typing import Annotated

from fastapi import Path
from fastapi.responses import HTMLResponse, StreamingResponse

from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.routers import studies_router as router
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_interventions import (
    StudyInterventionsService,
)
from clinical_mdr_api.services.utils.table_f import TableWithFootnotes
from common.auth import rbac

StudyUID = Path(description="The unique id of the study.")


@router.get(
    "/{study_uid}/interventions",
    dependencies=[rbac.STUDY_READ],
    summary="Returns Study Protocol Interventions table",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
    response_model=TableWithFootnotes,
)
def get_study_interventions(
    study_uid: Annotated[str, StudyUID],
) -> TableWithFootnotes:
    StudyService().check_if_study_exists(study_uid)
    return StudyInterventionsService().get_table(study_uid)


@router.get(
    "/{study_uid}/interventions.html",
    dependencies=[rbac.STUDY_READ],
    summary="Builds and returns an HTML document of Study Protocol Interventions table",
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"content": {"text/html": {"schema": {"type": "string"}}}},
        404: _generic_descriptions.ERROR_404,
    },
)
def get_study_interventions_html(
    study_uid: Annotated[str, StudyUID],
) -> HTMLResponse:
    StudyService().check_if_study_exists(study_uid)
    return HTMLResponse(StudyInterventionsService().get_html(study_uid))


@router.get(
    "/{study_uid}/interventions.docx",
    dependencies=[rbac.STUDY_READ],
    summary="Builds and returns a DOCX document of Study Protocol Interventions table",
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {}
            }
        },
        404: _generic_descriptions.ERROR_404,
    },
)
def get_study_interventions_docx(
    study_uid: Annotated[str, StudyUID],
) -> StreamingResponse:
    StudyService().check_if_study_exists(study_uid)
    docx = StudyInterventionsService().get_docx(study_uid)
    stream = docx.get_document_stream()
    size = stream.seek(0, os.SEEK_END)
    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{study_uid} interventions.docx"',
            "Content-Length": f"{size:d}",
        },
    )
