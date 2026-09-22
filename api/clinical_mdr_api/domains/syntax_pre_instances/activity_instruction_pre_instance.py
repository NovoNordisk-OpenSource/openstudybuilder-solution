from dataclasses import dataclass, field
from typing import Callable, Self

from clinical_mdr_api.domains.libraries.object import ParametrizedTemplateVO
from clinical_mdr_api.domains.syntax_pre_instances.pre_instance_ar import PreInstanceAR
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import SimpleTermModel
from clinical_mdr_api.models.generic_models import SimpleNameModel


@dataclass
class ActivityInstructionPreInstanceAR(PreInstanceAR):
    """
    Implementation of ActivityInstructionPreInstanceAR. Solely based on Parametrized Template.
    """

    _indications: list[SimpleTermModel] = field(default_factory=list)

    _activities: list[SimpleNameModel] = field(default_factory=list)

    _activity_groups: list[SimpleNameModel] = field(default_factory=list)

    _activity_subgroups: list[SimpleNameModel] = field(default_factory=list)

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
        template: ParametrizedTemplateVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
        sequence_id: str,
        study_count: int = 0,
        indications: list[SimpleTermModel] | None = None,
        activities: list[SimpleNameModel] | None = None,
        activity_groups: list[SimpleNameModel] | None = None,
        activity_subgroups: list[SimpleNameModel] | None = None,
    ) -> Self:
        if indications is None:
            indications = []
        if activities is None:
            activities = []
        if activity_groups is None:
            activity_groups = []
        if activity_subgroups is None:
            activity_subgroups = []
        return cls(
            _uid=uid,
            _sequence_id=sequence_id,
            _item_metadata=item_metadata,
            _library=library,
            _template=template,
            _indications=indications or [],
            _activities=activities or [],
            _activity_groups=activity_groups or [],
            _activity_subgroups=activity_subgroups or [],
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
        indications: list[SimpleTermModel] | None = None,
        activities: list[SimpleNameModel] | None = None,
        activity_groups: list[SimpleNameModel] | None = None,
        activity_subgroups: list[SimpleNameModel] | None = None,
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
        ar._indications = indications or []
        ar._activities = activities or []
        ar._activity_groups = activity_groups or []
        ar._activity_subgroups = activity_subgroups or []

        return ar
