from dataclasses import dataclass
from typing import Callable, Self

from neo4j.graph import Node

from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_item_class import (
    ActivityItemClassAR,
)
from clinical_mdr_api.domains.concepts.activities.activity import ActivityGroupingVO
from clinical_mdr_api.domains.concepts.activities.activity_item import ActivityItemVO
from clinical_mdr_api.domains.concepts.concept_base import (
    ConceptARBase,
    ConceptVO,
    _ConceptVOType,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
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


@dataclass(frozen=True)
class ActivityInstanceVO(ConceptVO):
    """
    The ActivityInstanceVO acts as the value object for a single ActivityInstance aggregate
    """

    nci_concept_id: str | None
    nci_concept_name: str | None
    is_research_lab: bool
    molecular_weight: float | None
    topic_code: str
    adam_param_code: str | None
    is_required_for_activity: bool
    is_default_selected_for_activity: bool
    is_data_sharing: bool
    is_legacy_usage: bool
    is_derived: bool
    legacy_description: str | None
    activity_name: str | None
    activity_groupings: list[ActivityInstanceGroupingVO]
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
        definition: str,
        abbreviation: str | None,
        is_research_lab: bool,
        molecular_weight: float | None,
        topic_code: str,
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
            activity_groupings=(
                activity_groupings if activity_groupings is not None else []
            ),
            activity_items=activity_items if activity_items is not None else [],
            activity_name=activity_name,
        )

        return activity_instance_vo

    def validate(
        self,
        get_final_activity_value_by_uid_callback: Callable[[str], Node | None],
        activity_subgroup_exists: Callable[[str], bool],
        activity_group_exists: Callable[[str], bool],
        ct_term_exists_by_uid_callback: Callable[[str], bool],
        unit_definition_exists_by_uid_callback: Callable[[str], bool],
        find_activity_item_class_by_uid_callback: Callable[[str], ActivityItemClassAR],
        find_activity_instance_class_by_uid_callback: Callable[
            [str], ActivityInstanceClassAR
        ],
        odm_item_exists_by_uid_callback: Callable[[str], bool],
        get_dimension_names_by_unit_definition_uids: Callable[[list[str]], list[str]],
        activity_instance_exists_by_property_value: Callable[
            [str, str, str], bool
        ] = lambda x, y, z: True,
        previous_name: str | None = None,
        previous_topic_code: str | None = None,
        library_name: str | None = None,
        preview: bool = False,
    ) -> None:
        if not preview:
            self.validate_name_sentence_case()
        existing_name = activity_instance_exists_by_property_value(
            library_name, "name", self.name
        )
        AlreadyExistsException.raise_if(
            existing_name and previous_name != self.name,
            "Activity Instance",
            self.name,
            "Name",
        )
        if self.topic_code is not None:
            existing_topic_code = activity_instance_exists_by_property_value(
                library_name, "topic_code", self.topic_code
            )
            AlreadyExistsException.raise_if(
                existing_topic_code and previous_topic_code != self.topic_code,
                "Activity Instance",
                self.topic_code,
                "Topic Code",
            )
        for activity_grouping in self.activity_groupings:
            activity = get_final_activity_value_by_uid_callback(
                activity_grouping.activity_uid
            )
            BusinessLogicException.raise_if(
                activity is None,
                msg=f"{type(self).__name__} tried to connect to non-existent or non-final Activity with UID '{activity_grouping.activity_uid}'.",
            )
            BusinessLogicException.raise_if_not(
                activity["is_data_collected"],
                msg=f"{type(self).__name__} tried to connect to Activity without data collection",
            )

            BusinessLogicException.raise_if_not(
                activity_subgroup_exists(activity_grouping.activity_subgroup_uid),
                msg=f"{type(self).__name__} tried to connect to non-existent or non-final Activity Sub Group with UID '{activity_grouping.activity_subgroup_uid}'.",
            )
            BusinessLogicException.raise_if_not(
                activity_group_exists(activity_grouping.activity_group_uid),
                msg=f"{type(self).__name__} tried to connect to non-existent or non-final Activity Group with UID '{activity_grouping.activity_group_uid}'.",
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
                        None,
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
                    unit_definition_exists_by_uid_callback(unit.uid),
                    msg=f"{type(self).__name__} tried to connect to non-existent or non-final Unit Definition with UID '{unit.uid}'.",
                )
            for odm_item in activity_item.odm_items:
                BusinessLogicException.raise_if_not(
                    odm_item_exists_by_uid_callback(odm_item.uid),
                    msg=f"{type(self).__name__} tried to connect to non-existent or non-final ODM Item with UID '{odm_item.uid}'.",
                )

        activity_instance_class = find_activity_instance_class_by_uid_callback(
            self.activity_instance_class_uid
        )
        ValidationException.raise_if_not(
            activity_instance_class,
            msg=f"Activity Instance Class with UID '{self.activity_instance_class_uid}' doesn't exist.",
        )

        unit_dimension_names = get_dimension_names_by_unit_definition_uids(
            [
                unit.uid
                for activity_item in self.activity_items
                for unit in activity_item.unit_definitions
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


@dataclass
class ActivityInstanceAR(ConceptARBase):
    _concept_vo: ActivityInstanceVO

    @property
    def concept_vo(self) -> _ConceptVOType:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: _ConceptVOType,
        library: LibraryVO | None,
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
        concept_vo: _ConceptVOType,
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
        ct_term_exists_by_uid_callback: Callable[[str], bool] | None = None,
        unit_definition_exists_by_uid_callback: Callable[[str], bool] | None = None,
        find_activity_item_class_by_uid_callback: Callable[[str], ActivityItemClassAR],
        find_activity_instance_class_by_uid_callback: Callable[
            [str], ActivityInstanceClassAR
        ],
        odm_item_exists_by_uid_callback: Callable[[str], bool] | None = None,
        get_dimension_names_by_unit_definition_uids: (
            Callable[[list[str]], list[str]] | None
        ) = None,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
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
            activity_instance_exists_by_property_value=concept_exists_by_library_and_property_value_callback,
            get_final_activity_value_by_uid_callback=get_final_activity_value_by_uid_callback,
            activity_subgroup_exists=activity_subgroup_exists,
            activity_group_exists=activity_group_exists,
            ct_term_exists_by_uid_callback=ct_term_exists_by_uid_callback,
            unit_definition_exists_by_uid_callback=unit_definition_exists_by_uid_callback,
            find_activity_item_class_by_uid_callback=find_activity_item_class_by_uid_callback,
            find_activity_instance_class_by_uid_callback=find_activity_instance_class_by_uid_callback,
            preview=preview,
            odm_item_exists_by_uid_callback=odm_item_exists_by_uid_callback,
            get_dimension_names_by_unit_definition_uids=get_dimension_names_by_unit_definition_uids,
            library_name=library.name,
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
        change_description: str | None,
        concept_vo: _ConceptVOType,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        concept_exists_by_library_and_property_value_callback: Callable[
            [str, str, str], bool
        ] = lambda x, y, z: True,
        get_final_activity_value_by_uid_callback: (
            Callable[[str], Node | None] | None
        ) = None,
        activity_subgroup_exists: Callable[[str], bool] | None = None,
        activity_group_exists: Callable[[str], bool] | None = None,
        ct_term_exists_by_uid_callback: Callable[[str], bool] | None = None,
        unit_definition_exists_by_uid_callback: Callable[[str], bool] | None = None,
        find_activity_item_class_by_uid_callback: (
            Callable[[str], ActivityItemClassAR] | None
        ) = None,
        find_activity_instance_class_by_uid_callback: (
            Callable[[str], ActivityInstanceClassAR] | None
        ) = None,
        odm_item_exists_by_uid_callback: Callable[[str], bool] | None = None,
        get_dimension_names_by_unit_definition_uids: (
            Callable[[list[str]], list[str]] | None
        ) = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            activity_instance_exists_by_property_value=concept_exists_by_library_and_property_value_callback,
            get_final_activity_value_by_uid_callback=get_final_activity_value_by_uid_callback,
            activity_subgroup_exists=activity_subgroup_exists,
            activity_group_exists=activity_group_exists,
            ct_term_exists_by_uid_callback=ct_term_exists_by_uid_callback,
            unit_definition_exists_by_uid_callback=unit_definition_exists_by_uid_callback,
            find_activity_item_class_by_uid_callback=find_activity_item_class_by_uid_callback,
            find_activity_instance_class_by_uid_callback=find_activity_instance_class_by_uid_callback,
            odm_item_exists_by_uid_callback=odm_item_exists_by_uid_callback,
            get_dimension_names_by_unit_definition_uids=get_dimension_names_by_unit_definition_uids,
            previous_name=self.name,
            previous_topic_code=self._concept_vo.topic_code,
            library_name=self.library.name,
        )
        if self._concept_vo != concept_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._concept_vo = concept_vo
