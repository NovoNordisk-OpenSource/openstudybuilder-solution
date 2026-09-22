from typing import Annotated, Callable, Self, overload

from pydantic import Field, field_validator

from clinical_mdr_api.domains.clinical_programmes.clinical_programme import (
    ClinicalProgrammeAR,
)
from clinical_mdr_api.domains.projects.project import ProjectAR
from clinical_mdr_api.models.clinical_programmes.clinical_programme import (
    ClinicalProgramme,
)
from clinical_mdr_api.models.utils import BaseModel, PatchInputModel, PostInputModel
from clinical_mdr_api.models.validators import to_uppercase


class Project(BaseModel):
    uid: Annotated[str, Field(description="The unique id of the Project.")]

    project_number: Annotated[str | None, Field(json_schema_extra={"nullable": True})]

    clinical_programme: Annotated[ClinicalProgramme, Field()]

    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})]

    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})]

    @overload
    @classmethod
    def from_uid(
        cls,
        uid: str,
        find_by_uid: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
    ) -> Self: ...
    @overload
    @classmethod
    def from_uid(
        cls,
        uid: None,
        find_by_uid: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
    ) -> None: ...
    @classmethod
    def from_uid(
        cls,
        uid: str | None,
        find_by_uid: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
    ) -> Self | None:
        project = None

        if uid is not None:
            project_ar: ProjectAR | None = find_by_uid(uid)
            if project_ar is not None:
                project = Project.from_project_ar(
                    project_ar, find_clinical_programme_by_uid
                )
        return project

    @classmethod
    def from_project_ar(
        cls,
        project_ar: ProjectAR,
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
    ) -> Self:
        return Project(
            uid=project_ar.uid,
            project_number=project_ar.project_number,
            name=project_ar.name,
            clinical_programme=ClinicalProgramme(
                uid=project_ar.clinical_programme_uid,
                name=find_clinical_programme_by_uid(
                    project_ar.clinical_programme_uid
                ).name,
            ),
            description=project_ar.description,
        )


class ProjectCreateInput(PostInputModel):
    project_number: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1)]

    description: Annotated[str, Field(min_length=1)]

    clinical_programme_uid: Annotated[str, Field(min_length=1)]

    _to_uppercase = field_validator("project_number", mode="after")(to_uppercase)


class ProjectEditInput(PatchInputModel):
    name: Annotated[str, Field(min_length=1)]

    description: Annotated[str, Field(min_length=1)]

    clinical_programme_uid: Annotated[str, Field(min_length=1)]
