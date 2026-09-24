import datetime
from dataclasses import dataclass
from typing import Any

from neomodel import db

from clinical_mdr_api import utils
from clinical_mdr_api.domain_repositories._utils.helpers import (
    acquire_write_lock_study_value,
)
from clinical_mdr_api.domain_repositories.generic_repository import (
    _manage_versioning_with_relations,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyArm,
    StudyBranchArm,
    StudyCohort,
)
from clinical_mdr_api.domains.enums import StudyDesignClassEnum
from clinical_mdr_api.domains.study_selections.study_selection_cohort import (
    StudySelectionCohortAR,
    StudySelectionCohortVO,
)
from common.exceptions import BusinessLogicException
from common.utils import convert_to_datetime


@dataclass
class SelectionHistoryCohort:
    """Class for selection history items"""

    study_selection_uid: str
    study_uid: str | None
    cohort_name: str | None
    cohort_short_name: str | None
    cohort_code: str | None
    cohort_description: str | None
    cohort_number_of_subjects: int | None
    branch_arm_roots: list[str] | None
    arm_roots: list[str] | None
    # Study selection Versioning
    start_date: datetime.datetime
    author_id: str
    change_type: str
    end_date: datetime.datetime | None
    order: int
    status: str | None
    accepted_version: bool | None


