from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.simple_concepts.numeric_value_with_unit_repository import (
    NumericValueWithUnitRepository,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    CTTermRoot,
    LagTimeRoot,
    LagTimeValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.simple_concepts.lag_time import (
    LagTimeAR,
    LagTimeVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.concept import LagTime as LagTimeAPIModel
from common.utils import convert_to_datetime


class LagTimeRepository(NumericValueWithUnitRepository):
    root_class = LagTimeRoot
    value_class = LagTimeValue
    aggregate_class = LagTimeAR
    value_object_class = LagTimeVO
    return_model = LagTimeAPIModel

    def _create_new_value_node(self, ar: LagTimeAR) -> LagTimeValue:
        value_node = super()._create_new_value_node(ar=ar)

        if ar.concept_vo.sdtm_domain_uid is not None:
            value_node.has_sdtm_domain.connect(
                CTTermRoot.nodes.get(uid=ar.concept_vo.sdtm_domain_uid)
            )

        return value_node

    def _has_data_changed(self, ar: LagTimeAR, value: LagTimeValue) -> bool:
        base_data_changed = super()._has_data_changed(ar=ar, value=value)
        additional_rels_changed = (
            ar.concept_vo.sdtm_domain_uid != value.has_sdtm_domain.get()
        )
        return base_data_changed or additional_rels_changed

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> LagTimeAR:
        major, minor = input_dict.get("version").split(".")
        return self.aggregate_class.from_repository_values(
            uid=input_dict.get("uid"),
            simple_concept_vo=self.value_object_class.from_repository_values(
                value=input_dict.get("value"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                is_template_parameter=input_dict.get("template_parameter"),
                unit_definition_uid=input_dict.get("unit_definition_uid"),
                sdtm_domain_uid=input_dict.get("sdtm_domain_uid"),
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
    ) -> LagTimeAR:
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
                sdtm_domain_uid=self._get_uid_or_none(
                    value.has_sdtm_domain.get_or_none()
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
            head([(concept_value)-[:HAS_UNIT_DEFINITION]->(unit_definition:UnitDefinitionRoot) | unit_definition.uid]) AS unit_definition_uid,
            head([(concept_value)-[:HAS_SDTM_DOMAIN]->(sdtm_domain:CTTermRoot) | sdtm_domain.uid]) AS sdtm_domain_uid
        """

    def find_uid_by_value_unit_and_domain(
        self,
        value: float,
        unit_definition_uid: str,
        sdtm_domain_uid: str,
    ) -> str | None:
        cypher_query = f"""
MATCH (or:{self.root_class.__label__})-[:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(ov:{self.value_class.__label__} {{value: $value}})
-[:HAS_UNIT_DEFINITION]->(unit_root:UnitDefinitionRoot {{uid: $unit_definition_uid}})
MATCH (ov)-[:HAS_SDTM_DOMAIN]->(term_root:CTTermRoot {{uid: $sdtm_domain_uid}})
RETURN or.uid
"""
        items, _ = db.cypher_query(
            cypher_query,
            {
                "value": value,
                "unit_definition_uid": unit_definition_uid,
                "sdtm_domain_uid": sdtm_domain_uid,
            },
        )
        if len(items) > 0:
            return items[0][0]
        return None
