"""Explanations for the enums shown throughout the review workflow."""

from pydantic import BaseModel


class EnumDescription(BaseModel):
    """One enum's own docstring, plus each member's, keyed by value.

    Every member of the enum is a key. `null` means that member never had a docstring
    to begin with — a plain lifecycle step like `EffectiveDateStatus.IMPORTING`, not a
    gap in this list.
    """

    description: str | None = None
    values: dict[str, str | None]
