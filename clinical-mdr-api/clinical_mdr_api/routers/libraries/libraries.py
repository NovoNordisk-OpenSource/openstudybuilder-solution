"""Objective templates router."""

from typing import Annotated

from fastapi import APIRouter, Body, Query

from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.libraries import libraries as service
from common.auth import rbac

# Prefixed with "/libraries"
router = APIRouter()


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all libraries",
    response_model=list[Library],
)
# pylint: disable=unused-argument
def get_libraries(
    is_editable: Annotated[
        bool | None,
        Query(
            description="If specified, only those libraries are returned that are editable. \n"
            "Valid values are: 'true' or 'false'.",
        ),
    ] = None,
):
    return service.get_libraries(is_editable)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new library.",
    response_model=Library,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The library was successfully created."},
        409: _generic_descriptions.ERROR_409,
    },
)
# pylint: disable=unused-argument
def create_library(
    library: Annotated[Library, Body()],
):
    return service.create(library.name, library.is_editable)
