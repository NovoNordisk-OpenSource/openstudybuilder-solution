from clinical_mdr_api.domain_repositories.concepts.simple_concepts.study_week_repository import (
    StudyWeekRepository,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_week import (
    StudyWeekAR,
    StudyWeekVO,
)
from clinical_mdr_api.services.concepts.simple_concepts.numeric_value import (
    NumericValueService,
)


class StudyWeekService(NumericValueService):
    aggregate_class = StudyWeekAR
    value_object_class = StudyWeekVO
    repository_interface = StudyWeekRepository
