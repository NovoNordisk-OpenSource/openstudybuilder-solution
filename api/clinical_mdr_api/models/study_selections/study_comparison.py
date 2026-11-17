from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field


class StudyComparisonChangeType(StrEnum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    MODIFIED = "MODIFIED"
    UNCHANGED = "UNCHANGED"
    RECREATED = "RECREATED"


class StudyComparisonFieldChange(BaseModel):
    field: Annotated[
        str,
        Field(
            description="Dot-separated path of the changed field, e.g. 'timing.visit_type_name'"
        ),
    ]
    old_value: Annotated[
        Any,
        Field(
            description="Value in the first version (null if the field did not exist)",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    new_value: Annotated[
        Any,
        Field(
            description="Value in the second version (null if the field no longer exists)",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    changed: Annotated[
        bool,
        Field(
            description="False for fields returned for context that are equal in both versions"
        ),
    ] = True


class StudyComparisonItemChange(BaseModel):
    key: Annotated[
        str, Field(description="Identifier matching the item across both versions")
    ]
    label: Annotated[
        str | None,
        Field(
            description="Human readable name of the item",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    change_type: StudyComparisonChangeType
    changes: Annotated[
        list[StudyComparisonFieldChange],
        Field(
            description="Fields of the item. For ADDED/REMOVED items all populated fields (the missing side is null). "
            "For MODIFIED items the differing fields, or all populated fields (with `changed` flags) "
            "when `include_unchanged` was requested. RECREATED items list the fields that differ (the uids). UNCHANGED items carry all populated fields. "
            "Empty for relationship entries."
        ),
    ] = []


class StudyComparisonSection(BaseModel):
    section: Annotated[
        str, Field(description="Machine readable name of the compared study area")
    ]
    title: Annotated[str, Field(description="Display name of the compared study area")]
    added: Annotated[
        int, Field(description="Number of items only in the second version")
    ]
    removed: Annotated[
        int, Field(description="Number of items only in the first version")
    ]
    modified: Annotated[
        int, Field(description="Number of items that differ between the versions")
    ]
    recreated: Annotated[
        int,
        Field(
            description="Number of items deleted and created again with identical values except for their uids"
        ),
    ] = 0
    unchanged: Annotated[
        int,
        Field(
            description="Number of identical items; only returned when `include_unchanged` was requested"
        ),
    ] = 0
    items: Annotated[
        list[StudyComparisonItemChange],
        Field(
            description="Items that differ between the versions, plus identical items when `include_unchanged` was requested"
        ),
    ]


class StudyComparison(BaseModel):
    study_uid: str
    version_a: Annotated[str, Field(description="Study version compared from")]
    version_b: Annotated[str, Field(description="Study version compared to")]
    has_changes: bool
    sections: list[StudyComparisonSection]
