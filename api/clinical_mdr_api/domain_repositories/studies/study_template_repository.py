from typing import Any, cast

from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.study_template import (
    StudyTemplateRoot,
    StudyTemplateValue,
)
from clinical_mdr_api.domains.enums import LibraryItemStatus
from clinical_mdr_api.domains.study_definition_aggregates.study_template import (
    StudyTemplateAR,
    StudyTemplateValueVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemMetadataVO


class StudyTemplateRepository(LibraryItemRepositoryImplBase):
    root_class = StudyTemplateRoot
    value_class = StudyTemplateValue
    user: str
    has_library = False

    def generate_uid(self) -> str:
        return self.root_class.get_next_free_uid_and_increment_counter()

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> StudyTemplateAR:
        ar_root = cast(StudyTemplateRoot, root)
        ar_value = cast(StudyTemplateValue, value)
        return StudyTemplateAR.from_repository_values(
            uid=ar_root.uid,
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            study_template_value=StudyTemplateValueVO.from_repository_values(
                study_uid=ar_value.study_uid,
                study_value_version=ar_value.study_value_version,
            ),
        )

    def _are_changes_possible(
        self,
        versioned_object: Any,
        previous_versioned_object: Any,
    ) -> bool:
        """
        Allow persisting PATCHed template target during FINAL/RETIRED states.

        The base `LibraryItemRepositoryImplBase` only allows value-node changes for
        DRAFT->DRAFT transitions. For Study templates, PATCH creates a new version
        and then approves back to FINAL, while the template item's status ends up
        FINAL->FINAL. We must allow a new value node when the target study reference
        (uid/version) changes.
        """

        new_status = versioned_object.item_metadata.status
        prev_status = previous_versioned_object.item_metadata.status

        if (
            prev_status == LibraryItemStatus.DRAFT
            and new_status == LibraryItemStatus.DRAFT
        ):
            return True

        if new_status == LibraryItemStatus.FINAL and prev_status in [
            LibraryItemStatus.FINAL,
            LibraryItemStatus.RETIRED,
        ]:
            prev_value = cast(StudyTemplateAR, previous_versioned_object).value
            new_value = cast(StudyTemplateAR, versioned_object).value
            return (
                prev_value.study_uid != new_value.study_uid
                or prev_value.study_value_version != new_value.study_value_version
            )

        return False

    def _maintain_parameters(
        self,
        versioned_object: Any,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:
        pass

    def _get_or_create_value(
        self, root: VersionRoot, ar: StudyTemplateAR, force_new_value_node: bool = False
    ) -> VersionValue:
        value = StudyTemplateValue(
            study_uid=ar.value.study_uid,
            study_value_version=ar.value.study_value_version,
        )
        self._db_save_node(node=value)
        return value

    def _is_new_version_necessary(
        self, ar: StudyTemplateAR, value: VersionValue
    ) -> bool:
        template_value = cast(StudyTemplateValue, value)
        return (
            template_value.study_uid != ar.value.study_uid
            or template_value.study_value_version != ar.value.study_value_version
        )

    def _create(self, item: StudyTemplateAR) -> StudyTemplateAR:
        relation_data: LibraryItemMetadataVO = item.item_metadata
        root = self.root_class(uid=item.uid)
        self._db_save_node(root)

        value = self._get_or_create_value(root=root, ar=item)
        root, value, _, _, _ = self._db_create_and_link_nodes(
            root, value, self._library_item_metadata_vo_to_datadict(relation_data)
        )
        self._maintain_parameters(item, root, value)
        return item
