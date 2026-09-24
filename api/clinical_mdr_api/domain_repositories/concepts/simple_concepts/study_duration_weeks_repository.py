from clinical_mdr_api.domain_repositories.concepts.simple_concepts.numeric_value_repository import (
    NumericValueRepository,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    StudyDurationWeeksRoot,
    StudyDurationWeeksValue,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_duration_weeks import (
    StudyDurationWeeksAR,
    StudyDurationWeeksVO,
)
from clinical_mdr_api.models.concepts.concept import (
    NumericValue as NumericValueAPIModel,
)


class StudyDurationWeeksRepository(NumericValueRepository):
    root_class = StudyDurationWeeksRoot
    value_class = StudyDurationWeeksValue
    aggregate_class = StudyDurationWeeksAR
    value_object_class = StudyDurationWeeksVO
    return_model = NumericValueAPIModel
