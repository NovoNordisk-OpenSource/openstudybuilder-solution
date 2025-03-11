import datetime

from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.activities.activity_repository import (
    ActivityRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity import (
    ActivityAR,
    ActivityGroupingVO,
    ActivityVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    Activity,
    ActivityCreateInput,
    ActivityEditInput,
    ActivityFromRequestInput,
    ActivityGrouping,
    ActivityOverview,
    ActivityRequestRejectInput,
    ActivityVersion,
)
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstanceEditInput,
)
from clinical_mdr_api.services._utils import is_library_editable
from clinical_mdr_api.services.concepts import constants
from clinical_mdr_api.services.concepts.activities.activity_instance_service import (
    ActivityInstanceService,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)
from clinical_mdr_api.utils import normalize_string
from common.config import REQUESTED_LIBRARY_NAME
from common.exceptions import BusinessLogicException, NotFoundException


class ActivityService(ConceptGenericService[ActivityAR]):
    aggregate_class = ActivityAR
    version_class = ActivityVersion
    repository_interface = ActivityRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityAR
    ) -> Activity:
        return Activity.from_activity_ar(activity_ar=item_ar)

    def _to_activity_grouping_vo(
        self, activity_groupings: list[ActivityGrouping | ActivityGroupingVO]
    ) -> list[ActivityGroupingVO]:
        """Converts to a list of ActivityGroupingVOs with name property resolve from the db"""

        activity_grouping_vos = []

        # collect activity group and subgroup uids
        activity_group_uids = set()
        activity_subgroup_uids = set()
        for activity_grouping in activity_groupings:
            activity_group_uids.add(activity_grouping.activity_group_uid)
            activity_subgroup_uids.add(activity_grouping.activity_subgroup_uid)

        activity_groups, _ = self._repos.activity_group_repository.get_all_optimized(
            filter_by={"uid": {"v": list(activity_group_uids), "op": "in"}},
        )
        activity_groups_by_uid = {group.uid: group for group in activity_groups}

        activity_subgroups, _ = (
            self._repos.activity_subgroup_repository.get_all_optimized(
                filter_by={"uid": {"v": list(activity_subgroup_uids), "op": "in"}},
            )
        )
        activity_subgroups_by_uid = {group.uid: group for group in activity_subgroups}

        # create ActivityGroupingVO-s with names
        for activity_grouping in activity_groupings:
            activity_grouping_vos.append(
                ActivityGroupingVO(
                    activity_group_uid=activity_grouping.activity_group_uid,
                    activity_group_name=(
                        activity_groups_by_uid[
                            activity_grouping.activity_group_uid
                        ].name
                        if activity_grouping.activity_group_uid
                        in activity_groups_by_uid
                        else None
                    ),
                    activity_subgroup_uid=activity_grouping.activity_subgroup_uid,
                    activity_subgroup_name=(
                        activity_subgroups_by_uid[
                            activity_grouping.activity_subgroup_uid
                        ].name
                        if activity_grouping.activity_subgroup_uid
                        in activity_subgroups_by_uid
                        else None
                    ),
                )
            )

        return activity_grouping_vos

    def _create_aggregate_root(
        self, concept_input: ActivityCreateInput, library
    ) -> _AggregateRootType:
        activity_groupings = (
            self._to_activity_grouping_vo(concept_input.activity_groupings)
            if concept_input.activity_groupings
            else []
        )
        return ActivityAR.from_input_values(
            author_id=self.author_id,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=concept_input.nci_concept_id,
                nci_concept_name=concept_input.nci_concept_name,
                name=concept_input.name,
                name_sentence_case=concept_input.name_sentence_case,
                synonyms=concept_input.synonyms or [],
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                activity_groupings=activity_groupings,
                request_rationale=concept_input.request_rationale,
                is_request_final=concept_input.is_request_final,
                is_data_collected=concept_input.is_data_collected,
                is_multiple_selection_allowed=concept_input.is_multiple_selection_allowed,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_library_and_name_callback=self._repos.activity_repository.latest_concept_in_library_exists_by_name,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
            get_activity_uids_by_synonyms_callback=self._repos.activity_repository.get_activity_uids_by_synonyms,
        )

    def _edit_aggregate(
        self, item: ActivityAR, concept_edit_input: ActivityEditInput
    ) -> ActivityAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=concept_edit_input.nci_concept_id,
                nci_concept_name=concept_edit_input.nci_concept_name,
                name=concept_edit_input.name,
                name_sentence_case=concept_edit_input.name_sentence_case,
                synonyms=concept_edit_input.synonyms or [],
                definition=concept_edit_input.definition,
                abbreviation=concept_edit_input.abbreviation,
                activity_groupings=(
                    self._to_activity_grouping_vo(concept_edit_input.activity_groupings)
                    if concept_edit_input.activity_groupings
                    else []
                ),
                request_rationale=concept_edit_input.request_rationale,
                is_request_final=concept_edit_input.is_request_final,
                is_data_collected=concept_edit_input.is_data_collected,
                is_multiple_selection_allowed=concept_edit_input.is_multiple_selection_allowed,
            ),
            concept_exists_by_library_and_name_callback=self._repos.activity_repository.latest_concept_in_library_exists_by_name,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
            get_activity_uids_by_synonyms_callback=self._repos.activity_repository.get_activity_uids_by_synonyms,
        )
        return item

    @db.transaction
    def replace_requested_activity_with_sponsor(
        self, sponsor_activity_input: ActivityFromRequestInput
    ) -> Activity:
        NotFoundException.raise_if_not(
            self._repos.library_repository.library_exists(
                normalize_string(sponsor_activity_input.library_name)
            ),
            "Library",
            sponsor_activity_input.library_name,
            "Name",
        )

        library_vo = LibraryVO.from_input_values_2(
            library_name=sponsor_activity_input.library_name,
            is_library_editable_callback=is_library_editable,
        )

        # retire Requested Activity first to not conflict the Sponsor Activity name
        activity_request_ar = self.repository.find_by_uid_2(
            uid=sponsor_activity_input.activity_request_uid, for_update=True
        )
        NotFoundException.raise_if(
            activity_request_ar is None,
            "Requested Activity",
            sponsor_activity_input.activity_request_uid,
            "activity_request_uid",
        )
        BusinessLogicException.raise_if(
            activity_request_ar.item_metadata.status != LibraryItemStatus.FINAL,
            msg=f"To update the Activity Request with Name '{activity_request_ar.name}' to Sponsor Activity it should be in Final state.",
        )
        activity_request_ar.inactivate(
            author_id=self.author_id,
            change_description="Inactivate Requested Activity as Sponsor Activity was created",
        )
        self.repository.save(activity_request_ar)

        concept_ar = self._create_aggregate_root(
            concept_input=sponsor_activity_input, library=library_vo
        )
        concept_ar.approve(
            author_id=self.author_id,
            change_description="Approve Sponsor Activity created from Requested Activity",
        )
        self.repository.save(concept_ar)
        self.repository.replace_request_with_sponsor_activity(
            activity_request_uid=sponsor_activity_input.activity_request_uid,
            sponsor_activity_uid=concept_ar.uid,
        )
        return self._transform_aggregate_root_to_pydantic_model(concept_ar)

    @db.transaction
    def reject_activity_request(
        self,
        activity_request_uid: str,
        activity_request_rejection_input: ActivityRequestRejectInput,
    ) -> Activity:
        # retire Requested Activity first to not conflict the Sponsor Activity name
        activity_request_ar = self.repository.find_by_uid_2(
            uid=activity_request_uid, for_update=True
        )
        BusinessLogicException.raise_if_not(
            activity_request_ar,
            msg=f"The Activity Request with UID '{activity_request_uid}' doesn't exist.",
        )
        BusinessLogicException.raise_if(
            activity_request_ar.item_metadata.status != LibraryItemStatus.FINAL,
            msg=f"To reject Activity Request with Name '{activity_request_ar.name}' it has to be in Final state.",
        )
        BusinessLogicException.raise_if(
            activity_request_ar.library.name != REQUESTED_LIBRARY_NAME,
            msg="Only Requested Activities can be rejected.",
        )
        activity_request_ar.create_new_version(author_id=self.author_id)
        self.repository.save(activity_request_ar)
        activity_request_ar.edit_draft(
            author_id=self.author_id,
            change_description=f"Rejecting with the following reason {activity_request_rejection_input.reason_for_rejecting}",
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=activity_request_ar.concept_vo.nci_concept_id,
                nci_concept_name=activity_request_ar.concept_vo.nci_concept_name,
                name=activity_request_ar.concept_vo.name,
                name_sentence_case=activity_request_ar.concept_vo.name_sentence_case,
                synonyms=activity_request_ar.concept_vo.synonyms,
                definition=activity_request_ar.concept_vo.definition,
                abbreviation=activity_request_ar.concept_vo.abbreviation,
                activity_groupings=activity_request_ar.concept_vo.activity_groupings,
                request_rationale=activity_request_ar.concept_vo.request_rationale,
                is_request_final=activity_request_ar.concept_vo.is_request_final,
                is_request_rejected=True,
                contact_person=activity_request_rejection_input.contact_person,
                reason_for_rejecting=activity_request_rejection_input.reason_for_rejecting,
                is_data_collected=activity_request_ar.concept_vo.is_data_collected,
                is_multiple_selection_allowed=activity_request_ar.concept_vo.is_multiple_selection_allowed,
            ),
            concept_exists_by_library_and_name_callback=self._repos.activity_repository.latest_concept_in_library_exists_by_name,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
            get_activity_uids_by_synonyms_callback=self._repos.activity_repository.get_activity_uids_by_synonyms,
        )
        self.repository.save(activity_request_ar)
        activity_request_ar.approve(
            author_id=self.author_id, change_description="Approving after rejecting"
        )
        self.repository.save(activity_request_ar)
        activity_request_ar.inactivate(
            author_id=self.author_id,
            change_description="Retiring rejected Activity Request",
        )
        self.repository.save(activity_request_ar)
        return self._transform_aggregate_root_to_pydantic_model(activity_request_ar)

    def get_activity_overview(
        self, activity_uid: str, version: str | None
    ) -> ActivityOverview:
        NotFoundException.raise_if_not(
            self.repository.exists_by("uid", activity_uid, True),
            "Activity",
            activity_uid,
        )

        overview = self._repos.activity_repository.get_activity_overview(
            uid=activity_uid, version=version
        )
        return ActivityOverview.from_repository_input(overview=overview)

    def get_cosmos_activity_overview(self, activity_uid: str) -> dict:
        NotFoundException.raise_if_not(
            self.repository.exists_by("uid", activity_uid, True),
            "Activity",
            activity_uid,
        )

        data: dict = self.repository.get_cosmos_activity_overview(uid=activity_uid)
        result: dict = {
            "packageDate": datetime.date.today().isoformat(),
            "packageType": "bc",
            "conceptId": data["activity_value"]["nci_concept_id"],
            "ncitCode": data["activity_value"]["nci_concept_id"],
            "href": constants.COSM0S_BASE_ITEM_HREF.format(
                data["activity_value"]["nci_concept_id"]
            ),
            "categories": data["activity_subgroups"],
            "shortName": data["activity_value"]["name"],
            "synonyms": data["activity_value"]["abbreviation"],
            "resultScales": list(
                set(
                    constants.COSM0S_RESULT_SCALES_MAP.get(
                        instance["activity_instance_class_name"], ""
                    )
                    for instance in data["activity_instances"]
                )
            ),
            "definition": data["activity_value"]["definition"],
            "dataElementConcepts": [],
        }
        for activity_item in data["activity_items"]:
            result["dataElementConcepts"].append(
                {
                    "conceptId": activity_item["nci_concept_id"],
                    "ncitCode": activity_item["nci_concept_id"],
                    "href": constants.COSM0S_BASE_ITEM_HREF.format(
                        activity_item["nci_concept_id"]
                    ),
                    "shortName": activity_item["name"],
                    "dataType": constants.COSMOS_DEC_TYPES_MAP.get(
                        activity_item["type"], activity_item["type"]
                    ),
                    "exampleSet": activity_item["example_set"],
                }
            )
        return result

    def cascade_edit_and_approve(self, item: ActivityAR):
        if not item.concept_vo.is_data_collected:
            # Do not upversion any instances if the activity is without data collection
            return

        _, _, _, activity_after_save = item.repository_closure_data
        _, _, _, activity_before_save = activity_after_save.repository_closure_data
        item_metadata = activity_before_save.item_metadata
        last_final_version = f"{item_metadata.major_version}.0"

        groupings = item.concept_vo.activity_groupings
        instance_groupings = []
        for grouping in groupings:
            grp = {
                "activity_uid": item.uid,
                "activity_group_uid": grouping.activity_group_uid,
                "activity_subgroup_uid": grouping.activity_subgroup_uid,
            }
            instance_groupings.append(grp)

        linked_instances = (
            self._repos.activity_repository.get_linked_upgradable_activity_instances(
                uid=item.uid, version=last_final_version
            )
        )
        if linked_instances is None:
            return
        instance_service = ActivityInstanceService()

        for instance in linked_instances.get("activity_instances", []):
            if instance["version"]["status"] not in (
                LibraryItemStatus.DRAFT.value,
                LibraryItemStatus.FINAL.value,
            ):
                continue
            if instance["version"]["status"] == LibraryItemStatus.FINAL.value:
                instance_service.non_transactional_create_new_version(instance["uid"])
            edit_input = ActivityInstanceEditInput(
                change_description="Cascade edit", activity_groupings=instance_groupings
            )
            instance_service.non_transactional_edit(
                uid=instance["uid"], concept_edit_input=edit_input
            )
            instance_service.non_transactional_approve(instance["uid"])
