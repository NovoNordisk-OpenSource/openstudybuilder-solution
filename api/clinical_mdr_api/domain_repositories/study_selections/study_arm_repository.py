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
from clinical_mdr_api.domain_repositories.models.study_selections import StudyArm
from clinical_mdr_api.domains.enums import StudyDesignClassEnum
from clinical_mdr_api.domains.study_selections.study_selection_arm import (
    StudySelectionArmAR,
    StudySelectionArmVO,
)
from common.config import settings
from common.exceptions import BusinessLogicException
from common.telemetry import trace_calls
from common.utils import convert_to_datetime, get_db_result_as_dict


@dataclass
class SelectionHistoryArm:
    """Class for selection history items"""

    study_selection_uid: str
    study_uid: str | None
    arm_name: str
    arm_short_name: str
    arm_label: str | None
    arm_code: str | None
    arm_description: str | None
    arm_randomization_group: str | None
    arm_number_of_subjects: int | None
    arm_type: str | None
    # Study selection Versioning
    start_date: datetime.datetime
    author_id: str
    change_type: str
    end_date: datetime.datetime | None
    order: int
    status: str | None
    accepted_version: bool | None
    merge_branch_for_this_arm_for_sdtm_adam: bool


class StudySelectionArmRepository:

    def arm_specific_has_connected_cell(self, study_uid: str, arm_uid: str) -> bool:
        """
        Returns True if StudyArm with specified uid has connected at least one StudyDesignCell.
        :return:
        """

        sdc_node = (
            StudyArm.nodes.traverse("has_design_cell", "has_after")
            .filter(
                study_value__latest_value__uid=study_uid,
                uid=arm_uid,
                has_design_cell__study_value__latest_value__uid=study_uid,
            )
            .resolve_subgraph()
        )
        return len(sdc_node) > 0

    def get_arms_branches_and_cohorts(
        self,
        study_uid: str | None = None,
        study_value_version: str | None = None,
    ) -> list[dict[str, Any]]:
        query = ""
        query_parameters = {}
        if study_value_version:
            if study_uid:
                query = "MATCH (sr:StudyRoot { uid: $uid})-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(sv:StudyValue)"
                query_parameters["study_value_version"] = study_value_version
                query_parameters["uid"] = study_uid
            else:
                query = "MATCH (sr:StudyRoot)-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(sv:StudyValue)"
                query_parameters["study_value_version"] = study_value_version
        else:
            if study_uid:
                query = "MATCH (sr:StudyRoot { uid: $uid})-[l:LATEST]->(sv:StudyValue)"
                query_parameters["uid"] = study_uid
            else:
                query = "MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)"

        query += """
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_ARM]->(sar:StudyArm)
            WITH DISTINCT sr, sv, sar

            // Get StudyCohorts
            OPTIONAL MATCH (sv)-[:HAS_STUDY_COHORT]->(study_cohorts:StudyCohort)
            WITH DISTINCT  sr, sv, sar, study_cohorts.uid as cohort_uid

            // Get latest version of StudyCohorts
            CALL (cohort_uid) {
                MATCH (study_cohort:StudyCohort {uid:cohort_uid})-[:AFTER]-(action:StudyAction)
                WITH study_cohort, action
                ORDER BY action.date ASC
                WITH last(collect(study_cohort)) as study_cohort
                RETURN CASE WHEN exists((study_cohort)--(:Delete)) THEN NULL ELSE study_cohort END AS study_cohort
            }

            // Get StudyBranchArms
            OPTIONAL MATCH (study_cohort)<-[:STUDY_BRANCH_ARM_HAS_COHORT]-(study_branch_arms:StudyBranchArm)-[:STUDY_ARM_HAS_BRANCH_ARM]-(sar)
            OPTIONAL MATCH (sv)-[:HAS_STUDY_BRANCH_ARM]->(study_branch_arms)
            WITH DISTINCT study_branch_arms, sr, sar, study_cohort
            ORDER BY study_branch_arms.order
            WITH DISTINCT study_branch_arms.uid as branch_arm_uid, sr, sar, study_cohort

            // Get latest version of StudyBranchArms
            CALL (branch_arm_uid) {
                MATCH (study_branch_arm:StudyBranchArm {uid:branch_arm_uid})-[:AFTER]-(action:StudyAction)
                WITH study_branch_arm, action
                ORDER BY action.date ASC
                WITH last(collect(study_branch_arm)) as branch_arm
                RETURN CASE WHEN exists((branch_arm)--(:Delete)) THEN NULL ELSE branch_arm END AS branch_arm
            }

            // Collect StudyBranchArms for given StudyCohort
            WITH sr, sar, study_cohort, 
                collect(branch_arm {
                    .uid,
                    .name,
                    .short_name,
                    .randomization_group,
                    .branch_arm_code,
                    .number_of_subjects
                }) as branch_arms
            ORDER BY study_cohort.order, sar.order
            WITH sr, sar, 
                collect(study_cohort {
                    .uid,
                    .name,
                    .short_name,
                    number_of_subjects: apoc.coll.sum([branch_arm in branch_arms WHERE branch_arm.number_of_subjects is not null | branch_arm.number_of_subjects]),
                    study_branch_arms:branch_arms
                }) AS study_cohorts
            RETURN DISTINCT 
                sr.uid AS study_uid,
                sar.uid AS uid,
                sar.name AS name,
                sar.short_name AS short_name,
                sar.label AS label,
                apoc.coll.sum([cohort in study_cohorts WHERE cohort.number_of_subjects is not null | cohort.number_of_subjects])AS number_of_subjects,
                study_cohorts
        """

        rows, columns = db.cypher_query(query, query_parameters)
        return [get_db_result_as_dict(row, columns) for row in rows]

    def _retrieves_all_data(
        self,
        study_uid: str | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        study_value_version: str | None = None,
    ) -> tuple[StudySelectionArmVO]:
        query = ""
        query_parameters: dict[str, Any] = {}
        if study_value_version:
            if study_uid:
                query = "MATCH (sr:StudyRoot { uid: $uid})-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(sv:StudyValue)"
                query_parameters["study_value_version"] = study_value_version
                query_parameters["uid"] = study_uid
            else:
                query = "MATCH (sr:StudyRoot)-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(sv:StudyValue)"
                query_parameters["study_value_version"] = study_value_version
        else:
            if study_uid:
                query = "MATCH (sr:StudyRoot { uid: $uid})-[l:LATEST]->(sv:StudyValue)"
                query_parameters["uid"] = study_uid
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
        query_parameters["is_cohort_stepper_defined"] = (
            StudyDesignClassEnum.STUDY_WITH_COHORTS_BRANCHES_AND_SUBPOPULATIONS.value
        )
        query += """
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_ARM]->(sar:StudyArm)
            WITH DISTINCT sr, sar, sv
            OPTIONAL MATCH (sar)-[:HAS_ARM_TYPE]->(st:CTTermContext)-[:HAS_SELECTED_TERM]->(elr:CTTermRoot)
            OPTIONAL MATCH (sv)-[:HAS_STUDY_BRANCH_ARM]-(bars:StudyBranchArm)<-[:STUDY_ARM_HAS_BRANCH_ARM]-(sar)
            WITH DISTINCT 
                bars.uid as branch_arm_uid, elr, sr, sar,
                exists((sv)-[:HAS_STUDY_DESIGN_CLASS]->(:StudyDesignClass {value:$is_cohort_stepper_defined})) AS is_cohort_stepper_defined
            CALL (branch_arm_uid) {
                MATCH (study_branch_arm:StudyBranchArm {uid:branch_arm_uid})-[:AFTER]-(action:StudyAction)
                WITH study_branch_arm, action
                ORDER BY action.date ASC
                WITH last(collect(study_branch_arm)) as study_branch_arm
                RETURN CASE WHEN exists((study_branch_arm)--(:Delete)) THEN NULL ELSE study_branch_arm END AS study_branch_arm
            }
            MATCH (sar)<-[:AFTER]-(sa:StudyAction)
            WITH DISTINCT elr, sr, sar, sa, sum(study_branch_arm.number_of_subjects) as branch_sum, is_cohort_stepper_defined
            RETURN DISTINCT 
                sr.uid AS study_uid,
                sar.uid AS study_selection_uid,
                sar.name AS arm_name,
                sar.short_name AS arm_short_name,
                sar.label AS arm_label,
                sar.arm_code AS arm_code,
                sar.description AS arm_description,
                sar.order AS order,
                sar.accepted_version AS accepted_version,
                CASE is_cohort_stepper_defined
                    WHEN true THEN branch_sum
                    ELSE sar.number_of_subjects
                END AS number_of_subjects,
                sar.randomization_group AS randomization_group,
                coalesce(sar.merge_branch_for_this_arm_for_sdtm_adam, false) AS merge_branch_for_this_arm_for_sdtm_adam,
                elr.uid AS arm_type_uid,
                sar.text AS text,
                sa.date AS start_date,
                sa.author_id AS author_id
                ORDER BY order
            """

        all_arm_selections = db.cypher_query(query, query_parameters)
        all_selections = []

        for selection in utils.db_result_to_list(all_arm_selections):
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionArmVO.from_input_values(
                author_id=selection["author_id"],
                study_uid=selection["study_uid"],
                name=selection["arm_name"],
                short_name=selection["arm_short_name"],
                label=selection["arm_label"],
                code=selection["arm_code"],
                description=selection["arm_description"],
                study_selection_uid=selection["study_selection_uid"],
                arm_type_uid=selection["arm_type_uid"],
                number_of_subjects=selection["number_of_subjects"],
                randomization_group=selection["randomization_group"],
                merge_branch_for_this_arm_for_sdtm_adam=selection[
                    "merge_branch_for_this_arm_for_sdtm_adam"
                ],
                start_date=convert_to_datetime(value=selection["start_date"]),
                accepted_version=selection["accepted_version"],
            )
            all_selections.append(selection_vo)
        return tuple(all_selections)

    def find_all(
        self,
        project_name: str | None = None,
        project_number: str | None = None,
    ) -> list[StudySelectionArmAR]:
        """
        Finds all the selected study endpoints for all studies, and create the aggregate
        :return: List of StudySelectionArmAR, potentially empty
        """
        all_selections = self._retrieves_all_data(
            project_name=project_name,
            project_number=project_number,
        )
        # Create a dictionary, with study_uid as key, and list of selections as value
        selection_aggregate_dict: dict[Any, Any] = {}
        selection_aggregates = []
        for selection in all_selections:
            if selection.study_uid in selection_aggregate_dict:
                selection_aggregate_dict[selection.study_uid].append(selection)
            else:
                selection_aggregate_dict[selection.study_uid] = [selection]
        # Then, create the list of VO from the dictionary
        for study_uid, selections in selection_aggregate_dict.items():
            selection_aggregates.append(
                StudySelectionArmAR.from_repository_values(
                    study_uid=study_uid, study_arms_selection=selections
                )
            )
        return selection_aggregates

    @trace_calls(
        args=[1, 2, 3], kwargs=["study_uid", "for_update", "study_value_version"]
    )
    def find_by_study(
        self,
        study_uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
    ) -> StudySelectionArmAR:
        """
        Finds all the selected study arms for a given study
        :param study_uid:
        :param for_update:
        :return:
        """
        if for_update:
            acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(
            study_uid, study_value_version=study_value_version
        )
        selection_aggregate = StudySelectionArmAR.from_repository_values(
            study_uid=study_uid, study_arms_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def _get_audit_node(
        self, study_selection: StudySelectionArmAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_arms_selection:
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
    def save(self, study_selection: StudySelectionArmAR, author_id: str) -> None:
        """
        Persist the set of selected study arms from the aggregate to the database
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
        if len(closure_data) > len(study_selection.study_arms_selection):
            # remove the last item from old list, as there will no longer be any study objective with that high order
            selections_to_remove.append((len(closure_data), closure_data[-1]))

        # loop through new data - start=1 as order starts at 1 not at 0 and find what needs to be removed and added
        for order, selection in enumerate(
            study_selection.study_arms_selection, start=1
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
        # dictionary of last nodes to traverse to their old connections
        last_nodes = {}
        # loop through and remove selections
        for order, selection in selections_to_remove:
            # traverse --> study_value__study_arm__uid
            last_study_selection_node = latest_study_value_node.has_study_arm.get(
                uid=selection.study_selection_uid
            )
            # detect if the action should be create, delete or edit, then create audit node of the that StudyAction type
            audit_node = self._get_audit_node(
                study_selection, selection.study_selection_uid
            )

            # storage of the removed node audit trail to after put the "after" relationship to the new one
            audit_trail_nodes[selection.study_selection_uid] = audit_node
            # storage of the removed node to after get its connections
            last_nodes[selection.study_selection_uid] = last_study_selection_node
            if isinstance(audit_node, Delete):
                self._add_new_selection(
                    study_root_node,
                    latest_study_value_node,
                    order,
                    selection,
                    audit_node,
                    for_deletion=True,
                    before_node=last_study_selection_node,
                )

        # loop through and add selections
        for order, selection in selections_to_add:
            # create last_study_selection_node None as the new study_selection could not have an audit trial node
            last_study_selection_node = None
            # if the study selection already has an audit trail node
            if selection.study_selection_uid in audit_trail_nodes:
                # extract the audit_trail_node
                audit_node = audit_trail_nodes[selection.study_selection_uid]
                # extract the last "AFTER" selection that now is "BEFORE"
                last_study_selection_node = last_nodes[selection.study_selection_uid]
            else:
                # if the audi_node doesn't exists, then create a new one
                audit_node = Create()

            self._add_new_selection(
                study_root_node,
                latest_study_value_node,
                order,
                selection,
                audit_node,
                for_deletion=False,
                before_node=last_study_selection_node,
            )

    @staticmethod
    def arm_exists_by(
        db_property: str, value: str, arm_vo: StudySelectionArmVO
    ) -> StudyArm | None:
        kwarg_value = getattr(arm_vo, value)
        arm_node = (
            StudyArm.nodes.has(study_value=True)
            .filter(
                uid__ne=arm_vo.study_selection_uid,
                study_value__latest_value__uid=arm_vo.study_uid,
            )
            .get_or_none(**{db_property: kwarg_value})
        )
        return arm_node

    @staticmethod
    def _add_new_selection(
        study_root: StudyRoot,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionArmVO,
        audit_node: StudyAction,
        for_deletion: bool = False,
        before_node: StudyArm | None = None,
    ):
        # Create new arm selection
        study_arm_selection_node: StudyArm = StudyArm(
            uid=selection.study_selection_uid,
            order=order,
            name=selection.name,
            short_name=selection.short_name,
            label=selection.label,
            arm_code=selection.code,
            description=selection.description,
            randomization_group=selection.randomization_group,
            number_of_subjects=selection.number_of_subjects,
            merge_branch_for_this_arm_for_sdtm_adam=selection.merge_branch_for_this_arm_for_sdtm_adam,
            accepted_version=selection.accepted_version,
        ).save()

        # Connect new node with study value
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_arm.connect(study_arm_selection_node)

        # check if arm type is set
        if selection.arm_type_uid:
            # find the CTTermRoot (but be sure that it is the actual one!!)
            study_arm_type = CTTermRoot.nodes.get(uid=selection.arm_type_uid)

            selected_arm_type_node = (
                CTCodelistAttributesRepository().get_or_create_selected_term(
                    study_arm_type,
                    codelist_submission_value=settings.study_arm_type_cl_submval,
                    catalogue_name=settings.sdtm_ct_catalogue_name,
                )
            )
            # connect to node
            # pylint: disable=no-member
            study_arm_selection_node.arm_type.connect(selected_arm_type_node)

        _manage_versioning_with_relations(
            study_root=study_root,
            action_type=type(audit_node),
            before=before_node,
            after=study_arm_selection_node,
            exclude_relationships=[CTTermContext],
            author_id=selection.author_id,
        )

    def generate_uid(self) -> str:
        return StudyArm.get_next_free_uid_and_increment_counter()

    def arm_specific_exists_by_uid(self, uid: str) -> bool:
        """
        Returns True if StudyArm with specified uid exists.
        :return:
        """
        query = """
            MATCH (study_arm:StudyArm {uid: $uid})
            RETURN study_arm
            """
        result, _ = db.cypher_query(query, {"uid": uid})
        return len(result) > 0

    def _get_selection_with_history(
        self, study_uid: str, study_selection_uid: str | None = None
    ):
        """
        returns the audit trail for study arm either for a specific selection or for all study arm for the study
        """
        if study_selection_uid:
            cypher = """
                    MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudyArm { uid: $study_selection_uid})
                    WITH sa
                    MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sa:StudyArm)
                    WITH distinct(all_sa)
                    """
        else:
            cypher = """
                    MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyArm)
                    WITH DISTINCT all_sa
                    """
        specific_arm_selections_audit_trail = db.cypher_query(
            cypher + """
            WITH DISTINCT all_sa
            OPTIONAL MATCH (all_sa)-[:HAS_ARM_TYPE]->(st:CTTermContext)-[:HAS_SELECTED_TERM]->(at:CTTermRoot)
            OPTIONAL MATCH (bars:StudyBranchArm)<-[:STUDY_ARM_HAS_BRANCH_ARM]-(all_sa)
            WITH DISTINCT bars.uid as branch_arm_uid, at, all_sa 
            CALL (branch_arm_uid) {
                MATCH (study_branch_arm:StudyBranchArm {uid:branch_arm_uid})-[:AFTER]-(action:StudyAction)
                WITH study_branch_arm, action
                ORDER BY action.date ASC
                WITH collect(study_branch_arm) as branch_arms
                RETURN last(branch_arms) AS study_branch_arm
            }
            WITH DISTINCT all_sa, at, sum(study_branch_arm.number_of_subjects) as branch_sum
            ORDER BY all_sa.order ASC
            MATCH (all_sa)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_sa)<-[:BEFORE]-(bsa:StudyAction)
            WITH all_sa, asa, bsa, at, branch_sum
            ORDER BY all_sa.uid, asa.date DESC
            RETURN
                all_sa.uid AS study_selection_uid,
                all_sa.name AS arm_name,
                all_sa.short_name AS arm_short_name,
                all_sa.label AS arm_label,
                all_sa.arm_code AS arm_code,
                all_sa.description AS arm_description,
                all_sa.order AS order,
                all_sa.accepted_version AS accepted_version,
                CASE branch_sum
                    WHEN 0 THEN all_sa.number_of_subjects 
                    ELSE branch_sum
                END AS number_of_subjects,
                all_sa.randomization_group AS randomization_group,
                coalesce(all_sa.merge_branch_for_this_arm_for_sdtm_adam, false) AS merge_branch_for_this_arm_for_sdtm_adam,
                at.uid AS arm_type_uid,
                all_sa.text AS text,
                asa.date AS start_date,
                asa.author_id AS author_id,
                labels(asa) AS change_type,
                bsa.date AS end_date
            """,
            {"study_uid": study_uid, "study_selection_uid": study_selection_uid},
        )
        result = []
        for res in utils.db_result_to_list(specific_arm_selections_audit_trail):
            change_type = ""
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            end_date = (
                convert_to_datetime(value=res["end_date"]) if res["end_date"] else None
            )
            result.append(
                SelectionHistoryArm(
                    study_selection_uid=res["study_selection_uid"],
                    study_uid=study_uid,
                    arm_name=res["arm_name"],
                    arm_short_name=res["arm_short_name"],
                    arm_label=res["arm_label"],
                    arm_code=res["arm_code"],
                    arm_description=res["arm_description"],
                    arm_randomization_group=res["randomization_group"],
                    arm_number_of_subjects=res["number_of_subjects"],
                    arm_type=res["arm_type_uid"],
                    merge_branch_for_this_arm_for_sdtm_adam=res[
                        "merge_branch_for_this_arm_for_sdtm_adam"
                    ],
                    start_date=convert_to_datetime(value=res["start_date"]),
                    author_id=res["author_id"],
                    change_type=change_type,
                    end_date=end_date,
                    accepted_version=res["accepted_version"],
                    status=None,
                    order=res["order"],
                )
            )
        return result

    def find_selection_history(
        self, study_uid: str, study_selection_uid: str | None = None
    ) -> list[SelectionHistoryArm]:
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
