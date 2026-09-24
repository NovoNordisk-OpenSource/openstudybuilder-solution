import unittest

from clinical_mdr_api.domain_repositories.feature_flag_repository import (
    FeatureFlagRepository,
)


class TestFeatureFlagRepositoryImpl(unittest.TestCase):
    def test__bump_version_increments_minor_version(self):
        repo = FeatureFlagRepository()

        self.assertEqual(repo._bump_version("1.4"), "1.5")

    def test__bump_version_handles_malformed_version(self):
        repo = FeatureFlagRepository()

        self.assertEqual(repo._bump_version("broken"), "1.1")
        self.assertEqual(repo._bump_version("7"), "7.1")
