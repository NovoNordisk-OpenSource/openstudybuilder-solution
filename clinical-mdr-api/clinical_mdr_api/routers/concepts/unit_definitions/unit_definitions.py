from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Query, Request, Response
from fastapi import status as fast_api_status
from pydantic.types import Json

from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
    UnitDefinitionPatchInput,
    UnitDefinitionPostInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.concepts.unit_definitions.unit_definition import (
    UnitDefinitionService,
)
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/concepts/unit-definitions"
router = APIRouter()

Service = UnitDefinitionService


# Argument definitions
UnitDefinitionUID = Path(description="The unique id of unit definition.")


@router.get(
    "",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns all unit definitions in their latest/newest version.",
    description=f"""
Allowed parameters include : filter on fields, sort by field name with sort direction, pagination.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[UnitDefinitionModel],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library","uid","name","start_date","end_date","status","version","change_description","author_username"
"Sponsor","826d80a7-0b6a-419d-8ef1-80aa241d7ac7","First  [ComparatorIntervention]","2020-10-22T10:19:29+00:00",,"Draft","0.1","Initial version","NdSJ"
"""
                },
                "text/xml": {
                    "example": """
                    <?xml version="1.0" encoding="UTF-8" ?><root><data type="list"><item type="dict"><uid type="str">e9117175-918f-489e-9a6e-65e0025233a6</uid><name type="str">Alamakota</name><start_date type="str">2020-11-19T11:51:43.000Z</start_date><status type="str">Draft</status><version type="str">0.2</version><change_description type="str">Test</change_description><author_username type="str">someone@example.com</author_username></item></data></root>
"""
                },
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
            }
        },
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "library_name",
            "name",
            "master_unit",
            "display_unit",
            "unit_subsets",
            "ucum=ucum.name",
            "ct_units",
            "convertible_unit",
            "si_unit",
            "us_conventional_unit",
            "use_complex_unit_conversion",
            "unit_dimension=unit_dimension.name",
            "legacy_code",
            "use_molecular_weight",
            "conversion_factor_to_master",
            "start_date",
            "status",
            "version",
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
def get_all(
    request: Request,  # request is actually required by the allow_exports decorator
    service: Annotated[Service, Depends(Service)],
    library_name: Annotated[str | None, Query()] = None,
    dimension: Annotated[
        str | None,
        Query(
            description="The code submission value of the unit dimension to filter, for instance 'Dose Unit'."
        ),
    ] = None,
    subset: Annotated[
        str | None,
        Query(
            description="The name of the unit subset to filter, for instance 'Age Unit'."
        ),
    ] = None,
    sort_by: Annotated[
        Json | None, Query(description=_generic_descriptions.SORT_BY)
    ] = None,
    page_number: Annotated[
        int | None, Query(ge=1, description=_generic_descriptions.PAGE_NUMBER)
    ] = config.DEFAULT_PAGE_NUMBER,
    page_size: Annotated[
        int | None,
        Query(
            ge=0,
            le=config.MAX_PAGE_SIZE,
            description=_generic_descriptions.PAGE_SIZE,
        ),
    ] = config.DEFAULT_PAGE_SIZE,
    filters: Annotated[
        Json | None,
        Query(
            description=_generic_descriptions.FILTERS,
            openapi_examples=_generic_descriptions.FILTERS_EXAMPLE,
        ),
    ] = None,
    operator: Annotated[
        str | None, Query(description=_generic_descriptions.FILTER_OPERATOR)
    ] = config.DEFAULT_FILTER_OPERATOR,
    total_count: Annotated[
        bool | None, Query(description=_generic_descriptions.TOTAL_COUNT)
    ] = False,
) -> CustomPage[UnitDefinitionModel]:
    results = service.get_all(
        library_name=library_name,
        dimension=dimension,
        subset=subset,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sort_by,
    )

    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/headers",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=list[Any],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
    },
)
def get_distinct_values_for_header(
    service: Annotated[Service, Depends(Service)],
    field_name: Annotated[
        str, Query(description=_generic_descriptions.HEADER_FIELD_NAME)
    ],
    library_name: Annotated[str | None, Query()] = None,
    dimension: Annotated[
        str | None,
        Query(
            description="The code submission value of the unit dimension to filter, for instance 'Dose Unit'.",
        ),
    ] = None,
    subset: Annotated[
        str | None,
        Query(
            description="The name of the unit subset to filter, for instance 'Age Unit'.",
        ),
    ] = None,
    search_string: Annotated[
        str | None, Query(description=_generic_descriptions.HEADER_SEARCH_STRING)
    ] = "",
    filters: Annotated[
        Json | None,
        Query(
            description=_generic_descriptions.FILTERS,
            openapi_examples=_generic_descriptions.FILTERS_EXAMPLE,
        ),
    ] = None,
    operator: Annotated[
        str | None, Query(description=_generic_descriptions.FILTER_OPERATOR)
    ] = config.DEFAULT_FILTER_OPERATOR,
    page_size: Annotated[
        int | None, Query(description=_generic_descriptions.HEADER_PAGE_SIZE)
    ] = config.DEFAULT_HEADER_PAGE_SIZE,
):
    return service.get_distinct_values_for_header(
        library_name=library_name,
        dimension=dimension,
        subset=subset,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/{unit_definition_uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the latest/newest version of a specific Unit definition identified by 'unit_definition_uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=UnitDefinitionModel,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": """Not Found - The unit definition with the specified
            'unit_definition_uid' (and the specified date/time, version and/or status) wasn't found.""",
        },
    },
)
def get_by_uid(
    service: Annotated[Service, Depends(Service)],
    unit_definition_uid: Annotated[str, UnitDefinitionUID],
    at_specified_date_time: Annotated[
        datetime | None,
        Query(
            description="If specified, the latest/newest representation of the unit definition at this point in time is returned.\n"
            "The point in time needs to be specified in ISO 8601 format including the timezone, e.g.: "
            "'2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. ",
        ),
    ] = None,
    status: Annotated[
        LibraryItemStatus | None,
        Query(
            description="If specified, the representation of the unit definition in that status is returned (if existent). "
            "This may be particularly useful if the unit definition has "
            "a) a 'Draft' and a 'Final' status or "
            "b) a 'Draft' and a 'Retired' status at the same time "
            "and you are interested in the 'Final' or 'Retired' status.\n"
            "Valid values are: 'Final', 'Draft' or 'Retired'.",
        ),
    ] = None,
    version: Annotated[
        str | None,
        Query(
            description=r"If specified, the latest/newest representation of the concept is returned. "
            r"Only exact matches are considered. "
            r"The version is specified in the following format: \<major\>.\<minor\> where \<major\> and \<minor\> are digits. "
            r"E.g. '0.1', '0.2', '1.0', ...",
        ),
    ] = None,
) -> UnitDefinitionModel:
    return service.get_by_uid(
        unit_definition_uid,
        version=version,
        status=status,
        at_specified_datetime=at_specified_date_time,
    )


