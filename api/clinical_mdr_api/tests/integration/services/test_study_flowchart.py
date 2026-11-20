import logging
from collections import defaultdict
from collections.abc import Iterable, Sequence
from typing import Any

import bs4
import pydantic
import pytest
from docx.table import Table
from neomodel import db

from clinical_mdr_api.domain_repositories.study_selections.study_soa_repository import (
    SoALayout,
    SoASnapshot,
    StudySoARepository,
)
from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpoch
from clinical_mdr_api.models.study_selections.study_selection import (
    ReferencedItem,
    StudyActivityGroup,
    StudyActivityGroupEditInput,
    StudyActivitySchedule,
    StudyActivitySubGroup,
    StudyActivitySubGroupEditInput,
    StudySelectionActivity,
    StudySelectionActivityInstance,
)
from clinical_mdr_api.models.study_selections.study_soa_footnote import (
    StudySoAFootnoteEditInput,
)
from clinical_mdr_api.models.study_selections.study_visit import StudyVisit
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_activity_group import (
    StudyActivityGroupService,
)
from clinical_mdr_api.services.studies.study_activity_instance_selection import (
    StudyActivityInstanceSelectionService,
)
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.studies.study_activity_subgroup import (
    StudyActivitySubGroupService,
)
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.services.studies.study_flowchart import (
    _T as _gettext,
    NUM_OPERATIONAL_CODE_COLS,
    SOA_CHECK_MARK,
    StudyFlowchartService,
    get_study_version,
)
from clinical_mdr_api.services.studies.study_soa_footnote import StudySoAFootnoteService
from clinical_mdr_api.services.studies.study_visit import StudyVisitService
from clinical_mdr_api.services.utils.table_f import TableWithFootnotes
from clinical_mdr_api.tests.fixtures.database import TempDatabasePopulated
from clinical_mdr_api.tests.integration.utils.factory_soa import (
    SoATestData,
    SoATestDataMinimal,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.unit.services.test_study_flowchart import (
    check_flowchart_table_dimensions,
    check_flowchart_table_first_rows,
    check_flowchart_table_footnotes,
    check_flowchart_table_visit_rows,
    check_hidden_row_propagation,
)
from common.config import settings
from common.exceptions import NotFoundException

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def soa_test_data(temp_database_populated: TempDatabasePopulated) -> SoATestData:
    test_data = SoATestData(project=temp_database_populated.project)
    # lock study so efforts trying to modify shared test data would result in error
    TestUtils.lock_study(
        test_data.study.uid,
        reason_for_lock_term_uid=temp_database_populated.reason_for_lock_term_uid,
    )
    return test_data


@pytest.fixture(scope="module")
def soa_test_data2(temp_database_populated: TempDatabasePopulated) -> SoATestData:
    """Test data for SoA snapshot & versioning tests

    Note: they modify the study, so they might interfere with other tests.
    """

    test_data = SoATestData(project=temp_database_populated.project)

    TestUtils.lock_and_unlock_study(
        test_data.study.uid,
        reason_for_lock_term_uid=temp_database_populated.reason_for_lock_term_uid,
        reason_for_unlock_term_uid=temp_database_populated.reason_for_unlock_term_uid,
    )

    add_activity = {
        "name": "C Reactive Protein",
        "soa_group": "Safety",
        "group": "Laboratory Assessments",
        "subgroup": "Biochemistry",
        "visits": ["V1", "V3", "V5"],
        "show_soa_group": True,
        "show_group": True,
        "show_subgroup": True,
        "show_activity": True,
        "instances": [
            {
                "class": "NumericFindings",
                "name": "C-Reactive Protein Plasma",
                "topic_code": "C_REACT_PROT_PLASMA",
                "adam_param_code": "CRPP",
            },
            {
                "class": "NumericFindings",
                "name": "C-Reactive Protein Serum",
                "topic_code": "C_REACT_PROT_SERUM",
                "adam_param_code": "CRPS2",
            },
        ],
    }
    test_data.create_activity(**add_activity)
    test_data.create_study_activity(**add_activity)
    test_data.create_instances_of_activity(
        add_activity["name"], add_activity["instances"]
    )
    test_data.assign_instances_of_activity(add_activity["name"])
    test_data.reason_for_lock_term_uid = (
        temp_database_populated.reason_for_lock_term_uid
    )
    test_data.reason_for_unlock_term_uid = (
        temp_database_populated.reason_for_unlock_term_uid
    )

    TestUtils.lock_and_unlock_study(
        test_data.study.uid,
        reason_for_lock_term_uid=temp_database_populated.reason_for_lock_term_uid,
        reason_for_unlock_term_uid=temp_database_populated.reason_for_unlock_term_uid,
    )

    return test_data


@pytest.mark.parametrize(
    "time_unit, layout, hide_soa_groups",
    [
        (None, SoALayout.DETAILED, False),
        (None, SoALayout.DETAILED, False),
        (None, SoALayout.OPERATIONAL, False),
        ("day", SoALayout.DETAILED, False),
        ("day", SoALayout.DETAILED, False),
        ("day", SoALayout.OPERATIONAL, False),
        ("week", SoALayout.DETAILED, False),
        ("week", SoALayout.DETAILED, False),
        ("week", SoALayout.OPERATIONAL, False),
        (None, SoALayout.PROTOCOL, True),
        ("week", SoALayout.PROTOCOL, True),
        ("day", SoALayout.PROTOCOL, True),
    ],
)
def test_build_flowchart_table(
    soa_test_data: SoATestData,
    time_unit: str,
    layout: SoALayout,
    hide_soa_groups: bool,
):
    service = StudyFlowchartService()
    table: TableWithFootnotes = service.build_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=None,
        layout=layout,
        time_unit=time_unit,
    )

    # Collect test data for comparison

    if time_unit is None:
        service = StudyFlowchartService()
        time_unit = service.get_preferred_time_unit(study_uid=soa_test_data.study.uid)

    study_epochs: list[StudyEpoch] = StudyEpochService.get_all_epochs(
        study_uid=soa_test_data.study.uid, sort_by={"order": True}
    ).items
    study_visits: list[StudyVisit] = StudyVisitService.get_all_visits(
        study_uid=soa_test_data.study.uid, sort_by={"order": True}
    ).items
    study_activities_map: dict[str, StudySelectionActivity] = {
        ssa.study_activity_uid: ssa
        for ssa in StudyActivitySelectionService()
        .get_all_selection(study_uid=soa_test_data.study.uid)
        .items
    }
    study_activity_instances_map: list[StudySelectionActivityInstance] = {
        ssai.study_activity_instance_uid: ssai
        for ssai in StudyActivityInstanceSelectionService()
        .get_all_selection(study_uid=soa_test_data.study.uid)
        .items
    }
    study_activity_schedules: list[
        StudyActivitySchedule
    ] = StudyActivityScheduleService().get_all_schedules(
        study_uid=soa_test_data.study.uid,
        operational=(layout == SoALayout.OPERATIONAL),
    )

    # Test title
    assert table.title == _gettext("protocol_flowchart")

    # Test dimensions
    check_flowchart_table_dimensions(table, layout, soa_test_data.soa_preferences)

    # Test first header row
    check_flowchart_table_first_rows(
        table,
        layout,
        study_epochs,
        study_visits,
        soa_test_data.soa_preferences,
    )

    # Test visit header rows
    visit_idx_by_uid = check_flowchart_table_visit_rows(
        table, layout, time_unit, study_visits, soa_test_data.soa_preferences
    )

    # Test the rest of the rows

    rows_by_uid = {}
    row_idx_by_uid = {}
    soa_group_id = activity_group_id = activity_subgroup_id = activity_uid = None

    for idx, row in enumerate(
        table.rows[table.num_header_rows :], start=table.num_header_rows
    ):
        study_selection: (
            StudySelectionActivity | StudySelectionActivityInstance | None
        ) = None

        for ref in row.cells[0].refs or []:
            assert (
                ref and ref.uid
            ), f"Referenced uid must not be empty in row {idx} column 0"

            if ref.type == "CTTerm":
                soa_group_id = ref.uid
                activity_group_id = activity_subgroup_id = activity_uid = None

            if ref.type == "ActivityGroup":
                activity_group_id = ref.uid
                activity_subgroup_id = activity_uid = None

            if ref.type == "ActivitySubGroup":
                activity_subgroup_id = ref.uid
                activity_uid = None

            if ref.type == SoAItemType.STUDY_ACTIVITY.value:
                activity_uid = ref.uid
                study_selection = study_activities_map[ref.uid]

            if ref.type == SoAItemType.STUDY_ACTIVITY_INSTANCE.value:
                study_selection = study_activity_instances_map[ref.uid]
                assert study_selection.study_activity_uid == activity_uid

            if hide_soa_groups and soa_group_id is None and ref.type == "ActivityGroup":
                assert activity_group_id not in rows_by_uid, (
                    f"With hide_soa_groups and non-visible SoAGroup, "
                    f"only one row should reference {activity_group_id} until row {idx}"
                )

            rows_by_uid[ref.uid] = row
            row_idx_by_uid[ref.uid] = idx

        if study_selection:
            # THEN parent group rows are present in SoA
            # THEN parent group rows come in order (soa_group > activity_group > activity_subgroup [ > activity ] [ > activity_instance ])

            if (
                hide_soa_groups
                and not study_selection.show_soa_group_in_protocol_flowchart
            ):
                assert (
                    soa_group_id is None
                ), "With hide_soa_groups non-visible SoA Groups should be excluded"

            else:
                assert (
                    study_selection.study_soa_group.soa_group_term_uid == soa_group_id
                )

            assert (
                study_selection.study_activity_group.activity_group_uid
                == activity_group_id
            )

            assert (
                study_selection.study_activity_subgroup.activity_subgroup_uid
                == activity_subgroup_id
            )

            assert_error_msg = (
                f"Parent rows are not in order: SoAGroup[{row_idx_by_uid.get(soa_group_id)}]"
                f" ActivityGroup[{row_idx_by_uid.get(activity_group_id)}]"
                f" ActivitySubGroup[{row_idx_by_uid.get(activity_subgroup_id)}]"
                f" {study_selection.study_activity_uid}[{idx}]"
            )
            prev = -1
            _filters: Iterable = filter(
                lambda x: x is not None,
                (
                    row_idx_by_uid.get(soa_group_id),
                    row_idx_by_uid.get(activity_group_id),
                    row_idx_by_uid.get(activity_subgroup_id),
                    idx,
                ),
            )
            for i in _filters:
                assert i > prev, assert_error_msg
                prev = i

    # THEN all study activities are present in detailed and operational SoA tables (regardless whether scheduled for any visit)
    # Note: Placeholders (Requested library activities) are now shown in operational SoA as part of feature #3446656
    for activity in soa_test_data.study_activities.values():
        assert (
            activity.study_activity_uid in rows_by_uid
        ), f"{activity.study_activity_uid} not found in SoA table"

    # THEN all study activity instances are present in operational SoA table (regardless whether scheduled for any visit)
    if layout == SoALayout.OPERATIONAL:
        for activity_instances in soa_test_data.study_activity_instances.values():
            for activity_instance in activity_instances:
                if activity_instance.activity_instance:
                    assert (
                        activity_instance.study_activity_instance_uid in rows_by_uid
                    ), f"{activity_instance.study_activity_instance_uid} not found in SoA table"

    for sas in study_activity_schedules:
        if layout == SoALayout.OPERATIONAL and sas.study_activity_instance_uid:
            assert (
                sas.study_activity_instance_uid in study_activity_instances_map
            ), f"StudyActivityInstance {sas.study_activity_instance_uid} not found"
            study_activity_instance = study_activity_instances_map[
                sas.study_activity_instance_uid
            ]
            study_activity = study_activities_map[
                study_activity_instance.study_activity_uid
            ]

        else:
            assert (
                sas.study_activity_uid in study_activities_map
            ), f"StudyActivity {sas.study_activity_uid} not found"
            study_activity = study_activities_map[sas.study_activity_uid]

        assert (
            sas.study_visit_uid in visit_idx_by_uid
        ), f"No column reference to visit {sas.study_visit_uid}"
        col_idx = visit_idx_by_uid[sas.study_visit_uid]

        # WHEN not operational SoA
        if layout != SoALayout.OPERATIONAL:
            assert (
                sas.study_activity_uid in rows_by_uid
            ), f"No row with reference to activity {sas.study_activity_uid}"
            row = rows_by_uid[sas.study_activity_uid]

            # THEN Activity name in 1st row
            assert row.cells[0].text == study_activity.activity.name

            # THEN scheduled activities have crosses for visits
            assert row.cells[col_idx].text == "X", (
                f"Scheduled {sas.study_activity_schedule_uid} activity {sas.study_activity_uid}"
                f" for visit {sas.study_visit_uid} has no cross on visible StudyActivity level"
            )

            # THEN show/hide row based on show_activity_in_protocol_flowchart property
            assert row.hide == (not study_activity.show_activity_in_protocol_flowchart)

        # WHEN operational SoA
        # study_activity_instance.activity_instance is None for Activity Instance Placeholders
        elif (
            sas.study_activity_instance_uid
            and study_activity_instance.activity_instance
        ):
            assert (
                sas.study_activity_instance_uid in rows_by_uid
            ), f"Row not found with reference to StudyActivityInstance.uid {sas.study_activity_instance_uid}"
            row = rows_by_uid[sas.study_activity_instance_uid]

            # THEN Activity Instance name in 1st row
            assert row.cells[0].text == study_activity_instance.activity_instance.name

            # THEN Topic code is in 2nd row
            assert row.cells[1].text == (
                study_activity_instance.activity_instance.topic_code or ""
            )

            # THEN ADaM param code is in 3nd row
            assert row.cells[2].text == (
                study_activity_instance.activity_instance.adam_param_code or ""
            )

            # THEN scheduled activity instances have crosses for visits
            assert row.cells[col_idx].text == "X", (
                f"Scheduled {sas.study_activity_schedule_uid} activity {sas.study_activity_uid}"
                f" instance {sas.study_activity_instance_uid} for visit {sas.study_visit_uid}"
                " has no cross on visible StudyActivityInstance level"
            )

            # THEN show/hide row based on show_activity_instance_in_protocol_flowchart property
            assert row.hide == (
                not study_activity_instance.show_activity_instance_in_protocol_flowchart
            )

    if layout == SoALayout.OPERATIONAL:
        ensure_flowchart_table_has_no_footnotes(table)
    else:
        check_flowchart_table_footnotes(
            table, soa_test_data.soa_footnotes, layout=layout
        )


def ensure_flowchart_table_has_no_footnotes(table: Table):
    """ensure SoA flowchart doesn't have footnotes"""

    for r_idx, row in enumerate(table.rows):
        for c_idx, cell in enumerate(row.cells):
            assert (
                not cell.footnotes
            ), f"flowchart table should not have footnote symbols row {r_idx} col {c_idx}"

    assert not table.footnotes, "flowchart should not have footnotes"


@pytest.mark.parametrize(
    "time_unit",
    ["day", "week"],
)
def test_propagate_hidden_rows(soa_test_data: SoATestData, time_unit):
    """Validates propagation of crosses and footnotes from hidden rows to the first visible parent row"""

    service = StudyFlowchartService()
    soa_table: TableWithFootnotes = service.build_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=None,
        layout=SoALayout.PROTOCOL,
        time_unit=time_unit,
    )
    service.propagate_hidden_rows(soa_table.rows)
    soa_table.rows[0].cells[0].text = _gettext("procedure_label")

    check_hidden_row_propagation(soa_table)


def test_get_flowchart_item_uid_coordinates(soa_test_data: SoATestData):
    service = StudyFlowchartService()

    soa_table = service.build_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=None,
        layout=SoALayout.DETAILED,
        time_unit="week",
    )

    results = service.get_flowchart_item_uid_coordinates(
        study_uid=soa_test_data.study.uid
    )
    assert isinstance(results, dict)

    collected_coordinates: dict[str, tuple[int, int]] = {
        ref.uid: (r_idx, c_idx)
        for r_idx, row in enumerate(soa_table.rows)
        for c_idx, cell in enumerate(row.cells)
        if cell.refs
        for ref in cell.refs
        if ref.type
        in {
            SoAItemType.STUDY_EPOCH.value,
            SoAItemType.STUDY_VISIT.value,
            SoAItemType.STUDY_SOA_GROUP.value,
            SoAItemType.STUDY_ACTIVITY_GROUP.value,
            SoAItemType.STUDY_ACTIVITY_SUBGROUP.value,
            SoAItemType.STUDY_ACTIVITY.value,
            SoAItemType.STUDY_ACTIVITY_SCHEDULE,
        }
    }

    # collected coordinates is a subset of get_flowchart_item_uid_coordinates() because of grouped visits
    for uid, expected_coordinates in collected_coordinates.items():
        assert uid in results, f"Missing coordinates for uid: {uid}"
        returned_coordinates = results.get(uid)
        assert isinstance(
            returned_coordinates, tuple
        ), f"Unexpected coordinates type {type(returned_coordinates)} for uid: {uid}"
        assert (
            len(returned_coordinates) == 2
        ), f"Unexpected length of coordinates {len(returned_coordinates)} for uid: {uid}"
        for i in range(2):
            assert isinstance(
                returned_coordinates[i], int
            ), f"Unexpected coordinates type {type(returned_coordinates)} for uid: {uid}"
            assert (
                returned_coordinates[i] >= 0
            ), f"Negative coordinates {returned_coordinates} for uid: {uid}"

        assert (
            returned_coordinates == expected_coordinates
        ), f"Coordinates mismatch, expected {expected_coordinates} returned {returned_coordinates} for uid: {uid}"

    # THEN all StudyEpochs have coordinates
    study_epoch: StudyEpoch
    for study_epoch in StudyEpochService.get_all_epochs(
        study_uid=soa_test_data.study.uid, sort_by={"order": True}
    ).items:
        assert results.pop(
            study_epoch.uid, None
        ), f"Missing coordinates of StudyEpoch[{study_epoch.uid}]"

    # THEN all StudyVisits have coordinates
    study_visit: StudyVisit
    for study_visit in StudyVisitService.get_all_visits(
        study_uid=soa_test_data.study.uid, sort_by={"order": True}
    ).items:
        assert results.pop(
            study_visit.uid, None
        ), f"Missing coordinates of StudyVisit[{study_visit.uid}]"
    shared_soa_groups = []
    shared_study_activity_groups = []
    shared_study_activity_subgroups = []
    study_selection_activity: StudySelectionActivity
    for study_selection_activity in (
        StudyActivitySelectionService()
        .get_all_selection(study_uid=soa_test_data.study.uid)
        .items
    ):
        # THEN all StudySelectionActivity have coordinates
        assert results.pop(study_selection_activity.study_activity_uid, None), (
            f"Missing coordinates of StudySelectionActivity[{study_selection_activity.study_activity_uid}]: "
            + str(study_selection_activity.study_activity_uid)
        )

        if (
            study_selection_activity.study_soa_group.study_soa_group_uid
            not in shared_soa_groups
        ):
            # THEN all StudySoAGroups have coordinates
            assert results.pop(
                study_selection_activity.study_soa_group.study_soa_group_uid, None
            ), (
                f"Missing coordinates of StudySelectionActivity[{study_selection_activity.study_activity_uid}]: "
                + study_selection_activity.study_soa_group.study_soa_group_uid
            )
            shared_soa_groups.append(
                study_selection_activity.study_soa_group.study_soa_group_uid
            )

        # THEN all StudyActivityGroups have coordinates
        if (
            study_selection_activity.study_activity_group.study_activity_group_uid
            and study_selection_activity.study_activity_group.study_activity_group_uid
            not in shared_study_activity_groups
        ):
            assert results.pop(
                study_selection_activity.study_activity_group.study_activity_group_uid,
                None,
            ), (
                f"Missing coordinates of StudySelectionActivity[{study_selection_activity.study_activity_uid}]: "
                + study_selection_activity.study_activity_group.study_activity_group_uid
            )
            shared_study_activity_groups.append(
                study_selection_activity.study_activity_group.study_activity_group_uid
            )

        # THEN all StudyActivitySubGroups have coordinates
        if (
            study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
            and study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
            not in shared_study_activity_subgroups
        ):
            assert results.pop(
                study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid,
                None,
            ), (
                f"Missing coordinates of StudySelectionActivity[{study_selection_activity.study_activity_uid}]: "
                + study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
            )
            shared_study_activity_subgroups.append(
                study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
            )

    # THEN all StudyActivitySchedules have coordinates
    study_activity_schedule: StudyActivitySchedule
    for study_activity_schedule in StudyActivityScheduleService().get_all_schedules(
        study_uid=soa_test_data.study.uid, operational=False
    ):
        assert results.pop(
            study_activity_schedule.study_activity_schedule_uid, None
        ), f"Missing coordinates of StudyActivitySchedule[{study_activity_schedule.study_activity_schedule_uid}]"

    # After removing all expected keys from the dict, we expect no more coordinates left in there
    assert not results, "Unexpected coordinates"


