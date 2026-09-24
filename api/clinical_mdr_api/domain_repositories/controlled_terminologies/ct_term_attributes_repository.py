from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_get_all_query_utils import (
    create_term_attributes_aggregate_instances_from_cypher_result,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_generic_repository import (
    CTTermGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermAttributesRoot,
    CTTermAttributesValue,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


class CTTermAttributesRepository(CTTermGenericRepository[CTTermAttributesAR]):
    root_class = CTTermAttributesRoot
    value_class = CTTermAttributesValue
    relationship_from_root = "has_attributes_root"

    def entity_exists_by_concept_id(
        self, entity_uid: str | None, concept_id: str | None
    ) -> bool:
        # Check if the concept_id is already in use by another term or codelist
        # We allow duplicates under the condition that the conflicting term is retired.
        if not concept_id:
            # no conflict if concept_id is not defined
            return False
        query = """
            MATCH
                (term_root:CTTermRoot WHERE $entity_uid IS NULL OR term_root.uid <> $entity_uid)-[:HAS_ATTRIBUTES_ROOT]->
                (term_ver_root:CTTermAttributesRoot)-[thv:HAS_VERSION WHERE thv.end_date IS NULL AND thv.status <> "Retired"]->
                (term_ver_value:CTTermAttributesValue {concept_id: $concept_id})
            RETURN term_root.uid as conflicting_uid
            UNION ALL
            MATCH
                (cl_root:CTCodelistRoot WHERE $entity_uid IS NULL OR cl_root.uid <> $entity_uid)-[:HAS_ATTRIBUTES_ROOT]->
                (cl_ver_root:CTCodelistAttributesRoot)-[clhv:HAS_VERSION WHERE clhv.end_date IS NULL AND clhv.status <> "Retired"]->
                (cl_ver_value:CTCodelistAttributesValue {concept_id: $concept_id})
            RETURN cl_root.uid as conflicting_uid
            """
        result, _ = db.cypher_query(
            query, {"entity_uid": entity_uid, "concept_id": concept_id}
        )
        return len(result) > 0

    def _create_aggregate_root_instance_from_cypher_result(
        self, term_dict: dict[str, Any]
    ) -> CTTermAttributesAR:
        return create_term_attributes_aggregate_instances_from_cypher_result(
            term_dict=term_dict, is_aggregated_query=False
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: CTTermAttributesRoot,
        library: Library,
        relationship: VersionRelationship,
        value: CTTermAttributesValue,
        **_kwargs,
    ) -> CTTermAttributesAR:
        ct_term_root_node = root.has_root.single()
        ct_codelist_term = ct_term_root_node.has_term_root.single()
        ct_codelist_root_node = (
            ct_codelist_term.has_term.single() if ct_codelist_term else None
        )

        catalogue_names = (
            [cat.name for cat in ct_codelist_root_node.has_codelist.all()]
            if ct_codelist_root_node
            else []
        )

        return CTTermAttributesAR.from_repository_values(
            uid=ct_term_root_node.uid,
            ct_term_attributes_vo=CTTermAttributesVO.from_repository_values(
                concept_id=value.concept_id,
                preferred_term=value.preferred_term,
                definition=value.definition,
                catalogue_names=catalogue_names,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _is_new_version_necessary(
        self, ar: CTTermAttributesAR, value: VersionValue
    ) -> bool:
        return self._has_data_changed(ar, value)

    def _get_or_create_value(
        self,
        root: CTTermAttributesRoot,
        ar: CTTermAttributesAR,
        force_new_value_node: bool = False,
    ) -> CTTermAttributesValue:
        if not force_new_value_node:
            for itm in root.has_version.filter(
                preferred_term=ar.ct_term_vo.preferred_term,
                definition=ar.ct_term_vo.definition,
                concept_id=ar.ct_term_vo.concept_id,
            ):
                return itm
            latest_draft = root.latest_draft.get_or_none()
            if latest_draft and not self._has_data_changed(ar, latest_draft):
                return latest_draft
            latest_final = root.latest_final.get_or_none()
            if latest_final and not self._has_data_changed(ar, latest_final):
                return latest_final
            latest_retired = root.latest_retired.get_or_none()
            if latest_retired and not self._has_data_changed(ar, latest_retired):
                return latest_retired

        new_value = self.value_class(
            preferred_term=ar.ct_term_vo.preferred_term,
            definition=ar.ct_term_vo.definition,
            concept_id=ar.ct_term_vo.concept_id,
        )
        self._db_save_node(new_value)
        return new_value

    def _has_data_changed(self, ar: CTTermAttributesAR, value: VersionValue):
        return (
            ar.ct_term_vo.preferred_term != value.preferred_term
            or ar.ct_term_vo.definition != value.definition
            or ar.ct_term_vo.concept_id != value.concept_id
        )

    def _create(self, item: CTTermAttributesAR) -> CTTermAttributesAR:
        """
        Creates new CTTermAttributesAR, checks possibility based on
        library setting, then creates database representation.
        Creates CTTermRoot, CTTermAttributesRoot and CTTermAttributesValue database object,
        recreates AR based on created database model and returns created AR.
        It also creates relationships to associated CTCodelistRoot and Library.
        """
        relation_data: LibraryItemMetadataVO = item.item_metadata
        root = self.root_class()
        value = self.value_class(
            preferred_term=item.ct_term_vo.preferred_term,
            definition=item.ct_term_vo.definition,
            concept_id=item.ct_term_vo.concept_id,
        )
        self._db_save_node(root)

        (
            root,
            value,
            _,
            _,
            _,
        ) = self._db_create_and_link_nodes(
            root, value, self._library_item_metadata_vo_to_datadict(relation_data)
        )

        ct_term_root_node = CTTermRoot(uid=item.uid)
        ct_term_root_node.save()
        ct_term_root_node.has_attributes_root.connect(root)

        library = self._get_library(item.library.name)
        ct_term_root_node.has_library.connect(library)

        self._maintain_parameters(item, root, value)

        return item

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass

    def is_repository_related_to_attributes(self) -> bool:
        """
        The method created to allow CTTermGenericRepository interface to handle filtering by package
        in different way for CTTermAttributesRepository and for CTTermNameRepository.
        :return:
        """
        return True
