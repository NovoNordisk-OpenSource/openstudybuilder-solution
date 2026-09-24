import unittest
from typing import Callable

from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameAR,
    CTCodelistNameVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str


def create_random_ct_codelist_name_vo(catalogue: str = "Catalogue") -> CTCodelistNameVO:
    random_ct_codelist_name_vo = CTCodelistNameVO.from_repository_values(
        catalogue_names=[catalogue], name=random_str(), is_template_parameter=False
    )
    return random_ct_codelist_name_vo


def create_random_ct_codelist_name_ar(
    # pylint: disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
    catalogue: str = "Catalogue",
) -> CTCodelistNameAR:
    random_ct_codelist_name_ar = CTCodelistNameAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        ct_codelist_name_vo=create_random_ct_codelist_name_vo(catalogue=catalogue),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
    )
    return random_ct_codelist_name_ar


class TestCTCodelistNameAR(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        ct_codelist_name_ar = create_random_ct_codelist_name_ar()

        # then
        self.assertIsNone(ct_codelist_name_ar.item_metadata._end_date)
        self.assertIsNotNone(ct_codelist_name_ar.item_metadata._start_date)
        self.assertEqual(ct_codelist_name_ar.item_metadata.version, "0.1")
        self.assertEqual(
            ct_codelist_name_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__approve__version_created(self):
        # given
        ct_codelist_name_ar = create_random_ct_codelist_name_ar()

        # when
        ct_codelist_name_ar.approve(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(ct_codelist_name_ar.item_metadata._end_date)
        self.assertIsNotNone(ct_codelist_name_ar.item_metadata._start_date)
        self.assertEqual(ct_codelist_name_ar.item_metadata.version, "1.0")
        self.assertEqual(
            ct_codelist_name_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__create_new_version__version_created(self):
        # given
        ct_codelist_name_ar = create_random_ct_codelist_name_ar()
        ct_codelist_name_ar.approve(author_id=AUTHOR_ID)

        # when
        ct_codelist_name_ar.create_new_version(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(ct_codelist_name_ar.item_metadata._end_date)
        self.assertIsNotNone(ct_codelist_name_ar.item_metadata._start_date)
        self.assertEqual(ct_codelist_name_ar.item_metadata.version, "1.1")
        self.assertEqual(
            ct_codelist_name_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__edit_draft_version__version_created(self):
        # given
        ct_codelist_name_ar = create_random_ct_codelist_name_ar()

        ct_codelist_name_ar.approve(author_id="Test")
        ct_codelist_name_ar.create_new_version(author_id=AUTHOR_ID)

        # when
        codelist_name_vo = create_random_ct_codelist_name_vo()
        ct_codelist_name_ar.edit_draft(
            author_id=AUTHOR_ID,
            change_description="Test",
            ct_codelist_vo=codelist_name_vo,
            codelist_exists_by_name_callback=lambda _: False,
        )

        # then
        self.assertIsNone(ct_codelist_name_ar.item_metadata.end_date)
        self.assertIsNotNone(ct_codelist_name_ar.item_metadata.start_date)
        self.assertEqual(ct_codelist_name_ar.item_metadata.version, "1.2")
        self.assertEqual(
            ct_codelist_name_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )
        self.assertEqual(ct_codelist_name_ar.item_metadata.author_id, AUTHOR_ID)
        self.assertEqual(ct_codelist_name_ar.item_metadata.change_description, "Test")
        self.assertEqual(ct_codelist_name_ar.name, codelist_name_vo.name)
        self.assertEqual(
            ct_codelist_name_ar.ct_codelist_vo.is_template_parameter,
            codelist_name_vo.is_template_parameter,
        )
        self.assertListEqual(
            ct_codelist_name_ar.ct_codelist_vo.catalogue_names,
            codelist_name_vo.catalogue_names,
        )
