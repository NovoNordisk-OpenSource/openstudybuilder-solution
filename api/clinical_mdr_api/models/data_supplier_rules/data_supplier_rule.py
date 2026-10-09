from collections.abc import Callable
from typing import Annotated, Self

from pydantic import ConfigDict, Field, ValidationInfo, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.data_supplier_rules.data_supplier_rule import (
    DataSupplierRuleAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    ObjectAction,
)
from clinical_mdr_api.models.concepts.concept import VersionProperties
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, InputModel
from common.config import settings


class DataSupplierRuleTypeTerm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_data_supplier_type.has_selected_term.uid",
                "nullable": True,
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_data_supplier_type.has_selected_term.has_name_root.has_latest_value.name",
                "nullable": True,
            },
        ),
    ] = None


class DataSupplierRuleActivityGrouping(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    activity_uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_activity_grouping.has_grouping.has_version.uid",
                "nullable": True,
            }
        ),
    ] = None
    activity_name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_activity_grouping.has_grouping.name",
                "nullable": True,
            }
        ),
    ] = None
    activity_group_uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_activity_grouping.has_selected_group.has_version.uid",
                "nullable": True,
            }
        ),
    ] = None
    activity_group_name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_activity_grouping.has_selected_group.name",
                "nullable": True,
            }
        ),
    ] = None
    activity_subgroup_uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_activity_grouping.has_selected_subgroup.has_version.uid",
                "nullable": True,
            }
        ),
    ] = None
    activity_subgroup_name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_activity_grouping.has_selected_subgroup.name",
                "nullable": True,
            }
        ),
    ] = None


class DataSupplierRule(VersionProperties):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None, Field(json_schema_extra={"source": "uid", "nullable": True})
    ] = None
    description: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.description",
                "nullable": True,
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.name",
                "nullable": True,
            }
        ),
    ] = None
    data_supplier_type: Annotated[DataSupplierRuleTypeTerm | None, Field()] = Field(
        default=None,
        json_schema_extra={
            "exclude_from_model_validate": True,
            "remove_from_wildcard": True,
        },
    )
    activity_groupings: list[DataSupplierRuleActivityGrouping] = Field(
        default_factory=list,
        json_schema_extra={
            "exclude_from_model_validate": True,
            "remove_from_wildcard": True,
        },
    )
    library_name: Annotated[
        str | None,
        Field(json_schema_extra={"source": "has_library.name", "nullable": True}),
    ] = None
    possible_actions: Annotated[
        list[str],
        Field(
            validate_default=True,
            description=(
                "Holds those actions that can be performed on the DataSupplierRules. "
                "Actions are: 'approve', 'edit', 'new_version'."
            ),
        ),
    ]

    @classmethod
    def from_data_supplier_rule_ar(
        cls,
        data_supplier_rule_ar: DataSupplierRuleAR,
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
    ) -> Self:
        data_supplier_type = None
        type_uid = data_supplier_rule_ar.data_supplier_rule_vo.data_supplier_type_uid
        if type_uid is not None:
            type_term = find_term_by_uid(type_uid)
            if type_term is not None:
                data_supplier_type = DataSupplierRuleTypeTerm(
                    uid=type_term.uid, name=type_term.name
                )

        return cls(
            uid=data_supplier_rule_ar.uid,
            description=data_supplier_rule_ar.data_supplier_rule_vo.description,
            name=data_supplier_rule_ar.data_supplier_rule_vo.name,
            data_supplier_type=data_supplier_type,
            activity_groupings=[
                DataSupplierRuleActivityGrouping(
                    activity_uid=grouping.activity_uid,
                    activity_name=grouping.activity_name,
                    activity_group_uid=grouping.activity_group_uid,
                    activity_group_name=grouping.activity_group_name,
                    activity_subgroup_uid=grouping.activity_subgroup_uid,
                    activity_subgroup_name=grouping.activity_subgroup_name,
                )
                for grouping in data_supplier_rule_ar.data_supplier_rule_vo.activity_groupings
            ],
            library_name=Library.from_library_vo(data_supplier_rule_ar.library).name,
            start_date=data_supplier_rule_ar.item_metadata.start_date,
            end_date=data_supplier_rule_ar.item_metadata.end_date,
            status=data_supplier_rule_ar.item_metadata.status.value,
            version=data_supplier_rule_ar.item_metadata.version,
            change_description=data_supplier_rule_ar.item_metadata.change_description,
            author_username=data_supplier_rule_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in data_supplier_rule_ar.get_possible_actions()]
            ),
        )

    @field_validator("possible_actions", mode="before")
    @classmethod
    def validate_possible_actions(cls, _, info: ValidationInfo):
        if info.data["status"] == LibraryItemStatus.FINAL.value:
            return [ObjectAction.EDIT.value, ObjectAction.INACTIVATE.value]
        if info.data["status"] == LibraryItemStatus.RETIRED.value:
            return [ObjectAction.REACTIVATE.value]
        return []


class DataSupplierRuleVersion(DataSupplierRule):
    """
    Class for storing DataSupplierRule and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)


class DataSupplierRuleActivityGroupingInput(InputModel):
    activity_uid: Annotated[str, Field(min_length=1)]
    activity_group_uid: Annotated[str, Field(min_length=1)]
    activity_subgroup_uid: Annotated[str, Field(min_length=1)]


class DataSupplierRuleInput(InputModel):
    name: Annotated[str, Field(min_length=1)]
    description: Annotated[str | None, Field(min_length=1)] = None
    activity_groupings: Annotated[
        list[DataSupplierRuleActivityGroupingInput], Field(min_length=1)
    ]
    data_supplier_type_uid: Annotated[str | None, Field(min_length=1)] = None
    library_name: Annotated[str, Field(min_length=1)] = settings.sponsor_library_name


class DataSupplierRuleEditInput(InputModel):
    """Input model for PATCH endpoint - all fields optional except change_description."""

    name: Annotated[str | None, Field(min_length=1)] = None
    description: Annotated[str | None, Field(min_length=1)] = None
    activity_groupings: Annotated[
        list[DataSupplierRuleActivityGroupingInput] | None,
        Field(
            min_length=1,
            description="Omit to leave the current activity groupings unchanged.",
        ),
    ] = None
    data_supplier_type_uid: Annotated[
        str | None,
        Field(
            description=(
                "UID of the data supplier type this rule is connected to. "
                "A rule can only be connected to a single data supplier type. "
                "Omit to leave unchanged, pass an empty string to disconnect the "
                "current data supplier type."
            )
        ),
    ] = None
    change_description: Annotated[str, Field(min_length=1)]
