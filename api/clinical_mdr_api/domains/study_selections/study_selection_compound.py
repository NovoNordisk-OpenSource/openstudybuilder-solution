import datetime
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Self

from clinical_mdr_api.domains.concepts.medicinal_product import MedicinalProductAR
from clinical_mdr_api.domains.controlled_terminologies.utils import CtTermInfo
from clinical_mdr_api.services.user_info import UserInfoService
from clinical_mdr_api.utils import normalize_string
from common import exceptions


def _raise(exc: ValueError) -> Any:
    raise exc


@dataclass(frozen=True)
class StudySelectionCompoundVO:
    """
    The StudySelectionCompoundVO acts as the value object for a single selection between a study and a compound
    """

    study_selection_uid: str
    study_uid: str | None
    compound_uid: str | None
    compound_alias_uid: str | None
    medicinal_product_uid: str | None
    type_of_treatment_uid: str | None
    reason_for_missing_value_uid: str | None
    dispenser_uid: str | None
    dispenser: CtTermInfo | None
    delivery_device_uid: str | None
    delivery_device: CtTermInfo | None
    other_info: str | None
    study_compound_dosing_count: int | None
    # Study selection Versioning
    start_date: datetime.datetime
    author_id: str
    author_username: str | None = None

    @classmethod
    def from_input_values(
        cls,  # NOSONAR - ignore too many parameters warning
        compound_uid: str | None,
        compound_alias_uid: str | None,
        medicinal_product_uid: str | None,
        type_of_treatment_uid: str | None,
        reason_for_missing_value_uid: str | None,
        dispenser_uid: str | None,
        delivery_device_uid: str | None,
        other_info: str | None,
        author_id: str,
        dispenser: CtTermInfo | None = None,
        delivery_device: CtTermInfo | None = None,
        study_uid: str | None = None,
        study_selection_uid: str | None = None,
        study_compound_dosing_count: int | None = None,
        start_date: datetime.datetime | None = None,
        generate_uid_callback: Callable[[], str] = (
            lambda: _raise(
                ValueError("generate_uid_callback necessary when uid not provided")
            )
        ),
    ) -> Self:
        """
        Factory method
        :param dispenser_uid:
        :param other_info:
        :param delivery_device_uid:
        :param compound_uid:
        :param compound_alias_uid:
        :param medicinal_product_uid:
        :param type_of_treatment_uid:
        :param reason_for_missing_value_uid:
        :param study_selection_uid:
        :param generate_uid_callback:
        :return:
        """
        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now(datetime.timezone.utc)

        # returns a new instance of the VO
        return StudySelectionCompoundVO(
            study_uid=study_uid,
            study_selection_uid=normalize_string(study_selection_uid),
            compound_uid=normalize_string(compound_uid),
            compound_alias_uid=normalize_string(compound_alias_uid),
            medicinal_product_uid=normalize_string(medicinal_product_uid),
            type_of_treatment_uid=normalize_string(type_of_treatment_uid),
            reason_for_missing_value_uid=normalize_string(reason_for_missing_value_uid),
            dispenser_uid=normalize_string(dispenser_uid),
            dispenser=dispenser,
            delivery_device_uid=normalize_string(delivery_device_uid),
            delivery_device=delivery_device,
            other_info=normalize_string(other_info),
            study_compound_dosing_count=study_compound_dosing_count,
            author_id=normalize_string(author_id),
            author_username=UserInfoService.get_author_username_from_id(author_id),
            start_date=start_date,
        )

    def validate(
        self,
        selection_uid_by_details_callback: Callable[
            ["StudySelectionCompoundVO"], str | None
        ] = lambda _: None,
        reason_for_missing_callback: Callable[[str], bool] = lambda _: True,
        compound_exist_callback: Callable[[str], bool] = lambda _: True,
        compound_alias_exist_callback: Callable[[str], bool] = lambda _: True,
        medicinal_product_exist_callback: Callable[[str], bool] = lambda _: True,
        medicinal_product_callback: Callable[
            ..., MedicinalProductAR | None
        ] = lambda _: None,
    ) -> None:
        """
        Raises ValueError or exceptions.BusinessLogicException if values do not comply with relevant business rules.

        """
        exceptions.ValidationException.raise_if(
            self.reason_for_missing_value_uid is not None
            and not reason_for_missing_callback(self.reason_for_missing_value_uid),
            msg="Unknown reason for missing value code provided for Reason For Missing",
        )

        if self.reason_for_missing_value_uid is not None:
            for value in (
                self.compound_uid,
                self.compound_alias_uid,
                self.medicinal_product_uid,
                self.other_info,
            ):
                exceptions.ValidationException.raise_if(
                    value is not None,
                    msg="If reason_for_missing_null_value_uid has a value, all fields except type of treatment have to be empty",
                )

        exceptions.BusinessLogicException.raise_if(
            self.compound_uid is not None
            and not compound_exist_callback(normalize_string(self.compound_uid)),
            msg=f"There is no approved Compound with UID '{self.compound_uid}'.",
        )

        exceptions.BusinessLogicException.raise_if(
            self.compound_alias_uid is not None
            and not compound_alias_exist_callback(
                normalize_string(self.compound_alias_uid)
            ),
            msg=f"There is no approved Compound Alias with UID '{self.compound_alias_uid}'.",
        )

        exceptions.BusinessLogicException.raise_if(
            self.medicinal_product_uid is not None
            and not medicinal_product_exist_callback(
                normalize_string(self.medicinal_product_uid)
            ),
            msg=f"There is no approved Medicinal Product with UID '{self.medicinal_product_uid}'.",
        )

        # Find an existing study compound selection with the same details:
        #   - Compound alias
        #   - Medicinal product
        #   - Dispenser
        #   - Delivery device
        existing_uid = selection_uid_by_details_callback(self)
        exceptions.AlreadyExistsException.raise_if(
            existing_uid and self.study_selection_uid != existing_uid,
            msg="Compound selection with the specified combination of compound, medicinal product, "
            "dispenser and delivery device already exists.",
        )

        medicinal_product: MedicinalProductAR | None = medicinal_product_callback(
            self.medicinal_product_uid
        )
        # Ensure that the provided CompoundAlias and MedicinalProduct both link to the same Compound
        exceptions.BusinessLogicException.raise_if(
            medicinal_product
            and medicinal_product.concept_vo.compound_uid != self.compound_uid,
            msg=f"Selected Compound Alias with UID '{self.compound_alias_uid}' and Medicinal Product with UID '{self.medicinal_product_uid}' must relate to the same compound",
        )


