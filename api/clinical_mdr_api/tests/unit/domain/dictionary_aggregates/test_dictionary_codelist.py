import unittest
from typing import Callable

from clinical_mdr_api.domains.dictionaries.dictionary_codelist import (
    DictionaryCodelistAR,
    DictionaryCodelistVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str


def create_random_dictionary_codelist_vo() -> DictionaryCodelistVO:
    random_dictionary_codelist_vo = DictionaryCodelistVO.from_repository_values(
        name=random_str(),
        is_template_parameter=False,
        current_terms=[],
        previous_terms=[],
    )
    return random_dictionary_codelist_vo


def create_random_dictionary_codelist_ar(
    # pylint: disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> DictionaryCodelistAR:
    random_dictionary_codelist_ar = DictionaryCodelistAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        dictionary_codelist_vo=create_random_dictionary_codelist_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
    )
    return random_dictionary_codelist_ar


class TestDictionaryCodelist(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        dictionary_codelist_ar = create_random_dictionary_codelist_ar()

        # then
        self.assertIsNone(dictionary_codelist_ar.item_metadata._end_date)
        self.assertIsNotNone(dictionary_codelist_ar.item_metadata._start_date)
        self.assertEqual(dictionary_codelist_ar.item_metadata.version, "0.1")
        self.assertEqual(
            dictionary_codelist_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__approve__version_created(self):
        # given
        dictionary_codelist_ar = create_random_dictionary_codelist_ar()

        # when
        dictionary_codelist_ar.approve(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(dictionary_codelist_ar.item_metadata._end_date)
        self.assertIsNotNone(dictionary_codelist_ar.item_metadata._start_date)
        self.assertEqual(dictionary_codelist_ar.item_metadata.version, "1.0")
        self.assertEqual(
            dictionary_codelist_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__create_new_version__version_created(self):
        # given
        dictionary_codelist_ar = create_random_dictionary_codelist_ar()
        dictionary_codelist_ar.approve(author_id=AUTHOR_ID)

        # when
        dictionary_codelist_ar.create_new_version(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(dictionary_codelist_ar.item_metadata._end_date)
        self.assertIsNotNone(dictionary_codelist_ar.item_metadata._start_date)
        self.assertEqual(dictionary_codelist_ar.item_metadata.version, "1.1")
        self.assertEqual(
            dictionary_codelist_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__edit_draft_version__version_created(self):
        # given
        dictionary_codelist_ar = create_random_dictionary_codelist_ar()

        dictionary_codelist_ar.approve(author_id="Test")
        dictionary_codelist_ar.create_new_version(author_id=AUTHOR_ID)

        # when
        dictionary_codelist_vo = create_random_dictionary_codelist_vo()
        dictionary_codelist_ar.edit_draft(
            author_id=AUTHOR_ID,
            change_description="Test",
            dictionary_codelist_vo=dictionary_codelist_vo,
            codelist_exists_by_name_callback=lambda _: False,
        )

        # then
        self.assertIsNone(dictionary_codelist_ar.item_metadata.end_date)
        self.assertIsNotNone(dictionary_codelist_ar.item_metadata.start_date)
        self.assertEqual(dictionary_codelist_ar.item_metadata.version, "1.2")
        self.assertEqual(
            dictionary_codelist_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )
        self.assertEqual(dictionary_codelist_ar.item_metadata.author_id, AUTHOR_ID)
        self.assertEqual(
            dictionary_codelist_ar.item_metadata.change_description, "Test"
        )
        self.assertEqual(dictionary_codelist_ar.name, dictionary_codelist_vo.name)
        self.assertEqual(
            dictionary_codelist_ar.dictionary_codelist_vo.is_template_parameter,
            dictionary_codelist_vo.is_template_parameter,
        )

    def test__add_term__term_added(self):
        # given
        dictionary_codelist_ar = create_random_dictionary_codelist_ar()
        amount_of_terms = 5
        term_data = []

        # when
        for _ in range(amount_of_terms):
            codelist_uid = random_str()
            term_uid = random_str()
            author_id = random_str()
            term_data.append({"term_uid": term_uid, "author_id": author_id})
            dictionary_codelist_ar.add_term(
                codelist_uid=codelist_uid, term_uid=term_uid, author_id=author_id
            )

        # then
        self.assertIsNone(dictionary_codelist_ar.item_metadata._end_date)
        self.assertIsNotNone(dictionary_codelist_ar.item_metadata._start_date)
        self.assertEqual(dictionary_codelist_ar.item_metadata.version, "0.1")
        self.assertEqual(
            dictionary_codelist_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )
        self.assertTrue(
            len(dictionary_codelist_ar.dictionary_codelist_vo.current_terms)
            == amount_of_terms
        )
        self.assertTrue(
            len(dictionary_codelist_ar.dictionary_codelist_vo.previous_terms) == 0
        )

        for term, current_term in zip(
            term_data, dictionary_codelist_ar.dictionary_codelist_vo.current_terms
        ):
            with self.subTest():
                self.assertEqual(term["term_uid"], current_term[0])
                self.assertEqual(term["author_id"], current_term[1])

    def test__remove_term__term_removed(self):
        # given
        dictionary_codelist_ar = create_random_dictionary_codelist_ar()
        amount_of_terms = 5
        amount_of_terms_to_delete = 2
        term_data = []
        codelist_uid = random_str()
        for _ in range(amount_of_terms):
            term_uid = random_str()
            author_id = random_str()
            term_data.append({"term_uid": term_uid, "author_id": author_id})
            dictionary_codelist_ar.add_term(
                codelist_uid=codelist_uid, term_uid=term_uid, author_id=author_id
            )

        # when
        deleted_terms = []
        for _ in range(amount_of_terms_to_delete):
            deleted_term = term_data.pop()
            deleted_terms.append(deleted_term)
            dictionary_codelist_ar.remove_term(
                codelist_uid=codelist_uid,
                term_uid=deleted_term["term_uid"],
                author_id=deleted_term["author_id"],
            )

        # then
        self.assertIsNone(dictionary_codelist_ar.item_metadata._end_date)
        self.assertIsNotNone(dictionary_codelist_ar.item_metadata._start_date)
        self.assertEqual(dictionary_codelist_ar.item_metadata.version, "0.1")
        self.assertEqual(
            dictionary_codelist_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )
        self.assertTrue(
            len(dictionary_codelist_ar.dictionary_codelist_vo.current_terms)
            == amount_of_terms - amount_of_terms_to_delete
        )
        self.assertTrue(
            len(dictionary_codelist_ar.dictionary_codelist_vo.previous_terms)
            == amount_of_terms_to_delete
        )

        for term, current_term in zip(
            term_data, dictionary_codelist_ar.dictionary_codelist_vo.current_terms
        ):
            with self.subTest():
                self.assertEqual(term["term_uid"], current_term[0])
                self.assertEqual(term["author_id"], current_term[1])
        for term, previous_term in zip(
            deleted_terms, dictionary_codelist_ar.dictionary_codelist_vo.previous_terms
        ):
            with self.subTest():
                self.assertEqual(term["term_uid"], previous_term[0])
                self.assertEqual(term["author_id"], previous_term[1])
