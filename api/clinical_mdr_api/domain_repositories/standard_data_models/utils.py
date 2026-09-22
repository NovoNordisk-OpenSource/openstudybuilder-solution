from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    SponsorModelValue,
)
from common.config import settings

# Sponsor models created before schemas were introduced (no FOLLOWS_SCHEMA link)
# are treated as following schema version 1.
DEFAULT_SCHEMA_VERSION = 1


def get_schema_library_and_version_for_sponsor_model_name(
    sponsor_model_name: str,
) -> tuple[str, int]:
    """Library and schema version a named SM follows, via its FOLLOWS_SCHEMA link.

    Both the library and the version come from the followed schema node itself:
    the write path records the link against the ``SponsorModelSchemaRoot`` for the
    sponsor model's library (uid ``SponsorModelSchema_<library>``), so reading them
    together pins a projection to the exact schema the model follows rather than
    assuming the default sponsor library.

    Falls back to the default sponsor library and version 1 for legacy sponsor
    models with no FOLLOWS_SCHEMA link (or when the model doesn't exist), matching
    the read-time treatment of pre-schema sponsor models.
    """
    default = (settings.sponsor_library_name, DEFAULT_SCHEMA_VERSION)
    sponsor_model_value = SponsorModelValue.nodes.get_or_none(name=sponsor_model_name)
    if sponsor_model_value is None:
        return default
    schema_node = sponsor_model_value.follows_schema.single()
    if schema_node is None or schema_node.schema_version is None:
        return default
    schema_root = schema_node.has_schema_version.single()
    if schema_root is None:
        return default
    library = schema_root.has_library.single()
    if library is None:
        return default
    return library.name, schema_node.schema_version