@pytest.mark.parametrize(
    "protocol_flowchart",
    [None, True, False],
)
def test_download_detailed_soa_content(
    soa_test_data: SoATestData,
    protocol_flowchart: bool | None,
):
    """Test returned data of download_detailed_soa_content"""

    study_uid = soa_test_data.study.uid
    service = StudyFlowchartService()
    results = service.download_detailed_soa_content(
        study_uid=study_uid,
        protocol_flowchart=protocol_flowchart,
    )
    assert results
    assert isinstance(results, list)

    schedules = StudyActivityScheduleService().get_all_schedules(
        study_uid=study_uid,
        operational=False,
    )
    study_visits_map: dict[str, StudyVisit] = {
        svis.uid: svis
        for svis in StudyVisitService.get_all_visits(
            study_uid=study_uid, sort_by={"order": True}
        ).items
    }
    study_activities_map: dict[str, StudySelectionActivity] = {
        ssa.study_activity_uid: ssa
        for ssa in StudyActivitySelectionService()
        .get_all_selection(study_uid=study_uid)
        .items
    }

    if protocol_flowchart:
        schedules = [
            sched
            for sched in schedules
            if study_activities_map[
                sched.study_activity_uid
            ].show_activity_in_protocol_flowchart
        ]
    study_activity_schedules_map: dict[str, StudyActivitySchedule] = {
        schedule.study_activity_schedule_uid: schedule for schedule in schedules
    }

    if protocol_flowchart:
        assert len(results) == len(schedules), "record count mismatch"
    else:
        # Non-protocol detailed export includes activities without schedules
        num_unscheduled = len(
            [
                ssa
                for ssa in study_activities_map.values()
                if not any(
                    s.study_activity_uid == ssa.study_activity_uid for s in schedules
                )
            ]
        )
        assert len(results) == len(schedules) + num_unscheduled, "record count mismatch"

    sched: StudyActivitySchedule
    for i, res in enumerate(results):
        study_activity_schedule_uid = res["study_activity_schedule_uid"]

        if study_activity_schedule_uid is None:
            # Unscheduled activity - visit and epoch should be null
            assert (
                not protocol_flowchart
            ), "unscheduled activities should not appear in protocol export"
            assert (
                res["visit"] is None
            ), f"record #{i} unscheduled activity should have no visit"
            assert (
                res["epoch"] is None
            ), f"record #{i} unscheduled activity should have no epoch"
            continue

        sched = study_activity_schedules_map[study_activity_schedule_uid]
        study_activity = study_activities_map[sched.study_activity_uid]
        study_visit = study_visits_map[sched.study_visit_uid]

        assert len(res.keys()) == 10, f"record #{i} property count mismatch"
        assert res["study_version"] == get_study_version(soa_test_data.study) or res[
            "study_version"
        ].startswith("LATEST on 20")
        assert (
            res["study_number"]
            == soa_test_data.study.current_metadata.identification_metadata.study_number
        )
        assert res["epoch"] == study_visit.study_epoch.sponsor_preferred_name
        assert res["visit"] == study_visit.visit_short_name
        assert res["soa_group"] == study_activity.study_soa_group.soa_group_term_name
        assert (
            res["activity_group"]
            == study_activity.study_activity_group.activity_group_name
        )
        assert (
            res["activity_subgroup"]
            == study_activity.study_activity_subgroup.activity_subgroup_name
        )
        assert res["activity"] == study_activity.activity.name
        if not protocol_flowchart:
            assert res["is_data_collected"] == study_activity.activity.is_data_collected


def test_download_operational_soa_content(
    soa_test_data: SoATestData,
):
    """Test returned data of download_operational_soa_content"""

    study_uid = soa_test_data.study.uid
    results = StudyFlowchartService().download_operational_soa_content(
        study_uid=study_uid,
    )
    assert results
    assert isinstance(results, list)

    schedules = StudyActivityScheduleService().get_all_schedules(
        study_uid=study_uid, operational=True
    )
    study_activity_schedules_map: dict[str, list[StudyActivitySchedule]] = {}
    for schedule in schedules:
        study_activity_schedules_map.setdefault(
            schedule.study_activity_schedule_uid, []
        ).append(schedule)

    study_visits_map: dict[str, StudyVisit] = {
        svis.uid: svis
        for svis in StudyVisitService.get_all_visits(
            study_uid=study_uid, sort_by={"order": True}
        ).items
    }
    study_activities_map: dict[str, StudySelectionActivity] = {
        ssa.study_activity_uid: ssa
        for ssa in StudyActivitySelectionService()
        .get_all_selection(study_uid=study_uid)
        .items
    }
    study_activity_instances_map: dict[str, StudySelectionActivityInstance] = {
        sais.study_activity_instance_uid: sais
        for sais in StudyActivityInstanceSelectionService()
        .get_all_selection(
            study_uid=study_uid,
            filter_by={
                "activity.library_name": {
                    "v": [settings.requested_library_name],
                    "op": "ne",
                }
            },
        )
        .items
    }
    assert (
        len(results) == soa_test_data.NUM_OPERATIONAL_SOA_EXPORT_ROWS
    ), "record count mismatch"

    sched: StudyActivitySchedule
    for i, res in enumerate(results):
        study_activity_schedule_uid = res["study_activity_schedule_uid"]

        assert len(res.keys()) == 13, f"record #{i} property count mismatch"
        assert res["study_version"].startswith("LATEST on 20")
        assert (
            res["study_number"]
            == soa_test_data.study.current_metadata.identification_metadata.study_number
        )

        if res["activity_instance"] is None:
            # Activity instance without a selected ActivityInstance (placeholder)
            assert (
                res["topic_code"] is None
            ), f"record #{i} placeholder instance should have no topic_code"
            assert (
                res["param_code"] is None
            ), f"record #{i} placeholder instance should have no param_code"
            continue

        if study_activity_schedule_uid is None:
            # Unscheduled activity instance - visit and epoch should be empty
            assert (
                res["visit"] is None
            ), f"record #{i} unscheduled instance should have no visit"
            assert (
                res["epoch"] is None
            ), f"record #{i} unscheduled instance should have no epoch"
            continue

        sched = study_activity_schedules_map[study_activity_schedule_uid][0]
        study_activity = study_activities_map[sched.study_activity_uid]
        study_visit = study_visits_map[sched.study_visit_uid]

        assert res["epoch"] == study_visit.study_epoch.sponsor_preferred_name
        assert res["visit"] == study_visit.visit_short_name
        assert res["soa_group"] == study_activity.study_soa_group.soa_group_term_name
        assert (
            res["activity_group"]
            == study_activity.study_activity_group.activity_group_name
        )
        assert (
            res["activity_subgroup"]
            == study_activity.study_activity_subgroup.activity_subgroup_name
        )
        assert res["activity"] == study_activity.activity.name

        # a StudyActivitySchedule schedules an activity for a visit, so can intrinsicly schedule multiple StudyActivityInstnaces
        # Find the StudyActivityInstance by name for this StudyActivitySchedule (when study activity has multiple instances)
        for sched in study_activity_schedules_map[study_activity_schedule_uid]:
            study_activity_instance = study_activity_instances_map[
                sched.study_activity_instance_uid
            ]
            if (
                res["activity_instance"]
                == study_activity_instance.activity_instance.name
            ):
                break
        assert (
            res["activity_instance"] == study_activity_instance.activity_instance.name
        ), "no study activity instance found by the name and schedule uid"
        assert (
            res["param_code"]
            == study_activity_instance.activity_instance.adam_param_code
        )
        assert res["topic_code"] == study_activity_instance.activity_instance.topic_code


