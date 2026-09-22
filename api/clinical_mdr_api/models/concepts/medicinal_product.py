from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.medicinal_product import MedicinalProductAR
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
    uid: Annotated[str, Field()]
    name: Annotated[str, Field()]
    name_sentence_case: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    external_id: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    library_name: Annotated[str, Field()]
    compound: Annotated[SimpleCompound, Field()]
    pharmaceutical_products: list[SimplePharmaceuticalProduct] = Field(
        default_factory=list
    )

    dose_values: list[SimpleNumericValueWithUnit] = Field(default_factory=list)
    dose_frequencies: list[SimpleTermModel] = Field(default_factory=list)
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
    ) -> Self:
        return cls(
            uid=medicinal_product_ar.uid,
            external_id=medicinal_product_ar.concept_vo.external_id,
            name=medicinal_product_ar.concept_vo.name or "",
            name_sentence_case=medicinal_product_ar.concept_vo.name_sentence_case,
            compound=SimpleCompound.from_input(
                medicinal_product_ar.concept_vo.compound,
            ),
            pharmaceutical_products=sorted(
                [
                    SimplePharmaceuticalProduct.from_input(x)
                    for x in medicinal_product_ar.concept_vo.pharmaceutical_products
                ],
                key=lambda item: item.external_id if item.external_id else "",
            ),
            dose_values=sorted(
                [
                    SimpleNumericValueWithUnit.from_input(x)
                    for x in medicinal_product_ar.concept_vo.dose_values
                ],
                key=lambda item: item.value,
            ),
            dose_frequencies=sorted(
                [
                    SimpleTermModel.from_input(input_data=x)
                    for x in medicinal_product_ar.concept_vo.dose_frequencies
                ],
                key=lambda item: item.name if item.name else "",
            ),
            delivery_device=(
                SimpleTermModel.from_input(
                    input_data=medicinal_product_ar.concept_vo.delivery_device
                )
                if medicinal_product_ar.concept_vo.delivery_device
                else None
            ),
            dispenser=(
                SimpleTermModel.from_input(
                    input_data=medicinal_product_ar.concept_vo.dispenser
                )
                if medicinal_product_ar.concept_vo.dispenser
                else None
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
    dose_value_uids: list[str] = Field(default_factory=list)
    dose_frequency_uids: list[str] = Field(default_factory=list)
    delivery_device_uid: Annotated[str | None, Field(min_length=1)] = None
    dispenser_uid: Annotated[str | None, Field(min_length=1)] = None
    compound_uid: Annotated[str, Field(min_length=1)]
    pharmaceutical_product_uids: list[str] = Field(default_factory=list)


class MedicinalProductEditInput(PatchInputModel):
    external_id: Annotated[str | None, Field(min_length=1)] = None
    name: Annotated[str | None, Field(min_length=1)] = None
    name_sentence_case: Annotated[str | None, Field(min_length=1)] = None
    library_name: Annotated[str | None, Field(min_length=1)] = None
    dose_value_uids: Annotated[list[str] | None, Field()] = None
    dose_frequency_uids: Annotated[list[str] | None, Field()] = None
    delivery_device_uid: Annotated[str | None, Field(min_length=1)] = None
    dispenser_uid: Annotated[str | None, Field(min_length=1)] = None
    compound_uid: Annotated[str | None, Field(min_length=1)] = None
    pharmaceutical_product_uids: Annotated[list[str] | None, Field()] = None
    change_description: Annotated[str, Field(min_length=1)]


class MedicinalProductVersion(MedicinalProduct):
    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
