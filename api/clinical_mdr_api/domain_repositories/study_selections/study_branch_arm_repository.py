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
from clinical_mdr_api.domains.study_selections.study_selection_branch_arm import (
    CompactStudyCohortVO,
    StudySelectionBranchArmAR,
    StudySelectionBranchArmVO,
)
from common.exceptions import BusinessLogicException
from common.utils import convert_to_datetime


@dataclass
class SelectionHistoryBranchArm:
    """Class for selection history items"""

    study_selection_uid: str
    study_uid: str | None
    branch_arm_name: str | None
    branch_arm_short_name: str | None
    branch_arm_code: str | None
    branch_arm_description: str | None
    branch_arm_randomization_group: str | None
    branch_arm_number_of_subjects: int | None
    arm_root: str
    # Study selection Versioning
    start_date: datetime.datetime
    author_id: str
    change_type: str
    end_date: datetime.datetime | None
    order: int
    status: str | None
    accepted_version: bool | None


class StudySelectionBranchArmRepository:

    def _retrieves_all_data(
        self,
        study_uid: str | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        study_value_version: str | None = None,
    ) -> tuple[StudySelectionBranchArmVO]:
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

        query += """
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_BRANCH_ARM]->(sba:StudyBranchArm)
            WITH DISTINCT sr, sv, sba
            OPTIONAL MATCH (sba)<-[:STUDY_ARM_HAS_BRANCH_ARM]-(ar:StudyArm)<-[:HAS_STUDY_ARM]-(sv)
            OPTIONAL MATCH (sba)-[:STUDY_BRANCH_ARM_HAS_COHORT]->(sc:StudyCohort)<-[:HAS_STUDY_COHORT]-(sv)
            WITH sr, sba, ar, collect(sc {.uid, .name, .cohort_code}) as study_cohorts
            MATCH (sba)<-[:AFTER]-(sa:StudyAction)

            RETURN DISTINCT 
                sr.uid AS study_uid,
                sba.uid AS study_selection_uid,
                sba.name AS branch_arm_name,
                sba.short_name AS branch_arm_short_name,
                sba.branch_arm_code AS branch_arm_code,
                sba.description AS branch_arm_description,
                sba.order AS order,
                sba.accepted_version AS accepted_version,
                sba.number_of_subjects AS number_of_subjects,
                sba.randomization_group AS randomization_group,
                sba.text AS text,
                ar.uid AS arm_root_uid,
                ar.order AS arm_order,
                study_cohorts,
                sa.date AS start_date,
                sa.author_id AS author_id
            ORDER BY arm_order, order
            """

        all_branch_arm_selections = db.cypher_query(query, query_parameters)
        all_selections = []

        for selection in utils.db_result_to_list(all_branch_arm_selections):
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionBranchArmVO.from_input_values(
                author_id=selection["author_id"],
                study_uid=selection["study_uid"],
                name=selection["branch_arm_name"],
                short_name=selection["branch_arm_short_name"],
                code=selection["branch_arm_code"],
                description=selection["branch_arm_description"],
                study_selection_uid=selection["study_selection_uid"],
                arm_root_uid=selection["arm_root_uid"],
                study_cohorts=[
                    CompactStudyCohortVO(
                        study_cohort_uid=study_cohort.get("uid"),
                        study_cohort_name=study_cohort.get("name"),
                        study_cohort_code=study_cohort.get("cohort_code"),
                    )
                    for study_cohort in selection.get("study_cohorts", [])
                ],
                number_of_subjects=selection["number_of_subjects"],
                randomization_group=selection["randomization_group"],
                start_date=convert_to_datetime(value=selection["start_date"]),
                accepted_version=selection["accepted_version"],
            )
            all_selections.append(selection_vo)
        return tuple(all_selections)

    def _retrieves_all_data_within_arm(
        self,
        study_arm_uid: str | None = None,
        study_uid: str | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        study_value_version: str | None = None,
    ) -> tuple[StudySelectionBranchArmVO]:
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

        query += """
            WITH sr, sv   
            MATCH (sv)-[:HAS_STUDY_ARM]->(ar:StudyArm{ uid: $uid})
            WITH DISTINCT sr, sv, ar 
            MATCH (ar)<-[:AFTER]-(:StudyAction)"""
        query_parameters["uid"] = study_arm_uid

        query += """
            WITH sr, sv, ar
            MATCH (sv)-[:HAS_STUDY_BRANCH_ARM]->(sba:StudyBranchArm)<-[:STUDY_ARM_HAS_BRANCH_ARM]-(ar)
            WITH DISTINCT sr, sba, ar
            
            MATCH (sba)<-[:AFTER]-(sa:StudyAction)

            RETURN DISTINCT 
                sr.uid AS study_uid,
                sba.uid AS study_selection_uid,
                sba.name AS branch_arm_name,
                sba.short_name AS branch_arm_short_name,
                sba.branch_arm_code AS branch_arm_code,
                sba.description AS branch_arm_description,
                sba.order AS order,
                sba.accepted_version AS accepted_version,
                sba.number_of_subjects AS number_of_subjects,
                sba.randomization_group AS randomization_group,
                ar.uid AS arm_root_uid,
                sba.text AS text,
                sa.date AS start_date,
                sa.author_id AS author_id
                ORDER BY order
            """

        all_branch_arm_selections = db.cypher_query(query, query_parameters)
        all_selections = []

        for selection in utils.db_result_to_list(all_branch_arm_selections):
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionBranchArmVO.from_input_values(
                author_id=selection["author_id"],
                study_uid=selection["study_uid"],
                name=selection["branch_arm_name"],
                short_name=selection["branch_arm_short_name"],
                code=selection["branch_arm_code"],
                description=selection["branch_arm_description"],
                study_selection_uid=selection["study_selection_uid"],
                arm_root_uid=selection["arm_root_uid"],
                number_of_subjects=selection["number_of_subjects"],
                randomization_group=selection["randomization_group"],
                start_date=convert_to_datetime(value=selection["start_date"]),
                accepted_version=selection["accepted_version"],
            )
            all_selections.append(selection_vo)
        return tuple(all_selections)

    def find_by_study(
        self,
        study_uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
    ) -> StudySelectionBranchArmAR:
        """
        Finds all the selected study branch arms for a given study
        :param study_uid:
        :param for_update:
        :return:
        """
        if for_update:
            acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(
            study_uid, study_value_version=study_value_version
        )
        selection_aggregate = StudySelectionBranchArmAR.from_repository_values(
            study_uid=study_uid,
            study_branch_arms_selection=all_selections,
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def find_by_arm(
        self,
        study_uid: str,
        study_arm_uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
    ) -> StudySelectionBranchArmAR | None:
        """
        Finds all the selected study branch arms for a given study_arm
        :param study_uid:
        :param study_arm_uid:
        :param for_update:
        :return:
        """
        if for_update:
            acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data_within_arm(
            study_arm_uid, study_value_version=study_value_version
        )
        selection_aggregate = StudySelectionBranchArmAR.from_repository_values(
            study_uid=study_uid, study_branch_arms_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def find_by_arm_nested_info(
        self,
        study_uid: str,
        study_arm_uid: str,
        author_id: str,
        study_value_version: str | None = None,
    ) -> list[tuple[StudySelectionBranchArmVO, int]] | None:
        """
        Return StudySelectionBranchArmVO's connected to the specified StudyArmUid
        :param study_uid: str
        :param study_arm_uid: str
        :param author_id: str
        :return: Return a list of tuples of StudySelectionBranchArmVO and ordering
        """
        if study_value_version:
            study_value_match = "MATCH (sr:StudyRoot {uid: $study_uid})-[:HAS_VERSION {version: $study_value_version}]->(sv:StudyValue)"
            query_parameters = {
                "study_uid": study_uid,
                "study_arm_uid": study_arm_uid,
                "study_value_version": study_value_version,
            }
        else:
            study_value_match = (
                "MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)"
            )
            query_parameters = {"study_uid": study_uid, "study_arm_uid": study_arm_uid}

        query = study_value_match + """
            MATCH (sv)-[:HAS_STUDY_ARM]->(sa:StudyArm {uid: $study_arm_uid})
            MATCH (sa)-[:STUDY_ARM_HAS_BRANCH_ARM]->(sba:StudyBranchArm)<-[:HAS_STUDY_BRANCH_ARM]-(sv)
            WHERE NOT (sba)--(:Delete)
            MATCH (sba)<-[:AFTER]-(action:StudyAction)
            RETURN DISTINCT sba, action.date AS start_date
            ORDER BY sba.order
            """

        results, _ = db.cypher_query(query, query_parameters, resolve_objects=True)

        study_branch_arms: list[tuple[StudySelectionBranchArmVO, int]] = []
        for sba_node, start_date in results:
            study_branch_arms.append(
                (
                    StudySelectionBranchArmVO.from_input_values(
                        author_id=author_id,
                        study_uid=study_uid,
                        study_selection_uid=sba_node.uid,
                        name=sba_node.name,
                        short_name=sba_node.short_name,
                        code=sba_node.branch_arm_code,
                        description=sba_node.description,
                        randomization_group=sba_node.randomization_group,
                        number_of_subjects=sba_node.number_of_subjects,
                        arm_root_uid="",
                        start_date=convert_to_datetime(value=start_date),
                        end_date=None,
                        status=None,
                        change_type=None,
                        accepted_version=False,
                    ),
                    sba_node.order,
                )
            )
        return study_branch_arms if study_branch_arms else None

    def _get_audit_node(
        self, study_selection: StudySelectionBranchArmAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_branch_arms_selection:
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

    def branch_arm_specific_exists_by_uid(
        self, study_uid: str, branch_arm_uid: str
    ) -> bool:
        """
        Returns True if StudyBranchArm with specified uid exists.
        :return:
        """
        sdc_node = (
            StudyBranchArm.nodes.traverse("has_after")
            .filter(study_value__latest_value__uid=study_uid, uid=branch_arm_uid)
            .resolve_subgraph()
        )
        return len(sdc_node) > 0

    def get_branch_arms_connected_to_arm(self, study_uid: str, study_arm_uid: str):
        sdc_nodes = (
            StudyArm.nodes.traverse("has_branch_arm__study_value__latest_value")
            .filter(uid=study_arm_uid, study_value__latest_value__uid=study_uid)
            .order_by("order")
            .all()
        )
        return sorted(
            [i_th[1] for i_th in sdc_nodes],
            key=lambda branch_arm: branch_arm.order,
            reverse=False,
        )

    def get_branch_arms_connected_to_cohort(
        self, study_uid: str, study_cohort_uid: str
    ):
        sdc_nodes = (
            StudyCohort.nodes.traverse("branch_arm_root__study_value__latest_value")
            .filter(uid=study_cohort_uid, study_value__latest_value__uid=study_uid)
            .order_by("order")
            .all()
        )
        return sorted(
            [i_th[1] for i_th in sdc_nodes],
            key=lambda branch_arm: branch_arm.order,
            reverse=False,
        )

    def branch_arm_specific_has_connected_cell(
        self, study_uid: str, branch_arm_uid: str
    ) -> bool:
        """
        Returns True if StudyBranchArm with specified uid has connected at least one StudyDesignCell.
        :return:
        """
        sdc_node = (
            StudyBranchArm.nodes.traverse("has_design_cell__study_value", "has_after")
            .filter(study_value__latest_value__uid=study_uid, uid=branch_arm_uid)
            .resolve_subgraph()
        )
        return len(sdc_node) > 0

    def branch_arm_specific_is_last_on_arm_root(
        self, study_uid: str, arm_root_uid: str, branch_arm_uid: str
    ) -> bool:
        """
        Returns True if Study Branch Arm with specified uid has connected is the last Study Branch Arm on its Study Arm root
        :return:
        """
        sdc_node = (
            StudyBranchArm.nodes.traverse("arm_root", "has_after")
            .filter(
                study_value__latest_value__uid=study_uid, arm_root__uid=arm_root_uid
            )
            .exclude(uid=branch_arm_uid)
            .resolve_subgraph()
        )
        return len(sdc_node) == 0

    # pylint: disable=unused-argument
    def save(self, study_selection: StudySelectionBranchArmAR, author_id: str) -> None:
        """
        Persist the set of selected study branch arms from the aggregate to the database
        :param study_selection:
        :param author_id:
        """
        assert study_selection.repository_closure_data is not None

        # getting the latest study value node
        study_root_node = StudyRoot.nodes.get(uid=study_selection.study_uid)
        latest_study_value_node = study_root_node.latest_value.single()

        BusinessLogicException.raise_if(
            study_root_node.latest_locked.get_or_none() == latest_study_value_node,
            msg="You cannot add or reorder a study selection when the study is in a locked state.",
        )

        # group closure by parent arm
        closure_group_by_root: dict[str, list[Any]] = {}
        for selected_object in study_selection.repository_closure_data:
            closure_group_by_root.setdefault(selected_object.arm_root_uid, []).append(
                selected_object
            )

        # group branch arm by root
        branch_arm_group_by_root: dict[str, list[Any]] = {}
        for selected_object in study_selection.study_branch_arms_selection:
            branch_arm_group_by_root.setdefault(
                selected_object.arm_root_uid, []
            ).append(selected_object)

        # process new/changed/deleted elements for each parent arm
        selections_to_remove: dict[Any, list[Any]] = {}
        selections_to_add: dict[Any, list[Any]] = {}

        # first, check for deleted elements
        for arm_root, closure_branch_arm_list in closure_group_by_root.items():

            # two options to detect object is removed: list for parent StudyArm is empty or smaller than the list in the closure
            current_branch_arm_list: list[Any] = branch_arm_group_by_root.get(
                arm_root, []
            )
            if (arm_root not in branch_arm_group_by_root) or len(
                closure_branch_arm_list
            ) > len(current_branch_arm_list):
                # remove StudyBranchArms that were avaiable in the closure but are not present in the current object
                branch_arms_to_remove = []
                for idx, branch_arm in enumerate(closure_branch_arm_list, start=1):
                    if branch_arm not in current_branch_arm_list:
                        branch_arms_to_remove.append((idx, branch_arm))
                selections_to_remove[arm_root] = branch_arms_to_remove

        # then, check for new/changed elements
        for arm_root, branch_arm_list in branch_arm_group_by_root.items():
            for order, selected_object in enumerate(branch_arm_list, start=1):
                if arm_root in closure_group_by_root:
                    _closure_data = closure_group_by_root[arm_root]
                    # check whether something new is added
                    if len(_closure_data) > order - 1:
                        # check if anything has changed
                        if selected_object is not _closure_data[order - 1]:
                            for closure_item in _closure_data:
                                if (
                                    selected_object.study_selection_uid
                                    == closure_item.study_selection_uid
                                ):
                                    # update the selection by removing the old if the old exists, and adding new selection
                                    selections_to_remove.setdefault(
                                        arm_root, []
                                    ).append((order, closure_item))
                                    selections_to_add.setdefault(arm_root, []).append(
                                        (order, selected_object)
                                    )
                                    break
                    else:
                        # else something new has been added
                        selections_to_add.setdefault(arm_root, []).append(
                            (order, selected_object)
                        )
                else:
                    selections_to_add.setdefault(arm_root, []).append(
                        (order, selected_object)
                    )

        # audit trail nodes dictionary, holds the new nodes created for the audit trail
        audit_trail_nodes = {}
        last_nodes = {}

        # loop through and remove selections
        for arm_root, branch_arm_list in selections_to_remove.items():
            for selection in branch_arm_list:
                order = selection[0]
                selected_object = selection[1]
                # traverse --> study_value__study_branch__uid
                last_study_selection_node = (
                    latest_study_value_node.has_study_branch_arm.get(
                        uid=selected_object.study_selection_uid
                    )
                )
                # detect if the action should be create, delete or edit, then create audit node of the that StudyAction type
                audit_node = self._get_audit_node(
                    study_selection, selected_object.study_selection_uid
                )

                audit_trail_nodes[selected_object.study_selection_uid] = audit_node
                last_nodes[selected_object.study_selection_uid] = (
                    last_study_selection_node
                )
                if isinstance(audit_node, Delete):
                    self._add_new_selection(
                        study_root_node,
                        latest_study_value_node,
                        order,
                        selected_object,
                        audit_node,
                        True,
                        before_node=last_study_selection_node,
                    )

        # loop through and add selections
        for arm_root, branch_arm_list in selections_to_add.items():
            for selection in branch_arm_list:
                order = selection[0]
                selected_object = selection[1]
                last_study_selection_node = None
                if selected_object.study_selection_uid in audit_trail_nodes:
                    audit_node = audit_trail_nodes[selected_object.study_selection_uid]
                    last_study_selection_node = last_nodes[
                        selected_object.study_selection_uid
                    ]
                else:
                    audit_node = Create()
                self._add_new_selection(
                    study_root_node,
                    latest_study_value_node,
                    order,
                    selected_object,
                    audit_node,
                    False,
                    before_node=last_study_selection_node,
                )

    @staticmethod
    def branch_arm_arm_update_conflict(
        branch_arm_vo: StudySelectionBranchArmVO,
    ) -> bool:
        """
        Return True if a BranchArm with a specific StudyArm root has connected StudyDesignCells
        To consider:
            - select StudyDesignCell that is connected to a StudyValue
        """
        branch_arm_with_connected_design_cell_with_diff_arm_root = (
            StudyBranchArm.nodes.has(has_design_cell=True)
            .filter(
                # If it matches a branch_arm with a different arm_root, then it would
                # mean that it is trying to change its arm_root, even though it's having design_cells connected to the BranchArm.
                arm_root__uid__ne=branch_arm_vo.arm_root_uid,
                study_value__latest_value__uid=branch_arm_vo.study_uid,
                has_design_cell__study_value__latest_value__uid=branch_arm_vo.study_uid,
            )
            .get_or_none(uid=branch_arm_vo.study_selection_uid)
        )
        return branch_arm_with_connected_design_cell_with_diff_arm_root is not None

    @staticmethod
    def branch_arm_exists_by(
        db_property: str, value: str, branch_arm_vo: StudySelectionBranchArmVO
    ) -> StudyBranchArm:
        kwarg_value = getattr(branch_arm_vo, value)
        branch_arm_node = (
            StudyBranchArm.nodes.has(study_value=True)
            .filter(
                uid__ne=branch_arm_vo.study_selection_uid,
                study_value__latest_value__uid=branch_arm_vo.study_uid,
            )
            .get_or_none(**{db_property: kwarg_value})
        )
        return branch_arm_node

    @staticmethod
    def _add_new_selection(
        study_root: StudyRoot,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionBranchArmVO,
        audit_node: StudyAction,
        for_deletion: bool = False,
        before_node: StudyBranchArm | None = None,
    ):
        """
        Add new BranchArm Selection
        StudyBranchArm Possible Outbound Relationships:
            - StudyDesignCell - optional
            - StudyArm - mandatory
            - StudyCohort - optional
        """
        # Create new arm selection
        study_branch_arm_selection_node = StudyBranchArm(
            uid=selection.study_selection_uid,
            order=order,
            accepted_version=selection.accepted_version,
            name=selection.name,
            short_name=selection.short_name,
            branch_arm_code=selection.code,
            description=selection.description,
            randomization_group=selection.randomization_group,
            number_of_subjects=selection.number_of_subjects,
        ).save()

        # Connect new node with study value
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_branch_arm.connect(
                study_branch_arm_selection_node
            )

        # check if arm root is set
        if selection.arm_root_uid:
            # find the study arm
            study_arm_root = latest_study_value_node.has_study_arm.get(
                uid=selection.arm_root_uid
            )
            # connect to node
            study_branch_arm_selection_node.arm_root.connect(study_arm_root)

        # check if study cohort is set
        for study_cohort in selection.study_cohorts:
            # find the study cohort
            study_cohort = latest_study_value_node.has_study_cohort.get(
                uid=study_cohort.study_cohort_uid
            )
            # connect to node
            study_branch_arm_selection_node.has_cohort.connect(study_cohort)

        _manage_versioning_with_relations(
            study_root=study_root,
            action_type=type(audit_node),
            before=before_node,
            after=study_branch_arm_selection_node,
            exclude_relationships=[StudyArm, StudyCohort],
            author_id=selection.author_id,
        )

    def generate_uid(self) -> str:
        return StudyBranchArm.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(
        self, study_uid: str, study_selection_uid: str | None = None
    ):
        """
        returns the audit trail for study branch arm either for a specific selection or for all study branch arm for the study
        """
        if study_selection_uid:
            cypher = """
                    MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudyBranchArm { uid: $study_selection_uid})
                    WITH sa
                    MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sba:StudyBranchArm)
                    WITH distinct(all_sba)
                    """
        else:
            cypher = """
                    MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sba:StudyBranchArm)
                    WITH DISTINCT all_sba
                    """
        specific_branch_arm_selections_audit_trail = db.cypher_query(
            cypher + """
            WITH DISTINCT all_sba
            OPTIONAL MATCH (at:StudyArm)-[:STUDY_ARM_HAS_BRANCH_ARM]->(all_sba)
            WITH DISTINCT all_sba, at
            ORDER BY all_sba.order ASC
            MATCH (all_sba)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_sba)<-[:BEFORE]-(bsa:StudyAction)
            WITH all_sba, asa, bsa, at
            ORDER BY all_sba.uid, asa.date DESC
            RETURN
                all_sba.uid AS study_selection_uid,
                all_sba.name AS branch_arm_name,
                all_sba.short_name AS branch_arm_short_name,
                all_sba.branch_arm_code AS branch_arm_code,
                all_sba.description AS branch_arm_description,
                all_sba.order AS order,
                all_sba.accepted_version AS accepted_version,
                all_sba.number_of_subjects AS number_of_subjects,
                all_sba.randomization_group AS randomization_group,
                at.uid AS arm_root_uid,
                all_sba.text AS text,
                asa.date AS start_date,
                asa.author_id AS author_id,
                labels(asa) AS change_type,
                bsa.date AS end_date
            """,
            {"study_uid": study_uid, "study_selection_uid": study_selection_uid},
        )
        result = []
        for res in utils.db_result_to_list(specific_branch_arm_selections_audit_trail):
            change_type = ""
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            end_date = (
                convert_to_datetime(value=res["end_date"]) if res["end_date"] else None
            )
            result.append(
                SelectionHistoryBranchArm(
                    study_selection_uid=res["study_selection_uid"],
                    study_uid=study_uid,
                    branch_arm_name=res["branch_arm_name"],
                    branch_arm_short_name=res["branch_arm_short_name"],
                    branch_arm_code=res["branch_arm_code"],
                    branch_arm_description=res["branch_arm_description"],
                    branch_arm_randomization_group=res["randomization_group"],
                    branch_arm_number_of_subjects=res["number_of_subjects"],
                    arm_root=res["arm_root_uid"],
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
    ) -> list[SelectionHistoryBranchArm]:
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
