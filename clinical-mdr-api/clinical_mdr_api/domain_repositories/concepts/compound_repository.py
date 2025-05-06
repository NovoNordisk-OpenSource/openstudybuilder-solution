from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.compounds import (
    CompoundRoot,
    CompoundValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.compound import CompoundAR, CompoundVO
from clinical_mdr_api.domains.concepts.concept_base import _AggregateRootType
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.compound import Compound
from common.utils import convert_to_datetime


class CompoundRepository(ConceptGenericRepository):
    root_class = CompoundRoot
    value_class = CompoundValue
    return_model = Compound

    def _create_new_value_node(self, ar: _AggregateRootType) -> VersionValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.is_sponsor_compound = ar.concept_vo.is_sponsor_compound
        value_node.save()

        return value_node

    def _has_data_changed(self, ar: _AggregateRootType, value: VersionValue) -> bool:
        was_parent_data_modified = super()._has_data_changed(ar=ar, value=value)

        are_props_changed = (
            ar.concept_vo.is_sponsor_compound != value.is_sponsor_compound
        )
        return was_parent_data_modified or are_props_changed

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> CompoundAR:
        major, minor = input_dict.get("version").split(".")
        return CompoundAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=CompoundVO.from_repository_values(
                name=input_dict.get("name"),
                name_sentence_case=input_dict.get("name_sentence_case"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                is_sponsor_compound=input_dict.get("is_sponsor_compound"),
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
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> CompoundAR:
        return CompoundAR.from_repository_values(
            uid=root.uid,
            concept_vo=CompoundVO.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                definition=value.definition,
                abbreviation=value.abbreviation,
                is_sponsor_compound=value.is_sponsor_compound,
                external_id=value.external_id,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name, **kwargs
    ) -> str:
        return """
            WITH *,            
                concept_value.is_sponsor_compound AS is_sponsor_compound
            """
