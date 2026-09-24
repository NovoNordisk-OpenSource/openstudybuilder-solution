from clinical_mdr_api.domain_repositories.syntax_instances.objective_repository import (
    ObjectiveRepository,
)
from clinical_mdr_api.domain_repositories.syntax_pre_instances.objective_pre_instance_repository import (
    ObjectivePreInstanceRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.objective_template_repository import (
    ObjectiveTemplateRepository,
)
from clinical_mdr_api.domains.syntax_instances.objective import ObjectiveAR
from clinical_mdr_api.domains.syntax_pre_instances.objective_pre_instance import (
    ObjectivePreInstanceAR,
)
from clinical_mdr_api.models.syntax_instances.objective import (
    Objective,
    ObjectiveVersion,
)
from clinical_mdr_api.models.syntax_pre_instances.objective_pre_instance import (
    ObjectivePreInstanceVersion,
)
from clinical_mdr_api.services.syntax_instances.generic_syntax_instance_service import (
    GenericSyntaxInstanceService,
    _AggregateRootType,
)


class ObjectiveService(GenericSyntaxInstanceService[ObjectiveAR | _AggregateRootType]):
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ObjectiveAR
    ) -> Objective:
        return Objective.from_objective_ar(item_ar)

    aggregate_class: type[ObjectiveAR] | type[ObjectivePreInstanceAR] = ObjectiveAR
    repository_interface: (
        type[ObjectiveRepository] | type[ObjectivePreInstanceRepository]
    ) = ObjectiveRepository
    template_repository_interface = ObjectiveTemplateRepository
    version_class: type[ObjectiveVersion] | type[ObjectivePreInstanceVersion] = (
        ObjectiveVersion
    )
    template_uid_property = "objective_template_uid"
