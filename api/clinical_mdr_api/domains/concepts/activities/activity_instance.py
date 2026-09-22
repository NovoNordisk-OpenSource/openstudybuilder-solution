from dataclasses import dataclass, field
from typing import AbstractSet, Callable, Self

from neo4j.graph import Node

from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_item_class import (
    ActivityItemClassAR,
)
from clinical_mdr_api.domains.concepts.activities.activity import ActivityGroupingVO
from clinical_mdr_api.domains.concepts.activities.activity_item import ActivityItemVO
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domains.enums import LibraryItemStatus, ObjectAction
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
    VersioningActionMixin,
)
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    ValidationException,
)


@dataclass(frozen=True)
class ActivityInstanceGroupingVO(ActivityGroupingVO):
    activity_uid: str | None = None
    activity_version: str | None = None
    activity_name: str | None = None


@dataclass(frozen=True)
class ActivityInstanceAttributesVO(ConceptVO):
    """
    The ActivityInstanceAttributesVO acts as the value object for a single ActivityInstanceAttributes aggregate
    """

    nci_concept_id: str | None
    nci_concept_name: str | None
    is_research_lab: bool
    molecular_weight: float | None
    topic_code: str | None
    adam_param_code: str | None
    is_required_for_activity: bool
    is_default_selected_for_activity: bool
    is_data_sharing: bool
    is_legacy_usage: bool
    is_derived: bool
    legacy_description: str | None
    activity_instance_class_uid: str
    activity_instance_class_name: str | None
    activity_items: list[ActivityItemVO]

    @classmethod
    def from_repository_values(
        cls,
        nci_concept_id: str | None,
        nci_concept_name: str | None,
        name: str,
        name_sentence_case: str,
        definition: str | None,
        abbreviation: str | None,
        is_research_lab: bool,
        molecular_weight: float | None,
        topic_code: str | None,
        adam_param_code: str | None,
        is_required_for_activity: bool,
        is_default_selected_for_activity: bool,
        is_data_sharing: bool,
        is_legacy_usage: bool,
        is_derived: bool,
        legacy_description: str | None,
        activity_instance_class_uid: str,
        activity_instance_class_name: str | None,
        activity_items: list[ActivityItemVO],
    ) -> Self:
        activity_instance_vo = cls(
            nci_concept_id=nci_concept_id,
            nci_concept_name=nci_concept_name,
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
            activity_instance_class_uid=activity_instance_class_uid,
            activity_instance_class_name=activity_instance_class_name,
            is_research_lab=is_research_lab,
            molecular_weight=molecular_weight,
            topic_code=topic_code,
            adam_param_code=adam_param_code,
            is_required_for_activity=is_required_for_activity,
            is_default_selected_for_activity=is_default_selected_for_activity,
            is_data_sharing=is_data_sharing,
            is_legacy_usage=is_legacy_usage,
            is_derived=is_derived,
            legacy_description=legacy_description,
            activity_items=activity_items if activity_items is not None else [],
        )

        return activity_instance_vo

    def validate(  # pylint: disable=too-many-locals
        self,
        ct_term_exists_by_uid_callback: Callable[[str], bool],
        unit_definition_exists_by_uid_callback: Callable[[str], bool],
        find_activity_item_class_by_uid_callback: Callable[
            ..., ActivityItemClassAR | None
        ],
        find_activity_instance_class_by_uid_callback: Callable[
            ..., ActivityInstanceClassAR | None
        ],
        get_dimension_names_by_unit_definition_uids: Callable[[list[str]], list[str]],
        activity_instance_exists_by_property_value: Callable[
            [str, str, str], bool
        ] = lambda x, y, z: True,
        previous_name: str | None = None,
        previous_topic_code: str | None = None,
        library_name: str | None = None,
        preview: bool = False,
        get_parent_class_uid_callback: Callable[[str], str | None] = lambda _: None,
        strict_mode: bool = False,
    ) -> None:
        if not preview:
            self.validate_name_sentence_case()

        if self.name and library_name is not None:
            existing_name = activity_instance_exists_by_property_value(
                library_name, "name", self.name
            )
            AlreadyExistsException.raise_if(
                existing_name and previous_name != self.name,
                "Activity Instance",
                self.name,
                "Name",
            )
        if self.topic_code is not None and library_name is not None:
            existing_topic_code = activity_instance_exists_by_property_value(
                library_name, "topic_code", self.topic_code
            )
            AlreadyExistsException.raise_if(
                existing_topic_code and previous_topic_code != self.topic_code,
                "Activity Instance",
                self.topic_code,
                "Topic Code",
            )

        activity_item_class_uids = [
            item.activity_item_class_uid for item in self.activity_items
        ]
        seen_activity_item_class_uids = []
        duplicate_activity_item_class_uids = []
        for activity_item_class_uid in activity_item_class_uids:
            if activity_item_class_uid in seen_activity_item_class_uids:
                duplicate_activity_item_class_uids.append(activity_item_class_uid)
            else:
                seen_activity_item_class_uids.append(activity_item_class_uid)

        if duplicate_activity_item_class_uids:
            raise BusinessLogicException(
                msg=f"The following Activity Item Class(es) have been associated to more than one Activity Item: {",".join(duplicate_activity_item_class_uids)}"
            )

        for activity_item in self.activity_items:
            activity_item_class = find_activity_item_class_by_uid_callback(
                activity_item.activity_item_class_uid
            )

            if activity_item_class:
                aic = find_activity_instance_class_by_uid_callback(
                    self.activity_instance_class_uid
                )
                if (
                    aic
                    and aic.activity_instance_class_vo.level == 2
                    and next(
                        (
                            itm.is_adam_param_specific_enabled
                            for itm in aic.activity_instance_class_vo.activity_item_classes
                            if itm.uid == activity_item_class.uid
                        ),
                        False,
                    )
                ):
                    continue

                for (
                    i
                ) in (
                    activity_item_class.activity_item_class_vo.activity_instance_classes
                ):
                    if (
                        self.activity_instance_class_uid == i.uid
                        and not i.is_adam_param_specific_enabled
                        and activity_item.is_adam_param_specific
                    ):
                        raise BusinessLogicException(
                            msg="Activity Item's 'is_adam_param_specific' cannot be 'True' when the Activity Item Class' 'is_adam_param_specific_enabled' is 'False'.",
                        )

            BusinessLogicException.raise_if_not(
                activity_item_class,
                msg=f"{type(self).__name__} tried to connect to non-existent or non-final Activity Item Class with UID '{activity_item.activity_item_class_uid}'.",
            )
            for ct_term in activity_item.ct_terms:
                BusinessLogicException.raise_if_not(
                    ct_term_exists_by_uid_callback(ct_term.uid),
                    msg=f"{type(self).__name__} tried to connect to non-existent or non-final CT Term with UID '{ct_term.uid}'.",
                )
            for unit in activity_item.unit_definitions:
                BusinessLogicException.raise_if_not(
                    unit.uid and unit_definition_exists_by_uid_callback(unit.uid),
                    msg=f"{type(self).__name__} tried to connect to non-existent or non-final Unit Definition with UID '{unit.uid}'.",
                )
            if activity_item.is_activity_instance_id_specific:
                BusinessLogicException.raise_if(
                    activity_item.ct_codelist is not None,
                    msg="An ActivityItem with 'is_activity_instance_id_specific' set to true must not have a ct_codelist.",
                )
                BusinessLogicException.raise_if(
                    len(activity_item.ct_terms) > 1,
                    msg="An ActivityItem with 'is_activity_instance_id_specific' set to true must not have more than one ct_term.",
                )
                BusinessLogicException.raise_if(
                    len(activity_item.unit_definitions) > 1,
                    msg="An ActivityItem with 'is_activity_instance_id_specific' set to true must not have more than one unit_definition.",
                )

        activity_instance_class = find_activity_instance_class_by_uid_callback(
            self.activity_instance_class_uid
        )
        ValidationException.raise_if_not(
            activity_instance_class,
            msg=f"Activity Instance Class with UID '{self.activity_instance_class_uid}' doesn't exist.",
        )

        # Validate that all mandatory Activity Item Classes for the selected
        # Activity Instance Class are present in the create input just if strict_mode is True
        if strict_mode:
            required_item_class_uids = {
                rel.uid
                for rel in activity_instance_class.activity_instance_class_vo.activity_item_classes
                if rel.mandatory
            }
            selected_item_class_uids = {
                activity_item.activity_item_class_uid
                for activity_item in self.activity_items
            }
            missing_required_uids = required_item_class_uids.difference(
                selected_item_class_uids
            )

            if missing_required_uids:
                # Get names for missing item classes
                missing_item_class_names = []
                for uid in sorted(missing_required_uids):
                    item_class = find_activity_item_class_by_uid_callback(uid)
                    if item_class:
                        missing_item_class_names.append(item_class.name)
                    else:
                        missing_item_class_names.append(
                            uid
                        )  # Fallback to UID if not found

                BusinessLogicException.raise_if(
                    True,
                    msg=(
                        "The following mandatory Activity Item Classes must be selected for "
                        f"Activity Instance Class '{activity_instance_class.name}': "
                        + ", ".join(missing_item_class_names)
                    ),
                )

        # Check parent class mandatory items if current class has level 3 and strict_mode is True
        current_level = activity_instance_class.activity_instance_class_vo.level
        if current_level == 3 and strict_mode:

            parent_class_uid = get_parent_class_uid_callback(
                self.activity_instance_class_uid
            )
            if parent_class_uid:
                parent_class = find_activity_instance_class_by_uid_callback(
                    parent_class_uid
                )
                if parent_class and parent_class.activity_instance_class_vo.level == 2:
                    # Get mandatory item classes from parent (level 2)
                    parent_required_item_class_uids = {
                        rel.uid
                        for rel in parent_class.activity_instance_class_vo.activity_item_classes
                        if rel.mandatory
                    }
                    # Check that parent mandatory items are selected with CT terms or unit definitions
                    # (i.e., they exist in activity_items AND have CT terms or unit definitions)
                    parent_missing_required_uids = []
                    for required_uid in parent_required_item_class_uids:
                        # Check if this item class is selected
                        matching_item = next(
                            (
                                item
                                for item in self.activity_items
                                if item.activity_item_class_uid == required_uid
                            ),
                            None,
                        )
                        if not matching_item:
                            parent_missing_required_uids.append(required_uid)
                        elif (
                            not matching_item.ct_terms
                            and not matching_item.unit_definitions
                        ):
                            # Item is selected but has neither CT terms nor unit definitions
                            parent_missing_required_uids.append(required_uid)

                    if parent_missing_required_uids:
                        # Get names for missing item classes
                        parent_missing_item_class_names = []
                        for uid in sorted(parent_missing_required_uids):
                            item_class = find_activity_item_class_by_uid_callback(uid)
                            if item_class:
                                parent_missing_item_class_names.append(item_class.name)
                            else:
                                parent_missing_item_class_names.append(
                                    uid
                                )  # Fallback to UID if not found

                        BusinessLogicException.raise_if(
                            True,
                            msg=(
                                "The following mandatory Activity Item Classes from the parent "
                                f"Activity Instance Class '{parent_class.name}' (level 2) must have CT terms or unit definitions selected for "
                                f"Activity Instance Class '{activity_instance_class.name}' (level 3): "
                                + ", ".join(parent_missing_item_class_names)
                            ),
                        )

        unit_dimension_names = get_dimension_names_by_unit_definition_uids(
            [
                unit.uid
                for activity_item in self.activity_items
                for unit in activity_item.unit_definitions
                if unit.uid is not None
            ]
        )

        ValidationException.raise_if(
            self.molecular_weight is not None
            and (
                activity_instance_class.activity_instance_class_vo.name
                != "NumericFindings"
                or not any(
                    "concentration" in unit_dimension_name.casefold()
                    for unit_dimension_name in unit_dimension_names
                )
            ),
            msg="Molecular Weight can only be set for NumericFindings that has concentration units.",
        )


