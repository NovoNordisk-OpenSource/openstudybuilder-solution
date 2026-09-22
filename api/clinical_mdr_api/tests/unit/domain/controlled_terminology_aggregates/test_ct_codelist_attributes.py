import unittest

from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
    CTCodelistAttributesVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str


def create_random_ct_codelist_attributes_vo(
    catalogue: str = "Catalogue",
    submission_value: str | None = None,
) -> CTCodelistAttributesVO:
    if submission_value is None:
        submission_value = random_str()
    random_ct_codelist_attributes_vo = CTCodelistAttributesVO.from_repository_values(
        catalogue_names=[catalogue],
        name=random_str(),
        parent_codelist_uid=None,
        child_codelist_uids=[],
        submission_value=submission_value,
        preferred_term=random_str(),
        definition=random_str(),
        extensible=True,
    )
    return random_ct_codelist_attributes_vo


def create_random_ct_codelist_attributes_ar(
    library: str = "Library",
    is_editable: bool = True,
    catalogue: str = "Catalogue",
    # pylint: disable=unnecessary-lambda
    generate_uid_callback=lambda: random_str(),
) -> CTCodelistAttributesAR:
    random_ct_codelist_attributes_ar = CTCodelistAttributesAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        ct_codelist_attributes_vo=create_random_ct_codelist_attributes_vo(
            catalogue=catalogue
        ),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
    )
    return random_ct_codelist_attributes_ar


class TestCTCodelistAttributeAR(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        ct_codelist_attributes_ar = create_random_ct_codelist_attributes_ar()

        # then
        self.assertIsNotNone(ct_codelist_attributes_ar.ct_codelist_vo.name)
        self.assertGreater(
            len(ct_codelist_attributes_ar.ct_codelist_vo.catalogue_names), 0
        )
        self.assertIsNotNone(ct_codelist_attributes_ar.ct_codelist_vo.submission_value)
        self.assertIsNotNone(ct_codelist_attributes_ar.ct_codelist_vo.preferred_term)
        self.assertIsNotNone(ct_codelist_attributes_ar.ct_codelist_vo.definition)
        self.assertIsNotNone(ct_codelist_attributes_ar.ct_codelist_vo.extensible)
        self.assertIsNone(ct_codelist_attributes_ar.item_metadata._end_date)
        self.assertIsNotNone(ct_codelist_attributes_ar.item_metadata._start_date)
        self.assertEqual(ct_codelist_attributes_ar.item_metadata.version, "0.1")
        self.assertEqual(
            ct_codelist_attributes_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__approve__version_created(self):
        # given
        ct_codelist_attributes_ar = create_random_ct_codelist_attributes_ar()

        # when
        ct_codelist_attributes_ar.approve(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(ct_codelist_attributes_ar.item_metadata._end_date)
        self.assertIsNotNone(ct_codelist_attributes_ar.item_metadata._start_date)
        self.assertEqual(ct_codelist_attributes_ar.item_metadata.version, "1.0")
        self.assertEqual(
            ct_codelist_attributes_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__create_new_version__version_created(self):
        # given
        ct_codelist_attributes_ar = create_random_ct_codelist_attributes_ar()
        ct_codelist_attributes_ar.approve(author_id=AUTHOR_ID)

        # when
        ct_codelist_attributes_ar.create_new_version(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(ct_codelist_attributes_ar.item_metadata._end_date)
        self.assertIsNotNone(ct_codelist_attributes_ar.item_metadata._start_date)
        self.assertEqual(ct_codelist_attributes_ar.item_metadata.version, "1.1")
        self.assertEqual(
            ct_codelist_attributes_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__edit_draft_version__version_created(self):
        # given
        ct_codelist_attributes_ar = create_random_ct_codelist_attributes_ar()

        ct_codelist_attributes_ar.approve(author_id="Test")
        ct_codelist_attributes_ar.create_new_version(author_id=AUTHOR_ID)

        # when
        codelist_name_vo = create_random_ct_codelist_attributes_vo()
        ct_codelist_attributes_ar.edit_draft(
            author_id=AUTHOR_ID,
            change_description="Test",
            ct_codelist_vo=codelist_name_vo,
            codelist_exists_by_name_callback=lambda _: False,
            codelist_exists_by_submission_value_callback=lambda _: False,
        )

        # then
        self.assertIsNone(ct_codelist_attributes_ar.item_metadata.end_date)
        self.assertIsNotNone(ct_codelist_attributes_ar.item_metadata.start_date)
        self.assertEqual(ct_codelist_attributes_ar.item_metadata.version, "1.2")
        self.assertEqual(
            ct_codelist_attributes_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )
        self.assertEqual(ct_codelist_attributes_ar.item_metadata.author_id, AUTHOR_ID)
        self.assertEqual(
            ct_codelist_attributes_ar.item_metadata.change_description, "Test"
        )
        self.assertEqual(ct_codelist_attributes_ar.name, codelist_name_vo.name)
        self.assertListEqual(
            ct_codelist_attributes_ar.ct_codelist_vo.catalogue_names,
            codelist_name_vo.catalogue_names,
        )
        self.assertEqual(
            ct_codelist_attributes_ar.ct_codelist_vo.submission_value,
            codelist_name_vo.submission_value,
        )
        self.assertEqual(
            ct_codelist_attributes_ar.ct_codelist_vo.preferred_term,
            codelist_name_vo.preferred_term,
        )
        self.assertEqual(
            ct_codelist_attributes_ar.ct_codelist_vo.definition,
            codelist_name_vo.definition,
        )
        self.assertEqual(
            ct_codelist_attributes_ar.ct_codelist_vo.extensible,
            codelist_name_vo.extensible,
        )
