import datetime
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Iterable, Self

from clinical_mdr_api.services.user_info import UserInfoService
from clinical_mdr_api.utils import normalize_string
from common import exceptions


@dataclass(frozen=True)
class StudySelectionCriteriaVO:
    """
    The StudySelectionCriteriaVO acts as the value object for a single selection between a study and a criteria
    """

    study_selection_uid: str
    study_uid: str | None
    syntax_object_uid: str
    syntax_object_version: str
    criteria_type_uid: str
    criteria_type_order: int
    is_instance: bool
    key_criteria: bool
    # Study selection Versioning
    start_date: datetime.datetime
    author_id: str
    accepted_version: bool = False
    author_username: str | None = None

    @classmethod
    def from_input_values(
        cls,
        syntax_object_uid: str,
        syntax_object_version: str,
        author_id: str,
        criteria_type_uid: str,
        criteria_type_order: int = 0,
        is_instance: bool = True,
        key_criteria: bool = False,
        study_uid: str | None = None,
        study_selection_uid: str | None = None,
        start_date: datetime.datetime | None = None,
        generate_uid_callback: Callable[[], str] = lambda: "",
        accepted_version: bool = False,
    ):
        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now(datetime.timezone.utc)

        return cls(
            study_uid=study_uid,
            criteria_type_uid=criteria_type_uid,
            criteria_type_order=criteria_type_order,
            syntax_object_uid=normalize_string(syntax_object_uid),
            syntax_object_version=syntax_object_version,
            is_instance=is_instance,
            key_criteria=key_criteria,
            start_date=start_date,
            study_selection_uid=normalize_string(study_selection_uid),
            author_id=normalize_string(author_id),
            author_username=UserInfoService.get_author_username_from_id(author_id),
            accepted_version=accepted_version,
        )

    def validate(
        self,
        criteria_exist_callback: Callable[[str | None], bool] = lambda _: True,
        ct_term_criteria_type_exist_callback: Callable[[str | None], bool] = (
            lambda _: True
        ),
    ) -> None:
        # Checks if there exists a criteria which is approved with criteria_uid
        exceptions.ValidationException.raise_if_not(
            criteria_exist_callback(normalize_string(self.syntax_object_uid)),
            msg=f"There is no approved Criteria with UID '{self.syntax_object_uid}'.",
        )
        exceptions.ValidationException.raise_if(
            self.criteria_type_uid
            and not ct_term_criteria_type_exist_callback(self.criteria_type_uid),
            msg=f"There is no approved Criteria Type with UID '{self.criteria_type_uid}'.",
        )

    def update_version(self, criteria_version: str):
        return replace(self, syntax_object_version=criteria_version)

    def accept_versions(self):
        return replace(self, accepted_version=True)


