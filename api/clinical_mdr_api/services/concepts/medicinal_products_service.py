from clinical_mdr_api.domain_repositories.concepts.medicinal_product_repository import (
    MedicinalProductRepository,
)
from clinical_mdr_api.domains.concepts.medicinal_product import (
    MedicinalProductAR,
    MedicinalProductVO,
)
from clinical_mdr_api.domains.controlled_terminologies.utils import CtTermInfo
from clinical_mdr_api.models.concepts.compound import SimpleCompound
from clinical_mdr_api.models.concepts.concept import SimpleNumericValueWithUnit
from clinical_mdr_api.models.concepts.medicinal_product import (
    MedicinalProduct,
    MedicinalProductCreateInput,
    MedicinalProductEditInput,
    MedicinalProductVersion,
)
from clinical_mdr_api.models.concepts.pharmaceutical_product import (
    SimplePharmaceuticalProduct,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import SimpleTermModel
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
)


class MedicinalProductService(ConceptGenericService[MedicinalProductAR]):
    aggregate_class = MedicinalProductAR
    version_class = MedicinalProductVersion
    repository_interface = MedicinalProductRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: MedicinalProductAR
    ) -> MedicinalProduct:
        return MedicinalProduct.from_medicinal_product_ar(
            medicinal_product_ar=item_ar,
        )

    def _create_aggregate_root(
        self, concept_input: MedicinalProductCreateInput, library
    ) -> MedicinalProductAR:
        compound = SimpleCompound.from_uid(
            uid=concept_input.compound_uid,
            find_by_uid=self._repos.compound_repository.find_by_uid_2,
        )
        dose_frequencies = [
            SimpleTermModel.from_ct_code(
                c_code=uid,
                find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            )
            for uid in (concept_input.dose_frequency_uids or [])
        ]
        delivery_device = SimpleTermModel.from_ct_code(
            c_code=concept_input.delivery_device_uid,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
        )
        dispenser = SimpleTermModel.from_ct_code(
            c_code=concept_input.dispenser_uid,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
        )

        dose_values = sorted(
            [
                SimpleNumericValueWithUnit.from_concept_uid(
                    uid=uid,
                    find_unit_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
                    find_numeric_value_by_uid=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
                )
                for uid in (concept_input.dose_value_uids or [])
            ],
            key=lambda item: item.value if item else "",
        )

        pharmaceutical_products = sorted(
            [
                SimplePharmaceuticalProduct.from_uid(
                    uid=uid,
                    find_by_uid=self._repos.pharmaceutical_product_repository.find_by_uid_2,
                )
                for uid in (concept_input.pharmaceutical_product_uids or [])
            ],
            key=lambda item: (item.external_id if (item and item.external_id) else ""),
        )

        return MedicinalProductAR.from_input_values(
            author_id=self.author_id,
            concept_vo=MedicinalProductVO.from_repository_values(
                external_id=concept_input.external_id,
                name=concept_input.name,
                name_sentence_case=concept_input.name_sentence_case,
                dose_value_uids=concept_input.dose_value_uids,
                dose_frequency_uids=concept_input.dose_frequency_uids,
                delivery_device_uid=concept_input.delivery_device_uid,
                dispenser_uid=concept_input.dispenser_uid,
                compound_uid=concept_input.compound_uid,
                pharmaceutical_product_uids=concept_input.pharmaceutical_product_uids,
                compound=(
                    MedicinalProductVO.CompoundInfo(
                        uid=compound.uid, name=compound.name
                    )
                    if compound
                    else None
                ),
                dose_frequencies=[
                    CtTermInfo(term_uid=df.term_uid, name=df.name)
                    for df in dose_frequencies
                    if df is not None
                ],
                delivery_device=(
                    CtTermInfo(
                        term_uid=delivery_device.term_uid, name=delivery_device.name
                    )
                    if delivery_device
                    else None
                ),
                dispenser=(
                    CtTermInfo(term_uid=dispenser.term_uid, name=dispenser.name)
                    if dispenser
                    else None
                ),
                dose_values=[
                    MedicinalProductVO.DoseValueInfo(
                        uid=dv.uid,
                        value=dv.value,
                        unit_definition_uid=dv.unit_definition_uid,
                        unit_label=dv.unit_label,
                    )
                    for dv in dose_values
                    if dv is not None
                ],
                pharmaceutical_products=[
                    MedicinalProductVO.PharmaceuticalProductInfo(
                        uid=pp.uid,
                        external_id=pp.external_id,
                    )
                    for pp in pharmaceutical_products
                    if pp is not None
                ],
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            medicinal_product_uid_by_property_value_callback=self.repository.get_uid_by_property_value,
            ct_term_exists_callback=self._repos.ct_term_name_repository.term_exists,
            numeric_value_exists_callback=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
            compound_exists_callback=self._repos.compound_repository.find_by_uid_2,
            pharmaceutical_product_exists_callback=self._repos.pharmaceutical_product_repository.find_by_uid_2,
        )

    def _edit_aggregate(
        self,
        item: MedicinalProductAR,
        concept_edit_input: MedicinalProductEditInput,
    ) -> MedicinalProductAR:
        compound = SimpleCompound.from_uid(
            uid=concept_edit_input.compound_uid,
            find_by_uid=self._repos.compound_repository.find_by_uid_2,
        )
        dose_frequencies = [
            SimpleTermModel.from_ct_code(
                c_code=uid,
                find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            )
            for uid in (concept_edit_input.dose_frequency_uids or [])
        ]
        delivery_device = SimpleTermModel.from_ct_code(
            c_code=concept_edit_input.delivery_device_uid,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
        )
        dispenser = SimpleTermModel.from_ct_code(
            c_code=concept_edit_input.dispenser_uid,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
        )

        dose_values = sorted(
            [
                SimpleNumericValueWithUnit.from_concept_uid(
                    uid=uid,
                    find_unit_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
                    find_numeric_value_by_uid=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
                )
                for uid in (concept_edit_input.dose_value_uids or [])
            ],
            key=lambda item: item.value if item else "",
        )

        pharmaceutical_products = sorted(
            [
                SimplePharmaceuticalProduct.from_uid(
                    uid=uid,
                    find_by_uid=self._repos.pharmaceutical_product_repository.find_by_uid_2,
                )
                for uid in (concept_edit_input.pharmaceutical_product_uids or [])
            ],
            key=lambda item: (item.external_id if (item and item.external_id) else ""),
        )

        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=MedicinalProductVO.from_repository_values(
                external_id=concept_edit_input.external_id,
                name=concept_edit_input.name or item.name,
                name_sentence_case=concept_edit_input.name_sentence_case,
                dose_value_uids=concept_edit_input.dose_value_uids,
                dose_frequency_uids=concept_edit_input.dose_frequency_uids,
                delivery_device_uid=concept_edit_input.delivery_device_uid,
                dispenser_uid=concept_edit_input.dispenser_uid,
                compound_uid=concept_edit_input.compound_uid
                or item.concept_vo.compound_uid,
                pharmaceutical_product_uids=concept_edit_input.pharmaceutical_product_uids,
                dose_frequencies=[
                    CtTermInfo(term_uid=df.term_uid, name=df.name)
                    for df in dose_frequencies
                    if df is not None
                ],
                delivery_device=(
                    CtTermInfo(
                        term_uid=delivery_device.term_uid, name=delivery_device.name
                    )
                    if delivery_device
                    else None
                ),
                dispenser=(
                    CtTermInfo(term_uid=dispenser.term_uid, name=dispenser.name)
                    if dispenser
                    else None
                ),
                dose_values=[
                    MedicinalProductVO.DoseValueInfo(
                        uid=dv.uid,
                        value=dv.value,
                        unit_definition_uid=dv.unit_definition_uid,
                        unit_label=dv.unit_label,
                    )
                    for dv in dose_values
                    if dv is not None
                ],
                pharmaceutical_products=[
                    MedicinalProductVO.PharmaceuticalProductInfo(
                        uid=pp.uid,
                        external_id=pp.external_id,
                    )
                    for pp in pharmaceutical_products
                    if pp is not None
                ],
                compound=(
                    MedicinalProductVO.CompoundInfo(
                        uid=compound.uid, name=compound.name
                    )
                    if compound
                    else None
                ),
            ),
            concept_exists_by_callback=self.repository.get_uid_by_property_value,
            ct_term_exists_callback=self._repos.ct_term_name_repository.term_exists,
            numeric_value_exists_callback=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
            compound_exists_callback=self._repos.compound_repository.find_by_uid_2,
            pharmaceutical_product_exists_callback=self._repos.pharmaceutical_product_repository.find_by_uid_2,
        )
        return item

    @staticmethod
    def fill_in_additional_fields(
        concept_edit_input: MedicinalProductEditInput,
        current_ar: MedicinalProductAR,
    ) -> None:
        """
        This method preserves values of these fields in case they are not explicitly sent in the PATCH payload:
            - dose_value_uids
            - dose_frequency_uids
            - dispenser_uid
            - delivery_device_uid
            - pharmaceutical_product_uids
            - compound_uid
        """
        for field in [
            "dose_value_uids",
            "dose_frequency_uids",
            "dispenser_uid",
            "delivery_device_uid",
            "pharmaceutical_product_uids",
            "compound_uid",
        ]:
            if field not in concept_edit_input.model_fields_set:
                setattr(
                    concept_edit_input,
                    field,
                    getattr(current_ar.concept_vo, field),
                )
