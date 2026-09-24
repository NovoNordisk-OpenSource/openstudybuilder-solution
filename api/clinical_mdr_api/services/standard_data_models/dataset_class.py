from clinical_mdr_api.domain_repositories.standard_data_models.dataset_class_repository import (
    DatasetClassRepository,
)
from clinical_mdr_api.models.standard_data_models.dataset_class import DatasetClass
from clinical_mdr_api.services.standard_data_models.standard_data_model_service import (
    StandardDataModelService,
)


class DatasetClassService(StandardDataModelService):
    repository_interface = DatasetClassRepository
    api_model_class = DatasetClass
    version_class = None
