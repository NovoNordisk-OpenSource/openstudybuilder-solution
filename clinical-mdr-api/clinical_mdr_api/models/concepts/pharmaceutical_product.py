from typing import Annotated, Callable, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.active_substance import ActiveSubstanceAR
from clinical_mdr_api.domains.concepts.pharmaceutical_product import (
    PharmaceuticalProductAR,
)
from clinical_mdr_api.domains.concepts.simple_concepts.lag_time import LagTimeAR
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
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
from clinical_mdr_api.models.controlled_terminologies.ct_term import SimpleTermModel
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel


class Ingredient(BaseModel):
    external_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    formulation_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    active_substance: SimpleActiveSubstance
    strength: Annotated[
        SimpleNumericValueWithUnit | None, Field(json_schema_extra={"nullable": True})
    ] = None
    half_life: Annotated[
        SimpleNumericValueWithUnit | None, Field(json_schema_extra={"nullable": True})
    ] = None
    lag_times: list[SimpleLagTime] = []


class IngredientCreateInput(PostInputModel):
    active_substance_uid: Annotated[str, Field(min_length=1)]
    formulation_name: Annotated[str | None, Field(min_length=1)] = None
    external_id: Annotated[str | None, Field(min_length=1)] = None
    strength_uid: Annotated[str | None, Field(min_length=1)] = None
    half_life_uid: Annotated[str | None, Field(min_length=1)] = None
    lag_time_uids: list[str] = []


class IngredientEditInput(PatchInputModel):
    active_substance_uid: Annotated[str | None, Field(min_length=1)] = None
    formulation_name: Annotated[str | None, Field(min_length=1)] = None
    external_id: Annotated[str | None, Field(min_length=1)] = None
    strength_uid: Annotated[str | None, Field(min_length=1)] = None
    half_life_uid: Annotated[str | None, Field(min_length=1)] = None
    lag_time_uids: list[str] | None = None


class Formulation(BaseModel):
    external_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    ingredients: list[Ingredient] = []


class FormulationCreateInput(PostInputModel):
    external_id: Annotated[str | None, Field(min_length=1)] = None
    ingredients: list[IngredientCreateInput] | None = None


class FormulationEditInput(PatchInputModel):
    external_id: Annotated[str | None, Field(min_length=1)] = None
    ingredients: list[IngredientEditInput] = []


class PharmaceuticalProduct(VersionProperties):
    uid: str

    external_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    library_name: str

    dosage_forms: list[SimpleTermModel] | None
    routes_of_administration: list[SimpleTermModel] | None
    formulations: list[Formulation]

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
        find_numeric_value_by_uid: Callable[[str], NumericValueAR | None],
        find_lag_time_by_uid: Callable[[str], LagTimeAR | None],
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_active_substance_by_uid: Callable[[str], ActiveSubstanceAR | None],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_substance_term_by_uid: Callable[[str], DictionaryTermSubstanceAR | None],
    ) -> Self:
        return cls(
            uid=pharmaceutical_product_ar.uid,
            external_id=pharmaceutical_product_ar.concept_vo.external_id,
            dosage_forms=sorted(
                [
                    SimpleTermModel.from_ct_code(
                        c_code=uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for uid in pharmaceutical_product_ar.concept_vo.dosage_form_uids
                ],
                key=lambda item: item.name if item.name else "",
            ),
            routes_of_administration=sorted(
                [
                    SimpleTermModel.from_ct_code(
                        c_code=uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for uid in pharmaceutical_product_ar.concept_vo.route_of_administration_uids
                ],
                key=lambda item: item.name if item.name else "",
            ),
            formulations=sorted(
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
            ),
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


class SimplePharmaceuticalProduct(BaseModel):
    @classmethod
    def from_uid(
        cls, uid: str, find_by_uid: Callable[[str], PharmaceuticalProductAR | None]
    ) -> Self | None:
        item = None
        if uid is not None:
            item_ar: PharmaceuticalProductAR = find_by_uid(uid)
            if item_ar is not None:
                item = cls(uid=uid, external_id=item_ar.concept_vo.external_id)

        return item

    uid: Annotated[str, Field()]
    external_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )

    @classmethod
    def from_item_ar(cls, item_ar: PharmaceuticalProductAR) -> Self:
        return cls(
            uid=item_ar.uid,
            name=item_ar.name,
        )


class PharmaceuticalProductCreateInput(PostInputModel):
    external_id: Annotated[str | None, Field(min_length=1)] = None
    library_name: Annotated[str, Field(min_length=1)]
    dosage_form_uids: list[str] = []
    route_of_administration_uids: list[str] = []
    formulations: list[FormulationCreateInput] = []


class PharmaceuticalProductEditInput(PatchInputModel):
    external_id: Annotated[str | None, Field(min_length=1)] = None
    library_name: Annotated[str | None, Field(min_length=1)] = None
    dosage_form_uids: list[str] = []
    route_of_administration_uids: list[str] = []
    formulations: list[FormulationEditInput] = []
    change_description: Annotated[str, Field(min_length=1)]


class PharmaceuticalProductVersion(PharmaceuticalProduct):
    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []
