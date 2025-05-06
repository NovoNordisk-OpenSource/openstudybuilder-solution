from datetime import date
from typing import Annotated, Callable, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.odms.form import OdmFormRefVO
from clinical_mdr_api.domains.concepts.odms.study_event import OdmStudyEventAR
from clinical_mdr_api.models.concepts.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_form import OdmFormRefModel
from clinical_mdr_api.models.utils import PostInputModel
from common import config


class OdmStudyEvent(ConceptModel):
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
    display_in_tree: bool = True
    forms: list[OdmFormRefModel]
    possible_actions: list[str]

    @classmethod
    def from_odm_study_event_ar(
        cls,
        odm_study_event_ar: OdmStudyEventAR,
        find_odm_form_by_uid_with_study_event_relation: Callable[
            [str, str], OdmFormRefVO | None
        ],
    ) -> Self:
        return cls(
            uid=odm_study_event_ar._uid,
            name=odm_study_event_ar.concept_vo.name,
            oid=odm_study_event_ar.concept_vo.oid,
            effective_date=odm_study_event_ar.concept_vo.effective_date,
            retired_date=odm_study_event_ar.concept_vo.retired_date,
            description=odm_study_event_ar.concept_vo.description,
            display_in_tree=odm_study_event_ar.concept_vo.display_in_tree,
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
                        find_odm_form_by_uid_with_study_event_relation=find_odm_form_by_uid_with_study_event_relation,
                    )
                    for form_uid in odm_study_event_ar.concept_vo.form_uids
                ],
                key=lambda item: (item.order_number, item.name),
            ),
            possible_actions=sorted(
                [_.value for _ in odm_study_event_ar.get_possible_actions()]
            ),
        )


class OdmStudyEventPostInput(ConceptPostInput):
    oid: Annotated[str | None, Field(min_length=1)] = None
    effective_date: date | None = None
    retired_date: date | None = None
    description: Annotated[str | None, Field(min_length=1)] = None
    display_in_tree: bool = True


class OdmStudyEventPatchInput(ConceptPatchInput):
    oid: Annotated[str | None, Field(min_length=1)]
    effective_date: date | None
    retired_date: date | None
    description: Annotated[str | None, Field(min_length=1)] = None
    display_in_tree: bool = True


class OdmStudyEventFormPostInput(PostInputModel):
    uid: Annotated[str, Field(min_length=1)]
    order_number: Annotated[int, Field(lt=config.MAX_INT_NEO4J)]
    mandatory: Annotated[str, Field(min_length=1)]
    locked: Annotated[str, Field(min_length=1)] = "No"
    collection_exception_condition_oid: Annotated[str | None, Field(min_length=1)] = (
        None
    )


class OdmStudyEventVersion(OdmStudyEvent):
    """
    Class for storing OdmStudyEvents and calculation of differences
    """

    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []
