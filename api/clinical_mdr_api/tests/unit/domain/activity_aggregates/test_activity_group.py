import unittest
from typing import Callable

from clinical_mdr_api.domains.concepts.activities.activity_group import (
    ActivityGroupAR,
    ActivityGroupVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str
from common import exceptions


def create_random_activity_group_vo() -> ActivityGroupVO:
    name = random_str()
    random_activity_group_vo = ActivityGroupVO.from_repository_values(
        name=name,
        name_sentence_case=name,
        definition=random_str(),
        abbreviation=random_str(),
    )
    return random_activity_group_vo


def create_random_activity_group_ar(
    # pylint: disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> ActivityGroupAR:
    random_activity_group_ar = ActivityGroupAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        concept_vo=create_random_activity_group_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
        concept_exists_by_callback=lambda x, y, z: False,
        concept_exists_by_library_and_name_callback=lambda x, y: False,
    )

    return random_activity_group_ar


class TestActivityGroup(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        activity_group_ar = create_random_activity_group_ar()

        # then
        self.assertIsNone(activity_group_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_group_ar.item_metadata._start_date)
        self.assertEqual(activity_group_ar.item_metadata.version, "0.1")
        self.assertEqual(
            activity_group_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__edit_draft_version__version_created(self):
        # given
        activity_group_ar = create_random_activity_group_ar()

        activity_group_ar.approve(author_id="Test")
        activity_group_ar.create_new_version(author_id=AUTHOR_ID)

        # when
        activity_vo = create_random_activity_group_vo()
        activity_group_ar.edit_draft(
            author_id=AUTHOR_ID,
            change_description="Test",
            concept_vo=activity_vo,
            concept_exists_by_library_and_name_callback=lambda x, y: False,
        )

        # then
        self.assertIsNone(activity_group_ar.item_metadata.end_date)
        self.assertIsNotNone(activity_group_ar.item_metadata.start_date)
        self.assertEqual(activity_group_ar.item_metadata.version, "1.2")
        self.assertEqual(
            activity_group_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )
        self.assertEqual(activity_group_ar.item_metadata.author_id, AUTHOR_ID)
        self.assertEqual(activity_group_ar.item_metadata.change_description, "Test")
        self.assertEqual(activity_group_ar.name, activity_vo.name)
        self.assertEqual(
            activity_group_ar.concept_vo.name_sentence_case,
            activity_vo.name_sentence_case,
        )
        self.assertEqual(
            activity_group_ar.concept_vo.definition, activity_vo.definition
        )

    def test__approve__version_created(self):
        # given
        activity_group_ar = create_random_activity_group_ar()

        # when
        activity_group_ar.approve(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(activity_group_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_group_ar.item_metadata._start_date)
        self.assertEqual(activity_group_ar.item_metadata.version, "1.0")
        self.assertEqual(
            activity_group_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__create_new_version__version_created(self):
        # given
        activity_group_ar = create_random_activity_group_ar()
        activity_group_ar.approve(author_id=AUTHOR_ID)

        # when
        activity_group_ar.create_new_version(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(activity_group_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_group_ar.item_metadata._start_date)
        self.assertEqual(activity_group_ar.item_metadata.version, "1.1")
        self.assertEqual(
            activity_group_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__inactivate_final__version_created(self):
        # given
        activity_group_ar = create_random_activity_group_ar()
        activity_group_ar.approve(author_id=AUTHOR_ID)

        # when
        activity_group_ar.inactivate(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(activity_group_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_group_ar.item_metadata._start_date)
        self.assertEqual(activity_group_ar.item_metadata.version, "1.0")
        self.assertEqual(
            activity_group_ar.item_metadata.status, LibraryItemStatus.RETIRED
        )

    def test__reactivate_retired__version_created(self):
        # given
        activity_group_ar = create_random_activity_group_ar()
        activity_group_ar.approve(author_id=AUTHOR_ID)
        activity_group_ar.inactivate(author_id=AUTHOR_ID)

        # when
        activity_group_ar.reactivate(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(activity_group_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_group_ar.item_metadata._start_date)
        self.assertEqual(activity_group_ar.item_metadata.version, "1.0")
        self.assertEqual(
            activity_group_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__delete_draft__object_deleted(self):
        # given
        activity_group_ar = create_random_activity_group_ar()

        # when
        activity_group_ar.soft_delete()

        # then
        self.assertTrue(activity_group_ar.is_deleted)


class TestActivityGroupNegative(unittest.TestCase):
    def test__init__ar_validation_failure(self):
        name = random_str()
        with self.assertRaises(exceptions.ValidationException) as context:
            ActivityGroupAR.from_input_values(
                generate_uid_callback=random_str,
                concept_vo=ActivityGroupVO.from_repository_values(
                    name=name,
                    name_sentence_case="Different from name",
                    definition=random_str(),
                    abbreviation=random_str(),
                ),
                library=LibraryVO.from_repository_values(
                    library_name="library", is_editable=True
                ),
                author_id=AUTHOR_ID,
                concept_exists_by_callback=lambda x, y, z: False,
            )

        assert (
            context.exception.msg
            == f"Lowercase versions of '{name}' and 'Different from name' must be equal"
        )

    def test__edit_draft_version__validation_failure(self):
        activity_group_ar = create_random_activity_group_ar()

        activity_group_ar.approve(author_id="Test")
        activity_group_ar.create_new_version(author_id=AUTHOR_ID)

        name = random_str()
        with self.assertRaises(exceptions.ValidationException) as context:
            activity_group_ar.edit_draft(
                author_id=AUTHOR_ID,
                change_description="Test",
                concept_vo=ActivityGroupVO.from_repository_values(
                    name=name,
                    name_sentence_case="Different from name",
                    definition=random_str(),
                    abbreviation=random_str(),
                ),
                concept_exists_by_callback=lambda x, y, z: False,
            )

        assert (
            context.exception.msg
            == f"Lowercase versions of '{name}' and 'Different from name' must be equal"
        )
