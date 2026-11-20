import unittest
from unittest.mock import MagicMock

from clinical_mdr_api.models.feature_flag import FeatureFlag
from clinical_mdr_api.services.feature_flags import FeatureFlagService


def _flag(uid: str, enabled: bool, version: str) -> FeatureFlag:
    return FeatureFlag(
        uid=uid,
        section="library",
        feature="feature",
        name=f"name {uid}",
        enabled=enabled,
        version=version,
    )


class TestFeatureFlagServiceAuditTrail(unittest.TestCase):
    def setUp(self):
        self.service = FeatureFlagService()
        self.service.repo = MagicMock()

    def test_get_audit_trail_diffs_each_version_against_its_own_previous(self):
        self.service.repo.get_audit_trail.return_value = (
            [
                (_flag("A", True, "1.1"), _flag("A", False, "1.0")),
                (_flag("B", False, "1.0"), None),
                (_flag("A", False, "1.0"), None),
            ],
            3,
        )

        page = self.service.get_audit_trail(
            page_number=2, page_size=3, total_count=True
        )

        self.service.repo.get_audit_trail.assert_called_once_with(
            page_number=2, page_size=3, total_count=True, section=None
        )
        self.assertEqual([item.uid for item in page.items], ["A", "B", "A"])
        self.assertIn("enabled", page.items[0].changes)
        self.assertEqual(page.items[1].changes, [])
        self.assertEqual(page.items[2].changes, [])
        self.assertEqual((page.total, page.page, page.size), (3, 2, 3))

    def test_get_audit_trail_without_versions_returns_empty_page(self):
        self.service.repo.get_audit_trail.return_value = ([], 0)

        page = self.service.get_audit_trail()

        self.assertEqual(list(page.items), [])
        self.assertEqual(page.total, 0)

    def test_get_audit_trail_passes_section_filter_to_repository(self):
        self.service.repo.get_audit_trail.return_value = ([], 0)

        self.service.get_audit_trail(section="admin")

        self.service.repo.get_audit_trail.assert_called_once_with(
            page_number=1, page_size=10, total_count=False, section="admin"
        )
