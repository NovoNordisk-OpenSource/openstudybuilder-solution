import unittest
from typing import Callable

from clinical_mdr_api.domains.dictionaries.dictionary_term import (
    DictionaryTermAR,
    DictionaryTermVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str


def create_random_dictionary_term_vo() -> DictionaryTermVO:
    name = random_str()
    random_dictionary_term_vo = DictionaryTermVO.from_repository_values(
        codelist_uid=random_str(),
        dictionary_id=random_str(),
        name="prefix" + name,
        name_sentence_case="Prefix" + name,
        abbreviation=random_str(),
        definition=random_str(),
    )
    return random_dictionary_term_vo


def create_random_dictionary_term_ar(
    # pylint: disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> DictionaryTermAR:
    random_dictionary_term_ar = DictionaryTermAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        dictionary_term_vo=create_random_dictionary_term_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
        term_exists_by_name_callback=lambda term_name, codelist_uid: False,
    )
    return random_dictionary_term_ar


class TestDictionaryTerm(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        dictionary_term_ar = create_random_dictionary_term_ar()

        # then
        self.assertIsNone(dictionary_term_ar.item_metadata._end_date)
        self.assertIsNotNone(dictionary_term_ar.item_metadata._start_date)
        self.assertEqual(dictionary_term_ar.item_metadata.version, "0.1")
        self.assertEqual(
            dictionary_term_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__approve__version_created(self):
        # given
        dictionary_term_ar = create_random_dictionary_term_ar()

        # when
        dictionary_term_ar.approve(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(dictionary_term_ar.item_metadata._end_date)
        self.assertIsNotNone(dictionary_term_ar.item_metadata._start_date)
        self.assertEqual(dictionary_term_ar.item_metadata.version, "1.0")
        self.assertEqual(
            dictionary_term_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__create_new_version__version_created(self):
        # given
        dictionary_term_ar = create_random_dictionary_term_ar()
        dictionary_term_ar.approve(author_id=AUTHOR_ID)

        # when
        dictionary_term_ar.create_new_version(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(dictionary_term_ar.item_metadata._end_date)
        self.assertIsNotNone(dictionary_term_ar.item_metadata._start_date)
        self.assertEqual(dictionary_term_ar.item_metadata.version, "1.1")
        self.assertEqual(
            dictionary_term_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__edit_draft_version__version_created(self):
        # given
        dictionary_term_ar = create_random_dictionary_term_ar()

        dictionary_term_ar.approve(author_id="Test")
        dictionary_term_ar.create_new_version(author_id=AUTHOR_ID)

        # when
        dictionary_term_vo = create_random_dictionary_term_vo()
        dictionary_term_ar.edit_draft(
            author_id=AUTHOR_ID,
            change_description="Test",
            dictionary_term_vo=dictionary_term_vo,
            term_exists_by_name_callback=lambda term_name, codelist_uid: False,
        )

        # then
        self.assertIsNone(dictionary_term_ar.item_metadata.end_date)
        self.assertIsNotNone(dictionary_term_ar.item_metadata.start_date)
        self.assertEqual(dictionary_term_ar.item_metadata.version, "1.2")
        self.assertEqual(
            dictionary_term_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )
        self.assertEqual(dictionary_term_ar.item_metadata.author_id, AUTHOR_ID)
        self.assertEqual(dictionary_term_ar.item_metadata.change_description, "Test")
        self.assertEqual(
            dictionary_term_ar.dictionary_term_vo.codelist_uid,
            dictionary_term_vo.codelist_uid,
        )
        self.assertEqual(dictionary_term_ar.name, dictionary_term_vo.name)
        self.assertEqual(
            dictionary_term_ar.dictionary_term_vo.dictionary_id,
            dictionary_term_vo.dictionary_id,
        )
        self.assertEqual(
            dictionary_term_ar.dictionary_term_vo.name_sentence_case,
            dictionary_term_vo.name_sentence_case,
        )
        self.assertEqual(
            dictionary_term_ar.dictionary_term_vo.abbreviation,
            dictionary_term_vo.abbreviation,
        )
        self.assertEqual(
            dictionary_term_ar.dictionary_term_vo.definition,
            dictionary_term_vo.definition,
        )

    def test__inactivate_final__version_created(self):
        # given
        dictionary_term_ar = create_random_dictionary_term_ar()
        dictionary_term_ar.approve(author_id=AUTHOR_ID)

        # when
        dictionary_term_ar.inactivate(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(dictionary_term_ar.item_metadata._end_date)
        self.assertIsNotNone(dictionary_term_ar.item_metadata._start_date)
        self.assertEqual(dictionary_term_ar.item_metadata.version, "1.0")
        self.assertEqual(
            dictionary_term_ar.item_metadata.status, LibraryItemStatus.RETIRED
        )

    def test__reactivate_retired__version_created(self):
        # given
        dictionary_term_ar = create_random_dictionary_term_ar()
        dictionary_term_ar.approve(author_id=AUTHOR_ID)
        dictionary_term_ar.inactivate(author_id=AUTHOR_ID)

        # when
        dictionary_term_ar.reactivate(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(dictionary_term_ar.item_metadata._end_date)
        self.assertIsNotNone(dictionary_term_ar.item_metadata._start_date)
        self.assertEqual(dictionary_term_ar.item_metadata.version, "1.0")
        self.assertEqual(
            dictionary_term_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__delete_draft__object_deleted(self):
        # given
        dictionary_term_ar = create_random_dictionary_term_ar()

        # when
        dictionary_term_ar.soft_delete()

        # then
        self.assertTrue(dictionary_term_ar.is_deleted)
