from clinical_mdr_api.domain_repositories.concepts.simple_concepts.numeric_value_repository import (
    NumericValueRepository,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    StudyWeekRoot,
    StudyWeekValue,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_week import (
    StudyWeekAR,
    StudyWeekVO,
)
from clinical_mdr_api.models.concepts.concept import (
    NumericValue as NumericValueAPIModel,
)


class StudyWeekRepository(NumericValueRepository):
    root_class = StudyWeekRoot
    value_class = StudyWeekValue
    aggregate_class = StudyWeekAR
    value_object_class = StudyWeekVO
    return_model = NumericValueAPIModel
