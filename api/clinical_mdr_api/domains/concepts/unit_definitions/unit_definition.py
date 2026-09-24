import math
from dataclasses import dataclass
from typing import AbstractSet, Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
    ObjectAction,
)
from clinical_mdr_api.utils import are_floats_equal, normalize_string
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    ValidationException,
)

CONCENTRATION_UNIT_DIMENSION_VALUE = "Concentration"


@dataclass
class CTTerm:
    uid: str
    name: str | None


@dataclass(frozen=True)
class UnitDefinitionValueVO(ConceptVO):
    ct_units: list[CTTerm]
    unit_subsets: list[CTTerm]
    ucum_uid: str | None
    unit_dimension_uid: str | None
    ucum_name: str | None
    unit_dimension_name: str | None
    convertible_unit: bool
    display_unit: bool
    master_unit: bool
    si_unit: bool
    us_conventional_unit: bool
    use_complex_unit_conversion: bool
    legacy_code: str | None
    use_molecular_weight: bool | None
    conversion_factor_to_master: float | None
    order: int | None
    comment: str | None

    @classmethod
    def from_input_values(
        cls,
        *,
        name: str,
        definition: str | None,
        convertible_unit: bool,
        display_unit: bool,
        master_unit: bool,
        si_unit: bool,
        us_conventional_unit: bool,
        use_complex_unit_conversion: bool,
        ct_units: list[str],
        unit_subsets: list[str],
        ucum_uid: str | None,
        unit_dimension_uid: str | None,
        legacy_code: str | None,
        use_molecular_weight: bool | None,
        conversion_factor_to_master: float | None,
        comment: str | None,
        order: int | None,
        unit_ct_uid_exists_callback: Callable[[str], bool],
        ucum_uid_exists_callback: Callable[[str], bool],
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
        is_template_parameter: bool,
    ) -> Self:
        ucum_uid = normalize_string(ucum_uid)
        unit_dimension_uid = normalize_string(unit_dimension_uid)

        ValidationException.raise_if(
            conversion_factor_to_master is not None
            and math.isnan(conversion_factor_to_master),
            msg="conversion factor to master if specified cannot be NaN value.",
        )

        ValidationException.raise_if(
            master_unit
            and (
                conversion_factor_to_master is None
                or not are_floats_equal(conversion_factor_to_master, 1.0)
            ),
            msg=f"conversion factor to master must be 1.0 for master unit (provided value: {conversion_factor_to_master})",
        )

        ValidationException.raise_if(
            unit_dimension_uid is not None and not find_term_by_uid(unit_dimension_uid),
            msg=f"Unknown CT dimension uid: {unit_dimension_uid}",
        )

        ValidationException.raise_if(
            unit_dimension_uid is not None
            and find_term_by_uid(unit_dimension_uid).name
            == CONCENTRATION_UNIT_DIMENSION_VALUE
            and use_molecular_weight is None,
            msg="use_molecular_weight must be provided with a value when unit dimension is set to 'Concentration'.",
        )

        for unit_ct_uid in ct_units:
            ValidationException.raise_if(
                unit_ct_uid is not None
                and not unit_ct_uid_exists_callback(unit_ct_uid),
                msg=f"Unknown CT unit uid: {unit_ct_uid}",
            )

        for unit_subset in unit_subsets:
            ValidationException.raise_if(
                unit_subset is not None
                and not unit_ct_uid_exists_callback(unit_subset),
                msg=f"Unknown Unit Subset uid: {unit_subset}",
            )

        ValidationException.raise_if(
            ucum_uid is not None and not ucum_uid_exists_callback(ucum_uid),
            msg=f"Unknown ucum uid: {ucum_uid}",
        )

        return cls.from_repository_values(
            name=normalize_string(name),
            definition=definition,
            ct_units=[CTTerm(uid=ct_unit, name=None) for ct_unit in ct_units],
            unit_subsets=[
                CTTerm(uid=unit_subset, name=None) for unit_subset in unit_subsets
            ],
            ucum_uid=ucum_uid,
            unit_dimension_uid=unit_dimension_uid,
            ucum_name=None,
            unit_dimension_name=None,
            convertible_unit=convertible_unit,
            display_unit=display_unit,
            master_unit=master_unit,
            si_unit=si_unit,
            us_conventional_unit=us_conventional_unit,
            use_complex_unit_conversion=use_complex_unit_conversion,
            legacy_code=normalize_string(legacy_code),
            use_molecular_weight=use_molecular_weight,
            conversion_factor_to_master=conversion_factor_to_master,
            order=order,
            comment=comment,
            is_template_parameter=is_template_parameter,
        )

    @classmethod
    def from_repository_values(
        cls,
        *,
        name: str,
        definition: str | None,
        convertible_unit: bool,
        display_unit: bool,
        master_unit: bool,
        si_unit: bool,
        us_conventional_unit: bool,
        use_complex_unit_conversion: bool,
        ct_units: list[CTTerm],
        unit_subsets: list[CTTerm],
        ucum_uid: str | None,
        unit_dimension_uid: str | None,
        ucum_name: str | None,
        unit_dimension_name: str | None,
        legacy_code: str | None,
        use_molecular_weight: bool | None,
        conversion_factor_to_master: float | None,
        order: int | None,
        comment: str | None,
        is_template_parameter: bool,
    ) -> Self:
        return cls(
            name=name,
            name_sentence_case=None,
            abbreviation=None,
            definition=definition,
            is_template_parameter=is_template_parameter,
            ct_units=ct_units,
            unit_subsets=unit_subsets,
            ucum_uid=ucum_uid,
            unit_dimension_uid=unit_dimension_uid,
            ucum_name=ucum_name,
            unit_dimension_name=unit_dimension_name,
            convertible_unit=convertible_unit,
            display_unit=display_unit,
            master_unit=master_unit,
            si_unit=si_unit,
            us_conventional_unit=us_conventional_unit,
            use_complex_unit_conversion=use_complex_unit_conversion is True,
            legacy_code=legacy_code,
            use_molecular_weight=use_molecular_weight,
            conversion_factor_to_master=conversion_factor_to_master,
            order=order,
            comment=comment,
        )


