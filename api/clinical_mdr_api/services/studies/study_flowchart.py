import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor  # pylint: disable=no-name-in-module
from datetime import datetime
from typing import Any, Iterable, Mapping, Sequence, TypeVar

from docx.enum.style import WD_STYLE_TYPE
from neomodel import db
from opencensus.common.runtime_context import RuntimeContext
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
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpochTiny
from clinical_mdr_api.models.study_selections.study_selection import (
    CellCoordinates,
    ReferencedItem,
    SimpleStudySoAGroup,
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
from clinical_mdr_api.models.study_selections.study_visit import StudyVisitLite
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
    table_to_html,
    table_to_xlsx,
    tables_to_docx,
    tables_to_html,
)
from clinical_mdr_api.utils import enumerate_letters
from common.auth.user import user
from common.config import settings
from common.exceptions import (
    BusinessLogicException,
    NotFoundException,
    ValidationException,
)
from common.telemetry import trace_calls
from common.utils import VisitClass, insert_space_after_commas

NUM_OPERATIONAL_CODE_COLS = 2
SOA_CHECK_MARK = "X"
LAB_TABLE_INCLUDE_ACTIVITY_GROUP = "Laboratory Assessments"

# Strings prepared for localization
_T = {
    "study_epoch": "",
    "procedure_label": "Procedure",
    "lab_assessments": "Laboratory assessments",
    "parameters": "Parameters",
    "visits_list": "Visits and timing of visits",
    "study_milestone": "",
    "protocol_section": "Protocol Section",
    "visit_short_name": "Visit short name",
    "study_week": "Study week",
    "study_day": "Study day",
    "visit_window": "Visit window ({unit_name})",
    "protocol_flowchart": "Protocol Flowchart",
    "protocol_lab_table": "Protocol - Lab table",
    "operational_soa": "Operational SoA",
    "detailed_soa": "Detailed SoA",
    "no_study_group": "(not selected)",
    "no_study_subgroup": "(not selected)",
    "topic_code": "Topic Code",
    "adam_param_code": "ADaM Param Code",
    "soagroup": "soa-group",
    "group": "group",
    "subgroup": "subgroup",
    "activity": "activity",
    "footnotes_in_last_table_slice": "Footnotes are found under the last SoA table.",
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
    "subGroupLabTable": ("Table lvl 2", WD_STYLE_TYPE.PARAGRAPH),
    "activity": ("Table lvl 4", WD_STYLE_TYPE.PARAGRAPH),
    "activityRequest": ("Table lvl 4", WD_STYLE_TYPE.PARAGRAPH),
    "activityRequestFinal": ("Table lvl 4", WD_STYLE_TYPE.PARAGRAPH),
    "activityPlaceholder": ("Table lvl 4", WD_STYLE_TYPE.PARAGRAPH),
    "activityPlaceholderSubmitted": ("Table lvl 4", WD_STYLE_TYPE.PARAGRAPH),
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
    "activityRequest": ("Table cell", WD_STYLE_TYPE.PARAGRAPH),
    "activityRequestFinal": ("Table cell", WD_STYLE_TYPE.PARAGRAPH),
    "activityPlaceholder": ("Table cell", WD_STYLE_TYPE.PARAGRAPH),
    "activityPlaceholderSubmitted": ("Table cell", WD_STYLE_TYPE.PARAGRAPH),
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
    "library": "Heading 4",
    "instance": "Heading 4",
    "activityRequest": "Heading 4",
    "activityRequestFinal": "Heading 4",
    "activityPlaceholder": "Heading 4",
    "activityPlaceholderSubmitted": "Heading 4",
    "topicCode": "Heading 4",
    "adamCode": "Heading 4",
    None: "Normal",
    "activitySchedule": "Normal",
}

