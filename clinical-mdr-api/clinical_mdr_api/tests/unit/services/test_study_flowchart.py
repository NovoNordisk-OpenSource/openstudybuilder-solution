# pylint: disable=too-many-lines

from collections import defaultdict
from copy import deepcopy

import pytest
from pydantic import BaseModel

from clinical_mdr_api.domain_repositories.study_selections.study_soa_repository import (
    SoALayout,
)
from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import CTTermName
from clinical_mdr_api.models.study_selections.study import StudySoaPreferencesInput
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpoch
from clinical_mdr_api.models.study_selections.study_soa_footnote import StudySoAFootnote
from clinical_mdr_api.models.study_selections.study_visit import StudyVisit
from clinical_mdr_api.services.studies.study_flowchart import _T as _gettext
from clinical_mdr_api.services.studies.study_flowchart import StudyFlowchartService
from clinical_mdr_api.services.utils.table_f import TableRow, TableWithFootnotes
from clinical_mdr_api.tests.unit.services.soa_test_data import (
    ADD_PROTOCOL_SECTION_COLUMN_CASE1,
    ADD_PROTOCOL_SECTION_COLUMN_CASE2,
    ADD_PROTOCOL_SECTION_COLUMN_CASE3,
    COORDINATES,
    DETAILED_SOA_TABLE,
    FOOTNOTES,
    PROTOCOL_SOA_TABLE,
    PROTOCOL_SOA_TABLE_WITH_REF_PROPAGATION,
    STUDY_ACTIVITIES,
    STUDY_ACTIVITY_SCHEDULES,
    STUDY_VISITS,
)
from common import config


class MockStudyEpoch(BaseModel):
    uid: str
    epoch_ctterm: CTTermName


class MockStudyFlowchartService(StudyFlowchartService):
    # pylint: disable=super-init-not-called
    def __init__(self):
        pass

    def _get_study_visits(self, *_args, **_kwargs):
        return STUDY_VISITS

    def _get_study_activities(self, *_args, **_kwargs):
        return STUDY_ACTIVITIES

    def _get_study_activity_schedules(self, *_args, **_kwargs):
        return STUDY_ACTIVITY_SCHEDULES

    def _get_study_activity_instances(self, *_args, **_kwargs):
        return []

    def _get_study_footnotes(self, *_args, **_kwargs):
        return FOOTNOTES

    def _validate_parameters(self, *_args, **_kwargs):
        pass

    def _get_soa_preferences(self, *_args, **_kwargs) -> StudySoaPreferencesInput:
        return StudySoaPreferencesInput()

    def get_preferred_time_unit(self, *_args, **_kwargs) -> str:
        return "week"


def check_flowchart_table_dimensions(
    table: TableWithFootnotes,
    layout: SoALayout,
    soa_preferences: StudySoaPreferencesInput,
):
    """tests dimensions of SoA table"""

    num_cols = sum(cell.span for cell in table.rows[0].cells)
    for i, row in enumerate(table.rows[1:], start=1):
        # THEN number of columns are the same in all rows
        assert len(row.cells) <= num_cols, f"Unexpected number of columns in row {i}"
        assert (
            sum(cell.span for cell in row.cells) == num_cols
        ), f"Unexpected span of columns in row {i}"

    # THEN table has the expected number of header rows
    # epochs row is always there, just hidden when not soa_preferences.show_epochs
    expected_num_headers = (
        3 + 1 + int(soa_preferences.show_milestones and layout != SoALayout.OPERATIONAL)
    )
    assert table.num_header_rows == expected_num_headers

    # THEN table has 1 header column
    assert table.num_header_cols == 1


