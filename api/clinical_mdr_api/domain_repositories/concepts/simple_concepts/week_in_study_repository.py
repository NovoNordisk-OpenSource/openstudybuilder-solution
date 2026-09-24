from clinical_mdr_api.domain_repositories.concepts.simple_concepts.numeric_value_repository import (
    NumericValueRepository,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    WeekInStudyRoot,
    WeekInStudyValue,
)
from clinical_mdr_api.domains.concepts.simple_concepts.week_in_study import (
    WeekInStudyAR,
    WeekInStudyVO,
)
from clinical_mdr_api.models.concepts.concept import (
    NumericValue as NumericValueAPIModel,
)


class WeekInStudyRepository(NumericValueRepository):
    root_class = WeekInStudyRoot
    value_class = WeekInStudyValue
    aggregate_class = WeekInStudyAR
    value_object_class = WeekInStudyVO
    return_model = NumericValueAPIModel
