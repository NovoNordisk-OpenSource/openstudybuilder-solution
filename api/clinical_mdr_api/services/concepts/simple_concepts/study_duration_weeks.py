from clinical_mdr_api.domain_repositories.concepts.simple_concepts.study_duration_weeks_repository import (
    StudyDurationWeeksRepository,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_duration_weeks import (
    StudyDurationWeeksAR,
    StudyDurationWeeksVO,
)
from clinical_mdr_api.services.concepts.simple_concepts.numeric_value import (
    NumericValueService,
)


class StudyDurationWeeksService(NumericValueService):
    aggregate_class = StudyDurationWeeksAR
    value_object_class = StudyDurationWeeksVO
    repository_interface = StudyDurationWeeksRepository
