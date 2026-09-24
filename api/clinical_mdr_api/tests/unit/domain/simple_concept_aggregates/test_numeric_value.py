import unittest
from typing import Callable

from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
    NumericValueVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str


def create_random_numeric_value_vo() -> NumericValueVO:
    random_numeric_value_vo = NumericValueVO.from_input_values(
        value=1.23,
        definition=random_str(),
        abbreviation=random_str(),
        is_template_parameter=True,
    )
    return random_numeric_value_vo


def create_random_numeric_value_ar(
    # pylint: disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> NumericValueAR:
    random_numeric_value_ar = NumericValueAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        simple_concept_vo=create_random_numeric_value_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
    )

    return random_numeric_value_ar


class TestNumericValue(unittest.TestCase):
    def test__init__ar_created(self):
        # pylint: disable=no-member
        # given

        # when
        numeric_value_ar = create_random_numeric_value_ar()

        # then
        self.assertIsNone(numeric_value_ar.item_metadata._end_date)
        self.assertIsNotNone(numeric_value_ar.item_metadata._start_date)
        self.assertEqual(numeric_value_ar.item_metadata.version, "1.0")
        self.assertEqual(numeric_value_ar.item_metadata.status, LibraryItemStatus.FINAL)
        self.assertEqual(numeric_value_ar.name, str(numeric_value_ar.concept_vo.value))
        self.assertEqual(
            numeric_value_ar.concept_vo.name_sentence_case,
            str(numeric_value_ar.concept_vo.value),
        )
