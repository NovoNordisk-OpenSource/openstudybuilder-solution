import unittest

from neomodel import db

from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyDesignCellBatchInput,
    StudyDesignCellCreateInput,
    StudyDesignCellDeleteInput,
    StudyDesignCellEditInput,
)
from clinical_mdr_api.services.studies.study_design_cell import StudyDesignCellService
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_arm,
    create_study_branch_arm,
    create_study_element,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    get_catalogue_name_library_name,
)
from common import exceptions


class StudyDesignCellTestCase(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("studydesigncelltestt")
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)

        # Generate UIDs
        # Create a study
        StudyRoot.generate_node_uids_if_not_present()
        self.study = StudyRoot.nodes.all()[0]

        # Create an epoch
        _catalogue_name, library_name = get_catalogue_name_library_name()
        catalogue_name = "SDTM CT"
        create_study_epoch_codelists_ret_cat_and_lib()
        self.study_epoch = create_study_epoch("EpochSubType_0001")
        self.study_epoch2 = create_study_epoch("EpochSubType_0001")

        # Create a study arm
        arm_type_codelist = create_codelist(
            "Arm Type",
            "CTCodelist_ArmType",
            catalogue_name,
            library_name,
            submission_value="ARMTTP",
        )
        arm_type_term = create_ct_term(
            "Arm Type",
            "ArmType_0001",
            catalogue_name,
            library_name,
            codelists=[
                {
                    "uid": arm_type_codelist.codelist_uid,
                    "order": 1,
                    "submission_value": "Arm Type",
                }
            ],
        )
        self.study_arms = [
            create_study_arm(
                study_uid=self.study.uid,
                name="Arm_Name_1",
                short_name="Arm_Short_Name_1",
                code="Arm_code_1",
                description="desc...",
                randomization_group="Randomization_Group_1",
                number_of_subjects=1,
                arm_type_uid=arm_type_term.uid,
            ),
            create_study_arm(
                study_uid=self.study.uid,
                name="Arm_Name_2",
                short_name="Arm_Short_Name_2",
                code="Arm_code_2",
                description="desc...",
                randomization_group="Randomization_Group_2",
                number_of_subjects=1,
                arm_type_uid=arm_type_term.uid,
            ),
            create_study_arm(
                study_uid=self.study.uid,
                name="Arm_Name_3",
                short_name="Arm_Short_Name_3",
                code="Arm_code_3",
                description="desc...",
                randomization_group="Randomization_Group_3",
                number_of_subjects=3,
                arm_type_uid=arm_type_term.uid,
            ),
            create_study_arm(
                study_uid=self.study.uid,
                name="Arm_Name_4",
                short_name="Arm_Short_Name_4",
                code="Arm_code_4",
                description="desc...",
                randomization_group="Randomization_Group_4",
                number_of_subjects=3,
                arm_type_uid=arm_type_term.uid,
            ),
            create_study_arm(
                study_uid=self.study.uid,
                name="Arm_Name_5",
                short_name="Arm_Short_Name_5",
                code="Arm_code_5",
                description="desc...",
                randomization_group="Randomization_Group_5",
                number_of_subjects=3,
                arm_type_uid=arm_type_term.uid,
            ),
        ]

        # Create a study element
        element_subtype_codelist = create_codelist(
            "Element Subtype",
            "CTCodelist_ElementType",
            catalogue_name,
            library_name,
            submission_value="ELEMSTP",
        )
        element_subtype_term = create_ct_term(
            "Element Subtype",
            "ElementSubType_0001",
            catalogue_name,
            library_name,
            codelists=[
                {
                    "uid": element_subtype_codelist.codelist_uid,
                    "order": 1,
                    "submission_value": "Element SubType",
                }
            ],
        )
        element_subtype_term_2 = create_ct_term(
            "Element Subtype2",
            "ElementSubType_0002",
            catalogue_name,
            library_name,
            codelists=[
                {
                    "uid": element_subtype_codelist.codelist_uid,
                    "order": 2,
                    "submission_value": "Element SubType2",
                }
            ],
        )
        self.study_elements = [
            create_study_element(element_subtype_term.uid, self.study.uid),
            create_study_element(element_subtype_term_2.uid, self.study.uid),
        ]

        # Create a study branch arm
        self.study_branch_arms = [
            create_study_branch_arm(
                self.study.uid,
                name="BranchArm_Name_1",
                short_name="BranchArm_Short_Name_1",
                code="BranchArm_code_1",
                description="desc...",
                randomization_group="Randomization_Group_1",
                number_of_subjects=1,
                arm_uid=self.study_arms[0].arm_uid,
            ),
            create_study_branch_arm(
                self.study.uid,
                name="BranchArm_Name_2",
                short_name="BranchArm_Short_Name_2",
                code="BranchArm_code_2",
                description="desc...",
                randomization_group="BranchArm_Randomization_Group_2",
                number_of_subjects=1,
                arm_uid=self.study_arms[1].arm_uid,
            ),
            create_study_branch_arm(
                self.study.uid,
                name="BranchArm_Name_3",
                short_name="BranchArm_Short_Name_3",
                code="BranchArm_code_3",
                description="desc...",
                randomization_group="Randomization_Group_3",
                number_of_subjects=1,
                arm_uid=self.study_arms[0].arm_uid,
            ),
            create_study_branch_arm(
                self.study.uid,
                name="BranchArm_Name_4",
                short_name="BranchArm_Short_Name_4",
                code="BranchArm_code_4",
                description="desc...",
                randomization_group="BranchArm_Randomization_Group_4",
                number_of_subjects=1,
                arm_uid=self.study_arms[1].arm_uid,
            ),
            create_study_branch_arm(
                self.study.uid,
                name="BranchArm_Name_5",
                short_name="BranchArm_Short_Name_5",
                code="BranchArm_code_5",
                description="desc...",
                randomization_group="BranchArm_Randomization_Group_5",
                number_of_subjects=1,
                arm_uid=self.study_arms[1].arm_uid,
            ),
        ]

    def test_create_patch_delete_design_cell(self):
        service = StudyDesignCellService()
        # Check if the BusinessLogicException is raised when a StudyDesignCell is assigned to an Arm that has StudyBranchArm assigned to it.
        with self.assertRaises(exceptions.BusinessLogicException):
            # Create a design cell -- Arm Specified
            design_cell = service.create(
                self.study.uid,
                StudyDesignCellCreateInput(
                    study_arm_uid=self.study_arms[0].arm_uid,
                    study_epoch_uid=self.study_epoch.uid,
                    study_element_uid=self.study_elements[0].element_uid,
                    transition_rule="Transition_Rule_2",
                ),
            )

        # Create a design cell -- Arm Specified
        design_cell = service.create(
            self.study.uid,
            StudyDesignCellCreateInput(
                study_arm_uid=self.study_arms[2].arm_uid,
                study_epoch_uid=self.study_epoch.uid,
                study_element_uid=self.study_elements[0].element_uid,
                transition_rule="Transition_Rule_2",
            ),
        )

        design_cells = service.get_all_design_cells(self.study.uid)
        assert len(design_cells) == 1

        # Patch a design cell - patch on study arm and study element
        # Will return a 204 no content
        design_cell_uid = design_cells[0].design_cell_uid
        service.patch(
            self.study.uid,
            StudyDesignCellEditInput(
                study_design_cell_uid=design_cell_uid,
                study_arm_uid=self.study_arms[2].arm_uid,
                study_element_uid=self.study_elements[1].element_uid,
            ),
        )
        # Get the updated design cell
        # This will also test the get specific design cell
        design_cell = service.get_specific_design_cell(self.study.uid, design_cell_uid)
        assert design_cell.study_element_uid == self.study_elements[1].element_uid
        assert design_cell.study_arm_uid == self.study_arms[2].arm_uid

        # Patch a design cell - switching between study arm and study branch arm
        # Will return a 204 no content
        design_cell_uid = design_cells[0].design_cell_uid
        service.patch(
            self.study.uid,
            StudyDesignCellEditInput(
                study_design_cell_uid=design_cell_uid,
                study_branch_arm_uid=self.study_branch_arms[0].branch_arm_uid,
            ),
        )
        # Get the updated design cell
        # This will also test the get specific design cell
        design_cell = service.get_specific_design_cell(self.study.uid, design_cell_uid)
        assert design_cell.study_arm_uid is None
        assert (
            design_cell.study_branch_arm_uid == self.study_branch_arms[0].branch_arm_uid
        )

        # Patch a design cell - patch on study branch arm
        # Will return a 204 no content
        design_cell_uid = design_cells[0].design_cell_uid
        service.patch(
            self.study.uid,
            StudyDesignCellEditInput(
                study_design_cell_uid=design_cell_uid,
                study_branch_arm_uid=self.study_branch_arms[1].branch_arm_uid,
            ),
        )
        # Get the updated design cell
        # This will also test the get specific design cell
        design_cell = service.get_specific_design_cell(self.study.uid, design_cell_uid)
        assert design_cell.study_arm_uid is None
        assert (
            design_cell.study_branch_arm_uid == self.study_branch_arms[1].branch_arm_uid
        )

        # Create a design cell -- Branch Specified
        design_cell = service.create(
            self.study.uid,
            StudyDesignCellCreateInput(
                study_branch_arm_uid=self.study_branch_arms[0].branch_arm_uid,
                study_epoch_uid=self.study_epoch.uid,
                study_element_uid=self.study_elements[0].element_uid,
                transition_rule="Transition_Rule_1",
            ),
        )
        design_cells = service.get_all_design_cells(self.study.uid)
        assert len(design_cells) == 2

        # Patch a design cell - patch on study arm and study element
        # Will return a 204 no content
        design_cell_uid = design_cells[0].design_cell_uid
        service.patch(
            self.study.uid,
            StudyDesignCellEditInput(
                study_design_cell_uid=design_cell_uid,
                study_branch_arm_uid=self.study_branch_arms[1].branch_arm_uid,
                study_element_uid=self.study_elements[1].element_uid,
            ),
        )
        # Get the updated design cell
        # This will also test the get specific design cell
        design_cell = service.get_specific_design_cell(self.study.uid, design_cell_uid)
        assert design_cell.study_arm_uid is None
        assert (
            design_cell.study_branch_arm_uid == self.study_branch_arms[1].branch_arm_uid
        )

        # Patch a design cell - switching between study branch arm and study arm
        # Will return a 204 no content
        design_cell_uid = design_cells[0].design_cell_uid
        service.patch(
            self.study.uid,
            StudyDesignCellEditInput(
                study_design_cell_uid=design_cell_uid,
                study_arm_uid=self.study_arms[2].arm_uid,
                study_branch_arm_uid=None,
            ),
        )
        # Get the updated design cell
        # This will also test the get specific design cell
        design_cell = service.get_specific_design_cell(self.study.uid, design_cell_uid)
        assert design_cell.study_element_uid == self.study_elements[1].element_uid
        assert design_cell.study_arm_uid == self.study_arms[2].arm_uid
        assert design_cell.study_branch_arm_uid is None

        # Patch a design cell - patch on study arm and study element
        # Will return a 204 no content
        design_cell_uid = design_cells[0].design_cell_uid
        service.patch(
            self.study.uid,
            StudyDesignCellEditInput(
                study_design_cell_uid=design_cell_uid,
                study_arm_uid=self.study_arms[2].arm_uid,
            ),
        )
        # Get the updated design cell
        # This will also test the get specific design cell
        design_cell = service.get_specific_design_cell(self.study.uid, design_cell_uid)
        assert design_cell.study_arm_uid == self.study_arms[2].arm_uid
        assert design_cell.study_branch_arm_uid is None

        # Delete a design cell
        service.delete(self.study.uid, design_cell_uid)
        design_cells = service.get_all_design_cells(self.study.uid)
        assert len(design_cells) == 1

    def test_batch_operations(self):
        service = StudyDesignCellService()

        # create
        service.handle_batch_operations(
            self.study.uid,
            [
                StudyDesignCellBatchInput(
                    method="POST",
                    content=StudyDesignCellCreateInput(
                        study_arm_uid=self.study_arms[2].arm_uid,
                        study_epoch_uid=self.study_epoch.uid,
                        study_element_uid=self.study_elements[0].element_uid,
                        transition_rule="Transition_Rule_1",
                    ),
                ),
                StudyDesignCellBatchInput(
                    method="POST",
                    content=StudyDesignCellCreateInput(
                        study_arm_uid=self.study_arms[3].arm_uid,
                        study_epoch_uid=self.study_epoch.uid,
                        study_element_uid=self.study_elements[1].element_uid,
                        transition_rule="Transition_Rule_2",
                    ),
                ),
                StudyDesignCellBatchInput(
                    method="POST",
                    content=StudyDesignCellCreateInput(
                        study_branch_arm_uid=self.study_branch_arms[0].branch_arm_uid,
                        study_epoch_uid=self.study_epoch.uid,
                        study_element_uid=self.study_elements[0].element_uid,
                        transition_rule="Transition_Rule_3",
                    ),
                ),
                StudyDesignCellBatchInput(
                    method="POST",
                    content=StudyDesignCellCreateInput(
                        study_branch_arm_uid=self.study_branch_arms[1].branch_arm_uid,
                        study_epoch_uid=self.study_epoch.uid,
                        study_element_uid=self.study_elements[1].element_uid,
                        transition_rule="Transition_Rule_4",
                    ),
                ),
            ],
        )
        design_cells = service.get_all_design_cells(self.study.uid)
        assert len(design_cells) == 4

        # patch
        design_cells = service.get_all_design_cells(self.study.uid)
        service.handle_batch_operations(
            self.study.uid,
            [
                StudyDesignCellBatchInput(
                    method="PATCH",
                    content=StudyDesignCellEditInput(
                        study_design_cell_uid=design_cells[0].design_cell_uid,
                        study_element_uid=self.study_elements[1].element_uid,
                        study_arm_uid=self.study_arms[2].arm_uid,
                        study_branch_arm_uid=None,
                    ),
                ),
                StudyDesignCellBatchInput(
                    method="PATCH",
                    content=StudyDesignCellEditInput(
                        study_design_cell_uid=design_cells[1].design_cell_uid,
                        study_element_uid=self.study_elements[0].element_uid,
                        study_branch_arm_uid=self.study_branch_arms[2].branch_arm_uid,
                    ),
                ),
                StudyDesignCellBatchInput(
                    method="PATCH",
                    content=StudyDesignCellEditInput(
                        study_design_cell_uid=design_cells[2].design_cell_uid,
                        study_branch_arm_uid=self.study_branch_arms[3].branch_arm_uid,
                    ),
                ),
                StudyDesignCellBatchInput(
                    method="PATCH",
                    content=StudyDesignCellEditInput(
                        study_design_cell_uid=design_cells[3].design_cell_uid,
                        study_branch_arm_uid=self.study_branch_arms[4].branch_arm_uid,
                    ),
                ),
            ],
        )
        design_cell = service.get_specific_design_cell(
            self.study.uid, design_cells[0].design_cell_uid
        )
        assert design_cell.study_element_uid == self.study_elements[1].element_uid
        assert design_cell.study_arm_uid == self.study_arms[2].arm_uid
        assert design_cell.study_branch_arm_uid is None
        design_cell = service.get_specific_design_cell(
            self.study.uid, design_cells[1].design_cell_uid
        )
        assert design_cell.study_element_uid == self.study_elements[0].element_uid
        assert design_cell.study_arm_uid is None
        assert (
            design_cell.study_branch_arm_uid == self.study_branch_arms[2].branch_arm_uid
        )
        design_cell = service.get_specific_design_cell(
            self.study.uid, design_cells[2].design_cell_uid
        )
        assert design_cell.study_arm_uid is None
        assert (
            design_cell.study_branch_arm_uid == self.study_branch_arms[3].branch_arm_uid
        )
        design_cell = service.get_specific_design_cell(
            self.study.uid, design_cells[3].design_cell_uid
        )
        assert design_cell.study_arm_uid is None
        assert (
            design_cell.study_branch_arm_uid == self.study_branch_arms[4].branch_arm_uid
        )

        # delete
        design_cells = service.get_all_design_cells(self.study.uid)
        service.handle_batch_operations(
            self.study.uid,
            [
                StudyDesignCellBatchInput(
                    method="DELETE",
                    content=StudyDesignCellDeleteInput(
                        uid=design_cells[0].design_cell_uid
                    ),
                ),
                StudyDesignCellBatchInput(
                    method="DELETE",
                    content=StudyDesignCellDeleteInput(
                        uid=design_cells[1].design_cell_uid
                    ),
                ),
                StudyDesignCellBatchInput(
                    method="DELETE",
                    content=StudyDesignCellDeleteInput(
                        uid=design_cells[2].design_cell_uid
                    ),
                ),
                StudyDesignCellBatchInput(
                    method="DELETE",
                    content=StudyDesignCellDeleteInput(
                        uid=design_cells[3].design_cell_uid
                    ),
                ),
            ],
        )
        design_cells = service.get_all_design_cells(self.study.uid)
        assert len(design_cells) == 0

    def test_get_design_matrix_structure_page_pagination(self):
        service = StudyDesignCellService()

        design_cells_to_create = [
            StudyDesignCellCreateInput(
                study_arm_uid=self.study_arms[2].arm_uid,
                study_epoch_uid=self.study_epoch.uid,
                study_element_uid=self.study_elements[0].element_uid,
                transition_rule="Transition_Rule_1",
            ),
            StudyDesignCellCreateInput(
                study_arm_uid=self.study_arms[3].arm_uid,
                study_epoch_uid=self.study_epoch.uid,
                study_element_uid=self.study_elements[1].element_uid,
                transition_rule="Transition_Rule_2",
            ),
            StudyDesignCellCreateInput(
                study_arm_uid=self.study_arms[4].arm_uid,
                study_epoch_uid=self.study_epoch.uid,
                study_element_uid=self.study_elements[0].element_uid,
                transition_rule="Transition_Rule_3",
            ),
            StudyDesignCellCreateInput(
                study_branch_arm_uid=self.study_branch_arms[0].branch_arm_uid,
                study_epoch_uid=self.study_epoch2.uid,
                study_element_uid=self.study_elements[1].element_uid,
                transition_rule="Transition_Rule_4",
            ),
            StudyDesignCellCreateInput(
                study_branch_arm_uid=self.study_branch_arms[1].branch_arm_uid,
                study_epoch_uid=self.study_epoch2.uid,
                study_element_uid=self.study_elements[0].element_uid,
                transition_rule="Transition_Rule_5",
            ),
        ]

        for design_cell_input in design_cells_to_create:
            service.create(self.study.uid, design_cell_input)

        first_page = service.get_design_matrix_structure_page(
            study_uid=self.study.uid, page_number=1, page_size=2
        )
        assert first_page.total == 5
        assert first_page.page == 1
        assert first_page.size == 2
        assert len(first_page.items) == 2

        third_page = service.get_design_matrix_structure_page(
            study_uid=self.study.uid, page_number=3, page_size=2
        )
        assert third_page.total == 5
        assert third_page.page == 3
        assert third_page.size == 2
        assert len(third_page.items) == 1

        out_of_range_page = service.get_design_matrix_structure_page(
            study_uid=self.study.uid, page_number=4, page_size=2
        )
        assert out_of_range_page.total == 5
        assert out_of_range_page.page == 4
        assert out_of_range_page.size == 2
        assert len(out_of_range_page.items) == 0

        unpaged = service.get_design_matrix_structure_page(
            study_uid=self.study.uid, page_number=1, page_size=0
        )
        assert unpaged.total == 5
        assert unpaged.page == 1
        assert unpaged.size == 5
        assert len(unpaged.items) == 5
