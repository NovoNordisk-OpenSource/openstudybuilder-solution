import unittest
from collections.abc import Callable

from clinical_mdr_api.domains.concepts.simple_concepts.study_day import (
    StudyDayAR,
    StudyDayVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str


def create_random_study_day_vo() -> StudyDayVO:
    return StudyDayVO.from_input_values(
        value=1.23,
        definition=random_str(),
        abbreviation=random_str(),
        is_template_parameter=True,
    )


def create_random_study_day_ar(
    generate_uid_callback: Callable[[], str] = random_str,
    library: str = "Library",
    is_editable: bool = True,
) -> StudyDayAR:
    return StudyDayAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        simple_concept_vo=create_random_study_day_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
    )


class TestStudyDay(unittest.TestCase):
    def test__init__ar_created(self):

        # given

        # when
        study_day_ar = create_random_study_day_ar()

        # then
        self.assertIsNone(study_day_ar.item_metadata._end_date)
        self.assertIsNotNone(study_day_ar.item_metadata._start_date)
        self.assertEqual(study_day_ar.item_metadata.version, "1.0")
        self.assertEqual(study_day_ar.item_metadata.status, LibraryItemStatus.FINAL)
        self.assertEqual(study_day_ar.name, f"Day {study_day_ar.concept_vo.value!s}")
        self.assertEqual(
            study_day_ar.concept_vo.name_sentence_case,
            f"day {study_day_ar.concept_vo.value!s}",
        )
