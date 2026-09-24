from datetime import datetime
from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.domains.study_selections.study_soa_footnote import (
    StudySoAFootnoteVO,
    StudySoAFootnoteVOHistory,
)
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.study_selection import (
    RESPONSE_CODE_FIELD,
    ReferencedItem,
)
from clinical_mdr_api.models.syntax_instances.footnote import FootnoteCreateInput
from clinical_mdr_api.models.utils import (
    BaseModel,
    PatchInputModel,
    PostInputModel,
    get_latest_on_datetime_str,
)


class CompactFootnote(BaseModel):
    uid: Annotated[str, Field()]
    name_plain: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    library_name: Annotated[str | None, Field()] = None
    status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    template_uid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    template_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def footnote_from_study_soa_footnote_vo(
        cls, study_soa_footnote_vo: StudySoAFootnoteVO
    ) -> Self:
        return cls(
            uid=study_soa_footnote_vo.footnote_uid or "",
            name=study_soa_footnote_vo.footnote_name,
            name_plain=study_soa_footnote_vo.footnote_name_plain,
            version=study_soa_footnote_vo.footnote_version,
            library_name=study_soa_footnote_vo.footnote_library_name,
            status=study_soa_footnote_vo.footnote_status,
            template_uid=study_soa_footnote_vo.footnote_template_uid,
            template_name=study_soa_footnote_vo.footnote_template_name,
        )

    @classmethod
    def minimal_response_footnote_from_study_soa_footnote_vo(
        cls, study_soa_footnote_vo: StudySoAFootnoteVO
    ) -> Self:
        return cls(
            uid=study_soa_footnote_vo.footnote_uid or "",
            name=study_soa_footnote_vo.footnote_name,
            name_plain=study_soa_footnote_vo.footnote_name_plain,
        )

    @classmethod
    def latest_footnote_from_study_soa_footnote_vo(
        cls,
        study_soa_footnote_vo: StudySoAFootnoteVO,
    ) -> Self:
        return cls(
            uid=study_soa_footnote_vo.footnote_uid or "",
            name_plain=study_soa_footnote_vo.latest_footnote_name_plain,
            name=None,
            status=None,
            version=study_soa_footnote_vo.latest_footnote_version,
            library_name=study_soa_footnote_vo.footnote_library_name,
            template_uid=study_soa_footnote_vo.footnote_template_uid,
            template_name=None,
        )

    @classmethod
    def footnote_from_study_soa_footnote_history_vo(
        cls,
        study_soa_footnote_vo: StudySoAFootnoteVOHistory,
    ) -> Self:
        return cls(
            uid=study_soa_footnote_vo.footnote_uid or "",
            name_plain=study_soa_footnote_vo.footnote_name_plain,
            version=study_soa_footnote_vo.footnote_version,
            template_uid=study_soa_footnote_vo.footnote_template_uid,
        )


class CompactFootnoteTemplate(BaseModel):
    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    name_plain: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    library_name: Annotated[str | None, Field()] = None
    parameters: Annotated[list[str] | None, Field()] = None

    @classmethod
    def footnote_template_from_study_soa_footnote_vo(
        cls, study_soa_footnote_vo: StudySoAFootnoteVO
    ) -> Self:
        return cls(
            uid=study_soa_footnote_vo.footnote_template_uid or "",
            name=study_soa_footnote_vo.footnote_template_name,
            name_plain=study_soa_footnote_vo.footnote_template_name_plain,
            version=study_soa_footnote_vo.footnote_template_version,
            library_name=study_soa_footnote_vo.footnote_template_library_name,
            parameters=study_soa_footnote_vo.footnote_template_parameters,
        )

    @classmethod
    def minimal_response_footnote_template_from_study_soa_footnote_vo(
        cls, study_soa_footnote_vo: StudySoAFootnoteVO
    ) -> Self:
        return cls(
            uid=study_soa_footnote_vo.footnote_template_uid or "",
            name=study_soa_footnote_vo.footnote_template_name,
            name_plain=study_soa_footnote_vo.footnote_template_name_plain,
        )

    @classmethod
    def footnote_template_from_study_soa_footnote_history_vo(
        cls,
        study_soa_footnote_vo: StudySoAFootnoteVOHistory,
    ) -> Self:
        return cls(
            uid=study_soa_footnote_vo.footnote_template_uid or "",
            name_plain=study_soa_footnote_vo.footnote_template_name_plain,
            version=study_soa_footnote_vo.footnote_template_version,
        )


