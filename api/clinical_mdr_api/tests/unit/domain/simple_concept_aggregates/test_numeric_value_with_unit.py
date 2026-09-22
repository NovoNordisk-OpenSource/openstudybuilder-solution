import unittest
from typing import Callable
from unittest.mock import patch

from clinical_mdr_api.domain_repositories.concepts.unit_definitions.unit_definition_repository import (
    UnitDefinitionRepository,
)
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value_with_unit import (
    NumericValueWithUnitAR,
    NumericValueWithUnitVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
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


def create_random_numeric_value_vo(unit_definition) -> NumericValueWithUnitVO:
    random_numeric_value_vo = NumericValueWithUnitVO.from_input_values(
        value=1.23,
        definition=random_str(),
        abbreviation=random_str(),
        is_template_parameter=True,
        unit_definition_uid=unit_definition.uid,
        find_unit_definition_by_uid=lambda _: unit_definition,
    )
    return random_numeric_value_vo


def create_random_numeric_value_ar(
    unit_definition,
    # pylint: disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> NumericValueWithUnitAR:
    random_numeric_value_ar = NumericValueWithUnitAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        simple_concept_vo=create_random_numeric_value_vo(unit_definition),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author_id=AUTHOR_ID,
        find_uid_by_name_callback=lambda _: unit_definition,
        find_uid_by_value_and_unit_callback=lambda _, __: random_str(),
    )

    return random_numeric_value_ar


class TestNumericValueWithUnit(unittest.TestCase):
    @patch(UnitDefinitionRepository.__module__)
    def test__init__ar_created(
        self,
        unit_definition_repository_mock,
    ):
        # pylint: disable=no-member
        # given
        unit_definition_mock = MockObject()
        unit_definition_repository_mock.find_by_uid_2.return_value = (
            unit_definition_mock
        )

        # when
        numeric_value_ar = create_random_numeric_value_ar(
            unit_definition=unit_definition_mock
        )

        # then
        self.assertIsNone(numeric_value_ar.item_metadata._end_date)
        self.assertIsNotNone(numeric_value_ar.item_metadata._start_date)
        self.assertEqual(numeric_value_ar.item_metadata.version, "1.0")
        self.assertEqual(numeric_value_ar.item_metadata.status, LibraryItemStatus.FINAL)
        self.assertEqual(
            numeric_value_ar.concept_vo.unit_definition_uid, unit_definition_mock.uid
        )
        self.assertEqual(
            numeric_value_ar.name,
            f"{numeric_value_ar.concept_vo.value} [{unit_definition_mock.uid}]",
        )
        self.assertEqual(
            numeric_value_ar.concept_vo.name_sentence_case,
            str(numeric_value_ar.concept_vo.value),
        )
