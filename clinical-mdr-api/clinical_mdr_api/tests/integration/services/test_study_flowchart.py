# pylint: disable=redefined-outer-name,unused-argument

import logging
from copy import deepcopy

import pytest

from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.domain_repositories.study_selections.study_soa_repository import (
    SoALayout,
)
from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpoch
from clinical_mdr_api.models.study_selections.study_selection import (
    ReferencedItem,
    SoACellReference,
    StudyActivitySchedule,
    StudySelectionActivity,
    StudySelectionActivityInstance,
)
from clinical_mdr_api.models.study_selections.study_soa_footnote import (
    StudySoAFootnoteEditInput,
)
from clinical_mdr_api.models.study_selections.study_visit import StudyVisit
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_activity_instance_selection import (
    StudyActivityInstanceSelectionService,
)
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.services.studies.study_flowchart import _T as _gettext
from clinical_mdr_api.services.studies.study_flowchart import (
    StudyFlowchartService,
    study_version,
)
from clinical_mdr_api.services.studies.study_soa_footnote import StudySoAFootnoteService
from clinical_mdr_api.services.studies.study_visit import StudyVisitService
from clinical_mdr_api.services.utils.table_f import TableRow, TableWithFootnotes
from clinical_mdr_api.tests.fixtures.database import TempDatabasePopulated
from clinical_mdr_api.tests.integration.utils.factory_soa import SoATestData
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.unit.services.test_study_flowchart import (
    check_flowchart_table_dimensions,
    check_flowchart_table_first_rows,
    check_flowchart_table_footnotes,
    check_flowchart_table_visit_rows,
    check_hidden_row_propagation,
)
from common import config

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def soa_test_data(temp_database_populated: TempDatabasePopulated) -> SoATestData:
    return SoATestData(project=temp_database_populated.project)


@pytest.fixture(scope="module")
def detailed_soa_table__days(soa_test_data: SoATestData) -> TableWithFootnotes:
    """get non-operational SoA table directly from StudyFlowchartService"""
    service = StudyFlowchartService()
    soa_table = service.build_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=None,
        layout=SoALayout.DETAILED,
        time_unit="day",
    )
    return soa_table


@pytest.fixture(scope="module")
def detailed_soa_table__weeks(soa_test_data: SoATestData) -> TableWithFootnotes:
    """get non-operational SoA table directly from StudyFlowchartService"""
    service = StudyFlowchartService()
    soa_table = service.build_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=None,
        layout=SoALayout.DETAILED,
        time_unit="week",
    )
    return soa_table


@pytest.fixture(scope="module")
def protocol_soa_table__days(soa_test_data: SoATestData) -> TableWithFootnotes:
    """get non-operational SoA table directly from StudyFlowchartService"""
    service = StudyFlowchartService()
    soa_table: TableWithFootnotes = service.build_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=None,
        layout=SoALayout.PROTOCOL,
        time_unit="day",
    )
    StudyFlowchartService.propagate_hidden_rows(soa_table.rows)
    soa_table.rows[0].cells[0].text = _gettext("procedure_label")
    return soa_table


@pytest.fixture(scope="module")
def protocol_soa_table__weeks(soa_test_data: SoATestData) -> TableWithFootnotes:
    """get non-operational SoA table directly from StudyFlowchartService"""
    service = StudyFlowchartService()
    soa_table: TableWithFootnotes = service.build_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=None,
        layout=SoALayout.PROTOCOL,
        time_unit="week",
    )
    StudyFlowchartService.propagate_hidden_rows(soa_table.rows)
    soa_table.rows[0].cells[0].text = _gettext("procedure_label")
    return soa_table


@pytest.fixture(scope="module")
def operational_soa_table__days(soa_test_data: SoATestData) -> TableWithFootnotes:
    """get non-operational SoA table directly from StudyFlowchartService"""
    service = StudyFlowchartService()
    soa_table = service.build_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=None,
        layout=SoALayout.OPERATIONAL,
        time_unit="day",
    )
    return soa_table


