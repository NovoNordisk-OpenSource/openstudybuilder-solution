# pylint: disable=invalid-name
from neomodel import db

from clinical_mdr_api.domain_repositories.data_completeness_tags_repository import (
    DataCompletenessTagRepository,
)
from clinical_mdr_api.models.data_completeness_tag import (
    DataCompletenessTag,
    DataCompletenessTagInput,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import ensure_transaction
from common.exceptions import AlreadyExistsException, NotFoundException


class DataCompletenessTagService:
    repo: DataCompletenessTagRepository
    _repos: MetaRepository

    def __init__(self) -> None:
        self.repo = DataCompletenessTagRepository()
        self._repos = MetaRepository()

    def get_all_data_completeness_tags(self) -> list[DataCompletenessTag]:
        return self.repo.retrieve_all_data_completeness_tags()

    @ensure_transaction(db)
    def create_data_completeness_tag(
        self,
        data_completeness_tag_input: DataCompletenessTagInput,
    ) -> DataCompletenessTag:
        AlreadyExistsException.raise_if(
            self.repo.find_data_completeness_tag_by_name(
                data_completeness_tag_input.name
            ),
            "Data Completeness Tag",
            data_completeness_tag_input.name,
            "Name",
        )

        return self.repo.create_data_completeness_tag(
            name=data_completeness_tag_input.name,
        )

    @ensure_transaction(db)
    def update_data_completeness_tag(
        self,
        uid: str,
        data_completeness_tag_input: DataCompletenessTagInput,
    ) -> DataCompletenessTag:
        return self.repo.update_data_completeness_tag(
            uid=uid, name=data_completeness_tag_input.name
        )

    @ensure_transaction(db)
    def delete_data_completeness_tag(self, uid: str) -> None:
        return self.repo.delete_data_completeness_tag(uid)

    def get_tags_for_study(self, study_uid: str) -> list[DataCompletenessTag]:
        return self.repo.get_tags_for_study(study_uid)

    @ensure_transaction(db)
    def assign_tag_to_study(self, study_uid: str, tag_uid: str) -> DataCompletenessTag:
        NotFoundException.raise_if_not(
            self._repos.study_definition_repository.study_exists_by_uid(study_uid),
            "Study",
            study_uid,
        )
        return self.repo.assign_tag_to_study(study_uid=study_uid, tag_uid=tag_uid)

    @ensure_transaction(db)
    def remove_tag_from_study(self, study_uid: str, tag_uid: str) -> None:
        NotFoundException.raise_if_not(
            self._repos.study_definition_repository.study_exists_by_uid(study_uid),
            "Study",
            study_uid,
        )
        return self.repo.remove_tag_from_study(study_uid=study_uid, tag_uid=tag_uid)
