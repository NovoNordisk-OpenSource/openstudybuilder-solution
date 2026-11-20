"""Service layer for feature flag operations."""

from neomodel import db

from clinical_mdr_api.domain_repositories.feature_flag_repository import (
    FeatureFlagRepository,
)
from clinical_mdr_api.domains.feature_flags.state_machine import FeatureFlagStateMachine
from clinical_mdr_api.models.feature_flag import (
    FeatureFlag,
    FeatureFlagInput,
    FeatureFlagPatchInput,
    FeatureFlagVersion,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.services._utils import calculate_diffs, get_otv
from common.auth.user import user
from common.exceptions import AlreadyExistsException


class FeatureFlagService:
    """Coordinate feature flag repository access and business rules."""

    repo: FeatureFlagRepository

    def __init__(self) -> None:
        """Initialize the feature flag service."""
        self.repo = FeatureFlagRepository()

    @property
    def author(self) -> str:
        """Return the current authenticated user's identifier."""
        return user().id()

    def get_all_feature_flags(self, include_retired: bool = False) -> list[FeatureFlag]:
        """Return current feature flags, optionally including retired ones."""
        return self.repo.retrieve_all_feature_flags(include_retired=include_retired)

    def get_feature_flag(self, uid: str) -> FeatureFlag:
        """Return the current feature flag for the provided uid."""
        return self.repo.retrieve_feature_flag(uid)

    @db.transaction
    def create_feature_flag(
        self,
        feature_flag_input: FeatureFlagInput,
    ) -> FeatureFlag:
        """Create a new feature flag after validating uniqueness by name."""
        AlreadyExistsException.raise_if(
            self.repo.find_feature_flag_by_name(feature_flag_input.name),
            "Feature Flag",
            feature_flag_input.name,
            "Name",
        )

        return self.repo.create_feature_flag(
            feature_flag_input=feature_flag_input,
            author_id=self.author,
        )

    @db.transaction
    def update_feature_flag(
        self,
        uid: str,
        feature_flag_patch_input: FeatureFlagPatchInput,
    ) -> FeatureFlag:
        """Update a Final feature flag by creating a new version."""
        current = self.repo.retrieve_feature_flag(uid)
        FeatureFlagStateMachine.ensure_can_update(current.status)
        return self.repo.update_feature_flag(
            uid=uid,
            author_id=self.author,
            **feature_flag_patch_input.model_dump(exclude_unset=True),
        )

    @db.transaction
    def inactivate_final(self, uid: str) -> FeatureFlag:
        """Inactivate a Final feature flag."""
        current = self.repo.retrieve_feature_flag(uid)
        FeatureFlagStateMachine.ensure_can_inactivate(current.status)
        return self.repo.inactivate_final(uid=uid, author_id=self.author)

    @db.transaction
    def reactivate_retired(self, uid: str) -> FeatureFlag:
        """Reactivate a Retired feature flag."""
        current = self.repo.retrieve_feature_flag(uid)
        FeatureFlagStateMachine.ensure_can_reactivate(current.status)
        return self.repo.reactivate_retired(uid=uid, author_id=self.author)

    def get_version_history(self, uid: str) -> list[FeatureFlagVersion]:
        """Return feature flag version history augmented with diff information."""
        versions = [item.model_dump() for item in self.repo.get_all_versions(uid=uid)]
        return calculate_diffs(versions, FeatureFlagVersion)

    def get_audit_trail(
        self,
        page_number: int = 1,
        page_size: int = 10,
        total_count: bool = False,
        section: str | None = None,
    ) -> CustomPage[FeatureFlagVersion]:
        """Return one page of the version history of all feature flags.

        Every version is diffed against the previous version of the same flag.
        When a section is given, only flags currently in that section are listed.
        """
        items, total = self.repo.get_audit_trail(
            page_number=page_number,
            page_size=page_size,
            total_count=total_count,
            section=section,
        )
        versions = [
            get_otv(
                FeatureFlagVersion,
                version.model_dump(),
                previous.model_dump() if previous else None,
            )
            for version, previous in items
        ]
        return CustomPage.create(
            items=versions, total=total, page=page_number, size=page_size
        )
