import datetime
from dataclasses import dataclass

from neomodel import db
from neomodel.sync_.match import Collect, Last, Optional

from clinical_mdr_api import utils
from clinical_mdr_api.domain_repositories.generic_repository import (
    manage_previous_connected_study_selection_relationships,
)
from clinical_mdr_api.domain_repositories.models._utils import ListDistinct
from clinical_mdr_api.domain_repositories.models.generic import ClinicalMdrNodeWithUID
from clinical_mdr_api.domain_repositories.models.study import (
    StudyArm,
    StudyBranchArm,
    StudyElement,
    StudyRoot,
    StudyValue,
)
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
)
from clinical_mdr_api.domain_repositories.models.study_epoch import StudyEpoch
from clinical_mdr_api.domain_repositories.models.study_selections import StudyDesignCell
from clinical_mdr_api.domains.study_selections.study_design_cell import (
    StudyDesignCellVO,
)
from common import exceptions
from common.utils import convert_to_datetime

STUDY_VALUE_VERSION_QUALIFIER = "study_value__has_version|version"
STUDY_VALUE_UID_QUALIFIER = "study_value__has_version__uid"
STUDY_VALUE_LATEST_UID_QUALIFIER = "study_value__latest_value__uid"


@dataclass
class StudyDesignCellHistory:
    """Class for selection history items"""

    study_selection_uid: str
    study_uid: str
    study_arm_uid: str
    study_branch_arm_uid: str
    study_epoch_uid: str
    study_element_uid: str
    author_id: str
    change_type: str
    start_date: datetime.datetime
    end_date: datetime.datetime | None
    transition_rule: str
    order: int


