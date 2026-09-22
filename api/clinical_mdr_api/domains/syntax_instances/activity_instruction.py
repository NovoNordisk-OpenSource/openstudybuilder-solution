from dataclasses import dataclass

from clinical_mdr_api.domains.libraries.object import ParametrizedTemplateARBase


@dataclass
class ActivityInstructionAR(ParametrizedTemplateARBase):
    """
    Implementation of Activity instruction AR. Solely based on
    Parametrized Template. If there will be a need to customize
    behavior of Activity instructions comparing to other template
    derived objects - this code should go here.

    """
