from clinical_mdr_api.domain_repositories.concepts.simple_concepts.study_day_repository import (
    StudyDayRepository,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_day import (
    StudyDayAR,
    StudyDayVO,
)
from clinical_mdr_api.services.concepts.simple_concepts.numeric_value import (
    NumericValueService,
)


class StudyDayService(NumericValueService):
    aggregate_class = StudyDayAR
    value_object_class = StudyDayVO
    repository_interface = StudyDayRepository
