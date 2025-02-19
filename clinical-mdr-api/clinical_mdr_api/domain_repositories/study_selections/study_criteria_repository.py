import datetime
from dataclasses import dataclass

from neomodel import db

from clinical_mdr_api import utils
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.study_selections import StudyCriteria
from clinical_mdr_api.domain_repositories.models.syntax import (
    CriteriaRoot,
    CriteriaTemplateRoot,
)
from clinical_mdr_api.domains.study_selections.study_selection_criteria import (
    StudySelectionCriteriaAR,
    StudySelectionCriteriaVO,
)
from common.exceptions import BusinessLogicException
from common.utils import convert_to_datetime


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    syntax_object_uid: str
    author_id: str
    change_type: str
    start_date: datetime.datetime
    criteria_type_uid: str | None
    criteria_type_order: int | None
    status: str | None
    end_date: datetime.datetime | None
    syntax_object_version: str | None
    is_instance: bool = True
    key_criteria: bool = False


class StudySelectionCriteriaRepository:
    @staticmethod
    def _acquire_write_lock_study_value(uid: str) -> None:
        db.cypher_query(
            """
             MATCH (sr:StudyRoot {uid: $uid})
             REMOVE sr.__WRITE_LOCK__
             RETURN true
            """,
            {"uid": uid},
        )

    def _retrieves_all_data(
        self,
        study_uids: str | list[str] | None = None,
        criteria_type_name: str | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        study_value_version: str | None = None,
    ) -> tuple[StudySelectionCriteriaVO]:
        query = ""
        query_parameters = {}
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

        if criteria_type_name:
            criteria_type_query = f"""
                AND (term)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(:CTTermNameValue {{name_sentence_case: '{criteria_type_name}'}})
                """
        else:
            criteria_type_query = ""

        query += f"""
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_CRITERIA]->(sc:StudyCriteria)
            CALL {{
                WITH sc
                MATCH (sc)-[:HAS_SELECTED_CRITERIA]->(:CriteriaValue)<-[ver]-(cr:CriteriaRoot)<-[:HAS_CRITERIA]-(:CriteriaTemplateRoot)-[:HAS_TYPE]->(term:CTTermRoot)
                WHERE ver.status = "Final" {criteria_type_query}
                RETURN ver as ver, cr as obj, term.uid as term_uid, true as is_instance
                ORDER BY ver.start_date DESC
                LIMIT 1
            UNION
                WITH sc
                MATCH (sc)-[:HAS_SELECTED_CRITERIA_TEMPLATE]->(:CriteriaTemplateValue)<-[ver]-(ctr:CriteriaTemplateRoot)-[:HAS_TYPE]->(term:CTTermRoot)
                WHERE ver.status = "Final" {criteria_type_query}
                RETURN ver as ver, ctr as obj, term.uid as term_uid, false as is_instance
                ORDER BY ver.start_date DESC
                LIMIT 1
            }}
            WITH DISTINCT sr, term_uid, sc, obj, ver, is_instance
            ORDER BY term_uid, sc.order ASC
            MATCH (sc)<-[:AFTER]-(sa:StudyAction)
            RETURN
                sr.uid AS study_uid,
                term_uid AS criteria_type_uid,
                sc.order AS criteria_type_order,
                sc.uid AS study_selection_uid,
                sc.accepted_version AS accepted_version,
                obj.uid AS syntax_object_uid,
                sa.date AS start_date,
                sa.author_id AS author_id,
                ver.version AS syntax_object_version,
                is_instance AS is_instance,
                sc.key_criteria as key_criteria
            """

        all_criteria_selections = db.cypher_query(query, query_parameters)
        all_selections = []
        for selection in utils.db_result_to_list(all_criteria_selections):
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionCriteriaVO.from_input_values(
                study_uid=selection["study_uid"],
                criteria_type_uid=selection["criteria_type_uid"],
                criteria_type_order=selection["criteria_type_order"],
                study_selection_uid=selection["study_selection_uid"],
                syntax_object_uid=selection["syntax_object_uid"],
                syntax_object_version=selection["syntax_object_version"],
                is_instance=selection["is_instance"],
                key_criteria=selection["key_criteria"],
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
    ) -> list[StudySelectionCriteriaAR]:
        """
        Finds all the selected study criteria for all studies, and create the aggregate
        :return: List of StudySelectionCriteriaAR, potentially empty
        """
        all_selections = self._retrieves_all_data(
            project_name=project_name,
            project_number=project_number,
            study_uids=study_uids,
        )
        # Create a dictionary, with study_uid as key, and list of selections as value
        selection_aggregate_dict = {}
        selection_aggregates = []
        for selection in all_selections:
            if selection.study_uid in selection_aggregate_dict:
                selection_aggregate_dict[selection.study_uid].append(selection)
            else:
                selection_aggregate_dict[selection.study_uid] = [selection]
        # Then, create the list of VO from the dictionary
        for study_uid, selections in selection_aggregate_dict.items():
            selection_aggregates.append(
                StudySelectionCriteriaAR.from_repository_values(
                    study_uid=study_uid, study_criteria_selection=selections
                )
            )

        return selection_aggregates

    def find_by_study(
        self,
        study_uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
        criteria_type_name: str | None = None,
    ) -> StudySelectionCriteriaAR | None:
        """
        Finds all the selected study criteria for a given study, and creates the aggregate
        :param study_uid:
        :param for_update:
        :return:
        """

        if for_update:
            self._acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(
            study_uid,
            study_value_version=study_value_version,
            criteria_type_name=criteria_type_name,
        )
        selection_aggregate = StudySelectionCriteriaAR.from_repository_values(
            study_uid=study_uid, study_criteria_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def _get_audit_node(
        self, study_selection: StudySelectionCriteriaAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_criteria_selection:
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

    def _get_latest_study_value(self, study_uid: str) -> tuple[StudyRoot, StudyValue]:
        """Returns the study root and latest study value nodes for the given study, if re-ordering is allowed

        Args:
            study_uid (str): UID of the study

        Returns:
            tuple[StudyRoot, StudyValue]: Returned node objects

        Raises:
            BusinessLogicException: Returns an error if the study cannot be reordered or get new items
        """
        study_root_node = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value_node = study_root_node.latest_value.single()

        BusinessLogicException.raise_if(
            study_root_node.latest_locked.get_or_none() == latest_study_value_node,
            msg="You cannot add or reorder a study selection when the study is in a locked state.",
        )

        return study_root_node, latest_study_value_node

    def _list_selections_to_add_or_remove(
        self, closure: dict, criteria: dict
    ) -> tuple[dict, dict]:
        """Compares the current and target state of the selection and returns the lists of objects to add/remove to/from the selection

        Args:
            closure (dict): The closure object containing the current selection
            criteria (dict): The object containing the new target state of the selection

        Returns:
            tuple[dict, dict]: Returns two lists of selections to add and to remove
        """
        selections_to_remove = {}
        selections_to_add = {}

        # First, check for any removed items
        for criteria_type, criteria_list in closure.items():
            # check if object is removed from the selection list - delete has been called
            # two options to detect object is removed : list for given criteria type is empty or smaller than the list in the closure
            if (criteria_type not in criteria) or len(criteria_list) > len(
                criteria[criteria_type]
            ):
                # remove the last item from old list, as there will no longer be any study criteria with that high order
                selections_to_remove[criteria_type] = [
                    (len(criteria_list), criteria_list[-1])
                ]

        # Then, check for any added items
        # This has to be done by criteria type
        for criteria_type, criteria_list in criteria.items():
            # For each criteria in the current type, check if it is new
            for order, selected_object in enumerate(criteria_list, start=1):
                if criteria_type in closure:
                    _closure_data = closure[criteria_type]
                    # Nothing has been added, but an object might have been replaced
                    if len(_closure_data) > order - 1:
                        # check if anything has changed
                        if selected_object is not _closure_data[order - 1]:
                            # update the selection by removing the old if the old exists, and adding new selection
                            selections_to_remove.setdefault(criteria_type, []).append(
                                (order, _closure_data[order - 1])
                            )
                            selections_to_add.setdefault(criteria_type, []).append(
                                (order, selected_object)
                            )
                    else:
                        # else something new has been added
                        selections_to_add.setdefault(criteria_type, []).append(
                            (order, selected_object)
                        )
                else:
                    selections_to_add[criteria_type] = [(1, criteria_list[0])]

        return selections_to_remove, selections_to_add

    def save(self, study_selection: StudySelectionCriteriaAR, author_id: str) -> None:
        """
        Persist the set of selected study criteria from the aggregate to the database
        :param study_selection:
        :param author_id:
        """
        assert study_selection.repository_closure_data is not None

        # getting the latest study value node
        study_root_node, latest_study_value_node = self._get_latest_study_value(
            study_uid=study_selection.study_uid
        )
        # group closure by criteria type
        closure_group_by_type = {}
        for selected_object in study_selection.repository_closure_data:
            closure_group_by_type.setdefault(
                selected_object.criteria_type_uid, []
            ).append(selected_object)
        # group criteria by type
        criteria_group_by_type = {}
        for selected_object in study_selection.study_criteria_selection:
            criteria_group_by_type.setdefault(
                selected_object.criteria_type_uid, []
            ).append(selected_object)

        # process new/changed/deleted elements for each criteria type
        (
            selections_to_remove,
            selections_to_add,
        ) = self._list_selections_to_add_or_remove(
            closure=closure_group_by_type, criteria=criteria_group_by_type
        )

        # audit trail nodes dictionary, holds the new nodes created for the audit trail
        audit_trail_nodes = {}

        # loop through and remove selections
        for criteria_list in selections_to_remove.values():
            for selection in criteria_list:
                order = selection[0]
                selected_object = selection[1]
                last_study_selection_node = (
                    latest_study_value_node.has_study_criteria.get(
                        uid=selected_object.study_selection_uid
                    )
                )
                self._remove_old_selection_if_exists(
                    study_selection.study_uid, selected_object
                )
                audit_node = self._get_audit_node(
                    study_selection, selected_object.study_selection_uid
                )
                audit_node = self._set_before_audit_info(
                    audit_node, last_study_selection_node, study_root_node, author_id
                )
                audit_trail_nodes[selected_object.study_selection_uid] = audit_node
                if isinstance(audit_node, Delete):
                    self._add_new_selection(
                        latest_study_value_node,
                        order,
                        selected_object,
                        audit_node,
                        True,
                    )

        # loop through and add selections
        for criteria_list in selections_to_add.values():
            for selection in criteria_list:
                order = selection[0]
                selected_object = selection[1]
                if selected_object.study_selection_uid in audit_trail_nodes:
                    audit_node = audit_trail_nodes[selected_object.study_selection_uid]
                else:
                    audit_node = Create()
                    audit_node.author_id = selected_object.author_id
                    audit_node.date = selected_object.start_date
                    audit_node.save()
                    study_root_node.audit_trail.connect(audit_node)
                self._add_new_selection(
                    latest_study_value_node, order, selected_object, audit_node, False
                )

    def _remove_old_selection_if_exists(
        self, study_uid: str, study_selection: StudySelectionCriteriaVO
    ) -> None:
        db.cypher_query(
            """
            MATCH (:StudyRoot { uid: $study_uid})-[:LATEST]->(:StudyValue)-[rel:HAS_STUDY_CRITERIA]->(so:StudyCriteria { uid: $study_selection_uid})
            DELETE rel
            """,
            {
                "study_uid": study_uid,
                "study_selection_uid": study_selection.study_selection_uid,
            },
        )

    @staticmethod
    def _set_before_audit_info(
        audit_node: StudyAction,
        study_criteria_selection_node: StudyCriteria,
        study_root_node: StudyRoot,
        author_id: str,
    ) -> StudyAction:
        audit_node.author_id = author_id
        audit_node.date = datetime.datetime.now(datetime.timezone.utc)
        audit_node.save()

        audit_node.has_before.connect(study_criteria_selection_node)
        study_root_node.audit_trail.connect(audit_node)
        return audit_node

    def _add_new_selection(
        self,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionCriteriaVO,
        audit_node: StudyAction,
        for_deletion: bool = False,
    ):
        if selection.is_instance:
            # Get the criteria value
            criteria_root_node: CriteriaRoot = CriteriaRoot.nodes.get(
                uid=selection.syntax_object_uid
            )
            latest_criteria_value_node = criteria_root_node.get_value_for_version(
                selection.syntax_object_version
            )
        else:
            # Get the criteria template value
            criteria_template_root_node: CriteriaTemplateRoot = (
                CriteriaTemplateRoot.nodes.get(uid=selection.syntax_object_uid)
            )
            latest_criteria_template_value_node = (
                criteria_template_root_node.get_value_for_version(
                    selection.syntax_object_version
                )
            )

        # Create new criteria selection
        study_criteria_selection_node = StudyCriteria(
            order=order, key_criteria=selection.key_criteria
        )
        study_criteria_selection_node.uid = selection.study_selection_uid
        study_criteria_selection_node.accepted_version = selection.accepted_version
        study_criteria_selection_node.save()
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_criteria.connect(
                study_criteria_selection_node
            )
        # Connect new node with audit trail
        audit_node.has_after.connect(study_criteria_selection_node)

        # Connect new node with object value node
        if selection.is_instance:
            study_criteria_selection_node.has_selected_criteria.connect(
                latest_criteria_value_node
            )
        else:
            study_criteria_selection_node.has_selected_criteria_template.connect(
                latest_criteria_template_value_node
            )

    def generate_uid(self) -> str:
        return StudyCriteria.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(
        self,
        study_uid: str,
        criteria_type_uid: str | None = None,
        study_selection_uid: str | None = None,
    ):
        """
        returns the audit trail for study criteria either for a specific selection or for all study criteria for the study
        """
        if study_selection_uid:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sc:StudyCriteria { uid: $study_selection_uid})
            WITH sc
            MATCH (sc)-[:AFTER|BEFORE*0..]-(all_sc:StudyCriteria)
            WITH DISTINCT(all_sc)
            """
        else:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sc:StudyCriteria)
            WITH DISTINCT all_sc
            """
        specific_criteria_selections_audit_trail_query = (
            """
            CALL {
                WITH all_sc
                MATCH (all_sc)-[:HAS_SELECTED_CRITERIA]->(:CriteriaValue)<-[ver]-(cr:CriteriaRoot)<-[:HAS_CRITERIA]
                -(:CriteriaTemplateRoot)-[:HAS_TYPE]->(term:CTTermRoot)
                WHERE ver.status = 'Final'"""
            + (" AND term.uid=$criteria_type_uid" if criteria_type_uid else "")
            + """
                RETURN ver as ver, cr as obj, term.uid as term_uid, true as is_instance
                ORDER BY ver.start_date DESC
                LIMIT 1
            UNION
                WITH all_sc
                MATCH (all_sc)-[:HAS_SELECTED_CRITERIA_TEMPLATE]->(:CriteriaTemplateValue)<-[ver]-(ctr:CriteriaTemplateRoot)-[:HAS_TYPE]->(term:CTTermRoot)
                WHERE ver.status = 'Final'"""
            + (" AND term.uid=$criteria_type_uid" if criteria_type_uid else "")
            + """
                RETURN ver as ver, ctr as obj, term.uid as term_uid, false as is_instance
                ORDER BY ver.start_date DESC
                LIMIT 1
            }

            WITH DISTINCT term_uid, all_sc, obj, ver, is_instance
            ORDER BY term_uid, all_sc.order ASC
            MATCH (all_sc)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_sc)<-[:BEFORE]-(bsa:StudyAction)
            WITH term_uid, all_sc, obj, asa, bsa, ver, is_instance
            ORDER BY all_sc.uid, asa.date DESC
            RETURN
                term_uid AS criteria_type_uid,
                all_sc.order AS criteria_type_order,
                all_sc.uid AS study_selection_uid,
                obj.uid AS syntax_object_uid,
                asa.date AS start_date,
                asa.status AS status,
                asa.author_id AS author_id,
                labels(asa) AS change_type,
                bsa.date AS end_date,
                ver.version AS syntax_object_version,
                is_instance AS is_instance,
                all_sc.key_criteria as key_criteria
            """
        )
        specific_criteria_selections_audit_trail = db.cypher_query(
            cypher + specific_criteria_selections_audit_trail_query,
            {
                "study_uid": study_uid,
                "study_selection_uid": study_selection_uid,
                "criteria_type_uid": criteria_type_uid,
            },
        )
        result = []
        for res in utils.db_result_to_list(specific_criteria_selections_audit_trail):
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
                    syntax_object_uid=res["syntax_object_uid"],
                    author_id=res["author_id"],
                    change_type=change_type,
                    start_date=convert_to_datetime(value=res["start_date"]),
                    criteria_type_uid=res["criteria_type_uid"],
                    criteria_type_order=res["criteria_type_order"],
                    status=res["status"],
                    end_date=end_date,
                    syntax_object_version=res["syntax_object_version"],
                    is_instance=res["is_instance"],
                    key_criteria=res["key_criteria"],
                )
            )
        return result

    def find_selection_history(
        self,
        study_uid: str,
        criteria_type_uid: str | None = None,
        study_selection_uid: str | None = None,
    ) -> list[dict | None]:
        """
        Simple method to return all versions of a study criteria for a study.
        Optionally a specific selection uid is given to see only the response for a specific selection.
        """
        if study_selection_uid is not None:
            return self._get_selection_with_history(
                study_uid=study_uid,
                study_selection_uid=study_selection_uid,
            )
        return self._get_selection_with_history(
            study_uid=study_uid,
            criteria_type_uid=criteria_type_uid,
        )

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass
