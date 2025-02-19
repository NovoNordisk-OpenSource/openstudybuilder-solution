from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.compound_repository import (
    CompoundRepository,
)
from clinical_mdr_api.domains.concepts.compound import CompoundAR, CompoundVO
from clinical_mdr_api.models.concepts.compound import (
    Compound,
    CompoundCreateInput,
    CompoundEditInput,
    CompoundVersion,
)
from clinical_mdr_api.services.concepts.compound_alias_service import (
    CompoundAliasService,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class CompoundService(ConceptGenericService[CompoundAR]):
    aggregate_class = CompoundAR
    version_class = CompoundVersion
    repository_interface = CompoundRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CompoundAR
    ) -> Compound:
        return Compound.from_compound_ar(
            compound_ar=item_ar,
        )

    def _create_aggregate_root(
        self, concept_input: CompoundCreateInput, library
    ) -> _AggregateRootType:
        return CompoundAR.from_input_values(
            author_id=self.author_id,
            concept_vo=CompoundVO.from_repository_values(
                name=concept_input.name,
                name_sentence_case=concept_input.name_sentence_case,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                is_sponsor_compound=concept_input.is_sponsor_compound,
                external_id=concept_input.external_id,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            compound_uid_by_property_value_callback=self.repository.get_uid_by_property_value,
        )

    def _edit_aggregate(
        self, item: CompoundAR, concept_edit_input: CompoundEditInput
    ) -> CompoundAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=CompoundVO.from_repository_values(
                name=concept_edit_input.name,
                name_sentence_case=concept_edit_input.name_sentence_case,
                definition=concept_edit_input.definition,
                abbreviation=concept_edit_input.abbreviation,
                is_sponsor_compound=concept_edit_input.is_sponsor_compound,
                external_id=concept_edit_input.external_id,
            ),
            compound_uid_by_property_value_callback=self.repository.get_uid_by_property_value,
        )
        return item

    @db.transaction
    def soft_delete(self, uid: str) -> None:
        # find all aliases and delete them
        aliases_uids = (
            self._repos.compound_alias_repository.get_aliases_by_compound_uid(
                compound_uid=uid,
            )
        )
        compound_alias_service = CompoundAliasService()
        for alias_uid in aliases_uids:
            compound_alias = compound_alias_service._find_by_uid_or_raise_not_found(
                alias_uid, for_update=True
            )
            compound_alias.soft_delete()
            self._repos.compound_alias_repository.save(compound_alias)

        compound = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        compound.soft_delete()
        self.repository.save(compound)
