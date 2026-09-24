import unittest
from typing import Callable

from clinical_mdr_api.domains.concepts.compound import CompoundAR, CompoundVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str


def create_random_compound_vo() -> CompoundVO:
    random_compound_vo = CompoundVO.from_repository_values(
        name=random_str(),
        name_sentence_case=random_str(),
        definition=random_str(),
        abbreviation=random_str(),
        external_id=random_str(),
    )
    return random_compound_vo


def create_random_compound_ar(
    # pylint: disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> CompoundAR:
    random_compound_ar = CompoundAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        concept_vo=create_random_compound_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
        compound_uid_by_property_value_callback=lambda _, __: False,
    )

    return random_compound_ar


class TestCompound(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        compound_ar = create_random_compound_ar()

        # then
        self.assertIsNone(compound_ar.item_metadata._end_date)
        self.assertIsNotNone(compound_ar.item_metadata._start_date)
        self.assertEqual(compound_ar.item_metadata.version, "0.1")
        self.assertEqual(compound_ar.item_metadata.status, LibraryItemStatus.DRAFT)

    def test__approve__version_created(self):
        # given
        compound_ar = create_random_compound_ar()

        # when
        compound_ar.approve(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(compound_ar.item_metadata._end_date)
        self.assertIsNotNone(compound_ar.item_metadata._start_date)
        self.assertEqual(compound_ar.item_metadata.version, "1.0")
        self.assertEqual(compound_ar.item_metadata.status, LibraryItemStatus.FINAL)

    def test__create_new_version__version_created(self):
        # given
        compound_ar = create_random_compound_ar()
        compound_ar.approve(author_id=AUTHOR_ID)

        # when
        compound_ar.create_new_version(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(compound_ar.item_metadata._end_date)
        self.assertIsNotNone(compound_ar.item_metadata._start_date)
        self.assertEqual(compound_ar.item_metadata.version, "1.1")
        self.assertEqual(compound_ar.item_metadata.status, LibraryItemStatus.DRAFT)

    def test__inactivate_final__version_created(self):
        # given
        compound_ar = create_random_compound_ar()
        compound_ar.approve(author_id=AUTHOR_ID)

        # when
        compound_ar.inactivate(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(compound_ar.item_metadata._end_date)
        self.assertIsNotNone(compound_ar.item_metadata._start_date)
        self.assertEqual(compound_ar.item_metadata.version, "1.0")
        self.assertEqual(compound_ar.item_metadata.status, LibraryItemStatus.RETIRED)

    def test__reactivate_retired__version_created(self):
        # given
        compound_ar = create_random_compound_ar()
        compound_ar.approve(author_id=AUTHOR_ID)
        compound_ar.inactivate(author_id=AUTHOR_ID)

        # when
        compound_ar.reactivate(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(compound_ar.item_metadata._end_date)
        self.assertIsNotNone(compound_ar.item_metadata._start_date)
        self.assertEqual(compound_ar.item_metadata.version, "1.0")
        self.assertEqual(compound_ar.item_metadata.status, LibraryItemStatus.FINAL)

    def test__delete_draft__object_deleted(self):
        # given
        compound_ar = create_random_compound_ar()

        # when
        compound_ar.soft_delete()

        # then
        self.assertTrue(compound_ar.is_deleted)

    def test__edit_draft_version__version_created(self):
        # given
        compound_ar = create_random_compound_ar()

        compound_ar.approve(author_id="Test")
        compound_ar.create_new_version(author_id=AUTHOR_ID)

        # when
        compound_vo = create_random_compound_vo()

        compound_ar.edit_draft(
            author_id=AUTHOR_ID,
            change_description="Test",
            concept_vo=compound_vo,
            compound_uid_by_property_value_callback=lambda _, __: False,
        )
        # then
        self.assertIsNone(compound_ar.item_metadata.end_date)
        self.assertIsNotNone(compound_ar.item_metadata.start_date)
        self.assertEqual(compound_ar.item_metadata.version, "1.2")
        self.assertEqual(compound_ar.item_metadata.status, LibraryItemStatus.DRAFT)
        self.assertEqual(compound_ar.item_metadata.author_id, AUTHOR_ID)
        self.assertEqual(compound_ar.item_metadata.change_description, "Test")
        self.assertEqual(compound_ar.name, compound_vo.name)
        self.assertEqual(
            compound_ar.concept_vo.name_sentence_case,
            compound_vo.name_sentence_case,
        )
        self.assertEqual(compound_ar.concept_vo.definition, compound_vo.definition)
