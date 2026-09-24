import datetime
from dataclasses import dataclass
from typing import Any

from neomodel import db

from clinical_mdr_api import utils
from clinical_mdr_api.domain_repositories.generic_repository import (
    _manage_versioning_with_relations,
)
from clinical_mdr_api.domain_repositories.models.activities import ActivityValue
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import StudyAction
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivity,
    StudyActivityGroup,
    StudyActivitySubGroup,
    StudySelection,
    StudySoAGroup,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_base_repository import (
    StudySelectionActivityBaseRepository,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity import (
    StudySelectionActivityAR,
    StudySelectionActivityVO,
)
from common import exceptions
from common.telemetry import trace_calls
from common.utils import convert_to_datetime


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    study_activity_subgroup_uid: str | None
    study_activity_subgroup_order: int | None
    activity_subgroup_uid: str | None
    study_activity_group_uid: str | None
    study_activity_group_order: int | None
    activity_group_uid: str | None
    activity_uid: str
    soa_group_term_uid: str
    study_soa_group_uid: str
    study_soa_group_order: int | None
    author_id: str
    change_type: str
    start_date: datetime.datetime
    show_activity_group_in_protocol_flowchart: bool | None
    show_activity_subgroup_in_protocol_flowchart: bool | None
    show_activity_in_protocol_flowchart: bool | None
    show_soa_group_in_protocol_flowchart: bool
    order: int
    end_date: datetime.datetime | None
    activity_version: str | None


class StudySelectionActivityRepository(
    StudySelectionActivityBaseRepository[StudySelectionActivityAR]
):
    _aggregate_root_type = StudySelectionActivityAR

    def _create_value_object_from_repository(
        self, selection: dict[Any, Any], acv: bool
    ) -> StudySelectionActivityVO:
        study_activity_subgroup = selection.get("study_activity_subgroup") or {}
        study_activity_group = selection.get("study_activity_group") or {}
        study_soa_group = selection.get("study_soa_group") or {}
        return StudySelectionActivityVO.from_input_values(
            study_selection_uid=selection["study_selection_uid"],
            study_activity_subgroup_uid=study_activity_subgroup.get("selection_uid"),
            study_activity_subgroup_order=study_activity_subgroup.get("order"),
            activity_subgroup_uid=study_activity_subgroup.get("activity_subgroup_uid"),
            activity_subgroup_name=study_activity_subgroup.get(
                "activity_subgroup_name"
            ),
            study_activity_group_uid=study_activity_group.get("selection_uid"),
            study_activity_group_order=study_activity_group.get("order"),
            activity_group_uid=study_activity_group.get("activity_group_uid"),
            activity_group_name=study_activity_group.get("activity_group_name"),
            study_uid=selection["study_uid"],
            activity_uid=selection["activity_uid"],
            activity_name=selection["activity_name"],
            activity_version=selection["activity_version"],
            activity_library_name=selection["activity_library_name"],
            soa_group_term_uid=study_soa_group["soa_group_term_uid"],
            soa_group_term_name=study_soa_group.get("soa_group_term_name"),
            study_soa_group_uid=study_soa_group["selection_uid"],
            study_soa_group_order=study_soa_group.get("order"),
            order=selection["order"],
            show_activity_in_protocol_flowchart=selection[
                "show_activity_in_protocol_flowchart"
            ],
            show_activity_group_in_protocol_flowchart=study_activity_group.get(
                "show_activity_group_in_protocol_flowchart", False
            ),
            show_activity_subgroup_in_protocol_flowchart=study_activity_subgroup.get(
                "show_activity_subgroup_in_protocol_flowchart", False
            ),
            show_soa_group_in_protocol_flowchart=study_soa_group.get(
                "show_soa_group_in_protocol_flowchart", False
            ),
            start_date=convert_to_datetime(value=selection["start_date"]),
            author_id=selection["author_id"],
            author_username=selection["author_username"],
            accepted_version=acv,
            keep_old_version=selection["keep_old_version"],
            keep_old_version_date=(
                convert_to_datetime(value=selection.get("keep_old_version_date"))
                if selection.get("keep_old_version_date")
                else None
            ),
        )

    def _additional_match(self, **kwargs) -> str:
        return """
            WITH sr, sv
            
            CALL (sr, sv) {
                OPTIONAL MATCH (sv)-[:HAS_STUDY_STANDARD_VERSION]->(study_standard_version:StudyStandardVersion)<-[:AFTER]-(:StudyAction)<-[:AUDIT_TRAIL]-(sr)
                OPTIONAL MATCH (study_standard_version)-[:HAS_CT_PACKAGE]->(ct_package:CTPackage)
                WHERE ct_package.uid CONTAINS "SDTM CT"
                RETURN datetime(toString(date(ct_package.effective_date)) + 'T23:59:59.999999000Z') AS terms_at_specific_datetime
            }
            
            MATCH (sv)-[:HAS_STUDY_ACTIVITY]->(sa:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue)<-[ver:HAS_VERSION]-(ar:ActivityRoot)<-[:CONTAINS_CONCEPT]-(lib:Library)
            
            WITH DISTINCT *
            
            CALL (sv, sa, terms_at_specific_datetime) {
                MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(soa_group_term_root:CTTermRoot)
                WHERE (soa_group)<-[:HAS_STUDY_SOA_GROUP]-(sv)
                MATCH (soa_group)<-[:AFTER]-(after_action:StudyAction)
                WITH *
                ORDER BY after_action.date DESC
                LIMIT 1
            
                WITH soa_group_term_root, terms_at_specific_datetime, soa_group
                MATCH (:Library)-[:CONTAINS_TERM]->(soa_group_term_root)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[term_version:HAS_VERSION]->(term_name_value:CTTermNameValue)
                WHERE term_version.status IN ['Final', 'Retired'] AND ( terms_at_specific_datetime IS NULL
                      OR term_version.start_date <= datetime(terms_at_specific_datetime)
                      AND (term_version.end_date IS NULL OR term_version.end_date > datetime(terms_at_specific_datetime)) )
                RETURN {uid: soa_group_term_root.uid, name: term_name_value.name} AS soa_group_term, soa_group
                ORDER BY term_version.start_date DESC
                LIMIT 1
            }
        """

    def _filter_clause(self, query_parameters: dict[Any, Any], **kwargs) -> str:
        # Filter on Activity, ActivityGroup or ActivityGroupNames if provided as a specific filter
        # This improves performance vs full service level filter
        activity_names = kwargs.get("activity_names")
        activity_group_names = kwargs.get("activity_group_names")
        activity_subgroup_names = kwargs.get("activity_subgroup_names")
        study_activity_subgroup_uid = kwargs.get("study_activity_subgroup_uid")
        study_soa_group_uid = kwargs.get("study_soa_group_uid")
        find_requested_study_activities = kwargs.get("find_requested_study_activities")
        filter_query = ""
        if (
            activity_names is not None
            or activity_group_names is not None
            or activity_subgroup_names is not None
            or study_activity_subgroup_uid is not None
            or study_soa_group_uid is not None
        ):
            filter_query += "\nWITH *\nWHERE\n"
            filter_list = []
            if activity_names is not None:
                filter_list.append("av.name IN $activity_names")
                query_parameters["activity_names"] = activity_names
            if activity_subgroup_names is not None:
                filter_list.append(
                    "size([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(sas:StudyActivitySubGroup)-"
                    "[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)"
                    " WHERE activity_subgroup_value.name IN $activity_subgroup_names | activity_subgroup_value.name]) > 0"
                )
                query_parameters["activity_subgroup_names"] = activity_subgroup_names
            if activity_group_names is not None:
                filter_list.append(
                    "size([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(sas:StudyActivityGroup)-"
                    "[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)"
                    " WHERE activity_group_value.name IN $activity_group_names | activity_group_value.name]) > 0"
                )
                query_parameters["activity_group_names"] = activity_group_names
            if study_activity_subgroup_uid is not None:
                filter_list.append(
                    """size([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(sas:StudyActivitySubGroup)
                            WHERE sas.uid=$study_activity_subgroup_uid | sas.uid]) > 0"""
                )
                query_parameters["study_activity_subgroup_uid"] = (
                    study_activity_subgroup_uid
                )
            if (
                find_requested_study_activities is not None
                and study_soa_group_uid is not None
                and study_activity_subgroup_uid is None
            ):
                filter_list.append(
                    """size([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soa_group:StudySoAGroup)
                            WHERE lib.name='Requested' AND soa_group.uid=$study_soa_group_uid AND NOT (sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->() | soa_group.uid]) > 0"""
                )
                query_parameters["study_soa_group_uid"] = study_soa_group_uid
            filter_query += " AND ".join(filter_list)
        return filter_query

    def _return_clause(self) -> str:
        return """
                RETURN DISTINCT
                sr.uid AS study_uid,
                sa.order AS order,
                sa.uid AS study_selection_uid,
                sa.show_activity_in_protocol_flowchart AS show_activity_in_protocol_flowchart,
                {
                    selection_uid: soa_group.uid, 
                    soa_group_term_uid: soa_group_term.uid,
                    soa_group_term_name: soa_group_term.name,
                    show_soa_group_in_protocol_flowchart: coalesce(soa_group.show_soa_group_in_protocol_flowchart, false),
                    order: soa_group.order
                } AS study_soa_group,
               head(apoc.coll.sortMulti([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_selection:StudyActivitySubGroup)
                -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
                WHERE (study_activity_subgroup_selection)<-[:HAS_STUDY_ACTIVITY_SUBGROUP]-(sv) |
                    {
                        selection_uid: study_activity_subgroup_selection.uid, 
                        activity_subgroup_uid:activity_subgroup_root.uid,
                        activity_subgroup_name:activity_subgroup_value.name,
                        show_activity_subgroup_in_protocol_flowchart:study_activity_subgroup_selection.show_activity_subgroup_in_protocol_flowchart,
                        order: study_activity_subgroup_selection.order,
                        date: head([(study_activity_subgroup_selection)<-[:AFTER]-(after_action:StudyAction) | after_action.date])
                    }], ['date'])) AS study_activity_subgroup,
                head(apoc.coll.sortMulti([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_selection:StudyActivityGroup)
                    -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
                    WHERE (study_activity_group_selection)<-[:HAS_STUDY_ACTIVITY_GROUP]-(sv) |
                    {
                        selection_uid: study_activity_group_selection.uid, 
                        activity_group_uid: activity_group_root.uid,
                        activity_group_name: activity_group_value.name,
                        show_activity_group_in_protocol_flowchart: study_activity_group_selection.show_activity_group_in_protocol_flowchart,
                        order: study_activity_group_selection.order,
                        date: head([(study_activity_group_selection)<-[:AFTER]-(after_action:StudyAction) | after_action.date])
                    }], ['date'])) AS study_activity_group,
                sa.accepted_version AS accepted_version,
                ar.uid AS activity_uid,
                av.name AS activity_name,
                sac.date AS start_date,
                sac.author_id AS author_id,
                COALESCE(head([(user:User)-[*0]-() WHERE user.user_id=sac.author_id | user.username]), sac.author_id) AS author_username,
                hv_ver.version AS activity_version,
                lib.name as activity_library_name,
                coalesce(sa.keep_old_version, false) AS keep_old_version,
                sa.keep_old_version_date AS keep_old_version_date
            """

    def get_selection_history(
        self,
        selection: dict[Any, Any],
        change_type: str,
        end_date: datetime.datetime | None,
    ):
        study_activity_subgroup = selection.get("study_activity_subgroup") or {}
        study_activity_group = selection.get("study_activity_group") or {}
        study_soa_group = selection.get("study_soa_group") or {}
        return SelectionHistory(
            study_selection_uid=selection["study_selection_uid"],
            study_activity_subgroup_uid=study_activity_subgroup.get("selection_uid"),
            study_activity_subgroup_order=study_activity_subgroup.get("order"),
            activity_subgroup_uid=study_activity_subgroup.get("activity_subgroup_uid"),
            study_activity_group_uid=study_activity_group.get("selection_uid"),
            study_activity_group_order=study_activity_group.get("order"),
            activity_group_uid=study_activity_group.get("activity_group_uid"),
            activity_uid=selection["activity_uid"],
            order=selection["order"],
            activity_version=selection["activity_version"],
            soa_group_term_uid=study_soa_group["soa_group_term_uid"],
            study_soa_group_uid=study_soa_group["selection_uid"],
            study_soa_group_order=study_soa_group.get("order"),
            author_id=selection["author_id"],
            change_type=change_type,
            start_date=convert_to_datetime(value=selection["start_date"]),
            show_activity_in_protocol_flowchart=selection[
                "show_activity_in_protocol_flowchart"
            ],
            show_activity_group_in_protocol_flowchart=study_activity_group.get(
                "show_activity_group_in_protocol_flowchart"
            ),
            show_activity_subgroup_in_protocol_flowchart=study_activity_subgroup.get(
                "show_activity_subgroup_in_protocol_flowchart"
            ),
            show_soa_group_in_protocol_flowchart=study_soa_group[
                "show_soa_group_in_protocol_flowchart"
            ],
            end_date=end_date,
        )

    def get_audit_trail_query(self, study_selection_uid: str | None):
        if study_selection_uid:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudyActivity { uid: $study_selection_uid})
            WITH sa
            MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sa:StudyActivity)
            WITH distinct(all_sa)
            """
        else:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivity)
            WITH DISTINCT all_sa
            """
        audit_trail_cypher += """
                    MATCH (all_sa)-[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue)

                    CALL (av) {
                      MATCH (av) <-[ver]-(ar:ActivityRoot)
                      WHERE ver.status = "Final"
                      RETURN ver as ver, ar as ar
                      ORDER BY ver.start_date DESC
                      LIMIT 1
                    }
                    WITH DISTINCT all_sa, ar, ver
                    ORDER BY all_sa.order ASC
                    MATCH (all_sa)<-[:AFTER]-(asa:StudyAction)
                    OPTIONAL MATCH (all_sa)<-[:BEFORE]-(bsa:StudyAction)
                    WITH all_sa, ar, asa, bsa, ver
                    ORDER BY all_sa.uid DESC, asa.date DESC
                    RETURN
                        all_sa.order AS order,
                        all_sa.uid AS study_selection_uid,
                        all_sa.show_activity_in_protocol_flowchart AS show_activity_in_protocol_flowchart,
                        head(apoc.coll.sortMulti([(all_sa)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(soa_group_term_root:CTTermRoot) | 
                        {
                            selection_uid: soa_group.uid, 
                            soa_group_term_uid: soa_group_term_root.uid,
                            show_soa_group_in_protocol_flowchart: coalesce(soa_group.show_soa_group_in_protocol_flowchart, false),
                            order: soa_group.order,
                            date: head([(soa_group)<-[:AFTER]-(after_action:StudyAction) | after_action.date])
                        }], ['date'])) AS study_soa_group,
                        head(apoc.coll.sortMulti([(all_sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_selection:StudyActivitySubGroup)
                            -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) | 
                            {
                                selection_uid: study_activity_subgroup_selection.uid, 
                                activity_subgroup_uid:activity_subgroup_root.uid,
                                show_activity_subgroup_in_protocol_flowchart:study_activity_subgroup_selection.show_activity_subgroup_in_protocol_flowchart,
                                order: study_activity_subgroup_selection.order,
                                date: head([(study_activity_subgroup_selection)<-[:AFTER]-(after_action:StudyAction) | after_action.date])
                            }], ['date'])) AS study_activity_subgroup,
                        head(apoc.coll.sortMulti([(all_sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_selection:StudyActivityGroup)
                            -[:HAS_SELECTED_ACTIVITY_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | 
                            {
                                selection_uid: study_activity_group_selection.uid, 
                                activity_group_uid: activity_group_root.uid,
                                show_activity_group_in_protocol_flowchart:study_activity_group_selection.show_activity_group_in_protocol_flowchart,
                                order: study_activity_group_selection.order,
                                date: head([(study_activity_group_selection)<-[:AFTER]-(after_action:StudyAction) | after_action.date])
                            }], ['date'])) AS study_activity_group,
                        ar.uid AS activity_uid,
                        asa.date AS start_date,
                        asa.author_id AS author_id,
                        labels(asa) AS change_type,
                        bsa.date AS end_date,
                        ver.version AS activity_version
                    """
        return audit_trail_cypher

    def get_study_selection_node_from_latest_study_value(
        self, study_value: StudyValue, study_selection: StudySelection
    ):
        return study_value.has_study_activity.get(
            uid=study_selection.study_selection_uid
        )

    def _add_new_selection(
        self,
        study_root: StudyRoot,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionActivityVO,
        audit_node: StudyAction,
        last_study_selection_node: StudyActivity,
        for_deletion: bool = False,
    ):
        # Build a single Cypher statement that MATCHes all dependency nodes, CREATEs the
        # StudyActivity node, and CREATEs all its relationships in one round-trip.
        match_lines = [
            "MATCH (activity_root:ActivityRoot {uid: $activity_uid})"
            "-[:HAS_VERSION {version: $activity_version}]->(latest_activity_value:ActivityValue)"
            " WITH * LIMIT 1",
            "MATCH (study_value:StudyValue) WHERE elementId(study_value) = $study_value_eid",
            "MATCH (study_soa_group:StudySoAGroup {uid:$study_soa_group_uid}) WHERE NOT (study_soa_group)-[:BEFORE]-()",
        ]
        params: dict[str, Any] = {
            "sa_uid": selection.study_selection_uid,
            "sa_order": order,
            "sa_show_activity": selection.show_activity_in_protocol_flowchart,
            "sa_keep_old": selection.keep_old_version,
            "sa_keep_old_date": selection.keep_old_version_date,
            "sa_accepted": selection.accepted_version,
            "activity_uid": selection.activity_uid,
            "activity_version": selection.activity_version,
            "study_soa_group_uid": selection.study_soa_group_uid,
            "study_value_eid": latest_study_value_node.element_id,
        }

        optional_matches: list[str] = []
        create_rels: list[str] = []

        if selection.study_activity_subgroup_uid:
            optional_matches.append(
                "MATCH (study_activity_subgroup:StudyActivitySubGroup {uid: $study_activity_subgroup_uid})"
                " WHERE NOT (study_activity_subgroup)-[:BEFORE]-()"
            )
            params["study_activity_subgroup_uid"] = (
                selection.study_activity_subgroup_uid
            )
            create_rels.append(
                "CREATE (sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup)"
            )

        if selection.study_activity_group_uid:
            optional_matches.append(
                "MATCH (study_activity_group:StudyActivityGroup {uid: $study_activity_group_uid})"
                " WHERE NOT (study_activity_group)-[:BEFORE]-()"
            )
            params["study_activity_group_uid"] = selection.study_activity_group_uid
            create_rels.append(
                "CREATE (sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group)"
            )

        create_node = (
            "CREATE (sa:StudyActivity:StudySelection {uid: $sa_uid, order: $sa_order,"
            " show_activity_in_protocol_flowchart: $sa_show_activity,"
            " keep_old_version: $sa_keep_old, keep_old_version_date: $sa_keep_old_date,"
            " accepted_version: $sa_accepted})"
        )
        create_core_rels = [
            "CREATE (sa)-[:HAS_SELECTED_ACTIVITY]->(latest_activity_value)",
            "CREATE (sa)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group)",
        ]
        if not for_deletion:
            create_core_rels.append("CREATE (study_value)-[:HAS_STUDY_ACTIVITY]->(sa)")

        all_lines = (
            match_lines
            + optional_matches
            + [create_node]
            + create_core_rels
            + create_rels
            + ["RETURN sa"]
        )
        results, _ = db.cypher_query("\n".join(all_lines), params, resolve_objects=True)
        if not results or not results[0]:
            raise exceptions.BusinessLogicException(
                msg=f"Failed to create StudyActivity node for '{selection.study_selection_uid}'."
            )
        study_activity_selection_node: StudyActivity = results[0][0]

        _manage_versioning_with_relations(
            study_root=study_root,
            action_type=type(audit_node),
            before=last_study_selection_node,
            after=study_activity_selection_node,
            exclude_relationships=[
                ActivityValue,
                StudySoAGroup,
                StudyActivitySubGroup,
                StudyActivityGroup,
            ],
            author_id=selection.author_id,
        )

    def generate_uid(self) -> str:
        return StudyActivity.get_next_free_uid_and_increment_counter()

    @trace_calls
    def delete_related_study_activity_schedules(
        self, study_uid: str, study_activity_uid: str, author_id: str
    ) -> list[Any]:
        """
        Deletes all related study activity schedules for a given study activity,
        by adding a DELETE action to their audit trail.
        """
        query = """
            MATCH 
                (sr:StudyRoot)-[:LATEST]->
                (sv:StudyValue)-->
                (s_activity:StudyActivity)-[:STUDY_ACTIVITY_HAS_SCHEDULE]->
                (ss:StudyActivitySchedule)<-[:AFTER]-
                (ss_action:StudyAction)
                WHERE 
                    s_activity.uid = $study_activity_uid
                    AND
                    sr.uid = $study_uid
                    AND
                    NOT EXISTS((sv)<-[:LATEST_LOCKED]-(sr))
                    AND
                    EXISTS((sv)-[:HAS_STUDY_ACTIVITY_SCHEDULE]->(ss))  // only live schedules; skip already soft-deleted ones

            //  CLONE NODE
            CALL apoc.refactor.cloneNodes(
                [ss],
                true //clone with relationships
            ) 
                YIELD input, output, error
            
            //GET input nodes
            MATCH (ss_old) 
                WHERE ID(ss_old)= input 
            CREATE (new_saction:StudyAction)
                SET new_saction:Delete
                SET new_saction.date = datetime()
                SET new_saction.author_id = $author_id
            CREATE (new_saction)<-[:AUDIT_TRAIL]-(sr)

            WITH ss_old,output, new_saction, sv

            //DISCONNECT NEW NODE
            MATCH 
                (output)<-[output_saction:AFTER]-
                (saction:StudyAction) // Delete from previous StudyAction, 
                                        //as previous action shouldn't be connected to the new one
            OPTIONAL MATCH 
                (output)<-[output_sv]-
                (:StudyValue)    // Delete StudyValue, because is being deleted
            OPTIONAL MATCH 
                (output)-[output_ss]-
                (ss_outbound:StudySelection) //Drop all StudySelections relationships to NON AVAILABLE nodes
                    WHERE NOT EXISTS ((ss_outbound)--(sv))

            //DISCONNECT OLD NODE
            OPTIONAL MATCH 
                (ss_old)<-[ss_old_sv]-
                (sv)  //From studyValue

            //DISCONNECT NEW
            DELETE output_saction
            DELETE output_sv
            DELETE output_ss
        
            MERGE 
                (output)<-[:AFTER]-
                (new_saction)
            MERGE
                (ss_old)<-[:BEFORE]-
                (new_saction)

            //DISCONNECT OLD NODE
            DELETE ss_old_sv

            RETURN DISTINCT output.uid
        """
        result = db.cypher_query(
            query,
            params={
                "study_activity_uid": study_activity_uid,
                "study_uid": study_uid,
                "author_id": author_id,
            },
        )
        return utils.db_result_to_list(result)

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    def activity_with_same_groupings_exists(
        self,
        study_uid: str,
        activity_name: str | None,
        activity_subgroup_uid: str | None,
        activity_group_uid: str | None,
        exclude_study_selection_uid: str | None = None,
    ) -> bool:
        """Check if a StudyActivity with the same activity name and groupings
        already exists in the study, optionally excluding a specific selection UID.
        """
        params: dict[str, Any] = {"study_uid": study_uid}
        exclude_clause = ""
        if exclude_study_selection_uid:
            exclude_clause = "AND sa.uid <> $exclude_uid"
            params["exclude_uid"] = exclude_study_selection_uid

        # Build match clauses depending on whether groupings are provided
        if activity_name is not None:
            name_clause = "AND av.name = $activity_name"
            params["activity_name"] = activity_name
        else:
            name_clause = "AND av.name IS NULL"

        if activity_subgroup_uid is not None:
            subgroup_clause = """AND EXISTS {
                MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(:StudyActivitySubGroup)
                    -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(:ActivitySubGroupValue)<-[:HAS_VERSION]-(asg_root:ActivitySubGroupRoot)
                WHERE asg_root.uid = $activity_subgroup_uid
            }"""
            params["activity_subgroup_uid"] = activity_subgroup_uid
        else:
            subgroup_clause = (
                "AND NOT (sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->()"
            )

        if activity_group_uid is not None:
            group_clause = """AND EXISTS {
                MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(:StudyActivityGroup)
                    -[:HAS_SELECTED_ACTIVITY_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(ag_root:ActivityGroupRoot)
                WHERE ag_root.uid = $activity_group_uid
            }"""
            params["activity_group_uid"] = activity_group_uid
        else:
            group_clause = "AND NOT (sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->()"

        query = f"""
            MATCH (:StudyRoot {{uid: $study_uid}})-[:LATEST]->(sv:StudyValue)-[:HAS_STUDY_ACTIVITY]->(sa:StudyActivity)
                -[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue)
            WHERE NOT (sa)<-[]-(:Delete)
                {exclude_clause}
                {name_clause}
                {subgroup_clause}
                {group_clause}
            RETURN sa.uid
            LIMIT 1
        """
        result, _ = db.cypher_query(query, params)
        return len(result) > 0

    @trace_calls
    def create_replaced_by_links_from_previous_version(
        self,
        study_uid: str,
        source_study_activity_uid: str,
        target_study_activity_uids: list[str],
    ) -> None:
        """
        Creates REPLACED_BY links from the previous version of a StudyActivity
        to one or more current StudyActivities in the latest StudyValue.
        """
        if not target_study_activity_uids:
            return

        query = """
            MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(edit_action:Edit)
                -[:AFTER]->(current_source:StudyActivity {uid: $source_study_activity_uid})
            WHERE NOT (current_source)-[:BEFORE]-() AND NOT (current_source)--(:Delete)
            WITH sr, edit_action
            ORDER BY edit_action.date DESC
            LIMIT 1

            MATCH (edit_action)-[:BEFORE]->(previous_source:StudyActivity {uid: $source_study_activity_uid})
            MATCH (sr)-[:LATEST]->(:StudyValue)-[:HAS_STUDY_ACTIVITY]->(target:StudyActivity)
            WHERE target.uid IN $target_study_activity_uids
                AND NOT (target)-[:BEFORE]-()
                AND NOT (target)--(:Delete)
            MERGE (previous_source)-[:REPLACED_BY]->(target)
        """
        db.cypher_query(
            query=query,
            params={
                "study_uid": study_uid,
                "source_study_activity_uid": source_study_activity_uid,
                "target_study_activity_uids": target_study_activity_uids,
            },
        )
