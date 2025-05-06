from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.concepts.odms.odm_generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.odm import (
    OdmStudyEventRoot,
    OdmStudyEventValue,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.odms.study_event import (
    OdmStudyEventAR,
    OdmStudyEventVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.odms.odm_study_event import OdmStudyEvent
from common.utils import convert_to_datetime


class StudyEventRepository(OdmGenericRepository[OdmStudyEventAR]):
    root_class = OdmStudyEventRoot
    value_class = OdmStudyEventValue
    return_model = OdmStudyEvent

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmStudyEventAR:
        return OdmStudyEventAR.from_repository_values(
            uid=root.uid,
            concept_vo=OdmStudyEventVO.from_repository_values(
                name=value.name,
                oid=value.oid,
                effective_date=value.effective_date,
                retired_date=value.retired_date,
                description=value.description,
                display_in_tree=value.display_in_tree,
                form_uids=[form.uid for form in root.form_ref.all()],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> _AggregateRootType:
        major, minor = input_dict.get("version").split(".")
        odm_form_ar = OdmStudyEventAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=OdmStudyEventVO.from_repository_values(
                name=input_dict.get("name"),
                oid=input_dict.get("oid"),
                effective_date=input_dict.get("effective_date"),
                retired_date=input_dict.get("retired_date"),
                description=input_dict.get("description"),
                display_in_tree=input_dict.get("display_in_tree"),
                form_uids=input_dict.get("form_uids"),
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

        return odm_form_ar

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name, **kwargs
    ) -> str:
        return f"""
WITH *,
concept_value.oid AS oid,
concept_value.effective_date AS effective_date,
concept_value.retired_date AS retired_date,
concept_value.description AS description,
concept_value.display_in_tree AS display_in_tree,

[(concept_value)<-[:{only_specific_status}]-(:OdmStudyEventRoot)-[fref:FORM_REF]->(fr:OdmFormRoot)-[:LATEST]->(fv:OdmFormValue) |
{{uid: fr.uid, name: fv.name, order: fref.order, mandatory: fref.mandatory, collection_exception_condition_oid: fref.collection_exception_condition_oid}}] AS forms

WITH *,
apoc.coll.toSet([form in forms | form.uid]) AS form_uids
"""

    def _create_new_value_node(self, ar: OdmStudyEventAR) -> OdmStudyEventValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.oid = ar.concept_vo.oid
        value_node.effective_date = ar.concept_vo.effective_date
        value_node.retired_date = ar.concept_vo.retired_date
        value_node.description = ar.concept_vo.description
        value_node.display_in_tree = ar.concept_vo.display_in_tree

        return value_node

    def _has_data_changed(self, ar: OdmStudyEventAR, value: OdmStudyEventValue) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        return (
            are_concept_properties_changed
            or ar.concept_vo.oid != value.oid
            or ar.concept_vo.oid != value.oid
            or ar.concept_vo.effective_date != value.effective_date
            or ar.concept_vo.retired_date != value.retired_date
            or ar.concept_vo.description != value.description
            or ar.concept_vo.display_in_tree != value.display_in_tree
        )
