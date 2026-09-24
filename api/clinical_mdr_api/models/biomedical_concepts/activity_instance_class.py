from typing import Annotated, Any, Callable, Self

from pydantic import ConfigDict, Field, ValidationInfo, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    ObjectAction,
)
from clinical_mdr_api.models.concepts.concept import VersionProperties
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, InputModel, PatchInputModel
from common.utils import convert_to_datetime


class ParentActivityItemClass(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "parent_class.has_activity_item_class.uid",
                "nullable": True,
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "parent_class.has_activity_item_class.has_latest_value.name",
                "nullable": True,
            }
        ),
    ] = None
    mandatory: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "parent_class.has_activity_item_class|mandatory",
                "nullable": True,
            }
        ),
    ] = None
    is_adam_param_specific_enabled: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "parent_class.has_activity_item_class|is_adam_param_specific_enabled",
                "nullable": True,
            }
        ),
    ] = None
    is_additional_optional: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "parent_class.has_activity_item_class|is_additional_optional",
                "nullable": True,
            }
        ),
    ] = False
    is_default_linked: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "parent_class.has_activity_item_class|is_default_linked",
                "nullable": True,
            }
        ),
    ] = False


class CompactActivityItemClassForInstanceClass(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_activity_item_class.uid",
                "nullable": True,
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_activity_item_class.has_latest_value.name",
                "nullable": True,
            }
        ),
    ] = None
    display_name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_activity_item_class.has_latest_value.display_name",
                "nullable": True,
            }
        ),
    ] = None
    mandatory: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_item_class|mandatory",
                "nullable": True,
            }
        ),
    ] = None
    is_adam_param_specific_enabled: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_item_class|is_adam_param_specific_enabled",
                "nullable": True,
            }
        ),
    ] = None
    is_additional_optional: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_item_class|is_additional_optional",
                "nullable": True,
            }
        ),
    ] = False
    is_default_linked: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_item_class|is_default_linked",
                "nullable": True,
            }
        ),
    ] = False
    data_type_uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_activity_item_class.has_latest_value.has_data_type.has_selected_term.uid",
                "nullable": True,
            }
        ),
    ] = None
    data_type_name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_activity_item_class.has_latest_value.has_data_type.has_selected_term.has_name_root.has_latest_value.name",
                "nullable": True,
            }
        ),
    ] = None


class CompactActivityInstanceClass(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(json_schema_extra={"source": "parent_class.uid", "nullable": True}),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "parent_class.has_latest_value.name",
                "nullable": True,
            },
        ),
    ] = None


class ActivityInstanceClass(VersionProperties):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None, Field(json_schema_extra={"source": "uid", "nullable": True})
    ] = None
    name: Annotated[
        str | None,
        Field(json_schema_extra={"source": "has_latest_value.name", "nullable": True}),
    ] = None
    order: Annotated[
        int | None,
        Field(json_schema_extra={"source": "has_latest_value.order", "nullable": True}),
    ] = None
    definition: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.definition",
                "nullable": True,
            }
        ),
    ] = None
    is_domain_specific: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.is_domain_specific",
                "nullable": True,
            },
        ),
    ] = None
    level: Annotated[
        int | None,
        Field(json_schema_extra={"source": "has_latest_value.level", "nullable": True}),
    ] = None
    nci_concept_id: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.nci_concept_id",
                "nullable": True,
            }
        ),
    ] = None
    nci_concept_name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.nci_concept_name",
                "nullable": True,
            }
        ),
    ] = None
    parent_class: Annotated[
        CompactActivityInstanceClass | None, Field(json_schema_extra={"nullable": True})
    ] = None
    library_name: Annotated[
        str | None,
        Field(json_schema_extra={"source": "has_library.name", "nullable": True}),
    ] = None
    possible_actions: Annotated[
        list[str],
        Field(
            validate_default=True,
            description=(
                "Holds those actions that can be performed on the ActivityInstances. "
                "Actions are: 'approve', 'edit', 'new_version'."
            ),
        ),
    ]

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

    @classmethod
    def from_activity_instance_class_ar(
        cls,
        activity_instance_class_ar: ActivityInstanceClassAR,
        get_parent_class: Callable[[str], tuple[str, str] | None],
    ) -> Self:
        parent_class = get_parent_class(activity_instance_class_ar.uid)

        return cls(
            uid=activity_instance_class_ar.uid,
            name=activity_instance_class_ar.name,
            order=activity_instance_class_ar.activity_instance_class_vo.order,
            definition=activity_instance_class_ar.activity_instance_class_vo.definition,
            is_domain_specific=activity_instance_class_ar.activity_instance_class_vo.is_domain_specific,
            level=activity_instance_class_ar.activity_instance_class_vo.level,
            nci_concept_id=activity_instance_class_ar.activity_instance_class_vo.nci_concept_id,
            nci_concept_name=activity_instance_class_ar.activity_instance_class_vo.nci_concept_name,
            parent_class=(
                CompactActivityInstanceClass(
                    uid=parent_class[0],
                    name=parent_class[1],
                )
                if parent_class
                else None
            ),
            library_name=Library.from_library_vo(
                activity_instance_class_ar.library
            ).name,
            start_date=activity_instance_class_ar.item_metadata.start_date,
            end_date=activity_instance_class_ar.item_metadata.end_date,
            status=activity_instance_class_ar.item_metadata.status.value,
            version=activity_instance_class_ar.item_metadata.version,
            change_description=activity_instance_class_ar.item_metadata.change_description,
            author_username=activity_instance_class_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in activity_instance_class_ar.get_possible_actions()]
            ),
        )

    @classmethod
    def from_cypher_row(cls, row: dict[str, Any]) -> Self:
        return cls(
            uid=row["uid"],
            name=row["name"],
            order=row.get("order_val"),
            definition=row.get("definition"),
            is_domain_specific=row.get("is_domain_specific"),
            level=row.get("level"),
            nci_concept_id=row.get("nci_concept_id"),
            nci_concept_name=row.get("nci_concept_name"),
            library_name=row.get("library_name"),
            start_date=convert_to_datetime(row.get("start_date")),
            end_date=convert_to_datetime(row.get("end_date")),
            status=row.get("status"),
            version=row.get("version"),
            change_description=row.get("change_description"),
            author_username=row.get("author_username"),
            possible_actions=[],
        )


class ActivityInstanceClassInput(InputModel):
    name: Annotated[str | None, Field(min_length=1)] = None
    order: Annotated[int | None, Field()] = None
    definition: Annotated[str | None, Field(min_length=1)] = None
    is_domain_specific: Annotated[bool, Field()] = False
    level: Annotated[int | None, Field()] = None
    nci_concept_id: Annotated[str | None, Field(min_length=1)] = None
    nci_concept_name: Annotated[str | None, Field(min_length=1)] = None
    library_name: Annotated[str | None, Field(min_length=1)] = None
    parent_uid: Annotated[str | None, Field(min_length=1)] = None
    dataset_class_uid: Annotated[str | None, Field(min_length=1)] = None


class ActivityInstanceClassEditInput(ActivityInstanceClassInput):
    change_description: Annotated[str, Field(min_length=1)]


class ActivityInstanceClassMappingInput(PatchInputModel):
    dataset_class_uid: str


class ActivityInstanceClassVersion(ActivityInstanceClass):
    """
    Class for storing ActivityInstanceClass and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)


class ActivityInstanceClassWithDataset(BaseModel):
    uid: Annotated[str, Field(json_schema_extra={"nullable": False})]
    name: Annotated[
        str,
        Field(json_schema_extra={"nullable": False}),
    ]

    datasets: list[str] = Field(default_factory=list)


class ActivityInstanceClassDetail(BaseModel):
    """Detailed view of an Activity Instance Class for the overview endpoint"""

    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]
    definition: Annotated[str | None, Field()] = None
    is_domain_specific: Annotated[bool, Field()] = False
    level: Annotated[int | None, Field()] = None
    nci_concept_id: Annotated[str | None, Field()] = None
    nci_concept_name: Annotated[str | None, Field()] = None
    library_name: Annotated[str | None, Field()] = None
    start_date: Annotated[str | None, Field()] = None
    end_date: Annotated[str | None, Field()] = None
    status: Annotated[str, Field()]
    version: Annotated[str, Field()]
    change_description: Annotated[str | None, Field()] = None
    author_username: Annotated[str | None, Field()] = None
    hierarchy: Annotated[str | None, Field()] = None
    parent_class: Annotated[CompactActivityInstanceClass | None, Field()] = None


class SimpleActivityInstanceClass(BaseModel):
    """Simple representation of an Activity Instance Class for overview listing"""

    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]
    definition: Annotated[str | None, Field()] = None
    is_domain_specific: Annotated[bool, Field()] = False
    library_name: Annotated[str | None, Field()] = None
    modified_date: Annotated[str | None, Field()] = None
    modified_by: Annotated[str | None, Field()] = None
    version: Annotated[str | None, Field()] = None
    status: Annotated[str | None, Field()] = None


class SimpleActivityItemClass(BaseModel):
    """Simple representation of an Activity Item Class for overview listing"""

    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]
    parent_name: Annotated[str | None, Field()] = None
    parent_uid: Annotated[str | None, Field()] = None
    definition: Annotated[str | None, Field()] = None
    modified_date: Annotated[str | None, Field()] = None
    modified_by: Annotated[str | None, Field()] = None
    version: Annotated[str | None, Field()] = None
    status: Annotated[str | None, Field()] = None


class ActivityInstanceParentClassOverview(BaseModel):
    """Complete overview model for an Activity Instance Parent Class"""

    parent_activity_instance_class: Annotated[ActivityInstanceClassDetail, Field()]
    all_versions: Annotated[list[str], Field()]


class ActivityInstanceClassOverview(BaseModel):
    """Complete overview model for an Activity Instance Class"""

    activity_instance_class: Annotated[ActivityInstanceClassDetail, Field()]
    all_versions: Annotated[list[str], Field()]
