from typing import Annotated, Callable, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.compound import CompoundAR
from clinical_mdr_api.domains.concepts.medicinal_product import MedicinalProductAR
from clinical_mdr_api.domains.concepts.pharmaceutical_product import (
    PharmaceuticalProductAR,
)
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.models.concepts.compound import SimpleCompound
from clinical_mdr_api.models.concepts.concept import (
    SimpleNumericValueWithUnit,
    VersionProperties,
)
from clinical_mdr_api.models.concepts.pharmaceutical_product import (
    SimplePharmaceuticalProduct,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import SimpleTermModel
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import PatchInputModel, PostInputModel


class MedicinalProduct(VersionProperties):
    uid: str
    name: Annotated[str, Field()]
    name_sentence_case: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    external_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    library_name: str
    compound: SimpleCompound
    pharmaceutical_products: list[SimplePharmaceuticalProduct] = []

    dose_values: list[SimpleNumericValueWithUnit] = []
    dose_frequency: Annotated[
        SimpleTermModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    delivery_device: Annotated[
        SimpleTermModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    dispenser: Annotated[
        SimpleTermModel | None, Field(json_schema_extra={"nullable": True})
    ] = None

    possible_actions: Annotated[
        list[str],
        Field(
            description=(
                "Holds those actions that can be performed on MedicinalProducts. "
                "Actions are: 'approve', 'edit', 'new_version'."
            )
        ),
    ]

    @classmethod
    def from_medicinal_product_ar(
        cls,
        medicinal_product_ar: MedicinalProductAR,
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
        find_numeric_value_by_uid: Callable[[str], NumericValueAR | None],
        find_unit_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_compound_by_uid: Callable[[str], CompoundAR | None],
        find_pharmaceutical_product_by_uid: Callable[
            [str], PharmaceuticalProductAR | None
        ],
    ) -> Self:
        return cls(
            uid=medicinal_product_ar.uid,
            external_id=medicinal_product_ar.concept_vo.external_id,
            name=medicinal_product_ar.concept_vo.name,
            name_sentence_case=medicinal_product_ar.concept_vo.name_sentence_case,
            compound=SimpleCompound.from_uid(
                uid=medicinal_product_ar.concept_vo.compound_uid,
                find_by_uid=find_compound_by_uid,
            ),
            pharmaceutical_products=sorted(
                [
                    SimplePharmaceuticalProduct.from_uid(
                        uid=uid,
                        find_by_uid=find_pharmaceutical_product_by_uid,
                    )
                    for uid in medicinal_product_ar.concept_vo.pharmaceutical_product_uids
                ],
                key=lambda item: item.external_id if item.external_id else "",
            ),
            dose_values=sorted(
                [
                    SimpleNumericValueWithUnit.from_concept_uid(
                        uid=uid,
                        find_unit_by_uid=find_unit_by_uid,
                        find_numeric_value_by_uid=find_numeric_value_by_uid,
                    )
                    for uid in medicinal_product_ar.concept_vo.dose_value_uids
                ],
                key=lambda item: item.value,
            ),
            dose_frequency=SimpleTermModel.from_ct_code(
                c_code=medicinal_product_ar.concept_vo.dose_frequency_uid,
                find_term_by_uid=find_term_by_uid,
            ),
            delivery_device=SimpleTermModel.from_ct_code(
                c_code=medicinal_product_ar.concept_vo.delivery_device_uid,
                find_term_by_uid=find_term_by_uid,
            ),
            dispenser=SimpleTermModel.from_ct_code(
                c_code=medicinal_product_ar.concept_vo.dispenser_uid,
                find_term_by_uid=find_term_by_uid,
            ),
            library_name=Library.from_library_vo(medicinal_product_ar.library).name,
            start_date=medicinal_product_ar.item_metadata.start_date,
            end_date=medicinal_product_ar.item_metadata.end_date,
            status=medicinal_product_ar.item_metadata.status.value,
            version=medicinal_product_ar.item_metadata.version,
            change_description=medicinal_product_ar.item_metadata.change_description,
            author_username=medicinal_product_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in medicinal_product_ar.get_possible_actions()]
            ),
        )


class MedicinalProductCreateInput(PostInputModel):
    external_id: Annotated[str | None, Field(min_length=1)] = None
    name: Annotated[str, Field(min_length=1)]
    name_sentence_case: Annotated[str | None, Field(min_length=1)] = None
    library_name: Annotated[str, Field(min_length=1)]
    dose_value_uids: list[str] = []
    dose_frequency_uid: Annotated[str | None, Field(min_length=1)] = None
    delivery_device_uid: Annotated[str | None, Field(min_length=1)] = None
    dispenser_uid: Annotated[str | None, Field(min_length=1)] = None
    compound_uid: Annotated[str, Field(min_length=1)]
    pharmaceutical_product_uids: list[str] = []


class MedicinalProductEditInput(PatchInputModel):
    external_id: Annotated[str | None, Field(min_length=1)] = None
    name: Annotated[str | None, Field(min_length=1)] = None
    name_sentence_case: Annotated[str | None, Field(min_length=1)] = None
    library_name: Annotated[str | None, Field(min_length=1)] = None
    dose_value_uids: list[str] | None = None
    dose_frequency_uid: Annotated[str | None, Field(min_length=1)] = None
    delivery_device_uid: Annotated[str | None, Field(min_length=1)] = None
    dispenser_uid: Annotated[str | None, Field(min_length=1)] = None
    compound_uid: Annotated[str | None, Field(min_length=1)] = None
    pharmaceutical_product_uids: list[str] | None = None
    change_description: Annotated[str, Field(min_length=1)]


class MedicinalProductVersion(MedicinalProduct):
    changes: Annotated[
        list[str],
        Field(
            description=CHANGES_FIELD_DESC,
        ),
    ] = []
