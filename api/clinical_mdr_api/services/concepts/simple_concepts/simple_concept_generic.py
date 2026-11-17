from abc import ABC

from clinical_mdr_api.models.concepts.concept import SimpleConceptPatchInput
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
)


class SimpleConceptGenericService[AggregateRootType, ModelT: BaseModel = BaseModel](
    ConceptGenericService[AggregateRootType, ModelT], ABC
):
    def _edit_aggregate(
        self, item: AggregateRootType, concept_edit_input: SimpleConceptPatchInput
    ) -> AggregateRootType:
        raise AttributeError(
            "_edit_aggregate function is not defined for NumericValueService"
        )
