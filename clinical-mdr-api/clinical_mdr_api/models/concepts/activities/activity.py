import datetime
from typing import Annotated, Callable, Self

from pydantic import Field, validator

from clinical_mdr_api.domains.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domains.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    ObjectAction,
)
from clinical_mdr_api.models.concepts.concept import (
    Concept,
    ExtendedConceptPatchInput,
    ExtendedConceptPostInput,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, InputModel, PatchInputModel
from common.exceptions import ValidationException
from common.utils import convert_to_datetime


class ActivityHierarchySimpleModel(BaseModel):

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(nullable=True)] = None

    @classmethod
    def from_activity_uid(
        cls,
        uid: str,
        find_activity_by_uid: Callable[[str], ConceptARBase | None],
        version: str | None = None,
    ) -> Self | None:
        if uid is not None:
            activity = find_activity_by_uid(uid, version=version)
            if activity is not None:
                simple_activity_model = cls(uid=uid, name=activity.concept_vo.name)
            else:
                simple_activity_model = cls(uid=uid, name=None)
        else:
            simple_activity_model = None
        return simple_activity_model

    @classmethod
    def from_activity_ar_object(
        cls, activity_ar: ActivityGroupAR | ActivitySubGroupAR
    ) -> Self:
        return cls(uid=activity_ar.uid, name=activity_ar.name)

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(nullable=True)] = None


class ActivityGroupingHierarchySimpleModel(BaseModel):
    class Config:
        orm_mode = True

    activity_group_uid: Annotated[
        str,
        Field(
            source="has_latest_value.has_grouping.in_subgroup.in_group.has_version.uid",
        ),
    ]
    activity_group_name: Annotated[
        str,
        Field(
            source="has_latest_value.has_grouping.in_subgroup.in_group.name",
        ),
    ]
    activity_subgroup_uid: Annotated[
        str,
        Field(
            source="has_latest_value.has_grouping.in_subgroup.has_group.has_version.uid",
        ),
    ]
    activity_subgroup_name: Annotated[
        str,
        Field(
            source="has_latest_value.has_grouping.in_subgroup.has_group.name",
        ),
    ]


class ActivityBase(Concept):
    possible_actions: Annotated[
        list[str],
        Field(
            description=(
                "Holds those actions that can be performed on the ActivityInstances. "
                "Actions are: 'approve', 'edit', 'new_version'."
            ),
        ),
    ]

    @validator("possible_actions", pre=True, always=True)
    # pylint: disable=no-self-argument,unused-argument
    def validate_possible_actions(cls, value, values):
        if values["status"] == LibraryItemStatus.DRAFT.value and values[
            "version"
        ].startswith("0"):
            return [
                ObjectAction.APPROVE.value,
                ObjectAction.DELETE.value,
                ObjectAction.EDIT.value,
            ]
        if values["status"] == LibraryItemStatus.DRAFT.value:
            return [ObjectAction.APPROVE.value, ObjectAction.EDIT.value]
        if values["status"] == LibraryItemStatus.FINAL.value:
            return [
                ObjectAction.INACTIVATE.value,
                ObjectAction.NEWVERSION.value,
            ]
        if values["status"] == LibraryItemStatus.RETIRED.value:
            return [ObjectAction.REACTIVATE.value]
        return []


