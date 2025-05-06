"""Study chart router."""

from typing import Annotated

from fastapi import Path, Query
from fastapi.responses import Response

from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.routers import studies_router as router
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_design_figure import (
    StudyDesignFigureService,
)
from common.auth import rbac

StudyUID = Path(description="The unique id of the study.")

time_unit = Query(
    pattern="^(weeks|days)$",
    description="The preferred time unit, either days or weeks.",
)


class SVGResponse(Response):
    media_type = "image/svg+xml"


@router.get(
    "/{study_uid}/design.svg",
    dependencies=[rbac.STUDY_READ],
    summary="Builds and returns a Study Design visualization image in SVG format",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"content": {"image/svg+xml": {"schema": {"type": "string"}}}},
        404: _generic_descriptions.ERROR_404,
    },
)
def get_study_flowchart_html(
    response: Response,
    study_uid: Annotated[str, StudyUID],
    debug: Annotated[
        bool | None, Query(description="Draw some lines for debugging the image layout")
    ] = False,
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> SVGResponse:
    StudyService().check_if_study_exists(study_uid)
    response.headers["Content-Disposition"] = (
        f'inline; filename="{study_uid} design.svg"'
    )
    return SVGResponse(
        StudyDesignFigureService(debug=debug).get_svg_document(
            study_uid, study_value_version=study_value_version
        )
    )
