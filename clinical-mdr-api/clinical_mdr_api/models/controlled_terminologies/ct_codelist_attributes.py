from datetime import datetime
from typing import Annotated, Callable, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel


class CTCodelistAttributes(BaseModel):
    @classmethod
    def from_ct_codelist_ar(cls, ct_codelist_ar: CTCodelistAttributesAR) -> Self:
        return cls(
            catalogue_name=ct_codelist_ar.ct_codelist_vo.catalogue_name,
            codelist_uid=ct_codelist_ar.uid,
            parent_codelist_uid=ct_codelist_ar.ct_codelist_vo.parent_codelist_uid,
            child_codelist_uids=ct_codelist_ar.ct_codelist_vo.child_codelist_uids,
            name=ct_codelist_ar.name,
            submission_value=ct_codelist_ar.ct_codelist_vo.submission_value,
            nci_preferred_name=ct_codelist_ar.ct_codelist_vo.preferred_term,
            definition=ct_codelist_ar.ct_codelist_vo.definition,
            extensible=ct_codelist_ar.ct_codelist_vo.extensible,
            library_name=Library.from_library_vo(ct_codelist_ar.library).name,
            start_date=ct_codelist_ar.item_metadata.start_date,
            end_date=ct_codelist_ar.item_metadata.end_date,
            status=ct_codelist_ar.item_metadata.status.value,
            version=ct_codelist_ar.item_metadata.version,
            change_description=ct_codelist_ar.item_metadata.change_description,
            author_username=ct_codelist_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in ct_codelist_ar.get_possible_actions()]
            ),
        )

    @classmethod
    def from_ct_codelist_ar_without_common_codelist_fields(
        cls, ct_codelist_ar: CTCodelistAttributesAR
    ) -> Self:
        return cls(
            name=ct_codelist_ar.name,
            submission_value=ct_codelist_ar.ct_codelist_vo.submission_value,
            nci_preferred_name=ct_codelist_ar.ct_codelist_vo.preferred_term,
            definition=ct_codelist_ar.ct_codelist_vo.definition,
            extensible=ct_codelist_ar.ct_codelist_vo.extensible,
            start_date=ct_codelist_ar.item_metadata.start_date,
            end_date=ct_codelist_ar.item_metadata.end_date,
            status=ct_codelist_ar.item_metadata.status.value,
            version=ct_codelist_ar.item_metadata.version,
            change_description=ct_codelist_ar.item_metadata.change_description,
            author_username=ct_codelist_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in ct_codelist_ar.get_possible_actions()]
            ),
        )

    catalogue_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    codelist_uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )

    parent_codelist_uid: Annotated[
        str | None,
        Field(json_schema_extra={"nullable": True, "remove_from_wildcard": True}),
    ] = None

    child_codelist_uids: Annotated[
        list[str], Field(json_schema_extra={"remove_from_wildcard": True})
    ] = []

    name: Annotated[str, Field()]

    submission_value: Annotated[str, Field()]

    nci_preferred_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    definition: Annotated[str, Field()]

    extensible: Annotated[bool, Field()]

    library_name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    start_date: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    end_date: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    change_description: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    possible_actions: Annotated[
        list[str],
        Field(
            description=(
                "Holds those actions that can be performed on the CTCodelistAttributes. "
                "Actions are: 'approve', 'edit', 'new_version'."
            ),
        ),
    ] = []


class CTCodelistAttributesSimpleModel(BaseModel):
    @classmethod
    def from_codelist_uid(
        cls,
        uid: str,
        find_codelist_attribute_by_codelist_uid: Callable[
            [str], CTCodelistAttributesAR | None
        ],
    ) -> Self | None:
        if uid is not None:
            codelist_attribute = find_codelist_attribute_by_codelist_uid(uid)

            if codelist_attribute is not None:
                simple_codelist_attribute_model = cls(
                    uid=uid,
                    name=codelist_attribute._ct_codelist_attributes_vo.name,
                    submission_value=codelist_attribute._ct_codelist_attributes_vo.submission_value,
                    preferred_term=codelist_attribute._ct_codelist_attributes_vo.preferred_term,
                )
            else:
                simple_codelist_attribute_model = cls(
                    uid=uid,
                    name=None,
                    submission_value=None,
                    preferred_term=None,
                )
        else:
            simple_codelist_attribute_model = None
        return simple_codelist_attribute_model

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    submission_value: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    preferred_term: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class CTCodelistAttributesVersion(CTCodelistAttributes):
    """
    Class for storing CTCodelistAttributes and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []


class CTCodelistAttributesEditInput(PatchInputModel):
    name: Annotated[str | None, Field(min_length=1)] = None
    submission_value: Annotated[str | None, Field(min_length=1)] = None
    nci_preferred_name: Annotated[str | None, Field(min_length=1)] = None
    definition: Annotated[str | None, Field(min_length=1)] = None
    extensible: bool | None = None
    change_description: Annotated[str | None, Field(min_length=1)] = None
