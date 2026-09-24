from datetime import datetime
from typing import Annotated, Callable, Self

from pydantic import Field, StrictBool

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_term import (
    CTSimpleCodelistTermAR,
)
from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.models.concepts.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCodelistTermModel,
    SimpleTermModel,
)
from clinical_mdr_api.models.utils import BaseModel
from common.config import settings


class UnitDefinitionModel(ConceptModel):
    convertible_unit: Annotated[bool, Field()]
    display_unit: Annotated[bool, Field()]
    master_unit: Annotated[bool, Field()]
    si_unit: Annotated[bool, Field()]
    us_conventional_unit: Annotated[bool, Field()]
    use_complex_unit_conversion: Annotated[bool, Field()]
    ct_units: Annotated[list[SimpleCodelistTermModel], Field()]
    unit_subsets: Annotated[list[SimpleCodelistTermModel], Field()]
    ucum: Annotated[
        SimpleTermModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    unit_dimension: Annotated[
        SimpleCodelistTermModel | None, Field(json_schema_extra={"nullable": True})
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
    template_parameter: Annotated[bool, Field()]

    @classmethod
    def from_unit_definition_ar(
        cls,
        unit_definition_ar: UnitDefinitionAR,
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_codelist_term_by_uid_and_submission_value: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
    ) -> Self:
        ct_units = []
        for ct_unit in unit_definition_ar.concept_vo.ct_units:
            controlled_terminology_unit = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=ct_unit.uid,
                codelist_submission_value=settings.unit_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submission_value,
            )
            if controlled_terminology_unit is not None:
                ct_units.append(controlled_terminology_unit)
        if not any(ct_unit.term_name is None for ct_unit in ct_units):
            ct_units.sort(key=lambda item: item.term_name)

        unit_subsets = []
        for unit_subset in unit_definition_ar.concept_vo.unit_subsets:
            unit_subset_term = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=unit_subset.uid,
                codelist_submission_value=settings.unit_subset_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submission_value,
            )
            if unit_subset_term is not None:
                unit_subsets.append(unit_subset_term)
        if not any(unit_subset.term_name is None for unit_subset in unit_subsets):
            unit_subsets.sort(key=lambda item: item.term_name)

        if unit_definition_ar.concept_vo.ucum_name is None:
            ucum = SimpleTermModel.from_ct_code(
                c_code=unit_definition_ar.concept_vo.ucum_uid,
                find_term_by_uid=find_dictionary_term_by_uid,
            )
        else:
            ucum = SimpleTermModel(
                term_uid=unit_definition_ar.concept_vo.ucum_uid or "",
                name=unit_definition_ar.concept_vo.ucum_name,
            )

        # if unit_definition_ar.concept_vo.unit_dimension_name is None:
        #    unit_dimension = SimpleTermModel.from_ct_code(
        #        c_code=unit_definition_ar.concept_vo.unit_dimension_uid,
        #        find_term_by_uid=find_term_by_uid,
        #    )
        # else:
        unit_dimension = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
            term_uid=unit_definition_ar.concept_vo.unit_dimension_uid,
            codelist_submission_value=settings.unit_dimension_cl_submval,
            find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submission_value,
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
    convertible_unit: Annotated[StrictBool, Field()]
    display_unit: Annotated[StrictBool, Field()]
    master_unit: Annotated[StrictBool, Field()]
    si_unit: Annotated[StrictBool, Field()]
    us_conventional_unit: Annotated[StrictBool, Field()]
    use_complex_unit_conversion: Annotated[StrictBool, Field()] = False
    ct_units: Annotated[list[str], Field()]
    unit_subsets: list[str] = Field(default_factory=list)
    ucum: Annotated[str | None, Field()] = None
    unit_dimension: Annotated[str | None, Field()] = None
    legacy_code: Annotated[str | None, Field()] = None
    use_molecular_weight: Annotated[StrictBool, Field()] = False
    conversion_factor_to_master: Annotated[float | None, Field()] = None
    comment: Annotated[str | None, Field()] = None
    order: Annotated[int | None, Field()] = None
    definition: Annotated[str | None, Field()] = None
    template_parameter: Annotated[StrictBool, Field()] = False


class UnitDefinitionPatchInput(ConceptPatchInput):
    convertible_unit: Annotated[StrictBool, Field()] = False
    display_unit: Annotated[StrictBool, Field()] = False
    master_unit: Annotated[StrictBool, Field()] = False
    si_unit: Annotated[StrictBool, Field()] = False
    us_conventional_unit: Annotated[StrictBool, Field()] = False
    use_complex_unit_conversion: Annotated[StrictBool, Field()] = False
    ct_units: list[str] = Field(default_factory=list)
    unit_subsets: list[str] = Field(default_factory=list)
    ucum: Annotated[str | None, Field()] = None
    unit_dimension: Annotated[str | None, Field()] = None
    legacy_code: Annotated[str | None, Field()] = None
    use_molecular_weight: Annotated[StrictBool, Field()] = False
    conversion_factor_to_master: Annotated[float | None, Field()] = None
    comment: Annotated[str | None, Field()] = None
    order: Annotated[int | None, Field()] = None
    definition: Annotated[str | None, Field()] = None
    template_parameter: Annotated[StrictBool, Field()] = False


class UnitDefinitionSimpleModel(BaseModel):
    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    dimension_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class UnitDefinitionModelVersion(UnitDefinitionModel):
    """
    Class for storing UnitDefinitionModel and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
