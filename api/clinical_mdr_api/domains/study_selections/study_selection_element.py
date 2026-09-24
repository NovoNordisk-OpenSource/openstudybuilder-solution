import datetime
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Self

from clinical_mdr_api.services.user_info import UserInfoService
from clinical_mdr_api.utils import normalize_string
from common import exceptions


@dataclass(frozen=True)
class StudySelectionElementVO:
    """
    The StudySelectionElementVO acts as the value object for a single selection between a study and an element
    """

    study_selection_uid: str
    study_uid: str | None
    name: str | None
    short_name: str | None
    code: str | None
    description: str | None
    planned_duration: str | None
    start_rule: str | None
    end_rule: str | None
    element_colour: str | None
    element_subtype_uid: str | None
    study_compound_dosing_count: int | None
    start_date: datetime.datetime
    author_id: str
    end_date: datetime.datetime | None
    status: str | None
    change_type: str | None
    accepted_version: bool = False
    author_username: str | None = None

    @classmethod
    def from_input_values(
        cls,
        author_id: str,
        study_selection_uid: str | None = None,
        study_uid: str | None = None,
        name: str | None = None,
        short_name: str | None = None,
        code: str | None = None,
        description: str | None = None,
        planned_duration: str | None = None,
        start_rule: str | None = None,
        end_rule: str | None = None,
        element_colour: str | None = None,
        element_subtype_uid: str | None = None,
        study_compound_dosing_count: int | None = None,
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
        :param planned_duration
        :param start_rule
        :param end_rule
        :param element_colour
        :param element_subtype_uid
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

        return StudySelectionElementVO(
            study_uid=study_uid,
            study_selection_uid=normalize_string(study_selection_uid),
            name=name,
            short_name=short_name,
            code=code,
            description=description,
            planned_duration=planned_duration,
            start_rule=start_rule,
            end_rule=end_rule,
            element_colour=element_colour,
            element_subtype_uid=element_subtype_uid,
            study_compound_dosing_count=study_compound_dosing_count,
            start_date=start_date,
            author_id=author_id,
            author_username=UserInfoService.get_author_username_from_id(author_id),
            end_date=end_date,
            status=status,
            change_type=change_type,
            accepted_version=accepted_version,
        )

    def validate(
        self, ct_term_exists_callback: Callable[[str], bool] = lambda _: True
    ) -> None:
        """
        Validating business logic for a VO
        :param ct_term_exists_callback:
        :return:
        """
        # Check if there exist a Term with the selected uid
        exceptions.ValidationException.raise_if(
            self.element_subtype_uid
            and not ct_term_exists_callback(self.element_subtype_uid),
            msg=f"There is no approved Element Level with UID '{self.element_subtype_uid}'.",
        )


@dataclass
class StudySelectionElementAR:
    _study_uid: str
    _study_elements_selection: tuple[StudySelectionElementVO, ...]
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    @property
    def study_uid(self) -> str:
        return self._study_uid

    # return a list of all study element selection object
    @property
    def study_elements_selection(self) -> tuple[StudySelectionElementVO, ...]:
        return self._study_elements_selection

    def get_specific_object_selection(
        self, study_selection_uid: str
    ) -> tuple[StudySelectionElementVO, int]:
        for order, selection in enumerate(self.study_elements_selection, start=1):
            if selection.study_selection_uid == study_selection_uid:
                return selection, order
        raise exceptions.NotFoundException(
            msg=f"The Study Selection with UID '{study_selection_uid}' doesn't exist for Study with UID '{self._study_uid}'."
        )

    def get_specific_element_selection(
        self, study_selection_uid: str
    ) -> tuple[StudySelectionElementVO, int]:
        """
        Used to receive a specific VO from the AR
        :param study_selection_uid:
        :return:
        """
        for order, selection in enumerate(self.study_elements_selection, start=1):
            if selection.study_selection_uid == study_selection_uid:
                return selection, order
        raise exceptions.NotFoundException(
            msg=f"There is no selection between the Study Element with UID '{study_selection_uid}' and the study."
        )

    def _add_selection(self, study_element_selection) -> None:
        new_selections = self._study_elements_selection + (study_element_selection,)
        self._study_elements_selection = new_selections

    def add_element_selection(
        self,
        study_element_selection: StudySelectionElementVO,
        ct_term_exists_callback: Callable[[str], bool] = lambda _: True,
        validate: bool = True,
    ) -> None:
        """
        Adding a new study element to the _study_element_selection
        :param study_element_selection:
        :param ct_term_exists_callback:
        :return:
        """
        if validate:
            study_element_selection.validate(ct_term_exists_callback)
        self._add_selection(study_element_selection)

    @classmethod
    def from_repository_values(
        cls, study_uid: str, study_elements_selection: Iterable[StudySelectionElementVO]
    ) -> Self:
        """
        Factory method to create a AR
        :param study_uid:
        :param study_endpoints_selection:
        :return:
        """
        return cls(
            _study_uid=normalize_string(study_uid),
            _study_elements_selection=tuple(study_elements_selection),
        )

    def remove_element_selection(self, study_selection_uid: str):
        """
        removing a study element
        :param study_selection_uid:
        :return:
        """
        updated_selection = []
        for selection in self.study_elements_selection:
            if selection.study_selection_uid != study_selection_uid:
                updated_selection.append(selection)
        self._study_elements_selection = tuple(updated_selection)

    def update_selection(
        self,
        updated_study_element_selection: StudySelectionElementVO,
        ct_term_exists_callback: Callable[[str], bool] = lambda _: True,
        validate: bool = True,
    ) -> None:
        """
        Used when a study endpoint is patched
        :param ct_term_exists_callback:
        :return:
        """
        if validate:
            updated_study_element_selection.validate(
                ct_term_exists_callback=ct_term_exists_callback
            )
        # Check if study objective or level have changed
        updated_selection = []
        for selection in self.study_elements_selection:
            if (
                selection.study_selection_uid
                == updated_study_element_selection.study_selection_uid
            ):
                updated_selection.append(updated_study_element_selection)
            else:
                updated_selection.append(selection)
        self._study_elements_selection = tuple(updated_selection)

    def set_new_order_for_selection(self, study_selection_uid: str, new_order: int):
        """
        Used to reorder a study compound
        :param study_selection_uid:
        :param new_order:
        :return:
        """
        # check if the new order is valid using the robustness principle
        if new_order > len(self.study_elements_selection):
            # If order is higher than maximum allowed then set to max
            new_order = len(self.study_elements_selection)
        elif new_order < 1:
            # If order is lower than 1 set to 1
            new_order = 1
        # find the selection
        selected_value, old_order = self.get_specific_element_selection(
            study_selection_uid
        )
        # change the order
        updated_selections = []
        for order, selection in enumerate(self.study_elements_selection, start=1):
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
        self._study_elements_selection = tuple(updated_selections)
