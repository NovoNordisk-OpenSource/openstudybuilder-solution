"""Study chart router."""

import io
import os
from typing import Annotated, Any, Literal

from fastapi import Path, Query, Response, status
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
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings

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
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns uid to [row,column] coordinates mapping of items included in SoA Protocol Flowchart table",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_study_flowchart_coordinates(
    study_uid: Annotated[str, STUDY_UID_PATH],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> dict[str, list[int]]:
    coordinates = StudyFlowchartService().get_flowchart_item_uid_coordinates(
        study_uid=study_uid, study_value_version=study_value_version
    )
    return coordinates


@router.get(
    "/{study_uid}/flowchart",
    dependencies=[security, rbac.STUDY_READ],
    summary="Protocol, Detailed or Operational SoA table with footnotes as JSON",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
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
        bool,
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
    dependencies=[security, rbac.STUDY_READ],
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
    include_uids: Annotated[
        bool, Query(description="Include uids in the HTML as data attributes")
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
            include_uids=include_uids,
        )
    )


@router.get(
    "/{study_uid}/flowchart.docx",
    dependencies=[security, rbac.STUDY_READ],
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

    study_id = StudyService().get_study_id(study_uid, study_value_version)
    filename = f"{study_id or study_uid} {layout.value} SoA.docx"
    mime_type = MIME_TYPE_DOCX

    return _streaming_response(stream, filename, mime_type)


@router.get(
    "/{study_uid}/flowchart.xlsx",
    dependencies=[security, rbac.STUDY_READ],
    summary="Builds and returns an XLSX document with Protocol, Detailed or Operational SoA table with footnotes",
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"content": {MIME_TYPE_XLSX: {}}},
        404: _generic_descriptions.ERROR_404,
    },
)
def get_study_flowchart_xlsx(
    study_uid: Annotated[str, STUDY_UID_PATH],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
    time_unit: Annotated[str | None, TIME_UNIT_QUERY] = None,
    layout: Annotated[SoALayout, LAYOUT_QUERY] = SoALayout.PROTOCOL,
) -> StreamingResponse:
    workbook = StudyFlowchartService().get_study_flowchart_xlsx(
        study_uid=study_uid,
        study_value_version=study_value_version,
        layout=layout,
        time_unit=time_unit,
    )

    # render document into Bytes stream
    stream = io.BytesIO()
    workbook.save(stream)

    study_id = StudyService().get_study_id(study_uid, study_value_version)
    filename = f"{study_id or study_uid} {layout.value} SoA.xlsx"
    mime_type = MIME_TYPE_XLSX

    return _streaming_response(stream, filename, mime_type)


@router.get(
    "/{study_uid}/operational-soa.xlsx",
    dependencies=[security, rbac.STUDY_READ],
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

    study_id = StudyService().get_study_id(study_uid, study_value_version)
    filename = f"{study_id or study_uid} {layout.value} SoA.xlsx"
    mime_type = MIME_TYPE_XLSX

    return _streaming_response(stream, filename, mime_type)


@router.get(
    "/{study_uid}/operational-soa.html",
    dependencies=[security, rbac.STUDY_READ],
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
    "/{study_uid}/detailed-soa.xlsx",
    dependencies=[security, rbac.STUDY_READ],
    summary="Builds and returns an XLSX document with Detailed SoA",
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"content": {MIME_TYPE_XLSX: {}}},
        404: _generic_descriptions.ERROR_404,
    },
)
def get_detailed_soa_xlsx(
    study_uid: Annotated[str, STUDY_UID_PATH],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
    time_unit: Annotated[str | None, TIME_UNIT_QUERY] = None,
) -> StreamingResponse:
    layout = SoALayout.DETAILED
    xlsx = StudyFlowchartService().get_detailed_soa_xlsx(
        study_uid=study_uid,
        time_unit=time_unit,
        study_value_version=study_value_version,
    )

    # render document into Bytes stream
    stream = io.BytesIO()
    xlsx.save(stream)

    study_id = StudyService().get_study_id(study_uid, study_value_version)
    filename = f"{study_id or study_uid} {layout.value} SoA.xlsx"
    mime_type = MIME_TYPE_XLSX

    return _streaming_response(stream, filename, mime_type)


