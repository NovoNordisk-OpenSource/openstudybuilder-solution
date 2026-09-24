from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_generic_repository import (
    CTCodelistGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCatalogue,
    CTCodelistAttributesRoot,
    CTCodelistAttributesValue,
    CTCodelistRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
    CTCodelistAttributesVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.services.user_info import UserInfoService
from common.exceptions import BusinessLogicException
from common.utils import convert_to_datetime


class CTCodelistAttributesRepository(
    CTCodelistGenericRepository[CTCodelistAttributesAR]
):
    root_class = CTCodelistAttributesRoot
    value_class = CTCodelistAttributesValue
    relationship_from_root = "has_attributes_root"

    def codelist_specific_exists_by_uid(self, uid: str) -> bool:
        result, _ = db.cypher_query(
            "MATCH (node:CTCodelistRoot) WHERE node.uid = $uid RETURN node",
            {"uid": uid},
        )

        return len(result) > 0

    def codelist_specific_exists_by_name(self, codelist_name: str) -> bool:
        query = """
            MATCH (codelist_ver_root:CTCodelistAttributesRoot)-[:LATEST]->(codelist_ver_value:CTCodelistAttributesValue {name: $codelist_name})
            RETURN codelist_ver_value
            """
        result, _ = db.cypher_query(query, {"codelist_name": codelist_name})
        return len(result) > 0

    def codelist_attributes_exists_by_submission_value(
        self, codelist_submission_value: str
    ) -> bool:
        query = """
            MATCH (codelist_ver_root:CTCodelistAttributesRoot)-[:LATEST]->
                (codelist_ver_value:CTCodelistAttributesValue {submission_value: $codelist_submission_value})
            RETURN codelist_ver_value
            """
        result, _ = db.cypher_query(
            query, {"codelist_submission_value": codelist_submission_value}
        )
        return len(result) > 0

    def _create_aggregate_root_instance_from_cypher_result(
        self, codelist_dict: dict[str, Any]
    ) -> CTCodelistAttributesAR:
        rel_data = codelist_dict["rel_data"]
        major, minor = rel_data.get("version").split(".")

        return CTCodelistAttributesAR.from_repository_values(
            uid=codelist_dict["codelist_uid"],
            ct_codelist_attributes_vo=CTCodelistAttributesVO.from_repository_values(
                name=codelist_dict.get("value_node").get("name"),
                catalogue_names=codelist_dict.get("catalogue_names", []),
                parent_codelist_uid=codelist_dict.get("parent_codelist_uid"),
                child_codelist_uids=codelist_dict["child_codelist_uids"],
                submission_value=codelist_dict.get("value_node").get(
                    "submission_value"
                ),
                preferred_term=codelist_dict.get("value_node").get("preferred_term"),
                definition=codelist_dict.get("value_node").get("definition"),
                extensible=codelist_dict.get("value_node").get("extensible"),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=codelist_dict["library_name"],
                is_library_editable_callback=(
                    lambda _: codelist_dict["is_library_editable"]
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=rel_data.get("change_description"),
                status=LibraryItemStatus(rel_data.get("status")),
                author_id=rel_data.get("author_id"),
                author_username=UserInfoService.get_author_username_from_id(
                    rel_data.get("author_id")
                ),
                start_date=convert_to_datetime(value=rel_data.get("start_date")),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: CTCodelistAttributesRoot,
        library: Library,
        relationship: VersionRelationship,
        value: CTCodelistAttributesValue,
        **_kwargs,
    ) -> CTCodelistAttributesAR:
        ct_codelist_root_node = root.has_root.single()
        return CTCodelistAttributesAR.from_repository_values(
            uid=ct_codelist_root_node.uid,
            ct_codelist_attributes_vo=CTCodelistAttributesVO.from_repository_values(
                name=value.name,
                parent_codelist_uid=(
                    ct_codelist_root_node.has_parent_codelist.single().uid
                    if ct_codelist_root_node.has_parent_codelist.single()
                    else None
                ),
                child_codelist_uids=[
                    ct.uid for ct in ct_codelist_root_node.has_child_codelist.all()
                ],
                catalogue_names=[
                    node.name for node in ct_codelist_root_node.has_codelist.all()
                ],
                submission_value=value.submission_value,
                preferred_term=value.preferred_term,
                definition=value.definition,
                extensible=value.extensible,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _is_new_version_necessary(
        self, ar: CTCodelistAttributesAR, value: VersionValue
    ) -> bool:
        return self._has_data_changed(ar, value)

    def _get_or_create_value(
        self,
        root: CTCodelistAttributesRoot,
        ar: CTCodelistAttributesAR,
        force_new_value_node: bool = False,
    ) -> CTCodelistAttributesValue:
        if not force_new_value_node:
            for itm in root.has_version.filter(
                name=ar.name,
                submission_value=ar.ct_codelist_vo.submission_value,
                preferred_term=ar.ct_codelist_vo.preferred_term,
                definition=ar.ct_codelist_vo.definition,
                extensible=ar.ct_codelist_vo.extensible,
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
            name=ar.name,
            submission_value=ar.ct_codelist_vo.submission_value,
            preferred_term=ar.ct_codelist_vo.preferred_term,
            definition=ar.ct_codelist_vo.definition,
            extensible=ar.ct_codelist_vo.extensible,
        )
        self._db_save_node(new_value)
        return new_value

    def _has_data_changed(self, ar: CTCodelistAttributesAR, value: VersionValue):
        return (
            ar.name != value.name
            or ar.ct_codelist_vo.submission_value != value.submission_value
            or ar.ct_codelist_vo.preferred_term != value.preferred_term
            or ar.ct_codelist_vo.definition != value.definition
            or ar.ct_codelist_vo.extensible != value.extensible
        )

    def _create(self, item: CTCodelistAttributesAR) -> CTCodelistAttributesAR:
        """
        Creates new CTCodelistAttributesAR, checks possibility based on
        library setting, then creates database representation.
        Creates CTCodelistRoot, CTCodelistAttributesRoot and CTCodelistAttributesValue database object,
        recreates AR based on created database model and returns created AR.
        """
        relation_data: LibraryItemMetadataVO = item.item_metadata
        root = self.root_class()
        value = self.value_class(
            name=item.name,
            submission_value=item.ct_codelist_vo.submission_value,
            preferred_term=item.ct_codelist_vo.preferred_term,
            definition=item.ct_codelist_vo.definition,
            extensible=item.ct_codelist_vo.extensible,
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

        ct_codelist_root_node = CTCodelistRoot(uid=item.uid)
        ct_codelist_root_node.save()
        ct_codelist_root_node.has_attributes_root.connect(root)

        library = self._get_library(item.library.name)
        ct_codelist_root_node.has_library.connect(library)

        parent_codelist = CTCodelistRoot.nodes.get_or_none(
            uid=item._ct_codelist_attributes_vo.parent_codelist_uid
        )
        if parent_codelist:
            ct_codelist_root_node.has_parent_codelist.connect(parent_codelist)

        for catalogue_name in item.ct_codelist_vo.catalogue_names:
            ct_catalogue_node = CTCatalogue.nodes.get_or_none(name=catalogue_name)
            if ct_catalogue_node is None:
                raise BusinessLogicException(
                    msg=f"Catalogue with name {catalogue_name} does not exist."
                )
            ct_codelist_root_node.has_codelist.connect(ct_catalogue_node)

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
        return True
