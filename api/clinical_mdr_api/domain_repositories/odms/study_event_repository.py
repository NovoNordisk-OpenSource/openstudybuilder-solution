from textwrap import dedent
from typing import Any

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
from clinical_mdr_api.domain_repositories.odms.generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domains.odms.study_event import OdmStudyEventAR, OdmStudyEventVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.odms.study_event import OdmStudyEvent
from common.utils import convert_to_datetime


class StudyEventRepository(OdmGenericRepository[OdmStudyEventAR]):
    root_class = OdmStudyEventRoot
    value_class = OdmStudyEventValue
    return_model = OdmStudyEvent

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmStudyEventAR:
        return OdmStudyEventAR.from_repository_values(
            uid=root.uid,
            odm_vo=OdmStudyEventVO.from_repository_values(
                name=value.name,
                oid=value.oid,
                effective_date=value.effective_date,
                retired_date=value.retired_date,
                description=value.description,
                display_in_tree=value.display_in_tree,
                form_uids=[
                    form_root.uid
                    for form_value in value.form_ref.all()
                    if (form_root := form_value.has_root.single())
                ],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> OdmStudyEventAR:
        major, minor = input_dict["version"].split(".")
        odm_form_ar = OdmStudyEventAR.from_repository_values(
            uid=input_dict["uid"],
            odm_vo=OdmStudyEventVO.from_repository_values(
                name=input_dict["name"],
                oid=input_dict.get("oid"),
                effective_date=input_dict.get("effective_date"),
                retired_date=input_dict.get("retired_date"),
                description=input_dict.get("description"),
                display_in_tree=input_dict["display_in_tree"],
                form_uids=input_dict["form_uids"],
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

        return odm_form_ar

    def _get_specific_field_mapping(self) -> dict[str, str]:
        """Study Event specific field mappings - simple fields only."""
        return {
            "name": "odm_value.name AS name",
            "oid": "odm_value.oid AS oid",
            "description": "odm_value.description AS description",
            "effective_date": "odm_value.effective_date AS effective_date",
            "retired_date": "odm_value.retired_date AS retired_date",
            "display_in_tree": "odm_value.display_in_tree AS display_in_tree",
        }

    def _get_computed_field_expressions(self) -> dict[str, str]:
        """Study Event computed field expressions."""
        # pylint: disable=line-too-long
        return {
            "forms": "[(odm_value)-[fref:FORM_REF]->(fv:OdmFormValue)<-[hv:HAS_VERSION]-(fr:OdmFormRoot) | {uid: fr.uid, oid: fv.oid, name: fv.name, order_number: fref.order_number, mandatory: fref.mandatory, locked: fref.locked, collection_exception_condition_oid: fref.collection_exception_condition_oid, version:hv.version}] AS forms",
        }

    def specific_alias_clause(self, **kwargs) -> str:
        return dedent(
            "WITH *,"
            + ", ".join(self._get_specific_field_mapping().values())
            + ","
            + ", ".join(self._get_computed_field_expressions().values())
            + """
            WITH *,
            apoc.coll.toSet([form in forms | form.uid]) AS form_uids
            """
        )

    def _get_or_create_value(
        self, root: VersionRoot, ar: OdmStudyEventAR, force_new_value_node: bool = False
    ) -> VersionValue:
        current_latest = root.has_latest_value.single()
        old_form_ref_nodes = current_latest.form_ref.all() if current_latest else []
        new_form_ref_nodes = [
            old_form_root.has_latest_value.single()
            for old_form_ref_node in old_form_ref_nodes
            if (old_form_root := old_form_ref_node.has_root.single())
        ]

        new_value = super()._get_or_create_value(root, ar, force_new_value_node)

        for old_form_ref_node, new_form_ref_node in zip(
            old_form_ref_nodes, new_form_ref_nodes
        ):
            params = current_latest.form_ref.relationship(old_form_ref_node)
            new_value.form_ref.connect(
                new_form_ref_node,
                {
                    "order_number": params.order_number,
                    "mandatory": params.mandatory,
                    "locked": params.locked,
                    "collection_exception_condition_oid": params.collection_exception_condition_oid,
                },
            )

        if ar.should_disconnect_relationships:
            for old_form_ref_node in old_form_ref_nodes:
                current_latest.form_ref.disconnect(old_form_ref_node)

        return new_value

    def _create_new_value_node(self, ar: OdmStudyEventAR) -> OdmStudyEventValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.oid = ar.odm_vo.oid
        value_node.effective_date = ar.odm_vo.effective_date
        value_node.retired_date = ar.odm_vo.retired_date
        value_node.description = ar.odm_vo.description
        value_node.display_in_tree = ar.odm_vo.display_in_tree

        return value_node

    def _has_data_changed(self, ar: OdmStudyEventAR, value: OdmStudyEventValue) -> bool:
        are_odm_properties_changed = super()._has_data_changed(ar=ar, value=value)

        return (
            are_odm_properties_changed
            or ar.odm_vo.oid != value.oid
            or ar.odm_vo.effective_date != value.effective_date
            or ar.odm_vo.retired_date != value.retired_date
            or ar.odm_vo.description != value.description
            or ar.odm_vo.display_in_tree != value.display_in_tree
        )