@dataclass
class StudySelectionCriteriaAR:
    """
    The StudySelectionCriteriaAR holds all the study criteria selections for a given study, the aggregate root also ,
    takes care of all operations changing the study selections for a study.
    * add more selections
    * remove selections
    * patch selection
    * delete selection
    """

    _study_uid: str
    _study_criteria_selection: tuple[StudySelectionCriteriaVO, ...]
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    @property
    def study_uid(self) -> str:
        return self._study_uid

    @property
    def study_criteria_selection(self) -> tuple[StudySelectionCriteriaVO, ...]:
        return self._study_criteria_selection

    @study_criteria_selection.setter
    def study_criteria_selection(self, value: Iterable[StudySelectionCriteriaVO]):
        self._study_criteria_selection = tuple(value)

    def get_specific_criteria_selection(
        self, study_criteria_uid: str, criteria_type_uid: str | None = None
    ) -> tuple[StudySelectionCriteriaVO, int]:
        # First, filter on criteria selection with the same criteria type
        # to get the order in the context of the criteria type
        # The criteria type might not be known by some caller methods
        # So first step is to get it
        if criteria_type_uid is None:
            _criteria_type_uid = [
                x.criteria_type_uid
                for x in self.study_criteria_selection
                if x.study_selection_uid == study_criteria_uid
            ]
            if len(_criteria_type_uid) == 1:
                criteria_type_uid = _criteria_type_uid[0]
            else:
                raise exceptions.NotFoundException("Study Criteria", study_criteria_uid)

        # Then, filter the list on criteria type, and return the order of the criteria selection in the type group
        study_criteria_selection_with_type = [
            x
            for x in self.study_criteria_selection
            if x.criteria_type_uid == criteria_type_uid
        ]
        for order, selection in enumerate(study_criteria_selection_with_type, start=1):
            if selection.study_selection_uid == study_criteria_uid:
                return selection, order
        raise exceptions.NotFoundException("Study Criteria", study_criteria_uid)

    def add_criteria_selection(
        self,
        study_criteria_selection: StudySelectionCriteriaVO,
        criteria_exist_callback: Callable[[str | None], bool] = lambda _: True,
        ct_term_criteria_type_exist_callback: Callable[[str | None], bool] = (
            lambda _: True
        ),
    ) -> None:
        study_criteria_selection.validate(
            criteria_exist_callback, ct_term_criteria_type_exist_callback
        )

        # add new value object in the list based on the criteria type order
        if study_criteria_selection.criteria_type_order:
            new_selections = self._study_criteria_selection + (
                study_criteria_selection,
            )
            self._study_criteria_selection = tuple(
                sorted(new_selections, key=lambda sel: sel.criteria_type_order or 0)
            )
        else:
            self._study_criteria_selection = self._study_criteria_selection + (
                study_criteria_selection,
            )

    @classmethod
    def from_repository_values(
        cls,
        study_uid: str,
        study_criteria_selection: Iterable[StudySelectionCriteriaVO],
    ) -> Self:
        return cls(
            _study_uid=normalize_string(study_uid),
            _study_criteria_selection=tuple(study_criteria_selection),
        )

    def remove_criteria_selection(self, study_selection_uid: str) -> None:
        updated_selection = []
        for selection in self.study_criteria_selection:
            if selection.study_selection_uid != study_selection_uid:
                updated_selection.append(selection)
        self._study_criteria_selection = tuple(updated_selection)

    def update_study_criteria_on_aggregated(
        self,
        updated_study_criteria_selection: StudySelectionCriteriaVO,
    ) -> None:
        """
        Used when a study criteria key criteria property is patched
        :param updated_study_criteria_selection:
        :return:
        """

        # Check if study cohort or level have changed
        updated_selection = []
        for selection in self.study_criteria_selection:
            if (
                selection.study_selection_uid
                != updated_study_criteria_selection.study_selection_uid
            ):
                updated_selection.append(selection)
            else:
                updated_selection.append(updated_study_criteria_selection)
        self._study_criteria_selection = tuple(updated_selection)

    def set_new_order_for_selection(
        self, study_selection_uid: str, new_order: int, author_id: str
    ):
        # check if the new order is valid using the robustness principle
        if new_order > len(self.study_criteria_selection):
            # If order is higher than maximum allowed then set to max
            new_order = len(self.study_criteria_selection)
        elif new_order < 1:
            # If order is lower than 1 set to 1
            new_order = 1
        # find the selection
        selected_value, _ = self.get_specific_criteria_selection(study_selection_uid)
        assert (
            selected_value.criteria_type_order is not None
        ), "Criteria type order should not be None at this point"
        old_order = selected_value.criteria_type_order
        # We have to reset the selected value so it can be set to edit in the domain
        selected_value = StudySelectionCriteriaVO.from_input_values(
            syntax_object_uid=selected_value.syntax_object_uid,
            criteria_type_uid=selected_value.criteria_type_uid,
            author_id=author_id,
            study_selection_uid=selected_value.study_selection_uid,
            criteria_type_order=selected_value.criteria_type_order,
            syntax_object_version=selected_value.syntax_object_version,
            is_instance=selected_value.is_instance,
            key_criteria=selected_value.key_criteria,
        )
        # change the order
        # to do so, first filter on criteria selection with the same criteria type as the selected one
        study_criteria_selection_with_type = [
            x
            for x in self.study_criteria_selection
            if x.criteria_type_uid == selected_value.criteria_type_uid
        ]
        # then, make sure that the list is properly ordered
        study_criteria_selection_with_type.sort(
            key=lambda x: x.criteria_type_order or 0
        )
        del study_criteria_selection_with_type[old_order - 1]
        study_criteria_selection_with_type.insert(new_order - 1, selected_value)

        # merge selections and replace it in the selection object
        study_criteria_selection_with_different_type = [
            x
            for x in self.study_criteria_selection
            if x.criteria_type_uid != selected_value.criteria_type_uid
        ]
        self._study_criteria_selection = tuple(
            study_criteria_selection_with_different_type
            + study_criteria_selection_with_type
        )

    def update_selection(
        self,
        updated_study_criteria_selection: StudySelectionCriteriaVO,
        criteria_exist_callback: Callable[[str | None], bool] = lambda _: True,
        ct_term_criteria_type_exist_callback: Callable[[str | None], bool] = (
            lambda _: True
        ),
    ) -> None:
        updated_study_criteria_selection.validate(
            criteria_exist_callback=criteria_exist_callback,
            ct_term_criteria_type_exist_callback=ct_term_criteria_type_exist_callback,
        )
        updated_selection = []
        for selection in self.study_criteria_selection:
            if (
                selection.study_selection_uid
                == updated_study_criteria_selection.study_selection_uid
            ):
                updated_selection.append(updated_study_criteria_selection)
            else:
                updated_selection.append(selection)

        self._study_criteria_selection = tuple(updated_selection)

    def validate(self):
        criteria = []
        for selection in self.study_criteria_selection:
            exceptions.AlreadyExistsException.raise_if(
                selection.syntax_object_uid in criteria,
                msg=f"There is already a Study Selection to a criteria with UID '{selection.syntax_object_uid}'.",
            )
            criteria.append(selection.syntax_object_uid)
