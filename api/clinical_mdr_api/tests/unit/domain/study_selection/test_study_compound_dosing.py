import datetime
import unittest

from clinical_mdr_api.domains.concepts.medicinal_product import (
    MedicinalProductAR,
    MedicinalProductVO,
)
from clinical_mdr_api.domains.study_selections.study_compound_dosing import (
    StudyCompoundDosingVO,
    StudySelectionCompoundDosingsAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import (
    AUTHOR_ID,
    AUTHOR_USERNAME,
    random_str,
)
from common import exceptions

MEDICINAL_PRODUCT_UID = "MedicinalProduct_000001"
DOSE_VALUE_UID = "dose_value_uid1"
DOSE_FREQUENCY_UID_1 = "dose_frequency_uid1"
DOSE_FREQUENCY_UID_2 = "dose_frequency_uid2"
STUDY_ACTIVITY_INSTANCE_UID_1 = "StudyActivityInstance_000001"
STUDY_ACTIVITY_INSTANCE_UID_2 = "StudyActivityInstance_000002"
FREE_TEXT_DOSE_VALUE_1 = "5 mL twice a day"
FREE_TEXT_DOSE_VALUE_2 = "10 mL twice a day"
FREE_TEXT_DOSE_FREQUENCY_1 = "Every other Tuesday"
FREE_TEXT_DOSE_FREQUENCY_2 = "Twice per menstrual cycle"


def create_medicinal_product_ar(
    dose_frequency_uids: list[str] | None = None,
    dose_value_uids: list[str] | None = None,
) -> MedicinalProductAR:
    return MedicinalProductAR.from_repository_values(
        uid=MEDICINAL_PRODUCT_UID,
        concept_vo=MedicinalProductVO.from_repository_values(
            name="medicinal product name",
            name_sentence_case="medicinal product name",
            external_id=None,
            compound_uid="compound_uid1",
            pharmaceutical_product_uids=[],
            delivery_device_uid=None,
            dispenser_uid=None,
            dose_value_uids=(
                dose_value_uids if dose_value_uids is not None else [DOSE_VALUE_UID]
            ),
            dose_frequency_uids=dose_frequency_uids,
        ),
        library=LibraryVO.from_repository_values(
            library_name="Sponsor", is_editable=True
        ),
        item_metadata=LibraryItemMetadataVO.from_repository_values(
            change_description="Initial version",
            status=LibraryItemStatus.FINAL,
            author_id=AUTHOR_ID,
            author_username=AUTHOR_USERNAME,
            start_date=datetime.datetime.now(datetime.UTC),
            end_date=None,
            major_version=1,
            minor_version=0,
        ),
    )


def create_study_compound_dosing_vo(
    dose_frequency_uid: str | None = None,
    dose_value_uid: str | None = DOSE_VALUE_UID,
    free_text_dose_value: str | None = None,
    free_text_dose_frequency: str | None = None,
    study_selection_uid: str | None = None,
    study_activity_instance_uid: str | None = None,
) -> StudyCompoundDosingVO:
    return StudyCompoundDosingVO.from_input_values(
        study_uid="Study_000001",
        study_selection_uid=(
            study_selection_uid if study_selection_uid is not None else random_str()
        ),
        study_compound_uid="StudyCompound_000001",
        study_element_uid="StudyElement_000001",
        medicinal_product_uid=MEDICINAL_PRODUCT_UID,
        dose_value_uid=dose_value_uid,
        free_text_dose_value=free_text_dose_value,
        dose_frequency_uid=dose_frequency_uid,
        free_text_dose_frequency=free_text_dose_frequency,
        study_activity_instance_uid=study_activity_instance_uid,
        author_id=AUTHOR_ID,
        start_date=datetime.datetime.now(datetime.UTC),
    )


class TestStudyCompoundDosingVOValidate(unittest.TestCase):
    def _validate(
        self,
        compound_dosing_vo: StudyCompoundDosingVO,
        medicinal_product_ar: MedicinalProductAR,
    ) -> None:
        compound_dosing_vo.validate(
            selection_uid_by_compound_dose_and_frequency_callback=lambda _: None,
            medicinal_product_callback=lambda _: medicinal_product_ar,
        )

    def test__validate__dose_frequency_defined_on_medicinal_product__success(self):
        medicinal_product_ar = create_medicinal_product_ar(
            dose_frequency_uids=[DOSE_FREQUENCY_UID_1, DOSE_FREQUENCY_UID_2]
        )
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_2
        )

        self._validate(compound_dosing_vo, medicinal_product_ar)

    def test__validate__dose_frequency_not_on_medicinal_product__success(self):
        """A dose frequency is NOT restricted to the medicinal product's own list.

        A medicinal product defines a handful of frequencies while studies need the
        rest of the codelist, so membership is checked against the codelist instead
        — see TestStudyCompoundDosingVODoseFrequencyCodelist.
        """
        medicinal_product_ar = create_medicinal_product_ar(
            dose_frequency_uids=[DOSE_FREQUENCY_UID_1]
        )
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_2
        )

        self._validate(compound_dosing_vo, medicinal_product_ar)

    def test__validate__medicinal_product_without_dose_frequencies__success(self):
        """A product that defines no frequencies does not block the selection."""
        medicinal_product_ar = create_medicinal_product_ar(dose_frequency_uids=[])
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_1
        )

        self._validate(compound_dosing_vo, medicinal_product_ar)

    def test__validate__no_dose_frequency_selected__success(self):
        medicinal_product_ar = create_medicinal_product_ar()
        compound_dosing_vo = create_study_compound_dosing_vo(dose_frequency_uid=None)

        self._validate(compound_dosing_vo, medicinal_product_ar)

    def test__validate__medicinal_product_not_found__success(self):
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_1
        )

        compound_dosing_vo.validate(
            selection_uid_by_compound_dose_and_frequency_callback=lambda _: None,
            medicinal_product_callback=lambda _: None,
        )

    def test__validate__dose_value_not_defined_on_medicinal_product__failure(self):
        """The dose VALUE is still constrained to the medicinal product's own list."""
        medicinal_product_ar = create_medicinal_product_ar(dose_value_uids=[])
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_1
        )

        with self.assertRaises(exceptions.BusinessLogicException) as context:
            self._validate(compound_dosing_vo, medicinal_product_ar)

        self.assertIn("dose value", context.exception.msg)

    def test__validate__dose_collection_study_activity_instance__not_part_of_key(self):
        """The uniqueness key is (compound, dose value, dose frequency) only."""
        medicinal_product_ar = create_medicinal_product_ar()
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_1,
            study_activity_instance_uid=STUDY_ACTIVITY_INSTANCE_UID_1,
        )

        self._validate(compound_dosing_vo, medicinal_product_ar)


