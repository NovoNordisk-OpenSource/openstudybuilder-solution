import datetime
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Self

from clinical_mdr_api.services.user_info import UserInfoService
from clinical_mdr_api.utils import normalize_string
from common import exceptions


@dataclass(frozen=True)
class StudySelectionCohortVO:
    """
    The StudySelectionCohortVO acts as the value object for a single selection between a study and an cohort
    """

    study_selection_uid: str
    study_uid: str | None
    name: str
    short_name: str
    code: str | None
    description: str | None
    number_of_subjects: int | None
    branch_arm_root_uids: list[str] | None
    arm_root_uids: list[str] | None
    start_date: datetime.datetime = field(compare=False)
    author_id: str
    end_date: datetime.datetime | None
    status: str | None
    change_type: str | None
    author_username: str | None = None
    accepted_version: bool = False

    @classmethod
    def from_input_values(
        cls,
        author_id: str,
        name: str,
        short_name: str,
        study_selection_uid: str | None = None,
        study_uid: str | None = None,
        code: str | None = None,
        description: str | None = None,
        number_of_subjects: int | None = 0,
        branch_arm_root_uids: list[str] | None = None,
        arm_root_uids: list[str] | None = None,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
        status: str | None = None,
        change_type: str | None = None,
        accepted_version: bool = False,
        generate_uid_callback: Callable[[], str] = lambda: "",
    ):
        """
        Factory method
        :param study_uid
        :param study_selection_uid
        :param name
        :param short_name
        :param code
        :param description
        :param number_of_subjects
        :param start_date
        :param author_id
        :param end_date
        :param status
        :param change_type
        :param accepted_version
        :return:
        """
        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now(datetime.timezone.utc)

        # returns a new instance of the VO

        return StudySelectionCohortVO(
            study_uid=study_uid,
            study_selection_uid=normalize_string(study_selection_uid),
            name=name,
            short_name=short_name,
            code=code,
            description=description,
            number_of_subjects=number_of_subjects,
            branch_arm_root_uids=branch_arm_root_uids,
            arm_root_uids=arm_root_uids,
            start_date=start_date,
            author_id=author_id,
            author_username=UserInfoService.get_author_username_from_id(author_id),
            end_date=end_date,
            status=status,
            change_type=change_type,
            accepted_version=accepted_version,
        )

    def validate(
        self,
        study_arm_exists_callback: Callable[[str], bool] = lambda _: True,
        study_branch_arm_exists_callback: Callable[
            [str, str], bool
        ] = lambda x, y: True,
        cohort_exists_callback_by: Callable[
            [str, str, "StudySelectionCohortVO"], bool
        ] = lambda x, y, z: True,
    ) -> None:
        """
        Validating business logic for a VO
        :param study_arm_exists_callback:
        :param study_branch_arm_exists_callback:
        :param cohort_exists_callback_by:
        :return:
        """
        # Check if there exist a StudyBranchArm with the selected uid
        if self.branch_arm_root_uids:
            for branch_arm_root_uid in self.branch_arm_root_uids:
                exceptions.ValidationException.raise_if(
                    self.study_uid
                    and not study_branch_arm_exists_callback(
                        self.study_uid, branch_arm_root_uid
                    ),
                    msg=f"There is no approved Branch Arm with UID '{branch_arm_root_uid}'.",
                )
        if self.arm_root_uids:
            for arm_root_uid in self.arm_root_uids:
                # Check if there exist a StudyArm with the selected uid
                exceptions.ValidationException.raise_if_not(
                    study_arm_exists_callback(arm_root_uid),
                    msg=f"There is no approved Arm with UID '{arm_root_uid}'.",
                )

        # check if the specified Name is already used
        exceptions.ValidationException.raise_if(
            self.name and cohort_exists_callback_by("name", "name", self),
            msg=f"Value '{self.name}' in field Cohort Name is not unique for the study.",
        )

        # check if the specified Short Name is already used
        exceptions.ValidationException.raise_if(
            self.short_name
            and cohort_exists_callback_by("short_name", "short_name", self),
            msg=f"Value '{self.short_name}' in field Cohort Short Name is not unique for the study.",
        )

        # check if the specified code is already used
        exceptions.ValidationException.raise_if(
            self.code and cohort_exists_callback_by("cohort_code", "code", self),
            msg=f"Value '{self.code}' in field Cohort code is not unique for the study.",
        )


@dataclass
class StudySelectionCohortAR:
    _study_uid: str
    _study_cohorts_selection: tuple[StudySelectionCohortVO, ...]
    # a dataclass feature that has Any value with a type field NOT included on the
    # generated init method, NOT included con copare generated methods, included on
    # the string returned by the generated method, and its default is None
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    def get_specific_object_selection(
        self, study_selection_uid: str
    ) -> tuple[StudySelectionCohortVO, int]:
        for order, selection in enumerate(self.study_cohorts_selection, start=1):
            if selection.study_selection_uid == study_selection_uid:
                return selection, order

        raise exceptions.NotFoundException(
            msg=f"The Study Selection with UID '{study_selection_uid}' doesn't exist for Study with UID '{self._study_uid}'."
        )

    @property
    def study_uid(self) -> str:
        return self._study_uid

    @property
    def study_cohorts_selection(self) -> tuple[StudySelectionCohortVO, ...]:
        return self._study_cohorts_selection

    def get_specific_cohort_selection(
        self, study_cohort_uid: str
    ) -> tuple[StudySelectionCohortVO, int]:
        exceptions.NotFoundException.raise_if(
            study_cohort_uid
            not in [x.study_selection_uid for x in self.study_cohorts_selection],
            "Study Cohort",
            study_cohort_uid,
        )

        for order, selection in enumerate(self.study_cohorts_selection, start=1):
            if selection.study_selection_uid == study_cohort_uid:
                return selection, order
        raise exceptions.NotFoundException(
            msg=f"There is no selection between the Study Cohort with UID '{study_cohort_uid}' and the study."
        )

    def _add_selection(self, study_cohort_selection) -> None:
        new_selections = self._study_cohorts_selection + (study_cohort_selection,)
        self._study_cohorts_selection = new_selections

    def add_cohort_selection(
        self,
        study_cohort_selection: StudySelectionCohortVO,
        study_arm_exists_callback: Callable[[str], bool] = lambda _: True,
        study_branch_arm_exists_callback: Callable[
            [str, str], bool
        ] = lambda x, y: True,
        cohort_exists_callback_by: Callable[
            [str, str, StudySelectionCohortVO], bool
        ] = lambda x, y, z: True,
        validate: bool = True,
    ) -> None:
        """
        Adding a new study cohort to the _study_cohort_selection
        :param study_cohort_selection:
        :param study_arm_exists_callback:
        :param study_branch_arm_exists_callback:
        :param cohort_exists_callback_by:
        :return:
        """
        if validate:
            study_cohort_selection.validate(
                study_arm_exists_callback=study_arm_exists_callback,
                study_branch_arm_exists_callback=study_branch_arm_exists_callback,
                cohort_exists_callback_by=cohort_exists_callback_by,
            )
        self._add_selection(study_cohort_selection)

    @classmethod
    def from_repository_values(
        cls, study_uid: str, study_cohorts_selection: Iterable[StudySelectionCohortVO]
    ) -> Self:
        """
        Factory method to create a AR
        :param study_uid:
        :param study_cohorts_selection:
        :return:
        """
        return cls(
            _study_uid=normalize_string(study_uid),
            _study_cohorts_selection=tuple(study_cohorts_selection),
        )

    def remove_cohort_selection(self, study_selection_uid: str):
        """
        removing a study Cohort
        :param study_selection_uid:
        :return:
        """
        updated_selection = []
        for selection in self.study_cohorts_selection:
            if selection.study_selection_uid != study_selection_uid:
                updated_selection.append(selection)
        self._study_cohorts_selection = tuple(updated_selection)

    def set_new_order_for_selection(self, study_selection_uid: str, new_order: int):
        """
        Used to reorder a study cohort
        :param study_selection_uid:
        :param new_order:
        :return:
        """
        # check if the new order is valid using the robustness principle
        if new_order > len(self.study_cohorts_selection):
            # If order is higher than maximum allowed then set to max
            new_order = len(self.study_cohorts_selection)
        elif new_order < 1:
            # If order is lower than 1 set to 1
            new_order = 1
        # find the selection
        selected_value, old_order = self.get_specific_cohort_selection(
            study_selection_uid
        )
        # change the order
        updated_selections = []
        for order, selection in enumerate(self.study_cohorts_selection, start=1):
            # if the order is the where the new item is meant to be put
            if order == new_order:
                # we check if the order is being changed to lower or higher and add it to the list appropriately
                if old_order >= new_order:
                    updated_selections.append(selected_value)
                    if (
                        selection.study_selection_uid
                        != selected_value.study_selection_uid
                    ):
                        updated_selections.append(selection)
                else:
                    if (
                        selection.study_selection_uid
                        != selected_value.study_selection_uid
                    ):
                        updated_selections.append(selection)
                    updated_selections.append(selected_value)
            # We add all other vo to in the same order as before, except for the vo we are moving
            elif selection.study_selection_uid != selected_value.study_selection_uid:
                updated_selections.append(selection)
        self._study_cohorts_selection = tuple(updated_selections)

    def update_selection(
        self,
        updated_study_cohort_selection: StudySelectionCohortVO,
        study_arm_exists_callback: Callable[[str], bool] = lambda _: True,
        study_branch_arm_exists_callback: Callable[
            [str, str], bool
        ] = lambda x, y: True,
        cohort_exists_callback_by: Callable[
            [str, str, StudySelectionCohortVO], bool
        ] = lambda x, y, z: True,
        validate: bool = True,
    ) -> None:
        """
        Used when a study cohort is patched
        :param updated_study_cohort_selection:
        :param study_arm_exists_callback:
        :param study_branch_arm_exists_callback:
        :param cohort_exists_callback_by:
        :return:
        """
        if validate:
            updated_study_cohort_selection.validate(
                study_branch_arm_exists_callback=study_branch_arm_exists_callback,
                study_arm_exists_callback=study_arm_exists_callback,
                cohort_exists_callback_by=cohort_exists_callback_by,
            )
        # Check if study cohort or level have changed
        updated_selection = []
        for selection in self.study_cohorts_selection:
            if (
                selection.study_selection_uid
                != updated_study_cohort_selection.study_selection_uid
            ):
                updated_selection.append(selection)
            else:
                updated_selection.append(updated_study_cohort_selection)
        self._study_cohorts_selection = tuple(updated_selection)