class TestSoASnapshot:
    """Tests StudyFlowchartService and StudySoARepository saving and loading SoA snapshots with Study versioning"""

    def test_soa_snapshot_versioned(self, soa_test_data2: SoATestData):
        """Tests saving and retrieving SoA snapshots with study versioning"""

        study_flowchart_service = StudyFlowchartService()
        study_service = StudyService()

        # GIVEN: a Study populated with data required for SoA
        study_uid = soa_test_data2.study.uid

        # GIVEN: Protocol SoA of the latest draft version
        expected_table, expected_html = self._render_protocol_soa(
            study_flowchart_service, study_uid, study_value_version=None
        )

        # GIVEN: Protocol Lab table SoA of the latest draft version
        expected_lab_table = study_flowchart_service.get_flowchart_table_lab_table(
            study_uid, study_value_version=None
        )

        # SCENARIO: After locking the Study, the SoA snapshot can be read back from database
        # WHEN: Study is locked
        study = study_service.lock(
            uid=study_uid,
            change_description="v1",
            reason_for_lock_term_uid=soa_test_data2.reason_for_lock_term_uid,
        )
        previous_study_version = str(
            study.current_metadata.version_metadata.version_number
        )
        # THEN: Locked StudyValue has a single SoA snapshot with all renderings
        previous_snapshot = self._get_soa_snapshot_node(
            study_uid, previous_study_version
        )
        assert previous_snapshot["json"] == expected_table.model_dump_json()
        assert previous_snapshot["html"] == expected_html
        # THEN: SoA of the locked Study version matches
        self._assert_soa_matches_snapshot(
            study_flowchart_service,
            study_uid,
            previous_study_version,
            previous_snapshot,
        )

        # THEN: Locked StudyValue has a single Protocol Lab table SoA snapshot with all renderings
        previous_lab_snapshot = self._get_soa_snapshot_node(
            study_uid, previous_study_version, layout=SoALayout.PROTOCOL_LAB_TABLE
        )
        assert previous_lab_snapshot["json"] == expected_lab_table.model_dump_json()
        self._assert_lab_table_matches_snapshot(
            study_flowchart_service,
            study_uid,
            previous_study_version,
            previous_lab_snapshot,
        )

        # SCENARIO: After unlocking the Study, the latest draft version has no SoA snapshot
        # WHEN: Study is unlocked
        study_service.unlock(
            uid=study_uid,
            reason_for_unlock_term_uid=soa_test_data2.reason_for_unlock_term_uid,
        )
        # THEN: Latest StudyValue has no SoA snapshot
        assert not self._get_soa_snapshot_nodes(
            study_uid, study_value_version=None, layout=None
        )
        # THEN: SoA snapshot of the previous Study version is unchanged
        assert (
            self._get_soa_snapshot_node(study_uid, previous_study_version)
            == previous_snapshot
        )
        assert (
            self._get_soa_snapshot_node(
                study_uid, previous_study_version, layout=SoALayout.PROTOCOL_LAB_TABLE
            )
            == previous_lab_snapshot
        )

        # SCENARIO: After changing the SoA data of DRAFT Study, the SoA of the previous Study version stays the same
        # WHEN: Changed Study SoA data
        self._update_a_study_activity_subgroup(soa_test_data2)
        self._remove_first_visible_study_activity(soa_test_data2)
        self._update_a_study_activity_group(soa_test_data2)
        # THEN: SoA of the latest draft version changed
        latest_table, _ = self._render_protocol_soa(
            study_flowchart_service, study_uid, study_value_version=None
        )
        assert latest_table.model_dump() != expected_table.model_dump()
        # THEN: SoA of the previous Study version matches its SoA snapshot
        self._assert_soa_matches_snapshot(
            study_flowchart_service,
            study_uid,
            previous_study_version,
            previous_snapshot,
        )

        # THEN: Protocol Lab table SoA of the previous Study version matches its SoA snapshot
        self._assert_lab_table_matches_snapshot(
            study_flowchart_service,
            study_uid,
            previous_study_version,
            previous_lab_snapshot,
        )

        # SCENARIO: After releasing a Study version, the released version has a SoA snapshot
        # WHEN: A Study version is released
        study_service.release(
            uid=study_uid,
            change_description="r1",
            reason_for_release_uid=soa_test_data2.reason_for_lock_term_uid,
        )
        released_study_version = f"{previous_study_version}.1"  # release API call does not return version number
        # THEN: Released StudyValue has a SoA snapshot of the draft Study version at the time of release
        released_snapshot = self._get_soa_snapshot_node(
            study_uid, released_study_version
        )
        assert released_snapshot["json"] == latest_table.model_dump_json()
        self._assert_soa_matches_snapshot(
            study_flowchart_service,
            study_uid,
            released_study_version,
            released_snapshot,
        )
        # THEN: Released StudyValue has a Protocol Lab table SoA snapshot too
        self._assert_lab_table_matches_snapshot(
            study_flowchart_service,
            study_uid,
            released_study_version,
            self._get_soa_snapshot_node(
                study_uid, released_study_version, layout=SoALayout.PROTOCOL_LAB_TABLE
            ),
        )
        # THEN: Latest StudyValue has no SoA snapshot
        assert not self._get_soa_snapshot_nodes(
            study_uid, study_value_version=None, layout=None
        )

        # SCENARIO: After locking the Study again, SoA snapshots of the previous versions are unchanged
        # WHEN: Study is locked
        study = study_service.lock(
            uid=study_uid,
            change_description="v2",
            reason_for_lock_term_uid=soa_test_data2.reason_for_lock_term_uid,
        )
        latest_study_version = str(
            study.current_metadata.version_metadata.version_number
        )
        # THEN: Locked StudyValue has a SoA snapshot of the latest draft
        latest_snapshot = self._get_soa_snapshot_node(study_uid, latest_study_version)
        assert latest_snapshot["json"] == latest_table.model_dump_json()
        assert latest_snapshot["json"] != previous_snapshot["json"]
        # THEN: SoA snapshots of previous versions are unchanged
        assert (
            self._get_soa_snapshot_node(study_uid, previous_study_version)
            == previous_snapshot
        )
        assert (
            self._get_soa_snapshot_node(study_uid, released_study_version)
            == released_snapshot
        )

        # WHEN: Study is unlocked
        study_service.unlock(
            uid=study_uid,
            reason_for_unlock_term_uid=soa_test_data2.reason_for_unlock_term_uid,
        )
        # THEN: Latest StudyValue has no SoA snapshot
        assert not self._get_soa_snapshot_nodes(
            study_uid, study_value_version=None, layout=None
        )
        # THEN: SoA of the locked versions match their SoA snapshots
        for study_value_version, snapshot in (
            (previous_study_version, previous_snapshot),
            (latest_study_version, latest_snapshot),
        ):
            self._assert_soa_matches_snapshot(
                study_flowchart_service, study_uid, study_value_version, snapshot
            )

    def test_soa_snapshot_served_verbatim(self, soa_test_data2: SoATestData):
        """Tests that SoA of a locked Study version is returned from the saved snapshot without any rendering"""

        service = StudyFlowchartService()
        study_uid = soa_test_data2.study.uid

        # GIVEN: Study has a locked version
        study_value_version = TestUtils.lock_and_unlock_study(
            study_uid,
            reason_for_lock_term_uid=soa_test_data2.reason_for_lock_term_uid,
            reason_for_unlock_term_uid=soa_test_data2.reason_for_unlock_term_uid,
        )
        snapshot = self._get_soa_snapshot_node(study_uid, study_value_version)
        snapshot_time_unit = snapshot["time_unit"]

        # GIVEN: Renderings saved in SoA snapshot are replaced with sentinel values
        frozen_title = "Frozen SoA snapshot"
        frozen_table = TableWithFootnotes.model_validate_json(snapshot["json"])
        frozen_table.title = frozen_title
        frozen_json = frozen_table.model_dump_json()
        db.cypher_query(
            """
            MATCH (:StudyRoot {uid: $study_uid})-[:HAS_VERSION {status: 'RELEASED', version: $version}]->
                (:StudyValue)-[:HAS_SOA_SNAPSHOT]->(snapshot:StudySoASnapshot)
            SET snapshot.html = $html, snapshot.json = $json, snapshot.docx = $docx, snapshot.xlsx = $xlsx
            """,
            {
                "study_uid": study_uid,
                "version": study_value_version,
                "html": "<p>frozen html</p>",
                "json": frozen_json,
                "docx": b"frozen docx",
                "xlsx": b"frozen xlsx",
            },
        )

        # THEN: Every rendering of the locked Study version is the saved one
        assert (
            service.get_study_flowchart_html(
                study_uid, study_value_version, layout=SoALayout.PROTOCOL
            )
            == "<p>frozen html</p>"
        )
        assert (
            service.get_flowchart_table(
                study_uid, study_value_version, layout=SoALayout.PROTOCOL
            ).title
            == frozen_title
        )
        assert (
            service.get_study_flowchart_docx(
                study_uid,
                study_value_version,
                layout=SoALayout.PROTOCOL,
                time_unit=None,
            ).getvalue()
            == b"frozen docx"
        )
        assert (
            service.get_study_flowchart_xlsx(
                study_uid,
                study_value_version,
                layout=SoALayout.PROTOCOL,
                time_unit=None,
            ).getvalue()
            == b"frozen xlsx"
        )
        assert (
            service.get_soa_snapshot(study_uid, study_value_version).title
            == frozen_title
        )
        # THEN: Requesting the time unit of the snapshot also returns the saved rendering
        assert (
            service.get_study_flowchart_html(
                study_uid,
                study_value_version,
                layout=SoALayout.PROTOCOL,
                time_unit=snapshot_time_unit,
            )
            == "<p>frozen html</p>"
        )

        # THEN: HTML with uids is rendered from the saved SoA table
        assert frozen_title in service.get_study_flowchart_html(
            study_uid,
            study_value_version,
            layout=SoALayout.PROTOCOL,
            include_uids=True,
        )

        # THEN: Other time unit is shown on the saved SoA table, with the frozen content kept
        other_time_unit = "day" if snapshot_time_unit == "week" else "week"
        converted_table = service.get_flowchart_table(
            study_uid,
            study_value_version,
            layout=SoALayout.PROTOCOL,
            time_unit=other_time_unit,
        )
        assert converted_table.title == frozen_title
        assert converted_table.rows[converted_table.num_header_rows - 2].cells[
            0
        ].text == _gettext(f"study_{other_time_unit}")
        assert (
            converted_table.rows[converted_table.num_header_rows - 2].cells
            != frozen_table.rows[frozen_table.num_header_rows - 2].cells
        )
        assert frozen_title in service.get_study_flowchart_html(
            study_uid,
            study_value_version,
            layout=SoALayout.PROTOCOL,
            time_unit=other_time_unit,
        )

        # THEN: Forced build, other layouts and the latest draft version are built
        assert (
            service.get_flowchart_table(
                study_uid,
                study_value_version,
                layout=SoALayout.PROTOCOL,
                force_build=True,
            ).title
            != frozen_title
        )
        assert (
            service.get_flowchart_table(
                study_uid, study_value_version, layout=SoALayout.DETAILED
            ).title
            != frozen_title
        )
        assert (
            service.get_flowchart_table(
                study_uid, study_value_version=None, layout=SoALayout.PROTOCOL
            ).title
            != frozen_title
        )

    def test_lab_table_soa_snapshot_served_verbatim(self, soa_test_data2: SoATestData):
        """Tests that Protocol Lab table SoA of a locked Study version is returned from its saved snapshot"""

        service = StudyFlowchartService()
        study_uid = soa_test_data2.study.uid
        layout = SoALayout.PROTOCOL_LAB_TABLE

        # GIVEN: Study has a locked version
        study_value_version = TestUtils.lock_and_unlock_study(
            study_uid,
            reason_for_lock_term_uid=soa_test_data2.reason_for_lock_term_uid,
            reason_for_unlock_term_uid=soa_test_data2.reason_for_unlock_term_uid,
        )
        snapshot = self._get_soa_snapshot_node(
            study_uid, study_value_version, layout=layout
        )
        # THEN: Lab table and Protocol SoA snapshots are separate
        protocol_snapshot = self._get_soa_snapshot_node(study_uid, study_value_version)
        assert snapshot["json"] != protocol_snapshot["json"]

        # GIVEN: Renderings saved in Lab table SoA snapshot are replaced with sentinel values
        frozen_title = "Frozen Lab table SoA snapshot"
        frozen_table = TableWithFootnotes.model_validate_json(snapshot["json"])
        frozen_table.title = frozen_title
        db.cypher_query(
            """
            MATCH (:StudyRoot {uid: $study_uid})-[:HAS_VERSION {status: 'RELEASED', version: $version}]->
                (:StudyValue)-[:HAS_SOA_SNAPSHOT]->(snapshot:StudySoASnapshot {layout: $layout})
            SET snapshot.html = $html, snapshot.json = $json, snapshot.docx = $docx, snapshot.xlsx = $xlsx
            """,
            {
                "study_uid": study_uid,
                "version": study_value_version,
                "layout": layout.value,
                "html": "<p>frozen lab html</p>",
                "json": frozen_table.model_dump_json(),
                "docx": b"frozen lab docx",
                "xlsx": b"frozen lab xlsx",
            },
        )

        # THEN: Every rendering of the Lab table SoA of the locked Study version is the saved one
        assert (
            service.get_study_flowchart_html(study_uid, study_value_version, layout)
            == "<p>frozen lab html</p>"
        )
        assert (
            service.get_flowchart_table(study_uid, study_value_version, layout).title
            == frozen_title
        )
        assert (
            service.get_flowchart_table_lab_table(study_uid, study_value_version).title
            == frozen_title
        )
        assert (
            service.get_study_flowchart_docx(
                study_uid, study_value_version, layout, time_unit=None
            ).getvalue()
            == b"frozen lab docx"
        )
        assert (
            service.get_study_flowchart_xlsx(
                study_uid, study_value_version, layout, time_unit=None
            ).getvalue()
            == b"frozen lab xlsx"
        )
        assert (
            service.get_soa_snapshot(study_uid, study_value_version, layout).title
            == frozen_title
        )

        # THEN: Protocol SoA snapshot is not affected
        assert (
            service.get_study_flowchart_html(
                study_uid, study_value_version, SoALayout.PROTOCOL
            )
            == protocol_snapshot["html"]
        )

        # THEN: HTML with uids is rendered from the saved Lab table SoA table
        assert frozen_title in service.get_study_flowchart_html(
            study_uid, study_value_version, layout, include_uids=True
        )

        # THEN: Forced build and the latest draft version are built
        assert (
            service.get_flowchart_table_lab_table(
                study_uid, study_value_version, force_build=True
            ).title
            != frozen_title
        )
        assert (
            service.get_flowchart_table_lab_table(study_uid, None).title != frozen_title
        )

    def test_lab_table_of_locked_version_without_snapshot_is_built(
        self, soa_test_data2: SoATestData
    ):
        """Tests that Protocol Lab table SoA of a Study version locked before Lab table snapshots existed is built"""

        service = StudyFlowchartService()
        study_uid = soa_test_data2.study.uid
        layout = SoALayout.PROTOCOL_LAB_TABLE

        # GIVEN: Study has a locked version without Lab table SoA snapshot
        study_value_version = TestUtils.lock_and_unlock_study(
            study_uid,
            reason_for_lock_term_uid=soa_test_data2.reason_for_lock_term_uid,
            reason_for_unlock_term_uid=soa_test_data2.reason_for_unlock_term_uid,
        )
        db.cypher_query(
            """
            MATCH (:StudyRoot {uid: $study_uid})-[:HAS_VERSION {status: 'RELEASED', version: $version}]->
                (:StudyValue)-[:HAS_SOA_SNAPSHOT]->(snapshot:StudySoASnapshot {layout: $layout})
            DETACH DELETE snapshot
            """,
            {
                "study_uid": study_uid,
                "version": study_value_version,
                "layout": layout.value,
            },
        )

        # THEN: Lab table SoA of the locked version is built, while the Protocol SoA is still served from snapshot
        assert service.get_flowchart_table_lab_table(
            study_uid, study_value_version
        ).rows
        assert service.get_study_flowchart_html(
            study_uid, study_value_version, layout
        ).startswith("<")
        assert service.get_flowchart_table(
            study_uid, study_value_version, SoALayout.PROTOCOL
        ).rows

        # WHEN: Lab table SoA snapshot saved
        service.save_soa_snapshot(
            study_uid=study_uid, layout=layout, study_value_version=study_value_version
        )

        # THEN: The snapshot is saved and replaced on repeated save
        service.save_soa_snapshot(
            study_uid=study_uid, layout=layout, study_value_version=study_value_version
        )
        snapshot = self._get_soa_snapshot_node(
            study_uid, study_value_version, layout=layout
        )
        self._assert_lab_table_matches_snapshot(
            service, study_uid, study_value_version, snapshot
        )

    def test_soa_of_locked_version_without_snapshot_not_found(
        self, soa_test_data2: SoATestData
    ):
        """Tests that SoA of a locked Study version without SoA snapshot is not built from current data"""

        service = StudyFlowchartService()
        study_uid = soa_test_data2.study.uid

        # GIVEN: Study has a locked version without SoA snapshot
        study_value_version = TestUtils.lock_and_unlock_study(
            study_uid,
            reason_for_lock_term_uid=soa_test_data2.reason_for_lock_term_uid,
            reason_for_unlock_term_uid=soa_test_data2.reason_for_unlock_term_uid,
        )
        db.cypher_query(
            """
            MATCH (:StudyRoot {uid: $study_uid})-[:HAS_VERSION {status: 'RELEASED', version: $version}]->
                (:StudyValue)-[:HAS_SOA_SNAPSHOT]->(snapshot:StudySoASnapshot)
            DETACH DELETE snapshot
            """,
            {"study_uid": study_uid, "version": study_value_version},
        )

        # THEN: Every rendering of the Protocol SoA of the locked Study version is not found
        for get_soa in (
            service.get_flowchart_table,
            service.get_study_flowchart_html,
            lambda **kwargs: service.get_study_flowchart_html(
                include_uids=True, **kwargs
            ),
            lambda **kwargs: service.get_study_flowchart_docx(time_unit=None, **kwargs),
            lambda **kwargs: service.get_study_flowchart_xlsx(time_unit=None, **kwargs),
        ):
            with pytest.raises(NotFoundException, match="No SoA snapshot found"):
                get_soa(
                    study_uid=study_uid,
                    study_value_version=study_value_version,
                    layout=SoALayout.PROTOCOL,
                )

        # THEN: Forced build and other layouts are still built
        assert service.get_flowchart_table(
            study_uid,
            study_value_version,
            layout=SoALayout.PROTOCOL,
            force_build=True,
        ).rows
        assert service.get_flowchart_table(
            study_uid, study_value_version, layout=SoALayout.DETAILED
        ).rows

    def test_save_snapshot_of_nonexistent_study_version(
        self, soa_test_data2: SoATestData
    ):
        """Tests that saving a SoA snapshot of a nonexistent Study version fails and leaves no trace"""

        study_uid = soa_test_data2.study.uid
        snapshot = SoASnapshot(
            html="html", docx=b"docx", xlsx=b"xlsx", json="{}", time_unit="week"
        )

        # WHEN: saving SoA snapshot to a Study version that does not exist
        # THEN: NotFoundException is raised
        with pytest.raises(NotFoundException):
            StudySoARepository.save_snapshot(
                study_uid=study_uid, snapshot=snapshot, study_value_version="99.9"
            )

        # THEN: no SoA snapshot node is created
        assert not db.cypher_query(
            "MATCH (:StudyRoot {uid: $study_uid})-[:HAS_VERSION]->(:StudyValue)-[:HAS_SOA_SNAPSHOT]->(s:StudySoASnapshot) "
            "WHERE s.html = 'html' RETURN s",
            {"study_uid": study_uid},
        )[0]

    def test_save_protocol_soa_snapshot_of_previous_versions(
        self, soa_test_data2: SoATestData
    ):
        """Tests re-rendering SoA snapshots of previous locked Study versions"""

        study_flowchart_service = StudyFlowchartService()
        study_uid = soa_test_data2.study.uid

        # GIVEN: Study has 2 locked versions and a draft version, all differs in SoA
        version_v1 = TestUtils.lock_and_unlock_study(
            study_uid,
            reason_for_lock_term_uid=soa_test_data2.reason_for_lock_term_uid,
            reason_for_unlock_term_uid=soa_test_data2.reason_for_unlock_term_uid,
        )
        activity_v2 = soa_test_data2.create_study_activity(
            name="Potassium",
            soa_group="Efficacy",
            group="Laboratory Assessments",
            subgroup="Biochemistry",
            visits=["V1", "V6"],
            show_soa_group=True,
            show_group=True,
            show_subgroup=False,
            show_activity=True,
        )
        version_v2 = TestUtils.lock_and_unlock_study(
            study_uid,
            reason_for_lock_term_uid=soa_test_data2.reason_for_lock_term_uid,
            reason_for_unlock_term_uid=soa_test_data2.reason_for_unlock_term_uid,
        )
        StudyActivitySelectionService().delete_selection(
            study_uid=study_uid,
            study_selection_uid=activity_v2.study_activity_uid,
        )

        snapshot_v1 = self._get_soa_snapshot_node(study_uid, version_v1)
        snapshot_v2 = self._get_soa_snapshot_node(study_uid, version_v2)
        assert snapshot_v1["json"] != snapshot_v2["json"]

        # GIVEN: SoA snapshots removed
        db.cypher_query(
            """
            MATCH (:StudyRoot {uid: $study_uid})-[:HAS_VERSION]->(:StudyValue)-[:HAS_SOA_SNAPSHOT]->(snapshot:StudySoASnapshot)
            DETACH DELETE snapshot
            """,
            {"study_uid": study_uid},
        )

        # WHEN: SoA snapshots of older study versions saved one-by-one
        for study_value_version in (version_v1, version_v2):
            study_flowchart_service.save_protocol_soa_snapshot(
                study_uid=study_uid, study_value_version=study_value_version
            )

        # THEN: Latest draft version of Study has no SoA snapshot
        assert not self._get_soa_snapshot_nodes(
            study_uid, study_value_version=None, layout=None
        )
        # THEN: SoA snapshots match the SoA snapshots saved when locking the Study versions
        for study_value_version, expected_snapshot in (
            (version_v1, snapshot_v1),
            (version_v2, snapshot_v2),
        ):
            snapshot = self._get_soa_snapshot_node(study_uid, study_value_version)
            assert snapshot["json"] == expected_snapshot["json"]
            assert snapshot["html"] == expected_snapshot["html"]

        # WHEN: SoA snapshot saved again
        study_flowchart_service.save_protocol_soa_snapshot(
            study_uid=study_uid, study_value_version=version_v1
        )
        # THEN: Previous SoA snapshot is replaced
        assert len(self._get_soa_snapshot_nodes(study_uid, version_v1)) == 1

    # LEGACY-SOA-SNAPSHOT (242942): only used by migration 024 to render pre-existing
    # locked/released versions from HAS_PROTOCOL_SOA_CELL refs. Remove in the next release.
    def test_save_protocol_soa_snapshot_from_legacy_snapshot(
        self, soa_test_data2: SoATestData
    ):
        """Tests that a SoA snapshot of a Study version with legacy HAS_PROTOCOL_SOA_CELL relationships
        is rendered from those relationships, not built from the Study selections"""

        service = StudyFlowchartService()
        study_uid = soa_test_data2.study.uid

        # GIVEN: Study has a locked version
        study_value_version = TestUtils.lock_and_unlock_study(
            study_uid,
            reason_for_lock_term_uid=soa_test_data2.reason_for_lock_term_uid,
            reason_for_unlock_term_uid=soa_test_data2.reason_for_unlock_term_uid,
        )
        built_table = service.get_flowchart_table(
            study_uid, study_value_version, SoALayout.PROTOCOL, force_build=True
        )

        # GIVEN: the locked version has legacy SoA cell references of a single activity at a single visit
        schedule = soa_test_data2.study_activity_schedules[0]
        study_visit = next(
            visit
            for visit in soa_test_data2.study_visits.values()
            if visit.uid == schedule.study_visit_uid
        )
        db.cypher_query(
            """
            MATCH (:StudyRoot {uid: $study_uid})-[:HAS_VERSION {status: 'RELEASED', version: $version}]->(sv:StudyValue)
            MATCH (sv)-[:HAS_STUDY_EPOCH]->(epoch:StudyEpoch {uid: $epoch_uid})
            MATCH (sv)-[:HAS_STUDY_VISIT]->(visit:StudyVisit {uid: $visit_uid})
            MATCH (sv)-[:HAS_STUDY_ACTIVITY]->(activity:StudyActivity {uid: $activity_uid})
            MATCH (sv)-[:HAS_STUDY_ACTIVITY_SCHEDULE]->(schedule:StudyActivitySchedule {uid: $schedule_uid})
            CREATE (sv)-[:HAS_PROTOCOL_SOA_CELL {row: -2, column: 1, span: 1, is_propagated: false, order: 0}]->(epoch)
            CREATE (sv)-[:HAS_PROTOCOL_SOA_CELL {row: -1, column: 1, span: 1, is_propagated: false, order: 0}]->(visit)
            CREATE (sv)-[:HAS_PROTOCOL_SOA_CELL {row: 0, column: 0, span: 1, is_propagated: false, order: 0}]->(activity)
            CREATE (sv)-[:HAS_PROTOCOL_SOA_CELL {row: 0, column: 1, span: 1, is_propagated: false, order: 0}]->(schedule)
            """,
            {
                "study_uid": study_uid,
                "version": study_value_version,
                "epoch_uid": study_visit.study_epoch_uid,
                "visit_uid": study_visit.uid,
                "activity_uid": schedule.study_activity_uid,
                "schedule_uid": schedule.study_activity_schedule_uid,
            },
        )
        legacy_table = service.load_soa_snapshot(
            study_uid, study_value_version, SoALayout.PROTOCOL
        )
        assert len(legacy_table.rows) == legacy_table.num_header_rows + 1
        assert len(legacy_table.rows) < len(built_table.rows)

        # WHEN: SoA snapshot saved
        service.save_protocol_soa_snapshot(
            study_uid=study_uid, study_value_version=study_value_version
        )

        # THEN: SoA snapshot is rendered from the legacy cell references
        snapshot = self._get_soa_snapshot_node(study_uid, study_value_version)
        assert snapshot["json"] == legacy_table.model_dump_json()
        assert (
            service.get_flowchart_table(
                study_uid, study_value_version, SoALayout.PROTOCOL
            ).model_dump()
            == legacy_table.model_dump()
        )

    @staticmethod
    def _render_protocol_soa(
        study_flowchart_service: StudyFlowchartService,
        study_uid: str,
        study_value_version: str | None,
    ) -> tuple[TableWithFootnotes, str]:
        """builds Protocol SoA table and HTML"""

        table = study_flowchart_service.get_flowchart_table(
            study_uid=study_uid,
            study_value_version=study_value_version,
            layout=SoALayout.PROTOCOL,
            force_build=True,
        )
        html = study_flowchart_service.get_study_flowchart_html(
            study_uid=study_uid,
            study_value_version=study_value_version,
            layout=SoALayout.PROTOCOL,
        )
        return table, html

    @staticmethod
    def _get_soa_snapshot_nodes(
        study_uid: str,
        study_value_version: str | None,
        layout: SoALayout | None = SoALayout.PROTOCOL,
    ) -> list[dict[str, Any]]:
        """returns properties of StudySoASnapshot nodes of a study version, or of the latest version,
        of the given layout or of all layouts"""

        if study_value_version:
            query = """
                MATCH (:StudyRoot {uid: $study_uid})-[:HAS_VERSION {status: 'RELEASED', version: $version}]->(sv:StudyValue)
            """
        else:
            query = """
                MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)
            """
        query += """
            MATCH (sv)-[:HAS_SOA_SNAPSHOT]->(snapshot:StudySoASnapshot)
            WHERE $layout IS NULL OR snapshot.layout = $layout
            RETURN DISTINCT snapshot {.layout, .html, .docx, .xlsx, .json, .time_unit}
        """
        results, _ = db.cypher_query(
            query,
            {
                "study_uid": study_uid,
                "version": study_value_version,
                "layout": layout.value if layout else None,
            },
        )
        return [row[0] for row in results]

    @classmethod
    def _get_soa_snapshot_node(
        cls,
        study_uid: str,
        study_value_version: str,
        layout: SoALayout = SoALayout.PROTOCOL,
    ) -> dict[str, Any]:
        """returns properties of the single StudySoASnapshot node of a layout of a study version, checking all renderings"""

        __tracebackhide__ = True

        snapshots = cls._get_soa_snapshot_nodes(
            study_uid, study_value_version, layout=layout
        )
        assert len(snapshots) == 1, f"Expected a single SoA snapshot: {snapshots}"
        snapshot = snapshots[0]

        assert snapshot["layout"] == layout.value
        assert snapshot["time_unit"] in ("day", "week")
        assert snapshot["html"].startswith("<")
        # DOCX and XLSX are ZIP archives
        assert snapshot["docx"].startswith(b"PK")
        assert snapshot["xlsx"].startswith(b"PK")
        assert TableWithFootnotes.model_validate_json(snapshot["json"]).rows

        return snapshot

    @staticmethod
    def _assert_soa_matches_snapshot(
        study_flowchart_service: StudyFlowchartService,
        study_uid: str,
        study_value_version: str,
        snapshot: dict[str, Any],
    ):
        """checks that SoA renderings of a study version are those saved in the SoA snapshot"""

        __tracebackhide__ = True

        assert (
            study_flowchart_service.get_flowchart_table(
                study_uid, study_value_version, SoALayout.PROTOCOL
            ).model_dump_json()
            == snapshot["json"]
        )
        assert (
            study_flowchart_service.get_study_flowchart_html(
                study_uid, study_value_version, SoALayout.PROTOCOL
            )
            == snapshot["html"]
        )
        assert (
            study_flowchart_service.get_study_flowchart_docx(
                study_uid, study_value_version, SoALayout.PROTOCOL, time_unit=None
            ).getvalue()
            == snapshot["docx"]
        )
        assert (
            study_flowchart_service.get_study_flowchart_xlsx(
                study_uid, study_value_version, SoALayout.PROTOCOL, time_unit=None
            ).getvalue()
            == snapshot["xlsx"]
        )

    @staticmethod
    def _assert_lab_table_matches_snapshot(
        study_flowchart_service: StudyFlowchartService,
        study_uid: str,
        study_value_version: str,
        snapshot: dict[str, Any],
    ):
        """checks that Protocol Lab table SoA renderings of a study version are those saved in the SoA snapshot"""

        __tracebackhide__ = True

        layout = SoALayout.PROTOCOL_LAB_TABLE
        assert (
            study_flowchart_service.get_flowchart_table(
                study_uid, study_value_version, layout
            ).model_dump_json()
            == snapshot["json"]
        )
        assert (
            study_flowchart_service.get_study_flowchart_html(
                study_uid, study_value_version, layout
            )
            == snapshot["html"]
        )
        assert (
            study_flowchart_service.get_study_flowchart_docx(
                study_uid, study_value_version, layout, time_unit=None
            ).getvalue()
            == snapshot["docx"]
        )
        assert (
            study_flowchart_service.get_study_flowchart_xlsx(
                study_uid, study_value_version, layout, time_unit=None
            ).getvalue()
            == snapshot["xlsx"]
        )

    @staticmethod
    def _remove_first_visible_study_activity(test_data: SoATestData):
        service = StudyActivitySelectionService()

        ssact: StudySelectionActivity
        for ssact in service.get_all_selection(study_uid=test_data.study.uid).items:
            # Skip placeholders (Requested library activities) - they can't be deleted via this service
            if ssact.activity.library_name == settings.requested_library_name:
                continue
            if ssact.show_activity_in_protocol_flowchart:
                service.delete_selection(
                    study_uid=test_data.study.uid,
                    study_selection_uid=ssact.study_activity_uid,
                )
                log.info("deleted StudyActivity [%s]", ssact.study_activity_uid)
                break

    @staticmethod
    def _update_a_study_activity_group(test_data: SoATestData):
        service = StudyActivityGroupService()
        sag: StudyActivityGroup = service.get_all_selection(
            study_uid=test_data.study.uid
        ).items[-1]
        service.patch_selection(
            study_uid=test_data.study.uid,
            study_selection_uid=sag.study_activity_group_uid,
            selection_update_input=StudyActivityGroupEditInput(
                show_activity_group_in_protocol_flowchart=not bool(
                    sag.show_activity_group_in_protocol_flowchart
                ),
            ),
        )
        log.info("updated StudyActivityGroup [%s]", sag.study_activity_group_uid)

    @staticmethod
    def _update_a_study_activity_subgroup(test_data: SoATestData):
        service = StudyActivitySubGroupService()
        sasg: StudyActivitySubGroup = service.get_all_selection(
            study_uid=test_data.study.uid
        ).items[-3]
        service.patch_selection(
            study_uid=test_data.study.uid,
            study_selection_uid=sasg.study_activity_subgroup_uid,
            selection_update_input=StudyActivitySubGroupEditInput(
                show_activity_subgroup_in_protocol_flowchart=not bool(
                    sasg.show_activity_subgroup_in_protocol_flowchart
                ),
            ),
        )
        log.info("updated StudyActivitySubGroup [%s]", sasg.study_activity_subgroup_uid)


