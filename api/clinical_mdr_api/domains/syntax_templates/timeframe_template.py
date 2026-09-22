from dataclasses import dataclass

from clinical_mdr_api.domains.syntax_templates.template import TemplateAggregateRootBase
from common.exceptions import BusinessLogicException


@dataclass
class TimeframeTemplateAR(TemplateAggregateRootBase):
    """
    A specific Timeframe Template AR. It can be used to customize Timeframe Template
    behavior. Inherits strictly generic template versioning behaviors
    """

    def _raise_versioning_exception(self):
        raise BusinessLogicException(
            msg="The template parameters cannot be modified after being a final version, only the plain text can be modified"
        )