def check_flowchart_table_first_rows(
    table: TableWithFootnotes,
    layout: SoALayout,
    study_epochs: list[StudyEpoch | MockStudyEpoch],
    study_visits: list[StudyVisit],
    soa_preferences: StudySoaPreferencesInput,
):
    """tests epoch and milestones header rows of study SoA table"""

    row = table.rows[0]

    # THEN epochs header is visible according to SoA preferences
    assert row.hide is not (
        soa_preferences.show_epochs or (layout == SoALayout.OPERATIONAL)
    )

    # THEN first cell text is Epoch
    if layout != SoALayout.PROTOCOL or row.hide:
        assert row.cells[0].text == _gettext("study_epoch")

    if layout == SoALayout.OPERATIONAL:
        # THEN has operational SoA column headers
        assert row.cells[1].text == _gettext("topic_code")
        assert row.cells[2].text == _gettext("adam_param_code")

    num_visits_per_epoch = defaultdict(int)
    # only one visit per group is considered
    visit: StudyVisit
    for _, e in {
        (
            visit.consecutive_visit_group or visit.visit_name,
            visit.study_epoch.sponsor_preferred_name,
        )
        for visit in study_visits
    }:
        num_visits_per_epoch[e] += 1

    i = 3 if (layout == SoALayout.OPERATIONAL) else 1
    epoch: StudyEpoch | MockStudyEpoch
    for epoch in study_epochs:
        cell = row.cells[i]

        # THEN cell style is header1
        assert cell.style == "header1"

        # THEN cell text is epoch name
        assert cell.text == epoch.epoch_ctterm.sponsor_preferred_name

        # THEN cell refs
        assert len(cell.refs) == 1
        assert cell.refs[0].type == SoAItemType.STUDY_EPOCH.value
        assert cell.refs[0].uid == epoch.uid

        # THEN span is number of visits
        assert (
            cell.span == num_visits_per_epoch[epoch.epoch_ctterm.sponsor_preferred_name]
        )

        for j in range(1, cell.span):
            # THEN span of following cells are 0 for the next visits of the epoch
            assert row.cells[i + j].span == 0

            # THEN text of following cells are empty
            assert not row.cells[i + j].text

        i += cell.span

    if (layout != SoALayout.OPERATIONAL) and soa_preferences.show_milestones:
        row = table.rows[1]

        first_visit_of_each_group: dict[str, StudyVisit] = {}
        for visit in study_visits:
            first_visit_of_each_group.setdefault(
                visit.consecutive_visit_group or visit.visit_name, visit
            )

        if not table.rows[0].hide:
            assert row.cells[0].text == _gettext("study_milestone")
        assert row.cells[0].style == "header1"
        assert row.hide is False

        i = 2 if (layout == SoALayout.OPERATIONAL) else 0
        prev_visit_type_uid = None
        for visit in first_visit_of_each_group.values():
            i += 1

            if visit.is_soa_milestone:
                if prev_visit_type_uid == visit.visit_type_uid:
                    # Same visit_type, then merged with the previous cell
                    assert row.cells[i].text == ""
                    assert row.cells[i].span == 0
                    # number of columns / sum of spans is checked by check_flowchart_table_dimensions()

                else:
                    # Different visit_type, new label
                    prev_visit_type_uid = visit.visit_type_uid
                    assert row.cells[i].text == visit.visit_type.sponsor_preferred_name
                    assert row.cells[i].style == "header1"
                    assert row.cells[i].span > 0

            else:
                # empty cell for non-milestones
                assert row.cells[i].text == ""
                assert row.cells[i].span == 1

    # check for procedure label in Protocol SoA
    if layout == SoALayout.PROTOCOL:
        for row in table.rows[: table.num_header_rows]:
            if not row.hide:
                assert row.cells[0].text == _gettext("procedure_label")
                break


