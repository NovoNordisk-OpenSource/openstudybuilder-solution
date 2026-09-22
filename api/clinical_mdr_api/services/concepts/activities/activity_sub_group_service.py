import logging
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.activities.activity_sub_group_repository import (
    ActivitySubGroupRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
    ActivitySubGroupVO,
)
from clinical_mdr_api.domains.enums import LibraryItemStatus
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityEditInput,
    ActivityGrouping,
)
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivityGroupForActivitySubGroup,
    ActivitySubGroup,
    ActivitySubGroupCreateInput,
    ActivitySubGroupDetail,
    ActivitySubGroupEditInput,
    ActivitySubGroupOverview,
    ActivitySubGroupVersion,
)
from clinical_mdr_api.models.utils import BaseModel, CustomPage, GenericFilteringReturn
from clinical_mdr_api.services._utils import ensure_transaction
from clinical_mdr_api.services.concepts.activities.activity_service import (
    ActivityService,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
)
from common import exceptions
from common.utils import sanitize_for_log

logger = logging.getLogger(__name__)


class ActivitySubGroupService(ConceptGenericService[ActivitySubGroupAR]):
    aggregate_class = ActivitySubGroupAR
    repository_interface = ActivitySubGroupRepository
    version_class = ActivitySubGroupVersion

    def _transform_aggregate_root_to_pydantic_model(
        self,
        item_ar: ActivitySubGroupAR,
    ) -> ActivitySubGroup:
        return ActivitySubGroup.from_activity_ar(
            activity_subgroup_ar=item_ar,
        )

    def _create_aggregate_root(
        self, concept_input: ActivitySubGroupCreateInput, library
    ) -> ActivitySubGroupAR:
        return ActivitySubGroupAR.from_input_values(
            author_id=self.author_id,
            concept_vo=ActivitySubGroupVO.from_repository_values(
                name=concept_input.name,
                name_sentence_case=concept_input.name_sentence_case,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                nci_concept_id=concept_input.nci_concept_id,
                nci_concept_name=concept_input.nci_concept_name,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_library_and_name_callback=self._repos.activity_subgroup_repository.latest_concept_in_library_exists_by_name,
        )

    def _edit_aggregate(
        self,
        item: ActivitySubGroupAR,
        concept_edit_input: ActivitySubGroupEditInput,
    ) -> ActivitySubGroupAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=ActivitySubGroupVO.from_repository_values(
                name=concept_edit_input.name,
                name_sentence_case=concept_edit_input.name_sentence_case,
                definition=concept_edit_input.definition,
                abbreviation=concept_edit_input.abbreviation,
                nci_concept_id=concept_edit_input.nci_concept_id,
                nci_concept_name=concept_edit_input.nci_concept_name,
            ),
            concept_exists_by_library_and_name_callback=self._repos.activity_subgroup_repository.latest_concept_in_library_exists_by_name,
        )
        return item

    def get_subgroup_overview(
        self, subgroup_uid: str, version: str | None = None
    ) -> ActivitySubGroupOverview:
        subgroup = self.get_by_uid(subgroup_uid, version=version)
        # Get all versions and deduplicate by version number for the overview
        version_history = self.get_version_history(subgroup_uid)
        all_versions = []
        for version_item in version_history:
            if version_item.version not in all_versions:
                all_versions.append(version_item.version)

        # Get UIDs and versions of activity groups linked to this subgroup at this specific version point
        linked_activity_group_data = (
            self._repos.activity_subgroup_repository.get_linked_activity_group_uids(
                subgroup_uid=subgroup_uid, version=subgroup.version
            )
        )
        logger.debug(
            "Linked activity group data for subgroup %s version %s: %s",
            sanitize_for_log(subgroup_uid),
            subgroup.version,
            linked_activity_group_data,
        )

        activity_subgroup_detail = ActivitySubGroupDetail(
            name=subgroup.name,
            name_sentence_case=subgroup.name_sentence_case,
            nci_concept_id=subgroup.nci_concept_id,
            nci_concept_name=subgroup.nci_concept_name,
            library_name=subgroup.library_name,
            definition=subgroup.definition,
            start_date=subgroup.start_date,
            end_date=subgroup.end_date,
            status=subgroup.status,
            version=subgroup.version,
            possible_actions=subgroup.possible_actions,
            change_description=subgroup.change_description,
            author_username=subgroup.author_username,
        )

        result = ActivitySubGroupOverview(
            activity_subgroup=activity_subgroup_detail,
            all_versions=all_versions,
        )
        return result

    def get_activities_for_subgroup(
        self,
        subgroup_uid: str,
        version: str | None = None,
        search_string: str = "",
        page_number: int = 1,
        page_size: int = 10,
        total_count: bool = False,
    ):
        """
        Get activities linked to a specific activity subgroup version with pagination.

        Args:
            subgroup_uid: The UID of the activity subgroup
            version: Optional specific version, or None for latest
            search_string: Optional search string to filter activities by name or other fields
            page_number: The page number for pagination (starting from 1)
            page_size: The number of items per page
            total_count: Whether to calculate the total count

        Returns:
            GenericFilteringReturn containing SimpleActivity objects linked to the activity subgroup
        """
        # Get the specific version of the subgroup to ensure it exists
        subgroup_ar = self.get_by_uid(subgroup_uid, version=version)

        linked_activity_data = (
            self._repos.activity_subgroup_repository.get_linked_activity_uids(
                subgroup_uid=subgroup_uid,
                version=subgroup_ar.version,
                search_string=search_string,
                page_number=page_number,
                page_size=page_size,
                total_count=total_count,
            )
        )
        logger.debug(
            "Linked activity data for subgroup %s version %s",
            sanitize_for_log(subgroup_uid),
            subgroup_ar.version,
        )

        activities = []
        if linked_activity_data and "activities" in linked_activity_data:
            activity_service = ActivityService()
            for activity_info in linked_activity_data["activities"]:
                try:
                    activity = activity_service.get_by_uid(
                        uid=activity_info["uid"], version=activity_info["version"]
                    )
                    activities.append(activity)
                except exceptions.NotFoundException:
                    logger.debug(
                        "Activity with UID '%s' version '%s' not found - skipping",
                        activity_info["uid"],
                        activity_info["version"],
                    )
                    continue
                except exceptions.BusinessLogicException as e:
                    logger.info(
                        "Business logic prevented access to activity '%s' version '%s': %s",
                        activity_info["uid"],
                        activity_info["version"],
                        str(e),
                    )
                    continue
                except db.DatabaseError as e:
                    logger.warning(
                        "Database error retrieving activity '%s' version '%s': %s",
                        activity_info["uid"],
                        activity_info["version"],
                        str(e),
                    )
                    continue

        # Get total count from repository call if requested
        total_items = linked_activity_data.get("total", 0) if total_count else 0

        # Return directly without additional pagination as it's now handled at the repository level
        return GenericFilteringReturn(items=activities, total=total_items)

    def get_activity_groups_for_subgroup_paginated(
        self,
        subgroup_uid: str,
        version: str | None = None,
        page_number: int = 1,
        page_size: int = 10,
        total_count: bool = False,
    ) -> CustomPage[ActivityGroupForActivitySubGroup]:
        """
        Get activity groups for a specific activity subgroup with pagination.

        Args:
            subgroup_uid: The UID of the activity subgroup
            version: Optional specific version, or None for latest
            page_number: The page number for pagination (starting from 1)
            page_size: The number of items per page (0 for all items)
            total_count: Whether to calculate the total count

        Returns:
            CustomPage containing paginated ActivityGroup objects
        """
        linked_groups = (
            self._repos.activity_subgroup_repository.get_linked_activity_group_uids(
                subgroup_uid=subgroup_uid, version=version
            )
        )

        # Apply pagination
        if page_size == 0:
            paginated_groups = linked_groups
        else:
            start_index = (page_number - 1) * page_size
            end_index = start_index + page_size
            paginated_groups = linked_groups[start_index:end_index]

        total = len(linked_groups) if total_count else 0

        # Transform to ActivityGroup models
        activity_groups: list[ActivityGroupForActivitySubGroup] = []
        for group in paginated_groups:
            activity_group = ActivityGroupForActivitySubGroup(
                uid=group["uid"],
                name=group["name"],
                version=group["version"],
                status=group["status"],
            )
            activity_groups.append(activity_group)

        return CustomPage(
            items=activity_groups, total=total, page=page_number, size=page_size
        )

    def get_cosmos_subgroup_overview(self, subgroup_uid: str) -> dict[str, Any]:
        """Get a COSMoS compatible representation of a specific activity subgroup.

        Args:
            subgroup_uid: The UID of the activity subgroup

        Returns:
            A dictionary representation compatible with COSMoS format
        """
        try:
            # Get the subgroup overview data formatted for COSMoS
            return (
                self._repos.activity_subgroup_repository.get_cosmos_subgroup_overview(
                    subgroup_uid=subgroup_uid
                )
            )
        except exceptions.BusinessLogicException as e:
            # Rethrow with more context if needed
            raise exceptions.BusinessLogicException(
                msg=f"Error getting COSMoS subgroup overview for {subgroup_uid}: {str(e)}"
            ) from e

    def cascade_edit_and_approve(self, item: ActivitySubGroupAR):
        last_final_version = f"{item.item_metadata.major_version-1}.0"

        linked_activities = (
            self._repos.activity_subgroup_repository.get_linked_upgradable_activities(
                uid=item.uid, version=last_final_version
            )
        )
        if linked_activities is None:
            return

        self.batch_cascade_update(linked_activities=linked_activities)

    def batch_cascade_update(self, linked_activities: dict[str, Any]):
        activity_service = ActivityService()
        activity_uids = [
            activity["uid"] for activity in linked_activities.get("activities", [])
        ]
        if activity_uids:
            self._repos.activity_repository.lock_objects(uids=activity_uids)
            activity_ars, _ = self._repos.activity_repository.find_all(
                uids=activity_uids,
            )

            for activity in activity_ars:
                # Only process FINAL status activities - skip DRAFT activities entirely
                if activity.item_metadata.status.value != LibraryItemStatus.FINAL.value:
                    continue

                activity_groupings: list[ActivityGrouping] | None = []
                for grouping in activity.concept_vo.activity_groupings:
                    grp = {
                        "activity_group_uid": grouping.activity_group_uid,
                        "activity_subgroup_uid": grouping.activity_subgroup_uid,
                    }
                    activity_groupings.append(ActivityGrouping(**grp))
                if not activity_groupings:
                    # No matching groupings found, skip this activity
                    continue

                # For FINAL activities: create new version, edit, and approve
                activity.create_new_version(author_id=self.author_id)

                edit_input = ActivityEditInput(
                    name=activity.concept_vo.name,
                    name_sentence_case=activity.concept_vo.name_sentence_case,
                    activity_groupings=activity_groupings,
                    definition=activity.concept_vo.definition,
                    abbreviation=activity.concept_vo.abbreviation,
                    nci_concept_id=activity.concept_vo.nci_concept_id,
                    nci_concept_name=activity.concept_vo.nci_concept_name,
                    synonyms=activity.concept_vo.synonyms,
                    request_rationale=activity.concept_vo.request_rationale,
                    is_request_final=activity.concept_vo.is_request_final,
                    is_data_collected=activity.concept_vo.is_data_collected,
                    is_multiple_selection_allowed=activity.concept_vo.is_multiple_selection_allowed,
                    library_name=activity.library.name,
                    change_description="Cascade edit",
                )
                activity = activity_service._edit_aggregate(
                    item=activity,
                    concept_edit_input=edit_input,
                    perform_validation=False,
                )

                activity.approve(author_id=self.author_id)
                self._repos.activity_repository.copy_activity_and_recreate_activity_groupings(
                    activity, author_id=self.author_id
                )
                activity_service.cascade_edit_and_approve(activity)

    @ensure_transaction(db)
    def approve(
        self, uid: str, cascade_edit_and_approve: bool = False, ignore_exc: bool = False
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        try:
            item.approve(author_id=self.author_id)
            self.repository.save(item)
        except exceptions.BusinessLogicException as exc:
            if not ignore_exc or exc.msg != "The object isn't in draft status.":
                raise
        if cascade_edit_and_approve:
            self.cascade_edit_and_approve(item)
        return self._transform_aggregate_root_to_pydantic_model(item)
