from neomodel import db

from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudySourceVariable as StudySourceVariableNeomodel,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySourceVariable,
    StudySourceVariableInput,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import ensure_transaction
from common import exceptions
from common.auth.user import user


class StudySourceVariableService:
    _repos: MetaRepository

    def __init__(self):
        self._repos = MetaRepository()
        self.author = user().id()

    def check_if_study_exists(self, study_uid: str):
        exceptions.NotFoundException.raise_if_not(
            self._repos.study_definition_repository.study_exists_by_uid(
                study_uid=study_uid
            ),
            "Study",
            study_uid,
        )

    def get_study_source_variable(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> StudySourceVariable | None:
        self.check_if_study_exists(study_uid=study_uid)
        study_source_variable_node = (
            self._repos.study_source_variable_repository.get_study_source_variable(
                study_uid=study_uid, study_value_version=study_value_version
            )
        )
        return (
            StudySourceVariable.model_validate(study_source_variable_node)
            if study_source_variable_node
            else None
        )

    @ensure_transaction(db)
    def create(
        self, study_uid: str, study_source_variable_input: StudySourceVariableInput
    ) -> StudySourceVariable:
        self.check_if_study_exists(study_uid=study_uid)
        exceptions.AlreadyExistsException.raise_if(
            self._repos.study_source_variable_repository.get_study_source_variable(
                study_uid=study_uid, for_update=True
            ),
            msg=f"StudySourceVariable already exist for Study with UID '{study_uid}'",
        )
        study_source_variable_node = (
            self._repos.study_source_variable_repository.post_study_source_variable(
                study_uid=study_uid,
                study_source_variable_input=study_source_variable_input,
                author_id=self.author,
            )
        )
        return StudySourceVariable.model_validate(study_source_variable_node)

    @ensure_transaction(db)
    def edit(
        self, study_uid: str, study_source_variable_input: StudySourceVariableInput
    ) -> StudySourceVariable:
        self.check_if_study_exists(study_uid=study_uid)
        previous_node: StudySourceVariableNeomodel | None = (
            self._repos.study_source_variable_repository.get_study_source_variable(
                study_uid=study_uid, for_update=True
            )
        )
        if previous_node is None:
            raise exceptions.NotFoundException(
                msg=f"The StudySourceVariable node for Study with UID '{study_uid}' doesn't exist."
            )

        if (
            previous_node.source_variable != study_source_variable_input.source_variable
            or previous_node.source_variable_description
            != study_source_variable_input.source_variable_description
        ):
            study_source_variable_node = (
                self._repos.study_source_variable_repository.edit_study_source_variable(
                    study_uid=study_uid,
                    study_source_variable_input=study_source_variable_input,
                    previous_node=previous_node,
                    author_id=self.author,
                )
            )
        else:
            study_source_variable_node = previous_node
        return StudySourceVariable.model_validate(study_source_variable_node)
