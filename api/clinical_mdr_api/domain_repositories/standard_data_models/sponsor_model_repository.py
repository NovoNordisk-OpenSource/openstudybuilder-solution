from typing import Any

from neomodel import NodeSet, RelationshipDefinition, db
from neomodel.sync_.match import Path

from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DataModelIGRoot,
    SponsorModelSchemaRoot,
    SponsorModelValue,
)
from clinical_mdr_api.domain_repositories.neomodel_ext_item_repository import (
    NeomodelExtBaseRepository,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model import (
    SponsorModelAR,
    SponsorModelMetadataVO,
    SponsorModelVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.standard_data_models.sponsor_model import SponsorModel
from clinical_mdr_api.services.user_info import UserInfoService
from common.config import settings
from common.exceptions import BusinessLogicException


class SponsorModelRepository(  # type: ignore[misc]
    NeomodelExtBaseRepository, LibraryItemRepositoryImplBase[SponsorModelAR]
):
    root_class = DataModelIGRoot
    value_class = SponsorModelValue
    return_model = SponsorModel

    # The sponsor model's library lives on the SponsorModelValue node, not on
    # the (shared) DataModelIGRoot, so the base repository must not manage a
    # library relationship on the root itself - doing so would repoint the
    # library of the underlying Implementation Guide root, which is shared by
    # every sponsor model built on it.
    has_library = False

    def get_neomodel_extension_query(self) -> NodeSet:
        # All three relations must be fetched from the SAME has_sponsor_model_version
        # binding. Chaining separate .traverse() calls would overwrite the first path,
        # and passing them as independent paths would produce a cartesian
        # product over the sponsor model versions; unique_variables() forces the
        # shared prefix to resolve to one binding. follows_schema/has_library are
        # optional so legacy sponsor models (created before those links existed)
        # are still returned.
        return DataModelIGRoot.nodes.traverse(
            "has_sponsor_model_version__extends_version",
            Path(value="has_sponsor_model_version__follows_schema", optional=True),
            Path(value="has_sponsor_model_version__has_library", optional=True),
        ).unique_variables("has_sponsor_model_version")

    def generate_name(
        self,
        ig_uid: str,
        ig_version_number: str,
        version_number: str,
        name_qualifier: str | None = None,
    ):
        segments = [str.lower(ig_uid), settings.sponsor_model_prefix]
        if name_qualifier:
            segments.append(str.lower(name_qualifier))
        segments.extend(
            [
                ig_version_number,
                f"{settings.sponsor_model_version_number_prefix}{int(version_number):02}",
            ]
        )
        return "_".join(segments)

    # Structural props on the SM value node that must not surface as extras.
    _EXTRA_PROPS_DENYLIST = frozenset({"name", "name_qualifier"})

    def get_value_properties_by_names(
        self, sponsor_model_names: list[str]
    ) -> dict[str, dict[str, Any]]:
        """Full stored property map of each SM value node, keyed by SM name."""
        if not sponsor_model_names:
            return {}
        rows, _ = db.cypher_query(
            """
            MATCH (value:SponsorModelValue)
            WHERE value.name IN $names
            RETURN value.name AS name, properties(value) AS props
            """,
            {"names": list(sponsor_model_names)},
        )
        return {
            row[0]: {
                key: val
                for key, val in (row[1] or {}).items()
                if key not in self._EXTRA_PROPS_DENYLIST
            }
            for row in rows
        }

    @staticmethod
    def _linked_schema_version(value: SponsorModelValue) -> int | None:
        linked = value.follows_schema.single()
        return linked.schema_version if linked is not None else None

    @staticmethod
    def _linked_library_name(value: SponsorModelValue) -> str | None:
        linked = value.has_library.single()
        return linked.name if linked is not None else None

    def _has_data_changed(self, ar: SponsorModelAR, value: SponsorModelValue) -> bool:
        changed = (
            ar.sponsor_model_vo.name != value.name
            or ar.sponsor_model_vo.name_qualifier != value.name_qualifier
            or ar.library.name != self._linked_library_name(value)
        )
        # Only consider the schema link when a version was explicitly requested,
        # so existing (unlinked) sponsor models are not needlessly re-versioned.
        if ar.sponsor_model_vo.schema_version is not None:
            changed = changed or (
                ar.sponsor_model_vo.schema_version != self._linked_schema_version(value)
            )
        return changed

    def _create(self, item: SponsorModelAR) -> SponsorModelAR:
        """
        Overrides generic LibraryItemRepository method
        """
        relation_data = item.item_metadata
        root = DataModelIGRoot.nodes.get_or_none(uid=item.uid)

        BusinessLogicException.raise_if(root is None, "Implementation Guide", item.uid)

        value = self._get_or_create_value(root=root, ar=item)

        (
            root,
            value,
            _,
            _,
            _,
        ) = self._db_create_and_link_nodes(
            root=root,
            value=value,
            rel_properties=self._library_item_metadata_vo_to_datadict(relation_data),
            save_root=False,
        )

        return item

    def _get_version_relation_keys(self, root_node: DataModelIGRoot) -> tuple[
        RelationshipDefinition,
        RelationshipDefinition,
        RelationshipDefinition,
        RelationshipDefinition,
        RelationshipDefinition,
    ]:
        return (
            root_node.has_sponsor_model_version,
            root_node.has_latest_sponsor_model_value,
            root_node.latest_sponsor_model_draft,
            root_node.latest_sponsor_model_final,
            root_node.latest_sponsor_model_retired,
        )

    @staticmethod
    def _library_item_metadata_vo_from_relation(
        relationship: VersionRelationship,
    ) -> SponsorModelMetadataVO:
        major = relationship.version
        return SponsorModelMetadataVO.from_repository_values(
            change_description=relationship.change_description,
            status=LibraryItemStatus(relationship.status),
            author_id=relationship.author_id,
            author_username=UserInfoService.get_author_username_from_id(
                relationship.author_id
            ),
            start_date=relationship.start_date,
            end_date=relationship.end_date,
            major_version=int(major),
            minor_version=0,
        )

    def _get_or_create_value(
        self,
        root: DataModelIGRoot,
        ar: SponsorModelAR,
        force_new_value_node: bool = False,
    ) -> SponsorModelValue:
        if not force_new_value_node:
            for itm in root.has_sponsor_model_version.all():
                if not self._has_data_changed(ar, itm):
                    return itm

        new_value = SponsorModelValue(
            name=ar.sponsor_model_vo.name,
            name_qualifier=ar.sponsor_model_vo.name_qualifier,
        )
        self._db_save_node(new_value)

        new_value.has_library.connect(self._get_library(ar.library.name))

        # Store sponsor-defined extras as node properties (neomodel only persists
        # declared properties), sanitizing keys for Neo4j.
        if ar.sponsor_model_vo.extra_properties:
            sanitized_props = {
                key.replace(" ", "_").replace("-", "_"): value
                for key, value in ar.sponsor_model_vo.extra_properties.items()
            }
            db.cypher_query(
                "MATCH (n) WHERE elementId(n) = $element_id SET n += $extra_props",
                {"element_id": new_value.element_id, "extra_props": sanitized_props},
            )

        ig_versions = root.has_version.filter(
            version_number=ar.sponsor_model_vo.ig_version_number
        )
        BusinessLogicException.raise_if(
            ig_versions is None or len(ig_versions) == 0,
            msg=f"The target version '{ar.sponsor_model_vo.ig_version_number}'"
            f" for the Implementation Guide with UID '{ar.sponsor_model_vo.ig_uid}' doesn't exist.",
        )

        new_value.extends_version.connect(ig_versions[0])

        self._link_schema_version(new_value, ar)

        return new_value

    @staticmethod
    def _link_schema_version(value: SponsorModelValue, ar: SponsorModelAR) -> None:
        """
        Link the sponsor model to the schema version it follows, for referential
        integrity. Skipped when no schema version was requested (the read path
        then defaults to version 1). The referenced schema version must already
        be published.
        """
        schema_version = ar.sponsor_model_vo.schema_version
        if schema_version is None:
            return

        library_name = ar.library.name
        schema_root = SponsorModelSchemaRoot.nodes.get_or_none(
            uid=f"SponsorModelSchema_{library_name}"
        )
        schema_values = (
            schema_root.has_schema_version.filter(schema_version=schema_version)
            if schema_root is not None
            else []
        )
        BusinessLogicException.raise_if(
            not schema_values,
            msg=f"The Sponsor Model Schema version '{schema_version}' doesn't exist "
            f"for library '{library_name}'.",
        )

        value.follows_schema.connect(schema_values[0])

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: DataModelIGRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: SponsorModelValue,
        **_kwargs,
    ) -> SponsorModelAR:
        # Prefer the library linked on the value node itself; fall back to the
        # (shared) IG root's library for sponsor models created before that
        # link existed, and finally to whatever the caller passed in.
        resolved_library = (
            value.has_library.single() or root.has_library.get_or_none() or library
        )
        return SponsorModelAR.from_repository_values(
            ig_uid=root.uid,
            sponsor_model_vo=SponsorModelVO.from_repository_values(
                ig_uid=root.uid,
                ig_version_number=relationship.version,
                name=value.name,
                version_number="",
                name_qualifier=value.name_qualifier,
                schema_version=self._linked_schema_version(value),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=resolved_library.name,
                is_library_editable_callback=lambda _: resolved_library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _maintain_parameters(
        self,
        versioned_object: SponsorModelAR,
        root: DataModelIGRoot,
        value: SponsorModelValue,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass
