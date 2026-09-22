import yaml

from clinical_mdr_api.domain_repositories.standard_data_models.sponsor_model_schema_repository import (
    SponsorModelSchemaRepository,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model_schema import (
    SponsorModelSchemaAR,
)
from clinical_mdr_api.models.standard_data_models.sponsor_model_schema import (
    SponsorModelSchema,
    SponsorModelSchemaCreateInput,
    SponsorModelSchemaMetadata,
)
from common.auth.user import user
from common.config import settings
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    NotFoundException,
)

# Schema versions are immutable, so a version can be safely cached in-process
# after first read. Keyed by (library_name, schema_version); a successful POST
# invalidates the affected key.
_SCHEMA_CACHE: dict[tuple[str, int], SponsorModelSchema] = {}


class SponsorModelSchemaService:
    def __init__(self) -> None:
        self.author_id = user().id()
        self.repository = SponsorModelSchemaRepository()

    def __del__(self) -> None:
        repository = getattr(self, "repository", None)
        if repository is not None:
            repository.close()

    @staticmethod
    def _validate_schema_is_parseable(schema: str) -> None:
        try:
            yaml.safe_load(schema)
        except yaml.YAMLError as exc:
            raise BusinessLogicException(
                msg=f"The provided schema is not valid YAML: {exc}"
            ) from exc

    def publish(
        self, item_input: SponsorModelSchemaCreateInput
    ) -> tuple[SponsorModelSchema, bool]:
        """
        Publish a schema version idempotently on ``(library_name, schema_version)``.

        Returns the schema and a flag that is True when a new version was created
        (201) and False when an identical version already existed (200 no-op).
        Differing content for an existing version raises 409.
        """
        library_name = item_input.library_name or settings.sponsor_library_name
        self._validate_schema_is_parseable(item_input.schema_content)

        candidate = SponsorModelSchemaAR.from_input_values(
            library_name=library_name,
            schema_version=item_input.schema_version,
            schema=item_input.schema_content,
            author_id=self.author_id,
        )

        existing = self.repository.get_by_version(
            library_name, item_input.schema_version
        )
        if existing is not None:
            AlreadyExistsException.raise_if(
                not existing.matches_content(candidate),
                msg=(
                    f"Sponsor Model Schema version '{item_input.schema_version}' "
                    f"already exists for library '{library_name}' with different "
                    "content. Published schema versions are immutable."
                ),
            )
            # Identical re-publish: no-op success, no duplicate node.
            return SponsorModelSchema.from_sponsor_model_schema_ar(existing), False

        saved = self.repository.save(candidate)
        _SCHEMA_CACHE.pop((library_name, item_input.schema_version), None)
        return SponsorModelSchema.from_sponsor_model_schema_ar(saved), True

    def get_by_version(
        self, schema_version: int, library_name: str = settings.sponsor_library_name
    ) -> SponsorModelSchema:
        cache_key = (library_name, schema_version)
        cached = _SCHEMA_CACHE.get(cache_key)
        if cached is not None:
            return cached

        item = self.repository.get_by_version(library_name, schema_version)
        if item is None:
            raise NotFoundException(
                msg=(
                    f"Sponsor Model Schema version '{schema_version}' doesn't exist "
                    f"for library '{library_name}'."
                )
            )

        model = SponsorModelSchema.from_sponsor_model_schema_ar(item)
        _SCHEMA_CACHE[cache_key] = model
        return model

    def get_all(
        self, library_name: str = settings.sponsor_library_name
    ) -> list[SponsorModelSchemaMetadata]:
        return [
            SponsorModelSchemaMetadata.from_sponsor_model_schema_ar(item)
            for item in self.repository.get_all(library_name)
        ]
