import datetime

from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityForStudyActivity,
    ActivityGroupingHierarchySimpleModel,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.study_selections.study_selection import (
    ReferencedItem,
    SimpleStudyActivityGroup,
    SimpleStudyActivitySubGroup,
    SimpleStudySoAGroup,
    StudyActivitySchedule,
    StudySelectionActivity,
)
from clinical_mdr_api.models.study_selections.study_soa_footnote import StudySoAFootnote
from clinical_mdr_api.models.study_selections.study_visit import StudyVisit
from clinical_mdr_api.models.syntax_instances.footnote import (
    Footnote,
    FootnoteTemplateWithType,
)
from clinical_mdr_api.services.utils.table_f import (
    Ref,
    SimpleFootnote,
    TableCell,
    TableRow,
    TableWithFootnotes,
)
from common import config

AUTHOR_USERNAME = "unknown-user"

STUDY_VISITS = [
    StudyVisit(
        study_epoch_uid="StudyEpoch_000004",
        visit_type_uid="CTTerm_000182",
        time_reference_uid="CTTerm_000122",
        time_value=-14,
        time_unit_uid="UnitDefinition_000364",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000081",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000012",
        study_uid="Study_000002",
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
            "term_uid": "CTTerm_000182",
            "sponsor_preferred_name": "Screening",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global anchor visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000081",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=-1209600.0,
        duration_time_unit="UnitDefinition_000364",
        study_day_number=-14,
        study_duration_days=-15,
        study_duration_days_label="-15 days",
        study_day_label="Day -14",
        study_week_number=-2,
        study_duration_weeks=-3,
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
        start_date=datetime.datetime(
            2023, 9, 25, 11, 41, 55, 138405, tzinfo=datetime.timezone.utc
        ),
        end_date=None,
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=22,
        change_type=None,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000005",
        visit_type_uid="CTTerm_000184",
        time_reference_uid="CTTerm_000122",
        time_value=-3,
        time_unit_uid="UnitDefinition_000364",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000081",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000013",
        study_uid="Study_000002",
        study_epoch_name="Run-in",
        study_epoch={
            "term_uid": "C98779_RUN-IN",
            "sponsor_preferred_name": "Run-in",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="C98779_RUN-IN",
        order=2,
        visit_type_name="Start of run-in",
        visit_type={
            "term_uid": "CTTerm_000184",
            "sponsor_preferred_name": "Start of run-in",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global anchor visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000081",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=-259200.0,
        duration_time_unit="UnitDefinition_000364",
        study_day_number=-3,
        study_duration_days=-4,
        study_duration_days_label="-4 days",
        study_day_label="Day -3",
        study_week_number=1,
        study_duration_weeks=0,
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
        start_date=datetime.datetime(
            2023, 9, 25, 11, 41, 56, 604440, tzinfo=datetime.timezone.utc
        ),
        end_date=None,
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=9,
        change_type=None,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000005",
        visit_type_uid="CTTerm_000177",
        time_reference_uid="CTTerm_000122",
        time_value=-2,
        time_unit_uid="UnitDefinition_000364",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=False,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000081",
        epoch_allocation_uid="CTTerm_000194",
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000014",
        study_uid="Study_000002",
        study_epoch_name="Run-in",
        study_epoch={
            "term_uid": "C98779_RUN-IN",
            "sponsor_preferred_name": "Run-in",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="C98779_RUN-IN",
        order=3,
        visit_type_name="Pre-treatment",
        visit_type={
            "term_uid": "CTTerm_000177",
            "sponsor_preferred_name": "Pre-treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global anchor visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000081",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name="Current Visit",
        duration_time=-172800.0,
        duration_time_unit="UnitDefinition_000364",
        study_day_number=-2,
        study_duration_days=-3,
        study_duration_days_label="-3 days",
        study_day_label="Day -2",
        study_week_number=1,
        study_duration_weeks=0,
        study_duration_weeks_label="0 weeks",
        week_in_study_label="Week 0",
        study_week_label="Week 1",
        visit_number=3,
        visit_subnumber=0,
        unique_visit_number=300,
        visit_subname="Visit 3",
        visit_name="Visit 3",
        visit_short_name="V3",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date=datetime.datetime(
            2023, 9, 27, 12, 50, 50, 931022, tzinfo=datetime.timezone.utc
        ),
        end_date=None,
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=7,
        change_type=None,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000005",
        visit_type_uid="CTTerm_000177",
        time_reference_uid="CTTerm_000122",
        time_value=-1,
        time_unit_uid="UnitDefinition_000364",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000081",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000015",
        study_uid="Study_000002",
        study_epoch_name="Run-in",
        study_epoch={
            "term_uid": "C98779_RUN-IN",
            "sponsor_preferred_name": "Run-in",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="C98779_RUN-IN",
        order=4,
        visit_type_name="Pre-treatment",
        visit_type={
            "term_uid": "CTTerm_000177",
            "sponsor_preferred_name": "Pre-treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global anchor visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000081",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=-86400.0,
        duration_time_unit="UnitDefinition_000364",
        study_day_number=-1,
        study_duration_days=-2,
        study_duration_days_label="-2 days",
        study_day_label="Day -1",
        study_week_number=1,
        study_duration_weeks=0,
        study_duration_weeks_label="0 weeks",
        week_in_study_label="Week 0",
        study_week_label="Week 1",
        visit_number=4,
        visit_subnumber=0,
        unique_visit_number=400,
        visit_subname="Visit 4",
        visit_name="Visit 4",
        visit_short_name="V4",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date=datetime.datetime(
            2023, 9, 25, 11, 41, 58, 200939, tzinfo=datetime.timezone.utc
        ),
        end_date=None,
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=7,
        change_type=None,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000006",
        visit_type_uid="CTTerm_000187",
        time_reference_uid="CTTerm_000122",
        time_value=0,
        time_unit_uid="UnitDefinition_000364",
        visit_sublabel_reference=None,
        consecutive_visit_group="V5-V7",
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        description="CYCLE 1, TREATMENT DAY 1",
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000081",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=True,
        is_soa_milestone=False,
        uid="StudyVisit_000016",
        study_uid="Study_000002",
        study_epoch_name="Treatment 1",
        study_epoch={
            "term_uid": "CTTerm_001163",
            "sponsor_preferred_name": "Treatment 1",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="CTTerm_001163",
        order=5,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000187",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global anchor visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000081",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=0.0,
        duration_time_unit="UnitDefinition_000364",
        study_day_number=1,
        study_duration_days=0,
        study_duration_days_label="0 days",
        study_day_label="Day 1",
        study_week_number=1,
        study_duration_weeks=0,
        study_duration_weeks_label="0 weeks",
        week_in_study_label="Week 0",
        study_week_label="Week 1",
        visit_number=5,
        visit_subnumber=0,
        unique_visit_number=500,
        visit_subname="Visit 5",
        visit_name="Visit 5",
        visit_short_name="V5",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date=datetime.datetime(
            2023, 9, 28, 7, 8, 37, 273657, tzinfo=datetime.timezone.utc
        ),
        end_date=None,
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=8,
        change_type=None,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000006",
        visit_type_uid="CTTerm_000187",
        time_reference_uid="CTTerm_000122",
        time_value=2,
        time_unit_uid="UnitDefinition_000364",
        visit_sublabel_reference=None,
        consecutive_visit_group="V5-V7",
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        description="CYCLE 1, TREATMENT DAY 3",
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000081",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000017",
        study_uid="Study_000002",
        study_epoch_name="Treatment 1",
        study_epoch={
            "term_uid": "CTTerm_001163",
            "sponsor_preferred_name": "Treatment 1",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="CTTerm_001163",
        order=6,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000187",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global anchor visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000081",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=172800.0,
        duration_time_unit="UnitDefinition_000364",
        study_day_number=3,
        study_duration_days=2,
        study_duration_days_label="2 days",
        study_day_label="Day 3",
        study_week_number=1,
        study_duration_weeks=0,
        study_duration_weeks_label="0 weeks",
        week_in_study_label="Week 0",
        study_week_label="Week 1",
        visit_number=6,
        visit_subnumber=0,
        unique_visit_number=600,
        visit_subname="Visit 6",
        visit_name="Visit 6",
        visit_short_name="V6",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date=datetime.datetime(
            2023, 9, 28, 7, 8, 37, 539422, tzinfo=datetime.timezone.utc
        ),
        end_date=None,
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=8,
        change_type=None,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000006",
        visit_type_uid="CTTerm_000187",
        time_reference_uid="CTTerm_000122",
        time_value=4,
        time_unit_uid="UnitDefinition_000364",
        visit_sublabel_reference=None,
        consecutive_visit_group="V5-V7",
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        description="CYCLE 1, TREATMENT DAY 5",
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000081",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000018",
        study_uid="Study_000002",
        study_epoch_name="Treatment 1",
        study_epoch={
            "term_uid": "CTTerm_001163",
            "sponsor_preferred_name": "Treatment 1",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="CTTerm_001163",
        order=7,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000187",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global anchor visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000081",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=345600.0,
        duration_time_unit="UnitDefinition_000364",
        study_day_number=5,
        study_duration_days=4,
        study_duration_days_label="4 days",
        study_day_label="Day 5",
        study_week_number=1,
        study_duration_weeks=0,
        study_duration_weeks_label="0 weeks",
        week_in_study_label="Week 0",
        study_week_label="Week 1",
        visit_number=7,
        visit_subnumber=0,
        unique_visit_number=700,
        visit_subname="Visit 7",
        visit_name="Visit 7",
        visit_short_name="V7",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date=datetime.datetime(
            2023, 9, 28, 7, 8, 37, 794881, tzinfo=datetime.timezone.utc
        ),
        end_date=None,
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=8,
        change_type=None,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000007",
        visit_type_uid="CTTerm_000187",
        time_reference_uid="CTTerm_000122",
        time_value=14,
        time_unit_uid="UnitDefinition_000364",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        description="CYCLE 2, TREATMENT DAY 1",
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000081",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000019",
        study_uid="Study_000002",
        study_epoch_name="Treatment 2",
        study_epoch={
            "term_uid": "CTTerm_001162",
            "sponsor_preferred_name": "Treatment 2",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="CTTerm_001162",
        order=8,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000187",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global anchor visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000081",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=1209600.0,
        duration_time_unit="UnitDefinition_000364",
        study_day_number=15,
        study_duration_days=14,
        study_duration_days_label="14 days",
        study_day_label="Day 15",
        study_week_number=3,
        study_duration_weeks=2,
        study_duration_weeks_label="2 weeks",
        week_in_study_label="Week 2",
        study_week_label="Week 3",
        visit_number=8,
        visit_subnumber=0,
        unique_visit_number=800,
        visit_subname="Visit 8",
        visit_name="Visit 8",
        visit_short_name="V8",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date=datetime.datetime(
            2023, 9, 25, 11, 42, 1, 370897, tzinfo=datetime.timezone.utc
        ),
        end_date=None,
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=6,
        change_type=None,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000007",
        visit_type_uid="CTTerm_000187",
        time_reference_uid="CTTerm_000122",
        time_value=16,
        time_unit_uid="UnitDefinition_000364",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        description="CYCLE 2, TREATMENT DAY 2",
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000081",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000020",
        study_uid="Study_000002",
        study_epoch_name="Treatment 2",
        study_epoch={
            "term_uid": "CTTerm_001162",
            "sponsor_preferred_name": "Treatment 2",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="CTTerm_001162",
        order=9,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000187",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global anchor visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000081",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=1382400.0,
        duration_time_unit="UnitDefinition_000364",
        study_day_number=17,
        study_duration_days=16,
        study_duration_days_label="16 days",
        study_day_label="Day 17",
        study_week_number=3,
        study_duration_weeks=2,
        study_duration_weeks_label="2 weeks",
        week_in_study_label="Week 2",
        study_week_label="Week 3",
        visit_number=9,
        visit_subnumber=0,
        unique_visit_number=900,
        visit_subname="Visit 9",
        visit_name="Visit 9",
        visit_short_name="V9",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date=datetime.datetime(
            2023, 9, 25, 11, 42, 2, 213618, tzinfo=datetime.timezone.utc
        ),
        end_date=None,
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=7,
        change_type=None,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000007",
        visit_type_uid="CTTerm_000187",
        time_reference_uid="CTTerm_000122",
        time_value=18,
        time_unit_uid="UnitDefinition_000364",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        description="CYCLE 2, TREATMENT DAY 5",
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000081",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000021",
        study_uid="Study_000002",
        study_epoch_name="Treatment 2",
        study_epoch={
            "term_uid": "CTTerm_001162",
            "sponsor_preferred_name": "Treatment 2",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="CTTerm_001162",
        order=10,
        visit_type_name="Treatment",
        visit_type={
            "term_uid": "CTTerm_000187",
            "sponsor_preferred_name": "Treatment",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global anchor visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000081",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=1555200.0,
        duration_time_unit="UnitDefinition_000364",
        study_day_number=19,
        study_duration_days=18,
        study_duration_days_label="18 days",
        study_day_label="Day 19",
        study_week_number=3,
        study_duration_weeks=2,
        study_duration_weeks_label="2 weeks",
        week_in_study_label="Week 2",
        study_week_label="Week 3",
        visit_number=10,
        visit_subnumber=0,
        unique_visit_number=1000,
        visit_subname="Visit 10",
        visit_name="Visit 10",
        visit_short_name="V10",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date=datetime.datetime(
            2023, 9, 25, 11, 42, 3, 81758, tzinfo=datetime.timezone.utc
        ),
        end_date=None,
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=10,
        change_type=None,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000008",
        visit_type_uid="CTTerm_000175",
        time_reference_uid="CTTerm_000122",
        time_value=21,
        time_unit_uid="UnitDefinition_000364",
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000081",
        epoch_allocation_uid=None,
        visit_class="SINGLE_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000022",
        study_uid="Study_000002",
        study_epoch_name="Follow-up",
        study_epoch={
            "term_uid": "C99158_FOLLOW-UP",
            "sponsor_preferred_name": "Follow-up",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="C99158_FOLLOW-UP",
        order=11,
        visit_type_name="Follow-up",
        visit_type={
            "term_uid": "CTTerm_000175",
            "sponsor_preferred_name": "Follow-up",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name="Global anchor visit",
        time_unit_name="days",
        visit_contact_mode_name="On Site Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000081",
            "sponsor_preferred_name": "On Site Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name=None,
        duration_time=1814400.0,
        duration_time_unit="UnitDefinition_000364",
        study_day_number=22,
        study_duration_days=21,
        study_duration_days_label="21 days",
        study_day_label="Day 22",
        study_week_number=4,
        study_duration_weeks=3,
        study_duration_weeks_label="3 weeks",
        week_in_study_label="Week 3",
        study_week_label="Week 4",
        visit_number=11,
        visit_subnumber=0,
        unique_visit_number=1100,
        visit_subname="Visit 11",
        visit_name="Visit 11",
        visit_short_name="V11",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date=datetime.datetime(
            2023, 9, 25, 11, 42, 4, 15590, tzinfo=datetime.timezone.utc
        ),
        end_date=None,
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=12,
        change_type=None,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000009",
        visit_type_uid="CTTerm_000192",
        time_reference_uid=None,
        time_value=None,
        time_unit_uid=None,
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=-9999,
        max_visit_window_value=9999,
        visit_window_unit_uid="UnitDefinition_000364",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000079",
        epoch_allocation_uid="CTTerm_000196",
        visit_class="UNSCHEDULED_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000023",
        study_uid="Study_000002",
        study_epoch_name="Basic",
        study_epoch={
            "term_uid": "CTTerm_000009",
            "sponsor_preferred_name": "Basic",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="CTTerm_000009",
        order=config.UNSCHEDULED_VISIT_NUMBER,
        visit_type_name="Unscheduled",
        visit_type={
            "term_uid": "CTTerm_000192",
            "sponsor_preferred_name": "Unscheduled",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name=None,
        time_unit_name=None,
        visit_contact_mode_name="Virtual Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000079",
            "sponsor_preferred_name": "Virtual Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name="Date Current Visit",
        duration_time=None,
        duration_time_unit=None,
        study_day_number=None,
        study_duration_days_label=None,
        study_day_label=None,
        study_week_number=None,
        study_duration_weeks_label=None,
        week_in_study_label=None,
        study_week_label=None,
        visit_number=config.UNSCHEDULED_VISIT_NUMBER,
        visit_subnumber=0,
        unique_visit_number=config.UNSCHEDULED_VISIT_NUMBER,
        visit_subname=f"Visit {config.UNSCHEDULED_VISIT_NUMBER}",
        visit_name=f"Visit {config.UNSCHEDULED_VISIT_NUMBER}",
        visit_short_name=f"{config.UNSCHEDULED_VISIT_NUMBER}",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date=datetime.datetime(
            2023, 9, 28, 7, 9, 58, 725540, tzinfo=datetime.timezone.utc
        ),
        end_date=None,
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=0,
        change_type=None,
    ),
    StudyVisit(
        study_epoch_uid="StudyEpoch_000009",
        visit_type_uid="CTTerm_000190",
        time_reference_uid=None,
        time_value=None,
        time_unit_uid=None,
        visit_sublabel_reference=None,
        consecutive_visit_group=None,
        show_visit=True,
        min_visit_window_value=-9999,
        max_visit_window_value=9999,
        visit_window_unit_uid="UnitDefinition_000364",
        description=None,
        start_rule=None,
        end_rule=None,
        visit_contact_mode_uid="CTTerm_000079",
        epoch_allocation_uid="CTTerm_000196",
        visit_class="NON_VISIT",
        visit_subclass="SINGLE_VISIT",
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        uid="StudyVisit_000024",
        study_uid="Study_000002",
        study_epoch_name="Basic",
        study_epoch={
            "term_uid": "CTTerm_000009",
            "sponsor_preferred_name": "Basic",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_uid="CTTerm_000009",
        order=config.NON_VISIT_NUMBER,
        visit_type_name="Non-visit",
        visit_type={
            "term_uid": "CTTerm_000190",
            "sponsor_preferred_name": "Non-visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        time_reference_name=None,
        time_unit_name=None,
        visit_contact_mode_name="Virtual Visit",
        visit_contact_mode={
            "term_uid": "CTTerm_000079",
            "sponsor_preferred_name": "Virtual Visit",
            "sponsor_preferred_name_sentence_case": "screening",
        },
        epoch_allocation_name="Date Current Visit",
        duration_time=None,
        duration_time_unit=None,
        study_day_number=None,
        study_duration_days_label=None,
        study_day_label=None,
        study_week_number=None,
        study_duration_weeks_label=None,
        week_in_study_label=None,
        study_week_label=None,
        visit_number=config.NON_VISIT_NUMBER,
        visit_subnumber=0,
        unique_visit_number=config.NON_VISIT_NUMBER,
        visit_subname=f"Visit {config.NON_VISIT_NUMBER}",
        visit_name=f"Visit {config.NON_VISIT_NUMBER}",
        visit_short_name=f"{config.NON_VISIT_NUMBER}",
        visit_window_unit_name="days",
        status="DRAFT",
        start_date=datetime.datetime(
            2023, 9, 28, 7, 9, 40, 605585, tzinfo=datetime.timezone.utc
        ),
        end_date=None,
        author_username=AUTHOR_USERNAME,
        possible_actions=["edit", "delete", "lock"],
        study_activity_count=0,
        change_type=None,
    ),
]
STUDY_ACTIVITIES = [
    StudySelectionActivity(
        study_uid="Study_000002",
        order=1,
        project_number=None,
        project_name=None,
        show_activity_in_protocol_flowchart=True,
        show_activity_subgroup_in_protocol_flowchart=True,
        show_activity_group_in_protocol_flowchart=True,
        show_soa_group_in_protocol_flowchart=True,
        study_activity_uid="StudyActivity_000033",
        study_activity_subgroup=SimpleStudyActivitySubGroup(
            study_activity_subgroup_uid="StudyActivitySubGroup_000033",
            activity_subgroup_uid="ActivitySubGroup_000016",
            activity_subgroup_name="Informed Consent and Demography",
            order=1,
        ),
        study_activity_group=SimpleStudyActivityGroup(
            study_activity_group_uid="StudyActivityGroup_000033",
            activity_group_uid="ActivityGroup_000010",
            activity_group_name="Informed Consent and Demography",
            order=1,
        ),
        study_soa_group=SimpleStudySoAGroup(
            study_soa_group_uid="StudySoAGroup_000033",
            soa_group_term_uid="CTTerm_000066",
            soa_group_term_name="SUBJECT RELATED INFORMATION",
            order=1,
        ),
        activity=ActivityForStudyActivity(
            start_date=datetime.datetime(2023, 9, 25, 11, 34, 8, 76019),
            end_date=None,
            status="Final",
            version="1.0",
            change_description="Approved version",
            author_username=AUTHOR_USERNAME,
            uid="Activity_000059",
            name="Informed Consent Obtained",
            name_sentence_case="informed consent obtained",
            synonyms=[],
            definition=None,
            abbreviation=None,
            library_name="Sponsor",
            possible_actions=["inactivate", "new_version"],
            nci_concept_id=None,
            activity_groupings=[
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000010",
                    activity_group_name="Informed Consent and Demography",
                    activity_subgroup_uid="ActivitySubGroup_000016",
                    activity_subgroup_name="Informed Consent and Demography",
                ),
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000013",
                    activity_group_name="Informed Consent",
                    activity_subgroup_uid="ActivitySubGroup_000026",
                    activity_subgroup_name="Informed Consent",
                ),
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000015",
                    activity_group_name="Future Research Biosample Consent",
                    activity_subgroup_uid="ActivitySubGroup_000029",
                    activity_subgroup_name="Future Research Biosample Consent",
                ),
            ],
            request_rationale=None,
            replaced_by_activity=None,
            is_data_collected=False,
        ),
        start_date=datetime.datetime(2023, 9, 26, 22, 7, 17, 577489),
        author_username=AUTHOR_USERNAME,
        end_date=None,
        status=None,
        change_type=None,
        latest_activity=None,
        accepted_version=False,
    ),
    StudySelectionActivity(
        study_uid="Study_000002",
        order=1,
        project_number=None,
        project_name=None,
        show_activity_in_protocol_flowchart=True,
        show_activity_subgroup_in_protocol_flowchart=False,
        show_activity_group_in_protocol_flowchart=False,
        show_soa_group_in_protocol_flowchart=True,
        study_activity_uid="StudyActivity_000034",
        study_activity_subgroup=SimpleStudyActivitySubGroup(
            study_activity_subgroup_uid="StudyActivitySubGroup_000034",
            activity_subgroup_uid="ActivitySubGroup_000018",
            activity_subgroup_name="Eligibility Criteria",
            order=1,
        ),
        study_activity_group=SimpleStudyActivityGroup(
            study_activity_group_uid="StudyActivityGroup_000034",
            activity_group_uid="ActivityGroup_000011",
            activity_group_name="Eligibility Criteria",
            order=2,
        ),
        study_soa_group=SimpleStudySoAGroup(
            study_soa_group_uid="StudySoAGroup_000034",
            soa_group_term_uid="CTTerm_000066",
            soa_group_term_name="SUBJECT RELATED INFORMATION",
            order=1,
        ),
        activity=ActivityForStudyActivity(
            start_date=datetime.datetime(2023, 9, 25, 11, 34, 5, 65621),
            end_date=None,
            status="Final",
            version="1.0",
            change_description="Approved version",
            author_username=AUTHOR_USERNAME,
            uid="Activity_000041",
            name="Eligibility Criteria Met",
            name_sentence_case="eligibility criteria met",
            synonyms=[],
            definition=None,
            abbreviation=None,
            library_name="Sponsor",
            possible_actions=["inactivate", "new_version"],
            nci_concept_id=None,
            activity_groupings=[
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000011",
                    activity_group_name="Eligibility Criteria",
                    activity_subgroup_uid="ActivitySubGroup_000018",
                    activity_subgroup_name="Eligibility Criteria",
                )
            ],
            request_rationale=None,
            replaced_by_activity=None,
            is_data_collected=False,
        ),
        start_date=datetime.datetime(2023, 9, 28, 12, 15, 35, 762079),
        author_username=AUTHOR_USERNAME,
        end_date=None,
        status=None,
        change_type=None,
        latest_activity=None,
        accepted_version=False,
    ),
    StudySelectionActivity(
        study_uid="Study_000002",
        order=1,
        project_number=None,
        project_name=None,
        show_activity_in_protocol_flowchart=False,
        show_activity_subgroup_in_protocol_flowchart=False,
        show_activity_group_in_protocol_flowchart=True,
        show_soa_group_in_protocol_flowchart=True,
        study_activity_uid="StudyActivity_000035",
        study_activity_subgroup=SimpleStudyActivitySubGroup(
            study_activity_subgroup_uid="StudyActivitySubGroup_000035",
            activity_subgroup_uid="ActivitySubGroup_000030",
            activity_subgroup_name="Medical History/Concomitant Illness",
            order=1,
        ),
        study_activity_group=SimpleStudyActivityGroup(
            study_activity_group_uid="StudyActivityGroup_000035",
            activity_group_uid="ActivityGroup_000017",
            activity_group_name="Medical History/Concomitant Illness",
            order=3,
        ),
        study_soa_group=SimpleStudySoAGroup(
            study_soa_group_uid="StudySoAGroup_000035",
            soa_group_term_uid="CTTerm_000066",
            soa_group_term_name="SUBJECT RELATED INFORMATION",
            order=1,
        ),
        activity=ActivityForStudyActivity(
            start_date=datetime.datetime(2023, 9, 25, 11, 34, 8, 699174),
            end_date=None,
            status="Final",
            version="1.0",
            change_description="Approved version",
            author_username=AUTHOR_USERNAME,
            uid="Activity_000062",
            name="Medical History/Concomitant Illness",
            name_sentence_case="medical history/concomitant illness",
            synonyms=[],
            definition=None,
            abbreviation=None,
            library_name="Sponsor",
            possible_actions=["inactivate", "new_version"],
            nci_concept_id=None,
            activity_groupings=[
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000017",
                    activity_group_name="Medical History/Concomitant Illness",
                    activity_subgroup_uid="ActivitySubGroup_000030",
                    activity_subgroup_name="Medical History/Concomitant Illness",
                )
            ],
            request_rationale=None,
            replaced_by_activity=None,
            is_data_collected=False,
        ),
        start_date=datetime.datetime(2023, 9, 28, 7, 18, 2, 633400),
        author_username=AUTHOR_USERNAME,
        end_date=None,
        status=None,
        change_type=None,
        latest_activity=None,
        accepted_version=False,
    ),
    StudySelectionActivity(
        study_uid="Study_000002",
        order=1,
        project_number=None,
        project_name=None,
        show_activity_in_protocol_flowchart=False,
        show_activity_subgroup_in_protocol_flowchart=True,
        show_activity_group_in_protocol_flowchart=False,
        show_soa_group_in_protocol_flowchart=True,
        study_activity_uid="StudyActivity_000036",
        study_activity_subgroup=SimpleStudyActivitySubGroup(
            study_activity_subgroup_uid="StudyActivitySubGroup_000036",
            activity_subgroup_uid="ActivitySubGroup_000010",
            activity_subgroup_name="Body Measurements",
            order=1,
        ),
        study_activity_group=SimpleStudyActivityGroup(
            study_activity_group_uid="StudyActivityGroup_000036",
            activity_group_uid="ActivityGroup_000005",
            activity_group_name="Body Measurements",
            order=4,
        ),
        study_soa_group=SimpleStudySoAGroup(
            study_soa_group_uid="StudySoAGroup_000036",
            soa_group_term_uid="CTTerm_000066",
            soa_group_term_name="SUBJECT RELATED INFORMATION",
            order=1,
        ),
        activity=ActivityForStudyActivity(
            start_date=datetime.datetime(2023, 9, 25, 11, 34, 7, 274454),
            end_date=None,
            status="Final",
            version="1.0",
            change_description="Approved version",
            author_username=AUTHOR_USERNAME,
            uid="Activity_000054",
            name="Height",
            name_sentence_case="height",
            synonyms=[],
            definition=None,
            abbreviation=None,
            library_name="Sponsor",
            possible_actions=["inactivate", "new_version"],
            nci_concept_id=None,
            activity_groupings=[
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000005",
                    activity_group_name="Body Measurements",
                    activity_subgroup_uid="ActivitySubGroup_000010",
                    activity_subgroup_name="Body Measurements",
                )
            ],
            request_rationale=None,
            replaced_by_activity=None,
            is_data_collected=False,
        ),
        start_date=datetime.datetime(2023, 9, 28, 12, 15, 14, 847955),
        author_username=AUTHOR_USERNAME,
        end_date=None,
        status=None,
        change_type=None,
        latest_activity=None,
        accepted_version=False,
    ),
    StudySelectionActivity(
        study_uid="Study_000002",
        order=2,
        project_number=None,
        project_name=None,
        show_activity_in_protocol_flowchart=False,
        show_activity_subgroup_in_protocol_flowchart=True,
        show_activity_group_in_protocol_flowchart=False,
        show_soa_group_in_protocol_flowchart=True,
        study_activity_uid="StudyActivity_000037",
        study_activity_subgroup=SimpleStudyActivitySubGroup(
            study_activity_subgroup_uid="StudyActivitySubGroup_000037",
            activity_subgroup_uid="ActivitySubGroup_000010",
            activity_subgroup_name="Body Measurements",
            order=1,
        ),
        study_activity_group=SimpleStudyActivityGroup(
            study_activity_group_uid="StudyActivityGroup_000037",
            activity_group_uid="ActivityGroup_000005",
            activity_group_name="Body Measurements",
            order=4,
        ),
        study_soa_group=SimpleStudySoAGroup(
            study_soa_group_uid="StudySoAGroup_000037",
            soa_group_term_uid="CTTerm_000066",
            soa_group_term_name="SUBJECT RELATED INFORMATION",
            order=1,
        ),
        activity=ActivityForStudyActivity(
            start_date=datetime.datetime(2023, 9, 25, 11, 34, 2, 443094),
            end_date=None,
            status="Final",
            version="1.0",
            change_description="Approved version",
            author_username=AUTHOR_USERNAME,
            uid="Activity_000025",
            name="Weight",
            name_sentence_case="weight",
            synonyms=[],
            definition=None,
            abbreviation=None,
            library_name="Sponsor",
            possible_actions=["inactivate", "new_version"],
            nci_concept_id=None,
            activity_groupings=[
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000005",
                    activity_group_name="Body Measurements",
                    activity_subgroup_uid="ActivitySubGroup_000010",
                    activity_subgroup_name="Body Measurements",
                )
            ],
            request_rationale=None,
            replaced_by_activity=None,
            is_data_collected=False,
        ),
        start_date=datetime.datetime(2023, 9, 28, 12, 15, 14, 549807),
        author_username=AUTHOR_USERNAME,
        end_date=None,
        status=None,
        change_type=None,
        latest_activity=None,
        accepted_version=False,
    ),
    StudySelectionActivity(
        study_uid="Study_000002",
        order=1,
        project_number=None,
        project_name=None,
        show_activity_in_protocol_flowchart=False,
        show_activity_subgroup_in_protocol_flowchart=False,
        show_activity_group_in_protocol_flowchart=True,
        show_soa_group_in_protocol_flowchart=True,
        study_activity_uid="StudyActivity_000038",
        study_activity_subgroup=SimpleStudyActivitySubGroup(
            study_activity_subgroup_uid="StudyActivitySubGroup_000038",
            activity_subgroup_uid="ActivitySubGroup_000021",
            activity_subgroup_name="Haematology",
            order=1,
        ),
        study_activity_group=SimpleStudyActivityGroup(
            study_activity_group_uid="StudyActivityGroup_000038",
            activity_group_uid="ActivityGroup_000004",
            activity_group_name="Laboratory Assessments",
            order=5,
        ),
        study_soa_group=SimpleStudySoAGroup(
            study_soa_group_uid="StudySoAGroup_000038",
            soa_group_term_uid="CTTerm_000066",
            soa_group_term_name="SUBJECT RELATED INFORMATION",
            order=1,
        ),
        activity=ActivityForStudyActivity(
            start_date=datetime.datetime(2023, 9, 25, 11, 34, 5, 630967),
            end_date=None,
            status="Final",
            version="1.0",
            change_description="Approved version",
            author_username=AUTHOR_USERNAME,
            uid="Activity_000044",
            name="Erythrocytes",
            name_sentence_case="erythrocytes",
            synonyms=[],
            definition=None,
            abbreviation=None,
            library_name="Sponsor",
            possible_actions=["inactivate", "new_version"],
            nci_concept_id=None,
            activity_groupings=[
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000003",
                    activity_group_name="AE Requiring Additional Data",
                    activity_subgroup_uid="ActivitySubGroup_000004",
                    activity_subgroup_name="Laboratory Assessment",
                ),
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000004",
                    activity_group_name="Laboratory Assessments",
                    activity_subgroup_uid="ActivitySubGroup_000006",
                    activity_subgroup_name="Urinalysis",
                ),
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000004",
                    activity_group_name="Laboratory Assessments",
                    activity_subgroup_uid="ActivitySubGroup_000021",
                    activity_subgroup_name="Haematology",
                ),
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000004",
                    activity_group_name="Laboratory Assessments",
                    activity_subgroup_uid="ActivitySubGroup_000022",
                    activity_subgroup_name="Urine Dipstick",
                ),
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000004",
                    activity_group_name="Laboratory Assessments",
                    activity_subgroup_uid="ActivitySubGroup_000023",
                    activity_subgroup_name="Urinalysis - Urine Dipstick",
                ),
            ],
            request_rationale=None,
            replaced_by_activity=None,
            is_data_collected=False,
        ),
        start_date=datetime.datetime(2023, 9, 28, 12, 15, 4, 769418),
        author_username=AUTHOR_USERNAME,
        end_date=None,
        status=None,
        change_type=None,
        latest_activity=None,
        accepted_version=False,
    ),
    StudySelectionActivity(
        study_uid="Study_000002",
        order=1,
        project_number=None,
        project_name=None,
        show_activity_in_protocol_flowchart=False,
        show_activity_subgroup_in_protocol_flowchart=True,
        show_activity_group_in_protocol_flowchart=True,
        show_soa_group_in_protocol_flowchart=True,
        study_activity_uid="StudyActivity_000039",
        study_activity_subgroup=SimpleStudyActivitySubGroup(
            study_activity_subgroup_uid="StudyActivitySubGroup_000039",
            activity_subgroup_uid="ActivitySubGroup_000009",
            activity_subgroup_name="Vital Signs",
            order=1,
        ),
        study_activity_group=SimpleStudyActivityGroup(
            study_activity_group_uid="StudyActivityGroup_000039",
            activity_group_uid="ActivityGroup_000006",
            activity_group_name="Vital Signs",
            order=6,
        ),
        study_soa_group=SimpleStudySoAGroup(
            study_soa_group_uid="StudySoAGroup_000039",
            soa_group_term_uid="CTTerm_000066",
            soa_group_term_name="SUBJECT RELATED INFORMATION",
            order=1,
        ),
        activity=ActivityForStudyActivity(
            start_date=datetime.datetime(2023, 9, 25, 11, 34, 2, 671856),
            end_date=None,
            status="Final",
            version="1.0",
            change_description="Approved version",
            author_username=AUTHOR_USERNAME,
            uid="Activity_000027",
            name="Systolic Blood Pressure",
            name_sentence_case="systolic blood pressure",
            synonyms=[],
            definition=None,
            abbreviation=None,
            library_name="Sponsor",
            possible_actions=["inactivate", "new_version"],
            nci_concept_id=None,
            activity_groupings=[
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000006",
                    activity_group_name="Vital Signs",
                    activity_subgroup_uid="ActivitySubGroup_000009",
                    activity_subgroup_name="Vital Signs",
                )
            ],
            request_rationale=None,
            replaced_by_activity=None,
            is_data_collected=False,
        ),
        start_date=datetime.datetime(2023, 9, 28, 12, 14, 20, 686382),
        author_username=AUTHOR_USERNAME,
        end_date=None,
        status=None,
        change_type=None,
        latest_activity=None,
        accepted_version=False,
    ),
    StudySelectionActivity(
        study_uid="Study_000002",
        order=2,
        project_number=None,
        project_name=None,
        show_activity_in_protocol_flowchart=False,
        show_activity_subgroup_in_protocol_flowchart=True,
        show_activity_group_in_protocol_flowchart=True,
        show_soa_group_in_protocol_flowchart=True,
        study_activity_uid="StudyActivity_000040",
        study_activity_subgroup=SimpleStudyActivitySubGroup(
            study_activity_subgroup_uid="StudyActivitySubGroup_000040",
            activity_subgroup_uid="ActivitySubGroup_000009",
            activity_subgroup_name="Vital Signs",
            order=1,
        ),
        study_activity_group=SimpleStudyActivityGroup(
            study_activity_group_uid="StudyActivityGroup_000040",
            activity_group_uid="ActivityGroup_000006",
            activity_group_name="Vital Signs",
            order=6,
        ),
        study_soa_group=SimpleStudySoAGroup(
            study_soa_group_uid="StudySoAGroup_000040",
            soa_group_term_uid="CTTerm_000066",
            soa_group_term_name="SUBJECT RELATED INFORMATION",
            order=1,
        ),
        activity=ActivityForStudyActivity(
            start_date=datetime.datetime(2023, 9, 25, 11, 34, 2, 546360),
            end_date=None,
            status="Final",
            version="1.0",
            change_description="Approved version",
            author_username=AUTHOR_USERNAME,
            uid="Activity_000026",
            name="Diastolic Blood Pressure",
            name_sentence_case="diastolic blood pressure",
            synonyms=[],
            definition=None,
            abbreviation=None,
            library_name="Sponsor",
            possible_actions=["inactivate", "new_version"],
            nci_concept_id=None,
            activity_groupings=[
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000006",
                    activity_group_name="Vital Signs",
                    activity_subgroup_uid="ActivitySubGroup_000009",
                    activity_subgroup_name="Vital Signs",
                )
            ],
            request_rationale=None,
            replaced_by_activity=None,
            is_data_collected=False,
        ),
        start_date=datetime.datetime(2023, 9, 26, 21, 44, 47, 302977),
        author_username=AUTHOR_USERNAME,
        end_date=None,
        status=None,
        change_type=None,
        latest_activity=None,
        accepted_version=False,
    ),
    StudySelectionActivity(
        study_uid="Study_000002",
        order=2,
        project_number=None,
        project_name=None,
        show_activity_in_protocol_flowchart=False,
        show_activity_subgroup_in_protocol_flowchart=True,
        show_activity_group_in_protocol_flowchart=True,
        show_soa_group_in_protocol_flowchart=True,
        study_activity_uid="StudyActivity_000041",
        study_activity_subgroup=SimpleStudyActivitySubGroup(
            study_activity_subgroup_uid="StudyActivitySubGroup_000041",
            activity_subgroup_uid="ActivitySubGroup_000016",
            activity_subgroup_name="Informed Consent and Demography",
            order=1,
        ),
        study_activity_group=SimpleStudyActivityGroup(
            study_activity_group_uid="StudyActivityGroup_000041",
            activity_group_uid="ActivityGroup_000010",
            activity_group_name="Informed Consent and Demography",
            order=1,
        ),
        study_soa_group=SimpleStudySoAGroup(
            study_soa_group_uid="StudySoAGroup_000041",
            soa_group_term_uid="CTTerm_000066",
            soa_group_term_name="SUBJECT RELATED INFORMATION",
            order=1,
        ),
        activity=ActivityForStudyActivity(
            start_date=datetime.datetime(2023, 9, 25, 11, 34, 4, 279777),
            end_date=None,
            status="Final",
            version="1.0",
            change_description="Approved version",
            author_username=AUTHOR_USERNAME,
            uid="Activity_000037",
            name="Date of Birth",
            name_sentence_case="date of birth",
            synonyms=[],
            definition=None,
            abbreviation=None,
            library_name="Sponsor",
            possible_actions=["inactivate", "new_version"],
            nci_concept_id=None,
            activity_groupings=[
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000010",
                    activity_group_name="Informed Consent and Demography",
                    activity_subgroup_uid="ActivitySubGroup_000016",
                    activity_subgroup_name="Informed Consent and Demography",
                ),
                ActivityGroupingHierarchySimpleModel(
                    activity_group_uid="ActivityGroup_000009",
                    activity_group_name="Demography",
                    activity_subgroup_uid="ActivitySubGroup_000017",
                    activity_subgroup_name="Demography",
                ),
            ],
            request_rationale=None,
            replaced_by_activity=None,
            is_data_collected=False,
        ),
        start_date=datetime.datetime(2023, 9, 28, 7, 17, 27, 538325),
        author_username=AUTHOR_USERNAME,
        end_date=None,
        status=None,
        change_type=None,
        latest_activity=None,
        accepted_version=False,
    ),
]
STUDY_ACTIVITY_SCHEDULES = [
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000237",
        study_activity_uid="StudyActivity_000033",
        study_activity_name="Informed Consent Obtained",
        study_visit_uid="StudyVisit_000021",
        study_visit_name="Visit 10",
        start_date=datetime.datetime(2023, 9, 28, 12, 16, 13, 789294),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000224",
        study_activity_uid="StudyActivity_000033",
        study_activity_name="Informed Consent Obtained",
        study_visit_uid="StudyVisit_000018",
        study_visit_name="Visit 7",
        start_date=datetime.datetime(2023, 9, 28, 7, 18, 41, 289272),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000223",
        study_activity_uid="StudyActivity_000033",
        study_activity_name="Informed Consent Obtained",
        study_visit_uid="StudyVisit_000017",
        study_visit_name="Visit 6",
        start_date=datetime.datetime(2023, 9, 28, 7, 18, 41, 200554),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000222",
        study_activity_uid="StudyActivity_000033",
        study_activity_name="Informed Consent Obtained",
        study_visit_uid="StudyVisit_000016",
        study_visit_name="Visit 5",
        start_date=datetime.datetime(2023, 9, 28, 7, 18, 41, 106152),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000180",
        study_activity_uid="StudyActivity_000033",
        study_activity_name="Informed Consent Obtained",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 44, 925699),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000167",
        study_activity_uid="StudyActivity_000033",
        study_activity_name="Informed Consent Obtained",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 40, 4090),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000239",
        study_activity_uid="StudyActivity_000041",
        study_activity_name="Date of Birth",
        study_visit_uid="StudyVisit_000013",
        study_visit_name="Visit 2",
        start_date=datetime.datetime(2023, 9, 28, 12, 16, 36, 941563),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000148",
        study_activity_uid="StudyActivity_000041",
        study_activity_name="Date of Birth",
        study_visit_uid="StudyVisit_000014",
        study_visit_name="Visit 3",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 29, 963794),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000174",
        study_activity_uid="StudyActivity_000041",
        study_activity_name="Date of Birth",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 42, 799372),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000150",
        study_activity_uid="StudyActivity_000041",
        study_activity_name="Date of Birth",
        study_visit_uid="StudyVisit_000015",
        study_visit_name="Visit 4",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 30, 666424),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000146",
        study_activity_uid="StudyActivity_000041",
        study_activity_name="Date of Birth",
        study_visit_uid="StudyVisit_000013",
        study_visit_name="Visit 2",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 29, 284104),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000209",
        study_activity_uid="StudyActivity_000041",
        study_activity_name="Date of Birth",
        study_visit_uid="StudyVisit_000017",
        study_visit_name="Visit 6",
        start_date=datetime.datetime(2023, 9, 28, 7, 8, 33, 792658),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000152",
        study_activity_uid="StudyActivity_000041",
        study_activity_name="Date of Birth",
        study_visit_uid="StudyVisit_000016",
        study_visit_name="Visit 5",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 31, 375534),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000186",
        study_activity_uid="StudyActivity_000041",
        study_activity_name="Date of Birth",
        study_visit_uid="StudyVisit_000015",
        study_visit_name="Visit 4",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 47, 957960),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000184",
        study_activity_uid="StudyActivity_000041",
        study_activity_name="Date of Birth",
        study_visit_uid="StudyVisit_000016",
        study_visit_name="Visit 5",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 47, 259826),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000213",
        study_activity_uid="StudyActivity_000041",
        study_activity_name="Date of Birth",
        study_visit_uid="StudyVisit_000018",
        study_visit_name="Visit 7",
        start_date=datetime.datetime(2023, 9, 28, 7, 8, 35, 538906),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000172",
        study_activity_uid="StudyActivity_000041",
        study_activity_name="Date of Birth",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 41, 800992),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000140",
        study_activity_uid="StudyActivity_000041",
        study_activity_name="Date of Birth",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 27, 180162),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000207",
        study_activity_uid="StudyActivity_000041",
        study_activity_name="Date of Birth",
        study_visit_uid="StudyVisit_000017",
        study_visit_name="Visit 6",
        start_date=datetime.datetime(2023, 9, 28, 7, 8, 33, 659383),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000215",
        study_activity_uid="StudyActivity_000041",
        study_activity_name="Date of Birth",
        study_visit_uid="StudyVisit_000018",
        study_visit_name="Visit 7",
        start_date=datetime.datetime(2023, 9, 28, 7, 8, 35, 692353),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000235",
        study_activity_uid="StudyActivity_000040",
        study_activity_name="Diastolic Blood Pressure",
        study_visit_uid="StudyVisit_000021",
        study_visit_name="Visit 10",
        start_date=datetime.datetime(2023, 9, 28, 12, 14, 53, 81287),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000232",
        study_activity_uid="StudyActivity_000040",
        study_activity_name="Diastolic Blood Pressure",
        study_visit_uid="StudyVisit_000019",
        study_visit_name="Visit 8",
        start_date=datetime.datetime(2023, 9, 28, 12, 14, 12, 896228),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000231",
        study_activity_uid="StudyActivity_000040",
        study_activity_name="Diastolic Blood Pressure",
        study_visit_uid="StudyVisit_000018",
        study_visit_name="Visit 7",
        start_date=datetime.datetime(2023, 9, 28, 12, 14, 11, 30893),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000230",
        study_activity_uid="StudyActivity_000040",
        study_activity_name="Diastolic Blood Pressure",
        study_visit_uid="StudyVisit_000017",
        study_visit_name="Visit 6",
        start_date=datetime.datetime(2023, 9, 28, 12, 14, 10, 952933),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000229",
        study_activity_uid="StudyActivity_000040",
        study_activity_name="Diastolic Blood Pressure",
        study_visit_uid="StudyVisit_000016",
        study_visit_name="Visit 5",
        start_date=datetime.datetime(2023, 9, 28, 12, 14, 10, 870893),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000228",
        study_activity_uid="StudyActivity_000040",
        study_activity_name="Diastolic Blood Pressure",
        study_visit_uid="StudyVisit_000014",
        study_visit_name="Visit 3",
        start_date=datetime.datetime(2023, 9, 28, 12, 14, 2, 996469),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000227",
        study_activity_uid="StudyActivity_000040",
        study_activity_name="Diastolic Blood Pressure",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 28, 12, 14, 1, 609735),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000212",
        study_activity_uid="StudyActivity_000039",
        study_activity_name="Systolic Blood Pressure",
        study_visit_uid="StudyVisit_000018",
        study_visit_name="Visit 7",
        start_date=datetime.datetime(2023, 9, 28, 7, 8, 35, 462210),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000210",
        study_activity_uid="StudyActivity_000039",
        study_activity_name="Systolic Blood Pressure",
        study_visit_uid="StudyVisit_000017",
        study_visit_name="Visit 6",
        start_date=datetime.datetime(2023, 9, 28, 7, 8, 33, 886820),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000177",
        study_activity_uid="StudyActivity_000039",
        study_activity_name="Systolic Blood Pressure",
        study_visit_uid="StudyVisit_000013",
        study_visit_name="Visit 2",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 43, 881792),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000145",
        study_activity_uid="StudyActivity_000039",
        study_activity_name="Systolic Blood Pressure",
        study_visit_uid="StudyVisit_000013",
        study_visit_name="Visit 2",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 28, 934309),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000216",
        study_activity_uid="StudyActivity_000039",
        study_activity_name="Systolic Blood Pressure",
        study_visit_uid="StudyVisit_000018",
        study_visit_name="Visit 7",
        start_date=datetime.datetime(2023, 9, 28, 7, 8, 35, 761803),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000187",
        study_activity_uid="StudyActivity_000039",
        study_activity_name="Systolic Blood Pressure",
        study_visit_uid="StudyVisit_000015",
        study_visit_name="Visit 4",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 48, 294076),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000185",
        study_activity_uid="StudyActivity_000039",
        study_activity_name="Systolic Blood Pressure",
        study_visit_uid="StudyVisit_000016",
        study_visit_name="Visit 5",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 47, 610633),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000171",
        study_activity_uid="StudyActivity_000039",
        study_activity_name="Systolic Blood Pressure",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 41, 454736),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000137",
        study_activity_uid="StudyActivity_000039",
        study_activity_name="Systolic Blood Pressure",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 25, 836096),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000206",
        study_activity_uid="StudyActivity_000039",
        study_activity_name="Systolic Blood Pressure",
        study_visit_uid="StudyVisit_000017",
        study_visit_name="Visit 6",
        start_date=datetime.datetime(2023, 9, 28, 7, 8, 33, 595642),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000147",
        study_activity_uid="StudyActivity_000039",
        study_activity_name="Systolic Blood Pressure",
        study_visit_uid="StudyVisit_000014",
        study_visit_name="Visit 3",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 29, 622008),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000163",
        study_activity_uid="StudyActivity_000039",
        study_activity_name="Systolic Blood Pressure",
        study_visit_uid="StudyVisit_000022",
        study_visit_name="Visit 11",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 37, 404001),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000151",
        study_activity_uid="StudyActivity_000039",
        study_activity_name="Systolic Blood Pressure",
        study_visit_uid="StudyVisit_000016",
        study_visit_name="Visit 5",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 31, 24714),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000179",
        study_activity_uid="StudyActivity_000039",
        study_activity_name="Systolic Blood Pressure",
        study_visit_uid="StudyVisit_000014",
        study_visit_name="Visit 3",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 44, 578341),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000181",
        study_activity_uid="StudyActivity_000038",
        study_activity_name="Erythrocytes",
        study_visit_uid="StudyVisit_000015",
        study_visit_name="Visit 4",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 45, 285530),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000139",
        study_activity_uid="StudyActivity_000038",
        study_activity_name="Erythrocytes",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 26, 830628),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000173",
        study_activity_uid="StudyActivity_000038",
        study_activity_name="Erythrocytes",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 42, 455121),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000165",
        study_activity_uid="StudyActivity_000038",
        study_activity_name="Erythrocytes",
        study_visit_uid="StudyVisit_000022",
        study_visit_name="Visit 11",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 38, 392756),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000166",
        study_activity_uid="StudyActivity_000038",
        study_activity_name="Erythrocytes",
        study_visit_uid="StudyVisit_000015",
        study_visit_name="Visit 4",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 39, 653893),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000141",
        study_activity_uid="StudyActivity_000037",
        study_activity_name="Weight",
        study_visit_uid="StudyVisit_000013",
        study_visit_name="Visit 2",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 27, 524314),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000136",
        study_activity_uid="StudyActivity_000037",
        study_activity_name="Weight",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 25, 471663),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000143",
        study_activity_uid="StudyActivity_000037",
        study_activity_name="Weight",
        study_visit_uid="StudyVisit_000019",
        study_visit_name="Visit 8",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 28, 215687),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000142",
        study_activity_uid="StudyActivity_000037",
        study_activity_name="Weight",
        study_visit_uid="StudyVisit_000016",
        study_visit_name="Visit 5",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 27, 860010),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000208",
        study_activity_uid="StudyActivity_000037",
        study_activity_name="Weight",
        study_visit_uid="StudyVisit_000017",
        study_visit_name="Visit 6",
        start_date=datetime.datetime(2023, 9, 28, 7, 8, 33, 734000),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000170",
        study_activity_uid="StudyActivity_000037",
        study_activity_name="Weight",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 41, 88442),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000144",
        study_activity_uid="StudyActivity_000037",
        study_activity_name="Weight",
        study_visit_uid="StudyVisit_000022",
        study_visit_name="Visit 11",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 28, 558020),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000211",
        study_activity_uid="StudyActivity_000037",
        study_activity_name="Weight",
        study_visit_uid="StudyVisit_000018",
        study_visit_name="Visit 7",
        start_date=datetime.datetime(2023, 9, 28, 7, 8, 35, 385759),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000176",
        study_activity_uid="StudyActivity_000037",
        study_activity_name="Weight",
        study_visit_uid="StudyVisit_000016",
        study_visit_name="Visit 5",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 43, 507686),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000205",
        study_activity_uid="StudyActivity_000037",
        study_activity_name="Weight",
        study_visit_uid="StudyVisit_000017",
        study_visit_name="Visit 6",
        start_date=datetime.datetime(2023, 9, 28, 7, 8, 33, 509835),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000214",
        study_activity_uid="StudyActivity_000037",
        study_activity_name="Weight",
        study_visit_uid="StudyVisit_000018",
        study_visit_name="Visit 7",
        start_date=datetime.datetime(2023, 9, 28, 7, 8, 35, 607005),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000175",
        study_activity_uid="StudyActivity_000037",
        study_activity_name="Weight",
        study_visit_uid="StudyVisit_000013",
        study_visit_name="Visit 2",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 43, 151406),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000221",
        study_activity_uid="StudyActivity_000036",
        study_activity_name="Height",
        study_visit_uid="StudyVisit_000020",
        study_visit_name="Visit 9",
        start_date=datetime.datetime(2023, 9, 28, 7, 18, 20, 595234),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000169",
        study_activity_uid="StudyActivity_000036",
        study_activity_name="Height",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 40, 711597),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000220",
        study_activity_uid="StudyActivity_000036",
        study_activity_name="Height",
        study_visit_uid="StudyVisit_000014",
        study_visit_name="Visit 3",
        start_date=datetime.datetime(2023, 9, 28, 7, 18, 16, 760068),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000219",
        study_activity_uid="StudyActivity_000035",
        study_activity_name="Medical History/Concomitant Illness",
        study_visit_uid="StudyVisit_000022",
        study_visit_name="Visit 11",
        start_date=datetime.datetime(2023, 9, 28, 7, 17, 58, 133816),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000218",
        study_activity_uid="StudyActivity_000035",
        study_activity_name="Medical History/Concomitant Illness",
        study_visit_uid="StudyVisit_000013",
        study_visit_name="Visit 2",
        start_date=datetime.datetime(2023, 9, 28, 7, 17, 53, 408971),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000217",
        study_activity_uid="StudyActivity_000035",
        study_activity_name="Medical History/Concomitant Illness",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 28, 7, 17, 50, 576524),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000134",
        study_activity_uid="StudyActivity_000034",
        study_activity_name="Eligibility Criteria Met",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 24, 778118),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
    StudyActivitySchedule(
        study_uid="Study_000002",
        study_activity_schedule_uid="StudyActivitySchedule_000168",
        study_activity_uid="StudyActivity_000034",
        study_activity_name="Eligibility Criteria Met",
        study_visit_uid="StudyVisit_000012",
        study_visit_name="Visit 1",
        start_date=datetime.datetime(2023, 9, 25, 11, 42, 40, 366106),
        author_username=AUTHOR_USERNAME,
        end_date=None,
    ),
]
COORDINATES = {
    "StudyEpoch_000004": (0, 1),
    "StudyVisit_000012": (1, 1),
    "StudyEpoch_000005": (0, 2),
    "StudyVisit_000013": (1, 2),
    "StudyVisit_000014": (1, 3),
    "StudyVisit_000015": (1, 4),
    "StudyEpoch_000006": (0, 5),
    "StudyVisit_000016": (1, 5),
    "StudyVisit_000017": (1, 5),
    "StudyVisit_000018": (1, 5),
    "StudyEpoch_000007": (0, 6),
    "StudyVisit_000019": (1, 6),
    "StudyVisit_000020": (1, 7),
    "StudyVisit_000021": (1, 8),
    "StudyEpoch_000008": (0, 9),
    "StudyVisit_000022": (1, 9),
    "StudyEpoch_000009": (0, 10),
    "StudyVisit_000023": (1, 10),
    "StudyVisit_000024": (1, 11),
    "StudySoAGroup_000033": (4, 0),
    "StudyActivityGroup_000033": (5, 0),
    "StudyActivitySubGroup_000033": (6, 0),
    "StudyActivity_000033": (7, 0),
    "StudyActivitySchedule_000167": (7, 1),
    "StudyActivitySchedule_000222": (7, 5),
    "StudyActivitySchedule_000223": (7, 5),
    "StudyActivitySchedule_000224": (7, 5),
    "StudyActivitySchedule_000237": (7, 8),
    "StudySoAGroup_000034": (4, 0),
    "StudyActivityGroup_000034": (8, 0),
    "StudyActivitySubGroup_000034": (9, 0),
    "StudyActivity_000034": (10, 0),
    "StudyActivitySchedule_000168": (10, 1),
    "StudySoAGroup_000035": (4, 0),
    "StudyActivityGroup_000035": (11, 0),
    "StudyActivitySubGroup_000035": (12, 0),
    "StudyActivity_000035": (13, 0),
    "StudyActivitySchedule_000217": (13, 1),
    "StudyActivitySchedule_000218": (13, 2),
    "StudyActivitySchedule_000219": (13, 9),
    "StudySoAGroup_000036": (4, 0),
    "StudyActivityGroup_000036": (14, 0),
    "StudyActivitySubGroup_000036": (15, 0),
    "StudyActivity_000036": (16, 0),
    "StudyActivitySchedule_000169": (16, 1),
    "StudyActivitySchedule_000220": (16, 3),
    "StudyActivitySchedule_000221": (16, 7),
    "StudySoAGroup_000037": (4, 0),
    "StudyActivityGroup_000037": (14, 0),
    "StudyActivitySubGroup_000037": (15, 0),
    "StudyActivity_000037": (17, 0),
    "StudyActivitySchedule_000170": (17, 1),
    "StudyActivitySchedule_000175": (17, 2),
    "StudyActivitySchedule_000176": (17, 5),
    "StudyActivitySchedule_000205": (17, 5),
    "StudyActivitySchedule_000214": (17, 5),
    "StudyActivitySchedule_000143": (17, 6),
    "StudyActivitySchedule_000144": (17, 9),
    "StudySoAGroup_000038": (4, 0),
    "StudyActivityGroup_000038": (18, 0),
    "StudyActivitySubGroup_000038": (19, 0),
    "StudyActivity_000038": (20, 0),
    "StudyActivitySchedule_000173": (20, 1),
    "StudyActivitySchedule_000166": (20, 4),
    "StudyActivitySchedule_000165": (20, 9),
    "StudySoAGroup_000039": (4, 0),
    "StudyActivityGroup_000039": (21, 0),
    "StudyActivitySubGroup_000039": (22, 0),
    "StudyActivity_000039": (23, 0),
    "StudyActivitySchedule_000137": (23, 1),
    "StudyActivitySchedule_000145": (23, 2),
    "StudyActivitySchedule_000179": (23, 3),
    "StudyActivitySchedule_000187": (23, 4),
    "StudyActivitySchedule_000151": (23, 5),
    "StudyActivitySchedule_000206": (23, 5),
    "StudyActivitySchedule_000216": (23, 5),
    "StudyActivitySchedule_000163": (23, 9),
    "StudySoAGroup_000040": (4, 0),
    "StudyActivityGroup_000040": (21, 0),
    "StudyActivitySubGroup_000040": (22, 0),
    "StudyActivity_000040": (24, 0),
    "StudyActivitySchedule_000227": (24, 1),
    "StudyActivitySchedule_000228": (24, 3),
    "StudyActivitySchedule_000229": (24, 5),
    "StudyActivitySchedule_000230": (24, 5),
    "StudyActivitySchedule_000231": (24, 5),
    "StudyActivitySchedule_000232": (24, 6),
    "StudyActivitySchedule_000235": (24, 8),
    "StudySoAGroup_000041": (4, 0),
    "StudyActivityGroup_000041": (25, 0),
    "StudyActivitySubGroup_000041": (26, 0),
    "StudyActivity_000041": (27, 0),
    "StudyActivitySchedule_000140": (27, 1),
    "StudyActivitySchedule_000146": (27, 2),
    "StudyActivitySchedule_000148": (27, 3),
    "StudyActivitySchedule_000186": (27, 4),
    "StudyActivitySchedule_000184": (27, 5),
    "StudyActivitySchedule_000207": (27, 5),
    "StudyActivitySchedule_000215": (27, 5),
}
FOOTNOTES: list[StudySoAFootnote] = [
    StudySoAFootnote(
        uid="StudySoAFootnote_000011",
        study_uid="Study_000002",
        order=1,
        modified=datetime.datetime(2023, 9, 28, 14, 2, 41, 550812),
        referenced_items=[
            ReferencedItem(
                item_uid="StudyEpoch_000004",
                item_name="Screening",
                item_type=SoAItemType.STUDY_EPOCH,
            ),
            ReferencedItem(
                item_uid="StudyVisit_000015",
                item_name="V4",
                item_type=SoAItemType.STUDY_VISIT,
            ),
        ],
        footnote=Footnote(
            uid="Footnote_000011",
            name="<p>The beginning is the most important part of the work</p>",
            name_plain="The beginning is the most important part of the work",
            start_date=datetime.datetime(2023, 9, 26, 21, 42, 25, 947953),
            end_date=None,
            status="Final",
            version="1.0",
            change_description="Approved version",
            author_username=AUTHOR_USERNAME,
            possible_actions=["inactivate"],
            footnote_template=FootnoteTemplateWithType(
                name="<p>The beginning is the most important part of the work</p>",
                name_plain="The beginning is the most important part of the work",
                uid="FootnoteTemplate_000012",
                sequence_id="FSA12",
                library_name="User Defined",
                type=None,
            ),
            parameter_terms=[],
            library=Library(name="User Defined", is_editable=True),
            study_count=0,
        ),
        footnote_template=None,
    ),
    StudySoAFootnote(
        uid="StudySoAFootnote_000012",
        study_uid="Study_000002",
        order=2,
        modified=datetime.datetime(2023, 9, 28, 14, 5, 43, 56490),
        referenced_items=[
            ReferencedItem(
                item_uid="StudyActivity_000039",
                item_name="Systolic Blood Pressure",
                item_type=SoAItemType.STUDY_ACTIVITY,
            ),
            ReferencedItem(
                item_uid="StudyActivity_000038",
                item_name="Erythrocytes",
                item_type=SoAItemType.STUDY_ACTIVITY,
            ),
            ReferencedItem(
                item_uid="StudyActivitySubGroup_000036",
                item_name="Body Measurements",
                item_type=SoAItemType.STUDY_ACTIVITY_SUBGROUP,
            ),
            ReferencedItem(
                item_uid="StudyActivitySubGroup_000037",
                item_name="Body Measurements",
                item_type=SoAItemType.STUDY_ACTIVITY_SUBGROUP,
            ),
            ReferencedItem(
                item_uid="StudyActivitySubGroup_000038",
                item_name="Haematology",
                item_type=SoAItemType.STUDY_ACTIVITY_SUBGROUP,
            ),
            ReferencedItem(
                item_uid="StudyActivityGroup_000038",
                item_name="Laboratory Assessments",
                item_type=SoAItemType.STUDY_ACTIVITY_GROUP,
            ),
            ReferencedItem(
                item_uid="StudyVisit_000012",
                item_name="V1",
                item_type=SoAItemType.STUDY_VISIT,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000144",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000147",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
        ],
        footnote=Footnote(
            uid="Footnote_000012",
            name="<p>For a man to conquer himself is the first and nobles of all victories</p>",
            name_plain="For a man to conquer himself is the first and nobles of all victories",
            start_date=datetime.datetime(2023, 9, 26, 21, 43, 13, 45570),
            end_date=None,
            status="Final",
            version="1.0",
            change_description="Approved version",
            author_username=AUTHOR_USERNAME,
            possible_actions=["inactivate"],
            footnote_template=FootnoteTemplateWithType(
                name="<p>For a man to conquer himself is the first and nobles of all victories</p>",
                name_plain="For a man to conquer himself is the first and nobles of all victories",
                uid="FootnoteTemplate_000013",
                sequence_id="FSA13",
                library_name="User Defined",
                type=None,
            ),
            parameter_terms=[],
            library=Library(name="User Defined", is_editable=True),
            study_count=0,
        ),
        footnote_template=None,
    ),
    StudySoAFootnote(
        uid="StudySoAFootnote_000013",
        study_uid="Study_000002",
        order=3,
        modified=datetime.datetime(2023, 9, 28, 14, 5, 13, 667573),
        referenced_items=[
            ReferencedItem(
                item_uid="StudyActivitySchedule_000142",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000176",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000205",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000137",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000175",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000220",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000208",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000214",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000211",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
        ],
        footnote=Footnote(
            uid="Footnote_000013",
            name="<p>Friendship is a single soul dwelling in two bodies</p>",
            name_plain="Friendship is a single soul dwelling in two bodies",
            start_date=datetime.datetime(2023, 9, 26, 21, 43, 48, 36499),
            end_date=None,
            status="Final",
            version="1.0",
            change_description="Approved version",
            author_username=AUTHOR_USERNAME,
            possible_actions=["inactivate"],
            footnote_template=FootnoteTemplateWithType(
                name="<p>Friendship is a single soul dwelling in two bodies</p>",
                name_plain="Friendship is a single soul dwelling in two bodies",
                uid="FootnoteTemplate_000014",
                sequence_id="FSA14",
                library_name="User Defined",
                type=None,
            ),
            parameter_terms=[],
            library=Library(name="User Defined", is_editable=True),
            study_count=0,
        ),
        footnote_template=None,
    ),
    StudySoAFootnote(
        uid="StudySoAFootnote_000014",
        study_uid="Study_000002",
        order=4,
        modified=datetime.datetime(2023, 9, 28, 14, 5, 13, 838614),
        referenced_items=[
            ReferencedItem(
                item_uid="StudyActivity_000039",
                item_name="Systolic Blood Pressure",
                item_type=SoAItemType.STUDY_ACTIVITY,
            ),
            ReferencedItem(
                item_uid="StudyActivitySubGroup_000038",
                item_name="Haematology",
                item_type=SoAItemType.STUDY_ACTIVITY_SUBGROUP,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000221",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000211",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000176",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000142",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000235",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000214",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000208",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000205",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
            ReferencedItem(
                item_uid="StudyActivitySchedule_000145",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
        ],
        footnote=Footnote(
            uid="Footnote_000008",
            name='<p>The best way to predict the future is to create it"</p>',
            name_plain='The best way to predict the future is to create it"',
            start_date=datetime.datetime(2023, 9, 26, 10, 50, 43, 523495),
            end_date=None,
            status="Final",
            version="1.0",
            change_description="Approved version",
            author_username=AUTHOR_USERNAME,
            possible_actions=["inactivate"],
            footnote_template=FootnoteTemplateWithType(
                name='<p>The best way to predict the future is to create it"</p>',
                name_plain='The best way to predict the future is to create it"',
                uid="FootnoteTemplate_000009",
                sequence_id="FSA9",
                library_name="User Defined",
                type=None,
            ),
            parameter_terms=[],
            library=Library(name="User Defined", is_editable=True),
            study_count=0,
        ),
        footnote_template=None,
    ),
]
DETAILED_SOA_TABLE = TableWithFootnotes(
    rows=[
        TableRow(
            cells=[
                TableCell(
                    style="header1",
                ),
                TableCell(
                    text="Screening",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000004")],
                    footnotes=["a"],
                ),
                TableCell(
                    text="Run-in",
                    span=2,
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000005")],
                ),
                TableCell(
                    span=0,
                ),
                TableCell(
                    text="Treatment 1",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000006")],
                ),
                TableCell(
                    text="Treatment 2",
                    span=3,
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000007")],
                ),
                TableCell(
                    span=0,
                ),
                TableCell(
                    span=0,
                ),
                TableCell(
                    text="Follow-up",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000008")],
                ),
            ],
            hide=False,
            order=None,
            level=None,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Visit short name",
                    style="header2",
                ),
                TableCell(
                    text="V1",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000012")],
                    footnotes=["b"],
                ),
                TableCell(
                    text="V2",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000013")],
                ),
                TableCell(
                    text="V4",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000015")],
                    footnotes=["a"],
                ),
                TableCell(
                    text="V5-V7",
                    style="header2",
                    refs=[
                        Ref(type="StudyVisit", uid="StudyVisit_000016"),
                        Ref(type="StudyVisit", uid="StudyVisit_000017"),
                        Ref(type="StudyVisit", uid="StudyVisit_000018"),
                    ],
                ),
                TableCell(
                    text="V8",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000019")],
                ),
                TableCell(
                    text="V9",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000020")],
                ),
                TableCell(
                    text="V10",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000021")],
                ),
                TableCell(
                    text="V11",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000022")],
                ),
            ],
            hide=False,
            order=None,
            level=None,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Study day",
                    style="header3",
                ),
                TableCell(
                    text="-14",
                    style="header3",
                ),
                TableCell(
                    text="-3",
                    style="header3",
                ),
                TableCell(
                    text="-1",
                    style="header3",
                ),
                TableCell(
                    text="1-5",
                    style="header3",
                ),
                TableCell(
                    text="15",
                    style="header3",
                ),
                TableCell(
                    text="17",
                    style="header3",
                ),
                TableCell(
                    text="19",
                    style="header3",
                ),
                TableCell(
                    text="22",
                    style="header3",
                ),
            ],
            hide=False,
            order=None,
            level=None,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Visit window (days)",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
            ],
            hide=False,
            order=None,
            level=None,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="SUBJECT RELATED INFORMATION",
                    style="soaGroup",
                    refs=[
                        Ref(type="StudySoAGroup", uid="StudySoAGroup_000033"),
                        Ref(type="CTTerm", uid="CTTerm_000066"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=1,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Informed Consent and Demography",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000033"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000010"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Informed Consent and Demography",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000033",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000016"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Informed Consent Obtained",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000033"),
                        Ref(type="Activity", uid="Activity_000059"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000167",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000222",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000223",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000224",
                        ),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000237",
                        )
                    ],
                ),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Eligibility Criteria",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000034"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000011"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=2,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Eligibility Criteria",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000034",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000018"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Eligibility Criteria Met",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000034"),
                        Ref(type="Activity", uid="Activity_000041"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000168",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Medical History/Concomitant Illness",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000035"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000017"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=3,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Medical History/Concomitant Illness",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000035",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000030"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Medical History/Concomitant Illness",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000035"),
                        Ref(type="Activity", uid="Activity_000062"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000217",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000218",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000219",
                        )
                    ],
                ),
            ],
            hide=True,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Body Measurements",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000036"),
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000037"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000005"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=4,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Body Measurements",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000036",
                        ),
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000037",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000010"),
                    ],
                    footnotes=["b"],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Height",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000036"),
                        Ref(type="Activity", uid="Activity_000054"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000169",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000221",
                        )
                    ],
                    footnotes=["d"],
                ),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Weight",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000037"),
                        Ref(type="Activity", uid="Activity_000025"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000170",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000175",
                        )
                    ],
                    footnotes=["c"],
                ),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000176",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000205",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000214",
                        ),
                    ],
                    footnotes=["c", "d"],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000143",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000144",
                        )
                    ],
                    footnotes=["b"],
                ),
            ],
            hide=True,
            order=2,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Laboratory Assessments",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000038"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000004"),
                    ],
                    footnotes=["b"],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=5,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Haematology",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000038",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000021"),
                    ],
                    footnotes=["b", "d"],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Erythrocytes",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000038"),
                        Ref(type="Activity", uid="Activity_000044"),
                    ],
                    footnotes=["b"],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000173",
                        )
                    ],
                ),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000166",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000165",
                        )
                    ],
                ),
            ],
            hide=True,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Vital Signs",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000039"),
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000040"),
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000041"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000006"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=6,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Vital Signs",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000039",
                        ),
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000040",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000009"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Systolic Blood Pressure",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000039"),
                        Ref(type="Activity", uid="Activity_000027"),
                    ],
                    footnotes=["b", "d"],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000137",
                        )
                    ],
                    footnotes=["c"],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000145",
                        )
                    ],
                    footnotes=["d"],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000187",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000151",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000206",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000216",
                        ),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000163",
                        )
                    ],
                ),
            ],
            hide=True,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Diastolic Blood Pressure",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000040"),
                        Ref(type="Activity", uid="Activity_000026"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000227",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000229",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000230",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000231",
                        ),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000232",
                        )
                    ],
                ),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000235",
                        )
                    ],
                    footnotes=["d"],
                ),
                TableCell(),
            ],
            hide=True,
            order=2,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Informed Consent and Demography",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000041",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000016"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Date of Birth",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000041"),
                        Ref(type="Activity", uid="Activity_000037"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000140",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000146",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000186",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000184",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000207",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000215",
                        ),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=2,
            level=4,
        ),
    ],
    footnotes={
        "a": SimpleFootnote(
            uid="StudySoAFootnote_000011",
            text_html="<p>The beginning is the most important part of the work</p>",
            text_plain="The beginning is the most important part of the work",
        ),
        "b": SimpleFootnote(
            uid="StudySoAFootnote_000012",
            text_html="<p>For a man to conquer himself is the first and nobles of all victories</p>",
            text_plain="For a man to conquer himself is the first and nobles of all victories",
        ),
        "c": SimpleFootnote(
            uid="StudySoAFootnote_000013",
            text_html="<p>Friendship is a single soul dwelling in two bodies</p>",
            text_plain="Friendship is a single soul dwelling in two bodies",
        ),
        "d": SimpleFootnote(
            uid="StudySoAFootnote_000014",
            text_html='<p>The best way to predict the future is to create it"</p>',
            text_plain='The best way to predict the future is to create it"',
        ),
    },
    num_header_rows=4,
    num_header_cols=1,
    title="Protocol Flowchart",
    id=None,
)
PROTOCOL_SOA_TABLE = TableWithFootnotes(
    rows=[
        TableRow(
            cells=[
                TableCell(
                    style="header1",
                ),
                TableCell(
                    text="Screening",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000004")],
                    footnotes=["a"],
                ),
                TableCell(
                    text="Run-in",
                    span=2,
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000005")],
                ),
                TableCell(
                    span=0,
                ),
                TableCell(
                    text="Treatment 1",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000006")],
                ),
                TableCell(
                    text="Treatment 2",
                    span=3,
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000007")],
                ),
                TableCell(
                    span=0,
                ),
                TableCell(
                    span=0,
                ),
                TableCell(
                    text="Follow-up",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000008")],
                ),
            ],
            hide=False,
            order=None,
            level=None,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Visit short name",
                    style="header2",
                ),
                TableCell(
                    text="V1",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000012")],
                    footnotes=["b"],
                ),
                TableCell(
                    text="V2",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000013")],
                ),
                TableCell(
                    text="V4",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000015")],
                    footnotes=["a"],
                ),
                TableCell(
                    text="V5-V7",
                    style="header2",
                    refs=[
                        Ref(type="StudyVisit", uid="StudyVisit_000016"),
                        Ref(type="StudyVisit", uid="StudyVisit_000017"),
                        Ref(type="StudyVisit", uid="StudyVisit_000018"),
                    ],
                ),
                TableCell(
                    text="V8",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000019")],
                ),
                TableCell(
                    text="V9",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000020")],
                ),
                TableCell(
                    text="V10",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000021")],
                ),
                TableCell(
                    text="V11",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000022")],
                ),
            ],
            hide=False,
            order=None,
            level=None,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Study day",
                    style="header3",
                ),
                TableCell(
                    text="-14",
                    style="header3",
                ),
                TableCell(
                    text="-3",
                    style="header3",
                ),
                TableCell(
                    text="-1",
                    style="header3",
                ),
                TableCell(
                    text="1-5",
                    style="header3",
                ),
                TableCell(
                    text="15",
                    style="header3",
                ),
                TableCell(
                    text="17",
                    style="header3",
                ),
                TableCell(
                    text="19",
                    style="header3",
                ),
                TableCell(
                    text="22",
                    style="header3",
                ),
            ],
            hide=False,
            order=None,
            level=None,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Visit window (days)",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
            ],
            hide=False,
            order=None,
            level=None,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="SUBJECT RELATED INFORMATION",
                    style="soaGroup",
                    refs=[
                        Ref(type="StudySoAGroup", uid="StudySoAGroup_000033"),
                        Ref(type="CTTerm", uid="CTTerm_000066"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=1,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Informed Consent and Demography",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000033"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000010"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Informed Consent and Demography",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000033",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000016"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Informed Consent Obtained",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000033"),
                        Ref(type="Activity", uid="Activity_000059"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000167",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000222",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000223",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000224",
                        ),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000237",
                        )
                    ],
                ),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Eligibility Criteria",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000034"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000011"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=2,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Eligibility Criteria",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000034",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000018"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Eligibility Criteria Met",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000034"),
                        Ref(type="Activity", uid="Activity_000041"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000168",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Medical History/Concomitant Illness",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000035"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000017"),
                    ],
                ),
                TableCell(
                    text="X",
                ),
                TableCell(
                    text="X",
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                ),
            ],
            hide=False,
            order=3,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Medical History/Concomitant Illness",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000035",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000030"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Medical History/Concomitant Illness",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000035"),
                        Ref(type="Activity", uid="Activity_000062"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000217",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000218",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000219",
                        )
                    ],
                ),
            ],
            hide=True,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Body Measurements",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000036"),
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000037"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000005"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=4,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Body Measurements",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000036",
                        ),
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000037",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000010"),
                    ],
                    footnotes=["b"],
                ),
                TableCell(
                    text="X",
                ),
                TableCell(
                    text="X",
                ),
                TableCell(),
                TableCell(
                    text="X",
                ),
                TableCell(
                    text="X",
                ),
                TableCell(
                    text="X",
                ),
                TableCell(),
                TableCell(
                    text="X",
                ),
            ],
            hide=False,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Height",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000036"),
                        Ref(type="Activity", uid="Activity_000054"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000169",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000221",
                        )
                    ],
                    footnotes=["d"],
                ),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Weight",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000037"),
                        Ref(type="Activity", uid="Activity_000025"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000170",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000175",
                        )
                    ],
                    footnotes=["c"],
                ),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000176",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000205",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000214",
                        ),
                    ],
                    footnotes=["c", "d"],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000143",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000144",
                        )
                    ],
                    footnotes=["b"],
                ),
            ],
            hide=True,
            order=2,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Laboratory Assessments",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000038"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000004"),
                    ],
                    footnotes=["b"],
                ),
                TableCell(
                    text="X",
                ),
                TableCell(),
                TableCell(
                    text="X",
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                ),
            ],
            hide=False,
            order=5,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Haematology",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000038",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000021"),
                    ],
                    footnotes=["b", "d"],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Erythrocytes",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000038"),
                        Ref(type="Activity", uid="Activity_000044"),
                    ],
                    footnotes=["b"],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000173",
                        )
                    ],
                ),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000166",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000165",
                        )
                    ],
                ),
            ],
            hide=True,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Vital Signs",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000039"),
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000040"),
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000041"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000006"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=6,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Vital Signs",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000039",
                        ),
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000040",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000009"),
                    ],
                ),
                TableCell(
                    text="X",
                ),
                TableCell(
                    text="X",
                ),
                TableCell(
                    text="X",
                ),
                TableCell(
                    text="X",
                ),
                TableCell(
                    text="X",
                ),
                TableCell(),
                TableCell(
                    text="X",
                ),
                TableCell(
                    text="X",
                ),
            ],
            hide=False,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Systolic Blood Pressure",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000039"),
                        Ref(type="Activity", uid="Activity_000027"),
                    ],
                    footnotes=["b", "d"],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000137",
                        )
                    ],
                    footnotes=["c"],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000145",
                        )
                    ],
                    footnotes=["d"],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000187",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000151",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000206",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000216",
                        ),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000163",
                        )
                    ],
                ),
            ],
            hide=True,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Diastolic Blood Pressure",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000040"),
                        Ref(type="Activity", uid="Activity_000026"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000227",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000229",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000230",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000231",
                        ),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000232",
                        )
                    ],
                ),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000235",
                        )
                    ],
                    footnotes=["d"],
                ),
                TableCell(),
            ],
            hide=True,
            order=2,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Informed Consent and Demography",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000041",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000016"),
                    ],
                ),
                TableCell(
                    text="X",
                ),
                TableCell(
                    text="X",
                ),
                TableCell(
                    text="X",
                ),
                TableCell(
                    text="X",
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Date of Birth",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000041"),
                        Ref(type="Activity", uid="Activity_000037"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000140",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000146",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000186",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000184",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000207",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000215",
                        ),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=2,
            level=4,
        ),
    ],
    footnotes={
        "a": SimpleFootnote(
            uid="StudySoAFootnote_000011",
            text_html="<p>The beginning is the most important part of the work</p>",
            text_plain="The beginning is the most important part of the work",
        ),
        "b": SimpleFootnote(
            uid="StudySoAFootnote_000012",
            text_html="<p>For a man to conquer himself is the first and nobles of all victories</p>",
            text_plain="For a man to conquer himself is the first and nobles of all victories",
        ),
        "c": SimpleFootnote(
            uid="StudySoAFootnote_000013",
            text_html="<p>Friendship is a single soul dwelling in two bodies</p>",
            text_plain="Friendship is a single soul dwelling in two bodies",
        ),
        "d": SimpleFootnote(
            uid="StudySoAFootnote_000014",
            text_html='<p>The best way to predict the future is to create it"</p>',
            text_plain='The best way to predict the future is to create it"',
        ),
    },
    num_header_rows=4,
    num_header_cols=1,
    title="Protocol Flowchart",
    id=None,
)
PROTOCOL_SOA_TABLE_WITH_REF_PROPAGATION = TableWithFootnotes(
    rows=[
        TableRow(
            cells=[
                TableCell(
                    style="header1",
                ),
                TableCell(
                    text="Screening",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000004")],
                    footnotes=["a"],
                ),
                TableCell(
                    text="Run-in",
                    span=2,
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000005")],
                ),
                TableCell(
                    span=0,
                ),
                TableCell(
                    text="Treatment 1",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000006")],
                ),
                TableCell(
                    text="Treatment 2",
                    span=3,
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000007")],
                ),
                TableCell(
                    span=0,
                ),
                TableCell(
                    span=0,
                ),
                TableCell(
                    text="Follow-up",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000008")],
                ),
            ],
            hide=False,
            order=None,
            level=None,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Visit short name",
                    style="header2",
                ),
                TableCell(
                    text="V1",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000012")],
                    footnotes=["b"],
                ),
                TableCell(
                    text="V2",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000013")],
                ),
                TableCell(
                    text="V4",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000015")],
                    footnotes=["a"],
                ),
                TableCell(
                    text="V5-V7",
                    style="header2",
                    refs=[
                        Ref(type="StudyVisit", uid="StudyVisit_000016"),
                        Ref(type="StudyVisit", uid="StudyVisit_000017"),
                        Ref(type="StudyVisit", uid="StudyVisit_000018"),
                    ],
                ),
                TableCell(
                    text="V8",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000019")],
                ),
                TableCell(
                    text="V9",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000020")],
                ),
                TableCell(
                    text="V10",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000021")],
                ),
                TableCell(
                    text="V11",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000022")],
                ),
            ],
            hide=False,
            order=None,
            level=None,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Study day",
                    style="header3",
                ),
                TableCell(
                    text="-14",
                    style="header3",
                ),
                TableCell(
                    text="-3",
                    style="header3",
                ),
                TableCell(
                    text="-1",
                    style="header3",
                ),
                TableCell(
                    text="1-5",
                    style="header3",
                ),
                TableCell(
                    text="15",
                    style="header3",
                ),
                TableCell(
                    text="17",
                    style="header3",
                ),
                TableCell(
                    text="19",
                    style="header3",
                ),
                TableCell(
                    text="22",
                    style="header3",
                ),
            ],
            hide=False,
            order=None,
            level=None,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Visit window (days)",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
                TableCell(
                    text="0",
                    style="header4",
                ),
            ],
            hide=False,
            order=None,
            level=None,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="SUBJECT RELATED INFORMATION",
                    style="soaGroup",
                    refs=[
                        Ref(type="StudySoAGroup", uid="StudySoAGroup_000033"),
                        Ref(type="CTTerm", uid="CTTerm_000066"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=1,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Informed Consent and Demography",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000033"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000010"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Informed Consent and Demography",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000033",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000016"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Informed Consent Obtained",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000033"),
                        Ref(type="Activity", uid="Activity_000059"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000167",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000222",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000223",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000224",
                        ),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000237",
                        )
                    ],
                ),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Eligibility Criteria",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000034"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000011"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=2,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Eligibility Criteria",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000034",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000018"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Eligibility Criteria Met",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000034"),
                        Ref(type="Activity", uid="Activity_000041"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000168",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Medical History/Concomitant Illness",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000035"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000017"),
                    ],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000217",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000218",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000219",
                        )
                    ],
                ),
            ],
            hide=False,
            order=3,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Medical History/Concomitant Illness",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000035",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000030"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Medical History/Concomitant Illness",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000035"),
                        Ref(type="Activity", uid="Activity_000062"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000217",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000218",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000219",
                        )
                    ],
                ),
            ],
            hide=True,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Body Measurements",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000036"),
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000037"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000005"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=4,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Body Measurements",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000036",
                        ),
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000037",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000010"),
                    ],
                    footnotes=["b"],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000169",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000170",
                        ),
                    ],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000175",
                        )
                    ],
                ),
                TableCell(),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000176",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000205",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000214",
                        ),
                    ],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000143",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000221",
                        )
                    ],
                ),
                TableCell(),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000144",
                        )
                    ],
                ),
            ],
            hide=False,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Height",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000036"),
                        Ref(type="Activity", uid="Activity_000054"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000169",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000221",
                        )
                    ],
                    footnotes=["d"],
                ),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Weight",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000037"),
                        Ref(type="Activity", uid="Activity_000025"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000170",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000175",
                        )
                    ],
                    footnotes=["c"],
                ),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000176",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000205",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000214",
                        ),
                    ],
                    footnotes=["c", "d"],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000143",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000144",
                        )
                    ],
                    footnotes=["b"],
                ),
            ],
            hide=True,
            order=2,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Laboratory Assessments",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000038"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000004"),
                    ],
                    footnotes=["b"],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000173",
                        )
                    ],
                ),
                TableCell(),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000166",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000165",
                        )
                    ],
                ),
            ],
            hide=False,
            order=5,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Haematology",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000038",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000021"),
                    ],
                    footnotes=["b", "d"],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Erythrocytes",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000038"),
                        Ref(type="Activity", uid="Activity_000044"),
                    ],
                    footnotes=["b"],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000173",
                        )
                    ],
                ),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000166",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000165",
                        )
                    ],
                ),
            ],
            hide=True,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Vital Signs",
                    style="group",
                    refs=[
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000039"),
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000040"),
                        Ref(type="StudyActivityGroup", uid="StudyActivityGroup_000041"),
                        Ref(type="ActivityGroup", uid="ActivityGroup_000006"),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=6,
            level=2,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Vital Signs",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000039",
                        ),
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000040",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000009"),
                    ],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000137",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000227",
                        ),
                    ],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000145",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000187",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000151",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000206",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000216",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000229",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000230",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000231",
                        ),
                    ],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000232",
                        )
                    ],
                ),
                TableCell(),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000235",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000163",
                        )
                    ],
                ),
            ],
            hide=False,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Systolic Blood Pressure",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000039"),
                        Ref(type="Activity", uid="Activity_000027"),
                    ],
                    footnotes=["b", "d"],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000137",
                        )
                    ],
                    footnotes=["c"],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000145",
                        )
                    ],
                    footnotes=["d"],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000187",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000151",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000206",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000216",
                        ),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000163",
                        )
                    ],
                ),
            ],
            hide=True,
            order=1,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Diastolic Blood Pressure",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000040"),
                        Ref(type="Activity", uid="Activity_000026"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000227",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000229",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000230",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000231",
                        ),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000232",
                        )
                    ],
                ),
                TableCell(),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000235",
                        )
                    ],
                    footnotes=["d"],
                ),
                TableCell(),
            ],
            hide=True,
            order=2,
            level=4,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Informed Consent and Demography",
                    style="subGroup",
                    refs=[
                        Ref(
                            type="StudyActivitySubGroup",
                            uid="StudyActivitySubGroup_000041",
                        ),
                        Ref(type="ActivitySubGroup", uid="ActivitySubGroup_000016"),
                    ],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000140",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000146",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000186",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000184",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000207",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000215",
                        ),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=False,
            order=1,
            level=3,
        ),
        TableRow(
            cells=[
                TableCell(
                    text="Date of Birth",
                    style="activity",
                    refs=[
                        Ref(type="StudyActivity", uid="StudyActivity_000041"),
                        Ref(type="Activity", uid="Activity_000037"),
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000140",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000146",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000186",
                        )
                    ],
                ),
                TableCell(
                    text="X",
                    style="activitySchedule",
                    refs=[
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000184",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000207",
                        ),
                        Ref(
                            type="StudyActivitySchedule",
                            uid="StudyActivitySchedule_000215",
                        ),
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            hide=True,
            order=2,
            level=4,
        ),
    ],
    footnotes={
        "a": SimpleFootnote(
            uid="StudySoAFootnote_000011",
            text_html="<p>The beginning is the most important part of the work</p>",
            text_plain="The beginning is the most important part of the work",
        ),
        "b": SimpleFootnote(
            uid="StudySoAFootnote_000012",
            text_html="<p>For a man to conquer himself is the first and nobles of all victories</p>",
            text_plain="For a man to conquer himself is the first and nobles of all victories",
        ),
        "c": SimpleFootnote(
            uid="StudySoAFootnote_000013",
            text_html="<p>Friendship is a single soul dwelling in two bodies</p>",
            text_plain="Friendship is a single soul dwelling in two bodies",
        ),
        "d": SimpleFootnote(
            uid="StudySoAFootnote_000014",
            text_html='<p>The best way to predict the future is to create it"</p>',
            text_plain='The best way to predict the future is to create it"',
        ),
    },
    num_header_rows=4,
    num_header_cols=1,
    title="Protocol Flowchart",
    id=None,
)
ADD_PROTOCOL_SECTION_COLUMN_CASE1 = (
    TableWithFootnotes(
        rows=[
            TableRow(
                cells=[
                    TableCell(),
                    TableCell("A", style="header1"),
                    TableCell("B"),
                    TableCell("C", style="header1"),
                ]
            ),
            TableRow(
                cells=[TableCell("Z"), TableCell("a"), TableCell("b"), TableCell("c")]
            ),
            TableRow(
                cells=[
                    TableCell(""),
                    TableCell("aa", span=2),
                    TableCell(span=0),
                    TableCell("cc"),
                ]
            ),
            TableRow(
                cells=[
                    TableCell("x1"),
                    TableCell("a x1"),
                    TableCell("b x 1"),
                    TableCell(),
                ]
            ),
            TableRow(
                cells=[
                    TableCell("x 2"),
                    TableCell("2 x a"),
                    TableCell(),
                    TableCell("x2 c"),
                ]
            ),
        ],
        num_header_rows=3,
        num_header_cols=2,
    ),
    TableWithFootnotes(
        rows=[
            TableRow(
                cells=[
                    TableCell(),
                    TableCell("A", style="header1"),
                    TableCell("Protocol Section", style="header1"),
                    TableCell("B"),
                    TableCell("C", style="header1"),
                ]
            ),
            TableRow(
                cells=[
                    TableCell("Z"),
                    TableCell("a"),
                    TableCell(),
                    TableCell("b"),
                    TableCell("c"),
                ],
            ),
            TableRow(
                cells=[
                    TableCell(""),
                    TableCell("aa", span=2),
                    TableCell(),
                    TableCell(span=0),
                    TableCell("cc"),
                ]
            ),
            TableRow(
                cells=[
                    TableCell("x1"),
                    TableCell("a x1"),
                    TableCell(),
                    TableCell("b x 1"),
                    TableCell(),
                ]
            ),
            TableRow(
                cells=[
                    TableCell("x 2"),
                    TableCell("2 x a"),
                    TableCell(),
                    TableCell(),
                    TableCell("x2 c"),
                ]
            ),
        ],
        num_header_rows=3,
        num_header_cols=2,
    ),
)
ADD_PROTOCOL_SECTION_COLUMN_CASE2 = (
    TableWithFootnotes(
        rows=[
            TableRow(cells=[TableCell("A"), TableCell("B"), TableCell("C")]),
            TableRow(cells=[TableCell("a"), TableCell("b"), TableCell("c")]),
            TableRow(cells=[TableCell("aa"), TableCell("bb"), TableCell("cc")]),
        ],
        num_header_rows=1,
        num_header_cols=0,
    ),
    TableWithFootnotes(
        rows=[
            TableRow(
                cells=[
                    TableCell("Protocol Section", style="header1"),
                    TableCell("A"),
                    TableCell("B"),
                    TableCell("C"),
                ]
            ),
            TableRow(
                cells=[TableCell(), TableCell("a"), TableCell("b"), TableCell("c")]
            ),
            TableRow(
                cells=[TableCell(), TableCell("aa"), TableCell("bb"), TableCell("cc")]
            ),
        ],
        num_header_rows=1,
        num_header_cols=0,
    ),
)
ADD_PROTOCOL_SECTION_COLUMN_CASE3 = (
    TableWithFootnotes(
        rows=[
            TableRow(cells=[TableCell("A"), TableCell("B"), TableCell("C")]),
            TableRow(cells=[TableCell("a"), TableCell("b"), TableCell("c")]),
            TableRow(cells=[TableCell("aa"), TableCell("bb"), TableCell("cc")]),
        ],
        num_header_rows=0,
        num_header_cols=1,
    ),
    TableWithFootnotes(
        rows=[
            TableRow(
                cells=[
                    TableCell("A"),
                    TableCell("Protocol Section", style="header1"),
                    TableCell("B"),
                    TableCell("C"),
                ]
            ),
            TableRow(
                cells=[TableCell("a"), TableCell(), TableCell("b"), TableCell("c")]
            ),
            TableRow(
                cells=[TableCell("aa"), TableCell(), TableCell("bb"), TableCell("cc")]
            ),
        ],
        num_header_rows=0,
        num_header_cols=1,
    ),
)
