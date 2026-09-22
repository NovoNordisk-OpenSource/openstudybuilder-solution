from dataclasses import dataclass

from neomodel import db

from clinical_mdr_api.models.complexity_score import (
    ActivityBurden,
    Burden,
    BurdenIdInput,
    BurdenInput,
    ComplexityScoreAssessment,
    ComplexityScoreDetails,
    ComplexityScoreVisit,
)
from common import exceptions
from common.utils import get_db_result_as_dict

ROUTINE_INITIAL_VISIT_BURDEN_ID = "99205"
ROUTINE_INITIAL_VISIT_BURDEN_DEFAULT_VAL = 3.17
ROUTINE_FOLLOW_UP_VISIT_BURDEN_ID = "99212"
ROUTINE_FOLLOW_UP_VISIT_BURDEN_DEFAULT_VAL = 0.48
PHYSICAL_VISIT_BURDEN_ID = "99211"
PHYSICAL_VISIT_BURDEN_DEFAULT_VAL = 0.18
NON_PHYSICAL_VISIT_BURDEN_ID = "NC008"
NON_PHYSICAL_VISIT_BURDEN_DEFAULT_VAL = 0.6
ANY_VISIT_BURDEN_ID = "EDC"
ANY_VISIT_BURDEN_DEFAULT_VAL = 0.2


@dataclass
class SoaRow:

    @dataclass
    class Visit:
        uid: str
        short_name: str
        visit_contact_mode: str | None = None

    activity_subgroup_uid: str
    activity_subgroup_name: str
    visits: list[Visit]


@dataclass
class VisitsSummary:
    physical_visits: int
    non_physical_visits: int


@dataclass
class VisitTypeBurdens:
    any: float
    physical: float
    virtual: float
    initial: float
    follow_up: float


class ComplexityScoreService:

    @classmethod
    def get_base_query_for_study_root_and_value(
        cls,
        study_version_number: str | None,
    ) -> str:
        if study_version_number:
            return """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[hv:HAS_VERSION {version: $study_version_number}]->(study_value:StudyValue)
            WITH study_root, study_value, hv ORDER BY hv.end_date DESC LIMIT 1
            """

        return """
        MATCH (study_root:StudyRoot {uid: $study_uid})-[latest:LATEST]->(study_value:StudyValue)
        MATCH (study_root)-[hv:HAS_VERSION]->(study_value)
        WITH study_root, study_value, hv ORDER BY hv.end_date DESC LIMIT 1
        """

    @classmethod
    def get_soa(cls, study_uid: str, study_version_number: str | None) -> list[SoaRow]:
        params = {"study_uid": study_uid, "study_version_number": study_version_number}

        query = cls.get_base_query_for_study_root_and_value(study_version_number)

        query += """
            MATCH (study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(study_value)
            MATCH (study_activity_schedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(study_value)
            MATCH (study_visit)-[:HAS_VISIT_CONTACT_MODE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(visit_contact_mode_term:CTCodelistTerm)
            MATCH (study_activity_schedule)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value)
            WHERE NOT (study_activity)<-[:BEFORE]-()
            
            WITH
                study_value,
                study_activity_schedule,
                study_visit,
                visit_contact_mode_term,
                study_activity,
                head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue)<-[:HAS_VERSION]-(activity_root:ActivityRoot) | {uid: activity_root.uid}]) AS activity,
                head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)<-[:LATEST]-(activity_subgroup_root:ActivitySubGroupRoot) | {name: activity_subgroup_value.name, uid: activity_subgroup_root.uid}]) AS activity_subgroup
            ORDER BY study_activity.order, study_visit.visit_number

            RETURN DISTINCT
                study_visit.uid AS visit_uid,
                study_visit.short_visit_label AS visit_short_name,
                visit_contact_mode_term.submission_value AS visit_contact_mode,
                activity_subgroup.uid AS activity_subgroup_uid,
                activity_subgroup.name AS activity_subgroup_name
                
            ORDER BY activity_subgroup_name   

            """

        rows, columns = db.cypher_query(
            query=query,
            params=params,
            handle_unique=True,
            retry_on_session_expire=False,
            resolve_objects=False,
        )

        res = [get_db_result_as_dict(row, columns) for row in rows]

        # Group rows by activity_subgroup_uid
        grouped = {}
        for row in res:
            activity_subgroup_uid = row["activity_subgroup_uid"]
            if activity_subgroup_uid not in grouped:
                grouped[activity_subgroup_uid] = SoaRow(
                    activity_subgroup_uid=row["activity_subgroup_uid"],
                    activity_subgroup_name=row["activity_subgroup_name"],
                    visits=[],
                )
            visit = next(
                (
                    v
                    for v in grouped[activity_subgroup_uid].visits
                    if v.uid == row["visit_uid"]
                ),
                None,
            )
            if not visit:
                visit = SoaRow.Visit(
                    uid=row["visit_uid"],
                    short_name=str(row["visit_short_name"]),
                    visit_contact_mode=(
                        row["visit_contact_mode"]
                        if "visit_contact_mode" in row
                        else None
                    ),
                )
                grouped[activity_subgroup_uid].visits.append(visit)

        # Sort each visits by short_name
        for subgroup in grouped.values():
            subgroup.visits.sort(key=lambda v: v.short_name)

        # Convert to list of SoaRow items
        soa = [
            SoaRow(
                activity_subgroup_uid=uid,
                activity_subgroup_name=data.activity_subgroup_name,
                visits=data.visits,
            )
            for uid, data in grouped.items()
        ]
        return soa

    @classmethod
    def get_visits_summary(
        cls, study_uid: str, study_version_number: str | None
    ) -> VisitsSummary:
        params = {"study_uid": study_uid, "study_version_number": study_version_number}

        query = cls.get_base_query_for_study_root_and_value(study_version_number)

        query += """
            MATCH (study_value)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)
                -[:HAS_VISIT_CONTACT_MODE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(visit_contact_mode_term:CTCodelistTerm)
            WHERE NOT (study_visit)<-[:BEFORE]-()
            
            WITH DISTINCT
                study_visit,
                visit_contact_mode_term

            RETURN 
                count(DISTINCT CASE WHEN visit_contact_mode_term.submission_value = 'ONSITE' THEN study_visit.uid END) AS physical_visits,
                count(DISTINCT CASE WHEN visit_contact_mode_term.submission_value <> 'ONSITE' THEN study_visit.uid END) AS non_physical_visits 
            """

        rows, columns = db.cypher_query(
            query=query,
            params=params,
            handle_unique=True,
            retry_on_session_expire=False,
            resolve_objects=False,
        )

        res = get_db_result_as_dict(rows[0], columns)
        return VisitsSummary(
            physical_visits=res["physical_visits"],
            non_physical_visits=res["non_physical_visits"],
        )

    @classmethod
    def get_activity_burdens(cls, lite: bool = True) -> list[ActivityBurden]:
        return_stmt = (
            """
            RETURN DISTINCT asg.uid as activity_subgroup_uid,
                cb.burden_id as burden_id,
                cb.site_burden as site_burden
            """
            if lite
            else """
            RETURN DISTINCT asg.uid as activity_subgroup_uid,
                asg_value.name as activity_subgroup_name,
                cb.burden_id as burden_id,
                cb.site_burden as site_burden,
                cb.patient_burden as patient_burden,
                cb.median_cost_usd as median_cost_usd
            """
        )

        query = f"""
            MATCH (asg:ActivitySubGroupRoot)-[:LATEST]->(asg_value:ActivitySubGroupValue)
            OPTIONAL MATCH (asg)-[rel:HAS_COMPLEXITY_BURDEN]->(cb:ComplexityBurden)
            {return_stmt}
            ORDER BY asg.uid
            """
        rows, columns = db.cypher_query(
            query=query,
            handle_unique=True,
            retry_on_session_expire=False,
            resolve_objects=False,
        )
        res = [get_db_result_as_dict(row, columns) for row in rows]
        return [ActivityBurden.from_dict(row) for row in res]

    def calculate_site_complexity_score(
        self, study_uid: str, study_version_number: str | None
    ) -> float:
        """Calculates the site complexity score for a study based on its Schedule of Activities (SoA) and predefined activity burdens."""

        visits_summary = self.get_visits_summary(study_uid, study_version_number)
        soa = self.get_soa(study_uid, study_version_number)
        activity_burdens = self.get_activity_burdens()
        activity_burden_dict = {ab.activity_subgroup_uid: ab for ab in activity_burdens}

        initial_visit_burden = (
            activity_burden_dict.get(ROUTINE_INITIAL_VISIT_BURDEN_ID).site_burden
            if ROUTINE_INITIAL_VISIT_BURDEN_ID in activity_burden_dict
            else ROUTINE_INITIAL_VISIT_BURDEN_DEFAULT_VAL
        )

        follow_up_visit_burden = (
            activity_burden_dict.get(ROUTINE_FOLLOW_UP_VISIT_BURDEN_ID).site_burden
            if ROUTINE_FOLLOW_UP_VISIT_BURDEN_ID in activity_burden_dict
            else ROUTINE_FOLLOW_UP_VISIT_BURDEN_DEFAULT_VAL
        )

        total_score = (
            initial_visit_burden
            + follow_up_visit_burden
            + self.get_total_visits_site_burden(visits_summary, activity_burden_dict)
            + self.get_total_activities_site_burden(soa, activity_burden_dict)
        )

        # Round total score to 3 decimal places
        return round(total_score, 3)

    def get_complexity_score_details(
        self, study_uid: str, study_version_number: str | None
    ) -> ComplexityScoreDetails:
        visits_summary = self.get_visits_summary(study_uid, study_version_number)
        soa = self.get_soa(study_uid, study_version_number)
        activity_burdens = self.get_activity_burdens()
        activity_burden_dict = {ab.activity_subgroup_uid: ab for ab in activity_burdens}

        burdens = self.get_visit_types_site_burdens(activity_burden_dict)

        visits = [
            ComplexityScoreVisit(
                type="initial",
                count=1,
                burden=burdens.initial,
            ),
            ComplexityScoreVisit(
                type="follow_up",
                count=1,
                burden=burdens.follow_up,
            ),
            ComplexityScoreVisit(
                type="physical",
                count=visits_summary.physical_visits,
                burden=round(burdens.any + burdens.physical, 3),
            ),
            ComplexityScoreVisit(
                type="virtual",
                count=visits_summary.non_physical_visits,
                burden=round(burdens.any + burdens.virtual, 3),
            ),
        ]

        assessments = []
        for row in soa:
            if not row.activity_subgroup_name:
                continue
            activity_burden = activity_burden_dict.get(row.activity_subgroup_uid)
            visit_count = len(row.visits)
            burden = round(activity_burden.site_burden, 3) if activity_burden else 0.0
            assessments.append(
                ComplexityScoreAssessment(
                    type=row.activity_subgroup_name,
                    count=visit_count,
                    burden=burden,
                )
            )

        return ComplexityScoreDetails(visits=visits, assessments=assessments)

    @classmethod
    def get_visit_types_site_burdens(cls, activity_burden_dict) -> VisitTypeBurdens:
        return VisitTypeBurdens(
            any=(
                activity_burden_dict.get(ANY_VISIT_BURDEN_ID).site_burden
                if ANY_VISIT_BURDEN_ID in activity_burden_dict
                else ANY_VISIT_BURDEN_DEFAULT_VAL
            ),
            virtual=(
                activity_burden_dict.get(NON_PHYSICAL_VISIT_BURDEN_ID).site_burden
                if NON_PHYSICAL_VISIT_BURDEN_ID in activity_burden_dict
                else NON_PHYSICAL_VISIT_BURDEN_DEFAULT_VAL
            ),
            physical=(
                activity_burden_dict.get(PHYSICAL_VISIT_BURDEN_ID).site_burden
                if PHYSICAL_VISIT_BURDEN_ID in activity_burden_dict
                else PHYSICAL_VISIT_BURDEN_DEFAULT_VAL
            ),
            initial=(
                activity_burden_dict.get(ROUTINE_INITIAL_VISIT_BURDEN_ID).site_burden
                if ROUTINE_INITIAL_VISIT_BURDEN_ID in activity_burden_dict
                else ROUTINE_INITIAL_VISIT_BURDEN_DEFAULT_VAL
            ),
            follow_up=(
                activity_burden_dict.get(ROUTINE_FOLLOW_UP_VISIT_BURDEN_ID).site_burden
                if ROUTINE_FOLLOW_UP_VISIT_BURDEN_ID in activity_burden_dict
                else ROUTINE_FOLLOW_UP_VISIT_BURDEN_DEFAULT_VAL
            ),
        )

    @classmethod
    def get_total_visits_site_burden(
        cls, visits_summary: VisitsSummary, activity_burden_dict
    ) -> float:
        # Total =
        #   + total_visits * "Any Visit [*EDC*]" burden		                    = x * 0.20
        #   + non_physical_visits * "simple or brief tel. visit [NC008]" burden	= x * 0.60
        #   + physical_visits * "brief visit with vital signs [99211]" burden	= x * 0.18

        burdens = cls.get_visit_types_site_burdens(activity_burden_dict)

        total_score = 0.0
        total_score += visits_summary.non_physical_visits * (
            burdens.any + burdens.virtual
        )
        total_score += visits_summary.physical_visits * (burdens.any + burdens.physical)

        return total_score

    @classmethod
    def get_total_activities_site_burden(cls, soa, activity_burden_dict) -> float:
        # Activity burdens summed up over all visits
        #   - all activities under the same activity subgroup will be added once per visit

        total_score = 0.0
        for row in soa:
            activity_burden = activity_burden_dict.get(row.activity_subgroup_uid, None)
            if activity_burden:
                for _visit in row.visits:
                    total_score += activity_burden.site_burden

        return total_score

    def get_burdens(self) -> list[Burden]:
        query = """
            MATCH (burden:ComplexityBurden)
            RETURN burden
            ORDER BY burden.burden_id
            """
        rows, columns = db.cypher_query(
            query=query,
            handle_unique=True,
            retry_on_session_expire=False,
            resolve_objects=False,
        )
        res = [get_db_result_as_dict(row, columns) for row in rows]
        return [Burden.from_dict(row["burden"]) for row in res]

    def get_burden_by_id(self, burden_id: str) -> Burden:
        query = """
            MATCH (burden:ComplexityBurden {burden_id: $burden_id})
            RETURN burden
            """
        params = {"burden_id": burden_id.strip().upper()}
        rows, columns = db.cypher_query(
            query=query,
            params=params,
            handle_unique=True,
            retry_on_session_expire=False,
            resolve_objects=False,
        )
        res = [get_db_result_as_dict(row, columns) for row in rows]
        if not res:
            raise exceptions.NotFoundException(
                msg=f"Complexity burden with ID '{burden_id}' not found."
            )
        return Burden.from_dict(res[0]["burden"])

    def create_burden(self, payload: BurdenInput) -> Burden:
        query = """
            MERGE (n:ComplexityBurden {burden_id: $burden_id})
            ON CREATE SET 
                n.name = $name,
                n.description = $description, 
                n.site_burden = $site_burden, 
                n.patient_burden = $patient_burden,
                n.median_cost_usd = $median_cost_usd,
                n.created_at = datetime()
            ON MATCH SET 
                n.name = $name,
                n.description = $description, 
                n.site_burden = $site_burden, 
                n.patient_burden = $patient_burden,
                n.median_cost_usd = $median_cost_usd,
                n.updated_at = datetime()
            """

        params = {
            "burden_id": payload.burden_id.strip().upper(),
            "name": payload.name,
            "description": payload.description,
            "site_burden": payload.site_burden,
            "patient_burden": payload.patient_burden,
            "median_cost_usd": payload.median_cost_usd,
        }
        _rows, _columns = db.cypher_query(
            query=query,
            params=params,
            handle_unique=True,
            retry_on_session_expire=False,
            resolve_objects=False,
        )
        return self.get_burden_by_id(payload.burden_id)

    def update_activity_burden(
        self, activity_subgroup_id: str, burden: BurdenIdInput
    ) -> ActivityBurden:
        # Validate that burden and activity subgroup exist
        self.get_burden_by_id(burden.burden_id)
        self.get_activity_burden(activity_subgroup_id)

        params = {
            "activity_subgroup_id": activity_subgroup_id,
            "burden_id": burden.burden_id,
        }

        # First remove existing activity->burden mapping, if any
        self.delete_activity_burden_mapping(activity_subgroup_id)

        # Then create new relationship
        query = """
                MATCH (asg:ActivitySubGroupRoot {uid: $activity_subgroup_id})
                MATCH (cb:ComplexityBurden {burden_id: $burden_id})
                MERGE (asg)-[rel:HAS_COMPLEXITY_BURDEN]->(cb)
                RETURN asg, rel,
                    cb.burden_id as burden_id,
                    cb.site_burden as site_burden,
                    cb.patient_burden as patient_burden,
                    cb.median_cost_usd as median_cost_usd
                """

        rows, columns = db.cypher_query(
            query=query,
            params=params,
            handle_unique=True,
            retry_on_session_expire=False,
            resolve_objects=False,
        )
        res = [get_db_result_as_dict(row, columns) for row in rows]
        if not res:
            raise exceptions.BusinessLogicException(
                msg=f"Failed to update activity burden mapping for activity subgroup '{activity_subgroup_id}' and burden '{burden.burden_id}'"
            )

        return self.get_activity_burden(activity_subgroup_id)

    def delete_activity_burden_mapping(self, activity_subgroup_id: str) -> None:
        params = {
            "activity_subgroup_id": activity_subgroup_id,
        }

        query = """
                MATCH (asg:ActivitySubGroupRoot {uid: $activity_subgroup_id})-[rel:HAS_COMPLEXITY_BURDEN]->(cb:ComplexityBurden)
                DELETE rel
                """

        db.cypher_query(
            query=query,
            params=params,
            handle_unique=True,
            retry_on_session_expire=False,
            resolve_objects=False,
        )

    def get_activity_burden(self, activity_subgroup_id: str) -> ActivityBurden:
        params = {
            "activity_subgroup_id": activity_subgroup_id,
        }

        query = """
            MATCH (asg:ActivitySubGroupRoot {uid: $activity_subgroup_id})-[:LATEST]->(asg_value:ActivitySubGroupValue)
            OPTIONAL MATCH (asg)-[rel:HAS_COMPLEXITY_BURDEN]->(cb:ComplexityBurden)
            RETURN asg.uid as activity_subgroup_uid,
                asg.value.name as activity_subgroup_name,
                cb.burden_id as burden_id,
                cb.site_burden as site_burden,
                cb.patient_burden as patient_burden,
                cb.median_cost_usd as median_cost_usd
            """

        rows, columns = db.cypher_query(
            query=query,
            params=params,
            handle_unique=True,
            retry_on_session_expire=False,
            resolve_objects=False,
        )
        res = [get_db_result_as_dict(row, columns) for row in rows]
        if not res:
            raise exceptions.NotFoundException(
                msg=f"Activity subgroup with UID '{activity_subgroup_id}' not found."
            )

        return ActivityBurden.from_dict(res[0])
