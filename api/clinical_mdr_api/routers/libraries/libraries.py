"""Objective templates router."""

from typing import Annotated

from fastapi import APIRouter, Body, Query

from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.libraries import libraries as service
from common.auth import rbac
from common.auth.dependencies import security

# Prefixed with "/libraries"
router = APIRouter()


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns all libraries",
)
# pylint: disable=unused-argument
def get_libraries(
    is_editable: Annotated[
        bool | None,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="If specified, only those libraries are returned that are editable. \n"
            "Valid values are: 'true' or 'false'.",
        ),
    ] = None,
) -> list[Library]:
    return service.get_libraries(is_editable)


@router.post(
    "",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates a new library.",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The library was successfully created."},
        409: _generic_descriptions.ERROR_409,
    },
)
def create_library(library: Annotated[Library, Body()]) -> Library:
    return service.create(library.name, library.is_editable)