DETAILED_SOA_XLSX_STYLES = OPERATIONAL_XLSX_STYLES


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
    def _get_study_visits(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudyVisitLite]:
        return StudyVisitService.get_all_visits(
            study_uid, study_value_version=study_value_version, lite=True
        ).items

    @trace_calls
    def _get_study_footnotes(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudySoAFootnote]:
        return self._study_soa_footnote_service.get_all_by_study_uid(
            study_uid,
            sort_by={"order": True},
            study_value_version=study_value_version,
            minimal_response=True,
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

    @staticmethod
    @trace_calls(args=[0, 1], kwargs=["study_uid", "study_value_version"])
    def fetch_study_activities(
        study_uid: str, study_value_version: str | None = None
    ) -> list[StudySelectionActivity]:
        results, _ = StudySoARepository.query_study_activities(
            study_uid=study_uid,
            study_value_version=study_value_version,
            get_instances=False,
        )
        return [StudySelectionActivity(**result[0]) for result in results]

    @staticmethod
    @trace_calls(args=[0, 1], kwargs=["study_uid", "study_value_version"])
    def fetch_study_activity_instances(
        study_uid: str, study_value_version: str | None = None
    ) -> list[StudySelectionActivityInstance]:
        results, _ = StudySoARepository.query_study_activities(
            study_uid=study_uid,
            study_value_version=study_value_version,
            get_instances=True,
        )
        return [StudySelectionActivityInstance(**result[0]) for result in results]

    @staticmethod
    @trace_calls(args=[1], kwargs=["hide_soa_groups"])
    def _sort_study_activities(
        study_selection_activities: list[StudySelectionActivity],
        hide_soa_groups: bool = False,
    ):
        """Sort StudySelectionActivities in place, grouping by SoAGroup, ActivityGroup, ActivitySubgroup"""

        soa_groups: dict[Any, Any] = {}
        activity_groups: dict[Any, Any] = {}
        activity_subgroups: dict[Any, Any] = {}
        order_keys: dict[Any, Any] = {}

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
            key=lambda activity: order_keys[activity.study_activity_uid],
        )

    @staticmethod
    @trace_calls
    def _group_visits(
        visits: Iterable[StudyVisitLite],
        collapse_visit_groups: bool = True,
    ) -> list[tuple[str | None, dict[str, list[StudyVisitLite]]]]:
        """
        Builds an ordered list of (study_epoch_uid, visit_groups) tuples where each entry
        represents a consecutive run of visits under the same epoch.
        visit_groups maps: consecutive_visit_group | visit_uid -> [Visits]

        Uses runs instead of a dict so that epochs appearing non-consecutively
        (e.g. Treatment, no-epoch, Treatment) are represented as separate entries
        rather than being merged into a single bucket.
        """

        result: list[tuple[str | None, dict[str, list[StudyVisitLite]]]] = []
        current_epoch_uid: Any = object()  # sentinel distinct from None
        current_group: dict[str, list[StudyVisitLite]] = {}

        for visit in visits:
            epoch_uid = visit.study_epoch_uid
            if epoch_uid != current_epoch_uid:
                current_epoch_uid = epoch_uid
                current_group = {}
                result.append((epoch_uid, current_group))
            current_group.setdefault(
                collapse_visit_groups and visit.consecutive_visit_group or visit.uid, []
            ).append(visit)

        return result

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
            self.fetch_study_activities(
                study_uid, study_value_version=study_value_version
            )
        )
        if hide_soa_groups:
            self._sort_study_activities(
                study_selection_activities, hide_soa_groups=hide_soa_groups
            )

        visits: list[StudyVisitLite] = self._get_study_visits(
            study_uid, study_value_version=study_value_version
        )

        grouped_visits = self._group_visits(visits)

        coordinates: dict[str, CellCoordinates] = {}

        col = 1
        for study_epoch_uid, visit_groups in grouped_visits:
            coordinates[study_epoch_uid] = CellCoordinates(0, col)
            for group in visit_groups.values():
                for visit in group:
                    coordinates[visit.uid] = CellCoordinates(1, col)
                col += 1

        row = 4

        prev_activity_group_uid: str | None
        prev_activity_subgroup_uid: str | None

        prev_soa_group_uid, soa_group_row = "", 0
        prev_activity_group_uid, activity_group_row = "", 0
        prev_activity_subgroup_uid, activity_subgroup_row = "", 0

        study_selection_activity: StudySelectionActivity
        for study_selection_activity in study_selection_activities:
            soa_group_uid = study_selection_activity.study_soa_group.soa_group_term_uid

            if soa_group_uid != prev_soa_group_uid:
                prev_soa_group_uid, soa_group_row = soa_group_uid, row
                prev_activity_group_uid, activity_group_row = "", 0
                prev_activity_subgroup_uid, activity_subgroup_row = "", 0
                row += 1

            coordinates[
                study_selection_activity.study_soa_group.study_soa_group_uid
            ] = CellCoordinates(soa_group_row, 0)

            activity_group_uid = (
                study_selection_activity.study_activity_group.activity_group_uid
            )

            if prev_activity_group_uid != activity_group_uid:
                prev_activity_group_uid, activity_group_row = activity_group_uid, row
                prev_activity_subgroup_uid, activity_subgroup_row = "", 0
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

            coordinates[study_selection_activity.study_activity_uid] = CellCoordinates(  # type: ignore[index]
                row,
                0,
            )

            col = 0
            for _, visit_groups in grouped_visits:
                for group in visit_groups.values():
                    col += 1

                    for visit in group:
                        study_activity_schedule: StudyActivitySchedule | None = (
                            study_activity_schedules_mapping.get(
                                (
                                    (study_selection_activity.study_activity_uid or ""),
                                    visit.uid,
                                ),
                                None,
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
        study_value_version: str | None,
        layout: SoALayout,
        time_unit: str | None = None,
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
                study_value_version=study_value_version,
                layout=layout,
                time_unit=time_unit,
            )

            if layout == SoALayout.PROTOCOL:
                # propagate checkmarks from hidden rows for protocol layout
                self.propagate_hidden_rows(table.rows)

                # remove hidden rows
                self.remove_hidden_rows(table)

        return table

    @trace_calls
    def get_flowchart_table_lab_table(
        self,
        study_uid: str,
        study_value_version: str | None,
        time_unit: str | None = None,
    ) -> TableWithFootnotes:
        """
        Returns internal TableWithFootnotes representation of Protocol Lab table SoA.

        This table includes:
        - An additional first column displaying activity subgroup names
        - Only activities whose activity group name is "Laboratory Assessments"

        Args:
            study_uid (str): The unique identifier of the study.
            study_value_version (str | None): The version of the study to check. Defaults to None.
            time_unit (str | None): The preferred time unit, either "day" or "week". Defaults to None.

        Returns:
            TableWithFootnotes: Protocol Lab table SoA flowchart table with footnotes.
        """

        if not time_unit:
            time_unit = self.get_preferred_time_unit(
                study_uid, study_value_version=study_value_version
            )

        self._validate_parameters(
            study_uid, study_value_version=study_value_version, time_unit=time_unit
        )

        # Fetch database objects in parallel
        with ThreadPoolExecutor() as executor:
            soa_preferences_future = executor.submit(
                RuntimeContext.with_current_context(self._get_soa_preferences),
                study_uid,
                study_value_version=study_value_version,
            )

            activities_future = executor.submit(
                RuntimeContext.with_current_context(self.fetch_study_activities),
                study_uid,
                study_value_version=study_value_version,
            )

            activity_schedules_future = executor.submit(
                RuntimeContext.with_current_context(self._get_study_activity_schedules),
                study_uid,
                study_value_version=study_value_version,
                operational=False,
            )

            visits_future = executor.submit(
                RuntimeContext.with_current_context(
                    self._get_study_visits_dict_filtered
                ),
                study_uid,
                study_value_version,
                SoALayout.PROTOCOL_LAB_TABLE,
            )

            footnotes_future = executor.submit(
                RuntimeContext.with_current_context(self._get_study_footnotes),
                study_uid,
                study_value_version=study_value_version,
            )

        soa_preferences: StudySoaPreferences = soa_preferences_future.result()
        all_activities: list[StudySelectionActivity] = activities_future.result()
        activity_schedules: list[StudyActivitySchedule] = (
            activity_schedules_future.result()
        )
        visits: dict[str, StudyVisitLite] = visits_future.result()

        # Filter for Laboratory Assessments group
        selection_activities = [
            activity
            for activity in all_activities
            if (
                activity.study_activity_group.activity_group_name
                and activity.study_activity_group.activity_group_name.lower().strip()
                == LAB_TABLE_INCLUDE_ACTIVITY_GROUP.lower().strip()
            )
        ]

        # Sort the filtered activities
        self._sort_study_activities(selection_activities, hide_soa_groups=True)

        # Filter visits to only those with a lab activity schedule assigned (aka 'X')
        lab_activity_uids = {sa.study_activity_uid for sa in selection_activities}
        scheduled_visit_uids = {
            sas.study_visit_uid
            for sas in activity_schedules
            if sas.study_activity_uid in lab_activity_uids
        }
        visits = {uid: v for uid, v in visits.items() if uid in scheduled_visit_uids}

        # group visits in nested dict: study_epoch_uid -> [ consecutive_visit_group |  visit_uid ] -> [Visits]
        grouped_visits = self._group_visits(visits.values(), collapse_visit_groups=True)

        # Build header rows with extra column for subgroup names
        header_rows = self._get_header_rows_lab_table(
            grouped_visits, time_unit, soa_preferences
        )

        # Build activity rows with subgroup name column
        activity_rows = self._get_activity_rows_lab_table(
            selection_activities,
            activity_schedules,
            grouped_visits,
        )

        table = TableWithFootnotes(
            rows=header_rows + activity_rows,
            num_header_rows=len(header_rows),
            num_header_cols=2,  # Two header columns: subgroup name + activity name
            title=_T("protocol_lab_table"),
        )

        # Filter rows without checkmarks
        self._hide_rows_without_checkmarks(
            table.rows, len(header_rows), table.num_header_cols
        )

        # Group rows by activity subgroup name so same-subgroup rows are consecutive
        self._group_rows_by_subgroup(table.rows, len(header_rows))

        # Do not repeat the activity subgroup name on subsequent rows
        self._hide_repeated_subgroup_names(table.rows)

        # In case show_all_visits_lab_table is False, keep only the first two columns (subgroup name + activity name) and remove the rest of the visit columns
        if not soa_preferences.show_all_visits_lab_table:
            for row in table.rows:
                row.cells = row.cells[:2]

        footnotes: list[StudySoAFootnote] = footnotes_future.result()
        self.add_footnotes(table, footnotes)

        return table

    @staticmethod
    @trace_calls
    def split_flowchart_table(
        table: TableWithFootnotes, split_uids: Iterable[str]
    ) -> list[TableWithFootnotes]:
        """Splits flowchart table into multiple tables at columns referencing StudyVisit.uids in split_uids"""

        split_uids = set(split_uids)

        # Iterate through visit header row to find columns indexes to split at
        split_indices = set()
        visit_row_idx = max(0, table.num_header_rows - 3)
        for col_idx, cell in enumerate(
            table.rows[visit_row_idx].cells[table.num_header_cols :],
            start=table.num_header_cols,
        ):
            if cell.refs:
                for ref in cell.refs:
                    if ref.uid in split_uids:
                        split_indices.add(col_idx)

        table_slices: list[TableWithFootnotes] = [
            table.model_copy(update={"rows": [], "footnotes": None})
            for _ in range(len(split_indices) + 1)
        ]
        for row_idx, row in enumerate(table.rows):
            spanning_cell, remaining_span = None, 0

            # row prototype includes only header cells
            row_proto = row.model_copy(
                update={"cells": row.cells[: table.num_header_cols]}
            )

            # select the first slice and append new row based on prototype
            iter_slices = iter(table_slices)
            table_slice: TableWithFootnotes = next(iter_slices)
            table_slice.rows.append(
                slice_row := row_proto.model_copy(
                    update={"cells": row_proto.cells.copy()}
                )
            )

            for col_idx, cell in enumerate(
                row.cells[table.num_header_cols :], start=table.num_header_cols
            ):
                # split at indexes referencing split_uids
                if col_idx in split_indices:
                    # select next slice and create new row based on prototype
                    table_slice = next(iter_slices)
                    table_slice.rows.append(
                        slice_row := row_proto.model_copy(
                            update={"cells": row_proto.cells.copy()}
                        )
                    )

                    # continue with a spanning cell from the previous slice
                    if (
                        row_idx < table.num_header_rows
                        and cell.span == 0
                        and remaining_span > 0
                    ):
                        spanning_cell = cell = spanning_cell.model_copy(
                            update={"span": 0}
                        )

                # handle cell spanning across slices (header rows only)
                if row_idx < table.num_header_rows:
                    if cell.span > 1:
                        spanning_cell = cell = (
                            cell.model_copy()
                        )  # shallow copy to avoid modifying original table when updating `spanning_cell`
                        remaining_span = cell.span - 1
                        spanning_cell.span = 1

                    elif cell.span == 0 and remaining_span > 0:
                        spanning_cell.span += 1
                        remaining_span -= 1

                    else:
                        spanning_cell, remaining_span = None, 0

                # append cell to current slice row
                slice_row.cells.append(cell)

        # add a comment footnote to each slice that footnotes are in the last slice
        comment = str(_T("footnotes_in_last_table_slice"))
        for table_slice in table_slices[:-1]:
            table_slice.footnotes = {
                "": SimpleFootnote(uid="", text_html=comment, text_plain=comment)
            }

        # last slice inherits all footnotes
        table_slices[-1].footnotes = table.footnotes

        return table_slices

    @trace_calls
    def build_flowchart_table(
        self,
        study_uid: str,
        study_value_version: str | None,
        layout: SoALayout,
        time_unit: str | None = None,
    ) -> TableWithFootnotes:
        """
        Builds SoA flowchart table

        Args:
            study_uid (str): The unique identifier of the study.
            study_value_version (str | None): The version of the study to check. Defaults to None.
            layout (SoALayout): The layout of the SoA.
            time_unit (str): The preferred time unit, either "day" or "week".

        Returns:
            TableWithFootnotes: SoA flowchart table with footnotes.
        """

        if not time_unit:
            time_unit = self.get_preferred_time_unit(
                study_uid, study_value_version=study_value_version
            )

        self._validate_parameters(
            study_uid, study_value_version=study_value_version, time_unit=time_unit
        )

        # Fetch database objects in parallel
        with ThreadPoolExecutor() as executor:
            soa_preferences_future = executor.submit(
                RuntimeContext.with_current_context(self._get_soa_preferences),
                study_uid,
                study_value_version=study_value_version,
            )

            selection_activities_future = executor.submit(
                RuntimeContext.with_current_context(
                    self._get_study_selection_activities_sorted
                ),
                study_uid=study_uid,
                study_value_version=study_value_version,
                layout=layout,
            )

            activity_schedules_future = executor.submit(
                RuntimeContext.with_current_context(self._get_study_activity_schedules),
                study_uid,
                study_value_version=study_value_version,
                operational=(layout == SoALayout.OPERATIONAL),
            )

            visits_future = executor.submit(
                RuntimeContext.with_current_context(
                    self._get_study_visits_dict_filtered
                ),
                study_uid,
                study_value_version,
                layout,
            )

            if layout != SoALayout.OPERATIONAL:
                footnotes_future = executor.submit(
                    RuntimeContext.with_current_context(self._get_study_footnotes),
                    study_uid,
                    study_value_version=study_value_version,
                )

        soa_preferences: StudySoaPreferences = soa_preferences_future.result()

        selection_activities: list[
            StudySelectionActivity | StudySelectionActivityInstance
        ] = selection_activities_future.result()

        activity_schedules: list[StudyActivitySchedule] = (
            activity_schedules_future.result()
        )

        visits: dict[str, StudyVisitLite] = visits_future.result()

        # group visits in nested dict: study_epoch_uid -> [ consecutive_visit_group |  visit_uid ] -> [Visits]
        grouped_visits = self._group_visits(
            visits.values(), collapse_visit_groups=(layout != SoALayout.OPERATIONAL)
        )

        # first 4 rows of protocol SoA flowchart contains epochs & visits
        header_rows = self._get_header_rows(
            grouped_visits, time_unit, soa_preferences, layout
        )

        # activity rows with grouping headers and check-marks
        activity_rows = self._get_activity_rows(
            selection_activities,
            activity_schedules,
            grouped_visits,
            layout=layout,
        )

        table = TableWithFootnotes(
            rows=header_rows + activity_rows,
            num_header_rows=len(header_rows),
            num_header_cols=1,
            title=_T("protocol_flowchart"),
        )

        if layout != SoALayout.OPERATIONAL:
            footnotes: list[StudySoAFootnote] = footnotes_future.result()
            self.add_footnotes(table, footnotes, layout=layout)

        return table

    @trace_calls
    def _get_study_selection_activities_sorted(
        self,
        study_uid: str,
        study_value_version: str,
        layout: SoALayout,
    ) -> list[StudySelectionActivity | StudySelectionActivityInstance]:
        selection_activities: (
            list[StudySelectionActivityInstance] | list[StudySelectionActivity]
        )
        if layout == SoALayout.OPERATIONAL:
            selection_activities = self.fetch_study_activity_instances(
                study_uid, study_value_version=study_value_version
            )

        else:
            selection_activities = self.fetch_study_activities(
                study_uid, study_value_version=study_value_version
            )
        if layout == SoALayout.PROTOCOL:
            self._sort_study_activities(selection_activities, hide_soa_groups=True)

        return selection_activities

    @trace_calls
    def _get_study_visits_dict_filtered(
        self, study_uid, study_value_version, layout: SoALayout = SoALayout.PROTOCOL
    ) -> dict[str, StudyVisitLite]:
        # get visits
        visits = self._get_study_visits(
            study_uid, study_value_version=study_value_version
        )

        # filter for visible visits
        # For Detailed and Operational layouts, include unscheduled and non-visit visits regardless of show_visit and epoch.
        # For Protocol layout, exclude unscheduled and non-visit visits entirely.
        basic_epoch_visit_classes = (VisitClass.UNSCHEDULED_VISIT, VisitClass.NON_VISIT)
        include_basic_epoch_visits = layout in (
            SoALayout.DETAILED,
            SoALayout.OPERATIONAL,
        )
        visits = {
            visit.uid: visit
            for visit in visits
            if (
                (
                    include_basic_epoch_visits
                    and visit.visit_class in basic_epoch_visit_classes
                )
                or (
                    visit.show_visit
                    and (
                        not visit.study_epoch
                        or visit.study_epoch.sponsor_preferred_name
                        != settings.basic_epoch_name
                    )
                    and not (
                        layout in (SoALayout.PROTOCOL, SoALayout.PROTOCOL_LAB_TABLE)
                        and visit.visit_class in basic_epoch_visit_classes
                    )
                )
            )
        }

        return visits

    @trace_calls
    def get_study_flowchart_html(
        self,
        study_uid: str,
        study_value_version: str | None,
        layout: SoALayout,
        time_unit: str | None = None,
        debug_uids: bool = False,
        debug_coordinates: bool = False,
        debug_propagation: bool = False,
        include_uids: bool = False,
    ) -> str:
        if layout == SoALayout.PROTOCOL_LAB_TABLE:
            table = self.get_flowchart_table_lab_table(
                study_uid=study_uid,
                study_value_version=study_value_version,
                time_unit=time_unit,
            )
            return tables_to_html([table], include_uids=include_uids)

        # build internal representation of flowchart
        table = self.get_flowchart_table(
            study_uid=study_uid,
            time_unit=time_unit,
            study_value_version=study_value_version,
            layout=layout,
        )

        # layout alterations
        if layout != SoALayout.PROTOCOL:
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

        # splitting
        if layout == SoALayout.PROTOCOL:
            tables = self.split_soa(study_uid, study_value_version, table)
        else:
            tables = [table]

        # convert flowchart to HTML document
        return tables_to_html(tables, include_uids=include_uids)

    def split_soa(self, study_uid: str, study_value_version: str | None, table) -> Any:
        # Get StudyVisit.uids for slicing the SoA table
        split_uids = set(
            sp.uid
            for sp in self._study_service.get_study_soa_splits(
                study_uid=study_uid, study_value_version=study_value_version
            )
        )

        # Split SoA table into multiple tables at specified StudyVisit.uids
        tables = self.split_flowchart_table(table, split_uids)
        return tables

    @trace_calls
    def get_study_flowchart_docx(
        self,
        study_uid: str,
        study_value_version: str | None,
        layout: SoALayout,
        time_unit: str | None,
    ) -> DocxBuilder:
        """Returns a DOCX document with SoA table and footnotes"""

        if layout == SoALayout.PROTOCOL_LAB_TABLE:
            # Lab table uses its own table builder with different filtering and structure
            table = self.get_flowchart_table_lab_table(
                study_uid=study_uid,
                study_value_version=study_value_version,
                time_unit=time_unit,
            )
            return tables_to_docx([table], styles=DOCX_STYLES)

        # build internal representation of flowchart
        table = self.get_flowchart_table(
            study_uid=study_uid,
            layout=layout,
            study_value_version=study_value_version,
            time_unit=time_unit,
        )

        # layout alterations
        if layout != SoALayout.PROTOCOL:
            self.show_hidden_rows(table.rows)

        # Add Protocol Section column
        if layout == SoALayout.PROTOCOL:
            self.add_protocol_section_column(table)

        # splitting
        if layout == SoALayout.PROTOCOL:
            tables = self.split_soa(study_uid, study_value_version, table)
        else:
            tables = [table]

        # convert flowchart to DOCX document applying styles
        return tables_to_docx(
            tables,
            styles=(
                OPERATIONAL_DOCX_STYLES
                if layout == SoALayout.OPERATIONAL
                else DOCX_STYLES
            ),
            template=(
                settings.operational_soa_docx_template
                if layout == SoALayout.OPERATIONAL
                else None
            ),
        )

    @trace_calls
    def get_study_flowchart_xlsx(
        self,
        study_uid: str,
        study_value_version: str | None,
        layout: SoALayout,
        time_unit: str | None,
    ) -> Workbook:
        if layout == SoALayout.PROTOCOL_LAB_TABLE:
            table = self.get_flowchart_table_lab_table(
                study_uid=study_uid,
                study_value_version=study_value_version,
                time_unit=time_unit,
            )
            return table_to_xlsx(
                table, styles=OPERATIONAL_XLSX_STYLES, hide_rows_without_checkmarks=True
            )

        # build internal representation of flowchart
        table = self.get_flowchart_table(
            study_uid=study_uid,
            layout=layout,
            study_value_version=study_value_version,
            time_unit=time_unit,
        )

        # layout alterations
        if layout != SoALayout.PROTOCOL:
            self.show_hidden_rows(table.rows)

        return table_to_xlsx(table, styles=OPERATIONAL_XLSX_STYLES)

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
            study_value_version=study_value_version,
            layout=SoALayout.OPERATIONAL,
            time_unit=time_unit,
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
            study_value_version=study_value_version,
            layout=SoALayout.OPERATIONAL,
            time_unit=time_unit,
        )
        return table_to_html(
            table,
            css_style="table, th { border: 2px solid black; border-collapse: collapse; }\n"
            "td { border: 1px solid black; }",
        )

    @trace_calls
    def get_detailed_soa_xlsx(
        self,
        study_uid: str,
        study_value_version: str | None,
        time_unit: str | None,
    ) -> Workbook:
        # build internal representation of flowchart
        table = self.get_operational_spreadsheet(
            study_uid=study_uid,
            study_value_version=study_value_version,
            layout=SoALayout.DETAILED,
            time_unit=time_unit,
        )

        return table_to_xlsx(table, styles=DETAILED_SOA_XLSX_STYLES)

    @trace_calls
    def get_detailed_soa_html(
        self,
        study_uid: str,
        study_value_version: str | None,
        time_unit: str | None,
    ) -> str:
        table = self.get_operational_spreadsheet(
            study_uid=study_uid,
            study_value_version=study_value_version,
            layout=SoALayout.DETAILED,
            time_unit=time_unit,
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
        study_value_version: str | None = None,
        layout: SoALayout = SoALayout.OPERATIONAL,
        time_unit: str | None = None,
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
            layout=layout,
        )

        study_activity_schedules: list[StudyActivitySchedule] = (
            self._get_study_activity_schedules(
                study_uid,
                study_value_version=study_value_version,
                operational=layout == SoALayout.OPERATIONAL,
            )
        )

        visits = self._get_study_visits_dict_filtered(
            study_uid, study_value_version, layout
        )

        # group visits in nested dict: study_epoch_uid -> [ visit_uid ] -> [Visits]
        grouped_visits = self._group_visits(
            visits.values(), collapse_visit_groups=False
        )

        # StudyActivitySchedules indexed by tuple of [uid, StudyVisit.uid]
        study_activity_schedules_mapping = {
            (
                sas.study_activity_instance_uid or sas.study_activity_uid,
                sas.study_visit_uid,
            ): sas
            for sas in study_activity_schedules
        }

        # header rows
        if layout == SoALayout.OPERATIONAL:
            rows = [
                TableRow(
                    cells=[
                        TableCell(
                            f"study_version: {get_study_version(study)}",
                            span=3,
                            style="studyVersion",
                        )
                    ]
                    + [TableCell(span=0, style="studyVersion")] * 4
                ),
                TableRow(
                    cells=[
                        TableCell(
                            f"study_number: {study.current_metadata.identification_metadata.study_id}",
                            span=3,
                            style="studyNumber",
                        )
                    ]
                    + [TableCell(span=0, style="studyNumber")] * 4
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
                        TableCell(),
                        TableCell(),
                        TableCell(),
                        TableCell(),
                        TableCell("Epochs", style="header1"),
                    ]
                ),
                TableRow(
                    cells=[
                        TableCell("lowest visibility layer", style="header3"),
                        TableCell("Library", style="header3"),
                        TableCell("SoA group", style="header3"),
                        TableCell("Group", style="header3"),
                        TableCell("Subgroup", style="header3"),
                        TableCell("Activity", style="header3"),
                        TableCell("Instance", style="header3"),
                        TableCell("Topic Code", style="header3"),
                        TableCell("ADaM Param Code", style="header3"),
                        TableCell("Visits", style="header1"),
                    ]
                ),
            ]

        elif layout == SoALayout.DETAILED:
            rows = [
                TableRow(
                    cells=[
                        TableCell("SoA group", style="header3"),
                        TableCell("Group", style="header3"),
                        TableCell("Subgroup", style="header3"),
                        TableCell("Activity", style="header3"),
                        TableCell("Visibility", style="header3"),
                    ]
                ),
            ]

        else:
            raise NotImplementedError(f"SoA layout '{layout.value}' is not implemented")

        # add epoch and visit cells to header rows
        perv_study_epoch_uid = None
        for study_epoch_uid, _visit_groups in grouped_visits:
            for group in _visit_groups.values():
                visit: StudyVisitLite = group[0]

                if layout == SoALayout.OPERATIONAL:
                    # Epoch
                    if perv_study_epoch_uid != study_epoch_uid:
                        perv_study_epoch_uid = study_epoch_uid

                        rows[-2].cells.append(
                            TableCell(
                                text=(
                                    visit.study_epoch.sponsor_preferred_name
                                    if visit.study_epoch
                                    else ""
                                ),
                                span=len(_visit_groups),
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
        visit_groups: list[list[StudyVisitLite]] = [
            visit_group
            for _, epochs_group in grouped_visits
            for visit_group in epochs_group.values()
        ]

        for study_selection_activity in selection_activities:
            rows.append(row := TableRow())

            # Visibility
            if getattr(
                study_selection_activity, "show_activity_in_protocol_flowchart", True
            ):
                visibility = _T("activity")
            elif getattr(
                study_selection_activity,
                "show_activity_subgroup_in_protocol_flowchart",
                True,
            ):
                visibility = _T("subgroup")
            elif getattr(
                study_selection_activity,
                "show_activity_group_in_protocol_flowchart",
                True,
            ):
                visibility = _T("group")
            elif getattr(
                study_selection_activity, "show_soa_group_in_protocol_flowchart", True
            ):
                visibility = _T("soagroup")
            else:
                visibility = None

            if layout == SoALayout.OPERATIONAL:
                row.cells.append(TableCell(visibility, style="visibility"))

                # Library
                row.cells.append(
                    TableCell(
                        study_selection_activity.activity.library_name or "",
                        style="library",
                    )
                )

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

            if layout == SoALayout.OPERATIONAL:
                # Instance
                row.cells.append(
                    TableCell(
                        (
                            study_selection_activity.activity_instance.name
                            if study_selection_activity.activity_instance
                            else ""
                        ),
                        style="instance",
                    )
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

            # Visibility
            if layout == SoALayout.DETAILED:
                row.cells.append(TableCell(visibility, style="visibility"))

            # Scheduling crosses
            self._append_activity_crosses(
                row,
                visit_groups,
                study_activity_schedules_mapping,
                (
                    study_selection_activity.study_activity_instance_uid
                    if layout == SoALayout.OPERATIONAL
                    else study_selection_activity.study_activity_uid
                ),
            )

        table = TableWithFootnotes(
            rows=rows,
            num_header_rows=4 if layout == SoALayout.OPERATIONAL else 1,
            num_header_cols=4 if layout == SoALayout.OPERATIONAL else 5,
            title=_T(f"{layout.value}_soa"),
        )

        return table

    @classmethod
    @trace_calls(args=[2, 3, 4], kwargs=["time_unit", "soa_preferences", "layout"])
    def _get_header_rows(
        cls,
        grouped_visits: list[tuple[str | None, dict[str, list[StudyVisitLite]]]],
        time_unit: str,
        soa_preferences: StudySoaPreferencesInput,
        layout: SoALayout,
    ) -> list[TableRow]:
        """Builds the 4 header rows of protocol SoA flowchart"""

        visit_timing_prop = cls._get_visit_timing_property(time_unit, soa_preferences)

        rows = []

        # Header line 1: Epoch names
        rows.append(epochs_row := TableRow())
        epochs_row.cells.append(TableCell(text=_T("study_epoch"), style="header1"))
        epochs_row.hide = not (
            layout == SoALayout.OPERATIONAL or soa_preferences.show_epochs
        )

        # Header line 2 (optional): Milestones
        milestones_row = None
        if layout != SoALayout.OPERATIONAL and soa_preferences.show_milestones:
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
                for _, visit_groups in grouped_visits
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
        if layout == SoALayout.OPERATIONAL:
            epochs_row.cells.append(TableCell(text=_T("topic_code"), style="header2"))
            epochs_row.cells.append(
                TableCell(text=_T("adam_param_code"), style="header2")
            )
            for row in rows[1:]:
                for _j in range(NUM_OPERATIONAL_CODE_COLS):
                    row.cells.append(TableCell())

        prev_visit_type_uid = None
        prev_milestone_cell: TableCell | None = None
        for _, visit_groups in grouped_visits:
            first_in_run = True
            for group in visit_groups.values():
                visit: StudyVisitLite = group[0]

                # Open new Epoch column at the start of each consecutive run
                if first_in_run:
                    first_in_run = False
                    epochs_row.cells.append(
                        TableCell(
                            text=(
                                visit.study_epoch.sponsor_preferred_name
                                if visit.study_epoch
                                else ""
                            ),
                            span=len(visit_groups),
                            style="header1",
                            refs=(
                                [
                                    Ref(
                                        type_=SoAItemType.STUDY_EPOCH.value,
                                        uid=visit.study_epoch_uid,
                                    )
                                ]
                                if visit.study_epoch_uid
                                else []
                            ),
                        )
                    )

                else:
                    # Add empty cells after Epoch cell with span > 1
                    epochs_row.cells.append(TableCell(span=0))

                # Milestones
                if milestones_row:
                    if visit.is_soa_milestone:
                        if prev_visit_type_uid == visit.visit_type.term_uid:
                            # Same visit_type, then merge with the previous cell in Milestone row
                            prev_milestone_cell.span += 1
                            milestones_row.cells.append(TableCell(span=0))

                        else:
                            # Different visit_type, new label in Milestones row
                            prev_visit_type_uid = visit.visit_type.term_uid
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

                visit_name = cls._get_visit_name(group)
                visit_timing = cls._get_visit_timing(group, visit_timing_prop)

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

        if layout == SoALayout.PROTOCOL:
            # amend procedure label on protocol SoA
            StudyFlowchartService.amend_procedure_label(rows)

        return rows

    @classmethod
    @trace_calls
    def _get_header_rows_lab_table(
        cls,
        grouped_visits: list[tuple[str | None, dict[str, list[StudyVisitLite]]]],
        time_unit: str,
        soa_preferences: StudySoaPreferencesInput,
    ) -> list[TableRow]:
        """Builds the header rows for Protocol Lab table SoA flowchart with subgroup name column"""

        visit_timing_prop = cls._get_visit_timing_property(time_unit, soa_preferences)

        rows = []

        # Calculate total number of visit columns
        total_visit_columns = sum(
            len(visit_groups) for _, visit_groups in grouped_visits
        )

        # Header line 1
        rows.append(header_row_1 := TableRow())
        header_row_1.cells.append(
            TableCell(text=_T("lab_assessments"), style="header1")
        )
        header_row_1.cells.append(TableCell(text=_T("parameters"), style="header1"))

        if soa_preferences.show_all_visits_lab_table:
            header_row_1.cells.append(
                TableCell(_T("visits_list"), span=total_visit_columns, style="header1")
            )

            # Header line 2: Visit names
            rows.append(visits_row := TableRow())
            visits_row.cells.append(
                TableCell(text=_T("visit_short_name"), style="header2")
            )
            visits_row.cells.append(TableCell())  # Empty cell for activity column

            # Header line 3: Visit timing
            rows.append(timing_row := TableRow())
            if time_unit == "day":
                timing_row.cells.append(
                    TableCell(text=_T("study_day"), style="header3")
                )
            else:
                timing_row.cells.append(
                    TableCell(text=_T("study_week"), style="header3")
                )
            timing_row.cells.append(TableCell())  # Empty cell for activity column

            # Header line 4: Visit window
            rows.append(window_row := TableRow())
            visit_window_unit = next(
                (
                    group[0].visit_window_unit_name
                    for _, visit_groups in grouped_visits
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
            window_row.cells.append(TableCell())  # Empty cell for activity column

            for _, visit_groups in grouped_visits:
                for group in visit_groups.values():
                    visit: StudyVisitLite = group[0]

                    # Add empty cells with span=0 for the "List of visits" spanning cell
                    header_row_1.cells.append(TableCell(span=0))

                    visit_name = cls._get_visit_name(group)
                    visit_timing = cls._get_visit_timing(group, visit_timing_prop)

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
        time_unit: str | None, soa_preferences: StudySoaPreferencesInput
    ) -> str:
        if time_unit == "day":
            if soa_preferences.baseline_as_time_zero:
                return "study_duration_days"
            return "study_day_number"
        if soa_preferences.baseline_as_time_zero:
            return "study_duration_weeks"
        return "study_week_number"

    @staticmethod
    def _get_visit_name(visits_in_group: Sequence[StudyVisitLite]) -> str:
        visit: StudyVisitLite = visits_in_group[0]
        visit_name = visit.consecutive_visit_group or visit.visit_short_name

        if len(visits_in_group) > 1 and "," in visit_name:
            # insert line-breaks after certain commas when the cell text gets too long
            visit_name = insert_space_after_commas(
                visit_name, settings.soa_insert_space_after_commas_length, space="\n"
            )

        # Replace ASCII hyphen-minus with non-breaking hyphen (U+2011) in the
        # negative-day subvisit suffix (e.g. "V2D-1") to prevent word-wrap at
        # the sign character in table header cells.
        visit_name = visit_name.replace("D-", "D‑")

        return visit_name

    @staticmethod
    def _get_visit_timing(
        visits: list[StudyVisitLite], visit_timing_property: str
    ) -> str:
        visit: StudyVisitLite = visits[0]
        num_visits_in_group = len(visits)

        # Single Visit
        if num_visits_in_group == 1:
            if (
                visit.visit_class != VisitClass.SPECIAL_VISIT
                and getattr(visit, visit_timing_property) is not None
            ):
                return f"{getattr(visit, visit_timing_property):d}"

        # Visit Group
        if not (
            getattr(visit, visit_timing_property) is None
            or getattr(visits[-1], visit_timing_property) is None
        ):
            visit_name = (
                num_visits_in_group > 1
                and visit.consecutive_visit_group
                or visit.visit_short_name
            )

            # If there is a comma it means that group was made in the LIST grouping way
            if visit_name and "," in visit_name:
                visit_timings = [
                    f"{getattr(visit, visit_timing_property):d}"
                    for visit in visits
                    if visit.visit_class != VisitClass.SPECIAL_VISIT
                    and getattr(visit, visit_timing_property) is not None
                ]
                visit_timing = ",".join(visit_timings)
                # insert line-breaks after certain commas when the cell text gets too long
                visit_timing = insert_space_after_commas(
                    visit_timing,
                    settings.soa_insert_space_after_commas_length,
                    space="\n",
                )
                return visit_timing

            return f"{getattr(visit, visit_timing_property):d}-{getattr(visits[-1], visit_timing_property):d}"

        return ""

    @staticmethod
    def _get_visit_window(visit: StudyVisitLite) -> str:
        if None not in (
            visit.min_visit_window_value,
            visit.max_visit_window_value,
        ):
            if visit.visit_class in (
                VisitClass.SPECIAL_VISIT,
                VisitClass.UNSCHEDULED_VISIT,
                VisitClass.NON_VISIT,
            ):
                return ""
            if visit.min_visit_window_value == visit.max_visit_window_value == 0:
                # visit window is zero
                return "0"
            if (
                visit.min_visit_window_value is not None
                and visit.min_visit_window_value * -1 == visit.max_visit_window_value
            ):
                # plus-minus sign can be used
                return f"±{visit.max_visit_window_value:d}"
            # plus and minus windows are different
            if visit.min_visit_window_value == 0:
                min_visit_window = f"{visit.min_visit_window_value}"
            else:
                min_visit_window = f"{visit.min_visit_window_value:+d}"
            if visit.max_visit_window_value == 0:
                max_visit_window = f"{visit.max_visit_window_value}"
            else:
                max_visit_window = f"{visit.max_visit_window_value:+d}"
            visit_window = f"{min_visit_window}/{max_visit_window}"
            return visit_window
        return ""

    @classmethod
    @trace_calls
    def _get_activity_rows(
        cls,
        study_selection_activities: Sequence[
            StudySelectionActivity | StudySelectionActivityInstance
        ],
        study_activity_schedules: Sequence[StudyActivitySchedule],
        grouped_visits: list[tuple[str | None, dict[str, list[StudyVisitLite]]]],
        layout: SoALayout,
    ) -> list[TableRow]:
        """Builds activity rows also adding various group header rows when required"""

        # Ordered StudyVisit.uids of visits to show (showing only the first visit of a consecutive_visit_group)
        visit_groups: list[list[StudyVisitLite]] = [
            visit_group
            for _, epochs_group in grouped_visits
            for visit_group in epochs_group.values()
        ]

        num_cols = len(visit_groups) + 1
        if layout == SoALayout.OPERATIONAL:
            num_cols += NUM_OPERATIONAL_CODE_COLS

        # StudyActivitySchedules indexed by tuple of [uid, StudyVisit.uid]
        study_activity_schedules_mapping = {
            (
                sas.study_activity_instance_uid or sas.study_activity_uid,
                sas.study_visit_uid,
            ): sas
            for sas in study_activity_schedules
        }

        rows = []

        prev_soa_group_uid = None
        prev_activity_group_keys: set[tuple[str | None, str | None] | str] = set()
        prev_activity_subgroup_keys: set[tuple[str | None, str | None] | str] = set()
        prev_study_selection_id = None

        study_selection_activity: (
            StudySelectionActivity | StudySelectionActivityInstance
        )
        for study_selection_activity in study_selection_activities:
            soa_group_uid = study_selection_activity.study_soa_group.soa_group_term_uid

            if layout != SoALayout.PROTOCOL or getattr(
                study_selection_activity,
                "show_soa_group_in_protocol_flowchart",
                True,
            ):
                # Add SoA Group row
                if soa_group_uid != prev_soa_group_uid:
                    prev_soa_group_uid = soa_group_uid
                    prev_activity_group_keys = set()
                    prev_activity_subgroup_keys = set()
                    prev_study_selection_id = None

                    soa_group_row = cls._get_soa_group_row(
                        study_selection_activity, num_cols
                    )
                    rows.append(soa_group_row)

            # Add Activity Group row
            activity_group_key = (
                study_selection_activity.study_activity_group.activity_group_uid,
                study_selection_activity.study_activity_group.activity_group_name,
            )
            if activity_group_key not in prev_activity_group_keys:
                if (
                    study_selection_activity.study_activity_group.activity_group_uid
                    is not None
                ):
                    prev_activity_group_keys.add(activity_group_key)
                if (
                    study_selection_activity.study_activity_group.study_activity_group_uid
                    is not None
                ):
                    prev_activity_group_keys.add(
                        study_selection_activity.study_activity_group.study_activity_group_uid
                    )
                prev_activity_subgroup_keys = set()
                prev_study_selection_id = None

                activity_group_row = cls._get_activity_group_row(
                    study_selection_activity, num_cols
                )
                rows.append(activity_group_row)

            else:
                if (
                    # ActivityRequests may have no study_activity_group_uid
                    study_activity_group_uid := study_selection_activity.study_activity_group.study_activity_group_uid
                ) and study_activity_group_uid not in prev_activity_group_keys:
                    # Reference uids of merged StudyActivityGroups
                    prev_activity_group_keys.add(
                        study_activity_group_uid,
                    )
                    activity_group_row.cells[0].refs.insert(
                        -1,
                        Ref(
                            type_=SoAItemType.STUDY_ACTIVITY_GROUP.value,
                            uid=study_selection_activity.study_activity_group.study_activity_group_uid,
                        ),
                    )

                # Unhide ActivityGroup row if any of the StudyActivityGroup members requests to show it.
                if getattr(
                    study_selection_activity,
                    "show_activity_group_in_protocol_flowchart",
                    True,
                ):
                    activity_group_row.hide = False

            # Add Activity Sub-Group row
            activity_subgroup_key = (
                study_selection_activity.study_activity_subgroup.activity_subgroup_uid,
                study_selection_activity.study_activity_subgroup.activity_subgroup_name,
            )
            if activity_subgroup_key not in prev_activity_subgroup_keys:
                if (
                    study_selection_activity.study_activity_subgroup.activity_subgroup_uid
                    is not None
                ):
                    prev_activity_subgroup_keys.add(activity_subgroup_key)
                if (
                    study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
                    is not None
                ):
                    prev_activity_subgroup_keys.add(
                        study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
                    )
                prev_study_selection_id = None

                activity_subgroup_row = cls._get_activity_subgroup_row(
                    study_selection_activity, num_cols
                )
                rows.append(activity_subgroup_row)

            else:
                if (
                    # ActivityRequests may have no study_activity_subgroup_uid
                    study_activity_subgroup_uid := study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
                ) and study_activity_subgroup_uid not in prev_activity_subgroup_keys:
                    # Reference uids of merged StudyActivitySubGroups
                    activity_subgroup_row.cells[0].refs.insert(
                        -1,
                        Ref(
                            type_=SoAItemType.STUDY_ACTIVITY_SUBGROUP.value,
                            uid=study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid,
                        ),
                    )

                # Unhide ActivitySubGroup row if any of the StudyActivitySubGroup members requests to show it.
                if getattr(
                    study_selection_activity,
                    "show_activity_subgroup_in_protocol_flowchart",
                    True,
                ):
                    activity_subgroup_row.hide = False

            # Add Activity row
            study_selection_id = study_selection_activity.study_activity_uid

            if (
                prev_study_selection_id != study_selection_id
                and study_selection_activity.study_activity_uid
            ):
                prev_study_selection_id = study_selection_id

                row = cls._get_activity_row(study_selection_activity, layout=layout)

                rows.append(row)

                cls._append_activity_crosses(
                    row,
                    visit_groups,
                    study_activity_schedules_mapping,
                    study_selection_activity.study_activity_uid,
                )

            # Add Activity Instance row
            if (
                getattr(study_selection_activity, "activity_instance", None)
                and study_selection_activity.study_activity_instance_uid
            ):
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
    @trace_calls
    def _get_activity_rows_lab_table(
        cls,
        study_selection_activities: Sequence[StudySelectionActivity],
        study_activity_schedules: Sequence[StudyActivitySchedule],
        grouped_visits: list[tuple[str | None, dict[str, list[StudyVisitLite]]]],
    ) -> list[TableRow]:
        """Builds activity rows for Protocol Lab table with subgroup name column"""

        # Ordered StudyVisit.uids of visits to show
        visit_groups: list[list[StudyVisitLite]] = [
            visit_group
            for _, epochs_group in grouped_visits
            for visit_group in epochs_group.values()
        ]

        # StudyActivitySchedules indexed by tuple of [uid, StudyVisit.uid]
        study_activity_schedules_mapping = {
            (sas.study_activity_uid, sas.study_visit_uid): sas
            for sas in study_activity_schedules
        }

        rows = []
        prev_study_selection_id = None

        for study_selection_activity in study_selection_activities:
            study_selection_id = study_selection_activity.study_activity_uid

            if (
                prev_study_selection_id != study_selection_id
                and study_selection_activity.study_activity_uid
            ):
                prev_study_selection_id = study_selection_id

                # Create row with subgroup name as first cell
                row = TableRow(
                    order=study_selection_activity.order,
                    level=4,
                )

                # Determine if we should show the subgroup name
                current_subgroup_name = (
                    study_selection_activity.study_activity_subgroup.activity_subgroup_name
                )

                # Add subgroup name cell
                row.cells.append(
                    TableCell(
                        text=current_subgroup_name,
                        style="subGroupLabTable",
                        refs=(
                            [
                                Ref(
                                    type_=SoAItemType.STUDY_ACTIVITY_SUBGROUP.value,
                                    uid=study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid,
                                )
                            ]
                            if study_selection_activity.study_activity_subgroup.study_activity_subgroup_uid
                            else []
                        ),
                    )
                )

                # Add activity name cell
                row.cells.append(cls._get_study_activity_cell(study_selection_activity))

                # Add crosses for visits
                cls._append_activity_crosses(
                    row,
                    visit_groups,
                    study_activity_schedules_mapping,
                    study_selection_activity.study_activity_uid,
                )

                rows.append(row)

        return rows

    @classmethod
    def _get_activity_row(
        cls,
        study_selection_activity: (
            StudySelectionActivity | StudySelectionActivityInstance
        ),
        layout: SoALayout,
    ) -> TableRow:
        """returns TableRow for Activity"""

        row = TableRow(
            order=study_selection_activity.order,
            level=4,
            hide=not getattr(
                study_selection_activity,
                "show_activity_in_protocol_flowchart",
                True,
            ),
        )

        # Activity name cell (Activity row first column)
        row.cells.append(cls._get_study_activity_cell(study_selection_activity))

        if layout == SoALayout.OPERATIONAL:
            for _ in range(NUM_OPERATIONAL_CODE_COLS):
                row.cells.append(TableCell())

        return row

    @staticmethod
    def _get_study_activity_cell(
        study_selection_activity: (
            StudySelectionActivity | StudySelectionActivityInstance
        ),
    ) -> TableCell:
        is_placeholder = (
            study_selection_activity.activity.library_name
            == settings.requested_library_name
        )
        if is_placeholder:
            is_submitted = getattr(
                study_selection_activity.activity, "is_request_final", False
            )
            style = (
                "activityPlaceholderSubmitted"
                if is_submitted
                else "activityPlaceholder"
            )
        else:
            style = "activity"
        return TableCell(
            study_selection_activity.activity.name,
            style=style,
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
        visit_groups: Iterable[list[StudyVisitLite]],
        study_activity_schedules_mapping: Mapping[
            tuple[str, str], StudyActivitySchedule
        ],
        activity_id: str,
    ) -> None:
        """appends TableCells to TableRow with crosses based on Activity Schedules to StudyVisit mapping"""

        # Iterate over visit groups to look up scheduled Activities
        for visit_group in visit_groups:
            # Look up scheduled activities from (activity_id, visit_uid)->schedule mapping
            study_activity_schedules = [
                study_activity_schedules_mapping.get((activity_id, visit.uid))
                for visit in visit_group
            ]
            # filter None values returned by mapping.get()
            study_activity_schedules = list(filter(None, study_activity_schedules))
            # get StudyActivitySchedule.uids
            study_activity_schedule_uids: list[str] = [
                sas.study_activity_schedule_uid for sas in study_activity_schedules
            ]
            # remove duplicates preserving order
            study_activity_schedule_uids = list(
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
        study_selection_activity: (
            StudySelectionActivityInstance | StudySelectionActivity
        ),
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
        study_selection_activity: (
            StudySelectionActivity | StudySelectionActivityInstance
        ),
        num_cols: int,
    ) -> TableRow:
        """returns TableRow for SoA Group row"""

        row = TableRow(
            order=study_selection_activity.study_soa_group.order,
            level=1,
            hide=not getattr(
                study_selection_activity, "show_soa_group_in_protocol_flowchart", True
            ),
        )

        if study_selection_activity.study_soa_group is None:
            raise BusinessLogicException(msg="Study SoA Group is None")

        row.cells.append(
            cls._get_soa_group_cell(study_selection_activity.study_soa_group)
        )

        # fill the row with empty cells for visits #
        row.cells += [TableCell() for _ in range(num_cols - 1)]

        return row

    @staticmethod
    def _get_soa_group_cell(
        study_soa_group: StudySoAGroup | SimpleStudySoAGroup,
    ) -> TableCell:
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
        study_selection_activity: (
            StudySelectionActivity | StudySelectionActivityInstance
        ),
        num_cols: int,
    ) -> TableRow:
        """returns TableRow for Activity Group row"""

        group_name = (
            study_selection_activity.study_activity_group.activity_group_name
            if study_selection_activity.study_activity_group.activity_group_uid
            else _T("no_study_group")
        )

        row = TableRow(
            order=study_selection_activity.study_activity_group.order,
            level=2,
            hide=not getattr(
                study_selection_activity,
                "show_activity_group_in_protocol_flowchart",
                True,
            ),
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
        study_selection_activity: (
            StudySelectionActivity | StudySelectionActivityInstance
        ),
        num_cols: int,
    ) -> TableRow:
        """returns TableRow for Activity SubGroup row"""

        group_name = (
            study_selection_activity.study_activity_subgroup.activity_subgroup_name
            if study_selection_activity.study_activity_subgroup.activity_subgroup_uid
            else _T("no_study_subgroup")
        )

        row = TableRow(
            order=study_selection_activity.study_activity_subgroup.order,
            level=3,
            hide=not getattr(
                study_selection_activity,
                "show_activity_subgroup_in_protocol_flowchart",
                True,
            ),
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
        footnotes: Iterable[StudySoAFootnote],
        layout: SoALayout | None = None,
    ):
        """Adds footnote symbols to table rows based on the referenced uids.

        In PROTOCOL layout, only footnotes whose referenced items appear in at least one visible (non-hidden)
        row are included. Footnotes that exclusively reference items in hidden rows are
        silently dropped before symbols are assigned, so they do not appear in the
        rendered footnote listing.
        """

        if layout == SoALayout.PROTOCOL:
            # Only process visible rows
            rows = (row for row in table.rows if not row.hide)

            # Collect referenced UIDs and the sequence of order they appear in the table
            referenced_uids_sequence: dict[str, int] = {}
            for row in rows:
                for cell in row.cells:
                    for ref in cell.refs or []:
                        if ref.uid not in referenced_uids_sequence:
                            referenced_uids_sequence[ref.uid] = len(
                                referenced_uids_sequence
                            )

            # Keep only footnotes that are referenced in visible rows
            footnotes = (
                fn
                for fn in footnotes
                if any(
                    ref.item_uid in referenced_uids_sequence
                    for ref in fn.referenced_items
                )
            )

            # Sort footnotes by the earliest table position of their referenced items
            footnotes = sorted(
                footnotes,
                key=lambda footnote: min(
                    (
                        referenced_uids_sequence[ref.item_uid]
                        for ref in footnote.referenced_items
                        if ref.item_uid in referenced_uids_sequence
                    ),
                    default=len(referenced_uids_sequence) + (footnote.order or 0),
                ),
            )

        (
            footnote_symbols_by_ref_uid,
            simple_footnotes_by_symbol,
        ) = cls._mk_simple_footnotes(footnotes)
        for row in table.rows:
            for cell in row.cells:
                _footnotes = set(cell.footnotes or [])
                for ref in cell.refs or []:
                    _footnotes.update(footnote_symbols_by_ref_uid.get(ref.uid, []))
                cell.footnotes = (
                    sorted(str(_footnote) for _footnote in _footnotes)
                    if _footnotes
                    and cell.text  # Only show footnote symbols if there is cell text to attach them to
                    else None
                )

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
    def _hide_rows_without_checkmarks(
        rows: list[TableRow], num_header_rows: int, num_header_cols: int = 2
    ):
        """
        Hides activity rows that don't contain any checkmarks in visit cells.

        Args:
            rows: List of table rows
            num_header_rows: Number of header rows to skip
            num_header_cols: Number of leading header columns to skip when checking for checkmarks
        """
        for row in rows[num_header_rows:]:
            has_checkmark = any(
                cell.text == SOA_CHECK_MARK for cell in row.cells[num_header_cols:]
            )
            if not has_checkmark:
                row.hide = True

    @staticmethod
    @trace_calls
    def _group_rows_by_subgroup(rows: list[TableRow], num_header_rows: int):
        """Reorders activity rows in place so rows with the same subgroup name (first cell) are consecutive."""
        activity_rows = rows[num_header_rows:]
        groups: dict[str, list[TableRow]] = {}
        for row in activity_rows:
            key = row.cells[0].text if row.cells else ""
            groups.setdefault(key, []).append(row)
        rows[num_header_rows:] = [row for group in groups.values() for row in group]

    @staticmethod
    @trace_calls
    def _hide_repeated_subgroup_names(rows: list[TableRow]):
        """Clears the activity subgroup name (first cell) on subsequent rows where it repeats."""
        prev_subgroup_name = None
        for row in rows:
            if row.hide or not row.cells:
                continue
            cell = row.cells[0]
            if cell.text == prev_subgroup_name:
                cell.text = ""
            else:
                prev_subgroup_name = cell.text

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
    def amend_procedure_label(rows: Sequence[TableRow]):
        """Set Procedure on the epochs header row when present; leave visit short name alone."""
        study_epoch_label = _T("study_epoch")
        procedure_label = _T("procedure_label", "")
        for row in rows[: min(3, len(rows))]:
            if row.hide or not row.cells:
                continue
            cell = row.cells[0]
            # Epochs row is header1 with study_epoch (or already Procedure); visits are header2
            if cell.style == "header1" and cell.text in (
                study_epoch_label,
                procedure_label,
            ):
                cell.text = procedure_label
                return
            if cell.style == "header2":
                # Visits row already has visit_short_name
                return

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

    @trace_calls
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
        protocol_lab_table: bool = False,
    ) -> list[dict[Any, Any]]:
        if not study_value_version:
            query = "MATCH (study_root:StudyRoot{uid:$study_uid})-[has_version:LATEST]-(study_value:StudyValue)"
        else:
            query = "MATCH (study_root:StudyRoot{uid:$study_uid})-[has_version:HAS_VERSION {version:$study_value_version}]-(study_value:StudyValue)"
        if protocol_flowchart or protocol_lab_table:
            # Protocol exports: only include activities that have schedules
            query += """
            MATCH (study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(study_value)
            MATCH (study_activity_schedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(study_value)
            MATCH (study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(study_value)
            MATCH (study_activity_schedule)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value)
            """
            if protocol_flowchart:
                query += "WHERE study_activity.show_activity_in_protocol_flowchart=true AND NOT study_visit.visit_class IN ['UNSCHEDULED_VISIT', 'NON_VISIT']"
        else:
            # Detailed SoA exports: include all activities, even those without schedules
            query += """
            MATCH (study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value)
            WHERE NOT (study_activity)-[:BEFORE]-()
            OPTIONAL MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(study_value),
                (study_activity_schedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(study_value),
                (study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(study_value)
            """
        query += """
        WITH has_version,study_value, study_activity_schedule, study_visit, study_epoch, study_activity,
            head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue) | activity_value]) as activity,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
                -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue) 
                    | {
                        activity_subgroup_value: activity_subgroup_value,
                        order: study_activity_subgroup.order
                    }]) as study_activity_subgroup,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
                -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue) 
                    | {
                        activity_group_value: activity_group_value,
                        order: study_activity_group.order
                    }]) as study_activity_group,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
                -[:HAS_FLOWCHART_GROUP]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue) 
                | {
                    term_name_value:term_name_value,
                    order: study_soa_group.order
                    }]) as study_soa_group,
            head([(study_epoch)-[:HAS_EPOCH]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]-
                (epoch_term:CTTermNameValue) | epoch_term.name]) as epoch_name,
            head([(study_visit)-[:HAS_VISIT_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]-
                (visity_type_term:CTTermNameValue) | 
                {
                    is_soa_milestone:study_visit.is_soa_milestone,
                    milestone_name:visity_type_term.name
                }]) as milestone
        """
        query += (
            "WHERE trim(toLower(study_activity_group.activity_group_value.name)) = $activity_group_filter"
            if protocol_lab_table
            else ""
        )
        query += """
        ORDER BY study_soa_group.order, study_activity_group.order, study_activity_subgroup.order, study_activity.order, study_visit.visit_number
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
            study_activity_subgroup.activity_subgroup_value.name AS activity_subgroup,
            study_activity_group.activity_group_value.name AS activity_group,
            study_soa_group.term_name_value.name as soa_group,
            milestone as milestone,
            coalesce(activity.is_data_collected, False) AS is_data_collected,
            study_activity_schedule.uid as study_activity_schedule_uid
        """

        result_array, attribute_names = db.cypher_query(
            query,
            params={
                "study_uid": study_uid,
                "study_value_version": study_value_version,
                "activity_group_filter": (
                    LAB_TABLE_INCLUDE_ACTIVITY_GROUP.lower().strip()
                    if protocol_lab_table
                    else None
                ),
            },
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
                            if content_prop and content_prop.get("is_soa_milestone")
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
    ) -> list[dict[Any, Any]]:
        if not study_value_version:
            query = "MATCH (study_root:StudyRoot{uid:$study_uid})-[has_version:LATEST]-(study_value:StudyValue)"
        else:
            query = "MATCH (study_root:StudyRoot{uid:$study_uid})-[has_version:HAS_VERSION {version:$study_value_version}]-(study_value:StudyValue)"
        query += """
            MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)
                -[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->(study_activity_instance:StudyActivityInstance)
                <-[:HAS_STUDY_ACTIVITY_INSTANCE]-(study_value)
            WHERE NOT (study_activity)-[:BEFORE]-()
            OPTIONAL MATCH (study_activity_instance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->(activity_instance_value:ActivityInstanceValue)
            MATCH (study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue)<-[:HAS_VERSION]-(:ActivityRoot)<-[:CONTAINS_CONCEPT]-(lib:Library)
            OPTIONAL MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(study_value),
                (study_activity_schedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(study_value),
                (study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(study_value)
            WITH has_version, study_value, study_activity_schedule, study_visit, study_epoch, study_activity_instance, study_activity, activity_instance_value, lib,
            head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue) | av]) as activity,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
                -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue) 
                    | {
                        activity_subgroup_value: activity_subgroup_value,
                        order: study_activity_subgroup.order
                    }]) as study_activity_subgroup,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
                -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue) 
                    | {
                        activity_group_value: activity_group_value,
                        order: study_activity_group.order
                    }]) as study_activity_group,
            head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
                -[:HAS_FLOWCHART_GROUP]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue) 
                | {
                    term_name_value:term_name_value,
                    order: study_soa_group.order
                    }]) as study_soa_group,
                head([(study_epoch)-[:HAS_EPOCH]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]-
                    (epoch_term:CTTermNameValue) | epoch_term.name]) as epoch_name
            ORDER BY study_soa_group.order, study_activity_group.order, study_activity_subgroup.order, study_activity.order, study_visit.visit_number
            RETURN DISTINCT
                CASE
                    WHEN has_version.status IN ["RELEASED", "LOCKED"]
                    THEN has_version.version
                    ELSE "LATEST on "+apoc.temporal.format(datetime(), 'yyyy-MM-dd HH:mm:ss zzz')
                END as study_version,
                study_value.study_number AS study_number,
                lib.name AS library,
                study_visit.short_visit_label AS visit,
                epoch_name AS epoch,
                activity.name AS activity,
                activity_instance_value.name AS activity_instance,
                activity_instance_value.topic_code AS topic_code,
                activity_instance_value.adam_param_code AS param_code,
                study_activity_subgroup.activity_subgroup_value.name AS activity_subgroup,
                study_activity_group.activity_group_value.name AS activity_group,
                study_soa_group.term_name_value.name as soa_group,
                study_activity_schedule.uid as study_activity_schedule_uid
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

        ValidationException.raise_if(
            layout != SoALayout.PROTOCOL,
            msg=f"SoA snapshot is only supported for layout '{SoALayout.PROTOCOL.value}', not '{layout.value}'.",
        )

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
    def _fetch_soa_snapshot_data(
        self, study_uid, study_value_version, layout, time_unit
    ):
        if not time_unit:
            time_unit = self.get_preferred_time_unit(
                study_uid, study_value_version=study_value_version
            )

        self._validate_parameters(
            study_uid, study_value_version=study_value_version, time_unit=time_unit
        )

        # Fetch database objects in parallel
        with ThreadPoolExecutor() as executor:
            soa_preferences_future = executor.submit(
                RuntimeContext.with_current_context(self._get_soa_preferences),
                study_uid,
                study_value_version=study_value_version,
            )

            soa_snapshot_future = executor.submit(
                RuntimeContext.with_current_context(self.repository.load),
                study_uid=study_uid,
                study_value_version=study_value_version,
                layout=layout,
            )

            study_visits_future = executor.submit(
                RuntimeContext.with_current_context(self._get_study_visits),
                study_uid=study_uid,
                study_value_version=study_value_version,
            )

            study_soa_groups_future = executor.submit(
                RuntimeContext.with_current_context(self._get_study_soa_groups),
                study_uid=study_uid,
                study_value_version=study_value_version,
            )

            study_activity_groups_future = executor.submit(
                RuntimeContext.with_current_context(self._get_study_activity_groups),
                study_uid=study_uid,
                study_value_version=study_value_version,
            )

            study_activity_subgroups_future = executor.submit(
                RuntimeContext.with_current_context(self._get_study_activity_subgroups),
                study_uid=study_uid,
                study_value_version=study_value_version,
            )

            study_activities_future = executor.submit(
                RuntimeContext.with_current_context(self.fetch_study_activities),
                study_uid=study_uid,
                study_value_version=study_value_version,
            )

            study_footnotes_future = executor.submit(
                RuntimeContext.with_current_context(self._get_study_footnotes),
                study_uid,
                study_value_version=study_value_version,
            )

        soa_preferences: StudySoaPreferences = soa_preferences_future.result()

        soa_cell_references, soa_footnote_references = soa_snapshot_future.result()

        NotFoundException.raise_if_not(
            soa_cell_references,
            msg=f"No SoA snapshot found for Study with uid '{study_uid}' and version '{study_value_version}'",
        )

        study_visits_by_uid: Mapping[str, StudyVisitLite] = self._map_by_uid(
            study_visits_future.result()
        )

        study_epochs_by_uid: Mapping[str, StudyEpochTiny] = self._map_by_uid(
            StudyEpochTiny.from_study_visit(study_visit)
            for study_visit in study_visits_by_uid.values()
        )

        study_soa_groups_by_uid = self._map_by_uid(
            study_soa_groups_future.result(),
            "study_soa_group_uid",
        )

        study_activity_groups_by_uid = self._map_by_uid(
            study_activity_groups_future.result(),
            "study_activity_group_uid",
        )

        study_activity_subgroups_by_uid = self._map_by_uid(
            study_activity_subgroups_future.result(),
            "study_activity_subgroup_uid",
        )

        study_activities_by_uid = self._map_by_uid(
            study_activities_future.result(),
            "study_activity_uid",
        )

        return (
            soa_cell_references,
            soa_footnote_references,
            soa_preferences,
            study_activities_by_uid,
            study_activity_groups_by_uid,
            study_activity_subgroups_by_uid,
            study_epochs_by_uid,
            study_footnotes_future,
            study_soa_groups_by_uid,
            study_visits_by_uid,
            time_unit,
        )

    @trace_calls
    def load_soa_snapshot(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        layout: SoALayout = SoALayout.PROTOCOL,
        time_unit: str | None = None,
    ) -> TableWithFootnotes:
        """Loads SoA snapshot from db, and reconstructs SoA table and footnotes"""

        ValidationException.raise_if(
            layout != SoALayout.PROTOCOL,
            msg=f"SoA snapshot is only supported for layout '{SoALayout.PROTOCOL.value}', not '{layout.value}'.",
        )

        (
            soa_cell_references,
            soa_footnote_references,
            soa_preferences,
            study_activities_by_uid,
            study_activity_groups_by_uid,
            study_activity_subgroups_by_uid,
            study_epochs_by_uid,
            study_footnotes_future,
            study_soa_groups_by_uid,
            study_visits_by_uid,
            time_unit,
        ) = self._fetch_soa_snapshot_data(
            study_uid, study_value_version, layout, time_unit
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
            study_epoch: StudyEpochTiny = study_epochs_by_uid[
                ref.referenced_item.item_uid
            ]
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
        prev_milestone_cell: TableCell | None = None
        for col_idx, refs in visit_references.items():
            visits_in_group = [
                study_visits_by_uid[ref.referenced_item.item_uid] for ref in refs
            ]
            visit: StudyVisitLite = visits_in_group[0]

            if visit.is_soa_milestone:
                if prev_visit_type_uid == visit.visit_type.term_uid:
                    # Same visit_type, then merge with the previous cell in Milestone row
                    prev_milestone_cell.span += 1
                    milestone_row.cells[col_idx].span = 0

                else:
                    # Different visit_type, new label in Milestones row
                    prev_visit_type_uid = visit.visit_type.term_uid
                    milestone_row.cells[col_idx] = prev_milestone_cell = TableCell(
                        visit.visit_type.sponsor_preferred_name,
                        style="header1",
                    )

            visit_row.cells[col_idx] = TableCell(
                self._get_visit_name(visits_in_group),
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
                row.order = study_soa_group.order
                row.level = 1

            elif refi.item_type == SoAItemType.STUDY_ACTIVITY_GROUP:
                study_activity_group = study_activity_groups_by_uid[refi.item_uid]
                row.cells[coords.col] = cell = self._get_activity_group_cell(
                    study_activity_group
                )
                row.order = study_activity_group.order
                row.level = 2

            elif refi.item_type == SoAItemType.STUDY_ACTIVITY_SUBGROUP:
                study_activity_subgroup = study_activity_subgroups_by_uid[refi.item_uid]
                row.cells[coords.col] = cell = self._get_activity_subgroup_cell(
                    study_activity_subgroup
                )
                row.order = study_activity_subgroup.order
                row.level = 3

            elif refi.item_type == SoAItemType.STUDY_ACTIVITY:
                study_activity = study_activities_by_uid[refi.item_uid]
                row.cells[coords.col] = cell = self._get_study_activity_cell(
                    study_activity
                )
                row.order = study_activity.order
                row.level = 4

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
            study_footnotes_future.result()
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
            StudyFlowchartService.amend_procedure_label(
                table.rows[: table.num_header_rows]
            )

        return table

    BaseModelType = TypeVar("BaseModelType", bound=BaseModel)

    @staticmethod
    def _map_by_uid(
        items: Iterable[BaseModelType], uid_property_name: str = "uid"
    ) -> dict[str, BaseModelType]:
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
            layout=layout,
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

    @staticmethod
    def _get_visit_refs(header_rows: Iterable[TableRow]) -> dict[int, Ref]:
        """Extracts StudyVisit references from SoA table header rows, indexed by column index"""

        visit_refs: dict[int, ReferencedItem] = {}

        for i, cell in enumerate(header_rows[-3].cells):  # type: ignore[index]
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
            accepted_ref_types: Iterable,
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
            num_header_cols += NUM_OPERATIONAL_CODE_COLS

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


def get_study_version(study: Study) -> str:
    """Returns study version as string"""
    if (
        study.current_metadata.version_metadata.study_status
        == StudyStatus.RELEASED.value
    ):
        return study.current_metadata.version_metadata.version_number
    return study.current_metadata.version_metadata.version_timestamp.strftime(
        "LATEST on %Y-%m-%d %H:%M:%S Z"
    )
