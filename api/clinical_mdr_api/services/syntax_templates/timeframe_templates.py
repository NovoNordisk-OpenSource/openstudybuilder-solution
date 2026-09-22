from clinical_mdr_api.domain_repositories.syntax_instances.timeframe_repository import (
    TimeframeRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.timeframe_template_repository import (
    TimeframeTemplateRepository,
)
from clinical_mdr_api.domains.syntax_templates.timeframe_template import (
    TimeframeTemplateAR,
)
from clinical_mdr_api.models.syntax_templates.timeframe_template import (
    TimeframeTemplate,
    TimeframeTemplateVersion,
    TimeframeTemplateWithCount,
)
from clinical_mdr_api.services.syntax_templates.generic_syntax_template_service import (
    GenericSyntaxTemplateService,
)


class TimeframeTemplateService(GenericSyntaxTemplateService[TimeframeTemplateAR]):
    aggregate_class = TimeframeTemplateAR
    version_class = TimeframeTemplateVersion
    repository_interface = TimeframeTemplateRepository
    instance_repository_interface = TimeframeRepository
    pre_instance_repository_interface = None

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: TimeframeTemplateAR
    ) -> TimeframeTemplate:
        cls = TimeframeTemplateWithCount if item_ar.counts != 0 else TimeframeTemplate
        return cls.from_timeframe_template_ar(item_ar)