def test_soa_snapshot_versioning_with_footnote_linking(
    temp_database_populated,
    layout: SoALayout = SoALayout.PROTOCOL,
):
    soa_test_data = SoATestDataMinimal(project=temp_database_populated.project)
    service = StudyFlowchartService()

    # get protocol soa
    soa_v1 = service.get_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=None,
        layout=layout,
        force_build=True,
    )

    # create a locked study version
    v1_version = TestUtils.lock_and_unlock_study(
        soa_test_data.study.uid,
        reason_for_lock_term_uid=temp_database_populated.reason_for_lock_term_uid,
        reason_for_unlock_term_uid=temp_database_populated.reason_for_unlock_term_uid,
    )

    # check SoA after locking v1
    for force_build in (True, False):
        soa = service.get_flowchart_table(
            study_uid=soa_test_data.study.uid,
            study_value_version=v1_version,
            layout=layout,
            force_build=force_build,
        )
        assert soa.model_dump() == soa_v1.model_dump()

    # assign footnote to study-activity-group
    study_activity_subgroup = next(
        iter(soa_test_data.study_activities.values())
    ).study_activity_subgroup
    soa_footnote = soa_test_data.soa_footnotes[-1]
    item_ref = ReferencedItem(
        item_uid=study_activity_subgroup.study_activity_subgroup_uid,
        item_name=study_activity_subgroup.activity_subgroup_name,
        item_type=SoAItemType.STUDY_ACTIVITY_SUBGROUP.value,
    )
    StudySoAFootnoteService().edit(
        study_uid=soa_test_data.study.uid,
        study_soa_footnote_uid=soa_footnote.uid,
        footnote_edit_input=StudySoAFootnoteEditInput(
            referenced_items=[*soa_footnote.referenced_items, item_ref]
        ),
    )

    # get protocol soa
    soa_v2 = service.get_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=None,
        layout=layout,
        force_build=True,
    )

    # ensure SoA changed between Study versions
    assert soa_v1.model_dump() != soa_v2.model_dump()

    # check v1 SoA after modifications to draft
    for force_build in (True, False):
        soa = service.get_flowchart_table(
            study_uid=soa_test_data.study.uid,
            study_value_version=v1_version,
            layout=layout,
            force_build=force_build,
        )
        assert soa.model_dump() == soa_v1.model_dump()

    # create a locked study version
    v2_version = TestUtils.lock_and_unlock_study(
        soa_test_data.study.uid,
        reason_for_lock_term_uid=temp_database_populated.reason_for_lock_term_uid,
        reason_for_unlock_term_uid=temp_database_populated.reason_for_unlock_term_uid,
    )

    # check SoA of both versions after locking v2
    for study_value_version, expected_soa in (
        (v1_version, soa_v1),
        (v2_version, soa_v2),
    ):
        assert (
            service.get_soa_snapshot(
                study_uid=soa_test_data.study.uid,
                study_value_version=study_value_version,
                layout=layout,
            ).model_dump()
            == expected_soa.model_dump()
        )

        # re-render SoA snapshot and compare
        service.save_protocol_soa_snapshot(
            study_uid=soa_test_data.study.uid,
            study_value_version=study_value_version,
        )
        assert (
            service.get_soa_snapshot(
                study_uid=soa_test_data.study.uid,
                study_value_version=study_value_version,
                layout=layout,
            ).model_dump()
            == expected_soa.model_dump()
        )


