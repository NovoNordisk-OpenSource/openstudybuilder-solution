import datetime
from dataclasses import dataclass


@dataclass
class StudyDesignPopulationVO:
    """
    Value object for a single version of a StudyDesignPopulation study
    selection: a study-specific description of the population being studied
    (e.g. group identifier, name, definition and free-text notes).
    """

    study_uid: str
    group_id: str | None
    name: str | None
    definition: str | None
    notes: str | None
    order: int
    author_id: str
    start_date: datetime.datetime | None = None
    author_username: str | None = None
    accepted_version: bool = False
    uid: str | None = None

    def edit_core_properties(
        self,
        group_id: str | None,
        name: str | None,
        definition: str | None,
        notes: str | None,
    ) -> None:
        self.group_id = group_id
        self.name = name
        self.definition = definition
        self.notes = notes

    def set_order(self, order: int) -> None:
        self.order = order


@dataclass
class StudyDesignPopulationHistoryVO(StudyDesignPopulationVO):
    """
    Value object for a single audit-trail entry of a StudyDesignPopulation,
    extending the plain VO with the ``change_type``/``status``/``end_date``
    metadata needed to render an audit trail (mirrors
    ``StudyDiseaseMilestoneHistoryVO``).
    """

    change_type: str | None = None
    status: str | None = None
    end_date: datetime.datetime | None = None
