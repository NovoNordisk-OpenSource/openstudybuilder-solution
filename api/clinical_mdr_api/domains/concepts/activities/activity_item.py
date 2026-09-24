from dataclasses import dataclass
from typing import Self

from pydantic import BaseModel

from clinical_mdr_api.models.concepts.activities.activity_item import (
    CompactUnitDefinition,
)


class LibraryItem(BaseModel):
    uid: str
    name: str | None = None


class CTCodelistItem(LibraryItem): ...


class CTTermItem(LibraryItem):
    codelist_uid: str | None = None
    submission_value: str | None = None


@dataclass(frozen=True)
class ActivityItemVO:
    """
    The ActivityItemVO acts as the value object for a single ActivityItem value object
    """

    is_adam_param_specific: bool
    is_activity_instance_id_specific: bool | None
    activity_item_class_uid: str
    activity_item_class_name: str | None
    ct_codelist: CTCodelistItem | None
    ct_terms: list[CTTermItem]
    unit_definitions: list[CompactUnitDefinition]
    text_value: str | None = None

    @classmethod
    def from_repository_values(
        cls,
        is_adam_param_specific: bool,
        activity_item_class_uid: str,
        activity_item_class_name: str | None,
        ct_codelist: CTCodelistItem | None,
        ct_terms: list[CTTermItem],
        unit_definitions: list[CompactUnitDefinition],
        text_value: str | None = None,
        is_activity_instance_id_specific: bool | None = None,
    ) -> Self:
        activity_item_vo = cls(
            is_adam_param_specific=is_adam_param_specific,
            is_activity_instance_id_specific=is_activity_instance_id_specific,
            activity_item_class_uid=activity_item_class_uid,
            activity_item_class_name=activity_item_class_name,
            ct_codelist=ct_codelist,
            ct_terms=ct_terms,
            unit_definitions=unit_definitions,
            text_value=text_value,
        )

        return activity_item_vo