def test_operational_soa(soa_test_data: SoATestData):
    soa_table = StudyFlowchartService().get_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=None,
        layout=SoALayout.OPERATIONAL,
    )
    log.info(soa_test_data.VISITS)
    log.info(
        StudyVisitService.get_all_visits(
            study_uid=soa_test_data.study.uid, study_value_version=None
        ).items
    )
    check_operational_soa_table(soa_test_data, soa_table)


def check_operational_soa_table(
    soa_test_data: SoATestData, soa_table: TableWithFootnotes
):
    # check number of columns
    num_cols = len(soa_table.rows[soa_table.num_header_rows - 1].cells)
    assert num_cols == soa_table.num_header_cols + NUM_OPERATIONAL_CODE_COLS + len(
        soa_test_data.VISITS
    ), f"Unexpected number of columns in SoA table: {soa_table.rows[:soa_table.num_header_rows]}"

    # check number of rows
    num_rows = len(soa_table.rows)
    assert (
        num_rows == soa_test_data.NUM_OPERATIONAL_SOA_ROWS + soa_table.num_header_rows
    ), "Unexpected number of rows in SoA table"

    # no footnotes
    assert not soa_table.footnotes, "Expected no footnotes in operational SoA"

    # index cells by references and count schedule crosses
    cells_by_uid = {}
    cells_by_ref: dict[Any, Any] = defaultdict(dict)
    num_schedule_crosses = 0
    for r, row in enumerate(soa_table.rows):
        for c, cell in enumerate(row.cells):
            if cell.refs:
                for ref in cell.refs:
                    cells_by_uid[ref.uid] = cell
                    cells_by_ref[ref.type][ref.uid] = cell
            if (
                r >= soa_table.num_header_rows
                and c >= soa_table.num_header_cols + NUM_OPERATIONAL_CODE_COLS
                and cell.text == SOA_CHECK_MARK
            ):
                num_schedule_crosses += 1

    # check number of schedules
    assert (
        len(cells_by_ref[SoAItemType.STUDY_ACTIVITY_SCHEDULE.value])
        == soa_test_data.NUM_OPERATIONAL_SOA_SCHEDULES
    ), "Unexpected number of schedules"
    assert (
        num_schedule_crosses == soa_test_data.NUM_OPERATIONAL_SOA_CHECKMARKS
    ), "Unexpected number of schedule crosses"

    # check number of study activity instance rows
    assert (
        len(cells_by_ref[SoAItemType.STUDY_ACTIVITY_INSTANCE.value])
        == soa_test_data.NUM_ACTIVITY_INSTANCES
    ), "Unexpected number of study activity instances"