def check_flowchart_table_footnotes(table: dict, soa_footnotes: list[StudySoAFootnote]):
    """check footnotes and their references in flowchart table"""

    symbol_ref_uid_map: dict[str, set] = defaultdict(set)
    soa_ref_uids = set()

    for r_idx, row in enumerate(table.rows):
        for c_idx, cell in enumerate(row.cells):
            has_footnotes = cell.footnotes

            if has_footnotes:
                assert (
                    cell.refs
                ), f"Cell [{r_idx},{c_idx}] without references should not have any footnotes"

            if not cell.refs:
                continue

            for ref in cell.refs:
                soa_ref_uids.add(ref.uid)

                if has_footnotes:
                    for symbol in cell.footnotes:
                        symbol_ref_uid_map[symbol].add(ref.uid)

    keys = list(symbol_ref_uid_map.keys())
    assert keys == sorted(keys), "Invalid order of footnotes symbols"

    if keys:
        assert table.footnotes, "Missing table footnotes"

    assert list(table.footnotes.keys()) == sorted(
        table.footnotes.keys()
    ), "Invalid footnote order"
    assert set(keys).issubset(
        table.footnotes.keys()
    ), "Invalid footnote symbols or missing footnote for symbol"

    footnote_uid_symbol_map: dict[str, str] = {
        fn.uid: sym for sym, fn in table.footnotes.items()
    }

    for footnote in soa_footnotes:
        assert (
            footnote.uid in footnote_uid_symbol_map
        ), f"No symbol found for footnote {footnote.uid}"
        symbol = footnote_uid_symbol_map[footnote.uid]

        # THEN verify footnote text matches footnote template text
        assert table.footnotes[symbol].text_plain == footnote.template.name_plain
        assert table.footnotes[symbol].text_html == footnote.template.name

        # Must filter out uids not giving any SoA row unless Activities can share StudyActivityGroup and SubGroup nodes
        footnote_referenced_uids = {
            ref.item_uid
            for ref in footnote.referenced_items
            if ref.item_uid in soa_ref_uids
        }
        referenced_uids_in_soa = set(symbol_ref_uid_map[symbol])

        if footnote_referenced_uids:
            # THEN verify footnotes are referenced in SoA
            footnote_uids_not_referenced_in_soa = (
                footnote_referenced_uids - referenced_uids_in_soa
            )
            assert not footnote_uids_not_referenced_in_soa

        else:
            # THEN a footnote without references should not be referenced in any cell of the SoA
            assert not referenced_uids_in_soa


