import datetime
import unittest

from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
)


class TestTimeframeTemplateCascade(unittest.TestCase):
    def test_status_modification(self):
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id="Test"
        )
        self.assertEqual(item_metadata.status, LibraryItemStatus.DRAFT)
        self.assertEqual(item_metadata.version, "0.1")
        self.assertEqual(item_metadata._author_id, "Test")
        self.assertEqual(item_metadata._change_description, "Initial version")

        start = datetime.datetime.now(datetime.timezone.utc)
        item_metadata = item_metadata.new_draft_version("Test new", "Change test")
        self.assertEqual(item_metadata._change_description, "Change test")
        self.assertEqual(item_metadata._author_id, "Test new")

        self.assertEqual(item_metadata.status, LibraryItemStatus.DRAFT)
        self.assertEqual(item_metadata.version, "0.2")
        after = datetime.datetime.now(datetime.timezone.utc)

        self.assertGreaterEqual(item_metadata.start_date, start)
        self.assertGreaterEqual(after, item_metadata.start_date)

        start = datetime.datetime.now(datetime.timezone.utc)
        item_metadata = item_metadata.new_final_version("Test new 2", "Change test 2")
        self.assertEqual(item_metadata._change_description, "Change test 2")
        self.assertEqual(item_metadata._author_id, "Test new 2")

        self.assertEqual(item_metadata.status, LibraryItemStatus.FINAL)
        self.assertEqual(item_metadata.version, "1.0")
        after = datetime.datetime.now(datetime.timezone.utc)

        self.assertGreaterEqual(item_metadata.start_date, start)
        self.assertGreaterEqual(after, item_metadata.start_date)

        start = datetime.datetime.now(datetime.timezone.utc)
        item_metadata = item_metadata.new_draft_version("Test new 3", "Change test 3")
        self.assertEqual(item_metadata._change_description, "Change test 3")
        self.assertEqual(item_metadata._author_id, "Test new 3")

        self.assertEqual(item_metadata.status, LibraryItemStatus.DRAFT)
        self.assertEqual(item_metadata.version, "1.1")
        after = datetime.datetime.now(datetime.timezone.utc)

        self.assertGreaterEqual(item_metadata.start_date, start)
        self.assertGreaterEqual(after, item_metadata.start_date)

        start = datetime.datetime.now(datetime.timezone.utc)
        item_metadata = item_metadata.new_final_version("Test new 4", "Change test 4")
        self.assertEqual(item_metadata._change_description, "Change test 4")
        self.assertEqual(item_metadata._author_id, "Test new 4")

        self.assertEqual(item_metadata.status, LibraryItemStatus.FINAL)
        self.assertEqual(item_metadata.version, "2.0")
        after = datetime.datetime.now(datetime.timezone.utc)

        self.assertGreaterEqual(item_metadata.start_date, start)
        self.assertGreaterEqual(after, item_metadata.start_date)

        start = datetime.datetime.now(datetime.timezone.utc)
        item_metadata = item_metadata.new_retired_version("Test new 5", "Change test 5")
        self.assertEqual(item_metadata._change_description, "Change test 5")
        self.assertEqual(item_metadata._author_id, "Test new 5")

        self.assertEqual(item_metadata.status, LibraryItemStatus.RETIRED)
        self.assertEqual(item_metadata.version, "2.0")
        after = datetime.datetime.now(datetime.timezone.utc)

        self.assertGreaterEqual(item_metadata.start_date, start)
        self.assertGreaterEqual(after, item_metadata.start_date)

        start = datetime.datetime.now(datetime.timezone.utc)
        item_metadata = item_metadata.new_version_start_date(
            "Test new", "Change test", start
        )
        self.assertEqual(item_metadata._change_description, "Change test")
        self.assertEqual(item_metadata._author_id, "Test new")

        self.assertEqual(item_metadata.status, LibraryItemStatus.RETIRED)
        self.assertEqual(item_metadata.version, "3.0")
        after = datetime.datetime.now(datetime.timezone.utc)

        self.assertEqual(item_metadata.start_date, start)

        start = datetime.datetime.now(datetime.timezone.utc)
        item_metadata = item_metadata.new_final_version("Test new 1", "Change test 1")
        self.assertEqual(item_metadata._change_description, "Change test 1")
        self.assertEqual(item_metadata._author_id, "Test new 1")

        self.assertEqual(item_metadata.status, LibraryItemStatus.FINAL)
        self.assertEqual(item_metadata.version, "3.0")
        after = datetime.datetime.now(datetime.timezone.utc)

        self.assertGreaterEqual(item_metadata.start_date, start)
        self.assertGreaterEqual(after, item_metadata.start_date)

        start = datetime.datetime.now(datetime.timezone.utc)
        item_metadata = item_metadata.new_version_start_date(
            "Test new", "Change test", start
        )
        self.assertEqual(item_metadata._change_description, "Change test")
        self.assertEqual(item_metadata._author_id, "Test new")

        self.assertEqual(item_metadata.status, LibraryItemStatus.FINAL)
        self.assertEqual(item_metadata.version, "4.0")
        after = datetime.datetime.now(datetime.timezone.utc)

        self.assertEqual(item_metadata.start_date, start)

        start = datetime.datetime.now(datetime.timezone.utc)
        item_metadata = item_metadata.new_draft_version("Test new 1", "Change test 1")
        self.assertEqual(item_metadata._change_description, "Change test 1")
        self.assertEqual(item_metadata._author_id, "Test new 1")

        self.assertEqual(item_metadata.status, LibraryItemStatus.DRAFT)
        self.assertEqual(item_metadata.version, "4.1")
        after = datetime.datetime.now(datetime.timezone.utc)

        self.assertGreaterEqual(item_metadata.start_date, start)
        self.assertGreaterEqual(after, item_metadata.start_date)

        start = datetime.datetime.now(datetime.timezone.utc)
        item_metadata = item_metadata.new_version_start_date(
            "Test new", "Change test", start
        )
        self.assertEqual(item_metadata._change_description, "Change test")
        self.assertEqual(item_metadata._author_id, "Test new")

        self.assertEqual(item_metadata.status, LibraryItemStatus.DRAFT)
        self.assertEqual(item_metadata.version, "4.2")
        after = datetime.datetime.now(datetime.timezone.utc)

        self.assertEqual(item_metadata.start_date, start)
