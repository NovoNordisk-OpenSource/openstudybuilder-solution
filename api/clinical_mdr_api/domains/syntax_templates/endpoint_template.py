from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.syntax_templates.template import (
    InstantiationCountsVO,
    TemplateAggregateRootBase,
    TemplateVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
    SimpleTermModel,
)


@dataclass
class EndpointTemplateAR(TemplateAggregateRootBase):
    """
    A specific Endpoint Template AR. It can be used to customize Endpoint Template
    behavior. Inherits generic template versioning behaviors
    """

    _indications: list[SimpleTermModel] | None = None

    _categories: list[SimpleCTTermNameAndAttributes] | None = None

    _subcategories: list[SimpleCTTermNameAndAttributes] | None = None

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
        sequence_id: str,
        template: TemplateVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
        study_count: int = 0,
        counts: InstantiationCountsVO | None = None,
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
            _indications=indications,
            _categories=categories,
            _subcategories=sub_categories,
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
        indications: list[SimpleTermModel] | None = None,
        categories: list[SimpleCTTermNameAndAttributes] | None = None,
        sub_categories: list[SimpleCTTermNameAndAttributes] | None = None,
    ) -> Self:
        ar: Self = super().from_input_values(
            author_id=author_id,
            template=template,
            library=library,
            generate_uid_callback=generate_uid_callback,
            next_available_sequence_id_callback=next_available_sequence_id_callback,
        )
        ar._indications = indications
        ar._categories = categories
        ar._subcategories = sub_categories

        return ar
