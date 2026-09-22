import datetime
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.activities.activity_instance_repository import (
    ActivityInstanceAttributesRepository,
    ActivityInstanceGroupingsRepository,
    ActivityInstanceRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity_instance import (
    ActivityInstanceAR,
    ActivityInstanceAttributesAR,
    ActivityInstanceAttributesVO,
    ActivityInstanceGroupingsAR,
    ActivityInstanceGroupingsVO,
    ActivityInstanceGroupingVO,
    ActivityInstanceVO,
)
from clinical_mdr_api.domains.concepts.activities.activity_item import (
    ActivityItemVO,
    CTCodelistItem,
    CTTermItem,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
    ActivityInstanceAttributes,
    ActivityInstanceAttributesVersion,
    ActivityInstanceCreateInput,
    ActivityInstanceEditInput,
    ActivityInstanceGroupings,
    ActivityInstanceGroupingsBatchInput,
    ActivityInstanceGroupingsEditInput,
    ActivityInstanceGroupingsVersion,
    ActivityInstanceOverview,
    ActivityInstanceVersion,
    SimplifiedActivityItem,
)
from clinical_mdr_api.models.concepts.activities.activity_item import (
    CompactUnitDefinition,
)
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.services._utils import ensure_transaction
from clinical_mdr_api.services.concepts import constants
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
)
from common.exceptions import BusinessLogicException, NotFoundException
from common.utils import get_edit_input_or_previous_value


