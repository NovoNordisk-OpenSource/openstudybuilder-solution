from clinical_mdr_api.domain_repositories.odms.metadata_repository import (
    MetadataRepository,
)
from clinical_mdr_api.domains.odms.utils import TargetType
from common.exceptions import BusinessLogicException


class OdmCsvExporterService:
    repo: MetadataRepository
    target_uid: str
    target_type: TargetType

    def __init__(
        self,
        target_uid: str,
        target_type: TargetType,
    ):
        self.target_uid = target_uid
        self.target_type = target_type
        self.repo = MetadataRepository()

    def get_odm_csv(self):
        if self.target_type == TargetType.STUDY_EVENT:
            return self.repo.get_odm_study_event(self.target_uid)
        if self.target_type == TargetType.FORM:
            return self.repo.get_odm_form(self.target_uid)
        if self.target_type == TargetType.ITEM_GROUP:
            return self.repo.get_odm_item_group(self.target_uid)
        if self.target_type == TargetType.ITEM:
            return self.repo.get_odm_item(self.target_uid)

        raise BusinessLogicException(msg="Requested target type not supported.")
