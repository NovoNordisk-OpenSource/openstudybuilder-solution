from typing import Any

from clinical_mdr_api.domain_repositories.concepts.simple_concepts.simple_concept_generic_repository import (
    SimpleConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    NumericValueRoot,
    TimePointRoot,
    TimePointValue,
    UnitDefinitionRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains.concepts.simple_concepts.time_point import (
    TimePointAR,
    TimePointVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.concept import TimePoint
from common.config import settings
from common.utils import convert_to_datetime


class TimePointRepository(SimpleConceptGenericRepository[TimePointAR]):
    root_class = TimePointRoot
    value_class = TimePointValue
    return_model = TimePoint

    def _create_new_value_node(self, ar: TimePointAR) -> TimePointValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.save()

        if ar.concept_vo.unit_definition_uid is not None:
            value_node.has_unit_definition.connect(
                UnitDefinitionRoot.nodes.get(uid=ar.concept_vo.unit_definition_uid)
            )
        if ar.concept_vo.numeric_value_uid is not None:
            value_node.has_value.connect(
                NumericValueRoot.nodes.get(uid=ar.concept_vo.numeric_value_uid)
            )
        if ar.concept_vo.time_reference_uid is not None:
            term_root = CTTermRoot.nodes.get(uid=ar.concept_vo.time_reference_uid)
            selected_term_node = (
                CTCodelistAttributesRepository().get_or_create_selected_term(
                    term_root,
                    codelist_submission_value=settings.time_ref_cl_submval,
                    catalogue_name=settings.sdtm_ct_catalogue_name,
                )
            )
            value_node.has_time_reference.connect(selected_term_node)

        return value_node

    def _has_data_changed(self, ar: TimePointAR, value: TimePointValue) -> bool:
        concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        are_labels_changed = (
            ar.concept_vo.is_template_parameter != self.is_concept_node_a_tp(value)
        )

        are_rels_changed = (
            ar.concept_vo.unit_definition_uid != value.has_unit_definition.get()
            or ar.concept_vo.numeric_value_uid != value.has_value.get()
            or ar.concept_vo.time_reference_uid != value.has_time_reference.get()
        )

        return concept_properties_changed or are_rels_changed or are_labels_changed

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> TimePointAR:
        major, minor = input_dict["version"].split(".")
        return TimePointAR.from_repository_values(
            uid=input_dict["uid"],
            simple_concept_vo=TimePointVO.from_repository_values(
                name=input_dict["name"],
                name_sentence_case=input_dict.get("name_sentence_case"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                is_template_parameter=input_dict["template_parameter"],
                unit_definition_uid=input_dict["unit_definition_uid"],
                numeric_value_uid=input_dict["numeric_value_uid"],
                time_reference_uid=input_dict["time_reference_uid"],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict["library_name"],
                is_library_editable_callback=(
                    lambda _: input_dict["is_library_editable"]
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict["change_description"],
                status=LibraryItemStatus(input_dict.get("status")),
                author_id=input_dict["author_id"],
                author_username=input_dict.get("author_username"),
                start_date=convert_to_datetime(value=input_dict["start_date"]),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> TimePointAR:
        return TimePointAR.from_repository_values(
            uid=root.uid,
            simple_concept_vo=TimePointVO.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                definition=value.definition,
                abbreviation=value.abbreviation,
                is_template_parameter=self.is_concept_node_a_tp(concept_node=value),
                unit_definition_uid=value.has_unit_definition.get().uid,
                numeric_value_uid=value.has_value.get().uid,
                time_reference_uid=value.has_time_reference.get().uid,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def specific_alias_clause(self, **kwargs) -> str:
        return """
        WITH *,
            head([(concept_value)-[:HAS_UNIT_DEFINITION]->(unit_definition) | unit_definition.uid]) AS unit_definition_uid,
            head([(concept_value)-[:HAS_VALUE]->(numeric_value_root) | numeric_value_root.uid]) AS numeric_value_uid,
            head([(concept_value)-[:HAS_TIME_REFERENCE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(ct_term_root) | ct_term_root.uid]) as time_reference_uid
        """
