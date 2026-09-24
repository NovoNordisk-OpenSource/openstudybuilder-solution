import datetime
from dataclasses import asdict
from typing import Annotated, Any, Callable, Iterable, Self, overload

from pydantic import ConfigDict, Field, ValidationInfo, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domains.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domains.concepts.activities.activity_instance import (
    ActivityInstanceAR,
)
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    ObjectAction,
)
from clinical_mdr_api.models.concepts.concept import Concept, ExtendedConceptPostInput
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import (
    BaseModel,
    EditInputModel,
    InputModel,
    PatchInputModel,
)
from common.utils import convert_to_datetime


class ActivityHierarchySimpleModel(BaseModel):
    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None

    @overload
    @classmethod
    def from_activity_uid(
        cls,
        uid: str,
        find_activity_by_uid: Callable[[str], ConceptARBase | None],
        version: str | None = None,
    ) -> Self: ...
    @overload
    @classmethod
    def from_activity_uid(
        cls,
        uid: None,
        find_activity_by_uid: Callable[[str], ConceptARBase | None],
        version: str | None = None,
    ) -> None: ...
    @classmethod
    def from_activity_uid(
        cls,
        uid: str | None,
        find_activity_by_uid: Callable[..., ConceptARBase | None],
        version: str | None = None,
    ) -> Self | None:
        simple_activity_model = None

        if uid is not None:
            activity = find_activity_by_uid(uid, version=version)
            if activity is not None:
                resolved_version = version or activity.item_metadata.version
                simple_activity_model = cls(
                    uid=uid, name=activity.concept_vo.name, version=resolved_version
                )
            else:
                simple_activity_model = cls(uid=uid, name=None, version=version)
        return simple_activity_model

    @classmethod
    def from_activity_ar_object(
        cls,
        activity_ar: ActivityGroupAR | ActivitySubGroupAR | ActivityInstanceAR | Self,
    ) -> Self:
        return cls(uid=activity_ar.uid, name=activity_ar.name)


class ActivityGroupingHierarchySimpleModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    activity_group_uid: Annotated[
        str,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_grouping.in_subgroup.in_group.has_version.uid"
            }
        ),
    ]
    activity_group_name: Annotated[
        str,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_grouping.in_subgroup.in_group.name"
            }
        ),
    ]
    activity_group_version: Annotated[
        str | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    activity_subgroup_uid: Annotated[
        str,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_grouping.in_subgroup.has_group.has_version.uid"
            }
        ),
    ]
    activity_subgroup_name: Annotated[
        str,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_grouping.in_subgroup.has_group.name"
            }
        ),
    ]
    activity_subgroup_version: Annotated[
        str | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None


class ActivityBase(Concept):
    possible_actions: Annotated[
        list[str] | None,
        Field(
            validate_default=True,
            description=(
                "Holds those actions that can be performed on the ActivityInstances. "
                "Actions are: 'approve', 'edit', 'new_version'."
            ),
        ),
    ] = None

    @field_validator("possible_actions", mode="before")
    @classmethod
    def validate_possible_actions(cls, _, info: ValidationInfo):
        if info.data["status"] == LibraryItemStatus.DRAFT.value and info.data[
            "version"
        ].startswith("0"):
            return [
                ObjectAction.APPROVE.value,
                ObjectAction.DELETE.value,
                ObjectAction.EDIT.value,
            ]
        if info.data["status"] == LibraryItemStatus.DRAFT.value:
            return [ObjectAction.APPROVE.value, ObjectAction.EDIT.value]
        if info.data["status"] == LibraryItemStatus.FINAL.value:
            return [
                ObjectAction.INACTIVATE.value,
                ObjectAction.NEWVERSION.value,
            ]
        if info.data["status"] == LibraryItemStatus.RETIRED.value:
            return [ObjectAction.REACTIVATE.value]
        return []


class Activity(ActivityBase):
    nci_concept_id: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    nci_concept_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    activity_groupings: Annotated[
        list[ActivityGroupingHierarchySimpleModel] | None,
        Field(json_schema_extra={"remove_from_wildcard": True}),
    ] = None
    activity_instances: list[ActivityHierarchySimpleModel] = Field(default_factory=list)
    synonyms: Annotated[
        list[str] | None, Field(json_schema_extra={"remove_from_wildcard": True})
    ] = None
    request_rationale: Annotated[
        str | None,
        Field(
            description="The rationale of the activity request",
            json_schema_extra={"nullable": True, "remove_from_wildcard": True},
        ),
    ] = None
    is_request_final: Annotated[
        bool,
        Field(
            description="The flag indicating if activity request is finalized",
            json_schema_extra={"remove_from_wildcard": True},
        ),
    ] = False
    is_request_rejected: Annotated[
        bool,
        Field(
            description="The flag indicating if activity request is rejected",
            json_schema_extra={"remove_from_wildcard": True},
        ),
    ] = False
    contact_person: Annotated[
        str | None,
        Field(
            description="The person to contact with about rejection",
            json_schema_extra={"nullable": True, "remove_from_wildcard": True},
        ),
    ] = None
    reason_for_rejecting: Annotated[
        str | None,
        Field(
            description="The reason why request was rejected",
            json_schema_extra={"nullable": True, "remove_from_wildcard": True},
        ),
    ] = None
    used_by_studies: list[str] = Field(
        description="The list of study ids which currently uses given Activity Request",
        json_schema_extra={"remove_from_wildcard": True},
        default_factory=list,
    )
    replaced_by_activity: Annotated[
        str | None,
        Field(
            description="The uid of the replacing Activity",
            json_schema_extra={"nullable": True, "remove_from_wildcard": True},
        ),
    ] = None
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
    is_finalized: Annotated[
        bool,
        Field(
            description="Evaluates to false, if is_request_rejected is false and replaced_by_activity is null else true",
        ),
    ] = False
    is_used_by_legacy_instances: Annotated[
        bool,
        Field(
            description="True if all instances linked to given Activity are legacy_used.",
        ),
    ] = False

    @classmethod
    def from_activity_ar(cls, activity_ar: ActivityAR) -> Self:
        activity_groupings = []
        for activity_grouping in activity_ar.concept_vo.activity_groupings:
            activity_groupings.append(
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid=activity_grouping.activity_group_uid,
                    activity_group_name=activity_grouping.activity_group_name or "",
                    activity_group_version=activity_grouping.activity_group_version,
                    activity_subgroup_uid=activity_grouping.activity_subgroup_uid,
                    activity_subgroup_name=activity_grouping.activity_subgroup_name
                    or "",
                    activity_subgroup_version=activity_grouping.activity_subgroup_version,
                )
            )

        activity_instances = []
        for activity_instance in activity_ar.concept_vo.activity_instances:
            activity_instances.append(
                ActivityHierarchySimpleModel(
                    uid=activity_instance["uid"], name=activity_instance["name"]
                )
            )

        return cls(
            uid=activity_ar.uid,
            nci_concept_id=activity_ar.concept_vo.nci_concept_id,
            nci_concept_name=activity_ar.concept_vo.nci_concept_name,
            name=activity_ar.name,
            name_sentence_case=activity_ar.concept_vo.name_sentence_case,
            synonyms=activity_ar.concept_vo.synonyms,
            definition=activity_ar.concept_vo.definition,
            abbreviation=activity_ar.concept_vo.abbreviation,
            activity_groupings=activity_groupings,
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
            request_rationale=activity_ar.concept_vo.request_rationale,
            activity_instances=sorted(
                activity_instances, key=lambda item: (item.name, item.uid)
            ),
            is_request_final=activity_ar.concept_vo.is_request_final,
            is_request_rejected=activity_ar.concept_vo.is_request_rejected,
            reason_for_rejecting=activity_ar.concept_vo.reason_for_rejecting,
            contact_person=activity_ar.concept_vo.contact_person,
            used_by_studies=activity_ar.concept_vo.used_by_studies,
            replaced_by_activity=activity_ar.concept_vo.replaced_by_activity,
            is_data_collected=(
                activity_ar.concept_vo.is_data_collected
                if activity_ar.concept_vo.is_data_collected
                else False
            ),
            is_multiple_selection_allowed=(
                activity_ar.concept_vo.is_multiple_selection_allowed
                if activity_ar.concept_vo.is_multiple_selection_allowed is not None
                else True
            ),
            is_finalized=activity_ar.concept_vo.is_finalized,
            is_used_by_legacy_instances=activity_ar.concept_vo.is_used_by_legacy_instances,
        )

    @classmethod
    def from_activity_ar_objects(
        cls,
        activity_ar: ActivityAR,
        activity_instance_ars: Iterable[
            ActivityInstanceAR | ActivityHierarchySimpleModel
        ] = tuple(),
    ) -> Self:
        activity_groupings = [
            ActivityGroupingHierarchySimpleModel(**asdict(ar))
            for ar in activity_ar.concept_vo.activity_groupings
        ]

        activity_instances = [
            ActivityHierarchySimpleModel.from_activity_ar_object(activity_ar=ar)
            for ar in activity_instance_ars
        ]

        return cls(
            uid=activity_ar.uid,
            nci_concept_id=activity_ar.concept_vo.nci_concept_id,
            nci_concept_name=activity_ar.concept_vo.nci_concept_name,
            name=activity_ar.name,
            name_sentence_case=activity_ar.concept_vo.name_sentence_case,
            synonyms=activity_ar.concept_vo.synonyms,
            definition=activity_ar.concept_vo.definition,
            abbreviation=activity_ar.concept_vo.abbreviation,
            activity_groupings=sorted(
                activity_groupings,
                key=lambda item: (
                    item.activity_subgroup_name,
                    item.activity_group_name,
                ),
            ),
            activity_instances=sorted(
                activity_instances, key=lambda item: (item.name, item.uid)
            ),
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
            request_rationale=activity_ar.concept_vo.request_rationale,
            is_request_final=activity_ar.concept_vo.is_request_final,
            is_request_rejected=activity_ar.concept_vo.is_request_rejected,
            reason_for_rejecting=activity_ar.concept_vo.reason_for_rejecting,
            contact_person=activity_ar.concept_vo.contact_person,
            used_by_studies=activity_ar.concept_vo.used_by_studies,
            replaced_by_activity=activity_ar.concept_vo.replaced_by_activity,
            is_data_collected=(
                activity_ar.concept_vo.is_data_collected
                if activity_ar.concept_vo.is_data_collected
                else False
            ),
            is_multiple_selection_allowed=(
                activity_ar.concept_vo.is_multiple_selection_allowed
                if activity_ar.concept_vo.is_multiple_selection_allowed is not None
                else True
            ),
            is_finalized=activity_ar.concept_vo.is_finalized,
            is_used_by_legacy_instances=activity_ar.concept_vo.is_used_by_legacy_instances,
        )


