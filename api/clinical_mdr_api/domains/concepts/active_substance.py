from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from common.exceptions import BusinessLogicException


@dataclass(frozen=True)
class ActiveSubstanceVO(ConceptVO):
    """
    The ActiveSubstanceVO acts as the single value object for ActiveSubstanceAR aggregate.
    """

    analyte_number: str | None
    short_number: str | None
    long_number: str | None
    inn: str | None
    external_id: str | None
    unii_term_uid: str | None

    @classmethod
    def from_repository_values(
        cls,
        analyte_number: str | None,
        short_number: str | None,
        long_number: str | None,
        inn: str | None,
        external_id: str | None,
        unii_term_uid: str | None,
    ) -> Self:
        active_substance_vo = cls(
            analyte_number=analyte_number,
            short_number=short_number,
            long_number=long_number,
            inn=inn,
            external_id=external_id,
            unii_term_uid=unii_term_uid,
            name=None,
            name_sentence_case=None,
            definition=None,
            abbreviation=None,
            is_template_parameter=False,
        )

        return active_substance_vo

    def validate(
        self,
        uid: str,
        active_substance_uid_by_property_value_callback: Callable[
            [str, str], str | None
        ],
        dictionary_term_exists_callback: Callable[[str], bool],
    ):
        if self.analyte_number is not None:
            self.validate_uniqueness(
                lookup_callback=active_substance_uid_by_property_value_callback,
                uid=uid,
                property_name="analyte_number",
                value=self.analyte_number,
                error_message=f"Active Substance with Analyte Number '{self.analyte_number}' already exists.",
            )

        if self.short_number is not None:
            self.validate_uniqueness(
                lookup_callback=active_substance_uid_by_property_value_callback,
                uid=uid,
                property_name="short_number",
                value=self.short_number,
                error_message=f"Active Substance with Short Number '{self.short_number}' already exists.",
            )

        if self.long_number is not None:
            self.validate_uniqueness(
                lookup_callback=active_substance_uid_by_property_value_callback,
                uid=uid,
                property_name="long_number",
                value=self.long_number,
                error_message=f"Active Substance with Long Number '{self.long_number}' already exists.",
            )

        if self.external_id is not None:
            self.validate_uniqueness(
                lookup_callback=active_substance_uid_by_property_value_callback,
                uid=uid,
                property_name="external_id",
                value=self.external_id,
                error_message=f"Active Substance with external_id '{self.external_id}' already exists.",
            )

        BusinessLogicException.raise_if(
            self.unii_term_uid
            and not dictionary_term_exists_callback(self.unii_term_uid),
            msg=f"{type(self).__name__} tried to connect to non existing UNII Term with UID '{self.unii_term_uid}'.",
        )


class ActiveSubstanceAR(ConceptARBase):
    _external_id: str | None
    _concept_vo: ActiveSubstanceVO

    @property
    def concept_vo(self) -> ActiveSubstanceVO:
        return self._concept_vo

    @concept_vo.setter
    def concept_vo(self, value: ActiveSubstanceVO) -> None:
        self._concept_vo = value

    @property
    def name(self) -> str:
        return self.concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author_id: str,
        concept_vo: ActiveSubstanceVO,
        library: LibraryVO,
        active_substance_uid_by_property_value_callback: Callable[
            [str, str], str | None
        ],
        dictionary_term_exists_callback: Callable[[str], bool],
        generate_uid_callback: Callable[[], str],
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )
        uid = generate_uid_callback()

        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )

        concept_vo.validate(
            uid=uid,
            active_substance_uid_by_property_value_callback=active_substance_uid_by_property_value_callback,
            dictionary_term_exists_callback=dictionary_term_exists_callback,
        )

        active_substance_ar = cls(
            _uid=uid,
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return active_substance_ar

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        concept_vo: ActiveSubstanceVO,
        concept_exists_by_callback: Callable[
            [str, str], str | None
        ] = lambda x, y: None,
        dictionary_term_exists_callback: Callable[[str], bool] = lambda x: False,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            self.uid,
            active_substance_uid_by_property_value_callback=concept_exists_by_callback,
            dictionary_term_exists_callback=dictionary_term_exists_callback,
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._concept_vo = concept_vo
