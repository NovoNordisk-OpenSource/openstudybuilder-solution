from dataclasses import dataclass
from typing import Self

from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
    NumericValueVO,
)


@dataclass(frozen=True)
class StudyDurationWeeksVO(NumericValueVO):
    @classmethod
    def from_input_values(
        cls,
        value: float,
        definition: str | None,
        abbreviation: str | None,
        is_template_parameter: bool,
    ) -> Self:
        value = cls.derive_value_property(value=value)
        simple_concept_vo = cls(
            name=f"{str(value)} weeks",
            value=value,
            name_sentence_case=f"{str(value)} weeks",
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=is_template_parameter,
        )

        return simple_concept_vo


class StudyDurationWeeksAR(NumericValueAR):
    _concept_vo: StudyDurationWeeksVO

    @property
    def concept_vo(self) -> StudyDurationWeeksVO:
        return self._concept_vo
