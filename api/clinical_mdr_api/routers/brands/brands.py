from typing import Annotated

from fastapi import APIRouter, Body, Path

from clinical_mdr_api.models.brands.brand import Brand, BrandCreateInput
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.brands.brand import BrandService
from common.auth import rbac
from common.auth.dependencies import security
from common.models.error import ErrorResponse

# Prefixed with "/brands"
router = APIRouter()

BrandUID = Path(description="The unique id of brand")
Service = BrandService


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns all brands.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_brands() -> list[Brand]:
    return Service().get_all_brands()


@router.get(
    "/{brand_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns the brand identified by the specified 'brand_uid'.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_brand(
    brand_uid: Annotated[str, BrandUID],
) -> Brand:
    return Service().get_brand(brand_uid)


@router.post(
    "",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates a new brand.",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The brand was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid to process the request. Expect more detailed"
            " information in response body.",
        },
    },
)
def create(
    brand_create_input: Annotated[
        BrandCreateInput,
        Body(description="Related parameters of the brand that shall be created."),
    ],
) -> Brand:
    return Service().create(brand_create_input)


@router.delete(
    "/{brand_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Deletes the brand identified by 'brand_uid'.",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The item was successfully deleted."},
    },
)
def delete(brand_uid: Annotated[str, BrandUID]):
    Service().delete(brand_uid)
