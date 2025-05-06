from datetime import datetime
from typing import Annotated, Callable, Self

from pydantic import ConfigDict, Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domains.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domains.concepts.activities.activity_instance import (
    ActivityInstanceAR,
)
from clinical_mdr_api.domains.concepts.activities.activity_item import LibraryItem
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    CompactActivityInstanceClass,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityBase,
    ActivityGrouping,
    ActivityHierarchySimpleModel,
    SimpleActivityGroup,
    SimpleActivityGrouping,
    SimpleActivityInstance,
    SimpleActivityInstanceClass,
    SimpleActivitySubGroup,
)
from clinical_mdr_api.models.concepts.activities.activity_item import (
    ActivityItem,
    ActivityItemCreateInput,
    CompactActivityItemClass,
    CompactCTTerm,
    CompactOdmItem,
    CompactUnitDefinition,
)
from clinical_mdr_api.models.concepts.concept import (
    ExtendedConceptPatchInput,
    ExtendedConceptPostInput,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel
from common.utils import convert_to_datetime


class ActivityInstanceHierarchySimpleModel(BaseModel):
    activity: ActivityHierarchySimpleModel
    activity_subgroup: ActivityHierarchySimpleModel
    activity_group: ActivityHierarchySimpleModel


class ActivityInstanceGrouping(ActivityGrouping):
    activity_uid: str


class ActivityInstance(ActivityBase):
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    nci_concept_id: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    nci_concept_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_activity_ar(
        cls,
        activity_ar: ActivityInstanceAR,
        find_activity_hierarchy_by_uid: Callable[[str], ActivityAR | None],
        find_activity_subgroup_by_uid: Callable[[str], ActivitySubGroupAR | None],
        find_activity_group_by_uid: Callable[[str], ActivityGroupAR | None],
    ) -> Self:
        activity_items = []
        for activity_item in activity_ar.concept_vo.activity_items:
            ct_terms = []
            unit_definitions = []
            odm_items = []
            for unit in activity_item.unit_definitions:
                unit_definitions.append(
                    CompactUnitDefinition(
                        uid=unit.uid, name=unit.name, dimension_name=unit.dimension_name
                    )
                )
            unit_definitions.sort(key=lambda x: x.uid)
            for term in activity_item.ct_terms:
                ct_terms.append(CompactCTTerm(uid=term.uid, name=term.name))
            ct_terms.sort(key=lambda x: x.uid)
            for odm_item in activity_item.odm_items:
                odm_items.append(
                    CompactOdmItem(
                        uid=odm_item.uid, oid=odm_item.oid, name=odm_item.name
                    )
                )
            odm_items.sort(key=lambda x: x.uid)

            activity_items.append(
                ActivityItem(
                    activity_item_class=CompactActivityItemClass(
                        uid=activity_item.activity_item_class_uid,
                        name=activity_item.activity_item_class_name,
                    ),
                    ct_terms=ct_terms,
                    unit_definitions=unit_definitions,
                    is_adam_param_specific=activity_item.is_adam_param_specific,
                    odm_items=odm_items,
                )
            )

        return cls(
            uid=activity_ar.uid,
            nci_concept_id=activity_ar.concept_vo.nci_concept_id,
            nci_concept_name=activity_ar.concept_vo.nci_concept_name,
            name=activity_ar.name,
            name_sentence_case=activity_ar.concept_vo.name_sentence_case,
            definition=activity_ar.concept_vo.definition,
            abbreviation=activity_ar.concept_vo.abbreviation,
            topic_code=activity_ar.concept_vo.topic_code,
            is_research_lab=activity_ar.concept_vo.is_research_lab,
            molecular_weight=activity_ar.concept_vo.molecular_weight,
            adam_param_code=activity_ar.concept_vo.adam_param_code,
            is_required_for_activity=activity_ar.concept_vo.is_required_for_activity,
            is_default_selected_for_activity=activity_ar.concept_vo.is_default_selected_for_activity,
            is_data_sharing=activity_ar.concept_vo.is_data_sharing,
            is_legacy_usage=activity_ar.concept_vo.is_legacy_usage,
            is_derived=activity_ar.concept_vo.is_derived,
            legacy_description=activity_ar.concept_vo.legacy_description,
            activity_groupings=[
                ActivityInstanceHierarchySimpleModel(
                    activity_group=ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_grouping.activity_group_uid,
                        find_activity_by_uid=find_activity_group_by_uid,
                        version=activity_grouping.activity_group_version,
                    ),
                    activity_subgroup=ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_grouping.activity_subgroup_uid,
                        find_activity_by_uid=find_activity_subgroup_by_uid,
                        version=activity_grouping.activity_subgroup_version,
                    ),
                    activity=ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_grouping.activity_uid,
                        find_activity_by_uid=find_activity_hierarchy_by_uid,
                        version=activity_grouping.activity_version,
                    ),
                )
                for activity_grouping in activity_ar.concept_vo.activity_groupings
            ],
            activity_name=activity_ar.concept_vo.activity_name,
            activity_instance_class=CompactActivityInstanceClass(
                uid=activity_ar.concept_vo.activity_instance_class_uid,
                name=activity_ar.concept_vo.activity_instance_class_name,
            ),
            activity_items=activity_items,
            library_name=Library.from_library_vo(activity_ar.library).name,
            start_date=activity_ar.item_metadata.start_date,
            end_date=activity_ar.item_metadata.end_date,
            status=activity_ar.item_metadata.status.value,
            version=activity_ar.item_metadata.version,
            change_description=activity_ar.item_metadata.change_description,
            author_username=activity_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in activity_ar.get_possible_actions()]
            ),
        )

    @classmethod
    def from_activity_instance_ar_objects(
        cls,
        activity_instance_ar: ActivityInstanceAR,
        activity_ars: list[ActivityAR],
        activity_instance_subgroup_ars: list[ActivitySubGroupAR],
        activity_instance_group_ars: list[ActivityGroupAR],
    ) -> Self:
        activity_items = []
        for activity_item in activity_instance_ar.concept_vo.activity_items:
            ct_terms = []
            unit_definitions = []
            odm_items = []
            for unit in activity_item.unit_definitions:
                unit_definitions.append(
                    CompactUnitDefinition(uid=unit.uid, name=unit.name)
                )
            unit_definitions.sort(key=lambda x: x.uid)
            for term in activity_item.ct_terms:
                ct_terms.append(CompactCTTerm(uid=term.uid, name=term.name))
            ct_terms.sort(key=lambda x: x.uid)
            for odm_item in activity_item.odm_items:
                odm_items.append(
                    CompactOdmItem(
                        uid=odm_item.uid, oid=odm_item.oid, name=odm_item.name
                    )
                )
            odm_items.sort(key=lambda x: x.uid)
            activity_items.append(
                ActivityItem(
                    activity_item_class=CompactActivityItemClass(
                        uid=activity_item.activity_item_class_uid,
                        name=activity_item.activity_item_class_name,
                    ),
                    ct_terms=ct_terms,
                    unit_definitions=unit_definitions,
                    is_adam_param_specific=activity_item.is_adam_param_specific,
                    odm_items=odm_items,
                )
            )
        activity_instance_groupings = []
        for (
            activity_instance_group_ar,
            activity_instance_subgroup_ar,
            activity_ar,
        ) in zip(
            activity_instance_group_ars, activity_instance_subgroup_ars, activity_ars
        ):
            activity = ActivityHierarchySimpleModel.from_activity_ar_object(
                activity_ar=activity_ar,
            )
            activity_instance_group = (
                ActivityHierarchySimpleModel.from_activity_ar_object(
                    activity_ar=activity_instance_group_ar,
                )
            )
            activity_instance_subgroup = (
                ActivityHierarchySimpleModel.from_activity_ar_object(
                    activity_ar=activity_instance_subgroup_ar,
                )
            )
            activity_instance_groupings.append(
                ActivityInstanceHierarchySimpleModel(
                    activity_group=activity_instance_group,
                    activity_subgroup=activity_instance_subgroup,
                    activity=activity,
                )
            )

        return cls(
            uid=activity_instance_ar.uid,
            nci_concept_id=activity_instance_ar.concept_vo.nci_concept_id,
            nci_concept_name=activity_instance_ar.concept_vo.nci_concept_name,
            name=activity_instance_ar.name,
            name_sentence_case=activity_instance_ar.concept_vo.name_sentence_case,
            definition=activity_instance_ar.concept_vo.definition,
            abbreviation=activity_instance_ar.concept_vo.abbreviation,
            topic_code=activity_instance_ar.concept_vo.topic_code,
            is_research_lab=activity_instance_ar.concept_vo.is_research_lab,
            molecular_weight=activity_instance_ar.concept_vo.molecular_weight,
            adam_param_code=activity_instance_ar.concept_vo.adam_param_code,
            is_required_for_activity=activity_instance_ar.concept_vo.is_required_for_activity,
            is_default_selected_for_activity=activity_instance_ar.concept_vo.is_default_selected_for_activity,
            is_data_sharing=activity_instance_ar.concept_vo.is_data_sharing,
            is_legacy_usage=activity_instance_ar.concept_vo.is_legacy_usage,
            is_derived=activity_instance_ar.concept_vo.is_derived,
            legacy_description=activity_instance_ar.concept_vo.legacy_description,
            activity_groupings=sorted(
                activity_instance_groupings,
                key=lambda item: (
                    item.activity_subgroup.name,
                    item.activity_group.name,
                    item.activity.name,
                ),
            ),
            activity_name=activity_instance_ar.concept_vo.activity_name,
            activity_instance_class=CompactActivityInstanceClass(
                uid=activity_instance_ar.concept_vo.activity_instance_class_uid,
                name=activity_instance_ar.concept_vo.activity_instance_class_name,
            ),
            activity_items=activity_items,
            library_name=Library.from_library_vo(activity_instance_ar.library).name,
            start_date=activity_instance_ar.item_metadata.start_date,
            end_date=activity_instance_ar.item_metadata.end_date,
            status=activity_instance_ar.item_metadata.status.value,
            version=activity_instance_ar.item_metadata.version,
            change_description=activity_instance_ar.item_metadata.change_description,
            author_username=activity_instance_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in activity_instance_ar.get_possible_actions()]
            ),
        )

    topic_code: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    adam_param_code: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    is_research_lab: Annotated[bool, Field()] = False
    molecular_weight: Annotated[
        float | None, Field(json_schema_extra={"nullable": True})
    ] = None
    is_required_for_activity: Annotated[bool, Field()] = False
    is_default_selected_for_activity: Annotated[bool, Field()] = False
    is_data_sharing: Annotated[bool, Field()] = False
    is_legacy_usage: Annotated[bool, Field()] = False
    is_derived: Annotated[bool, Field()] = False
    legacy_description: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    activity_groupings: Annotated[list[ActivityInstanceHierarchySimpleModel], Field()]
    activity_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    activity_instance_class: Annotated[
        CompactActivityInstanceClass,
        Field(description="The uid and the name of the linked activity instance class"),
    ]
    activity_items: Annotated[
        list[ActivityItem],
        Field(
            description="List of activity items",
        ),
    ]
    start_date: datetime
    end_date: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    status: str
    version: str
    change_description: str
    author_username: Annotated[
        str | None,
        Field(
            json_schema_extra={"nullable": True},
        ),
    ] = None
    possible_actions: Annotated[
        list[str],
        Field(
            description=(
                "Holds those actions that can be performed on the ActivityInstances. "
                "Actions are: 'approve', 'edit', 'new_version'."
            ),
        ),
    ]


