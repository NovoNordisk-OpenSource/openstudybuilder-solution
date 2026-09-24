from neomodel import db

from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyDesignClass as StudyDesignClassNeomodel,
)
from clinical_mdr_api.domains.enums import StudyDesignClassEnum
from clinical_mdr_api.domains.study_selections.study_selection_branch_arm import (
    StudySelectionBranchArmAR,
)
from clinical_mdr_api.domains.study_selections.study_selection_cohort import (
    StudySelectionCohortAR,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyDesignClass,
    StudyDesignClassInput,
    StudySourceVariableInput,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import ensure_transaction
from clinical_mdr_api.services.studies.study_source_variable import (
    StudySourceVariableService,
)
from common import exceptions
from common.auth.user import user


class StudyDesignClassService:
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

    @ensure_transaction(db)
    def get_study_design_class(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> StudyDesignClass:
        self.check_if_study_exists(study_uid=study_uid)
        study_design_class_node = (
            self._repos.study_design_class_repository.get_study_design_class(
                study_uid=study_uid, study_value_version=study_value_version
            )
        )
        # If Study Design Class does not exist we should return Study Design Class defaulter to 'Manual' value
        if not study_design_class_node:
            if study_value_version:
                raise exceptions.NotFoundException(
                    msg=f"The StudyDesignClass node for Study with UID '{study_uid}' and study value version '{study_value_version}' doesn't exist."
                )
            return self.create(
                study_uid=study_uid,
                study_design_class_input=StudyDesignClassInput(
                    value=StudyDesignClassEnum.MANUAL
                ),
            )

        return StudyDesignClass.model_validate(study_design_class_node)

    def is_study_design_class_edition_allowed(
        self,
        study_uid: str,
    ) -> bool:
        self.check_if_study_exists(study_uid=study_uid)
        return self._repos.study_design_class_repository.is_study_design_class_edition_allowed(
            study_uid=study_uid
        )

    @ensure_transaction(db)
    def create(
        self, study_uid: str, study_design_class_input: StudyDesignClassInput
    ) -> StudyDesignClass:
        self.check_if_study_exists(study_uid=study_uid)
        exceptions.AlreadyExistsException.raise_if(
            self._repos.study_design_class_repository.get_study_design_class(
                study_uid=study_uid
            ),
            msg=f"StudyDesignClass already exist for Study with UID '{study_uid}'",
        )
        study_design_class_node = (
            self._repos.study_design_class_repository.post_study_design_class(
                study_uid=study_uid,
                study_design_class_input=study_design_class_input,
                author_id=self.author,
            )
        )
        return StudyDesignClass.model_validate(study_design_class_node)

    @ensure_transaction(db)
    def edit(
        self, study_uid: str, study_design_class_input: StudyDesignClassInput
    ) -> StudyDesignClass:
        self.check_if_study_exists(study_uid=study_uid)
        previous_node: StudyDesignClassNeomodel | None = (
            self._repos.study_design_class_repository.get_study_design_class(
                study_uid=study_uid
            )
        )
        if previous_node is None:
            raise exceptions.NotFoundException(
                msg=f"The StudyDesignClass node for Study with UID '{study_uid}' doesn't exist."
            )

        if previous_node.value != study_design_class_input.value:
            study_design_class_node = (
                self._repos.study_design_class_repository.edit_study_design_class(
                    study_uid=study_uid,
                    study_design_class_input=study_design_class_input,
                    previous_node=previous_node,
                    author_id=self.author,
                )
            )
            # The StudyBranchArms should be removed in both cases when we are switching:
            # - from Cohort stepper into Study with arms only as there we don't need StudyBranchArms
            # - from Study with arms only into Cohort stepper as Cohort stepper needs to define StudyBranchArms in the new model
            branch_arm_aggregate: StudySelectionBranchArmAR = (
                self._repos.study_branch_arm_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )
            for study_branch_arm in branch_arm_aggregate.study_branch_arms_selection:
                branch_arm_aggregate.remove_branch_arm_selection(
                    study_branch_arm.study_selection_uid
                )

            self._repos.study_branch_arm_repository.save(
                branch_arm_aggregate, self.author
            )
            # When we are switching from Cohort stepper into Study with arms only
            if (
                previous_node.value
                == StudyDesignClassEnum.STUDY_WITH_COHORTS_BRANCHES_AND_SUBPOPULATIONS.value
                and study_design_class_input.value.value
                == StudyDesignClassEnum.MANUAL.value
            ):
                # Remove all StudyCohorts from the Study as switching to Study with arms only and StudyCohorts are not needed there
                cohort_aggregate: StudySelectionCohortAR = (
                    self._repos.study_cohort_repository.find_by_study(
                        study_uid=study_uid, for_update=True
                    )
                )
                for study_cohort in cohort_aggregate.study_cohorts_selection:
                    cohort_aggregate.remove_cohort_selection(
                        study_cohort.study_selection_uid
                    )
                self._repos.study_cohort_repository.save(cohort_aggregate, self.author)
                if self._repos.study_source_variable_repository.source_variable_exists(
                    study_uid=study_uid
                ):
                    study_source_variable_service = StudySourceVariableService()
                    study_source_variable_service.edit(
                        study_uid=study_uid,
                        study_source_variable_input=StudySourceVariableInput(
                            source_variable=None, source_variable_description=None
                        ),
                    )
        else:
            study_design_class_node = previous_node
        return StudyDesignClass.model_validate(study_design_class_node)
