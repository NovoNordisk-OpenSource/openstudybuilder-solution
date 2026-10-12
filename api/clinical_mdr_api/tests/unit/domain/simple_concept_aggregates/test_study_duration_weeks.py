import unittest
from collections.abc import Callable

from clinical_mdr_api.domains.concepts.simple_concepts.study_duration_weeks import (
    StudyDurationWeeksAR,
    StudyDurationWeeksVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str


def create_random_study_duration_weeks_vo() -> StudyDurationWeeksVO:
    random_study_duration_weeks_vo = StudyDurationWeeksVO.from_input_values(
        value=1.23,
        definition=random_str(),
        abbreviation=random_str(),
        is_template_parameter=True,
    )
    return random_study_duration_weeks_vo


def create_random_study_duration_weeks_ar(
    generate_uid_callback: Callable[[], str] = random_str,
    library: str = "Library",
    is_editable: bool = True,
) -> StudyDurationWeeksAR:
    random_study_duration_weeks_ar = StudyDurationWeeksAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        simple_concept_vo=create_random_study_duration_weeks_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
    )
    return random_study_duration_weeks_ar


class TestStudyDurationWeeks(unittest.TestCase):
    def test__init__ar_created(self):

        # given

        # when
        study_duration_weeks_ar = create_random_study_duration_weeks_ar()

        # then
        self.assertIsNone(study_duration_weeks_ar.item_metadata._end_date)
        self.assertIsNotNone(study_duration_weeks_ar.item_metadata._start_date)
        self.assertEqual(study_duration_weeks_ar.item_metadata.version, "1.0")
        self.assertEqual(
            study_duration_weeks_ar.item_metadata.status, LibraryItemStatus.FINAL
        )
        self.assertEqual(
            study_duration_weeks_ar.name,
            f"{study_duration_weeks_ar.concept_vo.value!s} weeks",
        )
        self.assertEqual(
            study_duration_weeks_ar.concept_vo.name_sentence_case,
            f"{study_duration_weeks_ar.concept_vo.value!s} weeks",
        )
