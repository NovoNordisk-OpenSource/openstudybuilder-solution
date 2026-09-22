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
class ObjectivePreInstanceAR(PreInstanceAR):
    """
    Implementation of ObjectivePreInstanceAR. Solely based on Parametrized Template.
    """

    _is_confirmatory_testing: bool = False

    _indications: list[SimpleTermModel] = field(default_factory=list)

    _categories: list[SimpleCTTermNameAndAttributes] = field(default_factory=list)

    @property
    def is_confirmatory_testing(self) -> bool:
        return self._is_confirmatory_testing

    @property
    def indications(self) -> list[SimpleTermModel]:
        return self._indications

    @property
    def categories(self) -> list[SimpleCTTermNameAndAttributes]:
        return self._categories

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        template: ParametrizedTemplateVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
        sequence_id: str,
        study_count: int = 0,
        is_confirmatory_testing: bool = False,
        indications: list[SimpleTermModel] | None = None,
        categories: list[SimpleCTTermNameAndAttributes] | None = None,
    ) -> Self:
        return cls(
            _uid=uid,
            _sequence_id=sequence_id,
            _item_metadata=item_metadata,
            _library=library,
            _template=template,
            _is_confirmatory_testing=is_confirmatory_testing,
            _indications=indications or [],
            _categories=categories or [],
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
        is_confirmatory_testing: bool = False,
        indications: list[SimpleTermModel] | None = None,
        categories: list[SimpleCTTermNameAndAttributes] | None = None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        generated_uid = generate_uid_callback()

        ar = cls(
            _uid=generated_uid,
            _sequence_id=next_available_sequence_id_callback(template.template_uid),
            _library=library,
            _template=template,
            _item_metadata=item_metadata,
        )
        ar._is_confirmatory_testing = is_confirmatory_testing
        ar._indications = indications or []
        ar._categories = categories or []

        return ar
