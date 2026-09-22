import unittest
from typing import Callable

from clinical_mdr_api.domains.concepts.simple_concepts.study_week import (
    StudyWeekAR,
    StudyWeekVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str


def create_random_study_week_vo() -> StudyWeekVO:
    random_study_week_vo = StudyWeekVO.from_input_values(
        value=1.23,
        definition=random_str(),
        abbreviation=random_str(),
        is_template_parameter=True,
    )
    return random_study_week_vo


def create_random_study_week_ar(
    # pylint: disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> StudyWeekAR:
    random_study_week_ar = StudyWeekAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        simple_concept_vo=create_random_study_week_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
    )

    return random_study_week_ar


class TestStudyWeek(unittest.TestCase):
    def test__init__ar_created(self):
        # pylint: disable=no-member
        # given

        # when
        study_week_ar = create_random_study_week_ar()

        # then
        self.assertIsNone(study_week_ar.item_metadata._end_date)
        self.assertIsNotNone(study_week_ar.item_metadata._start_date)
        self.assertEqual(study_week_ar.item_metadata.version, "1.0")
        self.assertEqual(study_week_ar.item_metadata.status, LibraryItemStatus.FINAL)
        self.assertEqual(
            study_week_ar.name, f"Week {str(study_week_ar.concept_vo.value)}"
        )
        self.assertEqual(
            study_week_ar.concept_vo.name_sentence_case,
            f"week {str(study_week_ar.concept_vo.value)}",
        )
