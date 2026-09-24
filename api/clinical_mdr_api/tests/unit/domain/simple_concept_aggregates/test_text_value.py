import unittest
from typing import Callable

from clinical_mdr_api.domains.concepts.simple_concepts.text_value import (
    TextValueAR,
    TextValueVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str


def create_random_text_value_vo() -> TextValueVO:
    name = random_str()
    random_text_value_vo = TextValueVO.from_repository_values(
        name=name,
        name_sentence_case=name.lower(),
        definition=random_str(),
        abbreviation=random_str(),
        is_template_parameter=True,
    )
    return random_text_value_vo


def create_random_text_value_ar(
    # pylint: disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> TextValueAR:
    random_text_value_ar = TextValueAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        simple_concept_vo=create_random_text_value_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
    )

    return random_text_value_ar


class TestTextValue(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        text_value_ar = create_random_text_value_ar()

        # then
        self.assertIsNone(text_value_ar.item_metadata._end_date)
        self.assertIsNotNone(text_value_ar.item_metadata._start_date)
        self.assertEqual(text_value_ar.item_metadata.version, "1.0")
        self.assertEqual(text_value_ar.item_metadata.status, LibraryItemStatus.FINAL)
