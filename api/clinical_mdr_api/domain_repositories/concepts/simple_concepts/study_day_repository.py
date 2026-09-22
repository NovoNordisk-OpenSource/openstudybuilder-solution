from clinical_mdr_api.domain_repositories.concepts.simple_concepts.numeric_value_repository import (
    NumericValueRepository,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    StudyDayRoot,
    StudyDayValue,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_day import (
    StudyDayAR,
    StudyDayVO,
)
from clinical_mdr_api.models.concepts.concept import (
    NumericValue as NumericValueAPIModel,
)


class StudyDayRepository(NumericValueRepository):
    root_class = StudyDayRoot
    value_class = StudyDayValue
    aggregate_class = StudyDayAR
    value_object_class = StudyDayVO
    return_model = NumericValueAPIModel
