from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.medicinal_product_repository import (
    MedicinalProductRepository,
)
from clinical_mdr_api.domains.concepts.medicinal_product import (
    MedicinalProductAR,
    MedicinalProductVO,
)
from clinical_mdr_api.models.concepts.medicinal_product import (
    MedicinalProduct,
    MedicinalProductCreateInput,
    MedicinalProductEditInput,
    MedicinalProductVersion,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
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
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_numeric_value_by_uid=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
            find_unit_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
            find_compound_by_uid=self._repos.compound_repository.find_by_uid_2,
            find_pharmaceutical_product_by_uid=self._repos.pharmaceutical_product_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: MedicinalProductCreateInput, library
    ) -> _AggregateRootType:
        return MedicinalProductAR.from_input_values(
            author_id=self.author_id,
            concept_vo=MedicinalProductVO.from_repository_values(
                external_id=concept_input.external_id,
                name=concept_input.name,
                name_sentence_case=concept_input.name_sentence_case,
                dose_value_uids=concept_input.dose_value_uids,
                dose_frequency_uid=concept_input.dose_frequency_uid,
                delivery_device_uid=concept_input.delivery_device_uid,
                dispenser_uid=concept_input.dispenser_uid,
                compound_uid=concept_input.compound_uid,
                pharmaceutical_product_uids=concept_input.pharmaceutical_product_uids,
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
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=MedicinalProductVO.from_repository_values(
                external_id=concept_edit_input.external_id,
                name=concept_edit_input.name,
                name_sentence_case=concept_edit_input.name_sentence_case,
                dose_value_uids=concept_edit_input.dose_value_uids,
                dose_frequency_uid=concept_edit_input.dose_frequency_uid,
                delivery_device_uid=concept_edit_input.delivery_device_uid,
                dispenser_uid=concept_edit_input.dispenser_uid,
                compound_uid=concept_edit_input.compound_uid,
                pharmaceutical_product_uids=concept_edit_input.pharmaceutical_product_uids,
            ),
            concept_exists_by_callback=self.repository.get_uid_by_property_value,
            ct_term_exists_callback=self._repos.ct_term_name_repository.term_exists,
            numeric_value_exists_callback=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
            compound_exists_callback=self._repos.compound_repository.find_by_uid_2,
            pharmaceutical_product_exists_callback=self._repos.pharmaceutical_product_repository.find_by_uid_2,
        )
        return item

    @db.transaction
    def soft_delete(self, uid: str) -> None:
        medicinal_product = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        medicinal_product.soft_delete()
        self.repository.save(medicinal_product)

    @staticmethod
    def fill_in_additional_fields(
        concept_edit_input: MedicinalProductEditInput,
        current_ar: MedicinalProductAR,
    ) -> None:
        """
        This method preserves values of these fields in case they are not explicitly sent in the PATCH payload:
            - dose_value_uids
            - dose_frequency_uid
            - dispenser_uid
            - delivery_device_uid
            - pharmaceutical_product_uids
            - compound_uid
        """
        for field in [
            "dose_value_uids",
            "dose_frequency_uid",
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
