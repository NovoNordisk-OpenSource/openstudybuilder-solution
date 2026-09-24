from clinical_mdr_api.domain_repositories.concepts.simple_concepts.text_value_repository import (
    TextValueRepository,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    VisitNameRoot,
    VisitNameValue,
)
from clinical_mdr_api.domains.concepts.simple_concepts.visit_name import (
    VisitNameAR,
    VisitNameVO,
)
from clinical_mdr_api.models.concepts.concept import VisitName as VisitNameAPIModel


class VisitNameRepository(TextValueRepository):
    root_class = VisitNameRoot
    value_class = VisitNameValue
    aggregate_class = VisitNameAR
    value_object_class = VisitNameVO
    return_model = VisitNameAPIModel
