from typing import Annotated, Self

from pydantic import BaseModel, Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.models.concepts.activities.activity import ActivityBase
from clinical_mdr_api.models.concepts.concept import ExtendedConceptPostInput
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import EditInputModel


class ActivityGroup(ActivityBase):
    nci_concept_id: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    nci_concept_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_activity_ar(cls, activity_group_ar: ActivityGroupAR) -> Self:
        return cls(
            uid=activity_group_ar.uid,
            name=activity_group_ar.name,
            name_sentence_case=activity_group_ar.concept_vo.name_sentence_case,
            definition=activity_group_ar.concept_vo.definition,
            abbreviation=activity_group_ar.concept_vo.abbreviation,
            nci_concept_id=activity_group_ar.concept_vo.nci_concept_id,
            nci_concept_name=activity_group_ar.concept_vo.nci_concept_name,
            library_name=Library.from_library_vo(activity_group_ar.library).name,
            start_date=activity_group_ar.item_metadata.start_date,
            end_date=activity_group_ar.item_metadata.end_date,
            status=activity_group_ar.item_metadata.status.value,
            version=activity_group_ar.item_metadata.version,
            change_description=activity_group_ar.item_metadata.change_description,
            author_username=activity_group_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in activity_group_ar.get_possible_actions()]
            ),
        )


class BaseActivityGroupInput(ExtendedConceptPostInput):
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


class ActivityGroupEditInput(BaseActivityGroupInput, EditInputModel):
    pass


class ActivityGroupCreateInput(BaseActivityGroupInput):
    library_name: Annotated[str, Field(min_length=1)]


class ActivityGroupVersion(ActivityGroup):
    """
    Class for storing ActivityGroup and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)


class ActivityGroupDetail(BaseModel):
    """Detailed view of an Activity Group for the overview endpoint"""

    name: Annotated[str, Field()]
    name_sentence_case: Annotated[str | None, Field()] = None
    nci_concept_id: Annotated[str | None, Field()] = None
    nci_concept_name: Annotated[str | None, Field()] = None
    library_name: Annotated[str | None, Field()] = None
    start_date: Annotated[str | None, Field()] = None
    end_date: Annotated[str | None, Field()] = None
    status: Annotated[str, Field()]
    version: Annotated[str, Field()]
    possible_actions: Annotated[list[str], Field()]
    change_description: Annotated[str, Field()]
    author_username: Annotated[str, Field()]
    definition: Annotated[str | None, Field()] = None
    abbreviation: Annotated[str | None, Field()] = None
    all_versions: list[str] = Field(default_factory=list)


class SimpleSubGroup(BaseModel):
    """Simple representation of a Subgroup for the overview listing"""

    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]
    version: Annotated[str, Field()]
    status: Annotated[str, Field()]
    start_date: Annotated[str, Field()]
    definition: Annotated[str | None, Field()] = None


class ActivityGroupOverview(BaseModel):
    """Complete overview model for an Activity Group"""

    group: Annotated[ActivityGroupDetail, Field()]
    subgroups: Annotated[list[SimpleSubGroup], Field()]
    all_versions: Annotated[list[str], Field()]