def check_flowchart_table_visit_rows(
    table: TableWithFootnotes,
    layout: SoALayout,
    time_unit: str,
    study_visits: list[StudyVisit],
    soa_preferences: StudySoaPreferencesInput,
):
    """test visit header rows of SoA table"""

    operational = layout == SoALayout.OPERATIONAL

    row_idx = 1
    if soa_preferences.show_milestones and not operational:
        row_idx += 1

    # THEN Second row label text is
    if not table.rows[0].hide:
        assert table.rows[row_idx].cells[0].text == _gettext("visit_short_name")

    # THEN Third row label text is
    assert _gettext(
        f"study_{time_unit}"
    ), f"translation key not found: study_{time_unit}"
    assert table.rows[row_idx + 1].cells[0].text == _gettext(f"study_{time_unit}")

    # THEN Fourth row label text is
    assert table.rows[row_idx + 2].cells[0].text == _gettext("visit_window").format(
        unit_name="days"
    )

    for i in range(1, 4):
        # THEN Rows label style
        if not soa_preferences.show_milestones or operational:
            assert table.rows[i].cells[0].style == f"header{i+1}"
        else:
            assert table.rows[i].cells[0].style == f"header{i}"

        # THEN Rows are visible
        assert not table.rows[i].hide

    visit_groups: dict[str, StudyVisit] = {}
    visit_idx_by_uid: dict[str, int] = {}
    for visit in study_visits:
        group_name = visit.consecutive_visit_group or visit.visit_name
        visit_groups.setdefault(group_name, []).append(visit)
        visit_idx_by_uid[visit.uid] = len(visit_groups) + (2 if operational else 0)

    for i, (group_name, visits) in enumerate(
        visit_groups.items(), start=3 if operational else 1
    ):
        visit = visits[0]

        # THEN visits name in second row
        assert (
            table.rows[row_idx].cells[i].text == visit.consecutive_visit_group
            or visit.visit_name
        )

        # THEN visits ref in second row
        assert len(table.rows[row_idx].cells[i].refs) == len(visits)
        assert {ref.type for ref in table.rows[row_idx].cells[i].refs} == {
            SoAItemType.STUDY_VISIT.value
        }, "Invalid reference type"
        assert {ref.uid for ref in table.rows[row_idx].cells[i].refs} == {
            visit.uid for visit in visits
        }, "Referenced visit uids doesn't match"

        # THEN study weeks/days in second row
        if len(visits) > 1:
            if time_unit == "week":
                visit_timing_prop = (
                    "study_duration_weeks"
                    if soa_preferences.baseline_as_time_zero
                    else "study_week_number"
                )
                assert (
                    table.rows[row_idx + 1].cells[i].text
                    == f"{getattr(visits[0], visit_timing_prop):d}-{getattr(visits[-1], visit_timing_prop):d}"
                )
            else:
                visit_timing_prop = (
                    "study_duration_days"
                    if soa_preferences.baseline_as_time_zero
                    else "study_day_number"
                )
                assert (
                    table.rows[row_idx + 1].cells[i].text
                    == f"{getattr(visits[0], visit_timing_prop):d}-{getattr(visits[-1], visit_timing_prop):d}"
                )
        else:
            if time_unit == "week":
                assert table.rows[row_idx + 1].cells[i].text == str(
                    visit.study_duration_weeks
                    if soa_preferences.baseline_as_time_zero
                    else visit.study_week_number
                )
            else:
                assert table.rows[row_idx + 1].cells[i].text == str(
                    visit.study_duration_days
                    if soa_preferences.baseline_as_time_zero
                    else visit.study_day_number
                )

        # THEN text in forth row
        if visit.min_visit_window_value == visit.max_visit_window_value == 0:
            assert table.rows[row_idx + 2].cells[i].text == "0"
        elif visit.min_visit_window_value == -visit.max_visit_window_value:
            assert (
                table.rows[row_idx + 2].cells[i].text
                == f"±{visit.max_visit_window_value:0.0f}"
            )
        else:
            assert (
                table.rows[row_idx + 2].cells[i].text
                == f"{visit.min_visit_window_value:+0.0f}/{visit.max_visit_window_value:+0.0f}"
            )

    for i, cell in enumerate(table.rows[0].cells):
        if cell.text and cell.span:
            # THEN first row cell style is header1
            assert cell.style == (
                "header2" if operational and i in (1, 2) else "header1"
            )

    for cell in table.rows[row_idx].cells:
        # THEN second row cell span is 1
        assert cell.span == 1
        if cell.text:
            # THEN second row cell style is header2
            assert cell.style == "header2"

    for cell in table.rows[row_idx + 1].cells:
        # THEN third row cell span is 1
        assert cell.span == 1
        if cell.text:
            # THEN third row cell style is header3
            assert cell.style == "header3"

    # THEN forth row style is header4
    for cell in table.rows[row_idx + 2].cells:
        # THEN forth row cell span is 1
        if cell.text and cell.span:
            assert cell.style == "header4"

    return visit_idx_by_uid