class TestStudyCompoundDosingVODoseFrequencyCodelist(unittest.TestCase):
    """A library dose frequency must be a term of the dose frequency codelist."""

    @staticmethod
    def _validate(
        compound_dosing_vo: StudyCompoundDosingVO,
        codelist_term_uids: list[str],
    ) -> None:
        compound_dosing_vo.validate(
            selection_uid_by_compound_dose_and_frequency_callback=lambda _: None,
            medicinal_product_callback=lambda _: create_medicinal_product_ar(),
            dose_frequency_term_exists_callback=(
                lambda term_uid: term_uid in codelist_term_uids
            ),
        )

    def test__validate__dose_frequency_in_codelist__success(self):
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_2
        )

        self._validate(compound_dosing_vo, [DOSE_FREQUENCY_UID_1, DOSE_FREQUENCY_UID_2])

    def test__validate__dose_frequency_not_in_codelist__failure(self):
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_2
        )

        with self.assertRaises(exceptions.ValidationException) as context:
            self._validate(compound_dosing_vo, [DOSE_FREQUENCY_UID_1])

        self.assertIn(DOSE_FREQUENCY_UID_2, context.exception.msg)

    def test__validate__no_dose_frequency__callback_not_consulted(self):
        compound_dosing_vo = create_study_compound_dosing_vo(dose_frequency_uid=None)

        self._validate(compound_dosing_vo, [])

    def test__validate__free_text_dose_frequency__callback_not_consulted(self):
        """Free text is not a codelist term, so the check must not apply to it."""
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=None,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
        )

        self._validate(compound_dosing_vo, [])

    def test__validate__callback_defaults_to_permissive(self):
        """Omitting the callback skips the check rather than rejecting everything."""
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_1
        )

        compound_dosing_vo.validate(
            selection_uid_by_compound_dose_and_frequency_callback=lambda _: None,
        )


class TestStudyCompoundDosingVODoseCollectionInstance(unittest.TestCase):
    def test__from_input_values__uid_is_normalized(self):
        compound_dosing_vo = create_study_compound_dosing_vo(
            study_activity_instance_uid=f"  {STUDY_ACTIVITY_INSTANCE_UID_1}  "
        )

        self.assertEqual(
            compound_dosing_vo.study_activity_instance_uid,
            STUDY_ACTIVITY_INSTANCE_UID_1,
        )

    def test__from_input_values__uid_defaults_to_none(self):
        compound_dosing_vo = create_study_compound_dosing_vo()

        self.assertIsNone(compound_dosing_vo.study_activity_instance_uid)


