from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.libraries.object import (
    ParametrizedTemplateARBase,
    ParametrizedTemplateVO,
)
from clinical_mdr_api.domains.libraries.parameter_term import ParameterTermEntryVO
from clinical_mdr_api.domains.syntax_templates.template import TemplateVO
from common.exceptions import NotFoundException


@dataclass(frozen=True)
class CriteriaTemplateVO(ParametrizedTemplateVO):
    @classmethod
    def from_repository_values(
        cls,
        *,
        template_name: str,
        template_uid: str,
        template_sequence_id: str,
        guidance_text: str,
        parameter_terms: list[ParameterTermEntryVO],
        library_name: str,
    ) -> Self:
        """
        Create object based on repository values.

        Overridden version to include guidance text.
        """
        return cls(
            template_uid=template_uid,
            template_sequence_id=template_sequence_id,
            template_name=template_name,
            parameter_terms=parameter_terms,
            guidance_text=guidance_text,
            library_name=library_name,
        )

    @classmethod
    def from_input_values_2(
        cls,
        *,
        template_uid: str,
        template_sequence_id: str,
        parameter_terms: list[ParameterTermEntryVO],
        library_name: str,
        get_final_template_vo_by_template_uid_callback: Callable[
            [str], TemplateVO | None
        ],
    ) -> Self:
        """
        Creates object based on external input.

        Overridden version to include guidance text.
        """
        template = get_final_template_vo_by_template_uid_callback(template_uid)

        NotFoundException.raise_if(template is None, field_value=template_uid)

        return cls(
            template_name=template.name,
            template_uid=template_uid,
            template_sequence_id=template_sequence_id,
            parameter_terms=parameter_terms,
            guidance_text=template.guidance_text,
            library_name=library_name,
        )


@dataclass
class CriteriaAR(ParametrizedTemplateARBase):
    """
    Implementation of Criteria AR. Solely based on Parametrized Template.
    If there will be a need to customize behavior of Criteria comparing to
    other template derived objects - this code should go here.
    """

    _template: CriteriaTemplateVO

    @property
    def guidance_text(self) -> str:
        """Shortcut to access template's guidance text."""
        return self._template.guidance_text
