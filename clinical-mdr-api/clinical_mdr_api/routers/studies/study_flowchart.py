"""Study chart router."""

import io
import os
from typing import Annotated

from fastapi import Path, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from starlette.requests import Request

from clinical_mdr_api.domain_repositories.study_selections.study_soa_repository import (
    SoALayout,
)
from clinical_mdr_api.models.study_selections.study_selection import DetailedSoAHistory
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers import studies_router as router
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.studies.study_flowchart import StudyFlowchartService
from clinical_mdr_api.services.utils.table_f import TableWithFootnotes
from common import config
from common.auth import rbac

LAYOUT_QUERY = Query(
    description="The requested layout or detail level of Schedule of Activities"
)

MIME_TYPE_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

MIME_TYPE_DOCX = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

STUDY_UID_PATH = Path(description="The unique id of the study.")

TIME_UNIT_QUERY = Query(
    pattern="^(week|day)$", description="The preferred time unit, either day or week."
)


@router.get(
    "/{study_uid}/flowchart/coordinates",
    dependencies=[rbac.STUDY_READ],
    summary="Returns uid to [row,column] coordinates mapping of items included in SoA Protocol Flowchart table",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
    response_model=dict[str, tuple[int, int]],
)
def get_study_flowchart_coordinates(
    study_uid: Annotated[str, STUDY_UID_PATH],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> dict[str, tuple[int, int]]:
    coordinates = StudyFlowchartService().get_flowchart_item_uid_coordinates(
        study_uid=study_uid, study_value_version=study_value_version
    )
    return coordinates


@router.get(
    "/{study_uid}/flowchart",
    dependencies=[rbac.STUDY_READ],
    summary="Protocol, Detailed or Operational SoA table with footnotes as JSON",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
    response_model=TableWithFootnotes,
    response_model_exclude_none=True,
)
def get_study_flowchart(
    study_uid: Annotated[str, STUDY_UID_PATH],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
    time_unit: Annotated[str | None, TIME_UNIT_QUERY] = None,
    layout: Annotated[SoALayout, LAYOUT_QUERY] = SoALayout.PROTOCOL,
    force_build: Annotated[
        bool | None,
        Query(description="Force building of SoA without using any saved snapshot"),
    ] = False,
) -> TableWithFootnotes:
    table = StudyFlowchartService().get_flowchart_table(
        study_uid=study_uid,
        time_unit=time_unit,
        study_value_version=study_value_version,
        layout=layout,
        force_build=force_build,
    )

    return table


@router.get(
    "/{study_uid}/flowchart.html",
    dependencies=[rbac.STUDY_READ],
    summary="Builds and returns an HTML document with Protocol, Detailed or Operational SoA table with footnotes",
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"content": {"text/html": {"schema": {"type": "string"}}}},
        404: _generic_descriptions.ERROR_404,
    },
)
def get_study_flowchart_html(
    study_uid: Annotated[str, STUDY_UID_PATH],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
    time_unit: Annotated[str | None, TIME_UNIT_QUERY] = None,
    layout: Annotated[SoALayout, LAYOUT_QUERY] = SoALayout.PROTOCOL,
    debug_uids: Annotated[
        bool, Query(description="Show uids on column superscript")
    ] = False,
    debug_coordinates: Annotated[
        bool, Query(description="Debug coordinates as superscripts")
    ] = False,
    debug_propagation: Annotated[
        bool, Query(description="Debug propagations without hiding rows")
    ] = False,
) -> HTMLResponse:
    return HTMLResponse(
        StudyFlowchartService().get_study_flowchart_html(
            study_uid=study_uid,
            time_unit=time_unit,
            study_value_version=study_value_version,
            layout=layout,
            debug_uids=debug_uids,
            debug_coordinates=debug_coordinates,
            debug_propagation=debug_propagation,
        )
    )


@router.get(
    "/{study_uid}/flowchart.docx",
    dependencies=[rbac.STUDY_READ],
    summary="Builds and returns an DOCX document with Protocol, Detailed or Operational SoA table with footnotes",
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"content": {MIME_TYPE_DOCX: {}}},
        404: _generic_descriptions.ERROR_404,
    },
)
def get_study_flowchart_docx(
    study_uid: Annotated[str, STUDY_UID_PATH],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
    time_unit: Annotated[str | None, TIME_UNIT_QUERY] = None,
    layout: Annotated[SoALayout, LAYOUT_QUERY] = SoALayout.PROTOCOL,
) -> StreamingResponse:
    stream = (
        StudyFlowchartService()
        .get_study_flowchart_docx(
            study_uid=study_uid,
            study_value_version=study_value_version,
            layout=layout,
            time_unit=time_unit,
        )
        .get_document_stream()
    )

    study_id = _get_study_id(study_uid, study_value_version)
    filename = f"{study_id or study_uid} {layout.value} SoA.docx"
    mime_type = MIME_TYPE_DOCX

    return _streaming_response(stream, filename, mime_type)


