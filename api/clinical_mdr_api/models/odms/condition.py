from typing import Annotated, Any, Self

from pydantic import Field, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.odms.condition import OdmConditionAR
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


class OdmCondition(OdmBaseModel):
    oid: Annotated[str | None, Field()]
    formal_expressions: Annotated[list[OdmFormalExpressionModel], Field()]
    translated_texts: Annotated[list[OdmTranslatedTextModel], Field()]
    aliases: Annotated[list[OdmAliasModel], Field()]
    possible_actions: Annotated[list[str], Field()]

    @classmethod
    def from_odm_condition_ar(cls, odm_condition_ar: OdmConditionAR) -> Self:
        return cls(
            uid=odm_condition_ar._uid,
            oid=odm_condition_ar.odm_vo.oid,
            name=odm_condition_ar.name,
            library_name=odm_condition_ar.library.name,
            start_date=odm_condition_ar.item_metadata.start_date,
            end_date=odm_condition_ar.item_metadata.end_date,
            status=odm_condition_ar.item_metadata.status.value,
            version=odm_condition_ar.item_metadata.version,
            change_description=odm_condition_ar.item_metadata.change_description,
            author_username=odm_condition_ar.item_metadata.author_username,
            formal_expressions=sorted(
                odm_condition_ar.odm_vo.formal_expressions,
                key=lambda item: item.context,
            ),
            translated_texts=sorted(
                odm_condition_ar.odm_vo.translated_texts,
                key=lambda item: (item.text_type.value, item.text),
            ),
            aliases=sorted(odm_condition_ar.odm_vo.aliases, key=lambda item: item.name),
            possible_actions=sorted(
                [_.value for _ in odm_condition_ar.get_possible_actions()]
            ),
        )


class OdmConditionPostInput(OdmPostInput):
    oid: Annotated[str | None, Field(min_length=1)] = None
    formal_expressions: Annotated[list[OdmFormalExpressionModel], Field()]
    translated_texts: Annotated[list[OdmTranslatedTextModel], Field()]
    aliases: Annotated[list[OdmAliasModel], Field()]

    _translated_text_uniqueness_check = field_validator("translated_texts")(
        translated_text_uniqueness_check
    )
    _english_description_validator = field_validator("translated_texts")(
        has_english_description
    )


class OdmConditionPatchInput(OdmPatchInput):
    name: Annotated[str, Field(min_length=1)]
    oid: Annotated[str | None, Field(min_length=1)]
    formal_expressions: Annotated[list[OdmFormalExpressionModel], Field()]
    translated_texts: Annotated[list[OdmTranslatedTextModel], Field()]
    aliases: Annotated[list[OdmAliasModel], Field()]

    _translated_text_uniqueness_check = field_validator("translated_texts")(
        translated_text_uniqueness_check
    )
    _english_description_validator = field_validator("translated_texts")(
        has_english_description
    )


@make_optional
class OdmConditionOptional(OdmCondition):
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(**data)


class OdmConditionVersion(OdmCondition):
    """
    Class for storing OdmCondition and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
