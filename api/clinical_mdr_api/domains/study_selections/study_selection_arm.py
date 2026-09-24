import datetime
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Self

from clinical_mdr_api.domain_repositories.models.study_selections import StudyArm
from clinical_mdr_api.services.user_info import UserInfoService
from clinical_mdr_api.utils import normalize_string
from common import exceptions


@dataclass(frozen=True)
class StudySelectionArmVO:
    """
    The StudySelectionArmVO acts as the value object for a single selection between a study and an arm
    """

    study_selection_uid: str
    study_uid: str | None
    name: str
    short_name: str
    label: str
    code: str | None
    description: str | None
    randomization_group: str | None
    number_of_subjects: int | None
    arm_type_uid: str | None
    start_date: datetime.datetime = field(compare=False)
    author_id: str
    author_username: str
    end_date: datetime.datetime | None
    status: str | None
    change_type: str | None
    merge_branch_for_this_arm_for_sdtm_adam: bool = False
    accepted_version: bool = False

    @classmethod
    def from_input_values(
        cls,
        author_id: str,
        study_selection_uid: str | None = None,
        study_uid: str | None = None,
        name: str | None = None,
        short_name: str | None = None,
        label: str | None = None,
        code: str | None = None,
        description: str | None = None,
        randomization_group: str | None = None,
        number_of_subjects: int | None = 0,
        arm_type_uid: str | None = None,
        start_date: datetime.datetime | None = None,
        end_date: datetime.datetime | None = None,
        status: str | None = None,
        change_type: str | None = None,
        accepted_version: bool = False,
        merge_branch_for_this_arm_for_sdtm_adam: bool = False,
        generate_uid_callback: Callable[[], str] = lambda: "",
    ) -> Self:
        """
        Factory method
        :param study_uid
        :param study_selection_uid
        :param name
        :param short_name
        :param label
        :param code
        :param description
        :param randomization_group
        :param number_of_subjects
        :param arm_type_uid
        :param start_date
        :param author_id
        :param end_date
        :param status
        :param change_type
        :param accepted_version
        :param merge_branch_for_this_arm_for_sdtm_adam
        :return:
        """
        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now(datetime.timezone.utc)

        # returns a new instance of the VO

        return StudySelectionArmVO(
            study_uid=study_uid,
            study_selection_uid=normalize_string(study_selection_uid),
            name=name or "",
            short_name=short_name or "",
            label=label or "",
            code=code,
            description=description,
            randomization_group=randomization_group,
            number_of_subjects=number_of_subjects,
            arm_type_uid=arm_type_uid,
            start_date=start_date,
            author_id=author_id,
            author_username=UserInfoService.get_author_username_from_id(author_id),
            end_date=end_date,
            status=status,
            change_type=change_type,
            accepted_version=accepted_version,
            merge_branch_for_this_arm_for_sdtm_adam=merge_branch_for_this_arm_for_sdtm_adam,
        )

    def validate(
        self,
        ct_term_exists_callback: Callable[[str], bool] = lambda _: True,
        arm_exists_callback_by: Callable[
            [str, str, "StudySelectionArmVO"], StudyArm | None
        ] = lambda x, y, z: None,
    ) -> None:
        """
        Validating business logic for a VO
        :param ct_term_exists_callback:
        :param arm_exists_callback:
        :return:
        """
        # Check if there exist a Term with the selected uid
        exceptions.ValidationException.raise_if(
            self.arm_type_uid and not ct_term_exists_callback(self.arm_type_uid),
            msg=f"There is no approved Arm Level Term with UID '{self.arm_type_uid}'.",
        )

        # check if the specified name is already used
        exceptions.ValidationException.raise_if(
            self.name and arm_exists_callback_by("name", "name", self),
            msg=f"Value '{self.name}' in field Arm name is not unique for the study.",
        )

        # check if the specified short_name is already used
        exceptions.ValidationException.raise_if(
            self.short_name
            and arm_exists_callback_by("short_name", "short_name", self),
            msg=f"Value '{self.short_name}' in field Arm short name is not unique for the study.",
        )

        # check if the specified code is already used with the callback
        exceptions.ValidationException.raise_if(
            self.code and arm_exists_callback_by("arm_code", "code", self),
            msg=f"Value '{self.code}' in field code is not unique for the study.",
        )

        # check if the specified randomization group is already used with the callback
        exceptions.ValidationException.raise_if(
            self.randomization_group
            and arm_exists_callback_by(
                "randomization_group", "randomization_group", self
            ),
            msg=f"Value '{self.randomization_group}' in field Arm Randomization code is not unique for the study.",
        )


