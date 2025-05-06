"""Study disclosure router"""

from typing import Annotated

from fastapi import Path
from fastapi.responses import Response

from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.routers.studies.study import router
from clinical_mdr_api.services.ctr_xml.ctr_xml_service import CTRXMLService
from common.auth import rbac

StudyUID = Path(description="The unique id of the study.")


class XMLResponse(Response):
    media_type = "text/xml"


@router.get(
    "/studies/{study_uid}/ctr/odm.xml",
    dependencies=[rbac.STUDY_READ],
    summary="Returns study disclosure document in CTR ODM XML format",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"content": {"text/xml": {"schema": {"type": "string"}}}},
        404: _generic_descriptions.ERROR_404,
    },
)
def get_odm_xml(
    study_uid: Annotated[str, StudyUID],
) -> XMLResponse:
    return XMLResponse(content=CTRXMLService().get_ctr_odm(study_uid))
