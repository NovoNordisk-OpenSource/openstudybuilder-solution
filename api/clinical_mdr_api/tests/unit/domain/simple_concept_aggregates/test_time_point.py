import unittest
from typing import Callable
from unittest.mock import patch

from clinical_mdr_api.domain_repositories.concepts.simple_concepts.numeric_value_repository import (
    NumericValueRepository,
)
from clinical_mdr_api.domain_repositories.concepts.unit_definitions.unit_definition_repository import (
    UnitDefinitionRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_name_repository import (
    CTTermNameRepository,
)
from clinical_mdr_api.domains.concepts.simple_concepts.time_point import (
    TimePointAR,
    TimePointVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.simple_concept_aggregates.test_numeric_value import (
    create_random_numeric_value_ar,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID, random_str


class MockObject:
    def __init__(self):
        self._uid = random_str()
        self._name = random_str()

    @property
    def uid(self):
        return self._uid

    @property
    def name(self):
        return self._name


def create_random_time_point_vo(
    numeric_value, unit_definition, time_reference
) -> TimePointVO:
    random_time_point_vo = TimePointVO.from_input_values(
        name_sentence_case=random_str(),
        definition=random_str(),
        abbreviation=random_str(),
        is_template_parameter=True,
        numeric_value_uid=random_str(),
        unit_definition_uid=random_str(),
        time_reference_uid=random_str(),
        find_numeric_value_by_uid=lambda _: numeric_value,
        find_unit_definition_by_uid=lambda _: unit_definition,
        find_time_reference_by_uid=lambda _: time_reference,
    )
    return random_time_point_vo


def create_random_time_point_ar(
    numeric_value,
    unit_definition,
    time_reference,
    # pylint: disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> TimePointAR:
    random_time_point_ar = TimePointAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        simple_concept_vo=create_random_time_point_vo(
            numeric_value=numeric_value,
            unit_definition=unit_definition,
            time_reference=time_reference,
        ),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
    )

    return random_time_point_ar


class TestTimePoint(unittest.TestCase):
    @patch(NumericValueRepository.__module__)
    @patch(UnitDefinitionRepository.__module__)
    @patch(CTTermNameRepository.__module__)
    def test__init__ar_created(
        self,
        unit_definition_repository_mock,
        numeric_value_repository_mock,
        ct_term_name_repository_mock,
    ):
        # given
        unit_definition_mock = MockObject()
        time_reference_mock = MockObject()
        numeric_value_mock = create_random_numeric_value_ar()
        unit_definition_repository_mock.find_by_uid_2.return_value = (
            unit_definition_mock
        )
        numeric_value_repository_mock.find_by_uid_2.return_value = numeric_value_mock
        ct_term_name_repository_mock.find_by_uid.return_value = time_reference_mock
        # when
        time_point_ar = create_random_time_point_ar(
            numeric_value=numeric_value_mock,
            unit_definition=unit_definition_mock,
            time_reference=time_reference_mock,
        )

        # then
        self.assertIsNone(time_point_ar.item_metadata._end_date)
        self.assertIsNotNone(time_point_ar.item_metadata._start_date)
        self.assertEqual(time_point_ar.item_metadata.version, "1.0")
        self.assertEqual(time_point_ar.item_metadata.status, LibraryItemStatus.FINAL)
        self.assertEqual(
            time_point_ar.name,
            f"{numeric_value_mock.name} {unit_definition_mock.name} after {time_reference_mock.name}",
        )
