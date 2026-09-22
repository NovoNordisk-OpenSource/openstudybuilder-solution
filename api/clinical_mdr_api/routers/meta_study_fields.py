"""MetaStudyFields router."""

from fastapi import APIRouter

from clinical_mdr_api.models.meta_study_field import MetaStudyField
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.meta_study_field import MetaStudyFieldService
from common.auth import rbac
from common.auth.dependencies import security

router = APIRouter()


@router.get(
    "/meta-study-fields",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns all predefined MetaStudyField nodes.",
    description=(
        "Returns every `MetaStudyField` node currently present in the graph "
        "with its `osb_field_name` and `osb_page_reference` properties. "
        "Useful for clients that need to enumerate the set of Trial Summary "
        "parameter slots without going through individual CT terms."
    ),
    status_code=200,
    response_model_exclude_unset=True,
    responses={
        403: _generic_descriptions.ERROR_403,
    },
)
def get_meta_study_fields() -> list[MetaStudyField]:
    return MetaStudyFieldService.get_all()
