"""Common utility constants / functions used by router functions."""

from fastapi import Path

# Useful type declarations

studyUID = Path(description="The unique id of the study.")

study_selection_uid = Path(description="The unique id of the study selection.")

study_design_cell_uid = Path(description="The unique id of the study design cell.")

study_activity_schedule_uid = Path(
    description="The unique id of the study activity schedule."
)

study_activity_instruction_uid = Path(
    description="The unique id of the study activity instruction."
)

study_compound_dosing_uid = Path(
    description="The unique id of the study compound dosing."
)

study_soa_footnote_uid = Path(description="The unique id of the study soa footnote.")
