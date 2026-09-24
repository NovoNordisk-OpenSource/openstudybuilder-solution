from typing import Annotated, Any, Self

from pydantic import Field, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.odms.method import OdmMethodAR
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmBaseModel,
    OdmFormalExpressionModel,
    OdmPatchInput,
    OdmPostInput,
    OdmTranslatedTextModel,
)
from clinical_mdr_api.models.utils import make_optional
from clinical_mdr_api.models.validators import (
    has_english_description,
    translated_text_uniqueness_check,
)


class OdmMethod(OdmBaseModel):
    oid: Annotated[str | None, Field()]
    method_type: Annotated[str | None, Field()]
    formal_expressions: Annotated[list[OdmFormalExpressionModel], Field()]
    translated_texts: Annotated[list[OdmTranslatedTextModel], Field()]
    aliases: Annotated[list[OdmAliasModel], Field()]
    possible_actions: Annotated[list[str], Field()]

    @classmethod
    def from_odm_method_ar(cls, odm_method_ar: OdmMethodAR) -> Self:
        return cls(
            uid=odm_method_ar._uid,
            oid=odm_method_ar.odm_vo.oid,
            name=odm_method_ar.name,
            method_type=odm_method_ar.odm_vo.method_type,
            library_name=odm_method_ar.library.name,
            start_date=odm_method_ar.item_metadata.start_date,
            end_date=odm_method_ar.item_metadata.end_date,
            status=odm_method_ar.item_metadata.status.value,
            version=odm_method_ar.item_metadata.version,
            change_description=odm_method_ar.item_metadata.change_description,
            author_username=odm_method_ar.item_metadata.author_username,
            formal_expressions=sorted(
                odm_method_ar.odm_vo.formal_expressions,
                key=lambda item: item.context,
            ),
            translated_texts=sorted(
                odm_method_ar.odm_vo.translated_texts,
                key=lambda item: (item.text_type.value, item.text),
            ),
            aliases=sorted(odm_method_ar.odm_vo.aliases, key=lambda item: item.name),
            possible_actions=sorted(
                [_.value for _ in odm_method_ar.get_possible_actions()]
            ),
        )


class OdmMethodPostInput(OdmPostInput):
    oid: Annotated[str | None, Field(min_length=1)] = None
    method_type: Annotated[str | None, Field(min_length=1)] = None
    formal_expressions: Annotated[list[OdmFormalExpressionModel], Field()]
    translated_texts: Annotated[list[OdmTranslatedTextModel], Field()]
    aliases: Annotated[list[OdmAliasModel], Field()] = Field(default_factory=list)

    _translated_text_uniqueness_check = field_validator("translated_texts")(
        translated_text_uniqueness_check
    )
    _english_description_validator = field_validator("translated_texts")(
        has_english_description
    )


@make_optional
class OdmMethodOptional(OdmMethod):
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(**data)


class OdmMethodPatchInput(OdmPatchInput):
    name: Annotated[str, Field(min_length=1)]
    oid: Annotated[str | None, Field(min_length=1)]
    method_type: Annotated[str | None, Field(min_length=1)]
    formal_expressions: Annotated[list[OdmFormalExpressionModel], Field()]
    translated_texts: Annotated[list[OdmTranslatedTextModel], Field()]
    aliases: Annotated[list[OdmAliasModel], Field()] = Field(default_factory=list)

    _translated_text_uniqueness_check = field_validator("translated_texts")(
        translated_text_uniqueness_check
    )
    _english_description_validator = field_validator("translated_texts")(
        has_english_description
    )


class OdmMethodVersion(OdmMethod):
    """
    Class for storing OdmMethod and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
