from clinical_mdr_api.domain_repositories.syntax_instances.criteria_repository import (
    CriteriaRepository,
)
from clinical_mdr_api.domain_repositories.syntax_pre_instances.criteria_pre_instance_repository import (
    CriteriaPreInstanceRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.criteria_template_repository import (
    CriteriaTemplateRepository,
)
from clinical_mdr_api.domains.syntax_instances.criteria import (
    CriteriaAR,
    CriteriaTemplateVO,
)
from clinical_mdr_api.domains.syntax_pre_instances.criteria_pre_instance import (
    CriteriaPreInstanceAR,
)
from clinical_mdr_api.models.syntax_instances.criteria import (
    Criteria,
    CriteriaVersion,
    CriteriaWithType,
)
from clinical_mdr_api.models.syntax_pre_instances.criteria_pre_instance import (
    CriteriaPreInstanceVersion,
)
from clinical_mdr_api.services.syntax_instances.generic_syntax_instance_service import (
    GenericSyntaxInstanceService,
    _AggregateRootType,
)


class CriteriaService(GenericSyntaxInstanceService[CriteriaAR | _AggregateRootType]):
    aggregate_class: type[CriteriaAR] | type[CriteriaPreInstanceAR] = CriteriaAR
    repository_interface: (
        type[CriteriaRepository] | type[CriteriaPreInstanceRepository]
    ) = CriteriaRepository
    template_repository_interface = CriteriaTemplateRepository
    version_class: type[CriteriaVersion] | type[CriteriaPreInstanceVersion] = (
        CriteriaVersion
    )
    template_uid_property = "criteria_template_uid"
    parametrized_template_vo_class = CriteriaTemplateVO

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CriteriaAR
    ) -> Criteria:
        return CriteriaWithType.from_criteria_ar(item_ar)
