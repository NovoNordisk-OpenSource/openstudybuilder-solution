from neomodel import NodeSet, RelationshipDefinition
from neomodel.sync_.match import (
    Collect,
    Last,
    NodeNameResolver,
    RawCypher,
    RelationNameResolver,
)

from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    DataModelIGRoot,
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
from common.config import SPONSOR_MODEL_PREFIX, SPONSOR_MODEL_VERSION_NUMBER_PREFIX
from common.exceptions import BusinessLogicException


class SponsorModelRepository(
    NeomodelExtBaseRepository, LibraryItemRepositoryImplBase[SponsorModelAR]
):
    root_class = DataModelIGRoot
    value_class = SponsorModelValue
    return_model = SponsorModel

    def get_neomodel_extension_query(self) -> NodeSet:
        return DataModelIGRoot.nodes.fetch_relations(
            "has_library",
            "has_latest_sponsor_model_value__extends_version",
        ).subquery(
            DataModelIGRoot.nodes.fetch_relations("has_sponsor_model_version")
            .intermediate_transform(
                {"rel": {"source": RelationNameResolver("has_sponsor_model_version")}},
                ordering=[
                    RawCypher("toInteger(split(rel.version, '.')[0])"),
                    RawCypher("toInteger(split(rel.version, '.')[1])"),
                    "rel.end_date",
                    "rel.start_date",
                ],
            )
            .annotate(latest_version=Last(Collect("rel"))),
            ["latest_version"],
            initial_context=[NodeNameResolver("self")],
        )

    def generate_name(self, ig_uid: str, ig_version_number: str, version_number: str):
        name = "_".join(
            [
                str.lower(ig_uid),
                SPONSOR_MODEL_PREFIX,
                ig_version_number,
                f"{SPONSOR_MODEL_VERSION_NUMBER_PREFIX}{int(version_number):02}",
            ]
        )
        return name

    def _has_data_changed(self, ar: SponsorModelAR, value: SponsorModelValue) -> bool:
        return ar.sponsor_model_vo.name != value.name

    def _create(self, item: SponsorModelAR) -> SponsorModelAR:
        """
        Overrides generic LibraryItemRepository method
        """
        relation_data: SponsorModelMetadataVO = item.item_metadata
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
        self, root: DataModelIGRoot, ar: SponsorModelAR
    ) -> SponsorModelValue:
        for itm in root.has_sponsor_model_version.all():
            if not self._has_data_changed(ar, itm):
                return itm

        new_value = SponsorModelValue(
            name=ar.sponsor_model_vo.name,
        )
        self._db_save_node(new_value)

        ig_versions = root.has_version.filter(
            version_number=ar.sponsor_model_vo.ig_version_number
        )
        BusinessLogicException.raise_if(
            ig_versions is None or len(ig_versions) == 0,
            msg=f"The target version '{ar.sponsor_model_vo.ig_version_number}'"
            f" for the Implementation Guide with UID '{ar.sponsor_model_vo.ig_uid}' doesn't exist.",
        )

        new_value.extends_version.connect(ig_versions[0])

        return new_value

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: DataModelIGRoot,
        library: Library,
        relationship: VersionRelationship,
        value: SponsorModelValue,
        **_kwargs,
    ) -> SponsorModelAR:
        return SponsorModelAR.from_repository_values(
            ig_uid=root.uid,
            sponsor_model_vo=SponsorModelVO.from_repository_values(
                ig_uid=root.uid,
                ig_version_number=relationship.version,
                name=value.name,
                version_number=None,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
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
