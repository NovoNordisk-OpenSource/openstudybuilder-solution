import datetime

from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.unit_definitions.unit_definition_repository import (
    UnitDefinitionRepository,
)
from clinical_mdr_api.domain_repositories.generic_repository import (
    manage_previous_connected_study_selection_relationships,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    StudyDayRoot,
    StudyDurationDaysRoot,
    StudyDurationWeeksRoot,
    StudyWeekRoot,
    TimePointRoot,
    UnitDefinitionRoot,
    VisitNameRoot,
    WeekInStudyRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
)
from clinical_mdr_api.domain_repositories.models.study_epoch import StudyEpoch
from clinical_mdr_api.domain_repositories.models.study_visit import StudyVisit
from clinical_mdr_api.domain_repositories.study_selections.study_epoch_repository import (
    get_ctlist_terms_by_name,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_epoch import StudyEpochEpoch
from clinical_mdr_api.domains.study_selections.study_visit import (
    NumericValue,
    SimpleStudyEpoch,
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
from common import config
from common.config import (
    GLOBAL_ANCHOR_VISIT_NAME,
    PREVIOUS_VISIT_NAME,
    STUDY_VISIT_TIMEREF_NAME,
)
from common.exceptions import ValidationException


def get_valid_time_references_for_study(
    study_uid: str, effective_date: datetime.datetime | None = None
):
    if not effective_date:
        time_reference_match = "MATCH (time_reference_value:CTTermNameValue)<-[:LATEST]-(time_reference_name_root)"
        visit_type_match = (
            "MATCH (visit_type_root)-[:LATEST]->(visit_type_value:CTTermNameValue)"
        )
    else:
        time_reference_match = """
        MATCH (time_reference_value:CTTermNameValue)<-[hv:HAS_VERSION]-(time_reference_name_root)
            WHERE (hv.start_date<= datetime($effective_date) < hv.end_date) OR (hv.end_date IS NULL AND (hv.start_date <= datetime($effective_date)))
        """
        visit_type_match = """
        MATCH (visit_type_root)-[hv_type:HAS_VERSION]->(visit_type_value:CTTermNameValue)
            WHERE (hv_type.start_date<= datetime($effective_date) < hv_type.end_date) OR (hv_type.end_date IS NULL AND (hv_type.start_date <= datetime($effective_date)))
        """
    cypher_query = f"""
        MATCH (time_reference_name_root:CTTermNameRoot)<-[HAS_NAME_ROOT]-
        (time_reference_root:CTTermRoot)<-[HAS_TERM]-(codelist_root:CTCodelistRoot)-[:HAS_NAME_ROOT]->
        (:CTCodelistNameRoot)-[:LATEST]->(:CTCodelistNameValue {{name:$time_reference_codelist_name}})

        {time_reference_match}
        
        MATCH (study_root:StudyRoot {{uid:$study_uid}})-[:LATEST]->(:StudyValue)-[:HAS_STUDY_VISIT]->
            (study_visit:StudyVisit)-[:HAS_VISIT_TYPE]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(visit_type_root:CTTermNameRoot) 
        
        {visit_type_match}
            
        WITH time_reference_root, time_reference_value, COLLECT(visit_type_value.name) AS visit_type_value_names 
            WHERE time_reference_value.name IN visit_type_value_names 
                OR time_reference_value.name IN [$global_anchor_visit_name, $previous_visit_name]
        RETURN time_reference_root.uid, time_reference_value.name
        """
    items, _ = db.cypher_query(
        cypher_query,
        {
            "time_reference_codelist_name": STUDY_VISIT_TIMEREF_NAME,
            "study_uid": study_uid,
            "global_anchor_visit_name": GLOBAL_ANCHOR_VISIT_NAME,
            "previous_visit_name": PREVIOUS_VISIT_NAME,
            "effective_date": (
                effective_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                if effective_date
                else None
            ),
        },
    )

    return {time_reference[0]: time_reference[1] for time_reference in items}


class StudyVisitRepository:
    def __init__(self, author_id: str):
        self.author_id = author_id
        unit_repository = UnitDefinitionRepository(self.author_id)
        units, _ = unit_repository.get_all_optimized()
        unit: UnitDefinitionAR
        self._day_unit = None
        self._week_unit = None
        for unit in units:
            if unit.concept_vo.name == "day":
                self._day_unit = unit
            if unit.concept_vo.name == "week":
                self._week_unit = unit

    def generate_uid(self) -> str:
        return StudyVisit.get_next_free_uid_and_increment_counter()

    def fetch_ctlist(self, codelist_names: str, effective_date=None):
        return get_ctlist_terms_by_name(codelist_names, effective_date=effective_date)

    def get_day_week_units(self):
        return (self._day_unit, self._week_unit)

    def save(self, visit: StudyVisitVO, create: bool = False):
        return self._update(visit, create)

    def count_activities(
        self, visit_uid: str, study_value_version: str | None = None
    ) -> int:
        """
        Returns the amount of activities assigned to given study visit

        :return: int
        """
        if study_value_version:
            query = """
                MATCH (:StudyRoot)-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]-(:StudyValue)-[:HAS_STUDY_VISIT]->(svis:StudyVisit{uid:$uid})
                MATCH (svis:StudyVisit)-[:STUDY_VISIT_HAS_SCHEDULE]->(activity_schedule:StudyActivitySchedule)-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(:StudyValue)-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]-(:StudyRoot)
                RETURN count(activity_schedule)
                """
            result, _ = db.cypher_query(
                query=query,
                params={"uid": visit_uid, "study_value_version": study_value_version},
            )
        else:
            query = """
                MATCH (:StudyValue)-[:HAS_STUDY_VISIT]->(svis:StudyVisit{uid:$uid})
                MATCH (svis:StudyVisit)-[:STUDY_VISIT_HAS_SCHEDULE]->(activity_schedule:StudyActivitySchedule)-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(:StudyValue)-[l:HAS_VERSION]-(:StudyRoot)
                RETURN count(activity_schedule)
                """
            result, _ = db.cypher_query(query=query, params={"uid": visit_uid})

        return result[0][0] if len(result) > 0 else 0

    def count_study_visits(self, study_uid: str) -> int:
        nodes = StudyVisit.nodes.filter(
            has_study_visit__latest_value__uid=study_uid  # , is_deleted=False
        ).resolve_subgraph()
        return len(nodes)

    def from_study_visit_vo_to_history_vo(
        self, study_visit_vo: StudyVisitVO, input_dict: dict
    ) -> StudyVisitHistoryVO:
        change_type = input_dict.get("change_type")
        for action in change_type:
            if "StudyAction" not in action:
                change_type = action
        study_action_before = input_dict.get("study_action_before") or {}
        return StudyVisitHistoryVO(
            uid=study_visit_vo.uid,
            visit_number=study_visit_vo.visit_number,
            visit_sublabel_reference=study_visit_vo.visit_sublabel_reference,
            consecutive_visit_group=study_visit_vo.consecutive_visit_group,
            show_visit=study_visit_vo.show_visit,
            timepoint=study_visit_vo.timepoint,
            study_day=study_visit_vo.study_day,
            study_duration_days=study_visit_vo.study_duration_days,
            study_week=study_visit_vo.study_week,
            study_duration_weeks=study_visit_vo.study_duration_weeks,
            week_in_study=study_visit_vo.week_in_study,
            visit_name_sc=study_visit_vo.visit_name_sc,
            time_unit_object=study_visit_vo.time_unit_object,
            window_unit_object=study_visit_vo.window_unit_object,
            visit_window_min=study_visit_vo.visit_window_min,
            visit_window_max=study_visit_vo.visit_window_max,
            window_unit_uid=study_visit_vo.window_unit_uid,
            description=study_visit_vo.description,
            start_rule=study_visit_vo.start_rule,
            end_rule=study_visit_vo.end_rule,
            visit_contact_mode=study_visit_vo.visit_contact_mode,
            epoch_allocation=study_visit_vo.epoch_allocation,
            visit_type=study_visit_vo.visit_type,
            status=study_visit_vo.status,
            start_date=study_visit_vo.start_date,
            author_id=study_visit_vo.author_id,
            author_username=study_visit_vo.author_username,
            day_unit_object=study_visit_vo.day_unit_object,
            week_unit_object=study_visit_vo.week_unit_object,
            epoch_connector=study_visit_vo.epoch_connector,
            visit_class=study_visit_vo.visit_class,
            visit_subclass=study_visit_vo.visit_subclass,
            is_global_anchor_visit=study_visit_vo.is_global_anchor_visit,
            is_soa_milestone=study_visit_vo.is_soa_milestone,
            visit_order=study_visit_vo.visit_number,
            vis_unique_number=study_visit_vo.vis_unique_number,
            vis_short_name=study_visit_vo.vis_short_name,
            # History VO params
            change_type=change_type,
            end_date=study_action_before.get("date"),
        )

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict, audit_trail: bool = False
    ) -> StudyVisitVO | StudyVisitHistoryVO:
        study_uid = input_dict.get("study_uid")
        study_epoch = input_dict.get("epoch")
        study_epoch_uid = study_epoch.get("study_epoch_uid")
        simple_study_epoch = SimpleStudyEpoch(
            uid=study_epoch_uid,
            study_uid=study_uid,
            order=study_epoch.get("order"),
            epoch=StudyEpochEpoch[study_epoch.get("epoch_ct_uid")],
        )
        timepoint = input_dict.get("timepoint")
        if timepoint:
            unit_definition = timepoint.get("unit_definition")
            time_unit_object = TimeUnit(
                name=unit_definition.get("name"),
                conversion_factor_to_master=unit_definition.get(
                    "conversion_factor_to_master"
                ),
                from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
            )
        else:
            time_unit_object = None
        if timepoint:
            timpeoint_object = TimePoint(
                uid=timepoint.get("uid"),
                time_unit_uid=timepoint.get("unit_definition").get("uid"),
                visit_timereference=StudyVisitTimeReference.get(
                    timepoint.get("time_reference_uid")
                ),
                visit_value=timepoint.get("value").get("value"),
            )
        else:
            timpeoint_object = None
        window_unit = input_dict.get("window_unit") or {}
        if window_unit is not None:
            window_unit_object = TimeUnit(
                name=window_unit.get("name"),
                conversion_factor_to_master=window_unit.get(
                    "conversion_factor_to_master"
                ),
                from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
            )
        else:
            window_unit_object = None
        day_unit_object = TimeUnit(
            name=config.DAY_UNIT_NAME,
            conversion_factor_to_master=config.DAY_UNIT_CONVERSION_FACTOR_TO_MASTER,
            from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
        )

        week_unit_object = TimeUnit(
            name=config.WEEK_UNIT_NAME,
            conversion_factor_to_master=config.WEEK_UNIT_CONVERSION_FACTOR_TO_MASTER,
            from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
        )
        visit_name = input_dict.get("visit_name")
        study_day = input_dict.get("study_day")
        study_duration_days = input_dict.get("study_duration_days")
        study_week = input_dict.get("study_week")
        study_duration_weeks = input_dict.get("study_duration_weeks")
        week_in_study = input_dict.get("week_in_study")
        vis_subclass = input_dict.get("study_visit").get("visit_subclass")
        visit_subclass = VisitSubclass[vis_subclass] if vis_subclass else None
        is_soa_milestone = input_dict.get("study_visit").get("is_soa_milestone")
        study_visit_vo = StudyVisitVO(
            uid=input_dict.get("study_visit").get("uid"),
            visit_number=input_dict.get("study_visit").get("visit_number"),
            visit_sublabel_reference=input_dict.get("study_visit").get(
                "visit_sublabel_reference"
            ),
            consecutive_visit_group=input_dict.get("study_visit").get(
                "consecutive_visit_group"
            ),
            show_visit=input_dict.get("study_visit").get("show_visit"),
            timepoint=timpeoint_object,
            study_day=(
                NumericValue(
                    uid=study_day.get("uid"), value=int(study_day.get("value"))
                )
                if study_day
                else None
            ),
            study_duration_days=(
                NumericValue(
                    uid=study_duration_days.get("uid"),
                    value=int(study_duration_days.get("value")),
                )
                if study_duration_days
                else None
            ),
            study_week=(
                NumericValue(
                    uid=study_week.get("uid"),
                    value=int(study_week.get("value")),
                )
                if study_week
                else None
            ),
            study_duration_weeks=(
                NumericValue(
                    uid=study_duration_weeks.get("uid"),
                    value=int(study_duration_weeks.get("value")),
                )
                if study_week
                else None
            ),
            week_in_study=(
                NumericValue(
                    uid=week_in_study.get("uid"),
                    value=int(week_in_study.get("value")),
                )
                if week_in_study
                else None
            ),
            visit_name_sc=TextValue(
                uid=visit_name.get("uid"), name=visit_name.get("name")
            ),
            time_unit_object=time_unit_object,
            window_unit_object=window_unit_object,
            visit_window_min=input_dict.get("study_visit").get("visit_window_min"),
            visit_window_max=input_dict.get("study_visit").get("visit_window_max"),
            window_unit_uid=window_unit.get("uid"),
            description=input_dict.get("study_visit").get("description"),
            start_rule=input_dict.get("study_visit").get("start_rule"),
            end_rule=input_dict.get("study_visit").get("end_rule"),
            visit_contact_mode=StudyVisitContactMode.get(
                input_dict.get("visit_contact_mode_uid")
            ),
            epoch_allocation=StudyVisitEpochAllocation.get(
                input_dict.get("epoch_allocation_uid")
            ),
            visit_type=StudyVisitType.get(input_dict.get("visit_type_uid")),
            status=StudyStatus(input_dict.get("study_visit").get("status")),
            start_date=input_dict.get("study_action").get("date"),
            author_id=input_dict.get("study_action").get("author_id"),
            author_username=input_dict.get("author_username"),
            day_unit_object=day_unit_object,
            week_unit_object=week_unit_object,
            epoch_connector=simple_study_epoch,
            visit_class=VisitClass[input_dict.get("study_visit").get("visit_class")],
            visit_subclass=visit_subclass,
            is_global_anchor_visit=input_dict.get("study_visit").get(
                "is_global_anchor_visit"
            ),
            is_soa_milestone=(
                is_soa_milestone if is_soa_milestone is not None else False
            ),
            visit_order=input_dict.get("study_visit").get("visit_order"),
            vis_unique_number=int(
                input_dict.get("study_visit").get("unique_visit_number")
            ),
            vis_short_name=input_dict.get("study_visit").get("short_visit_label"),
            repeating_frequency=StudyVisitRepeatingFrequency.get(
                input_dict.get("repeating_frequency_uid")
            ),
            number_of_assigned_activities=input_dict.get("count_activities"),
        )
        if not audit_trail:
            return study_visit_vo
        return self.from_study_visit_vo_to_history_vo(
            study_visit_vo=study_visit_vo, input_dict=input_dict
        )

    def _retrieve_concepts_from_cypher_res(
        self, result_array, attribute_names, audit_trail: bool = False
    ) -> list[StudyVisitVO]:
        """
        Method maps the result of the cypher query into real aggregate objects.
        :param result_array:
        :param attribute_names:
        :return Iterable[_AggregateRootType]:
        """
        concept_ars = []
        for concept in result_array:
            concept_dictionary = {}
            for concept_property, attribute_name in zip(concept, attribute_names):
                concept_dictionary[attribute_name] = concept_property
            concept_ars.append(
                self._create_aggregate_root_instance_from_cypher_result(
                    concept_dictionary, audit_trail=audit_trail
                )
            )
        return concept_ars

    def find_all_visits_query(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        study_visit_uid: str | None = None,
        audit_trail: bool = False,
    ) -> tuple[str, dict]:
        params = {}
        if not audit_trail:
            if study_value_version:
                query = "MATCH (study_root:StudyRoot {uid: $study_uid})-[:HAS_VERSION{status: $study_status, version: $study_value_version}]->(study_value:StudyValue)"
                params["study_value_version"] = study_value_version
                params["study_status"] = StudyStatus.RELEASED.value
            else:
                query = "MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)"
            params["study_uid"] = study_uid
            if study_visit_uid:
                query += "MATCH (study_value)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit {uid: $study_visit_uid})<-[:AFTER]-(study_action:StudyAction)"
                params["study_visit_uid"] = study_visit_uid
            else:
                query += "MATCH (study_value)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)<-[:AFTER]-(study_action:StudyAction)"
        else:
            if study_visit_uid:
                query = "MATCH (study_visit:StudyVisit {uid: $study_visit_uid})<-[:AFTER]-(study_action:StudyAction)<-[:AUDIT_TRAIL]-(study_root:StudyRoot)"
                params["study_visit_uid"] = study_visit_uid
            else:
                query = "MATCH (study_visit:StudyVisit)<-[:AFTER]-(study_action:StudyAction)<-[:AUDIT_TRAIL]-(study_root:StudyRoot {uid:$study_uid})"
                params["study_uid"] = study_uid
        if not (study_value_version or audit_trail):
            query += "WHERE NOT (study_visit)-[:BEFORE]-()"

        query += """
            WITH 
                study_root.uid AS study_uid,
                study_action,
                study_visit,
                head([(study_visit)<-[:STUDY_EPOCH_HAS_STUDY_VISIT]-(study_epoch:StudyEpoch)-[:HAS_EPOCH]->(epoch_ct_term:CTTermRoot) 
                    | {study_epoch_uid:study_epoch.uid, epoch_ct_uid:epoch_ct_term.uid, order: study_epoch.order}]) AS epoch,
                head([(study_visit)-[:HAS_VISIT_TYPE]->(visit_type:CTTermRoot) | visit_type.uid]) AS visit_type_uid,
                head([(study_visit)-[:HAS_VISIT_CONTACT_MODE]->(visit_contact_mode:CTTermRoot) | visit_contact_mode.uid]) AS visit_contact_mode_uid,
                head([(study_visit)-[:HAS_VISIT_NAME]->(visit_name_root:VisitNameRoot)-[:LATEST]->(visit_name_value:VisitNameValue) 
                    | {uid:visit_name_root.uid, name: visit_name_value.name }]) AS visit_name,
                head([(study_visit)-[:HAS_REPEATING_FREQUENCY]->(repeating_frequency:CTTermRoot) | repeating_frequency.uid]) AS repeating_frequency_uid,
                head([(study_visit)-[:HAS_WINDOW_UNIT]->(udr:UnitDefinitionRoot)-[:LATEST]->(udv:UnitDefinitionValue) 
                    | {
                        uid:udr.uid, 
                        name:udv.name,
                        conversion_factor_to_master: udv.conversion_factor_to_master
                    }]) AS window_unit,
                head([(study_visit)-[:HAS_TIMEPOINT]->(timepoint_root:TimePointRoot)-[:LATEST]->(timepoint_value:TimePointValue) 
                    | {
                        uid:timepoint_root.uid,
                        unit_definition: head([(timepoint_value)-[:HAS_UNIT_DEFINITION]->(udr:UnitDefinitionRoot)-[:LATEST]->(udv:UnitDefinitionValue) 
                            | {
                                uid:udr.uid, 
                                name:udv.name,
                                conversion_factor_to_master: udv.conversion_factor_to_master
                            }]),
                        time_reference_uid: head([(timepoint_value)-[:HAS_TIME_REFERENCE]->(time_reference_ct_term:CTTermRoot) | time_reference_ct_term.uid]),
                        value: head([(timepoint_value)-[:HAS_VALUE]->(nvr:NumericValueRoot)-[:LATEST]->(nvv:NumericValue) | {uid:nvr.uid, value:nvv.value}])
                    }]) AS timepoint,
                head([(study_visit)-[:HAS_STUDY_DAY]->(sdr:StudyDayRoot)-[:LATEST]->(sdv:StudyDayValue) | {uid:sdr.uid, value:sdv.value}]) AS study_day,
                head([(study_visit)-[:HAS_STUDY_DURATION_DAYS]->(sdr:StudyDurationDaysRoot)-[:LATEST]->(sdv:StudyDurationDaysValue) | {uid:sdr.uid, value:sdv.value}]) AS study_duration_days,
                head([(study_visit)-[:HAS_STUDY_WEEK]->(swr:StudyWeekRoot)-[:LATEST]->(swv:StudyWeekValue) | {uid:swr.uid, value:swv.value}]) AS study_week,
                head([(study_visit)-[:HAS_STUDY_DURATION_WEEKS]->(swr:StudyDurationWeeksRoot)-[:LATEST]->(swv:StudyDurationWeeksValue) | {uid:swr.uid, value:swv.value}]) AS study_duration_weeks,
                head([(study_visit)-[:HAS_WEEK_IN_STUDY]->(wisr:WeekInStudyRoot)-[:LATEST]->(wisv:WeekInStudyValue) | {uid:wisr.uid, value:wisv.value}]) AS week_in_study,
                head([(study_visit)-[:HAS_EPOCH_ALLOCATION]->(epoch_allocation:CTTermRoot) | epoch_allocation.uid]) AS epoch_allocation_uid,
                size([(study_visit)-[:STUDY_VISIT_HAS_SCHEDULE]->(activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(:StudyValue) | activity_schedule]) AS count_activities,
                coalesce(head([(user:User)-[*0]-() WHERE user.user_id=study_action.author_id | user.username]), study_action.author_id) AS author_username
        """
        if audit_trail:
            query += """,head([(study_visit:StudyVisit)<-[:BEFORE]-(study_action_before:StudyAction) | study_action_before]) AS study_action_before,
                labels(study_action) AS change_type
                RETURN * ORDER BY study_visit.uid, study_action.date DESC
            """
        else:
            query += "RETURN * ORDER BY study_visit.unique_visit_number"
        return query, params

    def find_all_visits_by_study_uid(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudyVisitVO]:
        query, params = self.find_all_visits_query(
            study_uid=study_uid, study_value_version=study_value_version
        )

        study_visits, attributes_names = db.cypher_query(query=query, params=params)

        extracted_items = self._retrieve_concepts_from_cypher_res(
            study_visits, attributes_names
        )
        return extracted_items

    def find_all_visits_referencing_study_visit(
        self, study_visit_uid: str
    ) -> list[StudyVisit]:
        return (
            StudyVisit.nodes.filter(
                visit_sublabel_reference=study_visit_uid,
            )
            .order_by("unique_visit_number")
            .has(has_before=False, has_study_visit=True)
            .all()
        )

    def find_by_uid(
        self, study_uid: str, uid: str, study_value_version: str | None = None
    ) -> StudyVisitVO:
        query, params = self.find_all_visits_query(
            study_uid=study_uid,
            study_value_version=study_value_version,
            study_visit_uid=uid,
        )
        study_visits, attributes_names = db.cypher_query(query=query, params=params)
        extracted_items = self._retrieve_concepts_from_cypher_res(
            study_visits, attributes_names
        )
        ValidationException.raise_if(
            len(extracted_items) > 1,
            msg=f"Found more than one StudyVisit node with UID '{uid}'.",
        )
        ValidationException.raise_if(
            len(extracted_items) == 0,
            msg=f"StudyVisit with UID '{uid}' doesn't exist.",
        )
        return extracted_items[0]

    def get_all_versions(
        self,
        study_uid: str,
        uid: str | None = None,
    ) -> list[StudyVisitHistoryVO]:
        query, params = self.find_all_visits_query(
            study_uid=study_uid, study_visit_uid=uid, audit_trail=True
        )
        study_visits, attributes_names = db.cypher_query(query=query, params=params)
        extracted_items = self._retrieve_concepts_from_cypher_res(
            study_visits, attributes_names, audit_trail=True
        )
        return extracted_items

    def manage_versioning_create(
        self, study_root: StudyRoot, study_visit: StudyVisitVO, new_item: StudyVisit
    ):
        action = Create(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=study_visit.status.value,
            author_id=study_visit.author_id,
        )
        action.save()
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def manage_versioning_update(
        self,
        study_root: StudyRoot,
        study_visit: StudyVisitVO,
        previous_item: StudyVisit,
        new_item: StudyVisit,
    ):
        action = Edit(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=study_visit.status.value,
            author_id=study_visit.author_id,
        )
        action.save()
        action.has_before.connect(previous_item)
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def manage_versioning_delete(
        self,
        study_root: StudyRoot,
        study_visit: StudyVisitVO,
        previous_item: StudyVisit,
        new_item: StudyVisit,
    ):
        action = Delete(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=study_visit.status.value,
            author_id=study_visit.author_id,
        )
        action.save()
        action.has_before.connect(previous_item)
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def _update(self, study_visit: StudyVisitVO, create: bool = False):
        study_root: StudyRoot = StudyRoot.nodes.get(uid=study_visit.study_uid)
        study_value: StudyValue = study_root.latest_value.get_or_none()
        ValidationException.raise_if(
            study_value is None, msg="Study doesn't have draft version."
        )
        if not create:
            previous_item = study_value.has_study_visit.get(uid=study_visit.uid)

        new_visit = StudyVisit(
            uid=study_visit.uid,
            visit_number=study_visit.visit_number,
            visit_sublabel_reference=study_visit.visit_sublabel_reference,
            short_visit_label=study_visit.visit_short_name,
            unique_visit_number=study_visit.unique_visit_number,
            consecutive_visit_group=study_visit.consecutive_visit_group,
            show_visit=study_visit.show_visit,
            visit_window_min=study_visit.visit_window_min,
            visit_window_max=study_visit.visit_window_max,
            description=study_visit.description,
            start_rule=study_visit.start_rule,
            end_rule=study_visit.end_rule,
            status=study_visit.status.name,
            visit_class=study_visit.visit_class.name,
            visit_subclass=(
                study_visit.visit_subclass.name if study_visit.visit_subclass else None
            ),
            is_global_anchor_visit=study_visit.is_global_anchor_visit,
            is_soa_milestone=study_visit.is_soa_milestone,
        )
        if study_visit.uid:
            new_visit.uid = study_visit.uid
        new_visit.save()
        if study_visit.uid is None:
            study_visit.uid = new_visit.uid

        visit_type = CTTermRoot.nodes.get(uid=study_visit.visit_type.term_uid)
        new_visit.has_visit_type.connect(visit_type)

        if study_visit.repeating_frequency:
            visit_repeating_frequency = CTTermRoot.nodes.get(
                uid=study_visit.repeating_frequency.term_uid
            )
            new_visit.has_repeating_frequency.connect(visit_repeating_frequency)

        if study_visit.timepoint:
            visit_timepoint = TimePointRoot.nodes.get(uid=study_visit.timepoint.uid)
            new_visit.has_timepoint.connect(visit_timepoint)
        if study_visit.study_day:
            study_day_numeric_value = StudyDayRoot.nodes.get(
                uid=study_visit.study_day.uid
            )
            new_visit.has_study_day.connect(study_day_numeric_value)
        if study_visit.study_duration_days:
            study_duration_days = StudyDurationDaysRoot.nodes.get(
                uid=study_visit.study_duration_days.uid
            )
            new_visit.has_study_duration_days.connect(study_duration_days)
        if study_visit.study_week:
            study_week_numeric_value = StudyWeekRoot.nodes.get(
                uid=study_visit.study_week.uid
            )
            new_visit.has_study_week.connect(study_week_numeric_value)
        if study_visit.study_duration_weeks:
            study_duration_weeks = StudyDurationWeeksRoot.nodes.get(
                uid=study_visit.study_duration_weeks.uid
            )
            new_visit.has_study_duration_weeks.connect(study_duration_weeks)
        if study_visit.week_in_study:
            week_in_study = WeekInStudyRoot.nodes.get(uid=study_visit.week_in_study.uid)
            new_visit.has_week_in_study.connect(week_in_study)

        visit_name_text_value = VisitNameRoot.nodes.get(
            uid=study_visit.visit_name_sc.uid
        )
        new_visit.has_visit_name.connect(visit_name_text_value)

        if study_visit.window_unit_uid is not None:
            window_unit = UnitDefinitionRoot.nodes.get(uid=study_visit.window_unit_uid)
            new_visit.has_window_unit.connect(window_unit)
        else:
            window_unit = None
        visit_contact_mode = CTTermRoot.nodes.get(
            uid=study_visit.visit_contact_mode.term_uid
        )
        new_visit.has_visit_contact_mode.connect(visit_contact_mode)
        if study_visit.epoch_allocation:
            epoch_allocation = CTTermRoot.nodes.get(
                uid=study_visit.epoch_allocation.term_uid
            )
            new_visit.has_epoch_allocation.connect(epoch_allocation)

        study_epoch = (
            StudyEpoch.nodes.has(has_after=True)
            .has(has_before=False)
            .get(uid=study_visit.epoch_uid)
        )
        new_visit.study_epoch_has_study_visit.connect(study_epoch)
        if not create:
            if study_visit.is_deleted:
                self.manage_versioning_delete(
                    study_root=study_root,
                    study_visit=study_visit,
                    previous_item=previous_item,
                    new_item=new_visit,
                )
            else:
                new_visit.has_study_visit.connect(study_value)
                self.manage_versioning_update(
                    study_root=study_root,
                    study_visit=study_visit,
                    previous_item=previous_item,
                    new_item=new_visit,
                )
            exclude_study_selection_relationships = [
                StudyEpoch,
            ]
            manage_previous_connected_study_selection_relationships(
                previous_item=previous_item,
                study_value_node=study_value,
                new_item=new_visit,
                exclude_study_selection_relationships=exclude_study_selection_relationships,
            )
        else:
            new_visit.has_study_visit.connect(study_value)
            self.manage_versioning_create(
                study_root=study_root, study_visit=study_visit, new_item=new_visit
            )

        return study_visit