class StudySelectionCohortRepository:

    def _retrieves_all_data(
        self,
        study_uid: str | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        arm_uid: str | None = None,
        study_value_version: str | None = None,
    ) -> tuple[StudySelectionCohortVO]:
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
            MATCH (sv)-[:HAS_STUDY_COHORT]->(sar:StudyCohort)
            WITH DISTINCT sr, sv, sar, exists((sv)-[:HAS_STUDY_DESIGN_CLASS]->(:StudyDesignClass {value:$is_cohort_stepper_defined})) AS is_cohort_stepper_defined
            CALL apoc.do.case([

                // The path to StudyArm goes through StudyBranchArm
                is_cohort_stepper_defined=true,
                'OPTIONAL MATCH (sar)<-[:STUDY_BRANCH_ARM_HAS_COHORT]-(bars:StudyBranchArm)<-[:STUDY_ARM_HAS_BRANCH_ARM]-(ars:StudyArm)<-[:HAS_STUDY_ARM]-(sv)
                OPTIONAL MATCH (sv)-[:HAS_STUDY_BRANCH_ARM]->(bars)
                RETURN ars AS ars, bars AS bars',

                // The path to StudyArm goes directly by a relationship
                is_cohort_stepper_defined=false,
                'OPTIONAL MATCH (sar)<-[:STUDY_ARM_HAS_COHORT]-(ars:StudyArm)<-[:HAS_STUDY_ARM]-(sv)
                OPTIONAL MATCH (sar)<-[:STUDY_BRANCH_ARM_HAS_COHORT]-(bars:StudyBranchArm)<-[:HAS_STUDY_BRANCH_ARM]-(sv)
                RETURN ars AS ars, bars AS bars'
            ],
            '',
            {
                is_cohort_stepper_defined: is_cohort_stepper_defined,
                sar: sar,
                sv: sv
            })
            YIELD value
            WITH DISTINCT value.bars.uid AS branch_arm_uid, value.ars AS ars, sr, sar, is_cohort_stepper_defined
            ORDER BY ars.order

            CALL (branch_arm_uid) {
                MATCH (study_branch_arm:StudyBranchArm {uid:branch_arm_uid})-[:AFTER]-(action:StudyAction)
                WITH study_branch_arm, action
                ORDER BY action.date ASC
                WITH last(collect(study_branch_arm)) as study_branch_arm
                RETURN CASE WHEN exists((study_branch_arm)--(:Delete)) THEN NULL ELSE study_branch_arm END AS study_branch_arm
            }

            // Get latest available version of given StudyArm
            CALL apoc.do.case([
                // If defined by CohortStepper and path to StudyArm goes through StudyBranchArm we need to check
                is_cohort_stepper_defined=true,
                '
                WITH ars, study_branch_arm
                OPTIONAL MATCH (study_branch_arm)<-[:STUDY_ARM_HAS_BRANCH_ARM]-(study_arm:StudyArm {uid:ars.uid})-[:AFTER]-(action:StudyAction)
                WITH study_arm, action
                ORDER BY action.date ASC
                WITH last(collect(study_arm)) as study_arm
                RETURN CASE WHEN exists((study_arm)--(:Delete)) THEN NULL ELSE study_arm END AS study_arm
                ',

                // The path to StudyArm goes directly by a relationship
                is_cohort_stepper_defined=false,
                'RETURN ars as study_arm'
            ],
            '',
            {
                is_cohort_stepper_defined: is_cohort_stepper_defined,
                ars: ars,
                study_branch_arm: study_branch_arm
            })
            YIELD value
            WITH DISTINCT 
                sr,
                sar,
                collect(DISTINCT value.study_arm.uid) AS arm_root_uids, 
                sum(study_branch_arm.number_of_subjects) as branch_sum, 
                collect(DISTINCT study_branch_arm.uid) AS branch_arm_root_uids,
                is_cohort_stepper_defined
            
            MATCH (sar)<-[:AFTER]-(sa:StudyAction)
        """

        if arm_uid:
            filter_by_arm_uid = """
            WHERE head([(study_arm:StudyArm)-[:STUDY_ARM_HAS_COHORT]->(sar) | study_arm.uid])=$arm_uid"""
            query += filter_by_arm_uid
            query_parameters["arm_uid"] = arm_uid
        query += """
            RETURN DISTINCT 
                sr.uid AS study_uid,
                sar.uid AS study_selection_uid,
                sar.name AS cohort_name,
                sar.short_name AS cohort_short_name,
                sar.cohort_code AS cohort_code,
                sar.description AS cohort_description,
                sar.order AS order,
                sar.accepted_version AS accepted_version,                
                CASE is_cohort_stepper_defined
                    WHEN true THEN branch_sum
                    ELSE sar.number_of_subjects
                END AS number_of_subjects,
                branch_arm_root_uids,
                arm_root_uids,
                sar.text AS text,
                sa.date AS start_date,
                sa.author_id AS author_id
                ORDER BY order
            """

        all_cohort_selections = db.cypher_query(query, query_parameters)
        all_selections = []

        for selection in utils.db_result_to_list(all_cohort_selections):
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionCohortVO.from_input_values(
                author_id=selection["author_id"],
                study_uid=selection["study_uid"],
                name=selection["cohort_name"],
                short_name=selection["cohort_short_name"],
                code=selection["cohort_code"],
                description=selection["cohort_description"],
                study_selection_uid=selection["study_selection_uid"],
                branch_arm_root_uids=selection["branch_arm_root_uids"],
                arm_root_uids=selection["arm_root_uids"],
                number_of_subjects=selection["number_of_subjects"],
                start_date=convert_to_datetime(value=selection["start_date"]),
                accepted_version=selection["accepted_version"],
            )
            all_selections.append(selection_vo)
        return tuple(all_selections)

    def find_by_study(
        self,
        study_uid: str,
        for_update: bool = False,
        arm_uid: str | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        study_value_version: str | None = None,
    ) -> StudySelectionCohortAR:
        """
        Finds all the selected study cohorts for a given study
        :param project_name:
        :param project_number:
        :param arm_uid:
        :param study_uid:
        :param for_update:
        :return:
        """
        if for_update:
            acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(
            study_uid,
            arm_uid=arm_uid,
            project_name=project_name,
            project_number=project_number,
            study_value_version=study_value_version,
        )
        selection_aggregate = StudySelectionCohortAR.from_repository_values(
            study_uid=study_uid, study_cohorts_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def _get_audit_node(
        self, study_selection: StudySelectionCohortAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_cohorts_selection:
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

    @staticmethod
    def cohort_exists_by(
        db_property: str, value: str, cohort_vo: StudySelectionCohortVO
    ) -> StudyArm:
        kwarg_value = getattr(cohort_vo, value)
        cohort_node = (
            StudyCohort.nodes.has(study_value=True)
            .filter(
                uid__ne=cohort_vo.study_selection_uid,
                study_value__latest_value__uid=cohort_vo.study_uid,
            )
            .get_or_none(**{db_property: kwarg_value})
        )
        return cohort_node

    # pylint: disable=unused-argument
    def save(self, study_selection: StudySelectionCohortAR, author_id: str) -> None:
        """
        Persist the set of selected study cohorts from the aggregate to the database
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
        if len(closure_data) > len(study_selection.study_cohorts_selection):
            for idx, closure_study_cohort in enumerate(closure_data, start=1):
                if closure_study_cohort not in study_selection.study_cohorts_selection:
                    selections_to_remove.append((idx, closure_study_cohort))

        # loop through new data - start=1 as order starts at 1 not at 0 and find what needs to be removed and added
        for order, selection in enumerate(
            study_selection.study_cohorts_selection, start=1
        ):
            # check whether something new is added
            if closure_data_length > order - 1:
                # check if anything has changed
                if selection is not closure_data[order - 1]:
                    for closure_item in closure_data:
                        if (
                            selection.study_selection_uid
                            == closure_item.study_selection_uid
                        ):
                            # update the selection by removing the old if the old exists, and adding new selection
                            selections_to_remove.append((order, closure_item))
                            selections_to_add.append((order, selection))
                            break
            else:
                # else something new have been added
                selections_to_add.append((order, selection))

        # audit trail nodes dictionary, holds the new nodes created for the audit trail
        audit_trail_nodes = {}
        # dictionary of last nodes to traverse to their old connections
        last_nodes = {}

        # loop through and remove selections
        for order, selection in selections_to_remove:
            # traverse --> study_value__study_branch__uid
            last_study_selection_node = latest_study_value_node.has_study_cohort.get(
                uid=selection.study_selection_uid
            )
            # detect if the action should be create, delete or edit, then create audit node of the that StudyAction type
            audit_node = self._get_audit_node(
                study_selection, selection.study_selection_uid
            )
            self._remove_old_selection_if_exists(study_selection.study_uid, selection)
            # storage of the removed node audit trail to after put the "after" relationship to the new one
            audit_trail_nodes[selection.study_selection_uid] = audit_node
            # storage of the removed node to after get its connections
            last_nodes[selection.study_selection_uid] = last_study_selection_node
            if isinstance(audit_node, Delete):
                self._add_new_selection(
                    study_root=study_root_node,
                    latest_study_value_node=latest_study_value_node,
                    order=order,
                    selection=selection,
                    audit_node=audit_node,
                    for_deletion=True,
                    before_node=last_study_selection_node,
                )

        # loop through and add selections
        for order, selection in selections_to_add:
            last_study_selection_node = None
            # if the study selection already has an audit trail node
            if selection.study_selection_uid in audit_trail_nodes:
                # extract the audit_trail_node
                audit_node = audit_trail_nodes[selection.study_selection_uid]
                last_study_selection_node = last_nodes[selection.study_selection_uid]
            else:
                audit_node = Create()
            self._add_new_selection(
                study_root=study_root_node,
                latest_study_value_node=latest_study_value_node,
                order=order,
                selection=selection,
                audit_node=audit_node,
                for_deletion=False,
                before_node=last_study_selection_node,
            )

    @staticmethod
    def _remove_old_selection_if_exists(
        study_uid: str, study_selection: StudySelectionCohortVO
    ) -> None:
        """
        Removal is taking both new and old uid. When a study selection is deleted, we do no longer need to use the uid
        on that study selection node anymore, however do to database constraint the node needs to have a uid. So we are
        overwriting a deleted node uid, with a new never used dummy uid.

        We are doing this to be able to maintain the selection instead of removing it, instead a removal will only
        detach the selection from the study value node. So we keep the old selection to have full audit trail available
        in the database.
        :param study_uid:
        :param old_uid:
        :param new_uid:
        :return:
        """
        db.cypher_query(
            """
            MATCH (:StudyRoot { uid: $study_uid})-[:LATEST]->(:StudyValue)-[rel:HAS_STUDY_COHORT]->(se:StudyCohort { uid: $selection_uid})
            DELETE rel
            """,
            {
                "study_uid": study_uid,
                "selection_uid": study_selection.study_selection_uid,
            },
        )

    @staticmethod
    def _add_new_selection(
        study_root: StudyRoot,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionCohortVO,
        audit_node: StudyAction,
        for_deletion: bool = False,
        before_node: StudyCohort | None = None,
    ):
        # Create new cohort selection
        study_cohort_selection_node = StudyCohort(
            order=order,
            uid=selection.study_selection_uid,
            accepted_version=selection.accepted_version,
            name=selection.name,
            short_name=selection.short_name,
            cohort_code=selection.code,
            description=selection.description,
            number_of_subjects=selection.number_of_subjects,
        ).save()

        # Connect new node with study value
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_cohort.connect(
                study_cohort_selection_node
            )

        # check if arm root is set
        if selection.arm_root_uids:
            for arm_root_uid in selection.arm_root_uids:
                # find the objective
                study_arm_root = StudyArm.nodes.filter(
                    study_value__latest_value__uid=selection.study_uid
                ).get_or_none(uid=arm_root_uid)[0]
                # connect to node
                # pylint: disable=no-member
                study_cohort_selection_node.arm_root.connect(study_arm_root)

        # check if branch arm root is set
        if selection.branch_arm_root_uids:
            for branch_arm_root_uid in selection.branch_arm_root_uids:
                # find the objective
                study_branch_arm_root = StudyBranchArm.nodes.filter(
                    study_value__latest_value__uid=selection.study_uid
                ).get_or_none(uid=branch_arm_root_uid)[0]
                # connect to node]
                # pylint: disable=no-member
                study_cohort_selection_node.branch_arm_root.connect(
                    study_branch_arm_root
                )

        _manage_versioning_with_relations(
            study_root=study_root,
            action_type=type(audit_node),
            before=before_node,
            after=study_cohort_selection_node,
            exclude_relationships=[StudyArm, StudyBranchArm],
            author_id=selection.author_id,
        )

    def generate_uid(self) -> str:
        return StudyCohort.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(
        self, study_uid: str, study_selection_uid: str | None = None
    ):
        """
        returns the audit trail for study cohort either for a specific selection or for all study cohort for the study
        """
        if study_selection_uid:
            cypher = """
                    MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudyCohort { uid: $study_selection_uid})
                    WITH sa
                    MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sc:StudyCohort)
                    WITH distinct(all_sc)
                    """
        else:
            cypher = """
                    MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sc:StudyCohort)
                    WITH DISTINCT all_sc
                    """
        specific_cohort_selections_audit_trail = db.cypher_query(
            cypher + """
            WITH DISTINCT all_sc
            OPTIONAL MATCH (ats:StudyArm)-[:STUDY_ARM_HAS_COHORT]->(all_sc)
            WITH all_sc, ats  ORDER BY ats.order
            OPTIONAL MATCH (bats:StudyBranchArm)-[:STUDY_BRANCH_ARM_HAS_COHORT]->(all_sc)
            WITH DISTINCT bats, all_sc, ats
            ORDER BY bats.order
            WITH DISTINCT bats.uid as branch_arm_uid, all_sc, ats
            CALL (branch_arm_uid) {
                MATCH (study_branch_arm:StudyBranchArm {uid:branch_arm_uid})-[:AFTER]-(action:StudyAction)
                WITH study_branch_arm, action
                ORDER BY action.date ASC
                WITH collect(study_branch_arm) as branch_arms
                RETURN last(branch_arms) AS study_branch_arm
            }

            WITH DISTINCT all_sc, ats, sum(study_branch_arm.number_of_subjects) as branch_sum, collect(study_branch_arm.uid) AS branch_arm_root_uids
            ORDER BY all_sc.order ASC
            MATCH (all_sc)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_sc)<-[:BEFORE]-(bsa:StudyAction)
            WITH all_sc, asa, bsa, ats, branch_sum, branch_arm_root_uids
            ORDER BY all_sc.uid, asa.date DESC
            RETURN
                all_sc.uid AS study_selection_uid,
                all_sc.name AS cohort_name,
                all_sc.short_name AS cohort_short_name,
                all_sc.cohort_code AS cohort_code,
                all_sc.description AS cohort_description,
                all_sc.order AS order,
                all_sc.accepted_version AS accepted_version,                
                CASE branch_sum
                    WHEN 0 THEN all_sc.number_of_subjects
                    ELSE branch_sum 
                END AS number_of_subjects,
                branch_arm_root_uids,
                COLLECT (ats.uid) AS arm_root_uids,
                all_sc.text AS text,
                asa.date AS start_date,
                asa.author_id AS author_id,
                labels(asa) AS change_type,
                bsa.date AS end_date
            """,
            {"study_uid": study_uid, "study_selection_uid": study_selection_uid},
        )
        result = []
        for res in utils.db_result_to_list(specific_cohort_selections_audit_trail):
            change_type = ""
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            end_date = (
                convert_to_datetime(value=res["end_date"]) if res["end_date"] else None
            )
            result.append(
                SelectionHistoryCohort(
                    study_selection_uid=res["study_selection_uid"],
                    study_uid=study_uid,
                    cohort_name=res["cohort_name"],
                    cohort_short_name=res["cohort_short_name"],
                    cohort_code=res["cohort_code"],
                    cohort_description=res["cohort_description"],
                    cohort_number_of_subjects=res["number_of_subjects"],
                    branch_arm_roots=res["branch_arm_root_uids"],
                    arm_roots=res["arm_root_uids"],
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
    ) -> list[SelectionHistoryCohort]:
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
