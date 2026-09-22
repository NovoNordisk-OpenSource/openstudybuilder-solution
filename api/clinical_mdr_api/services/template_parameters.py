from clinical_mdr_api.domain_repositories.template_parameters.complex_parameter import (
    ComplexTemplateParameterRepository,
)

repository = ComplexTemplateParameterRepository()


def get_all():
    return repository.find_all_with_samples()


def get_template_parameter_terms(name: str):
    return repository.find_values(name)
