import datetime
from dataclasses import dataclass
from typing import Any

from neomodel import db

from clinical_mdr_api import utils
from clinical_mdr_api.domain_repositories._utils.helpers import (
    acquire_write_lock_study_value,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.generic_repository import (
    _manage_versioning_with_relations,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermContext,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.study_selections import StudyObjective
from clinical_mdr_api.domain_repositories.models.syntax import (
    ObjectiveRoot,
    ObjectiveTemplateRoot,
    ObjectiveTemplateValue,
    ObjectiveValue,
)
from clinical_mdr_api.domains.study_selections.study_selection_objective import (
    StudySelectionObjectivesAR,
    StudySelectionObjectiveVO,
)
from common.config import settings
from common.exceptions import BusinessLogicException
from common.utils import convert_to_datetime

# from clinical_mdr_api.models.study_selections.study_selection


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    objective_uid: str | None
    objective_level_uid: str | None
    start_date: datetime.datetime
    status: str | None
    author_username: str
    change_type: str
    end_date: datetime.datetime | None
    order: int
    objective_version: str | None


class StudySelectionObjectiveRepository:

    def _retrieves_all_data(
        self,
        study_uids: str | list[str] | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        study_value_version: str | None = None,
    ) -> tuple[StudySelectionObjectiveVO]:
        query = ""
        query_parameters: dict[str, Any] = {}
        if study_uids:
            if isinstance(study_uids, str):
                study_uid_statement = "{uid: $uids}"
            else:
                study_uid_statement = "WHERE sr.uid IN $uids"
            if study_value_version:
                query = f"""
                    MATCH (sr:StudyRoot {study_uid_statement})-[l:HAS_VERSION{{status:'RELEASED', version:$study_value_version}}]->(sv:StudyValue)
                    """
                query_parameters["study_value_version"] = study_value_version
                query_parameters["uids"] = study_uids
            else:
                query = f"MATCH (sr:StudyRoot {study_uid_statement})-[l:LATEST]->(sv:StudyValue)"
                query_parameters["uids"] = study_uids
        else:
            if study_value_version:
                query = "MATCH (sr:StudyRoot)-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(sv:StudyValue)"
                query_parameters["study_value_version"] = study_value_version
            else:
                query = "MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)"

        if project_name is not None or project_number is not None:
            query += (
                "-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(proj:Project)"
            )
            filter_list = []
            if project_name is not None:
                filter_list.append("proj.name=$project_name")
                query_parameters["project_name"] = project_name
            if project_number is not None:
                filter_list.append("proj.project_number=$project_number")
                query_parameters["project_number"] = project_number
            query += " WHERE "
            query += " AND ".join(filter_list)

        query += """
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_OBJECTIVE]->(so:StudyObjective)
            CALL (so) {
                MATCH (so)-[:HAS_SELECTED_OBJECTIVE]->(:ObjectiveValue)<-[ver]-(or:ObjectiveRoot)
                WHERE ver.status = "Final"
                RETURN ver as ver, or as obj, true as is_instance
                ORDER BY ver.start_date DESC
                LIMIT 1
            UNION
                WITH so
                MATCH (so)-[:HAS_SELECTED_OBJECTIVE_TEMPLATE]->(:ObjectiveTemplateValue)<-[ver]-(otr:ObjectiveTemplateRoot)
                WHERE ver.status = "Final"
                RETURN ver as ver, otr as obj, false as is_instance
                ORDER BY ver.start_date DESC
                LIMIT 1
            }
            WITH DISTINCT sr, so, obj, ver, is_instance
            OPTIONAL MATCH (so)-[:HAS_OBJECTIVE_LEVEL]->(level_term_context:CTTermContext)-[:HAS_SELECTED_TERM]->(olr:CTTermRoot)
            OPTIONAL MATCH (level_term_context)-[:HAS_SELECTED_CODELIST]->(:CTCodelistRoot)-[has_term:HAS_TERM WHERE has_term.end_date IS NULL]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(olr)
            WITH sr, so, obj, ver, olr, has_term, is_instance
            ORDER BY has_term.order, so.order ASC
            MATCH (so)<-[:AFTER]-(sa:StudyAction)
            RETURN
                sr.uid AS study_uid,
                so.uid AS study_selection_uid,
                so.accepted_version AS accepted_version,
                obj.uid AS objective_uid,
                olr.uid AS objective_level_uid,
                has_term.order as objective_level_order,
                sa.date AS start_date,
                sa.author_id AS author_id,
                is_instance AS is_instance,
                ver.version AS objective_version
            """

        all_objective_selections = db.cypher_query(query, query_parameters)
        all_selections = []
        for selection in utils.db_result_to_list(all_objective_selections):
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionObjectiveVO.from_input_values(
                study_uid=selection["study_uid"],
                study_selection_uid=selection["study_selection_uid"],
                objective_uid=selection["objective_uid"],
                objective_version=selection["objective_version"],
                objective_level_uid=selection["objective_level_uid"],
                objective_level_order=selection["objective_level_order"],
                is_instance=selection["is_instance"],
                start_date=convert_to_datetime(value=selection["start_date"]),
                author_id=selection["author_id"],
                accepted_version=acv,
            )
            all_selections.append(selection_vo)
        return tuple(all_selections)

    def find_all(
        self,
        project_name: str | None = None,
        project_number: str | None = None,
        study_uids: list[str] | None = None,
    ) -> list[StudySelectionObjectivesAR]:
        """
        Finds all the selected study objectives for all studies, and create the aggregate
        :return: List of StudySelectionObjectivesAR, potentially empty
        """
        all_selections = self._retrieves_all_data(
            project_name=project_name,
            project_number=project_number,
            study_uids=study_uids,
        )
        # Create a dictionary, with study_uid as key, and list of selections as value
        selection_aggregate_dict: dict[str, Any] = {}
        selection_aggregates: list[Any] = []
        for selection in all_selections:
            if selection.study_uid in selection_aggregate_dict:
                selection_aggregate_dict[selection.study_uid].append(selection)
            else:
                selection_aggregate_dict[selection.study_uid] = [selection]  # type: ignore[index]
        # Then, create the list of VO from the dictionary
        for study_uid, selections in selection_aggregate_dict.items():
            selection_aggregates.append(
                StudySelectionObjectivesAR.from_repository_values(
                    study_uid=study_uid, study_objectives_selection=selections
                )
            )
        return selection_aggregates

    def find_by_study(
        self,
        study_uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
    ) -> StudySelectionObjectivesAR:
        """
        Finds all the selected study objectives for a given study, and creates the aggregate
        :param study_uid:
        :param for_update:
        :return:
        """
        if for_update:
            acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(
            study_uid, study_value_version=study_value_version
        )
        selection_aggregate = StudySelectionObjectivesAR.from_repository_values(
            study_uid=study_uid, study_objectives_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def _get_audit_node(
        self, study_selection: StudySelectionObjectivesAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_objectives_selection:
            all_current_ids.append(item.study_selection_uid)
        all_closure_ids = []
        for item in study_selection.repository_closure_data:
            all_closure_ids.append(item.study_selection_uid)
        # if uid is in current data
        if study_selection_uid in all_current_ids:
            # if uid is in closure data
            if study_selection_uid in all_closure_ids:
                return Edit()
            return Create()
        return Delete()

    # pylint: disable=unused-argument
    def save(self, study_selection: StudySelectionObjectivesAR, author_id: str) -> None:
        """
        Persist the set of selected study objectives from the aggregate to the database
        :param study_selection:
        :param author_id:
        """
        assert study_selection.repository_closure_data is not None

        # get the closure_data
        closure_data = study_selection.repository_closure_data
        closure_data_length = len(closure_data)

        # getting the latest study value node
        study_root_node = StudyRoot.nodes.get(uid=study_selection.study_uid)
        latest_study_value_node = study_root_node.latest_value.single()

        BusinessLogicException.raise_if(
            study_root_node.latest_locked.get_or_none() == latest_study_value_node,
            msg="You cannot add or reorder a study selection when the study is in a locked state.",
        )

        selections_to_remove = []
        selections_to_add = []

        # check if object is removed from the selection list - delete have been called
        if len(closure_data) > len(study_selection.study_objectives_selection):
            # remove the last item from old list, as there will no longer be any study objective with that high order
            selections_to_remove.append((len(closure_data), closure_data[-1]))

        # loop through new data - start=1 as order starts at 1 not at 0 and find what needs to be removed and added
        for order, selection in enumerate(
            study_selection.study_objectives_selection, start=1
        ):
            # check whether something new is added
            if closure_data_length > order - 1:
                # check if anything has changed
                if selection is not closure_data[order - 1]:
                    # update the selection by removing the old if the old exists, and adding new selection
                    selections_to_remove.append((order, closure_data[order - 1]))
                    selections_to_add.append((order, selection))
            else:
                # else something new have been added
                selections_to_add.append((order, selection))

        # audit trail nodes dictionary, holds the new nodes created for the audit trail
        audit_trail_nodes = {}

        # loop through and remove selections
        for order, study_objective in selections_to_remove:
            last_study_selection_node = latest_study_value_node.has_study_objective.get(
                uid=study_objective.study_selection_uid
            )
            audit_node = self._get_audit_node(
                study_selection, study_objective.study_selection_uid
            )
            audit_trail_nodes[study_objective.study_selection_uid] = (
                audit_node,
                last_study_selection_node,
            )
            if isinstance(audit_node, Delete):
                self._add_new_selection(
                    study_root_node,
                    latest_study_value_node,
                    order,
                    study_objective,
                    audit_node,
                    last_study_selection_node,
                    True,
                )

        # loop through and add selections
        for order, selection in selections_to_add:
            last_study_selection_node = None
            if selection.study_selection_uid in audit_trail_nodes:
                audit_node, last_study_selection_node = audit_trail_nodes[
                    selection.study_selection_uid
                ]
            else:
                audit_node = Create()
            self._add_new_selection(
                study_root_node,
                latest_study_value_node,
                order,
                selection,
                audit_node,
                last_study_selection_node,
                False,
            )

    def _add_new_selection(
        self,
        study_root: StudyRoot,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionObjectiveVO,
        audit_node: StudyAction,
        last_study_selection_node: StudyObjective,
        for_deletion: bool = False,
    ):
        # Create new objective selection
        study_objective_selection_node = StudyObjective(
            order=order,
            uid=selection.study_selection_uid,
            accepted_version=selection.accepted_version,
        ).save()

        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_objective.connect(
                study_objective_selection_node
            )

        # check if objective is set
        if selection.objective_uid:
            if selection.is_instance:
                # Get the objective value and connect new node with objective value
                objective_root_node: ObjectiveRoot = ObjectiveRoot.nodes.get(
                    uid=selection.objective_uid
                )
                latest_objective_value_node = objective_root_node.get_value_for_version(
                    selection.objective_version
                )
                study_objective_selection_node.has_selected_objective.connect(
                    latest_objective_value_node
                )
            else:
                # Get the objective template value
                objective_template_root_node: ObjectiveTemplateRoot = (
                    ObjectiveTemplateRoot.nodes.get(uid=selection.objective_uid)
                )
                latest_objective_template_value_node = (
                    objective_template_root_node.get_value_for_version(
                        selection.objective_version
                    )
                )
                study_objective_selection_node.has_selected_objective_template.connect(
                    latest_objective_template_value_node
                )

        # Set objective level if exists
        if selection.objective_level_uid:
            ct_term_root = CTTermRoot.nodes.get(uid=selection.objective_level_uid)
            selected_objective_level_node = (
                CTCodelistAttributesRepository().get_or_create_selected_term(
                    ct_term_root,
                    codelist_submission_value=settings.study_objective_level_cl_submval,
                    catalogue_name=settings.sdtm_ct_catalogue_name,
                )
            )
            study_objective_selection_node.has_objective_level.connect(
                selected_objective_level_node
            )
        _manage_versioning_with_relations(
            study_root=study_root,
            action_type=type(audit_node),
            before=last_study_selection_node,
            after=study_objective_selection_node,
            exclude_relationships=[
                ObjectiveValue,
                ObjectiveTemplateValue,
                CTTermContext,
            ],
            author_id=selection.author_id,
        )

    def study_objective_exists(self, study_objective_uid: str) -> bool:
        """
        Simple function checking whether a study objective exist for a uid
        :return: boolean value
        """
        study_objective_node = StudyObjective.nodes.first_or_none(
            uid=study_objective_uid
        )
        if study_objective_node is None:
            return False
        return True

    def generate_uid(self) -> str:
        return StudyObjective.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(
        self, study_uid: str, study_selection_uid: str | None = None
    ):
        """
        returns the audit trail for study objectives either for a specific selection or for all study objectives for the study
        """
        if study_selection_uid:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(so:StudyObjective { uid: $study_selection_uid})
            WITH so
            MATCH (so)-[:AFTER|BEFORE*0..]-(all_so:StudyObjective)
            WITH distinct(all_so)
            """
        else:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_so:StudyObjective)
            WITH DISTINCT all_so
            """
        specific_objective_selections_audit_trail = db.cypher_query(
            cypher + """
            MATCH (all_so)-[:HAS_SELECTED_OBJECTIVE]->(ov:ObjectiveValue)

            CALL (ov) {
              MATCH (ov) <-[ver]-(or:ObjectiveRoot) 
              WHERE ver.status = "Final"
              RETURN ver as ver, or as or
              ORDER BY ver.start_date DESC
              LIMIT 1
            }

            WITH DISTINCT all_so, or, ver
            OPTIONAL MATCH (all_so)-[:HAS_OBJECTIVE_LEVEL]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(olr:CTTermRoot)
            WITH DISTINCT all_so, or, olr, ver
            MATCH (all_so)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_so)<-[:BEFORE]-(bsa:StudyAction)
            WITH all_so, or, olr, asa, bsa, ver
                CALL (asa) {
                    OPTIONAL MATCH (author: User)
                    WHERE author.user_id = asa.author_id
                    RETURN coalesce(author.username, asa.author_id) AS author_username 
                }
            WITH *    
            ORDER BY all_so.uid, asa.date DESC
            RETURN
                all_so.uid AS study_selection_uid,
                or.uid AS objective_uid,
                olr.uid AS objective_level_uid,
                asa.date AS start_date,
                asa.status AS status,
                asa.author_id AS author_id,
                labels(asa) AS change_type,
                bsa.date AS end_date,
                all_so.order AS order,
                ver.version AS objective_version,
                author_username
                """,
            {"study_uid": study_uid, "study_selection_uid": study_selection_uid},
        )
        result = []
        for res in utils.db_result_to_list(specific_objective_selections_audit_trail):
            change_type = ""
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            if res["end_date"]:
                end_date = convert_to_datetime(value=res["end_date"])
            else:
                end_date = None
            result.append(
                SelectionHistory(
                    study_selection_uid=res["study_selection_uid"],
                    objective_uid=res["objective_uid"],
                    objective_level_uid=res["objective_level_uid"],
                    start_date=convert_to_datetime(value=res["start_date"]),
                    status=res["status"],
                    author_username=res["author_username"],
                    change_type=change_type,
                    end_date=end_date,
                    order=res["order"],
                    objective_version=res["objective_version"],
                )
            )
        return result

    def find_selection_history(
        self, study_uid: str, study_selection_uid: str | None = None
    ) -> list[SelectionHistory]:
        """
        Simple method to return all versions of a study objectives for a study.
        Optionally a specific selection uid is given to see only the response for a specific selection.
        """
        if study_selection_uid:
            return self._get_selection_with_history(
                study_uid=study_uid, study_selection_uid=study_selection_uid
            )
        return self._get_selection_with_history(study_uid=study_uid)

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass
