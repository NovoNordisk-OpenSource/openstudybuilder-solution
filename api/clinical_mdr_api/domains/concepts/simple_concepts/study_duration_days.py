from dataclasses import dataclass
from typing import Self

from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
    NumericValueVO,
)


@dataclass(frozen=True)
class StudyDurationDaysVO(NumericValueVO):
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
            name=f"{str(value)} days",
            value=value,
            name_sentence_case=f"{str(value)} days",
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=is_template_parameter,
        )

        return simple_concept_vo


class StudyDurationDaysAR(NumericValueAR):
    _concept_vo: StudyDurationDaysVO

    @property
    def concept_vo(self) -> StudyDurationDaysVO:
        return self._concept_vo