class ActivityInstanceCreateInput(ExtendedConceptPostInput):
    nci_concept_id: Annotated[str | None, Field(min_length=1)] = None
    nci_concept_name: Annotated[str | None, Field(min_length=1)] = None
    topic_code: Annotated[str | None, Field(min_length=1)] = None
    is_research_lab: bool = False
    molecular_weight: float | None = None
    adam_param_code: Annotated[str | None, Field(min_length=1)] = None
    is_required_for_activity: bool = False
    is_default_selected_for_activity: bool = False
    is_data_sharing: bool = False
    is_legacy_usage: bool = False
    is_derived: bool = False
    legacy_description: Annotated[str | None, Field(min_length=1)] = None
    activity_groupings: list[ActivityInstanceGrouping] | None = None
    activity_instance_class_uid: Annotated[str, Field(min_length=1)]
    activity_items: list[ActivityItemCreateInput] | None = None
    library_name: Annotated[str, Field(min_length=1)]


class ActivityInstancePreviewInput(ActivityInstanceCreateInput):
    name: Annotated[
        str | None,
        Field(
            description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
            min_length=1,
        ),
    ] = None


class ActivityInstanceEditInput(ExtendedConceptPatchInput):
    nci_concept_id: Annotated[str | None, Field(min_length=1)] = None
    nci_concept_name: Annotated[str | None, Field(min_length=1)] = None
    topic_code: Annotated[str | None, Field(min_length=1)] = None
    is_research_lab: bool | None = None
    molecular_weight: float | None = None
    adam_param_code: Annotated[str | None, Field(min_length=1)] = None
    is_required_for_activity: bool | None = None
    is_default_selected_for_activity: bool | None = None
    is_data_sharing: bool | None = None
    is_legacy_usage: bool | None = None
    is_derived: bool | None = None
    legacy_description: Annotated[str | None, Field(min_length=1)] = None
    activity_instance_class_uid: Annotated[str | None, Field(min_length=1)] = None
    activity_groupings: list[ActivityInstanceGrouping] | None = None
    activity_items: list[ActivityItemCreateInput] | None = None
    change_description: Annotated[str, Field(min_length=1)]


