from __future__ import annotations

from typing import TYPE_CHECKING

from clinical_mdr_api.domain_repositories.models.generic import ClinicalMdrNode
from clinical_mdr_api.domain_repositories.preferences_registry import (
    get_neomodel_properties,
)

if TYPE_CHECKING:

    class PreferencesMixin:  # static stub for mypy
        pass

else:
    # Dynamically build mixin from registry at runtime
    PreferencesMixin = type("PreferencesMixin", (), get_neomodel_properties())


class GlobalPreferences(PreferencesMixin, ClinicalMdrNode):
    pass


class UserPreferences(PreferencesMixin, ClinicalMdrNode):
    pass
