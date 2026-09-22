from datetime import datetime
from typing import Annotated, Any, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.models.concepts.activities.activity import ActivityBase
from clinical_mdr_api.models.concepts.concept import ExtendedConceptPostInput
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, EditInputModel


class ActivitySubGroup(ActivityBase):
    nci_concept_id: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    nci_concept_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_activity_ar(
        cls,
        activity_subgroup_ar: ActivitySubGroupAR,
    ) -> Self:

        return cls(
            uid=activity_subgroup_ar.uid,
            name=activity_subgroup_ar.name,
            name_sentence_case=activity_subgroup_ar.concept_vo.name_sentence_case,
            definition=activity_subgroup_ar.concept_vo.definition,
            abbreviation=activity_subgroup_ar.concept_vo.abbreviation,
            nci_concept_id=activity_subgroup_ar.concept_vo.nci_concept_id,
            nci_concept_name=activity_subgroup_ar.concept_vo.nci_concept_name,
            library_name=Library.from_library_vo(activity_subgroup_ar.library).name,
            start_date=activity_subgroup_ar.item_metadata.start_date,
            end_date=activity_subgroup_ar.item_metadata.end_date,
            status=activity_subgroup_ar.item_metadata.status.value,
            version=activity_subgroup_ar.item_metadata.version,
            change_description=activity_subgroup_ar.item_metadata.change_description,
            author_username=activity_subgroup_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in activity_subgroup_ar.get_possible_actions()]
            ),
        )


class ActivitySubGroupCreateInput(ExtendedConceptPostInput):
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
    library_name: Annotated[str, Field(min_length=1)]


class ActivitySubGroupEditInput(ActivitySubGroupCreateInput, EditInputModel):
    pass


class ActivitySubGroupVersion(ActivitySubGroup):
    """
    Class for storing ActivitySubGroup and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)


class ActivityGroupForActivitySubGroup(BaseModel):
    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]
    version: Annotated[str | None, Field()] = None
    status: Annotated[str | None, Field()] = None


class ActivitySubGroupDetail(BaseModel):
    name: Annotated[str | None, Field()] = None
    name_sentence_case: Annotated[str | None, Field()] = None
    nci_concept_id: Annotated[str | None, Field()] = None
    nci_concept_name: Annotated[str | None, Field()] = None
    library_name: Annotated[str | None, Field()] = None
    definition: Annotated[str | None, Field()] = None
    start_date: Annotated[datetime | None, Field()] = None
    end_date: Annotated[datetime | None, Field()] = None
    status: Annotated[str | None, Field()] = None
    version: Annotated[str | None, Field()] = None
    possible_actions: Annotated[list[str] | None, Field()] = None
    change_description: Annotated[str, Field()]
    author_username: Annotated[str | None, Field()] = None


class ActivitySubGroupOverview(BaseModel):
    activity_subgroup: Annotated[ActivitySubGroupDetail, Field()]
    all_versions: Annotated[list[str], Field()]

    @classmethod
    def from_repository_input(cls, overview: dict[str, Any]):
        # Extract subgroup data from correct nested structure
        subgroup_value = overview.get("subgroup_value", {})
        latest_version = overview.get("has_version", {})
        library_info = overview.get("library", {})

        # Get version data from correct structure
        version_data = latest_version.get("has_version", {}) if latest_version else {}

        return cls(
            activity_subgroup=ActivitySubGroupDetail(
                # Map basic fields from subgroup_value
                name=subgroup_value.get("name"),
                name_sentence_case=subgroup_value.get("name_sentence_case"),
                nci_concept_id=subgroup_value.get("nci_concept_id"),
                nci_concept_name=subgroup_value.get("nci_concept_name"),
                definition=subgroup_value.get("definition"),
                # Get library name from library node
                library_name=library_info.get("name"),
                # Get version metadata from version node
                start_date=convert_to_datetime(version_data.get("start_date")),
                end_date=convert_to_datetime(version_data.get("end_date")),
                status=version_data.get("status"),
                version=version_data.get("version"),
                possible_actions=version_data.get("possible_actions"),
                change_description=version_data["change_description"],
            ),
            all_versions=overview.get("all_versions", []),
        )
