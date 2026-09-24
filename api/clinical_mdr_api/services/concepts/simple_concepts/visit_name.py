from clinical_mdr_api.domain_repositories.concepts.simple_concepts.visit_name_repository import (
    VisitNameRepository,
)
from clinical_mdr_api.domains.concepts.simple_concepts.visit_name import (
    VisitNameAR,
    VisitNameVO,
)
from clinical_mdr_api.services.concepts.simple_concepts.text_value import (
    TextValueService,
)


class VisitNameService(TextValueService):
    aggregate_class = VisitNameAR
    value_object_class = VisitNameVO
    repository_interface = VisitNameRepository
