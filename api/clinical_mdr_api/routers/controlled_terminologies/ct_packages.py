"""CTPackage router."""

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query

from clinical_mdr_api.models.controlled_terminologies.ct_package import (
    CTPackage,
    CTPackageChanges,
    CTPackageChangesSpecificCodelist,
    CTPackageDates,
)
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.controlled_terminologies.ct_package import (
    CTPackageService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.models.error import ErrorResponse

# Prefixed with "/ct"
router = APIRouter()

CTCodelistUid = Path(description="The unique id of the CTCodelist")


@router.get(
    "/packages",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns all controlled terminology packages.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_packages(
    catalogue_name: Annotated[
        str | None,
        Query(
            description="If specified, only packages from given catalogue are returned.",
        ),
    ] = None,
    standards_only: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="If set to True, only standard packages are returned. Defaults to True",
        ),
    ] = True,
    sponsor_only: Annotated[
        bool,
        _generic_descriptions.STRICT_BOOL_VALIDATOR,
        Query(
            description="If set to True, only sponsor packages are returned.",
        ),
    ] = False,
) -> list[CTPackage]:
    ct_package_service = CTPackageService()

    return ct_package_service.get_all_ct_packages(
        catalogue_name=catalogue_name,
        standards_only=standards_only,
        sponsor_only=sponsor_only,
    )


@router.get(
    "/packages/changes",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns changes between codelists and terms inside two different packages.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_packages_changes_between_codelists_and_terms(
    catalogue_name: str,
    old_package_date: Annotated[
        date,
        Query(
            description="The date for the old package, for instance '2020-03-27'"
            "\n_the possible dates for given catalogue_name can be retrieved by the /ct/packages/dates endpoint",
        ),
    ],
    new_package_date: Annotated[
        date,
        Query(
            description="The datetime for the new package, for instance '2020-06-26'"
            "\n_the possible dates for given catalogue_name can be retrieved by the /ct/packages/dates endpoint",
        ),
    ],
) -> CTPackageChanges:
    ct_package_service = CTPackageService()
    return ct_package_service.get_ct_packages_changes(
        catalogue_name=catalogue_name,
        old_package_date=old_package_date,
        new_package_date=new_package_date,
    )


@router.get(
    "/packages/{codelist_uid}/changes",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns changes from given codelist and all associated terms inside two different packages.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_packages_changes_between_codelist_and_all_associated_terms(
    catalogue_name: str,
    codelist_uid: Annotated[str, CTCodelistUid],
    old_package_date: Annotated[
        date,
        Query(
            description="The date for the old package, for instance '2020-03-27'"
            "\n_the possible dates for given catalogue_name can be retrieved by the /ct/packages/dates endpoint",
        ),
    ],
    new_package_date: Annotated[
        date,
        Query(
            description="The date for the new package, for instance '2020-06-26'"
            "\n_the possible dates for given catalogue_name can be retrieved by the /ct/packages/dates endpoint",
        ),
    ],
) -> CTPackageChangesSpecificCodelist:
    ct_package_service = CTPackageService()
    return ct_package_service.get_ct_packages_codelist_changes(
        catalogue_name=catalogue_name,
        old_package_date=old_package_date,
        new_package_date=new_package_date,
        codelist_uid=codelist_uid,
    )


@router.get(
    "/packages/dates",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns all effective dates for packages in a given catalogue.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_package_dates(catalogue_name: str) -> CTPackageDates:
    ct_package_service = CTPackageService()
    return ct_package_service.get_all_effective_dates(catalogue_name=catalogue_name)


@router.post(
    "/packages/sponsor",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates a sponsor CT package, in the context of a study.",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The sponsor package was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Cannot create two CT Sponsor Packages with the same date.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Entity not found - Reasons include: \n"
            "- The parent package doesn't exist.",
        },
    },
)
def create(
    extends_package: Annotated[
        str,
        Body(
            description="The name of the parent package that the sponsor package extends."
        ),
    ],
    effective_date: Annotated[
        date,
        Body(
            description="The effective date of the package, for instance '2020-09-27'"
        ),
    ],
    library_name: Annotated[
        str | None,
        Body(
            description="The name of the library for this package. Defaults to the configured sponsor library."
        ),
    ] = None,
) -> CTPackage:
    ct_package_service = CTPackageService()
    kwargs: dict[str, Any] = {
        "extends_package": extends_package,
        "effective_date": effective_date,
    }
    if library_name is not None:
        kwargs["library_name"] = library_name
    return ct_package_service.create_sponsor_ct_package(**kwargs)
