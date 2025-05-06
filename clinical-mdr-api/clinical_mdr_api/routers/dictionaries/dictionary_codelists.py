"""DictionaryCodelist router."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.models.dictionaries.dictionary_codelist import (
    DictionaryCodelist,
    DictionaryCodelistCreateInput,
    DictionaryCodelistEditInput,
    DictionaryCodelistTermInput,
    DictionaryCodelistVersion,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.dictionaries.dictionary_codelist_generic_service import (
    DictionaryCodelistGenericService,
)
from common import config
from common.auth import rbac
from common.models.error import ErrorResponse

# Prefixed with "/dictionaries"
router = APIRouter()

DictionaryCodelistUID = Path(description="The unique id of the DictionaryCodelist")
DictionaryCodelistLibrary = Query(
    description="The Library from which the dictionaries codelists should be retrieved",
)
TermUID = Path(description="The unique id of the Codelist Term")


@router.get(
    "/codelists",
    dependencies=[rbac.LIBRARY_READ],
    summary="List all dictionary codelists.",
    description=f"""
State before:
 - The library must exist.
 
Business logic:
 - List all dictionary codelists (in their latest versions).
 
State after:
 - No change

Possible errors:
 - Invalid library name.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[DictionaryCodelist],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "dictionary_id",
            "name",
            "name_sentence_case",
            "abbreviation",
            "definition",
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
def get_codelists(
    request: Request,  # request is actually required by the allow_exports decorator
    library_name: Annotated[str, DictionaryCodelistLibrary],
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
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    results = dictionary_codelist_service.get_all_dictionary_codelists(
        library=library_name,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
    )
    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/codelists/headers",
    dependencies=[rbac.LIBRARY_READ],
    summary="Returns possibles values from the database for a given header",
    description="Allowed parameters include : field name for which to get possible values, "
    "search string to provide filtering for the field name, additional filters to apply on other fields",
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
    library_name: Annotated[str, DictionaryCodelistLibrary],
    field_name: Annotated[
        str, Query(description=_generic_descriptions.HEADER_FIELD_NAME)
    ],
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
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.post(
    "/codelists",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Creates new dictionary codelist.",
    description="""The following nodes are created
  * DictionaryCodelistRoot
  * DictionaryCodelistValue
""",
    response_model=DictionaryCodelist,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The dictionary codelist was successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't exist.\n"
            "- The library doesn't allow to add new items.\n",
        },
    },
)
def create(
    dictionary_codelist_input: Annotated[
        DictionaryCodelistCreateInput,
        Body(description="Properties to create DictionaryCodelistValue node."),
    ],
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.create(dictionary_codelist_input)


@router.get(
    "/codelists/{dictionary_codelist_uid}",
    dependencies=[rbac.LIBRARY_READ],
    summary="List details on the dictionary codelist with {dictionary_codelist_uid}",
    description="""
State before:
 - The selected codelist must exist.
 
Business logic:
 - List details of the selected codelist (in a given version, if specified)

State after:
 - No change""",
    response_model=DictionaryCodelist,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_codelist(
    dictionary_codelist_uid: Annotated[str, DictionaryCodelistUID],
    version: Annotated[
        str | None,
        Query(
            description="If specified then the latest/newest representation of the dictionary codelist "
            "for DictionaryCodelistValue in that version is returned.\n"
            "Only exact matches are considered. The version is specified in the following format:"
            "<major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0',",
        ),
    ],
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.get_by_uid(
        codelist_uid=dictionary_codelist_uid, version=version
    )


@router.get(
    "/codelists/{dictionary_codelist_uid}/versions",
    dependencies=[rbac.LIBRARY_READ],
    summary="List version history for a dictionary codelist",
    description="""
State before:
 - codelist_uid must exist.
 
Business logic:
 - List version history for the representation of the dictionary codelist, including the use as template parameter.
 - The returned versions are ordered by start_date descending (newest entries first).
 
State after:
 - No change
 
Possible errors:
 - Invalid codelist_uid.
    """,
    response_model=list[DictionaryCodelistVersion],
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The dictionary codelist with the specified 'dictionary_codelist_uid' wasn't found.",
        },
    },
)
def get_versions(
    dictionary_codelist_uid: Annotated[str, DictionaryCodelistUID],
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.get_version_history(
        codelist_uid=dictionary_codelist_uid
    )


@router.patch(
    "/codelists/{dictionary_codelist_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Update name or template parameter flag for dictionary codelist",
    description="""
State before:
 - codelist_uid must exist and the dictionary codelist must exist in status draft.
 
Business logic:
 - If the dictionary codelist related to codelist_uid exist in status draft then name attribute and Template Parameter node label are updated.
 - If Template Parameter have been set to 'Y' then it cannot be set back to 'N' (i.e. when the Template Parameter node label have been added it cannot be removed).
 
State after:
 - name attribute and Template Parameter node label are updated for the dictionary codelist.
 - Audit trail entry must be made with update of name attribute or Template Parameter flag.
 
Possible errors:
 - Invalid codelist_uid.
""",
    response_model=DictionaryCodelist,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The dictionary codelist is not in draft status.\n"
            "- The dictionary codelist had been in 'Final' status before.\n"
            "- The library doesn't allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The codelist with the specified 'codelist_uid' wasn't found.",
        },
    },
)
def edit(
    dictionary_codelist_uid: Annotated[str, DictionaryCodelistUID],
    dictionary_codelist_input: Annotated[
        DictionaryCodelistEditInput,
        Body(
            description="The new parameter terms for the dictionary codelist including the change description.",
        ),
    ],
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.edit_draft(
        codelist_uid=dictionary_codelist_uid, codelist_input=dictionary_codelist_input
    )


@router.post(
    "/codelists/{dictionary_codelist_uid}/versions",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Create a new version of the dictionary codelist",
    description="""
State before:
 - codelist_uid must exist and the dictionary codelist must be in status Final.
 
Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' or 'Retired' version increased by +0.1.
 - The 'change_description' property will be set automatically to 'New version'.
 
State after:
 - Dictionary codelist changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating new Draft version.
 
Possible errors:
 - Invalid codelist_uid or status not Final.
 
""",
    response_model=DictionaryCodelist,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The dictionary codelist was successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library doesn't allow to create codelists.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The dictionary codelist is not in final status.\n"
            "- The dictionary codelist with the specified 'dictionary_codelist_uid' could not be found.",
        },
    },
)
def create_new_version(
    dictionary_codelist_uid: Annotated[str, DictionaryCodelistUID],
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.create_new_version(
        codelist_uid=dictionary_codelist_uid
    )


@router.post(
    "/codelists/{dictionary_codelist_uid}/approvals",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Approve draft version of the dictionary codelist",
    description="""
State before:
 - codelist_uid must exist and the dictionary codelist must be in status Draft.
 
Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'change_description' property will be set automatically 'Approved version'.
 
State after:
 - Dictionary codelist changed status to Final and assigned a new major version number.
 - Audit trail entry must be made with action of approving to new Final version.
 
Possible errors:
 - Invalid codelist_uid or status not Draft.
    """,
    response_model=DictionaryCodelist,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "OK."},
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The codelist is not in draft status.\n"
            "- The library doesn't allow to approve codelist.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The codelist with the specified 'codelist_uid' wasn't found.",
        },
    },
)
def approve(
    dictionary_codelist_uid: Annotated[str, DictionaryCodelistUID],
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.approve(codelist_uid=dictionary_codelist_uid)


@router.post(
    "/codelists/{dictionary_codelist_uid}/terms",
    dependencies=[rbac.LIBRARY_WRITE],
    summary=" Attaches a dictionary term to a dictionary codelist",
    description="""
State before:
 - Codelist identified by uid must exist.

Business logic:
 - Create a HAS_TERM relationship between the selected codelist root and the selected term root, with the current date and current user.

Possible errors:
 - Invalid codelist_uid.
-  Invalid term_uid.
-  Codelist with {dictionary_codelist_uid} is not extensible.
- Term is already part of the specified codelist.""",
    response_model=DictionaryCodelist,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "The HAS_TERM relationship was successfully created.\n"
            "The TemplateParameter labels and HAS_PARAMETER_TERM relationship were successfully added "
            "if dictionary codelist identified by 'dictionary_codelist_uid' is a TemplateParameter."
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The dictionary codelist doesn't exist.\n"
            "- The dictionary term doesn't exist.\n"
            "- The dictionary codelist already has passed term.\n",
        },
        404: _generic_descriptions.ERROR_404,
    },
)
def add_term(
    dictionary_codelist_uid: Annotated[str, DictionaryCodelistUID],
    term_input: Annotated[
        DictionaryCodelistTermInput,
        Body(description="UID of the DictionaryTermRoot node."),
    ],
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.add_term(
        codelist_uid=dictionary_codelist_uid, term_uid=term_input.term_uid
    )


@router.delete(
    "/codelists/{dictionary_codelist_uid}/terms/{dictionary_term_uid}",
    dependencies=[rbac.LIBRARY_WRITE],
    summary="Removes a dictionary term from a dictionary codelist",
    description="""
State before:
 - Codelist identified by codelist_uid must exist.
 - Term identified by dictionary_term_uid must exist.
 - Codelist contains the term that is being removed.


Business logic:
 - Create a HAD_TERM relationship between the selected codelist root and the selected term root, with the current date as the end date, and current user.
 - Remove the old HAS_TERM relationship between the codelist and the term.

Possible errors:
 - Invalid codelist_uid.
 - Invalid dictionary_term_uid.
- Term is not part of the specified codelist. """,
    response_model=DictionaryCodelist,
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "The HAS_TERM relationship was successfully deleted and "
            "HAD_TERM relationship was successfully created.\n"
            "The HAS_PARAMETER_TERM relationship was successfully deleted if codelist identified by "
            "uid is a TemplateParameter"
        },
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The codelist doesn't exist.\n"
            "- The term doesn't exist.\n"
            "- The codelist doesn't have passed term.\n",
        },
        404: _generic_descriptions.ERROR_404,
    },
)
def remove_term(
    dictionary_codelist_uid: Annotated[str, DictionaryCodelistUID],
    dictionary_term_uid: Annotated[str, TermUID],
):
    dictionary_codelist_service = DictionaryCodelistGenericService()
    return dictionary_codelist_service.remove_term(
        codelist_uid=dictionary_codelist_uid, term_uid=dictionary_term_uid
    )
