import datetime
from dataclasses import dataclass
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.generic_repository import (
    _manage_versioning_with_relations,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivitySubGroupRoot,
    ActivitySubGroupValue,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import StudyAction
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivitySubGroup,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_base_repository import (
    StudySelectionActivityBaseRepository,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_subgroup import (
    StudySelectionActivitySubGroupAR,
    StudySelectionActivitySubGroupVO,
)
from common.telemetry import trace_calls
from common.utils import convert_to_datetime


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    activity_subgroup_uid: str
    activity_subgroup_name: str | None
    show_activity_subgroup_in_protocol_flowchart: bool
    study_activity_group_uid: str
    study_activity_uids: list[str] | None
    order: int | None
    author_id: str
    change_type: str
    start_date: datetime.datetime
    end_date: datetime.datetime | None
    activity_subgroup_version: str | None


class StudySelectionActivitySubGroupRepository(
    StudySelectionActivityBaseRepository[StudySelectionActivitySubGroupAR]
):
    _aggregate_root_type = StudySelectionActivitySubGroupAR

    def _create_value_object_from_repository(
        self, selection: dict[Any, Any], acv: bool
    ) -> StudySelectionActivitySubGroupVO:
        return StudySelectionActivitySubGroupVO.from_input_values(
            study_selection_uid=selection["study_selection_uid"],
            study_uid=selection["study_uid"],
            activity_subgroup_uid=selection["activity_subgroup_uid"],
            activity_subgroup_name=selection["activity_subgroup_name"],
            activity_subgroup_version=selection["activity_subgroup_version"],
            show_activity_subgroup_in_protocol_flowchart=selection[
                "show_activity_subgroup_in_protocol_flowchart"
            ],
            study_activity_group_uid=selection["study_activity_group_uid"],
            study_activity_uids=selection["study_activity_uids"],
            order=selection["order"],
            start_date=convert_to_datetime(value=selection["start_date"]),
            author_id=selection["author_id"],
            accepted_version=acv,
        )

    def _additional_match(self, **kwargs) -> str:
        return """
            WITH sr, sv
            
            MATCH (sv)-[:HAS_STUDY_ACTIVITY]->(sa:StudyActivity)
                -[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(sasg:StudyActivitySubGroup)
                <-[:HAS_STUDY_ACTIVITY_SUBGROUP]-(sv)
            
            OPTIONAL MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soag:StudySoAGroup)
                <-[:HAS_STUDY_SOA_GROUP]-(sv)
            
            OPTIONAL MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(sag:StudyActivityGroup)
                <-[:HAS_STUDY_ACTIVITY_GROUP]-(sv)
            
            WITH DISTINCT sr, sasg, soag, sag, collect(DISTINCT sa.uid) AS study_activity_uids
            
            MATCH (sasg)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(asgv:ActivitySubGroupValue)<-[:HAS_VERSION]-(asgr:ActivitySubGroupRoot)
            WITH DISTINCT *
            
            MATCH (sasg)<-[:AFTER]-(sac:StudyAction)
        """

    def _filter_clause(self, query_parameters: dict[Any, Any], **kwargs) -> str:
        filter_query = []

        if study_activity_group_uid := kwargs.get("study_activity_group_uid"):
            filter_query.append("sag.uid = $study_activity_group_uid")
            query_parameters["study_activity_group_uid"] = study_activity_group_uid

        if filter_query:
            return "WHERE " + " AND ".join(filter_query)
        return ""

    def _versioning_query(self):
        return """
            CALL (asgr, asgv) {
                MATCH (asgr)-[version:HAS_VERSION]-(asgv)
                WHERE version.status in ['Final', 'Retired']
                WITH version
                ORDER BY [i IN split(version.version, '.') | toInteger(i)] DESC,
                         version.end_date DESC, version.start_date DESC
                LIMIT 1
                RETURN version.version AS activity_subgroup_version
            }
        """

    def _order_by_query(self):
        return """
            WITH DISTINCT *
            ORDER BY soag.order, sag.order, sasg.order
        """

    def _return_clause(self) -> str:
        return """
            RETURN
                sr.uid AS study_uid,
                sasg.uid AS study_selection_uid,
                sasg.accepted_version AS accepted_version,
                COALESCE(sasg.show_activity_subgroup_in_protocol_flowchart, false) AS show_activity_subgroup_in_protocol_flowchart,
                asgr.uid AS activity_subgroup_uid,
                asgv.name AS activity_subgroup_name,
                sag.uid AS study_activity_group_uid,
                study_activity_uids,
                sasg.order AS order,
                sac.date AS start_date,
                sac.author_id AS author_id,
                activity_subgroup_version
        """

    def get_selection_history(
        self,
        selection: dict[Any, Any],
        change_type: str,
        end_date: datetime.datetime | None,
    ):
        return SelectionHistory(
            study_selection_uid=selection["study_selection_uid"],
            activity_subgroup_uid=selection["activity_subgroup_uid"],
            activity_subgroup_name=selection["activity_subgroup_name"],
            activity_subgroup_version=selection["activity_subgroup_version"],
            show_activity_subgroup_in_protocol_flowchart=selection[
                "show_activity_subgroup_in_protocol_flowchart"
            ],
            study_activity_group_uid=selection["study_activity_group_uid"],
            study_activity_uids=selection["study_activity_uids"],
            order=selection["order"],
            author_id=selection["author_id"],
            change_type=change_type,
            start_date=convert_to_datetime(value=selection["start_date"]),
            end_date=end_date,
        )

    def get_audit_trail_query(self, study_selection_uid: str | None):
        if study_selection_uid:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudyActivitySubGroup {uid: $study_selection_uid})
                <-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]-(study_activity:StudyActivity)
            WITH sa, study_activity
            MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sa:StudyActivitySubGroup)
            WITH distinct(all_sa), study_activity
            """
        else:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivitySubGroup)
                <-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]-(study_activity:StudyActivity)
            WITH DISTINCT all_sa, study_activity
            """
        audit_trail_cypher += """
                    MATCH (all_sa)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(av:ActivitySubGroupValue)

                    CALL (av) {
                      MATCH (av) <-[ver]-(ar:ActivitySubGroupRoot)
                      WHERE ver.status = "Final"
                      RETURN ver as ver, ar as ar
                      ORDER BY ver.start_date DESC
                      LIMIT 1
                    }

                    WITH DISTINCT all_sa, ar, av, ver, study_activity
                    ORDER BY study_activity.order ASC
                    MATCH (all_sa)<-[:AFTER]-(asa:StudyAction)
                    OPTIONAL MATCH (all_sa)<-[:BEFORE]-(bsa:StudyAction)
                    WITH all_sa, ar, av, asa, bsa, ver, fgr
                    ORDER BY all_sa.uid, asa.date DESC
                    RETURN
                        all_sa.uid AS study_selection_uid,
                        all_sa.show_activity_subgroup_in_protocol_flowchart AS show_activity_subgroup_in_protocol_flowchart,
                        ar.uid AS activity_subgroup_uid,
                        av.name AS activity_subgroup_name,
                        head([(all_sa)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]-(:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup) 
                            | study_activity_group.uid]) as study_activity_group_uid,
                        apoc.coll.toSet([(sa)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]-(study_activity:StudyActivity) | study_activity.uid]) as study_activity_uids,
                        sa.order AS order,
                        asa.date AS start_date,
                        asa.author_id AS author_id,
                        labels(asa) AS change_type,
                        bsa.date AS end_date,
                        ver.version AS activity_subgroup_version
                    """
        return audit_trail_cypher

    def get_study_selection_node_from_latest_study_value(
        self, study_value: StudyValue, study_selection: StudyActivitySubGroup
    ):
        return StudyActivitySubGroup.nodes.has(has_before=False).get(
            uid=study_selection.study_selection_uid
        )

    def _add_new_selection(
        self,
        study_root: StudyRoot,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionActivitySubGroupVO,
        audit_node: StudyAction,
        last_study_selection_node: StudyActivitySubGroup,
        for_deletion: bool = False,
    ):
        # find the activity subgroup value
        activity_subgroup_root_node: ActivitySubGroupRoot = (
            ActivitySubGroupRoot.nodes.get(uid=selection.activity_subgroup_uid)
        )
        latest_activity_subgroup_value_node: ActivitySubGroupValue = (
            activity_subgroup_root_node.get_value_for_version(
                selection.activity_subgroup_version
            )
        )
        # Create new activity subgroup selection
        study_activity_subgroup_selection_node = StudyActivitySubGroup(
            show_activity_subgroup_in_protocol_flowchart=selection.show_activity_subgroup_in_protocol_flowchart,
            order=order,
        )
        study_activity_subgroup_selection_node.uid = selection.study_selection_uid
        study_activity_subgroup_selection_node.accepted_version = (
            selection.accepted_version
        )
        study_activity_subgroup_selection_node.save()

        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_activity_subgroup.connect(
                study_activity_subgroup_selection_node
            )

        # Connect new node with Activity subgroup value
        study_activity_subgroup_selection_node.has_selected_activity_subgroup.connect(
            latest_activity_subgroup_value_node
        )
        _manage_versioning_with_relations(
            study_root=study_root,
            action_type=type(audit_node),
            before=last_study_selection_node,
            after=study_activity_subgroup_selection_node,
            exclude_relationships=[ActivitySubGroupValue],
            author_id=selection.author_id,
        )

    def generate_uid(self) -> str:
        return StudyActivitySubGroup.get_next_free_uid_and_increment_counter()

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    @trace_calls(args=[1, 2], kwargs=["study_uid", "study_activity_uid"])
    def get_all_study_activity_subgroups_for_study_activity(
        self, study_uid: str, study_activity_uid
    ) -> list[StudyActivitySubGroup]:
        query = """
            MATCH (study_activity_subgroup:StudyActivitySubGroup)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]-(study_activity:StudyActivity)
                <-[:HAS_STUDY_ACTIVITY]-(study_value:StudyValue)<-[:LATEST]-(study_root:StudyRoot)
            WITH study_root, study_activity_subgroup, collect(study_activity.uid) as all_sa_using_study_activity_subgroup
            WHERE NOT (study_activity_subgroup)<-[:BEFORE]-() 
                AND study_root.uid=$study_uid 
                AND all_sa_using_study_activity_subgroup=[$study_activity_uid]
            RETURN study_activity_subgroup
        """
        study_activity_subgroups, _ = db.cypher_query(
            query,
            params={"study_uid": study_uid, "study_activity_uid": study_activity_uid},
            resolve_objects=True,
        )
        if len(study_activity_subgroups) > 0:
            return study_activity_subgroups[0]
        return []

    @trace_calls
    def find_study_activity_subgroup_vo_with_same_groupings(
        self,
        study_uid: str,
        activity_subgroup_uid: str,
        activity_group_uid: str,
        soa_group_term_uid: str,
        sync_latest_version: bool = False,
    ) -> StudySelectionActivitySubGroupVO | None:
        """Returns a fully-populated VO for the existing StudyActivitySubGroup matching the given
        groupings, or None if not found. Avoids a full AR load."""
        query = """
            MATCH (activity_subgroup_root:ActivitySubGroupRoot)-[:HAS_VERSION]->(activity_subgroup_value:ActivitySubGroupValue)
                <-[:HAS_SELECTED_ACTIVITY_SUBGROUP]-(sasg:StudyActivitySubGroup)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]
                -(study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(:StudyValue)<-[:LATEST]-(:StudyRoot {uid:$study_uid})
            MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(sag:StudyActivityGroup)
                -[:HAS_SELECTED_ACTIVITY_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
            MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(:StudySoAGroup)
                -[:HAS_FLOWCHART_GROUP]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(flowchart_group_term:CTTermRoot)
            WHERE NOT (sasg)<-[:BEFORE]-() AND NOT (sasg)<-[]-(:Delete)
                AND activity_subgroup_root.uid=$activity_subgroup_uid
                AND activity_group_root.uid=$activity_group_uid
                AND flowchart_group_term.uid=$soa_group_term_uid
            WITH DISTINCT sasg, activity_subgroup_root, activity_subgroup_value, sag, $sync_latest_version AS sync_latest_version
            CALL apoc.do.case([
                sync_latest_version=true,
                'WHERE (activity_subgroup_root)-[:LATEST]->(activity_subgroup_value) RETURN *'
            ],
            '',
            {
                activity_subgroup_root: activity_subgroup_root,
                activity_subgroup_value: activity_subgroup_value,
                sync_latest_version: sync_latest_version
            })
            YIELD value
            WITH DISTINCT sasg, activity_subgroup_root, activity_subgroup_value, sag
            CALL (activity_subgroup_root, activity_subgroup_value) {
                MATCH (activity_subgroup_root)-[ver:HAS_VERSION]-(activity_subgroup_value)
                WHERE ver.status IN ['Final', 'Retired']
                WITH ver
                ORDER BY [i IN split(ver.version, '.') | toInteger(i)] DESC,
                         ver.end_date DESC, ver.start_date DESC
                LIMIT 1
                RETURN ver.version AS activity_subgroup_version
            }
            MATCH (sasg)<-[:AFTER]-(after_action:StudyAction)
            RETURN DISTINCT
                sasg.uid AS study_selection_uid,
                COALESCE(sasg.show_activity_subgroup_in_protocol_flowchart, false) AS show_activity_subgroup_in_protocol_flowchart,
                sasg.order AS order,
                coalesce(sasg.accepted_version, false) AS accepted_version,
                activity_subgroup_root.uid AS activity_subgroup_uid,
                activity_subgroup_value.name AS activity_subgroup_name,
                activity_subgroup_version,
                sag.uid AS study_activity_group_uid,
                after_action.date AS start_date,
                after_action.author_id AS author_id
            ORDER BY after_action.date DESC
            LIMIT 1
        """
        results, keys = db.cypher_query(
            query,
            params={
                "study_uid": study_uid,
                "activity_subgroup_uid": activity_subgroup_uid,
                "activity_group_uid": activity_group_uid,
                "soa_group_term_uid": soa_group_term_uid,
                "sync_latest_version": sync_latest_version,
            },
        )
        if not results:
            return None
        row = dict(zip(keys, results[0]))
        return StudySelectionActivitySubGroupVO.from_input_values(
            study_uid=study_uid,
            study_selection_uid=row["study_selection_uid"],
            activity_subgroup_uid=row["activity_subgroup_uid"],
            activity_subgroup_name=row["activity_subgroup_name"],
            activity_subgroup_version=row["activity_subgroup_version"],
            show_activity_subgroup_in_protocol_flowchart=row[
                "show_activity_subgroup_in_protocol_flowchart"
            ],
            order=row["order"],
            study_activity_group_uid=row["study_activity_group_uid"],
            start_date=convert_to_datetime(value=row["start_date"]),
            author_id=row["author_id"],
            accepted_version=row["accepted_version"],
        )
