from clinical_mdr_api.domain_repositories.concepts.simple_concepts.numeric_value_repository import (
    NumericValueRepository,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    StudyDurationDaysRoot,
    StudyDurationDaysValue,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_duration_days import (
    StudyDurationDaysAR,
    StudyDurationDaysVO,
)
from clinical_mdr_api.models.concepts.concept import (
    NumericValue as NumericValueAPIModel,
)


class StudyDurationDaysRepository(NumericValueRepository):
    root_class = StudyDurationDaysRoot
    value_class = StudyDurationDaysValue
    aggregate_class = StudyDurationDaysAR
    value_object_class = StudyDurationDaysVO
    return_model = NumericValueAPIModel
