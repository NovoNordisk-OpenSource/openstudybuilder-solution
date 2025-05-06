from dataclasses import dataclass
from typing import Self

from pydantic import BaseModel


class LibraryItem(BaseModel):
    uid: str
    name: str | None = None


@dataclass(frozen=True)
class ActivityItemVO:
    """
    The ActivityItemVO acts as the value object for a single ActivityItem value object
    """

    is_adam_param_specific: bool
    activity_item_class_uid: str
    activity_item_class_name: str | None
    ct_terms: list[LibraryItem]
    unit_definitions: list[LibraryItem]
    odm_items: list[LibraryItem]

    @classmethod
    def from_repository_values(
        cls,
        is_adam_param_specific: bool,
        activity_item_class_uid: str,
        activity_item_class_name: str | None,
        ct_terms: list[dict[str, str]],
        unit_definitions=list[dict[str, str]],
        odm_items=list[dict[str, str]],
    ) -> Self:
        activity_item_vo = cls(
            is_adam_param_specific=is_adam_param_specific,
            activity_item_class_uid=activity_item_class_uid,
            activity_item_class_name=activity_item_class_name,
            ct_terms=ct_terms,
            unit_definitions=unit_definitions,
            odm_items=odm_items,
        )

        return activity_item_vo
