# pylint: disable=invalid-name
from typing import Annotated

from fastapi import APIRouter, Body, Path

from clinical_mdr_api.models.feature_flag import (
    FeatureFlag,
    FeatureFlagInput,
    FeatureFlagPatchInput,
)
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.feature_flags import FeatureFlagService
from common.auth import rbac

# Prefixed with "/feature-flags"
router = APIRouter()

SN = Path(title="Serial Number of the feature flag")

service = FeatureFlagService()


@router.get(
    "/{serial_number}",
    dependencies=[rbac.ADMIN_READ],
    summary="Returns the feature flag identified by the provided Serial Number.",
    response_model=FeatureFlag,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.validate_serial_number_against_neo4j_max_and_min_int()
def get_feature_flag(serial_number: Annotated[int, SN]) -> FeatureFlag:
    return service.get_feature_flag(serial_number)


@router.post(
    "",
    dependencies=[rbac.ADMIN_WRITE],
    summary="Creates a feature flag.",
    response_model=FeatureFlag,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
        409: _generic_descriptions.ERROR_409,
    },
)
def create_feature_flag(
    feature_flag_input: Annotated[FeatureFlagInput, Body()],
) -> FeatureFlag:
    return service.create_feature_flag(feature_flag_input)


@router.patch(
    "/{serial_number}",
    dependencies=[rbac.ADMIN_WRITE],
    summary="Updates the feature flag identified by the provided Serial Number.",
    response_model=FeatureFlag,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
        409: _generic_descriptions.ERROR_409,
    },
)
@decorators.validate_serial_number_against_neo4j_max_and_min_int()
def update_feature_flag(
    serial_number: Annotated[int, SN],
    feature_flag_patch_input: Annotated[FeatureFlagPatchInput, Body()],
) -> FeatureFlag:
    return service.update_feature_flag(serial_number, feature_flag_patch_input)


@router.delete(
    "/{serial_number}",
    dependencies=[rbac.ADMIN_WRITE],
    summary="Deletes the feature flag identified by the provided Serial Number.",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.validate_serial_number_against_neo4j_max_and_min_int()
def delete_feature_flag(serial_number: Annotated[int, SN]) -> None:
    return service.delete_feature_flag(serial_number)