def check_hidden_row_propagation(table: TableWithFootnotes):
    """Validates propagation of crosses from hidden rows to the first visible parent row"""

    path = []
    soa_group_row = activity_group_row = activity_subgroup_row = activity_row = None

    for idx, row in enumerate(
        table.rows[table.num_header_rows :], start=table.num_header_rows
    ):
        if not row.cells[0].refs:
            # ActivityRequest placeholders may not have soa-group and soa-subgroup selected,
            # their group and subgroup rows may be dummy placeholders with filler text but no object to reference
            path = [soa_group_row]
            continue

        # THEN all data rows keep reference
        assert row.cells[0].refs
        ref = next(
            (
                r
                for r in row.cells[0].refs
                if r.type
                in {
                    "CTTerm",
                    "ActivityGroup",
                    "ActivitySubGroup",
                    SoAItemType.STUDY_ACTIVITY.value,
                    SoAItemType.STUDY_ACTIVITY_INSTANCE.value,
                }
            ),
            None,
        )
        assert ref, f"Unexpected reference types in row {idx} column 0"
        typ = ref.type

        if typ == "CTTerm":
            path = [soa_group_row := row]
            activity_group_row = activity_subgroup_row = activity_row = None
            continue

        if typ == "ActivityGroup":
            path = [soa_group_row, activity_group_row := row]
            activity_subgroup_row = activity_row = None
            continue

        if typ == "ActivitySubGroup":
            path = [soa_group_row, activity_group_row, activity_subgroup_row := row]
            activity_row = None
            continue

        if typ == SoAItemType.STUDY_ACTIVITY.value:
            path = [
                soa_group_row,
                activity_group_row,
                activity_subgroup_row,
                activity_row := row,
            ]

        if not row.hide:
            continue

        if typ == SoAItemType.STUDY_ACTIVITY_INSTANCE.value:
            path = [
                soa_group_row,
                activity_group_row,
                activity_subgroup_row,
                activity_row,
                row,
            ]

        # First visible parent
        parent = next(
            (row for row in reversed(path[:-1]) if row and not row.hide), None
        )
        if not parent:
            continue

        for i, cell in enumerate(row.cells):
            if not cell.text:
                continue

            if i:
                # THEN checkmarks form a non-visible row is propagated up to the first visible group row
                assert (
                    parent.cells[i].text == cell.text
                ), f"Hidden {typ} text in row {idx} was not propagated to visible parent row {parent.cells[0].refs}"

                # THEN parent cell has no propagated footnotes
                assert not parent.cells[i].footnotes


# pylint: disable=redefined-outer-name
@pytest.fixture(scope="module")
def mock_study_flowchart_service():
    return MockStudyFlowchartService()


def test_get_flowchart_item_uid_coordinates(mock_study_flowchart_service):
    coordinates = mock_study_flowchart_service.get_flowchart_item_uid_coordinates(
        study_uid=""
    )
    assert coordinates == COORDINATES


def test_group_visits(mock_study_flowchart_service):
    visits = mock_study_flowchart_service._get_study_visits()
    grouped_visits = mock_study_flowchart_service._group_visits(visits)

    count_visits = 0
    for study_epoch_uid, epoch_grouping in grouped_visits.items():
        assert isinstance(study_epoch_uid, str)
        assert isinstance(epoch_grouping, dict)

        for visit_group_id, visit_group in epoch_grouping.items():
            assert isinstance(visit_group_id, str)
            assert isinstance(visit_group, list)

            for visit in visit_group:
                count_visits += 1

                assert isinstance(visit, StudyVisit)
                assert study_epoch_uid == visit.study_epoch_uid

                if len(visit_group) == 1:
                    assert visit_group_id == visit.uid
                else:
                    assert visit_group_id == visit.consecutive_visit_group

    assert count_visits == len(visits)


def test_mk_simple_footnotes(mock_study_flowchart_service):
    footnotes: list[StudySoAFootnote] = (
        mock_study_flowchart_service._get_study_footnotes()
    )
    (
        footnote_symbols_by_ref_uid,
        simple_footnotes_by_symbol,
    ) = mock_study_flowchart_service._mk_simple_footnotes(footnotes)

    assert simple_footnotes_by_symbol == DETAILED_SOA_TABLE.footnotes

    footnotes_uid_to_symbol_mapping = {
        simple_footnote.uid: symbol
        for symbol, simple_footnote in simple_footnotes_by_symbol.items()
    }

    count_references = 0
    for soa_footnote in footnotes:
        assert soa_footnote.uid in footnotes_uid_to_symbol_mapping
        symbol = footnotes_uid_to_symbol_mapping[soa_footnote.uid]
        for ref in soa_footnote.referenced_items:
            assert ref.item_uid in footnote_symbols_by_ref_uid
            assert symbol in footnote_symbols_by_ref_uid[ref.item_uid]
            count_references += 1

    assert count_references == sum(
        len(symbols) for symbols in footnote_symbols_by_ref_uid.values()
    )


