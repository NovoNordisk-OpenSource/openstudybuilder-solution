from clinical_mdr_api.domains.controlled_terminologies.utils import TermParentType
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionSimpleModel,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    DurationJsonModel,
    StudyDesignCellCreateInput,
    StudyDesignCellEditInput,
    StudySelectionArmCreateInput,
    StudySelectionArmInput,
    StudySelectionBranchArmCreateInput,
    StudySelectionBranchArmEditInput,
    StudySelectionCohortCreateInput,
    StudySelectionElementCreateInput,
    StudySelectionElementInput,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from clinical_mdr_api.services.studies.study_arm_selection import (
    StudyArmSelectionService,
)
from clinical_mdr_api.services.studies.study_branch_arm_selection import (
    StudyBranchArmSelectionService,
)
from clinical_mdr_api.services.studies.study_cohort_selection import (
    StudyCohortSelectionService,
)
from clinical_mdr_api.services.studies.study_design_cell import StudyDesignCellService
from clinical_mdr_api.services.studies.study_element_selection import (
    StudyElementSelectionService,
)


def create_study_element(
    element_subtype_uid: str,
    study_uid: str,
    name: str = "Element_Name_1",
    short_name: str = "Element_Short_Name_1",
    code: str = "Element_code_1",
    description: str = "desc...",
):
    study_selection_element_create_input = StudySelectionElementCreateInput(
        name=name,
        short_name=short_name,
        code=code,
        description=description,
        element_subtype_uid=element_subtype_uid,
    )
    item = StudyElementSelectionService().make_selection(
        study_uid, selection_create_input=study_selection_element_create_input
    )
    return item


def edit_study_element(
    element_uid: str, study_uid: str, new_short_name="new_short_name"
):
    study_selection_element_edit_input = StudySelectionElementInput(
        element_uid=element_uid,
        short_name=new_short_name,
    )
    item = StudyElementSelectionService().patch_selection(
        study_uid,
        study_selection_uid=element_uid,
        selection_update_input=study_selection_element_edit_input,
    )
    return item


def add_parent_ct_term(element_subtype_term_uid1, element_type_term_uid1):
    CTTermService().add_parent(
        term_uid=element_subtype_term_uid1,
        parent_uid=element_type_term_uid1,
        relationship_type=TermParentType.PARENT_TYPE,
    )


def create_study_element_with_planned_duration(
    element_subtype_uid: str, study_uid: str, unit_definition_uid: str
):
    study_selection_element_create_input = StudySelectionElementCreateInput(
        name="Element_Name_1",
        short_name="Element_Short_Name_1",
        code="Element_code_1",
        description="desc...",
        start_rule="start_rule",
        end_rule="stop_rule",
        planned_duration=DurationJsonModel(
            duration_value=70,
            duration_unit_code=UnitDefinitionSimpleModel(uid=unit_definition_uid),
        ),
        element_subtype_uid=element_subtype_uid,
    )
    item = StudyElementSelectionService().make_selection(
        study_uid, selection_create_input=study_selection_element_create_input
    )
    return item


def create_study_arm(
    study_uid: str,
    name,
    short_name,
    code,
    description,
    randomization_group,
    number_of_subjects,
    arm_type_uid,
):
    study_selection_arm_create_input = StudySelectionArmCreateInput(
        name=name,
        short_name=short_name,
        code=code,
        description=description,
        randomization_group=randomization_group,
        number_of_subjects=number_of_subjects,
        arm_type_uid=arm_type_uid,
    )
    item = StudyArmSelectionService().make_selection(
        study_uid, selection_create_input=study_selection_arm_create_input
    )
    return item


def edit_study_arm(
    study_uid: str,
    arm_uid: str,
    name: str,
    short_name: str,
):
    study_selection_arm_edit_input = StudySelectionArmInput(
        arm_uid=arm_uid,
        name=name,
        short_name=short_name,
    )
    item = StudyArmSelectionService().patch_selection(
        study_uid,
        study_selection_uid=arm_uid,
        selection_update_input=study_selection_arm_edit_input,
    )
    return item


def create_study_branch_arm(
    study_uid: str,
    name,
    short_name,
    code,
    description,
    randomization_group,
    number_of_subjects,
    arm_uid,
):
    study_selection_branch_arm_create_input = StudySelectionBranchArmCreateInput(
        name=name,
        short_name=short_name,
        code=code,
        description=description,
        randomization_group=randomization_group,
        number_of_subjects=number_of_subjects,
        arm_uid=arm_uid,
    )
    item = StudyBranchArmSelectionService().make_selection(
        study_uid, selection_create_input=study_selection_branch_arm_create_input
    )
    return item


def patch_study_branch_arm(branch_arm_uid: str, study_uid: str):
    study_selection_branch_arm_edit_input = StudySelectionBranchArmEditInput(
        branch_arm_uid=branch_arm_uid,
        name="Branch_Arm_Name_1_edit",
    )
    item = StudyBranchArmSelectionService().patch_selection(
        study_uid=study_uid,
        study_selection_uid=branch_arm_uid,
        selection_update_input=study_selection_branch_arm_edit_input,
    )
    return item


def create_study_cohort(
    study_uid: str,
    name,
    short_name,
    code,
    description,
    number_of_subjects,
    arm_uids,
):
    study_selection_cohort_create_input = StudySelectionCohortCreateInput(
        name=name,
        short_name=short_name,
        code=code,
        description=description,
        number_of_subjects=number_of_subjects,
        arm_uids=arm_uids,
    )
    item = StudyCohortSelectionService().make_selection(
        study_uid, selection_create_input=study_selection_cohort_create_input
    )
    return item


def create_study_design_cell(
    study_element_uid: str,
    study_arm_uid: str,
    study_epoch_uid: str,
    study_uid: str,
):
    study_design_cell_create_input = StudyDesignCellCreateInput(
        study_arm_uid=study_arm_uid,
        study_epoch_uid=study_epoch_uid,
        study_element_uid=study_element_uid,
        transition_rule="Transition_Rule_1",
    )
    # Create a design cell -- Arm Specified
    item = StudyDesignCellService().create(
        study_uid=study_uid, design_cell_input=study_design_cell_create_input
    )
    return item


def patch_order_study_design_cell(
    study_design_cell_uid: str,
    study_uid: str,
    order=1,
):
    study_design_cell_update_input = StudyDesignCellEditInput(
        study_design_cell_uid=study_design_cell_uid, order=order
    )
    # Create a design cell -- Arm Specified
    item = StudyDesignCellService().patch(
        study_uid=study_uid, design_cell_update_input=study_design_cell_update_input
    )
    return item