@dataclass
class StudySelectionArmAR:
    _study_uid: str
    _study_arms_selection: tuple[StudySelectionArmVO, ...]
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    def get_specific_object_selection(
        self, study_selection_uid: str
    ) -> tuple[StudySelectionArmVO, int]:
        for order, selection in enumerate(self.study_arms_selection, start=1):
            if selection.study_selection_uid == study_selection_uid:
                return selection, order
        raise exceptions.NotFoundException(
            msg=f"Study Selection with UID '{study_selection_uid}' doesn't exist for Study with UID '{self._study_uid}'."
        )

    @property
    def study_uid(self) -> str:
        return self._study_uid

    @property
    def study_arms_selection(self) -> tuple[StudySelectionArmVO, ...]:
        return self._study_arms_selection

    def get_specific_arm_selection(
        self, study_selection_uid: str
    ) -> tuple[StudySelectionArmVO, int]:
        """
        Used to receive a specific VO from the AR
        :param study_selection_uid:
        :return:
        """
        for order, selection in enumerate(self.study_arms_selection, start=1):
            if selection.study_selection_uid == study_selection_uid:
                return selection, order
        raise exceptions.NotFoundException(
            msg=f"There is no selection between the Study Arm with UID '{study_selection_uid}' and the study"
        )

    def _add_selection(self, study_arm_selection) -> None:
        new_selections = self._study_arms_selection + (study_arm_selection,)
        self._study_arms_selection = new_selections

    def add_arm_selection(
        self,
        study_arm_selection: StudySelectionArmVO,
        ct_term_exists_callback: Callable[[str], bool] = lambda _: True,
        validate: bool = True,
        arm_exists_callback_by: Callable[
            [str, str, StudySelectionArmVO], StudyArm | None
        ] = lambda x, y, z: None,
    ) -> None:
        """
        Adding a new study arm to the study_arm_selection
        :param study_arm_selection:
        :param ct_term_exists_callback:
        :param arm_exists_callback_by:
        :return:
        """
        if validate:
            study_arm_selection.validate(
                ct_term_exists_callback=ct_term_exists_callback,
                arm_exists_callback_by=arm_exists_callback_by,
            )
        self._add_selection(study_arm_selection)

    @classmethod
    def from_repository_values(
        cls, study_uid: str, study_arms_selection: Iterable[StudySelectionArmVO]
    ) -> Self:
        """
        Factory method to create a AR
        :param study_uid:
        :param study_endpoints_selection:
        :return:
        """
        return cls(
            _study_uid=normalize_string(study_uid),
            _study_arms_selection=tuple(study_arms_selection),
        )

    def remove_arm_selection(self, study_selection_uid: str):
        """
        removing a study arm
        :param study_selection_uid:
        :return:
        """
        updated_selection = []
        for selection in self.study_arms_selection:
            if selection.study_selection_uid != study_selection_uid:
                updated_selection.append(selection)
        self._study_arms_selection = tuple(updated_selection)

    def set_new_order_for_selection(self, study_selection_uid: str, new_order: int):
        """
        Used to reorder a study compound
        :param study_selection_uid:
        :param new_order:
        :return:
        """
        # check if the new order is valid using the robustness principle
        if new_order > len(self.study_arms_selection):
            # If order is higher than maximum allowed then set to max
            new_order = len(self.study_arms_selection)
        elif new_order < 1:
            # If order is lower than 1 set to 1
            new_order = 1
        # find the selection
        selected_value, old_order = self.get_specific_arm_selection(study_selection_uid)
        # change the order
        updated_selections = []
        for order, selection in enumerate(self.study_arms_selection, start=1):
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
        self._study_arms_selection = tuple(updated_selections)

    def update_selection(
        self,
        updated_study_arm_selection: StudySelectionArmVO,
        ct_term_exists_callback: Callable[[str], bool] = lambda _: True,
        validate: bool = True,
        arm_exists_callback_by: Callable[
            [str, str, StudySelectionArmVO], StudyArm | None
        ] = lambda x, y, z: None,
    ) -> None:
        """
        Used when a study arm is patched
        :param updated_study_arm_selection:
        :param ct_term_exists_callback:
        :param arm_exists_callback:
        :return:
        """
        if validate:
            updated_study_arm_selection.validate(
                ct_term_exists_callback=ct_term_exists_callback,
                arm_exists_callback_by=arm_exists_callback_by,
            )
        updated_selection = []
        for selection in self.study_arms_selection:
            if (
                selection.study_selection_uid
                != updated_study_arm_selection.study_selection_uid
            ):
                updated_selection.append(selection)
            else:
                updated_selection.append(updated_study_arm_selection)
        self._study_arms_selection = tuple(updated_selection)
