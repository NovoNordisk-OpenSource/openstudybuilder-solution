from typing import Annotated, Callable, Self

from pydantic import ConfigDict, Field, ValidationInfo, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    ObjectAction,
)
from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityItemClass,
)
from clinical_mdr_api.models.concepts.concept import VersionProperties
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.standard_data_models.dataset_class import DatasetClass
from clinical_mdr_api.models.utils import BaseModel, InputModel


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


class DataDomain(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(json_schema_extra={"source": "has_data_domain.uid", "nullable": True}),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_data_domain.has_name_root.has_latest_value.name",
                "nullable": True,
            }
        ),
    ] = None
    code_submission_value: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_data_domain.has_attributes_root.has_latest_value.code_submission_value",
                "nullable": True,
            }
        ),
    ] = None


class ParentDataDomain(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "parent_class.has_data_domain.uid",
                "nullable": True,
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "parent_class.has_data_domain.has_name_root.has_latest_value.name",
                "nullable": True,
            }
        ),
    ] = None
    code_submission_value: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "parent_class.has_data_domain.has_attributes_root.has_latest_value.code_submission_value",
                "nullable": True,
            }
        ),
    ] = None


class CompactActivityItemClass(BaseModel):
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
    activity_item_classes: Annotated[
        list[ParentActivityItemClass] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    data_domains: Annotated[
        list[ParentDataDomain] | None, Field(json_schema_extra={"nullable": True})
    ] = None


class SimpleDatasetClass(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(json_schema_extra={"source": "maps_dataset_class.uid", "nullable": True}),
    ] = None
    title: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "maps_dataset_class.has_instance.title",
                "nullable": True,
            }
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
    parent_class: Annotated[
        CompactActivityInstanceClass | None, Field(json_schema_extra={"nullable": True})
    ] = None
    dataset_class: Annotated[
        SimpleDatasetClass | None, Field(json_schema_extra={"nullable": True})
    ] = None
    activity_item_classes: Annotated[
        list[CompactActivityItemClass] | None,
        Field(json_schema_extra={"nullable": True}),
    ] = []
    data_domains: Annotated[
        list[DataDomain] | None, Field(json_schema_extra={"nullable": True})
    ] = []
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
        find_activity_instance_class_by_uid: Callable[
            [str], ActivityInstanceClassAR | None
        ],
        find_dataset_class_by_uid: Callable[[str], DatasetClass | None],
        get_activity_item_classes: Callable[[str], list[ActivityItemClass]],
        get_ct_terms: Callable[[str], list[CTTerm]],
    ) -> Self:
        parent_class = find_activity_instance_class_by_uid(
            activity_instance_class_ar.activity_instance_class_vo.parent_uid
        )
        dataset_class = find_dataset_class_by_uid(
            activity_instance_class_ar.activity_instance_class_vo.dataset_class_uid
        )
        _activity_item_classes = []
        if (
            items := activity_instance_class_ar.activity_instance_class_vo.activity_item_classes
        ):
            _activity_item_classes = get_activity_item_classes(
                filter_by={"uid": {"v": [item.uid for item in items]}}
            )[0]
        _parent_activity_item_classes = []
        if parent_class and (
            items := parent_class.activity_instance_class_vo.activity_item_classes
        ):
            _parent_activity_item_classes = get_activity_item_classes(
                filter_by={"uid": {"v": [item.uid for item in items]}}
            )[0]

        data_domains = []
        if (
            uids := activity_instance_class_ar.activity_instance_class_vo.data_domain_uids
        ):
            data_domains = get_ct_terms(filter_by={"term_uid": {"v": uids}}).items

        activity_item_classes = []
        for activity_item_class in _activity_item_classes:
            rel = next(
                item
                for item in activity_item_class.activity_instance_classes
                if item.uid == activity_instance_class_ar.uid
            )
            activity_item_classes.append(
                CompactActivityItemClass(
                    uid=activity_item_class.uid,
                    name=activity_item_class.name,
                    mandatory=rel.mandatory,
                    is_adam_param_specific_enabled=rel.is_adam_param_specific_enabled,
                )
            )

        parent_activity_item_classes = []
        for parent_activity_item_class in _parent_activity_item_classes:
            rel = next(
                item
                for item in parent_activity_item_class.activity_instance_classes
                if item.uid
                == activity_instance_class_ar.activity_instance_class_vo.parent_uid
            )
            parent_activity_item_classes.append(
                ParentActivityItemClass(
                    uid=parent_activity_item_class.uid,
                    name=parent_activity_item_class.name,
                    mandatory=rel.mandatory,
                    is_adam_param_specific_enabled=rel.is_adam_param_specific_enabled,
                )
            )

        return cls(
            uid=activity_instance_class_ar.uid,
            name=activity_instance_class_ar.name,
            order=activity_instance_class_ar.activity_instance_class_vo.order,
            definition=activity_instance_class_ar.activity_instance_class_vo.definition,
            is_domain_specific=activity_instance_class_ar.activity_instance_class_vo.is_domain_specific,
            level=activity_instance_class_ar.activity_instance_class_vo.level,
            parent_class=(
                CompactActivityInstanceClass(
                    uid=parent_class.uid,
                    name=parent_class.name,
                    activity_item_classes=parent_activity_item_classes,
                    data_domain_uids=parent_class.activity_instance_class_vo.data_domain_uids,
                )
                if parent_class
                else None
            ),
            dataset_class=(
                SimpleDatasetClass(uid=dataset_class.uid, title=dataset_class.title)
                if dataset_class
                else None
            ),
            activity_item_classes=activity_item_classes,
            data_domains=(
                DataDomain(uid=data_domain.uid, name=data_domain.name)
                for data_domain in data_domains
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


class ActivityInstanceClassInput(InputModel):
    name: Annotated[str | None, Field(min_length=1)] = None
    order: int | None = None
    definition: Annotated[str | None, Field(min_length=1)] = None
    is_domain_specific: bool | None = None
    level: int | None = None
    library_name: Annotated[str | None, Field(min_length=1)] = None
    parent_uid: Annotated[str | None, Field(min_length=1)] = None
    dataset_class_uid: Annotated[str | None, Field(min_length=1)] = None
    data_domain_uids: list[str] | None = None
    change_description: Annotated[str | None, Field(min_length=1)] = None


class ActivityInstanceClassVersion(ActivityInstanceClass):
    """
    Class for storing ActivityInstanceClass and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []
