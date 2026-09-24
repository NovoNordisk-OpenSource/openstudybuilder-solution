# pylint: disable=too-many-lines

import datetime

from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityForStudyActivity,
    ActivityGroupingHierarchySimpleModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameWithConflictFlag,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    ReferencedItem,
    SimpleStudyActivityGroup,
    SimpleStudyActivitySubGroup,
    SimpleStudySoAGroup,
    StudyActivitySchedule,
    StudySelectionActivity,
)
from clinical_mdr_api.models.study_selections.study_soa_footnote import (
    CompactFootnote,
    StudySoAFootnote,
)
from clinical_mdr_api.models.study_selections.study_visit import StudyVisitLite
from clinical_mdr_api.services.utils.table_f import (
    Ref,
    SimpleFootnote,
    TableCell,
    TableRow,
    TableWithFootnotes,
)
from common.config import settings
from common.utils import VisitClass, VisitSubclass

AUTHOR_USERNAME = "unknown-user"

STUDY_VISITS = [
    StudyVisitLite(
        uid="StudyVisit_000012",
        consecutive_visit_group=None,
        consecutive_visit_group_uid=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        study_epoch_uid="StudyEpoch_000004",
        study_epoch=SimpleCTTermNameWithConflictFlag(
            term_uid="C48262_SCREENING",
            sponsor_preferred_name="Screening",
        ),
        study_day_number=-14,
        study_duration_days=-15,
        study_week_number=-2,
        study_duration_weeks=-3,
        visit_number=1.0,
        unique_visit_number=100,
        visit_short_name="V1",
        visit_window_unit_name="days",
        visit_class=VisitClass.SINGLE_VISIT,
        visit_subclass=VisitSubclass.SINGLE_VISIT,
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        visit_type=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_000182",
            sponsor_preferred_name="Screening",
        ),
    ),
    StudyVisitLite(
        uid="StudyVisit_000013",
        consecutive_visit_group=None,
        consecutive_visit_group_uid=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        study_epoch_uid="StudyEpoch_000005",
        study_epoch=SimpleCTTermNameWithConflictFlag(
            term_uid="C98779_RUN-IN",
            sponsor_preferred_name="Run-in",
        ),
        study_day_number=-3,
        study_duration_days=-4,
        study_week_number=1,
        study_duration_weeks=0,
        visit_number=2.0,
        unique_visit_number=200,
        visit_short_name="V2",
        visit_window_unit_name="days",
        visit_class=VisitClass.SINGLE_VISIT,
        visit_subclass=VisitSubclass.SINGLE_VISIT,
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        visit_type=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_000184",
            sponsor_preferred_name="Start of run-in",
        ),
    ),
    StudyVisitLite(
        uid="StudyVisit_000014",
        consecutive_visit_group=None,
        consecutive_visit_group_uid=None,
        show_visit=False,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        study_epoch_uid="StudyEpoch_000005",
        study_epoch=SimpleCTTermNameWithConflictFlag(
            term_uid="C98779_RUN-IN",
            sponsor_preferred_name="Run-in",
        ),
        study_day_number=-2,
        study_duration_days=-3,
        study_week_number=1,
        study_duration_weeks=0,
        visit_number=3.0,
        unique_visit_number=300,
        visit_short_name="V3",
        visit_window_unit_name="days",
        visit_class=VisitClass.SINGLE_VISIT,
        visit_subclass=VisitSubclass.SINGLE_VISIT,
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        visit_type=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_000177",
            sponsor_preferred_name="Pre-treatment",
        ),
    ),
    StudyVisitLite(
        uid="StudyVisit_000015",
        consecutive_visit_group=None,
        consecutive_visit_group_uid=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        study_epoch_uid="StudyEpoch_000005",
        study_epoch=SimpleCTTermNameWithConflictFlag(
            term_uid="C98779_RUN-IN",
            sponsor_preferred_name="Run-in",
        ),
        study_day_number=-1,
        study_duration_days=-2,
        study_week_number=1,
        study_duration_weeks=0,
        visit_number=4.0,
        unique_visit_number=400,
        visit_short_name="V4",
        visit_window_unit_name="days",
        visit_class=VisitClass.SINGLE_VISIT,
        visit_subclass=VisitSubclass.SINGLE_VISIT,
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        visit_type=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_000177",
            sponsor_preferred_name="Pre-treatment",
        ),
    ),
    StudyVisitLite(
        uid="StudyVisit_000016",
        consecutive_visit_group="V5-V7",
        consecutive_visit_group_uid="StudyVisitGroup_000007",
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        study_epoch_uid="StudyEpoch_000006",
        study_epoch=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_001163",
            sponsor_preferred_name="Treatment 1",
        ),
        study_day_number=1,
        study_duration_days=0,
        study_week_number=1,
        study_duration_weeks=0,
        visit_number=5.0,
        unique_visit_number=500,
        visit_short_name="V5",
        visit_window_unit_name="days",
        visit_class=VisitClass.SINGLE_VISIT,
        visit_subclass=VisitSubclass.SINGLE_VISIT,
        is_global_anchor_visit=True,
        is_soa_milestone=True,
        visit_type=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_000187",
            sponsor_preferred_name="Treatment",
        ),
    ),
    StudyVisitLite(
        uid="StudyVisit_000017",
        consecutive_visit_group="V5-V7",
        consecutive_visit_group_uid="StudyVisitGroup_000007",
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        study_epoch_uid="StudyEpoch_000006",
        study_epoch=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_001163",
            sponsor_preferred_name="Treatment 1",
        ),
        study_day_number=3,
        study_duration_days=2,
        study_week_number=1,
        study_duration_weeks=0,
        visit_number=6.0,
        unique_visit_number=600,
        visit_short_name="V6",
        visit_window_unit_name="days",
        visit_class=VisitClass.SINGLE_VISIT,
        visit_subclass=VisitSubclass.SINGLE_VISIT,
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        visit_type=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_000187",
            sponsor_preferred_name="Treatment",
        ),
    ),
    StudyVisitLite(
        uid="StudyVisit_000018",
        consecutive_visit_group="V5-V7",
        consecutive_visit_group_uid="StudyVisitGroup_000007",
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        study_epoch_uid="StudyEpoch_000006",
        study_epoch=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_001163",
            sponsor_preferred_name="Treatment 1",
        ),
        study_day_number=5,
        study_duration_days=4,
        study_week_number=1,
        study_duration_weeks=0,
        visit_number=7.0,
        unique_visit_number=700,
        visit_short_name="V7",
        visit_window_unit_name="days",
        visit_class=VisitClass.SINGLE_VISIT,
        visit_subclass=VisitSubclass.SINGLE_VISIT,
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        visit_type=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_000187",
            sponsor_preferred_name="Treatment",
        ),
    ),
    StudyVisitLite(
        uid="StudyVisit_000019",
        consecutive_visit_group=None,
        consecutive_visit_group_uid=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        study_epoch_uid="StudyEpoch_000007",
        study_epoch=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_001162",
            sponsor_preferred_name="Treatment 2",
        ),
        study_day_number=15,
        study_duration_days=14,
        study_week_number=3,
        study_duration_weeks=2,
        visit_number=8.0,
        unique_visit_number=800,
        visit_short_name="V8",
        visit_window_unit_name="days",
        visit_class=VisitClass.SINGLE_VISIT,
        visit_subclass=VisitSubclass.SINGLE_VISIT,
        is_global_anchor_visit=False,
        is_soa_milestone=True,
        visit_type=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_000187",
            sponsor_preferred_name="Treatment",
        ),
    ),
    StudyVisitLite(
        uid="StudyVisit_000020",
        consecutive_visit_group=None,
        consecutive_visit_group_uid=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        study_epoch_uid="StudyEpoch_000007",
        study_epoch=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_001162",
            sponsor_preferred_name="Treatment 2",
        ),
        study_day_number=17,
        study_duration_days=16,
        study_week_number=3,
        study_duration_weeks=2,
        visit_number=9.0,
        unique_visit_number=900,
        visit_short_name="V9",
        visit_window_unit_name="days",
        visit_class=VisitClass.SINGLE_VISIT,
        visit_subclass=VisitSubclass.SINGLE_VISIT,
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        visit_type=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_000187",
            sponsor_preferred_name="Treatment",
        ),
    ),
    StudyVisitLite(
        uid="StudyVisit_000021",
        consecutive_visit_group=None,
        consecutive_visit_group_uid=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        study_epoch_uid="StudyEpoch_000007",
        study_epoch=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_001162",
            sponsor_preferred_name="Treatment 2",
        ),
        study_day_number=19,
        study_duration_days=18,
        study_week_number=3,
        study_duration_weeks=2,
        visit_number=10.0,
        unique_visit_number=1000,
        visit_short_name="V10",
        visit_window_unit_name="days",
        visit_class=VisitClass.SINGLE_VISIT,
        visit_subclass=VisitSubclass.SINGLE_VISIT,
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        visit_type=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_000187",
            sponsor_preferred_name="Treatment",
        ),
    ),
    StudyVisitLite(
        uid="StudyVisit_000022",
        consecutive_visit_group=None,
        consecutive_visit_group_uid=None,
        show_visit=True,
        min_visit_window_value=0,
        max_visit_window_value=0,
        visit_window_unit_uid="UnitDefinition_000364",
        study_epoch_uid="StudyEpoch_000008",
        study_epoch=SimpleCTTermNameWithConflictFlag(
            term_uid="C99158_FOLLOW-UP",
            sponsor_preferred_name="Follow-up",
        ),
        study_day_number=22,
        study_duration_days=21,
        study_week_number=4,
        study_duration_weeks=3,
        visit_number=11.0,
        unique_visit_number=1100,
        visit_short_name="V11",
        visit_window_unit_name="days",
        visit_class=VisitClass.SINGLE_VISIT,
        visit_subclass=VisitSubclass.SINGLE_VISIT,
        is_global_anchor_visit=False,
        is_soa_milestone=True,
        visit_type=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_000175",
            sponsor_preferred_name="Follow-up",
        ),
    ),
    StudyVisitLite(
        uid="StudyVisit_000023",
        consecutive_visit_group=None,
        consecutive_visit_group_uid=None,
        show_visit=True,
        min_visit_window_value=-9999,
        max_visit_window_value=9999,
        visit_window_unit_uid="UnitDefinition_000364",
        study_epoch_uid="StudyEpoch_000009",
        study_epoch=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_000009",
            sponsor_preferred_name="Basic",
        ),
        study_day_number=None,
        study_duration_days=None,
        study_week_number=None,
        study_duration_weeks=None,
        visit_number=settings.unscheduled_visit_number,
        unique_visit_number=settings.unscheduled_visit_number,
        visit_short_name=f"V{settings.unscheduled_visit_number}",
        visit_window_unit_name="days",
        visit_class=VisitClass.UNSCHEDULED_VISIT,
        visit_subclass=VisitSubclass.SINGLE_VISIT,
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        visit_type=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_000192",
            sponsor_preferred_name="Unscheduled",
        ),
    ),
    StudyVisitLite(
        uid="StudyVisit_000024",
        consecutive_visit_group=None,
        consecutive_visit_group_uid=None,
        show_visit=True,
        min_visit_window_value=-9999,
        max_visit_window_value=9999,
        visit_window_unit_uid="UnitDefinition_000364",
        study_epoch_uid="StudyEpoch_000009",
        study_epoch=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_000009",
            sponsor_preferred_name="Basic",
        ),
        study_day_number=None,
        study_duration_days=None,
        study_week_number=None,
        study_duration_weeks=None,
        visit_number=settings.non_visit_number,
        unique_visit_number=settings.non_visit_number,
        visit_short_name=f"V{settings.non_visit_number}",
        visit_window_unit_name="days",
        visit_class=VisitClass.NON_VISIT,
        visit_subclass=VisitSubclass.SINGLE_VISIT,
        is_global_anchor_visit=False,
        is_soa_milestone=False,
        visit_type=SimpleCTTermNameWithConflictFlag(
            term_uid="CTTerm_000190",
            sponsor_preferred_name="Non-visit",
        ),
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
        show_activity_in_protocol_flowchart=True,
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
        study_activity_schedule_uid="StudyActivitySchedule_000237",
        study_activity_uid="StudyActivity_000033",
        study_visit_uid="StudyVisit_000021",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000224",
        study_activity_uid="StudyActivity_000033",
        study_visit_uid="StudyVisit_000018",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000223",
        study_activity_uid="StudyActivity_000033",
        study_visit_uid="StudyVisit_000017",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000222",
        study_activity_uid="StudyActivity_000033",
        study_visit_uid="StudyVisit_000016",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000180",
        study_activity_uid="StudyActivity_000033",
        study_visit_uid="StudyVisit_000012",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000167",
        study_activity_uid="StudyActivity_000033",
        study_visit_uid="StudyVisit_000012",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000239",
        study_activity_uid="StudyActivity_000041",
        study_visit_uid="StudyVisit_000013",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000148",
        study_activity_uid="StudyActivity_000041",
        study_visit_uid="StudyVisit_000014",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000174",
        study_activity_uid="StudyActivity_000041",
        study_visit_uid="StudyVisit_000012",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000150",
        study_activity_uid="StudyActivity_000041",
        study_visit_uid="StudyVisit_000015",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000146",
        study_activity_uid="StudyActivity_000041",
        study_visit_uid="StudyVisit_000013",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000209",
        study_activity_uid="StudyActivity_000041",
        study_visit_uid="StudyVisit_000017",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000152",
        study_activity_uid="StudyActivity_000041",
        study_visit_uid="StudyVisit_000016",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000186",
        study_activity_uid="StudyActivity_000041",
        study_visit_uid="StudyVisit_000015",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000184",
        study_activity_uid="StudyActivity_000041",
        study_visit_uid="StudyVisit_000016",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000213",
        study_activity_uid="StudyActivity_000041",
        study_visit_uid="StudyVisit_000018",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000172",
        study_activity_uid="StudyActivity_000041",
        study_visit_uid="StudyVisit_000012",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000140",
        study_activity_uid="StudyActivity_000041",
        study_visit_uid="StudyVisit_000012",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000207",
        study_activity_uid="StudyActivity_000041",
        study_visit_uid="StudyVisit_000017",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000215",
        study_activity_uid="StudyActivity_000041",
        study_visit_uid="StudyVisit_000018",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000235",
        study_activity_uid="StudyActivity_000040",
        study_visit_uid="StudyVisit_000021",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000232",
        study_activity_uid="StudyActivity_000040",
        study_visit_uid="StudyVisit_000019",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000231",
        study_activity_uid="StudyActivity_000040",
        study_visit_uid="StudyVisit_000018",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000230",
        study_activity_uid="StudyActivity_000040",
        study_visit_uid="StudyVisit_000017",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000229",
        study_activity_uid="StudyActivity_000040",
        study_visit_uid="StudyVisit_000016",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000228",
        study_activity_uid="StudyActivity_000040",
        study_visit_uid="StudyVisit_000014",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000227",
        study_activity_uid="StudyActivity_000040",
        study_visit_uid="StudyVisit_000012",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000212",
        study_activity_uid="StudyActivity_000039",
        study_visit_uid="StudyVisit_000018",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000210",
        study_activity_uid="StudyActivity_000039",
        study_visit_uid="StudyVisit_000017",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000177",
        study_activity_uid="StudyActivity_000039",
        study_visit_uid="StudyVisit_000013",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000145",
        study_activity_uid="StudyActivity_000039",
        study_visit_uid="StudyVisit_000013",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000216",
        study_activity_uid="StudyActivity_000039",
        study_visit_uid="StudyVisit_000018",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000187",
        study_activity_uid="StudyActivity_000039",
        study_visit_uid="StudyVisit_000015",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000185",
        study_activity_uid="StudyActivity_000039",
        study_visit_uid="StudyVisit_000016",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000171",
        study_activity_uid="StudyActivity_000039",
        study_visit_uid="StudyVisit_000012",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000137",
        study_activity_uid="StudyActivity_000039",
        study_visit_uid="StudyVisit_000012",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000206",
        study_activity_uid="StudyActivity_000039",
        study_visit_uid="StudyVisit_000017",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000147",
        study_activity_uid="StudyActivity_000039",
        study_visit_uid="StudyVisit_000014",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000163",
        study_activity_uid="StudyActivity_000039",
        study_visit_uid="StudyVisit_000022",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000151",
        study_activity_uid="StudyActivity_000039",
        study_visit_uid="StudyVisit_000016",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000179",
        study_activity_uid="StudyActivity_000039",
        study_visit_uid="StudyVisit_000014",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000181",
        study_activity_uid="StudyActivity_000038",
        study_visit_uid="StudyVisit_000015",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000139",
        study_activity_uid="StudyActivity_000038",
        study_visit_uid="StudyVisit_000012",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000173",
        study_activity_uid="StudyActivity_000038",
        study_visit_uid="StudyVisit_000012",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000165",
        study_activity_uid="StudyActivity_000038",
        study_visit_uid="StudyVisit_000022",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000166",
        study_activity_uid="StudyActivity_000038",
        study_visit_uid="StudyVisit_000015",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000141",
        study_activity_uid="StudyActivity_000037",
        study_visit_uid="StudyVisit_000013",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000136",
        study_activity_uid="StudyActivity_000037",
        study_visit_uid="StudyVisit_000012",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000143",
        study_activity_uid="StudyActivity_000037",
        study_visit_uid="StudyVisit_000019",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000142",
        study_activity_uid="StudyActivity_000037",
        study_visit_uid="StudyVisit_000016",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000208",
        study_activity_uid="StudyActivity_000037",
        study_visit_uid="StudyVisit_000017",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000170",
        study_activity_uid="StudyActivity_000037",
        study_visit_uid="StudyVisit_000012",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000144",
        study_activity_uid="StudyActivity_000037",
        study_visit_uid="StudyVisit_000022",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000211",
        study_activity_uid="StudyActivity_000037",
        study_visit_uid="StudyVisit_000018",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000176",
        study_activity_uid="StudyActivity_000037",
        study_visit_uid="StudyVisit_000016",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000205",
        study_activity_uid="StudyActivity_000037",
        study_visit_uid="StudyVisit_000017",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000214",
        study_activity_uid="StudyActivity_000037",
        study_visit_uid="StudyVisit_000018",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000175",
        study_activity_uid="StudyActivity_000037",
        study_visit_uid="StudyVisit_000013",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000221",
        study_activity_uid="StudyActivity_000036",
        study_visit_uid="StudyVisit_000020",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000169",
        study_activity_uid="StudyActivity_000036",
        study_visit_uid="StudyVisit_000012",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000220",
        study_activity_uid="StudyActivity_000036",
        study_visit_uid="StudyVisit_000014",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000219",
        study_activity_uid="StudyActivity_000035",
        study_visit_uid="StudyVisit_000022",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000218",
        study_activity_uid="StudyActivity_000035",
        study_visit_uid="StudyVisit_000013",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000217",
        study_activity_uid="StudyActivity_000035",
        study_visit_uid="StudyVisit_000012",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000134",
        study_activity_uid="StudyActivity_000034",
        study_visit_uid="StudyVisit_000012",
    ),
    StudyActivitySchedule(
        study_activity_schedule_uid="StudyActivitySchedule_000168",
        study_activity_uid="StudyActivity_000034",
        study_visit_uid="StudyVisit_000012",
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
        footnote=CompactFootnote(
            uid="Footnote_000011",
            name="<p>The beginning is the most important part of the work</p>",
            name_plain="The beginning is the most important part of the work",
            status="Final",
            version="1.0",
        ),
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
        footnote=CompactFootnote(
            uid="Footnote_000012",
            name="<p>For a man to conquer himself is the first and nobles of all victories</p>",
            name_plain="For a man to conquer himself is the first and nobles of all victories",
            status="Final",
            version="1.0",
        ),
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
        footnote=CompactFootnote(
            uid="Footnote_000013",
            name="<p>Friendship is a single soul dwelling in two bodies</p>",
            name_plain="Friendship is a single soul dwelling in two bodies",
            status="Final",
            version="1.0",
        ),
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
        footnote=CompactFootnote(
            uid="Footnote_000008",
            name='<p>The best way to predict the future is to create it"</p>',
            name_plain='The best way to predict the future is to create it"',
            status="Final",
            version="1.0",
        ),
    ),
    StudySoAFootnote(
        uid="StudySoAFootnote_000007",
        study_uid="Study_000002",
        order=5,
        modified=datetime.datetime(2026, 4, 22, 14, 40, 13, 836174),
        referenced_items=[
            ReferencedItem(
                item_uid="StudyActivitySchedule_000169",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
        ],
        footnote=CompactFootnote(
            uid="Footnote_000017",
            name="<p>Even the smallest paw can leave a <i>constellation</i> on the heart.</p>",
            name_plain="Even the smallest paw can leave a constellation on the heart.",
            status="Final",
            version="2.0",
        ),
    ),
    StudySoAFootnote(
        uid="StudySoAFootnote_000017",
        study_uid="Study_000002",
        order=6,
        modified=datetime.datetime(2026, 4, 22, 14, 41, 33, 134173),
        referenced_items=[
            ReferencedItem(
                item_uid="StudyActivitySchedule_000170",
                item_name=None,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
        ],
        footnote=CompactFootnote(
            uid="Footnote_000009",
            name="<p>When a mouse dares to dance, the house remembers its courage.</p>",
            name_plain="When a mouse dares to dance, the house remembers its courage.",
            status="Final",
            version="1.1",
        ),
    ),
]

DETAILED_SOA_TABLE = TableWithFootnotes(
    rows=[
        TableRow(
            cells=[
                TableCell(style="header1"),
                TableCell(
                    text="Screening",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000004")],
                    footnotes=["a"],
                ),
                TableCell(
                    text="Run-in",
                    style="header1",
                    span=2,
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000005")],
                ),
                TableCell(span=0),
                TableCell(
                    text="Treatment 1",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000006")],
                ),
                TableCell(
                    text="Treatment 2",
                    style="header1",
                    span=3,
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000007")],
                ),
                TableCell(span=0),
                TableCell(span=0),
                TableCell(
                    text="Follow-up",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000008")],
                ),
                TableCell(
                    text="Basic",
                    style="header1",
                    span=2,
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000009")],
                ),
                TableCell(span=0),
            ],
        ),
        TableRow(
            cells=[
                TableCell(text="Visit short name", style="header2"),
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
                TableCell(
                    text="V29500",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000023")],
                ),
                TableCell(
                    text="V29999",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000024")],
                ),
            ],
        ),
        TableRow(
            cells=[
                TableCell(text="Study day", style="header3"),
                TableCell(text="-14", style="header3"),
                TableCell(text="-3", style="header3"),
                TableCell(text="-1", style="header3"),
                TableCell(text="1-5", style="header3"),
                TableCell(text="15", style="header3"),
                TableCell(text="17", style="header3"),
                TableCell(text="19", style="header3"),
                TableCell(text="22", style="header3"),
                TableCell(style="header3"),
                TableCell(style="header3"),
            ],
        ),
        TableRow(
            cells=[
                TableCell(text="Visit window (days)", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(style="header4"),
                TableCell(style="header4"),
            ],
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
                TableCell(),
                TableCell(),
            ],
            level=1,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=2,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=4,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=2,
            order=2,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=4,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=2,
            order=3,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=2,
            order=4,
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
                TableCell(),
                TableCell(),
            ],
            level=3,
            order=1,
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
                    footnotes=["e"],
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=1,
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
                    footnotes=["f"],
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
                TableCell(),
                TableCell(),
            ],
            level=4,
            order=2,
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
                TableCell(),
                TableCell(),
            ],
            level=2,
            order=5,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=2,
            order=6,
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
                TableCell(),
                TableCell(),
            ],
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=2,
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
                TableCell(),
                TableCell(),
            ],
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=2,
        ),
    ],
    num_header_rows=4,
    num_header_cols=1,
    title="Protocol Flowchart",
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
        "e": SimpleFootnote(
            uid="StudySoAFootnote_000007",
            text_html="<p>Even the smallest paw can leave a <i>constellation</i> on the heart.</p>",
            text_plain="Even the smallest paw can leave a constellation on the heart.",
        ),
        "f": SimpleFootnote(
            uid="StudySoAFootnote_000017",
            text_html="<p>When a mouse dares to dance, the house remembers its courage.</p>",
            text_plain="When a mouse dares to dance, the house remembers its courage.",
        ),
    },
)

PROTOCOL_SOA_TABLE = TableWithFootnotes(
    rows=[
        TableRow(
            cells=[
                TableCell(style="header1"),
                TableCell(
                    text="Screening",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000004")],
                    footnotes=["a"],
                ),
                TableCell(
                    text="Run-in",
                    style="header1",
                    span=2,
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000005")],
                ),
                TableCell(span=0),
                TableCell(
                    text="Treatment 1",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000006")],
                ),
                TableCell(
                    text="Treatment 2",
                    style="header1",
                    span=3,
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000007")],
                ),
                TableCell(span=0),
                TableCell(span=0),
                TableCell(
                    text="Follow-up",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000008")],
                ),
                TableCell(
                    text="Basic",
                    style="header1",
                    span=2,
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000009")],
                ),
                TableCell(span=0),
            ],
        ),
        TableRow(
            cells=[
                TableCell(text="Visit short name", style="header2"),
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
                TableCell(
                    text="V29500",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000023")],
                ),
                TableCell(
                    text="V29999",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000024")],
                ),
            ],
        ),
        TableRow(
            cells=[
                TableCell(text="Study day", style="header3"),
                TableCell(text="-14", style="header3"),
                TableCell(text="-3", style="header3"),
                TableCell(text="-1", style="header3"),
                TableCell(text="1-5", style="header3"),
                TableCell(text="15", style="header3"),
                TableCell(text="17", style="header3"),
                TableCell(text="19", style="header3"),
                TableCell(text="22", style="header3"),
                TableCell(style="header3"),
                TableCell(style="header3"),
            ],
        ),
        TableRow(
            cells=[
                TableCell(text="Visit window (days)", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(style="header4"),
                TableCell(style="header4"),
            ],
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
                TableCell(),
                TableCell(),
            ],
            level=1,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=2,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=4,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=2,
            order=2,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=4,
            order=1,
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
                TableCell(text="X"),
                TableCell(text="X"),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(text="X"),
                TableCell(),
                TableCell(),
            ],
            level=2,
            order=3,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=2,
            order=4,
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
                TableCell(text="X"),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(text="X"),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            level=3,
            order=1,
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
                    footnotes=["e"],
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=1,
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
                    footnotes=["f"],
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
                TableCell(),
                TableCell(),
            ],
            level=4,
            order=2,
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
                TableCell(text="X"),
                TableCell(),
                TableCell(text="X"),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(text="X"),
                TableCell(),
                TableCell(),
            ],
            level=2,
            order=5,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=2,
            order=6,
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
                TableCell(text="X"),
                TableCell(text="X"),
                TableCell(text="X"),
                TableCell(text="X"),
                TableCell(text="X"),
                TableCell(),
                TableCell(text="X"),
                TableCell(text="X"),
                TableCell(),
                TableCell(),
            ],
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=2,
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
                TableCell(text="X"),
                TableCell(text="X"),
                TableCell(text="X"),
                TableCell(text="X"),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=2,
        ),
    ],
    num_header_rows=4,
    num_header_cols=1,
    title="Protocol Flowchart",
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
        "e": SimpleFootnote(
            uid="StudySoAFootnote_000007",
            text_html="<p>Even the smallest paw can leave a <i>constellation</i> on the heart.</p>",
            text_plain="Even the smallest paw can leave a constellation on the heart.",
        ),
        "f": SimpleFootnote(
            uid="StudySoAFootnote_000017",
            text_html="<p>When a mouse dares to dance, the house remembers its courage.</p>",
            text_plain="When a mouse dares to dance, the house remembers its courage.",
        ),
    },
)

