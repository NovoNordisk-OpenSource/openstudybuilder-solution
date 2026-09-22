from clinical_mdr_api.domain_repositories.syntax_instances.activity_instruction_repository import (
    ActivityInstructionRepository,
)
from clinical_mdr_api.domain_repositories.syntax_pre_instances.activity_instruction_pre_instance_repository import (
    ActivityInstructionPreInstanceRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.activity_instruction_template_repository import (
    ActivityInstructionTemplateRepository,
)
from clinical_mdr_api.domains.syntax_instances.activity_instruction import (
    ActivityInstructionAR,
)
from clinical_mdr_api.domains.syntax_pre_instances.activity_instruction_pre_instance import (
    ActivityInstructionPreInstanceAR,
)
from clinical_mdr_api.models.syntax_instances.activity_instruction import (
    ActivityInstruction,
    ActivityInstructionVersion,
)
from clinical_mdr_api.models.syntax_pre_instances.activity_instruction_pre_instance import (
    ActivityInstructionPreInstanceVersion,
)
from clinical_mdr_api.services.syntax_instances.generic_syntax_instance_service import (
    GenericSyntaxInstanceService,
    _AggregateRootType,
)


class ActivityInstructionService(
    GenericSyntaxInstanceService[ActivityInstructionAR | _AggregateRootType]
):
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityInstructionAR
    ) -> ActivityInstruction:
        return ActivityInstruction.from_activity_instruction_ar(item_ar)

    aggregate_class: (
        type[ActivityInstructionAR] | type[ActivityInstructionPreInstanceAR]
    ) = ActivityInstructionAR
    repository_interface: (
        type[ActivityInstructionRepository]
        | type[ActivityInstructionPreInstanceRepository]
    ) = ActivityInstructionRepository
    template_repository_interface = ActivityInstructionTemplateRepository
    template_uid_property = "activity_instruction_template_uid"
    version_class: (
        type[ActivityInstructionVersion] | type[ActivityInstructionPreInstanceVersion]
    ) = ActivityInstructionVersion
