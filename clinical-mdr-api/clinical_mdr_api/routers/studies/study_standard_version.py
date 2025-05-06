from typing import Annotated, Sequence

from fastapi import Body, Path, Request, Response, status

from clinical_mdr_api.models.study_selections import study_standard_version
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.services.studies.study_standard_version_selection import (
    StudyStandardVersionService,
)
from common.auth import rbac
from common.models.error import ErrorResponse

studyUID = Path(description="The unique id of the study.")

study_standard_version_uid_description = Path(
    description="The unique id of the study standard_version."
)


"""
    API endpoints to study standard versions
"""


@router.get(
    "/studies/{study_uid}/study-standard-versions",
    dependencies=[rbac.STUDY_READ],
    summary="List all study standard_versions currently selected for the study.",
    description="""
State before:
 - Study must exist.
 
Business logic:
 - By default (no study status is provided) list all study standard_versions for the study uid in status draft. If the study not exist in status draft then return the study standard_versions for the study in status released. If the study uid only exist as deleted then this is returned.
 - If a specific study status parameter is provided then return study standard_version for this study status.
 - If the locked study status parameter is requested then a study version should also be provided, and then the study standard_versions for the specific locked study version is returned.
 - Indicate by an boolean variable if the study standard_version can be updated (if the selected study is in status draft).  
 - Indicate by an boolean variable if all expected selections have been made for each study standard_versions, or some are missing.
   - e.g. duration time unit must is expected.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.

""",
    response_model=Sequence[study_standard_version.StudyStandardVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "ct_package",
            "study_uid",
            "study_version",
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
def get_all(
    request: Request,  # request is actually required by the allow_exports decorator
    study_uid: Annotated[str, studyUID],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> Sequence[study_standard_version.StudyStandardVersion]:
    service = StudyStandardVersionService()
    return service.get_standard_versions_in_study(
        study_uid=study_uid, study_value_version=study_value_version
    )


@router.get(
    "/studies/{study_uid}/study-standard-versions/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to all study standard_versions within the specified study-uid",
    description="""
State before:
 - Study and study standard_version must exist.

Business logic:
 - List all study standard_version audit trail within the specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.
     """,
    response_model=list[study_standard_version.StudyStandardVersionVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the provided study.",
        },
    },
)
def get_study_standard_versions_all_audit_trail(
    study_uid: Annotated[str, studyUID],
) -> list[study_standard_version.StudyStandardVersionVersion]:
    service = StudyStandardVersionService()
    return service.audit_trail_all_standard_versions(study_uid)


@router.get(
    "/studies/{study_uid}/study-standard-versions/{study_standard_version_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="List all definitions for a specific study standard_version",
    description="""
State before:
 - Study and study standard_version must exist
 
Business logic:
 - By default (no study status is provided) list all details for specified study standard_version for the study uid in status draft. If the study not exist in status draft then return the study standard_versions for the study in status released. If the study uid only exist as deleted then this is returned.
 - If a specific study status parameter is provided then return study standard_versions for this study status.
 - If the locked study status parameter is requested then a study version should also be provided, and then the specified study standard_version  for the specific locked study version is returned.
 - Indicate by an boolean variable if the study standard_version can be updated (if the selected study is in status draft).
 - Indicate by an boolean variable if all expected selections have been made for each study standard_version , or some are missing.
 - e.g. standard_version level, minimum one timeframe and one unit is expected.
 - Indicate by an boolean variable if the selected standard_version is available in a newer version.
 
State after:
 - no change
 
Possible errors:
 - Invalid study-uid or study_standard_version Uid.
    """,
    response_model=study_standard_version.StudyStandardVersion,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no standard_version for the study provided.",
        },
    },
)
# pylint: disable=unused-argument
def get_study_standard_version(
    study_uid: Annotated[str, studyUID],
    study_standard_version_uid: Annotated[str, study_standard_version_uid_description],
    study_value_version: Annotated[
        str | None, _generic_descriptions.STUDY_VALUE_VERSION_QUERY
    ] = None,
) -> study_standard_version.StudyStandardVersion:
    service = StudyStandardVersionService()
    return service.find_by_uid(
        study_uid=study_uid,
        study_standard_version_uid=study_standard_version_uid,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{study_uid}/study-standard-versions/{study_standard_version_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study standard_version",
    description="""
State before:
 - Study and study standard_versions must exist.

Business logic:
 - List a specific entry in the audit trail related to the specified study standard_version for the specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.
     """,
    response_model=list[study_standard_version.StudyStandardVersionVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the standard version provided for the study provided.",
        },
    },
)
def get_study_standard_version_audit_trail(
    study_uid: Annotated[str, studyUID],
    study_standard_version_uid: Annotated[str, study_standard_version_uid_description],
) -> list[study_standard_version.StudyStandardVersionVersion]:
    service = StudyStandardVersionService()
    return service.audit_trail(
        study_uid=study_uid, study_standard_version_uid=study_standard_version_uid
    )


