# pylint: disable=too-many-lines

from collections import defaultdict
from copy import deepcopy
from typing import Any

import pytest
from docx.table import Table
from pydantic import BaseModel

from clinical_mdr_api.domain_repositories.study_selections.study_soa_repository import (
    SoALayout,
)
from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityForStudyActivity,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameWithConflictFlag,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import CTTermName
from clinical_mdr_api.models.study_selections.study import StudySoaPreferencesInput
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpoch
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
from clinical_mdr_api.models.study_selections.study_visit import (
    StudyVisit,
    StudyVisitLite,
)
from clinical_mdr_api.services.studies.study_flowchart import _T as _gettext
from clinical_mdr_api.services.studies.study_flowchart import StudyFlowchartService
from clinical_mdr_api.services.utils.table_f import (
    Ref,
    TableCell,
    TableRow,
    TableWithFootnotes,
)
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
    TINY_SOA_TABLE,
)
from common.config import settings
from common.exceptions import ValidationException
from common.utils import VisitClass


class MockStudyEpoch(BaseModel):
    uid: str
    epoch_ctterm: CTTermName


class MockStudyFlowchartService(StudyFlowchartService):
    # pylint: disable=super-init-not-called
    def __init__(self):
        pass

    def _get_study_visits(self, *_args, **_kwargs):
        return STUDY_VISITS

    def fetch_study_activities(self, *_args, **_kwargs):
        return STUDY_ACTIVITIES

    def _get_study_activity_schedules(self, *_args, **_kwargs):
        return STUDY_ACTIVITY_SCHEDULES

    def fetch_study_activity_instances(self, *_args, **_kwargs):
        return []

    def _get_study_footnotes(self, *_args, **_kwargs):
        return FOOTNOTES

    def _validate_parameters(self, *_args, **_kwargs):
        pass

    def _get_soa_preferences(self, *_args, **_kwargs) -> StudySoaPreferencesInput:
        return StudySoaPreferencesInput(
            show_epochs=True, show_milestones=False, baseline_as_time_zero=False
        )

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

    collapse_visit_groups = layout != SoALayout.OPERATIONAL
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

    num_visits_per_epoch: dict[str, int] = defaultdict(int)
    # only one visit per group is considered
    visit: StudyVisit
    for _, e in {
        (
            collapse_visit_groups and visit.consecutive_visit_group or visit.uid,
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
                collapse_visit_groups
                and visit.consecutive_visit_group
                or visit.visit_short_name,
                visit,
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
                if prev_visit_type_uid == visit.visit_type.term_uid:
                    # Same visit_type, then merged with the previous cell
                    assert row.cells[i].text == ""
                    assert row.cells[i].span == 0
                    # number of columns / sum of spans is checked by check_flowchart_table_dimensions()

                else:
                    # Different visit_type, new label
                    prev_visit_type_uid = visit.visit_type.term_uid
                    assert row.cells[i].text == visit.visit_type.sponsor_preferred_name
                    assert row.cells[i].style == "header1"
                    assert row.cells[i].span > 0

            else:
                # empty cell for non-milestones
                assert row.cells[i].text == ""
                assert row.cells[i].span == 1

    # check corner label in Protocol SoA
    if layout == SoALayout.PROTOCOL:
        if soa_preferences.show_epochs:
            for row in table.rows[: table.num_header_rows]:
                if not row.hide:
                    assert row.cells[0].text == _gettext("procedure_label")
                    break
        else:
            visits_row = next(
                row
                for row in table.rows[: table.num_header_rows]
                if row.cells and row.cells[0].style == "header2"
            )
            assert visits_row.cells[0].text == _gettext("visit_short_name")


def check_flowchart_table_footnotes(
    table: Table, soa_footnotes: list[StudySoAFootnote], layout: SoALayout
):
    """check footnotes and their references in flowchart table"""

    symbol_ref_uid_map: dict[str, set[Any]] = defaultdict(set)
    soa_ref_uids = set()
    # Collect ref UIDs from visible rows only, matching add_footnotes filtering logic
    visible_ref_uids = set()

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
                if not row.hide:
                    visible_ref_uids.add(ref.uid)

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

    for soa_footnote in soa_footnotes:
        if layout == SoALayout.PROTOCOL:
            # Footnotes are excluded from the table by add_footnotes if none of their
            # referenced items appear in visible rows (matching add_footnotes filtering)
            has_visible_refs = any(
                ref.item_uid in visible_ref_uids
                for ref in soa_footnote.referenced_items
            )
            if not has_visible_refs:
                assert (
                    soa_footnote.uid not in footnote_uid_symbol_map
                ), f"Footnote {soa_footnote.uid} with no visible references should not appear in table"
                continue

        assert (
            soa_footnote.uid in footnote_uid_symbol_map
        ), f"No symbol found for footnote {soa_footnote.uid}"
        symbol = footnote_uid_symbol_map[soa_footnote.uid]

        # THEN verify footnote text matches footnote template text
        assert table.footnotes[symbol].text_plain == soa_footnote.footnote.name_plain
        assert table.footnotes[symbol].text_html == soa_footnote.footnote.name

        # Must filter out uids not giving any SoA row unless Activities can share StudyActivityGroup and SubGroup nodes
        footnote_referenced_uids = {
            ref.item_uid
            for ref in soa_footnote.referenced_items
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
            assert table.rows[i].cells[0].style == f"header{i + 1}"
        else:
            assert table.rows[i].cells[0].style == f"header{i}"

        # THEN Rows are visible
        assert not table.rows[i].hide

    visit_groups: dict[str, StudyVisit] = {}
    visit_idx_by_uid: dict[str, int] = {}
    for visit in study_visits:
        group_name = (
            not operational and visit.consecutive_visit_group
        ) or visit.visit_short_name
        visit_groups.setdefault(group_name, []).append(visit)
        visit_idx_by_uid[visit.uid] = len(visit_groups) + (2 if operational else 0)

    for i, (group_name, visits) in enumerate(
        visit_groups.items(), start=3 if operational else 1
    ):
        visit = visits[0]

        # THEN visits name in second row
        assert (
            table.rows[row_idx].cells[i].text
            == (not operational and visit.consecutive_visit_group)
            or visit.visit_short_name
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
        elif (
            visit.min_visit_window_value is not None
            and visit.max_visit_window_value is not None
            and visit.min_visit_window_value == -visit.max_visit_window_value
        ):
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


@pytest.mark.parametrize(
    "layout",
    [SoALayout.PROTOCOL_LAB_TABLE, SoALayout.DETAILED, SoALayout.OPERATIONAL],
)
def test_load_soa_snapshot_rejects_non_protocol_layout(
    mock_study_flowchart_service, layout
):
    with pytest.raises(ValidationException, match="only supported for layout"):
        mock_study_flowchart_service.load_soa_snapshot(
            study_uid="anything", layout=layout
        )


@pytest.mark.parametrize(
    "layout",
    [SoALayout.PROTOCOL_LAB_TABLE, SoALayout.DETAILED, SoALayout.OPERATIONAL],
)
def test_update_soa_snapshot_rejects_non_protocol_layout(
    mock_study_flowchart_service, layout
):
    with pytest.raises(ValidationException, match="only supported for layout"):
        mock_study_flowchart_service.update_soa_snapshot(
            study_uid="anything", layout=layout
        )


@pytest.mark.parametrize("collapse_visit_groups", [True, False])
def test_group_visits(
    mock_study_flowchart_service: MockStudyFlowchartService, collapse_visit_groups: bool
):
    visits = mock_study_flowchart_service._get_study_visits()
    grouped_visits = mock_study_flowchart_service._group_visits(
        visits, collapse_visit_groups=collapse_visit_groups
    )

    count_visits = 0
    for study_epoch_uid, epoch_grouping in grouped_visits:
        assert isinstance(study_epoch_uid, (str, type(None)))
        assert isinstance(epoch_grouping, dict)

        for visit_group_id, visit_group in epoch_grouping.items():
            assert isinstance(visit_group_id, str)
            assert isinstance(visit_group, list)
            if not collapse_visit_groups:
                assert len(visit_group) == 1

            for visit in visit_group:
                count_visits += 1

                assert isinstance(visit, (StudyVisit, StudyVisitLite))
                assert study_epoch_uid == visit.study_epoch_uid

                if len(visit_group) == 1:
                    assert visit_group_id == visit.uid
                else:
                    assert visit_group_id == visit.consecutive_visit_group

    assert count_visits == len(visits)


def test_group_visits_epoch_gap_preserves_visit_order():
    """Visits with no epoch interleaved between same-epoch visits must appear in their
    original sequence position, not all grouped after or before the surrounding epoch.
    """

    treatment_epoch = SimpleCTTermNameWithConflictFlag(
        term_uid="CTTerm_Treatment", sponsor_preferred_name="Treatment"
    )

    def make_visit(uid, epoch_uid, epoch, short_name, visit_number):
        return StudyVisitLite(
            uid=uid,
            study_epoch_uid=epoch_uid,
            study_epoch=epoch,
            show_visit=True,
            min_visit_window_value=0,
            max_visit_window_value=0,
            visit_number=visit_number,
            unique_visit_number=int(visit_number * 100),
            visit_short_name=short_name,
            visit_class=VisitClass.SINGLE_VISIT,
            is_global_anchor_visit=False,
            is_soa_milestone=False,
            visit_type=None,
        )

    # V1, V2, V3 → Treatment epoch; V4 → no epoch; V5, V6 → Treatment epoch again
    visits = [
        make_visit("v1", "epoch_treatment", treatment_epoch, "V1", 1.0),
        make_visit("v2", "epoch_treatment", treatment_epoch, "V2", 2.0),
        make_visit("v3", "epoch_treatment", treatment_epoch, "V3", 3.0),
        make_visit("v4", None, None, "V4", 4.0),
        make_visit("v5", "epoch_treatment", treatment_epoch, "V5", 5.0),
        make_visit("v6", "epoch_treatment", treatment_epoch, "V6", 6.0),
    ]

    grouped = StudyFlowchartService._group_visits(visits, collapse_visit_groups=False)

    # THEN three consecutive runs are produced, not two merged buckets
    assert len(grouped) == 3, (
        f"Expected 3 runs (Treatment, no-epoch, Treatment), got {len(grouped)}: "
        f"{[uid for uid, _ in grouped]}"
    )

    epoch_uids = [epoch_uid for epoch_uid, _ in grouped]
    assert epoch_uids == [
        "epoch_treatment",
        None,
        "epoch_treatment",
    ], f"Runs are out of order: {epoch_uids}"

    # THEN V4 is in the middle run (no-epoch), not appended after V5/V6
    visit_uids_per_run = [list(vgroups.keys()) for _, vgroups in grouped]
    assert visit_uids_per_run[0] == [
        "v1",
        "v2",
        "v3",
    ], f"First run: {visit_uids_per_run[0]}"
    assert visit_uids_per_run[1] == ["v4"], f"Middle run: {visit_uids_per_run[1]}"
    assert visit_uids_per_run[2] == ["v5", "v6"], f"Last run: {visit_uids_per_run[2]}"

    # THEN the epoch header row reflects three separate epoch spans
    header_rows = StudyFlowchartService._get_header_rows(
        grouped,
        time_unit="week",
        soa_preferences=StudySoaPreferencesInput(
            show_epochs=True,
            show_milestones=False,
            baseline_as_time_zero=False,
            show_all_visits_lab_table=False,
        ),
        layout=SoALayout.DETAILED,
    )

    epoch_cells = [cell for cell in header_rows[0].cells[1:] if cell.span > 0]
    assert (
        len(epoch_cells) == 3
    ), f"Expected 3 epoch header cells (Treatment / no-epoch / Treatment), got {len(epoch_cells)}"
    assert epoch_cells[0].text == "Treatment"
    assert epoch_cells[0].span == 3  # V1, V2, V3
    assert epoch_cells[1].text == ""  # no-epoch visit
    assert epoch_cells[1].span == 1  # V4 only
    assert epoch_cells[2].text == "Treatment"
    assert epoch_cells[2].span == 2  # V5, V6


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


@pytest.mark.parametrize(
    ("time_unit", "collapse_visit_groups"),
    [("day", True), ("week", True), ("day", False), ("week", False)],
)
def test_get_header_rows(
    mock_study_flowchart_service: StudyFlowchartService,
    time_unit: str,
    collapse_visit_groups: bool,
):
    visits = [
        visit
        for visit in mock_study_flowchart_service._get_study_visits()
        if visit.show_visit
        and visit.study_epoch.sponsor_preferred_name != settings.basic_epoch_name
    ]
    grouped_visits = mock_study_flowchart_service._group_visits(
        visits, collapse_visit_groups=collapse_visit_groups
    )

    header_rows = mock_study_flowchart_service._get_header_rows(
        grouped_visits,
        time_unit=time_unit,
        soa_preferences=StudySoaPreferencesInput(),
        layout=SoALayout.DETAILED,
    )

    visits = [
        visit_group[0]
        for _, epoch_grouping in grouped_visits
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
                == sum(len(epoch_group) for _, epoch_group in grouped_visits) + 1
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

    # Verify table structure
    assert len(table.rows) == len(DETAILED_SOA_TABLE.rows)
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
            and visit.study_epoch.sponsor_preferred_name != settings.basic_epoch_name
        }.values()
    )

    visits = [
        visit
        for visit in STUDY_VISITS
        if visit.show_visit
        and visit.study_epoch.sponsor_preferred_name != settings.basic_epoch_name
    ]
    grouped_visits = StudyFlowchartService._group_visits(
        visits, collapse_visit_groups=(layout != SoALayout.OPERATIONAL)
    )

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
    assert table.model_dump() == expected_table.model_dump()


@pytest.mark.parametrize("uids", [[], ["nonexistent-uid"]])
def test_split_flowchart_table_no_splits(
    uids: list[str], table: TableWithFootnotes = TINY_SOA_TABLE
):
    """Test StudyFlowchartService.split_flowchart_table when no split UIDs are provided"""

    slices = StudyFlowchartService.split_flowchart_table(table, uids)

    # Should return the original table as a single slice
    assert len(slices) == 1
    assert slices[0] == table


def test_split_flowchart_table_with_splits(table: TableWithFootnotes = TINY_SOA_TABLE):
    """Test StudyFlowchartService.split_flowchart_table with a single split UID"""

    slices = StudyFlowchartService.split_flowchart_table(table, ["visit-2"])

    # Should split at visit-2, creating 2 slices
    assert len(slices) == 2

    # First slice: Visits, V1
    slice0 = slices[0]
    # includes all rows
    assert len(slice0.rows) == len(table.rows)
    # same number of header rows/columns
    assert slice0.num_header_rows == table.num_header_rows
    assert slice0.num_header_cols == table.num_header_cols
    # same title and id
    assert slice0.title == table.title
    assert slice0.id == table.id
    # first slice has footnotes comment
    assert list(slice0.footnotes.keys()) == [""]
    # contains columns 0 and 1 (by index)
    for slice_row, orig_row in zip(slice0.rows, table.rows):
        assert slice_row.cells == orig_row.cells[:2]

    # Second slice: Visits, V2, V3
    slice1 = slices[1]
    # includes all rows
    assert len(slice1.rows) == len(table.rows)
    # same number of header rows/columns
    assert slice1.num_header_rows == table.num_header_rows
    assert slice1.num_header_cols == table.num_header_cols
    # same title and id
    assert slice1.title == table.title
    assert slice1.id == table.id
    # last slice has all the footnotes
    assert slice1.footnotes == table.footnotes
    # contains columns 0, 2, 3 and 4 (by index)
    for slice_row, orig_row in zip(slice1.rows, table.rows):
        assert slice_row.cells == [orig_row.cells[0]] + orig_row.cells[2:]


def test_split_flowchart_table_with_two_splits(
    table: TableWithFootnotes = TINY_SOA_TABLE,
):
    """Test StudyFlowchartService.split_flowchart_table with a single split UID"""

    slices = StudyFlowchartService.split_flowchart_table(table, ["visit-2", "visit-4"])

    # Should split at visit-2, creating 2 slices
    assert len(slices) == 3

    # First slice: Visits, V1
    slice0 = slices[0]
    # includes all rows
    assert len(slice0.rows) == len(table.rows)
    # same number of header rows/columns
    assert slice0.num_header_rows == table.num_header_rows
    assert slice0.num_header_cols == table.num_header_cols
    # same title and id
    assert slice0.title == table.title
    assert slice0.id == table.id
    # first slice has footnotes comment
    assert list(slice0.footnotes.keys()) == [""]
    # contains columns 0 and 1 (by index)
    for slice_row, orig_row in zip(slice0.rows, table.rows):
        assert slice_row.cells == orig_row.cells[:2]

    # Second slice: Visits, V2, V3
    slice1 = slices[1]
    # includes all rows
    assert len(slice1.rows) == len(table.rows)
    # same number of header rows/columns
    assert slice1.num_header_rows == table.num_header_rows
    assert slice1.num_header_cols == table.num_header_cols
    # same title and id
    assert slice1.title == table.title
    assert slice1.id == table.id
    # second slice has footnotes comment
    assert list(slice0.footnotes.keys()) == [""]
    # contains columns 0, 2 and 3 (by index)
    for i, (slice_row, orig_row) in enumerate(zip(slice1.rows, table.rows)):
        if i == 0:
            orig_row = orig_row.model_copy(deep=True)
            orig_row.cells[2].span = 2
        assert slice_row.cells == [orig_row.cells[0]] + orig_row.cells[2:4]

    # Third slice: Visits, V4
    slice2 = slices[2]
    # includes all rows
    assert len(slice2.rows) == len(table.rows)
    # same number of header rows/columns
    assert slice2.num_header_rows == table.num_header_rows
    assert slice2.num_header_cols == table.num_header_cols
    # same title and id
    assert slice2.title == table.title
    assert slice2.id == table.id
    # last slice has all the footnotes
    assert slice2.footnotes == table.footnotes
    # contains columns 0, 2 and 3 (by index)
    for i, (slice_row, orig_row) in enumerate(zip(slice2.rows, table.rows)):
        if i == 0:
            orig_row = orig_row.model_copy(deep=True)
            orig_row.cells[4] = orig_row.cells[2]
            orig_row.cells[4].span = 1
        assert slice_row.cells == [orig_row.cells[0], orig_row.cells[4]]


# Tests for Protocol Lab table functionality


class MockStudyFlowchartServiceLabTable(MockStudyFlowchartService):
    """Extended mock service for testing Protocol Lab table functionality"""

    def fetch_study_activities(self, *_args, **_kwargs):
        """Return activities with Laboratory Assessments group and subgroups"""
        activities = deepcopy(STUDY_ACTIVITIES)

        # Ensure we have Laboratory Assessments activities for testing
        lab_activities = [
            activity
            for activity in activities
            if activity.study_activity_group.activity_group_name
            == "Laboratory Assessments"
        ]

        # If no lab activities exist in test data, create some
        if not lab_activities:
            # Create test Laboratory Assessments activities
            lab_group = SimpleStudyActivityGroup(
                study_activity_group_uid="lab_group_uid",
                activity_group_name="Laboratory Assessments",
            )

            biochemistry_subgroup = SimpleStudyActivitySubGroup(
                study_activity_subgroup_uid="biochemistry_subgroup_uid",
                activity_subgroup_name="Biochemistry",
            )

            hematology_subgroup = SimpleStudyActivitySubGroup(
                study_activity_subgroup_uid="hematology_subgroup_uid",
                activity_subgroup_name="Hematology",
            )

            activities.append(
                StudySelectionActivity(
                    study_activity_uid="lab_activity_1",
                    study_activity_group=lab_group,
                    study_activity_subgroup=biochemistry_subgroup,
                    activity=ActivityForStudyActivity(
                        activity_name="Blood Chemistry",
                        uid="activity_1",
                        library_name="Sponsor",
                    ),
                    order=1,
                )
            )

            activities.append(
                StudySelectionActivity(
                    study_activity_uid="lab_activity_2",
                    study_activity_group=lab_group,
                    study_activity_subgroup=hematology_subgroup,
                    activity=ActivityForStudyActivity(
                        activity_name="Complete Blood Count",
                        uid="activity_2",
                        library_name="Sponsor",
                    ),
                    order=2,
                )
            )

        return activities


@pytest.fixture(scope="module")
def mock_study_flowchart_service_lab_table():
    return MockStudyFlowchartServiceLabTable()


def test_get_flowchart_table_lab_table(mock_study_flowchart_service_lab_table):
    """Test the new get_flowchart_table_lab_table method"""

    table = mock_study_flowchart_service_lab_table.get_flowchart_table_lab_table(
        study_uid="test_study", study_value_version=None, time_unit="week"
    )

    # THEN table is returned
    assert isinstance(table, TableWithFootnotes)

    # THEN table has correct structure for Lab table (2 header columns)
    assert table.num_header_cols == 2

    # THEN table has 1 header row (show_all_visits_lab_table defaults to False → no visit columns)
    assert table.num_header_rows == 1

    # THEN header row has correct structure (only 2 columns)
    header_row = table.rows[0]
    assert header_row.cells[0].text == _gettext("lab_assessments")
    assert header_row.cells[1].text == _gettext("parameters")
    assert len(header_row.cells) == 2


def test_get_flowchart_table_lab_table_filtering(
    mock_study_flowchart_service_lab_table,
):
    """Test that Laboratory Assessments filtering works correctly"""

    # Get all activities first
    all_activities = mock_study_flowchart_service_lab_table.fetch_study_activities()

    # Get filtered activities for Lab table
    table = mock_study_flowchart_service_lab_table.get_flowchart_table_lab_table(
        study_uid="test_study", study_value_version=None, time_unit="week"
    )

    # Count Laboratory Assessments activities
    lab_group_activities = [
        activity
        for activity in all_activities
        if activity.study_activity_group.activity_group_name == "Laboratory Assessments"
    ]

    # THEN all Laboratory Assessments activities are included in the table
    included_activity_uids = set()
    for row in table.rows[table.num_header_rows :]:
        for cell in row.cells:
            if cell.refs:
                for ref in cell.refs:
                    if ref.type == SoAItemType.STUDY_ACTIVITY.value:
                        included_activity_uids.add(ref.uid)

    assert (
        set(activity.study_activity_uid for activity in lab_group_activities)
        == included_activity_uids
    )


def test_get_header_rows_lab_table():
    """Test the new _get_header_rows_lab_table method"""

    # Create test data

    grouped_visits = [
        ("epoch1", {"visit1": [STUDY_VISITS[0]], "visit2": [STUDY_VISITS[1]]})
    ]

    soa_preferences = StudySoaPreferencesInput(
        show_epochs=True,
        show_milestones=False,
        baseline_as_time_zero=False,
        show_all_visits_lab_table=True,
    )

    header_rows = StudyFlowchartService._get_header_rows_lab_table(
        grouped_visits=grouped_visits, time_unit="week", soa_preferences=soa_preferences
    )

    # THEN returns correct number of header rows
    assert len(header_rows) == 4  # epochs, visits, timing, window

    # THEN first row has correct structure
    epochs_row = header_rows[0]
    assert epochs_row.cells[0].text == _gettext("lab_assessments")
    assert epochs_row.cells[1].text == _gettext("parameters")
    assert epochs_row.cells[2].text == _gettext("visits_list")

    # THEN subsequent rows have label in first cell and empty second cell
    for row in header_rows[1:]:
        assert row.cells[0].text != ""  # Label column (visit name / timing / window)
        assert row.cells[1].text == ""  # Empty activity column


def test_get_activity_rows_lab_table():
    """Test the new _get_activity_rows_lab_table method"""

    # Create test activities with Laboratory Assessments
    activities = MockStudyFlowchartServiceLabTable().fetch_study_activities()
    lab_activities = [
        activity
        for activity in activities
        if activity.study_activity_group.activity_group_name == "Laboratory Assessments"
    ]

    grouped_visits = [
        ("epoch1", {"visit1": [STUDY_VISITS[0]], "visit2": [STUDY_VISITS[1]]})
    ]

    activity_rows = StudyFlowchartService._get_activity_rows_lab_table(
        study_selection_activities=lab_activities,
        study_activity_schedules=[],
        grouped_visits=grouped_visits,
    )

    # THEN returns activity rows
    assert len(activity_rows) >= 0

    if lab_activities and activity_rows:
        # THEN first row has subgroup name in first cell
        first_row = activity_rows[0]
        assert len(first_row.cells) >= 2

        # Check that subgroup name is present in the first cell
        first_cell = first_row.cells[0]
        if first_cell.text:
            # Should contain a subgroup name
            assert first_cell.text != ""

        # Check that second cell contains activity information
        second_cell = first_row.cells[1]
        assert second_cell.refs is not None
        if second_cell.refs:
            # Should have activity reference
            activity_refs = [
                ref
                for ref in second_cell.refs
                if ref.type == SoAItemType.STUDY_ACTIVITY.value
            ]
            assert len(activity_refs) > 0


def test_hide_rows_without_checkmarks():
    """Test the _hide_rows_without_checkmarks method"""

    # Create test table with some rows having checkmarks and some not
    rows = [
        # Header rows
        TableRow(cells=[TableCell("Header1"), TableCell("Header2")]),
        TableRow(cells=[TableCell("Header1"), TableCell("Header2")]),
        # Activity rows - some with checkmarks, some without
        TableRow(
            cells=[
                TableCell("Subgroup1"),
                TableCell("Activity1"),
                TableCell("X"),  # Has checkmark
                TableCell(""),
            ]
        ),
        TableRow(
            cells=[
                TableCell("Subgroup2"),
                TableCell("Activity2"),
                TableCell(""),  # No checkmark
                TableCell(""),
            ]
        ),
        TableRow(
            cells=[
                TableCell("Subgroup3"),
                TableCell("Activity3"),
                TableCell(""),  # No checkmark
                TableCell("X"),  # Has checkmark
            ]
        ),
    ]

    # Apply the method
    StudyFlowchartService._hide_rows_without_checkmarks(
        rows, num_header_rows=2, num_header_cols=2
    )

    # THEN header rows are not hidden
    assert not rows[0].hide
    assert not rows[1].hide

    # THEN row with checkmark is not hidden
    assert not rows[2].hide

    # THEN row without checkmarks is hidden
    assert rows[3].hide

    # THEN row with checkmark is not hidden
    assert not rows[4].hide


def test_protocol_lab_table_layout_enum():
    """Test that the PROTOCOL_LAB_TABLE enum value exists"""

    # THEN enum value exists
    assert hasattr(SoALayout, "PROTOCOL_LAB_TABLE")
    assert SoALayout.PROTOCOL_LAB_TABLE.value == "protocol_lab_table"


def test_footnote_filtering_for_visible_rows():
    """Test that for PROTOCOL layout, footnotes are filtered to only include those referenced in visible rows"""

    # Create test footnotes
    footnote1 = StudySoAFootnote(
        uid="footnote1",
        study_uid="test_study",
        footnote=CompactFootnote(
            uid="compact_footnote1", name="Footnote 1", name_plain="Footnote 1"
        ),
        referenced_items=[
            ReferencedItem(item_uid="activity1", item_type=SoAItemType.STUDY_ACTIVITY)
        ],
    )
    footnote2 = StudySoAFootnote(
        uid="footnote2",
        study_uid="test_study",
        footnote=CompactFootnote(
            uid="compact_footnote2", name="Footnote 2", name_plain="Footnote 2"
        ),
        referenced_items=[
            ReferencedItem(item_uid="activity2", item_type=SoAItemType.STUDY_ACTIVITY)
        ],
    )
    footnote3 = StudySoAFootnote(
        uid="footnote3",
        study_uid="test_study",
        footnote=CompactFootnote(
            uid="compact_footnote3", name="Footnote 3", name_plain="Footnote 3"
        ),
        referenced_items=[
            ReferencedItem(item_uid="activity3", item_type=SoAItemType.STUDY_ACTIVITY)
        ],
    )

    # Create table with some visible and some hidden rows
    soa_table = TableWithFootnotes(
        rows=[
            TableRow(cells=[TableCell("Header")]),  # Header row - visible
            TableRow(
                cells=[
                    TableCell(
                        "Activity1",
                        refs=[
                            Ref(type_=SoAItemType.STUDY_ACTIVITY.value, uid="activity1")
                        ],
                    )
                ],
                hide=False,
            ),  # Visible row referencing activity1
            TableRow(
                cells=[
                    TableCell(
                        "Activity2",
                        refs=[
                            Ref(type_=SoAItemType.STUDY_ACTIVITY.value, uid="activity2")
                        ],
                    )
                ],
                hide=True,
            ),  # Hidden row referencing activity2
            TableRow(
                cells=[
                    TableCell(
                        "Activity3",
                        refs=[
                            Ref(type_=SoAItemType.STUDY_ACTIVITY.value, uid="activity3")
                        ],
                    )
                ],
                hide=False,
            ),  # Visible row referencing activity3
        ],
        num_header_rows=1,
        num_header_cols=1,
    )

    all_footnotes = [footnote1, footnote2, footnote3]

    for layout in SoALayout.PROTOCOL, SoALayout.DETAILED:
        # Apply footnotes to table
        table = deepcopy(soa_table)
        StudyFlowchartService().add_footnotes(table, all_footnotes, layout=layout)

        actual_footnote_uids = {fn.uid for fn in table.footnotes.values()}

        # footnote1 and footnote3 are referenced in visible rows — must be present
        assert (
            "footnote1" in actual_footnote_uids
        ), "footnote1 (visible row) should be included"
        assert (
            "footnote3" in actual_footnote_uids
        ), "footnote3 (visible row) should be included"

        if layout == SoALayout.PROTOCOL:
            # THEN only footnotes referenced in visible rows are included in PROTOCOL layout
            # footnote2 is only referenced in a hidden row — must be excluded
            assert (
                "footnote2" not in actual_footnote_uids
            ), f"footnote2 (hidden row only) should be excluded in {layout} layout"

        else:
            # THEN all footnotes are included in DETAILED layout
            assert (
                "footnote2" in actual_footnote_uids
            ), f"footnote2 (hidden row) should be included in {layout} layout"


# Tests for show_all_visits_lab_table visit filtering


class MockStudyFlowchartServiceLabTableVisitFilter(MockStudyFlowchartService):
    """Mock service for testing show_all_visits_lab_table visit filtering.

    Setup:
    - 3 visible visits: V1, V2, V3
    - 2 lab activities: lab_act_1 (scheduled on V1), lab_act_2 (scheduled on V1, V2)
    - V3 has NO lab activity schedule → should be excluded when show_all_visits_lab_table=False
    """

    def __init__(self, show_all_visits_lab_table: bool = False):
        super().__init__()
        self._show_all_visits_lab_table = show_all_visits_lab_table

    def _get_soa_preferences(self, *_args, **_kwargs) -> StudySoaPreferencesInput:
        return StudySoaPreferencesInput(
            show_epochs=True,
            show_milestones=False,
            baseline_as_time_zero=False,
            show_all_visits_lab_table=self._show_all_visits_lab_table,
        )

    def _get_study_visits_dict_filtered(self, *_args, **_kwargs):
        # Return 3 visits across 2 epochs
        return {
            v.uid: v
            for v in STUDY_VISITS[:3]
            if v.show_visit  # V1 (000012), V2 (000013) — V3 (000014) has show_visit=False
        } | {
            STUDY_VISITS[3].uid: STUDY_VISITS[3]  # V4 (000015) — no lab schedule
        }

    def fetch_study_activities(self, *_args, **_kwargs):
        lab_group = SimpleStudyActivityGroup(
            study_activity_group_uid="lab_group_uid",
            activity_group_uid="ActivityGroup_Lab",
            activity_group_name="Laboratory Assessments",
        )
        subgroup = SimpleStudyActivitySubGroup(
            study_activity_subgroup_uid="sub_uid",
            activity_subgroup_uid="SubGroup_1",
            activity_subgroup_name="Biochemistry",
        )
        soa_group = SimpleStudySoAGroup(
            study_soa_group_uid="SoAGroup_1",
            soa_group_term_uid="CTTerm_Lab",
            soa_group_term_name="PROCEDURES",
        )
        return [
            StudySelectionActivity(
                study_uid="test_study",
                study_activity_uid="lab_act_1",
                study_activity_group=lab_group,
                study_activity_subgroup=subgroup,
                study_soa_group=soa_group,
                activity=ActivityForStudyActivity(
                    uid="Activity_Lab1",
                    activity_name="Blood Chemistry",
                    library_name="Sponsor",
                ),
                order=1,
            ),
            StudySelectionActivity(
                study_uid="test_study",
                study_activity_uid="lab_act_2",
                study_activity_group=lab_group,
                study_activity_subgroup=subgroup,
                study_soa_group=soa_group,
                activity=ActivityForStudyActivity(
                    uid="Activity_Lab2",
                    activity_name="Complete Blood Count",
                    library_name="Sponsor",
                ),
                order=2,
            ),
        ]

    def _get_study_activity_schedules(self, *_args, **_kwargs):
        # lab_act_1 scheduled on V1, lab_act_2 scheduled on V1 and V2
        # V4 has no lab schedule at all
        return [
            StudyActivitySchedule(
                study_activity_schedule_uid="sched_1",
                study_activity_uid="lab_act_1",
                study_visit_uid="StudyVisit_000012",  # V1
            ),
            StudyActivitySchedule(
                study_activity_schedule_uid="sched_2",
                study_activity_uid="lab_act_2",
                study_visit_uid="StudyVisit_000012",  # V1
            ),
            StudyActivitySchedule(
                study_activity_schedule_uid="sched_3",
                study_activity_uid="lab_act_2",
                study_visit_uid="StudyVisit_000013",  # V2
            ),
        ]

    def _get_study_footnotes(self, *_args, **_kwargs):
        return []


def _extract_visit_uids_from_table(table: TableWithFootnotes) -> set[str]:
    """Extract StudyVisit uids from visit header row refs."""
    visit_row = table.rows[1]  # visits row in lab table header
    uids: set[str] = set()
    for cell in visit_row.cells:
        if cell.refs:
            for ref in cell.refs:
                if ref.type == SoAItemType.STUDY_VISIT.value:
                    uids.add(ref.uid)
    return uids


def test_lab_table_show_all_visits_false_filters_unscheduled_visits():
    """When show_all_visits_lab_table=False, the table has only 2 columns (no visit columns)."""
    service = MockStudyFlowchartServiceLabTableVisitFilter(
        show_all_visits_lab_table=False
    )

    table = service.get_flowchart_table_lab_table(
        study_uid="test_study", study_value_version=None, time_unit="week"
    )

    # THEN table has only 1 header row (no visit header rows)
    assert table.num_header_rows == 1

    # THEN every row has exactly 2 cells (subgroup + activity, no visit columns)
    for row in table.rows:
        assert len(row.cells) == 2, f"Expected 2 columns, got {len(row.cells)}"


def test_lab_table_show_all_visits_true_includes_all_visits():
    """When show_all_visits_lab_table=True, only visits with lab schedules are included."""
    service = MockStudyFlowchartServiceLabTableVisitFilter(
        show_all_visits_lab_table=True
    )

    table = service.get_flowchart_table_lab_table(
        study_uid="test_study", study_value_version=None, time_unit="week"
    )

    visit_uids = _extract_visit_uids_from_table(table)

    # V1 and V2 have lab schedules — must be present
    assert "StudyVisit_000012" in visit_uids, "V1 should be included"
    assert "StudyVisit_000013" in visit_uids, "V2 should be included"

    # V4 has no lab schedule — always filtered out
    assert "StudyVisit_000015" not in visit_uids, "V4 (unscheduled) should be excluded"


def test_lab_table_show_all_visits_false_fewer_columns_than_true():
    """When filtering is active, the table has fewer visit columns than when all visits are shown."""
    service_filtered = MockStudyFlowchartServiceLabTableVisitFilter(
        show_all_visits_lab_table=False
    )
    service_all = MockStudyFlowchartServiceLabTableVisitFilter(
        show_all_visits_lab_table=True
    )

    table_filtered = service_filtered.get_flowchart_table_lab_table(
        study_uid="test_study", study_value_version=None, time_unit="week"
    )
    table_all = service_all.get_flowchart_table_lab_table(
        study_uid="test_study", study_value_version=None, time_unit="week"
    )

    # Visit header row (row index 1)
    filtered_visit_count = len(_extract_visit_uids_from_table(table_filtered))
    all_visit_count = len(_extract_visit_uids_from_table(table_all))

    assert filtered_visit_count < all_visit_count, (
        f"Filtered table should have fewer visit columns ({filtered_visit_count}) "
        f"than unfiltered table ({all_visit_count})"
    )


# Tests for unscheduled visit and non-visit inclusion/exclusion by layout


@pytest.mark.parametrize(
    "layout",
    [SoALayout.DETAILED, SoALayout.OPERATIONAL],
)
@pytest.mark.parametrize(
    "visit_class",
    [VisitClass.UNSCHEDULED_VISIT, VisitClass.NON_VISIT],
)
def test_basic_epoch_visits_included_in_detailed_and_operational(
    mock_study_flowchart_service: StudyFlowchartService,
    layout: SoALayout,
    visit_class: VisitClass,
):
    """Unscheduled and non-visit visits appear in Detailed and Operational SoA, even though they are in the Basic epoch."""
    visits = mock_study_flowchart_service._get_study_visits_dict_filtered(
        study_uid="", study_value_version=None, layout=layout
    )
    matching_uids = {uid for uid, v in visits.items() if v.visit_class == visit_class}
    assert matching_uids, f"{visit_class.value} should be present in {layout.value} SoA"


@pytest.mark.parametrize(
    "layout",
    [SoALayout.PROTOCOL, SoALayout.PROTOCOL_LAB_TABLE],
)
@pytest.mark.parametrize(
    "visit_class",
    [VisitClass.UNSCHEDULED_VISIT, VisitClass.NON_VISIT],
)
def test_basic_epoch_visits_excluded_from_protocol(
    mock_study_flowchart_service: StudyFlowchartService,
    layout: SoALayout,
    visit_class: VisitClass,
):
    """Unscheduled and non-visit visits must NOT appear in Protocol SoA or Protocol Lab Table."""
    visits = mock_study_flowchart_service._get_study_visits_dict_filtered(
        study_uid="", study_value_version=None, layout=layout
    )
    matching_uids = {uid for uid, v in visits.items() if v.visit_class == visit_class}
    assert (
        not matching_uids
    ), f"{visit_class.value} should NOT be present in {layout.value} SoA"