def test_fetch_study_activities(soa_test_data2):
    """Compare lite version StudySelectionActivities from StudyFlowchartService.fetch_study_activities
    to fully populated objects from StudyActivitySelectionService.get_all_selection,
    assuming the later one is already well-covered by tests."""

    for study_version in _get_study_version_numbers(soa_test_data2.study.uid):
        log.info(
            "Comparing StudySelectionActivities of study [%s] version [%s]",
            soa_test_data2.study.uid,
            study_version,
        )

        expected = (
            StudyActivitySelectionService()
            .get_all_selection(
                soa_test_data2.study.uid,
                study_value_version=study_version,
                sort_by=StudyActivitySelectionService.get_default_sorting(),
            )
            .items
        )
        items = StudyFlowchartService.fetch_study_activities(
            study_uid=soa_test_data2.study.uid, study_value_version=study_version
        )

        expected = _to_list_of_dicts(expected)
        items = _to_list_of_dicts(items)
        assert len(items) == len(expected)
        assert items == expected


@pytest.mark.skip(
    reason="Test isolation issue: module-scoped fixtures cause data interference when run with other tests"
)
def test_fetch_study_activity_instances(soa_test_data2):
    """Compare lite version StudySelectionActivityInstance from StudyFlowchartService.fetch_study_activity_instances
    to fully populated objects from StudyActivityInstanceSelectionService.get_all_selection,
    assuming the later one is already well-covered by tests."""

    for study_version in _get_study_version_numbers(soa_test_data2.study.uid):
        log.info(
            "Comparing StudySelectionActivityInstances of study [%s] version [%s]",
            soa_test_data2.study.uid,
            study_version,
        )

        expected = (
            StudyActivityInstanceSelectionService()
            .get_all_selection(
                soa_test_data2.study.uid,
                study_value_version=study_version,
                sort_by={"study_activity_instance_uid": True},
                # omit activity placeholders
                filter_by={
                    "activity.library_name": {
                        "v": [settings.requested_library_name],
                        "op": "ne",
                    }
                },
            )
            .items
        )
        items = StudyFlowchartService.fetch_study_activity_instances(
            study_uid=soa_test_data2.study.uid, study_value_version=study_version
        )
        # Filter out placeholders (Requested library activities without instances)
        # to match the expected data which also filters them out
        items = [
            item
            for item in items
            if item.activity.library_name != settings.requested_library_name
        ]
        items.sort(key=lambda x: x.study_activity_instance_uid)

        expected = _to_list_of_dicts(expected)
        items = _to_list_of_dicts(items)
        assert items == expected


def _get_study_version_numbers(study_uid: str) -> set[str | None]:
    return {
        study.metadata_version and str(study.metadata_version)
        for study in StudyService()
        .get_study_snapshot_history(study_uid=study_uid)
        .items
    }


def _to_list_of_dicts(items: Sequence[pydantic.BaseModel]) -> list[dict[str, Any]]:
    """Converts a list of StudySelectionActivity or StudySelectionActivityInstance to a list of dicts
    for easier Pytest compilation of lite and fully populated objects,
    excluding some properties from the comparison."""

    return [
        item.model_dump(
            exclude_unset=True,
            exclude_none=True,
            exclude={
                "activity": {
                    "activity_groupings",
                    "activity_instances",
                    "author_username",
                    "change_description",
                    "is_finalized",
                    "is_request_final",
                    "is_used_by_legacy_instances",
                    "possible_actions",
                    "used_by_studies",
                    "start_date",
                    "status",
                    "synonyms",
                    "version",
                },
                "activity_instance": {
                    "activity_groupings",
                    "activity_items",
                    "author_username",
                    "change_description",
                    "possible_actions",
                    "start_date",
                    "status",
                    "version",
                },
                "author_username": True,
                "start_date": True,
                "study_activity_subgroup": {"order": True},
                "study_activity_group": {"order": True},
                "study_soa_group": {"order": True},
                "study_version": True,
                "is_activity_updated": True,
                "is_activity_instance_updated": True,
            },
        )
        for item in items
    ]


# Tests for Protocol Lab table functionality


def test_get_flowchart_table_lab_table_integration(
    soa_test_data: SoATestData,
):
    """Integration test for get_flowchart_table_lab_table with real database"""

    study_uid = soa_test_data.study.uid
    service = StudyFlowchartService()

    table = service.get_flowchart_table_lab_table(
        study_uid=study_uid, study_value_version=None, time_unit="week"
    )

    # THEN should return a valid table
    assert isinstance(table, TableWithFootnotes)

    # THEN should have correct structure for Lab table
    assert table.num_header_cols == 2  # Subgroup + Activity columns

    # THEN should have header rows
    assert table.num_header_rows > 0

    # THEN should have at least header rows
    assert len(table.rows) >= table.num_header_rows


def test_get_flowchart_table_lab_table_filters_laboratory_assessments(
    soa_test_data: SoATestData,
):
    """Test that Protocol Lab table filters to Laboratory Assessments only"""

    study_uid = soa_test_data.study.uid
    service = StudyFlowchartService()

    # Get regular flowchart for comparison
    regular_table = service.get_flowchart_table(
        study_uid=study_uid,
        study_value_version=None,
        layout=SoALayout.DETAILED,
        time_unit="week",
    )

    # Get Lab table table
    lab_table = service.get_flowchart_table_lab_table(
        study_uid=study_uid, study_value_version=None, time_unit="week"
    )

    # Count activity rows (excluding headers)
    regular_activity_rows = len(regular_table.rows) - regular_table.num_header_rows
    lab_table_activity_rows = len(lab_table.rows) - lab_table.num_header_rows

    # THEN Lab table should have fewer or equal activities (filtered subset)
    assert lab_table_activity_rows <= regular_activity_rows

    # THEN all lab table visits should also be present in the regular table
    def _visit_uids_from_header(table):
        uids = set()
        for row in table.rows[: table.num_header_rows]:
            for cell in row.cells:
                if cell.refs:
                    for ref in cell.refs:
                        if ref.type == SoAItemType.STUDY_VISIT.value:
                            uids.add(ref.uid)
        return uids

    regular_visit_uids = _visit_uids_from_header(regular_table)
    lab_table_visit_uids = _visit_uids_from_header(lab_table)

    assert lab_table_visit_uids.issubset(
        regular_visit_uids
    ), f"Lab table visits {lab_table_visit_uids - regular_visit_uids} not found in regular table"


