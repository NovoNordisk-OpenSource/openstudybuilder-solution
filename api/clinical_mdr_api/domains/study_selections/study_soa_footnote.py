from dataclasses import dataclass, replace
from datetime import datetime
from typing import Callable, Self

from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
from common.exceptions import AlreadyExistsException


@dataclass
class ReferencedItemVO:
    item_type: SoAItemType
    item_uid: str
    item_name: str | None = None
    visible_in_protocol_soa: bool | None = None
    order: list[int] | None = None


@dataclass
class StudySoAFootnoteVOHistory:
    uid: str
    study_uid: str
    footnote_uid: str | None
    footnote_version: str | None
    footnote_name_plain: str | None
    footnote_template_uid: str | None
    footnote_template_version: str | None
    footnote_template_name_plain: str | None
    referenced_items: list[ReferencedItemVO]
    start_date: datetime
    end_date: datetime | None
    change_type: str
    author_id: str
    author_username: str | None = None
    is_deleted: bool = False
    accepted_version: bool = False


@dataclass
class StudySoAFootnoteVO:
    uid: str
    study_uid: str
    footnote_uid: str | None
    footnote_version: str | None
    footnote_name: str | None
    footnote_name_plain: str | None
    footnote_library_name: str | None
    footnote_status: str | None
    latest_footnote_version: str | None
    latest_footnote_name_plain: str | None
    footnote_template_uid: str | None
    footnote_template_version: str | None
    footnote_template_name: str | None
    footnote_template_name_plain: str | None
    footnote_template_library_name: str | None
    footnote_template_parameters: list[str] | None
    referenced_items: list[ReferencedItemVO]
    author_id: str | None
    modified: datetime | None = None
    author_username: str | None = None
    is_deleted: bool = False
    accepted_version: bool = False

    @classmethod
    def from_input_values(
        cls,
        study_uid: str,
        footnote_uid: str | None,
        footnote_version: str | None,
        footnote_name_plain: str | None,
        footnote_name: str | None,
        footnote_library_name: str | None,
        footnote_status: str | None,
        latest_footnote_version: str | None,
        latest_footnote_name_plain: str | None,
        footnote_template_uid: str | None,
        footnote_template_version: str | None,
        footnote_template_name: str | None,
        footnote_template_name_plain: str | None,
        footnote_template_library_name: str | None,
        footnote_template_parameters: list[str] | None,
        referenced_items: list[ReferencedItemVO],
        author_id: str | None,
        modified: datetime | None = None,
        generate_uid_callback: Callable[[], str] = lambda: "",
        accepted_version: bool = False,
        author_username: str | None = None,
    ) -> Self:
        footnote_ar = cls(
            uid=generate_uid_callback(),
            study_uid=study_uid,
            footnote_uid=footnote_uid,
            footnote_version=footnote_version,
            footnote_name_plain=footnote_name_plain,
            footnote_name=footnote_name,
            footnote_library_name=footnote_library_name,
            footnote_status=footnote_status,
            latest_footnote_name_plain=latest_footnote_name_plain,
            latest_footnote_version=latest_footnote_version,
            footnote_template_uid=footnote_template_uid,
            footnote_template_version=footnote_template_version,
            footnote_template_name=footnote_template_name,
            footnote_template_name_plain=footnote_template_name_plain,
            footnote_template_library_name=footnote_template_library_name,
            footnote_template_parameters=footnote_template_parameters,
            referenced_items=referenced_items,
            author_id=author_id,
            author_username=author_username,
            modified=modified,
            accepted_version=accepted_version,
        )
        return footnote_ar

    @classmethod
    def from_repository_values(
        cls,
        study_uid: str,
        footnote_uid: str | None,
        footnote_template_uid: str | None,
        referenced_items: list[ReferencedItemVO],
        uid: str,
        modified: datetime | None,
        author_id: str | None,
        accepted_version: bool,
        footnote_version: str | None = None,
        footnote_name_plain: str | None = None,
        footnote_name: str | None = None,
        footnote_library_name: str | None = None,
        footnote_status: str | None = None,
        latest_footnote_version: str | None = None,
        latest_footnote_name_plain: str | None = None,
        footnote_template_version: str | None = None,
        footnote_template_name: str | None = None,
        footnote_template_name_plain: str | None = None,
        footnote_template_library_name: str | None = None,
        footnote_template_parameters: list[str] | None = None,
        author_username: str | None = None,
    ) -> Self:
        footnote_ar = cls(
            uid=uid,
            study_uid=study_uid,
            footnote_uid=footnote_uid,
            footnote_version=footnote_version,
            footnote_name=footnote_name,
            footnote_name_plain=footnote_name_plain,
            footnote_library_name=footnote_library_name,
            footnote_status=footnote_status,
            latest_footnote_name_plain=latest_footnote_name_plain,
            latest_footnote_version=latest_footnote_version,
            footnote_template_uid=footnote_template_uid,
            footnote_template_name=footnote_template_name,
            footnote_template_version=footnote_template_version,
            footnote_template_name_plain=footnote_template_name_plain,
            footnote_template_library_name=footnote_template_library_name,
            footnote_template_parameters=footnote_template_parameters,
            referenced_items=referenced_items,
            modified=modified,
            author_id=author_id,
            author_username=author_username,
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
