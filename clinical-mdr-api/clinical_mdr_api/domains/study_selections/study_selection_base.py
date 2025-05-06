from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable, Self, Type, TypeVar

from clinical_mdr_api.utils import normalize_string
from common import exceptions


class StudySelectionBaseVO:
    def validate(
        self,
        object_exist_callback: Callable[[str], bool] = (lambda _: True),
        ct_term_level_exist_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        raise NotImplementedError


# pylint: disable=invalid-name
TStudySelectionVO = TypeVar("TStudySelectionVO", bound="StudySelectionBaseVO")


@dataclass
class StudySelectionBaseAR:
    """
    The StudySelectionActivitiesAR holds all the study activity
    selections for a given study, the aggregate root also, takes care
    of all operations changing the study selections for a study.

    * add more selections
    * remove selections
    * patch selection
    * delete selection

    """

    _study_uid: str
    _study_objects_selection: tuple
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )
    closure_from_other_ar: StudySelectionBaseVO | None = None

    _object_type = None
    _object_uid_field = None
    _object_name_field = None
    _order_field_name = None

    @property
    def study_uid(self) -> str:
        return self._study_uid

    @property
    def study_objects_selection(self) -> tuple[Type[StudySelectionBaseVO]]:
        return self._study_objects_selection

    @study_objects_selection.setter
    def study_objects_selection(self, value: Iterable[Type[StudySelectionBaseVO]]):
        self._study_objects_selection = tuple(value)

    def get_specific_object_selection(
        self, study_selection_uid: str
    ) -> tuple[Type[StudySelectionBaseVO], int]:
        for order, selection in enumerate(self.study_objects_selection, start=1):
            if selection.study_selection_uid == study_selection_uid:
                return selection, order
        raise exceptions.NotFoundException(self._object_type, study_selection_uid)

    def add_object_selection(
        self,
        study_object_selection: Type[TStudySelectionVO],
        object_exist_callback: Callable[[str], bool] = (lambda _: True),
        ct_term_level_exist_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        study_object_selection.validate(
            object_exist_callback, ct_term_level_exist_callback
        )

        # add new value object in the list based on the object order
        selection_inserted = False
        if getattr(study_object_selection, self._order_field_name, None):
            updated_selections = []
            for selection in self._study_objects_selection:
                if (
                    getattr(selection, self._order_field_name)
                    > getattr(study_object_selection, self._order_field_name)
                    and not selection_inserted
                ):
                    updated_selections.append(study_object_selection)
                    selection_inserted = True
                updated_selections.append(selection)
            if not selection_inserted:
                updated_selections.append(study_object_selection)
            self._study_objects_selection = tuple(updated_selections)
        else:
            self._study_objects_selection = self._study_objects_selection + (
                study_object_selection,
            )

    def add_selection_to_closure_from_other_ar(
        self,
        study_object_selection: Type[TStudySelectionVO],
    ) -> None:
        self.closure_from_other_ar = study_object_selection

    @classmethod
    def from_repository_values(
        cls,
        study_uid: str,
        study_objects_selection: Iterable[Type[StudySelectionBaseVO]],
    ) -> Self:
        return cls(
            _study_uid=normalize_string(study_uid),
            _study_objects_selection=tuple(study_objects_selection),
        )

    def remove_object_selection(self, study_selection_uid: str) -> None:
        updated_selection = [
            selection
            for selection in self.study_objects_selection
            if selection.study_selection_uid != study_selection_uid
        ]
        self._study_objects_selection = tuple(updated_selection)

    # pylint: disable=unused-argument
    # TODO: Check why author_id is not used
    def set_new_order_for_selection(
        self, study_selection_uid: str, new_order: int, author_id: str
    ):
        # check if the new order is valid using the robustness principle
        if new_order > len(self.study_objects_selection):
            # If order is higher than maximum allowed then set to max
            new_order = len(self.study_objects_selection)
        elif new_order < 1:
            # If order is lower than 1 set to 1
            new_order = 1
        # find the selection
        selected_value, old_order = self.get_specific_object_selection(
            study_selection_uid
        )

        current_selection = list(self._study_objects_selection)
        del current_selection[old_order - 1]
        current_selection.insert(new_order - 1, selected_value)
        self._study_objects_selection = tuple(current_selection)

    def update_selection(
        self,
        updated_study_object_selection: Type[TStudySelectionVO],
        object_exist_callback: Callable[[str], bool] = (lambda _: True),
        ct_term_level_exist_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        updated_study_object_selection.validate(
            object_exist_callback=object_exist_callback,
            ct_term_level_exist_callback=ct_term_level_exist_callback,
        )
        updated_selection = []
        further_update = False
        for selection in self.study_objects_selection:
            if (
                selection.study_selection_uid
                != updated_study_object_selection.study_selection_uid
            ):
                updated_selection.append(selection)
            else:
                if getattr(
                    updated_study_object_selection, self._order_field_name, None
                ) == getattr(selection, self._order_field_name, None):
                    updated_selection.append(updated_study_object_selection)
                else:
                    # the object level has changed so the object order is changed
                    further_update = True
        if further_update:
            # The order is updated
            selection_inserted = False
            updated_selections = []
            for selection in updated_selection:
                selection_order = getattr(selection, self._order_field_name)
                updated_selection_order = getattr(
                    updated_study_object_selection, self._order_field_name
                )
                if selection_order > updated_selection_order and not selection_inserted:
                    updated_selections.append(updated_study_object_selection)
                    selection_inserted = True
                updated_selections.append(selection)
            if not selection_inserted:
                updated_selections.append(updated_study_object_selection)
            self._study_objects_selection = tuple(updated_selections)
        else:
            # The object order is unchanged
            self._study_objects_selection = tuple(updated_selection)

    def validate(self):
        objects = []
        for selection in self.study_objects_selection:
            object_name = getattr(selection, self._object_name_field, None)
            exceptions.AlreadyExistsException.raise_if(
                object_name and object_name in objects,
                msg=f"There is already a Study Selection to the {self._object_type} with Name '{object_name}'.",
            )
            objects.append(object_name)


class SoAItemType(Enum):
    STUDY_ACTIVITY_SCHEDULE = "StudyActivitySchedule"
    STUDY_ACTIVITY = "StudyActivity"
    STUDY_ACTIVITY_INSTANCE = "StudyActivityInstance"
    STUDY_ACTIVITY_SUBGROUP = "StudyActivitySubGroup"
    STUDY_ACTIVITY_GROUP = "StudyActivityGroup"
    STUDY_SOA_GROUP = "StudySoAGroup"
    STUDY_EPOCH = "StudyEpoch"
    STUDY_VISIT = "StudyVisit"
    STUDY_SOA_FOOTNOTE = "StudySoAFootnote"


SOA_ITEM_TYPES = {it.value for it in SoAItemType}