PROTOCOL_SOA_TABLE_WITH_REF_PROPAGATION = TableWithFootnotes(
    rows=[
        TableRow(
            cells=[
                TableCell(style="header1"),
                TableCell(
                    text="Screening",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000004")],
                    footnotes=["a"],
                ),
                TableCell(
                    text="Run-in",
                    style="header1",
                    span=2,
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000005")],
                ),
                TableCell(span=0),
                TableCell(
                    text="Treatment 1",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000006")],
                ),
                TableCell(
                    text="Treatment 2",
                    style="header1",
                    span=3,
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000007")],
                ),
                TableCell(span=0),
                TableCell(span=0),
                TableCell(
                    text="Follow-up",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000008")],
                ),
                TableCell(
                    text="Basic",
                    style="header1",
                    span=2,
                    refs=[Ref(type="StudyEpoch", uid="StudyEpoch_000009")],
                ),
                TableCell(span=0),
            ],
        ),
        TableRow(
            cells=[
                TableCell(text="Visit short name", style="header2"),
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
                TableCell(
                    text="V29500",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000023")],
                ),
                TableCell(
                    text="V29999",
                    style="header2",
                    refs=[Ref(type="StudyVisit", uid="StudyVisit_000024")],
                ),
            ],
        ),
        TableRow(
            cells=[
                TableCell(text="Study day", style="header3"),
                TableCell(text="-14", style="header3"),
                TableCell(text="-3", style="header3"),
                TableCell(text="-1", style="header3"),
                TableCell(text="1-5", style="header3"),
                TableCell(text="15", style="header3"),
                TableCell(text="17", style="header3"),
                TableCell(text="19", style="header3"),
                TableCell(text="22", style="header3"),
                TableCell(style="header3"),
                TableCell(style="header3"),
            ],
        ),
        TableRow(
            cells=[
                TableCell(text="Visit window (days)", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(text="0", style="header4"),
                TableCell(style="header4"),
                TableCell(style="header4"),
            ],
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
                TableCell(),
                TableCell(),
            ],
            level=1,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=2,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=4,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=2,
            order=2,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=4,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=2,
            order=3,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=2,
            order=4,
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
                            uid="StudyActivitySchedule_000221",
                        )
                    ],
                ),
                TableCell(),
                TableCell(),
                TableCell(),
                TableCell(),
            ],
            level=3,
            order=1,
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
                    footnotes=["e"],
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=1,
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
                    footnotes=["f"],
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
                TableCell(),
                TableCell(),
            ],
            level=4,
            order=2,
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
                TableCell(),
                TableCell(),
            ],
            level=2,
            order=5,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            level=2,
            order=6,
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
                TableCell(),
                TableCell(),
            ],
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=2,
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
                TableCell(),
                TableCell(),
            ],
            level=3,
            order=1,
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
                TableCell(),
                TableCell(),
            ],
            hide=True,
            level=4,
            order=2,
        ),
    ],
    num_header_rows=4,
    num_header_cols=1,
    title="Protocol Flowchart",
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
        "e": SimpleFootnote(
            uid="StudySoAFootnote_000007",
            text_html="<p>Even the smallest paw can leave a <i>constellation</i> on the heart.</p>",
            text_plain="Even the smallest paw can leave a constellation on the heart.",
        ),
        "f": SimpleFootnote(
            uid="StudySoAFootnote_000017",
            text_html="<p>When a mouse dares to dance, the house remembers its courage.</p>",
            text_plain="When a mouse dares to dance, the house remembers its courage.",
        ),
    },
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

