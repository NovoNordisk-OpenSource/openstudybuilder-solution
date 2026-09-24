from abc import ABC

from clinical_mdr_api.models.concepts.concept import SimpleConceptPatchInput
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class SimpleConceptGenericService(ConceptGenericService[_AggregateRootType], ABC):
    def _edit_aggregate(
        self, item: _AggregateRootType, concept_edit_input: SimpleConceptPatchInput
    ) -> _AggregateRootType:
        raise AttributeError(
            "_edit_aggregate function is not defined for NumericValueService"
        )
