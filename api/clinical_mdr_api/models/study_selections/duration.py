from typing import Annotated, Any, Callable, Self

from pydantic import ConfigDict, Field

from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionSimpleModel,
)
from clinical_mdr_api.models.utils import (
    BaseModel,
    from_duration_object_to_value_and_unit,
)


class DurationJsonModel(BaseModel):
    model_config = ConfigDict(title="Duration model to store ISO8601 duration")

    duration_value: Annotated[int | None, Field()] = None
    duration_unit_code: Annotated[UnitDefinitionSimpleModel | None, Field()] = None

    @classmethod
    def from_duration_object(
        cls,
        duration: Any,
        find_all_study_time_units: Callable[[str], tuple[list[UnitDefinitionAR], int]],
    ) -> Self:
        duration_value, duration_unit = from_duration_object_to_value_and_unit(
            duration, find_all_study_time_units
        )

        return cls(
            duration_value=duration_value,
            duration_unit_code=(
                UnitDefinitionSimpleModel(
                    uid=duration_unit.uid, name=duration_unit.name
                )
                if duration_unit
                else None
            ),
        )