TINY_SOA_TABLE = TableWithFootnotes(
    rows=[
        TableRow(
            cells=[
                TableCell(style="header1"),
                TableCell(
                    text="Screening",
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="epoch-4")],
                ),
                TableCell(
                    text="Treatment",
                    span=3,
                    style="header1",
                    refs=[Ref(type="StudyEpoch", uid="epoch-7")],
                    footnotes=["a"],
                ),
                TableCell(span=0),
                TableCell(span=0),
            ],
            hide=False,
        ),
        TableRow(
            cells=[
                TableCell(text="Visits"),
                TableCell(text="V1", refs=[Ref(type="StudyVisit", uid="visit-1")]),
                TableCell(text="V2", refs=[Ref(type="StudyVisit", uid="visit-2")]),
                TableCell(text="V3", refs=[Ref(type="StudyVisit", uid="visit-3")]),
                TableCell(text="V4", refs=[Ref(type="StudyVisit", uid="visit-4")]),
            ]
        ),
        TableRow(
            cells=[
                TableCell(text="Study day", style="header3"),
                TableCell(text="-14", style="header3"),
                TableCell(text="1", style="header3"),
                TableCell(text="5", style="header3"),
                TableCell(text="4", style="header3"),
            ],
        ),
        TableRow(
            cells=[
                TableCell(text="Visit window (days)", style="header4"),
                TableCell(text="1", style="header4"),
                TableCell(text="-2/+3", style="header4"),
                TableCell(text="-1/0", style="header4"),
                TableCell(text="±2", style="header4"),
            ],
        ),
        TableRow(
            cells=[
                TableCell(text="Activity-one"),
                TableCell(text="X", footnotes=["a"]),
                TableCell(text=""),
                TableCell(text="X"),
                TableCell(text="", footnotes=["a"]),
            ]
        ),
    ],
    num_header_rows=4,
    num_header_cols=1,
    title="Study Flowchart",
    id="soa-1",
    footnotes={
        "a": SimpleFootnote(
            uid="footnote-01",
            text_html="<p>The beginning is the most important part of the work</p>",
            text_plain="The beginning is the most important part of the work",
        ),
        "b": SimpleFootnote(
            uid="footnote-12",
            text_html="<p>For a man to conquer himself is the first and nobles of all victories</p>",
            text_plain="For a man to conquer himself is the first and nobles of all victories",
        ),
    },
)