class Activity(ActivityBase):
    nci_concept_id: Annotated[str | None, Field(nullable=True)] = None
    nci_concept_name: Annotated[str | None, Field(nullable=True)] = None

    @classmethod
    def from_activity_ar(cls, activity_ar: ActivityAR) -> Self:
        activity_groupings = []
        for activity_grouping in activity_ar.concept_vo.activity_groupings:
            activity_groupings.append(
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid=activity_grouping.activity_group_uid,
                    activity_group_name=activity_grouping.activity_group_name,
                    activity_subgroup_uid=activity_grouping.activity_subgroup_uid,
                    activity_subgroup_name=activity_grouping.activity_subgroup_name,
                )
            )
        activity_groupings.sort(
            key=lambda item: (item.activity_subgroup_name, item.activity_group_name)
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
            is_request_final=activity_ar.concept_vo.is_request_final,
            is_request_rejected=activity_ar.concept_vo.is_request_rejected,
            reason_for_rejecting=activity_ar.concept_vo.reason_for_rejecting,
            contact_person=activity_ar.concept_vo.contact_person,
            requester_study_id=activity_ar.concept_vo.requester_study_id,
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
        activity_subgroup_ars: list[ActivitySubGroupAR],
        activity_group_ars: list[ActivitySubGroupAR],
    ) -> Self:
        activity_groupings = []
        for activity_grouping in activity_ar.concept_vo.activity_groupings:
            activity_subgroup, activity_group = None, None
            for activity_subgroup_ar in activity_subgroup_ars:
                if activity_subgroup_ar.uid == activity_grouping.activity_subgroup_uid:
                    activity_subgroup = (
                        ActivityHierarchySimpleModel.from_activity_ar_object(
                            activity_ar=activity_subgroup_ar,
                        )
                    )
                    break
            for activity_group_ar in activity_group_ars:
                if activity_group_ar.uid == activity_grouping.activity_group_uid:
                    activity_group = (
                        ActivityHierarchySimpleModel.from_activity_ar_object(
                            activity_ar=activity_group_ar,
                        )
                    )
                    break
            ValidationException.raise_if(
                not activity_group or not activity_subgroup,
                msg="Either ActivityGroup or ActivitySubGroup can't be find in fetched groupings",
            )
            activity_groupings.append(
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid=activity_group.uid,
                    activity_group_name=activity_group.name,
                    activity_subgroup_uid=activity_subgroup.uid,
                    activity_subgroup_name=activity_subgroup.name,
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
            activity_groupings=sorted(
                activity_groupings,
                key=lambda item: (
                    item.activity_subgroup_name,
                    item.activity_group_name,
                ),
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
            requester_study_id=activity_ar.concept_vo.requester_study_id,
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

    activity_groupings: Annotated[
        list[ActivityGroupingHierarchySimpleModel], Field()
    ] = []
    synonyms: Annotated[list[str], Field(remove_from_wildcard=True)]
    request_rationale: Annotated[
        str | None,
        Field(
            description="The rationale of the activity request",
            nullable=True,
            remove_from_wildcard=True,
        ),
    ] = None
    is_request_final: Annotated[
        bool,
        Field(
            description="The flag indicating if activity request is finalized",
            nullable=False,
            remove_from_wildcard=True,
        ),
    ] = False
    is_request_rejected: Annotated[
        bool,
        Field(
            description="The flag indicating if activity request is rejected",
            nullable=False,
            remove_from_wildcard=True,
        ),
    ] = False
    contact_person: Annotated[
        str | None,
        Field(
            description="The person to contact with about rejection",
            nullable=True,
            remove_from_wildcard=True,
        ),
    ] = None
    reason_for_rejecting: Annotated[
        str | None,
        Field(
            description="The reason why request was rejected",
            nullable=True,
            remove_from_wildcard=True,
        ),
    ] = None
    requester_study_id: Annotated[
        str | None,
        Field(
            description="The study_id of the Study which requested an Activity request",
            nullable=True,
            remove_from_wildcard=True,
        ),
    ] = None
    replaced_by_activity: Annotated[
        str | None,
        Field(
            description="The uid of the replacing Activity",
            nullable=True,
            remove_from_wildcard=True,
        ),
    ] = None
    is_data_collected: Annotated[
        bool,
        Field(
            description="Boolean flag indicating whether data is collected for this activity",
            nullable=False,
        ),
    ] = False
    is_multiple_selection_allowed: Annotated[
        bool,
        Field(
            description="Boolean flag indicating whether multiple selections are allowed for this activity",
            nullable=False,
        ),
    ] = True
    is_finalized: Annotated[
        bool,
        Field(
            title="Computed boolean value based on is_request_rejected and replaced_by_activity",
            description="Evaluates to false, if is_request_rejected is false and replaced_by_activity is null else true",
            nullable=False,
        ),
    ] = False
    is_used_by_legacy_instances: Annotated[
        bool,
        Field(
            title="True if all instances linked to given Activity are legacy_used.",
            nullable=False,
        ),
    ] = False


class ActivityForStudyActivity(Activity):
    activity_groupings: Annotated[
        list[ActivityGroupingHierarchySimpleModel], Field(remove_from_wildcard=True)
    ]


class ActivityGrouping(InputModel):
    activity_group_uid: str
    activity_subgroup_uid: str


class ActivityPostInput(ExtendedConceptPostInput):
    nci_concept_id: Annotated[str | None, Field(min_length=1)] = None
    nci_concept_name: Annotated[str | None, Field(min_length=1)] = None
    activity_groupings: list[ActivityGrouping] | None = None
    synonyms: list[str] | None = None
    request_rationale: Annotated[str | None, Field(min_length=1)] = None
    is_request_final: bool = False
    is_data_collected: bool = False
    is_multiple_selection_allowed: bool = True


class ActivityEditInput(ExtendedConceptPatchInput):
    nci_concept_id: Annotated[str | None, Field(min_length=1)] = None
    nci_concept_name: Annotated[str | None, Field(min_length=1)] = None
    activity_groupings: list[ActivityGrouping] | None = None
    synonyms: list[str] | None = None
    request_rationale: Annotated[str | None, Field(min_length=1)] = None
    is_request_final: bool = False
    is_data_collected: bool = False
    is_multiple_selection_allowed: bool = True
    change_description: Annotated[str | None, Field(min_length=1)] = None


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

    changes: Annotated[
        dict[str, bool] | None,
        Field(
            description=(
                "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
                "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
            ),
            nullable=True,
        ),
    ] = None


class SimpleActivity(BaseModel):
    nci_concept_id: Annotated[
        str | None,
        Field(
            nullable=True,
        ),
    ] = None
    nci_concept_name: Annotated[str | None, Field(nullable=True)] = None
    name: Annotated[str | None, Field()] = None
    name_sentence_case: Annotated[str | None, Field()] = None
    synonyms: Annotated[list[str], Field()]
    definition: Annotated[str | None, Field(nullable=True)] = None
    abbreviation: Annotated[str | None, Field(nullable=True)] = None
    is_data_collected: Annotated[
        bool,
        Field(
            description="Boolean flag indicating whether data is collected for this activity",
            nullable=False,
        ),
    ] = False
    is_multiple_selection_allowed: Annotated[
        bool,
        Field(
            description="Boolean flag indicating whether multiple selections are allowed for this activity",
            nullable=False,
        ),
    ] = True
    library_name: Annotated[str | None, Field(nullable=True)] = None
    version: Annotated[str | None, Field(nullable=True)] = None
    status: Annotated[str | None, Field(nullable=True)] = None
    start_date: Annotated[datetime.datetime | None, Field(nullable=True)] = None
    end_date: Annotated[datetime.datetime | None, Field(nullable=True)] = None


class SimpleActivitySubGroup(BaseModel):
    name: Annotated[str | None, Field(nullable=True)] = None
    definition: Annotated[str | None, Field(nullable=True)] = None


class SimpleActivityGroup(BaseModel):
    name: Annotated[str | None, Field(nullable=True)] = None
    definition: Annotated[str | None, Field(nullable=True)] = None


class SimpleActivityGrouping(BaseModel):
    activity_group: SimpleActivityGroup
    activity_subgroup: SimpleActivitySubGroup


class SimpleActivityInstanceClass(BaseModel):
    name: Annotated[str, Field()]


class SimpleActivityInstance(BaseModel):
    uid: str
    nci_concept_id: Annotated[str | None, Field(nullable=True)] = None
    nci_concept_name: Annotated[str | None, Field(nullable=True)] = None
    name: Annotated[str, Field()]
    name_sentence_case: Annotated[str | None, Field()] = None
    abbreviation: Annotated[str | None, Field(nullable=True)] = None
    definition: Annotated[str | None, Field(nullable=True)] = None
    adam_param_code: Annotated[str | None, Field(nullable=True)] = None
    is_required_for_activity: Annotated[bool, Field()] = False
    is_default_selected_for_activity: Annotated[bool, Field()] = False
    is_data_sharing: Annotated[bool, Field()] = False
    is_legacy_usage: Annotated[bool, Field()] = False
    is_derived: Annotated[bool, Field()] = False
    topic_code: Annotated[str | None, Field(nullable=True)] = None
    is_research_lab: Annotated[bool, Field()] = False
    molecular_weight: Annotated[float | None, Field(nullable=True)] = None
    library_name: Annotated[str, Field()]
    activity_instance_class: Annotated[SimpleActivityInstanceClass, Field()]
    version: Annotated[str | None, Field(nullable=True)] = None
    status: Annotated[str | None, Field(nullable=True)] = None
    start_date: Annotated[datetime.datetime | None, Field(nullable=True)] = None
    end_date: Annotated[datetime.datetime | None, Field(nullable=True)] = None


class ActivityOverview(BaseModel):
    activity: Annotated[SimpleActivity, Field()]
    activity_groupings: Annotated[list[SimpleActivityGrouping], Field()]
    activity_instances: Annotated[list[SimpleActivityInstance], Field()]
    all_versions: Annotated[list[str], Field()]

    @classmethod
    def from_repository_input(cls, overview: dict):
        return cls(
            activity=SimpleActivity(
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
            ),
            activity_groupings=[
                SimpleActivityGrouping(
                    activity_group=SimpleActivityGroup(
                        name=activity_grouping.get("activity_group_value").get("name"),
                        definition=activity_grouping.get("activity_group_value").get(
                            "definition"
                        ),
                    ),
                    activity_subgroup=SimpleActivitySubGroup(
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
                    activity_instance_class=SimpleActivityInstanceClass(
                        name=activity_instance.get("activity_instance_class").get(
                            "name"
                        )
                    ),
                    version=f"{activity_instance.get('version', {}).get('major_version')}.{activity_instance.get('version', {}).get('minor_version')}",
                    status=activity_instance.get("version", {}).get("status"),
                )
                for activity_instance in overview.get("activity_instances")
            ],
            all_versions=overview.get("all_versions"),
        )
