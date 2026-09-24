# pylint: disable=invalid-name
from neomodel import db

from clinical_mdr_api.domain_repositories.preferences_registry import (
    PREFERENCE_DEFINITIONS,
    PREFERENCE_KEYS,
    to_metadata_dict,
)
from clinical_mdr_api.domain_repositories.preferences_repository import (
    PreferencesRepository,
)
from clinical_mdr_api.models.preferences import (
    GlobalPreferencesPatchInput,
    PreferenceMetadata,
    PreferencesResponse,
    UserPreferencesPatchInput,
    UserPreferencesResponse,
)
from clinical_mdr_api.services._utils import ensure_transaction
from common.exceptions import ValidationException


class PreferencesService:
    repo: PreferencesRepository

    def __init__(self) -> None:
        self.repo = PreferencesRepository()

    def _build_metadata_response(self) -> dict[str, PreferenceMetadata]:
        """Build metadata response from the preference registry."""
        return {
            preference_definition.key: PreferenceMetadata(
                **to_metadata_dict(preference_definition)
            )
            for preference_definition in PREFERENCE_DEFINITIONS
        }

    def get_global_preferences(self) -> PreferencesResponse:
        """Get global preferences with metadata."""
        preferences = self.repo.get_global_preferences()
        metadata = self._build_metadata_response()
        return PreferencesResponse(preferences=preferences, metadata=metadata)

    @ensure_transaction(db)
    def update_global_preferences(
        self, input_data: GlobalPreferencesPatchInput
    ) -> PreferencesResponse:
        """Update global preferences and return updated state with metadata."""
        updates = input_data.model_dump(exclude_unset=True)
        preferences = self.repo.update_global_preferences(updates)
        metadata = self._build_metadata_response()
        return PreferencesResponse(preferences=preferences, metadata=metadata)

    @ensure_transaction(db)
    def get_user_preferences(self, user_id: str) -> UserPreferencesResponse:
        """Get user preferences merged with global defaults and compute overrides flags."""
        global_preferences = self.repo.get_global_preferences()
        user_preferences = self.repo.get_user_preferences(user_id)

        # Merge: global defaults with user overrides
        merged_preferences = {}
        overrides = {}

        for key in PREFERENCE_KEYS:
            global_value = global_preferences.get(key)
            user_value = user_preferences.get(key) if user_preferences else None

            if user_value is not None:
                merged_preferences[key] = user_value
                overrides[key] = global_value
            else:
                merged_preferences[key] = global_value

        metadata = self._build_metadata_response()
        return UserPreferencesResponse(
            preferences=merged_preferences, overrides=overrides, metadata=metadata
        )

    @ensure_transaction(db)
    def update_user_preferences(
        self, user_id: str, input_data: UserPreferencesPatchInput
    ) -> UserPreferencesResponse:
        """Update user preferences and return merged state with overrides."""
        updates = input_data.model_dump(exclude_unset=True)
        self.repo.update_user_preferences(user_id, updates)
        return self.get_user_preferences(user_id)

    @ensure_transaction(db)
    def delete_user_preference_key(
        self, user_id: str, key: str
    ) -> UserPreferencesResponse:
        """Delete a single user preference key (reset to global default)."""
        if key not in PREFERENCE_KEYS:
            raise ValidationException(f"Invalid preference key: '{key}'")

        self.repo.delete_user_preference_key(user_id, key)
        return self.get_user_preferences(user_id)
