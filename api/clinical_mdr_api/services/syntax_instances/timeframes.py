from clinical_mdr_api.domain_repositories.syntax_instances.timeframe_repository import (
    TimeframeRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.timeframe_template_repository import (
    TimeframeTemplateRepository,
)
from clinical_mdr_api.domains.syntax_instances.timeframe import TimeframeAR
from clinical_mdr_api.models.syntax_instances.timeframe import (
    Timeframe,
    TimeframeVersion,
)
from clinical_mdr_api.services.syntax_instances.generic_syntax_instance_service import (
    GenericSyntaxInstanceService,
    _AggregateRootType,
)


class TimeframeService(GenericSyntaxInstanceService[TimeframeAR | _AggregateRootType]):
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: TimeframeAR
    ) -> Timeframe:
        return Timeframe.from_timeframe_ar(item_ar)

    aggregate_class = TimeframeAR
    repository_interface = TimeframeRepository
    template_repository_interface = TimeframeTemplateRepository
    version_class = TimeframeVersion
    template_uid_property = "timeframe_template_uid"