class TestStudyCompoundDosingVOFreeTextDoseValue(unittest.TestCase):
    @staticmethod
    def _validate(compound_dosing_vo: StudyCompoundDosingVO) -> None:
        compound_dosing_vo.validate(
            selection_uid_by_compound_dose_and_frequency_callback=lambda _: None,
            medicinal_product_callback=lambda _: create_medicinal_product_ar(),
        )

    def test__validate__free_text_dose_value_only__success(self):
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_value_uid=None, free_text_dose_value=FREE_TEXT_DOSE_VALUE_1
        )

        self._validate(compound_dosing_vo)

    def test__validate__library_dose_value_only__success(self):
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_value_uid=DOSE_VALUE_UID, free_text_dose_value=None
        )

        self._validate(compound_dosing_vo)

    def test__validate__no_dose_value_at_all__success(self):
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_value_uid=None, free_text_dose_value=None
        )

        self._validate(compound_dosing_vo)

    def test__validate__both_dose_values__failure(self):
        """The two dose value modes are mutually exclusive."""
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_value_uid=DOSE_VALUE_UID,
            free_text_dose_value=FREE_TEXT_DOSE_VALUE_1,
        )

        with self.assertRaises(exceptions.ValidationException) as context:
            self._validate(compound_dosing_vo)

        self.assertIn("dose_value_uid", context.exception.msg)
        self.assertIn("free_text_dose_value", context.exception.msg)

    def test__validate__both_dose_values__raises_before_duplicate_check(self):
        """A contradictory payload must not be reported as an existing selection."""
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_value_uid=DOSE_VALUE_UID,
            free_text_dose_value=FREE_TEXT_DOSE_VALUE_1,
        )

        with self.assertRaises(exceptions.ValidationException):
            compound_dosing_vo.validate(
                selection_uid_by_compound_dose_and_frequency_callback=(
                    lambda _: "StudyCompoundDosing_000042"
                ),
            )

    def test__from_input_values__free_text_dose_value_is_normalized(self):
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_value_uid=None,
            free_text_dose_value=f"  {FREE_TEXT_DOSE_VALUE_1}  ",
        )

        self.assertEqual(
            compound_dosing_vo.free_text_dose_value, FREE_TEXT_DOSE_VALUE_1
        )

    def test__from_input_values__blank_free_text_dose_value_becomes_none(self):
        """Blank input must not defeat the exclusivity rule or the uniqueness key."""
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_value_uid=DOSE_VALUE_UID, free_text_dose_value="   "
        )

        self.assertIsNone(compound_dosing_vo.free_text_dose_value)
        self._validate(compound_dosing_vo)

    def test__from_input_values__free_text_dose_value_defaults_to_none(self):
        compound_dosing_vo = create_study_compound_dosing_vo()

        self.assertIsNone(compound_dosing_vo.free_text_dose_value)


