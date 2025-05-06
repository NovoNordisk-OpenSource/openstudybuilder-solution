import unittest
from typing import Callable

from clinical_mdr_api.domains.concepts.activities.activity import (
    ActivityAR,
    ActivityGroupingVO,
    ActivityVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str
from common import exceptions


def create_random_activity_grouping_vo() -> ActivityGroupingVO:
    random_activity_grouping_vo = ActivityGroupingVO(
        activity_group_uid=random_str(), activity_subgroup_uid=random_str()
    )
    return random_activity_grouping_vo


def create_random_activity_vo() -> ActivityVO:
    name = random_str()
    random_activity_vo = ActivityVO.from_repository_values(
        nci_concept_id=random_str(),
        nci_concept_name=random_str(),
        name=name,
        name_sentence_case=name,
        synonyms=[random_str(), random_str()],
        definition=random_str(),
        abbreviation=random_str(),
        activity_groupings=[
            create_random_activity_grouping_vo(),
            create_random_activity_grouping_vo(),
        ],
        activity_instances=[],
        request_rationale=random_str(),
        is_data_collected=True,
    )
    return random_activity_vo


def create_random_activity_ar(
    # pylint: disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> ActivityAR:
    random_activity_ar = ActivityAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        concept_vo=create_random_activity_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
        concept_exists_by_library_and_name_callback=lambda _l, _c: False,
        activity_subgroup_exists=lambda _: True,
        activity_group_exists=lambda _: True,
    )

    return random_activity_ar


class TestActivity(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        activity_ar = create_random_activity_ar()

        # then
        self.assertIsNone(activity_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_ar.item_metadata._start_date)
        self.assertEqual(activity_ar.item_metadata.version, "0.1")
        self.assertEqual(activity_ar.item_metadata.status, LibraryItemStatus.DRAFT)

    def test__edit_draft_version__version_created(self):
        # given
        activity_ar = create_random_activity_ar()

        activity_ar.approve(author_id="Test")
        activity_ar.create_new_version(author_id=AUTHOR_ID)

        # when
        activity_vo = create_random_activity_vo()
        activity_ar.edit_draft(
            author_id=AUTHOR_ID,
            change_description="Test",
            concept_vo=activity_vo,
            concept_exists_by_library_and_name_callback=lambda _l, _c: False,
            activity_subgroup_exists=lambda _: True,
            activity_group_exists=lambda _: True,
        )

        # then
        self.assertIsNone(activity_ar.item_metadata.end_date)
        self.assertIsNotNone(activity_ar.item_metadata.start_date)
        self.assertEqual(activity_ar.item_metadata.version, "1.2")
        self.assertEqual(activity_ar.item_metadata.status, LibraryItemStatus.DRAFT)
        self.assertEqual(activity_ar.item_metadata.author_id, AUTHOR_ID)
        self.assertEqual(activity_ar.item_metadata.change_description, "Test")
        self.assertEqual(activity_ar.name, activity_vo.name)
        self.assertEqual(
            activity_ar.concept_vo.name_sentence_case,
            activity_vo.name_sentence_case,
        )
        self.assertEqual(activity_ar.concept_vo.definition, activity_vo.definition)
        self.assertEqual(
            activity_vo.activity_groupings, activity_ar.concept_vo.activity_groupings
        )

    def test__approve__version_created(self):
        # given
        activity_ar = create_random_activity_ar()

        # when
        activity_ar.approve(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(activity_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_ar.item_metadata._start_date)
        self.assertEqual(activity_ar.item_metadata.version, "1.0")
        self.assertEqual(activity_ar.item_metadata.status, LibraryItemStatus.FINAL)

    def test__create_new_version__version_created(self):
        # given
        activity_ar = create_random_activity_ar()
        activity_ar.approve(author_id=AUTHOR_ID)

        # when
        activity_ar.create_new_version(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(activity_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_ar.item_metadata._start_date)
        self.assertEqual(activity_ar.item_metadata.version, "1.1")
        self.assertEqual(activity_ar.item_metadata.status, LibraryItemStatus.DRAFT)

    def test__inactivate_final__version_created(self):
        # given
        activity_ar = create_random_activity_ar()
        activity_ar.approve(author_id=AUTHOR_ID)

        # when
        activity_ar.inactivate(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(activity_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_ar.item_metadata._start_date)
        self.assertEqual(activity_ar.item_metadata.version, "1.0")
        self.assertEqual(activity_ar.item_metadata.status, LibraryItemStatus.RETIRED)

    def test__reactivate_retired__version_created(self):
        # given
        activity_ar = create_random_activity_ar()
        activity_ar.approve(author_id=AUTHOR_ID)
        activity_ar.inactivate(author_id=AUTHOR_ID)

        # when
        activity_ar.reactivate(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(activity_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_ar.item_metadata._start_date)
        self.assertEqual(activity_ar.item_metadata.version, "1.0")
        self.assertEqual(activity_ar.item_metadata.status, LibraryItemStatus.FINAL)

    def test__delete_draft__object_deleted(self):
        # given
        activity_ar = create_random_activity_ar()

        # when
        activity_ar.soft_delete()

        # then
        self.assertTrue(activity_ar.is_deleted)


class TestActivityNegative(unittest.TestCase):
    def test__init__ar_validation_failure(self):
        name = random_str()
        with self.assertRaises(exceptions.ValidationException) as context:
            ActivityAR.from_input_values(
                generate_uid_callback=random_str(),
                concept_vo=ActivityVO.from_repository_values(
                    nci_concept_id="C123",
                    nci_concept_name=random_str(),
                    name=name,
                    name_sentence_case="Different from name",
                    synonyms=[random_str(), random_str()],
                    definition=random_str(),
                    abbreviation=random_str(),
                    activity_groupings=[
                        create_random_activity_grouping_vo(),
                        create_random_activity_grouping_vo(),
                    ],
                    activity_instances=[],
                    request_rationale=random_str(),
                    is_data_collected=True,
                ),
                library=LibraryVO.from_repository_values(
                    library_name="library", is_editable=True
                ),
                author_id=AUTHOR_ID,
                concept_exists_by_library_and_name_callback=lambda _l, _c: False,
                activity_subgroup_exists=lambda _: True,
                activity_group_exists=lambda _: True,
            )

        assert (
            context.exception.msg
            == f"Lowercase versions of '{name}' and 'Different from name' must be equal"
        )

    def test__edit_draft_version__name_validation_failure(self):
        activity_ar = create_random_activity_ar()

        activity_ar.approve(author_id="Test")
        activity_ar.create_new_version(author_id=AUTHOR_ID)

        name = random_str()
        with self.assertRaises(exceptions.ValidationException) as context:
            activity_ar.edit_draft(
                author_id=AUTHOR_ID,
                change_description="Test",
                concept_vo=ActivityVO.from_repository_values(
                    nci_concept_id="C123",
                    nci_concept_name=random_str(),
                    name=name,
                    name_sentence_case="Different from name",
                    synonyms=[random_str(), random_str()],
                    definition=random_str(),
                    abbreviation=random_str(),
                    activity_groupings=[
                        create_random_activity_grouping_vo(),
                        create_random_activity_grouping_vo(),
                    ],
                    activity_instances=[],
                    request_rationale=random_str(),
                    is_data_collected=True,
                ),
                concept_exists_by_library_and_name_callback=lambda _l, _c: False,
                activity_subgroup_exists=lambda _: True,
                activity_group_exists=lambda _: True,
            )
        assert (
            context.exception.msg
            == f"Lowercase versions of '{name}' and 'Different from name' must be equal"
        )
