from typing import Annotated, Callable, Self

from pydantic import ConfigDict, Field, ValidationInfo, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.data_suppliers.data_supplier import DataSupplierAR
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    ObjectAction,
)
from clinical_mdr_api.models.concepts.concept import VersionProperties
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, InputModel
from common.config import settings


class DataSupplierTypeTerm(BaseModel):
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


class DataSupplierOriginSourceTerm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_origin_source.has_selected_term.uid",
                "nullable": True,
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_origin_source.has_selected_term.has_name_root.has_latest_value.name",
                "nullable": True,
            },
        ),
    ] = None


class DataSupplierOriginTypeTerm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_origin_type.has_selected_term.uid",
                "nullable": True,
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_origin_type.has_selected_term.has_name_root.has_latest_value.name",
                "nullable": True,
            },
        ),
    ] = None


class DataSupplier(VersionProperties):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None, Field(json_schema_extra={"source": "uid", "nullable": True})
    ] = None
    name: Annotated[
        str | None,
        Field(json_schema_extra={"source": "has_latest_value.name", "nullable": True}),
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
    order: Annotated[
        int | None,
        Field(json_schema_extra={"source": "has_latest_value.order", "nullable": True}),
    ] = None
    supplier_type: Annotated[DataSupplierTypeTerm, Field()]
    origin_source: Annotated[DataSupplierOriginSourceTerm | None, Field()] = None
    origin_type: Annotated[DataSupplierOriginTypeTerm | None, Field()] = None
    api_base_url: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.api_base_url",
                "nullable": True,
            }
        ),
    ] = None
    ui_base_url: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.ui_base_url",
                "nullable": True,
            }
        ),
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
                "Holds those actions that can be performed on the DataSuppliers. "
                "Actions are: 'approve', 'edit', 'new_version'."
            ),
        ),
    ]

    @classmethod
    def from_data_supplier_ar(
        cls,
        data_supplier_ar: DataSupplierAR,
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
    ) -> Self:
        supplier_type = find_term_by_uid(
            data_supplier_ar.data_supplier_vo.supplier_type_uid
        )
        origin_source = (
            find_term_by_uid(data_supplier_ar.data_supplier_vo.origin_source_uid)
            if data_supplier_ar.data_supplier_vo.origin_source_uid is not None
            else None
        )
        origin_type = (
            find_term_by_uid(data_supplier_ar.data_supplier_vo.origin_type_uid)
            if data_supplier_ar.data_supplier_vo.origin_type_uid is not None
            else None
        )

        return cls(
            uid=data_supplier_ar.uid,
            name=data_supplier_ar.name,
            order=data_supplier_ar.data_supplier_vo.order,
            api_base_url=data_supplier_ar.data_supplier_vo.api_base_url,
            ui_base_url=data_supplier_ar.data_supplier_vo.ui_base_url,
            description=data_supplier_ar.data_supplier_vo.description,
            supplier_type=(
                DataSupplierTypeTerm(uid=supplier_type.uid, name=supplier_type.name)
            ),
            origin_source=(
                DataSupplierOriginSourceTerm(
                    uid=origin_source.uid, name=origin_source.name
                )
                if origin_source
                else None
            ),
            origin_type=(
                DataSupplierOriginTypeTerm(uid=origin_type.uid, name=origin_type.name)
                if origin_type
                else None
            ),
            library_name=Library.from_library_vo(data_supplier_ar.library).name,
            start_date=data_supplier_ar.item_metadata.start_date,
            end_date=data_supplier_ar.item_metadata.end_date,
            status=data_supplier_ar.item_metadata.status.value,
            version=data_supplier_ar.item_metadata.version,
            change_description=data_supplier_ar.item_metadata.change_description,
            author_username=data_supplier_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in data_supplier_ar.get_possible_actions()]
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


class DataSupplierVersion(DataSupplier):
    """
    Class for storing DataSupplier and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)


class DataSupplierInput(InputModel):
    name: Annotated[str, Field(min_length=1)]
    order: Annotated[int | None, Field(gt=0, le=settings.max_int_neo4j)] = None
    supplier_type_uid: Annotated[str, Field(min_length=1)]
    description: Annotated[str | None, Field(min_length=1)]
    api_base_url: Annotated[str | None, Field(min_length=1)]
    ui_base_url: Annotated[str | None, Field(min_length=1)]
    origin_source_uid: Annotated[str | None, Field(min_length=1)]
    origin_type_uid: Annotated[str | None, Field(min_length=1)]
    library_name: Annotated[str, Field(min_length=1)] = settings.sponsor_library_name


class DataSupplierEditInput(InputModel):
    """Input model for PATCH endpoint - all fields optional except change_description."""

    name: Annotated[str | None, Field(min_length=1)] = None
    order: Annotated[int | None, Field(gt=0, le=settings.max_int_neo4j)] = None
    supplier_type_uid: Annotated[str | None, Field(min_length=1)] = None
    description: Annotated[str | None, Field(min_length=1)] = None
    api_base_url: Annotated[str | None, Field(min_length=1)] = None
    ui_base_url: Annotated[str | None, Field(min_length=1)] = None
    origin_source_uid: Annotated[str | None, Field(min_length=1)] = None
    origin_type_uid: Annotated[str | None, Field(min_length=1)] = None
    change_description: Annotated[str, Field(min_length=1)]
