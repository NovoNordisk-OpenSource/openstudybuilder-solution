from dataclasses import dataclass
from typing import Any

from neomodel import RelationshipDefinition, StructuredNode, db

from clinical_mdr_api import utils
from clinical_mdr_api.domain_repositories.generic_repository import (
    _manage_versioning_with_relations,
)
from clinical_mdr_api.domain_repositories.models._utils import ListDistinct
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Delete as DeleteAction,
)
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivity,
    StudyActivitySchedule,
)
from clinical_mdr_api.domain_repositories.models.study_visit import StudyVisit
from clinical_mdr_api.domain_repositories.study_selections import base
from clinical_mdr_api.domains.study_selections.study_activity_schedule import (
    StudyActivityScheduleVO,
)
from common.config import settings
from common.exceptions import BusinessLogicException, NotFoundException
from common.telemetry import trace_calls
from common.utils import convert_to_datetime


@dataclass
class SelectionHistory(base.SelectionHistory):
    """Class for selection history items."""

    study_activity_uid: str
    study_visit_uid: str
    study_activity_instance_uid: str | None


class StudyActivityScheduleRepository(base.StudySelectionRepository):

    def _from_repository_values(
        self, study_uid: str, selection: StudyActivitySchedule, selection_vo=None
    ) -> StudyActivityScheduleVO:
        # When selection_vo is provided (from save/delete), use its fields directly
        # instead of doing 3 separate .single() neomodel lookups.
        if selection_vo is not None:
            return StudyActivityScheduleVO(
                uid=selection.uid,
                study_uid=study_uid,
                study_activity_uid=selection_vo.study_activity_uid,
                study_activity_instance_uid=selection_vo.study_activity_instance_uid,
                study_visit_uid=selection_vo.study_visit_uid,
            )
        study_activity = selection.study_activity.single()

        study_visit = selection.study_visit.single()
        study_activity_instance = (
            study_activity.study_activity_has_study_activity_instance.single()
        )
        return StudyActivityScheduleVO(
            uid=selection.uid,
            study_uid=study_uid,
            study_activity_uid=study_activity.uid,
            study_activity_instance_uid=(
                study_activity_instance.uid if study_activity_instance else None
            ),
            study_visit_uid=study_visit.uid,
        )

    def exclude_relationships(
        self,
    ) -> list[type[StructuredNode] | RelationshipDefinition | str]:
        return [StudyActivity, StudyVisit]

    def perform_save(
        self,
        study_value_node: StudyValue,
        selection_vo: StudyActivityScheduleVO,
        author_id: str,
    ) -> StudyActivitySchedule:
        # Detach previous node from study
        if selection_vo.uid is not None:
            self._remove_old_selection_if_exists(selection_vo.study_uid, selection_vo)
        # If this is a new selection we want to check if any other similar Schedule exists
        else:
            BusinessLogicException.raise_if(
                self.find_schedule_for_study_visit_and_study_activity(
                    study_uid=selection_vo.study_uid,
                    study_activity_uid=selection_vo.study_activity_uid,
                    study_visit_uid=selection_vo.study_visit_uid or "",
                ),
                msg=f"There already exist a schedule for the same Activity and Visit in the Study with UID '{selection_vo.study_uid}'",
            )

        # Pre-generate UID so we can CREATE node + all relationships in one round-trip.
        uid = (
            selection_vo.uid
            or StudyActivitySchedule.get_next_free_uid_and_increment_counter()
        )
        results, _ = db.cypher_query(
            """
            MATCH (study_value:StudyValue) WHERE elementId(study_value) = $study_value_eid
            MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity {uid: $study_activity_uid})
            MATCH (study_value)-[:HAS_STUDY_VISIT]->(study_visit:StudyVisit {uid: $study_visit_uid})
            CREATE (schedule:StudyActivitySchedule:StudySelection {uid: $uid})
            CREATE (study_value)-[:HAS_STUDY_ACTIVITY_SCHEDULE]->(schedule)
            CREATE (study_activity)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->(schedule)
            CREATE (study_visit)-[:STUDY_VISIT_HAS_SCHEDULE]->(schedule)
            RETURN schedule
            """,
            {
                "study_value_eid": study_value_node.element_id,
                "study_activity_uid": selection_vo.study_activity_uid,
                "study_visit_uid": selection_vo.study_visit_uid,
                "uid": uid,
            },
            resolve_objects=True,
        )
        if not results or not results[0]:
            raise BusinessLogicException(
                msg=f"Failed to create StudyActivitySchedule for activity '{selection_vo.study_activity_uid}' "
                f"and visit '{selection_vo.study_visit_uid}'."
            )
        return results[0][0]

    def find_schedule_for_study_visit_and_study_activity(
        self, study_uid: str, study_activity_uid: str, study_visit_uid: str
    ) -> list[StudyActivitySchedule]:
        study_activity_schedules = ListDistinct(
            StudyActivitySchedule.nodes.filter(
                study_value__latest_value__uid=study_uid,
                study_activity__uid=study_activity_uid,
                study_visit__uid=study_visit_uid,
            )
            .has(has_before=False)
            .resolve_subgraph()
        ).distinct()
        return study_activity_schedules

    def _remove_old_selection_if_exists(
        self, study_uid: str, schedule: StudyActivityScheduleVO
    ):
        return db.cypher_query(
            """
            MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(:StudyValue)
            -[rel:HAS_STUDY_ACTIVITY_SCHEDULE]->(:StudyActivitySchedule {uid: $schedule_uid})
            DELETE rel
            """,
            {
                "study_uid": study_uid,
                "schedule_uid": schedule.uid,
            },
        )

    def get_study_selection(
        self, study_value_node: StudyValue, selection_uid: str
    ) -> StudyActivitySchedule:
        schedule = study_value_node.has_study_activity_schedule.get_or_none(
            uid=selection_uid
        )

        NotFoundException.raise_if(
            schedule is None, "Study Activity Schedule", selection_uid
        )

        return schedule

    def generate_uid(self) -> str:
        return StudyActivity.get_next_free_uid_and_increment_counter()

    @trace_calls(args=[1, 2], kwargs=["study_uid", "selection_uid"])
    def delete(self, study_uid: str, selection_uid: str, author_id: str) -> None:
        # Single Cypher to fetch StudyRoot + latest StudyValue
        results, _ = db.cypher_query(
            "MATCH (sr:StudyRoot {uid: $uid})-[:LATEST]->(sv:StudyValue) RETURN sr, sv",
            {"uid": study_uid},
            resolve_objects=True,
        )
        NotFoundException.raise_if(not results, "Study", study_uid)
        study_root_node, latest_study_value_node = results[0]

        selection = self.get_study_selection(latest_study_value_node, selection_uid)

        # Single Cypher to fetch related UIDs (replaces 3 .single() calls)
        uid_results, _ = db.cypher_query(
            """
            MATCH (sas:StudyActivitySchedule) WHERE elementId(sas) = $eid
            MATCH (sas)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(sa:StudyActivity)
            MATCH (sas)<-[:STUDY_VISIT_HAS_SCHEDULE]-(sv:StudyVisit)
            OPTIONAL MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->(sai:StudyActivityInstance)
            RETURN sa.uid AS sa_uid, sv.uid AS sv_uid, sai.uid AS sai_uid
            """,
            {"eid": selection.element_id},
        )
        sa_uid, sv_uid, sai_uid = uid_results[0] if uid_results else (None, None, None)
        assert isinstance(sa_uid, str)
        selection_vo = StudyActivityScheduleVO(
            uid=selection.uid,
            study_uid=study_uid,
            study_activity_uid=sa_uid,
            study_activity_instance_uid=sai_uid,
            study_visit_uid=sv_uid,
        )

        new_selection = self.perform_save(
            latest_study_value_node, selection_vo, author_id
        )
        # Audit trail — _manage_versioning_with_relations also disconnects `selection`
        _manage_versioning_with_relations(
            study_root=study_root_node,
            action_type=DeleteAction,
            before=selection,
            after=new_selection,
            exclude_relationships=self.exclude_relationships(),
            author_id=author_id,
        )
        new_selection.study_value.disconnect(latest_study_value_node)

    def _get_selection_with_history(
        self, study_uid: str, selection_uid: str | None = None
    ):
        """
        returns the audit trail for study activity schedule either for a
        specific selection or for all study activity schedules for the study.
        """
        if selection_uid:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sas:StudyActivitySchedule {uid: $selection_uid})
            WITH sas
            MATCH (sas)-[:AFTER|BEFORE*0..]-(all_sas:StudyActivitySchedule)
            WITH distinct(all_sas)
            """
        else:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sas:StudyActivitySchedule)
            WITH DISTINCT all_sas
            """
        specific_schedules_audit_trail = db.cypher_query(
            cypher + """
            MATCH (all_sas)<-[:STUDY_VISIT_HAS_SCHEDULE]-(svi:StudyVisit)
            MATCH (all_sas)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_sas)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(sa:StudyActivity)
            OPTIONAL MATCH (all_sas)<-[:STUDY_ACTIVITY_INSTANCE_HAS_SCHEDULE]-(sa_instance:StudyActivityInstance)
            OPTIONAL MATCH (all_sas)<-[:BEFORE]-(bsa:StudyAction)
            WITH all_sas, sa, sa_instance, svi, asa, bsa
            ORDER BY all_sas.uid, asa.date DESC
            RETURN
                all_sas.uid AS uid,
                svi.uid AS study_visit_uid,
                sa.uid AS study_activity_uid,
                sa_instance.uid AS study_activity_instance_uid,
                labels(asa) AS change_type,
                asa.date AS start_date,
                bsa.date AS end_date,
                asa.author_id AS author_id
            """,
            {"study_uid": study_uid, "selection_uid": selection_uid},
        )
        result = []
        for res in utils.db_result_to_list(specific_schedules_audit_trail):
            change_type = ""
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            end_date = (
                convert_to_datetime(value=res["end_date"]) if res["end_date"] else None
            )
            result.append(
                SelectionHistory(
                    study_uid=study_uid,
                    study_selection_uid=res["uid"],
                    study_activity_uid=res["study_activity_uid"],
                    study_activity_instance_uid=res["study_activity_instance_uid"],
                    study_visit_uid=res["study_visit_uid"],
                    author_id=res["author_id"],
                    change_type=change_type,
                    start_date=convert_to_datetime(value=res["start_date"]),
                    end_date=end_date,
                )
            )
        return result

    @trace_calls
    def _get_all_schedules_in_study(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        operational: bool = False,
        study_visit_uid: str | None = None,
    ):
        """
        returns study activity schedules for a study_uid
        """
        query_parameters: dict[str, Any] = {}
        query_parameters["study_visit_uid"] = study_visit_uid
        query_parameters["library_name"] = settings.requested_library_name
        if study_value_version:
            query = "MATCH (sr:StudyRoot { uid: $uid})-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(sv:StudyValue)"
            query_parameters["study_value_version"] = study_value_version
            query_parameters["uid"] = study_uid
        else:
            query = "MATCH (sr:StudyRoot { uid: $uid})-[l:LATEST]->(sv:StudyValue)"
            query_parameters["uid"] = study_uid

        query += """
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_ACTIVITY_SCHEDULE]->(sas:StudyActivitySchedule)
        """
        operational_match = ""
        operational_return = ""
        if operational:
            operational_match = """
            MATCH (sv)--(sa_instance:StudyActivityInstance)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]-(sa)
            MATCH (sa_instance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->(:ActivityInstanceValue)
            MATCH (sa)-[:HAS_SELECTED_ACTIVITY]-(:ActivityValue)-[:HAS_VERSION]-(:ActivityRoot)-[:CONTAINS_CONCEPT]-(lib:Library)
                WHERE lib.name <> $library_name
            """
            operational_return = """
                , sa_instance.uid AS study_activity_instance_uid
            """
        if study_visit_uid:
            visit_filter_query = "WHERE svi.uid=$study_visit_uid"
        else:
            visit_filter_query = ""
        query += f"""
            MATCH (sas)<-[:STUDY_VISIT_HAS_SCHEDULE]-(svi:StudyVisit)--(sv)
            MATCH (sas)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(sa:StudyActivity)--(sv)
            {visit_filter_query}
            {operational_match}
            WITH *
            ORDER BY sas.uid
            RETURN DISTINCT
                sas.uid AS uid,
                svi.uid AS study_visit_uid,
                sa.uid AS study_activity_uid
                {operational_return}
        """

        specific_schedules_audit_trail = db.cypher_query(
            query,
            query_parameters,
        )
        result = []
        for res in utils.db_result_to_list(specific_schedules_audit_trail):
            result.append(
                StudyActivityScheduleVO(
                    study_uid=study_uid,
                    uid=res["uid"],
                    study_activity_uid=res["study_activity_uid"],
                    study_activity_instance_uid=(
                        res["study_activity_instance_uid"] if operational else None
                    ),
                    study_visit_uid=res["study_visit_uid"],
                )
            )
        return result

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass
