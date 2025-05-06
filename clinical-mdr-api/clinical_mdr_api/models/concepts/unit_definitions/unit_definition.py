from typing import Annotated, Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.models.concepts.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import SimpleTermModel
from clinical_mdr_api.models.utils import BaseModel


class UnitDefinitionModel(ConceptModel):
    convertible_unit: bool
    display_unit: bool
    master_unit: bool
    si_unit: bool
    us_conventional_unit: bool
    use_complex_unit_conversion: bool
    ct_units: list[SimpleTermModel]
    unit_subsets: list[SimpleTermModel]
    ucum: Annotated[
        SimpleTermModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    unit_dimension: Annotated[
        SimpleTermModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    legacy_code: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    use_molecular_weight: Annotated[
        bool | None, Field(json_schema_extra={"nullable": True})
    ] = None
    conversion_factor_to_master: Annotated[
        float | None, Field(json_schema_extra={"nullable": True})
    ] = None
    comment: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    definition: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    template_parameter: bool

    @classmethod
    def from_unit_definition_ar(
        cls,
        unit_definition_ar: UnitDefinitionAR,
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
    ) -> Self:
        ct_units = []
        for ct_unit in unit_definition_ar.concept_vo.ct_units:
            if ct_unit.name is None:
                controlled_terminology_unit = SimpleTermModel.from_ct_code(
                    c_code=ct_unit.uid, find_term_by_uid=find_term_by_uid
                )
            else:
                controlled_terminology_unit = SimpleTermModel(
                    term_uid=ct_unit.uid, name=ct_unit.name
                )
            ct_units.append(controlled_terminology_unit)
        if not any(ct_unit.name is None for ct_unit in ct_units):
            ct_units.sort(key=lambda item: item.name)

        unit_subsets = []
        for unit_subset in unit_definition_ar.concept_vo.unit_subsets:
            if unit_subset.name is None:
                controlled_terminology_subset = SimpleTermModel.from_ct_code(
                    c_code=unit_subset.uid, find_term_by_uid=find_term_by_uid
                )
            else:
                controlled_terminology_subset = SimpleTermModel(
                    term_uid=unit_subset.uid, name=unit_subset.name
                )
            unit_subsets.append(controlled_terminology_subset)
        if not any(unit_subset.name is None for unit_subset in unit_subsets):
            unit_subsets.sort(key=lambda item: item.name)

        if unit_definition_ar.concept_vo.ucum_name is None:
            ucum = SimpleTermModel.from_ct_code(
                c_code=unit_definition_ar.concept_vo.ucum_uid,
                find_term_by_uid=find_dictionary_term_by_uid,
            )
        else:
            ucum = SimpleTermModel(
                term_uid=unit_definition_ar.concept_vo.ucum_uid,
                name=unit_definition_ar.concept_vo.ucum_name,
            )

        if unit_definition_ar.concept_vo.unit_dimension_name is None:
            unit_dimension = SimpleTermModel.from_ct_code(
                c_code=unit_definition_ar.concept_vo.unit_dimension_uid,
                find_term_by_uid=find_term_by_uid,
            )
        else:
            unit_dimension = SimpleTermModel(
                term_uid=unit_definition_ar.concept_vo.unit_dimension_uid,
                name=unit_definition_ar.concept_vo.unit_dimension_name,
            )

        return UnitDefinitionModel(
            uid=unit_definition_ar.uid,
            name=unit_definition_ar.name,
            definition=unit_definition_ar.concept_vo.definition,
            ct_units=ct_units,
            unit_subsets=unit_subsets,
            ucum=ucum,
            convertible_unit=unit_definition_ar.concept_vo.convertible_unit,
            display_unit=unit_definition_ar.concept_vo.display_unit,
            master_unit=unit_definition_ar.concept_vo.master_unit,
            si_unit=unit_definition_ar.concept_vo.si_unit,
            us_conventional_unit=unit_definition_ar.concept_vo.us_conventional_unit,
            use_complex_unit_conversion=unit_definition_ar.concept_vo.use_complex_unit_conversion,
            legacy_code=unit_definition_ar.concept_vo.legacy_code,
            use_molecular_weight=unit_definition_ar.concept_vo.use_molecular_weight,
            conversion_factor_to_master=unit_definition_ar.concept_vo.conversion_factor_to_master,
            start_date=unit_definition_ar.item_metadata.start_date,
            end_date=unit_definition_ar.item_metadata.end_date,
            author_username=unit_definition_ar.item_metadata.author_username,
            status=unit_definition_ar.item_metadata.status.value,
            change_description=unit_definition_ar.item_metadata.change_description,
            library_name=unit_definition_ar.library.name,
            version=unit_definition_ar.item_metadata.version,
            unit_dimension=unit_dimension,
            comment=unit_definition_ar.concept_vo.comment,
            order=unit_definition_ar.concept_vo.order,
            template_parameter=unit_definition_ar.concept_vo.is_template_parameter,
        )


class UnitDefinitionPostInput(ConceptPostInput):
    convertible_unit: bool
    display_unit: bool
    master_unit: bool
    si_unit: bool
    us_conventional_unit: bool
    use_complex_unit_conversion: bool = False
    ct_units: list[str]
    unit_subsets: list[str] | None = []
    ucum: str | None = None
    unit_dimension: str | None = None
    legacy_code: str | None = None
    use_molecular_weight: bool | None = None
    conversion_factor_to_master: float | None = None
    comment: str | None = None
    order: int | None = None
    definition: str | None = None
    template_parameter: bool = False


class UnitDefinitionPatchInput(ConceptPatchInput):
    convertible_unit: bool | None = None
    display_unit: bool | None = None
    master_unit: bool | None = None
    si_unit: bool | None = None
    us_conventional_unit: bool | None = None
    use_complex_unit_conversion: bool | None = None
    ct_units: list[str] | None = []
    unit_subsets: list[str] | None = []
    ucum: str | None = None
    unit_dimension: str | None = None
    legacy_code: str | None = None
    use_molecular_weight: bool | None = None
    conversion_factor_to_master: float | None = None
    comment: str | None = None
    order: int | None = None
    definition: str | None = None
    template_parameter: bool | None = None


class UnitDefinitionSimpleModel(BaseModel):
    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    dimension_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
