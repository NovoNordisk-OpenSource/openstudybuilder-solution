import datetime

from clinical_mdr_api.domain_repositories.concepts.activities.activity_instance_repository import (
    ActivityInstanceRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity_instance import (
    ActivityInstanceAR,
    ActivityInstanceGroupingVO,
    ActivityInstanceVO,
)
from clinical_mdr_api.domains.concepts.activities.activity_item import (
    ActivityItemVO,
    LibraryItem,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
    ActivityInstanceCreateInput,
    ActivityInstanceEditInput,
    ActivityInstanceOverview,
    ActivityInstancePreviewInput,
    ActivityInstanceVersion,
)
from clinical_mdr_api.models.concepts.activities.activity_item import (
    CompactOdmItem,
    CompactUnitDefinition,
)
from clinical_mdr_api.services.concepts import constants
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)
from common.exceptions import NotFoundException
from common.utils import get_edit_input_or_previous_value


class ActivityInstanceService(ConceptGenericService[ActivityInstanceAR]):
    aggregate_class = ActivityInstanceAR
    repository_interface = ActivityInstanceRepository
    version_class = ActivityInstanceVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityInstanceAR
    ) -> ActivityInstance:
        return ActivityInstance.from_activity_ar(
            activity_ar=item_ar,
            find_activity_hierarchy_by_uid=self._repos.activity_repository.find_by_uid_2,
            find_activity_subgroup_by_uid=self._repos.activity_subgroup_repository.find_by_uid_2,
            find_activity_group_by_uid=self._repos.activity_group_repository.find_by_uid_2,
        )

    def create(
        self,
        concept_input: ActivityInstanceCreateInput | ActivityInstancePreviewInput,
        preview: bool = False,
    ) -> ActivityInstance:
        return self.non_transactional_create(concept_input, preview=preview)

    def _create_aggregate_root(
        self,
        concept_input: ActivityInstanceCreateInput,
        library: LibraryVO,
        preview: bool = False,
    ) -> _AggregateRootType:
        activity_items = []
        if (
            getattr(concept_input, "activity_items", None)
            and concept_input.activity_items is not None
        ):
            for item in concept_input.activity_items:
                unit_definitions = [
                    CompactUnitDefinition(uid=unit_uid, name=None, dimension_name=None)
                    for unit_uid in item.unit_definition_uids
                ]
                ct_terms = [
                    LibraryItem(uid=term_uid, name=None)
                    for term_uid in item.ct_term_uids
                ]
                odm_items = [
                    CompactOdmItem(uid=odm_item_uid, oid=None, name=None)
                    for odm_item_uid in item.odm_item_uids
                ]
                activity_items.append(
                    ActivityItemVO.from_repository_values(
                        is_adam_param_specific=item.is_adam_param_specific,
                        activity_item_class_uid=item.activity_item_class_uid,
                        activity_item_class_name=None,
                        ct_terms=ct_terms,
                        unit_definitions=unit_definitions,
                        odm_items=odm_items,
                    )
                )

        return ActivityInstanceAR.from_input_values(
            author_id=self.author_id,
            concept_vo=ActivityInstanceVO.from_repository_values(
                nci_concept_id=concept_input.nci_concept_id,
                nci_concept_name=concept_input.nci_concept_name,
                name=concept_input.name,
                name_sentence_case=concept_input.name_sentence_case,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                is_research_lab=concept_input.is_research_lab,
                molecular_weight=concept_input.molecular_weight,
                topic_code=concept_input.topic_code,
                adam_param_code=concept_input.adam_param_code,
                is_required_for_activity=concept_input.is_required_for_activity,
                is_default_selected_for_activity=concept_input.is_default_selected_for_activity,
                is_data_sharing=concept_input.is_data_sharing,
                is_legacy_usage=concept_input.is_legacy_usage,
                is_derived=concept_input.is_derived,
                legacy_description=concept_input.legacy_description,
                activity_groupings=(
                    [
                        ActivityInstanceGroupingVO(
                            activity_uid=activity_grouping.activity_uid,
                            activity_group_uid=activity_grouping.activity_group_uid,
                            activity_subgroup_uid=activity_grouping.activity_subgroup_uid,
                        )
                        for activity_grouping in concept_input.activity_groupings
                    ]
                    if concept_input.activity_groupings
                    else []
                ),
                activity_instance_class_uid=concept_input.activity_instance_class_uid,
                activity_instance_class_name=None,
                activity_items=activity_items,
            ),
            library=library,
            generate_uid_callback=(
                self.repository.generate_uid
                if not preview
                else lambda: "PreviewTemporalUid"
            ),
            concept_exists_by_library_and_property_value_callback=self._repos.activity_instance_repository.latest_concept_in_library_exists_by_property_value,
            ct_term_exists_by_uid_callback=self._repos.ct_term_name_repository.term_exists,
            unit_definition_exists_by_uid_callback=self._repos.unit_definition_repository.final_concept_exists,
            odm_item_exists_by_uid_callback=self._repos.odm_item_repository.final_concept_exists,
            get_final_activity_value_by_uid_callback=self._repos.activity_repository.final_concept_value,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            find_activity_item_class_by_uid_callback=self._repos.activity_item_class_repository.find_by_uid_2,
            find_activity_instance_class_by_uid_callback=self._repos.activity_instance_class_repository.find_by_uid_2,
            preview=preview,
            get_dimension_names_by_unit_definition_uids=self._repos.unit_definition_repository.get_dimension_names_by_unit_definition_uids,
        )

    def non_transactional_edit(
        self,
        uid: str,
        concept_edit_input: ActivityInstanceEditInput,
    ) -> ActivityInstance:
        item = self._find_by_uid_or_raise_not_found(uid=uid, for_update=True)
        edited_item = self._edit_aggregate(
            item=item, concept_edit_input=concept_edit_input
        )
        self.repository.save(edited_item)
        return self._transform_aggregate_root_to_pydantic_model(edited_item)

    def _edit_aggregate(
        self, item: ActivityInstanceAR, concept_edit_input: ActivityInstanceEditInput
    ) -> ActivityInstanceAR:
        fields_set = concept_edit_input.model_fields_set
        if "activity_groupings" in fields_set:
            if concept_edit_input.activity_groupings:
                activity_groupings = [
                    ActivityInstanceGroupingVO(
                        activity_uid=activity_grouping.activity_uid,
                        activity_group_uid=activity_grouping.activity_group_uid,
                        activity_subgroup_uid=activity_grouping.activity_subgroup_uid,
                    )
                    for activity_grouping in concept_edit_input.activity_groupings
                ]
            else:
                activity_groupings = []
        else:
            if item.concept_vo.activity_groupings:
                activity_groupings = [
                    ActivityInstanceGroupingVO(
                        activity_uid=activity_grouping.activity_uid,
                        activity_group_uid=activity_grouping.activity_group_uid,
                        activity_subgroup_uid=activity_grouping.activity_subgroup_uid,
                    )
                    for activity_grouping in item.concept_vo.activity_groupings
                ]
            else:
                activity_groupings = []

        if "activity_items" in fields_set:
            activity_items = []
            if concept_edit_input.activity_items is not None:
                for activity_item in concept_edit_input.activity_items:
                    unit_definitions = [
                        CompactUnitDefinition(
                            uid=unit_uid, name=None, dimension_name=None
                        )
                        for unit_uid in activity_item.unit_definition_uids
                    ]
                    ct_terms = [
                        LibraryItem(uid=term_uid, name=None)
                        for term_uid in activity_item.ct_term_uids
                    ]
                    odm_items = [
                        CompactOdmItem(uid=odm_item_uid, oid=None, name=None)
                        for odm_item_uid in activity_item.odm_item_uids
                    ]
                    activity_items.append(
                        ActivityItemVO.from_repository_values(
                            is_adam_param_specific=activity_item.is_adam_param_specific,
                            activity_item_class_uid=activity_item.activity_item_class_uid,
                            activity_item_class_name=None,
                            ct_terms=ct_terms,
                            unit_definitions=unit_definitions,
                            odm_items=odm_items,
                        )
                    )
        else:
            activity_items = item.concept_vo.activity_items

        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=ActivityInstanceVO.from_repository_values(
                nci_concept_id=get_edit_input_or_previous_value(
                    concept_edit_input,
                    item.concept_vo,
                    "nci_concept_id",
                ),
                nci_concept_name=get_edit_input_or_previous_value(
                    concept_edit_input,
                    item.concept_vo,
                    "nci_concept_name",
                ),
                name=concept_edit_input.name or item.name,
                name_sentence_case=concept_edit_input.name_sentence_case
                or item.concept_vo.name_sentence_case,
                definition=concept_edit_input.definition or item.concept_vo.definition,
                abbreviation=concept_edit_input.abbreviation
                or item.concept_vo.abbreviation,
                is_research_lab=(
                    concept_edit_input.is_research_lab
                    if concept_edit_input.is_research_lab is not None
                    else item.concept_vo.is_research_lab
                ),
                molecular_weight=get_edit_input_or_previous_value(
                    concept_edit_input, item.concept_vo, "molecular_weight"
                ),
                topic_code=get_edit_input_or_previous_value(
                    concept_edit_input, item.concept_vo, "topic_code"
                ),
                adam_param_code=get_edit_input_or_previous_value(
                    concept_edit_input, item.concept_vo, "adam_param_code"
                ),
                is_required_for_activity=(
                    concept_edit_input.is_required_for_activity
                    if concept_edit_input.is_required_for_activity is not None
                    else item.concept_vo.is_required_for_activity
                ),
                is_default_selected_for_activity=(
                    concept_edit_input.is_default_selected_for_activity
                    if concept_edit_input.is_default_selected_for_activity is not None
                    else item.concept_vo.is_default_selected_for_activity
                ),
                is_data_sharing=(
                    concept_edit_input.is_data_sharing
                    if concept_edit_input.is_data_sharing is not None
                    else item.concept_vo.is_data_sharing
                ),
                is_legacy_usage=(
                    concept_edit_input.is_legacy_usage
                    if concept_edit_input.is_legacy_usage is not None
                    else item.concept_vo.is_legacy_usage
                ),
                is_derived=concept_edit_input.is_derived or item.concept_vo.is_derived,
                legacy_description=get_edit_input_or_previous_value(
                    concept_edit_input, item.concept_vo, "legacy_description"
                ),
                activity_groupings=activity_groupings,
                activity_instance_class_uid=concept_edit_input.activity_instance_class_uid
                or item.concept_vo.activity_instance_class_uid,
                activity_instance_class_name=None,
                activity_items=activity_items,
            ),
            concept_exists_by_library_and_property_value_callback=self._repos.activity_instance_repository.latest_concept_in_library_exists_by_property_value,
            ct_term_exists_by_uid_callback=self._repos.ct_term_name_repository.term_exists,
            unit_definition_exists_by_uid_callback=self._repos.unit_definition_repository.final_concept_exists,
            odm_item_exists_by_uid_callback=self._repos.odm_item_repository.final_concept_exists,
            get_final_activity_value_by_uid_callback=self._repos.activity_repository.final_concept_value,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            find_activity_item_class_by_uid_callback=self._repos.activity_item_class_repository.find_by_uid_2,
            find_activity_instance_class_by_uid_callback=self._repos.activity_instance_class_repository.find_by_uid_2,
            get_dimension_names_by_unit_definition_uids=self._repos.unit_definition_repository.get_dimension_names_by_unit_definition_uids,
        )
        return item

    def get_activity_instance_overview(
        self, activity_instance_uid: str, version: str | None = None
    ) -> ActivityInstanceOverview:
        NotFoundException.raise_if_not(
            self.repository.exists_by("uid", activity_instance_uid, True),
            "Activity Instance",
            activity_instance_uid,
        )
        overview = (
            self._repos.activity_instance_repository.get_activity_instance_overview(
                uid=activity_instance_uid, version=version
            )
        )
        return ActivityInstanceOverview.from_repository_input(overview=overview)

    def get_cosmos_activity_instance_overview(self, activity_instance_uid: str) -> dict:
        NotFoundException.raise_if_not(
            self.repository.exists_by("uid", activity_instance_uid, True),
            "Activity Instance",
            activity_instance_uid,
        )
        data: dict = self.repository.get_cosmos_activity_instance_overview(
            uid=activity_instance_uid
        )
        result: dict = {
            "packageDate": datetime.date.today().isoformat(),
            "packageType": "bc",
            "conceptId": data["activity_instance_value"]["nci_concept_id"],
            "ncitCode": data["activity_instance_value"]["nci_concept_id"],
            "href": constants.COSM0S_BASE_ITEM_HREF.format(
                data["activity_instance_value"]["nci_concept_id"]
            ),
            "categories": data["activity_subgroups"],
            "shortName": data["activity_instance_value"]["name"],
            "synonyms": data["activity_instance_value"]["abbreviation"],
            "resultScales": [
                constants.COSM0S_RESULT_SCALES_MAP.get(
                    data["activity_instance_class_name"], ""
                )
            ],
            "definition": data["activity_instance_value"]["definition"],
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
