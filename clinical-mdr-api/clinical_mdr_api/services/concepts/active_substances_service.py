from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.active_substance_repository import (
    ActiveSubstanceRepository,
)
from clinical_mdr_api.domains.concepts.active_substance import (
    ActiveSubstanceAR,
    ActiveSubstanceVO,
)
from clinical_mdr_api.models.concepts.active_substance import (
    ActiveSubstance,
    ActiveSubstanceCreateInput,
    ActiveSubstanceEditInput,
    ActiveSubstanceVersion,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class ActiveSubstanceService(ConceptGenericService[ActiveSubstanceAR]):
    aggregate_class = ActiveSubstanceAR
    version_class = ActiveSubstanceVersion
    repository_interface = ActiveSubstanceRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActiveSubstanceAR
    ) -> ActiveSubstance:
        return ActiveSubstance.from_active_substance_ar(
            active_substance_ar=item_ar,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid_2,
            find_substance_term_by_uid=self._repos.dictionary_term_substance_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: ActiveSubstanceCreateInput, library
    ) -> _AggregateRootType:
        return ActiveSubstanceAR.from_input_values(
            author_id=self.author_id,
            concept_vo=ActiveSubstanceVO.from_repository_values(
                analyte_number=concept_input.analyte_number,
                short_number=concept_input.short_number,
                long_number=concept_input.long_number,
                inn=concept_input.inn,
                external_id=concept_input.external_id,
                unii_term_uid=concept_input.unii_term_uid,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            active_substance_uid_by_property_value_callback=self.repository.get_uid_by_property_value,
            dictionary_term_exists_callback=self._repos.dictionary_term_generic_repository.find_by_uid_2,
        )

    def _edit_aggregate(
        self, item: ActiveSubstanceAR, concept_edit_input: ActiveSubstanceEditInput
    ) -> ActiveSubstanceAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=ActiveSubstanceVO.from_repository_values(
                analyte_number=concept_edit_input.analyte_number,
                short_number=concept_edit_input.short_number,
                long_number=concept_edit_input.long_number,
                inn=concept_edit_input.inn,
                external_id=concept_edit_input.external_id,
                unii_term_uid=concept_edit_input.unii_term_uid,
            ),
            concept_exists_by_callback=self.repository.get_uid_by_property_value,
            dictionary_term_exists_callback=self._repos.dictionary_term_generic_repository.find_by_uid_2,
        )
        return item

    @db.transaction
    def soft_delete(self, uid: str) -> None:
        active_substance = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        active_substance.soft_delete()
        self.repository.save(active_substance)

    @staticmethod
    def fill_in_additional_fields(
        concept_edit_input: ActiveSubstanceEditInput,
        current_ar: ActiveSubstanceAR,
    ) -> None:
        """
        This method preserves values of these fields in case they are not explicitly sent in the PATCH payload:
            - unii_term_uid
        """
        if "unii_term_uid" not in concept_edit_input.model_fields_set:
            concept_edit_input.unii_term_uid = current_ar.concept_vo.unii_term_uid
