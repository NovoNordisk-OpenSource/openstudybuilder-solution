import dataclasses
import datetime
from typing import Any

from neomodel import Q, db

from clinical_mdr_api.domain_repositories.models.study_visit import (
    StudyVisit as StudyVisitNeoModel,
)
from clinical_mdr_api.domain_repositories.study_selections.study_visit_repository import (
    get_valid_time_references_for_study,
)
from clinical_mdr_api.domains.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
    NumericValueType,
    NumericValueVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_day import (
    StudyDayAR,
    StudyDayVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_duration_days import (
    StudyDurationDaysAR,
    StudyDurationDaysVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_duration_weeks import (
    StudyDurationWeeksAR,
    StudyDurationWeeksVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.study_week import (
    StudyWeekAR,
    StudyWeekVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.time_point import (
    TimePointAR,
    TimePointVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.visit_name import (
    VisitNameAR,
    VisitNameVO,
)
from clinical_mdr_api.domains.concepts.simple_concepts.week_in_study import (
    WeekInStudyAR,
    WeekInStudyVO,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_epoch import (
    StudyEpochEpoch,
    StudyEpochSubType,
    StudyEpochType,
    StudyEpochVO,
    TimelineAR,
)
from clinical_mdr_api.domains.study_selections.study_visit import (
    NumericValue,
    StudyVisitContactMode,
    StudyVisitEpochAllocation,
    StudyVisitHistoryVO,
    StudyVisitRepeatingFrequency,
    StudyVisitTimeReference,
    StudyVisitType,
    StudyVisitVO,
    TextValue,
    TimePoint,
    TimeUnit,
    VisitClass,
    VisitSubclass,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyActivityScheduleCreateInput,
)
from clinical_mdr_api.models.study_selections.study_visit import (
    AllowedTimeReferences,
    SimpleStudyVisit,
    StudyVisit,
    StudyVisitCreateInput,
    StudyVisitEditInput,
    StudyVisitVersion,
)
from clinical_mdr_api.models.utils import (
    GenericFilteringReturn,
    get_latest_on_datetime_str,
)
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from clinical_mdr_api.services.user_info import UserInfoService
from common import config as settings
from common import exceptions
from common.auth.user import user
from common.config import (
    ANCHOR_VISIT_IN_VISIT_GROUP,
    GLOBAL_ANCHOR_VISIT_NAME,
    NON_VISIT_NUMBER,
    PREVIOUS_VISIT_NAME,
    STUDY_VISIT_TYPE_INFORMATION_VISIT,
    UNSCHEDULED_VISIT_NUMBER,
)
from common.exceptions import (
    BusinessLogicException,
    NotFoundException,
    ValidationException,
    VisitsAreNotEqualException,
)
from common.telemetry import trace_calls


class StudyVisitService(StudySelectionMixin):
    def __init__(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ):
        self._repos = MetaRepository()
        self.repo = self._repos.study_visit_repository
        self.study_epoch_types = []
        self.study_epoch_subtypes = []
        self.study_epoch_epochs = []
        self.study_visit_types = []
        self.study_visit_repeating_frequency = []
        self.study_visit_timeref = []
        self.study_visit_contact_mode = []
        self.study_visit_epoch_allocation = []
        self.author = user().id()
        self.terms_at_specific_datetime = self._extract_effective_date(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )
        self._create_ctlist_map()
        self._day_unit, self._week_unit = self.repo.get_day_week_units()

    def _extract_effective_date(self, study_uid, study_value_version: str = None):
        study_standard_versions = self._repos.study_standard_version_repository.find_standard_versions_in_study(
            study_uid=study_uid,
            study_value_version=study_value_version,
        )
        study_standard_versions_sdtm = [
            study_standard_version
            for study_standard_version in study_standard_versions
            if "SDTM CT" in study_standard_version.ct_package_uid
        ]
        study_standard_version_sdtm = (
            study_standard_versions_sdtm[0] if study_standard_versions_sdtm else None
        )
        terms_at_specific_date = None
        if study_standard_version_sdtm:
            terms_at_specific_date = self._repos.ct_package_repository.find_by_uid(
                study_standard_version_sdtm.ct_package_uid
            ).effective_date
        return (
            datetime.datetime(
                terms_at_specific_date.year,
                terms_at_specific_date.month,
                terms_at_specific_date.day,
                23,
                59,
                59,
                999999,
            )
            if terms_at_specific_date
            else None
        )

    def _create_ctlist_map(self):
        ct_terms = self.repo.fetch_ctlist(
            codelist_names=[
                settings.STUDY_EPOCH_TYPE_NAME,
                settings.STUDY_EPOCH_SUBTYPE_NAME,
                settings.STUDY_EPOCH_EPOCH_NAME,
                settings.STUDY_VISIT_TYPE_NAME,
                settings.STUDY_VISIT_REPEATING_FREQUENCY,
                settings.STUDY_VISIT_TIMEREF_NAME,
                settings.STUDY_VISIT_CONTACT_MODE_NAME,
                settings.STUDY_VISIT_EPOCH_ALLOCATION_NAME,
            ]
        )
        for ct_term_uid, codelist_names in ct_terms.items():
            if settings.STUDY_EPOCH_TYPE_NAME in codelist_names:
                self.study_epoch_types.append(ct_term_uid)
            if settings.STUDY_EPOCH_SUBTYPE_NAME in codelist_names:
                self.study_epoch_subtypes.append(ct_term_uid)
            if settings.STUDY_EPOCH_EPOCH_NAME in codelist_names:
                self.study_epoch_epochs.append(ct_term_uid)
            if settings.STUDY_VISIT_TYPE_NAME in codelist_names:
                self.study_visit_types.append(ct_term_uid)
            if settings.STUDY_VISIT_REPEATING_FREQUENCY in codelist_names:
                self.study_visit_repeating_frequency.append(ct_term_uid)
            if settings.STUDY_VISIT_TIMEREF_NAME in codelist_names:
                self.study_visit_timeref.append(ct_term_uid)
            if settings.STUDY_VISIT_CONTACT_MODE_NAME in codelist_names:
                self.study_visit_contact_mode.append(ct_term_uid)
            if settings.STUDY_VISIT_EPOCH_ALLOCATION_NAME in codelist_names:
                self.study_visit_epoch_allocation.append(ct_term_uid)

        ctterm_uids = list(
            set(
                self.study_epoch_types
                + self.study_epoch_subtypes
                + self.study_epoch_epochs
                + self.study_visit_types
                + self.study_visit_repeating_frequency
                + self.study_visit_timeref
                + self.study_visit_contact_mode
                + self.study_visit_epoch_allocation
            )
        )

        ctterms = self._find_terms_by_uids(
            term_uids=ctterm_uids,
            at_specific_date=self.terms_at_specific_datetime,
            return_simple_object=True,
        )

        StudyEpochType.clear()
        StudyEpochType.update(
            [
                (ct_term.term_uid, ct_term)
                for ct_term in ctterms
                if ct_term.term_uid in self.study_epoch_types
            ]
        )

        StudyEpochSubType.clear()
        StudyEpochSubType.update(
            [
                (ct_term.term_uid, ct_term)
                for ct_term in ctterms
                if ct_term.term_uid in self.study_epoch_subtypes
            ]
        )

        StudyEpochEpoch.clear()
        StudyEpochEpoch.update(
            [
                (ct_term.term_uid, ct_term)
                for ct_term in ctterms
                if ct_term.term_uid in self.study_epoch_epochs
            ]
        )

        StudyVisitType.clear()
        StudyVisitType.update(
            [
                (ct_term.term_uid, ct_term)
                for ct_term in ctterms
                if ct_term.term_uid in self.study_visit_types
            ]
        )

        StudyVisitRepeatingFrequency.clear()
        StudyVisitRepeatingFrequency.update(
            [
                (ct_term.term_uid, ct_term)
                for ct_term in ctterms
                if ct_term.term_uid in self.study_visit_repeating_frequency
            ]
        )

        StudyVisitTimeReference.clear()
        StudyVisitTimeReference.update(
            [
                (ct_term.term_uid, ct_term)
                for ct_term in ctterms
                if ct_term.term_uid in self.study_visit_timeref
            ]
        )

        StudyVisitContactMode.clear()
        StudyVisitContactMode.update(
            [
                (ct_term.term_uid, ct_term)
                for ct_term in ctterms
                if ct_term.term_uid in self.study_visit_contact_mode
            ]
        )

        StudyVisitEpochAllocation.clear()
        StudyVisitEpochAllocation.update(
            [
                (ct_term.term_uid, ct_term)
                for ct_term in ctterms
                if ct_term.term_uid in self.study_visit_epoch_allocation
            ]
        )

    def get_allowed_time_references_for_study(self, study_uid: str):
        resp = []
        for uid, name in get_valid_time_references_for_study(
            study_uid=study_uid, effective_date=self.terms_at_specific_datetime
        ).items():
            resp.append(
                AllowedTimeReferences(time_reference_uid=uid, time_reference_name=name)
            )
        # if we don't have any visits we have to remove 'previous visit' time reference
        if self.repo.count_study_visits(study_uid=study_uid) < 1:
            resp = [
                item for item in resp if item.time_reference_name != PREVIOUS_VISIT_NAME
            ]

        resp.sort(key=lambda time_reference: time_reference.time_reference_name)

        return resp

    def _transform_all_to_response_model(
        self,
        visit: StudyVisitVO,
        study_activity_count: int | None = None,
        study_value_version: str | None = None,
    ) -> StudyVisit:
        timepoint = visit.timepoint
        if timepoint:
            visit_timereference = StudyVisitTimeReference.get(
                timepoint.visit_timereference.term_uid
            )
            timepoint.visit_timereference = visit_timereference
        visit.epoch_connector.epoch = StudyEpochEpoch.get(visit.epoch.epoch.term_uid)
        visit.visit_type = StudyVisitType.get(visit.visit_type.term_uid)
        visit.visit_contact_mode = StudyVisitContactMode.get(
            visit.visit_contact_mode.term_uid
        )
        epoch_allocation_uid = getattr(visit.epoch_allocation, "term_uid", None)
        if epoch_allocation_uid:
            visit.epoch_allocation = StudyVisitEpochAllocation.get(epoch_allocation_uid)
        repeating_frequency_uid = getattr(visit.repeating_frequency, "term_uid", None)
        if repeating_frequency_uid:
            visit.repeating_frequency = StudyVisitRepeatingFrequency.get(
                repeating_frequency_uid
            )
        return StudyVisit(
            visit_type_name=visit.visit_type.sponsor_preferred_name,
            uid=visit.uid,
            study_uid=visit.study_uid,
            study_id=(
                f"{visit.study_id_prefix}-{visit.study_number}"
                if visit.study_id_prefix and visit.study_number
                else None
            ),
            study_version=study_value_version or get_latest_on_datetime_str(),
            study_epoch_uid=visit.epoch_uid,
            study_epoch=visit.epoch.epoch,
            epoch_uid=visit.epoch.epoch.term_uid,
            order=visit.visit_order,
            visit_type_uid=visit.visit_type.term_uid,
            visit_type=visit.visit_type,
            time_reference_uid=(
                timepoint.visit_timereference.term_uid if timepoint else None
            ),
            time_reference_name=(
                timepoint.visit_timereference.sponsor_preferred_name
                if timepoint
                else None
            ),
            time_reference=getattr(timepoint, "visit_timereference", None),
            time_value=getattr(timepoint, "visit_value", None),
            time_unit_uid=getattr(timepoint, "time_unit_uid", None),
            time_unit_name=getattr(visit.time_unit_object, "name", None),
            duration_time=visit.get_absolute_duration() if timepoint else None,
            duration_time_unit=getattr(timepoint, "time_unit_uid", None),
            study_day_number=getattr(visit, "study_day_number", None),
            study_day_label=getattr(visit, "study_day_label", None),
            study_duration_days=getattr(visit.study_duration_days, "value", None),
            study_duration_days_label=getattr(visit, "study_duration_days_label", None),
            study_week_number=getattr(visit, "study_week_number", None),
            study_week_label=getattr(visit, "study_week_label", None),
            study_duration_weeks=getattr(visit.study_duration_weeks, "value", None),
            study_duration_weeks_label=getattr(
                visit, "study_duration_weeks_label", None
            ),
            week_in_study_label=getattr(visit, "week_in_study_label", None),
            visit_number=visit.visit_number,
            visit_subnumber=visit.visit_subnumber,
            unique_visit_number=visit.unique_visit_number,
            visit_subname=visit.visit_subname,
            visit_sublabel_reference=visit.visit_sublabel_reference,
            visit_name=visit.visit_name,
            visit_short_name=str(visit.visit_short_name),
            consecutive_visit_group=visit.consecutive_visit_group,
            show_visit=visit.show_visit,
            min_visit_window_value=visit.visit_window_min,
            max_visit_window_value=visit.visit_window_max,
            visit_window_unit_uid=visit.window_unit_uid,
            visit_window_unit_name=getattr(visit.window_unit_object, "name", None),
            description=visit.description,
            start_rule=visit.start_rule,
            end_rule=visit.end_rule,
            visit_contact_mode_uid=visit.visit_contact_mode.term_uid,
            visit_contact_mode=visit.visit_contact_mode,
            epoch_allocation_uid=epoch_allocation_uid,
            epoch_allocation=getattr(visit, "epoch_allocation", None),
            status=visit.status.value,
            start_date=visit.start_date.strftime(settings.DATE_TIME_FORMAT),
            author_username=visit.author_username or visit.author_id,
            possible_actions=visit.possible_actions,
            study_activity_count=study_activity_count,
            visit_class=visit.visit_class.name,
            visit_subclass=getattr(visit.visit_subclass, "name", None),
            is_global_anchor_visit=visit.is_global_anchor_visit,
            is_soa_milestone=visit.is_soa_milestone,
            repeating_frequency_uid=repeating_frequency_uid,
            repeating_frequency=getattr(visit, "repeating_frequency", None),
        )

    def _transform_all_to_response_history_model(
        self, visit: StudyVisitHistoryVO
    ) -> StudyVisit:
        study_visit: StudyVisit = self._transform_all_to_response_model(visit)
        study_visit.change_type = visit.change_type
        study_visit.end_date = (
            visit.end_date.strftime(settings.DATE_TIME_FORMAT)
            if visit.end_date
            else None
        )
        # Assign properties directly from database values
        # We should not derive properies based on Visit order in the schedule
        # as we can't represent schedule for old versions of Visits
        study_visit.unique_visit_number = visit.vis_unique_number

        return study_visit

    def _get_all_visits(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudyVisitVO]:
        repos = self._repos
        try:
            study_visits = self.repo.find_all_visits_by_study_uid(
                study_uid=study_uid, study_value_version=study_value_version
            )
            timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
            assert study_visits is not None
            return timeline.ordered_study_visits
        finally:
            repos.close()

    def get_amount_of_visits_in_given_epoch(
        self, study_uid: str, study_epoch_uid: str
    ) -> int:
        visits_in_given_study_epoch = StudyVisitNeoModel.nodes.filter(
            study_epoch_has_study_visit__uid=study_epoch_uid,
            has_study_visit__latest_value__uid=study_uid,
        ).resolve_subgraph()
        return len(visits_in_given_study_epoch)

    def get_global_anchor_visit(self, study_uid: str) -> SimpleStudyVisit | None:
        global_anchor_visit = (
            StudyVisitNeoModel.nodes.fetch_relations(
                "has_visit_name__has_latest_value",
                "has_visit_type__has_name_root__has_latest_value",
            )
            .filter(
                has_study_visit__latest_value__uid=study_uid,
                is_global_anchor_visit=True,
            )
            .resolve_subgraph()
        )

        NotFoundException.raise_if(
            len(global_anchor_visit) < 1,
            msg=f"Global anchor visit for Study with UID '{study_uid}' doesn't exist.",
        )

        return SimpleStudyVisit.model_validate(global_anchor_visit[0])

    def get_anchor_visits_in_a_group_of_subvisits(
        self, study_uid: str
    ) -> list[SimpleStudyVisit]:
        anchor_visits_in_a_group_of_subv = (
            StudyVisitNeoModel.nodes.fetch_relations(
                "has_visit_name__has_latest_value",
                "has_visit_type__has_name_root__has_latest_value",
            )
            .filter(
                has_study_visit__latest_value__uid=study_uid,
                visit_subclass=VisitSubclass.ANCHOR_VISIT_IN_GROUP_OF_SUBV.name,
            )
            .resolve_subgraph()
        )
        return [
            SimpleStudyVisit.model_validate(anchor_visit)
            for anchor_visit in anchor_visits_in_a_group_of_subv
        ]

    def get_anchor_for_special_visit(
        self, study_uid: str, study_epoch_uid: str
    ) -> list[SimpleStudyVisit]:
        anchor_visits_for_special_visit = (
            StudyVisitNeoModel.nodes.fetch_relations(
                "has_visit_name__has_latest_value",
                "has_visit_type__has_name_root__has_latest_value",
            )
            .filter(
                Q(visit_subclass=VisitSubclass.SINGLE_VISIT.name)
                | Q(visit_subclass=VisitSubclass.ANCHOR_VISIT_IN_GROUP_OF_SUBV.name),
                visit_class=VisitClass.SINGLE_VISIT.name,
                has_study_visit__latest_value__uid=study_uid,
                study_epoch_has_study_visit__uid=study_epoch_uid,
            )
            .resolve_subgraph()
        )
        return sorted(
            [
                SimpleStudyVisit.model_validate(anchor_visit)
                for anchor_visit in anchor_visits_for_special_visit
            ],
            key=lambda visit: int(visit.visit_name.split()[1]),
        )

    @trace_calls
    def get_all_visits(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
    ) -> GenericFilteringReturn[StudyVisit]:
        visits = self._get_all_visits(
            study_uid, study_value_version=study_value_version
        )
        visits = [
            self._transform_all_to_response_model(
                visit,
                study_activity_count=visit.number_of_assigned_activities,
                study_value_version=study_value_version,
            )
            for visit in visits
        ]

        filtered_visits = service_level_generic_filtering(
            items=visits,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        return filtered_visits

    def get_distinct_values_for_header(
        self,
        study_uid: str,
        field_name: str,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        page_size: int = 10,
        study_value_version: str | None = None,
    ):
        all_items = self.get_all_visits(
            study_uid=study_uid, study_value_version=study_value_version
        )

        # Do filtering, sorting, pagination and count
        header_values = service_level_generic_header_filtering(
            items=all_items.items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
        )
        # Return values for field_name
        return header_values

    @db.transaction
    def get_all_references(self, study_uid: str) -> list[StudyVisit]:
        visits = self._get_all_visits(study_uid)
        result = []
        sponsor_names = [
            timeref.sponsor_preferred_name
            for timeref in StudyVisitTimeReference.values()
        ]
        for visit in visits:
            if visit.visit_type.sponsor_preferred_name in sponsor_names:
                result.append(self._transform_all_to_response_model(visit))
        return result

    @db.transaction
    def find_by_uid(
        self, study_uid: str, uid: str, study_value_version: str | None = None
    ) -> StudyVisit | None:
        """
        finds latest version of visit by uid, status ans version
        if user do not give status and version - will be overwritten by DRAFT
        """
        repos = self._repos
        try:
            study_visit = self.repo.find_by_uid(
                study_uid=study_uid, uid=uid, study_value_version=study_value_version
            )

            study_visits = self.repo.find_all_visits_by_study_uid(
                study_visit.study_uid, study_value_version=study_value_version
            )
            timeline = TimelineAR(study_uid=study_visit.study_uid, _visits=study_visits)
            assert study_visits is not None
            for ordered_study_visit in timeline.ordered_study_visits:
                if ordered_study_visit.uid == study_visit.uid:
                    return self._transform_all_to_response_model(
                        ordered_study_visit,
                        study_activity_count=self.repo.count_activities(
                            visit_uid=study_visit.uid,
                            study_value_version=study_value_version,
                        ),
                    )
        finally:
            repos.close()

        return None

    def _chronological_order_check(
        self,
        visit_vo: StudyVisitVO,
        ordered_visits: list[StudyVisitVO],
    ):
        chronological_order_dict = {}
        for idx, visit in enumerate(ordered_visits[:-1]):
            if VisitClass.SPECIAL_VISIT not in (
                visit.visit_class,
                ordered_visits[idx + 1].visit_class,
            ) and VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV not in (
                visit.visit_subclass,
                ordered_visits[idx + 1].visit_subclass,
            ):
                if visit.visit_number > ordered_visits[idx + 1].visit_number:
                    chronological_order_dict["visit number"] = visit_vo.visit_number
                if (
                    visit.unique_visit_number
                    > ordered_visits[idx + 1].unique_visit_number
                ):
                    chronological_order_dict["unique visit number"] = (
                        visit_vo.unique_visit_number
                    )
        return chronological_order_dict

    def _validate_derived_properties(
        self, visit_vo: StudyVisitVO, ordered_visits: list[StudyVisitVO]
    ):
        if (
            visit_vo.visit_class != VisitClass.SPECIAL_VISIT
            and visit_vo.visit_subclass
            not in (
                VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV,
                VisitSubclass.ANCHOR_VISIT_IN_GROUP_OF_SUBV,
            )
        ):
            error_dict = {}
            chronological_order_dict = {}
            for idx, visit in enumerate(ordered_visits):
                if (
                    visit_vo.uid != visit.uid
                    and visit.visit_class != VisitClass.SPECIAL_VISIT
                    and visit.visit_subclass
                    != VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
                ):
                    if visit_vo.visit_number == visit.visit_number:
                        error_dict["visit number"] = visit_vo.visit_number
                    if visit_vo.unique_visit_number == visit.unique_visit_number:
                        error_dict["unique visit number"] = visit_vo.unique_visit_number
                    if visit_vo.visit_name == visit.visit_name:
                        error_dict["visit name"] = visit_vo.visit_name
                    if visit_vo.visit_short_name == visit.visit_short_name:
                        error_dict["visit short name"] = visit_vo.visit_short_name
                elif visit_vo.uid == visit.uid:
                    # If visit which is about to be created is the fist visit in schedule
                    if idx == 0 and len(ordered_visits) > 1:
                        chronological_order_dict = self._chronological_order_check(
                            visit_vo=visit_vo,
                            ordered_visits=[visit_vo, ordered_visits[idx + 1]],
                        )
                    # If visit which is about to be created is the last visit in schedule
                    elif idx + 1 == len(ordered_visits) and len(ordered_visits) > 1:
                        chronological_order_dict = self._chronological_order_check(
                            visit_vo=visit_vo,
                            ordered_visits=[ordered_visits[idx - 1], visit_vo],
                        )
                    # If visit which is about to be created is not the first or the last one visit in the schedule
                    elif len(ordered_visits) > 2:
                        chronological_order_dict = self._chronological_order_check(
                            visit_vo=visit_vo,
                            ordered_visits=[
                                ordered_visits[idx - 1],
                                visit_vo,
                                ordered_visits[idx + 1],
                            ],
                        )
            if chronological_order_dict:
                count = len(chronological_order_dict)
                joined_error = " and ".join(
                    [f"{v} in field {k}" for k, v in chronological_order_dict.items()]
                )
                error_msg = f"Value{'s' if count > 1 else ''} {joined_error} {'are' if count > 1 else 'is'}"
                error_msg += " not defined in chronological order by study visit timing"
                if visit_vo.visit_class == VisitClass.SINGLE_VISIT:
                    error_msg += " as a manually defined value exists. Change the manually defined value before this visit can be defined."
                raise exceptions.ValidationException(msg=error_msg)
            if error_dict:
                count = len(error_dict)
                joined_error = " and ".join(
                    [f"{k} - {v}" for k, v in error_dict.items()]
                )
                error_msg = f"Field{'s' if count > 1 else ''} {joined_error} {'are' if count > 1 else 'is'} not unique for the Study"
                if visit_vo.visit_class == VisitClass.SINGLE_VISIT:
                    error_msg += " as a manually defined value exists. Change the manually defined value before this visit can be defined."
                raise exceptions.ValidationException(msg=error_msg)

    def _validate_visit(
        self,
        visit_input: StudyVisitCreateInput,
        visit_vo: StudyVisitVO,
        timeline: TimelineAR,
        create: bool = True,
        preview: bool = False,
        study_visits: list[StudyVisitVO | None] = None,
    ):
        if study_visits is None:
            study_visits = []
        visit_classes_without_timing = (
            VisitClass.NON_VISIT,
            VisitClass.UNSCHEDULED_VISIT,
            VisitClass.SPECIAL_VISIT,
        )
        is_time_reference_visit = False
        if (
            visit_vo.visit_class
            not in (
                VisitClass.NON_VISIT,
                VisitClass.UNSCHEDULED_VISIT,
                VisitClass.SPECIAL_VISIT,
            )
            and visit_vo.visit_type.sponsor_preferred_name
            == visit_vo.timepoint.visit_timereference.sponsor_preferred_name
        ):
            is_time_reference_visit = True

        time_reference_values = [
            timeref.sponsor_preferred_name
            for timeref in StudyVisitTimeReference.values()
        ]
        if len(timeline._visits) == 0:
            is_first_reference_visit = (
                visit_vo.visit_type.sponsor_preferred_name in time_reference_values
            )
            is_reference_visit = is_first_reference_visit
        else:
            is_first_reference_visit = False
            is_reference_visit = (
                visit_vo.visit_type.sponsor_preferred_name in time_reference_values
            )

        if (
            is_first_reference_visit
            and visit_vo.visit_class not in visit_classes_without_timing
        ):
            ValidationException.raise_if(
                visit_vo.timepoint.visit_value != 0
                and visit_vo.timepoint.visit_timereference.sponsor_preferred_name.lower()
                != GLOBAL_ANCHOR_VISIT_NAME.lower(),
                msg="The first visit should have time span set to 0 or reference to GLOBAL ANCHOR VISIT",
            )
            for visit in timeline._visits:
                ValidationException.raise_if(
                    visit.visit_type == visit_vo.visit_type
                    and visit.uid != visit_vo.uid,
                    msg=f"There can be only one visit with the following visit type {visit_vo.visit_type.sponsor_preferred_name}",
                )

        if (
            is_reference_visit
            and visit_vo.visit_class not in visit_classes_without_timing
        ):
            for visit in [
                vis
                for vis in timeline._visits
                if vis.visit_class not in visit_classes_without_timing
            ]:
                ValidationException.raise_if(
                    # if we found another visit with the same visit type
                    visit.visit_type == visit_vo.visit_type
                    # if visit with the same visit type had selected the same value for visit type and time reference
                    and visit.visit_type.sponsor_preferred_name
                    == visit.timepoint.visit_timereference.sponsor_preferred_name
                    # if visit we are creating has the same value selected as visit type and time reference
                    and is_time_reference_visit and visit.uid != visit_vo.uid,
                    msg=f"There can be only one visit with visit type '{visit_vo.visit_type.sponsor_preferred_name}' that works as time reference.",
                )
                BusinessLogicException.raise_if(
                    # We shouldn't allow to create circular time references between Study Visits
                    visit.visit_type.sponsor_preferred_name
                    == visit_vo.timepoint.visit_timereference.sponsor_preferred_name
                    and visit.timepoint.visit_timereference.sponsor_preferred_name
                    == visit_vo.visit_type.sponsor_preferred_name
                    and visit.uid != visit_vo.uid,
                    msg=f"""Circular Visit time reference detected: The visit which is being created, refers to ({visit_vo.timepoint.visit_timereference.sponsor_preferred_name})
                    Visit which refers by time reference to Visit Type ({visit.timepoint.visit_timereference.sponsor_preferred_name}) of the Visit which is being created""",
                )

        if visit_vo.is_global_anchor_visit:
            BusinessLogicException.raise_if(
                (
                    visit_vo.timepoint.visit_value != 0
                    or visit_vo.timepoint.visit_timereference.sponsor_preferred_name
                    != GLOBAL_ANCHOR_VISIT_NAME
                )
                and visit_vo.visit_type.sponsor_preferred_name
                != STUDY_VISIT_TYPE_INFORMATION_VISIT,
                msg="The global anchor visit must take place at day 0 and time reference has to be set to 'Global anchor Visit' or be an Information Visit",
            )
            if create:
                for visit in timeline._visits:
                    ValidationException.raise_if(
                        visit.is_global_anchor_visit,
                        msg="There can be only one global anchor visit",
                    )

        reference_found = False
        if (
            not is_first_reference_visit
            and not is_time_reference_visit
            and visit_vo.visit_class not in visit_classes_without_timing
        ):
            reference_name = StudyVisitTimeReference[visit_input.time_reference_uid]
            for visit in timeline._visits:
                if (
                    visit.visit_type.sponsor_preferred_name
                    == reference_name.sponsor_preferred_name
                ):
                    reference_found = True
            ValidationException.raise_if(
                not reference_found
                and reference_name.sponsor_preferred_name.lower()
                not in [
                    PREVIOUS_VISIT_NAME.lower(),
                    GLOBAL_ANCHOR_VISIT_NAME.lower(),
                    ANCHOR_VISIT_IN_VISIT_GROUP.lower(),
                ],
                msg=f"Time reference of type '{visit_vo.timepoint.visit_timereference.sponsor_preferred_name}' wasn't used by previous visits as visit type.",
            )

        visit_window_units = {
            visit.window_unit_uid
            for visit in timeline._visits
            if visit.visit_class not in visit_classes_without_timing
            and visit.window_unit_uid
        }

        BusinessLogicException.raise_if(
            len(visit_window_units) > 1,
            msg="All StudyVisits should have same window unit in a single Study",
        )
        BusinessLogicException.raise_if(
            len(visit_window_units) == 1
            and visit_vo.window_unit_uid
            and visit_vo.window_unit_uid != visit_window_units.pop()
            and visit_vo.visit_class not in visit_classes_without_timing,
            msg="The StudyVisit which is being created has selected different window unit than other StudyVisits in a Study",
        )

        if visit_vo.visit_class not in (
            VisitClass.NON_VISIT,
            VisitClass.UNSCHEDULED_VISIT,
        ):
            ValidationException.raise_if(
                visit_vo.visit_class == VisitClass.SPECIAL_VISIT
                and visit_vo.visit_sublabel_reference is None,
                msg="Special Visit has to time reference to some other visit.",
            )

            if create:
                timeline.add_visit(visit_vo)
                ordered_visits = timeline.ordered_study_visits

                for index, visit in enumerate(ordered_visits):
                    if visit_vo.visit_class != VisitClass.SPECIAL_VISIT:
                        if (
                            visit.get_absolute_duration()
                            == visit_vo.get_absolute_duration()
                            and visit.uid != visit_vo.uid
                        ):
                            raise exceptions.AlreadyExistsException(
                                msg=f"There already exists a visit with timing set to {visit.timepoint.visit_value}"
                            )
                        if index + 2 < len(ordered_visits):
                            # we check whether the created visit is not from the epoch that sits
                            # out of the epoch schedule
                            ValidationException.raise_if(
                                visit.epoch.order
                                > ordered_visits[index + 2].epoch.order
                                and ordered_visits[index + 2].visit_class
                                not in (
                                    VisitClass.NON_VISIT,
                                    VisitClass.UNSCHEDULED_VISIT,
                                ),
                                msg=f"Visit with Study Day '{visit.study_day_number}' from "
                                f"Epoch with order '{visit.epoch.order}' '{visit.epoch.epoch.sponsor_preferred_name}' is out of order with "
                                f"Visit with Study Day '{ordered_visits[index+2].study_day_number}' from Epoch with order "
                                f"'{ordered_visits[index+2].epoch.order}' '{ordered_visits[index+2].epoch.epoch.sponsor_preferred_name}'",
                            )
                    elif (
                        visit_vo.visit_class == VisitClass.SPECIAL_VISIT
                        and visit.visit_class == VisitClass.SPECIAL_VISIT
                        and visit_vo.epoch_uid == visit.epoch_uid
                        and visit.uid != visit_vo.uid
                    ):
                        raise exceptions.AlreadyExistsException(
                            msg=f"There already exists a Special Visit with UID '{visit.uid}' in the following epoch {visit.epoch_connector.epoch.sponsor_preferred_name}"
                        )
                self._validate_derived_properties(
                    visit_vo=visit_vo, ordered_visits=ordered_visits
                )
            else:
                ordered_visits = timeline.ordered_study_visits
                for index, visit in enumerate(ordered_visits):
                    if (
                        visit_vo.visit_class != VisitClass.SPECIAL_VISIT
                        and visit.get_absolute_duration()
                        == visit_vo.get_absolute_duration()
                        and visit.uid != visit_vo.uid
                    ):
                        raise exceptions.AlreadyExistsException(
                            msg=f"There already exists a visit with timing set to {visit.timepoint.visit_value}"
                        )
                self._validate_derived_properties(
                    visit_vo=visit_vo, ordered_visits=ordered_visits
                )

            if not preview:
                study_epochs = (
                    self._repos.study_epoch_repository.find_all_epochs_by_study(
                        study_uid=visit_vo.study_uid
                    )
                )
                timeline.collect_visits_to_epochs(study_epochs)

                for epoch in study_epochs:
                    if epoch.uid == visit_input.study_epoch_uid:
                        if epoch.previous_visit and (
                            visit_vo.get_absolute_duration()
                            < epoch.previous_visit.get_absolute_duration()
                        ):
                            raise exceptions.BusinessLogicException(
                                msg="The following visit can't be created as previous Epoch Name "
                                f"'{epoch.previous_visit.epoch.epoch.sponsor_preferred_name}' "
                                f"ends at the '{epoch.previous_visit.study_day_number}' Study Day"
                            )
                        if epoch.next_visit and (
                            visit_vo.get_absolute_duration()
                            > epoch.next_visit.get_absolute_duration()
                        ):
                            raise exceptions.BusinessLogicException(
                                msg="The following visit can't be created as the next Epoch Name "
                                f"'{epoch.next_visit.epoch.epoch.sponsor_preferred_name}' "
                                f"starts at the '{epoch.next_visit.study_day_number}' Study Day"
                            )

            if create:
                timeline.remove_visit(visit_vo)

        ValidationException.raise_if(
            visit_input.visit_contact_mode_uid not in StudyVisitContactMode,
            msg=f"CT Term with UID '{visit_input.visit_contact_mode_uid}' is not a valid Visit Contact Mode term.",
        )
        visits_class = [visit.visit_class for visit in study_visits]
        ValidationException.raise_if(
            not preview
            and visit_input.visit_class == VisitClass.NON_VISIT.name
            and VisitClass.NON_VISIT in visits_class,
            msg=f"There's already and exists Non Visit in Study {visit_vo.study_uid}",
        )
        ValidationException.raise_if(
            not preview
            and visit_input.visit_class == VisitClass.UNSCHEDULED_VISIT.name
            and VisitClass.UNSCHEDULED_VISIT in visits_class,
            msg=f"There's already and exists an Unschedule Visit in Study {visit_vo.study_uid}",
        )

    def _get_sponsor_library_vo(self):
        lib = self._repos.library_repository.find_by_name(name="Sponsor")
        return LibraryVO.from_input_values_2(
            library_name=lib.library_name,
            is_library_editable_callback=lambda _: lib.is_editable,
        )

    def _create_visit_name_simple_concept(self, visit_name: str):
        visit_name_ar = VisitNameAR.from_input_values(
            author_id=self.author,
            simple_concept_vo=VisitNameVO.from_repository_values(
                name=visit_name,
                name_sentence_case=visit_name.lower(),
                definition=None,
                abbreviation=None,
                is_template_parameter=True,
            ),
            library=self._get_sponsor_library_vo(),
            generate_uid_callback=self._repos.visit_name_repository.generate_uid,
            find_uid_by_name_callback=self._repos.visit_name_repository.find_uid_by_name,
        )
        self._repos.visit_name_repository.save(visit_name_ar)
        visit_name = TextValue(uid=visit_name_ar.uid, name=visit_name_ar.name)
        return visit_name

    def _create_numeric_value_simple_concept(
        self, value: int, numeric_value_type: NumericValueType
    ):
        if numeric_value_type == NumericValueType.NUMERIC_VALUE:
            aggregate_class = NumericValueAR
            value_object_class = NumericValueVO
            repository_class = self._repos.numeric_value_repository
        elif numeric_value_type == NumericValueType.STUDY_DAY:
            aggregate_class = StudyDayAR
            value_object_class = StudyDayVO
            repository_class = self._repos.study_day_repository
        elif numeric_value_type == NumericValueType.STUDY_DURATION_DAYS:
            aggregate_class = StudyDurationDaysAR
            value_object_class = StudyDurationDaysVO
            repository_class = self._repos.study_duration_days_repository
        elif numeric_value_type == NumericValueType.STUDY_WEEK:
            aggregate_class = StudyWeekAR
            value_object_class = StudyWeekVO
            repository_class = self._repos.study_week_repository
        elif numeric_value_type == NumericValueType.STUDY_DURATION_WEEKS:
            aggregate_class = StudyDurationWeeksAR
            value_object_class = StudyDurationWeeksVO
            repository_class = self._repos.study_duration_weeks_repository
        elif numeric_value_type == NumericValueType.WEEK_IN_STUDY:
            aggregate_class = WeekInStudyAR
            value_object_class = WeekInStudyVO
            repository_class = self._repos.week_in_study_repository
        else:
            raise exceptions.ValidationException(
                msg=f"Unknown numeric value type to create {numeric_value_type.value}"
            )

        numeric_ar = aggregate_class.from_input_values(
            author_id=self.author,
            simple_concept_vo=value_object_class.from_input_values(
                value=float(value),
                definition=None,
                abbreviation=None,
                is_template_parameter=True,
            ),
            library=self._get_sponsor_library_vo(),
            generate_uid_callback=repository_class.generate_uid,
            find_uid_by_name_callback=repository_class.find_uid_by_name,
        )
        repository_class.save(numeric_ar)
        numeric_value_object = NumericValue(
            uid=numeric_ar.uid, value=numeric_ar.concept_vo.value
        )
        return numeric_value_object

    def _create_timepoint_simple_concept(
        self, study_visit_input: StudyVisitCreateInput
    ):
        numeric_ar = self._create_numeric_value_simple_concept(
            value=study_visit_input.time_value,
            numeric_value_type=NumericValueType.NUMERIC_VALUE,
        )
        timepoint_ar = TimePointAR.from_input_values(
            author_id=self.author,
            simple_concept_vo=TimePointVO.from_input_values(
                name_sentence_case=None,
                definition=None,
                abbreviation=None,
                is_template_parameter=True,
                numeric_value_uid=numeric_ar.uid,
                unit_definition_uid=study_visit_input.time_unit_uid,
                time_reference_uid=study_visit_input.time_reference_uid,
                find_numeric_value_by_uid=self._repos.numeric_value_repository.find_by_uid_2,
                find_unit_definition_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
                find_time_reference_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            ),
            library=self._get_sponsor_library_vo(),
            generate_uid_callback=self._repos.time_point_repository.generate_uid,
            find_uid_by_name_callback=self._repos.time_point_repository.find_uid_by_name,
        )
        self._repos.time_point_repository.save(timepoint_ar)
        timepoint_object = TimePoint(
            uid=timepoint_ar.uid,
            visit_timereference=StudyVisitTimeReference[
                study_visit_input.time_reference_uid
            ],
            time_unit_uid=study_visit_input.time_unit_uid,
            visit_value=study_visit_input.time_value,
        )
        return timepoint_object

    def derive_visit_number(self, visit_class: VisitClass):
        if visit_class == VisitClass.NON_VISIT:
            return NON_VISIT_NUMBER
        if visit_class == VisitClass.UNSCHEDULED_VISIT:
            return UNSCHEDULED_VISIT_NUMBER
        return 1

    def _from_input_values(
        self, create_input: StudyVisitCreateInput, epoch: StudyEpochVO
    ):
        unit_repository = self._repos.unit_definition_repository
        if create_input.time_unit_uid:
            req_time_unit_ar: UnitDefinitionAR = unit_repository.find_by_uid_2(
                create_input.time_unit_uid
            )
            req_time_unit = req_time_unit_ar.concept_vo
        else:
            req_time_unit = None
        if create_input.visit_window_unit_uid:
            window_time_unit_ar: UnitDefinitionAR = unit_repository.find_by_uid_2(
                create_input.visit_window_unit_uid
            )
            window_time_unit = window_time_unit_ar.concept_vo
            window_unit_object = TimeUnit(
                name=window_time_unit.name,
                conversion_factor_to_master=window_time_unit.conversion_factor_to_master,
                from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
            )
        else:
            window_unit_object = None

        if req_time_unit:
            time_unit_object = TimeUnit(
                name=req_time_unit.name,
                conversion_factor_to_master=req_time_unit.conversion_factor_to_master,
                from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
            )
        else:
            time_unit_object = None
        day_unit_object = TimeUnit(
            name="day",
            conversion_factor_to_master=self._day_unit.concept_vo.conversion_factor_to_master,
            from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
        )

        week_unit_object = TimeUnit(
            name="Week",
            conversion_factor_to_master=self._week_unit.concept_vo.conversion_factor_to_master,
            from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
        )
        visit_class = (
            VisitClass[create_input.visit_class] if create_input.visit_class else None
        )
        visit_subclass = (
            VisitSubclass[create_input.visit_subclass]
            if create_input.visit_subclass
            else None
        )
        study_visit_vo = StudyVisitVO(
            uid=self.repo.generate_uid(),
            visit_sublabel_reference=create_input.visit_sublabel_reference,
            consecutive_visit_group=create_input.consecutive_visit_group,
            show_visit=create_input.show_visit,
            visit_window_min=create_input.min_visit_window_value,
            visit_window_max=create_input.max_visit_window_value,
            window_unit_uid=create_input.visit_window_unit_uid,
            window_unit_object=window_unit_object,
            time_unit_object=time_unit_object,
            description=create_input.description,
            start_rule=create_input.start_rule,
            end_rule=create_input.end_rule,
            visit_contact_mode=StudyVisitContactMode[
                create_input.visit_contact_mode_uid
            ],
            epoch_allocation=(
                StudyVisitEpochAllocation[create_input.epoch_allocation_uid]
                if create_input.epoch_allocation_uid
                else None
            ),
            visit_type=StudyVisitType[create_input.visit_type_uid],
            start_date=datetime.datetime.now(datetime.timezone.utc),
            author_id=self.author,
            author_username=UserInfoService().get_author_username_from_id(
                user_id=self.author
            ),
            status=StudyStatus.DRAFT,
            day_unit_object=day_unit_object,
            week_unit_object=week_unit_object,
            epoch_connector=epoch,
            visit_class=visit_class,
            visit_subclass=visit_subclass if create_input.visit_subclass else None,
            is_global_anchor_visit=create_input.is_global_anchor_visit,
            is_soa_milestone=create_input.is_soa_milestone,
            visit_number=self.derive_visit_number(visit_class=visit_class),
            visit_order=self.derive_visit_number(visit_class=visit_class),
            repeating_frequency=(
                StudyVisitRepeatingFrequency[create_input.repeating_frequency_uid]
                if create_input.repeating_frequency_uid
                else None
            ),
        )
        if study_visit_vo.visit_class not in [
            VisitClass.NON_VISIT,
            VisitClass.UNSCHEDULED_VISIT,
            VisitClass.SPECIAL_VISIT,
        ]:
            missing_fields = []
            if create_input.time_unit_uid is None:
                missing_fields.append("time_unit_uid")
            if create_input.time_reference_uid is None:
                missing_fields.append("time_reference_uid")
            if create_input.time_value is None:
                missing_fields.append("time_value")
            ValidationException.raise_if(
                missing_fields,
                msg=f"The following fields are missing '{missing_fields}' for the Visit with Visit Class '{visit_class.value}'.",
            )
            study_visit_vo.timepoint = self._create_timepoint_simple_concept(
                study_visit_input=create_input
            )

            if study_visit_vo.visit_class == visit_class.MANUALLY_DEFINED_VISIT:
                study_visit_vo.visit_number = create_input.visit_number
                study_visit_vo.vis_unique_number = create_input.unique_visit_number
                study_visit_vo.vis_short_name = create_input.visit_short_name
                study_visit_vo.visit_name_sc = self._create_visit_name_simple_concept(
                    visit_name=create_input.visit_name
                )
            elif (
                study_visit_vo.visit_class != visit_class.MANUALLY_DEFINED_VISIT
                and any(
                    [
                        create_input.visit_number,
                        create_input.unique_visit_number,
                        create_input.visit_short_name,
                        create_input.visit_name,
                    ]
                )
            ):
                raise exceptions.ValidationException(
                    msg="Only Manually defined visit can specify visit_number, unique_visit_number, visit_short_name or visit_name properties."
                )
        return study_visit_vo

    def synchronize_visit_numbers(
        self, ordered_visits: list[Any], start_index_to_synchronize: int
    ):
        """
        Fixes the visit number if some visit was added in between of others or some of the visits were removed, edited.
        :param ordered_visits:
        :param start_index_to_synchronize:
        :return:
        """
        for visit in ordered_visits[start_index_to_synchronize:]:
            # Manually defined visits have explicitly specified order properties
            if visit.visit_class != VisitClass.MANUALLY_DEFINED_VISIT:
                self.assign_props_derived_from_visit_number(study_visit=visit)
                self.repo.save(visit)

    def assign_props_derived_from_visit_number(self, study_visit: StudyVisitVO):
        """
        Assigns some properties of StudyVisitVO that are derived from Visit Number.
        Visit Number property is not assigned when we create StudyVisitVO.
        It's done later as we need to derive VisitNumber from the order of given Visit in a sequence of all Study Visits.
        This is why we need to initialize some of the properties later then creation of StudyVisitVO.
        :param study_visit:
        :return:
        """
        study_visit.visit_name_sc = self._create_visit_name_simple_concept(
            visit_name=study_visit.derive_visit_name()
        )

    def assign_props_derived_from_visit_absolute_timing(
        self, study_visit_vo: StudyVisitVO
    ):
        """
        Assigns some properties of StudyVisitVO that are derived by the absolute timing of a given StudyVisit.
        The absolute timing can be known after Visits are set in the schedule and we assign Anchor Visits if given Visit anchors the other one.
        """
        if study_visit_vo.visit_class not in [
            VisitClass.NON_VISIT,
            VisitClass.UNSCHEDULED_VISIT,
            VisitClass.SPECIAL_VISIT,
        ]:
            study_visit_vo.study_day = self._create_numeric_value_simple_concept(
                value=study_visit_vo.derive_study_day_number(),
                numeric_value_type=NumericValueType.STUDY_DAY,
            )
            study_visit_vo.study_duration_days = (
                self._create_numeric_value_simple_concept(
                    value=study_visit_vo.derive_study_duration_days_number(),
                    numeric_value_type=NumericValueType.STUDY_DURATION_DAYS,
                )
            )
            study_visit_vo.study_week = self._create_numeric_value_simple_concept(
                value=study_visit_vo.derive_study_week_number(),
                numeric_value_type=NumericValueType.STUDY_WEEK,
            )
            study_visit_vo.study_duration_weeks = (
                self._create_numeric_value_simple_concept(
                    value=study_visit_vo.derive_study_duration_weeks_number(),
                    numeric_value_type=NumericValueType.STUDY_DURATION_WEEKS,
                )
            )
            study_visit_vo.week_in_study = self._create_numeric_value_simple_concept(
                value=study_visit_vo.derive_week_in_study_number(),
                numeric_value_type=NumericValueType.WEEK_IN_STUDY,
            )

    @db.transaction
    def create(self, study_uid: str, study_visit_input: StudyVisitCreateInput):
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid)

        epoch = self._repos.study_epoch_repository.find_by_uid(
            uid=study_visit_input.study_epoch_uid, study_uid=study_uid
        )
        study_visit = self._from_input_values(study_visit_input, epoch)
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        self._validate_visit(
            study_visit_input,
            study_visit,
            timeline,
            create=True,
            study_visits=study_visits,
        )
        self.assign_props_derived_from_visit_number(study_visit=study_visit)
        self.assign_props_derived_from_visit_absolute_timing(study_visit_vo=study_visit)
        added_item = self.repo.save(study_visit, create=True)

        timeline.add_visit(added_item)

        ordered_visits = timeline.ordered_study_visits
        # if added item is not last in ordered_study_visits, then we have to synchronize Visit Numbers
        if added_item.uid != ordered_visits[-1].uid:
            self.synchronize_visit_numbers(
                ordered_visits=ordered_visits,
                start_index_to_synchronize=int(added_item.visit_number),
            )
        return self._transform_all_to_response_model(added_item)

    @db.transaction
    def preview(self, study_uid: str, study_visit_input: StudyVisitCreateInput):
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid)

        epoch = self._repos.study_epoch_repository.find_by_uid(
            uid=study_visit_input.study_epoch_uid, study_uid=study_uid
        )
        study_visit = self._from_input_values(study_visit_input, epoch)
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        self._validate_visit(
            study_visit_input, study_visit, timeline, create=True, preview=True
        )

        study_visit.uid = "preview"
        timeline.add_visit(study_visit)
        self.assign_props_derived_from_visit_absolute_timing(study_visit_vo=study_visit)
        return self._transform_all_to_response_model(study_visit)

    @db.transaction
    def edit(
        self,
        study_uid: str,
        study_visit_uid: str,
        study_visit_input: StudyVisitEditInput,
    ):
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid)
        study_visit = self.repo.find_by_uid(study_uid=study_uid, uid=study_visit_uid)

        epoch = self._repos.study_epoch_repository.find_by_uid(
            uid=study_visit_input.study_epoch_uid, study_uid=study_uid
        )
        updated_visit = self._from_input_values(study_visit_input, epoch)
        update_dict = {
            k: v
            for k, v in dataclasses.asdict(updated_visit).items()
            if k not in ["uid"]
        }
        update_dict["time_unit_object"] = updated_visit.time_unit_object
        update_dict["window_unit_object"] = updated_visit.window_unit_object
        update_dict["day_unit_object"] = updated_visit.day_unit_object
        update_dict["week_unit_object"] = updated_visit.week_unit_object
        update_dict["timepoint"] = updated_visit.timepoint
        update_dict["study_day"] = updated_visit.study_day
        update_dict["study_duration_days"] = updated_visit.study_duration_days
        update_dict["study_duration_weeks"] = updated_visit.study_duration_weeks
        update_dict["week_in_study"] = updated_visit.week_in_study
        update_dict["study_week"] = updated_visit.study_week
        update_dict["visit_name_sc"] = updated_visit.visit_name_sc

        new_study_visit = dataclasses.replace(study_visit, **update_dict)
        new_study_visit.epoch_connector = epoch

        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        timeline.update_visit(new_study_visit)

        self._validate_visit(study_visit_input, new_study_visit, timeline, create=False)

        ordered_visits = timeline.ordered_study_visits

        # If Visit Number was edited, then we have to synchronize the Visit Numbers in the database
        if study_visit.visit_number != new_study_visit.visit_number:
            if new_study_visit.visit_number < study_visit.visit_number:
                start_index_to_sync = int(new_study_visit.visit_number) - 1
            else:
                start_index_to_sync = int(study_visit.visit_number) - 1
            self.synchronize_visit_numbers(
                ordered_visits=ordered_visits,
                start_index_to_synchronize=start_index_to_sync,
            )
        self.assign_props_derived_from_visit_absolute_timing(
            study_visit_vo=new_study_visit
        )
        self.assign_props_derived_from_visit_number(study_visit=new_study_visit)

        self.repo.save(new_study_visit)

        return self._transform_all_to_response_model(new_study_visit)

    @db.transaction
    def delete(self, study_uid: str, study_visit_uid: str):
        study_visit = self.repo.find_by_uid(study_uid=study_uid, uid=study_visit_uid)
        BusinessLogicException.raise_if(
            study_visit.status != StudyStatus.DRAFT,
            msg="Cannot delete visits non DRAFT status",
        )

        subvisits_references = self.repo.find_all_visits_referencing_study_visit(
            study_visit_uid=study_visit_uid
        )

        BusinessLogicException.raise_if(
            subvisits_references,
            msg=f"The Visit can't be deleted as other visits ({[x.short_visit_label for x in subvisits_references]}) are referencing this Visit",
        )

        # add check if visits that we want to group are the same
        schedules_service = StudyActivityScheduleService()

        # Load aggregate
        study_activity_schedules = (
            schedules_service.get_all_schedules_for_specific_visit(
                study_uid=study_uid, study_visit_uid=study_visit.uid
            )
        )
        for study_activity_schedule in study_activity_schedules:
            self._repos.study_activity_schedule_repository.delete(
                study_uid,
                study_activity_schedule.study_activity_schedule_uid,
                self.author,
            )

        study_visit.delete()

        self.repo.save(study_visit)

        study_visits = self.repo.find_all_visits_by_study_uid(study_uid)
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        ordered_visits = timeline.ordered_study_visits

        # we want to synchronize numbers if we have more than one visit
        if len(ordered_visits) > 0:
            # After removing specific visit if it was not the last visit,
            # we have to synchronize the Visit Numbers to fill in the gap
            if study_visit.uid != ordered_visits[-1].uid:
                self.synchronize_visit_numbers(
                    ordered_visits=ordered_visits,
                    start_index_to_synchronize=int(study_visit.visit_number) - 1,
                )

    @db.transaction
    def get_consecutive_groups(self, study_uid: str):
        all_visits = self.repo.find_all_visits_by_study_uid(study_uid)
        groups = [
            visit.consecutive_visit_group
            for visit in all_visits
            if visit.consecutive_visit_group is not None
        ]
        groups_set = set(groups)
        return groups_set

    @db.transaction
    def audit_trail(
        self,
        visit_uid: str,
        study_uid: str,
    ) -> list[StudyVisitVersion]:
        all_versions = self.repo.get_all_versions(
            uid=visit_uid,
            study_uid=study_uid,
        )

        # Extract start dates from the selection history
        start_dates = [history.start_date for history in all_versions]

        # Extract effective dates for each version based on the start dates
        effective_dates = self._extract_multiple_version_study_standards_effective_date(
            study_uid=study_uid, list_of_start_dates=start_dates
        )

        selection_history: list[StudyVisit] = []
        previous_effective_date = None
        for study_visit_version, effective_date in zip(all_versions, effective_dates):
            # The CTTerms should be only reloaded when effective_date changed for some of StudyVisits
            if effective_date != previous_effective_date:
                previous_effective_date = effective_date
                self.terms_at_specific_datetime = effective_date
                self._create_ctlist_map()
            selection_history.append(
                self._transform_all_to_response_history_model(
                    study_visit_version
                ).model_dump()
            )

        data = calculate_diffs(selection_history, StudyVisitVersion)
        return data

    @db.transaction
    def audit_trail_all_visits(
        self,
        study_uid: str,
    ) -> list[StudyVisitVersion]:
        data = []
        all_versions = self.repo.get_all_versions(
            study_uid=study_uid,
        )
        # Extract start dates from the selection history
        start_dates = [history.start_date for history in all_versions]

        effective_dates = self._extract_multiple_version_study_standards_effective_date(
            study_uid=study_uid, list_of_start_dates=start_dates
        )

        selection_history: list[StudyVisit] = []
        previous_effective_date = None
        all_versions_dict = {}
        for study_visit_version, effective_date in zip(all_versions, effective_dates):
            all_versions_dict.setdefault(study_visit_version.uid, []).append(
                (study_visit_version, effective_date)
            )

        for study_visit_versions_of_same_uid in all_versions_dict.values():
            for study_visit_version, effective_date in study_visit_versions_of_same_uid:
                # The CTTerms should be only reloaded when effective_date changed for some of StudyVisits
                if effective_date != previous_effective_date:
                    previous_effective_date = effective_date
                    self.terms_at_specific_datetime = effective_date
                    self._create_ctlist_map()
                selection_history.append(
                    self._transform_all_to_response_history_model(
                        study_visit_version
                    ).model_dump()
                )
            if not data:
                data = calculate_diffs(selection_history, StudyVisitVersion)
            else:
                data.extend(calculate_diffs(selection_history, StudyVisitVersion))
            # All StudyVisits of same uid are processed, the selection_history array is being prepared for the new uid
            selection_history.clear()

        return data

    @db.transaction
    def remove_visit_consecutive_group(
        self, study_uid: str, consecutive_visit_group: str
    ):
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid=study_uid)
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        ordered_visits = timeline.ordered_study_visits
        for visit in ordered_visits:
            if visit.consecutive_visit_group == consecutive_visit_group:
                visit.consecutive_visit_group = None
                self.repo.save(visit)

    @db.transaction
    def assign_visit_consecutive_group(
        self,
        study_uid: str,
        visits_to_assign: list[str],
        overwrite_visit_from_template: str | None = None,
    ) -> list[StudyVisit]:
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid=study_uid)
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        ordered_visits = timeline.ordered_study_visits

        # Sort Visits that are about to be grouped
        visits_to_assign.sort()
        # Get StudyVisitVOs for these visits that should be assigned to consecutive visit group
        visits_to_be_assigned = [
            study_visit
            for study_visit in ordered_visits
            if study_visit.uid in visits_to_assign
        ]
        found_visit_uids = [study_visit.uid for study_visit in visits_to_be_assigned]
        ValidationException.raise_if(
            len(visits_to_assign) != len(found_visit_uids),
            msg=f"The following Visits were not found {set(visits_to_assign)- set(found_visit_uids)}",
        )

        # Get visit short labels to derive the consecutive visit group name
        visits_short_labels = [
            visit.visit_short_name
            for visit in sorted(visits_to_be_assigned, key=lambda v: v.visit_order)
        ]
        consecutive_visit_group = f"{visits_short_labels[0]}-{visits_short_labels[-1]}"
        self._validate_consecutive_group_assignment(
            study_uid=study_uid,
            visits_to_be_assigned=visits_to_be_assigned,
            overwrite_visit_from_template=overwrite_visit_from_template,
        )
        updated_visits = []
        for visit in ordered_visits:
            if visit.uid in visits_to_assign:
                visit.consecutive_visit_group = consecutive_visit_group
                self.repo.save(visit)
                updated_visits.append(self._transform_all_to_response_model(visit))
        return updated_visits

    def _validate_consecutive_group_assignment(
        self,
        study_uid: str,
        visits_to_be_assigned: list[StudyVisitVO],
        overwrite_visit_from_template: str | None = None,
    ):
        visit_epochs = list(
            {visit.epoch_connector.epoch.term_uid for visit in visits_to_be_assigned}
        )
        BusinessLogicException.raise_if(
            len(visit_epochs) > 1,
            msg=f"Given Visits can't be collapsed as they exist in different Epochs {visit_epochs}",
        )
        visit_to_overwrite_from = None
        for visit in visits_to_be_assigned:
            if visit.uid == overwrite_visit_from_template:
                visit_to_overwrite_from = visit
        # check if none of visits that we want to assign to consecutive group is not having a group already
        for visit in visits_to_be_assigned:
            if visit.consecutive_visit_group:
                BusinessLogicException.raise_if_not(
                    overwrite_visit_from_template,
                    msg=f"Visit with UID '{visit.uid}' already has consecutive group {visit.consecutive_visit_group}",
                )

                # overwrite visit with props from overwrite_visit_from_template
                self._overwrite_visit_from_template(
                    visit=visit, visit_template=visit_to_overwrite_from
                )

        # check if we don't have a gap between visits that we are trying to assign to a consecutive visit group
        if len(visits_to_be_assigned) > 0:
            order = visits_to_be_assigned[0].visit_order
            for visit_to_assign in visits_to_be_assigned:
                BusinessLogicException.raise_if(
                    visit_to_assign.visit_order != order,
                    msg="To create visits group please select consecutive visits.",
                )
                order += 1

        # add check if visits that we want to group are the same
        schedules_service = StudyActivityScheduleService()
        if visit_to_overwrite_from:
            reference_visit = visit_to_overwrite_from
        else:
            reference_visit = visits_to_be_assigned[0]
        reference_visit_study_activities = {
            schedule.study_activity_uid
            for schedule in schedules_service.get_all_schedules_for_specific_visit(
                study_uid=study_uid, study_visit_uid=reference_visit.uid
            )
            if schedule.study_activity_uid is not None
        }
        for visit in visits_to_be_assigned:
            other_visit_study_activities = {
                schedule.study_activity_uid
                for schedule in schedules_service.get_all_schedules_for_specific_visit(
                    study_uid=study_uid, study_visit_uid=visit.uid
                )
                if schedule.study_activity_uid is not None
            }
            are_visits_the_same = reference_visit.compare_cons_group_equality(
                other_visit=visit,
            )
            are_schedules_the_same = set(reference_visit_study_activities) == set(
                other_visit_study_activities
            )
            # if not are_visits_the_same:
            BusinessLogicException.raise_if_not(
                are_visits_the_same,
                msg=f"Visit with Name '{reference_visit.visit_name}' is not the same as {visit.visit_name}",
            )
            if not are_schedules_the_same:
                VisitsAreNotEqualException.raise_if_not(
                    overwrite_visit_from_template,
                    msg=f"Visit with Name '{reference_visit.visit_name}' has different schedules assigned than {visit.visit_name}",
                )
                # overwrite
                self._overwrite_visit_from_template(
                    visit=visit, visit_template=visit_to_overwrite_from
                )

    def _overwrite_visit_from_template(self, visit, visit_template):
        schedules_service = StudyActivityScheduleService()

        # remove old activity schedules
        for schedule in schedules_service.get_all_schedules_for_specific_visit(
            study_uid=visit.study_uid, study_visit_uid=visit.uid
        ):
            self._repos.study_activity_schedule_repository.delete(
                study_uid=visit.study_uid,
                selection_uid=schedule.study_activity_schedule_uid,
                author_id=self.author,
            )

        # copy activity schedules from the visit to overwrite
        for schedule in schedules_service.get_all_schedules_for_specific_visit(
            study_uid=visit_template.study_uid, study_visit_uid=visit_template.uid
        ):
            self._repos.study_activity_schedule_repository.save(
                schedules_service._from_input_values(
                    study_uid=visit.study_uid,
                    schedule_input=StudyActivityScheduleCreateInput(
                        study_activity_uid=schedule.study_activity_uid,
                        study_visit_uid=visit.uid,
                    ),
                ),
                self.author,
            )
        self._repos.study_visit_repository.save(visit)
