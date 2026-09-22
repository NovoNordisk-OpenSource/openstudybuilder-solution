from clinical_mdr_api.domain_repositories.standard_data_models.variable_class_repository import (
    VariableClassRepository,
)
from clinical_mdr_api.models.standard_data_models.variable_class import VariableClass
from clinical_mdr_api.services.standard_data_models.standard_data_model_service import (
    StandardDataModelService,
)


class VariableClassService(StandardDataModelService):
    repository_interface = VariableClassRepository
    api_model_class = VariableClass
    version_class = None
