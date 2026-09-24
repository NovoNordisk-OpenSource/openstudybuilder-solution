from abc import ABC
from dataclasses import dataclass

from clinical_mdr_api.domain_repositories.study_definitions.study_title.study_title_repository import (
    StudyTitleRepository,
)


@dataclass(frozen=True)
class StudyTitleTestAR(ABC):
    name: str


class StudyTitleRepositoryForTestImpl(StudyTitleRepository):
    _repo_content = frozenset(
        {
            StudyTitleTestAR("My Study #1"),
            StudyTitleTestAR("My Study #2"),
            StudyTitleTestAR("12345"),
        }
    )

    @staticmethod
    def study_title_exists(study_title: str, study_number: str) -> bool:
        for entry in StudyTitleRepositoryForTestImpl._repo_content:
            if entry.name == study_title:
                return True
        return False