@router.get(
    "/{study_uid}/detailed-soa.html",
    dependencies=[security, rbac.STUDY_READ],
    summary="Builds and returns an HTML document with Detailed SoA",
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"content": {"text/html": {}}},
        404: _generic_descriptions.ERROR_404,
    },
)
def get_detailed_soa_html(
    study_uid: Annotated[str, STUDY_UID_PATH],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
    time_unit: Annotated[str | None, TIME_UNIT_QUERY] = None,
) -> HTMLResponse:
    return HTMLResponse(
        StudyFlowchartService().get_detailed_soa_html(
            study_uid=study_uid,
            time_unit=time_unit,
            study_value_version=study_value_version,
        )
    )


@router.get(
    "/{study_uid}/detailed-soa-history",
    dependencies=[security, rbac.STUDY_READ],
    summary="Returns the history of changes performed to a specific detailed SoA",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_detailed_soa_history(
    study_uid: Annotated[str, STUDY_UID_PATH],
    page_number: _generic_descriptions.PAGE_NUMBER_QUERY = settings.default_page_number,
    page_size: _generic_descriptions.PAGE_SIZE_QUERY = settings.default_page_size,
    total_count: _generic_descriptions.TOTAL_COUNT_QUERY = False,
) -> CustomPage[DetailedSoAHistory]:
    detailed_soa_history = StudyActivitySelectionService().get_detailed_soa_history(
        study_uid=study_uid,
        page_size=page_size,
        page_number=page_number,
        total_count=total_count,
    )
    return CustomPage(
        items=detailed_soa_history.items,
        total=detailed_soa_history.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/{study_uid}/detailed-soa-exports",
    dependencies=[security, rbac.STUDY_READ],
    summary="Exports the Detailed SoA content",
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
) -> list[dict[str, Any]]:
    soa_content = StudyFlowchartService().download_detailed_soa_content(
        study_uid=study_uid,
        study_value_version=study_value_version,
    )
    return soa_content


@router.get(
    "/{study_uid}/operational-soa-exports",
    dependencies=[security, rbac.STUDY_READ],
    summary="Exports the Operational SoA content",
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
            "library",
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
            "Library=library",
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
) -> list[dict[str, Any]]:
    soa_content = StudyFlowchartService().download_operational_soa_content(
        study_uid=study_uid,
        study_value_version=study_value_version,
    )
    return soa_content


@router.get(
    "/{study_uid}/protocol-soa-exports",
    dependencies=[security, rbac.STUDY_READ],
    summary="Exports the Protocol SoA content",
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
    protocol_lab_table: Annotated[
        bool,
        Query(description="Whether to export Protocol Lab table SoA"),
    ] = False,
) -> list[dict[str, Any]]:
    soa_content = StudyFlowchartService().download_detailed_soa_content(
        study_uid=study_uid,
        study_value_version=study_value_version,
        protocol_flowchart=not protocol_lab_table,
        protocol_lab_table=protocol_lab_table,
    )
    return soa_content


@router.get(
    "/{study_uid}/flowchart/snapshot",
    dependencies=[security, rbac.ADMIN_READ],
    summary="Retrieve the saved SoA snapshot for a study version. If no SoA snapshot saved, returns 404.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: _generic_descriptions.ERROR_404,
    },
    response_model=TableWithFootnotes,
    response_model_exclude_none=True,
    tags=["Data Migration"],
)
def get_soa_snapshot(
    study_uid: Annotated[str, STUDY_UID_PATH],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
    layout: Annotated[Literal["protocol"], LAYOUT_QUERY] = "protocol",
) -> TableWithFootnotes:
    return StudyFlowchartService().load_soa_snapshot(
        study_uid=study_uid,
        study_value_version=study_value_version,
        layout=SoALayout(layout),
    )


@router.post(
    "/{study_uid}/flowchart/snapshot",
    dependencies=[security, rbac.ADMIN_WRITE],
    summary="Update SoA snapshot for a study version based on the recent SoA rules (intended for data migration only)",
    responses={
        status.HTTP_201_CREATED: {"model": None, "description": "SoA snapshot updated"},
        status.HTTP_404_NOT_FOUND: _generic_descriptions.ERROR_404,
    },
    response_model=None,
    tags=["Data Migration"],
)
def update_soa_snapshot(
    study_uid: Annotated[str, STUDY_UID_PATH],
    study_value_version: Annotated[
        str, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ],
    layout: Annotated[Literal["protocol"], LAYOUT_QUERY] = "protocol",
) -> Response:
    StudyFlowchartService().update_soa_snapshot(
        study_uid=study_uid,
        study_value_version=study_value_version,
        layout=SoALayout(layout),
    )
    return Response(content=None, status_code=status.HTTP_201_CREATED)


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
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'",
        },
    )

    return response
