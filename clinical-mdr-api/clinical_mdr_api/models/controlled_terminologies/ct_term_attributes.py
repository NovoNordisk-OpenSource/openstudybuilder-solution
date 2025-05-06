from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_codelist import (
    CTTermCodelist,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel


class CTTermAttributes(BaseModel):
    @classmethod
    def from_ct_term_ar(cls, ct_term_attributes_ar: CTTermAttributesAR) -> Self:
        return cls(
            term_uid=ct_term_attributes_ar.uid,
            catalogue_name=ct_term_attributes_ar.ct_term_vo.catalogue_name,
            codelists=[
                CTTermCodelist(
                    codelist_uid=x.codelist_uid,
                    order=x.order,
                    library_name=x.library_name,
                )
                for x in ct_term_attributes_ar.ct_term_vo.codelists
            ],
            concept_id=ct_term_attributes_ar.ct_term_vo.concept_id,
            code_submission_value=ct_term_attributes_ar.ct_term_vo.code_submission_value,
            name_submission_value=ct_term_attributes_ar.ct_term_vo.name_submission_value,
            nci_preferred_name=ct_term_attributes_ar.ct_term_vo.preferred_term,
            definition=ct_term_attributes_ar.ct_term_vo.definition,
            library_name=Library.from_library_vo(ct_term_attributes_ar.library).name,
            possible_actions=sorted(
                [_.value for _ in ct_term_attributes_ar.get_possible_actions()]
            ),
            start_date=ct_term_attributes_ar.item_metadata.start_date,
            end_date=ct_term_attributes_ar.item_metadata.end_date,
            status=ct_term_attributes_ar.item_metadata.status.value,
            version=ct_term_attributes_ar.item_metadata.version,
            change_description=ct_term_attributes_ar.item_metadata.change_description,
            author_username=ct_term_attributes_ar.item_metadata.author_username,
        )

    @classmethod
    def from_ct_term_ar_without_common_term_fields(
        cls, ct_term_attributes_ar: CTTermAttributesAR
    ) -> Self:
        return cls(
            concept_id=ct_term_attributes_ar.ct_term_vo.concept_id,
            code_submission_value=ct_term_attributes_ar.ct_term_vo.code_submission_value,
            name_submission_value=ct_term_attributes_ar.ct_term_vo.name_submission_value,
            nci_preferred_name=ct_term_attributes_ar.ct_term_vo.preferred_term,
            definition=ct_term_attributes_ar.ct_term_vo.definition,
            possible_actions=sorted(
                [_.value for _ in ct_term_attributes_ar.get_possible_actions()]
            ),
            start_date=ct_term_attributes_ar.item_metadata.start_date,
            end_date=ct_term_attributes_ar.item_metadata.end_date,
            status=ct_term_attributes_ar.item_metadata.status.value,
            version=ct_term_attributes_ar.item_metadata.version,
            change_description=ct_term_attributes_ar.item_metadata.change_description,
            author_username=ct_term_attributes_ar.item_metadata.author_username,
        )

    term_uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None

    catalogue_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    codelists: Annotated[list[CTTermCodelist], Field()] = []

    concept_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )

    code_submission_value: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    name_submission_value: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    nci_preferred_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    definition: Annotated[str, Field(json_schema_extra={"remove_from_wildcard": True})]

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
                "Holds those actions that can be performed on the CTTermAttributes. "
                "Actions are: 'approve', 'edit', 'new_version'."
            )
        ),
    ] = []


class CTTermAttributesVersion(CTTermAttributes):
    """
    Class for storing CTTermAttributes and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []


class CTTermAttributesEditInput(PatchInputModel):
    code_submission_value: Annotated[str | None, Field(min_length=1)] = None
    name_submission_value: Annotated[str | None, Field(min_length=1)] = None
    nci_preferred_name: Annotated[str | None, Field(min_length=1)] = None
    definition: Annotated[str | None, Field()] = None
    change_description: Annotated[str | None, Field(min_length=1)] = None