@pytest.mark.parametrize("time_unit", ["day", "week"])
def test_get_header_rows(mock_study_flowchart_service, time_unit):
    visits = [
        visit
        for visit in mock_study_flowchart_service._get_study_visits()
        if visit.show_visit
        and visit.study_epoch.sponsor_preferred_name != config.BASIC_EPOCH_NAME
    ]
    grouped_visits = mock_study_flowchart_service._group_visits(visits)

    header_rows = mock_study_flowchart_service._get_header_rows(
        grouped_visits,
        time_unit=time_unit,
        soa_preferences=StudySoaPreferencesInput(),
        layout=SoALayout.DETAILED,
    )

    visits = [
        visit_group[0]
        for epoch_grouping in grouped_visits.values()
        for visit_group in epoch_grouping.values()
    ]

    assert len(header_rows) == 4

    for _r, row in enumerate(header_rows):
        assert row.hide is False

        if _r == 0:
            assert (
                len([cell.span for cell in row.cells if cell.span > 0])
                == len(grouped_visits) + 1
            ), "Epoch count mismatch"
        else:
            assert (
                sum(cell.span for cell in row.cells)
                == sum(len(epoch_group) for epoch_group in grouped_visits.values()) + 1
            ), "Visit row count mismatch"

        if _r == 1:
            for _c, cell in enumerate(row.cells[1:]):
                visit = visits[_c]
                assert (
                    cell.text == visit.consecutive_visit_group or visit.visit_short_name
                ), "Error in visit name"

        if _r == 2:
            for _c, cell in enumerate(row.cells[1:]):
                visit = visits[_c]
                if not visit.consecutive_visit_group:
                    expected = (
                        visit.study_day_number
                        if time_unit == "day"
                        else visit.study_week_number
                    )
                    assert cell.text == f"{expected:d}", "Error in day/week number"


def test_build_flowchart_table(mock_study_flowchart_service):
    table = mock_study_flowchart_service.build_flowchart_table(
        study_uid="",
        study_value_version=None,
        layout=SoALayout.DETAILED,
        time_unit="day",
    )

    assert table.num_header_rows == DETAILED_SOA_TABLE.num_header_rows
    assert table.num_header_cols == DETAILED_SOA_TABLE.num_header_cols
    assert table.title == DETAILED_SOA_TABLE.title
    assert table.footnotes == DETAILED_SOA_TABLE.footnotes

    assert table.dict() == DETAILED_SOA_TABLE.model_dump()


@pytest.mark.parametrize(
    ("propagate_refs", "soa", "expected_soa"),
    [
        (False, DETAILED_SOA_TABLE, PROTOCOL_SOA_TABLE),
        (True, DETAILED_SOA_TABLE, PROTOCOL_SOA_TABLE_WITH_REF_PROPAGATION),
    ],
)
def test_propagate_hidden_rows(
    propagate_refs: bool, soa: TableWithFootnotes, expected_soa: TableWithFootnotes
):
    table = deepcopy(soa)
    StudyFlowchartService.propagate_hidden_rows(
        table.rows, propagate_refs=propagate_refs
    )
    assert table.model_dump() == expected_soa.model_dump()


def test_propagate_hidden_rows_2():
    table: TableWithFootnotes = deepcopy(DETAILED_SOA_TABLE)
    StudyFlowchartService.propagate_hidden_rows(table.rows)
    check_hidden_row_propagation(table)


def test_show_hidden_rows():
    table = deepcopy(DETAILED_SOA_TABLE)
    StudyFlowchartService.show_hidden_rows(table.rows)

    assert table.num_header_rows == DETAILED_SOA_TABLE.num_header_rows
    assert table.num_header_cols == DETAILED_SOA_TABLE.num_header_cols
    assert table.title == DETAILED_SOA_TABLE.title
    assert table.footnotes == DETAILED_SOA_TABLE.footnotes
    assert len(table.rows) == len(DETAILED_SOA_TABLE.rows)

    row: TableRow
    for row, expected_row in zip(table.rows, DETAILED_SOA_TABLE.rows):
        assert row.cells == expected_row.cells
        assert row.hide is False


@pytest.mark.parametrize(
    (
        "layout",
        "time_unit",
        "show_epochs",
        "show_milestones",
        "baseline_as_time_zero",
    ),
    [
        (SoALayout.PROTOCOL, "day", False, True, False),
        (SoALayout.PROTOCOL, "day", False, False, True),
        (SoALayout.PROTOCOL, "day", True, True, True),
        (SoALayout.PROTOCOL, "week", False, True, True),
        (SoALayout.PROTOCOL, "week", False, False, False),
        (SoALayout.DETAILED, "day", True, False, True),
        (SoALayout.PROTOCOL, "week", True, True, False),
        (SoALayout.DETAILED, "day", False, True, False),
        (SoALayout.DETAILED, "week", False, False, True),
        (SoALayout.PROTOCOL, "day", True, False, False),
        (SoALayout.OPERATIONAL, "week", True, True, True),
        (SoALayout.OPERATIONAL, "day", False, True, True),
        (SoALayout.OPERATIONAL, "week", True, False, True),
        (SoALayout.OPERATIONAL, "day", True, True, False),
        (SoALayout.OPERATIONAL, "week", False, True, False),
        (SoALayout.OPERATIONAL, "day", False, False, True),
        (SoALayout.OPERATIONAL, "week", True, False, False),
    ],
)
def test_get_header_rows_with_soa_preferences(
    layout: SoALayout,
    time_unit: str,
    show_epochs: bool,
    show_milestones: bool,
    baseline_as_time_zero: bool,
):
    epochs = list(
        {
            visit.study_epoch_uid: MockStudyEpoch(
                uid=visit.study_epoch_uid,
                epoch_ctterm=CTTermName(
                    sponsor_preferred_name=visit.study_epoch.sponsor_preferred_name,
                    sponsor_preferred_name_sentence_case=visit.study_epoch.sponsor_preferred_name,
                ),
            )
            for visit in STUDY_VISITS
            if visit.show_visit
            and visit.study_epoch.sponsor_preferred_name != config.BASIC_EPOCH_NAME
        }.values()
    )

    visits = [
        visit
        for visit in STUDY_VISITS
        if visit.show_visit
        and visit.study_epoch.sponsor_preferred_name != config.BASIC_EPOCH_NAME
    ]
    grouped_visits = StudyFlowchartService._group_visits(visits)

    soa_preferences = StudySoaPreferencesInput(
        show_epochs=show_epochs,
        show_milestones=show_milestones,
        baseline_as_time_zero=baseline_as_time_zero,
    )

    header_rows = StudyFlowchartService._get_header_rows(
        grouped_visits,
        time_unit=time_unit,
        soa_preferences=soa_preferences,
        layout=layout,
    )

    table = TableWithFootnotes(
        rows=header_rows, num_header_rows=len(header_rows), num_header_cols=1
    )

    # Test dimensions
    check_flowchart_table_dimensions(table, layout, soa_preferences)

    # Test first header row
    check_flowchart_table_first_rows(table, layout, epochs, visits, soa_preferences)

    # Test visit header rows
    check_flowchart_table_visit_rows(table, layout, time_unit, visits, soa_preferences)


@pytest.mark.parametrize(
    "test_table, expected_table",
    [
        ADD_PROTOCOL_SECTION_COLUMN_CASE1,
        ADD_PROTOCOL_SECTION_COLUMN_CASE2,
        ADD_PROTOCOL_SECTION_COLUMN_CASE3,
    ],
)
def test_add_protocol_section_column(test_table, expected_table):
    table = deepcopy(test_table)
    StudyFlowchartService.add_protocol_section_column(table)
    assert table.dict() == expected_table.dict()