class StudyDesignCellRepository:
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

    def find_by_uid(self, study_uid: str, uid: str) -> StudyDesignCellVO:
        unique_design_cells = ListDistinct(
            StudyDesignCell.nodes.fetch_relations(
                "study_epoch__has_epoch__has_name_root__has_latest_value",
                "has_after__audit_trail",
                "study_epoch",
                Optional("study_arm__study_value"),
                Optional("study_branch_arm__study_value"),
                Optional("study_element__study_value"),
            )
            .filter(
                study_value__latest_value__uid=study_uid,
                study_epoch__study_value__latest_value__uid=study_uid,
                uid=uid,
            )
            .order_by("order")
            .resolve_subgraph()
        ).distinct()

        exceptions.ValidationException.raise_if(
            len(unique_design_cells) > 1,
            msg=f"Found more than one StudyDesignCell node with UID '{uid}' in the Study with UID '{study_uid}'.",
        )
        exceptions.ValidationException.raise_if(
            len(unique_design_cells) == 0,
            msg=f"The StudyDesignCell with UID '{uid}' could not be found in the Study with UID '{study_uid}'.",
        )

        return self._from_repository_values(
            study_uid=study_uid, design_cell=unique_design_cells[0]
        )

    def find_all_design_cells_by_study(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> list[StudyDesignCellVO]:
        if study_value_version:
            filters = {
                STUDY_VALUE_VERSION_QUALIFIER: study_value_version,
                STUDY_VALUE_UID_QUALIFIER: study_uid,
            }
        else:
            filters = {STUDY_VALUE_LATEST_UID_QUALIFIER: study_uid}
        all_design_cells = [
            self._from_repository_values(
                study_uid=study_uid,
                design_cell=sas_node,
                study_value_version=study_value_version,
            )
            for sas_node in ListDistinct(
                StudyDesignCell.nodes.fetch_relations(
                    "study_epoch__has_epoch__has_name_root__has_latest_value",
                    "has_after__audit_trail",
                    "study_epoch__study_value",
                    "study_element__study_value",
                    Optional("study_arm__study_value"),
                    Optional("study_branch_arm__study_value"),
                )
                .filter(**filters)
                .order_by("order")
                .resolve_subgraph()
            ).distinct()
        ]
        return all_design_cells

    def _from_repository_values(
        self,
        study_uid: str,
        design_cell: StudyDesignCell,
        study_value_version: str | None = None,
    ) -> StudyDesignCellVO:
        study_action = design_cell.has_after.all()[0]
        if study_value_version:
            filters = {
                "has_version|version": study_value_version,
                "has_version__uid": study_uid,
            }
        else:
            filters = {
                "latest_value__uid": study_uid,
            }
        study_value: StudyValue = (
            StudyValue.nodes.filter(**filters)
            .intermediate_transform({"studyvalue": {"source": "studyvalue"}})
            .annotate(study_value=Last(Collect("studyvalue", distinct=True)))
            .get_or_none()
        )
        assert isinstance(study_value, StudyValue)

        assert len(set(ith.uid for ith in design_cell.study_arm.all())) <= 1
        assert len(set(ith.uid for ith in design_cell.study_branch_arm.all())) <= 1
        assert len(set(ith.uid for ith in design_cell.study_element.all())) <= 1
        assert len(set(ith.uid for ith in design_cell.study_epoch.all())) <= 1

        study_epoch: StudyEpoch = self.get_current_outbound_node(
            node=design_cell, outbound_rel_name="study_epoch", study_value=study_value
        )
        study_arm: StudyArm = self.get_current_outbound_node(
            node=design_cell, outbound_rel_name="study_arm", study_value=study_value
        )
        study_branch_arm: StudyBranchArm = self.get_current_outbound_node(
            node=design_cell,
            outbound_rel_name="study_branch_arm",
            study_value=study_value,
        )
        study_element: StudyElement = self.get_current_outbound_node(
            node=design_cell, outbound_rel_name="study_element", study_value=study_value
        )

        study_epoch_name = (
            study_epoch.has_epoch.single()
            .has_name_root.single()
            .has_latest_value.single()
            .name
        )
        return StudyDesignCellVO(
            uid=design_cell.uid,
            study_uid=study_uid,
            order=design_cell.order,
            study_arm_uid=study_arm.uid if study_arm is not None else None,
            study_arm_name=study_arm.name if study_arm is not None else None,
            study_branch_arm_uid=(
                study_branch_arm.uid if study_branch_arm is not None else None
            ),
            study_branch_arm_name=(
                study_branch_arm.name if study_branch_arm is not None else None
            ),
            study_epoch_uid=study_epoch.uid,
            study_epoch_name=study_epoch_name,
            study_element_uid=study_element.uid,
            study_element_name=study_element.name,
            transition_rule=design_cell.transition_rule,
            start_date=study_action.date,
            author_id=study_action.author_id,
        )

    def get_current_outbound_node(
        self,
        node: ClinicalMdrNodeWithUID,
        outbound_rel_name: str,
        study_value: StudyValue,
    ):
        outbound_node = None
        outbound_nodes = getattr(node, outbound_rel_name).all()
        for i_outbound_node in outbound_nodes:
            if i_outbound_node.study_value.is_connected(study_value):
                outbound_node = i_outbound_node
        return outbound_node

    # pylint: disable=unused-argument
    def save(
        self,
        design_cell_vo: StudyDesignCellVO,
        author_id: str,
        create: bool = False,
        allow_none_arm_branch_arm=False,
    ) -> StudyDesignCellVO:
        # Get nodes and check if they can play together
        study_root_node: StudyRoot = StudyRoot.nodes.get_or_none(
            uid=design_cell_vo.study_uid
        )

        exceptions.NotFoundException.raise_if(
            study_root_node is None, "Study", design_cell_vo.study_uid
        )

        latest_study_value_node: StudyValue = study_root_node.latest_value.single()

        # check if something has changed
        if not create:
            # get the previous item
            previous_item: StudyDesignCell = (
                latest_study_value_node.has_study_design_cell.get_or_none(
                    uid=design_cell_vo.uid
                )
            )
            previous_study_epoch: StudyEpoch = self.get_current_outbound_node(
                node=previous_item,
                outbound_rel_name="study_epoch",
                study_value=latest_study_value_node,
            )
            previous_study_arm: StudyArm = self.get_current_outbound_node(
                node=previous_item,
                outbound_rel_name="study_arm",
                study_value=latest_study_value_node,
            )
            previous_study_branch_arm: StudyBranchArm = self.get_current_outbound_node(
                node=previous_item,
                outbound_rel_name="study_branch_arm",
                study_value=latest_study_value_node,
            )
            previous_study_element: StudyElement = self.get_current_outbound_node(
                node=previous_item,
                outbound_rel_name="study_element",
                study_value=latest_study_value_node,
            )
            to_compare_previous = [
                (
                    previous_study_arm.uid
                    if not previous_study_branch_arm and previous_study_arm
                    else None
                ),
                previous_study_branch_arm.uid if previous_study_branch_arm else None,
                previous_study_epoch.uid if previous_study_epoch else None,
                previous_study_element.uid if previous_study_element else None,
                previous_item.transition_rule,
                previous_item.order,
            ]
            to_compare_post = list(
                map(
                    design_cell_vo.__dict__.get,
                    [
                        "study_arm_uid",
                        "study_branch_arm_uid",
                        "study_epoch_uid",
                        "study_element_uid",
                        "transition_rule",
                        "order",
                    ],
                )
            )

            exceptions.BusinessLogicException.raise_if(
                not previous_study_arm
                and not previous_study_branch_arm
                and not allow_none_arm_branch_arm,
                msg="Broken Existing Design Cell without Arm and BranchArm",
            )
            # check if there's something to change
            if to_compare_previous == to_compare_post:
                return self._from_repository_values(
                    design_cell_vo.study_uid, previous_item
                )

        # check if the study_arm has StudyBranchArms assigned to it
        # get StudyArm only if it's necessary
        if design_cell_vo.study_arm_uid:
            study_arm_node: StudyArm = (
                latest_study_value_node.has_study_arm.get_or_none(
                    uid=design_cell_vo.study_arm_uid
                )
            )
            # if any StudyBranchArms connectect to StudyArm has a study_value
            exceptions.BusinessLogicException.raise_if(
                study_arm_node
                and self.get_current_outbound_node(
                    node=study_arm_node,
                    outbound_rel_name="has_branch_arm",
                    study_value=latest_study_value_node,
                ),
                msg=f"The Study Arm with UID '{design_cell_vo.study_arm_uid}' cannot be "
                "assigned to a Study Design Cell because it has Study Branch Arms assigned to it",
            )
        else:
            study_arm_node = None

        # get StudyBranchArm only if it's necessary
        if design_cell_vo.study_branch_arm_uid:
            study_branch_arm_node = (
                latest_study_value_node.has_study_branch_arm.get_or_none(
                    uid=design_cell_vo.study_branch_arm_uid
                )
            )
        else:
            study_branch_arm_node = None

        # at least one of the two has to be defined
        exceptions.NotFoundException.raise_if(
            study_arm_node is None and study_branch_arm_node is None,
            msg=f"Study Arm with UID '{design_cell_vo.study_arm_uid}' or Study Branch Arm with UID '{design_cell_vo.study_branch_arm_uid}' must exist.",
        )

        # get StudyEpoch
        study_epoch_node = latest_study_value_node.has_study_epoch.get_or_none(
            uid=design_cell_vo.study_epoch_uid
        )
        exceptions.NotFoundException.raise_if(
            study_epoch_node is None, "Study Epoch", design_cell_vo.study_epoch_uid
        )

        # get StudyElement
        if design_cell_vo.study_element_uid is not None:
            study_element_node = latest_study_value_node.has_study_element.get_or_none(
                uid=design_cell_vo.study_element_uid
            )
            exceptions.NotFoundException.raise_if(
                study_element_node is None,
                "Study Element",
                design_cell_vo.study_element_uid,
            )
        # Create new node
        design_cell = StudyDesignCell(
            uid=design_cell_vo.uid,
            transition_rule=design_cell_vo.transition_rule,
            order=design_cell_vo.order,
        )
        design_cell.save()

        # Create relations
        # ensure switching
        #       study_branch_arm was defined even if the arm was specified will be connected to study branch arm
        if study_branch_arm_node is not None:
            design_cell.study_branch_arm.connect(study_branch_arm_node)
        #       just arm was defined
        else:
            design_cell.study_arm.connect(study_arm_node)
        design_cell.study_epoch.connect(study_epoch_node)
        design_cell.study_element.connect(study_element_node)

        if create:
            self.manage_versioning_create(
                study_root=study_root_node,
                study_design_cell=design_cell_vo,
                new_item=design_cell,
            )
        else:
            self.manage_versioning_update(
                study_root=study_root_node,
                study_design_cell=design_cell_vo,
                previous_item=previous_item,
                new_item=design_cell,
            )
            exclude_study_selection_relationships = [
                StudyArm,
                StudyBranchArm,
                StudyEpoch,
                StudyElement,
            ]
            manage_previous_connected_study_selection_relationships(
                previous_item=previous_item,
                study_value_node=latest_study_value_node,
                new_item=design_cell,
                exclude_study_selection_relationships=exclude_study_selection_relationships,
            )

        # check if the new cell already exists
        all_existing = self.get_design_cells_connected_to_epoch(
            design_cell_vo.study_uid, design_cell_vo.study_epoch_uid
        )
        for existing in all_existing:
            arm = existing.study_arm.single()
            branch = existing.study_branch_arm.single()
            arm_uid = arm.uid if arm else None
            branch_uid = branch.uid if branch else None

            exceptions.AlreadyExistsException.raise_if(
                branch_uid and branch_uid == design_cell_vo.study_branch_arm_uid,
                msg="A study design cell already exists for the given combination study branch arm and study epoch.",
            )
            exceptions.AlreadyExistsException.raise_if(
                not branch_uid and arm_uid == design_cell_vo.study_arm_uid,
                msg="A study design cell already exists for the given combination of study arm and study epoch.",
            )

        design_cell.study_value.connect(latest_study_value_node)
        # return the json response model
        return self._from_repository_values(design_cell_vo.study_uid, design_cell)

    def manage_versioning_update(
        self,
        study_root: StudyRoot,
        study_design_cell: StudyDesignCellVO,
        previous_item: StudyDesignCell,
        new_item: StudyDesignCell,
    ):
        # Record StudyAction
        action = Edit(
            date=datetime.datetime.now(datetime.timezone.utc),
            author_id=study_design_cell.author_id,
        )
        action.save()
        action.has_before.connect(previous_item)
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def manage_versioning_create(
        self,
        study_root: StudyRoot,
        study_design_cell: StudyDesignCellVO,
        new_item: StudyDesignCell,
    ):
        # create StudyAction node
        action = Create(
            date=datetime.datetime.now(datetime.timezone.utc),
            author_id=study_design_cell.author_id,
        )
        action.save()
        # connect the new item to the newly StudyAction
        action.has_after.connect(new_item)
        # connect the audit trail to the study_root node
        study_root.audit_trail.connect(action)

    def patch_study_arm(
        self,
        study_uid: str,
        design_cell_uid: str,
        study_arm_uid: str,
        author_id: str,
        allow_none_arm_branch_arm=False,
    ):
        study_design_cell = self.find_by_uid(study_uid=study_uid, uid=design_cell_uid)
        study_design_cell.study_arm_uid = study_arm_uid
        study_design_cell.study_branch_arm_uid = None

        self.save(
            study_design_cell,
            author_id,
            create=False,
            allow_none_arm_branch_arm=allow_none_arm_branch_arm,
        )

    def get_design_cells_connected_to_branch_arm(
        self,
        study_uid: str,
        study_branch_arm_uid: str,
        study_value_version: str | None = None,
    ):
        if study_value_version:
            filters = {
                STUDY_VALUE_VERSION_QUALIFIER: study_value_version,
                STUDY_VALUE_UID_QUALIFIER: study_uid,
                "study_branch_arm__uid": study_branch_arm_uid,
                "study_branch_arm__study_value__has_version|version": study_value_version,
                "study_branch_arm__study_value__has_version__uid": study_uid,
            }
        else:
            filters = {
                STUDY_VALUE_LATEST_UID_QUALIFIER: study_uid,
                "study_branch_arm__uid": study_branch_arm_uid,
                "study_branch_arm__study_value__latest_value__uid": study_uid,
            }
        sdc_node = ListDistinct(
            StudyDesignCell.nodes.fetch_relations(
                "study_epoch__has_epoch__has_name_root__has_latest_value",
                "has_after__audit_trail",
                "study_epoch__study_value",
                "study_branch_arm",
                Optional("study_branch_arm__study_value"),
                Optional("study_element__study_value"),
            )
            .filter(**filters)
            .order_by("order")
            .resolve_subgraph()
        ).distinct()
        return sdc_node

    def get_design_cells_connected_to_epoch(
        self,
        study_uid: str,
        study_epoch_uid: str,
        study_value_version: str | None = None,
    ):
        if study_value_version:
            filters = {
                STUDY_VALUE_VERSION_QUALIFIER: study_value_version,
                STUDY_VALUE_UID_QUALIFIER: study_uid,
                "study_epoch__uid": study_epoch_uid,
                "study_epoch__study_value__has_version|version": study_value_version,
                "study_epoch__study_value__has_version__uid": study_uid,
            }
        else:
            filters = {
                STUDY_VALUE_LATEST_UID_QUALIFIER: study_uid,
                "study_epoch__uid": study_epoch_uid,
                "study_epoch__study_value__latest_value__uid": study_uid,
            }
        sdc_node = ListDistinct(
            StudyDesignCell.nodes.fetch_relations(
                "study_epoch__has_epoch__has_name_root__has_latest_value",
                "has_after__audit_trail",
                "study_epoch__study_value",
                Optional("study_arm__study_value"),
                Optional("study_branch_arm__study_value"),
                Optional("study_element__study_value"),
            )
            .filter(**filters)
            .order_by("order")
            .resolve_subgraph()
        ).distinct()

        return sdc_node

    def get_design_cells_connected_to_arm(
        self, study_uid: str, study_arm_uid: str, study_value_version: str | None = None
    ):
        if study_value_version:
            filters = {
                STUDY_VALUE_VERSION_QUALIFIER: study_value_version,
                STUDY_VALUE_UID_QUALIFIER: study_uid,
                "study_arm__uid": study_arm_uid,
                "study_arm__study_value__has_version|version": study_value_version,
                "study_arm__study_value__has_version__uid": study_uid,
            }
        else:
            filters = {
                STUDY_VALUE_LATEST_UID_QUALIFIER: study_uid,
                "study_arm__uid": study_arm_uid,
                "study_arm__study_value__latest_value__uid": study_uid,
            }
        sdc_node = ListDistinct(
            StudyDesignCell.nodes.fetch_relations(
                "study_epoch__has_epoch__has_name_root__has_latest_value",
                "study_arm__study_value",
                "has_after__audit_trail",
                "study_epoch__study_value",
                Optional("study_element__study_value"),
            )
            .filter(**filters)
            .order_by("order")
            .resolve_subgraph()
        ).distinct()

        return sdc_node

    def get_design_cells_connected_to_element(
        self,
        study_uid: str,
        study_element_uid: str,
        study_value_version: str | None = None,
    ):
        if study_value_version:
            filters = {
                STUDY_VALUE_VERSION_QUALIFIER: study_value_version,
                STUDY_VALUE_UID_QUALIFIER: study_uid,
                "study_element__uid": study_element_uid,
                "study_element__study_value__has_version|version": study_value_version,
                "study_element__study_value__has_version__uid": study_uid,
            }
        else:
            filters = {
                STUDY_VALUE_LATEST_UID_QUALIFIER: study_uid,
                "study_element__uid": study_element_uid,
                "study_element__study_value__latest_value__uid": study_uid,
            }
        sdc_node = ListDistinct(
            StudyDesignCell.nodes.fetch_relations(
                "study_element",
                "has_after__audit_trail",
            )
            .filter(**filters)
            .order_by("order")
            .resolve_subgraph()
        ).distinct()
        return sdc_node

    def delete(self, study_uid: str, design_cell_uid: str, author_id: str):
        study_root_node = StudyRoot.nodes.get_or_none(uid=study_uid)

        exceptions.NotFoundException.raise_if(
            study_root_node is None, "Study", study_uid
        )

        latest_study_value_node = study_root_node.latest_value.single()
        design_cell = latest_study_value_node.has_study_design_cell.get_or_none(
            uid=design_cell_uid
        )

        exceptions.NotFoundException.raise_if(
            design_cell is None, "Study Design Cell", design_cell_uid
        )

        # create delete version
        new_design_cell = StudyDesignCell(
            uid=design_cell.uid,
            transition_rule=design_cell.transition_rule,
            order=design_cell.order,
        )
        new_design_cell.save()

        study_arm_node = design_cell.study_arm.single()
        study_branch_arm_node = design_cell.study_branch_arm.single()
        # at least one of the two has to be defined
        if study_arm_node:
            new_design_cell.study_arm.connect(study_arm_node)
        elif study_branch_arm_node:
            new_design_cell.study_branch_arm.connect(study_branch_arm_node)
        else:
            raise exceptions.NotFoundException(
                msg="Study arm or Study Branch Arm must exist"
            )

        # get StudyEpoch
        study_epoch_node = design_cell.study_epoch.single()

        exceptions.NotFoundException.raise_if_not(
            study_epoch_node, msg="Study epoch must exists"
        )

        new_design_cell.study_epoch.connect(study_epoch_node)

        # gest StudyElement
        study_element_node = design_cell.study_element.single()

        exceptions.NotFoundException.raise_if_not(
            study_element_node, msg="Study element must exists"
        )

        new_design_cell.study_element.connect(study_element_node)

        # Audit trail
        audit_node = Delete(
            author_id=author_id, date=datetime.datetime.now(datetime.timezone.utc)
        )
        audit_node.save()
        study_root_node.audit_trail.connect(audit_node)
        audit_node.has_before.connect(design_cell)
        audit_node.has_after.connect(new_design_cell)
        exclude_study_selection_relationships = [
            StudyArm,
            StudyBranchArm,
            StudyEpoch,
            StudyElement,
        ]
        manage_previous_connected_study_selection_relationships(
            previous_item=design_cell,
            study_value_node=latest_study_value_node,
            new_item=new_design_cell,
            exclude_study_selection_relationships=exclude_study_selection_relationships,
        )

    def generate_uid(self) -> str:
        return StudyDesignCell.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(
        self, study_uid: str, design_cell_uid: str | None = None
    ):
        """
        returns the audit trail for study design cell either for a
        specific selection or for all study design cells for the study.
        """
        # if some DesignCell is specified
        if design_cell_uid:
            # then query just that specific design cell
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sdc:StudyDesignCell {uid: $design_cell_uid})
            WITH sdc
            MATCH (sdc)-[:AFTER|BEFORE*0..]-(all_sdc:StudyDesignCell)
            WITH distinct(all_sdc)
            """
        # if get all study design cells history is called
        else:
            # then query all the design cells
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sdc:StudyDesignCell)
            WITH DISTINCT all_sdc
            """
        specific_design_cells_audit_trail = db.cypher_query(
            cypher
            + """
            OPTIONAL MATCH (all_sdc)<-[:STUDY_BRANCH_ARM_HAS_DESIGN_CELL]-(sba:StudyBranchArm)
            OPTIONAL MATCH (all_sdc)<-[:STUDY_ARM_HAS_DESIGN_CELL]-(sa:StudyArm)
            MATCH (all_sdc)<-[:STUDY_EPOCH_HAS_DESIGN_CELL]-(se:StudyEpoch)
            OPTIONAL MATCH (all_sdc)<-[:STUDY_ELEMENT_HAS_DESIGN_CELL]-(sel:StudyElement)
            MATCH (all_sdc)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_sdc)<-[:BEFORE]-(bsa:StudyAction)
            WITH all_sdc, sa, se, sel, asa, bsa, sba
            ORDER BY all_sdc.uid, asa.date DESC
            RETURN DISTINCT
                all_sdc.uid AS uid,
                all_sdc.transition_rule AS transition_rule,
                all_sdc.order AS order,
                sa.uid AS study_arm_uid, 
                sba.uid AS study_branch_arm_uid,
                se.uid AS study_epoch_uid,
                sel.uid AS study_element_uid,
                labels(asa) AS change_type,
                asa.date AS start_date,
                bsa.date AS end_date,
                asa.author_id AS author_id
            """,
            {"study_uid": study_uid, "design_cell_uid": design_cell_uid},
        )
        result = []
        for res in utils.db_result_to_list(specific_design_cells_audit_trail):
            change_type = ""
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            end_date = (
                convert_to_datetime(value=res["end_date"]) if res["end_date"] else None
            )
            result.append(
                StudyDesignCellHistory(
                    study_uid=study_uid,
                    study_selection_uid=res["uid"],
                    study_arm_uid=res["study_arm_uid"],
                    study_branch_arm_uid=res["study_branch_arm_uid"],
                    study_epoch_uid=res["study_epoch_uid"],
                    study_element_uid=res["study_element_uid"],
                    author_id=res["author_id"],
                    change_type=change_type,
                    start_date=convert_to_datetime(value=res["start_date"]),
                    transition_rule=res["transition_rule"],
                    order=res["order"],
                    end_date=end_date,
                )
            )
        return result

    def find_selection_history(
        self, study_uid: str, design_cell_uid: str | None = None
    ) -> list[dict | None]:
        if design_cell_uid:
            return self._get_selection_with_history(
                study_uid=study_uid, design_cell_uid=design_cell_uid
            )
        return self._get_selection_with_history(study_uid=study_uid)

    def close(self) -> None:
        pass
