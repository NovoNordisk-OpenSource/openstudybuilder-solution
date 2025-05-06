import datetime

from clinical_mdr_api.domain_repositories.concepts.activities.activity_group_repository import (
    ActivityGroupRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity_group import (
    ActivityGroupAR,
    ActivityGroupVO,
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
from clinical_mdr_api.services.concepts import constants
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
            ),
            concept_exists_by_library_and_name_callback=self._repos.activity_group_repository.latest_concept_in_library_exists_by_name,
        )
        return item

    def get_group_overview(
        self, group_uid: str, version: str | None = None
    ) -> ActivityGroupOverview:
        group = self.get_by_uid(group_uid, version=version)
        all_versions = [
            version.version for version in self.get_version_history(group_uid)
        ]

        # Convert dates to ISO format strings if they exist
        start_date = group.start_date.isoformat() if group.start_date else None
        end_date = group.end_date.isoformat() if group.end_date else None

        group_detail = ActivityGroupDetail(
            name=group.name,
            name_sentence_case=group.name_sentence_case,
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
        )

        # Fetch subgroups linked to this specific group version
        subgroups = []
        version_to_use = version if version else group.version

        # Get subgroups linked to this specific activity group version
        linked_subgroups = (
            self._repos.activity_group_repository.get_linked_activity_subgroup_uids(
                group_uid=group_uid, version=version_to_use
            )
        )

        if linked_subgroups:
            # Direct conversion from the repository result to SimpleSubGroup objects
            subgroups = [
                SimpleSubGroup(
                    uid=subgroup["uid"],
                    name=subgroup["name"],
                    version=subgroup["version"],
                    status=subgroup["status"],
                    definition=subgroup["definition"],
                )
                for subgroup in linked_subgroups
            ]

        return ActivityGroupOverview(
            group=group_detail, subgroups=subgroups, all_versions=all_versions
        )

    def get_cosmos_group_overview(self, group_uid: str) -> dict:
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