class ActivityInstanceService(ConceptGenericService[ActivityInstanceAR]):
    aggregate_class = ActivityInstanceAR
    repository_interface = ActivityInstanceRepository
    version_class = ActivityInstanceVersion

    def _get_parent_class_uid(self, uid: str) -> str | None:
        """Get parent class UID for a given activity instance class UID"""
        parent = self._repos.activity_instance_class_repository.get_parent_class(uid)
        return parent[0] if parent else None

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityInstanceAR
    ) -> ActivityInstance:
        return ActivityInstance.from_activity_ar(
            activity_ar=item_ar,
            find_activity_hierarchy_by_uid=self._repos.activity_repository.find_by_uid_2,
            find_activity_subgroup_by_uid=self._repos.activity_subgroup_repository.find_by_uid_2,
            find_activity_group_by_uid=self._repos.activity_group_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self,
        concept_input: ActivityInstanceCreateInput,
        library: LibraryVO,
        preview: bool = False,
    ) -> ActivityInstanceAR:
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
                    CTTermItem(
                        uid=ct_term.term_uid,
                        name=None,
                        codelist_uid=ct_term.codelist_uid,
                    )
                    for ct_term in item.ct_terms
                ]
                activity_items.append(
                    ActivityItemVO.from_repository_values(
                        is_adam_param_specific=item.is_adam_param_specific,
                        activity_item_class_uid=item.activity_item_class_uid,
                        activity_item_class_name=None,
                        ct_codelist=(
                            CTCodelistItem(uid=item.ct_codelist_uid)
                            if item.ct_codelist_uid
                            else None
                        ),
                        ct_terms=ct_terms,
                        unit_definitions=unit_definitions,
                        text_value=item.text_value,
                        is_activity_instance_id_specific=item.is_activity_instance_id_specific,
                    )
                )

        return ActivityInstanceAR.from_input_values(
            author_id=self.author_id,
            concept_vo=ActivityInstanceVO.from_repository_values(
                nci_concept_id=concept_input.nci_concept_id,
                nci_concept_name=concept_input.nci_concept_name,
                name=concept_input.name or "",
                name_sentence_case=concept_input.name_sentence_case or "",
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
            get_final_activity_value_by_uid_callback=self._repos.activity_repository.final_concept_value,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            activity_group_latest_is_final=self._repos.activity_group_repository.latest_concept_is_final,
            activity_subgroup_latest_is_final=self._repos.activity_subgroup_repository.latest_concept_is_final,
            get_activity_group_name=self._repos.activity_group_repository.get_latest_concept_name,
            get_activity_subgroup_name=self._repos.activity_subgroup_repository.get_latest_concept_name,
            find_activity_item_class_by_uid_callback=self._repos.activity_item_class_repository.find_by_uid_2,
            find_activity_instance_class_by_uid_callback=self._repos.activity_instance_class_repository.find_by_uid_2,
            preview=preview,
            get_dimension_names_by_unit_definition_uids=self._repos.unit_definition_repository.get_dimension_names_by_unit_definition_uids,
            get_parent_class_uid_callback=self._get_parent_class_uid,
            strict_mode=getattr(concept_input, "strict_mode", False),
        )

    def _edit_aggregate(
        self,
        item: ActivityInstanceAR,
        concept_edit_input: BaseModel,
    ) -> ActivityInstanceAR:
        # Editing happens on the different aggregate roots for attributes and groupings,
        # so this method is never used.
        raise NotImplementedError

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

    def get_activity_instance_items(
        self, activity_instance_uid: str, version: str | None = None
    ) -> list[SimplifiedActivityItem]:
        NotFoundException.raise_if_not(
            self.repository.exists_by("uid", activity_instance_uid, True),
            "Activity Instance",
            activity_instance_uid,
        )
        overview = self.repository.get_activity_instance_overview(
            uid=activity_instance_uid, version=version
        )
        return ActivityInstanceOverview.from_repository_input(
            overview=overview
        ).activity_items

    def get_cosmos_activity_instance_overview(
        self, activity_instance_uid: str
    ) -> dict[str, Any]:
        NotFoundException.raise_if_not(
            self.repository.exists_by("uid", activity_instance_uid, True),
            "Activity Instance",
            activity_instance_uid,
        )
        data: dict[Any, Any] = self.repository.get_cosmos_activity_instance_overview(
            uid=activity_instance_uid
        )
        result: dict[str, Any] = {
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


class ActivityInstanceAttributesService(
    ConceptGenericService[ActivityInstanceAttributesAR]
):
    aggregate_class = ActivityInstanceAttributesAR
    repository_interface = ActivityInstanceAttributesRepository
    version_class = ActivityInstanceAttributesVersion

    def _get_parent_class_uid(self, uid: str) -> str | None:
        """Get parent class UID for a given activity instance class UID"""
        parent = self._repos.activity_instance_class_repository.get_parent_class(uid)
        return parent[0] if parent else None

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityInstanceAttributesAR
    ) -> ActivityInstanceAttributes:
        return ActivityInstanceAttributes.from_activity_ar(
            activity_ar=item_ar,
        )

    def _create_aggregate_root(
        self,
        concept_input: ActivityInstanceCreateInput,
        library: LibraryVO,
        preview: bool = False,
    ) -> ActivityInstanceAttributesAR:
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
                    CTTermItem(
                        uid=ct_term.term_uid,
                        name=None,
                        codelist_uid=ct_term.codelist_uid,
                    )
                    for ct_term in item.ct_terms
                ]
                ct_codelist = (
                    CTCodelistItem(uid=item.ct_codelist_uid)
                    if item.ct_codelist_uid
                    else None
                )
                activity_items.append(
                    ActivityItemVO.from_repository_values(
                        is_adam_param_specific=item.is_adam_param_specific,
                        activity_item_class_uid=item.activity_item_class_uid,
                        activity_item_class_name=None,
                        ct_codelist=ct_codelist,
                        ct_terms=ct_terms,
                        unit_definitions=unit_definitions,
                        is_activity_instance_id_specific=item.is_activity_instance_id_specific,
                    )
                )

        return ActivityInstanceAttributesAR.from_input_values(
            author_id=self.author_id,
            concept_vo=ActivityInstanceAttributesVO.from_repository_values(
                nci_concept_id=concept_input.nci_concept_id,
                nci_concept_name=concept_input.nci_concept_name,
                name=concept_input.name or "",
                name_sentence_case=concept_input.name_sentence_case or "",
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
            find_activity_item_class_by_uid_callback=self._repos.activity_item_class_repository.find_by_uid_2,
            find_activity_instance_class_by_uid_callback=self._repos.activity_instance_class_repository.find_by_uid_2,
            preview=preview,
            get_dimension_names_by_unit_definition_uids=self._repos.unit_definition_repository.get_dimension_names_by_unit_definition_uids,
            get_parent_class_uid_callback=self._get_parent_class_uid,
            strict_mode=getattr(concept_input, "strict_mode", False),
        )

    def _edit_aggregate(
        self,
        item: ActivityInstanceAttributesAR,
        concept_edit_input: ActivityInstanceEditInput,
        perform_validation: bool = True,
    ) -> ActivityInstanceAttributesAR:
        fields_set = concept_edit_input.model_fields_set

        # Validate that restricted fields cannot be modified
        # Check activity_instance_class_uid
        if (
            "activity_instance_class_uid" in fields_set
            and concept_edit_input.activity_instance_class_uid is not None
            and concept_edit_input.activity_instance_class_uid
            != item.concept_vo.activity_instance_class_uid
        ):
            raise BusinessLogicException(
                msg="Activity instance class cannot be modified after creation.",
            )

        # Check topic_code
        if "topic_code" in fields_set:
            existing_topic_code = item.concept_vo.topic_code
            new_topic_code = get_edit_input_or_previous_value(
                concept_edit_input, item.concept_vo, "topic_code"
            )
            if existing_topic_code != new_topic_code:
                raise BusinessLogicException(
                    msg="Topic code cannot be modified after creation.",
                )

        # Check is_research_lab
        if concept_edit_input.is_research_lab is not None:
            if concept_edit_input.is_research_lab != item.concept_vo.is_research_lab:
                raise BusinessLogicException(
                    msg="Research lab flag cannot be modified after creation.",
                )

        # Check activity items with param/paramcd - their ct_terms cannot be modified
        if (
            "activity_items" in fields_set
            and concept_edit_input.activity_items is not None
        ):
            # Create a map of existing activity items by their activity_item_class_uid
            existing_items_by_class_uid: dict[str, ActivityItemVO] = {}
            for existing_item in item.concept_vo.activity_items:
                existing_items_by_class_uid[existing_item.activity_item_class_uid] = (
                    existing_item
                )

            # Check each incoming activity item
            for incoming_item in concept_edit_input.activity_items:
                # Find the corresponding existing item
                matched_existing_item = existing_items_by_class_uid.get(
                    incoming_item.activity_item_class_uid
                )

                if (
                    matched_existing_item is not None
                    and matched_existing_item.is_adam_param_specific
                ):
                    # This activity item has param/paramcd - ct_terms cannot be modified
                    existing_ct_term_uids = {
                        term.uid for term in matched_existing_item.ct_terms
                    }
                    incoming_ct_term_uids = {
                        ct_term.term_uid for ct_term in incoming_item.ct_terms
                    }

                    if existing_ct_term_uids != incoming_ct_term_uids:
                        raise BusinessLogicException(
                            msg="Activity items with param/paramcd cannot have their terms (ct_terms) modified after creation.",
                        )

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
                        CTTermItem(
                            uid=ct_term.term_uid,
                            name=None,
                            codelist_uid=ct_term.codelist_uid,
                        )
                        for ct_term in activity_item.ct_terms
                    ]
                    activity_items.append(
                        ActivityItemVO.from_repository_values(
                            is_adam_param_specific=activity_item.is_adam_param_specific,
                            activity_item_class_uid=activity_item.activity_item_class_uid,
                            activity_item_class_name=None,
                            ct_codelist=(
                                CTCodelistItem(uid=activity_item.ct_codelist_uid)
                                if activity_item.ct_codelist_uid
                                else None
                            ),
                            ct_terms=ct_terms,
                            unit_definitions=unit_definitions,
                            text_value=activity_item.text_value,
                            is_activity_instance_id_specific=activity_item.is_activity_instance_id_specific,
                        )
                    )
        else:
            activity_items = item.concept_vo.activity_items

        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=ActivityInstanceAttributesVO.from_repository_values(
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
                or item.name_sentence_case,
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
                activity_instance_class_uid=concept_edit_input.activity_instance_class_uid
                or item.concept_vo.activity_instance_class_uid,
                activity_instance_class_name=None,
                activity_items=activity_items,
            ),
            concept_exists_by_library_and_property_value_callback=self._repos.activity_instance_repository.latest_concept_in_library_exists_by_property_value,
            ct_term_exists_by_uid_callback=self._repos.ct_term_name_repository.term_exists,
            unit_definition_exists_by_uid_callback=self._repos.unit_definition_repository.final_concept_exists,
            find_activity_item_class_by_uid_callback=self._repos.activity_item_class_repository.find_by_uid_2,
            find_activity_instance_class_by_uid_callback=self._repos.activity_instance_class_repository.find_by_uid_2,
            get_dimension_names_by_unit_definition_uids=self._repos.unit_definition_repository.get_dimension_names_by_unit_definition_uids,
            get_parent_class_uid_callback=self._get_parent_class_uid,
            strict_mode=(
                concept_edit_input.strict_mode
                if concept_edit_input.strict_mode is not None
                else False
            ),
            perform_validation=perform_validation,
        )
        return item

    @ensure_transaction(db)
    def inactivate_final(
        self,
        uid: str,
        cascade_inactivate: bool = False,
        force_new_value_node: bool = False,
    ) -> BaseModel:
        """
        Inactivates the attributes and groupings of an activity instance.

        Each part must currently be in Final or Retired status (a part already
        in Retired is left untouched so the operation is idempotent and can
        recover from a previously-stuck mixed state). At least one part must
        be Final, otherwise there is nothing to do.
        """
        attributes_item = self._find_by_uid_or_raise_not_found(uid, for_update=True)

        groupings_repository = self._repos.activity_instance_groupings_repository
        groupings_item = groupings_repository.find_by_uid_2(uid=uid, for_update=True)
        NotFoundException.raise_if(
            groupings_item is None,
            msg=(f"Activity Instance Groupings with UID '{uid}' doesn't exist."),
        )

        attrs_status = attributes_item.item_metadata.status
        groupings_status = groupings_item.item_metadata.status
        allowed = {LibraryItemStatus.FINAL, LibraryItemStatus.RETIRED}

        BusinessLogicException.raise_if(
            attrs_status not in allowed,
            msg=(
                "Cannot inactivate: activity instance attributes must be in"
                f" Final or Retired status (current: {attrs_status.value})."
            ),
        )
        BusinessLogicException.raise_if(
            groupings_status not in allowed,
            msg=(
                "Cannot inactivate: activity instance groupings must be in"
                f" Final or Retired status (current: {groupings_status.value})."
            ),
        )
        BusinessLogicException.raise_if(
            attrs_status == LibraryItemStatus.RETIRED
            and groupings_status == LibraryItemStatus.RETIRED,
            msg=(
                "Cannot inactivate: both activity instance attributes and"
                " groupings are already Retired."
            ),
        )

        if attrs_status == LibraryItemStatus.FINAL:
            attributes_item.inactivate(
                author_id=self.author_id, force_new_value_node=force_new_value_node
            )
            self.repository.save(
                attributes_item, force_new_value_node=force_new_value_node
            )
        if groupings_status == LibraryItemStatus.FINAL:
            groupings_item.inactivate(
                author_id=self.author_id, force_new_value_node=force_new_value_node
            )
            groupings_repository.save(
                groupings_item, force_new_value_node=force_new_value_node
            )
        return self._transform_aggregate_root_to_pydantic_model(attributes_item)

    @ensure_transaction(db)
    def reactivate_retired(
        self,
        uid: str,
        cascade_reactivate: bool = False,
        force_new_value_node: bool = False,
    ) -> BaseModel:
        """
        Reactivates the attributes and groupings of an activity instance.

        Each part must currently be in Retired or Final status (a part already
        in Final is left untouched so the operation is idempotent and can
        recover from a previously-stuck mixed state). At least one part must
        be Retired, otherwise there is nothing to do.
        """
        attributes_item = self._find_by_uid_or_raise_not_found(uid, for_update=True)

        groupings_repository = self._repos.activity_instance_groupings_repository
        groupings_item = groupings_repository.find_by_uid_2(uid=uid, for_update=True)
        NotFoundException.raise_if(
            groupings_item is None,
            msg=(f"Activity Instance Groupings with UID '{uid}' doesn't exist."),
        )

        attrs_status = attributes_item.item_metadata.status
        groupings_status = groupings_item.item_metadata.status
        allowed = {LibraryItemStatus.RETIRED, LibraryItemStatus.FINAL}

        BusinessLogicException.raise_if(
            attrs_status not in allowed,
            msg=(
                "Cannot reactivate: activity instance attributes must be in"
                f" Retired or Final status (current: {attrs_status.value})."
            ),
        )
        BusinessLogicException.raise_if(
            groupings_status not in allowed,
            msg=(
                "Cannot reactivate: activity instance groupings must be in"
                f" Retired or Final status (current: {groupings_status.value})."
            ),
        )
        BusinessLogicException.raise_if(
            attrs_status == LibraryItemStatus.FINAL
            and groupings_status == LibraryItemStatus.FINAL,
            msg=(
                "Cannot reactivate: both activity instance attributes and"
                " groupings are already Final."
            ),
        )

        if attrs_status == LibraryItemStatus.RETIRED:
            attributes_item.reactivate(
                author_id=self.author_id, force_new_value_node=force_new_value_node
            )
            self.repository.save(
                attributes_item, force_new_value_node=force_new_value_node
            )
        if groupings_status == LibraryItemStatus.RETIRED:
            groupings_item.reactivate(
                author_id=self.author_id, force_new_value_node=force_new_value_node
            )
            groupings_repository.save(
                groupings_item, force_new_value_node=force_new_value_node
            )
        return self._transform_aggregate_root_to_pydantic_model(attributes_item)


