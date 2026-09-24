from clinical_mdr_api.domain_repositories.concepts.simple_concepts.numeric_value_repository import (
    NumericValueRepository,
)
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
    NumericValueVO,
)
from clinical_mdr_api.models.concepts.concept import (
    NumericValue,
    NumericValuePostInput,
    SimpleConceptPatchInput,
)
from clinical_mdr_api.services.concepts.simple_concepts.simple_concept_generic import (
    SimpleConceptGenericService,
)


class NumericValueService(SimpleConceptGenericService[NumericValueAR]):
    aggregate_class = NumericValueAR
    value_object_class = NumericValueVO
    repository_interface = NumericValueRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: NumericValueAR
    ) -> NumericValue:
        return NumericValue.from_concept_ar(numeric_value=item_ar)

    def _create_aggregate_root(
        self, concept_input: NumericValuePostInput, library
    ) -> NumericValueAR:
        return self.aggregate_class.from_input_values(
            author_id=self.author_id,
            simple_concept_vo=self.value_object_class.from_input_values(
                value=concept_input.value,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                is_template_parameter=concept_input.template_parameter,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            find_uid_by_name_callback=self.repository.find_uid_by_name,
        )

    def _edit_aggregate(
        self, item: NumericValueAR, concept_edit_input: SimpleConceptPatchInput
    ) -> NumericValueAR:
        raise AttributeError(
            "_edit_aggregate function is not defined for NumericValueService"
        )
