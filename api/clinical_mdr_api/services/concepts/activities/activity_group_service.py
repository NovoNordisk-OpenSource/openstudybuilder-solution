import datetime
from typing import Any

from clinical_mdr_api.domain_repositories.concepts.activities.activity_group_repository import (
    ActivityGroupRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity_group import (
    ActivityGroupAR,
    ActivityGroupVO,
)
from clinical_mdr_api.domains.enums import LibraryItemStatus
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityEditInput,
    ActivityGrouping,
)
from clinical_mdr_api.models.concepts.activities.activity_group import (
    ActivityGroup,
    ActivityGroupCreateInput,
    ActivityGroupDetail,
    ActivityGroupEditInput,
    ActivityGroupOverview,
    ActivityGroupVersion,
    SimpleSubGroup,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.services.concepts import constants
from clinical_mdr_api.services.concepts.activities.activity_service import (
    ActivityService,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
)
from common.exceptions import NotFoundException


class ActivityGroupService(ConceptGenericService[ActivityGroupAR]):
    aggregate_class = ActivityGroupAR
    repository_interface = ActivityGroupRepository
    version_class = ActivityGroupVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityGroupAR
    ) -> ActivityGroup:
        return ActivityGroup.from_activity_ar(activity_group_ar=item_ar)

    def _create_aggregate_root(
        self, concept_input: ActivityGroupCreateInput, library
    ) -> ActivityGroupAR:
        return ActivityGroupAR.from_input_values(
            author_id=self.author_id,
            concept_vo=ActivityGroupVO.from_repository_values(
                name=concept_input.name,
                name_sentence_case=concept_input.name_sentence_case,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                nci_concept_id=concept_input.nci_concept_id,
                nci_concept_name=concept_input.nci_concept_name,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_library_and_name_callback=self._repos.activity_group_repository.latest_concept_in_library_exists_by_name,
        )

    def _edit_aggregate(
        self, item: ActivityGroupAR, concept_edit_input: ActivityGroupEditInput
    ) -> ActivityGroupAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=ActivityGroupVO.from_repository_values(
                name=concept_edit_input.name,
                name_sentence_case=concept_edit_input.name_sentence_case,
                definition=concept_edit_input.definition,
                abbreviation=concept_edit_input.abbreviation,
                nci_concept_id=concept_edit_input.nci_concept_id,
                nci_concept_name=concept_edit_input.nci_concept_name,
            ),
            concept_exists_by_library_and_name_callback=self._repos.activity_group_repository.latest_concept_in_library_exists_by_name,
        )
        return item

    def get_group_details(
        self, group_uid: str, version: str | None = None
    ) -> ActivityGroupDetail:
        """
        Get just the activity group details without subgroups.

        Args:
            group_uid: The UID of the activity group
            version: Optional specific version, or None for latest

        Returns:
            ActivityGroupDetail object with the group information
        """
        group = self.get_by_uid(group_uid, version=version)

        # Convert dates to ISO format strings if they exist
        start_date = group.start_date.isoformat() if group.start_date else None
        end_date = group.end_date.isoformat() if group.end_date else None

        # Get all versions for this group and deduplicate for the overview
        version_history = self.get_version_history(group_uid)
        all_versions = []
        for version_item in version_history:
            if version_item.version not in all_versions:
                all_versions.append(version_item.version)

        return ActivityGroupDetail(
            name=group.name,
            name_sentence_case=group.name_sentence_case,
            nci_concept_id=group.nci_concept_id,
            nci_concept_name=group.nci_concept_name,
            library_name=group.library_name,
            start_date=start_date,
            end_date=end_date,
            status=group.status,
            version=group.version,
            possible_actions=group.possible_actions,
            change_description=group.change_description,
            author_username=group.author_username,
            definition=group.definition,
            abbreviation=group.abbreviation,
            all_versions=all_versions,
        )

    def get_group_subgroups(
        self,
        group_uid: str,
        version: str | None = None,
        page_number: int = 1,
        page_size: int = 10,
        total_count: bool = False,
    ) -> GenericFilteringReturn[SimpleSubGroup]:
        """
        Get just the activity subgroups linked to a specific activity group version.

        Args:
            group_uid: The UID of the activity group
            version: Optional specific version, or None for latest
            page_number: The page number for pagination (starting from 1)
            page_size: The number of items per page
            total_count: Whether to calculate the total count

        Returns:
            GenericFilteringReturn containing SimpleSubGroup objects linked to the activity group
        """
        # If no specific version provided, get the latest one
        if not version:
            group = self.get_by_uid(group_uid)
            version_to_use = group.version
        else:
            version_to_use = version

        # Calculate pagination parameters for the database query
        # If page_size is 0, we don't apply limits (return all items)
        skip = (page_number - 1) * page_size if page_size > 0 else 0
        limit = page_size if page_size > 0 else None

        # Get subgroups linked to this specific activity group version with pagination in the database
        result = (
            self._repos.activity_group_repository.get_linked_activity_subgroup_uids(
                group_uid=group_uid,
                version=version_to_use,
                skip=skip,
                limit=limit,
                count_total=total_count,
            )
        )

        # Extract data from the repository response
        linked_subgroups = result.get("subgroups", [])
        total = result.get("total", 0) if total_count else 0

        if not linked_subgroups:
            return GenericFilteringReturn(items=[], total=0)

        # Direct conversion from the repository result to SimpleSubGroup objects
        items = [
            SimpleSubGroup(
                uid=subgroup["uid"],
                name=subgroup["name"],
                version=subgroup["version"],
                status=subgroup["status"],
                start_date=subgroup["start_date"].isoformat(),
                definition=subgroup["definition"],
            )
            for subgroup in linked_subgroups
        ]

        return GenericFilteringReturn(items=items, total=total)

    def get_group_overview(
        self, group_uid: str, version: str | None = None
    ) -> ActivityGroupOverview:
        """
        Get a complete overview of an activity group including details, subgroups, and version history.

        Args:
            group_uid: The UID of the activity group
            version: Optional specific version, or None for latest

        Returns:
            ActivityGroupOverview object with complete group information
        """
        # Get the group details
        group_detail = self.get_group_details(group_uid, version)

        subgroups_result = self.get_group_subgroups(group_uid, version, page_size=0)
        subgroups = subgroups_result.items

        # Get all versions
        # Get all versions and deduplicate by version number for the overview
        version_history = self.get_version_history(group_uid)
        all_versions = []
        for version_item in version_history:
            if version_item.version not in all_versions:
                all_versions.append(version_item.version)

        return ActivityGroupOverview(
            group=group_detail, subgroups=subgroups, all_versions=all_versions
        )

    def get_cosmos_group_overview(self, group_uid: str) -> dict[str, Any]:
        """
        Get a COSMoS compatible representation of a specific activity group.

        Args:
            group_uid: The UID of the activity group

        Returns:
            A dictionary representation compatible with COSMoS format
        """

        NotFoundException.raise_if_not(
            self.repository.exists_by("uid", group_uid, True),
            "ActivityGroup",
            group_uid,
        )

        # Get the group overview data formatted for COSMoS
        overview_data = self._repos.activity_group_repository.get_cosmos_group_overview(
            group_uid=group_uid
        )

        # Transform the data to COSMoS format
        result = {
            "packageDate": datetime.date.today().isoformat(),
            "packageType": "bc",
            "groupId": group_uid,
            "shortName": overview_data["group_value"]["name"],
            "definition": overview_data["group_value"]["definition"],
            "library": overview_data["group_library_name"],
            "subgroups": [],
            "activities": [],
        }

        # Add linked subgroups
        if overview_data["linked_subgroups"]:
            for subgroup in overview_data["linked_subgroups"]:
                result["subgroups"].append(
                    {
                        "subgroupId": subgroup["uid"],
                        "shortName": subgroup["name"],
                        "definition": subgroup["definition"],
                        "version": subgroup["version"],
                        "status": subgroup["status"],
                    }
                )

        # Add linked activities
        if overview_data["linked_activities"]:
            for activity in overview_data["linked_activities"]:
                activity_entry = {
                    "activityId": activity["uid"],
                    "shortName": activity["name"],
                    "definition": activity["definition"],
                    "version": activity["version"],
                    "status": activity["status"],
                }

                # Add NCI concept ID if available
                if activity.get("nci_concept_id"):
                    activity_entry["conceptId"] = activity["nci_concept_id"]
                    activity_entry["href"] = constants.COSM0S_BASE_ITEM_HREF.format(
                        activity["nci_concept_id"]
                    )

                result["activities"].append(activity_entry)

        return result

    def cascade_edit_and_approve(self, item: ActivityGroupAR):
        last_final_version = f"{item.item_metadata.major_version-1}.0"

        linked_activities = (
            self._repos.activity_group_repository.get_linked_upgradable_activities(
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
        return True
