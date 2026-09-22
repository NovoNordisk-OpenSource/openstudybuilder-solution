import unittest
from typing import Callable, Sequence

from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str


def create_random_ct_term_name_vo() -> CTTermNameVO:
    name = random_str()
    random_ct_term_name_vo = CTTermNameVO.from_repository_values(
        catalogue_names=[random_str()],
        name=name,
        name_sentence_case=name.lower(),
    )
    return random_ct_term_name_vo


def create_random_ct_term_name_ar(
    # pylint: disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> CTTermNameAR:
    random_ct_term_name_ar = CTTermNameAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        ct_term_name_vo=create_random_ct_term_name_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
    )
    return random_ct_term_name_ar


def create_random_ct_term_name_ars(
    # pylint: disable=unnecessary-lambda
    term_uids: Sequence[str] = [random_str() for i in range(10)],
    library: str = "Library",
    is_editable: bool = True,
) -> CTTermNameAR:
    random_ct_term_name_ars = []
    for codelist_uid in term_uids:
        random_ct_term_name_ars.append(
            CTTermNameAR.from_input_values(
                generate_uid_callback=lambda codelist_uid=codelist_uid: codelist_uid,
                ct_term_name_vo=create_random_ct_term_name_vo(),
                library=LibraryVO.from_repository_values(
                    library_name=library, is_editable=is_editable
                ),
                author_id=AUTHOR_ID,
            )
        )
    return random_ct_term_name_ars


class TestCTTermNameAR(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        ct_term_name_ar = create_random_ct_term_name_ar()

        # then
        self.assertIsNone(ct_term_name_ar.item_metadata._end_date)
        self.assertIsNotNone(ct_term_name_ar.item_metadata._start_date)
        self.assertEqual(ct_term_name_ar.item_metadata.version, "0.1")
        self.assertEqual(ct_term_name_ar.item_metadata.status, LibraryItemStatus.DRAFT)

    def test__approve__version_created(self):
        # given
        ct_term_name_ar = create_random_ct_term_name_ar()

        # when
        ct_term_name_ar.approve(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(ct_term_name_ar.item_metadata._end_date)
        self.assertIsNotNone(ct_term_name_ar.item_metadata._start_date)
        self.assertEqual(ct_term_name_ar.item_metadata.version, "1.0")
        self.assertEqual(ct_term_name_ar.item_metadata.status, LibraryItemStatus.FINAL)

    def test__create_new_version__version_created(self):
        # given
        ct_term_name_ar = create_random_ct_term_name_ar()
        ct_term_name_ar.approve(author_id=AUTHOR_ID)

        # when
        ct_term_name_ar.create_new_version(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(ct_term_name_ar.item_metadata._end_date)
        self.assertIsNotNone(ct_term_name_ar.item_metadata._start_date)
        self.assertEqual(ct_term_name_ar.item_metadata.version, "1.1")
        self.assertEqual(ct_term_name_ar.item_metadata.status, LibraryItemStatus.DRAFT)

    def test__edit_draft_version__version_created(self):
        # given
        ct_term_name_ar = create_random_ct_term_name_ar()

        ct_term_name_ar.approve(author_id="Test")
        ct_term_name_ar.create_new_version(author_id=AUTHOR_ID)

        # when
        ct_term_vo = create_random_ct_term_name_vo()
        ct_term_name_ar.edit_draft(
            term_uid=ct_term_name_ar.uid,
            author_id=AUTHOR_ID,
            change_description="Test",
            ct_term_vo=ct_term_vo,
            term_exists_by_name_in_codelists_callback=lambda x, y: False,
        )

        # then
        self.assertIsNone(ct_term_name_ar.item_metadata.end_date)
        self.assertIsNotNone(ct_term_name_ar.item_metadata.start_date)
        self.assertEqual(ct_term_name_ar.item_metadata.version, "1.2")
        self.assertEqual(ct_term_name_ar.item_metadata.status, LibraryItemStatus.DRAFT)
        self.assertEqual(ct_term_name_ar.item_metadata.author_id, AUTHOR_ID)
        self.assertEqual(ct_term_name_ar.item_metadata.change_description, "Test")
        self.assertEqual(ct_term_name_ar.name, ct_term_vo.name)
        self.assertEqual(
            ct_term_name_ar.ct_term_vo.name_sentence_case, ct_term_vo.name_sentence_case
        )
        self.assertListEqual(
            ct_term_name_ar.ct_term_vo.catalogue_names, ct_term_vo.catalogue_names
        )
