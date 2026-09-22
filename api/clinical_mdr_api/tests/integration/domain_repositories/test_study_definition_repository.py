# pylint: disable=unused-argument

import dataclasses
import unittest

import pytest
from neomodel import db

from clinical_mdr_api.domain_repositories.clinical_programmes.clinical_programme_repository import (
    ClinicalProgrammeRepository,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.domain_repositories.projects.project_repository import (
    ProjectRepository,
)
from clinical_mdr_api.domain_repositories.study_definitions.study_definition_repository import (
    StudyDefinitionRepository,
)
from clinical_mdr_api.domain_repositories.study_definitions.study_definition_repository_impl import (
    StudyDefinitionRepositoryImpl,
)
from clinical_mdr_api.domains.study_definition_aggregates.root import StudyDefinitionAR
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyDescriptionVO,
)
from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.models.study_selections.study import (
    StudyFieldAuditTrailAction,
    StudySoaPreferencesInput,
)
from clinical_mdr_api.tests.integration.domain_repositories._utils import (
    current_function_name,
    wipe_clinical_programme_repository,
    wipe_project_repository,
    wipe_study_definition_repository,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_PARAMETERS_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.unit.domain.clinical_programme_aggregate.test_clinical_programme import (
    create_random_clinical_programme,
)
from clinical_mdr_api.tests.unit.domain.project_aggregate.test_project import (
    create_random_project,
)
from clinical_mdr_api.tests.unit.domain.study_definition_aggregate.test_root import (
    create_random_study,
    make_random_study_metadata_edit,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str
from common.auth.user import user
from common.config import settings

IGNORE_ORDER_FOR = [
    "trial_intent_types_codes",
    "trial_phase_codes",
    "trial_type_codes",
    "dictionary_terms",
]
IGNORED_FIELDS = [
    "not_for_update",
    "additional_closure",
    "repository_closure_data",
    "repository",
]


def assert_dataclasses_equal(obj1, obj2):
    for field in dataclasses.fields(obj1):
        attr = field.name
        if attr in IGNORED_FIELDS:
            continue
        attr1 = getattr(obj1, attr)
        attr2 = getattr(obj2, attr)
        if callable(attr1):
            continue
        if attr1 is None:
            assert attr2 is None
        elif isinstance(attr1, list | tuple):
            if attr in IGNORE_ORDER_FOR:
                assert set(attr1) == set(attr2)
            else:
                assert attr1 == attr2
        elif dataclasses.is_dataclass(attr1):
            assert_dataclasses_equal(attr1, attr2)
        else:
            assert attr1 == attr2


class TestStudyDefinitionRepository(unittest.TestCase):
    TEST_DB_NAME = "studydeftest"

    @classmethod
    def setUpClass(cls) -> None:
        inject_and_clear_db(cls.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)

        wipe_study_definition_repository()
        wipe_project_repository()
        wipe_clinical_programme_repository()

        clinical_programme_repo = ClinicalProgrammeRepository()
        cls.created_clinical_programme = create_random_clinical_programme(
            clinical_programme_repo.generate_uid
        )
        clinical_programme_repo.save(cls.created_clinical_programme)

        project_repo = ProjectRepository()
        cls.created_project = create_random_project(
            clinical_programme_uid=cls.created_clinical_programme.uid,
            generate_uid_callback=project_repo.generate_uid,
        )
        project_repo.save(cls.created_project)

        cls.project_to_amend = create_random_project(
            clinical_programme_uid=cls.created_clinical_programme.uid,
            generate_uid_callback=project_repo.generate_uid,
        )
        project_repo.save(cls.project_to_amend)

        TestUtils.create_library()
        TestUtils.create_library(name="UCUM", is_editable=True)
        TestUtils.create_ct_catalogue()

        TestUtils.create_study_ct_data_map(codelist_uid=None)

    def test__assert_dataclasses_equal(self):
        # create a study
        with db.transaction:
            repository1 = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                repository1.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repository1.save(created_study)
            repository1.close()

        # edit the study
        with db.transaction:
            repository2 = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repository2.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            repository2.save(amended_study)
            repository2.close()

        # fetch the edited study and make sure the assert function catches the difference
        with db.transaction:
            repository3 = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repository3.find_by_uid(created_study.uid, for_update=False)
            with pytest.raises(AssertionError):
                assert_dataclasses_equal(created_study, amended_study)
            repository3.close()

    def test__find_by_uid__non_existent_uid__returns_none(self):
        with db.transaction:
            # given
            non_existent_uid = f"this-uid-for-sure-does-not-exists-especially-after-adding-this-{random_str()}"
            repository = StudyDefinitionRepositoryImpl(f"{current_function_name()}")

            # when
            result = repository.find_by_uid(non_existent_uid)
            repository.close()

            # then
            self.assertIsNone(result)

    def test__create__exists(self):
        with db.transaction:
            # given
            repository1 = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repository1.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            # when
            repository1.save(created_study)
            repository1.close()

        # then
        with db.transaction:
            repository2 = StudyDefinitionRepositoryImpl(current_function_name())
            retrieved_study = repository2.find_by_uid(created_study.uid)
            repository2.close()
        print("CRE", created_study)
        print("RET", retrieved_study)
        assert_dataclasses_equal(retrieved_study, created_study)

    def test__save__locked__locked(self):
        def can_lock(_: StudyDefinitionAR) -> bool:
            return _.current_metadata.id_metadata.study_id is not None

        # given
        with db.transaction:
            repository1 = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                condition=can_lock,
                generate_uid_callback=repository1.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                author_id=current_function_name(),
            )
            repository1.save(created_study)
            repository1.close()

        # when
        with db.transaction:
            repository2 = StudyDefinitionRepositoryImpl(current_function_name())
            study_to_lock = repository2.find_by_uid(created_study.uid, for_update=True)
            study_to_lock.edit_metadata(
                study_title_exists_callback=lambda _, study_number: False,
                study_short_title_exists_callback=lambda _, study_number: False,
                new_study_description=StudyDescriptionVO.from_input_values(
                    study_title="new_study_title", study_short_title="study_short_title"
                ),
                author_id=current_function_name(),
            )
            repository2.save(study_to_lock)
            study_to_lock = repository2.find_by_uid(created_study.uid, for_update=True)
            study_to_lock.lock(
                version_description="locked version",
                author_id=current_function_name(),
            )
            repository2.save(study_to_lock)
            repository2.close()

        # then
        with db.transaction:
            repository3 = StudyDefinitionRepositoryImpl(current_function_name())
            locked_study = repository3.find_by_uid(created_study.uid)
            repository3.close()
        print("LOCKED", locked_study)
        assert_dataclasses_equal(
            locked_study.current_metadata.ver_metadata,
            study_to_lock.current_metadata.ver_metadata,
        )
        assert_dataclasses_equal(locked_study, study_to_lock)

    def test__save__after_metadata_edit_with_different_values__result(self):
        # given
        with db.transaction:
            repository1 = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                repository1.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repository1.save(created_study)
            repository1.close()

        # when
        with db.transaction:
            repository2 = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repository2.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            repository2.save(amended_study)
            repository2.close()

        # then
        with db.transaction:
            repository3 = StudyDefinitionRepositoryImpl(current_function_name())
            final_retrieved_study = repository3.find_by_uid(created_study.uid)
            repository3.close()
        print(f"final {final_retrieved_study}")
        print(f"amended {amended_study}")
        assert_dataclasses_equal(final_retrieved_study, amended_study)

    def test__save__after_metadata_edit_with_same_values__result(self):
        # given
        with db.transaction:
            repository1 = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                repository1.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repository1.save(created_study)
            repository1.close()

        # when
        with db.transaction:
            repository2 = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repository2.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            amended_study.edit_metadata(
                new_id_metadata=amended_study.current_metadata.id_metadata,
                project_exists_callback=lambda _: True,
                author_id=current_function_name(),
            )
            repository2.save(amended_study)
            repository2.close()

        # then
        with db.transaction:
            repository3 = StudyDefinitionRepositoryImpl(current_function_name())
            final_retrieved_study = repository3.find_by_uid(created_study.uid)
            repository3.close()

        assert_dataclasses_equal(final_retrieved_study, amended_study)

    def test__save__after_unlock__result(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_condition=lambda _: _.study_number is not None,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            amended_study.edit_metadata(
                study_title_exists_callback=lambda _, study_number: False,
                study_short_title_exists_callback=lambda _, study_number: False,
                new_study_description=StudyDescriptionVO.from_input_values(
                    study_title="new_study_title", study_short_title="study_short_title"
                ),
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            locked_study = repo.find_by_uid(created_study.uid, for_update=True)
            print("LCK", locked_study)
            print("LCK", amended_study)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(locked_study, amended_study)
            locked_study.lock(
                version_description="very important version",
                author_id=current_function_name(),
            )
            repo.save(locked_study)
            repo.close()

        # when
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            unlocked_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(unlocked_study, locked_study)
            unlocked_study.unlock(author_id=current_function_name())
            repo.save(unlocked_study)
            repo.close()

        # then
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            final_retrieved_study = repo.find_by_uid(created_study.uid)
            repo.close()

        assert_dataclasses_equal(final_retrieved_study, unlocked_study)

    def test__save__after_release__result(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            released_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(released_study, amended_study)
            released_study.release(
                change_description="making a release in test",
                author_id=current_function_name(),
            )
            repo.save(released_study)
            repo.close()

        # then
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            final_retrieved_study = repo.find_by_uid(created_study.uid)
            repo.close()

        assert_dataclasses_equal(final_retrieved_study, released_study)

    def test__save__after_release_and_edit__result(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            released_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(released_study, amended_study)
            released_study.release(
                change_description="making a release in test",
                author_id=current_function_name(),
            )
            repo.save(released_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, released_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        # then
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            final_retrieved_study = repo.find_by_uid(created_study.uid)
            repo.close()
        print(
            "FIN",
            final_retrieved_study.current_metadata.id_metadata.study_number,
            created_study.current_metadata.id_metadata.study_number,
        )
        print(
            "FIN",
            final_retrieved_study.current_metadata.id_metadata.project_number,
            amended_study.current_metadata.id_metadata.project_number,
        )
        print(f"final {final_retrieved_study}")
        print(f"amended {amended_study}")
        assert_dataclasses_equal(final_retrieved_study, amended_study)

    def test__save__after_lock_unlock_release_lock__result(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_condition=(
                    lambda _: _.project_number is not None
                    and _.study_number is not None
                ),
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            amended_study.edit_metadata(
                study_title_exists_callback=lambda _, study_number: False,
                study_short_title_exists_callback=lambda _, study_number: False,
                new_study_description=StudyDescriptionVO.from_input_values(
                    study_title="new_study_title", study_short_title="study_short_title"
                ),
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            locked_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(locked_study, amended_study)
            locked_study.lock(
                version_description="very important version",
                author_id=current_function_name(),
            )
            repo.save(locked_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            unlocked_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(unlocked_study, locked_study)
            unlocked_study.unlock(author_id=current_function_name())
            repo.save(unlocked_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            released_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(released_study, unlocked_study)
            released_study.release(
                change_description="making a release in test",
                author_id=current_function_name(),
            )
            repo.save(released_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            locked_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(locked_study, released_study)
            locked_study.lock(
                author_id=current_function_name(),
                version_description="another very important version",
            )
            repo.save(locked_study)
            repo.close()

        # then
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            final_retrieved_study = repo.find_by_uid(created_study.uid)
            repo.close()

        assert_dataclasses_equal(final_retrieved_study, locked_study)

    def test__save__after_lock_unlock_release_lock_and_edits_in_between__result(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_condition=lambda _: _.study_number is not None,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            amended_study.edit_metadata(
                study_title_exists_callback=lambda _, study_number: False,
                study_short_title_exists_callback=lambda _, study_number: False,
                new_study_description=StudyDescriptionVO.from_input_values(
                    study_title="new_study_title", study_short_title="study_short_title"
                ),
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            locked_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(locked_study, amended_study)
            locked_study.lock(
                version_description="very important version",
                author_id=current_function_name(),
            )
            repo.save(locked_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            unlocked_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(unlocked_study, locked_study)
            unlocked_study.unlock(author_id=current_function_name())
            repo.save(unlocked_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            print("amended_study", amended_study)
            print("unlocked_study", unlocked_study)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, unlocked_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_condition=(
                    lambda _: _.project_number is not None
                    and _.study_number is not None
                ),
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            released_study = repo.find_by_uid(created_study.uid, for_update=True)
            print("released_study", released_study)
            print("amended_study", amended_study)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(released_study, amended_study)
            released_study.release(
                change_description="making a release in test",
                author_id=current_function_name(),
            )
            repo.save(released_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            print("amended_study", amended_study)
            print("released_study", released_study)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, released_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_condition=lambda _: _.project_number is not None,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            locked_study = repo.find_by_uid(created_study.uid, for_update=True)
            print("locked_study", locked_study)
            print("amended_study", amended_study)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(locked_study, amended_study)
            locked_study.lock(
                author_id=current_function_name(),
                version_description="another very important version",
            )
            repo.save(locked_study)
            repo.close()

        # then
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            final_retrieved_study = repo.find_by_uid(created_study.uid)
            repo.close()

        assert_dataclasses_equal(final_retrieved_study, locked_study)

    def test__find_all__results(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            test_studies = [
                create_random_study(
                    repo.generate_uid,
                    new_id_metadata_fixed_values={
                        "project_number": self.created_project.project_number
                    },
                    is_study_after_create=True,
                    author_id="test__find_all__results",
                )
                for _ in range(0, 10)
            ]
            for study in test_studies:
                repo.save(study)
            repo.close()

        # when
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            all_studies_in_db = repo.find_all(
                page_number=1, page_size=settings.max_int_neo4j - 1
            ).items
            repo.close()

        # then
        # we check if all test_studies are in all_studies_in_db
        # to achieve this we build a dictionary first
        db_studies: dict[str, StudyDefinitionAR] = {}
        for _study in all_studies_in_db:
            db_studies[_study.uid] = _study

        # then we go by test_studies and assert all of them are in the dictionary
        for test_study in test_studies:
            with self.subTest():
                assert_dataclasses_equal(db_studies[test_study.uid], test_study)

    def test__find_all__with_custom_sort_order__success(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            test_studies = [
                create_random_study(
                    repo.generate_uid,
                    new_id_metadata_fixed_values={
                        "project_number": self.created_project.project_number
                    },
                    is_study_after_create=True,
                    author_id="test__find_all__with_custom_sort_order__success",
                )
                for _ in range(0, 10)
            ]
            for study in test_studies:
                repo.save(study)
            repo.close()

        # when
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            all_studies_in_db = repo.find_all(
                page_number=1, page_size=settings.max_int_neo4j - 1
            ).items
            repo.close()

        # then
        # we check if all test_studies are in all_studies_in_db
        # to achieve this we build a dictionary first
        # TODO: would be nice to do the sort order check as well (not doing that currently)
        db_studies: dict[str, StudyDefinitionAR] = {}
        for _study in all_studies_in_db:
            db_studies[_study.uid] = _study

        # then we go by test_studies and assert all of them are in the dictionary
        for test_study in test_studies:
            with self.subTest():
                assert_dataclasses_equal(db_studies[test_study.uid], test_study)

    def test__find_by_id__find_for_update_without_transaction__failure(self):
        # given
        uid = "some-uid"

        # then
        with self.assertRaises(SystemError):
            # when
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            repo.find_by_uid(uid, for_update=True)

    def test__save__after_create_and_closing_transaction__failure(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                author_id=current_function_name(),
            )

        # then
        with self.assertRaises(SystemError):
            # when
            repo.save(study)

    def test__save__after_retrieve_for_update_and_closing_transaction__failure(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                author_id=current_function_name(),
            )
            repo.save(study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            study = repo.find_by_uid(study.uid, for_update=True)

        # then
        with self.assertRaises(SystemError):
            # when
            repo.save(study)

    def test__get_study_id__with_valid_study__returns_study_id(self):
        """Test that get_study_id returns correct study_id when study exists with both prefix and number"""
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        # when
        study_id = StudyDefinitionRepositoryImpl.get_study_id(created_study.uid)

        # then
        expected_id = f"{created_study.current_metadata.id_metadata.study_id_prefix}-{created_study.current_metadata.id_metadata.study_number}"
        assert study_id == expected_id

    def test__get_study_id__with_specific_version__returns_study_id(self):
        """Test that get_study_id returns study_id for a specific version"""
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)

            # Create a locked version
            study_to_lock = repo.find_by_uid(created_study.uid, for_update=True)
            study_to_lock.edit_metadata(
                study_title_exists_callback=lambda _, study_number: False,
                study_short_title_exists_callback=lambda _, study_number: False,
                new_study_description=StudyDescriptionVO.from_input_values(
                    study_title="new_study_title", study_short_title="study_short_title"
                ),
                author_id=current_function_name(),
            )
            repo.save(study_to_lock)
            study_to_lock = repo.find_by_uid(created_study.uid, for_update=True)
            study_to_lock.lock(
                version_description="locked version",
                author_id=current_function_name(),
            )
            repo.save(study_to_lock)
            locked_version = str(
                study_to_lock.current_metadata.ver_metadata.version_number
            )
            repo.close()

        # when
        study_id = StudyDefinitionRepositoryImpl.get_study_id(
            created_study.uid, study_value_version=locked_version
        )

        # then
        expected_id = f"{created_study.current_metadata.id_metadata.study_id_prefix}-{created_study.current_metadata.id_metadata.study_number}"
        assert study_id == expected_id

    def test__get_study_id__with_nonexistent_uid__returns_none(self):
        """Test that get_study_id returns None when study doesn't exist"""
        # given
        non_existent_uid = f"non-existent-uid-{random_str()}"

        # when
        study_id = StudyDefinitionRepositoryImpl.get_study_id(non_existent_uid)

        # then
        assert study_id is None

    def test__get_study_id__with_nonexistent_version__returns_none(self):
        """Test that get_study_id returns None when version doesn't exist"""
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        # when
        study_id = StudyDefinitionRepositoryImpl.get_study_id(
            created_study.uid, study_value_version="999.999"
        )

        # then
        assert study_id is None

    def test__get_study_id__with_missing_study_id_prefix__returns_none(self):
        """Test that get_study_id returns None when study_id_prefix is missing"""
        # given - create study and manually remove study_id_prefix
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        # Manually set study_id_prefix to NULL in database
        db.cypher_query(
            """
            MATCH (sr:StudyRoot {uid: $uid})-[:LATEST]->(sv:StudyValue)
            SET sv.study_id_prefix = NULL
            """,
            {"uid": created_study.uid},
        )

        # when
        study_id = StudyDefinitionRepositoryImpl.get_study_id(created_study.uid)

        # then
        assert study_id is None

    def test__get_study_id__with_missing_study_number__returns_none(self):
        """Test that get_study_id returns None when study_number is missing"""
        # given - create study and manually remove study_number
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        # Manually set study_number to NULL in database
        db.cypher_query(
            """
            MATCH (sr:StudyRoot {uid: $uid})-[:LATEST]->(sv:StudyValue)
            SET sv.study_number = NULL
            """,
            {"uid": created_study.uid},
        )

        # when
        study_id = StudyDefinitionRepositoryImpl.get_study_id(created_study.uid)

        # then
        assert study_id is None

    def test__get_study_id__with_subpart__returns_study_id_with_subpart(self):
        """Test that get_study_id returns study_id including study_subpart_acronym when present"""
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        # Manually add study_subpart_acronym to the study
        study_subpart_acronym = "SUB1"
        db.cypher_query(
            """
            MATCH (sr:StudyRoot {uid: $uid})-[:LATEST]->(sv:StudyValue)
            SET sv.study_subpart_acronym = $study_subpart_acronym
            """,
            {"uid": created_study.uid, "study_subpart_acronym": study_subpart_acronym},
        )

        # when
        study_id = StudyDefinitionRepositoryImpl.get_study_id(created_study.uid)

        # then
        expected_id = f"{created_study.current_metadata.id_metadata.study_id_prefix}-{created_study.current_metadata.id_metadata.study_number}-{study_subpart_acronym}"
        assert study_id == expected_id

    def test__get_study_id__after_release__returns_study_id(self):
        """Test that get_study_id works correctly for released studies"""
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)

            # Release the study
            study_to_release = repo.find_by_uid(created_study.uid, for_update=True)
            study_to_release.release(
                change_description="test release",
                author_id=current_function_name(),
            )
            repo.save(study_to_release)
            repo.close()

        # when
        study_id = StudyDefinitionRepositoryImpl.get_study_id(created_study.uid)

        # then
        expected_id = f"{created_study.current_metadata.id_metadata.study_id_prefix}-{created_study.current_metadata.id_metadata.study_number}"
        assert study_id == expected_id

    def test__retrieve_snapshot__with_study_value_version__returns_locked_snapshot(
        self,
    ):
        """Test that _retrieve_snapshot correctly returns specific version metadata when study_value_version is provided,
        and that LOCKED is preferred over RELEASED when both exist for the same version.
        """

        def can_lock(_: StudyDefinitionAR) -> bool:
            return _.current_metadata.id_metadata.study_id is not None

        # given - create, lock, and then retrieve at specific version
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                condition=can_lock,
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                author_id=current_function_name(),
            )
            repo.save(created_study)

            # Edit to give it a title (required for lock)
            study = repo.find_by_uid(created_study.uid, for_update=True)
            study.edit_metadata(
                study_title_exists_callback=lambda _, study_number: False,
                study_short_title_exists_callback=lambda _, study_number: False,
                new_study_description=StudyDescriptionVO.from_input_values(
                    study_title="Version Test Title", study_short_title="VTT"
                ),
                author_id=current_function_name(),
            )
            repo.save(study)

            # Lock the study
            study = repo.find_by_uid(created_study.uid, for_update=True)
            study.lock(
                version_description="first locked version",
                author_id=current_function_name(),
            )
            repo.save(study)
            locked_version = str(study.current_metadata.ver_metadata.version_number)
            repo.close()

        # when - retrieve with specific version
        with db.transaction:
            repo2 = StudyDefinitionRepositoryImpl(current_function_name())
            study_at_version = repo2.find_by_uid(
                created_study.uid, study_value_version=locked_version
            )
            repo2.close()

        # then - specific metadata should be populated and match locked version
        assert study_at_version is not None
        assert study_at_version.current_metadata is not None
        assert study_at_version.current_metadata.ver_metadata.version_number is not None
        assert (
            str(study_at_version.current_metadata.ver_metadata.version_number)
            == locked_version
        )

    def test__retrieve_snapshot__with_parent_subpart__populates_relationships(self):
        """Test that _retrieve_snapshot correctly populates parent_uid and subpart_uids
        when parent/subpart relationships exist."""
        # given - create a parent study and a subpart study, link them via Cypher
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            parent_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(parent_study)

            subpart_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(subpart_study)
            repo.close()

        # Link parent -> subpart via HAS_STUDY_SUBPART on their LATEST values
        db.cypher_query(
            """
            MATCH (parent_root:StudyRoot {uid: $parent_uid})-[:LATEST]->(parent_val:StudyValue)
            MATCH (sub_root:StudyRoot {uid: $sub_uid})-[:LATEST]->(sub_val:StudyValue)
            MERGE (parent_val)-[:HAS_STUDY_SUBPART]->(sub_val)
            """,
            {"parent_uid": parent_study.uid, "sub_uid": subpart_study.uid},
        )

        # when - retrieve the parent (should have subpart)
        with db.transaction:
            repo2 = StudyDefinitionRepositoryImpl(current_function_name())
            retrieved_parent = repo2.find_by_uid(parent_study.uid)
            repo2.close()

        # then - parent should list the subpart
        assert retrieved_parent is not None
        assert subpart_study.uid in retrieved_parent.study_subpart_uids

        # when - retrieve the subpart (should have parent)
        with db.transaction:
            repo3 = StudyDefinitionRepositoryImpl(current_function_name())
            retrieved_subpart = repo3.find_by_uid(subpart_study.uid)
            repo3.close()

        # then - subpart should reference the parent
        assert retrieved_subpart is not None
        assert retrieved_subpart.study_parent_part_uid == parent_study.uid

    def test__retrieve_data_from_study_value__with_text_type_terms_and_array_fields(
        self,
    ):
        """Test that _retrieve_data_from_study_value correctly handles text fields with
        HAS_TYPE terms and array fields with multiple HAS_TYPE terms."""
        # given - create a study with metadata that populates text and array fields
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        # when - retrieve the study (internally calls _retrieve_data_from_study_value)
        with db.transaction:
            repo2 = StudyDefinitionRepositoryImpl(current_function_name())
            retrieved_study = repo2.find_by_uid(created_study.uid)
            repo2.close()

        # then - metadata should be fully populated and match what was created
        assert retrieved_study is not None
        assert_dataclasses_equal(retrieved_study, created_study)

        # Verify specific field groups are populated
        current = retrieved_study.current_metadata
        assert current.id_metadata.project_number == self.created_project.project_number

    def test__retrieve_data_from_study_value__locked_snapshot_preserves_field_data(
        self,
    ):
        """Test that _retrieve_data_from_study_value correctly retrieves field data
        from a locked StudyValue node, ensuring data is preserved across lock."""

        def can_lock(_: StudyDefinitionAR) -> bool:
            return _.current_metadata.id_metadata.study_id is not None

        # given - create, edit, lock
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                condition=can_lock,
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                author_id=current_function_name(),
            )
            repo.save(created_study)

            study = repo.find_by_uid(created_study.uid, for_update=True)
            study.edit_metadata(
                study_title_exists_callback=lambda _, study_number: False,
                study_short_title_exists_callback=lambda _, study_number: False,
                new_study_description=StudyDescriptionVO.from_input_values(
                    study_title="Locked Field Data Test", study_short_title="LFDT"
                ),
                author_id=current_function_name(),
            )
            repo.save(study)

            study = repo.find_by_uid(created_study.uid, for_update=True)
            study.lock(
                version_description="lock for field data test",
                author_id=current_function_name(),
            )
            repo.save(study)
            locked_version = str(study.current_metadata.ver_metadata.version_number)
            repo.close()

        # when - retrieve at locked version
        with db.transaction:
            repo2 = StudyDefinitionRepositoryImpl(current_function_name())
            study_at_version = repo2.find_by_uid(
                created_study.uid, study_value_version=locked_version
            )
            repo2.close()

        # then - locked snapshot should have the correct field data
        assert study_at_version is not None
        # The locked version's metadata should include our title
        locked_metadata = None
        for lm in study_at_version.get_all_locked_versions():
            if str(lm.ver_metadata.version_number) == locked_version:
                locked_metadata = lm
                break
        assert locked_metadata is not None
        assert locked_metadata.study_description.study_title == "Locked Field Data Test"
        assert locked_metadata.study_description.study_short_title == "LFDT"


@pytest.mark.parametrize(
    ("soa_preferences_input", "expected_preferences"),
    (
        (  # 0
            StudySoaPreferencesInput(),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
                "soa_show_all_visits_lab_table": False,
            },
        ),
        (  # 1
            StudySoaPreferencesInput(show_milestones=True),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": True,
                "baseline_as_time_zero": False,
                "soa_show_all_visits_lab_table": False,
            },
        ),
        (  # 2
            StudySoaPreferencesInput(
                show_milestones=True, show_epochs=False, baseline_as_time_zero=True
            ),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": True,
                "baseline_as_time_zero": True,
                "soa_show_all_visits_lab_table": False,
            },
        ),
        (  # 3
            StudySoaPreferencesInput(show_epochs=True, baseline_as_time_zero=True),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": True,
                "soa_show_all_visits_lab_table": False,
            },
        ),
        (  # 4
            StudySoaPreferencesInput(
                show_epochs=False, show_milestones=False, baseline_as_time_zero=False
            ),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
                "soa_show_all_visits_lab_table": False,
            },
        ),
        (  # 5
            StudySoaPreferencesInput(show_milestones=True, show_epochs=True),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": True,
                "baseline_as_time_zero": False,
                "soa_show_all_visits_lab_table": False,
            },
        ),
        (  # 6
            StudySoaPreferencesInput(show_epochs=True, show_milestones=False),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
                "soa_show_all_visits_lab_table": False,
            },
        ),
        (  # 7
            StudySoaPreferencesInput(
                baseline_as_time_zero=True, show_epochs=True, show_milestones=False
            ),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": True,
                "soa_show_all_visits_lab_table": False,
            },
        ),
        (  # 8
            StudySoaPreferencesInput(baseline_as_time_zero=True),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": True,
                "soa_show_all_visits_lab_table": False,
            },
        ),
    ),
)
def test_post_soa_preferences(
    base_data,
    tst_project: Project,
    soa_preferences_input: StudySoaPreferencesInput,
    expected_preferences: dict[str, bool],
):
    repo: StudyDefinitionRepository = StudyDefinitionRepositoryImpl(user().id())

    study = TestUtils.create_study(project_number=tst_project.project_number)

    # should have four StudySoaPreferencesInput created at Study creation
    nodes = repo.get_soa_preferences(study.uid)
    assert len(nodes) == 4

    unlink_study_soa_properties(study.uid, repo)

    assert not repo.get_soa_preferences(study.uid)

    with db.transaction:
        nodes = repo.post_soa_preferences(study.uid, soa_preferences_input)

    preferences = {node.field_name: node.value for node in nodes}
    assert preferences == expected_preferences


@pytest.mark.parametrize(
    (
        "soa_preferences_initial",
        "soa_preferences_update",
        "expected_preferences",
        "expected_num_actions",
    ),
    (
        (None, StudySoaPreferencesInput(), {}, 4),  # 0
        (  # 1
            StudySoaPreferencesInput(show_epochs=False, show_milestones=True),
            StudySoaPreferencesInput(),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": True,
                "baseline_as_time_zero": False,
                "soa_show_all_visits_lab_table": False,
            },
            8,
        ),
        (  # 2
            StudySoaPreferencesInput(
                show_epochs=False, show_milestones=False, baseline_as_time_zero=False
            ),
            StudySoaPreferencesInput(),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
                "soa_show_all_visits_lab_table": False,
            },
            8,
        ),
        (  # 3
            StudySoaPreferencesInput(
                show_epochs=True, show_milestones=False, baseline_as_time_zero=True
            ),
            StudySoaPreferencesInput(),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": True,
                "soa_show_all_visits_lab_table": False,
            },
            8,
        ),
        (  # 4
            StudySoaPreferencesInput(
                show_epochs=True, show_milestones=True, baseline_as_time_zero=True
            ),
            StudySoaPreferencesInput(),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": True,
                "baseline_as_time_zero": True,
                "soa_show_all_visits_lab_table": False,
            },
            8,
        ),
        (  # 5
            StudySoaPreferencesInput(),
            StudySoaPreferencesInput(),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
                "soa_show_all_visits_lab_table": False,
            },
            8,
        ),
        (  # 6
            StudySoaPreferencesInput(show_milestones=False),
            StudySoaPreferencesInput(show_milestones=False),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
                "soa_show_all_visits_lab_table": False,
            },
            8,
        ),
        (  # 7
            StudySoaPreferencesInput(show_milestones=True, show_epochs=False),
            StudySoaPreferencesInput(show_milestones=True, show_epochs=False),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": True,
                "baseline_as_time_zero": False,
                "soa_show_all_visits_lab_table": False,
            },
            8,
        ),
        (  # 8
            StudySoaPreferencesInput(show_epochs=True),
            StudySoaPreferencesInput(show_milestones=False, show_epochs=False),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
                "soa_show_all_visits_lab_table": False,
            },
            9,
        ),
        (  # 9
            StudySoaPreferencesInput(show_epochs=True),
            StudySoaPreferencesInput(show_epochs=False),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
                "soa_show_all_visits_lab_table": False,
            },
            9,
        ),
        (  # 10
            StudySoaPreferencesInput(show_milestones=True, show_epochs=False),
            StudySoaPreferencesInput(show_epochs=True, show_milestones=False),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
                "soa_show_all_visits_lab_table": False,
            },
            10,
        ),
        (  # 11
            StudySoaPreferencesInput(
                show_milestones=True, show_epochs=False, baseline_as_time_zero=True
            ),
            StudySoaPreferencesInput(show_milestones=True, show_epochs=False),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": True,
                "baseline_as_time_zero": True,
                "soa_show_all_visits_lab_table": False,
            },
            8,
        ),
        (  # 12
            StudySoaPreferencesInput(show_epochs=True, baseline_as_time_zero=False),
            StudySoaPreferencesInput(show_milestones=False, show_epochs=False),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
                "soa_show_all_visits_lab_table": False,
            },
            9,
        ),
        (  # 13
            StudySoaPreferencesInput(show_epochs=True, baseline_as_time_zero=True),
            StudySoaPreferencesInput(show_epochs=False, baseline_as_time_zero=False),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
                "soa_show_all_visits_lab_table": False,
            },
            10,
        ),
        (  # 14
            StudySoaPreferencesInput(show_milestones=True, show_epochs=False),
            StudySoaPreferencesInput(
                show_epochs=True, show_milestones=False, baseline_as_time_zero=True
            ),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": True,
                "soa_show_all_visits_lab_table": False,
            },
            11,
        ),
    ),
)
def test_edit_soa_preferences(
    base_data,
    tst_project: Project,
    soa_preferences_initial: StudySoaPreferencesInput | None,
    soa_preferences_update: StudySoaPreferencesInput,
    expected_preferences: dict[str, bool],
    expected_num_actions: int,
):
    repo: StudyDefinitionRepository = StudyDefinitionRepositoryImpl(user().id())

    study = TestUtils.create_study(project_number=tst_project.project_number)

    unlink_study_soa_properties(study.uid, repo)

    if soa_preferences_initial:
        with db.transaction:
            repo.post_soa_preferences(study.uid, soa_preferences_initial)

    with db.transaction:
        nodes = repo.edit_soa_preferences(study.uid, soa_preferences_update)

    preferences = {node.field_name: node.value for node in nodes}
    assert preferences == expected_preferences

    actions = _get_study_soa_preferences_audit_trail_actions(study.uid, repo)
    assert len(actions) == expected_num_actions

    for action in actions:
        if action.action == "Create":
            assert action.before_value is None
        if action.action == "Edit":
            assert action.before_value is not None
        assert action.after_value is not None


def _get_study_soa_preferences_audit_trail_actions(
    study_uid: str, repo: StudyDefinitionRepository
) -> list[StudyFieldAuditTrailAction]:
    """Gets audit trail actions on StudySoaPreferences fields"""

    trails = repo.get_audit_trail_by_uid(study_uid)
    trails.sort(key=lambda x: x.date)

    actions = [
        action
        for trail in trails
        for action in trail.actions
        if action.field_name in settings.study_soa_preferences_fields
    ]

    return actions


def unlink_study_soa_properties(
    study_uid: str, repo: StudyDefinitionRepository | None = None
):
    """Removes existing StudySoaPreferences"""

    if repo is None:
        repo = StudyDefinitionRepositoryImpl(user().id())

    latest_study_value = StudyRoot.nodes.get(uid=study_uid).latest_value.single()

    for node in repo.get_soa_preferences(study_uid):
        latest_study_value.has_boolean_field.disconnect(node)
