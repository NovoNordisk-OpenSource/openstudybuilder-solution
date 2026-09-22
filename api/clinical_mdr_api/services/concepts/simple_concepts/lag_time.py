from clinical_mdr_api.domain_repositories.concepts.simple_concepts.lag_time_repository import (
    LagTimeRepository,
)
from clinical_mdr_api.domains.concepts.simple_concepts.lag_time import (
    LagTimeAR,
    LagTimeVO,
)
from clinical_mdr_api.models.concepts.concept import (
    LagTime,
    LagTimePostInput,
    SimpleConceptPatchInput,
)
from clinical_mdr_api.services.concepts.simple_concepts.simple_concept_generic import (
    SimpleConceptGenericService,
)


class LagTimeService(SimpleConceptGenericService[LagTimeAR]):
    aggregate_class = LagTimeAR
    value_object_class = LagTimeVO
    repository_interface = LagTimeRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: LagTimeAR
    ) -> LagTime:
        return LagTime.from_concept_ar(
            numeric_value=item_ar,
            find_unit_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: LagTimePostInput, library
    ) -> LagTimeAR:
        return self.aggregate_class.from_input_values(
            author_id=self.author_id,
            simple_concept_vo=self.value_object_class.from_input_values(
                value=concept_input.value,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                is_template_parameter=concept_input.template_parameter,
                unit_definition_uid=concept_input.unit_definition_uid,
                sdtm_domain_uid=concept_input.sdtm_domain_uid,
                find_unit_definition_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
                find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            find_uid_by_value_unit_and_domain_callback=self._repos.lag_time_repository.find_uid_by_value_unit_and_domain,
        )

    def _edit_aggregate(
        self, item: LagTimeAR, concept_edit_input: SimpleConceptPatchInput
    ) -> LagTimeAR:
        raise AttributeError(
            "_edit_aggregate function is not defined for LagTimeService"
        )
