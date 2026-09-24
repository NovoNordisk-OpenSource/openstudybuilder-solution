from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
    NumericValueVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.simple_concept import (
    SimpleConceptVO,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from common.exceptions import BusinessLogicException


@dataclass(frozen=True)
class NumericValueWithUnitVO(NumericValueVO):
    unit_definition_uid: str

    @classmethod
    def derive_value_property(cls, value):
        return int(value) if value.is_integer() else value

    @classmethod
    def from_repository_values(
        cls,
        value: float,
        definition: str | None,
        abbreviation: str | None,
        is_template_parameter: bool,
        unit_definition_uid: str,
    ) -> Self:
        value = cls.derive_value_property(value=value)
        simple_concept_vo = cls(
            name=str(value),
            value=value,
            name_sentence_case=str(value).lower(),
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=is_template_parameter,
            unit_definition_uid=unit_definition_uid,
        )

        return simple_concept_vo

    @classmethod
    def from_input_values(
        cls,
        value: float,
        definition: str | None,
        abbreviation: str | None,
        is_template_parameter: bool,
        find_unit_definition_by_uid: Callable[[str], UnitDefinitionAR],
        unit_definition_uid: str,
    ) -> Self:
        unit_definition = find_unit_definition_by_uid(unit_definition_uid)
        BusinessLogicException.raise_if(
            unit_definition is None,
            msg=f"{cls.__name__} tried to connect to non-existent Unit Definition with UID '{unit_definition_uid}'.",
        )
        value = cls.derive_value_property(value=value)
        simple_concept_vo = cls(
            name=f"{value} [{unit_definition_uid}]",
            value=value,
            name_sentence_case=str(value).lower(),
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=is_template_parameter,
            unit_definition_uid=unit_definition_uid,
        )

        return simple_concept_vo


class NumericValueWithUnitAR(NumericValueAR):
    _concept_vo: NumericValueWithUnitVO

    @property
    def concept_vo(self) -> NumericValueWithUnitVO:
        return self._concept_vo

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        simple_concept_vo: SimpleConceptVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = lambda: None,
        find_uid_by_name_callback: Callable[[str], str | None] = lambda _: None,
        find_uid_by_value_and_unit_callback: (
            Callable[[float, str], str | None] | None
        ) = None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO(
            _change_description="Initial version",
            _status=LibraryItemStatus.FINAL,
            _author_id=author_id,
            _start_date=datetime.now(timezone.utc),
            _end_date=None,
            _major_version=1,
            _minor_version=0,
        )

        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )

        if find_uid_by_value_and_unit_callback:
            # Check whether simple concept with the same value and unit already exists. If yes, return its uid, otherwise None.
            simple_concept_uid = find_uid_by_value_and_unit_callback(
                getattr(simple_concept_vo, "value"),
                getattr(simple_concept_vo, "unit_definition_uid"),
            )
        else:
            # Check whether simple concept with the same name already exits. If yes, return its uid, otherwise None.
            simple_concept_uid = None
            if simple_concept_vo.name is not None:
                simple_concept_uid = find_uid_by_name_callback(simple_concept_vo.name)

        simple_concept_ar = cls(
            _uid=(
                generate_uid_callback()
                if simple_concept_uid is None
                else simple_concept_uid
            ),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=simple_concept_vo,
        )
        return simple_concept_ar
