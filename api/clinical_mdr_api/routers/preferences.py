from fastapi import APIRouter

from clinical_mdr_api.models.preferences import (
    UserPreferencesPatchInput,
    UserPreferencesResponse,
)
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.preferences import PreferencesService
from common.auth.dependencies import security
from common.auth.user import user

# Prefixed with "/user-preferences"
router = APIRouter()


@router.get(
    "",
    dependencies=[security],
    summary="Returns user preferences",
    status_code=200,
    responses={
        401: _generic_descriptions.ERROR_401,
    },
)
def get_user_preferences() -> UserPreferencesResponse:
    service = PreferencesService()
    return service.get_user_preferences(user().id())


@router.patch(
    "",
    dependencies=[security],
    summary="Update user preferences",
    description="Update one or more user preference settings",
    status_code=200,
    responses={
        401: _generic_descriptions.ERROR_401,
    },
)
def patch_user_preferences(
    payload: UserPreferencesPatchInput,
) -> UserPreferencesResponse:
    service = PreferencesService()
    return service.update_user_preferences(user().id(), payload)


@router.delete(
    "/{preference_key}",
    dependencies=[security],
    summary="Delete user preference",
    description="Reset a user preference to global default by deleting the user override",
    status_code=200,
    responses={
        401: _generic_descriptions.ERROR_401,
    },
)
def delete_user_preference(preference_key: str) -> UserPreferencesResponse:
    service = PreferencesService()
    return service.delete_user_preference_key(user().id(), preference_key)
