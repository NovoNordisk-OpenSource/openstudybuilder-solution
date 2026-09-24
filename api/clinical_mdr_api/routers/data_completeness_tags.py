# pylint: disable=invalid-name
from typing import Annotated

from fastapi import APIRouter, Body, Path

from clinical_mdr_api.models.data_completeness_tag import (
    DataCompletenessTag,
    DataCompletenessTagInput,
)
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.data_completeness_tags import DataCompletenessTagService
from common.auth import rbac
from common.auth.dependencies import security

# Prefixed with "/data-completeness-tags"
router = APIRouter()

UID = Path(title="UID of the data completeness tag")

service = DataCompletenessTagService()


@router.get(
    "",
    dependencies=[security, rbac.ADMIN_READ],
    summary="Returns all data completeness tags.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_data_completeness_tags() -> list[DataCompletenessTag]:
    return service.get_all_data_completeness_tags()


@router.post(
    "",
    dependencies=[security, rbac.ADMIN_WRITE],
    summary="Creates a data completeness tag.",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
        409: _generic_descriptions.ERROR_409,
    },
)
def create_data_completeness_tag(
    data_completeness_tag_input: Annotated[DataCompletenessTagInput, Body()],
) -> DataCompletenessTag:
    return service.create_data_completeness_tag(data_completeness_tag_input)


@router.put(
    "/{uid}",
    dependencies=[security, rbac.ADMIN_WRITE],
    summary="Updates the data completeness tag identified by the provided UID.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
        409: _generic_descriptions.ERROR_409,
    },
)
def update_data_completeness_tag(
    uid: Annotated[str, UID],
    data_completeness_tag_input: Annotated[DataCompletenessTagInput, Body()],
) -> DataCompletenessTag:
    return service.update_data_completeness_tag(uid, data_completeness_tag_input)


@router.delete(
    "/{uid}",
    dependencies=[security, rbac.ADMIN_WRITE],
    summary="Deletes the data completeness tag identified by the provided UID.",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def delete_data_completeness_tag(uid: Annotated[str, UID]) -> None:
    return service.delete_data_completeness_tag(uid)