@pytest.fixture(scope="module")
def operational_soa_table__weeks(soa_test_data: SoATestData) -> TableWithFootnotes:
    """get non-operational SoA table directly from StudyFlowchartService"""
    service = StudyFlowchartService()
    soa_table = service.build_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=None,
        layout=SoALayout.OPERATIONAL,
        time_unit="week",
    )
    return soa_table


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
    table = service.build_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=None,
        layout=layout,
        time_unit=time_unit,
    )

    # Collect test data for comparison

    if time_unit is None:
        service = StudyFlowchartService()
        time_unit = service.get_preferred_time_unit(study_uid=soa_test_data.study.uid)

    study_epochs: list[StudyEpoch] = (
        StudyEpochService()
        .get_all_epochs(study_uid=soa_test_data.study.uid, sort_by={"order": True})
        .items
    )
    study_visits: list[StudyVisit] = (
        StudyVisitService(study_uid=soa_test_data.study.uid)
        .get_all_visits(study_uid=soa_test_data.study.uid, sort_by={"order": True})
        .items
    )
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
        study_selection = None

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
                study_selection: StudySelectionActivity = study_activities_map[ref.uid]

            if ref.type == SoAItemType.STUDY_ACTIVITY_INSTANCE.value:
                study_selection: StudySelectionActivityInstance = (
                    study_activity_instances_map[ref.uid]
                )
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
            for i in filter(
                lambda x: x is not None,
                (
                    row_idx_by_uid.get(soa_group_id),
                    row_idx_by_uid.get(activity_group_id),
                    row_idx_by_uid.get(activity_subgroup_id),
                    idx,
                ),
            ):
                assert i > prev, assert_error_msg
                prev = i

    # THEN all study activities are present in detailed and operational SoA tables (regardless whether scheduled for any visit)
    for activity in soa_test_data.study_activities.values():
        if (
            layout == SoALayout.OPERATIONAL
            and activity.activity.library_name == config.REQUESTED_LIBRARY_NAME
        ):
            # THEN Study Activity Placeholders are not shown in operational SoA
            assert (
                activity.study_activity_uid not in rows_by_uid
            ), f"{activity.study_activity_uid} should not be shown in operational SoA table"
        else:
            assert (
                activity.study_activity_uid in rows_by_uid
            ), f"{activity.study_activity_uid} not found in SoA table"

    # THEN all study activity instances are present in operational SoA table (regardless whether scheduled for any visit)
    if layout == SoALayout.OPERATIONAL:
        for activity in soa_test_data.study_activity_instances.values():
            if activity.activity_instance:
                assert (
                    activity.study_activity_instance_uid in rows_by_uid
                ), f"{activity.study_activity_instance_uid} not found in SoA table"

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
            row: TableRow = rows_by_uid[sas.study_activity_uid]

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
        check_flowchart_table_footnotes(table, soa_test_data.soa_footnotes)


def ensure_flowchart_table_has_no_footnotes(table: dict):
    """ensure SoA flowchart doesn't have footnotes"""

    for r_idx, row in enumerate(table.rows):
        for c_idx, cell in enumerate(row.cells):
            assert (
                not cell.footnotes
            ), f"flowchart table should not have footnote symbols row {r_idx} col {c_idx}"

    assert not table.footnotes, "flowchart should not have footnotes"


@pytest.mark.parametrize(
    "soa_table_fixture_name",
    ["protocol_soa_table__days", "protocol_soa_table__weeks"],
)
def test_propagate_hidden_rows(request, soa_table_fixture_name):
    """Validates propagation of crosses and footnotes from hidden rows to the first visible parent row"""
    soa_table: TableWithFootnotes = deepcopy(
        request.getfixturevalue(soa_table_fixture_name)
    )
    StudyFlowchartService.propagate_hidden_rows(soa_table.rows)
    check_hidden_row_propagation(soa_table)


