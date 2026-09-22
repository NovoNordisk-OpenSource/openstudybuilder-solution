from datetime import datetime

from neomodel import db

from clinical_mdr_api.domain_repositories.biomedical_concepts.activity_instance_class_repository import (
    ActivityInstanceClassRepository,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
    ActivityInstanceClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
    ActivityInstanceClassDetail,
    ActivityInstanceClassEditInput,
    ActivityInstanceClassInput,
    ActivityInstanceClassMappingInput,
    ActivityInstanceClassOverview,
    ActivityInstanceClassVersion,
    ActivityInstanceClassWithDataset,
    ActivityInstanceParentClassOverview,
    CompactActivityInstanceClass,
    SimpleActivityInstanceClass,
    SimpleActivityItemClass,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.services._utils import ensure_transaction
from clinical_mdr_api.services.neomodel_ext_generic import NeomodelExtGenericService
from common.config import settings
from common.exceptions import BusinessLogicException, NotFoundException
from common.utils import version_string_to_tuple


class ActivityInstanceClassService(NeomodelExtGenericService[ActivityInstanceClassAR]):
    repository_interface = ActivityInstanceClassRepository
    api_model_class = ActivityInstanceClass
    version_class = ActivityInstanceClassVersion

    @ensure_transaction(db)
    def get_all_item_versions(
        self,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
    ) -> GenericFilteringReturn[ActivityInstanceClass]:
        items, total = self.repository.find_all_versions(
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            total_count=total_count,
        )
        return GenericFilteringReturn(items=items, total=total)

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityInstanceClassAR
    ) -> ActivityInstanceClass:
        return ActivityInstanceClass.from_activity_instance_class_ar(
            activity_instance_class_ar=item_ar,
            get_parent_class=self._repos.activity_instance_class_repository.get_parent_class,
        )

    def _create_aggregate_root(
        self, item_input: ActivityInstanceClassInput, library: LibraryVO
    ) -> ActivityInstanceClassAR:
        return ActivityInstanceClassAR.from_input_values(
            author_id=self.author_id,
            activity_instance_class_vo=ActivityInstanceClassVO.from_repository_values(
                name=item_input.name or "",
                order=item_input.order,
                definition=item_input.definition,
                is_domain_specific=item_input.is_domain_specific,
                level=item_input.level,
                nci_concept_id=item_input.nci_concept_id,
                nci_concept_name=item_input.nci_concept_name,
                dataset_class_uid=item_input.dataset_class_uid,
                activity_item_classes=[],
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            activity_instance_class_exists_by_name_callback=self._repos.activity_instance_class_repository.check_exists_by_name,
            dataset_class_exists_by_uid=self._repos.dataset_class_repository.find_by_uid,  # type: ignore[arg-type]
        )

    def _edit_aggregate(
        self,
        item: ActivityInstanceClassAR,
        item_edit_input: ActivityInstanceClassEditInput,
    ) -> ActivityInstanceClassAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=item_edit_input.change_description,
            activity_instance_class_vo=ActivityInstanceClassVO.from_repository_values(
                name=item_edit_input.name or item.activity_instance_class_vo.name,
                order=item_edit_input.order,
                definition=item_edit_input.definition,
                is_domain_specific=item_edit_input.is_domain_specific,
                level=item_edit_input.level,
                nci_concept_id=item_edit_input.nci_concept_id,
                nci_concept_name=item_edit_input.nci_concept_name,
                dataset_class_uid=item_edit_input.dataset_class_uid,
                activity_item_classes=[],
            ),
            activity_instance_class_exists_by_name_callback=self._repos.activity_instance_class_repository.check_exists_by_name,
            dataset_class_exists_by_uid=self._repos.dataset_class_repository.find_by_uid,  # type: ignore[arg-type]
        )
        return item

    def patch_mappings(
        self, uid: str, mapping_input: ActivityInstanceClassMappingInput
    ) -> ActivityInstanceClass:
        activity_instance_class = (
            self._repos.activity_instance_class_repository.find_by_uid(uid)
        )

        NotFoundException.raise_if_not(
            activity_instance_class, "Activity Instance Class", uid
        )

        try:
            self._repos.activity_instance_class_repository.patch_mappings(
                uid, mapping_input.dataset_class_uid
            )
        finally:
            self._repos.activity_instance_class_repository.close()

        return self.get_by_uid(uid)

    def get_mapped_datasets(
        self,
        activity_instance_class_uid: str | None = None,
        ig_uid: str | None = None,
        include_sponsor: bool = True,
    ) -> list[ActivityInstanceClassWithDataset]:
        mapped_datasets = (
            self._repos.activity_instance_class_repository.get_mapped_datasets(
                activity_instance_class_uid=activity_instance_class_uid,
                ig_uid=ig_uid,
                include_sponsor=include_sponsor,
            )
        )

        return mapped_datasets

    @ensure_transaction(db)
    def create(self, item_input: ActivityInstanceClassInput) -> ActivityInstanceClass:
        rs = super().create(item_input=item_input)

        self.update_parent(rs.uid, item_input.parent_uid)

        return self.get_by_uid(rs.uid)

    @ensure_transaction(db)
    def edit_draft(
        self, uid: str, item_edit_input: ActivityInstanceClassEditInput
    ) -> ActivityInstanceClass:
        self._find_by_uid_or_raise_not_found(uid=uid, for_update=False)

        self.update_parent(uid, item_edit_input.parent_uid)

        return super().edit_draft(uid=uid, item_edit_input=item_edit_input)

    @ensure_transaction(db)
    def update_parent(self, uid: str, parent_uid: str | None = None):
        BusinessLogicException.raise_if(
            parent_uid
            and not self._repos.activity_instance_class_repository.check_exists_final_version(
                parent_uid
            ),
            msg=f"Activity Instance Class tried to connect to non-existent or non-final Activity Instance Class with UID '{parent_uid}'.",
        )

        self._repos.activity_instance_class_repository.update_parent(parent_uid, uid)

    def get_by_uid(
        self,
        uid: str,
        version: str | None = None,
        at_specific_date: datetime | None = None,
        status: LibraryItemStatus | None = None,
    ) -> ActivityInstanceClass:
        """Get an activity instance class by UID with optional version."""
        item = self._find_by_uid_or_raise_not_found(
            uid=uid, version=version, at_specific_date=at_specific_date, status=status
        )
        return self._transform_aggregate_root_to_pydantic_model(item)

    def _find_by_uid_or_raise_not_found(  # pylint: disable=arguments-renamed
        self,
        uid: str,
        version: str | None = None,
        at_specific_date: datetime | None = None,
        status: LibraryItemStatus | None = None,
        for_update: bool = False,
    ) -> ActivityInstanceClassAR:
        """Find an activity instance class by UID with optional version."""
        item = self.repository.find_by_uid_2(
            uid=uid,
            version=version,
            at_specific_date=at_specific_date,
            status=status,
            for_update=for_update,
        )

        NotFoundException.raise_if(
            item is None,
            "Activity Instance Class",
            f"{uid} (version: {version or 'latest'})",
        )

        return item

    def _sort_semantic_versions(
        self, versions: list[str], reverse: bool = True
    ) -> list[str]:
        """Sort semantic version strings properly (e.g., '2.0' before '10.0')."""
        return sorted(versions, key=version_string_to_tuple, reverse=reverse)

    def get_parent_class_overview(
        self, parent_class_uid: str, version: str | None = None
    ) -> ActivityInstanceParentClassOverview:
        """
        Get a complete overview of an activity instance parent class including details,
        child classes, item classes, and version history.

        Args:
            parent_class_uid: The UID of the parent activity instance class
            version: Optional specific version, or None for latest

        Returns:
            ActivityInstanceParentClassOverview object with complete parent class information
        """
        # Get the parent class details with specific version
        parent_class_ar = self._find_by_uid_or_raise_not_found(
            uid=parent_class_uid, version=version, for_update=False
        )

        # Check if this class actually has child classes (structural check)
        # Use ignore_parent_version=True to check if PARENT_CLASS relationships exist
        child_classes_data, _ = (
            self._repos.activity_instance_class_repository.get_child_instance_classes(
                parent_class_uid,
                version=None,
                page_size=1,
                total_count=False,
                ignore_parent_version=True,
            )
        )
        if not child_classes_data:
            NotFoundException.raise_if(
                True,
                "Activity Instance Parent Class",
                f"{parent_class_uid} is not a parent class (has no child classes)",
            )

        # Transform to detail model
        parent_class_detail = ActivityInstanceClassDetail(
            uid=parent_class_ar.uid,
            name=parent_class_ar.name,
            definition=parent_class_ar.activity_instance_class_vo.definition,
            is_domain_specific=parent_class_ar.activity_instance_class_vo.is_domain_specific
            or False,
            level=parent_class_ar.activity_instance_class_vo.level,
            nci_concept_id=parent_class_ar.activity_instance_class_vo.nci_concept_id,
            nci_concept_name=parent_class_ar.activity_instance_class_vo.nci_concept_name,
            library_name=(
                parent_class_ar.library.name if parent_class_ar.library else None
            ),
            start_date=(
                parent_class_ar.item_metadata.start_date.isoformat()
                if parent_class_ar.item_metadata.start_date
                else None
            ),
            end_date=(
                parent_class_ar.item_metadata.end_date.isoformat()
                if parent_class_ar.item_metadata.end_date
                else None
            ),
            status=parent_class_ar.item_metadata.status.value,
            version=parent_class_ar.item_metadata.version,
            change_description=parent_class_ar.item_metadata.change_description,
            author_username=parent_class_ar.item_metadata.author_username,
            hierarchy=self._get_hierarchy_string(parent_class_ar),
            parent_class=self._get_parent_class_info(parent_class_ar),
        )

        # Get all versions
        all_versions = (
            self._repos.activity_instance_class_repository.get_all_version_numbers(
                parent_class_uid
            )
        )
        all_versions = self._sort_semantic_versions(all_versions, reverse=True)

        return ActivityInstanceParentClassOverview(
            parent_activity_instance_class=parent_class_detail,
            all_versions=all_versions,
        )

    def get_activity_instance_class_overview(
        self, activity_instance_class_uid: str, version: str | None = None
    ) -> ActivityInstanceClassOverview:
        """
        Get a complete overview of an activity instance class including details,
        item classes, and version history.

        Args:
            activity_instance_class_uid: The UID of the activity instance class
            version: Optional specific version, or None for latest

        Returns:
            ActivityInstanceClassOverview object with complete class information
        """
        # Get the class details with specific version
        class_ar = self._find_by_uid_or_raise_not_found(
            uid=activity_instance_class_uid, version=version, for_update=False
        )

        # Transform to detail model
        class_detail = ActivityInstanceClassDetail(
            uid=class_ar.uid,
            name=class_ar.name,
            definition=class_ar.activity_instance_class_vo.definition,
            is_domain_specific=class_ar.activity_instance_class_vo.is_domain_specific
            or False,
            level=class_ar.activity_instance_class_vo.level,
            nci_concept_id=class_ar.activity_instance_class_vo.nci_concept_id,
            nci_concept_name=class_ar.activity_instance_class_vo.nci_concept_name,
            library_name=class_ar.library.name if class_ar.library else None,
            start_date=(
                class_ar.item_metadata.start_date.isoformat()
                if class_ar.item_metadata.start_date
                else None
            ),
            end_date=(
                class_ar.item_metadata.end_date.isoformat()
                if class_ar.item_metadata.end_date
                else None
            ),
            status=class_ar.item_metadata.status.value,
            version=class_ar.item_metadata.version,
            change_description=class_ar.item_metadata.change_description,
            author_username=class_ar.item_metadata.author_username,
            hierarchy=self._get_hierarchy_string(class_ar),
            parent_class=self._get_parent_class_info(class_ar),
        )

        # Get all versions
        all_versions = (
            self._repos.activity_instance_class_repository.get_all_version_numbers(
                activity_instance_class_uid
            )
        )
        all_versions = self._sort_semantic_versions(all_versions, reverse=True)

        return ActivityInstanceClassOverview(
            activity_instance_class=class_detail,
            all_versions=all_versions,
        )

    def _get_hierarchy_string(self, class_ar: ActivityInstanceClassAR) -> str | None:
        """Build hierarchy string for display (e.g., 'General Observation/Subject Observation/Finding')"""
        # Build the hierarchy path from root to parent (not including current class)
        hierarchy_parts: list[str] = []
        current_uid = class_ar.uid

        # Walk up the hierarchy to build the path
        while True:
            parent_info = (
                self._repos.activity_instance_class_repository.get_parent_class(
                    current_uid
                )
            )
            if not parent_info:
                # No parent means we've reached the root
                break
            parent_uid, parent_name = parent_info
            hierarchy_parts.insert(0, parent_name)  # Add parent to beginning of list
            current_uid = parent_uid

        # Return the hierarchy path (without current class name)
        if len(hierarchy_parts) == 0:
            # This class has no parents (it's a root class)
            return "No Parent"
        # Join all parts with '/'
        return "/".join(hierarchy_parts)

    def _get_parent_class_info(
        self, class_ar: ActivityInstanceClassAR
    ) -> CompactActivityInstanceClass | None:
        """Get parent class information if exists"""
        parent_info = self._repos.activity_instance_class_repository.get_parent_class(
            class_ar.uid
        )
        if parent_info:
            parent_uid, parent_name = parent_info
            return CompactActivityInstanceClass(uid=parent_uid, name=parent_name)
        return None

    def get_child_instance_classes_paginated(
        self,
        parent_uid: str,
        version: str | None = None,
        page_number: int = 1,
        page_size: int = 10,
        total_count: bool = False,
        sort_by: dict[str, bool] | None = None,
    ) -> GenericFilteringReturn[SimpleActivityInstanceClass]:
        """Get paginated child activity instance classes for a parent class."""
        child_classes_data, total = (
            self._repos.activity_instance_class_repository.get_child_instance_classes(
                parent_uid,
                version=version,
                page_number=page_number,
                page_size=page_size,
                total_count=total_count,
                sort_by=sort_by,
            )
        )

        child_classes = []
        for child in child_classes_data:
            child_classes.append(
                SimpleActivityInstanceClass(
                    uid=child["uid"],
                    name=child["name"],
                    definition=child.get("definition"),
                    is_domain_specific=(
                        bool(child.get("is_domain_specific"))
                        if child.get("is_domain_specific") is not None
                        else False
                    ),
                    library_name=child.get("library_name")
                    or settings.sponsor_library_name,
                    modified_date=(
                        child["modified_date"].isoformat()
                        if child.get("modified_date")
                        else None
                    ),
                    modified_by=child.get("modified_by") or "unknown",
                    version=child.get("version") or "1.0",
                    status=child.get("status") or "Final",
                )
            )
        return GenericFilteringReturn(items=child_classes, total=total)

    def get_activity_item_classes_paginated(
        self,
        activity_instance_class_uid: str,
        version: str | None = None,
        page_number: int = 1,
        page_size: int = 10,
        total_count: bool = False,
        sort_by: dict[str, bool] | None = None,
    ) -> GenericFilteringReturn[SimpleActivityItemClass]:
        """Get paginated activity item classes for an activity instance class."""
        item_classes_data, total = (
            self._repos.activity_instance_class_repository.get_activity_item_classes(
                activity_instance_class_uid,
                version=version,
                page_number=page_number,
                page_size=page_size,
                total_count=total_count,
                sort_by=sort_by,
            )
        )

        item_classes = []
        for item in item_classes_data:
            item_classes.append(
                SimpleActivityItemClass(
                    uid=item["uid"],
                    name=item["name"],
                    parent_name=item.get("parent_name"),
                    parent_uid=item.get("parent_uid"),
                    definition=item.get("definition"),
                    modified_date=(
                        item["modified_date"].isoformat()
                        if item.get("modified_date")
                        else None
                    ),
                    modified_by=item.get("modified_by", "unknown"),
                    version=item.get("version", "1.0"),
                    status=item.get("status", "Final"),
                )
            )
        return GenericFilteringReturn(items=item_classes, total=total)

    def _get_child_instance_classes(
        self, parent_uid: str, version: str | None = None
    ) -> list[SimpleActivityInstanceClass]:
        """Get all child activity instance classes for a parent at a specific version"""
        # Use the paginated method with page_size=0 to get all items
        child_classes_data, _ = (
            self._repos.activity_instance_class_repository.get_child_instance_classes(
                parent_uid, version=version, page_size=0
            )
        )

        child_classes = []
        for child in child_classes_data:
            child_classes.append(
                SimpleActivityInstanceClass(
                    uid=child["uid"],
                    name=child["name"],
                    definition=child.get("definition"),
                    is_domain_specific=(
                        bool(child.get("is_domain_specific"))
                        if child.get("is_domain_specific") is not None
                        else False
                    ),
                    library_name=child.get("library_name")
                    or settings.sponsor_library_name,
                    modified_date=(
                        child["modified_date"].isoformat()
                        if child.get("modified_date")
                        else None
                    ),
                    modified_by=child.get("modified_by") or "unknown",
                    version=child.get("version") or "1.0",
                    status=child.get("status") or "Final",
                )
            )
        return child_classes

    def _get_activity_item_classes(
        self, activity_instance_class_uid: str, version: str | None = None
    ) -> list[SimpleActivityItemClass]:
        """Get all activity item classes for an activity instance class at a specific version"""
        # Use the paginated method with page_size=0 to get all items
        item_classes_data, _ = (
            self._repos.activity_instance_class_repository.get_activity_item_classes(
                activity_instance_class_uid, version=version, page_size=0
            )
        )

        item_classes = []
        for item in item_classes_data:
            item_classes.append(
                SimpleActivityItemClass(
                    uid=item["uid"],
                    name=item["name"],
                    parent_name=item.get("parent_name"),
                    definition=item.get("definition"),
                    modified_date=(
                        item["modified_date"].isoformat()
                        if item.get("modified_date")
                        else None
                    ),
                    modified_by=item.get("modified_by", "unknown"),
                    version=item.get("version", "1.0"),
                    status=item.get("status", "Final"),
                )
            )
        return item_classes
