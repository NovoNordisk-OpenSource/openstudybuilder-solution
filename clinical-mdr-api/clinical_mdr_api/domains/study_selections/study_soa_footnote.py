from dataclasses import dataclass, replace
from datetime import datetime
from typing import Callable, Self

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
from clinical_mdr_api.services.user_info import UserInfoService
from common.exceptions import AlreadyExistsException


@dataclass
class ReferencedItemVO:
    item_type: SoAItemType
    item_uid: str
    item_name: str | None = None


@dataclass
class StudySoAFootnoteVOHistory:
    uid: str
    study_uid: str
    footnote_uid: str | None
    footnote_version: str | None
    footnote_template_uid: str | None
    footnote_template_version: str | None
    referenced_items: list[ReferencedItemVO]
    footnote_number: int
    start_date: datetime
    end_date: datetime | None
    change_type: str
    status: StudyStatus | None = None
    author_id: str | None = None
    author_username: str | None = None
    is_deleted: bool = False
    accepted_version: bool = False


@dataclass
class StudySoAFootnoteVO:
    uid: str
    study_uid: str
    footnote_uid: str | None
    footnote_version: str | None
    footnote_template_uid: str | None
    footnote_template_version: str | None
    referenced_items: list[ReferencedItemVO]
    footnote_number: int
    modified: datetime | None = None
    status: StudyStatus | None = None
    author_id: str | None = None
    author_username: str | None = None
    is_deleted: bool = False
    accepted_version: bool = False

    @classmethod
    def from_input_values(
        cls,
        study_uid: str,
        footnote_uid: str,
        footnote_version: str | None,
        footnote_template_uid: str,
        footnote_template_version: str | None,
        referenced_items: list[ReferencedItemVO],
        footnote_number: int,
        author_id: str,
        status: StudyStatus,
        modified: datetime | None = None,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
        accepted_version: bool = False,
    ) -> Self:
        footnote_ar = cls(
            uid=generate_uid_callback(),
            study_uid=study_uid,
            footnote_uid=footnote_uid,
            footnote_version=footnote_version,
            footnote_template_uid=footnote_template_uid,
            footnote_template_version=footnote_template_version,
            footnote_number=footnote_number,
            referenced_items=referenced_items,
            author_id=author_id,
            author_username=UserInfoService.get_author_username_from_id(author_id),
            status=status,
            modified=modified,
            accepted_version=accepted_version,
        )
        return footnote_ar

    @classmethod
    def from_repository_values(
        cls,
        study_uid: str,
        footnote_uid: str,
        footnote_template_uid: str,
        referenced_items: list[ReferencedItemVO],
        footnote_number: int,
        uid: str,
        modified: datetime,
        author_id: str,
        status: StudyStatus,
        accepted_version: bool,
        footnote_version: str = None,
        footnote_template_version: str = None,
    ) -> Self:
        footnote_ar = cls(
            uid=uid,
            study_uid=study_uid,
            footnote_uid=footnote_uid,
            footnote_version=footnote_version,
            footnote_template_uid=footnote_template_uid,
            footnote_template_version=footnote_template_version,
            footnote_number=footnote_number,
            referenced_items=referenced_items,
            modified=modified,
            author_id=author_id,
            author_username=UserInfoService.get_author_username_from_id(author_id),
            status=status,
            accepted_version=accepted_version,
        )
        return footnote_ar

    def validate(self):
        AlreadyExistsException.raise_if(
            self.footnote_uid and self.footnote_template_uid,
            msg=f"Footnote UID '{self.footnote_uid}' and Footnote Template UID '{self.footnote_template_uid}' can't be both set.",
        )
        AlreadyExistsException.raise_if(
            not self.footnote_uid and not self.footnote_template_uid,
            msg=f"At least one of Footnote UID '{self.footnote_uid}' and Footnote Template UID '{self.footnote_template_uid}' must be set.",
        )

    def accept_versions(self):
        return replace(self, accepted_version=True)
