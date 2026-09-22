from clinical_mdr_api.domain_repositories.standard_data_models.dataset_variable_repository import (
    DatasetVariableRepository,
)
from clinical_mdr_api.models.standard_data_models.dataset_variable import (
    DatasetVariable,
)
from clinical_mdr_api.services.standard_data_models.standard_data_model_service import (
    StandardDataModelService,
)


class DatasetVariableService(StandardDataModelService):
    repository_interface = DatasetVariableRepository
    api_model_class = DatasetVariable
    version_class = None
