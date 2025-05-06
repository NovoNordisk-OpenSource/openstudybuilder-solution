from clinical_mdr_api.domain_repositories.concepts.simple_concepts.simple_concept_generic_repository import (
    SimpleConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    NumericValue,
    NumericValueRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
    NumericValueVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.concept import (
    NumericValue as NumericValueAPIModel,
)
from common.utils import convert_to_datetime


class NumericValueRepository(SimpleConceptGenericRepository[NumericValueAR]):
    root_class = NumericValueRoot
    value_class = NumericValue
    aggregate_class = NumericValueAR
    value_object_class = NumericValueVO
    return_model = NumericValueAPIModel

    def _create_new_value_node(self, ar: NumericValueAR) -> NumericValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.save()
        value_node.value = ar.concept_vo.value
        return value_node

    def _has_data_changed(self, ar: NumericValueAR, value: NumericValue) -> bool:
        concept_properties_changed = super()._has_data_changed(ar=ar, value=value)
        is_value_changed = ar.concept_vo.value != value.value
        are_labels_changed = (
            ar.concept_vo.is_template_parameter != self.is_concept_node_a_tp(value)
        )
        return concept_properties_changed or are_labels_changed or is_value_changed

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> NumericValueAR:
        major, minor = input_dict.get("version").split(".")
        return self.aggregate_class.from_repository_values(
            uid=input_dict.get("uid"),
            simple_concept_vo=self.value_object_class.from_repository_values(
                name=input_dict.get("name"),
                name_sentence_case=input_dict.get("name_sentence_case"),
                value=input_dict.get("value"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                is_template_parameter=input_dict.get("template_parameter"),
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
    ) -> NumericValueAR:
        return self.aggregate_class.from_repository_values(
            uid=root.uid,
            simple_concept_vo=self.value_object_class.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                value=value.value,
                definition=value.definition,
                abbreviation=value.abbreviation,
                is_template_parameter=self.is_concept_node_a_tp(concept_node=value),
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
            concept_value.value as value
        """