def test_get_flowchart_item_uid_coordinates(
    soa_test_data: SoATestData, detailed_soa_table__weeks: TableWithFootnotes
):
    service = StudyFlowchartService()
    results = service.get_flowchart_item_uid_coordinates(
        study_uid=soa_test_data.study.uid
    )
    assert isinstance(results, dict)

    collected_coordinates: dict(str, tuple(int, int)) = {
        ref.uid: (r_idx, c_idx)
        for r_idx, row in enumerate(detailed_soa_table__weeks.rows)
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
    for study_epoch in (
        StudyEpochService()
        .get_all_epochs(study_uid=soa_test_data.study.uid, sort_by={"order": True})
        .items
    ):
        assert results.pop(
            study_epoch.uid, None
        ), f"Missing coordinates of StudyEpoch[{study_epoch.uid}]"

    # THEN all StudyVisits have coordinates
    study_visit: StudyVisit
    for study_visit in (
        StudyVisitService(study_uid=soa_test_data.study.uid)
        .get_all_visits(study_uid=soa_test_data.study.uid, sort_by={"order": True})
        .items
    ):
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
            + study_selection_activity.study_activity_uid
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
        for svis in StudyVisitService(study_uid=soa_test_data.study.uid)
        .get_all_visits(study_uid=study_uid, sort_by={"order": True})
        .items
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
    assert len(results) == len(schedules), "record count mismatch"

    sched: StudyActivitySchedule
    for i, res in enumerate(results):
        study_activity_schedule_uid = res["study_activity_schedule_uid"]
        sched = study_activity_schedules_map[study_activity_schedule_uid]
        study_activity = study_activities_map[sched.study_activity_uid]
        study_visit = study_visits_map[sched.study_visit_uid]

        assert len(res.keys()) == 10, f"record #{i} property count mismatch"
        assert res["study_version"] == study_version(soa_test_data.study) or res[
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
    service = StudyFlowchartService()
    results = service.download_operational_soa_content(
        study_uid=study_uid,
    )
    assert results
    assert isinstance(results, list)

    schedules = StudyActivityScheduleService().get_all_schedules(
        study_uid=study_uid,
        operational=True,
    )
    study_visits_map: dict[str, StudyVisit] = {
        svis.uid: svis
        for svis in StudyVisitService(study_uid=soa_test_data.study.uid)
        .get_all_visits(study_uid=study_uid, sort_by={"order": True})
        .items
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
                    "v": [config.REQUESTED_LIBRARY_NAME],
                    "op": "ne",
                }
            },
        )
        .items
    }
    study_activity_schedules_map: dict[str, StudyActivitySchedule] = {
        schedule.study_activity_schedule_uid: schedule for schedule in schedules
    }
    assert len(results) == len(schedules), "record count mismatch"

    sched: StudyActivitySchedule
    for i, res in enumerate(results):
        study_activity_schedule_uid = res["study_activity_schedule_uid"]
        sched = study_activity_schedules_map[study_activity_schedule_uid]
        study_activity = study_activities_map[sched.study_activity_uid]
        study_activity_instance = study_activity_instances_map[
            sched.study_activity_instance_uid
        ]
        study_visit = study_visits_map[sched.study_visit_uid]

        assert len(res.keys()) == 12, f"record #{i} property count mismatch"
        assert res["study_version"] == study_version(soa_test_data.study) or res[
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

        assert res["activity_instance"] == (
            study_activity_instance.activity_instance.name
            if study_activity_instance.activity_instance
            else None
        )
        assert res["param_code"] == (
            study_activity_instance.activity_instance.adam_param_code
            if study_activity_instance.activity_instance
            else None
        )
        assert res["topic_code"] == (
            study_activity_instance.activity_instance.topic_code
            if study_activity_instance.activity_instance
            else None
        )


class TestSoASnapshot:
    """Tests StudyFlowchartService and StudySoARepository saving and loading SoA snapshots with Study versioning"""

    def test_soa_snapshot_versioned(
        self, soa_test_data: SoATestData, layout: SoALayout = SoALayout.PROTOCOL
    ):
        """Tests saving and retrieving SoA snapshots with study versioning"""

        study_flowchart_service = StudyFlowchartService()
        study_service = StudyService()

        # GIVEN: a Study populated with data required for SoA
        study_uid = soa_test_data.study.uid

        # GIVEN: references of SoA snapshot
        expected_refs: list[SoACellReference] = (
            study_flowchart_service.build_soa_snapshot(
                study_uid, study_value_version=None, layout=layout
            )
        )

        # SCENARIO: After locking the Study, the SoA snapshot can be read back from database
        # WHEN: Study is locked
        study = study_service.lock(uid=study_uid, change_description="v1")
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
        study_service.unlock(uid=study_uid)
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
        self._remove_first_visible_study_activity(soa_test_data)
        # WHEN: SoA snapshot of the previous Study version read from the db
        # THEN: It matches the SoA snapshot of the previous Study version
        self._assert_soa_snapshot_refs_from_db_match_expected_refs(
            study_flowchart_service,
            study_uid,
            study_value_version=previous_study_version,
            layout=layout,
            expected_refs=expected_refs,
        )

        # SCENARIO: After locking the Study, the SoA snapshots of the latest draft and previous locked versions differ
        # GIVEN: Study is locked
        study = study_service.lock(uid=study_uid, change_description="v2")
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
        study = study_service.unlock(uid=study_uid)
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
        expected_refs: list[SoACellReference],
    ):
        """loads SoA snapshot references from db and compares them to expected references"""

        # pylint: disable=unused-variable
        __tracebackhide__ = True

        refs = TestSoASnapshot._load_soa_snapshot_for_comparison(
            study_flowchart_service, study_uid, study_value_version, layout
        )

        # THEN: SoA snapshot (without cell footnote references) match as expected
        assert refs == expected_refs

    @staticmethod
    def _load_soa_snapshot_for_comparison(
        study_flowchart_service, study_uid, study_value_version, layout
    ):
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
            if ssact.show_activity_in_protocol_flowchart:
                service.delete_selection(
                    study_uid=test_data.study.uid,
                    study_selection_uid=ssact.study_activity_uid,
                )
                log.info("deleted StudyActivity [%s]", ssact.study_activity_uid)
                break

    def test_build_soa_snapshot_versioned(
        self, soa_test_data: SoATestData, layout: SoALayout = SoALayout.PROTOCOL
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
            study_uid=soa_test_data.study.uid, study_value_version=None, layout=layout
        )
        # GIVEN: Study has a locked version
        previous_study_version = TestUtils.lock_and_unlock_study(
            soa_test_data.study.uid
        )

        # GIVEN: Latest draft version has a new activity added
        soa_test_data.create_study_activity(
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
            study_uid=soa_test_data.study.uid,
            study_value_version=previous_study_version,
            layout=layout,
        )
        # THEN It matches the SoA snapshot built from the previous study version
        assert refs == previous_refs

        # WHEN Building SoA snapshot of the latest draft
        current_refs = study_flowchart_service.build_soa_snapshot(
            study_uid=soa_test_data.study.uid,
            study_value_version=None,
            layout=layout,
        )
        # THEN The row references from the SoA snapshot of the previous study version is a subset of those from the SoA snapshot of the latest draft version
        current_refs = set(ref.referenced_item.item_uid for ref in current_refs[0])
        previous_refs = set(ref.referenced_item.item_uid for ref in previous_refs[0])
        assert current_refs > previous_refs

    def test_soa_snapshot_of_previous_locked_versions(
        self, soa_test_data: SoATestData, layout: SoALayout = SoALayout.PROTOCOL
    ):
        """Tests SoA snapshot of previous locked Study versions"""

        study_flowchart_service = StudyFlowchartService()
        study_service = StudyService()

        # GIVEN: a Study populated with SoA data
        study_uid = soa_test_data.study.uid
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
                uid=study_uid, change_description="vz1"
            ).current_metadata.version_metadata.version_number
        )
        study_service.unlock(uid=study_uid)

        # add a new activity
        activity_v2 = soa_test_data.create_study_activity(
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
                uid=study_uid, change_description="vz2"
            ).current_metadata.version_metadata.version_number
        )
        study_service.unlock(uid=study_uid)

        # add another activity
        soa_test_data.create_study_activity(
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
                uid=study_uid, change_description="vz2"
            ).current_metadata.version_metadata.version_number
        )
        study_service.unlock(uid=study_uid)

        # remove an activity from draft version
        StudyActivitySelectionService().delete_selection(
            study_uid=soa_test_data.study.uid,
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
        self, soa_test_data: SoATestData, layout: SoALayout = SoALayout.PROTOCOL
    ):
        """checks that saving and loading SoA snapshot references match"""

        service = StudyFlowchartService()

        expected_cell_references, expected_footnote_references = (
            service.build_soa_snapshot(
                study_uid=soa_test_data.study.uid,
                study_value_version=None,
                layout=layout,
            )
        )

        service.update_soa_snapshot(
            study_uid=soa_test_data.study.uid, study_value_version=None, layout=layout
        )

        cell_references, footnote_references = self._load_soa_snapshot_for_comparison(
            service,
            study_uid=soa_test_data.study.uid,
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
        soa_test_data: SoATestData,
        time_unit: str,
        layout: SoALayout = SoALayout.PROTOCOL,
    ):
        """tests saving of SoA snapshot and reconstruction of SoA from snapshot"""

        service = StudyFlowchartService()

        expected_table = service.build_flowchart_table(
            study_uid=soa_test_data.study.uid,
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
            study_uid=soa_test_data.study.uid, study_value_version=None, layout=layout
        )

        table = service.load_soa_snapshot(
            study_uid=soa_test_data.study.uid,
            study_value_version=None,
            layout=layout,
            time_unit=time_unit,
        )

        assert table.dict() == expected_table.dict()


def test_soa_snapshot_versioning_with_footnote_linking(
    soa_test_data: SoATestData,
    layout: SoALayout = SoALayout.PROTOCOL,
):
    # soa_test_data = SoATestDataMinimal(project=temp_database_populated.project)
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
    v1_version = TestUtils.lock_and_unlock_study(soa_test_data.study.uid)

    # check SoA after locking v1
    soa = service.get_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=v1_version,
        layout=layout,
        force_build=True,
    )
    assert soa.dict() == soa_v1.dict()

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
    assert soa_v1.dict() != soa_v2.dict()

    # check v1 SoA after modifications to draft
    soa = service.get_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=v1_version,
        layout=layout,
        force_build=True,
    )
    assert soa.dict() == soa_v1.dict()

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
    v2_version = TestUtils.lock_and_unlock_study(soa_test_data.study.uid)

    # check SoA after locking v2
    soa = service.get_flowchart_table(
        study_uid=soa_test_data.study.uid,
        study_value_version=v1_version,
        layout=layout,
        force_build=True,
    )
    assert soa.dict() == soa_v1.dict()

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
    assert soa.dict() == soa_v1.dict()

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
    assert soa.dict() == soa_v2.dict()
