import re
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
from clinical_mdr_api.models.generic_models import SimpleNameModel


@dataclass
class FootnoteTemplateAR(TemplateAggregateRootBase):
    """
    A specific Footnote Template AR. It can be used to customize Footnote Template
    behavior. Inherits generic template versioning behaviors
    """

    _type: SimpleCTTermNameAndAttributes | None = None

    _indications: list[SimpleTermModel] | None = None

    _activities: list[SimpleNameModel] | None = None

    _activity_groups: list[SimpleNameModel] | None = None

    _activity_subgroups: list[SimpleNameModel] | None = None

    @property
    def type(self) -> SimpleCTTermNameAndAttributes | None:
        return self._type

    @property
    def indications(self) -> list[SimpleTermModel]:
        return self._indications

    @property
    def activities(self) -> list[SimpleNameModel]:
        return self._activities

    @property
    def activity_groups(self) -> list[SimpleNameModel]:
        return self._activity_groups

    @property
    def activity_subgroups(self) -> list[SimpleNameModel]:
        return self._activity_subgroups

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
        footnote_type: SimpleCTTermNameAndAttributes | None = None,
        indications: list[SimpleTermModel] | None = None,
        activities: list[SimpleNameModel] | None = None,
        activity_groups: list[SimpleNameModel] | None = None,
        activity_subgroups: list[SimpleNameModel] | None = None,
    ) -> Self:
        return cls(
            _uid=uid,
            _sequence_id=sequence_id,
            _item_metadata=item_metadata,
            _library=library,
            _template=template,
            _type=footnote_type,
            _indications=indications,
            _activities=activities,
            _activity_groups=activity_groups,
            _activity_subgroups=activity_subgroups,
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
        next_available_sequence_id_callback: Callable[..., str] = lambda x, y, z, w: "",
        generate_uid_callback: Callable[[], str | None] = lambda: None,
        footnote_type: SimpleCTTermNameAndAttributes | None = None,
        indications: list[SimpleTermModel] | None = None,
        activities: list[SimpleNameModel] | None = None,
        activity_groups: list[SimpleNameModel] | None = None,
        activity_subgroups: list[SimpleNameModel] | None = None,
    ) -> Self:
        footnote_type_name = re.sub(
            "footnote",
            "",
            footnote_type.name.sponsor_preferred_name,
            flags=re.IGNORECASE,
        )

        ar: FootnoteTemplateAR = super().from_input_values(
            author_id=author_id,
            template=template,
            library=library,
            generate_uid_callback=generate_uid_callback,
        )
        ar._sequence_id = next_available_sequence_id_callback(
            uid=ar._uid,
            prefix="F"
            + "".join([char for char in footnote_type_name if char.isupper()]),
            type_uid=footnote_type.term_uid,
            library=library,
        )
        ar._type = footnote_type
        ar._indications = indications
        ar._activities = activities
        ar._activity_groups = activity_groups
        ar._activity_subgroups = activity_subgroups

        return ar
