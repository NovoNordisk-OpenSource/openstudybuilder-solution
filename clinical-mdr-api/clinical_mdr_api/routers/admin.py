from typing import Annotated, Any

from fastapi import APIRouter, Query

from clinical_mdr_api.domain_repositories.user_repository import UserRepository
from clinical_mdr_api.models.user import UserInfo, UserInfoPatchInput
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services._meta_repository import MetaRepository
from common import exceptions
from common.auth import rbac

# Prefixed with "/admin"
router = APIRouter()

CACHE_STORE_NAMES = [
    "cache_store_item_by_uid",
    "cache_store_item_by_study_uid",
    "cache_store_item_by_project_number",
]


@router.get(
    "/caches",
    dependencies=[rbac.ADMIN_READ],
    summary="Returns all cache stores",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_caches(show_items: Annotated[bool | None, Query()] = False) -> list[dict]:
    all_repos = _get_all_repos()
    return [_get_cache_info(x, show_items) for x in all_repos]


@router.delete(
    "/caches",
    dependencies=[rbac.ADMIN_WRITE],
    summary="Clears all cache stores",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def clear_caches() -> list[dict]:
    all_repos = _get_all_repos()
    for repo in all_repos:
        for store_name in CACHE_STORE_NAMES:
            cache_store = getattr(repo, store_name, None)
            if cache_store is not None:
                cache_store.clear()

    return get_caches()


@router.get(
    "/users",
    dependencies=[rbac.ADMIN_READ],
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
    dependencies=[rbac.ADMIN_WRITE],
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


def _get_cache_info(repo: Any, show_items: bool = False) -> dict:
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
