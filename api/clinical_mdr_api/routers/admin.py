from typing import Annotated, Any

from fastapi import APIRouter, Query
from fastapi.requests import Request

from clinical_mdr_api.domain_repositories.user_repository import UserRepository
from clinical_mdr_api.models.complexity_score import (
    ActivityBurden,
    Burden,
    BurdenIdInput,
    BurdenInput,
)
from clinical_mdr_api.models.preferences import (
    GlobalPreferencesPatchInput,
    PreferencesResponse,
)
from clinical_mdr_api.models.user import UserInfo, UserInfoPatchInput
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.preferences import PreferencesService
from clinical_mdr_api.services.studies.complexity_score import ComplexityScoreService
from common import exceptions
from common.auth import rbac
from common.auth.dependencies import security

# Prefixed with "/admin"
router = APIRouter()

CACHE_STORE_NAMES = [
    "cache_store_item_by_uid",
    "cache_store_item_by_study_uid",
    "cache_store_item_by_project_number",
    "cache_get_user",
]


@router.get(
    "/caches",
    dependencies=[security, rbac.ADMIN_READ],
    summary="Returns all cache stores",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_caches(
    show_items: Annotated[
        bool, _generic_descriptions.STRICT_BOOL_VALIDATOR, Query()
    ] = False,
) -> list[dict[Any, Any]]:
    all_repos = _get_all_repos()
    return [_get_cache_info(x, show_items) for x in all_repos]


@router.delete(
    "/caches",
    dependencies=[security, rbac.ADMIN_WRITE],
    summary="Clears all cache stores",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def clear_caches() -> list[dict[Any, Any]]:
    all_repos = _get_all_repos()
    for repo in all_repos:
        for store_name in CACHE_STORE_NAMES:
            cache_store = getattr(repo, store_name, None)
            if cache_store is not None:
                cache_store.clear()

    # Clear shared service-level caches
    from clinical_mdr_api.services.studies.study_activity_selection_base import (
        StudyActivitySelectionBaseService,
    )

    with StudyActivitySelectionBaseService._shared_terms_date_cache_lock:
        StudyActivitySelectionBaseService._shared_terms_date_cache.clear()

    return get_caches()


@router.get(
    "/users",
    dependencies=[security, rbac.ADMIN_READ],
    summary="Returns all users",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_users() -> list[UserInfo]:
    user_repository = UserRepository()
    return user_repository.get_all_users()


@router.patch(
    "/users/{user_id}",
    dependencies=[security, rbac.ADMIN_WRITE],
    summary="Patch user",
    description="Set the username and/or email of a user",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def patch_user(user_id: str, payload: UserInfoPatchInput) -> UserInfo:
    user_repository = UserRepository()
    user = user_repository.patch_user(user_id, payload)
    if user:
        return user
    raise exceptions.NotFoundException(msg=f"User with ID '{user_id}' doesn't exist.")


def _get_all_repos():
    meta_repository = MetaRepository()
    all_repos = []
    for val in dir(meta_repository):
        if val.endswith("_repository"):
            repo = getattr(meta_repository, val)
            all_repos.append(repo)
    return all_repos


def _get_cache_info(repo: Any, show_items: bool = False) -> dict[str, Any]:
    ret = {
        "class": str(repo.__class__),
        "cache_stores": [],
    }

    for store_name in CACHE_STORE_NAMES:
        store_details = {
            "store_name": store_name,
            "size": (
                getattr(repo, store_name).currsize
                if getattr(repo, store_name, None) is not None
                else None
            ),
            "items": (
                _get_cache_item_info(getattr(repo, store_name)._Cache__data)
                if getattr(repo, store_name, None) is not None and show_items
                else None
            ),
        }
        ret["cache_stores"].append(store_details)

    return ret


def _get_cache_item_info(items):
    ret = []
    for key in items.keys():
        ret.append(
            {
                "key": str(key),
                "value_uid": getattr(items[key], "uid", "") if items[key] else None,
            }
        )
    return ret


@router.get(
    "/complexity-scores/activity-burdens",
    dependencies=[security, rbac.ADMIN_READ],
    summary="Returns activity groups and their corresponding site/patient burdens used for complexity score calculations",
    status_code=200,
)
@decorators.allow_exports(
    {
        "defaults": [
            "activity_subgroup_uid",
            "activity_subgroup_name",
            "burden_id",
            "site_burden",
            "patient_burden",
            "median_cost_usd",
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
def get_complexity_activity_burdens(
    request: Request,  # request is actually required by the allow_exports decorator
) -> list[ActivityBurden]:
    service = ComplexityScoreService()
    return service.get_activity_burdens(lite=False)


@router.get(
    "/complexity-scores/burdens",
    dependencies=[security, rbac.ADMIN_READ],
    summary="Returns site/patient burdens used for complexity score calculations",
    status_code=200,
)
@decorators.allow_exports(
    {
        "defaults": [
            "burden_id",
            "name",
            "description",
            "site_burden",
            "patient_burden",
            "median_cost_usd",
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
def get_complexity_burdens(
    request: Request,  # request is actually required by the allow_exports decorator
) -> list[Burden]:
    service = ComplexityScoreService()
    return service.get_burdens()


@router.post(
    "/complexity-scores/burdens",
    dependencies=[security, rbac.ADMIN_WRITE],
    summary="Creates a new or updates and existing site/patient burden used for complexity score calculations",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def create_complexity_burden(payload: BurdenInput) -> Burden:
    service = ComplexityScoreService()
    return service.create_burden(payload)


@router.put(
    "/complexity-scores/burdens/activity-burdens/{activity_subgroup_id}",
    dependencies=[security, rbac.ADMIN_WRITE],
    summary="Sets or updates a mapping between an activity subgroup and a site/patient burden used for complexity score calculations",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def update_complexity_activity_burden(
    activity_subgroup_id: str, burden: BurdenIdInput
) -> ActivityBurden:
    service = ComplexityScoreService()
    return service.update_activity_burden(activity_subgroup_id, burden)


@router.get(
    "/global-preferences",
    dependencies=[security, rbac.ADMIN_READ],
    summary="Returns global preferences",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_global_preferences() -> PreferencesResponse:
    service = PreferencesService()
    return service.get_global_preferences()


@router.patch(
    "/global-preferences",
    dependencies=[security, rbac.ADMIN_WRITE],
    summary="Update global preferences",
    description="Update one or more global preference settings",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def patch_global_preferences(
    payload: GlobalPreferencesPatchInput,
) -> PreferencesResponse:
    service = PreferencesService()
    return service.update_global_preferences(payload)