class ActivityForStudyActivity(Activity):
    activity_groupings: Annotated[
        list[ActivityGroupingHierarchySimpleModel] | None,
        Field(json_schema_extra={"remove_from_wildcard": True}),
    ] = None


class ActivityGrouping(InputModel):
    activity_group_uid: Annotated[str, Field()]
    activity_subgroup_uid: Annotated[str, Field()]


class ActivityPostInput(ExtendedConceptPostInput):
    name: Annotated[
        str,
        Field(
            description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
            min_length=1,
        ),
    ]
    name_sentence_case: Annotated[str, Field(min_length=1)]
    nci_concept_id: Annotated[str | None, Field(min_length=1)] = None
    nci_concept_name: Annotated[str | None, Field(min_length=1)] = None
    activity_groupings: Annotated[list[ActivityGrouping] | None, Field()] = None
    synonyms: Annotated[list[str] | None, Field()] = None
    request_rationale: Annotated[str | None, Field(min_length=1)] = None
    is_request_final: Annotated[bool, Field()] = False
    is_data_collected: Annotated[bool, Field()] = False
    is_multiple_selection_allowed: Annotated[bool, Field()] = True


class ActivityEditInput(ActivityPostInput, EditInputModel):
    pass


class ActivityCreateInput(ActivityPostInput):
    library_name: Annotated[str, Field(min_length=1)]


class ActivityRequestRejectInput(PatchInputModel):
    contact_person: Annotated[str, Field(min_length=1)]
    reason_for_rejecting: Annotated[str, Field(min_length=1)]


class ActivityFromRequestInput(ActivityPostInput):
    activity_request_uid: Annotated[str, Field(min_length=1)]


