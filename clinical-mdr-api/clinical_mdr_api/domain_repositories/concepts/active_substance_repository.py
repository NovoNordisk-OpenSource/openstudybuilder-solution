from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.active_substance import (
    ActiveSubstanceRoot,
    ActiveSubstanceValue,
)
from clinical_mdr_api.domain_repositories.models.dictionary import DictionaryTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.active_substance import (
    ActiveSubstanceAR,
    ActiveSubstanceVO,
)
from clinical_mdr_api.domains.concepts.concept_base import _AggregateRootType
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.active_substance import ActiveSubstance
from common.utils import convert_to_datetime


class ActiveSubstanceRepository(ConceptGenericRepository):
    root_class = ActiveSubstanceRoot
    value_class = ActiveSubstanceValue
    return_model = ActiveSubstance

    def _create_new_value_node(self, ar: _AggregateRootType) -> VersionValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.analyte_number = ar.concept_vo.analyte_number
        value_node.short_number = ar.concept_vo.short_number
        value_node.long_number = ar.concept_vo.long_number
        value_node.inn = ar.concept_vo.inn
        value_node.save()

        if ar.concept_vo.unii_term_uid:
            value_node.has_unii_value.connect(
                DictionaryTermRoot.nodes.get(uid=ar.concept_vo.unii_term_uid)
            )

        return value_node

    def _has_data_changed(self, ar: _AggregateRootType, value: VersionValue) -> bool:
        was_parent_data_modified = super()._has_data_changed(ar=ar, value=value)

        are_props_changed = (
            ar.concept_vo.analyte_number != value.analyte_number
            or ar.concept_vo.short_number != value.short_number
            or ar.concept_vo.long_number != value.long_number
            or ar.concept_vo.inn != value.inn
        )

        are_rels_changed = False

        if (ar.concept_vo.unii_term_uid and not value.has_unii_value) or (
            not ar.concept_vo.unii_term_uid and value.has_unii_value
        ):
            are_rels_changed = True

        if (
            value.has_unii_value
            and value.has_unii_value.get().uid
            and ar.concept_vo.unii_term_uid != value.has_unii_value.get().uid
        ):
            are_rels_changed = True

        return was_parent_data_modified or are_props_changed or are_rels_changed

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> ActiveSubstanceAR:
        major, minor = input_dict.get("version").split(".")
        ar = ActiveSubstanceAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=ActiveSubstanceVO.from_repository_values(
                analyte_number=input_dict.get("analyte_number"),
                short_number=input_dict.get("short_number"),
                long_number=input_dict.get("long_number"),
                inn=input_dict.get("inn"),
                unii_term_uid=(
                    input_dict.get("unii_data").get("unii_term_uid")
                    if input_dict.get("unii_data")
                    else None
                ),
                external_id=input_dict.get("external_id"),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict.get("library_name"),
                is_library_editable_callback=(
                    lambda _: input_dict.get("is_library_editable")
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict.get("change_description"),
                status=LibraryItemStatus(input_dict.get("status")),
                author_id=input_dict.get("author_id"),
                author_username=input_dict.get("author_username"),
                start_date=convert_to_datetime(value=input_dict.get("start_date")),
                end_date=convert_to_datetime(value=input_dict.get("end_date")),
                major_version=int(major),
                minor_version=int(minor),
            ),
        )
        return ar

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> ActiveSubstanceAR:
        unii_term = value.has_unii_value.get_or_none()
        ar = ActiveSubstanceAR.from_repository_values(
            uid=root.uid,
            concept_vo=ActiveSubstanceVO.from_repository_values(
                analyte_number=value.analyte_number,
                short_number=value.short_number,
                long_number=value.long_number,
                inn=value.inn,
                external_id=value.external_id,
                unii_term_uid=unii_term.uid if unii_term else None,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )
        return ar

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name, **kwargs
    ) -> str:
        return """
            WITH *,
                concept_value.analyte_number AS analyte_number,
                concept_value.short_number AS short_number,
                concept_value.long_number AS long_number,
                concept_value.inn AS inn,
                head([(concept_value)-[:HAS_UNII_VALUE]->(unii:DictionaryTermRoot)-[:LATEST]->(unii_value:DictionaryTermValue) |
                {
                    unii_term_uid:unii.uid, 
                    unii_term_unii:unii_value.dictionary_id,
                    unii_term_name:unii_value.name
                }
                ]) AS unii_data,
                head([(concept_value)-[:HAS_UNII_VALUE]->(unii:DictionaryTermRoot)-[:LATEST]->(unii_value:DictionaryTermValue)-[:HAS_PCLASS]->(pclass_root:DictionaryTermRoot)-[:LATEST]->(pclass_value:DictionaryTermValue) |
                {
                    pclass_name:pclass_value.name,
                    pclass_id:pclass_value.dictionary_id,
                    pclass_uid:pclass_root.uid
                }
                ]) AS pclass_data

                """
