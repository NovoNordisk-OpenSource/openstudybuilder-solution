from datetime import datetime
from typing import Annotated, Callable, Self, overload

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.active_substance import ActiveSubstanceAR
from clinical_mdr_api.domains.concepts.pharmaceutical_product import (
    PharmaceuticalProductAR,
)
from clinical_mdr_api.domains.concepts.simple_concepts.lag_time import LagTimeAR
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value_with_unit import (
    NumericValueWithUnitAR,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_term import (
    CTSimpleCodelistTermAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domains.dictionaries.dictionary_term_substance import (
    DictionaryTermSubstanceAR,
)
from clinical_mdr_api.models.concepts.active_substance import SimpleActiveSubstance
from clinical_mdr_api.models.concepts.concept import (
    SimpleLagTime,
    SimpleNumericValueWithUnit,
    VersionProperties,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCodelistTermModel,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel
from common.config import settings


class Ingredient(BaseModel):
    external_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    formulation_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    active_substance: Annotated[SimpleActiveSubstance, Field()]
    strength: Annotated[
        SimpleNumericValueWithUnit | None, Field(json_schema_extra={"nullable": True})
    ] = None
    half_life: Annotated[
        SimpleNumericValueWithUnit | None, Field(json_schema_extra={"nullable": True})
    ] = None
    lag_times: list[SimpleLagTime] = Field(default_factory=list)


class IngredientCreateInput(PostInputModel):
    active_substance_uid: Annotated[str, Field(min_length=1)]
    formulation_name: Annotated[str | None, Field(min_length=1)] = None
    external_id: Annotated[str | None, Field(min_length=1)] = None
    strength_uid: Annotated[str | None, Field(min_length=1)] = None
    half_life_uid: Annotated[str | None, Field(min_length=1)] = None
    lag_time_uids: list[str] = Field(default_factory=list)


class IngredientEditInput(PatchInputModel):
    active_substance_uid: Annotated[str | None, Field(min_length=1)] = None
    formulation_name: Annotated[str | None, Field(min_length=1)] = None
    external_id: Annotated[str | None, Field(min_length=1)] = None
    strength_uid: Annotated[str | None, Field(min_length=1)] = None
    half_life_uid: Annotated[str | None, Field(min_length=1)] = None
    lag_time_uids: Annotated[list[str] | None, Field()] = None


class Formulation(BaseModel):
    external_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    ingredients: list[Ingredient] = Field(default_factory=list)


class FormulationCreateInput(PostInputModel):
    external_id: Annotated[str | None, Field(min_length=1)] = None
    ingredients: Annotated[list[IngredientCreateInput] | None, Field()] = None


class FormulationEditInput(PatchInputModel):
    external_id: Annotated[str | None, Field(min_length=1)] = None
    ingredients: list[IngredientEditInput] = Field(default_factory=list)


class PharmaceuticalProduct(VersionProperties):
    uid: Annotated[str, Field()]
    derived_name: Annotated[str, Field()] = ""

    external_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    library_name: Annotated[str, Field()]

    dosage_forms: Annotated[list[SimpleCodelistTermModel] | None, Field()]
    routes_of_administration: Annotated[list[SimpleCodelistTermModel] | None, Field()]
    formulations: Annotated[list[Formulation], Field()]

    possible_actions: Annotated[
        list[str],
        Field(
            description=(
                "Holds those actions that can be performed on PharmaceuticalProducts. "
                "Actions are: 'approve', 'edit', 'new_version'."
            )
        ),
    ]

    @classmethod
    def from_pharmaceutical_product_ar(
        cls,
        pharmaceutical_product_ar: PharmaceuticalProductAR,
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
        find_numeric_value_by_uid: Callable[[str], NumericValueWithUnitAR | None],
        find_lag_time_by_uid: Callable[[str], LagTimeAR | None],
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_active_substance_by_uid: Callable[[str], ActiveSubstanceAR | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_substance_term_by_uid: Callable[[str], DictionaryTermSubstanceAR | None],
        find_codelist_term_by_uid_and_submission_value: Callable[
            [str | None, str | None, datetime | None], CTSimpleCodelistTermAR | None
        ],
    ) -> Self:
        dosage_form_terms = []
        for uid in pharmaceutical_product_ar.concept_vo.dosage_form_uids:
            term = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=uid,
                codelist_submission_value=settings.dosage_form_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submission_value,
            )
            if term is not None:
                dosage_form_terms.append(term)
        admin_route_terms = []
        for uid in pharmaceutical_product_ar.concept_vo.route_of_administration_uids:
            term = SimpleCodelistTermModel.from_term_uid_and_codelist_submval(
                term_uid=uid,
                codelist_submission_value=settings.route_of_administration_cl_submval,
                find_codelist_term_by_uid_and_submission_value=find_codelist_term_by_uid_and_submission_value,
            )
            if term is not None:
                admin_route_terms.append(term)

        formulations = sorted(
            [
                Formulation(
                    external_id=formulation.external_id,
                    ingredients=sorted(
                        [
                            Ingredient(
                                external_id=ingredient.external_id,
                                formulation_name=ingredient.formulation_name,
                                active_substance=SimpleActiveSubstance.from_concept_uid(
                                    uid=ingredient.active_substance_uid,
                                    find_by_uid=find_active_substance_by_uid,
                                    find_dictionary_term_by_uid=find_dictionary_term_by_uid,
                                    find_substance_term_by_uid=find_substance_term_by_uid,
                                ),
                                strength=(
                                    SimpleNumericValueWithUnit.from_concept_uid(
                                        uid=ingredient.strength_uid,
                                        find_unit_by_uid=find_unit_by_uid,
                                        find_numeric_value_by_uid=find_numeric_value_by_uid,
                                    )
                                    if ingredient.strength_uid
                                    else None
                                ),
                                half_life=(
                                    SimpleNumericValueWithUnit.from_concept_uid(
                                        uid=ingredient.half_life_uid,
                                        find_unit_by_uid=find_unit_by_uid,
                                        find_numeric_value_by_uid=find_numeric_value_by_uid,
                                    )
                                    if ingredient.half_life_uid
                                    else None
                                ),
                                lag_times=sorted(
                                    [
                                        SimpleLagTime.from_concept_uid(
                                            uid=uid,
                                            find_unit_by_uid=find_unit_by_uid,
                                            find_lag_time_by_uid=find_lag_time_by_uid,
                                            find_term_by_uid=find_term_by_uid,
                                        )
                                        for uid in ingredient.lag_time_uids
                                    ],
                                    key=lambda item: item.value,
                                ),
                            )
                            for ingredient in formulation.ingredients
                        ],
                        key=lambda item: (
                            item.active_substance.analyte_number
                            if item.active_substance.analyte_number
                            else item.active_substance.uid
                        ),
                    ),
                )
                for formulation in pharmaceutical_product_ar.concept_vo.formulations
            ],
            key=lambda item: item.external_id if item.external_id else "",
        )

        return cls(
            uid=pharmaceutical_product_ar.uid,
            derived_name=cls._compute_derived_name(formulations),
            external_id=pharmaceutical_product_ar.concept_vo.external_id,
            dosage_forms=sorted(
                dosage_form_terms,
                key=lambda item: item.term_name if item.term_name else "",
            ),
            routes_of_administration=sorted(
                admin_route_terms,
                key=lambda item: item.term_name if item.term_name else "",
            ),
            formulations=formulations,
            library_name=Library.from_library_vo(
                pharmaceutical_product_ar.library
            ).name,
            start_date=pharmaceutical_product_ar.item_metadata.start_date,
            end_date=pharmaceutical_product_ar.item_metadata.end_date,
            status=pharmaceutical_product_ar.item_metadata.status.value,
            version=pharmaceutical_product_ar.item_metadata.version,
            change_description=pharmaceutical_product_ar.item_metadata.change_description,
            author_username=pharmaceutical_product_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in pharmaceutical_product_ar.get_possible_actions()]
            ),
        )

    @staticmethod
    def _compute_derived_name(formulations: list["Formulation"]) -> str:
        parts = []
        for formulation in formulations:
            for ingredient in formulation.ingredients:
                sub = ingredient.active_substance
                ingredient_name = (
                    (
                        sub.inn
                        or sub.long_number
                        or sub.short_number
                        or (sub.unii.substance_unii if sub.unii else None)
                        or sub.analyte_number
                        or "?"
                    )
                    if sub
                    else "?"
                )
                form_name = (
                    ingredient.formulation_name if ingredient.formulation_name else ""
                )
                part = f"{ingredient_name.strip()} {form_name.strip()}"
                if ingredient.strength:
                    value = ingredient.strength.value
                    value_str = str(int(value)) if value == int(value) else str(value)
                    part += f" ({value_str} {ingredient.strength.unit_label})"
                parts.append(part)
        return ", ".join(parts).strip()


class SimplePharmaceuticalProduct(BaseModel):
    @overload
    @classmethod
    def from_uid(
        cls, uid: str, find_by_uid: Callable[[str], PharmaceuticalProductAR | None]
    ) -> Self: ...
    @overload
    @classmethod
    def from_uid(
        cls, uid: None, find_by_uid: Callable[[str], PharmaceuticalProductAR | None]
    ) -> None: ...
    @classmethod
    def from_uid(
        cls,
        uid: str | None,
        find_by_uid: Callable[[str], PharmaceuticalProductAR | None],
    ) -> Self | None:
        item = None
        if uid is not None:
            item_ar: PharmaceuticalProductAR | None = find_by_uid(uid)
            if item_ar is not None:
                item = cls(
                    uid=uid,
                    external_id=item_ar.concept_vo.external_id,
                )

        return item

    @classmethod
    def from_input(cls, input_data) -> Self:
        return cls(
            uid=input_data.uid,
            external_id=input_data.external_id,
        )

    uid: Annotated[str, Field()]
    external_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class PharmaceuticalProductCreateInput(PostInputModel):
    external_id: Annotated[str | None, Field(min_length=1)] = None
    library_name: Annotated[str, Field(min_length=1)]
    dosage_form_uids: list[str] = Field(default_factory=list)
    route_of_administration_uids: list[str] = Field(default_factory=list)
    formulations: list[FormulationCreateInput] = Field(default_factory=list)


class PharmaceuticalProductEditInput(PatchInputModel):
    external_id: Annotated[str | None, Field(min_length=1)] = None
    library_name: Annotated[str | None, Field(min_length=1)] = None
    dosage_form_uids: list[str] = Field(default_factory=list)
    route_of_administration_uids: list[str] = Field(default_factory=list)
    formulations: list[FormulationEditInput] = Field(default_factory=list)
    change_description: Annotated[str, Field(min_length=1)]


class PharmaceuticalProductVersion(PharmaceuticalProduct):
    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
