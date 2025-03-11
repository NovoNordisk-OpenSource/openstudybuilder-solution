import datetime
from collections import OrderedDict

from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTermName
from clinical_mdr_api.models.study_selections.study import StudySoaPreferences
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpoch
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyDesignCell,
    StudySelectionArmWithConnectedBranchArms,
    StudySelectionElement,
)
from clinical_mdr_api.models.study_selections.study_visit import StudyVisit
from clinical_mdr_api.services.studies.study_design_figure import (
    StudyDesignFigureService,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_USERNAME

STUDY_UID = "Study_000001"

STUDY_ARMS = OrderedDict(
    (
        (
            "StudyArm_000009",
            StudySelectionArmWithConnectedBranchArms(
                study_uid=STUDY_UID,
                order=1,
                arm_uid="StudyArm_000009",
                name="NPH insulin",
                short_name="NPH insulin",
                description=None,
                code="A",
                arm_colour="#FFFDE7FF",
                randomization_group="A",
                number_of_subjects=50,
                arm_type=CTTermName(
                    term_uid="CTTerm_000081",
                    codelist_uid="CTCodelist_000022",
                    sponsor_preferred_name="Investigational Arm",
                    sponsor_preferred_name_sentence_case="investigational arm",
                    order=1,
                    start_date=datetime.datetime(2022, 7, 14, 11, 18, 29, 635044),
                ),
                start_date=datetime.datetime(2022, 8, 25, 19, 32, 11, 640636),
                author_username=AUTHOR_USERNAME,
            ),
        ),
        (
            "StudyArm_000011",
            StudySelectionArmWithConnectedBranchArms(
                study_uid=STUDY_UID,
                order=2,
                arm_uid="StudyArm_000011",
                name="Metformin",
                short_name="Metformin is longer",
                description=None,
                code="B",
                arm_colour="#FFEBEEFF",
                randomization_group="B",
                number_of_subjects=50,
                arm_type=CTTermName(
                    term_uid="CTTerm_000081",
                    codelist_uid="CTCodelist_000022",
                    sponsor_preferred_name="Investigational Arm",
                    sponsor_preferred_name_sentence_case="investigational arm",
                    order=1,
                    start_date=datetime.datetime(2022, 7, 14, 11, 18, 29, 635044),
                ),
                start_date=datetime.datetime(2022, 8, 25, 9, 33, 24, 232339),
                author_username=AUTHOR_USERNAME,
            ),
        ),
        (
            "StudyArm_000045",
            StudySelectionArmWithConnectedBranchArms(
                study_uid=STUDY_UID,
                order=3,
                arm_uid="StudyArm_000045",
                name="Another arm",
                short_name="Another arm",
                description=None,
                code=None,
                arm_colour="#F3E5F5FF",
                randomization_group=None,
                number_of_subjects=None,
                arm_type=None,
                start_date=datetime.datetime(2022, 8, 25, 19, 32, 0, 886693),
                author_username=AUTHOR_USERNAME,
            ),
        ),
        (
            "StudyArm_000048",
            StudySelectionArmWithConnectedBranchArms(
                study_uid=STUDY_UID,
                order=4,
                arm_uid="StudyArm_000048",
                name="More arms",
                short_name="More arms",
                description=None,
                code=None,
                arm_colour="#E8EAF6FF",
                randomization_group=None,
                number_of_subjects=None,
                arm_type=None,
                start_date=datetime.datetime(2022, 8, 25, 19, 46, 11, 300649),
                author_username=AUTHOR_USERNAME,
            ),
        ),
    )
)

STUDY_EPOCHS = (
    StudyEpoch(
        study_uid=STUDY_UID,
        start_rule="Subject must sign informed consent",
        epoch="C48262_SCREENING",
        epoch_subtype="C48262_SCREENING",
        order=1,
        duration=15,
        color_hash="#A5D6A7FF",
        uid="StudyEpoch_000001",
        epoch_name="Screening",
        epoch_ctterm={
            "term_uid": "C48262_SCREENING",
            "sponsor_preferred_name": "Screening",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_subtype_name="Screening",
        epoch_subtype_ctterm={
            "term_uid": "C48262_SCREENING",
            "sponsor_preferred_name": "Screening",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_type="CTTerm_000001",
        epoch_type_name="Screening epoch type name",
        epoch_type_ctterm={
            "term_uid": "CTTerm_000001",
            "sponsor_preferred_name": "Screening epoch type name",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        start_day=-14,
        end_day=1,
        start_date="2022-07-16 09:13:42",
        status="DRAFT",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        change_description="Initial Version",
        change_type="add",
        study_visit_count=1,
    ),
    StudyEpoch(
        study_uid=STUDY_UID,
        start_rule="Subject must fulfil randomisation criteria",
        epoch="C101526_TREATMENT",
        epoch_subtype="C101526_TREATMENT",
        order=2,
        duration=63,
        color_hash="#2E7D32FF",
        uid="StudyEpoch_000002",
        epoch_name="Treatment",
        epoch_ctterm={
            "term_uid": "C101526_TREATMENT",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_subtype_name="Treatment",
        epoch_subtype_ctterm={
            "term_uid": "C101526_TREATMENT",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_type="C101526_TREATMENT",
        epoch_type_name="Treatment",
        epoch_type_ctterm={
            "term_uid": "C101526_TREATMENT",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        start_day=1,
        end_day=64,
        start_date="2022-07-16 09:13:42",
        status="DRAFT",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        change_description="Initial Version",
        change_type="add",
        study_visit_count=9,
    ),
    StudyEpoch(
        study_uid=STUDY_UID,
        start_rule=None,
        epoch="CTTerm_000007",
        epoch_subtype="CTTerm_000007",
        order=3,
        description="Treatment Extension",
        duration=119,
        color_hash="#80DEEAFF",
        uid="StudyEpoch_000042",
        epoch_name="Extension",
        epoch_ctterm={
            "term_uid": "CTTerm_000007",
            "sponsor_preferred_name": "Extension",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_subtype_name="Extension",
        epoch_subtype_ctterm={
            "term_uid": "CTTerm_000007",
            "sponsor_preferred_name": "Extension",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_type="C101526_TREATMENT",
        epoch_type_name="Treatment",
        epoch_type_ctterm={
            "term_uid": "C101526_TREATMENT",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        start_day=64,
        end_day=183,
        start_date="2022-08-26 02:06:50",
        status="DRAFT",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        change_description="Initial Version",
        change_type="add",
        study_visit_count=1,
    ),
    StudyEpoch(
        study_uid=STUDY_UID,
        start_rule="Subject must attend follow-up visit",
        epoch="C99158_FOLLOW-UP",
        epoch_subtype="C99158_FOLLOW-UP",
        order=4,
        duration=183,
        color_hash="#009688FF",
        uid="StudyEpoch_000003",
        epoch_name="Follow-up",
        epoch_ctterm={
            "term_uid": "C99158_FOLLOW-UP",
            "sponsor_preferred_name": "Follow-up",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_subtype_name="Follow-up",
        epoch_subtype_ctterm={
            "term_uid": "C99158_FOLLOW-UP",
            "sponsor_preferred_name": "Follow-up",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_type="CTTerm_000003",
        epoch_type_name="Follow-up epoch type name",
        epoch_type_ctterm={
            "term_uid": "CTTerm_000003",
            "sponsor_preferred_name": "Follow-up epoch type name",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        start_day=183,
        end_day=366,
        start_date="2022-08-26 02:06:50",
        status="DRAFT",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        change_description="Initial Version",
        change_type="add",
        study_visit_count=1,
    ),
    StudyEpoch(
        study_uid=STUDY_UID,
        epoch="CTTerm_000008",
        epoch_subtype="CTTerm_000008",
        order=5,
        description="Hula lula",
        duration=7,
        color_hash="#C5CAE9FF",
        uid="StudyEpoch_000034",
        epoch_name="Elimination",
        epoch_ctterm={
            "term_uid": "CTTerm_000008",
            "sponsor_preferred_name": "Elimination",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_subtype_name="Elimination",
        epoch_subtype_ctterm={
            "term_uid": "CTTerm_000008",
            "sponsor_preferred_name": "Elimination",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_type="CTTerm_000003",
        epoch_type_name="Elimination epoch type name",
        epoch_type_ctterm={
            "term_uid": "CTTerm_000003",
            "sponsor_preferred_name": "Elimination epoch type name",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        start_day=366,
        end_day=373,
        start_date="2022-08-26 02:06:50",
        status="DRAFT",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        change_description="Initial Version",
        change_type="add",
        study_visit_count=1,
    ),
    StudyEpoch(
        study_uid=STUDY_UID,
        epoch="CTTerm_000005",
        epoch_subtype="CTTerm_000005",
        order=6,
        duration=0,
        color_hash="#80CBC4FF",
        uid="StudyEpoch_000041",
        epoch_name="Dose Escalation",
        epoch_ctterm={
            "term_uid": "CTTerm_000005",
            "sponsor_preferred_name": "Dose Escalation",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_subtype_name="Dose Escalation",
        epoch_subtype_ctterm={
            "term_uid": "CTTerm_000005",
            "sponsor_preferred_name": "Dose Escalation",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_type="C101526_TREATMENT",
        epoch_type_name="Treatment",
        epoch_type_ctterm={
            "term_uid": "C101526_TREATMENT",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        start_date="2022-08-26 02:06:50",
        status="DRAFT",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock", "reorder"],
        change_description="Initial Version",
        change_type="add",
        study_visit_count=0,
    ),
)

STUDY_ELEMENTS = OrderedDict(
    (
        (
            "StudyElement_000018",
            StudySelectionElement(
                study_uid=STUDY_UID,
                order=1,
                start_rule=None,
                end_rule=None,
                description=None,
                element_uid="StudyElement_000018",
                name="Screening",
                short_name="Screening",
                code="CTTerm_000130",
                planned_duration=None,
                element_colour=None,
                element_type=None,
                element_subtype=CTTermName(
                    term_uid="CTTerm_000135",
                    codelist_uid="CTCodelist_000024",
                    sponsor_preferred_name="Screening",
                    sponsor_preferred_name_sentence_case="screening",
                    order=1,
                    start_date=datetime.datetime(2022, 7, 14, 11, 18, 43, 459307),
                ),
                study_compound_dosing_count=0,
                start_date=datetime.datetime(2022, 7, 22, 9, 57, 9, 373874),
                author_username=AUTHOR_USERNAME,
            ),
        ),
        (
            "StudyElement_000020",
            StudySelectionElement(
                study_uid=STUDY_UID,
                order=2,
                start_rule=None,
                end_rule=None,
                description=None,
                element_uid="StudyElement_000020",
                name="NPH insulin",
                short_name="NPH insulin",
                code="CTTerm_000129",
                planned_duration=None,
                element_colour=None,
                element_type=None,
                element_subtype=CTTermName(
                    term_uid="CTTerm_000131",
                    codelist_uid="CTCodelist_000024",
                    sponsor_preferred_name="Treatment",
                    sponsor_preferred_name_sentence_case="treatment",
                    order=3,
                    start_date=datetime.datetime(2022, 7, 14, 11, 18, 42, 889737),
                ),
                study_compound_dosing_count=0,
                start_date=datetime.datetime(2022, 7, 22, 9, 57, 10, 406127),
                author_username=AUTHOR_USERNAME,
            ),
        ),
        (
            "StudyElement_000022",
            StudySelectionElement(
                study_uid=STUDY_UID,
                order=3,
                start_rule=None,
                end_rule=None,
                description=None,
                element_uid="StudyElement_000022",
                name="Metformin",
                short_name="Metformin",
                code="CTTerm_000129",
                planned_duration=None,
                element_colour=None,
                element_type=None,
                element_subtype=CTTermName(
                    term_uid="CTTerm_000131",
                    codelist_uid="CTCodelist_000024",
                    sponsor_preferred_name="Treatment",
                    sponsor_preferred_name_sentence_case="treatment",
                    order=3,
                    start_date=datetime.datetime(2022, 7, 14, 11, 18, 42, 889737),
                ),
                study_compound_dosing_count=0,
                start_date=datetime.datetime(2022, 7, 22, 9, 57, 10, 503358),
                author_username=AUTHOR_USERNAME,
            ),
        ),
        (
            "StudyElement_000024",
            StudySelectionElement(
                study_uid=STUDY_UID,
                order=4,
                start_rule=None,
                end_rule=None,
                description=None,
                element_uid="StudyElement_000024",
                name="Follow-up",
                short_name="Follow-up",
                code="CTTerm_000130",
                planned_duration=None,
                element_colour=None,
                element_type=None,
                element_subtype=CTTermName(
                    term_uid="CTTerm_000134",
                    codelist_uid="CTCodelist_000024",
                    sponsor_preferred_name="Follow-up",
                    sponsor_preferred_name_sentence_case="follow-up",
                    order=5,
                    start_date=datetime.datetime(2022, 7, 14, 11, 18, 43, 264949),
                ),
                study_compound_dosing_count=0,
                start_date=datetime.datetime(2022, 7, 22, 9, 57, 10, 985130),
                author_username=AUTHOR_USERNAME,
            ),
        ),
    )
)

STUDY_DESIGN_CELLS = (
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000011",
        study_arm_uid="StudyArm_000009",
        study_arm_name="NPH insulin",
        study_epoch_uid="StudyEpoch_000001",
        study_epoch_name="Screening",
        study_element_uid="StudyElement_000018",
        study_element_name="Screening",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 16, 9, 37, 25, 904287),
        author_username=AUTHOR_USERNAME,
        order=1,
    ),
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000012",
        study_arm_uid="StudyArm_000009",
        study_arm_name="NPH insulin",
        study_epoch_uid="StudyEpoch_000002",
        study_epoch_name="Treatment",
        study_element_uid="StudyElement_000020",
        study_element_name="NPH insulin",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 16, 9, 37, 25, 749029),
        author_username=AUTHOR_USERNAME,
        order=2,
    ),
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000013",
        study_arm_uid="StudyArm_000009",
        study_arm_name="NPH insulin",
        study_epoch_uid="StudyEpoch_000003",
        study_epoch_name="Follow-up",
        study_element_uid="StudyElement_000024",
        study_element_name="Follow-up",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 16, 9, 37, 25, 583916),
        author_username=AUTHOR_USERNAME,
        order=3,
    ),
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000014",
        study_arm_uid="StudyArm_000009",
        study_arm_name="NPH insulin",
        study_epoch_uid="StudyEpoch_000034",
        study_epoch_name="Elimination",
        study_element_uid="StudyElement_000020",
        study_element_name="NPH insulin",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 16, 9, 37, 25, 309418),
        author_username=AUTHOR_USERNAME,
        order=4,
    ),
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000015",
        study_arm_uid="StudyArm_000011",
        study_arm_name="Metformin",
        study_epoch_uid="StudyEpoch_000001",
        study_epoch_name="Screening",
        study_element_uid="StudyElement_000018",
        study_element_name="Screening",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 16, 9, 35, 11, 107228),
        author_username=AUTHOR_USERNAME,
        order=5,
    ),
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000016",
        study_arm_uid="StudyArm_000011",
        study_arm_name="Metformin",
        study_epoch_uid="StudyEpoch_000002",
        study_epoch_name="Treatment",
        study_element_uid="StudyElement_000022",
        study_element_name="Metformin",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 16, 9, 35, 12, 69303),
        author_username=AUTHOR_USERNAME,
        order=6,
    ),
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000017",
        study_arm_uid="StudyArm_000011",
        study_arm_name="Metformin",
        study_epoch_uid="StudyEpoch_000003",
        study_epoch_name="Follow-up",
        study_element_uid="StudyElement_000024",
        study_element_name="Follow-up",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 16, 9, 35, 12, 323734),
        author_username=AUTHOR_USERNAME,
        order=7,
    ),
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000018",
        study_arm_uid="StudyArm_000011",
        study_arm_name="Metformin",
        study_epoch_uid="StudyEpoch_000034",
        study_epoch_name="Elimination",
        study_element_uid="StudyElement_000022",
        study_element_name="Metformin",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 16, 9, 35, 12, 591836),
        author_username=AUTHOR_USERNAME,
        order=8,
    ),
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000039",
        study_arm_uid="StudyArm_000045",
        study_arm_name="Another arm",
        study_epoch_uid="StudyEpoch_000002",
        study_epoch_name="Treatment",
        study_element_uid="StudyElement_000020",
        study_element_name="NPH insulin",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 25, 22, 54, 8, 133786),
        author_username=AUTHOR_USERNAME,
        order=9,
    ),
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000042",
        study_arm_uid="StudyArm_000045",
        study_arm_name="Another arm",
        study_epoch_uid="StudyEpoch_000003",
        study_epoch_name="Follow-up",
        study_element_uid="StudyElement_000020",
        study_element_name="NPH insulin",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 26, 2, 7, 34, 231184),
        author_username=AUTHOR_USERNAME,
        order=10,
    ),
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000044",
        study_arm_uid="StudyArm_000009",
        study_arm_name="NPH insulin",
        study_epoch_uid="StudyEpoch_000042",
        study_epoch_name="Extension",
        study_element_uid="StudyElement_000020",
        study_element_name="NPH insulin",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 26, 2, 7, 34, 318480),
        author_username=AUTHOR_USERNAME,
        order=11,
    ),
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000045",
        study_arm_uid="StudyArm_000011",
        study_arm_name="Metformin",
        study_epoch_uid="StudyEpoch_000042",
        study_epoch_name="Extension",
        study_element_uid="StudyElement_000022",
        study_element_name="Metformin",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 26, 2, 8, 31, 590352),
        author_username=AUTHOR_USERNAME,
        order=12,
    ),
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000046",
        study_arm_uid="StudyArm_000045",
        study_arm_name="Another arm",
        study_epoch_uid="StudyEpoch_000042",
        study_epoch_name="Extension",
        study_element_uid="StudyElement_000022",
        study_element_name="Metformin",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 26, 2, 8, 31, 765647),
        author_username=AUTHOR_USERNAME,
        order=13,
    ),
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000047",
        study_arm_uid="StudyArm_000009",
        study_arm_name="NPH insulin",
        study_epoch_uid="StudyEpoch_000042",
        study_epoch_name="Extension",
        study_element_uid="StudyElement_000020",
        study_element_name="NPH insulin",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 26, 2, 7, 59, 750359),
        author_username=AUTHOR_USERNAME,
        order=14,
    ),
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000048",
        study_arm_uid="StudyArm_000011",
        study_arm_name="Metformin",
        study_epoch_uid="StudyEpoch_000042",
        study_epoch_name="Extension",
        study_element_uid="StudyElement_000020",
        study_element_name="NPH insulin",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 26, 2, 8, 0, 315389),
        author_username=AUTHOR_USERNAME,
        order=15,
    ),
    StudyDesignCell(
        study_uid=STUDY_UID,
        design_cell_uid="StudyDesignCell_000049",
        study_arm_uid="StudyArm_000045",
        study_arm_name="Another arm",
        study_epoch_uid="StudyEpoch_000042",
        study_epoch_name="Extension",
        study_element_uid="StudyElement_000020",
        study_element_name="NPH insulin",
        transition_rule=None,
        start_date=datetime.datetime(2022, 8, 26, 2, 8, 0, 807474),
        author_username=AUTHOR_USERNAME,
        order=16,
    ),
)

