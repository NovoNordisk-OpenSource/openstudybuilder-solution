from clinical_mdr_api.domain_repositories.standard_data_models.dataset_scenario_repository import (
    DatasetScenarioRepository,
)
from clinical_mdr_api.models.standard_data_models.dataset_scenario import (
    DatasetScenario,
)
from clinical_mdr_api.services.standard_data_models.standard_data_model_service import (
    StandardDataModelService,
)


class DatasetScenarioService(StandardDataModelService):
    repository_interface = DatasetScenarioRepository
    api_model_class = DatasetScenario
    version_class = None