@router.get(
    "/{unit_definition_uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns the version history of a specific concept identified by 'unit_definition_uid'.",
    description=f"""
The returned versions are ordered by `start_date` descending (newest entries first)

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=list[UnitDefinitionModel],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library";"uid";"name";"start_date";"end_date";"status";"version";"change_description";"author_username"
"Sponsor";"826d80a7-0b6a-419d-8ef1-80aa241d7ac7";"First  [ComparatorIntervention]";"2020-10-22T10:19:29+00:00";;"Draft";"0.1";"Initial version";"NdSJ"
"""
                },
                "text/xml": {
                    "example": """
                    <?xml version="1.0" encoding="UTF-8" ?><root><data type="list"><item type="dict"><name type="str">Alamakota</name><start_date type="str">2020-11-19 11:51:43+00:00</start_date><end_date type="str">None</end_date><status type="str">Draft</status><version type="str">0.2</version><change_description type="str">Test</change_description><author_username type="str">someone@example.com</author_username></item><item type="dict"><name type="str">Alamakota</name><start_date type="str">2020-11-19 11:51:07+00:00</start_date><end_date type="str">2020-11-19 11:51:43+00:00</end_date><status type="str">Draft</status><version type="str">0.1</version><change_description type="str">Initial version</change_description><author_username type="str">someone@example.com</author_username></item></data></root>
"""
                },
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
            }
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The concept with the specified 'unit_definition_uid' wasn't found.",
        },
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "library_name",
            "uid",
            "name",
            "unit_ct",
            "convertible_unit",
            "display_unit",
            "master_unit",
            "si_unit",
            "us_conventional_unit",
            "use_complex_unit_conversion",
            "legacy_code",
            "use_molecular_weight",
            "conversion_factor_to_master",
            "start_date",
            "end_date",
            "status",
            "version",
            "change_description",
            "author_username",
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
def get_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    service: Annotated[Service, Depends(Service)],
    unit_definition_uid: Annotated[str, UnitDefinitionUID],
) -> list[UnitDefinitionModel]:
    return service.get_versions(unit_definition_uid)


@router.post(
    "",
    dependencies=[rbac.LIBRARY_WRITE],
    response_model=UnitDefinitionModel,
    summary="Creates a new unit definition in 'Draft' status.",
    description="""This request is only valid if the unit definition
* belongs to a library that allows creating (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'change_description' property will be set automatically.
* The 'version' property will be set to '0.1'.
* The unit definition template will be linked to a library.

""",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The concept was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The concept name is not valid.\n"
            "- The library doesn't allow to create concept.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The library with the specified 'library_name' could not be found.",
        },
        409: _generic_descriptions.ERROR_409,
    },
)
def post(
    service: Annotated[Service, Depends(Service)],
    unit_definition_post_input: Annotated[
        UnitDefinitionPostInput, Body(description="The concept that shall be created.")
    ],
) -> UnitDefinitionModel:
    return service.post(unit_definition_post_input)  # type: ignore


@router.patch(
    "/{unit_definition_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Updates the unit definition identified by 'unit_definition_uid'.",
    description="""This request is only valid if the unit definition
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.

""",
    response_model=UnitDefinitionModel,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The unit definition is not in draft status.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The concept with the specified 'unit_definition_uid' could not be found.",
        },
        409: _generic_descriptions.ERROR_409,
    },
)
def patch(
    service: Annotated[Service, Depends(Service)],
    unit_definition_uid: Annotated[str, UnitDefinitionUID],
    patch_input: Annotated[
        UnitDefinitionPatchInput,
        Body(
            description="The new content of the concept including the change description.",
        ),
    ],
) -> UnitDefinitionModel:
    return service.patch(unit_definition_uid, patch_input)


@router.post(
    "/{unit_definition_uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates a new version of the unit definition identified by 'unit_definition_uid'.",
    description="""This request is only valid if the unit definition
* is in 'Final' or 'Retired' status only (so no latest 'Draft' status exists) and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The latest 'Final' or 'Retired' version will remain the same as before.
* The status of the new version will be automatically set to 'Draft'.
* The 'version' property of the new version will be automatically set to the version of the latest 'Final' or 'Retired' version increased by +0.1.

""",
    response_model=UnitDefinitionModel,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The unit definition is not in final or retired status or has a draft status.\n"
            "- The library doesn't allow to create a new version.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The  concept with the specified 'unit_definition_uid' could not be found.",
        },
    },
)
def new_version(
    service: Annotated[Service, Depends(Service)],
    unit_definition_uid: Annotated[str, UnitDefinitionUID],
) -> UnitDefinitionModel:
    return service.new_version(unit_definition_uid)


@router.post(
    "/{unit_definition_uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approves the unit definition identified by 'unit_definition_uid'.",
    description="""This request is only valid if the unit definition
* is in 'Draft' status and
* belongs to a library that allows editing (the 'is_editable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=UnitDefinitionModel,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The unit definition is not in draft status.\n"
            "- The library doesn't allow to approve drafts.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The unit definition with the specified 'unit_definition_uid' could not be found.",
        },
    },
)
def approve(
    service: Annotated[Service, Depends(Service)],
    unit_definition_uid: Annotated[str, UnitDefinitionUID],
) -> UnitDefinitionModel:
    return service.approve(unit_definition_uid)


@router.delete(
    "/{unit_definition_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Inactivates/deactivates the unit definition identified by 'unit_definition_uid'.",
    description="""This request is only valid if the unit definition
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'change_description' property will be set automatically.
* The 'version' property will remain the same as before.
    """,
    response_model=UnitDefinitionModel,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The unit definition is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The unit definition with the specified 'unit_definition_uid' could not be found.",
        },
    },
)
def inactivate(
    service: Annotated[Service, Depends(Service)],
    unit_definition_uid: Annotated[str, UnitDefinitionUID],
) -> UnitDefinitionModel:
    return service.inactivate(unit_definition_uid)


@router.post(
    "/{unit_definition_uid}/activations",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Reactivates the unit definition identified by 'unit_definition_uid'.",
    description="""This request is only valid if the unit definition
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'change_description' property will be set automatically.
* The 'version' property will remain the same as before.
    """,
    response_model=UnitDefinitionModel,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The unit definition is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The concept with the specified 'unit_definition_uid' could not be found.",
        },
    },
)
def reactivate(
    service: Annotated[Service, Depends(Service)],
    unit_definition_uid: Annotated[str, UnitDefinitionUID],
) -> UnitDefinitionModel:
    return service.reactivate(unit_definition_uid)


@router.delete(
    "/{unit_definition_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Deletes the unit definition identified by 'unit_definition_uid'.",
    description="""This request is only valid if \n
* the unit definition is in 'Draft' status and
* the unit definition has never been in 'Final' status and
* the unit definition belongs to a library that allows deleting (the 'is_editable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        204: {"description": "No Content - The concept was successfully deleted."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The concept is not in draft status.\n"
            "- The concept was already in final state or is in use.\n"
            "- The library doesn't allow to delete concept.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An concept with the specified uid could not be found.",
        },
    },
)
def delete(
    service: Annotated[Service, Depends(Service)],
    unit_definition_uid: Annotated[str, UnitDefinitionUID],
) -> None:
    service.delete(unit_definition_uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)
