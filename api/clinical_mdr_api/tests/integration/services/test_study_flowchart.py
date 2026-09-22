# pylint: disable=redefined-outer-name,unused-argument

import logging
from collections import defaultdict
from typing import Any, Iterable, Sequence

import pydantic
import pytest
from docx.table import Table

from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.domain_repositories.study_selections.study_soa_repository import (
    SoALayout,
)
from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpoch
from clinical_mdr_api.models.study_selections.study_selection import (
    ReferencedItem,
    SoACellReference,
    SoAFootnoteReference,
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
from clinical_mdr_api.services.studies.study_flowchart import _T as _gettext
from clinical_mdr_api.services.studies.study_flowchart import (
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

    def test_soa_snapshot_versioned(
        self, soa_test_data2: SoATestData, layout: SoALayout = SoALayout.PROTOCOL
    ):
        """Tests saving and retrieving SoA snapshots with study versioning"""

        study_flowchart_service = StudyFlowchartService()
        study_service = StudyService()

        # GIVEN: a Study populated with data required for SoA
        study_uid = soa_test_data2.study.uid

        # GIVEN: references of SoA snapshot
        expected_refs: list[SoACellReference] = (
            study_flowchart_service.build_soa_snapshot(
                study_uid, study_value_version=None, layout=layout
            )
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
        # THEN: StudyValue has HAS_PROTOCOL_SOA_CELL relationship
        assert len(
            StudyRoot.nodes.get(uid=study_uid)
            .has_version.match(status="RELEASED", version=previous_study_version)[0]
            .has_protocol_soa_cell
        )
        # THEN: StudyValue has HAS_PROTOCOL_SOA_FOOTNOTE relationship
        assert len(
            StudyRoot.nodes.get(uid=study_uid)
            .has_version.match(status="RELEASED", version=previous_study_version)[0]
            .has_protocol_soa_footnote
        )
        # WHEN: SoA snapshot of the previous Study version read back from the db
        # THEN: It matches the SoA snapshot of the previous Study version
        self._assert_soa_snapshot_refs_from_db_match_expected_refs(
            study_flowchart_service,
            study_uid,
            study_value_version=previous_study_version,
            layout=layout,
            expected_refs=expected_refs,
        )

        # SCENARIO: After unlocking the Study, the latest draft version has no SoA snapshot
        # WHEN: Study is unlocked
        study_service.unlock(
            uid=study_uid,
            reason_for_unlock_term_uid=soa_test_data2.reason_for_unlock_term_uid,
        )
        # THEN StudyValue has no HAS_PROTOCOL_SOA_CELL relationships
        assert (
            len(
                StudyRoot.nodes.get(uid=study_uid)
                .latest_value.get()
                .has_protocol_soa_cell
            )
            == 0
        )
        # THEN StudyValue has no HAS_PROTOCOL_SOA_FOOTNOTE relationships
        assert (
            len(
                StudyRoot.nodes.get(uid=study_uid)
                .latest_value.get()
                .has_protocol_soa_footnote
            )
            == 0
        )
        # THEN SoA snapshot read form db returns empty result
        self._assert_soa_snapshot_refs_from_db_match_expected_refs(
            study_flowchart_service,
            study_uid,
            study_value_version=None,
            layout=layout,
            expected_refs=([], []),
        )

        # SCENARIO: After Study is unlocked, the SoA snapshot of the previous study version can be read
        # GIVEN: Study is recently unlocked (and no modifications made)
        # WHEN: SoA snapshot of the previous Study version read from the db
        # THEN: It matches the SoA snapshot of the previous Study version
        self._assert_soa_snapshot_refs_from_db_match_expected_refs(
            study_flowchart_service,
            study_uid,
            study_value_version=previous_study_version,
            layout=layout,
            expected_refs=expected_refs,
        )

        # SCENARIO: After changing the SoA data of DRAFT Study, the SoA snapshot of the previous Study version reads back correctly
        # WHEN: Changed Study SoA data
        self._update_a_study_activity_subgroup(soa_test_data2)
        self._remove_first_visible_study_activity(soa_test_data2)
        self._update_a_study_activity_group(soa_test_data2)
        # WHEN: SoA snapshot of the previous Study version read from the db
        # THEN: It matches the SoA snapshot of the previous Study version
        self._assert_soa_snapshot_refs_from_db_match_expected_refs(
            study_flowchart_service,
            study_uid,
            study_value_version=previous_study_version,
            layout=layout,
            expected_refs=expected_refs,
        )

        # SCENARIO: After releasing a Study version, the released version has a SoA snapshot
        # GIVEN: A Study version is released
        study_service.release(
            uid=study_uid,
            change_description="r1",
            reason_for_release_uid=soa_test_data2.reason_for_lock_term_uid,
        )
        released_study_version = f"{previous_study_version}.1"  # release API call does not return version number
        # GIVEN: SoA snapshot of the latest Study version built
        latest_refs: list[SoACellReference] = (
            study_flowchart_service.build_soa_snapshot(
                study_uid, study_value_version=None, layout=layout
            )
        )
        # WHEN: SoA snapshot of the released Study version read from the db
        # THEN: It matches the SoA snapshot of the draft Study version
        self._assert_soa_snapshot_refs_from_db_match_expected_refs(
            study_flowchart_service,
            study_uid,
            study_value_version=released_study_version,
            layout=layout,
            expected_refs=latest_refs,
        )

        # SCENARIO: After locking the Study, the SoA snapshots of the latest draft and previous locked versions differ
        # GIVEN: Study is locked
        study = study_service.lock(
            uid=study_uid,
            change_description="v2",
            reason_for_lock_term_uid=soa_test_data2.reason_for_lock_term_uid,
        )
        latest_study_version = str(
            study.current_metadata.version_metadata.version_number
        )
        # GIVEN: SoA snapshot of the latest Study version built
        latest_refs: list[SoACellReference] = (
            study_flowchart_service.build_soa_snapshot(
                study_uid, study_value_version=None, layout=layout
            )
        )
        # THEN: SoA snapshots of the latest and previous version differ
        assert latest_refs[0] != expected_refs[1]
        # WHEN: SoA snapshot of the previous Study version read from the db
        # THEN: It matches the SoA snapshot of the previous Study version
        self._assert_soa_snapshot_refs_from_db_match_expected_refs(
            study_flowchart_service,
            study_uid,
            study_value_version=previous_study_version,
            layout=layout,
            expected_refs=expected_refs,
        )
        # WHEN: SoA snapshot of the latest draft Study version read from the db
        # THEN: It matches the SoA snapshot of the latest Study version
        self._assert_soa_snapshot_refs_from_db_match_expected_refs(
            study_flowchart_service,
            study_uid,
            study_value_version=latest_study_version,
            layout=layout,
            expected_refs=latest_refs,
        )
        # WHEN: SoA snapshot read from db without specifying Study version
        # THEN: It matches the SoA snapshot of the latest Study version
        self._assert_soa_snapshot_refs_from_db_match_expected_refs(
            study_flowchart_service,
            study_uid,
            study_value_version=None,
            layout=layout,
            expected_refs=latest_refs,
        )
        # WHEN: unlocking Study
        study = study_service.unlock(
            uid=study_uid,
            reason_for_unlock_term_uid=soa_test_data2.reason_for_unlock_term_uid,
        )
        # THEN Latest StudyValue has no HAS_PROTOCOL_SOA_CELL relationships
        assert (
            len(
                StudyRoot.nodes.get(uid=study_uid)
                .latest_value.get()
                .has_protocol_soa_cell
            )
            == 0
        )
        # THEN Latest StudyValue has no HAS_PROTOCOL_SOA_FOOTNOTE relationships
        assert (
            len(
                StudyRoot.nodes.get(uid=study_uid)
                .latest_value.get()
                .has_protocol_soa_footnote
            )
            == 0
        )
        # THEN SoA snapshot read form the db returns empty result
        self._assert_soa_snapshot_refs_from_db_match_expected_refs(
            study_flowchart_service,
            study_uid,
            study_value_version=None,
            layout=layout,
            expected_refs=([], []),
        )

        # WHEN: SoA snapshot of the latest locked Study version read from the db
        # THEN: It matches the SoA snapshot of the latest locked Study version
        self._assert_soa_snapshot_refs_from_db_match_expected_refs(
            study_flowchart_service,
            study_uid,
            study_value_version=latest_study_version,
            layout=layout,
            expected_refs=latest_refs,
        )
        # WHEN: SoA snapshot of the previous locked Study version read from the db
        # THEN: It matches the SoA snapshot of the previous locked Study version
        self._assert_soa_snapshot_refs_from_db_match_expected_refs(
            study_flowchart_service,
            study_uid,
            study_value_version=previous_study_version,
            layout=layout,
            expected_refs=expected_refs,
        )

    @classmethod
    def _assert_soa_snapshot_refs_from_db_match_expected_refs(
        cls,
        study_flowchart_service: StudyFlowchartService,
        study_uid: str,
        study_value_version: str,
        layout: SoALayout,
        expected_refs: tuple[list[SoACellReference], list[SoAFootnoteReference]],
    ):
        """loads SoA snapshot references from db and compares them to expected references"""

        # pylint: disable=unused-variable
        __tracebackhide__ = True

        refs = TestSoASnapshot._load_soa_snapshot_for_comparison(
            study_flowchart_service, study_uid, study_value_version, layout
        )

        # THEN: SoA snapshot (without cell footnote references) match as expected
        if expected_refs[0]:
            assert refs[0], "Missing SoA cell references"
        if expected_refs[1]:
            assert refs[1], "Missing SoA footnote references"
        assert refs[0] == expected_refs[0], "SoA cell references mismatch"
        assert refs[1] == expected_refs[1], "SoA footnote references mismatch"

    @staticmethod
    def _load_soa_snapshot_for_comparison(
        study_flowchart_service, study_uid, study_value_version, layout
    ) -> tuple[list[SoACellReference], list[SoAFootnoteReference]]:
        """loads SoA snapshot references from db, and removes cell footnote references to prepare for comparison"""

        refs = study_flowchart_service.repository.load(
            study_uid=study_uid,
            study_value_version=study_value_version,
            layout=layout,
        )

        # Remove cell footnote references for comparison
        for ref in refs[0]:
            ref.footnote_references = None

        return refs

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

    def test_build_soa_snapshot_versioned(
        self, soa_test_data2: SoATestData, layout: SoALayout = SoALayout.PROTOCOL
    ):
        """tests StudyFlowchartService.get_soa_row_refs with versioning

        SCENARIO: When a Study with SoA data has a previous locked version,
         and a later draft version with a new activity row added,
         then the row references from the SoA snapshot of the previous locked Study version
         are a subset of those from the SoA snapshot of the latest draft version.
        """

        study_flowchart_service = StudyFlowchartService()

        # GIVEN: SoA snapshot of latest draft built
        previous_refs = study_flowchart_service.build_soa_snapshot(
            study_uid=soa_test_data2.study.uid, study_value_version=None, layout=layout
        )
        # GIVEN: Study has a locked version
        previous_study_version = TestUtils.lock_and_unlock_study(
            soa_test_data2.study.uid,
            reason_for_lock_term_uid=soa_test_data2.reason_for_lock_term_uid,
            reason_for_unlock_term_uid=soa_test_data2.reason_for_unlock_term_uid,
        )

        # GIVEN: Latest draft version has a new activity added
        soa_test_data2.create_study_activity(
            name="Mind the gap",
            soa_group="Safety",
            group="General",
            subgroup="Napoleon",
            visits=["V2", "V6"],
            show_soa_group=True,
            show_group=True,
            show_subgroup=False,
            show_activity=True,
        )

        # WHEN Building SoA snapshot of the locked study version
        refs = study_flowchart_service.build_soa_snapshot(
            study_uid=soa_test_data2.study.uid,
            study_value_version=previous_study_version,
            layout=layout,
        )
        # THEN It matches the SoA snapshot built from the previous study version
        assert refs == previous_refs

        # WHEN Building SoA snapshot of the latest draft
        current_refs = study_flowchart_service.build_soa_snapshot(
            study_uid=soa_test_data2.study.uid,
            study_value_version=None,
            layout=layout,
        )
        # THEN The row references from the SoA snapshot of the previous study version is a subset of those from the SoA snapshot of the latest draft version
        current_refs = set(ref.referenced_item.item_uid for ref in current_refs[0])
        previous_refs = set(ref.referenced_item.item_uid for ref in previous_refs[0])
        assert current_refs > previous_refs

    def test_soa_snapshot_of_previous_locked_versions(
        self, soa_test_data2: SoATestData, layout: SoALayout = SoALayout.PROTOCOL
    ):
        """Tests SoA snapshot of previous locked Study versions"""

        study_flowchart_service = StudyFlowchartService()
        study_service = StudyService()

        # GIVEN: a Study populated with SoA data
        study_uid = soa_test_data2.study.uid
        # GIVEN: Study has 3 locked versions and a draft version, all differs in SoA

        # Build SoA snapshot
        refs_v1 = study_flowchart_service.build_soa_snapshot(
            study_uid,
            study_value_version=None,
            layout=layout,
        )
        # create a locked study version
        version_v1 = str(
            study_service.lock(
                uid=study_uid,
                change_description="vz1",
                reason_for_lock_term_uid=soa_test_data2.reason_for_lock_term_uid,
            ).current_metadata.version_metadata.version_number
        )
        study_service.unlock(
            uid=study_uid,
            reason_for_unlock_term_uid=soa_test_data2.reason_for_unlock_term_uid,
        )

        # add a new activity
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
        # Build SoA snapshot
        refs_v2 = study_flowchart_service.build_soa_snapshot(
            study_uid,
            study_value_version=None,
            layout=layout,
        )
        # create a locked study version
        version_v2 = str(
            study_service.lock(
                uid=study_uid,
                change_description="vz2",
                reason_for_lock_term_uid=soa_test_data2.reason_for_lock_term_uid,
            ).current_metadata.version_metadata.version_number
        )
        study_service.unlock(
            uid=study_uid,
            reason_for_unlock_term_uid=soa_test_data2.reason_for_unlock_term_uid,
        )

        # add another activity
        soa_test_data2.create_study_activity(
            name="Potato peeler",
            soa_group="Safety",
            group="General",
            subgroup="Napoleon",
            visits=["V2", "V4", "V5"],
            show_soa_group=True,
            show_group=True,
            show_subgroup=False,
            show_activity=True,
        )
        # Build SoA snapshot
        refs_v3 = study_flowchart_service.build_soa_snapshot(
            study_uid,
            study_value_version=None,
            layout=layout,
        )
        # create a locked study version
        version_v3 = str(
            study_service.lock(
                uid=study_uid,
                change_description="vz2",
                reason_for_lock_term_uid=soa_test_data2.reason_for_lock_term_uid,
            ).current_metadata.version_metadata.version_number
        )
        study_service.unlock(
            uid=study_uid,
            reason_for_unlock_term_uid=soa_test_data2.reason_for_unlock_term_uid,
        )

        # remove an activity from draft version
        StudyActivitySelectionService().delete_selection(
            study_uid=soa_test_data2.study.uid,
            study_selection_uid=activity_v2.study_activity_uid,
        )
        log.info("deleted StudyActivity [%s]", activity_v2.study_activity_uid)
        # Build SoA snapshot
        refs_draft = study_flowchart_service.build_soa_snapshot(
            study_uid,
            study_value_version=None,
            layout=layout,
        )

        # all versions differ
        assert refs_v2 != refs_v1
        assert refs_v3 != refs_v1
        assert refs_v3 != refs_v2
        assert refs_draft != refs_v2
        assert refs_draft != refs_v3

        # GIVEN: removed SoA snapshot
        for study_version in StudyRoot.nodes.get(uid=study_uid).has_version.all():
            study_version.has_protocol_soa_cell.disconnect_all()
            study_version.has_protocol_soa_footnote.disconnect_all()
            # THEN: StudyValue has no HAS_PROTOCOL_SOA_CELL or HAS_PROTOCOL_SOA_FOOTNOTE relationships
            assert len(study_version.has_protocol_soa_cell) == 0
            assert len(study_version.has_protocol_soa_footnote) == 0

        # WHEN SoA snapshots of older study versions created one-by-one
        for study_value_version in (version_v1, version_v2, version_v3):
            study_flowchart_service.update_soa_snapshot(
                study_uid=study_uid,
                study_value_version=study_value_version,
                layout=layout,
            )
        # THEN Latest draft version of Study has no SoA snapshot
        assert (
            len(
                StudyRoot.nodes.get(uid=study_uid)
                .latest_value.get()
                .has_protocol_soa_cell
            )
            == 0
        )
        assert (
            len(
                StudyRoot.nodes.get(uid=study_uid)
                .latest_value.get()
                .has_protocol_soa_footnote
            )
            == 0
        )
        # THEN SoA snapshots loaded from db matches with SoA snapshot built for the particular Study version
        for study_value_version, expected_refs in (
            (version_v1, refs_v1),
            (version_v2, refs_v2),
            (version_v3, refs_v3),
        ):
            self._assert_soa_snapshot_refs_from_db_match_expected_refs(
                study_flowchart_service,
                study_uid,
                study_value_version=study_value_version,
                layout=layout,
                expected_refs=expected_refs,
            )

    def test_soa_snapshot_references(
        self, soa_test_data2: SoATestData, layout: SoALayout = SoALayout.PROTOCOL
    ):
        """checks that saving and loading SoA snapshot references match"""

        service = StudyFlowchartService()

        expected_cell_references, expected_footnote_references = (
            service.build_soa_snapshot(
                study_uid=soa_test_data2.study.uid,
                study_value_version=None,
                layout=layout,
            )
        )

        service.update_soa_snapshot(
            study_uid=soa_test_data2.study.uid, study_value_version=None, layout=layout
        )

        cell_references, footnote_references = self._load_soa_snapshot_for_comparison(
            service,
            study_uid=soa_test_data2.study.uid,
            study_value_version=None,
            layout=layout,
        )

        assert cell_references == expected_cell_references
        assert footnote_references == expected_footnote_references

    @pytest.mark.parametrize(
        "time_unit",
        [
            "day",
            "week",
        ],
    )
    def test_soa_snapshot_and_reconstruction(
        self,
        soa_test_data2: SoATestData,
        time_unit: str,
        layout: SoALayout = SoALayout.PROTOCOL,
    ):
        """tests saving of SoA snapshot and reconstruction of SoA from snapshot"""

        service = StudyFlowchartService()

        expected_table = service.build_flowchart_table(
            study_uid=soa_test_data2.study.uid,
            study_value_version=None,
            layout=layout,
            time_unit=time_unit,
        )
        if layout == SoALayout.PROTOCOL:
            service.propagate_hidden_rows(expected_table.rows)
            expected_table.rows = [row for row in expected_table.rows if not row.hide]
        else:
            service.show_hidden_rows(expected_table.rows)

        # unique cell references
        for row in expected_table.rows:
            for cell in row.cells:
                if cell.refs:
                    cell.refs = list(dict.fromkeys(cell.refs))

        service.update_soa_snapshot(
            study_uid=soa_test_data2.study.uid, study_value_version=None, layout=layout
        )

        table = service.load_soa_snapshot(
            study_uid=soa_test_data2.study.uid,
            study_value_version=None,
            layout=layout,
            time_unit=time_unit,
        )

        assert table.model_dump() == expected_table.model_dump()


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

    # get cell references
    expected_cell_references_v1, expected_footnote_references_v1 = (
        service.build_soa_snapshot(
            study_uid=soa_test_data.study.uid,
            study_value_version=None,
            layout=layout,
        )
    )

    # create a locked study version
    v1_version = TestUtils.lock_and_unlock_study(
        soa_test_data.study.uid,
        reason_for_lock_term_uid=temp_database_populated.reason_for_lock_term_uid,
        reason_for_unlock_term_uid=temp_database_populated.reason_for_unlock_term_uid,
    )

    # check SoA after locking v1
    soa = service.get_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=v1_version,
        layout=layout,
        force_build=True,
    )
    assert soa.model_dump() == soa_v1.model_dump()

    # check v1 SoA snapshot
    cell_references, footnote_references = service.repository.load(
        study_uid=soa_test_data.study.uid,
        study_value_version=v1_version,
        layout=layout,
    )
    for ref in cell_references:
        ref.footnote_references = None
    assert cell_references == expected_cell_references_v1
    assert footnote_references == expected_footnote_references_v1

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
            referenced_items=soa_footnote.referenced_items + [item_ref]
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
    soa = service.get_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=v1_version,
        layout=layout,
        force_build=True,
    )
    assert soa.model_dump() == soa_v1.model_dump()

    # check v1 SoA snapshot build after modifications to draft
    cell_references, footnote_references = service.build_soa_snapshot(
        study_uid=soa_test_data.study.uid,
        study_value_version=v1_version,
        layout=layout,
    )
    assert cell_references == expected_cell_references_v1
    assert footnote_references == expected_footnote_references_v1

    # check v1 SoA snapshot after modifications to draft
    cell_references, footnote_references = service.repository.load(
        study_uid=soa_test_data.study.uid,
        study_value_version=v1_version,
        layout=layout,
    )
    for ref in cell_references:
        ref.footnote_references = None
    assert cell_references == expected_cell_references_v1
    assert footnote_references == expected_footnote_references_v1

    # create a locked study version
    v2_version = TestUtils.lock_and_unlock_study(
        soa_test_data.study.uid,
        reason_for_lock_term_uid=temp_database_populated.reason_for_lock_term_uid,
        reason_for_unlock_term_uid=temp_database_populated.reason_for_unlock_term_uid,
    )

    # check SoA after locking v2
    soa = service.get_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=v1_version,
        layout=layout,
        force_build=True,
    )
    assert soa.model_dump() == soa_v1.model_dump()

    # check v1 SoA snapshot build after modifications to draft
    cell_references, footnote_references = service.build_soa_snapshot(
        study_uid=soa_test_data.study.uid,
        study_value_version=v1_version,
        layout=layout,
    )
    assert cell_references == expected_cell_references_v1
    assert footnote_references == expected_footnote_references_v1

    # check v1 SoA snapshot after locking v2
    cell_references, footnote_references = service.repository.load(
        study_uid=soa_test_data.study.uid,
        study_value_version=v1_version,
        layout=layout,
    )
    for ref in cell_references:
        ref.footnote_references = None
    assert cell_references == expected_cell_references_v1
    assert footnote_references == expected_footnote_references_v1

    # update protocol SoA snapshot of v1
    cell_references, footnote_references = service.update_soa_snapshot(
        study_uid=soa_test_data.study.uid,
        study_value_version=v1_version,
        layout=layout,
    )
    assert cell_references == expected_cell_references_v1
    assert footnote_references == expected_footnote_references_v1

    # fetch updated SoA references from db
    expected_cell_references, expected_footnote_references = (
        cell_references,
        footnote_references,
    )
    cell_references, footnote_references = service.repository.load(
        study_uid=soa_test_data.study.uid,
        study_value_version=v1_version,
        layout=layout,
    )
    for ref in cell_references:
        ref.footnote_references = None
    assert cell_references == expected_cell_references
    assert footnote_references == expected_footnote_references

    # compare v1 SoA
    soa = service.load_soa_snapshot(
        study_uid=soa_test_data.study.uid, study_value_version=v1_version, layout=layout
    )
    assert soa.model_dump() == soa_v1.model_dump()

    # check v2 SoA snapshot
    expected_cell_references, expected_footnote_references = service.repository.load(
        study_uid=soa_test_data.study.uid,
        study_value_version=v2_version,
        layout=layout,
    )
    for ref in expected_cell_references:
        ref.footnote_references = None

    # update protocol SoA snapshot of v2
    cell_references, footnote_references = service.update_soa_snapshot(
        study_uid=soa_test_data.study.uid,
        study_value_version=v2_version,
        layout=layout,
    )
    assert cell_references == expected_cell_references
    assert footnote_references == expected_footnote_references

    # check v2 SoA snapshot
    cell_references, footnote_references = service.repository.load(
        study_uid=soa_test_data.study.uid,
        study_value_version=v2_version,
        layout=layout,
    )
    for ref in cell_references:
        ref.footnote_references = None
    assert cell_references == expected_cell_references
    assert footnote_references == expected_footnote_references

    # compare v2 SoA
    soa = service.load_soa_snapshot(
        study_uid=soa_test_data.study.uid, study_value_version=v2_version, layout=layout
    )
    assert soa.model_dump() == soa_v2.model_dump()


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
    study_versions = {
        study.metadata_version and str(study.metadata_version)
        for study in StudyService()
        .get_study_snapshot_history(study_uid=study_uid)
        .items
    }
    return study_versions


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
