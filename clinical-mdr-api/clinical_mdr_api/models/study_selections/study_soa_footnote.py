from datetime import datetime
from typing import Annotated, Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.study_selections.study_soa_footnote import (
    StudySoAFootnoteVO,
    StudySoAFootnoteVOHistory,
)
from clinical_mdr_api.domains.syntax_instances.footnote import FootnoteAR
from clinical_mdr_api.domains.syntax_templates.footnote_template import (
    FootnoteTemplateAR,
)
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.study_selection import (
    RESPONSE_CODE_FIELD,
    ReferencedItem,
)
from clinical_mdr_api.models.syntax_instances.footnote import (
    Footnote,
    FootnoteCreateInput,
)
from clinical_mdr_api.models.syntax_templates.footnote_template import FootnoteTemplate
from clinical_mdr_api.models.utils import (
    BaseModel,
    PatchInputModel,
    PostInputModel,
    get_latest_on_datetime_str,
)


class StudySoAFootnote(BaseModel):
    uid: Annotated[str, Field()]
    study_uid: Annotated[str, Field()]
    study_version: Annotated[
        str | None,
        Field(
            title="study version or date information",
            description="Study version number, if specified, otherwise None.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    order: Annotated[int, Field()]
    modified: Annotated[
        datetime | None,
        Field(
            json_schema_extra={"nullable": True},
            description="The most recent point in time when the study soa footnote was edited."
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        ),
    ] = None
    referenced_items: Annotated[list[ReferencedItem], Field()] = []
    footnote: Annotated[
        Footnote | None, Field(json_schema_extra={"nullable": True})
    ] = None
    template: Annotated[
        FootnoteTemplate | None, Field(json_schema_extra={"nullable": True})
    ] = None
    accepted_version: Annotated[
        bool | None,
        Field(
            description="Denotes if user accepted obsolete objective versions",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    latest_footnote: Annotated[
        Footnote | None,
        Field(
            description="Latest version of footnote selected for study selection.",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    @classmethod
    def from_study_soa_footnote_vo(
        cls,
        study_soa_footnote_vo: StudySoAFootnoteVO,
        find_footnote_by_uid: Callable[[str], FootnoteAR | None],
        find_footnote_template_by_uid: Callable[[str], FootnoteTemplateAR | None],
        study_value_version: str | None = None,
    ) -> Self:
        footnote = None
        latest_footnote = None
        footnote_template = None
        if study_soa_footnote_vo.footnote_uid:
            latest_footnote = Footnote.from_footnote_ar(
                find_footnote_by_uid(study_soa_footnote_vo.footnote_uid)
            )
            if study_soa_footnote_vo.footnote_version:
                if latest_footnote.version == study_soa_footnote_vo.footnote_version:
                    footnote = latest_footnote
                    latest_footnote = None
                else:
                    footnote = Footnote.from_footnote_ar(
                        find_footnote_by_uid(
                            study_soa_footnote_vo.footnote_uid,
                            version=study_soa_footnote_vo.footnote_version,
                        )
                    )
            else:
                footnote = Footnote.from_footnote_ar(
                    find_footnote_by_uid(
                        study_soa_footnote_vo.footnote_uid,
                    )
                )
        elif study_soa_footnote_vo.footnote_template_uid:
            footnote_template = FootnoteTemplate.from_footnote_template_ar(
                find_footnote_template_by_uid(
                    study_soa_footnote_vo.footnote_template_uid,
                    version=study_soa_footnote_vo.footnote_template_version,
                )
                if study_soa_footnote_vo.footnote_template_version
                else find_footnote_template_by_uid(
                    study_soa_footnote_vo.footnote_template_uid
                )
            )
        return cls(
            uid=study_soa_footnote_vo.uid,
            study_uid=study_soa_footnote_vo.study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            order=study_soa_footnote_vo.footnote_number,
            referenced_items=[
                ReferencedItem(
                    item_uid=ref_item.item_uid,
                    item_name=ref_item.item_name,
                    item_type=ref_item.item_type,
                )
                for ref_item in study_soa_footnote_vo.referenced_items
            ],
            footnote=footnote,
            latest_footnote=latest_footnote,
            template=footnote_template,
            modified=study_soa_footnote_vo.modified,
            accepted_version=study_soa_footnote_vo.accepted_version,
        )


class StudySoAFootnoteCreateInput(PostInputModel):
    footnote_uid: Annotated[str | None, Field()] = None
    footnote_template_uid: Annotated[str | None, Field()] = None
    referenced_items: Annotated[
        list[ReferencedItem],
        Field(title="The list of items referenced by a single footnote"),
    ] = []


class StudySoAFootnoteCreateFootnoteInput(PostInputModel):
    footnote_data: Annotated[
        FootnoteCreateInput,
        Field(description="Footnote data to create new footnote"),
    ]
    referenced_items: Annotated[
        list[ReferencedItem],
        Field(title="The list of items referenced by a single footnote"),
    ] = []


class StudySoAFootnoteEditInput(PatchInputModel):
    footnote_uid: Annotated[str | None, Field()] = None
    footnote_template_uid: Annotated[str | None, Field()] = None
    referenced_items: Annotated[
        list[ReferencedItem] | None,
        Field(title="The list of items referenced by a single footnote"),
    ] = None


class StudySoAFootnoteHistory(StudySoAFootnote):
    change_type: Annotated[
        str,
        Field(
            description="type of action",
        ),
    ]
    start_date: Annotated[datetime, Field()]
    end_date: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_study_soa_footnote_vo_history(
        cls,
        study_soa_footnote_vo: StudySoAFootnoteVOHistory,
        find_footnote_by_uid: Callable[[str], FootnoteAR | None],
        find_footnote_template_by_uid: Callable[[str], FootnoteTemplateAR | None],
    ) -> Self:
        footnote = None
        footnote_template = None
        if study_soa_footnote_vo.footnote_uid:
            footnote = Footnote.from_footnote_ar(
                find_footnote_by_uid(study_soa_footnote_vo.footnote_uid)
            )
        elif study_soa_footnote_vo.footnote_template_uid:
            footnote_template = FootnoteTemplate.from_footnote_template_ar(
                find_footnote_template_by_uid(
                    study_soa_footnote_vo.footnote_template_uid
                )
            )
        return cls(
            uid=study_soa_footnote_vo.uid,
            study_uid=study_soa_footnote_vo.study_uid,
            order=study_soa_footnote_vo.footnote_number,
            referenced_items=[
                ReferencedItem(
                    item_uid=ref_item.item_uid,
                    item_name=ref_item.item_name,
                    item_type=ref_item.item_type,
                )
                for ref_item in study_soa_footnote_vo.referenced_items
            ],
            footnote=footnote,
            template=footnote_template,
            start_date=study_soa_footnote_vo.start_date,
            end_date=study_soa_footnote_vo.end_date,
            change_type=study_soa_footnote_vo.change_type,
        )


class StudySoAFootnoteVersion(StudySoAFootnoteHistory):
    changes: list[str]


class StudySoAFootnoteBatchEditInput(StudySoAFootnoteEditInput):
    study_soa_footnote_uid: str


class StudySoAFootnoteBatchOutput(BaseModel):
    response_code: int = RESPONSE_CODE_FIELD
    content: StudySoAFootnote | None | BatchErrorResponse
