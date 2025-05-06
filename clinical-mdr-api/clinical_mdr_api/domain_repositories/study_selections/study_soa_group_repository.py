import datetime
from dataclasses import dataclass

from neomodel import db

from clinical_mdr_api.domain_repositories.generic_repository import (
    manage_previous_connected_study_selection_relationships,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import StudyAction
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudySelection,
    StudySoAGroup,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_base_repository import (
    StudySelectionActivityBaseRepository,
)
from clinical_mdr_api.domains.study_selections.study_soa_group_selection import (
    StudySoAGroupAR,
    StudySoAGroupVO,
)
from clinical_mdr_api.utils import unpack_list_of_lists
from common.utils import convert_to_datetime


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    soa_group_term_uid: str
    soa_group_term_name: str | None
    show_soa_group_in_protocol_flowchart: bool
    author_id: str | None
    change_type: str
    order: int | None
    study_activity_group_uids: list[str] | None
    start_date: datetime.datetime
    end_date: datetime.datetime | None


class StudySoAGroupRepository(StudySelectionActivityBaseRepository[StudySoAGroupAR]):
    _aggregate_root_type = StudySoAGroupAR

    def _create_value_object_from_repository(
        self, selection: dict, acv: bool
    ) -> StudySoAGroupVO:
        return StudySoAGroupVO.from_input_values(
            study_selection_uid=selection["study_selection_uid"],
            soa_group_term_uid=selection["soa_group_term_uid"],
            soa_group_term_name=selection["soa_group_term_name"],
            show_soa_group_in_protocol_flowchart=selection[
                "show_soa_group_in_protocol_flowchart"
            ],
            study_activity_group_uids=(
                selection["study_activity_group_uids"]
                if selection["study_activity_group_uids"]
                else None
            ),
            order=selection["order"],
            study_uid=selection["study_uid"],
            start_date=convert_to_datetime(value=selection["start_date"]),
            author_id=selection["author_id"],
            accepted_version=acv,
        )

    def _versioning_query(self) -> str:
        return ""

    def _additional_match(self) -> str:
        return """
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_ACTIVITY]->(study_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->
                (sa:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(elr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(soa_group_term_name:CTTermNameValue)
        """

    def _filter_clause(self, query_parameters: dict, **kwargs) -> str:
        filter_query = "WHERE NOT (sa)<-[:BEFORE]-()"
        return filter_query

    def _order_by_query(self):
        return """
            WITH DISTINCT *
            ORDER BY sa.order ASC
            MATCH (sa)<-[:AFTER]-(sac:StudyAction)
        """

    def _return_clause(self) -> str:
        return """RETURN DISTINCT
                sr.uid AS study_uid,
                sa.uid AS study_selection_uid,
                coalesce(sa.show_soa_group_in_protocol_flowchart, false) AS show_soa_group_in_protocol_flowchart,
                elr.uid AS soa_group_term_uid,
                soa_group_term_name.name AS soa_group_term_name,
                apoc.coll.toSet([(sa)<-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup) 
                    | study_activity_group.uid]) AS study_activity_group_uids,
                sa.order AS order,
                sa.accepted_version AS accepted_version,
                sac.date AS start_date,
                sac.author_id AS author_id"""

    def get_selection_history(
        self, selection: dict, change_type: str, end_date: datetime
    ):
        return SelectionHistory(
            study_selection_uid=selection["study_selection_uid"],
            author_id=selection["author_id"],
            soa_group_term_uid=selection["soa_group_term_uid"],
            soa_group_term_name=selection["soa_group_term_name"],
            show_soa_group_in_protocol_flowchart=selection[
                "show_soa_group_in_protocol_flowchart"
            ],
            study_activity_group_uids=(
                selection["study_activity_group_uids"]
                if selection["study_activity_group_uids"]
                else None
            ),
            order=selection["order"],
            change_type=change_type,
            start_date=convert_to_datetime(value=selection["start_date"]),
            end_date=end_date,
        )

    def get_audit_trail_query(self, study_selection_uid: str):
        if study_selection_uid:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudySoAGroup {uid: $study_selection_uid})
                <-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(study_activity:StudyActivity)
            WITH sa, study_activity
            MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sa:StudySoAGroup)
            WITH distinct(all_sa), study_activity
            """
        else:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudySoAGroup)-[:BEFORE|AFTER]->(all_sa:StudySoAGroup)
                <-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(study_activity:StudyActivity)
            WITH DISTINCT all_sa, study_activity
            """
        audit_trail_cypher += """

                    WITH DISTINCT all_sa, study_activity
                    OPTIONAL MATCH (all_sa)-[:HAS_FLOWCHART_GROUP]->(fgr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(soa_group_term_name:CTTermNameValue)
                    WITH DISTINCT all_sa, fgr, soa_group_term_name, study_activity
                    ORDER BY study_activity.order ASC
                    MATCH (all_sa)<-[:AFTER]-(asa:StudyAction)
                    OPTIONAL MATCH (all_sa)<-[:BEFORE]-(bsa:StudyAction)
                    WITH all_sa, asa, bsa, fgr, soa_group_term_name
                    ORDER BY all_sa.uid, asa.date DESC
                    RETURN
                        all_sa.uid AS study_selection_uid,
                        all_sa.show_soa_group_in_protocol_flowchart AS show_soa_group_in_protocol_flowchart,
                        fgr.uid AS soa_group_term_uid,
                        soa_group_term_name.name AS soa_group_term_name,
                        apoc.coll.toSet([(all_sa)<-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup) 
                            | study_activity_group.uid]) as study_activity_group_uids,
                        sa.order AS order,
                        asa.date AS start_date,
                        asa.author_id AS author_id,
                        labels(asa) AS change_type,
                        bsa.date AS end_date
                    """
        return audit_trail_cypher

    def get_study_selection_node_from_latest_study_value(
        self, study_value: StudyValue, study_selection: StudySelection
    ):
        return StudySoAGroup.nodes.has(has_before=False).get(
            uid=study_selection.study_selection_uid
        )

    def _add_new_selection(
        self,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySoAGroupVO,
        audit_node: StudyAction,
        last_study_selection_node: StudySoAGroup,
        for_deletion: bool = False,
    ):
        # Create new activity selection
        study_soa_group_node = StudySoAGroup(
            show_soa_group_in_protocol_flowchart=selection.show_soa_group_in_protocol_flowchart,
            order=order,
        )
        study_soa_group_node.uid = selection.study_selection_uid
        study_soa_group_node.accepted_version = selection.accepted_version
        study_soa_group_node.save()

        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_soa_group.connect(study_soa_group_node)

        # Connect new node with audit trail
        audit_node.has_after.connect(study_soa_group_node)
        # Set flowchart group
        ct_term_root = CTTermRoot.nodes.get(uid=selection.soa_group_term_uid)
        study_soa_group_node.has_flowchart_group.connect(ct_term_root)
        if last_study_selection_node:
            manage_previous_connected_study_selection_relationships(
                previous_item=last_study_selection_node,
                study_value_node=latest_study_value_node,
                new_item=study_soa_group_node,
            )

    def generate_uid(self) -> str:
        return StudySoAGroup.get_next_free_uid_and_increment_counter()

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    def get_all_study_soa_groups_for_study_activity(
        self, study_uid: str, study_activity_uid
    ) -> list[StudySoAGroup]:
        query = """
            MATCH (study_soa_group:StudySoAGroup)<-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(study_activity:StudyActivity)
                <-[:HAS_STUDY_ACTIVITY]-(study_value:StudyValue)<-[:LATEST]-(study_root:StudyRoot)
            WITH study_root, study_soa_group, collect(study_activity.uid) as all_sa_using_soa_group
            WHERE NOT (study_soa_group)<-[:BEFORE]-() 
                AND study_root.uid=$study_uid 
                AND all_sa_using_soa_group=[$study_activity_uid]
            RETURN study_soa_group
        """
        study_soa_groups, _ = db.cypher_query(
            query,
            params={"study_uid": study_uid, "study_activity_uid": study_activity_uid},
            resolve_objects=True,
        )
        if len(study_soa_groups) > 0:
            return study_soa_groups[0]
        return []

    def find_study_soa_group_in_a_study(
        self, study_uid: str, soa_group_term_uid: str
    ) -> StudySoAGroup | None:
        query = """
            MATCH (flowchart_group_term:CTTermRoot)<-[:HAS_FLOWCHART_GROUP]-(study_soa_group:StudySoAGroup)<-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]
                -(:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(:StudyValue)<-[:LATEST]-(:StudyRoot {uid:$study_uid})
            WHERE NOT (study_soa_group)<-[:BEFORE]-() AND NOT (study_soa_group)<-[]-(:Delete)
                AND flowchart_group_term.uid=$soa_group_term_uid
            RETURN DISTINCT study_soa_group
        """
        study_soa_groups, _ = db.cypher_query(
            query,
            params={"study_uid": study_uid, "soa_group_term_uid": soa_group_term_uid},
            resolve_objects=True,
        )
        if len(study_soa_groups) > 0:
            return unpack_list_of_lists(study_soa_groups)[0]
        return None
