import datetime
from collections import namedtuple
from dataclasses import dataclass

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)

TypeNameDefinition = namedtuple("TypeNameDefinition", ["named", "definition"])

DiseaseMilestoneTypeNamedTuple = namedtuple(
    "DiseaseMilestoneTypeNamedTuple", ["name", "value"]
)
StudyDiseaseMilestoneType: dict[str, DiseaseMilestoneTypeNamedTuple] = {}


@dataclass
class StudyDiseaseMilestoneVO:
    study_uid: str
    repetition_indicator: bool
    order: int
    status: StudyStatus
    start_date: datetime.datetime
    author_id: str
    author_username: str
    disease_milestone_type: str
    disease_milestone_type_definition: str
    disease_milestone_type_name: str
    accepted_version: bool = False
    uid: str | None = None

    @property
    def dm_type(self) -> DiseaseMilestoneTypeNamedTuple:
        return StudyDiseaseMilestoneType[self.disease_milestone_type]

    def edit_core_properties(
        self,
        disease_milestone_type: str,
        repetition_indicator: bool,
    ):
        self.disease_milestone_type = disease_milestone_type
        self.repetition_indicator = repetition_indicator

    def set_order(self, order):
        self.order = order

    @property
    def possible_actions(self):
        if self.status == StudyStatus.DRAFT:
            return ["edit", "delete", "lock"]
        return None


@dataclass
class StudyDiseaseMilestoneHistoryVO(StudyDiseaseMilestoneVO):
    change_type: str | None = None
    end_date: datetime.datetime | None = None