class TestStudyCompoundDosingVOFreeTextDoseFrequency(unittest.TestCase):
    @staticmethod
    def _validate(compound_dosing_vo: StudyCompoundDosingVO) -> None:
        compound_dosing_vo.validate(
            selection_uid_by_compound_dose_and_frequency_callback=lambda _: None,
            medicinal_product_callback=lambda _: create_medicinal_product_ar(),
        )

    def test__validate__free_text_dose_frequency_only__success(self):
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=None,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
        )

        self._validate(compound_dosing_vo)

    def test__validate__library_dose_frequency_only__success(self):
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_1, free_text_dose_frequency=None
        )

        self._validate(compound_dosing_vo)

    def test__validate__no_dose_frequency_at_all__success(self):
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=None, free_text_dose_frequency=None
        )

        self._validate(compound_dosing_vo)

    def test__validate__both_dose_frequencies__failure(self):
        """The two dose frequency modes are mutually exclusive."""
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_1,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
        )

        with self.assertRaises(exceptions.ValidationException) as context:
            self._validate(compound_dosing_vo)

        self.assertIn("dose_frequency_uid", context.exception.msg)
        self.assertIn("free_text_dose_frequency", context.exception.msg)

    def test__validate__both_dose_frequencies__raises_before_duplicate_check(self):
        """A contradictory payload must not be reported as an existing selection."""
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_1,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
        )

        with self.assertRaises(exceptions.ValidationException):
            compound_dosing_vo.validate(
                selection_uid_by_compound_dose_and_frequency_callback=(
                    lambda _: "StudyCompoundDosing_000042"
                ),
            )

    def test__validate__both_fields_as_free_text__success(self):
        """The dose value and the dose frequency choices are independent axes."""
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_value_uid=None,
            free_text_dose_value=FREE_TEXT_DOSE_VALUE_1,
            dose_frequency_uid=None,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
        )

        self._validate(compound_dosing_vo)

    def test__validate__library_value_with_free_text_frequency__success(self):
        """Mixing one library source with one free text source is legal."""
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_value_uid=DOSE_VALUE_UID,
            dose_frequency_uid=None,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
        )

        self._validate(compound_dosing_vo)

    def test__from_input_values__free_text_dose_frequency_is_normalized(self):
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=None,
            free_text_dose_frequency=f"  {FREE_TEXT_DOSE_FREQUENCY_1}  ",
        )

        self.assertEqual(
            compound_dosing_vo.free_text_dose_frequency, FREE_TEXT_DOSE_FREQUENCY_1
        )

    def test__from_input_values__blank_free_text_dose_frequency_becomes_none(self):
        """Blank input must not defeat the exclusivity rule or the uniqueness key."""
        compound_dosing_vo = create_study_compound_dosing_vo(
            dose_frequency_uid=DOSE_FREQUENCY_UID_1, free_text_dose_frequency="   "
        )

        self.assertIsNone(compound_dosing_vo.free_text_dose_frequency)
        self._validate(compound_dosing_vo)

    def test__from_input_values__free_text_dose_frequency_defaults_to_none(self):
        compound_dosing_vo = create_study_compound_dosing_vo()

        self.assertIsNone(compound_dosing_vo.free_text_dose_frequency)


class TestStudySelectionCompoundDosingsARHasDataChanges(unittest.TestCase):
    def test__has_data_changes__only_instance_uid_differs__true(self):
        """Regression guard: the dose collection uid must take part in the diff."""
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            study_activity_instance_uid=STUDY_ACTIVITY_INSTANCE_UID_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            study_activity_instance_uid=STUDY_ACTIVITY_INSTANCE_UID_2,
        )

        self.assertTrue(
            StudySelectionCompoundDosingsAR._has_data_changes(current, updated)
        )

    def test__has_data_changes__instance_uid_cleared__true(self):
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            study_activity_instance_uid=STUDY_ACTIVITY_INSTANCE_UID_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            study_activity_instance_uid=None,
        )

        self.assertTrue(
            StudySelectionCompoundDosingsAR._has_data_changes(current, updated)
        )

    def test__has_data_changes__only_free_text_dose_value_differs__true(self):
        """Regression guard: without this the patch is a silent no-op."""
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_value_uid=None,
            free_text_dose_value=FREE_TEXT_DOSE_VALUE_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_value_uid=None,
            free_text_dose_value=FREE_TEXT_DOSE_VALUE_2,
        )

        self.assertTrue(
            StudySelectionCompoundDosingsAR._has_data_changes(current, updated)
        )

    def test__has_data_changes__free_text_dose_value_set__true(self):
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_value_uid=None,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_value_uid=None,
            free_text_dose_value=FREE_TEXT_DOSE_VALUE_1,
        )

        self.assertTrue(
            StudySelectionCompoundDosingsAR._has_data_changes(current, updated)
        )

    def test__has_data_changes__free_text_dose_value_cleared__true(self):
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_value_uid=None,
            free_text_dose_value=FREE_TEXT_DOSE_VALUE_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_value_uid=None,
            free_text_dose_value=None,
        )

        self.assertTrue(
            StudySelectionCompoundDosingsAR._has_data_changes(current, updated)
        )

    def test__has_data_changes__free_text_dose_value_unchanged__false(self):
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_value_uid=None,
            free_text_dose_value=FREE_TEXT_DOSE_VALUE_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_value_uid=None,
            free_text_dose_value=FREE_TEXT_DOSE_VALUE_1,
        )

        self.assertFalse(
            StudySelectionCompoundDosingsAR._has_data_changes(current, updated)
        )

    def test__has_data_changes__only_free_text_dose_frequency_differs__true(self):
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_frequency_uid=None,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_frequency_uid=None,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_2,
        )

        self.assertTrue(
            StudySelectionCompoundDosingsAR._has_data_changes(current, updated)
        )

    def test__has_data_changes__free_text_dose_frequency_set__true(self):
        """Switching the frequency from the library to free text is a change."""
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_frequency_uid=DOSE_FREQUENCY_UID_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_frequency_uid=None,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
        )

        self.assertTrue(
            StudySelectionCompoundDosingsAR._has_data_changes(current, updated)
        )

    def test__has_data_changes__free_text_dose_frequency_cleared__true(self):
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_frequency_uid=None,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_frequency_uid=None,
            free_text_dose_frequency=None,
        )

        self.assertTrue(
            StudySelectionCompoundDosingsAR._has_data_changes(current, updated)
        )

    def test__has_data_changes__free_text_dose_frequency_unchanged__false(self):
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_frequency_uid=None,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_frequency_uid=None,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
        )

        self.assertFalse(
            StudySelectionCompoundDosingsAR._has_data_changes(current, updated)
        )