class StudySoAFootnote(BaseModel):
    uid: Annotated[str, Field()]
    study_uid: Annotated[str, Field()]
    study_version: Annotated[
        str | None,
        Field(
            description="Study version number, if specified, otherwise None.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    modified: Annotated[
        datetime | None,
        Field(
            json_schema_extra={"nullable": True},
            description="The most recent point in time when the study soa footnote was edited."
            "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        ),
    ] = None
    referenced_items: list[ReferencedItem] = Field(default_factory=list)
    footnote: Annotated[
        CompactFootnote | None, Field(json_schema_extra={"nullable": True})
    ] = None
    template: Annotated[
        CompactFootnoteTemplate | None, Field(json_schema_extra={"nullable": True})
    ] = None
    accepted_version: Annotated[
        bool | None,
        Field(
            description="Denotes if user accepted obsolete objective versions",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    latest_footnote: Annotated[
        CompactFootnote | None,
        Field(
            description="Latest version of footnote selected for study selection.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_study_soa_footnote_vo(
        cls,
        study_soa_footnote_vo: StudySoAFootnoteVO,
        study_value_version: str | None = None,
        order: int | None = None,
    ) -> Self:
        return cls(
            uid=study_soa_footnote_vo.uid,
            study_uid=study_soa_footnote_vo.study_uid,
            study_version=(
                study_value_version
                if study_value_version
                else get_latest_on_datetime_str()
            ),
            order=order,
            referenced_items=[
                ReferencedItem(
                    item_uid=ref_item.item_uid,
                    item_name=ref_item.item_name,
                    item_type=ref_item.item_type,
                    visible_in_protocol_soa=ref_item.visible_in_protocol_soa,
                )
                for ref_item in study_soa_footnote_vo.referenced_items
            ],
            footnote=(
                CompactFootnote.footnote_from_study_soa_footnote_vo(
                    study_soa_footnote_vo=study_soa_footnote_vo,
                )
                if study_soa_footnote_vo.footnote_uid
                else None
            ),
            latest_footnote=(
                CompactFootnote.latest_footnote_from_study_soa_footnote_vo(
                    study_soa_footnote_vo=study_soa_footnote_vo
                )
                if study_soa_footnote_vo.footnote_version
                != study_soa_footnote_vo.latest_footnote_version
                else None
            ),
            template=(
                CompactFootnoteTemplate.footnote_template_from_study_soa_footnote_vo(
                    study_soa_footnote_vo=study_soa_footnote_vo,
                )
                if not study_soa_footnote_vo.footnote_uid
                else None
            ),
            modified=study_soa_footnote_vo.modified,
            accepted_version=study_soa_footnote_vo.accepted_version,
            author_username=study_soa_footnote_vo.author_username,
        )

    @classmethod
    def minimal_response_from_study_soa_footnote_vo(
        cls,
        study_soa_footnote_vo: StudySoAFootnoteVO,
        order: int | None = None,
    ) -> Self:
        return cls(
            uid=study_soa_footnote_vo.uid,
            study_uid=study_soa_footnote_vo.study_uid,
            order=order,
            referenced_items=[
                ReferencedItem(
                    item_uid=ref_item.item_uid,
                    item_type=ref_item.item_type,
                )
                for ref_item in study_soa_footnote_vo.referenced_items
            ],
            footnote=(
                CompactFootnote.minimal_response_footnote_from_study_soa_footnote_vo(
                    study_soa_footnote_vo=study_soa_footnote_vo,
                )
                if study_soa_footnote_vo.footnote_uid
                else None
            ),
            template=(
                CompactFootnoteTemplate.minimal_response_footnote_template_from_study_soa_footnote_vo(
                    study_soa_footnote_vo=study_soa_footnote_vo,
                )
                if not study_soa_footnote_vo.footnote_uid
                else None
            ),
        )


class StudySoAFootnoteCreateInput(PostInputModel):
    footnote_uid: Annotated[str | None, Field()] = None
    footnote_template_uid: Annotated[str | None, Field()] = None
    referenced_items: list[ReferencedItem] = Field(
        description="The list of items referenced by a single footnote",
        default_factory=list,
    )


class StudySoAFootnoteCreateFootnoteInput(PostInputModel):
    footnote_data: Annotated[
        FootnoteCreateInput,
        Field(description="Footnote data to create new footnote"),
    ]
    referenced_items: list[ReferencedItem] = Field(
        description="The list of items referenced by a single footnote",
        default_factory=list,
    )


class StudySoAFootnoteEditInput(PatchInputModel):
    footnote_uid: Annotated[str | None, Field()] = None
    footnote_template_uid: Annotated[str | None, Field()] = None
    referenced_items: Annotated[
        list[ReferencedItem] | None,
        Field(description="The list of items referenced by a single footnote"),
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
    ) -> Self:
        return cls(
            uid=study_soa_footnote_vo.uid,
            study_uid=study_soa_footnote_vo.study_uid,
            referenced_items=[
                ReferencedItem(
                    item_uid=ref_item.item_uid,
                    item_name=ref_item.item_name,
                    item_type=ref_item.item_type,
                )
                for ref_item in study_soa_footnote_vo.referenced_items
            ],
            footnote=(
                CompactFootnote.footnote_from_study_soa_footnote_history_vo(
                    study_soa_footnote_vo=study_soa_footnote_vo
                )
                if study_soa_footnote_vo.footnote_uid
                else None
            ),
            template=(
                CompactFootnoteTemplate.footnote_template_from_study_soa_footnote_history_vo(
                    study_soa_footnote_vo=study_soa_footnote_vo
                )
                if not study_soa_footnote_vo.footnote_uid
                else None
            ),
            start_date=study_soa_footnote_vo.start_date,
            end_date=study_soa_footnote_vo.end_date,
            change_type=study_soa_footnote_vo.change_type,
            author_username=study_soa_footnote_vo.author_username,
        )


class StudySoAFootnoteVersion(StudySoAFootnoteHistory):
    changes: Annotated[list[str], Field()]


class StudySoAFootnoteBatchEditInput(StudySoAFootnoteEditInput):
    study_soa_footnote_uid: Annotated[str, Field()]


class StudySoAFootnoteBatchOutput(BaseModel):
    response_code: Annotated[int, Field()] = RESPONSE_CODE_FIELD
    content: Annotated[StudySoAFootnote | None | BatchErrorResponse, Field()]
