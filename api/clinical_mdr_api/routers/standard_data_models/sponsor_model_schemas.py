"""Sponsor Model Schemas router"""

from typing import Annotated

from fastapi import APIRouter, Body, Path, Query, Response

from clinical_mdr_api.models.standard_data_models.sponsor_model_schema import (
    SponsorModelSchema,
    SponsorModelSchemaCreateInput,
    SponsorModelSchemaMetadata,
)
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.standard_data_models.sponsor_model_schema import (
    SponsorModelSchemaService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/standards/sponsor-models/schema"
router = APIRouter()

LibraryNameQuery = Query(
    description=f"Library the schema belongs to. Defaults to {settings.sponsor_library_name}."
)
SchemaVersionPath = Path(description="The integer version of the schema.", ge=1)


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List available sponsor model schema versions",
    description="""
Returns the metadata of all published schema versions for a library, ordered by
version. The schema blob itself is not included to keep the listing cheap; fetch a
single version to retrieve it.
""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
    },
)
def list_schemas(
    library_name: Annotated[str, LibraryNameQuery] = settings.sponsor_library_name,
) -> list[SponsorModelSchemaMetadata]:
    return SponsorModelSchemaService().get_all(library_name=library_name)


@router.get(
    "/{schema_version}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get a single sponsor model schema version",
    description="""
Returns a single, immutable schema version including the schema blob. This is the
endpoint the frontend calls to decide which columns to render.
""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The schema version doesn't exist for the library.",
        },
    },
)
def get_schema(
    schema_version: Annotated[int, SchemaVersionPath],
    library_name: Annotated[str, LibraryNameQuery] = settings.sponsor_library_name,
) -> SponsorModelSchema:
    return SponsorModelSchemaService().get_by_version(
        schema_version=schema_version, library_name=library_name
    )


@router.post(
    "",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Publish a sponsor model schema version",
    description="""
State before:
 - The specified library must exist.

Business logic:
 - Publishes an immutable schema version, keyed on (library, schema_version).
 - Idempotent on the version number:
   - version does not exist -> the version is created (201).
   - version exists and the submitted content is identical -> no-op success (200); no duplicate is created.
   - version exists and the submitted content differs -> rejected with 409; published versions are never overwritten.
 - The schema string must be valid YAML, otherwise 400 is returned. Its contents are otherwise opaque to the API.

State after:
 - A SponsorModelSchemaValue node is created (or left unchanged on an identical re-publish).

Possible errors:
 - Invalid (non-parseable) schema, missing library, or a conflicting re-publish.
""",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        200: {
            "model": SponsorModelSchema,
            "description": "OK - an identical version already existed; no change was made.",
        },
        201: {
            "model": SponsorModelSchema,
            "description": "Created - a new schema version was successfully published.",
        },
        400: {
            "model": ErrorResponse,
            "description": "BusinessLogicException - The schema is not valid YAML, or the library doesn't exist.",
        },
        409: {
            "model": ErrorResponse,
            "description": "AlreadyExistsException - The schema version already exists with different content.",
        },
    },
)
def publish_schema(
    response: Response,
    schema_input: Annotated[
        SponsorModelSchemaCreateInput,
        Body(description="The schema version to publish."),
    ],
) -> SponsorModelSchema:
    schema, was_created = SponsorModelSchemaService().publish(item_input=schema_input)
    response.status_code = 201 if was_created else 200
    return schema
