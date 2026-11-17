import datetime
from dataclasses import dataclass

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)


@dataclass
class StudyAuxiliaryDeviceVO:
    study_uid: str
    order: int
    status: StudyStatus
    start_date: datetime.datetime
    author_id: str
    auxiliary_device_term_uid: str
    author_username: str | None = None
    accepted_version: bool = False
    uid: str | None = None

    def set_order(self, order: int) -> None:
        self.order = order
