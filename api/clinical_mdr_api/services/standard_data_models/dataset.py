from clinical_mdr_api.domain_repositories.standard_data_models.dataset_repository import (
    DatasetRepository,
)
from clinical_mdr_api.models.standard_data_models.dataset import Dataset
from clinical_mdr_api.services.standard_data_models.standard_data_model_service import (
    StandardDataModelService,
)


class DatasetService(StandardDataModelService):
    repository_interface = DatasetRepository
    api_model_class = Dataset
    version_class = None