class ActivityInstanceVersion(ActivityInstance):
    """
    Class for storing ActivityInstance and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []


class SimpleActivity(BaseModel):
    uid: Annotated[str, Field()]
    nci_concept_id: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    nci_concept_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    definition: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    synonyms: Annotated[list[str], Field()]
    is_data_collected: Annotated[
        bool,
        Field(
            description="Boolean flag indicating whether data is collected for this activity",
        ),
    ] = False
    is_multiple_selection_allowed: Annotated[
        bool,
        Field(
            description="Boolean flag indicating whether multiple selections are allowed for this activity",
        ),
    ] = True
    library_name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class SimpleActivityItemClass(BaseModel):
    name: Annotated[str, Field()]
    order: Annotated[int, Field()]
    role_name: Annotated[str, Field()]
    data_type_name: Annotated[str, Field()]


class SimplifiedActivityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ct_terms: Annotated[list[LibraryItem], Field()] = []
    unit_definitions: Annotated[list[CompactUnitDefinition], Field()] = []
    activity_item_class: Annotated[SimpleActivityItemClass, Field()]
    is_adam_param_specific: bool
    odm_items: Annotated[list[CompactOdmItem], Field()] = []


class SimpleActivityInstanceGrouping(SimpleActivityGrouping):
    activity: Annotated[SimpleActivity, Field()]


class ActivityInstanceOverview(BaseModel):
    activity_groupings: Annotated[list[SimpleActivityInstanceGrouping], Field()]
    activity_instance: Annotated[SimpleActivityInstance, Field()]
    activity_items: Annotated[list[SimplifiedActivityItem], Field()]
    all_versions: Annotated[list[str], Field()]

    @classmethod
    def from_repository_input(cls, overview: dict):
        activity_items = []
        for activity_item in overview.get("activity_items"):
            units = sorted(
                [
                    CompactUnitDefinition(
                        name=unit.get("name"),
                        uid=unit.get("uid"),
                        dimension_name=unit.get("dimension_name"),
                    )
                    for unit in activity_item.get("unit_definitions", {})
                ],
                key=lambda x: x.uid,
            )
            terms = sorted(
                [
                    LibraryItem(name=term.get("name"), uid=term.get("uid"))
                    for term in activity_item.get("ct_terms", {})
                ],
                key=lambda x: x.uid,
            )
            odm_items = sorted(
                [
                    CompactOdmItem(
                        uid=odm_item.get("uid"),
                        oid=odm_item.get("oid"),
                        name=odm_item.get("name"),
                    )
                    for odm_item in activity_item.get("odm_items", {})
                ],
                key=lambda x: x.uid,
            )
            activity_items.append(
                SimplifiedActivityItem(
                    ct_terms=terms,
                    unit_definitions=units,
                    odm_items=odm_items,
                    activity_item_class=SimpleActivityItemClass(
                        name=activity_item.get("activity_item_class").get("name"),
                        order=activity_item.get("activity_item_class").get("order"),
                        role_name=activity_item.get("activity_item_class_role"),
                        data_type_name=activity_item.get(
                            "activity_item_class_data_type"
                        ),
                    ),
                    is_adam_param_specific=activity_item.get(
                        "is_adam_param_specific", False
                    ),
                )
            )

        return cls(
            activity_groupings=[
                SimpleActivityInstanceGrouping(
                    activity=SimpleActivity(
                        uid=activity_grouping.get("uid"),
                        name=activity_grouping.get("activity_value").get("name"),
                        definition=activity_grouping.get("activity_value").get(
                            "definition"
                        ),
                        nci_concept_id=activity_grouping.get("activity_value").get(
                            "nci_concept_id"
                        ),
                        nci_concept_name=activity_grouping.get("activity_value").get(
                            "nci_concept_name"
                        ),
                        synonyms=activity_grouping.get("activity_value").get(
                            "synonyms", []
                        ),
                        is_data_collected=activity_grouping.get("activity_value").get(
                            "is_data_collected", False
                        ),
                        is_multiple_selection_allowed=activity_grouping.get(
                            "activity_value"
                        ).get("is_multiple_selection_allowed", True),
                        library_name=activity_grouping.get("activity_library_name"),
                        version=activity_grouping.get("version", {}).get("version"),
                        status=activity_grouping.get("version", {}).get("status"),
                    ),
                    activity_group=SimpleActivityGroup(
                        uid=activity_grouping.get("activity_group_uid"),
                        name=activity_grouping.get("activity_group_value").get("name"),
                        definition=activity_grouping.get("activity_group_value").get(
                            "definition"
                        ),
                    ),
                    activity_subgroup=SimpleActivitySubGroup(
                        uid=activity_grouping.get("activity_subgroup_uid"),
                        name=activity_grouping.get("activity_subgroup_value").get(
                            "name"
                        ),
                        definition=activity_grouping.get("activity_subgroup_value").get(
                            "definition"
                        ),
                    ),
                )
                for activity_grouping in overview.get("hierarchy")
            ],
            activity_instance=SimpleActivityInstance(
                uid=overview.get("activity_instance_root").get("uid"),
                name=overview.get("activity_instance_value").get("name"),
                name_sentence_case=overview.get("activity_instance_value").get(
                    "name_sentence_case"
                ),
                abbreviation=overview.get("activity_instance_value").get(
                    "abbreviation"
                ),
                definition=overview.get("activity_instance_value").get("definition"),
                nci_concept_id=overview.get("activity_instance_value").get(
                    "nci_concept_id"
                ),
                nci_concept_name=overview.get("activity_instance_value").get(
                    "nci_concept_name"
                ),
                adam_param_code=overview.get("activity_instance_value").get(
                    "adam_param_code"
                ),
                is_required_for_activity=overview.get("activity_instance_value").get(
                    "is_required_for_activity", False
                ),
                is_default_selected_for_activity=overview.get(
                    "activity_instance_value"
                ).get("is_default_selected_for_activity", False),
                is_data_sharing=overview.get("activity_instance_value").get(
                    "is_data_sharing", False
                ),
                is_legacy_usage=overview.get("activity_instance_value").get(
                    "is_legacy_usage", False
                ),
                is_derived=overview.get("activity_instance_value").get(
                    "is_derived", False
                ),
                topic_code=overview.get("activity_instance_value").get("topic_code"),
                is_research_lab=overview.get("activity_instance_value").get(
                    "is_research_lab", False
                ),
                molecular_weight=overview.get("activity_instance_value").get(
                    "molecular_weight"
                ),
                library_name=overview.get("instance_library_name"),
                activity_instance_class=SimpleActivityInstanceClass(
                    name=overview.get("activity_instance_class").get("name")
                ),
                status=overview.get("has_version", {}).get("status"),
                version=overview.get("has_version", {}).get("version"),
                start_date=convert_to_datetime(
                    overview.get("has_version", {}).get("start_date")
                ),
                end_date=convert_to_datetime(
                    overview.get("has_version", {}).get("end_date")
                ),
            ),
            activity_items=activity_items,
            all_versions=overview.get("all_versions"),
        )