STUDY_VISITS = (
    StudyVisit(
        study_epoch_uid="StudyEpoch_000001",
        visit_type_uid="CTTerm_000171",
        time_reference_uid="CTTerm_000117",
        time_value=-2,
        time_unit_uid="UnitDefinition_000171",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000151",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000080",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=True,
        uid="StudyVisit_000021",
        study_uid="Study_000001",
        study_epoch_name="Screening",
        study_epoch={
            "term_uid": "C48262_SCREENING",
            "sponsor_preferred_name": "Screening",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="C48262_SCREENING",
        order=1,
        visit_type_name="Screening",
        visit_type={
            "term_uid": "CTTerm_000171",
            "sponsor_preferred_name": "Screening",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global Anchor Visit",
        time_unit_name="weeks",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000080",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=-1209600.0,
        duration_time_unit="UnitDefinition_000171",
        study_day_number=-14,
        study_duration_days_label="-15 days",
        study_day_label="Day -14",
        study_week_number=-2,
        study_duration_weeks_label="-3 weeks",
        week_in_study_label="Week -3",
        study_week_label="Week -2",
        visit_number=1,
        visit_subnumber=0,
        unique_visit_number=100,
        visit_subname="Visit 1",
        visit_name="Visit 1",
        visit_short_name="V1",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date="2022-08-24 11:52:48",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=0,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000002",
        visit_type_uid="CTTerm_000176",
        time_reference_uid="CTTerm_000117",
        time_value=0,
        time_unit_uid="UnitDefinition_000151",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000151",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000080",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=True,
        is_soa_milestone=True,
        uid="StudyVisit_000022",
        study_uid="Study_000001",
        study_epoch_name="Treatment",
        study_epoch={
            "term_uid": "C101526_TREATMENT",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="C101526_TREATMENT",
        order=2,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000176",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global Anchor Visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000080",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=0.0,
        duration_time_unit="UnitDefinition_000151",
        study_day_number=1,
        study_duration_days_label="0 days",
        study_day_label="Day 1",
        study_week_number=1,
        study_duration_weeks_label="0 weeks",
        week_in_study_label="Week 0",
        study_week_label="Week 1",
        visit_number=2,
        visit_subnumber=0,
        unique_visit_number=200,
        visit_subname="Visit 2",
        visit_name="Visit 2",
        visit_short_name="V2",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date="2022-08-24 11:52:49",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=0,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000002",
        visit_type_uid="CTTerm_000176",
        time_reference_uid="CTTerm_000117",
        time_value=7,
        time_unit_uid="UnitDefinition_000151",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000151",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000080",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=True,
        uid="StudyVisit_000023",
        study_uid="Study_000001",
        study_epoch_name="Treatment",
        study_epoch={
            "term_uid": "C101526_TREATMENT",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="C101526_TREATMENT",
        order=3,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000176",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global Anchor Visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000080",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=604800.0,
        duration_time_unit="UnitDefinition_000151",
        study_day_number=8,
        study_duration_days_label="7 days",
        study_day_label="Day 8",
        study_week_number=2,
        study_duration_weeks_label="1 weeks",
        week_in_study_label="Week 1",
        study_week_label="Week 2",
        visit_number=3,
        visit_subnumber=0,
        unique_visit_number=300,
        visit_subname="Visit 3",
        visit_name="Visit 3",
        visit_short_name="V3",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date="2022-08-24 11:52:49",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=0,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000002",
        visit_type_uid="CTTerm_000176",
        time_reference_uid="CTTerm_000117",
        time_value=14,
        time_unit_uid="UnitDefinition_000151",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000151",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000080",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000024",
        study_uid="Study_000001",
        study_epoch_name="Treatment",
        study_epoch={
            "term_uid": "C101526_TREATMENT",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="C101526_TREATMENT",
        order=4,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000176",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global Anchor Visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000080",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=1209600.0,
        duration_time_unit="UnitDefinition_000151",
        study_day_number=15,
        study_duration_days_label="14 days",
        study_day_label="Day 15",
        study_week_number=3,
        study_duration_weeks_label="2 weeks",
        week_in_study_label="Week 2",
        study_week_label="Week 3",
        visit_number=4,
        visit_subnumber=0,
        unique_visit_number=400,
        visit_subname="Visit 4",
        visit_name="Visit 4",
        visit_short_name="V4",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date="2022-08-24 11:52:49",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=0,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000002",
        visit_type_uid="CTTerm_000176",
        time_reference_uid="CTTerm_000117",
        time_value=21,
        time_unit_uid="UnitDefinition_000151",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000151",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000080",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000025",
        study_uid="Study_000001",
        study_epoch_name="Treatment",
        study_epoch={
            "term_uid": "C101526_TREATMENT",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="C101526_TREATMENT",
        order=5,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000176",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global Anchor Visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000080",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=1814400.0,
        duration_time_unit="UnitDefinition_000151",
        study_day_number=22,
        study_duration_days_label="21 days",
        study_day_label="Day 22",
        study_week_number=4,
        study_duration_weeks_label="3 weeks",
        week_in_study_label="Week 3",
        study_week_label="Week 4",
        visit_number=5,
        visit_subnumber=0,
        unique_visit_number=500,
        visit_subname="Visit 5",
        visit_name="Visit 5",
        visit_short_name="V5",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date="2022-08-24 11:52:50",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=0,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000002",
        visit_type_uid="CTTerm_000176",
        time_reference_uid="CTTerm_000117",
        time_value=28,
        time_unit_uid="UnitDefinition_000151",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000151",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000080",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000026",
        study_uid="Study_000001",
        study_epoch_name="Treatment",
        study_epoch={
            "term_uid": "C101526_TREATMENT",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="C101526_TREATMENT",
        order=6,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000176",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global Anchor Visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000080",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=2419200.0,
        duration_time_unit="UnitDefinition_000151",
        study_day_number=29,
        study_duration_days_label="28 days",
        study_day_label="Day 29",
        study_week_number=5,
        study_duration_weeks_label="4 weeks",
        week_in_study_label="Week 4",
        study_week_label="Week 5",
        visit_number=6,
        visit_subnumber=0,
        unique_visit_number=600,
        visit_subname="Visit 6",
        visit_name="Visit 6",
        visit_short_name="V6",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date="2022-08-24 11:52:50",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=0,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000002",
        visit_type_uid="CTTerm_000176",
        time_reference_uid="CTTerm_000117",
        time_value=35,
        time_unit_uid="UnitDefinition_000151",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000151",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000080",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000027",
        study_uid="Study_000001",
        study_epoch_name="Treatment",
        study_epoch={
            "term_uid": "C101526_TREATMENT",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="C101526_TREATMENT",
        order=7,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000176",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global Anchor Visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000080",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=3024000.0,
        duration_time_unit="UnitDefinition_000151",
        study_day_number=36,
        study_duration_days_label="35 days",
        study_day_label="Day 36",
        study_week_number=6,
        study_duration_weeks_label="5 weeks",
        week_in_study_label="Week 5",
        study_week_label="Week 6",
        visit_number=7,
        visit_subnumber=0,
        unique_visit_number=700,
        visit_subname="Visit 7",
        visit_name="Visit 7",
        visit_short_name="V7",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date="2022-08-24 11:52:50",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=0,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000002",
        visit_type_uid="CTTerm_000176",
        time_reference_uid="CTTerm_000117",
        time_value=42,
        time_unit_uid="UnitDefinition_000151",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000151",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000080",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000028",
        study_uid="Study_000001",
        study_epoch_name="Treatment",
        study_epoch={
            "term_uid": "C101526_TREATMENT",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="C101526_TREATMENT",
        order=8,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000176",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global Anchor Visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000080",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=3628800.0,
        duration_time_unit="UnitDefinition_000151",
        study_day_number=43,
        study_duration_days_label="42 days",
        study_day_label="Day 43",
        study_week_number=7,
        study_duration_weeks_label="6 weeks",
        week_in_study_label="Week 6",
        study_week_label="Week 7",
        visit_number=8,
        visit_subnumber=0,
        unique_visit_number=800,
        visit_subname="Visit 8",
        visit_name="Visit 8",
        visit_short_name="V8",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date="2022-08-24 11:52:50",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=0,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000002",
        visit_type_uid="CTTerm_000176",
        time_reference_uid="CTTerm_000117",
        time_value=49,
        time_unit_uid="UnitDefinition_000151",
        visit_sublabel_reference=None,
        consecutive_visit_group="TreatGroup",
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000151",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000080",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000029",
        study_uid="Study_000001",
        study_epoch_name="Treatment",
        study_epoch={
            "term_uid": "C101526_TREATMENT",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="C101526_TREATMENT",
        order=9,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000176",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global Anchor Visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000080",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=4233600.0,
        duration_time_unit="UnitDefinition_000151",
        study_day_number=50,
        study_duration_days_label="49 days",
        study_day_label="Day 50",
        study_week_number=8,
        study_duration_weeks_label="7 weeks",
        week_in_study_label="Week 7",
        study_week_label="Week 8",
        visit_number=9,
        visit_subnumber=0,
        unique_visit_number=900,
        visit_subname="Visit 9",
        visit_name="Visit 9",
        visit_short_name="V9",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date="2022-08-24 11:52:50",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=0,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000002",
        visit_type_uid="CTTerm_000176",
        time_reference_uid="CTTerm_000117",
        time_value=56,
        time_unit_uid="UnitDefinition_000151",
        visit_sublabel_reference=None,
        consecutive_visit_group="TreatGroup",
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000151",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000080",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000030",
        study_uid="Study_000001",
        study_epoch_name="Treatment",
        study_epoch={
            "term_uid": "C101526_TREATMENT",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="C101526_TREATMENT",
        order=10,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000176",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global Anchor Visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000080",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=4838400.0,
        duration_time_unit="UnitDefinition_000151",
        study_day_number=57,
        study_duration_days_label="56 days",
        study_day_label="Day 57",
        study_week_number=9,
        study_duration_weeks_label="8 weeks",
        week_in_study_label="Week 8",
        study_week_label="Week 9",
        visit_number=10,
        visit_subnumber=0,
        unique_visit_number=1000,
        visit_subname="Visit 10",
        visit_name="Visit 10",
        visit_short_name="V10",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date="2022-08-24 11:52:51",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=0,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000042",
        visit_type_uid="CTTerm_000176",
        time_reference_uid="CTTerm_000113",
        time_value=1,
        time_unit_uid="UnitDefinition_000166",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000151",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000080",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000044",
        study_uid="Study_000001",
        study_epoch_name="Extension",
        study_epoch={
            "term_uid": "CTTerm_000007",
            "sponsor_preferred_name": "Extension",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="CTTerm_000007",
        order=11,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000176",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Previous Visit",
        time_unit_name="week",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000080",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=5443200.0,
        duration_time_unit="UnitDefinition_000166",
        study_day_number=64,
        study_duration_days_label="7 days",
        study_day_label="Day 64",
        study_week_number=10,
        study_duration_weeks_label="1 weeks",
        week_in_study_label="Week 1",
        study_week_label="Week 10",
        visit_number=11,
        visit_subnumber=0,
        unique_visit_number=1100,
        visit_subname="Visit 11",
        visit_name="Visit 11",
        visit_short_name="V11",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date="2022-08-26 02:14:58",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=0,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000003",
        visit_type_uid="CTTerm_000161",
        time_reference_uid="CTTerm_000117",
        time_value=182,
        time_unit_uid="UnitDefinition_000151",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000151",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000080",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=True,
        uid="StudyVisit_000031",
        study_uid="Study_000001",
        study_epoch_name="Follow-up",
        study_epoch={
            "term_uid": "C99158_FOLLOW-UP",
            "sponsor_preferred_name": "Follow-up",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="C99158_FOLLOW-UP",
        order=12,
        visit_type_name="Follow-up",
        visit_type={
            "term_uid": "CTTerm_000161",
            "sponsor_preferred_name": "Follow-up",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global Anchor Visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000080",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=15724800.0,
        duration_time_unit="UnitDefinition_000151",
        study_day_number=183,
        study_duration_days_label="182 days",
        study_day_label="Day 183",
        study_week_number=27,
        study_duration_weeks_label="26 weeks",
        week_in_study_label="Week 26",
        study_week_label="Week 27",
        visit_number=12,
        visit_subnumber=0,
        unique_visit_number=1200,
        visit_subname="Visit 12",
        visit_name="Visit 12",
        visit_short_name="V12",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date="2022-08-26 02:14:31",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=0,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000034",
        visit_type_uid="CTTerm_000164",
        time_reference_uid="CTTerm_000113",
        time_value=183,
        time_unit_uid="UnitDefinition_000151",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000151",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000079",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000045",
        study_uid="Study_000001",
        study_epoch_name="Elimination",
        study_epoch={
            "term_uid": "CTTerm_000008",
            "sponsor_preferred_name": "Elimination",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="CTTerm_000008",
        order=13,
        visit_type_name="Post treatment activity",
        visit_type={
            "term_uid": "CTTerm_000164",
            "sponsor_preferred_name": "Post treatment activity",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Previous Visit",
        time_unit_name="days",
        visit_contact_mode_name="Phone Contact",
        visit_contact_mode={
            "term_uid": "CTTerm_000079",
            "sponsor_preferred_name": "Phone Contact",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=31536000.0,
        duration_time_unit="UnitDefinition_000151",
        study_day_number=366,
        study_duration_days_label="183 days",
        study_day_label="Day 366",
        study_week_number=53,
        study_duration_weeks_label="26 weeks",
        week_in_study_label="Week 26",
        study_week_label="Week 53",
        visit_number=13,
        visit_subnumber=0,
        unique_visit_number=1300,
        visit_subname="Visit 13",
        visit_name="Visit 13",
        visit_short_name="P13",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date="2022-09-01 09:39:57",
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=0,
    ),
)

MATRIX = [
    [
        {},
        {
            "klass": "epoch",
            "id": "StudyEpoch_000001",
            "text": "Screening",
            "colors": ("#a5d6a7", "#204621", "#000"),
            "margin": 10,
            "paddings": (3, 3),
        },
        {
            "klass": "epoch",
            "id": "StudyEpoch_000002",
            "text": "Treatment",
            "colors": ("#2e7d32", "#1b4b1e", "#fff"),
            "margin": 10,
            "paddings": (3, 3),
        },
        {
            "klass": "epoch",
            "id": "StudyEpoch_000042",
            "text": "Extension",
            "colors": ("#80deea", "#0e4f58", "#000"),
            "margin": 10,
            "paddings": (3, 3),
        },
        {
            "klass": "epoch",
            "id": "StudyEpoch_000003",
            "text": "Follow-up",
            "colors": ("#009688", "#00665c", "#fff"),
            "margin": 10,
            "paddings": (3, 3),
        },
        {
            "klass": "epoch",
            "id": "StudyEpoch_000034",
            "text": "Elimination",
            "colors": ("#c5cae9", "#1c224a", "#000"),
            "margin": 10,
            "paddings": (3, 3),
        },
        {
            "klass": "epoch",
            "id": "StudyEpoch_000041",
            "text": "Dose Escalation",
            "colors": ("#80cbc4", "#1e4844", "#000"),
            "margin": 10,
            "paddings": (3, 3),
        },
    ],
    [
        {
            "klass": "arm",
            "id": "StudyArm_000009",
            "text": "NPH insulin",
            "colors": ("#fffde7", "#665d00", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000018",
            "text": "Screening",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000020",
            "text": "NPH insulin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000020",
            "text": "NPH insulin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000024",
            "text": "Follow-up",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000020",
            "text": "NPH insulin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {},
    ],
    [
        {
            "klass": "arm",
            "id": "StudyArm_000011",
            "text": "Metformin is longer",
            "colors": ("#ffebee", "#66000f", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000018",
            "text": "Screening",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000022",
            "text": "Metformin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000020",
            "text": "NPH insulin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000024",
            "text": "Follow-up",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000022",
            "text": "Metformin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {},
    ],
    [
        {
            "klass": "arm",
            "id": "StudyArm_000045",
            "text": "Another arm",
            "colors": ("#f3e5f5", "#441c4a", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {},
        {
            "klass": "element",
            "id": "StudyElement_000020",
            "text": "NPH insulin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000020",
            "text": "NPH insulin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000020",
            "text": "NPH insulin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {},
        {},
    ],
    [
        {
            "klass": "arm",
            "id": "StudyArm_000048",
            "text": "More arms",
            "colors": ("#e8eaf6", "#1d2349", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {},
        {},
        {},
        {},
        {},
        {},
    ],
]

VISIT_IDS = {
    "StudyVisit_000021",
    "StudyVisit_000022",
    "StudyVisit_000044",
    "StudyVisit_000031",
    "StudyVisit_000045",
}

TIMELINE = {
    "labels": [
        [
            {
                "id": "CTTerm_000171",
                "klass": "visit-type",
                "paddings": (0, 0),
                "text": "Screening",
                "width": 114,
                "x": 175,
                "y": 227,
                "height": 20,
                "lines": ((25, 16, "Screening"),),
            },
            {
                "id": "CTTerm_000176",
                "klass": "visit-type",
                "paddings": (0, 0),
                "text": "Treatment",
                "width": 270,
                "x": 299,
                "y": 227,
                "height": 20,
                "lines": ((102, 16, "Treatment"),),
            },
            {
                "id": "CTTerm_000161",
                "klass": "visit-type",
                "paddings": (0, 0),
                "text": "Follow-up",
                "width": 130,
                "x": 579,
                "y": 227,
                "height": 20,
                "lines": ((31, 16, "Follow-up"),),
            },
            {
                "id": "CTTerm_000164",
                "klass": "visit-type",
                "paddings": (0, 0),
                "text": "Post treatment activity",
                "width": 130,
                "x": 719,
                "y": 218,
                "height": 39,
                "lines": ((18, 16, "Post treatment"), (41, 35, "activity")),
            },
        ],
        [
            {
                "id": "StudyVisit_000021",
                "klass": "visit-timing",
                "paddings": (0, 0),
                "text": "Week -2",
                "x": 175,
                "y": 279,
                "width": 53,
                "height": 15,
                "lines": ((0, 16, "Week -2"),),
            },
            {
                "id": "StudyVisit_000022",
                "klass": "visit-timing",
                "paddings": (0, 0),
                "text": "Week 1",
                "x": 299,
                "y": 279,
                "width": 48,
                "height": 15,
                "lines": ((0, 16, "Week 1"),),
            },
            {
                "id": "StudyVisit_000044",
                "klass": "visit-timing",
                "paddings": (0, 0),
                "text": "Week 10",
                "x": 439,
                "y": 279,
                "width": 56,
                "height": 15,
                "lines": ((0, 16, "Week 10"),),
            },
            {
                "id": "StudyVisit_000031",
                "klass": "visit-timing",
                "paddings": (0, 0),
                "text": "Week 27",
                "x": 579,
                "y": 279,
                "width": 56,
                "height": 15,
                "lines": ((0, 16, "Week 27"),),
            },
            {
                "id": "StudyVisit_000045",
                "klass": "visit-timing",
                "paddings": (0, 0),
                "text": "Week 53",
                "x": 719,
                "y": 279,
                "width": 56,
                "height": 15,
                "lines": ((0, 16, "Week 53"),),
            },
        ],
        [
            {
                "height": 15,
                "id": "StudyVisit_000021",
                "klass": "visit-timing",
                "lines": ((0, 16, "V1"),),
                "paddings": (0, 0),
                "text": "V1",
                "width": 20,
                "x": 175,
                "y": 297,
            },
            {
                "height": 15,
                "id": "StudyVisit_000022",
                "klass": "visit-timing",
                "lines": ((0, 16, "V2"),),
                "paddings": (0, 0),
                "text": "V2",
                "width": 20,
                "x": 299,
                "y": 297,
            },
            {
                "height": 15,
                "id": "StudyVisit_000044",
                "klass": "visit-timing",
                "lines": ((0, 16, "V11"),),
                "paddings": (0, 0),
                "text": "V11",
                "width": 27,
                "x": 439,
                "y": 297,
            },
            {
                "height": 15,
                "id": "StudyVisit_000031",
                "klass": "visit-timing",
                "lines": ((0, 16, "V12"),),
                "paddings": (0, 0),
                "text": "V12",
                "width": 28,
                "x": 579,
                "y": 297,
            },
            {
                "height": 15,
                "id": "StudyVisit_000045",
                "klass": "visit-timing",
                "lines": ((0, 16, "P13"),),
                "paddings": (0, 0),
                "text": "P13",
                "width": 25,
                "x": 719,
                "y": 297,
            },
        ],
        [
            {
                "height": 18,
                "id": "StudyVisit_000021",
                "klass": "visit-timing",
                "lines": ((0, 16, "Screening"),),
                "paddings": (0, 0),
                "text": "Screening",
                "vertical": True,
                "width": 64,
                "x": 175,
                "y": 321,
            },
            {
                "height": 15,
                "id": "StudyVisit_000022",
                "klass": "visit-timing",
                "lines": ((0, 16, "Treatment"),),
                "paddings": (0, 0),
                "text": "Treatment",
                "vertical": True,
                "width": 66,
                "x": 299,
                "y": 321,
            },
            {
                "height": 18,
                "id": "StudyVisit_000031",
                "klass": "visit-timing",
                "lines": ((0, 16, "Follow-up"),),
                "paddings": (0, 0),
                "text": "Follow-up",
                "vertical": True,
                "width": 67,
                "x": 579,
                "y": 321,
            },
        ],
    ],
    "arrows": [
        {"klass": "timeline-arrow", "x1": 175, "x2": 299, "y1": 262, "y2": 262},
        {"klass": "timeline-arrow", "x1": 299, "x2": 579, "y1": 262, "y2": 262},
        {"klass": "timeline-arrow", "x1": 579, "x2": 719, "y1": 262, "y2": 262},
        {"klass": "timeline-arrow", "x1": 719, "x2": 859, "y1": 262, "y2": 262},
        {"klass": "visit-arrow", "x1": 175, "x2": 175, "y1": 276, "y2": 264},
        {"klass": "visit-arrow", "x1": 299, "x2": 299, "y1": 276, "y2": 264},
        {"klass": "visit-arrow", "x1": 439, "x2": 439, "y1": 276, "y2": 264},
        {"klass": "visit-arrow", "x1": 579, "x2": 579, "y1": 276, "y2": 264},
        {"klass": "visit-arrow", "x1": 719, "x2": 719, "y1": 276, "y2": 264},
    ],
}

SOA_PREFERENCES = StudySoaPreferences(
    study_uid=STUDY_UID,
    show_epochs=True,
    show_milestones=True,
    baseline_as_time_zero=False,
)

SVG_DOCUMENT = """
<svg version="1.1" xmlns="http://www.w3.org/2000/svg" width="1009" height="393">
  <defs>
    <marker id="arrowhead1" viewBox="0 0 6 6" refX="6" refY="3" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 6 3 L 0 6 z" />
    </marker>
    <marker id="arrowhead2" viewBox="0 0 6 6" refX="3" refY="0" markerWidth="6" markerHeight="6" orient="0">
      <path d="M 0 6 L 3 0 L 6 6 z" />
    </marker>
    <marker id="arrowtail1" viewBox="0 0 6 6" refX="3" refY="3" markerWidth="6" markerHeight="6" orient="auto">
      <polyline points="3 0, 3 6" />
    </marker>
  </defs>
  <g id="StudyArm_000009" class="arm" transform="translate(5, 36)">
    <rect x="0" y="0" width="999" height="40" rx="5" ry="5" />
    <text>
      <tspan x="5" y="21">NPH insulin</tspan>
    </text>
  </g>
  <g id="StudyArm_000011" class="arm" transform="translate(5, 81)">
    <rect x="0" y="0" width="999" height="40" rx="5" ry="5" />
    <text>
      <tspan x="5" y="21">Metformin is longer</tspan>
    </text>
  </g>
  <g id="StudyArm_000045" class="arm" transform="translate(5, 126)">
    <rect x="0" y="0" width="999" height="40" rx="5" ry="5" />
    <text>
      <tspan x="5" y="21">Another arm</tspan>
    </text>
  </g>
  <g id="StudyArm_000048" class="arm" transform="translate(5, 171)">
    <rect x="0" y="0" width="999" height="30" rx="5" ry="5" />
    <text>
      <tspan x="5" y="21">More arms</tspan>
    </text>
  </g>
  <g id="StudyEpoch_000001" class="epoch" transform="translate(175, 5)">
    <rect x="0" y="0" width="114" height="201" rx="5" ry="5" />
    <text>
      <tspan x="25" y="19">Screening</tspan>
    </text>
  </g>
  <g id="StudyEpoch_000002" class="epoch" transform="translate(299, 5)">
    <rect x="0" y="0" width="130" height="201" rx="5" ry="5" />
    <text>
      <tspan x="32" y="19">Treatment</tspan>
    </text>
  </g>
  <g id="StudyEpoch_000042" class="epoch" transform="translate(439, 5)">
    <rect x="0" y="0" width="130" height="201" rx="5" ry="5" />
    <text>
      <tspan x="33" y="19">Extension</tspan>
    </text>
  </g>
  <g id="StudyEpoch_000003" class="epoch" transform="translate(579, 5)">
    <rect x="0" y="0" width="130" height="201" rx="5" ry="5" />
    <text>
      <tspan x="31" y="19">Follow-up</tspan>
    </text>
  </g>
  <g id="StudyEpoch_000034" class="epoch" transform="translate(719, 5)">
    <rect x="0" y="0" width="130" height="201" rx="5" ry="5" />
    <text>
      <tspan x="27" y="19">Elimination</tspan>
    </text>
  </g>
  <g id="StudyEpoch_000041" class="epoch" transform="translate(859, 5)">
    <rect x="0" y="0" width="140" height="201" rx="5" ry="5" />
    <text>
      <tspan x="18" y="19">Dose Escalation</tspan>
    </text>
  </g>
  <g id="StudyElement_000018" class="element" transform="translate(180, 41)">
    <rect x="0" y="0" width="104" height="75" rx="5" ry="5" />
    <text>
      <tspan x="5" y="21">Screening</tspan>
    </text>
  </g>
  <g id="StudyElement_000020" class="element" transform="translate(304, 41)">
    <rect x="0" y="0" width="120" height="30" rx="5" ry="5" />
    <text>
      <tspan x="5" y="21">NPH insulin</tspan>
    </text>
  </g>
  <g id="StudyElement_000020" class="element" transform="translate(444, 41)">
    <rect x="0" y="0" width="120" height="120" rx="5" ry="5" />
    <text>
      <tspan x="5" y="21">NPH insulin</tspan>
    </text>
  </g>
  <g id="StudyElement_000024" class="element" transform="translate(584, 41)">
    <rect x="0" y="0" width="120" height="75" rx="5" ry="5" />
    <text>
      <tspan x="5" y="21">Follow-up</tspan>
    </text>
  </g>
  <g id="StudyElement_000020" class="element" transform="translate(724, 41)">
    <rect x="0" y="0" width="120" height="30" rx="5" ry="5" />
    <text>
      <tspan x="5" y="21">NPH insulin</tspan>
    </text>
  </g>
  <g id="StudyElement_000022" class="element" transform="translate(304, 86)">
    <rect x="0" y="0" width="120" height="30" rx="5" ry="5" />
    <text>
      <tspan x="5" y="21">Metformin</tspan>
    </text>
  </g>
  <g id="StudyElement_000022" class="element" transform="translate(724, 86)">
    <rect x="0" y="0" width="120" height="30" rx="5" ry="5" />
    <text>
      <tspan x="5" y="21">Metformin</tspan>
    </text>
  </g>
  <g id="StudyElement_000020" class="element" transform="translate(304, 131)">
    <rect x="0" y="0" width="120" height="30" rx="5" ry="5" />
    <text>
      <tspan x="5" y="21">NPH insulin</tspan>
    </text>
  </g>
  <g id="StudyElement_000020" class="element" transform="translate(584, 131)">
    <rect x="0" y="0" width="120" height="30" rx="5" ry="5" />
    <text>
      <tspan x="5" y="21">NPH insulin</tspan>
    </text>
  </g>
  <g id="CTTerm_000171" class="visit-type" transform="translate(175, 227)">
    <text>
      <tspan x="25" y="16">Screening</tspan>
    </text>
  </g>
  <g id="CTTerm_000176" class="visit-type" transform="translate(299, 227)">
    <text>
      <tspan x="102" y="16">Treatment</tspan>
    </text>
  </g>
  <g id="CTTerm_000161" class="visit-type" transform="translate(579, 227)">
    <text>
      <tspan x="31" y="16">Follow-up</tspan>
    </text>
  </g>
  <g id="CTTerm_000164" class="visit-type" transform="translate(719, 218)">
    <text>
      <tspan x="18" y="16">Post treatment</tspan>
      <tspan x="41" y="35">activity</tspan>
    </text>
  </g>
  <g id="StudyVisit_000021" class="visit-timing" transform="translate(175, 279)">
    <text>
      <tspan x="0" y="16">Week -2</tspan>
    </text>
  </g>
  <g id="StudyVisit_000022" class="visit-timing" transform="translate(299, 279)">
    <text>
      <tspan x="0" y="16">Week 1</tspan>
    </text>
  </g>
  <g id="StudyVisit_000044" class="visit-timing" transform="translate(439, 279)">
    <text>
      <tspan x="0" y="16">Week 10</tspan>
    </text>
  </g>
  <g id="StudyVisit_000031" class="visit-timing" transform="translate(579, 279)">
    <text>
      <tspan x="0" y="16">Week 27</tspan>
    </text>
  </g>
  <g id="StudyVisit_000045" class="visit-timing" transform="translate(719, 279)">
    <text>
      <tspan x="0" y="16">Week 53</tspan>
    </text>
  </g>
  <g id="StudyVisit_000021" class="visit-timing" transform="translate(175, 297)">
    <text>
      <tspan x="0" y="16">V1</tspan>
    </text>
  </g>
  <g id="StudyVisit_000022" class="visit-timing" transform="translate(299, 297)">
    <text>
      <tspan x="0" y="16">V2</tspan>
    </text>
  </g>
  <g id="StudyVisit_000044" class="visit-timing" transform="translate(439, 297)">
    <text>
      <tspan x="0" y="16">V11</tspan>
    </text>
  </g>
  <g id="StudyVisit_000031" class="visit-timing" transform="translate(579, 297)">
    <text>
      <tspan x="0" y="16">V12</tspan>
    </text>
  </g>
  <g id="StudyVisit_000045" class="visit-timing" transform="translate(719, 297)">
    <text>
      <tspan x="0" y="16">P13</tspan>
    </text>
  </g>
  <g id="StudyVisit_000021" class="visit-timing" transform="translate(175, 321)">
    <text transform="rotate(90) translate(0, -18)">
      <tspan x="0" y="16">Screening</tspan>
    </text>
  </g>
  <g id="StudyVisit_000022" class="visit-timing" transform="translate(299, 321)">
    <text transform="rotate(90) translate(0, -18)">
      <tspan x="0" y="16">Treatment</tspan>
    </text>
  </g>
  <g id="StudyVisit_000031" class="visit-timing" transform="translate(579, 321)">
    <text transform="rotate(90) translate(0, -18)">
      <tspan x="0" y="16">Follow-up</tspan>
    </text>
  </g>
  <line class="timeline-arrow" x1="175" x2="299" y1="262" y2="262" />
  <line class="timeline-arrow" x1="299" x2="579" y1="262" y2="262" />
  <line class="timeline-arrow" x1="579" x2="719" y1="262" y2="262" />
  <line class="timeline-arrow" x1="719" x2="859" y1="262" y2="262" />
  <line class="visit-arrow" x1="175" x2="175" y1="276" y2="264" />
  <line class="visit-arrow" x1="299" x2="299" y1="276" y2="264" />
  <line class="visit-arrow" x1="439" x2="439" y1="276" y2="264" />
  <line class="visit-arrow" x1="579" x2="579" y1="276" y2="264" />
  <line class="visit-arrow" x1="719" x2="719" y1="276" y2="264" />
  <style type="text/css">
    text {
      font-family: "Times New Roman";
      font-size: 12pt;
    }
    .arm rect {
      rx: 5px;
      ry: 5px;
      stroke-width: 2px;
    }
    .epoch rect {
      rx: 5px;
      ry: 5px;
      stroke-width: 2px;
    }
    .element rect {
      rx: 5px;
      ry: 5px;
      stroke-width: 1px;
    }
    .timeline-arrow {
      stroke: #AAA;
      stroke-width: 2px;
      marker-start: url(#arrowtail1);
      marker-end: url(#arrowhead1);
      stroke-dasharray: 6 2;
    }
    #arrowtail1 polyline {
      stroke: #AAA;
      stroke-width: 1px;
    }
    #arrowhead1 path {
      fill: #AAA;
    }
    #arrowhead2 path {
      fill: #000;
    }
    .visit-arrow {
      stroke: #000;
      stroke-width: 1px;
      marker-end: url(#arrowhead2);
    }
    #StudyArm_000009 rect {
      fill: #fffde7;
      stroke: #665d00;
    }
    #StudyArm_000009 text {
      fill: #000;
    }
    #StudyArm_000011 rect {
      fill: #ffebee;
      stroke: #66000f;
    }
    #StudyArm_000011 text {
      fill: #000;
    }
    #StudyArm_000045 rect {
      fill: #f3e5f5;
      stroke: #441c4a;
    }
    #StudyArm_000045 text {
      fill: #000;
    }
    #StudyArm_000048 rect {
      fill: #e8eaf6;
      stroke: #1d2349;
    }
    #StudyArm_000048 text {
      fill: #000;
    }
    #StudyEpoch_000001 rect {
      fill: #a5d6a7;
      stroke: #204621;
    }
    #StudyEpoch_000001 text {
      fill: #000;
    }
    #StudyEpoch_000002 rect {
      fill: #2e7d32;
      stroke: #1b4b1e;
    }
    #StudyEpoch_000002 text {
      fill: #fff;
    }
    #StudyEpoch_000042 rect {
      fill: #80deea;
      stroke: #0e4f58;
    }
    #StudyEpoch_000042 text {
      fill: #000;
    }
    #StudyEpoch_000003 rect {
      fill: #009688;
      stroke: #00665c;
    }
    #StudyEpoch_000003 text {
      fill: #fff;
    }
    #StudyEpoch_000034 rect {
      fill: #c5cae9;
      stroke: #1c224a;
    }
    #StudyEpoch_000034 text {
      fill: #000;
    }
    #StudyEpoch_000041 rect {
      fill: #80cbc4;
      stroke: #1e4844;
    }
    #StudyEpoch_000041 text {
      fill: #000;
    }
    #StudyElement_000018 rect {
      fill: #d2e4f3;
      stroke: #153651;
    }
    #StudyElement_000018 text {
      fill: #000;
    }
    #StudyElement_000020 rect {
      fill: #d2e4f3;
      stroke: #153651;
    }
    #StudyElement_000020 text {
      fill: #000;
    }
    #StudyElement_000024 rect {
      fill: #d2e4f3;
      stroke: #153651;
    }
    #StudyElement_000024 text {
      fill: #000;
    }
    #StudyElement_000022 rect {
      fill: #d2e4f3;
      stroke: #153651;
    }
    #StudyElement_000022 text {
      fill: #000;
    }
  </style>
</svg>
""".strip()


class MockStudyDesignFigureService(StudyDesignFigureService):
    @staticmethod
    def _get_study_arms(*_args, **_kwargs):
        return STUDY_ARMS

    @staticmethod
    def _get_study_epochs(*_args, **_kwargs):
        return STUDY_EPOCHS

    @staticmethod
    def _get_study_elements(*_args, **_kwargs):
        return STUDY_ELEMENTS

    @staticmethod
    def _get_study_design_cells(*_args, **_kwargs):
        return STUDY_DESIGN_CELLS

    @staticmethod
    def _get_study_visits(*_args, **_kwargs):
        return STUDY_VISITS

    @staticmethod
    def _get_soa_preferences(*_args, **_kwargs):
        return SOA_PREFERENCES

    @staticmethod
    def _get_preferred_time_unit_name(*_args, **_kwargs):
        return "week"


def test_mk_data_matrix():
    table = MockStudyDesignFigureService()._mk_data_matrix(
        STUDY_ARMS,
        STUDY_EPOCHS,
        STUDY_ELEMENTS,
        STUDY_DESIGN_CELLS,
        SOA_PREFERENCES,
    )
    assert table == MATRIX


def test_select_first_visits():
    visits = MockStudyDesignFigureService()._pick_first_visit_of_epochs(STUDY_VISITS)
    visit_ids = {visit.uid for visit in visits if visit}
    assert visit_ids == VISIT_IDS


def test_mk_timeline():
    # pylint: disable=unused-argument
    def draw_svg(table, timeline, doc_width, doc_height):
        # pylint: disable=unused-variable
        __tracebackhide__ = True
        assert timeline == TIMELINE

    service = MockStudyDesignFigureService()
    service.draw_svg = draw_svg
    service.get_svg_document(STUDY_UID)


# pylint: disable=unsupported-membership-test
def test_get_svg_document():
    service = MockStudyDesignFigureService()
    doc: str = service.get_svg_document("")

    assert "</svg>" in doc, "no </svg> tag in document, not an SVG?"
    assert "</defs>" in doc, "no </defs> tag in document, missing defs?"
    assert "</style>" in doc, "no </style> tag in document, missing styles?"

    assert 'class="arm"' in doc, 'class="arm" found, missing arms?'
    assert 'class="epoch"' in doc, 'class="epoch" found, missing epochs?'
    assert (
        'class="element"' in doc
    ), 'class="element" found, missing study design cells?'

    for uid in STUDY_ARMS.keys():
        assert f'id="{uid}"' in doc, f'arm id="{uid}" not found in document'
    for epoch in STUDY_EPOCHS:
        uid = epoch.uid
        assert f'id="{uid}"' in doc, f'epoch id="{uid}" not found in document'
    for uid in STUDY_ELEMENTS.keys():
        assert f'id="{uid}"' in doc, f'element id="{uid}" not found in document'

    assert (
        'class="visit-type"' in doc
    ), 'class="visit-type" found, missing visit type labels?'
    assert (
        'class="visit-timing"' in doc
    ), 'class="visit-timing" found, missing visit milestones?'

    assert (
        'class="timeline-arrow"' in doc
    ), 'class="timeline-arrow" not found, missing timeline arrows?'
    assert (
        'class="timeline-arrow"' in doc
    ), 'class="visit-arrow" not found, missing visit arrows?'
    assert "markerWidth" in doc, '"markerWidth" found, missing arrowhead markers?'

    assert doc == SVG_DOCUMENT
