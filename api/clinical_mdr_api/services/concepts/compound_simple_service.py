from clinical_mdr_api.domain_repositories.concepts.compound_repository import (
    CompoundRepository,
)
from clinical_mdr_api.domains.concepts.compound import CompoundAR
from clinical_mdr_api.models.concepts.compound import (
    CompoundCreateInput,
    CompoundEditInput,
    CompoundVersion,
    SimpleCompound,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
)


class CompoundSimpleService(ConceptGenericService[CompoundAR]):
    aggregate_class = CompoundAR
    version_class = CompoundVersion
    repository_interface = CompoundRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CompoundAR
    ) -> SimpleCompound:
        return SimpleCompound.from_compound_ar(
            compound_ar=item_ar,
        )

    def _create_aggregate_root(
        self, concept_input: CompoundCreateInput, library
    ) -> None:
        return None

    def _edit_aggregate(
        self, item: CompoundAR, concept_edit_input: CompoundEditInput
    ) -> None:
        return None
