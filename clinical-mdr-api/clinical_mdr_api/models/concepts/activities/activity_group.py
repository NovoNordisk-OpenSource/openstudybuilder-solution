from typing import Annotated, Self

from pydantic import BaseModel, Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.models.concepts.activities.activity import ActivityBase
from clinical_mdr_api.models.concepts.concept import (
    ExtendedConceptPatchInput,
    ExtendedConceptPostInput,
)
from clinical_mdr_api.models.libraries.library import Library


class ActivityGroup(ActivityBase):
    @classmethod
    def from_activity_ar(cls, activity_group_ar: ActivityGroupAR) -> Self:
        return cls(
            uid=activity_group_ar.uid,
            name=activity_group_ar.name,
            name_sentence_case=activity_group_ar.concept_vo.name_sentence_case,
            definition=activity_group_ar.concept_vo.definition,
            abbreviation=activity_group_ar.concept_vo.abbreviation,
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


class ActivityGroupEditInput(ExtendedConceptPatchInput):
    change_description: Annotated[str | None, Field(min_length=1)] = None


class ActivityGroupCreateInput(ExtendedConceptPostInput):
    library_name: Annotated[str, Field(min_length=1)]


class ActivityGroupVersion(ActivityGroup):
    """
    Class for storing ActivityGroup and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []


class ActivityGroupDetail(BaseModel):
    """Detailed view of an Activity Group for the overview endpoint"""

    name: str
    name_sentence_case: str | None = None
    library_name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: str
    version: str
    possible_actions: list[str]
    change_description: str | None = None
    author_username: str
    definition: str | None = None
    abbreviation: str | None = None


class SimpleSubGroup(BaseModel):
    """Simple representation of a Subgroup for the overview listing"""

    uid: str
    name: str
    version: str
    status: str
    definition: str | None = None


class ActivityGroupOverview(BaseModel):
    """Complete overview model for an Activity Group"""

    group: ActivityGroupDetail
    subgroups: list[SimpleSubGroup]
    all_versions: list[str]