class ActivityInstanceGroupingsService(
    ConceptGenericService[ActivityInstanceGroupingsAR]
):
    aggregate_class = ActivityInstanceGroupingsAR
    repository_interface = ActivityInstanceGroupingsRepository
    version_class = ActivityInstanceGroupingsVersion

    def _get_parent_class_uid(self, uid: str) -> str | None:
        """Get parent class UID for a given activity instance class UID"""
        parent = self._repos.activity_instance_class_repository.get_parent_class(uid)
        return parent[0] if parent else None

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityInstanceGroupingsAR
    ) -> ActivityInstanceGroupings:
        return ActivityInstanceGroupings.from_activity_ar(
            activity_ar=item_ar,
            find_activity_hierarchy_by_uid=self._repos.activity_repository.find_by_uid_2,
            find_activity_subgroup_by_uid=self._repos.activity_subgroup_repository.find_by_uid_2,
            find_activity_group_by_uid=self._repos.activity_group_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self,
        concept_input: ActivityInstanceCreateInput,
        library: LibraryVO,
        preview: bool = False,
    ) -> ActivityInstanceGroupingsAR:
        # Groupings are never created by themselves, creation only happens together with attributes,
        # so we can raise NotImplementedError here and use the del
        raise NotImplementedError

    def _edit_aggregate(
        self,
        item: ActivityInstanceGroupingsAR,
        concept_edit_input: ActivityInstanceGroupingsEditInput,
        perform_validation: bool = True,
    ) -> ActivityInstanceGroupingsAR:
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

        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=ActivityInstanceGroupingsVO.from_repository_values(
                activity_groupings=activity_groupings,
            ),
            get_final_activity_value_by_uid_callback=self._repos.activity_repository.final_concept_value,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            perform_validation=perform_validation,
        )
        return item

    @ensure_transaction(db)
    def batch_update_groupings(
        self,
        batch_input: ActivityInstanceGroupingsBatchInput,
    ) -> list[ActivityInstanceGroupings]:
        """
        Batch-update groupings for multiple activity instances in a single transaction.

        For each instance in the batch:
        1. Create a new groupings version (draft) if not already in draft status.
        2. Edit the groupings with the provided data.
        3. Approve the new groupings version.

        If any step fails, the entire transaction is rolled back.

        Optimized to minimize DB round-trips:
        - Pre-caches all validation and transform lookups upfront
        - Reuses in-memory aggregates between steps (no redundant reloads)
        - Transforms use cached data (no additional DB calls)

        Args:
            batch_input: The batch input containing instance UIDs and their new groupings.

        Returns:
            List of approved ActivityInstanceGroupings for each processed instance.
        """
        # Pre-collect all unique UIDs from the entire batch
        all_activity_uids: set[str] = set()
        all_group_uids: set[str] = set()
        all_subgroup_uids: set[str] = set()
        for batch_item in batch_input.items:
            for g in batch_item.activity_groupings:
                if g.activity_uid:
                    all_activity_uids.add(g.activity_uid)
                if g.activity_group_uid:
                    all_group_uids.add(g.activity_group_uid)
                if g.activity_subgroup_uid:
                    all_subgroup_uids.add(g.activity_subgroup_uid)

        # Pre-fetch validation data (one DB call per unique UID, not per item*grouping)
        activity_value_cache = {
            uid: self._repos.activity_repository.final_concept_value(uid)
            for uid in all_activity_uids
        }
        group_exists_cache = {
            uid: self._repos.activity_group_repository.final_concept_exists(uid)
            for uid in all_group_uids
        }
        subgroup_exists_cache = {
            uid: self._repos.activity_subgroup_repository.final_concept_exists(uid)
            for uid in all_subgroup_uids
        }

        # Pre-fetch transform data (find_by_uid_2 for name resolution in response)
        activity_ar_cache = {
            uid: self._repos.activity_repository.find_by_uid_2(uid)
            for uid in all_activity_uids
        }
        group_ar_cache = {
            uid: self._repos.activity_group_repository.find_by_uid_2(uid)
            for uid in all_group_uids
        }
        subgroup_ar_cache = {
            uid: self._repos.activity_subgroup_repository.find_by_uid_2(uid)
            for uid in all_subgroup_uids
        }

        results = []
        for batch_item in batch_input.items:
            uid = batch_item.activity_instance_uid

            # 1. Load aggregate once and create new draft version
            item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
            try:
                item.create_new_version(author_id=self.author_id)
                self.repository.save(item)
            except BusinessLogicException as exc:
                if (
                    exc.msg
                    != "New draft version can be created only for FINAL versions."
                ):
                    raise

            # 2. Edit groupings on in-memory aggregate using cached validation (no reload)
            activity_groupings = [
                ActivityInstanceGroupingVO(
                    activity_uid=g.activity_uid,
                    activity_group_uid=g.activity_group_uid,
                    activity_subgroup_uid=g.activity_subgroup_uid,
                )
                for g in batch_item.activity_groupings
            ]
            item.edit_draft(
                author_id=self.author_id,
                change_description=batch_input.change_description,
                concept_vo=ActivityInstanceGroupingsVO.from_repository_values(
                    activity_groupings=activity_groupings,
                ),
                get_final_activity_value_by_uid_callback=activity_value_cache.get,
                activity_group_exists=lambda uid_val: group_exists_cache.get(
                    uid_val, False
                ),
                activity_subgroup_exists=lambda uid_val: subgroup_exists_cache.get(
                    uid_val, False
                ),
            )
            self.repository.save(item)

            # 3. Approve on in-memory aggregate and save
            item.approve(author_id=self.author_id)
            self.repository.save(item)

            # 4. Transform using cached lookups (no additional DB calls)
            results.append(
                ActivityInstanceGroupings.from_activity_ar(
                    activity_ar=item,
                    find_activity_hierarchy_by_uid=lambda uid_val, **_: activity_ar_cache.get(
                        uid_val
                    ),
                    find_activity_subgroup_by_uid=lambda uid_val, **_: subgroup_ar_cache.get(
                        uid_val
                    ),
                    find_activity_group_by_uid=lambda uid_val, **_: group_ar_cache.get(
                        uid_val
                    ),
                )
            )

        return results
