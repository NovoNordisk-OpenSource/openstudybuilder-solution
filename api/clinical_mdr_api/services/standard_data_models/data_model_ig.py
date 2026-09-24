from clinical_mdr_api.domain_repositories.standard_data_models.data_model_ig_repository import (
    DataModelIGRepository,
)
from clinical_mdr_api.models.standard_data_models.data_model_ig import DataModelIG
from clinical_mdr_api.services.standard_data_models.standard_data_model_service import (
    StandardDataModelService,
)


class DataModelIGService(StandardDataModelService):
    repository_interface = DataModelIGRepository
    api_model_class = DataModelIG
    version_class = None
