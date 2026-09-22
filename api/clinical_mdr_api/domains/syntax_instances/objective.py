from dataclasses import dataclass

from clinical_mdr_api.domains.libraries.object import ParametrizedTemplateARBase


@dataclass
class ObjectiveAR(ParametrizedTemplateARBase):
    """
    Implementation of Objective AR. Solely based on Parametrized Template.
    If there will be a need to customize behavior of Objectives comparing to
    other template derived objects - this code should go here.
    """
