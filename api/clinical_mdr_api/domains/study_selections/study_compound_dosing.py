import datetime
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any, Self

from clinical_mdr_api.domains.concepts.medicinal_product import MedicinalProductAR
from clinical_mdr_api.utils import normalize_string
from common import exceptions


def _raise(exc: ValueError) -> Any:
    raise exc


@dataclass
class StudyCompoundDosingVO:
    study_uid: str
    study_selection_uid: str
    study_compound_uid: str | None
    study_element_uid: str | None

    # Study selection Versioning
    start_date: datetime.datetime
    author_id: str
    author_username: str | None = None

    # Optional information
    compound_uid: str | None = None
    compound_alias_uid: str | None = None
    medicinal_product_uid: str | None = None
    dose_frequency_uid: str | None = None
    dose_value_uid: str | None = None
    free_text_dose_value: str | None = None
    free_text_dose_frequency: str | None = None
    composition: str | None = None
    study_activity_instance_uid: str | None = None

    @classmethod
    def from_input_values(
        cls,
        study_compound_uid: str | None,
        study_element_uid: str | None,
        dose_value_uid: str | None,
        dose_frequency_uid: str | None,
        author_id: str,
        study_uid: str,
        compound_uid: str | None = None,
        compound_alias_uid: str | None = None,
        medicinal_product_uid: str | None = None,
        free_text_dose_value: str | None = None,
        free_text_dose_frequency: str | None = None,
        composition: str | None = None,
        study_activity_instance_uid: str | None = None,
        study_selection_uid: str | None = None,
        start_date: datetime.datetime | None = None,
        generate_uid_callback: Callable[[], str] = (
            lambda: _raise(
                ValueError("generate_uid_callback necessary when uid not provided")
            )
        ),
    ) -> Self:
        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now(datetime.UTC)

        return StudyCompoundDosingVO(
            study_uid=study_uid,
            study_selection_uid=normalize_string(study_selection_uid),
            study_compound_uid=normalize_string(study_compound_uid),
            compound_uid=normalize_string(compound_uid),
            compound_alias_uid=normalize_string(compound_alias_uid),
            medicinal_product_uid=normalize_string(medicinal_product_uid),
            study_element_uid=normalize_string(study_element_uid),
            dose_value_uid=normalize_string(dose_value_uid),
            dose_frequency_uid=normalize_string(dose_frequency_uid),
            # Normalized so that a blank string cannot masquerade as a set value
            # and defeat the exclusivity rule or the uniqueness key.
            free_text_dose_value=normalize_string(free_text_dose_value),
            free_text_dose_frequency=normalize_string(free_text_dose_frequency),
            composition=composition,
            study_activity_instance_uid=normalize_string(study_activity_instance_uid),
            author_id=normalize_string(author_id),
            start_date=start_date,
        )

    def validate(
        self,
        selection_uid_by_compound_dose_and_frequency_callback: Callable[
            [Self], str | None
        ],
        medicinal_product_callback: Callable[..., MedicinalProductAR | None] = (
            lambda _: None
        ),
        # Answers "is this uid a term of the dose frequency codelist?". Boolean
        # rather than the term itself, so the permissive default below reads as
        # "skip the check" — a default returning None would instead reject every
        # frequency whenever the callback is omitted.
        dose_frequency_term_exists_callback: Callable[[str], bool] = lambda _: True,
    ) -> None:
        """
        Raises ValueError or exceptions.BusinessLogicException if values do not comply with relevant business rules.

        """
        # The dose value and the dose frequency are each either picked from the
        # library or given as study level free text, never both. The two fields are
        # independent of one another: a library value with a free text frequency is
        # a legal combination. Checked first, so that a contradictory payload gets a
        # clear error instead of a confusing 'already exists'.
        exceptions.ValidationException.raise_if(
            self.dose_value_uid is not None and self.free_text_dose_value is not None,
            msg="Only one of 'dose_value_uid' and 'free_text_dose_value' may be provided.",
        )
        exceptions.ValidationException.raise_if(
            self.dose_frequency_uid is not None
            and self.free_text_dose_frequency is not None,
            msg="Only one of 'dose_frequency_uid' and 'free_text_dose_frequency' may be provided.",
        )

        # A library dose frequency may be any term of the dose frequency codelist,
        # not only one of those defined on the medicinal product. Checked here so
        # the caller gets this message rather than the persistence layer's, which
        # names the codelist by uid and is raised mid-transaction.
        exceptions.ValidationException.raise_if(
            self.dose_frequency_uid is not None
            and not dose_frequency_term_exists_callback(self.dose_frequency_uid),
            msg=f"Dose frequency term '{self.dose_frequency_uid}' is not a term of the dose frequency codelist.",
        )

        # Find a compound dosing selection with the same medicinal product, dose value, dose frequency
        existing_uid = selection_uid_by_compound_dose_and_frequency_callback(self)
        exceptions.AlreadyExistsException.raise_if(
            existing_uid and self.study_selection_uid != existing_uid,
            msg="Compound dosing selection with the specified compound, dose value and dose frequency already exists.",
        )

        # Validate that the dose value is actually defined on the selected library
        # compound (i.e. medicinal product). The dose FREQUENCY is deliberately not
        # constrained this way — it may be any codelist term, checked above — because
        # a medicinal product lists only a handful of frequencies while studies need
        # the rest of the codelist. The dose value has no such wider set to fall back
        # on: it points at a numeric value concept, not a codelist term.
        # Guarded on the uid being set, so a study level free text value escapes it.
        medicinal_product: MedicinalProductAR | None = medicinal_product_callback(
            self.medicinal_product_uid
        )
        if medicinal_product is not None:
            exceptions.BusinessLogicException.raise_if(
                self.dose_value_uid is not None
                and medicinal_product.concept_vo.dose_value_uids is not None
                and self.dose_value_uid
                not in medicinal_product.concept_vo.dose_value_uids,
                msg=f"Selected dose value is not valid for medicinal product '{medicinal_product.concept_vo.name}'.",
            )