@dataclass
class StudySelectionCompoundsAR:
    _study_uid: str
    _study_compounds_selection: list[StudySelectionCompoundVO]
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    @property
    def study_uid(self) -> str:
        return self._study_uid

    @property
    def study_compounds_selection(self) -> list[StudySelectionCompoundVO]:
        return self._study_compounds_selection

    def get_specific_compound_selection(
        self, study_selection_uid: str
    ) -> tuple[StudySelectionCompoundVO, int]:
        """
        Used to receive a specific VO from the AR
        :param study_selection_uid:
        :return:
        """
        for order, selection in enumerate(self.study_compounds_selection, start=1):
            if selection.study_selection_uid == study_selection_uid:
                return selection, order
        raise exceptions.NotFoundException(
            msg=f"There is no selection between the Study Compound with UID '{study_selection_uid}' and the study."
        )

    def add_compound_selection(
        self,
        study_compound_selection: StudySelectionCompoundVO,
        selection_uid_by_details_callback: Callable[
            ["StudySelectionCompoundVO"], str | None
        ],
        reason_for_missing_callback: Callable[[str], bool] = lambda _: True,
        compound_exist_callback: Callable[[str], bool] = lambda _: True,
        compound_alias_exist_callback: Callable[[str], bool] = lambda _: True,
        medicinal_product_exist_callback: Callable[[str], bool] = lambda _: True,
        medicinal_product_callback: Callable[..., MedicinalProductAR | None] = (
            lambda _: None
        ),
    ) -> None:
        """
        Adding a new study compound to the _study_compound_selection
        :param study_compound_selection:
        :param reason_for_missing_callback:
        :param compound_exist_callback:
        :param compound_alias_exist_callback:
        :param medicinal_product_exist_callback:
        :param medicinal_product_callback:
        :return:
        """
        # validate VO before adding
        study_compound_selection.validate(
            selection_uid_by_details_callback=selection_uid_by_details_callback,
            reason_for_missing_callback=reason_for_missing_callback,
            compound_exist_callback=compound_exist_callback,
            compound_alias_exist_callback=compound_alias_exist_callback,
            medicinal_product_exist_callback=medicinal_product_exist_callback,
            medicinal_product_callback=medicinal_product_callback,
        )
        self._study_compounds_selection = self._study_compounds_selection + [
            study_compound_selection
        ]

    @classmethod
    def from_repository_values(
        cls,
        study_uid: str,
        study_compounds_selection: Iterable[StudySelectionCompoundVO],
    ) -> Self:
        """
        Factory method to create a AR
        :param study_uid:
        :param study_compounds_selection:
        :return:
        """
        return cls(
            _study_uid=normalize_string(study_uid),
            _study_compounds_selection=list(study_compounds_selection),
        )

    def remove_compound_selection(self, study_selection_uid: str):
        """
        removing a study compound
        :param study_selection_uid:
        :return:
        """
        updated_selection = []
        for selection in self.study_compounds_selection:
            if selection.study_selection_uid != study_selection_uid:
                updated_selection.append(selection)
        self._study_compounds_selection = updated_selection

    def set_new_order_for_selection(self, study_selection_uid: str, new_order: int):
        """
        Used to reorder a study compound
        :param study_selection_uid:
        :param new_order:
        :return:
        """
        # check if the new order is valid using the robustness principle
        if new_order > len(self.study_compounds_selection):
            # If order is higher than maximum allowed then set to max
            new_order = len(self.study_compounds_selection)
        elif new_order < 1:
            # If order is lower than 1 set to 1
            new_order = 1
        # find the selection
        selected_value, old_order = self.get_specific_compound_selection(
            study_selection_uid
        )
        # change the order
        updated_selections = []
        for order, selection in enumerate(self.study_compounds_selection, start=1):
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
        self._study_compounds_selection = updated_selections

    def update_selection(
        self,
        updated_study_compound_selection: StudySelectionCompoundVO,
        selection_uid_by_details_callback: Callable[
            ["StudySelectionCompoundVO"], str | None
        ],
        reason_for_missing_callback: Callable[[str], bool] = lambda _: True,
        compound_exist_callback: Callable[[str], bool] = lambda _: True,
        compound_alias_exist_callback: Callable[[str], bool] = lambda _: True,
        medicinal_product_exist_callback: Callable[[str], bool] = lambda _: True,
    ) -> None:
        """
        Used when a study compound is updated
        :param compound_exist_callback:
        :param reason_for_missing_callback:
        :param updated_study_compound_selection:
        :return:
        """
        updated_study_compound_selection.validate(
            selection_uid_by_details_callback=selection_uid_by_details_callback,
            reason_for_missing_callback=reason_for_missing_callback,
            compound_exist_callback=compound_exist_callback,
            compound_alias_exist_callback=compound_alias_exist_callback,
            medicinal_product_exist_callback=medicinal_product_exist_callback,
        )
        updated_selection = []
        for selection in self.study_compounds_selection:
            if (
                selection.study_selection_uid
                == updated_study_compound_selection.study_selection_uid
            ):
                updated_selection.append(updated_study_compound_selection)
            else:
                updated_selection.append(selection)
        self._study_compounds_selection = updated_selection
