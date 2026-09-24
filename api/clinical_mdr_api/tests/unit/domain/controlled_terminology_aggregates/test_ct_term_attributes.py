import unittest

from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import (
    AUTHOR_ID,
    random_opt_str,
    random_str,
)


def create_random_ct_term_attributes_vo() -> CTTermAttributesVO:
    random_ct_term_attributes_vo = CTTermAttributesVO.from_repository_values(
        catalogue_names=[random_str()],
        concept_id=random_opt_str(),
        preferred_term=random_str(),
        definition=random_str(),
    )
    return random_ct_term_attributes_vo


def create_random_ct_term_attributes_ar(
    library: str = "Library", is_editable: bool = True
) -> CTTermAttributesAR:
    random_ct_term_attributes_ar = CTTermAttributesAR.from_input_values(
        # pylint: disable=unnecessary-lambda
        generate_uid_callback=lambda: random_str(),
        ct_term_attributes_vo=create_random_ct_term_attributes_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
    )
    return random_ct_term_attributes_ar


class TestCTTermAttributesAR(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        ct_term_attributes_ar = create_random_ct_term_attributes_ar()

        # then
        self.assertIsNone(ct_term_attributes_ar.item_metadata._end_date)
        self.assertIsNotNone(ct_term_attributes_ar.item_metadata._start_date)
        self.assertEqual(ct_term_attributes_ar.item_metadata.version, "0.1")
        self.assertEqual(
            ct_term_attributes_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__approve__version_created(self):
        # given
        ct_term_attributes_ar = create_random_ct_term_attributes_ar()

        # when
        ct_term_attributes_ar.approve(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(ct_term_attributes_ar.item_metadata._end_date)
        self.assertIsNotNone(ct_term_attributes_ar.item_metadata._start_date)
        self.assertEqual(ct_term_attributes_ar.item_metadata.version, "1.0")
        self.assertEqual(
            ct_term_attributes_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__create_new_version__version_created(self):
        # given
        ct_term_attributes_ar = create_random_ct_term_attributes_ar()
        ct_term_attributes_ar.approve(author_id=AUTHOR_ID)

        # when
        ct_term_attributes_ar.create_new_version(author_id=AUTHOR_ID)

        # then
        self.assertIsNone(ct_term_attributes_ar.item_metadata._end_date)
        self.assertIsNotNone(ct_term_attributes_ar.item_metadata._start_date)
        self.assertEqual(ct_term_attributes_ar.item_metadata.version, "1.1")
        self.assertEqual(
            ct_term_attributes_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__edit_draft_version__version_created(self):
        # given
        ct_term_attributes_ar = create_random_ct_term_attributes_ar()

        ct_term_attributes_ar.approve(author_id="Test")
        ct_term_attributes_ar.create_new_version(author_id=AUTHOR_ID)

        # when
        ct_term_vo = create_random_ct_term_attributes_vo()
        ct_term_attributes_ar.edit_draft(
            author_id=AUTHOR_ID,
            change_description="Test",
            ct_term_vo=ct_term_vo,
        )

        # then
        self.assertIsNone(ct_term_attributes_ar.item_metadata.end_date)
        self.assertIsNotNone(ct_term_attributes_ar.item_metadata.start_date)
        self.assertEqual(ct_term_attributes_ar.item_metadata.version, "1.2")
        self.assertEqual(
            ct_term_attributes_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )
        self.assertEqual(ct_term_attributes_ar.item_metadata.author_id, AUTHOR_ID)
        self.assertEqual(ct_term_attributes_ar.item_metadata.change_description, "Test")
        self.assertEqual(
            ct_term_attributes_ar.ct_term_vo.preferred_term, ct_term_vo.preferred_term
        )
        self.assertEqual(
            ct_term_attributes_ar.ct_term_vo.definition, ct_term_vo.definition
        )
        self.assertListEqual(
            ct_term_attributes_ar.ct_term_vo.catalogue_names, ct_term_vo.catalogue_names
        )