class TestStudySelectionCompoundDosingsARUpdateSelection(unittest.TestCase):
    @staticmethod
    def _update(
        current: StudyCompoundDosingVO, updated: StudyCompoundDosingVO
    ) -> StudyCompoundDosingVO:
        selection_ar = StudySelectionCompoundDosingsAR.from_repository_values(
            study_uid="Study_000001", selection=[current]
        )
        selection_ar.update_selection(
            updated_study_compound_dosing_selection=updated,
            selection_uid_by_compound_dose_and_frequency_callback=lambda _: None,
        )
        return selection_ar.study_compound_dosings_selection[0]

    def test__update_selection__only_instance_uid_changed__replaces_vo(self):
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            study_activity_instance_uid=STUDY_ACTIVITY_INSTANCE_UID_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            study_activity_instance_uid=STUDY_ACTIVITY_INSTANCE_UID_2,
        )

        selection = self._update(current, updated)

        self.assertIs(selection, updated)
        self.assertEqual(
            selection.study_activity_instance_uid,
            STUDY_ACTIVITY_INSTANCE_UID_2,
        )

    def test__update_selection__only_free_text_dose_value_changed__replaces_vo(self):
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_value_uid=None,
            free_text_dose_value=FREE_TEXT_DOSE_VALUE_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_value_uid=None,
            free_text_dose_value=FREE_TEXT_DOSE_VALUE_2,
        )

        selection = self._update(current, updated)

        self.assertIs(selection, updated)
        self.assertEqual(selection.free_text_dose_value, FREE_TEXT_DOSE_VALUE_2)

    def test__update_selection__both_dose_values__failure(self):
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_value_uid=None,
            free_text_dose_value=FREE_TEXT_DOSE_VALUE_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_value_uid=DOSE_VALUE_UID,
            free_text_dose_value=FREE_TEXT_DOSE_VALUE_1,
        )

        with self.assertRaises(exceptions.ValidationException):
            self._update(current, updated)

    def test__update_selection__only_free_text_dose_frequency_changed__replaces_vo(
        self,
    ):
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_frequency_uid=None,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_frequency_uid=None,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_2,
        )

        selection = self._update(current, updated)

        self.assertIs(selection, updated)
        self.assertEqual(selection.free_text_dose_frequency, FREE_TEXT_DOSE_FREQUENCY_2)

    def test__update_selection__frequency_switched_to_library__clears_free_text(self):
        """Switching back to the library must drop the free text frequency."""
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_frequency_uid=None,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_frequency_uid=DOSE_FREQUENCY_UID_1,
            free_text_dose_frequency=None,
        )

        selection = self._update(current, updated)

        self.assertIs(selection, updated)
        self.assertIsNone(selection.free_text_dose_frequency)
        self.assertEqual(selection.dose_frequency_uid, DOSE_FREQUENCY_UID_1)

    def test__update_selection__both_dose_frequencies__failure(self):
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_frequency_uid=None,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            dose_frequency_uid=DOSE_FREQUENCY_UID_1,
            free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
        )

        with self.assertRaises(exceptions.ValidationException):
            self._update(current, updated)

    def test__update_selection__nothing_changed__preserves_object_identity(self):
        """The repository detects a no-op by identity (`is not`), so it must hold."""
        current = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            study_activity_instance_uid=STUDY_ACTIVITY_INSTANCE_UID_1,
        )
        updated = create_study_compound_dosing_vo(
            study_selection_uid="StudyCompoundDosing_000001",
            study_activity_instance_uid=STUDY_ACTIVITY_INSTANCE_UID_1,
        )

        selection = self._update(current, updated)

        self.assertIs(selection, current)
