from typing import Annotated, Callable, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.concepts.odms.alias import OdmAliasAR
from clinical_mdr_api.models.concepts.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.utils import BaseModel, BatchInputModel


class OdmAlias(ConceptModel):
    context: str
    possible_actions: list[str]

    @classmethod
    def from_odm_alias_ar(cls, odm_alias_ar: OdmAliasAR) -> Self:
        return cls(
            uid=odm_alias_ar._uid,
            name=odm_alias_ar.name,
            context=odm_alias_ar.concept_vo.context,
            library_name=odm_alias_ar.library.name,
            start_date=odm_alias_ar.item_metadata.start_date,
            end_date=odm_alias_ar.item_metadata.end_date,
            status=odm_alias_ar.item_metadata.status.value,
            version=odm_alias_ar.item_metadata.version,
            change_description=odm_alias_ar.item_metadata.change_description,
            author_username=odm_alias_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in odm_alias_ar.get_possible_actions()]
            ),
        )


class OdmAliasSimpleModel(BaseModel):
    @classmethod
    def from_odm_alias_uid(
        cls, uid: str, find_odm_alias_by_uid: Callable[[str], ConceptARBase | None]
    ) -> Self | None:
        if uid is not None:
            odm_alias = find_odm_alias_by_uid(uid)

            if odm_alias is not None:
                simple_odm_alias_model = cls(
                    uid=uid,
                    name=odm_alias.concept_vo.name,
                    context=odm_alias.concept_vo.context,
                    version=odm_alias.item_metadata.version,
                )
            else:
                simple_odm_alias_model = cls(
                    uid=uid, name=None, context=None, version=None
                )
        else:
            simple_odm_alias_model = None
        return simple_odm_alias_model

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    context: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class OdmAliasPostInput(ConceptPostInput):
    context: Annotated[str, Field(min_length=1)]


class OdmAliasPatchInput(ConceptPatchInput):
    context: Annotated[str | None, Field(min_length=1)]


class OdmAliasBatchPatchInput(ConceptPatchInput):
    uid: Annotated[str, Field(min_length=1)]
    context: Annotated[str | None, Field(min_length=1)]


class OdmAliasBatchInput(BatchInputModel):
    method: Annotated[
        str,
        Field(description="HTTP method corresponding to operation type", min_length=1),
    ]
    content: OdmAliasBatchPatchInput | OdmAliasPostInput


class OdmAliasBatchOutput(BaseModel):
    response_code: Annotated[
        int, Field(description="The HTTP response code related to input operation")
    ]
    content: OdmAlias | None | BatchErrorResponse


class OdmAliasVersion(OdmAlias):
    """
    Class for storing OdmAlias and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []
