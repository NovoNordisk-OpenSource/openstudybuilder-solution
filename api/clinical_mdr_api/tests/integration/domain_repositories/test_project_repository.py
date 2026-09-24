import unittest

from clinical_mdr_api.domain_repositories.clinical_programmes.clinical_programme_repository import (
    ClinicalProgrammeRepository,
)
from clinical_mdr_api.domain_repositories.projects.project_repository import (
    ProjectRepository,
)
from clinical_mdr_api.domains.projects.project import ProjectAR
from clinical_mdr_api.tests.integration.domain_repositories._utils import (
    wipe_clinical_programme_repository,
    wipe_project_repository,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.unit.domain.clinical_programme_aggregate.test_clinical_programme import (
    create_random_clinical_programme,
)
from clinical_mdr_api.tests.unit.domain.project_aggregate.test_project import (
    create_random_project,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str
from common.exceptions import NotFoundException


class TestProjectRepository(unittest.TestCase):
    TEST_DB_NAME = "projects.repo"

    @classmethod
    def setUp(cls) -> None:
        wipe_project_repository()

    @classmethod
    def setUpClass(cls) -> None:
        inject_and_clear_db(cls.TEST_DB_NAME)
        clinical_programme_repo = ClinicalProgrammeRepository()
        cls.created_clinical_programme = create_random_clinical_programme(
            clinical_programme_repo.generate_uid
        )
        clinical_programme_repo.save(cls.created_clinical_programme)

    @classmethod
    def tear_down_class(cls) -> None:
        wipe_clinical_programme_repository()

    def test__project_number_exist__non_existent_pr__returns_false(self):
        # given
        non_existent_project_number = f"this-uid-for-sure-does-not-exists-especially-after-adding-this-{random_str()}"
        repo = ProjectRepository()

        # when
        result = repo.project_number_exists(non_existent_project_number)
        repo.close()

        # then
        self.assertFalse(result)

    def test__project_number_exist__existing_pr__returns_true(self):
        # given
        repo = ProjectRepository()
        created_project = create_random_project(
            clinical_programme_uid=self.created_clinical_programme.uid,
            generate_uid_callback=repo.generate_uid,
        )

        # when
        repo.save(created_project)
        result = repo.project_number_exists(created_project.project_number)
        repo.close()

        # then
        self.assertTrue(result)

    def test__find_by_uid__non_existent_uid__returns_none(self):
        # given
        non_existent_uid = f"this-uid-for-sure-does-not-exists-especially-after-adding-this-{random_str()}"
        repo = ProjectRepository()

        # then
        with self.assertRaises(NotFoundException):
            # when
            repo.find_by_uid(non_existent_uid)
            repo.close()

    def test__find_by_uid__existing_uid__returns_project_ar(self):
        # given
        repo = ProjectRepository()
        created_project = create_random_project(
            clinical_programme_uid=self.created_clinical_programme.uid,
            generate_uid_callback=repo.generate_uid,
        )

        # when
        repo.save(created_project)
        result = repo.find_by_uid(created_project.uid)
        repo.close()

        # then
        self.assertEqual(result, created_project)

    def test__create__exists(self):
        # given

        repo = ProjectRepository()
        created_project = create_random_project(
            clinical_programme_uid=self.created_clinical_programme.uid,
            generate_uid_callback=repo.generate_uid,
        )

        # when
        repo.save(created_project)

        # clinical_programme_node = ClinicalProgramme.nodes.get(uid=project.holds_project)
        # project_node.holds_project.connect(clinical_programme_node)

        repo.close()

        # then
        repo = ProjectRepository()
        retrieved_project = repo.find_by_uid(created_project.uid)
        repo.close()

        self.assertEqual(retrieved_project, created_project)

    def test__find_all__existing_projects__returns_projects(self):
        # given
        repo = ProjectRepository()
        test_projects = [
            create_random_project(
                clinical_programme_uid=self.created_clinical_programme.uid,
                generate_uid_callback=repo.generate_uid,
            )
            for _ in range(0, 10)
        ]
        for project in test_projects:
            repo.save(project)
        repo.close()

        # when
        repo = ProjectRepository()
        all_projects_in_db = repo.find_all()
        repo.close()

        # then
        # we check if all test_projects are in all_projects_in_db
        # to achieve this we build a dictionary first
        db_projects: dict[str, ProjectAR] = {}
        for _project, _programme_name in all_projects_in_db:
            db_projects[_project.uid] = _project

        # then we go by test_projects and assert all of them are in the dictionary
        for test_project in test_projects:
            with self.subTest():
                self.assertEqual(db_projects[test_project.uid], test_project)

    def test__find_all__non_existent_projects__returns_empty_seq(self):
        # given
        repo = ProjectRepository()

        # when
        all_projects_in_db = repo.find_all()
        repo.close()

        # then
        self.assertEqual(len(all_projects_in_db), 0)