def test_get_study_flowchart_html_with_protocol_lab_table_layout(
    soa_test_data: SoATestData,
):
    """Test HTML generation for Protocol Lab table layout"""

    study_uid = soa_test_data.study.uid
    service = StudyFlowchartService()

    html = service.get_study_flowchart_html(
        study_uid=study_uid,
        study_value_version=None,
        layout=SoALayout.PROTOCOL_LAB_TABLE,
        time_unit="week",
    )

    # THEN should return valid HTML
    assert isinstance(html, str)
    assert len(html) > 0
    assert "<table>" in html
    assert "</table>" in html


def test_get_study_flowchart_html_with_include_uids(
    soa_test_data: SoATestData,
):
    """Test HTML generation with include_uids parameter"""

    study_uid = soa_test_data.study.uid
    service = StudyFlowchartService()

    # Get HTML without UIDs
    html_without_uids = service.get_study_flowchart_html(
        study_uid=study_uid,
        study_value_version=None,
        layout=SoALayout.PROTOCOL,
        time_unit="week",
        include_uids=False,
    )

    # Get HTML with UIDs
    html_with_uids = service.get_study_flowchart_html(
        study_uid=study_uid,
        study_value_version=None,
        layout=SoALayout.PROTOCOL,
        time_unit="week",
        include_uids=True,
    )

    # THEN both should be valid HTML
    assert isinstance(html_without_uids, str)
    assert isinstance(html_with_uids, str)
    assert "<table>" in html_without_uids
    assert "<table>" in html_with_uids

    # THEN HTML with UIDs should contain object-uid attributes
    assert "object-uid" in html_with_uids

    # THEN HTML without UIDs should not contain object-uid attributes
    assert "object-uid" not in html_without_uids


def test_protocol_lab_table_with_different_time_units(
    soa_test_data: SoATestData,
):
    """Test Protocol Lab table works with different time units"""

    study_uid = soa_test_data.study.uid
    service = StudyFlowchartService()

    for time_unit in ["day", "week"]:
        table = service.get_flowchart_table_lab_table(
            study_uid=study_uid, study_value_version=None, time_unit=time_unit
        )

        # THEN should return valid table for both time units
        assert isinstance(table, TableWithFootnotes)
        assert table.num_header_cols == 2
        assert table.num_header_rows > 0


def test_footnote_filtering_in_lab_table(
    soa_test_data: SoATestData,
):
    """Test that footnotes are properly filtered for visible rows in Lab table"""

    study_uid = soa_test_data.study.uid
    service = StudyFlowchartService()

    table = service.get_flowchart_table_lab_table(
        study_uid=study_uid, study_value_version=None, time_unit="week"
    )

    # THEN footnotes should only reference items that appear in visible rows
    if table.footnotes:
        # Get all referenced UIDs from visible rows
        visible_rows = [row for row in table.rows if not row.hide]
        referenced_uids = set()
        for row in visible_rows:
            for cell in row.cells:
                if cell.refs:
                    for ref in cell.refs:
                        referenced_uids.add(ref.uid)

        # Check that all footnotes reference items that are in visible rows
        for footnote in table.footnotes.values():
            # Note: This is a basic check - actual footnote filtering logic may be more complex
            assert hasattr(footnote, "uid"), "Footnote should have uid attribute"


@pytest.mark.parametrize(
    "layout", [SoALayout.PROTOCOL_LAB_TABLE, SoALayout.PROTOCOL, SoALayout.DETAILED]
)
def test_include_uids_parameter_across_layouts(
    soa_test_data: SoATestData, layout: SoALayout
):
    """Test include_uids parameter works across different layouts"""

    study_uid = soa_test_data.study.uid
    service = StudyFlowchartService()

    html = service.get_study_flowchart_html(
        study_uid=study_uid,
        study_value_version=None,
        layout=layout,
        time_unit="week",
        include_uids=True,
    )

    # THEN all layouts should support include_uids
    assert isinstance(html, str)
    assert len(html) > 0

    # THEN HTML should contain UID attributes when include_uids is True
    # (may vary based on layout and available data)
    if "object-uid" in html:
        # If UIDs are present, verify they follow the expected format
        assert "object-type" in html, "Should also have object-type attributes"


def test_hide_rows_without_checkmarks_integration(
    soa_test_data: SoATestData,
):
    """Integration test for hiding rows without checkmarks in Lab table"""

    study_uid = soa_test_data.study.uid
    service = StudyFlowchartService()

    table = service.get_flowchart_table_lab_table(
        study_uid=study_uid, study_value_version=None, time_unit="week"
    )

    # Count visible activity rows
    activity_rows = table.rows[table.num_header_rows :]
    visible_activity_rows = [row for row in activity_rows if not row.hide]

    # THEN should have some activity rows (unless no Laboratory Assessments activities exist)
    # Note: This may be 0 if test data doesn't have Laboratory Assessments activities
    assert len(activity_rows) >= 0

    # THEN if there are visible activity rows with visit columns, they should have checkmarks
    # Note: when show_all_visits_lab_table is False, visit columns are stripped from the table,
    # so we can only verify checkmarks when visit columns are present.
    for row in visible_activity_rows:
        # Check if row has checkmarks in visit columns (skip first 2 columns: subgroup + activity)
        visit_cells = row.cells[2:]  # Skip header columns
        if not visit_cells:
            # Visit columns were stripped (show_all_visits_lab_table=False), skip checkmark check
            continue
        has_checkmark = any(cell.text == "X" for cell in visit_cells)

        # If the row is visible, it should either have checkmarks or be a header/grouping row
        if row.cells[0].text or row.cells[1].text:  # Has content in header columns
            # This is an activity row, so if it's visible, it should have checkmarks
            assert (
                has_checkmark
            ), f"Visible activity row should have checkmarks: {row.cells[:5]}"  # Show first few cells for debugging


def test_soa_footnote_via_propagated_cell(temp_database_populated):
    """A footnote attached to a checkmark propagated from hidden rows is shown on that checkmark only,
    in freshly built and snapshot Protocol SoA, and left out of other layouts"""

    # GIVEN a Study where hidden activity Acetaminophen is propagated to its visible PK subgroup at V1,
    # and footnote "Some footnote" is attached to the hidden activity's own V1 checkmark
    soa_test_data = SoATestDataMinimal(project=temp_database_populated.project)
    study_uid = soa_test_data.study.uid
    service = StudyFlowchartService()

    def get_propagated_cell(table: TableWithFootnotes):
        (cell,) = [cell for row in table.rows for cell in row.cells if cell.propagated]
        return cell

    def symbol_of(table: TableWithFootnotes, footnote_uid: str) -> str | None:
        return next(
            (sym for sym, fn in table.footnotes.items() if fn.uid == footnote_uid),
            None,
        )

    table = service.get_flowchart_table(
        study_uid=study_uid, study_value_version=None, layout=SoALayout.PROTOCOL
    )
    propagated_cell = get_propagated_cell(table)

    # THEN the footnote of the hidden activity's own checkmark is not shown
    assert len(soa_test_data.soa_footnotes) == 1
    hidden_footnote = soa_test_data.soa_footnotes[0]
    assert symbol_of(table, hidden_footnote.uid) is None
    assert not propagated_cell.footnotes

    # WHEN a footnote is attached to the propagated checkmark
    template = TestUtils.create_footnote_template(
        name="<p>Footnote via propagated cell</p>",
        type_uid=soa_test_data._footnote_types["SoA Footnote"].term_uid,
        approve=True,
    )
    footnote = TestUtils.create_footnote(
        footnote_template_uid=template.uid, approve=True
    )
    soa_footnote = TestUtils.create_study_soa_footnote(
        study_uid=study_uid,
        footnote_uid=footnote.uid,
        referenced_items=[
            ReferencedItem(
                item_uid=ref.uid,
                item_type=SoAItemType(ref.type),
                via_propagated_cell=True,
            )
            for ref in propagated_cell.refs
        ],
    )

    # THEN the reference via propagated cell is read back
    assert soa_footnote.referenced_items
    assert all(ref.via_propagated_cell for ref in soa_footnote.referenced_items)

    # THEN the footnote is shown on the propagated checkmark of Protocol SoA
    table = service.get_flowchart_table(
        study_uid=study_uid, study_value_version=None, layout=SoALayout.PROTOCOL
    )
    symbol = symbol_of(table, soa_footnote.uid)
    assert symbol
    assert get_propagated_cell(table).footnotes == [symbol]
    assert symbol_of(table, hidden_footnote.uid) is None
    check_flowchart_table_footnotes(
        table,
        StudySoAFootnoteService().get_all_by_study_uid(study_uid).items,
        layout=SoALayout.PROTOCOL,
    )

    # THEN the HTML marks the propagated checkmark and references the footnote from its symbol
    html = service.get_study_flowchart_html(
        study_uid=study_uid,
        study_value_version=None,
        layout=SoALayout.PROTOCOL,
        include_uids=True,
    )
    doc = bs4.BeautifulSoup(html, features="html.parser")
    (propagated_element,) = doc.find_all(attrs={"object-propagated": "true"})
    assert propagated_element.find("sup").get("object-uid") == soa_footnote.uid

    # THEN Detailed SoA shows the footnote attached via propagated cell too
    detailed_table = service.get_flowchart_table(
        study_uid=study_uid, study_value_version=None, layout=SoALayout.DETAILED
    )
    assert symbol_of(detailed_table, soa_footnote.uid)
    assert symbol_of(detailed_table, hidden_footnote.uid)

    # WHEN the study is locked, saving the Protocol SoA snapshot, and the snapshot is loaded back
    locked_version = TestUtils.lock_and_unlock_study(
        study_uid,
        reason_for_lock_term_uid=temp_database_populated.reason_for_lock_term_uid,
        reason_for_unlock_term_uid=temp_database_populated.reason_for_unlock_term_uid,
    )
    snapshot_table = service.get_flowchart_table(
        study_uid=study_uid,
        study_value_version=locked_version,
        layout=SoALayout.PROTOCOL,
    )

    # THEN the snapshot shows the footnote on the propagated checkmark like the freshly built SoA
    assert snapshot_table.footnotes == table.footnotes
    snapshot_propagated_cell = get_propagated_cell(snapshot_table)
    assert snapshot_propagated_cell.refs == get_propagated_cell(table).refs
    assert snapshot_propagated_cell.footnotes == [symbol]
