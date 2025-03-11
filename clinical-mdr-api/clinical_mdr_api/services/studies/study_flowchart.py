import logging
from collections import defaultdict
from datetime import datetime
from typing import Iterable, Mapping, Sequence

from docx.enum.style import WD_STYLE_TYPE
from neomodel import db
from openpyxl.workbook import Workbook

from clinical_mdr_api.domain_repositories.study_selections.study_soa_repository import (
    SoALayout,
    StudySoARepository,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
from clinical_mdr_api.models.study_selections.study import (
    Study,
    StudySoaPreferences,
    StudySoaPreferencesInput,
)
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpoch
from clinical_mdr_api.models.study_selections.study_selection import (
    CellCoordinates,
    ReferencedItem,
    SoACellReference,
    SoAFootnoteReference,
    StudyActivityGroup,
    StudyActivitySchedule,
    StudyActivitySubGroup,
    StudySelectionActivity,
    StudySelectionActivityInstance,
    StudySoAGroup,
)
from clinical_mdr_api.models.study_selections.study_soa_footnote import StudySoAFootnote
from clinical_mdr_api.models.study_selections.study_visit import StudyVisit
from clinical_mdr_api.models.syntax_instances.footnote import Footnote
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.services._utils import ensure_transaction
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
from clinical_mdr_api.services.studies.study_soa_footnote import StudySoAFootnoteService
from clinical_mdr_api.services.studies.study_soa_group import StudySoAGroupService
from clinical_mdr_api.services.studies.study_visit import StudyVisitService
from clinical_mdr_api.services.utils.docx_builder import DocxBuilder
from clinical_mdr_api.services.utils.table_f import (
    Ref,
    SimpleFootnote,
    TableCell,
    TableRow,
    TableWithFootnotes,
    table_to_docx,
    table_to_html,
    table_to_xlsx,
)
from clinical_mdr_api.utils import enumerate_letters
from common import config
from common.auth.user import user
from common.exceptions import BusinessLogicException, NotFoundException
from common.telemetry import trace_calls

NUM_OPERATIONAL_CODE_ROWS = 2
SOA_CHECK_MARK = "X"

# Strings prepared for localization
_T = {
    "study_epoch": "",
    "procedure_label": "Procedure",
    "study_milestone": "",
    "protocol_section": "Protocol Section",
    "visit_short_name": "Visit short name",
    "study_week": "Study week",
    "study_day": "Study day",
    "visit_window": "Visit window ({unit_name})",
    "protocol_flowchart": "Protocol Flowchart",
    "operational_soa": "Operational SoA",
    "no_study_group": "(not selected)",
    "no_study_subgroup": "(not selected)",
    "topic_code": "Topic Code",
    "adam_param_code": "ADaM Param Code",
    "soagroup": "soagroup",
    "group": "group",
    "subgroup": "subgroup",
    "activity": "Activity",
}.get

log = logging.getLogger(__name__)

# pylint: disable=no-member
DOCX_STYLES = {
    "table": ("SB Table Condensed", WD_STYLE_TYPE.TABLE),
    "header1": ("Table Header lvl1", WD_STYLE_TYPE.PARAGRAPH),
    "header2": ("Table Header lvl2", WD_STYLE_TYPE.PARAGRAPH),
    "header3": ("Table Header lvl2", WD_STYLE_TYPE.PARAGRAPH),
    "header4": ("Table Header lvl2", WD_STYLE_TYPE.PARAGRAPH),
    "soaGroup": ("Table lvl 1", WD_STYLE_TYPE.PARAGRAPH),
    "group": ("Table lvl 2", WD_STYLE_TYPE.PARAGRAPH),
    "subGroup": ("Table lvl 3", WD_STYLE_TYPE.PARAGRAPH),
    "activity": ("Table lvl 4", WD_STYLE_TYPE.PARAGRAPH),
    "activityInstance": ("Table lvl 4", WD_STYLE_TYPE.PARAGRAPH),
    "cell": ("Table Text", WD_STYLE_TYPE.PARAGRAPH),
    "footnote": ("Table Text", WD_STYLE_TYPE.PARAGRAPH),
}

OPERATIONAL_DOCX_STYLES = {
    "table": ("SB Table Condensed", WD_STYLE_TYPE.TABLE),
    "header1": ("Table cell", WD_STYLE_TYPE.PARAGRAPH),
    "header2": ("Table cell", WD_STYLE_TYPE.PARAGRAPH),
    "header3": ("Table cell", WD_STYLE_TYPE.PARAGRAPH),
    "header4": ("Table cell", WD_STYLE_TYPE.PARAGRAPH),
    "soaGroup": ("SoAGroup", WD_STYLE_TYPE.PARAGRAPH),
    "group": ("ActivityGroup", WD_STYLE_TYPE.PARAGRAPH),
    "subGroup": ("ActivitySubGroup", WD_STYLE_TYPE.PARAGRAPH),
    "activity": ("Table cell", WD_STYLE_TYPE.PARAGRAPH),
    "activityInstance": ("Table cell", WD_STYLE_TYPE.PARAGRAPH),
    "cell": ("Table cell", WD_STYLE_TYPE.PARAGRAPH),
    "activitySchedule": ("Table cell", WD_STYLE_TYPE.PARAGRAPH),
    None: ("Table cell", WD_STYLE_TYPE.PARAGRAPH),
    "footnote": ("Table cell", WD_STYLE_TYPE.PARAGRAPH),
}

OPERATIONAL_XLSX_STYLES = {
    "studyVersion": "Note",
    "studyNumber": "Note",
    "dateTime": "Note",
    "extractedBy": "Note",
    "header1": "Heading 1",
    "header2": "Heading 2",
    "header3": "Heading 3",
    "visibility": "Heading 4",
    "soaGroup": "Heading 4",
    "group": "Heading 4",
    "subGroup": "Heading 4",
    "activity": "Heading 4",
    "topicCode": "Heading 4",
    "adamCode": "Heading 4",
    None: "Normal",
    "activitySchedule": "Normal",
}


class StudyFlowchartService:
    """Service to build/retrieve Study Shedule-of-Activities (SoA, was: Flowchart) table and footnotes"""

    def __init__(self) -> None:
        self.user = user().id()
        self._study_service = StudyService()
        self._study_activity_schedule_service = StudyActivityScheduleService()
        self._study_soa_footnote_service = StudySoAFootnoteService()
        self._study_activity_selection_service = StudyActivitySelectionService()
        self._study_activity_instance_selection_service = (
            StudyActivityInstanceSelectionService()
        )

    _repository = None

    @property
    def repository(self):
        if self._repository is None:
            self._repository = StudySoARepository()
        return self._repository

    @trace_calls
    def _validate_parameters(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        time_unit: str | None = None,
    ):
        """
        Validates request parameters

        Raises NotFoundException if no Study with study_uid exists, or if Study doesn't have a version corresponding
        to optional study_value_version. Raises BusinessLogicException if time_unit is not "day" or "week".

        Args:
            study_uid (str): The unique identifier of the study.
            study_value_version (str | None): The version of the study to check. Defaults to None.
            time_unit (str): The preferred time unit, either "day" or "week".
        """
        self._study_service.check_if_study_uid_and_version_exists(
            study_uid, study_value_version=study_value_version
        )

        BusinessLogicException.raise_if(
            time_unit not in (None, "day", "week"),
            msg="time_unit has to be 'day' or 'week'",
        )

    @trace_calls
    def _get_study(
        self, study_uid: str, study_value_version: str | None = None
    ) -> Study:
        return self._study_service.get_by_uid(
            study_uid, study_value_version=study_value_version
        )

    @trace_calls
    def _get_study_activity_schedules(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        operational: bool = False,
    ) -> list[StudyActivitySchedule]:
        return self._study_activity_schedule_service.get_all_schedules(
            study_uid,
            study_value_version=study_value_version,
            operational=operational,
        )

    @trace_calls
    def _get_study_epochs(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudyEpoch]:
        return (
            StudyEpochService(
                study_uid=study_uid, study_value_version=study_value_version
            )
            .get_all_epochs(study_uid, study_value_version=study_value_version)
            .items
        )

    @trace_calls
    def _get_study_visits(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudyVisit]:
        return (
            StudyVisitService(
                study_uid=study_uid, study_value_version=study_value_version
            )
            .get_all_visits(study_uid, study_value_version=study_value_version)
            .items
        )

    @trace_calls
    def _get_study_footnotes(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudySoAFootnote]:
        return self._study_soa_footnote_service.get_all_by_study_uid(
            study_uid,
            sort_by={"order": True},
            study_value_version=study_value_version,
        ).items

    @trace_calls
    def _get_study_activities(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudySelectionActivity]:
        return self._study_activity_selection_service.get_all_selection(
            study_uid,
            study_value_version=study_value_version,
            sort_by={"order": True},
        ).items

    @trace_calls
    def _get_study_soa_groups(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudySoAGroup]:
        return (
            StudySoAGroupService()
            .get_all_selection(
                study_uid,
                study_value_version=study_value_version,
                sort_by={"order": True},
            )
            .items
        )

    @trace_calls
    def _get_study_activity_groups(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudyActivityGroup]:
        return (
            StudyActivityGroupService()
            .get_all_selection(
                study_uid,
                study_value_version=study_value_version,
                sort_by={"order": True},
            )
            .items
        )

    @trace_calls
    def _get_study_activity_subgroups(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudyActivitySubGroup]:
        return (
            StudyActivitySubGroupService()
            .get_all_selection(
                study_uid,
                study_value_version=study_value_version,
                sort_by={"order": True},
            )
            .items
        )

    @trace_calls
    def _get_study_activity_instances(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudySelectionActivity]:
        return self._study_activity_instance_selection_service.get_all_selection(
            study_uid,
            study_value_version=study_value_version,
            # filter-out activity placeholders
            filter_by={
                "activity.library_name": {
                    "v": [config.REQUESTED_LIBRARY_NAME],
                    "op": "ne",
                }
            },
        ).items

    @staticmethod
    @trace_calls(args=[1], kwargs=["hide_soa_groups"])
    def _sort_study_activities(
        study_selection_activities: list[StudySelectionActivity],
        hide_soa_groups: bool = False,
    ):
        """Sort StudySelectionActivities in place, grouping by SoAGroup, ActivityGroup, ActivitySubgroup"""

        soa_groups = {}
        activity_groups = {}
        activity_subgroups = {}
        order_keys = {}

        for activity in study_selection_activities:
            key = []

            if hide_soa_groups and not getattr(
                activity, "show_soa_group_in_protocol_flowchart", None
            ):
                key.append(-1)

            else:
                key.append(
                    soa_groups.setdefault(
                        activity.study_soa_group.soa_group_term_uid, len(soa_groups)
                    )
                )

            key.append(
                activity_groups.setdefault(
                    activity.study_activity_group.activity_group_uid,
                    (
                        len(activity_groups)
                        if activity.study_activity_group.activity_group_uid
                        else -1
                    ),
                )
            )

            key.append(
                activity_subgroups.setdefault(
                    activity.study_activity_subgroup.activity_subgroup_uid,
                    len(activity_subgroups),
                )
            )

            order_keys[activity.study_activity_uid] = tuple(key)

        list.sort(
            study_selection_activities,
            key=lambda activity: order_keys.get(activity.study_activity_uid),
        )

    @staticmethod
    @trace_calls
    def _group_visits(
        visits: Iterable[StudyVisit],
    ) -> dict[str, dict[str, list[StudyVisit]]]:
        """
        Builds a graph of visits from nested dict of
        study_epoch_uid -> [ consecutive_visit_group | visit_uid ] -> [Visits]
        """

        grouped = {}
        visits: list[StudyVisit] = sorted(visits, key=lambda v: v.order)

        for visit in visits:
            grouped.setdefault(visit.study_epoch_uid, {}).setdefault(
                visit.consecutive_visit_group or visit.uid, []
            ).append(visit)

        return grouped

    @classmethod
    @trace_calls
    def _mk_simple_footnotes(
        cls,
        footnotes: Sequence[StudySoAFootnote],
    ) -> tuple[dict[str, list[str]], dict[str, Footnote]]:
        # mapping of referenced item uid to list of footnote symbols (to display in table cell)
        footnote_symbols_by_ref_uid: dict[str, list[str]] = {}

        # mapping of footnote symbols to SimpleFootnote model to print footnotes at end of document
        simple_footnotes_by_symbol: dict[str, Footnote] = {}
        for symbol, soa_footnote in enumerate_letters(footnotes):
            simple_footnotes_by_symbol[symbol] = cls._to_simple_footnote(soa_footnote)

            for ref in soa_footnote.referenced_items:
                footnote_symbols_by_ref_uid.setdefault(ref.item_uid, []).append(symbol)

        return (
            footnote_symbols_by_ref_uid,
            simple_footnotes_by_symbol,
        )

    @staticmethod
    def _to_simple_footnote(soa_footnote):
        return SimpleFootnote(
            uid=soa_footnote.uid,
            text_html=(
                soa_footnote.footnote.name
                if soa_footnote.footnote
                else soa_footnote.template.name
            ),
            text_plain=(
                soa_footnote.footnote.name_plain
                if soa_footnote.footnote
                else soa_footnote.template.name_plain
            ),
        )

    @trace_calls
    def get_flowchart_item_uid_coordinates(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        hide_soa_groups: bool = False,
    ) -> dict[str, CellCoordinates]:
        """
        Returns mapping of item uid to [row, column] coordinates of item's position in the detailed SoA.

        Args:
            study_uid (str): The unique identifier of the study.
            study_value_version (str | None): The version of the study to check. Defaults to None.

        Returns:
            dict[str, tuple[int, int]: Mapping item uid to [row, column] coordinates
                                       of item's position in the detailed SoA table.
        """

        self._validate_parameters(study_uid, study_value_version=study_value_version)

        study_activity_schedules: list[StudyActivitySchedule] = (
            self._get_study_activity_schedules(
                study_uid, study_value_version=study_value_version
            )
        )

        # StudyActivitySchedules indexed by tuple of [StudyActivity.uid, StudyVisit.uid]
        study_activity_schedules_mapping = {
            (sas.study_activity_uid, sas.study_visit_uid): sas
            for sas in study_activity_schedules
        }

        study_selection_activities: list[StudySelectionActivity] = (
            self._get_study_activities(
                study_uid, study_value_version=study_value_version
            )
        )

        self._sort_study_activities(
            study_selection_activities, hide_soa_groups=hide_soa_groups
        )

        visits: list[StudyVisit] = self._get_study_visits(
            study_uid, study_value_version=study_value_version
        )

        grouped_visits = self._group_visits(visits)

        coordinates: dict[str, CellCoordinates] = {}

        col = 1
        for study_epoch_uid, visit_groups in grouped_visits.items():
            coordinates[study_epoch_uid] = CellCoordinates(0, col)
            for group in visit_groups.values():
                for visit in group:
                    coordinates[visit.uid] = CellCoordinates(1, col)
                col += 1

        row = 4

        prev_soa_group_uid, soa_group_row = False, None
        prev_activity_group_uid, activity_group_row = False, None
        prev_activity_subgroup_uid, activity_subgroup_row = False, None

        study_selection_activity: StudySelectionActivity
        for study_selection_activity in study_selection_activities:
            soa_group_uid = study_selection_activity.study_soa_group.soa_group_term_uid

            if soa_group_uid != prev_soa_group_uid:
                prev_soa_group_uid, soa_group_row = soa_group_uid, row
                prev_activity_group_uid, activity_group_row = False, None
                prev_activity_subgroup_uid, activity_subgroup_row = False, None
                row += 1

            coordinates[
                study_selection_activity.study_soa_group.study_soa_group_uid
            ] = CellCoordinates(soa_group_row, 0)

            activity_group_uid = (
                study_selection_activity.study_activity_group.activity_group_uid
            )

            if prev_activity_group_uid != activity_group_uid:
                prev_activity_group_uid, activity_group_row = activity_group_uid, row
                prev_activity_subgroup_uid, activity_subgroup_row = False, None
                row += 1

            if study_selection_activity.study_activity_group.study_activity_group_uid:
                coordinates[
                    study_selection_activity.study_activity_group.study_activity_group_uid
                ] = CellCoordinates(activity_group_row, 0)

            activity_subgroup_uid = (
                study_selection_activity.study_activity_subgroup.activity_subgroup_uid
            )

            if prev_activity_subgroup_uid != activity_subgroup_uid:
                prev_activity_subgroup_uid = activity_subgroup_uid
                activity_subgroup_row = row
                row += 1

            if (
                study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
            ):
                coordinates[
                    study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
                ] = CellCoordinates(activity_subgroup_row, 0)

            coordinates[study_selection_activity.study_activity_uid] = CellCoordinates(
                row,
                0,
            )

            col = 0
            for visit_groups in grouped_visits.values():
                for group in visit_groups.values():
                    col += 1

                    for visit in group:
                        study_activity_schedule: StudyActivitySchedule = (
                            study_activity_schedules_mapping.get(
                                (study_selection_activity.study_activity_uid, visit.uid)
                            )
                        )

                        if study_activity_schedule:
                            coordinates[
                                study_activity_schedule.study_activity_schedule_uid
                            ] = CellCoordinates(
                                row,
                                col,
                            )

            row += 1

        return coordinates

    @trace_calls
    def get_flowchart_table(
        self,
        study_uid: str,
        time_unit: str | None = None,
        study_value_version: str | None = None,
        layout: SoALayout = SoALayout.PROTOCOL,
        force_build: bool = False,
    ) -> TableWithFootnotes:
        """Returns internal TableWithFootnotes representation of SoA, either from snapshot or freshly built"""

        if study_value_version and layout == SoALayout.PROTOCOL and not force_build:
            # Return protocol SoA from snapshot for a locked study version
            table = self.load_soa_snapshot(
                study_uid=study_uid,
                study_value_version=study_value_version,
                layout=layout,
                time_unit=time_unit,
            )

        else:
            # Build SoA (of the latest draft version or detailed and operational SoA of locked versions too)
            table = self.build_flowchart_table(
                study_uid=study_uid,
                time_unit=time_unit,
                study_value_version=study_value_version,
                operational=(layout == SoALayout.OPERATIONAL),
                hide_soa_groups=(layout == SoALayout.PROTOCOL),
            )

            if layout == SoALayout.PROTOCOL:
                # propagate checkmarks from hidden rows for protocol layout
                self.propagate_hidden_rows(table.rows)

                # remove hidden rows
                self.remove_hidden_rows(table)

        return table

    @trace_calls
    def build_flowchart_table(
        self,
        study_uid: str,
        time_unit: str | None = None,
        study_value_version: str | None = None,
        operational: bool = False,
        hide_soa_groups: bool = False,
    ) -> TableWithFootnotes:
        """
        Builds SoA flowchart table

        Args:
            study_uid (str): The unique identifier of the study.
            time_unit (str): The preferred time unit, either "day" or "week".
            study_value_version (str | None): The version of the study to check. Defaults to None.
            operational (bool): Defaults to False, gets protocol SoA, or operational SoA when True.

        Returns:
            TableWithFootnotes: SoA flowchart table with footnotes.
        """

        soa_preferences = self._get_soa_preferences(
            study_uid, study_value_version=study_value_version
        )

        if not time_unit:
            time_unit = self.get_preferred_time_unit(
                study_uid, study_value_version=study_value_version
            )

        self._validate_parameters(
            study_uid, study_value_version=study_value_version, time_unit=time_unit
        )

        selection_activities = self._get_study_selection_activities_sorted(
            study_uid=study_uid,
            study_value_version=study_value_version,
            operational=operational,
            hide_soa_groups=hide_soa_groups,
        )

        activity_schedules: list[StudyActivitySchedule] = (
            self._get_study_activity_schedules(
                study_uid,
                study_value_version=study_value_version,
                operational=operational,
            )
        )

        visits = self._get_study_visits_dict_filtered(study_uid, study_value_version)

        # group visits in nested dict: study_epoch_uid -> [ consecutive_visit_group |  visit_uid ] -> [Visits]
        grouped_visits = self._group_visits(visits.values())

        # first 4 rows of protocol SoA flowchart contains epochs & visits
        header_rows = self._get_header_rows(
            grouped_visits, time_unit, soa_preferences, operational
        )

        # activity rows with grouping headers and check-marks
        activity_rows = self._get_activity_rows(
            selection_activities,
            activity_schedules,
            grouped_visits,
            operational,
            hide_soa_groups=hide_soa_groups,
        )

        table = TableWithFootnotes(
            rows=header_rows + activity_rows,
            num_header_rows=len(header_rows),
            num_header_cols=1,
            title=_T("protocol_flowchart"),
        )

        if not operational:
            footnotes: list[StudySoAFootnote] = self._get_study_footnotes(
                study_uid, study_value_version=study_value_version
            )

            self.add_footnotes(table, footnotes)

            if hide_soa_groups:
                # amend procedure label on protocol SoA
                StudyFlowchartService.amend_procedure_label(table)

        return table

    @trace_calls
    def _get_study_selection_activities_sorted(
        self,
        study_uid: str,
        study_value_version: str,
        operational: bool,
        hide_soa_groups: bool,
    ) -> list[StudySelectionActivity | StudySelectionActivityInstance]:
        if operational:
            selection_activities: list[StudySelectionActivityInstance] = (
                self._get_study_activity_instances(
                    study_uid, study_value_version=study_value_version
                )
            )

        else:
            selection_activities: list[StudySelectionActivity] = (
                self._get_study_activities(
                    study_uid, study_value_version=study_value_version
                )
            )

        self._sort_study_activities(
            selection_activities, hide_soa_groups=hide_soa_groups
        )

        return selection_activities

    @trace_calls
    def _get_study_visits_dict_filtered(self, study_uid, study_value_version):
        # get visits
        visits = self._get_study_visits(
            study_uid, study_value_version=study_value_version
        )

        # filter for visible visits
        visits = {
            visit.uid: visit
            for visit in visits
            if (
                visit.show_visit
                and visit.study_epoch.sponsor_preferred_name != config.BASIC_EPOCH_NAME
            )
        }

        return visits

    @trace_calls
    def get_study_flowchart_html(
        self,
        study_uid: str,
        study_value_version: str | None,
        time_unit: str | None,
        detailed: bool | None,
        debug_uids: bool | None,
        debug_coordinates: bool | None,
        debug_propagation: bool | None,
        operational: bool | None,
    ) -> str:
        # build internal representation of flowchart
        table = self.get_flowchart_table(
            study_uid=study_uid,
            time_unit=time_unit,
            study_value_version=study_value_version,
            layout=self.choose_soa_layout(detailed, operational),
        )

        # layout alterations
        if detailed or operational:
            self.show_hidden_rows(table.rows)

        # debugging
        if debug_propagation:
            self.propagate_hidden_rows(table.rows)
            self.show_hidden_rows(table.rows)

        if debug_coordinates:
            coordinates = self.get_flowchart_item_uid_coordinates(
                study_uid=study_uid, study_value_version=study_value_version
            )
            self.add_coordinates(table, coordinates)

        if debug_uids:
            self.add_uid_debug(table)

        # convert flowchart to HTML document
        return table_to_html(table)

    @trace_calls
    def get_study_flowchart_docx(
        self,
        study_uid: str,
        study_value_version: str | None,
        time_unit: str | None,
        detailed: bool | None,
        operational: bool | None,
    ) -> DocxBuilder:
        """Returns a DOCX document with SoA table and footnotes"""

        # build internal representation of flowchart
        table = self.get_flowchart_table(
            study_uid=study_uid,
            time_unit=time_unit,
            study_value_version=study_value_version,
            layout=self.choose_soa_layout(detailed, operational),
        )

        # layout alterations
        if detailed or operational:
            self.show_hidden_rows(table.rows)

        # Add Protocol Section column
        if not operational:
            self.add_protocol_section_column(table)

        # convert flowchart to DOCX document applying styles
        return table_to_docx(
            table,
            styles=OPERATIONAL_DOCX_STYLES if operational else DOCX_STYLES,
            template=config.OPERATIONAL_SOA_DOCX_TEMPLATE if operational else None,
        )

    @trace_calls
    def get_operational_soa_xlsx(
        self,
        study_uid: str,
        study_value_version: str | None,
        time_unit: str | None,
    ) -> Workbook:
        # build internal representation of flowchart
        table = self.get_operational_spreadsheet(
            study_uid=study_uid,
            time_unit=time_unit,
            study_value_version=study_value_version,
        )

        return table_to_xlsx(table, styles=OPERATIONAL_XLSX_STYLES)

    @trace_calls
    def get_operational_soa_html(
        self,
        study_uid: str,
        study_value_version: str | None,
        time_unit: str | None,
    ) -> str:
        table = self.get_operational_spreadsheet(
            study_uid=study_uid,
            time_unit=time_unit,
            study_value_version=study_value_version,
        )
        return table_to_html(
            table,
            css_style="table, th { border: 2px solid black; border-collapse: collapse; }\n"
            "td { border: 1px solid black; }",
        )

    @trace_calls
    def get_operational_spreadsheet(
        self,
        study_uid: str,
        time_unit: str | None = None,
        study_value_version: str | None = None,
    ) -> TableWithFootnotes:
        """
        Builds operational SoA table in spreadsheet format

        Args:
            study_uid (str): The unique identifier of the study.
            time_unit (str): The preferred time unit, either "day" or "week".
            study_value_version (str | None): The version of the study to check. Defaults to None.

        Returns:
            TableWithFootnotes: Operational SoA flowchart table.
        """

        study = self._get_study(study_uid, study_value_version=study_value_version)

        if not time_unit:
            time_unit = self.get_preferred_time_unit(
                study_uid, study_value_version=study_value_version
            )

        self._validate_parameters(
            study_uid, study_value_version=study_value_version, time_unit=time_unit
        )

        selection_activities = self._get_study_selection_activities_sorted(
            study_uid=study_uid,
            study_value_version=study_value_version,
            operational=True,
            hide_soa_groups=False,
        )

        study_activity_schedules: list[StudyActivitySchedule] = (
            self._get_study_activity_schedules(
                study_uid,
                study_value_version=study_value_version,
                operational=True,
            )
        )

        visits = self._get_study_visits_dict_filtered(study_uid, study_value_version)

        # group visits in nested dict: study_epoch_uid -> [ consecutive_visit_group |  visit_uid ] -> [Visits]
        grouped_visits = self._group_visits(visits.values())

        # StudyActivitySchedules indexed by tuple of [uid, StudyVisit.uid]
        study_activity_schedules_mapping = {
            (
                sas.study_activity_instance_uid or sas.study_activity_uid,
                sas.study_visit_uid,
            ): sas
            for sas in study_activity_schedules
        }

        # header rows
        rows = [
            TableRow(
                cells=[
                    TableCell(
                        f"study_version: {study_version(study)}",
                        span=3,
                        style="studyVersion",
                    )
                ]
                + [TableCell(span=0, style="studyVersion")] * 2
            ),
            TableRow(
                cells=[
                    TableCell(
                        f"study_number: {study.current_metadata.identification_metadata.study_id}",
                        span=3,
                        style="studyNumber",
                    )
                ]
                + [TableCell(span=0, style="studyNumber")] * 2
            ),
            TableRow(
                cells=[
                    TableCell(
                        f"Date/time of extraction: {datetime.now().strftime('%Y-%m-%d %H:%M:%S Z')}",
                        span=3,
                        style="dateTime",
                    ),
                    TableCell(span=0, style="dateTime"),
                    TableCell(span=0, style="dateTime"),
                    TableCell(f"By: {user().id()}", span=2, style="extractedBy"),
                    TableCell(span=0, style="extractedBy"),
                    TableCell(span=2),
                    TableCell("Epochs", style="header1"),
                ]
            ),
            TableRow(
                cells=[
                    TableCell("lowest visibility layer", style="header3"),
                    TableCell("SoA group", style="header3"),
                    TableCell("Group", style="header3"),
                    TableCell("Subgroup", style="header3"),
                    TableCell("Activity", style="header3"),
                    TableCell("Topic Code", style="header3"),
                    TableCell("ADaM Param Code", style="header3"),
                    TableCell("Visits", style="header1"),
                ]
            ),
        ]

        # add epoch and visit cells to header rows
        perv_study_epoch_uid = None
        for study_epoch_uid, visit_groups in grouped_visits.items():
            for group in visit_groups.values():
                visit: StudyVisit = group[0]

                # Epoch
                if perv_study_epoch_uid != study_epoch_uid:
                    perv_study_epoch_uid = study_epoch_uid

                    rows[-2].cells.append(
                        TableCell(
                            text=visit.study_epoch.sponsor_preferred_name,
                            span=len(visit_groups),
                            style="header2",
                        )
                    )

                else:
                    rows[-2].cells.append(TableCell(span=0, style="header2"))

                # Visit
                rows[-1].cells.append(
                    TableCell(
                        (
                            visit.consecutive_visit_group
                            if len(group) > 1
                            else visit.visit_short_name
                        ),
                        style="header3",
                    )
                )

        # Add activity rows
        visit_groups: list[list[StudyVisit]] = [
            visit_group
            for epochs_group in grouped_visits.values()
            for visit_group in epochs_group.values()
        ]

        for study_selection_activity in selection_activities:
            rows.append(row := TableRow())

            # Visibility
            if getattr(
                study_selection_activity, "show_activity_in_protocol_flowchart", True
            ):
                row.cells.append(TableCell(_T("activity"), style="visibility"))
            elif getattr(
                study_selection_activity,
                "show_activity_subgroup_in_protocol_flowchart",
                True,
            ):
                row.cells.append(TableCell(_T("subgroup"), style="visibility"))
            elif getattr(
                study_selection_activity,
                "show_activity_group_in_protocol_flowchart",
                True,
            ):
                row.cells.append(TableCell(_T("group"), style="visibility"))
            elif getattr(
                study_selection_activity, "show_soa_group_in_protocol_flowchart", True
            ):
                row.cells.append(TableCell(_T("soagroup"), style="visibility"))
            else:
                row.cells.append(TableCell(style="visibility"))

            # SoA Group
            row.cells.append(
                TableCell(
                    study_selection_activity.study_soa_group.soa_group_term_name,
                    style="soaGroup",
                )
            )

            # Activity Group
            row.cells.append(
                TableCell(
                    (
                        study_selection_activity.study_activity_group.activity_group_name
                        if study_selection_activity.study_activity_group.activity_group_uid
                        else _T("no_study_group")
                    ),
                    style="group",
                )
            )

            # Activity Sub-Group
            row.cells.append(
                TableCell(
                    (
                        study_selection_activity.study_activity_subgroup.activity_subgroup_name
                        if study_selection_activity.study_activity_subgroup.activity_subgroup_uid
                        else _T("no_study_subgroup")
                    ),
                    style="subGroup",
                )
            )

            # Activity
            row.cells.append(
                TableCell(study_selection_activity.activity.name, style="activity")
            )

            # Topic Code
            row.cells.append(
                TableCell(
                    (
                        study_selection_activity.activity_instance.topic_code
                        if study_selection_activity.activity_instance
                        else ""
                    ),
                    style="topicCode",
                )
            )

            # ADaM Param Code
            row.cells.append(
                TableCell(
                    (
                        study_selection_activity.activity_instance.adam_param_code
                        if study_selection_activity.activity_instance
                        else ""
                    ),
                    style="adamCode",
                )
            )

            # Empty header column
            row.cells.append(TableCell())

            # Scheduling crosses
            self._append_activity_crosses(
                row,
                visit_groups,
                study_activity_schedules_mapping,
                study_selection_activity.study_activity_instance_uid,
            )

        table = TableWithFootnotes(
            rows=rows,
            num_header_rows=4,
            num_header_cols=7,
            title=_T("operational_soa"),
        )

        return table

    @classmethod
    @trace_calls(args=[1, 2], kwargs=["time_unit", "operational"])
    def _get_header_rows(
        cls,
        grouped_visits: dict[str, dict[str, list[StudyVisit]]],
        time_unit: str,
        soa_preferences: StudySoaPreferencesInput,
        operational: bool = False,
    ) -> list[TableRow]:
        """Builds the 4 header rows of protocol SoA flowchart"""

        visit_timing_prop = cls._get_visit_timing_property(time_unit, soa_preferences)

        rows = []

        # Header line 1: Epoch names
        rows.append(epochs_row := TableRow())
        epochs_row.cells.append(TableCell(text=_T("study_epoch"), style="header1"))
        epochs_row.hide = not (operational or soa_preferences.show_epochs)

        # Header line 2 (optional): Milestones
        milestones_row = None
        if not operational and soa_preferences.show_milestones:
            rows.append(milestones_row := TableRow())
            milestones_row.cells.append(
                TableCell(text=_T("study_milestone"), style="header1")
            )
            milestones_row.hide = not soa_preferences.show_milestones

        # Header line 2/3: Visit names
        rows.append(visits_row := TableRow())
        visits_row.cells.append(TableCell(text=_T("visit_short_name"), style="header2"))

        # Header line 3/4: Visit timing day/week sequence
        rows.append(timing_row := TableRow())
        if time_unit == "day":
            timing_row.cells.append(TableCell(text=_T("study_day"), style="header3"))
        else:
            timing_row.cells.append(TableCell(text=_T("study_week"), style="header3"))

        # Header line 4/5: Visit window
        rows.append(window_row := TableRow())

        visit_window_unit = next(
            (
                group[0].visit_window_unit_name
                for visit_groups in grouped_visits.values()
                for group in visit_groups.values()
            ),
            "",
        )
        # Append window unit used for all StudyVisits
        window_row.cells.append(
            TableCell(
                text=_T("visit_window").format(unit_name=visit_window_unit),
                style="header4",
            )
        )

        # Add Operation SoA's extra columns
        if operational:
            epochs_row.cells.append(TableCell(text=_T("topic_code"), style="header2"))
            epochs_row.cells.append(
                TableCell(text=_T("adam_param_code"), style="header2")
            )
            for row in rows[1:]:
                for _j in range(NUM_OPERATIONAL_CODE_ROWS):
                    row.cells.append(TableCell())

        perv_study_epoch_uid = None
        prev_visit_type_uid = None
        for study_epoch_uid, visit_groups in grouped_visits.items():
            for group in visit_groups.values():
                visit: StudyVisit = group[0]

                # Open new Epoch column
                if perv_study_epoch_uid != study_epoch_uid:
                    perv_study_epoch_uid = study_epoch_uid

                    epochs_row.cells.append(
                        TableCell(
                            text=visit.study_epoch.sponsor_preferred_name,
                            span=len(visit_groups),
                            style="header1",
                            refs=[
                                Ref(
                                    type_=SoAItemType.STUDY_EPOCH.value,
                                    uid=visit.study_epoch_uid,
                                )
                            ],
                        )
                    )

                else:
                    # Add empty cells after Epoch cell with span > 1
                    epochs_row.cells.append(TableCell(span=0))

                # Milestones
                if milestones_row:
                    if visit.is_soa_milestone:
                        if prev_visit_type_uid == visit.visit_type_uid:
                            # Same visit_type, then merge with the previous cell in Milestone row
                            prev_milestone_cell.span += 1
                            milestones_row.cells.append(TableCell(span=0))

                        else:
                            # Different visit_type, new label in Milestones row
                            prev_visit_type_uid = visit.visit_type_uid
                            milestones_row.cells.append(
                                prev_milestone_cell := TableCell(
                                    visit.visit_type.sponsor_preferred_name,
                                    style="header1",
                                )
                            )

                    else:
                        # Just an empty cell for non-milestones
                        prev_visit_type_uid = None
                        milestones_row.cells.append(TableCell())

                visit_timing = ""

                # Visit group
                if len(group) > 1:
                    visit_name = visit.consecutive_visit_group

                    if not (
                        getattr(visit, visit_timing_prop) is None
                        or getattr(group[-1], visit_timing_prop) is None
                    ):
                        visit_timing = f"{getattr(visit, visit_timing_prop):d}-{getattr(group[-1], visit_timing_prop):d}"

                # Single Visit
                else:
                    visit_name = visit.visit_short_name

                    if getattr(visit, visit_timing_prop) is not None:
                        visit_timing = f"{getattr(visit, visit_timing_prop):d}"

                # Visit name cell
                visits_row.cells.append(
                    TableCell(
                        visit_name,
                        style="header2",
                        refs=[
                            Ref(type_=SoAItemType.STUDY_VISIT.value, uid=vis.uid)
                            for vis in group
                        ],
                    )
                )

                # Visit timing cell
                timing_row.cells.append(TableCell(visit_timing, style="header3"))

                # Visit window
                visit_window = cls._get_visit_window(visit)

                # Visit window cell
                window_row.cells.append(TableCell(visit_window, style="header4"))

        return rows

    @staticmethod
    def _get_visit_timing_property(
        time_unit: str, soa_preferences: StudySoaPreferencesInput
    ) -> str:
        if time_unit == "day":
            if soa_preferences.baseline_as_time_zero:
                return "study_duration_days"
            return "study_day_number"
        if soa_preferences.baseline_as_time_zero:
            return "study_duration_weeks"
        return "study_week_number"

    @staticmethod
    def _get_visit_name(visit: StudyVisit, num_visits_in_group: int = 0) -> str:
        if num_visits_in_group:
            return (
                visit.consecutive_visit_group
                if num_visits_in_group > 1
                else visit.visit_short_name
            )
        return visit.consecutive_visit_group or visit.visit_short_name

    @staticmethod
    def _get_visit_timing(visits: list[StudyVisit], visit_timing_property: str) -> str:
        visit = visits[0]

        # Visit group
        if len(visits) > 1:
            if not (
                getattr(visit, visit_timing_property) is None
                or getattr(visits[-1], visit_timing_property) is None
            ):
                return f"{getattr(visit, visit_timing_property):d}-{getattr(visits[-1], visit_timing_property):d}"

        # Single Visit
        else:
            if getattr(visit, visit_timing_property) is not None:
                return f"{getattr(visit, visit_timing_property):d}"

        return ""

    @staticmethod
    def _get_visit_window(visit: StudyVisit) -> str:
        if None not in (
            visit.min_visit_window_value,
            visit.max_visit_window_value,
        ):
            if visit.min_visit_window_value == visit.max_visit_window_value == 0:
                # visit window is zero
                return "0"
            if visit.min_visit_window_value * -1 == visit.max_visit_window_value:
                # plus-minus sign can be used
                return f"±{visit.max_visit_window_value:d}"
            # plus and minus windows are different
            if visit.min_visit_window_value == 0:
                min_visit_window = visit.min_visit_window_value
            else:
                min_visit_window = f"{visit.min_visit_window_value:+d}"
            if visit.max_visit_window_value == 0:
                max_visit_window = visit.max_visit_window_value
            else:
                max_visit_window = f"{visit.max_visit_window_value:+d}"
            visit_window = f"{min_visit_window}/{max_visit_window}"
            return visit_window
        return ""

    @classmethod
    def _get_activity_rows(
        cls,
        study_selection_activities: Sequence[
            StudySelectionActivity | StudySelectionActivityInstance
        ],
        study_activity_schedules: Sequence[StudyActivitySchedule],
        grouped_visits: dict[str, dict[str, list[StudyVisit]]],
        operational: bool = False,
        hide_soa_groups: bool = False,
    ) -> list[TableRow]:
        """Builds activity rows also adding various group header rows when required"""

        # Ordered StudyVisit.uids of visits to show (showing only the first visit of a consecutive_visit_group)
        visit_groups: list[list[StudyVisit]] = [
            visit_group
            for epochs_group in grouped_visits.values()
            for visit_group in epochs_group.values()
        ]

        num_cols = len(visit_groups) + 1
        if operational:
            num_cols += NUM_OPERATIONAL_CODE_ROWS

        # StudyActivitySchedules indexed by tuple of [uid, StudyVisit.uid]
        study_activity_schedules_mapping = {
            (
                sas.study_activity_instance_uid or sas.study_activity_uid,
                sas.study_visit_uid,
            ): sas
            for sas in study_activity_schedules
        }

        rows = []

        prev_soa_group_uid = False
        prev_activity_group_uid = False
        prev_activity_subgroup_uid = False
        prev_study_selection_id = False

        study_selection_activity: (
            StudySelectionActivity | StudySelectionActivityInstance
        )
        for study_selection_activity in study_selection_activities:
            soa_group_uid = study_selection_activity.study_soa_group.soa_group_term_uid

            if not hide_soa_groups or getattr(
                study_selection_activity,
                "show_soa_group_in_protocol_flowchart",
                True,
            ):
                # Add SoA Group row
                if soa_group_uid != prev_soa_group_uid:
                    prev_soa_group_uid = soa_group_uid
                    prev_activity_group_uid = False
                    prev_activity_subgroup_uid = False
                    prev_study_selection_id = False

                    soa_group_row = cls._get_soa_group_row(
                        study_selection_activity, num_cols
                    )
                    rows.append(soa_group_row)

            # Add Activity Group row
            activity_group_uid = (
                study_selection_activity.study_activity_group.activity_group_uid
            )

            if prev_activity_group_uid != activity_group_uid:
                prev_activity_group_uid = activity_group_uid
                prev_activity_subgroup_uid = False
                prev_study_selection_id = False

                activity_group_row = cls._get_activity_group_row(
                    study_selection_activity, num_cols
                )
                rows.append(activity_group_row)

            else:
                # Unhide ActivityGroup row if any of the StudyActivityGroup members requests to show it.
                if getattr(
                    study_selection_activity,
                    "show_activity_group_in_protocol_flowchart",
                    True,
                ):
                    activity_group_row.hide = False

            # Add Activity Sub-Group row
            activity_subgroup_uid = (
                study_selection_activity.study_activity_subgroup.activity_subgroup_uid
            )

            if prev_activity_subgroup_uid != activity_subgroup_uid:
                prev_activity_subgroup_uid = activity_subgroup_uid
                prev_study_selection_id = False

                activity_subgroup_row = cls._get_activity_subgroup_row(
                    study_selection_activity, num_cols
                )
                rows.append(activity_subgroup_row)

            else:
                # Unhide ActivitySubGroup row if any of the StudyActivitySubGroup members requests to show it.
                if getattr(
                    study_selection_activity,
                    "show_activity_subgroup_in_protocol_flowchart",
                    True,
                ):
                    activity_subgroup_row.hide = False

            # Add Activity row
            study_selection_id = study_selection_activity.study_activity_uid

            if prev_study_selection_id != study_selection_id:
                prev_study_selection_id = study_selection_id

                row = cls._get_activity_row(study_selection_activity, operational)

                rows.append(row)

                cls._append_activity_crosses(
                    row,
                    visit_groups,
                    study_activity_schedules_mapping,
                    study_selection_activity.study_activity_uid,
                )

            # Add Activity Instance row
            if getattr(study_selection_activity, "activity_instance", None):
                row = cls._get_activity_instance_row(study_selection_activity)

                rows.append(row)

                cls._append_activity_crosses(
                    row,
                    visit_groups,
                    study_activity_schedules_mapping,
                    study_selection_activity.study_activity_instance_uid,
                )

        return rows

    @classmethod
    def _get_activity_row(cls, study_selection_activity, operational) -> TableRow:
        """returns TableRow for Activity"""

        row = TableRow(
            hide=not getattr(
                study_selection_activity,
                "show_activity_in_protocol_flowchart",
                True,
            )
        )

        # Activity name cell (Activity row first column)
        row.cells.append(cls._get_study_activity_cell(study_selection_activity))

        if operational:
            for _ in range(NUM_OPERATIONAL_CODE_ROWS):
                row.cells.append(TableCell())

        return row

    @staticmethod
    def _get_study_activity_cell(
        study_selection_activity: StudySelectionActivity,
    ) -> TableCell:
        return TableCell(
            study_selection_activity.activity.name,
            style="activity",
            refs=[
                Ref(
                    type_=SoAItemType.STUDY_ACTIVITY.value,
                    uid=study_selection_activity.study_activity_uid,
                ),
                Ref(
                    type_="Activity",
                    uid=study_selection_activity.activity.uid,
                ),
            ],
        )

    @staticmethod
    def _append_activity_crosses(
        row: TableRow,
        visit_groups: Iterable[list[StudyVisit]],
        study_activity_schedules_mapping: Mapping[
            tuple[str, str], StudyActivitySchedule
        ],
        activity_id: str,
    ) -> None:
        """appends TableCells to TableRow with crosses based on Activity Schedules to StudyVisit mapping"""

        # Iterate over visit groups to look up scheduled Activities
        for visit_group in visit_groups:
            # Look up scheduled activities from (activity_id, visit_uid)->schedule mapping
            study_activity_schedules = (
                study_activity_schedules_mapping.get((activity_id, visit.uid))
                for visit in visit_group
            )
            # filter None values returned by mapping.get()
            study_activity_schedules = filter(None, study_activity_schedules)
            # get StudyActivitySchedule.uids
            study_activity_schedule_uids = map(
                lambda sas: sas.study_activity_schedule_uid, study_activity_schedules
            )
            # remove duplicates preserving order
            study_activity_schedule_uids: list[str] = list(
                dict.fromkeys(study_activity_schedule_uids)
            )

            # Append a cell with check-mark if Activities are scheduled
            if study_activity_schedule_uids:
                row.cells.append(
                    TableCell(
                        SOA_CHECK_MARK,
                        style="activitySchedule",
                        refs=[
                            Ref(
                                type_=SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
                                uid=uid,
                            )
                            for uid in study_activity_schedule_uids
                        ],
                    )
                )

            # Append an empty cell if no Activity is scheduled
            else:
                row.cells.append(TableCell())

    @staticmethod
    def _get_activity_instance_row(
        study_selection_activity: StudySelectionActivityInstance,
    ) -> TableRow:
        """returns TableRow for Activity Instance row"""

        row = TableRow(
            hide=not getattr(
                study_selection_activity,
                "show_activity_instance_in_protocol_flowchart",
                True,
            )
        )

        # Activity name cell (Activity row first column)
        row.cells.append(
            TableCell(
                study_selection_activity.activity_instance.name,
                style="activityInstance",
                refs=[
                    Ref(
                        type_=SoAItemType.STUDY_ACTIVITY_INSTANCE.value,
                        uid=study_selection_activity.study_activity_instance_uid,
                    )
                ],
            )
        )

        row.cells.append(
            TableCell(study_selection_activity.activity_instance.topic_code or "")
        )
        row.cells.append(
            TableCell(study_selection_activity.activity_instance.adam_param_code or "")
        )

        return row

    @classmethod
    def _get_soa_group_row(
        cls,
        study_selection_activity: StudySelectionActivity,
        num_cols: int,
    ) -> TableRow:
        """returns TableRow for SoA Group row"""

        row = TableRow(
            hide=not getattr(
                study_selection_activity, "show_soa_group_in_protocol_flowchart", True
            )
        )

        row.cells.append(
            cls._get_soa_group_cell(study_selection_activity.study_soa_group)
        )

        # fill the row with empty cells for visits #
        row.cells += [TableCell() for _ in range(num_cols - 1)]

        return row

    @staticmethod
    def _get_soa_group_cell(study_soa_group: StudySoAGroup) -> TableCell:
        return TableCell(
            study_soa_group.soa_group_term_name,
            style="soaGroup",
            refs=[
                Ref(
                    type_=SoAItemType.STUDY_SOA_GROUP.value,
                    uid=study_soa_group.study_soa_group_uid,
                ),
                Ref(
                    type_="CTTerm",
                    uid=study_soa_group.soa_group_term_uid,
                ),
            ],
        )

    @staticmethod
    def _get_activity_group_row(
        study_selection_activity: StudySelectionActivity,
        num_cols: int,
    ) -> TableRow:
        """returns TableRow for Activity Group row"""

        group_name = (
            study_selection_activity.study_activity_group.activity_group_name
            if study_selection_activity.study_activity_group.activity_group_uid
            else _T("no_study_group")
        )

        row = TableRow(
            hide=not getattr(
                study_selection_activity,
                "show_activity_group_in_protocol_flowchart",
                True,
            )
        )

        row.cells.append(
            TableCell(
                group_name,
                style="group",
                refs=(
                    [
                        Ref(
                            type_=SoAItemType.STUDY_ACTIVITY_GROUP.value,
                            uid=study_selection_activity.study_activity_group.study_activity_group_uid,
                        ),
                        Ref(
                            type_="ActivityGroup",
                            uid=study_selection_activity.study_activity_group.activity_group_uid,
                        ),
                    ]
                    if study_selection_activity.study_activity_group.study_activity_group_uid
                    else []
                ),
            )
        )

        # fill the row with empty cells for visits #
        row.cells += [TableCell() for _ in range(num_cols - 1)]

        return row

    @staticmethod
    def _get_activity_group_cell(study_activity_group: StudyActivityGroup) -> TableCell:
        name = (
            study_activity_group.activity_group_name
            if study_activity_group.activity_group_uid
            else _T("no_study_group")
        )

        return TableCell(
            name,
            style="group",
            refs=(
                [
                    Ref(
                        type_=SoAItemType.STUDY_ACTIVITY_GROUP.value,
                        uid=study_activity_group.study_activity_group_uid,
                    ),
                    Ref(
                        type_="ActivityGroup",
                        uid=study_activity_group.activity_group_uid,
                    ),
                ]
                if study_activity_group.study_activity_group_uid
                else []
            ),
        )

    @staticmethod
    def _get_activity_subgroup_row(
        study_selection_activity: StudySelectionActivity,
        num_cols: int,
    ) -> TableRow:
        """returns TableRow for Activity SubGroup row"""

        group_name = (
            study_selection_activity.study_activity_subgroup.activity_subgroup_name
            if study_selection_activity.study_activity_subgroup.activity_subgroup_uid
            else _T("no_study_subgroup")
        )

        row = TableRow(
            hide=not getattr(
                study_selection_activity,
                "show_activity_subgroup_in_protocol_flowchart",
                True,
            )
        )

        row.cells.append(
            TableCell(
                group_name,
                style="subGroup",
                refs=(
                    [
                        Ref(
                            type_=SoAItemType.STUDY_ACTIVITY_SUBGROUP.value,
                            uid=study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid,
                        ),
                        Ref(
                            type_="ActivitySubGroup",
                            uid=study_selection_activity.study_activity_subgroup.activity_subgroup_uid,
                        ),
                    ]
                    if study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
                    else []
                ),
            )
        )

        # fill the row with empty cells for visits #
        row.cells += [TableCell() for _ in range(num_cols - 1)]

        return row

    @staticmethod
    def _get_activity_subgroup_cell(
        study_activity_subgroup: StudyActivitySubGroup,
    ) -> TableCell:
        name = (
            study_activity_subgroup.activity_subgroup_name
            if study_activity_subgroup.activity_subgroup_uid
            else _T("no_study_subgroup")
        )

        return TableCell(
            name,
            style="subGroup",
            refs=(
                [
                    Ref(
                        type_=SoAItemType.STUDY_ACTIVITY_SUBGROUP.value,
                        uid=study_activity_subgroup.study_activity_subgroup_uid,
                    ),
                    Ref(
                        type_="ActivitySubGroup",
                        uid=study_activity_subgroup.activity_subgroup_uid,
                    ),
                ]
                if study_activity_subgroup.study_activity_subgroup_uid
                else []
            ),
        )

    @classmethod
    @trace_calls
    def add_footnotes(
        cls,
        table: TableWithFootnotes,
        footnotes: list[StudySoAFootnote],
    ):
        """Adds footnote symbols to table rows based on the referenced uids"""

        (
            footnote_symbols_by_ref_uid,
            simple_footnotes_by_symbol,
        ) = cls._mk_simple_footnotes(footnotes)
        for row in table.rows:
            for cell in row.cells:
                footnotes = set(cell.footnotes or [])
                for ref in cell.refs or []:
                    footnotes.update(footnote_symbols_by_ref_uid.get(ref.uid, []))
                cell.footnotes = sorted(list(footnotes)) if footnotes else None

        table.footnotes = simple_footnotes_by_symbol

    @staticmethod
    @trace_calls
    def show_hidden_rows(rows: Iterable[TableRow]):
        """Unhides all rows in-place"""

        row: TableRow
        for row in rows:
            # unhide all rows
            row.hide = False

    @staticmethod
    @trace_calls
    def remove_hidden_rows(table: TableWithFootnotes):
        """Removes hidden rows from table"""

        hidden_header_rows_count = sum(
            1 for row in table.rows[: table.num_header_rows] if row.hide
        )
        table.rows[:] = (row for row in table.rows if not row.hide)
        table.num_header_rows -= hidden_header_rows_count

    @staticmethod
    @trace_calls
    def propagate_hidden_rows(rows: Iterable[TableRow], propagate_refs: bool = False):
        """
        Modify table in place to for Protocol SoA

        For hidden activity rows, up-propagate the crosses and footnotes onto the next visible group level.
        """

        soa_group_term_row = None
        activity_group_row = None
        activity_subgroup_row = None

        row: TableRow
        for row in rows:
            if not (row.cells and row.cells[0].refs):
                continue

            if row.cells[0].refs[0].type == SoAItemType.STUDY_SOA_GROUP.value:
                soa_group_term_row = row
                activity_group_row = None
                activity_subgroup_row = None

            elif row.cells[0].refs[0].type == SoAItemType.STUDY_ACTIVITY_GROUP.value:
                activity_group_row = row
                activity_subgroup_row = None

            elif row.cells[0].refs[0].type == SoAItemType.STUDY_ACTIVITY_SUBGROUP.value:
                activity_subgroup_row = row

            elif (
                row.hide
                and row.cells[0].refs[0].type == SoAItemType.STUDY_ACTIVITY.value
            ):
                update_row = None

                if activity_subgroup_row and not activity_subgroup_row.hide:
                    update_row = activity_subgroup_row
                elif activity_group_row and not activity_group_row.hide:
                    update_row = activity_group_row
                elif soa_group_term_row and not soa_group_term_row.hide:
                    update_row = soa_group_term_row

                if update_row and len(update_row.cells) == len(row.cells):
                    cell: TableCell
                    for i, cell in enumerate(row.cells):
                        update_cell: TableCell = update_row.cells[i]

                        if i > 0:
                            update_cell.text = update_cell.text or cell.text
                            # update_cell.style = update_cell.style or cell.style

                            # propagate references
                            if propagate_refs and cell.refs:
                                if update_cell.refs:
                                    update_cell.refs += cell.refs
                                else:
                                    update_cell.refs = list(cell.refs)

    @staticmethod
    @trace_calls
    def add_protocol_section_column(table: TableWithFootnotes):
        """Add Protocol Section column to table, updates table in place"""

        table.rows[0].cells.insert(
            table.num_header_cols,
            TableCell(text=_T("protocol_section"), style="header1"),
        )

        row: TableRow
        for row in table.rows[1:]:
            row.cells.insert(table.num_header_cols, TableCell())

    @staticmethod
    @trace_calls
    def amend_procedure_label(table: TableWithFootnotes):
        """Amends SoA table overwriting the text in the first column first visible header row"""
        for row in table.rows[: min(table.num_header_rows, 2, len(table.rows))]:
            if not row.hide:
                row.cells[0].text = _T("procedure_label")
                break

    @staticmethod
    @trace_calls
    def add_coordinates(
        table: TableWithFootnotes, coordinates: Mapping[str, tuple[int, int]]
    ):
        """Append coordinates as if they were footnote references to each table cell"""
        for row in table.rows:
            for cell in row.cells:
                if cell.refs:
                    for ref in cell.refs:
                        if ref.uid in coordinates:
                            cell.footnotes = [
                                f"[{','.join(map(str, coordinates[ref.uid]))}]"
                            ]

    @staticmethod
    @trace_calls
    def add_uid_debug(table: TableWithFootnotes):
        """Append coordinates as if they were footnote references to each table cell"""
        for row in table.rows:
            for cell in row.cells:
                cell.footnotes = [ref.uid for ref in cell.refs or []]

    @trace_calls
    def get_preferred_time_unit(
        self, study_uid: str, study_value_version: str | None = None
    ) -> str:
        """Gets preferred time unit of study from the db"""
        return self._study_service.get_study_preferred_time_unit(
            study_uid,
            for_protocol_soa=True,
            study_value_version=study_value_version,
        ).time_unit_name

    def _get_soa_preferences(
        self, study_uid: str, study_value_version: str | None = None
    ) -> StudySoaPreferences:
        """Gets SoA preferences"""
        return self._study_service.get_study_soa_preferences(
            study_uid,
            study_value_version=study_value_version,
        )

    @trace_calls
    def download_detailed_soa_content(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        protocol_flowchart: bool = False,
    ) -> list[dict]:
        if not study_value_version:
            query = "MATCH (study_root:StudyRoot{uid:$study_uid})-[has_version:LATEST]-(study_value:StudyValue)"
        else:
            query = "MATCH (study_root:StudyRoot{uid:$study_uid})-[has_version:HAS_VERSION {version:$study_value_version}]-(study_value:StudyValue)"
        query += """
            MATCH (study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(study_value)
            MATCH (study_activity_schedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(study_value)
            MATCH (study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(study_value)
            MATCH (study_activity_schedule)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value)
        """
        query += (
            "WHERE study_activity.show_activity_in_protocol_flowchart=true"
            if protocol_flowchart
            else ""
        )
        query += """
        WITH has_version,study_value, study_activity_schedule, study_visit, study_epoch, study_activity,
            head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue) | activity_value]) as activity,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(:StudyActivitySubGroup)
                -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value]) as activity_subgroup,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(:StudyActivityGroup)
                -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue) | activity_group_value]) as activity_group,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(:StudySoAGroup)
                -[:HAS_FLOWCHART_GROUP]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue) 
                | term_name_value]) as term_name_value,
            head([(study_epoch)-[:HAS_EPOCH]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]-
                (epoch_term:CTTermNameValue) | epoch_term.name]) as epoch_name,
            head([(study_visit)-[:HAS_VISIT_TYPE]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]-
                (visity_type_term:CTTermNameValue) | 
                {
                    is_soa_milestone:study_visit.is_soa_milestone,
                    milestone_name:visity_type_term.name
                }]) as milestone
        ORDER BY study_activity.order, study_visit.visit_number
        RETURN
            CASE
                WHEN has_version.status IN ["RELEASED", "LOCKED"]
                THEN has_version.version
                ELSE "LATEST on "+apoc.temporal.format(datetime(), 'yyyy-MM-dd HH:mm:ss zzz')
            END as study_version,
            study_value.study_number AS study_number,
            study_visit.short_visit_label AS visit,
            epoch_name AS epoch,
            activity.name AS activity,
            activity_subgroup.name AS activity_subgroup,
            activity_group.name AS activity_group,
            term_name_value.name as soa_group,
            milestone as milestone,
            coalesce(activity.is_data_collected, False) AS is_data_collected
        """

        result_array, attribute_names = db.cypher_query(
            query,
            params={"study_uid": study_uid, "study_value_version": study_value_version},
        )
        soa_preferences = self._get_soa_preferences(
            study_uid, study_value_version=study_value_version
        )
        content_rows = []
        for soa_content in result_array:
            content_dict = {}
            for content_prop, attribute_name in zip(soa_content, attribute_names):
                if attribute_name == "epoch":
                    if soa_preferences.show_epochs:
                        content_dict[attribute_name] = content_prop
                elif attribute_name == "milestone":
                    if soa_preferences.show_milestones:
                        content_dict[attribute_name] = (
                            content_prop.get("milestone_name")
                            if content_prop.get("is_soa_milestone")
                            else None
                        )
                else:
                    content_dict[attribute_name] = content_prop
            content_rows.append(content_dict)
        return content_rows

    @staticmethod
    @trace_calls
    def download_operational_soa_content(
        study_uid: str,
        study_value_version: str | None = None,
    ) -> list[dict]:
        if not study_value_version:
            query = "MATCH (study_root:StudyRoot{uid:$study_uid})-[has_version:LATEST]-(study_value:StudyValue)"
        else:
            query = "MATCH (study_root:StudyRoot{uid:$study_uid})-[has_version:HAS_VERSION {version:$study_value_version}]-(study_value:StudyValue)"
        query += """
            MATCH (study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(study_value)
            MATCH (study_activity_schedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(study_value)
            MATCH (study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(study_value)
            MATCH (study_activity_schedule)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(study_activity:StudyActivity)
                -[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->(study_activity_instance:StudyActivityInstance)
                <-[:HAS_STUDY_ACTIVITY_INSTANCE]-(study_value)
            WITH has_version,study_value, study_activity_schedule, study_visit, study_epoch, study_activity_instance, study_activity,
                head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue) | activity_value]) as activity,
                head([(study_activity_instance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->(activity_instance_value:ActivityInstanceValue) | 
                    activity_instance_value]) as activity_instance,
                head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(:StudyActivitySubGroup)
                    -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value]) as activity_subgroup,
                head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(:StudyActivityGroup)
                    -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue) | activity_group_value]) as activity_group,
                head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(:StudySoAGroup)
                    -[:HAS_FLOWCHART_GROUP]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue) 
                    | term_name_value]) as term_name_value,
                head([(study_epoch)-[:HAS_EPOCH]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]-
                    (epoch_term:CTTermNameValue) | epoch_term.name]) as epoch_name
            ORDER BY study_activity.order, study_visit.visit_number
            RETURN
                CASE
                    WHEN has_version.status IN ["RELEASED", "LOCKED"]
                    THEN has_version.version
                    ELSE "LATEST on "+apoc.temporal.format(datetime(), 'yyyy-MM-dd HH:mm:ss zzz')
                END as study_version,
                study_value.study_number AS study_number,
                study_visit.short_visit_label AS visit,
                epoch_name AS epoch,
                activity.name AS activity,
                activity_instance.name AS activity_instance,
                activity_instance.topic_code AS topic_code,
                activity_instance.adam_param_code AS param_code,
                activity_subgroup.name AS activity_subgroup,
                activity_group.name AS activity_group,
                term_name_value.name as soa_group
        """

        result_array, attribute_names = db.cypher_query(
            query,
            params={"study_uid": study_uid, "study_value_version": study_value_version},
        )
        content_rows = []
        for soa_content in result_array:
            content_dict = {}
            for content_prop, attribute_name in zip(soa_content, attribute_names):
                content_dict[attribute_name] = content_prop
            content_rows.append(content_dict)
        return content_rows

    @trace_calls
    @ensure_transaction(db)
    def update_soa_snapshot(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        layout: SoALayout = SoALayout.PROTOCOL,
        study_status: StudyStatus | None = None,
    ) -> tuple[list[SoACellReference], list[SoAFootnoteReference]]:
        """Builds and saves SoA snapshot into the db"""

        cell_references, footnote_references = self.build_soa_snapshot(
            study_uid=study_uid, study_value_version=study_value_version, layout=layout
        )

        self.repository.save(
            study_uid=study_uid,
            study_value_version=study_value_version,
            cell_references=cell_references,
            footnote_references=footnote_references,
            layout=layout,
            study_status=study_status,
        )

        return cell_references, footnote_references

    @trace_calls
    @ensure_transaction(db)
    def load_soa_snapshot(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        layout: SoALayout = SoALayout.PROTOCOL,
        time_unit: str | None = None,
    ) -> TableWithFootnotes:
        """Loads SoA snapshot from db, and reconstructs SoA table and footnotes"""

        self._study_service.check_if_study_uid_and_version_exists(
            study_uid, study_value_version=study_value_version
        )

        soa_cell_references, soa_footnote_references = self.repository.load(
            study_uid=study_uid, study_value_version=study_value_version, layout=layout
        )

        NotFoundException.raise_if_not(
            soa_cell_references,
            msg=f"No SoA snapshot found for Study with uid '{study_uid}' and version '{study_value_version}'",
        )

        soa_preferences = self._get_soa_preferences(
            study_uid, study_value_version=study_value_version
        )

        if not time_unit:
            time_unit = self.get_preferred_time_unit(
                study_uid, study_value_version=study_value_version
            )

        self._validate_parameters(
            study_uid, study_value_version=study_value_version, time_unit=time_unit
        )

        study_epochs_by_uid = self._map_by_uid(
            self._get_study_epochs(
                study_uid=study_uid, study_value_version=study_value_version
            )
        )
        study_visits_by_uid = self._map_by_uid(
            self._get_study_visits(
                study_uid=study_uid, study_value_version=study_value_version
            )
        )
        study_soa_groups_by_uid = self._map_by_uid(
            self._get_study_soa_groups(
                study_uid=study_uid, study_value_version=study_value_version
            ),
            "study_soa_group_uid",
        )
        study_activity_groups_by_uid = self._map_by_uid(
            self._get_study_activity_groups(
                study_uid=study_uid, study_value_version=study_value_version
            ),
            "study_activity_group_uid",
        )
        study_activity_subgroups_by_uid = self._map_by_uid(
            self._get_study_activity_subgroups(
                study_uid=study_uid, study_value_version=study_value_version
            ),
            "study_activity_subgroup_uid",
        )
        study_activities_by_uid = self._map_by_uid(
            self._get_study_activities(
                study_uid=study_uid, study_value_version=study_value_version
            ),
            "study_activity_uid",
        )

        epoch_references: dict[int, SoACellReference] = {}
        visit_references: dict[int, list[SoACellReference]] = defaultdict(list)
        cell_references: dict[CellCoordinates, list[SoACellReference]] = defaultdict(
            list
        )
        num_rows, num_cols = 0, 0

        ref: SoACellReference
        for ref in soa_cell_references:
            num_rows = max(num_rows, ref.row + 1)
            num_cols = max(num_cols, ref.column + 1)

            if ref.referenced_item.item_type == SoAItemType.STUDY_EPOCH:
                epoch_references[ref.column] = ref

            elif ref.referenced_item.item_type == SoAItemType.STUDY_VISIT:
                visit_references[ref.column].append(ref)

            else:
                coords = CellCoordinates(row=ref.row, col=ref.column)
                cell_references[coords].append(ref)

        NotFoundException.raise_if_not(
            num_rows and num_cols,
            msg=f"Study with uid '{study_uid}' and version '{study_value_version}' has insufficient data in SoA snapshot",
        )

        table = TableWithFootnotes(
            rows=[
                TableRow(cells=[TableCell() for _ in range(num_cols)], hide=False)
                for _ in range(num_rows)
            ],
            num_header_cols=1,
            title=_T("protocol_flowchart"),
        )

        epoch_row = TableRow(
            cells=[TableCell(span=0) for _ in range(num_cols)],
            hide=not (layout == SoALayout.OPERATIONAL or soa_preferences.show_epochs),
        )
        epoch_row.cells[0] = TableCell(text=_T("study_epoch"), style="header1")

        for col_idx, ref in epoch_references.items():
            study_epoch = study_epochs_by_uid[ref.referenced_item.item_uid]
            epoch_row.cells[col_idx] = TableCell(
                text=study_epoch.epoch_name,
                span=ref.span,
                style="header1",
                refs=[
                    Ref(
                        type_=ref.referenced_item.item_type.value,
                        uid=study_epoch.uid,
                    )
                ],
                # add footnote symbols
                footnotes=[fr.symbol for fr in ref.footnote_references] or None,
            )
            for i in range(1, ref.span):
                epoch_row.cells[col_idx + i].span = 0

        milestone_row = TableRow(
            cells=[TableCell() for _ in range(num_cols)],
            hide=(
                layout == SoALayout.OPERATIONAL or not soa_preferences.show_milestones
            ),
        )
        milestone_row.cells[0] = TableCell(text=_T("study_milestone"), style="header1")

        visit_row = TableRow(cells=[TableCell() for _ in range(num_cols)], hide=False)
        visit_row.cells[0] = TableCell(text=_T("visit_short_name"), style="header2")

        timing_row = TableRow(cells=[TableCell() for _ in range(num_cols)], hide=False)
        if time_unit == "day":
            timing_row.cells[0] = TableCell(text=_T("study_day"), style="header3")
        else:
            timing_row.cells[0] = TableCell(text=_T("study_week"), style="header3")
        visit_timing_prop = self._get_visit_timing_property(time_unit, soa_preferences)

        window_row = TableRow(cells=[TableCell() for _ in range(num_cols)], hide=False)
        visit_window_unit = next(
            (
                study_visits_by_uid[ref.referenced_item.item_uid].visit_window_unit_name
                for refs in visit_references.values()
                for ref in refs
            ),
            "",
        )
        # Append window unit used by all StudyVisits
        window_row.cells[0] = TableCell(
            text=_T("visit_window").format(unit_name=visit_window_unit), style="header4"
        )

        prev_visit_type_uid = None
        prev_milestone_cell = None
        for col_idx, refs in visit_references.items():
            visits_in_group = [
                study_visits_by_uid[ref.referenced_item.item_uid] for ref in refs
            ]
            visit = visits_in_group[0]

            if visit.is_soa_milestone:
                if prev_visit_type_uid == visit.visit_type_uid:
                    # Same visit_type, then merge with the previous cell in Milestone row
                    prev_milestone_cell.span += 1
                    milestone_row.cells[col_idx].span = 0

                else:
                    # Different visit_type, new label in Milestones row
                    prev_visit_type_uid = visit.visit_type_uid
                    milestone_row.cells[col_idx] = prev_milestone_cell = TableCell(
                        visit.visit_type.sponsor_preferred_name,
                        style="header1",
                    )

            visit_row.cells[col_idx] = TableCell(
                self._get_visit_name(visit, num_visits_in_group=len(visits_in_group)),
                style="header2",
                refs=[
                    Ref(
                        type_=ref.referenced_item.item_type.value,
                        uid=ref.referenced_item.item_uid,
                    )
                    for ref in refs
                ],
                # add footnote symbols
                footnotes=[fr.symbol for fr in refs[0].footnote_references] or None,
            )

            timing_row.cells[col_idx] = TableCell(
                self._get_visit_timing(visits_in_group, visit_timing_prop),
                style="header3",
            )

            window_row.cells[col_idx] = TableCell(
                self._get_visit_window(visit), style="header4"
            )

        for coords, refs in cell_references.items():
            ref = refs[0]
            refi = ref.referenced_item

            row = table.rows[coords.row]
            if refi.item_type == SoAItemType.STUDY_SOA_GROUP:
                study_soa_group = study_soa_groups_by_uid[refi.item_uid]
                row.cells[coords.col] = cell = self._get_soa_group_cell(study_soa_group)

            elif refi.item_type == SoAItemType.STUDY_ACTIVITY_GROUP:
                study_activity_group = study_activity_groups_by_uid[refi.item_uid]
                row.cells[coords.col] = cell = self._get_activity_group_cell(
                    study_activity_group
                )

            elif refi.item_type == SoAItemType.STUDY_ACTIVITY_SUBGROUP:
                study_activity_subgroup = study_activity_subgroups_by_uid[refi.item_uid]
                row.cells[coords.col] = cell = self._get_activity_subgroup_cell(
                    study_activity_subgroup
                )

            elif refi.item_type == SoAItemType.STUDY_ACTIVITY:
                study_activity = study_activities_by_uid[refi.item_uid]
                row.cells[coords.col] = cell = self._get_study_activity_cell(
                    study_activity
                )

            elif refi.item_type == SoAItemType.STUDY_ACTIVITY_SCHEDULE:
                cell = row.cells[coords.col]
                cell.text = SOA_CHECK_MARK

                # add refs only for non-propagated rows to avoid footnote propagation
                if not ref.is_propagated:
                    cell.refs = [
                        Ref(
                            type_=ref.referenced_item.item_type.value,
                            uid=ref.referenced_item.item_uid,
                        )
                    ]

                    # add style only if checkmark is not propagated to match behaviour with propagate_hidden_rows()
                    cell.style = "activitySchedule"

            if not ref.is_propagated:
                # append remaining refs to cell to exactly match result of get_soa_flowchart()
                add_refs = [
                    Ref(
                        type_=ref.referenced_item.item_type.value,
                        uid=ref.referenced_item.item_uid,
                    )
                    for ref in refs[1:]
                ]
                if cell.refs:
                    cell.refs = [cell.refs[0]] + add_refs + cell.refs[1:]
                elif add_refs:
                    cell.refs = add_refs

                # add footnote symbols
                cell.footnotes = [fr.symbol for fr in ref.footnote_references] or None

        # merge header rows
        header_rows = [
            row
            for row in (epoch_row, milestone_row, visit_row, timing_row, window_row)
            if not row.hide
        ]
        table.num_header_rows = len(header_rows)
        table.rows = header_rows + table.rows

        study_soa_footnotes_by_uid: dict[str, StudySoAFootnote] = self._map_by_uid(
            self._get_study_footnotes(
                study_uid, study_value_version=study_value_version
            )
        )

        table.footnotes = {
            soa_footnote_reference.symbol: self._to_simple_footnote(
                study_soa_footnotes_by_uid[
                    soa_footnote_reference.referenced_item.item_uid
                ]
            )
            for soa_footnote_reference in soa_footnote_references
        }

        if layout == SoALayout.PROTOCOL:
            # amend procedure label on protocol SoA
            StudyFlowchartService.amend_procedure_label(table)

        return table

    @staticmethod
    def _map_by_uid(items: Iterable[BaseModel], uid_property_name: str = "uid"):
        return {getattr(item, uid_property_name): item for item in items}

    @trace_calls
    def build_soa_snapshot(
        self,
        study_uid: str,
        study_value_version: str | None,
        layout: SoALayout,
    ) -> tuple[list[SoACellReference], list[SoAFootnoteReference]]:
        """Returns SoA cell and footnote references from a freshly built SoA"""

        table = self.build_flowchart_table(
            study_uid=study_uid,
            study_value_version=study_value_version,
            operational=(layout == SoALayout.OPERATIONAL),
            hide_soa_groups=(layout == SoALayout.PROTOCOL),
        )

        if layout == SoALayout.PROTOCOL:
            # propagate checkmarks from hidden rows for protocol layout
            self.propagate_hidden_rows(table.rows, propagate_refs=True)

            # remove hidden rows
            self.remove_hidden_rows(table)

        soa_cell_references = self._extract_soa_cell_refs(table=table, layout=layout)

        soa_footnote_references = self._extract_soa_footnote_refs(table)

        return soa_cell_references, soa_footnote_references

    @staticmethod
    @trace_calls
    def _extract_soa_footnote_refs(
        table: TableWithFootnotes,
    ) -> list[SoAFootnoteReference]:
        footnote_references = [
            SoAFootnoteReference(
                order=i,
                symbol=symbol,
                referenced_item=ReferencedItem(
                    item_uid=fn.uid, item_type=SoAItemType.STUDY_SOA_FOOTNOTE
                ),
            )
            for i, (symbol, fn) in enumerate(table.footnotes.items())
        ]
        return footnote_references

    def _get_study_visits_dict_filtered(self, study_uid, study_value_version):
        # get visits
        visits = self._get_study_visits(
            study_uid, study_value_version=study_value_version
        )

        # filter for visible visits
        visits = {
            visit.uid: visit
            for visit in visits
            if (
                visit.show_visit
                and visit.study_epoch.sponsor_preferred_name != config.BASIC_EPOCH_NAME
            )
        }

        return visits

    @staticmethod
    def _get_visit_refs(header_rows: Iterable[TableRow]) -> dict[int, Ref]:
        """Extracts StudyVisit references from SoA table header rows, indexed by column index"""

        visit_refs: dict[int, Ref] = {}

        for i, cell in enumerate(header_rows[-3].cells):
            if cell.refs:
                for ref in cell.refs:
                    if ref.type == SoAItemType.STUDY_VISIT.value:
                        visit_refs[i] = ReferencedItem(
                            item_uid=ref.uid, item_type=SoAItemType(ref.type)
                        )
                        break

        return visit_refs

    @staticmethod
    @trace_calls
    def _extract_soa_cell_refs(
        table: TableWithFootnotes, layout: SoALayout
    ) -> list[SoACellReference]:
        """Extracts SoA cell references from SoA table

        Rows index given to StudyEpochs -2 and StudyVisits -1.
        Multiple StudyVisits are possible with the same row/column index due to visit grouping.
        Other SoAItemTypes are extracted from data rows given row index starting from 0.
        """

        references: list[SoACellReference] = []

        def collect_cell_references(
            row_idx: int,
            col_idx: int,
            cell: TableCell,
            accepted_ref_types: Iterable[str],
            is_propagated=False,
            order: int = 0,
        ):
            if not cell.refs:
                return
            for ref in dict.fromkeys(
                cell.refs
            ):  # iterate on unique refs preserving their order
                if ref.type in accepted_ref_types:
                    referenced_item = ReferencedItem(
                        item_uid=ref.uid, item_type=SoAItemType(ref.type)
                    )
                    references.append(
                        SoACellReference(
                            row=row_idx,
                            column=col_idx,
                            span=cell.span,
                            is_propagated=is_propagated,
                            order=order,
                            referenced_item=referenced_item,
                        )
                    )
                    order += 1

        num_header_cols = table.num_header_cols
        if layout == SoALayout.OPERATIONAL:
            num_header_cols += NUM_OPERATIONAL_CODE_ROWS

        # collect references from table header (Epochs and Visits)
        for row in table.rows[: table.num_header_rows]:
            for c, cell in enumerate(row.cells[num_header_cols:], start=1):
                collect_cell_references(-2, c, cell, {SoAItemType.STUDY_EPOCH.value})
                collect_cell_references(-1, c, cell, {SoAItemType.STUDY_VISIT.value})

                # collect_footnote_references(0, c, cell)

        # collect referenced items from table data
        for r, row in enumerate(table.rows[table.num_header_rows :]):
            # collect row references
            collect_cell_references(
                r,
                0,
                row.cells[0],
                {
                    SoAItemType.STUDY_SOA_GROUP.value,
                    SoAItemType.STUDY_ACTIVITY_GROUP.value,
                    SoAItemType.STUDY_ACTIVITY_SUBGROUP.value,
                    SoAItemType.STUDY_ACTIVITY.value,
                    (
                        layout == SoALayout.OPERATIONAL
                        and SoAItemType.STUDY_ACTIVITY_INSTANCE.value
                        # No Ref.type will match with False as Ref.type cannot be bool by model definition
                    ),
                },
            )

            # collect schedule references
            is_propagated = not (
                row.cells[0].refs
                and row.cells[0].refs[0].type
                in {
                    SoAItemType.STUDY_ACTIVITY.value,
                    SoAItemType.STUDY_ACTIVITY_INSTANCE.value,
                }
            )
            for c, cell in enumerate(row.cells[num_header_cols:], start=1):
                collect_cell_references(
                    r,
                    c,
                    cell,
                    {SoAItemType.STUDY_ACTIVITY_SCHEDULE.value},
                    is_propagated=is_propagated,
                )

        return references

    @staticmethod
    def choose_soa_layout(detailed: bool | None, operational: bool | None) -> SoALayout:
        """Chooses SoA layout based on detailed and operational boolean flags from router"""
        if operational:
            return SoALayout.OPERATIONAL
        if detailed:
            return SoALayout.DETAILED
        return SoALayout.PROTOCOL


def study_version(study: Study) -> str:
    """Returns study version as string"""
    if (
        study.current_metadata.version_metadata.study_status
        == StudyStatus.RELEASED.value
    ):
        return study.current_metadata.version_metadata.version_number
    return study.current_metadata.version_metadata.version_timestamp.strftime(
        "LATEST on %Y-%m-%d %H:%M:%S Z"
    )
