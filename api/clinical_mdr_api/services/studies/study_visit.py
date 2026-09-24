import dataclasses
import datetime
from typing import Any

from neomodel import Q, db
from neomodel.sync_.match import Path

from clinical_mdr_api.domain_repositories._utils.helpers import (
    acquire_write_lock_study_value,
)
from clinical_mdr_api.domain_repositories.models._utils import ListDistinct
from clinical_mdr_api.domain_repositories.models.study_visit import (
    StudyVisit as StudyVisitNeoModel,
)
from clinical_mdr_api.domain_repositories.models.study_visit import (
    StudyVisitGroup,
)
from clinical_mdr_api.domain_repositories.study_selections.study_visit_repository import (
    StudyVisitRepository,
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
    StudyEpochVO,
    TimelineAR,
)
from clinical_mdr_api.domains.study_selections.study_visit import (
    NumericValue,
    StudyVisitHistoryVO,
    StudyVisitVO,
    TextValue,
    TimePoint,
    VisitGroup,
    VisitGroupFormat,
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
    StudyVisitDetailed,
    StudyVisitEditInput,
)
from clinical_mdr_api.models.study_selections.study_visit import (
    StudyVisitGroup as StudyVisitGroupModel,
)
from clinical_mdr_api.models.study_selections.study_visit import (
    StudyVisitLite,
    StudyVisitVersion,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    ensure_transaction,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.services.studies.study_selection_base import StudySelectionMixin
from clinical_mdr_api.services.user_info import UserInfoService
from common import exceptions
from common.auth.user import user
from common.config import settings
from common.exceptions import (
    BusinessLogicException,
    NotFoundException,
    ValidationException,
    VisitsAreNotEqualException,
)
from common.telemetry import trace_calls
from common.utils import TimeUnit, VisitClass, VisitSubclass, convert_to_datetime


class StudyVisitService(StudySelectionMixin):

    @trace_calls
    def __init__(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        load_terms: bool = True,
    ):
        self._repos = MetaRepository()
        self.repo = self._repos.study_visit_repository
        self.author = user().id()

        self.check_if_study_exists(study_uid=study_uid)

        if load_terms:
            self.terms_at_specific_datetime = (
                self.get_study_standard_version_ct_terms_datetime(
                    study_uid=study_uid,
                    study_value_version=study_value_version,
                )
            )

            self.update_ctterm_maps(self.terms_at_specific_datetime)

            self._day_unit, self._week_unit = self.repo.get_day_week_units()

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
                item
                for item in resp
                if item.time_reference_name != settings.previous_visit_name
            ]

        resp.sort(key=lambda time_reference: time_reference.time_reference_name)

        return resp

    def _transform_all_to_response_history_model(
        self, visit: StudyVisitHistoryVO
    ) -> StudyVisitDetailed:
        # For audit trail return model we shouldn't derive properties based on their position in the timeline as we don't know how the visit timeline looked for past visit versions
        # Due to this we have to take the values that are derived based on timeline directly from database representation
        self.update_ct_term_properties_of_study_visit(visit)
        study_visit: StudyVisitDetailed = (
            StudyVisitDetailed.transform_to_response_model(visit)
        )
        study_visit.change_type = visit.change_type
        study_visit.end_date = convert_to_datetime(visit.end_date)

        return study_visit

    @staticmethod
    @trace_calls
    def _get_all_visits(
        study_uid: str, study_value_version: str | None = None
    ) -> list[StudyVisitVO]:
        study_visits = StudyVisitRepository.find_all_visits_by_study_uid(
            study_uid=study_uid, study_value_version=study_value_version
        )
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        assert study_visits is not None
        return timeline.ordered_study_visits

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
            StudyVisitNeoModel.nodes.traverse(
                Path("has_visit_name__has_latest_value", include_rels_in_return=False),
                Path(
                    "has_visit_type__has_selected_term__has_name_root__has_latest_value",
                    include_rels_in_return=False,
                ),
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
            StudyVisitNeoModel.nodes.traverse(
                "has_visit_name__has_latest_value",
                "has_visit_type__has_selected_term__has_name_root__has_latest_value",
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
            StudyVisitNeoModel.nodes.traverse(
                "has_visit_name__has_latest_value",
                "has_visit_type__has_selected_term__has_name_root__has_latest_value",
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

    def get_study_visits_for_specific_activity_instance(
        self, study_uid: str, study_activity_instance_uid: str
    ) -> list[SimpleStudyVisit]:
        return [
            SimpleStudyVisit.model_validate(sv_node)
            for sv_node in ListDistinct(
                StudyVisitNeoModel.nodes.traverse(
                    Path(
                        "has_study_visit__latest_value",
                        include_rels_in_return=False,
                        include_nodes_in_return=False,
                    ),
                    Path(
                        "has_study_activity_schedule__study_value__latest_value",
                        include_rels_in_return=False,
                        include_nodes_in_return=False,
                    ),
                    Path(
                        "has_study_activity_schedule__study_activity__study_activity_has_study_activity_instance",
                        include_rels_in_return=False,
                        include_nodes_in_return=False,
                    ),
                    Path(
                        "has_visit_name__has_latest_value",
                        include_rels_in_return=False,
                    ),
                    Path(
                        "has_visit_type__has_selected_term__has_name_root__has_latest_value",
                        include_rels_in_return=False,
                    ),
                )
                .unique_variables("has_study_activity_schedule")
                .filter(
                    has_study_visit__latest_value__uid=study_uid,  # Visit in study
                    has_study_activity_schedule__study_value__latest_value__uid=study_uid,  # With schedule in study
                    has_study_activity_schedule__study_activity__has_study_activity__latest_value__uid=study_uid,
                    # With activity in study
                    has_study_activity_schedule__study_activity__study_activity_has_study_activity_instance__uid=study_activity_instance_uid,
                    # And activity is parent of instance
                )
                .order_by("visit_number")
                .resolve_subgraph()
            ).distinct()
        ]

    @staticmethod
    @trace_calls
    def get_all_visits(
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_value_version: str | None = None,
        derive_props_based_on_timeline: bool = False,
        lite: bool = False,
    ) -> GenericFilteringReturn[StudyVisitLite | StudyVisit]:
        StudyService.check_if_study_uid_and_version_exists(
            study_uid, study_value_version
        )

        if lite:
            dicts = StudyVisitRepository.list_all_visits_by_study_uid(
                study_uid=study_uid, study_value_version=study_value_version
            )
            visits = [StudyVisitLite(**d) for d in dicts]

        else:
            visit_vos = StudyVisitService._get_all_visits(
                study_uid, study_value_version=study_value_version
            )
            visits = [
                StudyVisit.transform_to_response_model(
                    visit,
                    study_value_version=study_value_version,
                    derive_props_based_on_timeline=derive_props_based_on_timeline,
                )
                for visit in visit_vos
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

    @classmethod
    @trace_calls
    def get_distinct_values_for_header(
        cls,
        study_uid: str,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
        study_value_version: str | None = None,
    ):
        all_items = cls.get_all_visits(
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

    def get_all_references(self, study_uid: str) -> list[StudyVisit]:
        visits = self._get_all_visits(study_uid)
        result = []
        sponsor_names = [
            timeref.sponsor_preferred_name
            for timeref in self.study_visit_time_references_by_uid.values()
        ]
        for visit in visits:
            if visit.visit_type.sponsor_preferred_name in sponsor_names:
                result.append(StudyVisit.transform_to_response_model(visit))
        return result

    @staticmethod
    def find_by_uid(
        study_uid: str,
        uid: str,
        study_value_version: str | None = None,
        derive_props_based_on_timeline: bool = False,
    ) -> StudyVisit | None:
        """
        finds latest version of visit by uid, status ans version
        if user do not give status and version - will be overwritten by DRAFT
        """

        # All visits are required for building the TimelineAR which sets some properties on StudyVisitVOs
        all_study_visits = StudyVisitRepository.find_all_visits_by_study_uid(
            study_uid=study_uid, study_value_version=study_value_version
        )
        exceptions.NotFoundException.raise_if_not(all_study_visits, "Study visits")

        # Find StudyVisitVO by uid in TimelineAR._generate_timeline() results, which sets properties on StudyVisitVOs
        timeline = TimelineAR(study_uid=study_uid, _visits=all_study_visits)
        study_visit: StudyVisitVO | None = next(
            (sv for sv in timeline.ordered_study_visits if sv.uid == uid), None
        )
        if study_visit is None:
            raise exceptions.NotFoundException("Study Visit", uid)

        return StudyVisit.transform_to_response_model(
            study_visit, derive_props_based_on_timeline=derive_props_based_on_timeline
        )

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
        if visit_vo.visit_class != VisitClass.SPECIAL_VISIT:
            error_dict = {}
            chronological_order_dict = {}
            for idx, visit in enumerate(ordered_visits):
                if (
                    visit_vo.uid != visit.uid
                    and visit.visit_class != VisitClass.SPECIAL_VISIT
                ):
                    exclude_from_comparison = (
                        (
                            visit_vo.visit_subclass
                            == VisitSubclass.ANCHOR_VISIT_IN_GROUP_OF_SUBV
                            and visit.visit_subclass
                            == VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
                        )
                        or visit_vo.visit_subclass
                        == VisitSubclass.ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
                    )
                    if (
                        visit_vo.visit_number == visit.visit_number
                        and not exclude_from_comparison
                    ):
                        error_dict["visit number"] = visit_vo.visit_number
                    if visit_vo.unique_visit_number == visit.unique_visit_number:
                        error_dict["unique visit number"] = visit_vo.unique_visit_number
                    if (
                        visit_vo.visit_name == visit.visit_name
                        and not exclude_from_comparison
                    ):
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
        visit_input: StudyVisitCreateInput | StudyVisitEditInput,
        visit_vo: StudyVisitVO,
        timeline: TimelineAR,
        create: bool = True,
        preview: bool = False,
    ):
        visit_group_name = (
            visit_vo.study_visit_group.group_name if visit_vo.study_visit_group else ""
        )
        BusinessLogicException.raise_if(
            not create and visit_vo.study_visit_group is not None,
            msg=f"The study visit can't be edited as it is part of visit group {visit_group_name}. The visit group should be uncollapsed first.",
        )
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
            for timeref in self.study_visit_time_references_by_uid.values()
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
                != settings.global_anchor_visit_name.lower(),
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
                    != settings.global_anchor_visit_name
                )
                and visit_vo.visit_type.sponsor_preferred_name
                != settings.study_visit_type_information_visit,
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
            reference_name = self.study_visit_time_references_by_uid[
                visit_input.time_reference.term_uid
            ]
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
                    settings.previous_visit_name.lower(),
                    settings.global_anchor_visit_name.lower(),
                    settings.anchor_visit_in_visit_group.lower(),
                ],
                msg=f"Time reference of type '{visit_vo.timepoint.visit_timereference.sponsor_preferred_name}' wasn't used by previous visits as visit type.",
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

            ordered_visits = timeline.ordered_study_visits
            if create:
                timeline.add_visit(visit_vo)
                ordered_visits = timeline.ordered_study_visits
                # derive timing properties in the end when all subvisits are set
                # for the Visit that is currently being created timepoint will be filled but study_day will be empty as it's
                # being assigned afterwards
                if visit_vo.timepoint and visit_vo.study_day:
                    visit_vo.study_day.value = visit_vo.derive_study_day_number()
                    visit_vo.study_duration_days.value = (
                        visit_vo.derive_study_duration_days_number()
                    )
                    visit_vo.study_week.value = visit_vo.derive_study_week_number()
                    visit_vo.study_duration_weeks.value = (
                        visit_vo.derive_study_duration_weeks_number()
                    )
                    visit_vo.week_in_study.value = (
                        visit_vo.derive_week_in_study_number()
                    )

            self._validate_derived_properties(
                visit_vo=visit_vo, ordered_visits=ordered_visits
            )
            # Perform validation check if visit is not being placed in the middle of Visit group, grouped in the range way
            for index, visit in enumerate(ordered_visits):
                if visit.uid == visit_vo.uid:
                    if index > 0:
                        previous_visit = ordered_visits[index - 1]
                    else:
                        previous_visit = None
                    if index < len(ordered_visits) - 1:
                        next_visit = ordered_visits[index + 1]
                    else:
                        next_visit = None
                    break

            if (
                previous_visit
                and next_visit
                and previous_visit.study_visit_group
                and next_visit.study_visit_group
                and previous_visit.study_visit_group.uid
                == next_visit.study_visit_group.uid
            ):
                group = previous_visit.study_visit_group
                if group.group_format == VisitGroupFormat.RANGE.value:
                    raise ValidationException(
                        msg=f"The visit can't be placed in the middle of Visit Group '{group.group_name}' which is grouped in the Range way. Uncollapse the '{group.group_name}' Visit Group first."
                    )

            # Perform check for timing uniqueness excluding Special Visits.
            # There can exist 2 visits with the same timing unless timing is 0, then there can exist only one such visit
            if visit_vo.visit_class != VisitClass.SPECIAL_VISIT:
                all_visit_timings = [
                    visit.get_absolute_duration()
                    for visit in ordered_visits
                    if visit.uid != visit_vo.uid
                    and visit.visit_class != VisitClass.SPECIAL_VISIT
                ]
                existing_visits_with_same_timing = all_visit_timings.count(
                    visit_vo.get_absolute_duration()
                )
                exceptions.AlreadyExistsException.raise_if(
                    existing_visits_with_same_timing > 0
                    and visit_vo.get_absolute_duration() == 0,
                    msg=f"There already exists a visit with timing set to {visit_vo.timepoint.visit_value}",
                )

            if create:
                timeline.remove_visit(visit_vo)

        ValidationException.raise_if(
            visit_input.visit_contact_mode.term_uid
            not in self.study_visit_contact_modes_by_uid,
            msg=f"CT Term with UID '{visit_input.visit_contact_mode.term_uid}' is not a valid Visit Contact Mode term.",
        )

        visits_classes = [
            visit.visit_class for visit in timeline._visits if visit.uid != visit_vo.uid
        ]
        ValidationException.raise_if(
            not preview
            and visit_input.visit_class == VisitClass.NON_VISIT
            and VisitClass.NON_VISIT in visits_classes,
            msg=f"There's already and exists Non Visit in Study {visit_vo.study_uid}",
        )
        ValidationException.raise_if(
            not preview
            and visit_input.visit_class == VisitClass.UNSCHEDULED_VISIT
            and VisitClass.UNSCHEDULED_VISIT in visits_classes,
            msg=f"There's already and exists an Unscheduled Visit in Study {visit_vo.study_uid}",
        )

    def _get_sponsor_library_vo(
        self, library_name: str = settings.sponsor_library_name
    ):
        lib = self._repos.library_repository.find_by_name(name=library_name)
        return LibraryVO.from_input_values_2(
            library_name=lib.library_name,
            is_library_editable_callback=lambda _: lib.is_editable,
        )

    def _create_visit_name_simple_concept(self, visit_name: str | None):
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
        return TextValue(uid=visit_name_ar.uid, name=visit_name_ar.name)

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
        self, study_visit_input: StudyVisitCreateInput | StudyVisitEditInput
    ):
        if study_visit_input.time_value is None:
            raise exceptions.BusinessLogicException(
                msg="Time value is required for creating a timepoint."
            )

        if study_visit_input.time_unit_uid is None:
            raise exceptions.BusinessLogicException(
                msg="Time unit UID is required for creating a timepoint."
            )

        if study_visit_input.time_reference is None:
            raise exceptions.BusinessLogicException(
                msg="Time reference UID is required for creating a timepoint."
            )

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
                time_reference_uid=study_visit_input.time_reference.term_uid,
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
            visit_timereference=self.study_visit_time_references_by_uid[
                study_visit_input.time_reference.term_uid
            ],
            time_unit_uid=study_visit_input.time_unit_uid,
            visit_value=study_visit_input.time_value,
        )
        return timepoint_object

    def derive_visit_number(self, visit_class: VisitClass | None):
        if visit_class == VisitClass.NON_VISIT:
            return settings.non_visit_number
        if visit_class == VisitClass.UNSCHEDULED_VISIT:
            return settings.unscheduled_visit_number
        return 1

    def _from_input_values(
        self,
        create_input: StudyVisitCreateInput | StudyVisitEditInput,
        epoch: StudyEpochVO | None,
        study_uid: str | None = None,
    ):
        unit_repository = self._repos.unit_definition_repository
        if create_input.time_unit_uid:
            req_time_unit_ar: UnitDefinitionAR = unit_repository.find_by_uid_2(
                create_input.time_unit_uid
            )
            if req_time_unit_ar is None:
                raise exceptions.ValidationException(
                    msg=f"Time unit with UID '{create_input.time_unit_uid}' does not exist."
                )
            req_time_unit = req_time_unit_ar.concept_vo
        else:
            req_time_unit = None

        if create_input.visit_window_unit_uid:
            window_time_unit_ar: UnitDefinitionAR = unit_repository.find_by_uid_2(
                create_input.visit_window_unit_uid
            )
            if window_time_unit_ar is None:
                raise exceptions.ValidationException(
                    msg=f"Visit window unit with UID '{create_input.visit_window_unit_uid}' does not exist."
                )
            window_time_unit = window_time_unit_ar.concept_vo
            if window_time_unit.name is None:
                raise exceptions.ValidationException(
                    msg="Visit window unit UID is required for creating a visit window."
                )
            if window_time_unit.conversion_factor_to_master is None:
                raise exceptions.ValidationException(
                    msg="Visit window unit conversion factor to master is required for creating a visit window."
                )
            window_unit_object = TimeUnit(
                name=window_time_unit.name,
                conversion_factor_to_master=window_time_unit.conversion_factor_to_master,
            )
        else:
            window_unit_object = None

        if req_time_unit and req_time_unit.name:
            if req_time_unit.conversion_factor_to_master is None:
                raise exceptions.ValidationException(
                    msg="Time unit conversion factor to master is required for creating a visit."
                )
            time_unit_object = TimeUnit(
                name=req_time_unit.name,
                conversion_factor_to_master=req_time_unit.conversion_factor_to_master,
            )
        else:
            time_unit_object = None
        day_unit_object = TimeUnit(
            name="day",
            conversion_factor_to_master=self._day_unit.concept_vo.conversion_factor_to_master,
        )

        week_unit_object = TimeUnit(
            name="Week",
            conversion_factor_to_master=self._week_unit.concept_vo.conversion_factor_to_master,
        )
        visit_contact_mode = self.study_visit_contact_modes_by_uid.get(
            create_input.visit_contact_mode.term_uid
        )
        exceptions.ValidationException.raise_if_not(
            visit_contact_mode,
            msg=f"Visit contact mode '{create_input.visit_contact_mode.term_uid}' is invalid.",
        )
        visit_type = self.study_visit_types_by_uid.get(create_input.visit_type.term_uid)
        exceptions.ValidationException.raise_if_not(
            visit_type,
            msg=f"Visit type with UID '{create_input.visit_type.term_uid}' is not valid.",
        )
        start_rule: str | None
        if create_input.visit_class == VisitClass.NON_VISIT:
            start_rule = create_input.start_rule or settings.non_visit_start_rule
        elif create_input.visit_class == VisitClass.UNSCHEDULED_VISIT:
            start_rule = (
                create_input.start_rule or settings.unscheduled_visit_start_rule
            )
        else:
            start_rule = create_input.start_rule
        # Unscheduled and non-visits do not have window unit information
        if create_input.visit_class in (
            VisitClass.NON_VISIT,
            VisitClass.UNSCHEDULED_VISIT,
        ):
            window_unit_object = None
            visit_window_min = None
            visit_window_max = None
            window_unit_uid = None
        else:
            visit_window_min = create_input.min_visit_window_value
            visit_window_max = create_input.max_visit_window_value
            window_unit_uid = create_input.visit_window_unit_uid
        study_visit_vo = StudyVisitVO(
            uid=self.repo.generate_uid(),
            visit_sublabel_reference=create_input.visit_sublabel_reference,
            show_visit=create_input.show_visit,
            visit_window_min=visit_window_min,
            visit_window_max=visit_window_max,
            window_unit_uid=window_unit_uid,
            window_unit_object=window_unit_object,
            time_unit_object=time_unit_object,
            description=create_input.description,
            start_rule=start_rule,
            end_rule=create_input.end_rule,
            visit_contact_mode=visit_contact_mode,
            epoch_allocation=(
                self.study_visit_epoch_allocations_by_uid.get(
                    create_input.epoch_allocation.term_uid
                )
                if create_input.epoch_allocation
                else None
            ),
            visit_type=visit_type,
            start_date=datetime.datetime.now(datetime.timezone.utc),
            author_id=self.author,
            author_username=UserInfoService().get_author_username_from_id(
                user_id=self.author
            ),
            status=StudyStatus.DRAFT,
            day_unit_object=day_unit_object,
            week_unit_object=week_unit_object,
            epoch_connector=epoch,
            _study_uid=study_uid,
            visit_class=create_input.visit_class,
            visit_subclass=create_input.visit_subclass,
            is_global_anchor_visit=create_input.is_global_anchor_visit,
            is_soa_milestone=create_input.is_soa_milestone,
            visit_number=self.derive_visit_number(visit_class=create_input.visit_class),
            visit_order=self.derive_visit_number(visit_class=create_input.visit_class),
            repeating_frequency=(
                self.study_visit_repeating_frequencies_by_uid.get(
                    create_input.repeating_frequency_uid
                )
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
            if create_input.time_reference is None:
                missing_fields.append("time_reference")
            if create_input.time_value is None:
                missing_fields.append("time_value")
            ValidationException.raise_if(
                missing_fields,
                msg=f"The following fields are missing '{missing_fields}' for the Visit with Visit Class '{study_visit_vo.visit_class.value}'.",
            )
            study_visit_vo.timepoint = self._create_timepoint_simple_concept(
                study_visit_input=create_input
            )

            if study_visit_vo.visit_class == VisitClass.MANUALLY_DEFINED_VISIT:
                study_visit_vo.visit_number = create_input.visit_number  # type: ignore[assignment]
                study_visit_vo.vis_unique_number = create_input.unique_visit_number
                study_visit_vo.vis_short_name = create_input.visit_short_name
                study_visit_vo.visit_name_sc = self._create_visit_name_simple_concept(
                    visit_name=create_input.visit_name
                )
            elif (
                study_visit_vo.visit_class != VisitClass.MANUALLY_DEFINED_VISIT
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

    def _reconcile_visit_numbering(
        self,
        timeline: TimelineAR,
        skip: set[str | None] | None = None,
    ) -> None:
        """
        Re-derive numbering-related properties (visit_number, visit_order,
        vis_unique_number, vis_short_name, visit_name_sc) for every visit in
        the timeline and persist any visit whose stored value drifted from
        the value derived from its current position.

        This is the single entry point that replaces the previous
        index-based partial sync routines. It removes the need for each
        mutation method to know which other visits might have been affected
        by a change (e.g. cross-thresholds in sub-visit numbering, anchor
        visits whose own number depends on the size of their sub-visit
        group, downstream visits whose numbers shifted by one).

        :param timeline: TimelineAR built from the current set of study
            visits. The reconciliation iterates over ``ordered_study_visits``
            which guarantees the timeline has been freshly generated.
        :param skip: Optional set of visit UIDs to leave untouched. Callers
            pass the UID of a visit they have just persisted with up-to-date
            derived properties, to avoid an unnecessary re-save.
        """
        skip = skip or set()
        for visit in timeline.ordered_study_visits:
            if visit.uid in skip:
                continue
            # Manually defined visits have explicitly specified numbering
            # that is never derived from the timeline.
            if visit.visit_class == VisitClass.MANUALLY_DEFINED_VISIT:
                continue
            if not self._derived_numbering_drifted(visit):
                continue
            self.assign_props_derived_from_visit_number(study_visit=visit)
            self.repo.save(visit)

    @staticmethod
    def _derived_numbering_drifted(visit: StudyVisitVO) -> bool:
        """
        Return True if any persisted numbering-derived property differs from
        the value derived from the visit's current position in the timeline.
        """
        if visit.vis_unique_number != visit.unique_visit_number:
            return True
        if visit.vis_short_name != visit.visit_short_name:
            return True
        if (
            visit.visit_name_sc is None
            or visit.visit_name_sc.name != visit.derive_visit_name()
        ):
            return True
        return False

    def assign_props_derived_from_visit_number(self, study_visit: StudyVisitVO):
        """
        Assigns some properties of StudyVisitVO that are derived from Visit Number.
        Visit Number property is not assigned when we create StudyVisitVO.
        It's done later as we need to derive VisitNumber from the order of given Visit in a sequence of all Study Visits.
        This is why we need to initialize some of the properties later then creation of StudyVisitVO.
        :param study_visit:
        :return:
        """
        derived_name = study_visit.derive_visit_name()
        # Avoid hitting the simple-concept repository when the derived visit
        # name has not actually changed - which is the common case during
        # reconciliation.
        if (
            study_visit.visit_name_sc is None
            or study_visit.visit_name_sc.name != derived_name
        ):
            study_visit.visit_name_sc = self._create_visit_name_simple_concept(
                visit_name=derived_name
            )
        study_visit.vis_short_name = study_visit.visit_short_name
        study_visit.vis_unique_number = study_visit.unique_visit_number

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
            if (value := study_visit_vo.derive_study_day_number()) is not None:
                study_visit_vo.study_day = self._create_numeric_value_simple_concept(
                    value=value,
                    numeric_value_type=NumericValueType.STUDY_DAY,
                )
            if (
                value := study_visit_vo.derive_study_duration_days_number()
            ) is not None:
                study_visit_vo.study_duration_days = (
                    self._create_numeric_value_simple_concept(
                        value=value,
                        numeric_value_type=NumericValueType.STUDY_DURATION_DAYS,
                    )
                )
            if (value := study_visit_vo.derive_study_week_number()) is not None:
                study_visit_vo.study_week = self._create_numeric_value_simple_concept(
                    value=value,
                    numeric_value_type=NumericValueType.STUDY_WEEK,
                )
            if (
                value := study_visit_vo.derive_study_duration_weeks_number()
            ) is not None:
                study_visit_vo.study_duration_weeks = (
                    self._create_numeric_value_simple_concept(
                        value=value,
                        numeric_value_type=NumericValueType.STUDY_DURATION_WEEKS,
                    )
                )
            if (value := study_visit_vo.derive_week_in_study_number()) is not None:
                study_visit_vo.week_in_study = (
                    self._create_numeric_value_simple_concept(
                        value=value,
                        numeric_value_type=NumericValueType.WEEK_IN_STUDY,
                    )
                )

    @ensure_transaction(db)
    def create(self, study_uid: str, study_visit_input: StudyVisitCreateInput):
        acquire_write_lock_study_value(uid=study_uid)
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid)

        epoch = None
        if study_visit_input.study_epoch_uid:
            epoch = self._repos.study_epoch_repository.find_by_uid(
                uid=study_visit_input.study_epoch_uid, study_uid=study_uid
            )
        study_visit = self._from_input_values(
            study_visit_input, epoch, study_uid=study_uid
        )
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        self._validate_visit(
            study_visit_input,
            study_visit,
            timeline,
            create=True,
        )
        timeline.add_visit(study_visit)
        self.assign_props_derived_from_visit_number(study_visit=study_visit)
        self.assign_props_derived_from_visit_absolute_timing(study_visit_vo=study_visit)
        added_item = self.repo.save(study_visit, create=True)

        # Persist any drift caused by the new visit's insertion (downstream
        # visit numbers shifting, sub-visit numbering thresholds, anchor
        # numbers, etc.). The new visit is skipped because its derived
        # properties were just assigned from the correct post-insertion timeline.
        self._reconcile_visit_numbering(timeline, skip={study_visit.uid})

        return StudyVisit.transform_to_response_model(added_item)

    def update_ct_term_properties_of_study_visit(
        self, visit: StudyVisitVO
    ) -> StudyVisitVO:
        """
        Amends CTTerm related properties of study visit with value stored in dictionary for each CTTerm.
        """
        timepoint = visit.timepoint
        if timepoint:
            visit_timereference = self.study_visit_time_references_by_uid.get(
                timepoint.visit_timereference.term_uid
            )
            if visit_timereference is not None:
                timepoint.visit_timereference = visit_timereference

        if visit.epoch and visit.epoch.epoch:
            epoch = self.study_epoch_epochs_by_uid.get(visit.epoch.epoch.term_uid)
            if epoch is not None:
                visit.epoch_connector.epoch = epoch

        visit_type = self.study_visit_types_by_uid.get(visit.visit_type.term_uid)
        if visit_type is not None:
            visit.visit_type = visit_type

        visit_contact_mode = self.study_visit_contact_modes_by_uid.get(
            visit.visit_contact_mode.term_uid
        )
        if visit_contact_mode is not None:
            visit.visit_contact_mode = visit_contact_mode

        epoch_allocation_uid = getattr(visit.epoch_allocation, "term_uid", None)
        if epoch_allocation_uid:
            epoch_allocation = self.study_visit_epoch_allocations_by_uid.get(
                epoch_allocation_uid
            )
            if epoch_allocation is not None:
                visit.epoch_allocation = epoch_allocation

        repeating_frequency_uid = getattr(visit.repeating_frequency, "term_uid", None)
        if repeating_frequency_uid:
            repeating_frequency = self.study_visit_repeating_frequencies_by_uid.get(
                repeating_frequency_uid
            )
            if repeating_frequency is not None:
                visit.repeating_frequency = repeating_frequency

        return visit

    @ensure_transaction(db)
    def preview(self, study_uid: str, study_visit_input: StudyVisitCreateInput):
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid)

        epoch = None
        if study_visit_input.study_epoch_uid:
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
        self.assign_props_derived_from_visit_number(study_visit=study_visit)
        return StudyVisit.transform_to_response_model(study_visit)

    @ensure_transaction(db)
    def edit(
        self,
        study_uid: str,
        study_visit_uid: str,
        study_visit_input: StudyVisitEditInput,
    ):
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid)
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        acquire_write_lock_study_value(uid=study_uid)
        study_visit: StudyVisitVO | None = next(
            (sv for sv in timeline.ordered_study_visits if sv.uid == study_visit_uid),
            None,
        )
        if study_visit is None:
            raise exceptions.NotFoundException("Study Visit", study_visit_uid)

        epoch = None
        if study_visit_input.study_epoch_uid:
            epoch = self._repos.study_epoch_repository.find_by_uid(
                uid=study_visit_input.study_epoch_uid, study_uid=study_uid
            )
        updated_visit = self._from_input_values(
            study_visit_input, epoch, study_uid=study_uid
        )
        update_dict = {
            field.name: getattr(updated_visit, field.name)
            for field in dataclasses.fields(updated_visit)
            if field.name not in ["uid", "study_visit_group"]
        }

        # Preserve study_visit_group from original as it can't be modified in Edit flow
        new_study_visit = dataclasses.replace(
            study_visit, **update_dict, study_visit_group=study_visit.study_visit_group
        )
        new_study_visit.epoch_connector = epoch

        timeline.update_visit(new_study_visit)
        # Force the timeline to regenerate so that numbering-related fields
        # (visit_number, subvisit_number, special_visit_number, anchor_visit)
        # are recomputed for every visit - including new_study_visit - before
        # we derive and persist its name / short name / unique visit number.
        _ = timeline.ordered_study_visits

        self.assign_props_derived_from_visit_number(study_visit=new_study_visit)
        self.assign_props_derived_from_visit_absolute_timing(
            study_visit_vo=new_study_visit
        )
        self._validate_visit(study_visit_input, new_study_visit, timeline, create=False)
        self.repo.save(new_study_visit)

        # Persist any drift on other visits caused by this edit (visit order
        # changes, sub-visit threshold crossings, anchor renumbering, ...).
        # The edited visit was just saved with up-to-date derived properties,
        # so it is skipped to avoid a redundant write.
        self._reconcile_visit_numbering(timeline, skip={new_study_visit.uid})

        return StudyVisit.transform_to_response_model(new_study_visit)

    @ensure_transaction(db)
    def delete(self, study_uid: str, study_visit_uid: str):
        acquire_write_lock_study_value(uid=study_uid)
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid)
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        ordered_visits = timeline.ordered_study_visits
        study_visit: StudyVisitVO | None = None
        for visit in ordered_visits:
            if visit.uid == study_visit_uid:
                study_visit = visit
                break
        else:
            raise ValidationException(
                msg=f"StudyVisit with UID '{study_visit_uid}' doesn't exist in Study '{study_uid}'",
            )
        group_name = (
            study_visit.study_visit_group.group_name
            if study_visit.study_visit_group
            else ""
        )
        BusinessLogicException.raise_if(
            study_visit.study_visit_group is not None,
            msg=f"The study visit can't be deleted as it is part of visit group {group_name}. The visit group should be uncollapsed first.",
        )
        BusinessLogicException.raise_if(
            study_visit.status != StudyStatus.DRAFT,
            msg="Cannot delete visits non DRAFT status",
        )

        BusinessLogicException.raise_if(
            self.repo.was_visit_created_before_final_protocol_lock(
                study_uid=study_uid, study_visit_uid=study_visit_uid
            ),
            msg="The visit cannot be deleted because it was part of the study when it was locked for Final Protocol. It can be hidden in the SoA instead.",
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
        study_activity_schedules = schedules_service.get_all_schedules(
            study_uid=study_uid, study_visit_uid=study_visit.uid
        )
        for study_activity_schedule in study_activity_schedules:
            schedules_service.delete(
                study_uid,
                study_activity_schedule.study_activity_schedule_uid,
            )

        study_visit.delete()
        timeline.remove_visit(study_visit)
        self.repo.save(study_visit)

        # Persist any drift on the remaining visits caused by the removal
        # (downstream visit numbers shifting back, sub-visit threshold
        # transitions, anchor renumbering, ...).
        self._reconcile_visit_numbering(timeline)

    def get_consecutive_groups(self, study_uid: str) -> list[StudyVisitGroupModel]:
        all_visits = self.repo.find_all_visits_by_study_uid(study_uid)
        known_groups = set()
        study_visit_groups: list[StudyVisitGroupModel] = []

        for visit in all_visits:
            if (study_visit_group := visit.study_visit_group) is not None:
                if study_visit_group.uid not in known_groups:
                    known_groups.add(study_visit_group.uid)
                    study_visit_groups.append(
                        StudyVisitGroupModel(
                            uid=study_visit_group.uid,
                            group_name=study_visit_group.group_name,
                        )
                    )

        return study_visit_groups

    @trace_calls
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

        selection_history = []
        previous_effective_date = None
        for study_visit_version, effective_date in zip(all_versions, effective_dates):
            # The CTTerms should be only reloaded when effective_date changed for some of StudyVisits
            if effective_date != previous_effective_date:
                previous_effective_date = effective_date
                self.terms_at_specific_datetime = effective_date
                self.update_ctterm_maps(self.terms_at_specific_datetime)
            selection_history.append(
                self._transform_all_to_response_history_model(
                    study_visit_version
                ).model_dump()
            )

        data = calculate_diffs(selection_history, StudyVisitVersion)
        return data

    @trace_calls
    def audit_trail_all_visits(
        self,
        study_uid: str,
    ) -> list[StudyVisitVersion]:
        data: list[StudyVisitVersion] = []
        all_versions = self.repo.get_all_versions(
            study_uid=study_uid,
        )
        # Extract start dates from the selection history
        start_dates = [history.start_date for history in all_versions]

        effective_dates = self._extract_multiple_version_study_standards_effective_date(
            study_uid=study_uid, list_of_start_dates=start_dates
        )

        selection_history = []
        previous_effective_date = None
        all_versions_dict: dict[Any, Any] = {}
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
                    self.update_ctterm_maps(self.terms_at_specific_datetime)
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

    @ensure_transaction(db)
    def remove_visit_consecutive_group(
        self, study_uid: str, consecutive_visit_group_uid: str
    ):
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid=study_uid)
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        ordered_visits = timeline.ordered_study_visits
        for visit in ordered_visits:
            if (
                visit.study_visit_group
                and visit.study_visit_group.uid == consecutive_visit_group_uid
            ):
                visit.study_visit_group = None
                self.repo.save(visit)

    @ensure_transaction(db)
    def assign_visit_consecutive_group(
        self,
        study_uid: str,
        visits_to_assign: list[str],
        group_format: VisitGroupFormat = VisitGroupFormat.RANGE,
        overwrite_visit_from_template: str | None = None,
        validate_only: bool = False,
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
            msg=f"The following Visits were not found {set(visits_to_assign) - set(found_visit_uids)}",
        )
        self._validate_consecutive_visit_group_assignment(
            study_uid=study_uid,
            visits_to_be_assigned=visits_to_be_assigned,
            overwrite_visit_from_template=overwrite_visit_from_template,
            group_format=group_format,
            validate_only=validate_only,
        )
        if not validate_only:
            # Create StudyVisit group node
            study_visit_group: StudyVisitGroup = StudyVisitGroup(
                group_format=group_format.value
            ).save()

            # Get visit short labels to derive the consecutive visit group name
            visits_short_labels = [
                visit.visit_short_name
                for visit in sorted(visits_to_be_assigned, key=lambda v: v.visit_order)
            ]
            consecutive_visit_group = None
            if group_format == VisitGroupFormat.RANGE:
                consecutive_visit_group = (
                    f"{visits_short_labels[0]}-{visits_short_labels[-1]}"
                )
            elif group_format == VisitGroupFormat.LIST:
                consecutive_visit_group = ",".join(visits_short_labels)
            else:
                ValidationException.raise_if(
                    True,
                    msg=f"Unrecognized VisitGroup format {group_format.value} passed.",
                )

            for visit in visits_to_be_assigned:
                visit.study_visit_group = VisitGroup(
                    uid=study_visit_group.uid,
                    group_name=consecutive_visit_group,
                    group_format=study_visit_group.group_format,
                )
                self.repo.save(visit)

        return [
            StudyVisit.transform_to_response_model(visit)
            for visit in visits_to_be_assigned
        ]

    def _validate_consecutive_visit_group_assignment(
        self,
        study_uid: str,
        visits_to_be_assigned: list[StudyVisitVO],
        overwrite_visit_from_template: str | None = None,
        group_format: VisitGroupFormat = VisitGroupFormat.RANGE,
        validate_only: bool = False,
    ):
        visit_epochs = sorted(
            {
                visit.epoch_connector.epoch.sponsor_preferred_name
                for visit in visits_to_be_assigned
                if visit.epoch_connector and visit.epoch_connector.epoch
            }
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
            if visit.study_visit_group:
                BusinessLogicException.raise_if_not(
                    overwrite_visit_from_template,
                    msg=f"Visit with UID '{visit.uid}' already has consecutive group {visit.study_visit_group.group_name}",
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
                    visit_to_assign.visit_order != order
                    and group_format == VisitGroupFormat.RANGE
                    and not validate_only,
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
            for schedule in schedules_service.get_all_schedules(
                study_uid=study_uid, study_visit_uid=reference_visit.uid
            )
            if schedule.study_activity_uid is not None
        }
        for visit in visits_to_be_assigned:
            other_visit_study_activities = {
                schedule.study_activity_uid
                for schedule in schedules_service.get_all_schedules(
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
            BusinessLogicException.raise_if(
                are_visits_the_same,
                msg=f"Visit '{reference_visit.visit_short_name}' and '{visit.visit_short_name}' have the following properties different {are_visits_the_same}",
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
        for schedule in schedules_service.get_all_schedules(
            study_uid=visit.study_uid, study_visit_uid=visit.uid
        ):
            self._repos.study_activity_schedule_repository.delete(
                study_uid=visit.study_uid,
                selection_uid=schedule.study_activity_schedule_uid,
                author_id=self.author,
            )

        # copy activity schedules from the visit to overwrite
        for schedule in schedules_service.get_all_schedules(
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