class ActivityVersion(Activity):
    """
    Class for storing Activity and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)


class ActivityVersionDetailGroup(BaseModel):
    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]
    version: Annotated[str, Field()]
    status: Annotated[str, Field()]


class ActivityVersionDetailSubgroup(BaseModel):
    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]
    version: Annotated[str, Field()]
    status: Annotated[str, Field()]


class ActivityVersionDetailGrouping(BaseModel):
    valid_group_uid: Annotated[str, Field()]
    group: Annotated[ActivityVersionDetailGroup, Field()]
    subgroup: Annotated[ActivityVersionDetailSubgroup, Field()]
    activity_instances: list[ActivityHierarchySimpleModel] = Field(default_factory=list)

    @classmethod
    def from_repository_input(cls, data: dict[str, Any]) -> Self:
        return cls(
            valid_group_uid=data["valid_group_uid"],
            subgroup=ActivityVersionDetailSubgroup(
                uid=data["subgroup"]["uid"],
                name=data["subgroup"]["name"],
                version=data["subgroup"]["version"],
                status=data["subgroup"]["status"],
            ),
            group=ActivityVersionDetailGroup(
                uid=data["group"]["uid"],
                name=data["group"]["name"],
                version=data["group"]["version"],
                status=data["group"]["status"],
            ),
            activity_instances=[
                ActivityHierarchySimpleModel(**instance)
                for instance in data.get("activity_instances", [])
            ],
        )


class ActivityVersionDetail(BaseModel):
    """
    Model representing detailed information about a specific version of an activity.
    """

    activity_uid: Annotated[str, Field()]
    activity_version: Annotated[str, Field()]
    activity_groupings: Annotated[list[ActivityVersionDetailGrouping], Field()]
    activity_instances: Annotated[list[ActivityHierarchySimpleModel], Field()]

    @classmethod
    def from_repository_input(cls, data: dict[Any, Any]) -> Self:
        return cls(
            activity_uid=data["activity_uid"],
            activity_version=data["activity_version"],
            activity_groupings=[
                ActivityVersionDetailGrouping(
                    valid_group_uid=grouping["valid_group_uid"],
                    subgroup=ActivityVersionDetailSubgroup(
                        uid=grouping["subgroup"]["uid"],
                        name=grouping["subgroup"]["name"],
                        version=grouping["subgroup"]["version"],
                        status=grouping["subgroup"]["status"],
                    ),
                    group=ActivityVersionDetailGroup(
                        uid=grouping["group"]["uid"],
                        name=grouping["group"]["name"],
                        version=grouping["group"]["version"],
                        status=grouping["group"]["status"],
                    ),
                    activity_instances=[
                        ActivityHierarchySimpleModel(**instance)
                        for instance in grouping.get("activity_instances", [])
                    ],
                )
                for grouping in data["activity_groupings"]
            ],
            activity_instances=[
                ActivityHierarchySimpleModel(**instance)
                for instance in data["activity_instances"]
            ],
        )


class ActivityInstanceGroupingCompact(BaseModel):
    """Compact grouping info for an activity instance: group and subgroup uid/name."""

    activity_group_uid: Annotated[str, Field()]
    activity_group_name: Annotated[str, Field()]
    activity_subgroup_uid: Annotated[str, Field()]
    activity_subgroup_name: Annotated[str, Field()]


class ActivityInstanceCompact(BaseModel):
    """Compact activity instance with minimal info and groupings."""

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    topic_code: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    groupings: list[ActivityInstanceGroupingCompact] = Field(default_factory=list)


class ActivityVersionWithInstances(BaseModel):
    """An activity version number with all its linked instances."""

    version: Annotated[str, Field()]
    instances: list[ActivityInstanceCompact] = Field(default_factory=list)


class SimpleActivity(BaseModel):
    uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    nci_concept_id: Annotated[
        str | None,
        Field(
            json_schema_extra={"nullable": True},
        ),
    ] = None
    nci_concept_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    name: Annotated[str | None, Field()] = None
    name_sentence_case: Annotated[str | None, Field()] = None
    synonyms: Annotated[list[str], Field()]
    definition: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    abbreviation: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
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
    start_date: Annotated[
        datetime.datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    end_date: Annotated[
        datetime.datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class SimpleActivitySubGroup(BaseModel):
    uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    definition: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class SimpleActivityGroup(BaseModel):
    uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    definition: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class SimpleActivityGrouping(BaseModel):
    activity_group: Annotated[SimpleActivityGroup, Field()]
    activity_subgroup: Annotated[SimpleActivitySubGroup, Field()]


class SimpleActivityInstanceClassForActivity(BaseModel):
    name: Annotated[str, Field()]


class SimpleActivityInstance(BaseModel):
    uid: Annotated[str, Field()]
    nci_concept_id: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    nci_concept_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    name: Annotated[str, Field()]
    name_sentence_case: Annotated[str | None, Field()] = None
    abbreviation: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    definition: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    adam_param_code: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    is_required_for_activity: Annotated[bool, Field()] = False
    is_default_selected_for_activity: Annotated[bool, Field()] = False
    is_data_sharing: Annotated[bool, Field()] = False
    is_legacy_usage: Annotated[bool, Field()] = False
    is_derived: Annotated[bool, Field()] = False
    topic_code: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    is_research_lab: Annotated[bool, Field()] = False
    molecular_weight: Annotated[
        float | None, Field(json_schema_extra={"nullable": True})
    ] = None
    library_name: Annotated[str, Field()]
    activity_instance_class: Annotated[SimpleActivityInstanceClassForActivity, Field()]
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    start_date: Annotated[
        datetime.datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    end_date: Annotated[
        datetime.datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class ActivityOverview(BaseModel):
    activity: Annotated[SimpleActivity, Field()]
    activity_groupings: Annotated[list[SimpleActivityGrouping], Field()]
    activity_instances: Annotated[list[SimpleActivityInstance], Field()]
    all_versions: Annotated[list[str], Field()]

    @classmethod
    def from_repository_input(cls, overview: dict[str, Any]):
        return cls(
            activity=SimpleActivity(
                uid=overview.get("activity_value").get("uid"),
                nci_concept_id=overview.get("activity_value").get("nci_concept_id"),
                nci_concept_name=overview.get("activity_value").get("nci_concept_name"),
                name=overview.get("activity_value").get("name"),
                synonyms=overview.get("activity_value").get("synonyms", []),
                name_sentence_case=overview.get("activity_value").get(
                    "name_sentence_case"
                ),
                definition=overview.get("activity_value").get("definition"),
                abbreviation=overview.get("activity_value").get("abbreviation"),
                is_data_collected=overview.get("activity_value").get(
                    "is_data_collected", False
                ),
                is_multiple_selection_allowed=overview.get("activity_value").get(
                    "is_multiple_selection_allowed", True
                ),
                library_name=overview.get("activity_library_name"),
                version=overview.get("has_version", {}).get("version"),
                status=overview.get("has_version", {}).get("status"),
                start_date=convert_to_datetime(
                    overview.get("has_version", {}).get("start_date")
                ),
                end_date=convert_to_datetime(
                    overview.get("has_version", {}).get("end_date")
                ),
                author_username=overview.get("has_version", {}).get("author_username"),
            ),
            activity_groupings=[
                SimpleActivityGrouping(
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
            activity_instances=[
                SimpleActivityInstance(
                    uid=activity_instance.get("uid"),
                    nci_concept_id=activity_instance.get("nci_concept_id"),
                    nci_concept_name=activity_instance.get("nci_concept_name"),
                    name=activity_instance.get("name"),
                    name_sentence_case=activity_instance.get("name_sentence_case"),
                    abbreviation=activity_instance.get("abbreviation"),
                    definition=activity_instance.get("definition"),
                    adam_param_code=activity_instance.get("adam_param_code"),
                    is_required_for_activity=activity_instance.get(
                        "is_required_for_activity", False
                    ),
                    is_default_selected_for_activity=activity_instance.get(
                        "is_default_selected_for_activity", False
                    ),
                    is_data_sharing=activity_instance.get("is_data_sharing", False),
                    is_legacy_usage=activity_instance.get("is_legacy_usage", False),
                    is_derived=activity_instance.get("is_derived", False),
                    topic_code=activity_instance.get("topic_code"),
                    is_research_lab=activity_instance.get("is_research_lab", False),
                    molecular_weight=activity_instance.get("molecular_weight"),
                    library_name=activity_instance.get(
                        "activity_instance_library_name"
                    ),
                    activity_instance_class=SimpleActivityInstanceClassForActivity(
                        name=activity_instance.get("activity_instance_class").get(
                            "name"
                        )
                    ),
                    version=f"{activity_instance.get('version', {}).get('major_version')}.{activity_instance.get('version', {}).get('minor_version')}",
                    status=activity_instance.get("version", {}).get("status"),
                )
                for activity_instance in overview.get("activity_instances")
            ],
            all_versions=overview["all_versions"],
        )
