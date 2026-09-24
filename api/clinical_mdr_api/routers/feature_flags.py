"""Feature flag API routes."""

# pylint: disable=invalid-name
from typing import Annotated

from fastapi import APIRouter, Body, Path, Query

from clinical_mdr_api.models.feature_flag import (
    FeatureFlag,
    FeatureFlagInput,
    FeatureFlagPatchInput,
    FeatureFlagVersion,
)
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.feature_flags import FeatureFlagService
from common.auth import rbac
from common.auth.dependencies import security

# Prefixed with "/feature-flags"
router = APIRouter()

UID = Path(title="Unique id of the feature flag")

service = FeatureFlagService()


@router.get(
    "",
    dependencies=[security, rbac.FEATURE_FLAG_READ],
    summary="Returns feature flags. By default only Final flags.",
    description=(
        "Requires Admin.Read, Library.Read, or Study.Read. "
        "Used for client feature gating and admin listing. "
        "Pass include_retired=true to also return Retired flags; "
        "include_deprecated=true remains supported as a compatibility alias. "
        "when false (default), only Final flags are returned."
    ),
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_feature_flags(
    include_retired: Annotated[
        bool,
        Query(
            description="When false (default), only Final flags are returned. "
            "When true, Retired flags are included as well.",
        ),
    ] = False,
    include_deprecated: Annotated[
        bool | None,
        Query(
            alias="include_deprecated",
            include_in_schema=False,
            description="Compatibility alias for include_retired.",
        ),
    ] = None,
) -> list[FeatureFlag]:
    """Return current feature flags, optionally including retired ones."""
    return service.get_all_feature_flags(
        include_retired=include_retired or bool(include_deprecated)
    )


@router.get(
    "/{uid}",
    dependencies=[security, rbac.ADMIN_READ],
    summary="Returns the feature flag identified by the provided uid.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_feature_flag(uid: Annotated[str, UID]) -> FeatureFlag:
    """Return the current feature flag for the provided uid."""
    return service.get_feature_flag(uid)


@router.get(
    "/{uid}/versions",
    dependencies=[security, rbac.ADMIN_READ],
    summary="Returns the version history of the feature flag identified by the provided uid.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_feature_flag_versions(uid: Annotated[str, UID]) -> list[FeatureFlagVersion]:
    """Return the version history for the provided feature flag uid."""
    return service.get_version_history(uid)


@router.post(
    "",
    dependencies=[security, rbac.ADMIN_WRITE],
    summary="Creates a feature flag as Final version 1.0.",
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
    """Create a new feature flag."""
    return service.create_feature_flag(feature_flag_input)


@router.patch(
    "/{uid}",
    dependencies=[security, rbac.ADMIN_WRITE],
    summary="Updates the feature flag by creating a new Final version.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
        409: _generic_descriptions.ERROR_409,
    },
)
def update_feature_flag(
    uid: Annotated[str, UID],
    feature_flag_patch_input: Annotated[FeatureFlagPatchInput, Body()],
) -> FeatureFlag:
    """Update a feature flag by creating a new Final version."""
    return service.update_feature_flag(uid, feature_flag_patch_input)


@router.delete(
    "/{uid}/activations",
    dependencies=[security, rbac.ADMIN_WRITE],
    summary="Inactivates/deprecates the feature flag (Final → Retired).",
    description="""Only valid when the feature flag is in Final status.
If the request succeeds, status is set to Retired and version is unchanged.""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
        400: _generic_descriptions.ERROR_400,
    },
)
def inactivate_feature_flag(uid: Annotated[str, UID]) -> FeatureFlag:
    """Inactivate a Final feature flag without changing its enabled value."""
    return service.inactivate_final(uid)


@router.post(
    "/{uid}/activations",
    dependencies=[security, rbac.ADMIN_WRITE],
    summary="Reactivates a retired feature flag (Retired → Final).",
    description="""Only valid when the feature flag is in Retired status.
If the request succeeds, status is set to Final and version is unchanged.""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
        400: _generic_descriptions.ERROR_400,
    },
)
def reactivate_feature_flag(uid: Annotated[str, UID]) -> FeatureFlag:
    """Reactivate a Retired feature flag without changing its enabled value."""
    return service.reactivate_retired(uid)
