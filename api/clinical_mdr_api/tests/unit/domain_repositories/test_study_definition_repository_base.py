import copy
import random
import unittest
from dataclasses import dataclass, field
from typing import AbstractSet, Any, Callable, Generic, Sequence, TypeVar, cast

from clinical_mdr_api.domain_repositories.models.study_field import StudyBooleanField
from clinical_mdr_api.domain_repositories.study_definitions.study_definition_repository import (
    StudyDefinitionRepository,
)
from clinical_mdr_api.domains.study_definition_aggregates.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domains.study_definition_aggregates.root import (
    StudyDefinitionAR,
    StudyDefinitionSnapshot,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyDescriptionVO,
    StudyFieldAuditTrailEntryAR,
    StudyIdentificationMetadataVO,
    StudyStatus,
)
from clinical_mdr_api.models.study_selections.study import (
    StudyPreferredTimeUnit,
    StudySoaPreferencesInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._utils import service_level_generic_filtering
from clinical_mdr_api.tests.unit.domain.utils import random_str
from common.exceptions import BusinessLogicException

T = TypeVar("T")


@dataclass
class GenericInMemoryDB(Generic[T]):
    _db: dict[str, Any] = field(init=False, default_factory=dict)

    def find_by_id(self, aggregate_id: str) -> T | None:
        serialized_form_of_aggregate = self._db.get(aggregate_id)
        if serialized_form_of_aggregate is None:
            return None
        return self._deserialize_aggregate_from_storage(serialized_form_of_aggregate)

    def find_by_filter(self, filter_callback: Callable[[T], bool]) -> list[T]:
        return [x for x in self.get_all_instances() if filter_callback(x)]

    def get_all_ids(self) -> AbstractSet[str]:
        return self._db.keys()

    def get_all_instances(self) -> list[T]:
        return [cast(T, self.find_by_id(uid)) for uid in self.get_all_ids()]

    def _get_id_for_aggregate(self, aggregate: T) -> str:
        """
        abstract method for concrete repositories to implement extracting id from an aggregate
        """
        raise NotImplementedError

    def _serialize_aggregate_for_storage(self, aggregate: T) -> Any:
        """
        abstract method for concrete repositories to implement extracting some representation for storage
        """
        raise NotImplementedError

    def _deserialize_aggregate_from_storage(self, serialized: Any) -> T:
        """
        abstract method for concrete repositories to implement extracting some representation for storage
        """
        raise NotImplementedError

    def save(self, aggregate_instance: T) -> None:
        aggregate_id: str = self._get_id_for_aggregate(aggregate_instance)
        serialized_form_of_aggregate = self._serialize_aggregate_for_storage(
            aggregate_instance
        )
        self._db[aggregate_id] = serialized_form_of_aggregate


class TestGenericInMemoryDB(unittest.TestCase):
    def test__generic_in_memory_db(self):
        # given
        class StringRepo(GenericInMemoryDB[str]):
            def _get_id_for_aggregate(self, aggregate: str) -> str:
                return aggregate[0:2]

            def _serialize_aggregate_for_storage(self, aggregate: str) -> Any:
                return aggregate

            def _deserialize_aggregate_from_storage(self, serialized: Any) -> str:
                return str(serialized)

        repo = StringRepo()
        test_set = ["00-something", "01-other-thing", "02-yet-another-thing", "FF_g"]

        # when
        for value in test_set:
            repo.save(value)

        # then
        expected_ids = {"00", "01", "02", "FF"}
        self.assertEqual(repo.get_all_instances(), test_set)
        self.assertEqual(repo.get_all_ids(), expected_ids)
        self.assertEqual(repo.find_by_filter(lambda x: x.isidentifier()), ["FF_g"])


class StudyDefinitionsDBFake(GenericInMemoryDB[StudyDefinitionSnapshot]):
    """
    Simple in memory database to underpin. MemoryBasedStudyDefinitionsRepository for testing purposes.
    """

    def _get_id_for_aggregate(self, aggregate: StudyDefinitionSnapshot) -> str:
        return aggregate.uid

    def _serialize_aggregate_for_storage(
        self, aggregate: StudyDefinitionSnapshot
    ) -> Any:
        return copy.deepcopy(aggregate)

    def _deserialize_aggregate_from_storage(
        self, serialized: Any
    ) -> StudyDefinitionSnapshot:
        return copy.deepcopy(serialized)


class StudyDefinitionRepositoryFake(StudyDefinitionRepository):
    def check_if_study_is_deleted(self, study_uid: str) -> bool:
        return False

    def check_if_study_is_locked(self, study_uid: str) -> bool:
        return False

    @staticmethod
    def check_if_study_uid_and_version_exists(
        study_uid: str, study_value_version: str | None = None
    ) -> bool:
        return True

    def get_preferred_time_unit(
        self,
        study_uid: str,
        for_protocol_soa: bool = False,
        study_value_version: str | None = None,
    ) -> StudyPreferredTimeUnit:
        return NotImplementedError()

    def post_preferred_time_unit(
        self, study_uid: str, unit_definition_uid: str, for_protocol_soa: bool = False
    ) -> StudyPreferredTimeUnit:
        return NotImplementedError

    def edit_preferred_time_unit(
        self, study_uid: str, unit_definition_uid: str, for_protocol_soa: bool = False
    ) -> StudyPreferredTimeUnit:
        return NotImplementedError()

    def study_exists_by_uid(self, study_uid: str) -> bool:
        snapshot: StudyDefinitionSnapshot | None = self._simulated_db.find_by_id(
            study_uid
        )
        return bool(snapshot)

    _simulated_db: StudyDefinitionsDBFake

    def __init__(self, _simulated_db: StudyDefinitionsDBFake):
        super().__init__()
        self._simulated_db = _simulated_db

    def _retrieve_snapshot_by_uid(
        self,
        uid: str,
        for_update: bool,
        study_value_version: str | None = None,
    ) -> tuple[StudyDefinitionSnapshot | None, Any]:
        snapshot: StudyDefinitionSnapshot | None = self._simulated_db.find_by_id(uid)
        additional_closure: Any = None
        if snapshot is not None:
            if for_update:
                additional_closure = copy.deepcopy(snapshot)
        return snapshot, additional_closure

    def _save(
        self,
        snapshot: StudyDefinitionSnapshot,
        additional_closure: Any,
        is_subpart_relationship_update: bool = False,
    ) -> None:
        # we do primitive form of optimistic locking (which works only if we assume single threaded processing)
        assert snapshot.uid is not None
        BusinessLogicException.raise_if(
            additional_closure != self._simulated_db.find_by_id(snapshot.uid),
            msg="Optimistic lock failure",
        )
        self._simulated_db.save(snapshot)

    def _create(self, snapshot: StudyDefinitionSnapshot) -> None:
        # we do primitive uniqueness check on key (works only in single threaded environment)
        assert snapshot.uid is not None
        BusinessLogicException.raise_if(
            self._simulated_db.find_by_id(snapshot.uid),
            msg="Attempt to create a study with non-unique uid.",
        )
        self._simulated_db.save(snapshot)

    def _retrieve_all_snapshots(
        self,
        has_study_footnote: bool | None = None,
        has_study_objective: bool | None = None,
        has_study_endpoint: bool | None = None,
        has_study_criteria: bool | None = None,
        has_study_activity: bool | None = None,
        has_study_activity_instruction: bool | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        deleted: bool = False,
    ) -> GenericFilteringReturn[StudyDefinitionSnapshot]:
        everything: list[StudyDefinitionSnapshot] = list(
            self._simulated_db.get_all_instances()
        )
        filtered_items = service_level_generic_filtering(
            items=everything,
            filter_by=filter_by,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        return filtered_items

    def generate_uid(self) -> str:
        return random_str()

    def _retrieve_fields_audit_trail(
        self, uid: str
    ) -> list[StudyFieldAuditTrailEntryAR] | None:
        raise NotImplementedError("Study fields audit trail is not yet mocked.")

    def _retrieve_study_subpart_with_history(
        self,
        uid: str,
        is_subpart: bool = False,
        study_value_version: str | None = None,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
    ):
        raise NotImplementedError("Study Subpart audit trail is not yet mocked.")

    @staticmethod
    def get_soa_preferences(
        study_uid: str,
        study_value_version: str | None = None,
        field_names: Sequence[str] | None = None,
    ) -> list[StudyBooleanField]:
        raise NotImplementedError("get_soa_preferences")

    def post_soa_preferences(
        self,
        study_uid: str,
        soa_preferences: StudySoaPreferencesInput,
    ) -> list[StudyBooleanField]:
        return []

    def edit_soa_preferences(
        self,
        study_uid: str,
        soa_preferences: StudySoaPreferencesInput,
    ) -> list[StudyBooleanField]:
        raise NotImplementedError("edit_soa_preferences")

    @staticmethod
    def get_soa_split_uids(
        study_uid: str,
        study_value_version: str | None,
    ):
        return None

    def add_soa_split_uid(
        self,
        study_uid: str,
        uid: str,
    ):
        raise NotImplementedError("add_soa_split_uid")

    def remove_soa_split_uid(
        self,
        study_uid: str,
        uid: str,
    ):
        return None

    def remove_soa_splits(
        self,
        study_uid: str,
    ) -> None:
        return

    @staticmethod
    def get_study_id(
        study_uid: str, study_value_version: str | None = None
    ) -> str | None:
        return None


def _random_study_number() -> str:
    choice = [str(_) for _ in range(0, 10)]
    return (
        random.choice(choice)
        + random.choice(choice)
        + random.choice(choice)
        + random.choice(choice)
    )


class TestStudyDefinitionsRepositoryBase(unittest.TestCase):
    @staticmethod
    def make_random_study_edit(study: StudyDefinitionAR):
        new_id_metadata = StudyIdentificationMetadataVO.from_input_values(
            study_number=study.current_metadata.id_metadata.study_number,
            subpart_id=None,
            study_acronym=random_str(),
            description=random_str(),
            registry_identifiers=RegistryIdentifiersVO.from_input_values(
                ct_gov_id=random_str(),
                eudract_id=random_str(),
                universal_trial_number_utn=random_str(),
                japanese_trial_registry_id_japic=random_str(),
                investigational_new_drug_application_number_ind=random_str(),
                eu_trial_number=random_str(),
                civ_id_sin_number=random_str(),
                national_clinical_trial_number=random_str(),
                japanese_trial_registry_number_jrct=random_str(),
                national_medical_products_administration_nmpa_number=random_str(),
                eudamed_srn_number=random_str(),
                investigational_device_exemption_ide_number=random_str(),
                eu_pas_number=random_str(),
                ct_gov_id_null_value_code=None,
                eudract_id_null_value_code=None,
                universal_trial_number_utn_null_value_code=None,
                japanese_trial_registry_id_japic_null_value_code=None,
                investigational_new_drug_application_number_ind_null_value_code=None,
                eu_trial_number_null_value_code=None,
                civ_id_sin_number_null_value_code=None,
                national_clinical_trial_number_null_value_code=None,
                japanese_trial_registry_number_jrct_null_value_code=None,
                national_medical_products_administration_nmpa_number_null_value_code=None,
                eudamed_srn_number_null_value_code=None,
                investigational_device_exemption_ide_number_null_value_code=None,
                eu_pas_number_null_value_code=None,
            ),
            project_number=random_str(),
        )
        study.edit_metadata(
            new_id_metadata=new_id_metadata,
            project_exists_callback=lambda _: True,
            author_id=random_str(),
        )

    @staticmethod
    def create_random_study() -> StudyDefinitionAR:
        new_id_metadata = StudyIdentificationMetadataVO.from_input_values(
            study_number=_random_study_number(),
            subpart_id=None,
            study_acronym=random_str(),
            description=random_str(),
            registry_identifiers=RegistryIdentifiersVO.from_input_values(
                ct_gov_id=random_str(),
                eudract_id=random_str(),
                universal_trial_number_utn=random_str(),
                japanese_trial_registry_id_japic=random_str(),
                investigational_new_drug_application_number_ind=random_str(),
                eu_trial_number=random_str(),
                civ_id_sin_number=random_str(),
                national_clinical_trial_number=random_str(),
                japanese_trial_registry_number_jrct=random_str(),
                national_medical_products_administration_nmpa_number=random_str(),
                eudamed_srn_number=random_str(),
                investigational_device_exemption_ide_number=random_str(),
                eu_pas_number=random_str(),
                ct_gov_id_null_value_code=None,
                eudract_id_null_value_code=None,
                universal_trial_number_utn_null_value_code=None,
                japanese_trial_registry_id_japic_null_value_code=None,
                investigational_new_drug_application_number_ind_null_value_code=None,
                eu_trial_number_null_value_code=None,
                civ_id_sin_number_null_value_code=None,
                national_clinical_trial_number_null_value_code=None,
                japanese_trial_registry_number_jrct_null_value_code=None,
                national_medical_products_administration_nmpa_number_null_value_code=None,
                eudamed_srn_number_null_value_code=None,
                investigational_device_exemption_ide_number_null_value_code=None,
                eu_pas_number_null_value_code=None,
            ),
            project_number=random_str(),
        )
        return StudyDefinitionAR.from_initial_values(
            # pylint: disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
            initial_id_metadata=new_id_metadata,
            project_exists_callback=lambda _: True,
            study_number_exists_callback=lambda _x, y: False,
            study_title_exists_callback=lambda _, study_number: False,
            study_short_title_exists_callback=lambda _, study_number: False,
            author_id=random_str(),
        )

    @staticmethod
    def prepare_random_study() -> StudyDefinitionAR:
        """
        Function prepares random Study for testing having (on average) 5 locked versions.
        One third chance of being in LOCKED state.
        One third of being DRAFT without any RELEASED version.
        One third of being DRAFT and having RELEASED version.
        :return: StudyDefinitionAR
        """
        study = TestStudyDefinitionsRepositoryBase.create_random_study()
        while random.random() > 0.2:
            study.edit_metadata(
                study_title_exists_callback=lambda _, study_number: False,
                study_short_title_exists_callback=lambda _, study_number: False,
                new_study_description=StudyDescriptionVO.from_input_values(
                    study_title="new_study_title", study_short_title="study_short_title"
                ),
                author_id=random_str(),
            )
            study.lock(version_description=random_str(), author_id=random_str())
            study.unlock(random_str())
            TestStudyDefinitionsRepositoryBase.make_random_study_edit(study)
        if random.random() < 0.667:
            if random.random() < 0.5:
                study.release(
                    change_description="making a release in test",
                    author_id=random_str(),
                )
                TestStudyDefinitionsRepositoryBase.make_random_study_edit(study)
            else:
                study.edit_metadata(
                    study_title_exists_callback=lambda _, study_number: False,
                    study_short_title_exists_callback=lambda _, study_number: False,
                    new_study_description=StudyDescriptionVO.from_input_values(
                        study_title="new_study_title",
                        study_short_title="study_short_title",
                    ),
                    author_id=random_str(),
                )
                study.lock(version_description=random_str(), author_id=random_str())
        return study

    def test__save__new_instance__results(self):
        test_data = [
            TestStudyDefinitionsRepositoryBase.prepare_random_study()
            for _ in range(0, 100)
        ]
        test_db = StudyDefinitionsDBFake()
        for test_study in test_data:
            with self.subTest():
                # given
                studies_repository = StudyDefinitionRepositoryFake(test_db)

                # when
                studies_repository.save(test_study)

                # then
                self.assertEqual(
                    test_db.find_by_id(test_study.uid), test_study.get_snapshot()
                )
                self.assertEqual(
                    test_study.repository_closure_data.not_for_update, True
                )

    def test__save__modified_instance__results(self):
        test_data = [
            TestStudyDefinitionsRepositoryBase.prepare_random_study()
            for _ in range(0, 100)
        ]
        test_db = StudyDefinitionsDBFake()
        for item in test_data:
            test_db.save(item.get_snapshot())

        for uid in test_db.get_all_ids():
            with self.subTest():
                # given
                studies_repository = StudyDefinitionRepositoryFake(test_db)
                modified_study = studies_repository.find_by_uid(
                    uid=uid, for_update=True
                )
                # we can edit study only in DRAFT state, otherwise we can only unlock it
                if (
                    modified_study.current_metadata.ver_metadata.study_status
                    == StudyStatus.DRAFT
                ):
                    TestStudyDefinitionsRepositoryBase.make_random_study_edit(
                        modified_study
                    )
                else:
                    modified_study.unlock(random_str())

                # when
                studies_repository.save(modified_study)

                # then
                self.assertEqual(test_db.find_by_id(uid), modified_study.get_snapshot())
                self.assertEqual(
                    modified_study.repository_closure_data.not_for_update, True
                )

    def test__get_all__results(self):
        test_data = [
            TestStudyDefinitionsRepositoryBase.prepare_random_study()
            for _ in range(0, 100)
        ]
        test_db = StudyDefinitionsDBFake()
        for item in test_data:
            test_db.save(item.get_snapshot())
        test_tuples = [(1, 5), (10, 5), (3, 7), (3, 2), (100000, 67)]
        for test_tuple in test_tuples:
            with self.subTest():
                # given
                studies_repo = StudyDefinitionRepositoryFake(test_db)
                page_number = test_tuple[0]
                page_size = test_tuple[1]

                # when
                results = studies_repo.find_all(
                    page_number=page_number, page_size=page_size
                ).items

                # then
                # since we are testing base class test only what is dependent on base class
                expected_result_in_form_of_snapshots = (
                    studies_repo._retrieve_all_snapshots(
                        page_number=page_number, page_size=page_size
                    ).items
                )
                self.assertEqual(
                    [r.get_snapshot() for r in results],
                    expected_result_in_form_of_snapshots,
                )
                for result in results:
                    self.assertEqual(
                        result.repository_closure_data.not_for_update, True
                    )
                    self.assertIs(
                        result.repository_closure_data.repository, studies_repo
                    )
                    self.assertIsNone(result.repository_closure_data.additional_closure)
