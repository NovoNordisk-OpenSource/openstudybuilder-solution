"""Unit tests for the Study Interventions protocol table text helpers."""

from types import SimpleNamespace

from clinical_mdr_api.services.studies.study_interventions import (
    StudyInterventionsService,
)

STUDY_COMPOUND_UID = "StudyCompound_000001"
FREE_TEXT_DOSE_VALUE = "5 mL"
FREE_TEXT_DOSE_FREQUENCY = "Every other Tuesday"


def _compound() -> SimpleNamespace:
    return SimpleNamespace(study_compound_uid=STUDY_COMPOUND_UID)


def _dosing(
    dose_value: SimpleNamespace | None = None,
    free_text_dose_value: str | None = None,
    dose_frequency: SimpleNamespace | None = None,
    free_text_dose_frequency: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        dose_value=dose_value,
        free_text_dose_value=free_text_dose_value,
        dose_frequency=dose_frequency,
        free_text_dose_frequency=free_text_dose_frequency,
    )


def test_dosing_txt_renders_library_dose_value():
    dosings = {
        STUDY_COMPOUND_UID: [
            _dosing(
                dose_value=SimpleNamespace(value=10, unit_label="mg"),
                dose_frequency=SimpleNamespace(term_name="BID"),
            )
        ]
    }

    assert StudyInterventionsService._dosing_txt(_compound(), dosings) == "10 mg BID"


def test_dosing_txt_falls_back_to_free_text_dose_value():
    """Without the fallback the dose cell is blank for a free text dosing."""
    dosings = {
        STUDY_COMPOUND_UID: [
            _dosing(
                free_text_dose_value=FREE_TEXT_DOSE_VALUE,
                dose_frequency=SimpleNamespace(term_name="BID"),
            )
        ]
    }

    assert (
        StudyInterventionsService._dosing_txt(_compound(), dosings)
        == f"{FREE_TEXT_DOSE_VALUE} BID"
    )


def test_dosing_txt_free_text_dose_value_without_dose_frequency():
    dosings = {STUDY_COMPOUND_UID: [_dosing(free_text_dose_value=FREE_TEXT_DOSE_VALUE)]}

    assert (
        StudyInterventionsService._dosing_txt(_compound(), dosings)
        == FREE_TEXT_DOSE_VALUE
    )


def test_dosing_txt_without_any_dose_value():
    dosings = {STUDY_COMPOUND_UID: [_dosing()]}

    assert StudyInterventionsService._dosing_txt(_compound(), dosings) == "-"


def test_dosing_txt_without_any_dosing():
    assert StudyInterventionsService._dosing_txt(_compound(), {}) == "-"


def test_dosing_txt_falls_back_to_free_text_dose_frequency():
    """Without the fallback the frequency is missing from the dose cell."""
    dosings = {
        STUDY_COMPOUND_UID: [
            _dosing(
                dose_value=SimpleNamespace(value=10, unit_label="mg"),
                free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY,
            )
        ]
    }

    assert (
        StudyInterventionsService._dosing_txt(_compound(), dosings)
        == f"10 mg {FREE_TEXT_DOSE_FREQUENCY}"
    )


def test_dosing_txt_free_text_dose_frequency_without_dose_value():
    dosings = {
        STUDY_COMPOUND_UID: [_dosing(free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY)]
    }

    assert (
        StudyInterventionsService._dosing_txt(_compound(), dosings)
        == FREE_TEXT_DOSE_FREQUENCY
    )


def test_dosing_txt_both_dose_value_and_frequency_as_free_text():
    """The two free text fields are independent and both render."""
    dosings = {
        STUDY_COMPOUND_UID: [
            _dosing(
                free_text_dose_value=FREE_TEXT_DOSE_VALUE,
                free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY,
            )
        ]
    }

    assert (
        StudyInterventionsService._dosing_txt(_compound(), dosings)
        == f"{FREE_TEXT_DOSE_VALUE} {FREE_TEXT_DOSE_FREQUENCY}"
    )


def test_dosing_txt_library_frequency_wins_over_free_text():
    """Defensive: the API rejects both, but the library term takes precedence."""
    dosings = {
        STUDY_COMPOUND_UID: [
            _dosing(
                dose_value=SimpleNamespace(value=10, unit_label="mg"),
                dose_frequency=SimpleNamespace(term_name="BID"),
                free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY,
            )
        ]
    }

    assert StudyInterventionsService._dosing_txt(_compound(), dosings) == "10 mg BID"


def test_dosing_txt_renders_one_line_per_dosing():
    dosings = {
        STUDY_COMPOUND_UID: [
            _dosing(dose_value=SimpleNamespace(value=10, unit_label="mg")),
            _dosing(free_text_dose_value=FREE_TEXT_DOSE_VALUE),
        ]
    }

    assert (
        StudyInterventionsService._dosing_txt(_compound(), dosings)
        == f"10 mg\n{FREE_TEXT_DOSE_VALUE}"
    )