@dataclass
class StudySelectionCompoundDosingsAR:
    _study_uid: str
    _study_compound_dosings_selection: list[StudyCompoundDosingVO]
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    @property
    def study_uid(self) -> str:
        return self._study_uid

    @property
    def study_compound_dosings_selection(self) -> list[StudyCompoundDosingVO]:
        return self._study_compound_dosings_selection

    def get_specific_compound_dosing_selection(
        self, study_selection_uid: str
    ) -> tuple[StudyCompoundDosingVO, int]:
        """
        Used to receive a specific VO from the AR
        :param study_selection_uid:
        :return:
        """
        for order, selection in enumerate(
            self.study_compound_dosings_selection, start=1
        ):
            if selection.study_selection_uid == study_selection_uid:
                return selection, order
        raise exceptions.NotFoundException(
            msg=f"There is no selection between the Compound Dosing with UID '{study_selection_uid}' and the study."
        )

    def add_compound_dosing_selection(
        self,
        study_compound_dosing_selection: StudyCompoundDosingVO,
        selection_uid_by_compound_dose_and_frequency_callback: Callable[
            [StudyCompoundDosingVO], str | None
        ],
        medicinal_product_callback: Callable[..., MedicinalProductAR | None] = (
            lambda _: None
        ),
        dose_frequency_term_exists_callback: Callable[[str], bool] = lambda _: True,
    ) -> None:
        """
        Adding a new study compound to the _study_compound_selection
        """
        # validate VO before adding
        study_compound_dosing_selection.validate(
            selection_uid_by_compound_dose_and_frequency_callback=selection_uid_by_compound_dose_and_frequency_callback,
            medicinal_product_callback=medicinal_product_callback,
            dose_frequency_term_exists_callback=dose_frequency_term_exists_callback,
        )
        self._study_compound_dosings_selection = [
            *self._study_compound_dosings_selection,
            study_compound_dosing_selection,
        ]

    @classmethod
    def from_repository_values(
        cls,
        study_uid: str,
        selection: Iterable[StudyCompoundDosingVO],
    ) -> Self:
        """
        Factory method to create a AR
        """
        return cls(
            _study_uid=normalize_string(study_uid),
            _study_compound_dosings_selection=list(selection),
        )

    def remove_compound_dosing_selection(self, study_selection_uid: str):
        """
        removing a study compound dosing
        :param study_selection_uid:
        :return:
        """
        updated_selection = []
        for selection in self.study_compound_dosings_selection:
            if selection.study_selection_uid != study_selection_uid:
                updated_selection.append(selection)
        self._study_compound_dosings_selection = updated_selection

    def set_new_order_for_selection(self, study_selection_uid: str, new_order: int):
        """
        Used to reorder a study compound dosing
        :param study_selection_uid:
        :param new_order:
        :return:
        """
        # check if the new order is valid using the robustness principle
        if new_order > len(self.study_compound_dosings_selection):
            # If order is higher than maximum allowed then set to max
            new_order = len(self.study_compound_dosings_selection)
        elif new_order < 1:
            # If order is lower than 1 set to 1
            new_order = 1
        # find the selection
        selected_value, old_order = self.get_specific_compound_dosing_selection(
            study_selection_uid
        )
        # change the order
        updated_selections = []
        for order, selection in enumerate(
            self.study_compound_dosings_selection, start=1
        ):
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
        self._study_compound_dosings_selection = updated_selections

    @staticmethod
    def _has_data_changes(
        current: StudyCompoundDosingVO, updated: StudyCompoundDosingVO
    ) -> bool:
        return (
            current.study_compound_uid != updated.study_compound_uid
            or current.study_element_uid != updated.study_element_uid
            or current.compound_uid != updated.compound_uid
            or current.compound_alias_uid != updated.compound_alias_uid
            or current.medicinal_product_uid != updated.medicinal_product_uid
            or current.dose_frequency_uid != updated.dose_frequency_uid
            or current.dose_value_uid != updated.dose_value_uid
            or current.free_text_dose_value != updated.free_text_dose_value
            or current.free_text_dose_frequency != updated.free_text_dose_frequency
            or current.composition != updated.composition
            or current.study_activity_instance_uid
            != updated.study_activity_instance_uid
        )

    def update_selection(
        self,
        updated_study_compound_dosing_selection: StudyCompoundDosingVO,
        selection_uid_by_compound_dose_and_frequency_callback: Callable[
            [StudyCompoundDosingVO], str | None
        ],
        medicinal_product_callback: Callable[..., MedicinalProductAR | None] = (
            lambda _: None
        ),
        dose_frequency_term_exists_callback: Callable[[str], bool] = lambda _: True,
    ) -> None:
        """
        Used when a study compound is updated
        """
        updated_study_compound_dosing_selection.validate(
            selection_uid_by_compound_dose_and_frequency_callback=selection_uid_by_compound_dose_and_frequency_callback,
            medicinal_product_callback=medicinal_product_callback,
            dose_frequency_term_exists_callback=dose_frequency_term_exists_callback,
        )
        updated_selection = []
        for selection in self.study_compound_dosings_selection:
            if (
                selection.study_selection_uid
                == updated_study_compound_dosing_selection.study_selection_uid
            ):
                # Only replace the VO if data fields actually changed,
                # so that the repository's identity check (is not) correctly
                # detects no change and skips creating a new node.
                if self._has_data_changes(
                    selection, updated_study_compound_dosing_selection
                ):
                    updated_selection.append(updated_study_compound_dosing_selection)
                else:
                    updated_selection.append(selection)
            else:
                updated_selection.append(selection)
        self._study_compound_dosings_selection = updated_selection
