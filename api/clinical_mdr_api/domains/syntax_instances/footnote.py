from dataclasses import dataclass

from clinical_mdr_api.domains.libraries.object import ParametrizedTemplateARBase


@dataclass
class FootnoteAR(ParametrizedTemplateARBase):
    """
    Implementation of Footnote AR. Solely based on Parametrized Template.
    If there will be a need to customize behavior of Footnote comparing to
    other template derived objects - this code should go here.
    """
