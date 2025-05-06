import logging

from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.activities.activity_sub_group_repository import (
    ActivitySubGroupRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
    ActivitySubGroupVO,
    SimpleActivityGroupVO,
)
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivityGroup,
    ActivitySubGroup,
    ActivitySubGroupCreateInput,
    ActivitySubGroupDetail,
    ActivitySubGroupEditInput,
    ActivitySubGroupOverview,
    ActivitySubGroupVersion,
)
from clinical_mdr_api.services.concepts.activities.activity_service import (
    ActivityService,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
)
from common import exceptions

logger = logging.getLogger(__name__)


class ActivitySubGroupService(ConceptGenericService[ActivitySubGroupAR]):
    aggregate_class = ActivitySubGroupAR
    repository_interface = ActivitySubGroupRepository
    version_class = ActivitySubGroupVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivitySubGroupAR
    ) -> ActivitySubGroup:
        return ActivitySubGroup.from_activity_ar(
            activity_subgroup_ar=item_ar,
            find_activity_by_uid=self._repos.activity_group_repository.find_by_uid_2,
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
                activity_groups=(
                    [
                        SimpleActivityGroupVO(activity_group_uid=activity_group)
                        for activity_group in concept_input.activity_groups
                    ]
                    if concept_input.activity_groups
                    else []
                ),
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_library_and_name_callback=self._repos.activity_subgroup_repository.latest_concept_in_library_exists_by_name,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
        )

    def _edit_aggregate(
        self,
        item: ActivitySubGroupAR,
        concept_edit_input: ActivitySubGroupEditInput,
    ) -> ActivitySubGroupAR:
        if "activity_groups" in concept_edit_input.model_fields_set:
            activity_groups = (
                [
                    SimpleActivityGroupVO(activity_group_uid=activity_group)
                    for activity_group in concept_edit_input.activity_groups
                ]
                if concept_edit_input.activity_groups
                else []
            )
        else:
            activity_groups = item.concept_vo.activity_groups
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=ActivitySubGroupVO.from_repository_values(
                name=concept_edit_input.name,
                name_sentence_case=concept_edit_input.name_sentence_case,
                definition=concept_edit_input.definition,
                abbreviation=concept_edit_input.abbreviation,
                activity_groups=activity_groups,
            ),
            concept_exists_by_library_and_name_callback=self._repos.activity_subgroup_repository.latest_concept_in_library_exists_by_name,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
        )
        return item

    def get_subgroup_overview(
        self, subgroup_uid: str, version: str | None = None
    ) -> ActivitySubGroupOverview:
        subgroup = self.get_by_uid(subgroup_uid, version=version)
        all_versions = [
            version.version for version in self.get_version_history(subgroup_uid)
        ]

        # Get UIDs of activities directly linked to this subgroup
        linked_activity_uids = (
            self._repos.activity_subgroup_repository.get_linked_activity_uids(
                subgroup_uid=subgroup_uid, version=version
            )
        )

        # Get activity groups linked to this specific subgroup version
        linked_activity_group_data = (
            self._repos.activity_subgroup_repository.get_linked_activity_group_uids(
                subgroup_uid=subgroup_uid, version=version
            )
        )
        logger.debug("Linked activity group data: %s", linked_activity_group_data)

        # Fetch complete activity objects for these UIDs
        activity_service = ActivityService()
        activities = []
        for uid in linked_activity_uids:
            try:
                activity = activity_service.get_by_uid(uid=uid)
                activities.append(activity)
            except exceptions.NotFoundException:
                logger.debug("Activity with UID '%s' not found - skipping", uid)
                continue
            except exceptions.BusinessLogicException as e:
                logger.info(
                    "Business logic prevented access to activity '%s': %s", uid, str(e)
                )
                continue
            except db.DatabaseError as e:
                logger.warning(
                    "Database error retrieving activity '%s': %s", uid, str(e)
                )
                continue

        # Fetch activity groups - using dynamic import to avoid circular import
        activity_groups = []
        if linked_activity_group_data:
            # Import ActivityGroupService dynamically to avoid circular import
            from clinical_mdr_api.services.concepts.activities.activity_group_service import (
                ActivityGroupService,
            )

            activity_group_service = ActivityGroupService()

            for group_data in linked_activity_group_data:
                try:
                    logger.debug(
                        "Fetching activity group with UID: %s and version: %s",
                        group_data["uid"],
                        group_data["version"],
                    )
                    activity_group = activity_group_service.get_by_uid(
                        uid=group_data["uid"], version=group_data["version"]
                    )
                    # Add the linked version to the activity group information
                    activity_groups.append(
                        ActivityGroup(
                            uid=activity_group.uid,
                            name=activity_group.name,
                            version=group_data["version"],
                            status=activity_group.status,
                        )
                    )
                    logger.debug(
                        "Added activity group: %s with version %s",
                        activity_group,
                        group_data["version"],
                    )
                except exceptions.NotFoundException:
                    logger.debug(
                        "Activity group with UID '%s' not found - skipping",
                        group_data["uid"],
                    )
                    continue
                except exceptions.BusinessLogicException as e:
                    logger.info(
                        "Business logic prevented access to activity group '%s': %s",
                        group_data["uid"],
                        str(e),
                    )
                    continue
                except db.DatabaseError as e:
                    logger.warning(
                        "Database error retrieving activity group '%s': %s",
                        group_data["uid"],
                        str(e),
                    )
                    continue

        logger.debug("Final activity groups: %s", activity_groups)

        activity_subgroup_detail = ActivitySubGroupDetail(
            name=subgroup.name,
            name_sentence_case=subgroup.name_sentence_case,
            library_name=subgroup.library_name,
            definition=subgroup.definition,
            start_date=subgroup.start_date,
            end_date=subgroup.end_date,
            status=subgroup.status,
            version=subgroup.version,
            possible_actions=subgroup.possible_actions,
            change_description=subgroup.change_description,
            author_username=subgroup.author_username,
            activity_groups=activity_groups,
        )

        result = ActivitySubGroupOverview(
            activity_subgroup=activity_subgroup_detail,
            activities=activities,
            all_versions=all_versions,
        )
        logger.debug(
            "Created overview with %s activity groups",
            len(activity_subgroup_detail.activity_groups),
        )
        return result

    def get_cosmos_subgroup_overview(self, subgroup_uid: str) -> dict:
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
                f"Error getting COSMoS subgroup overview for {subgroup_uid}: {str(e)}"
            ) from e
