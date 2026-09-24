from clinical_mdr_api.domain_repositories.concepts.simple_concepts.study_duration_days_repository import (
    StudyDurationDaysRepository,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_duration_days import (
    StudyDurationDaysAR,
    StudyDurationDaysVO,
)
from clinical_mdr_api.services.concepts.simple_concepts.numeric_value import (
    NumericValueService,
)


class StudyDurationDaysService(NumericValueService):
    aggregate_class = StudyDurationDaysAR
    value_object_class = StudyDurationDaysVO
    repository_interface = StudyDurationDaysRepository
