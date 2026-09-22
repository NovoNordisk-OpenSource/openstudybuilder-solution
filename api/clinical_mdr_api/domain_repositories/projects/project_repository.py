from threading import Lock

from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from neomodel import db, exceptions

from clinical_mdr_api.domain_repositories.generic_repository import (
    RepositoryClosureData,
)
from clinical_mdr_api.domain_repositories.models.clinical_programme import (
    ClinicalProgramme,
)
from clinical_mdr_api.domain_repositories.models.project import Project
from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.domains.projects.project import ProjectAR
from clinical_mdr_api.repositories._utils import sb_clear_cache
from common.config import settings
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    NotFoundException,
)


class ProjectRepository:
    cache_store_item_by_uid = TTLCache(
        maxsize=settings.cache_max_size, ttl=settings.cache_ttl
    )
    lock_store_item_by_uid = Lock()
    cache_store_item_by_study_uid = TTLCache(
        maxsize=settings.cache_max_size, ttl=settings.cache_ttl
    )
    lock_store_item_by_study_uid = Lock()
    cache_store_item_by_project_number = TTLCache(
        maxsize=settings.cache_max_size, ttl=settings.cache_ttl
    )
    lock_store_item_by_project_number = Lock()

    def project_number_exists(self, project_number: str) -> bool:
        project = Project.nodes.first_or_none(project_number=project_number)
        return bool(project)

    def generate_uid(self) -> str:
        return Project.get_next_free_uid_and_increment_counter()

    def get_hashkey(
        self,
        uid: str,
    ):
        """
        Returns a hash key that will be used for mapping objects stored in cache,
        which ultimately determines whether a method invocation is a hit or miss.
        """
        return hashkey(
            str(type(self)),
            uid,
        )

    @cached(cache=cache_store_item_by_uid, key=get_hashkey, lock=lock_store_item_by_uid)
    def find_by_uid(self, uid: str) -> ProjectAR:
        project = Project.nodes.get_or_none(uid=uid)

        NotFoundException.raise_if_not(project, "Project", uid)

        return ProjectAR.from_input_values(
            project_number=project.project_number,
            name=project.name,
            clinical_programme_uid=project.holds_project.single().uid,
            description=project.description,
            generate_uid_callback=lambda: project.uid,
            clinical_programme_exists_callback=lambda _: True,
        )

    def delete_by_uid(self, uid: str) -> None:
        project: Project = Project.nodes.get_or_none(uid=uid)

        if project:
            BusinessLogicException.raise_if(
                self.is_used_in_studies(uid),
                msg=f"Cannot delete Project with UID '{uid}' because it is used by studies.",
            )

            project.delete()

    @cached(
        cache=cache_store_item_by_project_number,
        key=get_hashkey,
        lock=lock_store_item_by_project_number,
    )
    def find_by_project_number(self, project_number: str) -> ProjectAR | None:
        project = Project.nodes.first_or_none(project_number=project_number)
        if project is not None:
            project = ProjectAR.from_input_values(
                project_number=project.project_number,
                name=project.name,
                clinical_programme_uid=project.holds_project.single().uid,
                description=project.description,
                generate_uid_callback=lambda: project.uid,
                clinical_programme_exists_callback=lambda _: True,
            )
            return project
        return None

    @cached(
        cache=cache_store_item_by_study_uid,
        key=get_hashkey,
        lock=lock_store_item_by_study_uid,
    )
    def find_by_study_uid(self, uid: str) -> ProjectAR:
        """
        Returns data from the project to which the study with provided uid belongs.

        :param uid: uid of the study for which to get project data
        :return: The project Aggregate Root object
        """
        study_root = StudyRoot.nodes.get(uid=uid)
        if study_root is not None:
            study_value = study_root.latest_value.get_or_none()
            study_project_node = study_value.has_project.get_or_none()
            project_node = study_project_node.has_field.get_or_none()
            return ProjectAR.from_input_values(
                project_number=project_node.project_number,
                name=project_node.name,
                clinical_programme_uid=project_node.holds_project.single().uid,
                description=project_node.description,
                generate_uid_callback=lambda: project_node.uid,
                clinical_programme_exists_callback=lambda _: True,
            )
        raise exceptions.DoesNotExist(f"Study with UID '{uid}' doesn't exist.")

    @sb_clear_cache(
        caches=[
            "cache_store_item_by_uid",
            "cache_store_item_by_project_number",
            "cache_store_item_by_study_uid",
        ]
    )
    def save(self, project_ar: ProjectAR, update: bool = False) -> None:
        """
        Create or update a Project in the database.

        This method handles the creation of a new Project or updating an existing one based on the `update` flag.

        Args:
            project_ar
            update (bool): A flag indicating whether to update an existing Project (if True) or create a new one (if False).
            Default is False.

        Raises:
            NotFoundException: If the Project with the given UID does not exist.
            BusinessLogicException:
                - If the Project with the given UID is used in studies.
                - If the Clinical Programme with the given UID does not exist.
        """
        if not update:
            AlreadyExistsException.raise_if(
                Project.nodes.get_or_none(project_number=project_ar.project_number),
                "Project",
                project_ar.project_number,
                "Project Number",
            )

            project_node = Project(
                uid=project_ar.uid,
                project_number=project_ar.project_number,
                name=project_ar.name,
                description=project_ar.description,
            )
            project_node.save()
            clinical_programme_node = ClinicalProgramme.nodes.get_or_none(
                uid=project_ar.clinical_programme_uid
            )
            NotFoundException.raise_if_not(
                clinical_programme_node,
                "Clinical Programme",
                project_ar.clinical_programme_uid,
            )
            project_node.holds_project.connect(clinical_programme_node)
        else:
            project = Project.nodes.get_or_none(uid=project_ar.uid)

            BusinessLogicException.raise_if_not(project, "Project", project_ar.uid)

            BusinessLogicException.raise_if(
                self.is_used_in_studies(project_ar.uid),
                msg=f"Cannot update Project with UID '{project_ar.uid}' because it is used by studies.",
            )

            project.name = project_ar.name
            project.description = project_ar.description
            project.save()

            project.holds_project.disconnect_all()
            clinical_programme_node = ClinicalProgramme.nodes.get_or_none(
                uid=project_ar.clinical_programme_uid
            )
            BusinessLogicException.raise_if_not(
                clinical_programme_node,
                "Clinical Programme",
                project_ar.clinical_programme_uid,
            )
            project.holds_project.connect(clinical_programme_node)

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    def find_all(self) -> list[tuple[ProjectAR, str]]:
        """
        Single Cypher query that fetches all projects together with their
        clinical programme uid and name.  Returns a list of (ProjectAR, programme_name) tuples.
        """
        rs, _ = db.cypher_query("""
            MATCH (cp:ClinicalProgramme)-[:HOLDS_PROJECT]->(p:Project)
            RETURN p.uid, p.project_number, p.name, p.description, cp.uid, cp.name
            """)

        results: list[tuple[ProjectAR, str]] = []
        repository_closure_data = RepositoryClosureData(
            not_for_update=True, repository=self, additional_closure=None
        )
        for row in rs:
            p_uid: str
            p_uid, p_number, p_name, p_desc, cp_uid, cp_name = row
            project_ar = ProjectAR.from_input_values(
                project_number=p_number,
                name=p_name,
                clinical_programme_uid=cp_uid,
                description=p_desc,
                # pylint: disable=unnecessary-lambda
                generate_uid_callback=lambda uid=p_uid: uid,  # type: ignore[misc]
                clinical_programme_exists_callback=lambda _: True,
            )
            project_ar.repository_closure_data = repository_closure_data
            results.append((project_ar, cp_name))

        return results

    def is_used_in_studies(self, uid: str) -> bool:
        rs = db.cypher_query(
            """
            MATCH (p:Project {uid: $uid})-[:HAS_FIELD]->(:StudyProjectField)<-[:HAS_PROJECT]-(:StudyValue)
            RETURN DISTINCT COUNT(p)
            """,
            params={"uid": uid},
        )

        return bool(rs[0][0][0])