@router.get(
    "/{study_uid}/operational-soa.xlsx",
    dependencies=[rbac.STUDY_READ],
    summary="Builds and returns an XLSX document with Operational SoA",
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"content": {MIME_TYPE_XLSX: {}}},
        404: _generic_descriptions.ERROR_404,
    },
)
def get_operational_soa_xlsx(
    study_uid: Annotated[str, STUDY_UID_PATH],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
    time_unit: Annotated[str | None, TIME_UNIT_QUERY] = None,
) -> StreamingResponse:
    layout = SoALayout.OPERATIONAL
    xlsx = StudyFlowchartService().get_operational_soa_xlsx(
        study_uid=study_uid,
        time_unit=time_unit,
        study_value_version=study_value_version,
    )

    # render document into Bytes stream
    stream = io.BytesIO()
    xlsx.save(stream)

    study_id = _get_study_id(study_uid, study_value_version)
    filename = f"{study_id or study_uid} {layout.value} SoA.xlsx"
    mime_type = MIME_TYPE_XLSX

    return _streaming_response(stream, filename, mime_type)


@router.get(
    "/{study_uid}/operational-soa.html",
    dependencies=[rbac.STUDY_READ],
    summary="Builds and returns an HTML document with Operational SoA",
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"content": {"text/html": {}}},
        404: _generic_descriptions.ERROR_404,
    },
)
def get_operational_soa_html(
    study_uid: Annotated[str, STUDY_UID_PATH],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
    time_unit: Annotated[str | None, TIME_UNIT_QUERY] = None,
) -> HTMLResponse:
    return HTMLResponse(
        StudyFlowchartService().get_operational_soa_html(
            study_uid=study_uid,
            time_unit=time_unit,
            study_value_version=study_value_version,
        )
    )


@router.get(
    "/{study_uid}/detailed-soa-history",
    dependencies=[rbac.STUDY_READ],
    summary="Returns the history of changes performed to a specific detailed SoA",
    response_model=CustomPage[DetailedSoAHistory],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_detailed_soa_history(
    study_uid: Annotated[str, STUDY_UID_PATH],
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
    total_count: Annotated[
        bool | None, Query(description=_generic_descriptions.TOTAL_COUNT)
    ] = False,
) -> CustomPage[DetailedSoAHistory]:
    detailed_soa_history = StudyActivitySelectionService().get_detailed_soa_history(
        study_uid=study_uid,
        page_size=page_size,
        page_number=page_number,
        total_count=total_count,
    )
    return CustomPage.create(
        items=detailed_soa_history.items,
        total=detailed_soa_history.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/{study_uid}/detailed-soa-exports",
    dependencies=[rbac.STUDY_READ],
    summary="Exports the Detailed SoA content",
    response_model=list[dict],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "study_number",
            "study_version",
            "soa_group",
            "activity_group",
            "activity_subgroup",
            "visit",
            "activity",
            "is_data_collected",
        ],
        "include_if_exists": [
            "epoch",
            "milestone",
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
def export_detailed_soa_content(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: Annotated[str, STUDY_UID_PATH],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> list[dict]:
    soa_content = StudyFlowchartService().download_detailed_soa_content(
        study_uid=study_uid,
        study_value_version=study_value_version,
    )
    return soa_content


@router.get(
    "/{study_uid}/operational-soa-exports",
    dependencies=[rbac.STUDY_READ],
    summary="Exports the Operational SoA content",
    response_model=list[dict],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "study_number",
            "study_version",
            "soa_group",
            "activity_group",
            "activity_subgroup",
            "epoch",
            "visit",
            "activity",
            "activity_instance",
            "topic_code",
            "param_code",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
            "Study number=study_number",
            "Study version=study_version",
            "SoA group=soa_group",
            "Activity group=activity_group",
            "Activity subgroup=activity_subgroup",
            "Epoch=epoch",
            "Visit=visit",
            "Activity=activity",
            "Activity instance=activity_instance",
            "Topic code=topic_code",
            "Param code=param_code",
        ],
    }
)
# pylint: disable=unused-argument
def export_operational_soa_content(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: Annotated[str, STUDY_UID_PATH],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> list[dict]:
    soa_content = StudyFlowchartService().download_operational_soa_content(
        study_uid=study_uid,
        study_value_version=study_value_version,
    )
    return soa_content


@router.get(
    "/{study_uid}/protocol-soa-exports",
    dependencies=[rbac.STUDY_READ],
    summary="Exports the Protocol SoA content",
    response_model=list[dict],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "study_number",
            "study_version",
            "soa_group",
            "activity_group",
            "activity_subgroup",
            "visit",
            "activity",
        ],
        "include_if_exists": [
            "epoch",
            "milestone",
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
def export_protocol_soa_content(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: Annotated[str, STUDY_UID_PATH],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> list[dict]:
    soa_content = StudyFlowchartService().download_detailed_soa_content(
        study_uid=study_uid,
        study_value_version=study_value_version,
        protocol_flowchart=True,
    )
    return soa_content


def _get_study_id(study_uid, study_value_version):
    """gets study_id of study"""

    study = StudyService().get_by_uid(
        study_uid, study_value_version=study_value_version
    )

    return study.current_metadata.identification_metadata.study_id


def _streaming_response(
    stream: io.BytesIO, filename: str, mime_type: str
) -> StreamingResponse:
    """Returns StreamingResponse from a stream, with filename, size, and mime-type HTTP headers."""

    # determine the size of the binary data
    filesize = stream.seek(0, os.SEEK_END)
    stream.seek(0)

    # response with document info HTTP headers
    response = StreamingResponse(
        stream,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": f"{filesize:d}",
        },
    )

    return response
