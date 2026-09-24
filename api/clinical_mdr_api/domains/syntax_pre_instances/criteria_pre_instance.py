from dataclasses import dataclass, field
from typing import Callable, Self

from clinical_mdr_api.domains.libraries.object import ParametrizedTemplateVO
from clinical_mdr_api.domains.syntax_pre_instances.pre_instance_ar import PreInstanceAR
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
    SimpleTermModel,
)


@dataclass
class CriteriaPreInstanceAR(PreInstanceAR):
    """
    Implementation of CriteriaPreInstanceAR. Solely based on Parametrized Template.
    """

    guidance_text: str | None = None

    _indications: list[SimpleTermModel] = field(default_factory=list)

    _categories: list[SimpleCTTermNameAndAttributes] = field(default_factory=list)

    _subcategories: list[SimpleCTTermNameAndAttributes] = field(default_factory=list)

    _type: SimpleCTTermNameAndAttributes | None = None

    @property
    def type(self) -> SimpleCTTermNameAndAttributes | None:
        return self._type

    @property
    def indications(self) -> list[SimpleTermModel]:
        return self._indications

    @property
    def categories(self) -> list[SimpleCTTermNameAndAttributes]:
        return self._categories

    @property
    def sub_categories(self) -> list[SimpleCTTermNameAndAttributes]:
        return self._subcategories

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        template: ParametrizedTemplateVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
        sequence_id: str,
        study_count: int = 0,
        guidance_text: str | None = None,
        criteria_type: SimpleCTTermNameAndAttributes | None = None,
        indications: list[SimpleTermModel] | None = None,
        categories: list[SimpleCTTermNameAndAttributes] | None = None,
        sub_categories: list[SimpleCTTermNameAndAttributes] | None = None,
    ) -> Self:
        return cls(
            _uid=uid,
            _sequence_id=sequence_id,
            _item_metadata=item_metadata,
            _library=library,
            _template=template,
            _type=criteria_type,
            guidance_text=guidance_text,
            _indications=indications or [],
            _categories=categories or [],
            _subcategories=sub_categories or [],
            _study_count=study_count,
        )

    @classmethod
    def from_input_values(
        cls,
        author_id: str,
        library: LibraryVO,
        template: ParametrizedTemplateVO,
        generate_uid_callback: Callable[[], str | None] = lambda: None,
        next_available_sequence_id_callback: Callable[..., str] = lambda _: "",
        criteria_type: SimpleCTTermNameAndAttributes | None = None,
        guidance_text: str | None = None,
        indications: list[SimpleTermModel] | None = None,
        categories: list[SimpleCTTermNameAndAttributes] | None = None,
        sub_categories: list[SimpleCTTermNameAndAttributes] | None = None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        generated_uid = generate_uid_callback()

        ar = cls(
            _uid=generated_uid,
            _sequence_id=next_available_sequence_id_callback(template.template_uid),
            _library=library,
            guidance_text=guidance_text,
            _template=template,
            _item_metadata=item_metadata,
        )
        ar._type = criteria_type
        ar._indications = indications or []
        ar._categories = categories or []
        ar._subcategories = sub_categories or []

        return ar

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        template: ParametrizedTemplateVO,
        guidance_text: str | None = None,
    ):
        """
        Creates a new draft version for the object.
        """
        if self._template != template or self.guidance_text != guidance_text:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._template = template
            self.guidance_text = guidance_text
