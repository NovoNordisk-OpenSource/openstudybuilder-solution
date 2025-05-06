from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.simple_concepts.simple_concept_generic_repository import (
    SimpleConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    NumericValueWithUnitRoot,
    NumericValueWithUnitValue,
    UnitDefinitionRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value_with_unit import (
    NumericValueWithUnitAR,
    NumericValueWithUnitVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.concept import (
    NumericValueWithUnit as NumericValueWithUnitAPIModel,
)
from common.utils import convert_to_datetime


class NumericValueWithUnitRepository(
    SimpleConceptGenericRepository[NumericValueWithUnitAR]
):
    root_class = NumericValueWithUnitRoot
    value_class = NumericValueWithUnitValue
    aggregate_class = NumericValueWithUnitAR
    value_object_class = NumericValueWithUnitVO
    return_model = NumericValueWithUnitAPIModel

    def _create_new_value_node(
        self, ar: NumericValueWithUnitAR
    ) -> NumericValueWithUnitValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.save()
        value_node.value = ar.concept_vo.value
        if ar.concept_vo.unit_definition_uid is not None:
            value_node.has_unit_definition.connect(
                UnitDefinitionRoot.nodes.get(uid=ar.concept_vo.unit_definition_uid)
            )
        return value_node

    def _has_data_changed(
        self, ar: NumericValueWithUnitAR, value: NumericValueWithUnitValue
    ) -> bool:
        concept_properties_changed = super()._has_data_changed(ar=ar, value=value)
        is_value_changed = ar.concept_vo.value != value.value
        are_labels_changed = (
            ar.concept_vo.is_template_parameter != self.is_concept_node_a_tp(value)
        )
        are_rels_changed = (
            ar.concept_vo.unit_definition_uid != value.has_unit_definition.get()
        )
        return (
            concept_properties_changed
            or are_labels_changed
            or is_value_changed
            or are_rels_changed
        )

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> NumericValueWithUnitAR:
        major, minor = input_dict.get("version").split(".")
        return self.aggregate_class.from_repository_values(
            uid=input_dict.get("uid"),
            simple_concept_vo=self.value_object_class.from_repository_values(
                value=input_dict.get("value"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                is_template_parameter=input_dict.get("template_parameter"),
                unit_definition_uid=input_dict.get("unit_definition_uid"),
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
    ) -> NumericValueWithUnitAR:
        return self.aggregate_class.from_repository_values(
            uid=root.uid,
            simple_concept_vo=self.value_object_class.from_repository_values(
                value=value.value,
                definition=value.definition,
                abbreviation=value.abbreviation,
                is_template_parameter=self.is_concept_node_a_tp(concept_node=value),
                unit_definition_uid=self._get_uid_or_none(
                    value.has_unit_definition.get_or_none()
                ),
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
            concept_value.value as value,
            head([(concept_value)-[:HAS_UNIT_DEFINITION]->(unit_definition:UnitDefinitionRoot) | unit_definition.uid]) AS unit_definition_uid
        """

    def find_uid_by_value_and_unit(
        self, value: float, unit_definition_uid: str
    ) -> str | None:
        cypher_query = f"""
MATCH (or:{self.root_class.__label__})-[:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(ov:{self.value_class.__label__} {{value: $value}})
-[:HAS_UNIT_DEFINITION]->(unit_root:UnitDefinitionRoot {{uid: $unit_definition_uid}})
RETURN or.uid
"""
        items, _ = db.cypher_query(
            cypher_query, {"value": value, "unit_definition_uid": unit_definition_uid}
        )
        if len(items) > 0:
            return items[0][0]
        return None
