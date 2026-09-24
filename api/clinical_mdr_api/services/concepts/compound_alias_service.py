from clinical_mdr_api.domain_repositories.concepts.compound_alias_repository import (
    CompoundAliasRepository,
)
from clinical_mdr_api.domains.concepts.compound_alias import (
    CompoundAliasAR,
    CompoundAliasVO,
)
from clinical_mdr_api.models.concepts.compound_alias import (
    CompoundAlias,
    CompoundAliasCreateInput,
    CompoundAliasEditInput,
    CompoundAliasVersion,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
)


class CompoundAliasService(ConceptGenericService[CompoundAliasAR]):
    aggregate_class = CompoundAliasAR
    version_class = CompoundAliasVersion
    repository_interface = CompoundAliasRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CompoundAliasAR
    ) -> CompoundAlias:
        return CompoundAlias.from_ar(
            ar=item_ar,
            find_compound_by_uid=self._repos.compound_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: CompoundAliasCreateInput, library
    ) -> CompoundAliasAR:
        return CompoundAliasAR.from_input_values(
            author_id=self.author_id,
            concept_vo=CompoundAliasVO.from_repository_values(
                name=concept_input.name,  # type: ignore[arg-type]
                name_sentence_case=concept_input.name_sentence_case,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                compound_uid=concept_input.compound_uid,
                is_preferred_synonym=concept_input.is_preferred_synonym,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            compound_alias_uid_by_property_value_callback=self.repository.get_uid_by_property_value,
            compound_exists_callback=self._repos.compound_repository.find_by_uid_2,
            compound_existing_preferred_synonyms_callback=self._repos.compound_alias_repository.get_compound_preferred_synonyms,
        )

    def _edit_aggregate(
        self, item: CompoundAliasAR, concept_edit_input: CompoundAliasEditInput
    ) -> CompoundAliasAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=CompoundAliasVO.from_repository_values(
                name=concept_edit_input.name or item.name,
                name_sentence_case=concept_edit_input.name_sentence_case,
                definition=concept_edit_input.definition,
                abbreviation=concept_edit_input.abbreviation,
                compound_uid=concept_edit_input.compound_uid,
                is_preferred_synonym=concept_edit_input.is_preferred_synonym,
            ),
            compound_alias_uid_by_property_value_callback=self.repository.get_uid_by_property_value,
            compound_exists_callback=self._repos.compound_repository.find_by_uid_2,
            compound_existing_preferred_synonyms_callback=self._repos.compound_alias_repository.get_compound_preferred_synonyms,
        )
        return item
