from dataclasses import dataclass, field
from typing import Any, Self

from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    ObjectAction,
    VersioningActionMixin,
)
from common.exceptions import BusinessLogicException


@dataclass(frozen=True)
class StudyTemplateValueVO:
    study_uid: str
    study_value_version: str

    @classmethod
    def from_input_values(
        cls,
        *,
        study_uid: str,
        study_value_version: str,
    ) -> Self:
        return cls.from_repository_values(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )

    @classmethod
    def from_repository_values(
        cls,
        *,
        study_uid: str,
        study_value_version: str,
    ) -> Self:
        return cls(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )


@dataclass
class StudyTemplateAR(VersioningActionMixin):
    _value: StudyTemplateValueVO
    _item_metadata: LibraryItemMetadataVO
    _uid: str | None = None
    _is_deleted: bool = field(init=False, default=False)
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    def get_possible_actions(self) -> set[ObjectAction]:
        raise NotImplementedError("Possible actions retrieval not implemented.")

    @property
    def item_metadata(self) -> LibraryItemMetadataVO:
        return self._item_metadata

    @property
    def value(self) -> StudyTemplateValueVO:
        return self._value

    @property
    def uid(self) -> str | None:
        return self._uid

    @property
    def is_deleted(self) -> bool:
        return self._is_deleted

    def create_new_version(self, author_id: str):
        super()._create_new_version(author_id)

    def edit_draft(
        self,
        *,
        author_id: str,
        change_description: str,
        new_study_template_value: StudyTemplateValueVO,
    ) -> None:
        if self._value != new_study_template_value:
            super()._edit_draft(
                author_id=author_id,
                change_description=change_description,
            )
            self._value = new_study_template_value

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        study_template_value: StudyTemplateValueVO,
        generate_uid_callback=lambda: None,
    ) -> Self:
        return cls(
            _uid=generate_uid_callback(),
            _value=study_template_value,
            _item_metadata=LibraryItemMetadataVO.get_initial_item_metadata(
                author_id=author_id
            ),
        )

    @classmethod
    def from_repository_values(
        cls,
        *,
        uid: str,
        item_metadata: LibraryItemMetadataVO,
        study_template_value: StudyTemplateValueVO,
    ) -> Self:
        return cls(
            _uid=uid,
            _item_metadata=item_metadata,
            _value=study_template_value,
        )

    def _is_edit_allowed_in_non_editable_library(self):
        return True

    def soft_delete(self):
        raise BusinessLogicException(
            msg="Deleting the Study Template configuration is not supported."
        )
