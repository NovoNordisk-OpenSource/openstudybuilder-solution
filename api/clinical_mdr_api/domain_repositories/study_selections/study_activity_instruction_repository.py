from neomodel import RelationshipDefinition, StructuredNode, db

from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivityInstruction,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    ActivityInstructionRoot,
    ActivityInstructionValue,
)
from clinical_mdr_api.domain_repositories.study_selections import base
from clinical_mdr_api.domains.study_selections.study_activity_instruction import (
    StudyActivityInstructionVO,
)
from common.exceptions import NotFoundException


class StudyActivityInstructionRepository(base.StudySelectionRepository):
    def _from_repository_values(
        self, study_uid: str, selection: StudyActivityInstruction, selection_vo=None
    ) -> StudyActivityInstructionVO:
        study_action = selection.has_after.all()[0]
        study_activity = selection.study_activity.single()
        activity_instruction_value = selection.activity_instruction_value.single()
        return StudyActivityInstructionVO(
            uid=selection.uid,
            study_uid=study_uid,
            study_activity_uid=study_activity.uid,
            activity_instruction_uid=activity_instruction_value.get_root_uid_by_latest(),
            activity_instruction_name=activity_instruction_value.name,
            start_date=study_action.date,
            author_id=study_action.author_id,
        )

    def exclude_relationships(
        self,
    ) -> list[type[StructuredNode] | RelationshipDefinition | str]:
        return [ActivityInstructionValue]

    def perform_save(
        self,
        study_value_node: StudyValue,
        selection_vo: StudyActivityInstructionVO,
        author_id: str,
    ):
        study_activity_node = study_value_node.has_study_activity.get_or_none(
            uid=selection_vo.study_activity_uid
        )

        NotFoundException.raise_if(
            study_activity_node is None,
            "Study Activity",
            selection_vo.study_activity_uid,
        )

        activity_instruction_root_node = ActivityInstructionRoot.nodes.get_or_none(
            uid=selection_vo.activity_instruction_uid
        )

        NotFoundException.raise_if(
            activity_instruction_root_node is None,
            "Study Activity Instruction",
            selection_vo.activity_instruction_uid,
        )

        activity_instruction_value_node = (
            activity_instruction_root_node.latest_final.single()
        )

        # Detach previous node from study
        if selection_vo.uid is not None:
            self._remove_old_selection_if_exists(selection_vo.study_uid, selection_vo)

        # Create new node
        node = StudyActivityInstruction(uid=selection_vo.uid).save()

        # Create relations
        node.study_activity.connect(study_activity_node)
        node.activity_instruction_value.connect(activity_instruction_value_node)
        study_value_node.has_study_activity_instruction.connect(node)

        return node

    def _remove_old_selection_if_exists(
        self, study_uid: str, instruction: StudyActivityInstructionVO
    ):
        return db.cypher_query(
            """
            MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(:StudyValue)
            -[rel:HAS_STUDY_ACTIVITY_INSTRUCTION]->(:StudyActivityInstruction {uid: $instruction_uid})
            DELETE rel
            """,
            {
                "study_uid": study_uid,
                "instruction_uid": instruction.uid,
            },
        )

    def get_study_selection(
        self, study_value_node: StudyValue, selection_uid: str
    ) -> StudyActivityInstruction:
        node = study_value_node.has_study_activity_instruction.get_or_none(
            uid=selection_uid
        )

        NotFoundException.raise_if(
            node is None, "Study Activity Instruction", selection_uid
        )

        return node

    def _get_selection_with_history(
        self, study_uid: str, selection_uid: str | None = None
    ):
        raise NotImplementedError
