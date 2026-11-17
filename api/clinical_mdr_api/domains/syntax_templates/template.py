from collections.abc import Callable, Iterable, Set
from dataclasses import dataclass, field, replace
from typing import Self

from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
)
from clinical_mdr_api.utils import extract_parameters, strip_html
from common.exceptions import BusinessLogicException, ValidationException


@dataclass(frozen=True)
class TemplateVO:
    """
    Value Object class representing template values
    """

    # template name value
    name: str
    name_plain: str | None = None

    # template guidance text
    guidance_text: str | None = None

    # names of the template parameters used as placeholders in the name, in order.
    # Bracketed text that is not a template parameter name is literal text.
    parameter_names: list[str] = field(default_factory=list)

    @classmethod
    def from_input_values_2(
        cls,
        template_name: str,
        parameter_name_exists_callback: Callable[[str], bool],
        guidance_text: str | None = None,
    ) -> Self:
        return cls(
            name=template_name,
            name_plain=strip_html(template_name),
            guidance_text=guidance_text,
            parameter_names=extract_parameters(
                template_name, parameter_name_exists_callback
            ),
        )

    @classmethod
    def from_repository_values(
        cls,
        template_name: str,
        template_name_plain: str,
        guidance_text: str | None = None,
        linked_parameter_names: Iterable[str] = (),
    ) -> Self:
        """
        Restores the template from the database. The placeholders are resolved against
        the template parameters the template is linked to, not against all existing
        template parameters, so creating a template parameter later on does not turn
        literal text of a stored template into a placeholder.
        """
        return cls(
            name=template_name,
            name_plain=template_name_plain,
            guidance_text=guidance_text,
            parameter_names=extract_parameters(
                template_name, set(linked_parameter_names).__contains__
            ),
        )

    def with_literal_text(self, names: Set[str]) -> Self:
        """
        Returns the template with the bracketed `names` treated as literal text
        instead of placeholders.
        """
        if not names.intersection(self.parameter_names):
            return self
        return replace(
            self,
            parameter_names=[
                parameter_name
                for parameter_name in self.parameter_names
                if parameter_name not in names
            ],
        )


@dataclass
class InstantiationCountsVO:
    _count_draft: int = 0
    _count_final: int = 0
    _count_retired: int = 0

    @property
    def count_draft(self):
        return self._count_draft

    @property
    def count_final(self):
        return self._count_final

    @property
    def count_retired(self):
        return self._count_retired

    @property
    def count_total(self):
        return self._count_draft + self._count_final + self._count_retired

    @classmethod
    def from_counts(cls, final: int, draft: int, retired: int):
        return cls(_count_draft=draft, _count_final=final, _count_retired=retired)


@dataclass
class TemplateAggregateRootBase(LibraryItemAggregateRootBase):
    """
    A generic class implementing versioning of templates. It will be
    inherited from by other Template AR classes.
    """

    _sequence_id: str

    _template: TemplateVO | None = None

    _counts: InstantiationCountsVO | None = None

    _study_count: int = 0

    @property
    def sequence_id(self) -> str:
        return self._sequence_id

    @sequence_id.setter
    def sequence_id(self, sequence_id: str) -> None:
        self.__set_sequence_id(sequence_id)

    # Setter for supporting sequence_id creation
    def __set_sequence_id(self, sequence_id: str) -> None:
        self.__raise_error_if_deleted()
        if self._sequence_id is None:
            self._sequence_id = sequence_id
        else:
            raise TypeError("Cannot modify existing sequence_id.")

    @property
    def study_count(self) -> int:
        return self._study_count

    @property
    def name(self) -> str:
        assert self._template is not None
        return self._template.name

    @property
    def name_plain(self) -> str:
        assert self._template is not None
        return self._template.name_plain

    @property
    def guidance_text(self) -> str | None:
        assert self._template is not None
        return self._template.guidance_text

    @property
    def counts(self):
        return self._counts

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        sequence_id: str,
        template: TemplateVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
        study_count: int = 0,
        counts: InstantiationCountsVO | None = None,
    ) -> Self:
        return cls(
            _uid=uid,
            _sequence_id=sequence_id,
            _item_metadata=item_metadata,
            _library=library,
            _template=template,
            _study_count=study_count,
            _counts=counts,
        )

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        template: TemplateVO,
        library: LibraryVO,
        next_available_sequence_id_callback: Callable[
            ..., str
        ] = lambda uid, library: "",
        generate_uid_callback: Callable[[], str | None] = lambda: None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )
        ValidationException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )

        generated_uid = generate_uid_callback()

        return cls(
            _uid=generated_uid,
            _sequence_id=next_available_sequence_id_callback(
                uid=generated_uid, library=library
            ),
            _item_metadata=item_metadata,
            _library=library,
            _template=template,
        )

    @property
    def template_value(self) -> TemplateVO:
        assert self._template is not None
        return self._template

    def edit_draft(
        self, author_id: str, change_description: str, template: TemplateVO
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        if self.item_metadata.version >= "1.0":
            template = self._keep_literal_text(template)
            if self.template_value.parameter_names != template.parameter_names:
                self._raise_versioning_exception()
        if self._template != template:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._template = template

    def _raise_versioning_exception(self):
        raise BusinessLogicException(
            msg="You cannot change number or order of template parameters for a previously approved template."
        )

    def _keep_literal_text(self, template: TemplateVO) -> TemplateVO:
        """
        Bracketed text that is literal in the current version stays literal, even when a
        template parameter with that name has been created since. The placeholders of an
        approved template are fixed, and its instances would silently lose that text.
        """
        literal_names = set(extract_parameters(self.name, lambda _: True)) - set(
            self.template_value.parameter_names
        )
        return template.with_literal_text(literal_names)

    def create_new_version(
        self, author_id: str, change_description: str, template: TemplateVO
    ) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        template = self._keep_literal_text(template)
        if self.template_value.parameter_names != template.parameter_names:
            self._raise_versioning_exception()
        super()._create_new_version(
            change_description=change_description, author_id=author_id
        )
        self._template = template

    def get_possible_actions(self) -> Set[ObjectAction]:
        """
        Returns list of possible actions
        """
        if (
            self._item_metadata.status == LibraryItemStatus.DRAFT
            and self._item_metadata.major_version == 0
        ):
            return {ObjectAction.APPROVE, ObjectAction.EDIT, ObjectAction.DELETE}
        if self._item_metadata.status == LibraryItemStatus.DRAFT:
            return {ObjectAction.APPROVE, ObjectAction.EDIT}
        if self._item_metadata.status == LibraryItemStatus.FINAL:
            return {ObjectAction.NEWVERSION, ObjectAction.INACTIVATE}
        if self._item_metadata.status == LibraryItemStatus.RETIRED:
            return {ObjectAction.REACTIVATE}
        return frozenset()