@dataclass
class UnitDefinitionAR(ConceptARBase):
    _concept_vo: UnitDefinitionValueVO

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        raise NotImplementedError("Possible actions retrieval not implemented.")

    @property
    def concept_vo(self) -> UnitDefinitionValueVO:
        return self._concept_vo

    @concept_vo.setter
    def concept_vo(self, value: UnitDefinitionValueVO) -> None:
        self._concept_vo = value

    @property
    def name(self) -> str:
        return self.concept_vo.name

    def create_new_version(self, author_id: str):
        super()._create_new_version(author_id)

    def edit_draft(
        self,
        *,
        author_id: str,
        change_description: str,
        new_unit_definition_value: UnitDefinitionValueVO | None = None,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        master_unit_exists_for_dimension_predicate: Callable[
            [str], bool
        ] = lambda _: True,
        unit_definition_exists_by_legacy_code: Callable[[str], bool] = lambda _: True,
    ) -> None:
        """
        Edits a draft version of the object, creating a new draft version.
        """

        if new_unit_definition_value.name is None:
            raise ValidationException(msg="Unit Definition name must be provided.")

        UnitDefinitionValueVO.duplication_check(
            [("name", new_unit_definition_value.name, self.name)],
            concept_exists_by_callback,
            "Unit Definition",
        )

        BusinessLogicException.raise_if(
            (
                new_unit_definition_value.legacy_code is not None
                and new_unit_definition_value.legacy_code != self.concept_vo.legacy_code
                and unit_definition_exists_by_legacy_code(
                    new_unit_definition_value.legacy_code
                )
            ),
            msg=f"Attempt to change Unit Definition legacy code into non-unique value: {new_unit_definition_value.legacy_code}",
        )

        BusinessLogicException.raise_if(
            (
                new_unit_definition_value.unit_dimension_uid is not None
                and new_unit_definition_value.master_unit
                and (
                    not self.concept_vo.master_unit
                    or new_unit_definition_value.unit_dimension_uid
                    != self.concept_vo.unit_dimension_uid
                )
                and master_unit_exists_for_dimension_predicate(
                    new_unit_definition_value.unit_dimension_uid
                )
            ),
            msg=f"Attempt to make '{self.uid}' another master unit in dimension '{new_unit_definition_value.unit_dimension_uid}'.",
        )

        if self._concept_vo != new_unit_definition_value:
            super()._edit_draft(
                author_id=author_id,
                change_description=normalize_string(change_description),
            )
            if new_unit_definition_value is None:
                raise BusinessLogicException(msg="UnitDefinitionVO is missing.")

            self._concept_vo = new_unit_definition_value

    @classmethod
    def from_input_values(
        cls,
        *,
        unit_definition_value: UnitDefinitionValueVO,
        author_id: str,
        library: LibraryVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        master_unit_exists_for_dimension_predicate: Callable[[str], bool],
        unit_definition_exists_by_legacy_code: Callable[[str], bool],
        uid_supplier: Callable[[], str] = lambda: "",
    ) -> Self:
        if unit_definition_value.name is None:
            raise ValidationException(msg="Unit Definition name must be provided.")

        UnitDefinitionValueVO.duplication_check(
            [("name", unit_definition_value.name, None)],
            concept_exists_by_callback,
            "Unit Definition",
        )

        AlreadyExistsException.raise_if(
            unit_definition_value.legacy_code is not None
            and unit_definition_exists_by_legacy_code(
                unit_definition_value.legacy_code
            ),
            "Unit Definition",
            unit_definition_value.legacy_code,
            "Legacy Code",
        )

        BusinessLogicException.raise_if(
            unit_definition_value.unit_dimension_uid is not None
            and unit_definition_value.master_unit
            and master_unit_exists_for_dimension_predicate(
                unit_definition_value.unit_dimension_uid
            ),
            msg=f"Attempt to create another master unit in dimension '{unit_definition_value.unit_dimension_uid}'.",
        )

        result: Self = cls._from_input_values(
            author_id=author_id,
            library=library,
            uid_supplier=uid_supplier,
            _concept_vo=unit_definition_value,
        )
        return result

    @classmethod
    def from_repository_values(
        cls,
        *,
        library: LibraryVO,
        uid: str,
        item_metadata: LibraryItemMetadataVO,
        unit_definition_value: UnitDefinitionValueVO,
    ) -> Self:
        result: Self = cls._from_repository_values(
            library=library,
            uid=uid,
            item_metadata=item_metadata,
            _concept_vo=unit_definition_value,
        )
        return result
