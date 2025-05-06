import datetime
import sys
from dataclasses import dataclass, field, replace
from typing import Annotated, Any, Callable, Iterable, Self

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.services.user_info import UserInfoService
from clinical_mdr_api.utils import normalize_string
from common import exceptions
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    ValidationException,
)


class EndpointUnitItem(BaseModel):
    uid: Annotated[str, Field(description="uid of the endpoint unit")]

    name: Annotated[
        str | None,
        Field(
            description="name of the endpoint unit",
            json_schema_extra={"nullable": True},
        ),
    ] = None


class EndpointUnits(BaseModel):
    units: Annotated[
        tuple[EndpointUnitItem, ...] | None,
        Field(
            description="list of endpoint units selected for the study endpoint",
            json_schema_extra={"nullable": True},
        ),
    ]

    separator: Annotated[
        str | None,
        Field(
            description="separator, if more than one endpoint units were selected for the study endpoint",
            json_schema_extra={"nullable": True},
        ),
    ] = None


@dataclass
class StudyEndpointSelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    endpoint_uid: str | None
    endpoint_version: str | None
    endpoint_level: str | None
    endpoint_sublevel: str | None
    study_objective_uid: str | None
    timeframe_uid: str | None
    timeframe_version: str | None
    endpoint_units: EndpointUnits | None
    unit_separator: str | None
    # Study selection Versioning
    start_date: datetime.datetime
    author_id: str | None
    change_type: str
    end_date: datetime.datetime | None
    order: int
    status: str | None
    author_username: str | None = None