@router.post(
    "/studies/{study_uid}/study-standard-versions",
    dependencies=[rbac.STUDY_WRITE],
    summary="Add a study standard version to a study",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - Study must not have assigned a Study Standard Version previously

Business logic:
 - Add a study standard_version to a study based on selection of an CTPackage.

State after:
 - StandardVersion Selection is added to the study.
 - Added new entry in the audit trail for the creation of the study-standard_version.
 
Possible errors:
 - Invalid study-uid or CTPackage
 - The study contains already a Selected Study Standard Version
    """,
    response_model=study_standard_version.StudyStandardVersion,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the study_standard_version",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study is not found with the passed 'study_uid'.",
        },
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
def post_new_standard_version_create(
    study_uid: Annotated[str, studyUID],
    selection: Annotated[
        study_standard_version.StudyStandardVersionInput,
        Body(description="Related parameters of the selection that shall be created."),
    ],
) -> study_standard_version.StudyStandardVersion:
    service = StudyStandardVersionService()
    return service.create(study_uid=study_uid, study_standard_version_input=selection)


@router.delete(
    "/studies/{study_uid}/study-standard-versions/{study_standard_version_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study standard_version.",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - study-standard_version-uid must exist. 

Business logic:
 - Remove specified study-standard_version from the study.
 - Reference to the study-standard_version should still exist in the audit trail.
- Update the order value of all other standard_versions for this study to be consecutive.

State after:
- Study standard_versions deleted from the study, but still exist as a node in the database with a reference from the audit trail.
- Added new entry in the audit trail for the deletion of the study-standard_version.
 
Possible errors:
- Invalid study-uid or study_standard_version_uid.
    """,
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - the study or standard_version doesn't exist.",
        },
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
# pylint: disable=unused-argument
def delete_study_standard_version(
    study_uid: Annotated[str, studyUID],
    study_standard_version_uid: Annotated[str, study_standard_version_uid_description],
):
    service = StudyStandardVersionService()

    service.delete(
        study_uid=study_uid, study_standard_version_uid=study_standard_version_uid
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/studies/{study_uid}/study-standard-versions/{study_standard_version_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit a study standard_version",
    description="""
State before:
 - Study must exist and study status must be in draft.

Business logic:
 - Same logic applies as for selecting or creating an study standard_version (see two POST statements for /study-standard-versions)
 - Update the order value of all other standard_versions for this study to be consecutive.

State after:
 - StandardVersionType is added as study standard_version to the study.
 - This PATCH method can cover cover two parts:

 - Added new entry in the audit trail for the update of the study-standard_version.

Possible errors:
 - Invalid study-uid or study_standard_version_uid .
    """,
    response_model=study_standard_version.StudyStandardVersion,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no study or standard_version .",
        },
    },
)
@decorators.validate_if_study_is_not_locked("study_uid")
# pylint: disable=unused-argument
def patch_update_standard_version(
    study_uid: Annotated[str, studyUID],
    study_standard_version_uid: Annotated[str, study_standard_version_uid_description],
    selection: Annotated[
        study_standard_version.StudyStandardVersionEditInput,
        Body(description="Related parameters of the selection that shall be created."),
    ],
) -> study_standard_version.StudyStandardVersion:
    service = StudyStandardVersionService()
    return service.edit(
        study_uid=study_uid,
        study_standard_version_uid=study_standard_version_uid,
        study_standard_version_input=selection,
    )
