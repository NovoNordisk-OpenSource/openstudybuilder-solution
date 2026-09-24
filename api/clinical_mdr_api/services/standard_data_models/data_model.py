from clinical_mdr_api.domain_repositories.standard_data_models.data_model_repository import (
    DataModelRepository,
)
from clinical_mdr_api.models.standard_data_models.data_model import DataModel
from clinical_mdr_api.services.standard_data_models.standard_data_model_service import (
    StandardDataModelService,
)


class DataModelService(StandardDataModelService):
    repository_interface = DataModelRepository
    api_model_class = DataModel
    version_class = None
