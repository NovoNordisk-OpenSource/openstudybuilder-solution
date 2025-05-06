from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.pharmaceutical_product_repository import (
    PharmaceuticalProductRepository,
)
from clinical_mdr_api.domains.concepts.pharmaceutical_product import (
    FormulationVO,
    IngredientVO,
    PharmaceuticalProductAR,
    PharmaceuticalProductVO,
)
from clinical_mdr_api.models.concepts.pharmaceutical_product import (
    Formulation,
    PharmaceuticalProduct,
    PharmaceuticalProductCreateInput,
    PharmaceuticalProductEditInput,
    PharmaceuticalProductVersion,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class PharmaceuticalProductService(ConceptGenericService[PharmaceuticalProductAR]):
    aggregate_class = PharmaceuticalProductAR
    version_class = PharmaceuticalProductVersion
    repository_interface = PharmaceuticalProductRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: PharmaceuticalProductAR
    ) -> PharmaceuticalProduct:
        return PharmaceuticalProduct.from_pharmaceutical_product_ar(
            pharmaceutical_product_ar=item_ar,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_numeric_value_by_uid=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
            find_lag_time_by_uid=self._repos.lag_time_repository.find_by_uid_2,
            find_unit_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
            find_active_substance_by_uid=self._repos.active_substance_repository.find_by_uid_2,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid_2,
            find_substance_term_by_uid=self._repos.dictionary_term_substance_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: PharmaceuticalProductCreateInput, library
    ) -> _AggregateRootType:
        return PharmaceuticalProductAR.from_input_values(
            author_id=self.author_id,
            concept_vo=PharmaceuticalProductVO.from_repository_values(
                external_id=concept_input.external_id,
                dosage_form_uids=concept_input.dosage_form_uids,
                route_of_administration_uids=concept_input.route_of_administration_uids,
                formulations=[
                    FormulationVO.from_repository_values(
                        external_id=formulation_input.external_id,
                        ingredients=[
                            IngredientVO.from_repository_values(
                                active_substance_uid=ingredient_input.active_substance_uid,
                                formulation_name=ingredient_input.formulation_name,
                                external_id=ingredient_input.external_id,
                                strength_uid=ingredient_input.strength_uid,
                                half_life_uid=ingredient_input.half_life_uid,
                                lag_time_uids=ingredient_input.lag_time_uids,
                            )
                            for ingredient_input in formulation_input.ingredients
                        ],
                    )
                    for formulation_input in concept_input.formulations
                ],
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            pharmaceutical_product_uid_by_property_value_callback=self.repository.get_uid_by_property_value,
            ct_term_exists_callback=self._repos.ct_term_name_repository.term_exists,
            numeric_value_exists_callback=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
            lag_time_exists_callback=self._repos.lag_time_repository.find_by_uid_2,
            active_substance_exists_callback=self._repos.active_substance_repository.find_by_uid_2,
        )

    def _edit_aggregate(
        self,
        item: PharmaceuticalProductAR,
        concept_edit_input: PharmaceuticalProductEditInput,
    ) -> PharmaceuticalProductAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=PharmaceuticalProductVO.from_repository_values(
                external_id=concept_edit_input.external_id,
                dosage_form_uids=concept_edit_input.dosage_form_uids,
                route_of_administration_uids=concept_edit_input.route_of_administration_uids,
                formulations=(
                    [
                        FormulationVO.from_repository_values(
                            external_id=getattr(x, "external_id", None),
                            ingredients=(
                                [
                                    IngredientVO.from_repository_values(
                                        active_substance_uid=getattr(
                                            y, "active_substance_uid", None
                                        ),
                                        formulation_name=getattr(
                                            y, "formulation_name", None
                                        ),
                                        external_id=getattr(y, "external_id", None),
                                        strength_uid=getattr(y, "strength_uid", None),
                                        half_life_uid=getattr(y, "half_life_uid", None),
                                        lag_time_uids=getattr(y, "lag_time_uids", []),
                                    )
                                    for y in x.ingredients
                                ]
                                if x.ingredients
                                else []
                            ),
                        )
                        for x in concept_edit_input.formulations
                    ]
                    if concept_edit_input.formulations
                    else []
                ),
            ),
            concept_exists_by_callback=self.repository.get_uid_by_property_value,
            ct_term_exists_callback=self._repos.ct_term_name_repository.term_exists,
            numeric_value_exists_callback=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
            lag_time_exists_callback=self._repos.lag_time_repository.find_by_uid_2,
            active_substance_exists_callback=self._repos.active_substance_repository.find_by_uid_2,
        )
        return item

    @db.transaction
    def soft_delete(self, uid: str) -> None:
        pharmaceutical_product = self._find_by_uid_or_raise_not_found(
            uid, for_update=True
        )
        pharmaceutical_product.soft_delete()
        self.repository.save(pharmaceutical_product)

    @staticmethod
    def fill_in_additional_fields(
        concept_edit_input: PharmaceuticalProductEditInput,
        current_ar: PharmaceuticalProductAR,
    ) -> None:
        """
        This method preserves values of these fields in case they are not explicitly sent in the PATCH payload:
            - dosage_form_uids
            - route_of_administration_uids
            - formulations
        """
        for field in [
            "dosage_form_uids",
            "route_of_administration_uids",
        ]:
            if field not in concept_edit_input.model_fields_set:
                setattr(
                    concept_edit_input,
                    field,
                    getattr(current_ar.concept_vo, field),
                )

            if concept_edit_input.formulations and isinstance(
                concept_edit_input.formulations[0], Formulation
            ):
                # This means that `formulations` field was not sent in the payload
                # but filled by `_fill_missing_values_in_base_model_from_reference_base_model` method,
                # so we need to preserve it by using the current FormulationVO values
                concept_edit_input.formulations = current_ar.concept_vo.formulations
