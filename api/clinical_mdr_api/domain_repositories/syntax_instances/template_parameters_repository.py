from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameter,
    TemplateParameterTermRoot,
)


class TemplateParameterRepository:
    def parameter_name_exists(self, parameter_name: str) -> bool:
        return TemplateParameter.nodes.get_or_none(name=parameter_name) is not None

    def is_parameter_term_uid_valid_for_parameter_name(
        self,
        *,
        parameter_name: str,
        parameter_term_uid: str,
    ) -> bool:
        return TemplateParameterTermRoot.check_parameter_term_exists(
            parameter_name, parameter_term_uid
        )

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass
