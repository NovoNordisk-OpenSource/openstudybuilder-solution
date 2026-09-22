import datetime
from dataclasses import dataclass
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.generic_repository import (
    _manage_versioning_with_relations,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupRoot,
    ActivityGroupValue,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import StudyAction
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivityGroup,
    StudySelection,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_base_repository import (
    StudySelectionActivityBaseRepository,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_group import (
    StudySelectionActivityGroupAR,
    StudySelectionActivityGroupVO,
)
from common.telemetry import trace_calls
from common.utils import convert_to_datetime


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    activity_group_uid: str
    activity_group_name: str | None
    show_activity_group_in_protocol_flowchart: bool
    author_id: str
    change_type: str
    start_date: datetime.datetime
    study_soa_group_uid: str
    study_activity_subgroup_uids: list[str] | None
    order: int | None
    end_date: datetime.datetime | None
    activity_group_version: str | None


class StudySelectionActivityGroupRepository(
    StudySelectionActivityBaseRepository[StudySelectionActivityGroupAR]
):
    _aggregate_root_type = StudySelectionActivityGroupAR

    def _create_value_object_from_repository(
        self, selection: dict[Any, Any], acv: bool
    ) -> StudySelectionActivityGroupVO:
        return StudySelectionActivityGroupVO.from_input_values(
            study_selection_uid=selection["study_selection_uid"],
            study_uid=selection["study_uid"],
            activity_group_uid=selection["activity_group_uid"],
            activity_group_name=selection["activity_group_name"],
            activity_group_version=selection["activity_group_version"],
            show_activity_group_in_protocol_flowchart=selection[
                "show_activity_group_in_protocol_flowchart"
            ],
            study_soa_group_uid=selection["study_soa_group_uid"],
            study_activity_subgroup_uids=(
                selection.get("study_activity_subgroup_uids") or None
            ),
            order=selection["order"],
            start_date=convert_to_datetime(value=selection["start_date"]),
            author_id=selection["author_id"],
            accepted_version=acv,
        )

    def _additional_match(self, **kwargs) -> str:
        return """
            WITH sr, sv
            
            MATCH (sv)-[:HAS_STUDY_ACTIVITY]->(sa:StudyActivity)
                -[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(sag:StudyActivityGroup)
                <-[:HAS_STUDY_ACTIVITY_GROUP]-(sv)
            
            OPTIONAL MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soag:StudySoAGroup)
                <-[:HAS_STUDY_SOA_GROUP]-(sv)
            
            OPTIONAL MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(sasg:StudyActivitySubGroup)
                <-[:HAS_STUDY_ACTIVITY_SUBGROUP]-(sv)
            
            WITH DISTINCT sr, sag, soag, collect(DISTINCT sasg.uid) AS study_activity_subgroup_uids
            
            MATCH (sag)-[:HAS_SELECTED_ACTIVITY_GROUP]->(agv:ActivityGroupValue)<-[:HAS_VERSION]-(agr:ActivityGroupRoot)
            WITH DISTINCT *
            
            MATCH (sag)<-[:AFTER]-(sac:StudyAction)
        """

    def _filter_clause(self, query_parameters: dict[Any, Any], **kwargs) -> str:
        filter_query = []

        if study_soa_group_uid := kwargs.get("study_soa_group_uid"):
            filter_query.append("soag.uid = $study_soa_group_uid")
            query_parameters["study_soa_group_uid"] = study_soa_group_uid

        if filter_query:
            return "WHERE " + " AND ".join(filter_query)
        return ""

    def _versioning_query(self):
        return """
            CALL (agr, agv) {
                MATCH (agr)-[version:HAS_VERSION]-(agv)
                WHERE version.status in ['Final', 'Retired']
                WITH version
                ORDER BY [i IN split(version.version, '.') | toInteger(i)] DESC,
                         version.end_date DESC, version.start_date DESC
                LIMIT 1
                RETURN version.version AS activity_group_version
            }
        """

    def _order_by_query(self):
        return """
            WITH DISTINCT *
            ORDER BY soag.order, sag.order
        """

    def _return_clause(self) -> str:
        return """
            RETURN
                sr.uid AS study_uid,
                sag.uid AS study_selection_uid,
                sag.accepted_version AS accepted_version,
                coalesce(sag.show_activity_group_in_protocol_flowchart, false) AS show_activity_group_in_protocol_flowchart,
                agr.uid AS activity_group_uid,
                agv.name AS activity_group_name,
                soag.uid AS study_soa_group_uid,
                study_activity_subgroup_uids,
                sag.order AS order,
                sac.date AS start_date,
                sac.author_id AS author_id,
                activity_group_version
        """

    def get_selection_history(
        self,
        selection: dict[Any, Any],
        change_type: str,
        end_date: datetime.datetime | None,
    ):
        return SelectionHistory(
            study_selection_uid=selection["study_selection_uid"],
            activity_group_uid=selection["activity_group_uid"],
            activity_group_name=selection["activity_group_name"],
            activity_group_version=selection["activity_group_version"],
            show_activity_group_in_protocol_flowchart=selection[
                "show_activity_group_in_protocol_flowchart"
            ],
            study_soa_group_uid=selection["study_soa_group_uid"],
            study_activity_subgroup_uids=(
                selection.get("study_activity_subgroup_uids") or None
            ),
            author_id=selection["author_id"],
            change_type=change_type,
            start_date=convert_to_datetime(value=selection["start_date"]),
            end_date=end_date,
            order=selection["order"],
        )

    def get_audit_trail_query(self, study_selection_uid: str | None):
        if study_selection_uid:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudyActivityGroup {uid: $study_selection_uid})
                <-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity:StudyActivity)
            WITH sa, study_activity
            MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sa:StudyActivityGroup)
            WITH distinct(all_sa), study_activity
            """
        else:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivityGroup)
                <-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity:StudyActivity)
            WITH DISTINCT all_sa, study_activity
            """
        audit_trail_cypher += """
                    MATCH (all_sa)-[:HAS_SELECTED_ACTIVITY_GROUP]->(av:ActivityGroupValue)

                    CALL (av) {
                      MATCH (av) <-[ver]-(ar:ActivityGroupRoot)
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
                        all_sa.show_activity_group_in_protocol_flowchart AS show_activity_group_in_protocol_flowchart,
                        ar.uid AS activity_group_uid,
                        av.name AS activity_group_name,
                        head([(all_sa)<-[STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup) 
                            | study_soa_group.uid]) as study_soa_group_uid,
                        apoc.coll.toSet([(all_sa)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup) 
                            | study_activity_subgroup.uid]) as study_activity_subgroup_uids,
                        sa.order AS order,
                        asa.date AS start_date,
                        asa.author_id AS author_id,
                        labels(asa) AS change_type,
                        bsa.date AS end_date,
                        ver.version AS activity_group_version
                    """
        return audit_trail_cypher

    def get_study_selection_node_from_latest_study_value(
        self, study_value: StudyValue, study_selection: StudySelection
    ):
        return StudyActivityGroup.nodes.has(has_before=False).get(
            uid=study_selection.study_selection_uid
        )

    def _add_new_selection(
        self,
        study_root: StudyRoot,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionActivityGroupVO,
        audit_node: StudyAction,
        last_study_selection_node: StudyActivityGroup,
        for_deletion: bool = False,
    ):
        # find the activity group value
        activity_group_root_node: ActivityGroupRoot = ActivityGroupRoot.nodes.get(
            uid=selection.activity_group_uid
        )
        latest_activity_group_value_node: ActivityGroupValue = (
            activity_group_root_node.get_value_for_version(
                selection.activity_group_version
            )
        )
        # Create new activity group selection
        study_activity_group_selection_node = StudyActivityGroup(
            show_activity_group_in_protocol_flowchart=selection.show_activity_group_in_protocol_flowchart,
            order=order,
        )
        study_activity_group_selection_node.uid = selection.study_selection_uid
        study_activity_group_selection_node.accepted_version = (
            selection.accepted_version
        )
        study_activity_group_selection_node.save()

        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_activity_group.connect(
                study_activity_group_selection_node
            )

        # Connect new node with Activity subgroup value
        study_activity_group_selection_node.has_selected_activity_group.connect(
            latest_activity_group_value_node
        )
        _manage_versioning_with_relations(
            study_root=study_root,
            action_type=type(audit_node),
            before=last_study_selection_node,
            after=study_activity_group_selection_node,
            exclude_relationships=[ActivityGroupValue],
            author_id=selection.author_id,
        )

    def generate_uid(self) -> str:
        return StudyActivityGroup.get_next_free_uid_and_increment_counter()

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    @trace_calls(args=[1, 2], kwargs=["study_uid", "study_activity_uid"])
    def get_all_study_activity_groups_for_study_activity(
        self, study_uid: str, study_activity_uid: str
    ) -> list[StudyActivityGroup]:
        query = """
            MATCH (study_activity_group:StudyActivityGroup)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity:StudyActivity)
                <-[:HAS_STUDY_ACTIVITY]-(study_value:StudyValue)<-[:LATEST]-(study_root:StudyRoot)
            WITH study_root, study_activity_group, collect(study_activity.uid) as all_sa_using_study_activity_group
            WHERE NOT (study_activity_group)<-[:BEFORE]-() 
                AND study_root.uid=$study_uid 
                AND all_sa_using_study_activity_group=[$study_activity_uid]
            RETURN study_activity_group
        """
        study_activity_groups, _ = db.cypher_query(
            query,
            params={"study_uid": study_uid, "study_activity_uid": study_activity_uid},
            resolve_objects=True,
        )
        if len(study_activity_groups) > 0:
            return study_activity_groups[0]
        return []

    @trace_calls
    def find_study_activity_group_vo_with_same_groupings(
        self,
        study_uid: str,
        activity_group_uid: str,
        soa_group_term_uid: str,
        sync_latest_version: bool = False,
    ) -> StudySelectionActivityGroupVO | None:
        """Returns a fully-populated VO for the existing StudyActivityGroup matching the given
        groupings, or None if not found. Avoids a full AR load."""
        query = """
            MATCH (activity_group_root:ActivityGroupRoot)-[:HAS_VERSION]->(activity_group_value:ActivityGroupValue)
                <-[:HAS_SELECTED_ACTIVITY_GROUP]-(sag:StudyActivityGroup)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]
                -(study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(:StudyValue)<-[:LATEST]-(:StudyRoot {uid:$study_uid})
            MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soag:StudySoAGroup)
                -[:HAS_FLOWCHART_GROUP]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(flowchart_group_term:CTTermRoot)
            WHERE NOT (sag)<-[:BEFORE]-() AND NOT (sag)<-[]-(:Delete)
                AND activity_group_root.uid=$activity_group_uid
                AND flowchart_group_term.uid=$soa_group_term_uid
            WITH DISTINCT sag, activity_group_root, activity_group_value, soag, $sync_latest_version AS sync_latest_version
            CALL apoc.do.case([
                sync_latest_version=true,
                'WHERE (activity_group_root)-[:LATEST]->(activity_group_value) RETURN *'
            ],
            '',
            {
                activity_group_root: activity_group_root,
                activity_group_value: activity_group_value,
                sync_latest_version: sync_latest_version
            })
            YIELD value
            WITH DISTINCT sag, activity_group_root, activity_group_value, soag
            CALL (activity_group_root, activity_group_value) {
                MATCH (activity_group_root)-[ver:HAS_VERSION]-(activity_group_value)
                WHERE ver.status IN ['Final', 'Retired']
                WITH ver
                ORDER BY [i IN split(ver.version, '.') | toInteger(i)] DESC,
                         ver.end_date DESC, ver.start_date DESC
                LIMIT 1
                RETURN ver.version AS activity_group_version
            }
            MATCH (sag)<-[:AFTER]-(after_action:StudyAction)
            RETURN DISTINCT
                sag.uid AS study_selection_uid,
                coalesce(sag.show_activity_group_in_protocol_flowchart, false) AS show_activity_group_in_protocol_flowchart,
                sag.order AS order,
                coalesce(sag.accepted_version, false) AS accepted_version,
                activity_group_root.uid AS activity_group_uid,
                activity_group_value.name AS activity_group_name,
                activity_group_version,
                soag.uid AS study_soa_group_uid,
                after_action.date AS start_date,
                after_action.author_id AS author_id
            ORDER BY after_action.date DESC
            LIMIT 1
        """
        results, keys = db.cypher_query(
            query,
            params={
                "study_uid": study_uid,
                "activity_group_uid": activity_group_uid,
                "soa_group_term_uid": soa_group_term_uid,
                "sync_latest_version": sync_latest_version,
            },
        )
        if not results:
            return None
        row = dict(zip(keys, results[0]))
        return StudySelectionActivityGroupVO.from_input_values(
            study_uid=study_uid,
            study_selection_uid=row["study_selection_uid"],
            activity_group_uid=row["activity_group_uid"],
            activity_group_name=row["activity_group_name"],
            activity_group_version=row["activity_group_version"],
            show_activity_group_in_protocol_flowchart=row[
                "show_activity_group_in_protocol_flowchart"
            ],
            order=row["order"],
            study_soa_group_uid=row["study_soa_group_uid"],
            start_date=convert_to_datetime(value=row["start_date"]),
            author_id=row["author_id"],
            accepted_version=row["accepted_version"],
        )