@dataclass(frozen=True)
class ActivityInstanceGroupingsVO:
    """
    The ActivityInstanceGroupingsVO acts as the value object for a single ActivityInstanceGroupings aggregate
    """

    activity_name: str | None
    activity_groupings: list[ActivityInstanceGroupingVO]

    @classmethod
    def from_repository_values(
        cls,
        activity_groupings: list[ActivityInstanceGroupingVO],
        activity_name: str | None = None,
    ) -> Self:
        activity_instance_vo = cls(
            activity_groupings=(
                activity_groupings if activity_groupings is not None else []
            ),
            activity_name=activity_name,
        )

        return activity_instance_vo

    def validate(  # pylint: disable=too-many-locals
        self,
        get_final_activity_value_by_uid_callback: Callable[[str], Node | None],
        activity_subgroup_exists: Callable[[str], bool],
        activity_group_exists: Callable[[str], bool],
        activity_subgroup_latest_is_final: Callable[[str], bool] = lambda x: True,
        activity_group_latest_is_final: Callable[[str], bool] = lambda x: True,
        get_activity_subgroup_name: Callable[[str], str | None] = lambda x: None,
        get_activity_group_name: Callable[[str], str | None] = lambda x: None,
        update: bool = False,
    ) -> None:

        if not self.activity_groupings:
            raise BusinessLogicException(
                msg="Activity Instance must have at least one grouping",
            )

        for activity_grouping in self.activity_groupings:
            if activity_grouping.activity_uid is None:
                raise BusinessLogicException(
                    msg="Activity UID missing for one of the Activity Groupings"
                )
            activity = get_final_activity_value_by_uid_callback(
                activity_grouping.activity_uid
            )
            if activity is None:
                raise BusinessLogicException(
                    msg=f"{type(self).__name__} tried to connect to non-existent or non-final Activity with UID '{activity_grouping.activity_uid}'.",
                )
            BusinessLogicException.raise_if_not(
                activity["is_data_collected"],
                msg=f"{type(self).__name__} tried to connect to Activity without data collection",
            )

            # Check that the selected subgroup and group exist
            BusinessLogicException.raise_if_not(
                activity_subgroup_exists(activity_grouping.activity_subgroup_uid),
                msg=f"{type(self).__name__} tried to connect to non-existent Activity Sub Group with UID '{activity_grouping.activity_subgroup_uid}'.",
            )
            BusinessLogicException.raise_if_not(
                activity_group_exists(activity_grouping.activity_group_uid),
                msg=f"{type(self).__name__} tried to connect to non-existent Activity Group with UID '{activity_grouping.activity_group_uid}'.",
            )

            # Check that the LATEST version of the selected subgroup and group are Final (only during creation)
            if not update:  # This is a creation, not an edit
                if not activity_subgroup_latest_is_final(
                    activity_grouping.activity_subgroup_uid
                ):
                    # Get the subgroup name for a better error message
                    name = get_activity_subgroup_name(
                        activity_grouping.activity_subgroup_uid
                    )
                    if name:
                        subgroup_str = (
                            f"'{name}' ({activity_grouping.activity_subgroup_uid})"
                        )
                    else:
                        subgroup_str = f"'{activity_grouping.activity_subgroup_uid}'"

                    raise BusinessLogicException(
                        msg=f"Cannot create activity instance: Activity Sub Group {subgroup_str} is currently not in Final status."
                    )
                if not activity_group_latest_is_final(
                    activity_grouping.activity_group_uid
                ):
                    # Get the group name for a better error message
                    name = get_activity_group_name(activity_grouping.activity_group_uid)
                    if name:
                        group_str = f"'{name}' ({activity_grouping.activity_group_uid})"
                    else:
                        group_str = f"'{activity_grouping.activity_group_uid}'"

                    raise BusinessLogicException(
                        msg=f"Cannot create activity instance: Activity Group {group_str} is currently not in Final status."
                    )


@dataclass(frozen=True)
class ActivityInstanceVO(ConceptVO):
    """
    The ActivityInstanceVO acts as the value object for a single ActivityInstance aggregate.
    Combines ActivityInstanceAttributesVO with grouping information.
    """

    activity_instance_attributes: ActivityInstanceAttributesVO
    activity_name: str | None
    activity_groupings: list[ActivityInstanceGroupingVO]

    @property
    def nci_concept_id(self) -> str | None:
        return self.activity_instance_attributes.nci_concept_id

    @property
    def nci_concept_name(self) -> str | None:
        return self.activity_instance_attributes.nci_concept_name

    @classmethod
    def from_repository_values(
        cls,
        nci_concept_id: str | None,
        nci_concept_name: str | None,
        name: str,
        name_sentence_case: str,
        definition: str | None,
        abbreviation: str | None,
        is_research_lab: bool,
        molecular_weight: float | None,
        topic_code: str | None,
        adam_param_code: str | None,
        is_required_for_activity: bool,
        is_default_selected_for_activity: bool,
        is_data_sharing: bool,
        is_legacy_usage: bool,
        is_derived: bool,
        legacy_description: str | None,
        activity_groupings: list[ActivityInstanceGroupingVO],
        activity_instance_class_uid: str,
        activity_instance_class_name: str | None,
        activity_items: list[ActivityItemVO],
        activity_name: str | None = None,
    ) -> Self:
        attributes_vo = ActivityInstanceAttributesVO.from_repository_values(
            nci_concept_id=nci_concept_id,
            nci_concept_name=nci_concept_name,
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_research_lab=is_research_lab,
            molecular_weight=molecular_weight,
            topic_code=topic_code,
            adam_param_code=adam_param_code,
            is_required_for_activity=is_required_for_activity,
            is_default_selected_for_activity=is_default_selected_for_activity,
            is_data_sharing=is_data_sharing,
            is_legacy_usage=is_legacy_usage,
            is_derived=is_derived,
            legacy_description=legacy_description,
            activity_instance_class_uid=activity_instance_class_uid,
            activity_instance_class_name=activity_instance_class_name,
            activity_items=activity_items if activity_items is not None else [],
        )

        activity_instance_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
            activity_instance_attributes=attributes_vo,
            activity_groupings=(
                activity_groupings if activity_groupings is not None else []
            ),
            activity_name=activity_name,
        )

        return activity_instance_vo

    def validate(  # pylint: disable=too-many-locals
        self,
        get_final_activity_value_by_uid_callback: Callable[[str], Node | None],
        activity_subgroup_exists: Callable[[str], bool],
        activity_group_exists: Callable[[str], bool],
        ct_term_exists_by_uid_callback: Callable[[str], bool],
        unit_definition_exists_by_uid_callback: Callable[[str], bool],
        find_activity_item_class_by_uid_callback: Callable[
            ..., ActivityItemClassAR | None
        ],
        find_activity_instance_class_by_uid_callback: Callable[
            ..., ActivityInstanceClassAR | None
        ],
        get_dimension_names_by_unit_definition_uids: Callable[[list[str]], list[str]],
        activity_instance_exists_by_property_value: Callable[
            [str, str, str], bool
        ] = lambda x, y, z: True,
        previous_name: str | None = None,
        previous_topic_code: str | None = None,
        library_name: str | None = None,
        preview: bool = False,
        activity_subgroup_latest_is_final: Callable[[str], bool] = lambda x: True,
        activity_group_latest_is_final: Callable[[str], bool] = lambda x: True,
        get_activity_subgroup_name: Callable[[str], str | None] = lambda x: None,
        get_activity_group_name: Callable[[str], str | None] = lambda x: None,
        get_parent_class_uid_callback: Callable[[str], str | None] = lambda _: None,
        strict_mode: bool = False,
    ) -> None:
        # Delegate attributes validation to the embedded ActivityInstanceAttributesVO
        self.activity_instance_attributes.validate(
            ct_term_exists_by_uid_callback=ct_term_exists_by_uid_callback,
            unit_definition_exists_by_uid_callback=unit_definition_exists_by_uid_callback,
            find_activity_item_class_by_uid_callback=find_activity_item_class_by_uid_callback,
            find_activity_instance_class_by_uid_callback=find_activity_instance_class_by_uid_callback,
            get_dimension_names_by_unit_definition_uids=get_dimension_names_by_unit_definition_uids,
            activity_instance_exists_by_property_value=activity_instance_exists_by_property_value,
            previous_name=previous_name,
            previous_topic_code=previous_topic_code,
            library_name=library_name,
            preview=preview,
            get_parent_class_uid_callback=get_parent_class_uid_callback,
            strict_mode=strict_mode,
        )

        if not self.activity_groupings:
            raise BusinessLogicException(
                msg="Activity Instance must have at least one grouping",
            )

        for activity_grouping in self.activity_groupings:
            if activity_grouping.activity_uid is None:
                raise BusinessLogicException(
                    msg="Activity UID missing for one of the Activity Groupings"
                )
            activity = get_final_activity_value_by_uid_callback(
                activity_grouping.activity_uid
            )
            if activity is None:
                raise BusinessLogicException(
                    msg=f"{type(self).__name__} tried to connect to non-existent or non-final Activity with UID '{activity_grouping.activity_uid}'.",
                )
            BusinessLogicException.raise_if_not(
                activity["is_data_collected"],
                msg=f"{type(self).__name__} tried to connect to Activity without data collection",
            )

            # Check that the selected subgroup and group exist
            BusinessLogicException.raise_if_not(
                activity_subgroup_exists(activity_grouping.activity_subgroup_uid),
                msg=f"{type(self).__name__} tried to connect to non-existent Activity Sub Group with UID '{activity_grouping.activity_subgroup_uid}'.",
            )
            BusinessLogicException.raise_if_not(
                activity_group_exists(activity_grouping.activity_group_uid),
                msg=f"{type(self).__name__} tried to connect to non-existent Activity Group with UID '{activity_grouping.activity_group_uid}'.",
            )

            # Check that the LATEST version of the selected subgroup and group are Final (only during creation)
            if previous_name is None:  # This is a creation, not an edit
                if not activity_subgroup_latest_is_final(
                    activity_grouping.activity_subgroup_uid
                ):
                    # Get the subgroup name for a better error message
                    name = get_activity_subgroup_name(
                        activity_grouping.activity_subgroup_uid
                    )
                    if name:
                        subgroup_str = (
                            f"'{name}' ({activity_grouping.activity_subgroup_uid})"
                        )
                    else:
                        subgroup_str = f"'{activity_grouping.activity_subgroup_uid}'"

                    raise BusinessLogicException(
                        msg=f"Cannot create activity instance: Activity Sub Group {subgroup_str} is currently not in Final status."
                    )
                if not activity_group_latest_is_final(
                    activity_grouping.activity_group_uid
                ):
                    # Get the group name for a better error message
                    name = get_activity_group_name(activity_grouping.activity_group_uid)
                    if name:
                        group_str = f"'{name}' ({activity_grouping.activity_group_uid})"
                    else:
                        group_str = f"'{activity_grouping.activity_group_uid}'"

                    raise BusinessLogicException(
                        msg=f"Cannot create activity instance: Activity Group {group_str} is currently not in Final status."
                    )


