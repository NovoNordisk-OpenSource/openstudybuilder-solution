from typing import Any

from neomodel import db  # type: ignore

from clinical_mdr_api.domains.projects.project import ProjectAR
from clinical_mdr_api.models.clinical_programmes.clinical_programme import (
    ClinicalProgramme,
)
from clinical_mdr_api.models.projects.project import (
    Project,
    ProjectCreateInput,
    ProjectEditInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import (
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from common.auth.user import user


class ProjectService:
    author_id: str

    def __init__(self):
        self.author_id = user().id()

    def get_all_projects(
        self,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 10,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[Project]:
        repos = MetaRepository()
        try:
            all_projects_with_programme = repos.project_repository.find_all()
            items = [
                Project(
                    uid=project_ar.uid,
                    project_number=project_ar.project_number,
                    name=project_ar.name,
                    clinical_programme=ClinicalProgramme(
                        uid=project_ar.clinical_programme_uid,
                        name=programme_name,
                    ),
                    description=project_ar.description,
                )
                for project_ar, programme_name in all_projects_with_programme
            ]
            filtered_items = service_level_generic_filtering(
                items=items,
                filter_by=filter_by,
                filter_operator=filter_operator,
                sort_by=sort_by,
                total_count=total_count,
                page_number=page_number,
                page_size=page_size,
            )
            return GenericFilteringReturn(
                items=filtered_items.items, total=filtered_items.total
            )
        finally:
            repos.close()

    def get_project_headers(
        self,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ):
        repos = MetaRepository()
        all_projects_with_programme = repos.project_repository.find_all()
        items = [
            Project(
                uid=project_ar.uid,
                project_number=project_ar.project_number,
                name=project_ar.name,
                clinical_programme=ClinicalProgramme(
                    uid=project_ar.clinical_programme_uid,
                    name=programme_name,
                ),
                description=project_ar.description,
            )
            for project_ar, programme_name in all_projects_with_programme
        ]
        filtered_items = service_level_generic_header_filtering(
            items=items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )
        return filtered_items

    def get_by_study_uid(self, study_uid: str) -> Project:
        repos = MetaRepository()
        project_ar = repos.project_repository.find_by_study_uid(study_uid)
        return Project.from_project_ar(
            project_ar, repos.clinical_programme_repository.find_by_uid
        )

    def get_project_by_uid(self, uid: str) -> Project:
        repos = MetaRepository()
        project_ar = repos.project_repository.find_by_uid(uid)

        return Project.from_project_ar(
            project_ar, repos.clinical_programme_repository.find_by_uid
        )

    @db.transaction
    def create(self, project_create_input: ProjectCreateInput) -> Project:
        repos = MetaRepository()
        try:
            project_ar = ProjectAR.from_input_values(
                project_number=project_create_input.project_number,
                name=project_create_input.name,
                clinical_programme_uid=project_create_input.clinical_programme_uid,
                description=project_create_input.description,
                generate_uid_callback=repos.project_repository.generate_uid,
                clinical_programme_exists_callback=repos.clinical_programme_repository.clinical_programme_exists,
            )

            repos.project_repository.save(project_ar)
            return Project.from_uid(
                uid=project_ar.uid,
                find_by_uid=repos.project_repository.find_by_uid,
                find_clinical_programme_by_uid=repos.clinical_programme_repository.find_by_uid,
            )
        finally:
            repos.close()

    @db.transaction
    def edit(self, uid: str, project_edit_input: ProjectEditInput) -> Project:
        repos = MetaRepository()
        try:
            project_ar = repos.project_repository.find_by_uid(uid)

            project_ar.name = project_edit_input.name
            project_ar.description = project_edit_input.description
            project_ar.clinical_programme_uid = (
                project_edit_input.clinical_programme_uid
            )

            repos.project_repository.save(project_ar, update=True)
            return Project.from_uid(
                uid=project_ar.uid,
                find_by_uid=repos.project_repository.find_by_uid,
                find_clinical_programme_by_uid=repos.clinical_programme_repository.find_by_uid,
            )
        finally:
            repos.close()

    @db.transaction
    def delete(self, uid: str) -> None:
        repos = MetaRepository()
        try:
            repos.project_repository.delete_by_uid(uid)
        finally:
            repos.close()
