from dataclasses import dataclass
from typing import Any, Literal

from neomodel import BooleanProperty, IntegerProperty, StringProperty


@dataclass(frozen=True)
class PreferenceDefinition:
    """Single source of truth for a preference field."""

    key: str
    preference_type: Literal["integer", "boolean", "enum", "string"]
    label: str
    description: str
    default: int | bool | str
    min: int | None = None
    max: int | None = None
    allowed_values: list[str] | None = None


PREFERENCE_DEFINITIONS: tuple[PreferenceDefinition, ...] = (
    PreferenceDefinition(
        key="language",
        preference_type="enum",
        label="Language",
        description="Preferred language for the application",
        default="en",
        allowed_values=["en"],
    ),
    PreferenceDefinition(
        key="theme",
        preference_type="string",
        label="Theme",
        description="Preferred theme for the application",
        default="NNCustomLightTheme",
    ),
    PreferenceDefinition(
        key="rows_per_page",
        preference_type="integer",
        label="Rows per page",
        description="Number of rows to display per page in tables",
        default=10,
        min=5,
        max=100,
    ),
    PreferenceDefinition(
        key="sidebar_visible",
        preference_type="boolean",
        label="Sidebar visible",
        description="Whether the sidebar is visible by default",
        default=True,
    ),
    PreferenceDefinition(
        key="sidebar_auto_minimize",
        preference_type="boolean",
        label="Auto-minimize sidebar",
        description="Automatically minimize the sidebar to rail mode",
        default=False,
    ),
)

# Derived lookups (computed once at import time)
PREFERENCE_KEYS: list[str] = [d.key for d in PREFERENCE_DEFINITIONS]
PREFERENCES_BY_KEY: dict[str, PreferenceDefinition] = {
    d.key: d for d in PREFERENCE_DEFINITIONS
}

# Map pref_type -> neomodel property constructor
_NEOMODEL_TYPE_MAP = {
    "integer": IntegerProperty,
    "boolean": BooleanProperty,
    "enum": StringProperty,
    "string": StringProperty,
}


def get_neomodel_properties() -> dict[str, Any]:
    """Return a dict of {key: NeomodelProperty()} for use in mixin class body."""
    return {
        d.key: _NEOMODEL_TYPE_MAP[d.preference_type]() for d in PREFERENCE_DEFINITIONS
    }


def to_metadata_dict(preference_definition: PreferenceDefinition) -> dict[str, Any]:
    """Convert a PreferenceDefinition to the API metadata dict shape."""
    result: dict[str, Any] = {
        "type": preference_definition.preference_type,
        "label": preference_definition.label,
        "description": preference_definition.description,
        "default": preference_definition.default,
    }
    if preference_definition.min is not None:
        result["min"] = preference_definition.min
    if preference_definition.max is not None:
        result["max"] = preference_definition.max
    if preference_definition.allowed_values is not None:
        result["allowed_values"] = preference_definition.allowed_values
    return result