@dataclass
class ActivityInstanceAR(ConceptARBase):
    _concept_vo: ActivityInstanceVO
    _groupings_item_metadata: LibraryItemMetadataVO

    @property
    def concept_vo(self) -> ActivityInstanceVO:
        return self._concept_vo

    @concept_vo.setter
    def concept_vo(self, value: ActivityInstanceVO) -> None:
        self._concept_vo = value

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def name_sentence_case(self) -> str:
        return self._concept_vo.name_sentence_case

    @property
    def groupings_item_metadata(self) -> LibraryItemMetadataVO:
        return self._groupings_item_metadata

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: ActivityInstanceVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
        groupings_item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        activity_ar = cls(
            _uid=uid,
            _concept_vo=concept_vo,
            _item_metadata=item_metadata,
            _groupings_item_metadata=groupings_item_metadata,
            _library=library,
        )
        return activity_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        concept_vo: ActivityInstanceVO,
        library: LibraryVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        concept_exists_by_library_and_property_value_callback: Callable[
            [str, str, str], bool
        ] = lambda x, y, z: True,
        get_final_activity_value_by_uid_callback: Callable[[str], Node | None],
        activity_subgroup_exists: Callable[[str], bool],
        activity_group_exists: Callable[[str], bool],
        ct_term_exists_by_uid_callback: Callable[[str], bool] = lambda _: False,
        unit_definition_exists_by_uid_callback: Callable[[str], bool] = lambda _: False,
        find_activity_item_class_by_uid_callback: Callable[[str], ActivityItemClassAR],
        find_activity_instance_class_by_uid_callback: Callable[
            [str], ActivityInstanceClassAR
        ],
        get_dimension_names_by_unit_definition_uids: Callable[
            [list[str]], list[str]
        ] = lambda _: [],
        activity_subgroup_latest_is_final: Callable[[str], bool] = lambda x: True,
        activity_group_latest_is_final: Callable[[str], bool] = lambda x: True,
        get_activity_subgroup_name: Callable[[str], str | None] = lambda x: None,
        get_activity_group_name: Callable[[str], str | None] = lambda x: None,
        get_parent_class_uid_callback: Callable[[str], str | None] = lambda _: None,
        strict_mode: bool = False,
        generate_uid_callback: Callable[[], str | None] = lambda: None,
        preview: bool = False,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )

        concept_vo.validate(
            get_final_activity_value_by_uid_callback=get_final_activity_value_by_uid_callback,
            activity_subgroup_exists=activity_subgroup_exists,
            activity_group_exists=activity_group_exists,
            ct_term_exists_by_uid_callback=ct_term_exists_by_uid_callback,
            unit_definition_exists_by_uid_callback=unit_definition_exists_by_uid_callback,
            find_activity_item_class_by_uid_callback=find_activity_item_class_by_uid_callback,
            find_activity_instance_class_by_uid_callback=find_activity_instance_class_by_uid_callback,
            get_dimension_names_by_unit_definition_uids=get_dimension_names_by_unit_definition_uids,
            library_name=library.name,
            preview=preview,
            activity_subgroup_latest_is_final=activity_subgroup_latest_is_final,
            activity_group_latest_is_final=activity_group_latest_is_final,
            get_activity_subgroup_name=get_activity_subgroup_name,
            get_activity_group_name=get_activity_group_name,
            get_parent_class_uid_callback=get_parent_class_uid_callback,
            strict_mode=strict_mode,
            activity_instance_exists_by_property_value=concept_exists_by_library_and_property_value_callback,
        )

        activity_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _groupings_item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return activity_ar

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        concept_vo: ActivityInstanceVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        concept_exists_by_library_and_property_value_callback: Callable[
            [str, str, str], bool
        ] = lambda x, y, z: True,
        get_final_activity_value_by_uid_callback: Callable[
            [str], Node | None
        ] = lambda _: None,
        activity_subgroup_exists: Callable[[str], bool] = lambda _: True,
        activity_group_exists: Callable[[str], bool] = lambda _: True,
        ct_term_exists_by_uid_callback: Callable[[str], bool] = lambda _: True,
        unit_definition_exists_by_uid_callback: Callable[[str], bool] = lambda _: True,
        find_activity_item_class_by_uid_callback: Callable[
            ..., ActivityItemClassAR | None
        ] = lambda _: None,
        find_activity_instance_class_by_uid_callback: Callable[
            ..., ActivityInstanceClassAR | None
        ] = lambda _: None,
        get_dimension_names_by_unit_definition_uids: Callable[
            [list[str]], list[str]
        ] = lambda _: [],
        get_parent_class_uid_callback: Callable[[str], str | None] = lambda _: None,
        strict_mode: bool = False,
        perform_validation: bool = True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        if perform_validation:
            concept_vo.validate(
                get_final_activity_value_by_uid_callback=get_final_activity_value_by_uid_callback,
                activity_subgroup_exists=activity_subgroup_exists,
                activity_group_exists=activity_group_exists,
                ct_term_exists_by_uid_callback=ct_term_exists_by_uid_callback,
                unit_definition_exists_by_uid_callback=unit_definition_exists_by_uid_callback,
                find_activity_item_class_by_uid_callback=find_activity_item_class_by_uid_callback,
                find_activity_instance_class_by_uid_callback=find_activity_instance_class_by_uid_callback,
                get_dimension_names_by_unit_definition_uids=get_dimension_names_by_unit_definition_uids,
                get_parent_class_uid_callback=get_parent_class_uid_callback,
                strict_mode=strict_mode,
                activity_instance_exists_by_property_value=concept_exists_by_library_and_property_value_callback,
                previous_name=self.name,
                previous_topic_code=self._concept_vo.topic_code,
                library_name=self.library.name,
            )
        if self._concept_vo != concept_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._concept_vo = concept_vo

    def get_groupings_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions for the groupings versioning track.
        """
        md = self._groupings_item_metadata
        if md.status == LibraryItemStatus.DRAFT and md.major_version == 0:
            return {ObjectAction.APPROVE, ObjectAction.EDIT, ObjectAction.DELETE}
        if md.status == LibraryItemStatus.DRAFT:
            return {ObjectAction.APPROVE, ObjectAction.EDIT}
        if md.status == LibraryItemStatus.FINAL:
            return {ObjectAction.NEWVERSION, ObjectAction.INACTIVATE}
        if md.status == LibraryItemStatus.RETIRED:
            return {ObjectAction.REACTIVATE}
        return frozenset()

    def soft_delete(self) -> None:
        BusinessLogicException.raise_if(
            self._groupings_item_metadata.major_version != 0,
            msg="Object has been accepted",
        )
        super().soft_delete()


@dataclass
class ActivityInstanceAttributesAR(ConceptARBase):
    _concept_vo: ActivityInstanceAttributesVO

    @property
    def concept_vo(self) -> ActivityInstanceAttributesVO:
        return self._concept_vo

    @concept_vo.setter
    def concept_vo(self, value: ActivityInstanceAttributesVO) -> None:
        self._concept_vo = value

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def name_sentence_case(self) -> str:
        return self._concept_vo.name_sentence_case

    @property
    def groupings_item_metadata(self) -> LibraryItemMetadataVO:
        return self._groupings_item_metadata

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: ActivityInstanceAttributesVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        activity_ar = cls(
            _uid=uid,
            _concept_vo=concept_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return activity_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        concept_vo: ActivityInstanceAttributesVO,
        library: LibraryVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        concept_exists_by_library_and_property_value_callback: Callable[
            [str, str, str], bool
        ] = lambda x, y, z: True,
        ct_term_exists_by_uid_callback: Callable[[str], bool] = lambda _: False,
        unit_definition_exists_by_uid_callback: Callable[[str], bool] = lambda _: False,
        find_activity_item_class_by_uid_callback: Callable[[str], ActivityItemClassAR],
        find_activity_instance_class_by_uid_callback: Callable[
            [str], ActivityInstanceClassAR
        ],
        get_dimension_names_by_unit_definition_uids: Callable[
            [list[str]], list[str]
        ] = lambda _: [],
        get_parent_class_uid_callback: Callable[[str], str | None] = lambda _: None,
        strict_mode: bool = False,
        generate_uid_callback: Callable[[], str | None] = lambda: None,
        preview: bool = False,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )

        concept_vo.validate(
            ct_term_exists_by_uid_callback=ct_term_exists_by_uid_callback,
            unit_definition_exists_by_uid_callback=unit_definition_exists_by_uid_callback,
            find_activity_item_class_by_uid_callback=find_activity_item_class_by_uid_callback,
            find_activity_instance_class_by_uid_callback=find_activity_instance_class_by_uid_callback,
            get_dimension_names_by_unit_definition_uids=get_dimension_names_by_unit_definition_uids,
            library_name=library.name,
            preview=preview,
            get_parent_class_uid_callback=get_parent_class_uid_callback,
            strict_mode=strict_mode,
            activity_instance_exists_by_property_value=concept_exists_by_library_and_property_value_callback,
        )

        activity_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return activity_ar

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        concept_vo: ActivityInstanceAttributesVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        concept_exists_by_library_and_property_value_callback: Callable[
            [str, str, str], bool
        ] = lambda x, y, z: True,
        get_final_activity_value_by_uid_callback: Callable[
            [str], Node | None
        ] = lambda _: None,
        ct_term_exists_by_uid_callback: Callable[[str], bool] = lambda _: True,
        unit_definition_exists_by_uid_callback: Callable[[str], bool] = lambda _: True,
        find_activity_item_class_by_uid_callback: Callable[
            ..., ActivityItemClassAR | None
        ] = lambda _: None,
        find_activity_instance_class_by_uid_callback: Callable[
            ..., ActivityInstanceClassAR | None
        ] = lambda _: None,
        get_dimension_names_by_unit_definition_uids: Callable[
            [list[str]], list[str]
        ] = lambda _: [],
        get_parent_class_uid_callback: Callable[[str], str | None] = lambda _: None,
        strict_mode: bool = False,
        perform_validation: bool = True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        _ = get_final_activity_value_by_uid_callback
        if perform_validation:
            concept_vo.validate(
                ct_term_exists_by_uid_callback=ct_term_exists_by_uid_callback,
                unit_definition_exists_by_uid_callback=unit_definition_exists_by_uid_callback,
                find_activity_item_class_by_uid_callback=find_activity_item_class_by_uid_callback,
                find_activity_instance_class_by_uid_callback=find_activity_instance_class_by_uid_callback,
                get_dimension_names_by_unit_definition_uids=get_dimension_names_by_unit_definition_uids,
                get_parent_class_uid_callback=get_parent_class_uid_callback,
                strict_mode=strict_mode,
                activity_instance_exists_by_property_value=concept_exists_by_library_and_property_value_callback,
                previous_name=self.name,
                previous_topic_code=self._concept_vo.topic_code,
                library_name=self.library.name,
            )
        if self._concept_vo != concept_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._concept_vo = concept_vo


@dataclass
class ActivityInstanceGroupingsAR(VersioningActionMixin):
    _concept_vo: ActivityInstanceGroupingsVO
    _item_metadata: LibraryItemMetadataVO

    # used for soft delete
    _is_deleted: bool = field(init=False, default=False)

    # Properties from ActivityInstanceRoot
    _uid: str | None
    _library: LibraryVO

    @property
    def uid(self) -> str | None:
        return self._uid

    @property
    def library(self) -> LibraryVO:
        return self._library

    @property
    def is_deleted(self) -> bool:
        return self._is_deleted

    @property
    def concept_vo(self) -> ActivityInstanceGroupingsVO:
        return self._concept_vo

    @concept_vo.setter
    def concept_vo(self, value: ActivityInstanceGroupingsVO) -> None:
        self._concept_vo = value

    @property
    def item_metadata(self) -> LibraryItemMetadataVO:
        return self._item_metadata

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def name_sentence_case(self) -> str:
        return self._concept_vo.name_sentence_case

    def _is_edit_allowed_in_non_editable_library(self):
        return True

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: ActivityInstanceGroupingsVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        activity_ar = cls(
            _uid=uid,
            _library=library,
            _concept_vo=concept_vo,
            _item_metadata=item_metadata,
        )
        return activity_ar

    def create_new_version(self, author_id: str) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        super()._create_new_version(author_id=author_id)

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        concept_vo: ActivityInstanceGroupingsVO,
        get_final_activity_value_by_uid_callback: Callable[
            [str], Node | None
        ] = lambda _: None,
        activity_subgroup_exists: Callable[[str], bool] = lambda _: True,
        activity_group_exists: Callable[[str], bool] = lambda _: True,
        perform_validation: bool = True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        if perform_validation:
            concept_vo.validate(
                get_final_activity_value_by_uid_callback=get_final_activity_value_by_uid_callback,
                activity_subgroup_exists=activity_subgroup_exists,
                activity_group_exists=activity_group_exists,
                update=True,
            )
        if self._concept_vo != concept_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._concept_vo = concept_vo

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions
        """
        if (
            self._item_metadata.status == LibraryItemStatus.DRAFT
            and self._item_metadata.major_version == 0
        ):
            return {ObjectAction.APPROVE, ObjectAction.EDIT, ObjectAction.DELETE}
        if self._item_metadata.status == LibraryItemStatus.DRAFT:
            return {ObjectAction.APPROVE, ObjectAction.EDIT}
        if self._item_metadata.status == LibraryItemStatus.FINAL:
            return {ObjectAction.NEWVERSION, ObjectAction.INACTIVATE}
        if self._item_metadata.status == LibraryItemStatus.RETIRED:
            return {ObjectAction.REACTIVATE}
        return frozenset()
