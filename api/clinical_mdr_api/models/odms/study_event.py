from datetime import date
from typing import Annotated, Any, Callable, Self

from pydantic import Field, StrictBool, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.odms.form import OdmFormRefVO
from clinical_mdr_api.domains.odms.study_event import OdmStudyEventAR
from clinical_mdr_api.models.odms.common_models import (
    OdmBaseModel,
    OdmPatchInput,
    OdmPostInput,
    deduplicate_and_keep_newest_version,
)
from clinical_mdr_api.models.odms.form import OdmFormRefModel
from clinical_mdr_api.models.utils import PostInputModel, make_optional
from clinical_mdr_api.models.validators import reject_non_string_datetime
from common.config import settings
from common.utils import booltostr


class OdmStudyEvent(OdmBaseModel):
    oid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    effective_date: Annotated[
        date | None, Field(json_schema_extra={"nullable": True})
    ] = None
    retired_date: Annotated[
        date | None, Field(json_schema_extra={"nullable": True})
    ] = None
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    display_in_tree: Annotated[bool, Field()] = True
    forms: Annotated[list[OdmFormRefModel], Field()]
    possible_actions: Annotated[list[str], Field()]

    @classmethod
    def from_odm_study_event_ar(
        cls,
        odm_study_event_ar: OdmStudyEventAR,
        find_odm_form_by_uid_with_study_event_relation: Callable[
            [str, str, str], OdmFormRefVO
        ],
    ) -> Self:
        return cls(
            uid=odm_study_event_ar._uid,
            name=odm_study_event_ar.name,
            oid=odm_study_event_ar.odm_vo.oid,
            effective_date=odm_study_event_ar.odm_vo.effective_date,
            retired_date=odm_study_event_ar.odm_vo.retired_date,
            description=odm_study_event_ar.odm_vo.description,
            display_in_tree=odm_study_event_ar.odm_vo.display_in_tree,
            library_name=odm_study_event_ar.library.name,
            start_date=odm_study_event_ar.item_metadata.start_date,
            end_date=odm_study_event_ar.item_metadata.end_date,
            status=odm_study_event_ar.item_metadata.status.value,
            version=odm_study_event_ar.item_metadata.version,
            change_description=odm_study_event_ar.item_metadata.change_description,
            author_username=odm_study_event_ar.item_metadata.author_username,
            forms=sorted(
                [
                    OdmFormRefModel.from_odm_form_uid(
                        uid=form_uid,
                        study_event_uid=odm_study_event_ar._uid,
                        study_event_version=odm_study_event_ar.item_metadata.version,
                        find_odm_form_by_uid_with_study_event_relation=find_odm_form_by_uid_with_study_event_relation,
                    )
                    for form_uid in odm_study_event_ar.odm_vo.form_uids
                ],
                key=lambda item: (item.order_number, item.name),
            ),
            possible_actions=sorted(
                [_.value for _ in odm_study_event_ar.get_possible_actions()]
            ),
        )


class OdmStudyEventPostInput(OdmPostInput):
    oid: Annotated[str | None, Field(min_length=1)] = None
    effective_date: Annotated[date | None, Field()] = None
    retired_date: Annotated[date | None, Field()] = None
    description: Annotated[str | None, Field(min_length=1)] = None
    display_in_tree: Annotated[StrictBool, Field()] = True

    _reject_non_string_date = field_validator(
        "effective_date", "retired_date", mode="before"
    )(reject_non_string_datetime)


class OdmStudyEventPatchInput(OdmPatchInput):
    name: Annotated[str, Field(min_length=1)]
    oid: Annotated[str | None, Field(min_length=1)]
    effective_date: Annotated[date | None, Field()]
    retired_date: Annotated[date | None, Field()]
    description: Annotated[str | None, Field(min_length=1)] = None
    display_in_tree: Annotated[StrictBool, Field()] = True

    _reject_non_string_date = field_validator(
        "effective_date", "retired_date", mode="before"
    )(reject_non_string_datetime)


@make_optional
class OdmStudyEventOptional(OdmStudyEvent):
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        if data.get("forms") is not None:
            data["forms"] = deduplicate_and_keep_newest_version(data.get("forms", []))

            for form in data["forms"]:
                if "order_number" in form:
                    form["order_number"] = form.pop("order_number")
                if form.get("mandatory") is not None and isinstance(
                    form["mandatory"], bool
                ):
                    form["mandatory"] = booltostr(form["mandatory"])
                if form.get("locked") is not None and isinstance(form["locked"], bool):
                    form["locked"] = booltostr(form["locked"])

        return cls(**data)


class OdmStudyEventFormPostInput(PostInputModel):
    uid: Annotated[str, Field(min_length=1)]
    order_number: Annotated[int, Field(lt=settings.max_int_neo4j)]
    mandatory: Annotated[str, Field(min_length=1)]
    locked: Annotated[str, Field(min_length=1)] = "No"
    collection_exception_condition_oid: Annotated[str | None, Field()] = None


class OdmStudyEventVersion(OdmStudyEvent):
    """
    Class for storing OdmStudyEvents and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