@dataclass(frozen=True)
class StudySelectionEndpointVO:
    """
    The StudySelectionEndpointVO acts as the value object for a single selection between a study and a endpoint
    """

    study_selection_uid: str
    study_uid: str | None
    endpoint_uid: str | None
    endpoint_version: str | None
    endpoint_level_uid: str | None
    endpoint_sublevel_uid: str | None
    study_objective_uid: str | None
    timeframe_uid: str | None
    timeframe_version: str | None
    endpoint_units: tuple[dict[str, Any]]
    unit_separator: str | None
    endpoint_level_order: int | None
    is_instance: bool
    # Study selection Versioning
    start_date: datetime.datetime
    author_id: str
    author_username: str | None = None
    accepted_version: bool = False

    @classmethod
    def from_input_values(
        cls,
        endpoint_uid: str | None,
        endpoint_version: str | None,
        endpoint_level_uid: str | None,
        endpoint_sublevel_uid: str | None,
        unit_separator: str | None,
        study_objective_uid: str | None,
        timeframe_uid: str | None,
        timeframe_version: str | None,
        endpoint_units: list[Any] | None,
        endpoint_level_order: int | None,
        author_id: str,
        study_uid: str | None = None,
        study_selection_uid: str | None = None,
        is_instance: bool = True,
        start_date: datetime.datetime | None = None,
        accepted_version: bool | None = False,
        generate_uid_callback: Callable[[], str] | None = None,
    ):
        """
        Factory method
        :param study_uid:
        :param endpoint_uid:
        :param endpoint_level_uid:
        :param endpoint_sublevel_uid:
        :param unit_separator:
        :param study_objective_uid:
        :param timeframe_uid:
        :param endpoint_units:
        :param in_instance:
        :param start_date:
        :param study_selection_uid:
        :param generate_uid_callback:
        :return:
        """
        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now(datetime.timezone.utc)

        if endpoint_units:
            # built-in dict remembers insertion order (guaranteed since Python 3.7)
            units = {}
            for unit in endpoint_units:
                unit = {
                    k: normalize_string(v) if isinstance(v, str) else v
                    for k, v in unit.items()
                }
                if unit["uid"]:
                    units[unit["uid"]] = unit
            units = tuple(units.values())

        else:
            units = tuple()

        # returns a new instance of the VO
        return StudySelectionEndpointVO(
            study_uid=study_uid,
            study_selection_uid=normalize_string(study_selection_uid),
            endpoint_uid=normalize_string(endpoint_uid),
            endpoint_version=normalize_string(endpoint_version),
            endpoint_level_uid=normalize_string(endpoint_level_uid),
            endpoint_sublevel_uid=normalize_string(endpoint_sublevel_uid),
            unit_separator=normalize_string(unit_separator),
            study_objective_uid=normalize_string(study_objective_uid),
            timeframe_uid=normalize_string(timeframe_uid),
            timeframe_version=normalize_string(timeframe_version),
            endpoint_level_order=endpoint_level_order,
            endpoint_units=units,
            is_instance=is_instance,
            author_id=author_id,
            author_username=UserInfoService.get_author_username_from_id(author_id),
            start_date=start_date,
            accepted_version=accepted_version,
        )

    def validate(
        self,
        study_objective_exist_callback: Callable[[str], bool] = (lambda _: True),
        endpoint_exist_callback: Callable[[str], bool] = (lambda _: True),
        timeframe_exist_callback: Callable[[str], bool] = (lambda _: True),
        ct_term_exists_callback: Callable[[str], bool] = (lambda _: True),
        unit_definition_exists_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        """
        Validating business logic for a VO
        :param study_objective_exist_callback:
        :param endpoint_exist_callback:
        :param timeframe_exist_callback:
        :param ct_term_exists_callback:
        :param unit_definition_exists_callback:
        :return:
        """
        # Checks if there exists a endpoint which is approved with endpoint_uid
        BusinessLogicException.raise_if(
            self.endpoint_uid is not None
            and not endpoint_exist_callback(normalize_string(self.endpoint_uid)),
            msg=f"There is no approved Endpoint with UID '{self.endpoint_uid}'.",
        )
        # Checks if there exists a timeframe with the
        BusinessLogicException.raise_if(
            self.timeframe_uid is not None
            and not timeframe_exist_callback(normalize_string(self.timeframe_uid)),
            msg=f"There is no approved Timeframe with UID '{self.timeframe_uid}'.",
        )
        # Check if the study objective exists
        BusinessLogicException.raise_if(
            self.study_objective_uid is not None
            and not study_objective_exist_callback(
                normalize_string(self.study_objective_uid)
            ),
            msg=f"There is no selected Study Objective with UID '{self.study_objective_uid}'.",
        )
        # check that if there are more than one unit then there need to be a separator
        ValidationException.raise_if(
            len(self.endpoint_units) > 1 and self.unit_separator is None,
            msg="In case of more than one endpoint units, a unit separator is required.",
        )
        ValidationException.raise_if(
            self.unit_separator is not None and len(self.endpoint_units) < 2,
            msg=f"Separator should only be set if more than 1 units are selected '{self.endpoint_units}'.",
        )
        # Check if there exist a Term with the selected uid
        BusinessLogicException.raise_if(
            not ct_term_exists_callback(self.endpoint_level_uid)
            and self.endpoint_level_uid,
            msg=f"There is no approved Endpoint Level with UID '{self.endpoint_level_uid}'.",
        )
        BusinessLogicException.raise_if(
            self.endpoint_sublevel_uid
            and not ct_term_exists_callback(self.endpoint_sublevel_uid),
            msg=f"There is no approved Endpoint Sub Level with UID '{self.endpoint_sublevel_uid}'.",
        )
        for unit in self.endpoint_units:
            uid = unit.get("uid")

            ValidationException.raise_if_not(
                uid, msg=f"There is no uid for unit definition '{unit}'."
            )
            ValidationException.raise_if_not(
                unit_definition_exists_callback(uid),
                msg=f"There is no approved Unit Definition with UID '{uid}'.",
            )

    def update_endpoint_version(self, endpoint_version: str):
        return replace(self, endpoint_version=endpoint_version)

    def update_timeframe_version(self, timeframe_version: str):
        return replace(self, timeframe_version=timeframe_version)

    def accept_versions(self):
        return replace(self, accepted_version=True)


@dataclass
class StudySelectionEndpointsAR:
    _study_uid: str
    _study_endpoints_selection: tuple
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    @property
    def study_uid(self) -> str:
        return self._study_uid

    @property
    def study_endpoints_selection(self) -> tuple[StudySelectionEndpointVO]:
        return self._study_endpoints_selection

    @study_endpoints_selection.setter
    def study_endpoints_selection(self, value: Iterable[StudySelectionEndpointVO]):
        self._study_endpoints_selection = tuple(value)

    def get_specific_endpoint_selection(
        self, study_selection_uid: str
    ) -> tuple[StudySelectionEndpointVO, int]:
        """
        Used to receive a specific VO from the AR
        :param study_selection_uid:
        :return:
        """
        for order, selection in enumerate(self.study_endpoints_selection, start=1):
            if selection.study_selection_uid == study_selection_uid:
                return selection, order
        raise exceptions.NotFoundException(
            msg=f"There is no selection between the Study Endpoint with UID '{study_selection_uid}' and the study."
        )

    def _add_selection(self, study_endpoint_selection) -> None:
        def _selection_sort_logic(study_endpoint_sel: tuple):
            if study_endpoint_sel.study_objective_uid is not None:
                # extracting integer part of uid
                study_objective_uid = int(
                    study_endpoint_sel.study_objective_uid.split("_")[-1]
                )
            else:
                # returning maxsize to put study endpoints with no study objective uid at the end
                study_objective_uid = sys.maxsize
            if study_endpoint_sel.endpoint_level_order is not None:
                endpoint_level_order = study_endpoint_sel.endpoint_level_order
            else:
                # returning maxsize to put study endpoints with no endpoint level at the end
                endpoint_level_order = sys.maxsize
            return study_objective_uid, endpoint_level_order

        new_selections = self._study_endpoints_selection + (study_endpoint_selection,)
        sorted_selections = tuple(sorted(new_selections, key=_selection_sort_logic))
        self._study_endpoints_selection = sorted_selections

    def add_endpoint_selection(
        self,
        study_endpoint_selection: StudySelectionEndpointVO,
        study_objective_exist_callback: Callable[[str], bool] = (lambda _: True),
        endpoint_exist_callback: Callable[[str], bool] = (lambda _: True),
        timeframe_exist_callback: Callable[[str], bool] = (lambda _: True),
        ct_term_exists_callback: Callable[[str], bool] = (lambda _: True),
        unit_definition_exists_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        """
        Adding a new study endpoint to the _study_endpoint_selection
        :param study_endpoint_selection:
        :param study_objective_exist_callback:
        :param endpoint_exist_callback:
        :param timeframe_exist_callback:
        :param ct_term_exists_callback:
        :param unit_definition_exists_callback:
        :return:
        """
        study_endpoint_selection.validate(
            study_objective_exist_callback,
            endpoint_exist_callback,
            timeframe_exist_callback,
            ct_term_exists_callback,
            unit_definition_exists_callback,
        )
        self._add_selection(study_endpoint_selection)

    @classmethod
    def from_repository_values(
        cls,
        study_uid: str,
        study_endpoints_selection: Iterable[StudySelectionEndpointVO],
    ) -> Self:
        """
        Factory method to create a AR
        :param study_uid:
        :param study_endpoints_selection:
        :return:
        """
        return cls(
            _study_uid=normalize_string(study_uid),
            _study_endpoints_selection=tuple(study_endpoints_selection),
        )

    def remove_endpoint_selection(self, study_selection_uid: str):
        """
        removing a study endpoint
        :param study_selection_uid:
        :return:
        """
        updated_selection = []
        for selection in self.study_endpoints_selection:
            if selection.study_selection_uid != study_selection_uid:
                updated_selection.append(selection)
        self._study_endpoints_selection = tuple(updated_selection)

    def set_new_order_for_selection(self, study_selection_uid: str, new_order: int):
        """
        Used to reorder a study endpoint
        :param study_selection_uid:
        :param new_order:
        :return:
        """
        # check if the new order is valid using the robustness principle
        if new_order > len(self.study_endpoints_selection):
            # If order is higher than maximum allowed then set to max
            new_order = len(self.study_endpoints_selection)
        elif new_order < 1:
            # If order is lower than 1 set to 1
            new_order = 1

        # find the selection
        selected_value, old_order = self.get_specific_endpoint_selection(
            study_selection_uid
        )
        # change the order
        updated_selections = []
        for order, selection in enumerate(self.study_endpoints_selection, start=1):
            # if the order is the where the new item is meant to be put
            if order == new_order:
                # we check if the order is being changed to lower or higher and add it to the list appropriately
                if old_order >= new_order:
                    # moving the selection to lower order
                    # Check if we are allowed to insert the value here, the rules are:
                    # - The study objective have to be the same as the looped selection
                    # - The endpoint level have to be the same as the looped selection
                    ValidationException.raise_if(
                        selection.endpoint_level_order
                        != selected_value.endpoint_level_order
                        or selection.study_objective_uid
                        != selected_value.study_objective_uid,
                        msg=f"Not allowed to move the selection to order ({str(new_order)})",
                    )
                    updated_selections.append(selected_value)
                    if (
                        selection.study_selection_uid
                        != selected_value.study_selection_uid
                    ):
                        updated_selections.append(selection)
                else:
                    # moving the selection to higher order
                    # Check if we are allowed to insert the value here, the rules are:
                    # - The study objective have to be the same as the looped selection
                    # - The endpoint level have to be the same as the looped selection
                    ValidationException.raise_if(
                        selection.endpoint_level_order
                        != selected_value.endpoint_level_order
                        or selection.study_objective_uid
                        != selected_value.study_objective_uid,
                        msg=f"Not allowed to move the selection to order ({str(new_order)})",
                    )
                    if (
                        selection.study_selection_uid
                        != selected_value.study_selection_uid
                    ):
                        updated_selections.append(selection)
                    updated_selections.append(selected_value)

            # We add all other vo to in the same order as before, except for the vo we are moving
            elif selection.study_selection_uid != selected_value.study_selection_uid:
                updated_selections.append(selection)
        self._study_endpoints_selection = tuple(updated_selections)

    def update_selection(
        self,
        updated_study_endpoint_selection: StudySelectionEndpointVO,
        study_objective_exist_callback: Callable[[str], bool] = (lambda _: True),
        endpoint_exist_callback: Callable[[str], bool] = (lambda _: True),
        timeframe_exist_callback: Callable[[str], bool] = (lambda _: True),
        ct_term_exists_callback: Callable[[str], bool] = (lambda _: True),
        unit_definition_exists_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        """
        Used when a study endpoint is patched
        :param updated_study_endpoint_selection:
        :param study_objective_exist_callback:
        :param endpoint_exist_callback:
        :param timeframe_exist_callback:
        :param ct_term_exists_callback:
        :param unit_definition_exists_callback:
        :return:
        """
        updated_study_endpoint_selection.validate(
            study_objective_exist_callback=study_objective_exist_callback,
            endpoint_exist_callback=endpoint_exist_callback,
            timeframe_exist_callback=timeframe_exist_callback,
            ct_term_exists_callback=ct_term_exists_callback,
            unit_definition_exists_callback=unit_definition_exists_callback,
        )
        # get original selection
        original_selection, _ = self.get_specific_endpoint_selection(
            study_selection_uid=updated_study_endpoint_selection.study_selection_uid
        )
        # Check if study objective or level have changed
        if (
            original_selection.endpoint_level_order
            != updated_study_endpoint_selection.endpoint_level_order
            or original_selection.study_objective_uid
            != updated_study_endpoint_selection.study_objective_uid
        ):
            # Remove the selections
            self.remove_endpoint_selection(
                study_selection_uid=updated_study_endpoint_selection.study_selection_uid
            )
            # Add it back
            self._add_selection(updated_study_endpoint_selection)
        else:
            updated_selection = []
            for selection in self.study_endpoints_selection:
                if (
                    selection.study_selection_uid
                    == updated_study_endpoint_selection.study_selection_uid
                ):
                    updated_selection.append(updated_study_endpoint_selection)
                else:
                    updated_selection.append(selection)
            self._study_endpoints_selection = tuple(updated_selection)

    def deleting_study_objective(self, study_objective_uid: str):
        """
        Function used when a study objective is deleted, logic is to set all study objective values used by study
        endpoints to None
        :param study_objective_uid:
        :return:
        """
        updated_selection = []
        for selection in self.study_endpoints_selection:
            if selection.study_objective_uid == study_objective_uid:
                updated_selection.append(
                    StudySelectionEndpointVO.from_input_values(
                        endpoint_uid=selection.endpoint_uid,
                        endpoint_version=selection.endpoint_version,
                        endpoint_level_uid=selection.endpoint_level_uid,
                        endpoint_sublevel_uid=selection.endpoint_sublevel_uid,
                        unit_separator=selection.unit_separator,
                        study_objective_uid=None,
                        study_selection_uid=selection.study_selection_uid,
                        start_date=selection.start_date,
                        timeframe_uid=selection.timeframe_uid,
                        timeframe_version=selection.timeframe_version,
                        endpoint_units=selection.endpoint_units,
                        endpoint_level_order=selection.endpoint_level_order,
                        author_id=selection.author_id,
                    )
                )
            else:
                updated_selection.append(selection)
        self._study_endpoints_selection = tuple(updated_selection)

    def validate(self):
        endpoints_timeframes = []
        for selection in self.study_endpoints_selection:
            AlreadyExistsException.raise_if(
                (
                    selection.study_objective_uid,
                    selection.endpoint_uid,
                    selection.timeframe_uid,
                    *selection.endpoint_units,
                )
                in endpoints_timeframes,
                msg="There is already a study endpoint created for the selected endpoint, timeframe and unit combination",
            )
            endpoints_timeframes.append(
                (
                    selection.study_objective_uid,
                    selection.endpoint_uid,
                    selection.timeframe_uid,
                    *selection.endpoint_units,
                )
            )
