# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=invalid-name

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.main import app
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpochEditInput
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.tests.integration.api.old.utils import assert_study_arm
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    create_reason_for_lock_unlock_terms,
    fix_study_preferred_time_unit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_arm,
    create_study_branch_arm,
    create_study_cohort,
    create_study_design_cell,
    create_study_element,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    edit_study_arm,
    edit_study_element,
    edit_study_epoch,
    get_catalogue_name_library_name,
    patch_study_branch_arm,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

test_data_dict = {}
reason_for_lock_term_uid = None
reason_for_unlock_term_uid = None


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.design.joint")
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    StudyRoot.generate_node_uids_if_not_present()
    study = StudyRoot.nodes.all()[0]
    test_data_dict["study"] = study
    TestUtils.create_ct_catalogue(catalogue_name=settings.sdtm_ct_catalogue_name)
    TestUtils.set_study_standard_version(
        study_uid=study.uid, create_codelists_and_terms_for_package=False
    )
    global reason_for_lock_term_uid, reason_for_unlock_term_uid
    lock_unlock_data = create_reason_for_lock_unlock_terms()
    reason_for_lock_term_uid = lock_unlock_data["reason_for_lock_terms"][0].term_uid
    reason_for_unlock_term_uid = lock_unlock_data["reason_for_unlock_terms"][0].term_uid

    create_study_epoch_codelists_ret_cat_and_lib()
    _catalogue_name, library_name = get_catalogue_name_library_name()
    catalogue_name = "SDTM CT"
    study_epoch = create_study_epoch("EpochSubType_0001")
    test_data_dict["study_epoch"] = study_epoch
    study_epoch2 = create_study_epoch("EpochSubType_0001")
    test_data_dict["study_epoch2"] = study_epoch2

    # Create a study element
    element_subtype_codelist = create_codelist(
        "Element Sub Type",
        "CTCodelist_ElementSubType",
        catalogue_name,
        library_name,
        submission_value="ELEMSTP",
    )
    test_data_dict["element_subtype_codelist"] = element_subtype_codelist
    element_type_term = create_ct_term(
        "Element Sub Type",
        "ElementSubType_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": element_subtype_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Element Sub Type",
            }
        ],
    )
    test_data_dict["element_type_term"] = element_type_term
    element_type_term_2 = create_ct_term(
        "Element Sub Type 2",
        "ElementSubType_0002",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": element_subtype_codelist.codelist_uid,
                "order": 2,
                "submission_value": "Element Sub Type 2",
            }
        ],
    )
    test_data_dict["element_type_term_2"] = element_type_term_2
    study_elements = [
        create_study_element(element_type_term.uid, study.uid),
        create_study_element(element_type_term_2.uid, study.uid),
    ]
    test_data_dict["study_elements"] = study_elements

    arm_type_codelist = create_codelist(
        name="Arm Type",
        uid="CTCodelist_00004",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="ARMTTP",
    )
    test_data_dict["arm_type_codelist"] = arm_type_codelist

    arm_type = create_ct_term(
        name="Arm Type",
        uid="ArmType_0001",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": arm_type_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Arm Type",
            }
        ],
    )
    test_data_dict["arm_type"] = arm_type

    arm1 = create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_1",
        short_name="Arm_Short_Name_1",
        code="Arm_code_1",
        description="desc...",
        randomization_group="Arm_randomizationGroup",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )
    test_data_dict["arm1"] = arm1
    arm2 = create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_2",
        short_name="Arm_Short_Name_2",
        code="Arm_code_2",
        description="desc...",
        randomization_group="Arm_randomizationGroup2",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )
    test_data_dict["arm2"] = arm2
    arm3 = create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_3",
        short_name="Arm_Short_Name_3",
        code="Arm_code_3",
        description="desc...",
        randomization_group="Arm_randomizationGroup3",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )
    test_data_dict["arm3"] = arm3

    arm4 = create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_9",
        short_name="Arm_Short_Name_9",
        code="Arm_code_9",
        description="desc...",
        randomization_group="Arm_randomizationGroup9",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )
    test_data_dict["arm4"] = arm4
    arm5 = create_study_arm(
        study_uid=study.uid,
        name="Arm_Name_10",
        short_name="Arm_Short_Name_10",
        code="Arm_code_10",
        description="desc...",
        randomization_group="Arm_randomizationGroup10",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )
    test_data_dict["arm5"] = arm5

    design_cell = create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch.uid,
        study_arm_uid=arm3.arm_uid,
        study_uid=study.uid,
    )
    test_data_dict["design_cell"] = design_cell
    design_cell2 = create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid=arm3.arm_uid,
        study_uid=study.uid,
    )
    test_data_dict["design_cell3"] = design_cell2

    design_cell2 = create_study_design_cell(
        study_element_uid=study_elements[1].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid=arm1.arm_uid,
        study_uid=study.uid,
    )
    test_data_dict["design_cell4"] = design_cell2

    branch_arm = create_study_branch_arm(
        study_uid=study.uid,
        name="Branch_Arm_Name_1",
        short_name="Branch_Arm_Short_Name_1",
        code="Branch_Arm_code_1",
        description="desc...",
        randomization_group="Branch_Arm_randomizationGroup",
        number_of_subjects=100,
        arm_uid=arm3.arm_uid,
    )
    test_data_dict["branch_arm"] = branch_arm
    branch_arm = patch_study_branch_arm(
        branch_arm_uid=branch_arm.branch_arm_uid, study_uid=study.uid
    )
    branch_arm2 = create_study_branch_arm(
        study_uid=study.uid,
        name="Branch_Arm_Name_2",
        short_name="Branch_Arm_Short_Name_2",
        code="Branch_Arm_code_2",
        description="desc 2...",
        randomization_group="Branch_Arm_randomizationGroup2",
        number_of_subjects=100,
        arm_uid=arm3.arm_uid,
    )
    test_data_dict["branch_arm2"] = branch_arm2
    branch_arm3 = create_study_branch_arm(
        study_uid=study.uid,
        name="Branch_Arm_Name_3",
        short_name="Branch_Arm_Short_Name_3",
        code="Branch_Arm_code_3",
        description="desc 3...",
        randomization_group="Branch_Arm_randomizationGroup3",
        number_of_subjects=100,
        arm_uid=arm3.arm_uid,
    )
    test_data_dict["branch_arm3"] = branch_arm3
    branch_arm4 = create_study_branch_arm(
        study_uid=study.uid,
        name="Branch_Arm_Name_4",
        short_name="Branch_Arm_Short_Name_4",
        code="Branch_Arm_code_4",
        description="desc 4...",
        randomization_group="Branch_Arm_randomizationGroup4",
        number_of_subjects=100,
        arm_uid=arm5.arm_uid,
    )
    test_data_dict["branch_arm4"] = branch_arm4

    design_cell3 = create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid=arm4.arm_uid,
        study_uid=study.uid,
    )
    test_data_dict["design_cell3"] = design_cell3

    cohort = create_study_cohort(
        study_uid=study.uid,
        name="Cohort_Name_1",
        short_name="Cohort_Short_Name_1",
        code="Cohort_code_1",
        description="desc...",
        number_of_subjects=100,
        arm_uids=[arm1.arm_uid],
    )
    test_data_dict["cohort"] = cohort
    # edit arm, epoch, elements to track if the relationships keep maintained and the ZeroOrMore cardinality is managed
    arm1 = edit_study_arm(
        study_uid=study.uid,
        arm_uid=arm1.arm_uid,
        name="last_edit_arm_name",  # previous "Arm_Name_1"
        short_name="last_edit_short_name",  # previous "Arm_Short_Name_1"
    )
    study_epoch = edit_study_epoch(
        epoch_uid=study_epoch.uid, study_uid=study_epoch.study_uid
    )
    study_epoch2 = edit_study_epoch(
        epoch_uid=study_epoch2.uid, study_uid=study_epoch2.study_uid
    )
    study_elements = [
        edit_study_element(
            element_uid=study_elements[0].element_uid,
            study_uid=study.uid,
            new_short_name="short_element 1",
        ),
        edit_study_element(
            element_uid=study_elements[1].element_uid,
            study_uid=study.uid,
            new_short_name="short_element_2",
        ),
    ]
    epoch_service = StudyEpochService()
    epoch = epoch_service.find_by_uid(
        study_epoch2.uid, study_uid=study_epoch2.study_uid
    )
    start_rule = "New start rule"
    end_rule = "New end rule"
    edit_input = StudyEpochEditInput(
        study_uid=epoch.study_uid,
        start_rule=start_rule,
        end_rule=end_rule,
        change_description="rules change",
    )
    study_epoch3 = epoch_service.edit(
        study_uid=epoch.study_uid,
        study_epoch_uid=epoch.uid,
        study_epoch_input=edit_input,
    )
    test_data_dict["study_epoch3"] = study_epoch3
    # locking and unlocking to create multiple study value relationships on the existent StudySelections
    fix_study_preferred_time_unit(study.uid)

    yield

    drop_db("old.json.test.study.design.joint")


def test_if_the_study_design_cells_connected_to_branch_arm_update_the_connection_the_updated_one(
    api_client,
):
    response = api_client.get("/studies/study_root/study-branch-arms")

    assert_response_status_code(response, 200)

    res = response.json()["items"]

    assert res[0]["study_uid"] == test_data_dict["study"].uid
    assert res[0]["order"] == 1
    assert res[0]["study_version"]
    assert res[0]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res[0]["name"] == "Branch_Arm_Name_1_edit"
    assert res[0]["short_name"] == "Branch_Arm_Short_Name_1"
    assert res[0]["code"] == "Branch_Arm_code_1"
    assert res[0]["description"] == "desc..."
    assert res[0]["randomization_group"] == "Branch_Arm_randomizationGroup"
    assert res[0]["number_of_subjects"] == 100
    assert_study_arm(res[0]["arm_root"], test_data_dict["arm3"])
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] is None
    assert res[0]["accepted_version"] is False


def test_if_the_studydesigncells_relations_update_arm_root(api_client):
    response = api_client.delete(
        "studies/study_root/study-branch-arms/StudyBranchArm_000001"
    )

    assert_response_status_code(response, 204)


def test_adding_selection_studybrancharm_to_switch_the_studydeisgncells_from_the_studybrancharm_to_the_studyarm(
    api_client,
):
    data = {
        "name": "BranchArm_Name_7",
        "short_name": "BranchArm_Short_Name_7",
        "code": "BranchArm_code_7",
        "description": "desc...",
        "randomization_group": "Randomization_Group_7",
        "number_of_subjects": 2,
        "arm_uid": test_data_dict["arm3"].arm_uid,
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == test_data_dict["study"].uid
    assert res["study_version"]
    assert res["branch_arm_uid"].startswith("StudyBranchArm_")
    # assert res["order"] == 1
    assert res["name"] == "BranchArm_Name_7"
    assert res["short_name"] == "BranchArm_Short_Name_7"
    assert res["code"] == "BranchArm_code_7"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert_study_arm(res["arm_root"], test_data_dict["arm3"])
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 2
    assert res["randomization_group"] == "Randomization_Group_7"
    assert res["author_username"] == "unknown-user@example.com"


def test_get_audit_trail_for_all_design_cells_should_expect_to_the_study_design_cell_00001_and_study_design_cell_000002_to_switch_from_arm_000003_to_brancharm_000005(
    api_client,
):
    response = api_client.get("/studies/study_root/study-design-cells/audit-trail/")

    assert_response_status_code(response, 200)


def test_adding_selection_studybrancharm_to_then_test_delete_on_many_studybrancharms_so_after_not_switch_the_studydesigncells_but_delete_them(
    api_client,
):
    data = {
        "name": "BranchArm_Name_9",
        "short_name": "BranchArm_Short_Name_9",
        "code": "BranchArm_code_9",
        "description": "desc...",
        "randomization_group": "Randomization_Group_9",
        "number_of_subjects": 2,
        "arm_uid": test_data_dict["arm3"].arm_uid,
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == test_data_dict["study"].uid
    assert res["study_version"]
    assert res["branch_arm_uid"].startswith("StudyBranchArm_")
    # assert res["order"] == 4
    assert res["name"] == "BranchArm_Name_9"
    assert res["short_name"] == "BranchArm_Short_Name_9"
    assert res["code"] == "BranchArm_code_9"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert_study_arm(res["arm_root"], test_data_dict["arm3"])
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 2
    assert res["randomization_group"] == "Randomization_Group_9"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_designcell_to_the_many_studybranch(api_client):
    data = {
        "study_branch_arm_uid": test_data_dict["branch_arm2"].branch_arm_uid,
        "study_epoch_uid": test_data_dict["study_epoch"].uid,
        "study_element_uid": test_data_dict["study_elements"][0].element_uid,
        "transition_rule": "Transition_Rule_3",
    }
    response = api_client.post(
        f"/studies/{test_data_dict["study"].uid}/study-design-cells", json=data
    )

    assert response.status_code == 201


def test_add_study_title_test_to_have_multiple_study_value_relationships_attached4(
    api_client,
):
    data = {"current_metadata": {"study_description": {"study_title": "new title"}}}
    response = api_client.patch("/studies/study_root", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == test_data_dict["study"].uid
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "0"
    assert res["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert res["current_metadata"]["identification_metadata"]["study_acronym"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert res["current_metadata"]["identification_metadata"]["project_number"] == "123"
    assert res["current_metadata"]["identification_metadata"]["description"] is None
    assert res["current_metadata"]["identification_metadata"]["project_name"] == "name"
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "Test CP"
    )
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "some_id-0"
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"] is not None
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["study_description"]["study_title"] == "new title"
    assert res["current_metadata"]["study_description"]["study_short_title"] is None


def test_lock_study_test_to_have_multiple_study_value_relationships_attached8(
    api_client,
):
    data = {
        "change_description": "Lock 1",
        "reason_for_change_uid": reason_for_lock_term_uid,
    }
    response = api_client.post("/studies/study_root/locks", json=data)

    assert response.status_code == 201


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached8(
    api_client,
):
    response = api_client.post(
        "/studies/study_root/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": reason_for_unlock_term_uid,
        },
    )

    assert response.status_code == 201


def test_patch_specific_try_to_patch_the_studyarm_of_a_studybrancharm_that_has_studydesigncell_connected_to_it(
    api_client,
):
    data = {"arm_uid": test_data_dict["arm1"].arm_uid}
    response = api_client.patch(
        f"/studies/{test_data_dict["study"].uid}/study-branch-arms/{test_data_dict['branch_arm2'].branch_arm_uid}",
        json=data,
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == f"Cannot change StudyArm when the BranchArm with UID '{test_data_dict['branch_arm2'].branch_arm_uid}' has connected StudyDesignCells."
    )


def test_test_if_the_cascade_delete_of_studydesigncells_on_the_study_arm_works(
    api_client,
):
    response = api_client.delete(
        f"/studies/study_root/study-arms/{test_data_dict['arm2'].arm_uid}"
    )

    assert_response_status_code(response, 204)


def test_get_audit_trail_for_all_design_cells_should_expect_to_delete_the_study_design_cell_000004_change_of_order_of_study_design_cell_00005(
    api_client,
):
    response = api_client.get("/studies/study_root/study-design-cells/audit-trail/")

    assert_response_status_code(response, 200)


def test_lock_study_test_to_have_multiple_study_value_relationships_attached9(
    api_client,
):
    data = {
        "change_description": "Lock 1",
        "reason_for_change_uid": reason_for_lock_term_uid,
    }
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached9(
    api_client,
):
    response = api_client.post(
        "/studies/study_root/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": reason_for_unlock_term_uid,
        },
    )

    assert_response_status_code(response, 201)


def test_patch_specific_set_name5(api_client):
    data = {"name": "New_Element_Name_2", "element_subtype_uid": "ElementSubType_0001"}
    response = api_client.patch(
        "/studies/study_root/study-elements/StudyElement_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == test_data_dict["study"].uid
    assert res["order"] == 1
    assert res["study_version"]
    assert res["element_uid"] == "StudyElement_000001"
    assert res["name"] == "New_Element_Name_2"
    assert res["short_name"] == "short_element 1"
    assert res["code"] == "Element_code_1"
    assert res["description"] == "desc..."
    assert res["planned_duration"] is None
    assert res["start_rule"] is None
    assert res["end_rule"] is None
    assert res["element_colour"] is None
    assert res["study_compound_dosing_count"] == 0
    assert res["element_type"] is None
    assert res["element_subtype"]["term_uid"] == "ElementSubType_0001"
    assert res["element_subtype"]["term_name"] == "Element Sub Type"
    assert res["element_subtype"]["codelist_uid"] == "CTCodelist_ElementSubType"
    assert res["element_subtype"]["codelist_name"] == "Element Sub Type"
    assert res["element_subtype"]["codelist_submission_value"] == "ELEMSTP"
    assert res["element_subtype"]["order"] == 1
    assert res["element_subtype"]["submission_value"] == "Element Sub Type"
    assert res["element_subtype"]["queried_effective_date"] is not None
    assert res["element_subtype"]["date_conflict"] is False
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False


def test_adding_selection_studybrancharm_and_then_deleting_it_to_test_that_the_nested_branches_on_arms_are_just_the_one_with_study_value_connected_to_them(
    api_client,
):
    data = {
        "name": "BranchArm_Name_10",
        "short_name": "BranchArm_Short_Name_10",
        "code": "BranchArm_code_10",
        "description": "desc...",
        "randomization_group": "Randomization_Group_10",
        "number_of_subjects": 2,
        "arm_uid": test_data_dict["arm3"].arm_uid,
    }
    response = api_client.post(
        f"/studies/{test_data_dict["study"].uid}/study-branch-arms", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == test_data_dict["study"].uid
    assert res["study_version"]
    assert res["branch_arm_uid"].startswith("StudyBranchArm_")
    # assert res["order"] == 3
    assert res["name"] == "BranchArm_Name_10"
    assert res["short_name"] == "BranchArm_Short_Name_10"
    assert res["code"] == "BranchArm_code_10"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert_study_arm(res["arm_root"], test_data_dict["arm3"])
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 2
    assert res["randomization_group"] == "Randomization_Group_10"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_designcell_to_the_many_studybranch1(api_client):
    data = {
        "study_branch_arm_uid": test_data_dict["branch_arm3"].branch_arm_uid,
        "study_epoch_uid": test_data_dict["study_epoch"].uid,
        "study_element_uid": test_data_dict["study_elements"][0].element_uid,
        "transition_rule": "Transition_Rule_4",
    }
    response = api_client.post("/studies/study_root/study-design-cells", json=data)

    assert_response_status_code(response, 201)


def test_delete_studybrancharms_to_then_be_sure_that_the_connected_branches_are_just_those_who_actually_has_study_value_connection(
    api_client,
):
    response = api_client.delete(
        f"/studies/study_root/study-arms/{test_data_dict['arm4'].arm_uid}"
    )

    assert_response_status_code(response, 204)


def test_be_sure_that_the_connected_branches_are_just_those_who_actually_has_study_value_connection(
    api_client,
):
    response = api_client.get(
        f"/studies/study_root/study-arms/{test_data_dict['arm5'].arm_uid}"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == test_data_dict["study"].uid
    assert res["arm_uid"] == test_data_dict["arm5"].arm_uid
    assert len(res["arm_connected_branch_arms"]) == 1
    assert (
        res["arm_connected_branch_arms"][0]["study_uid"] == test_data_dict["study"].uid
    )
    assert (
        res["arm_connected_branch_arms"][0]["branch_arm_uid"]
        == test_data_dict["branch_arm4"].branch_arm_uid
    )
    assert res["arm_connected_branch_arms"][0]["number_of_subjects"] == 100
    assert res["arm_connected_branch_arms"][0]["start_date"]
    assert (
        res["arm_connected_branch_arms"][0]["author_username"]
        == "unknown-user@example.com"
    )
    assert res["arm_connected_branch_arms"][0]["end_date"] is None
    assert res["arm_connected_branch_arms"][0]["status"] is None
    assert res["arm_connected_branch_arms"][0]["change_type"] is None
    assert res["arm_connected_branch_arms"][0]["accepted_version"] is False


def test_patch_specific_set_arm_type_uid_to_null1(api_client):
    data = {"arm_type_uid": ""}
    response = api_client.patch(
        f"/studies/study_root/study-arms/{test_data_dict['arm3'].arm_uid}", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == test_data_dict["study"].uid
    assert res["order"] == 2
    assert res["study_version"]
    assert res["arm_uid"] == test_data_dict["arm3"].arm_uid
    assert res["name"] == "Arm_Name_3"
    assert res["short_name"] == "Arm_Short_Name_3"
    assert res["code"] == "Arm_code_3"
    assert res["description"] == "desc..."
    assert res["randomization_group"] == "Arm_randomizationGroup3"
    assert res["number_of_subjects"] == 100
    assert res["arm_type"] is None
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False

    assert res["arm_connected_branch_arms"][0]["study_uid"] == "study_root"
    assert res["arm_connected_branch_arms"][0]["order"] == 1
    assert (
        res["arm_connected_branch_arms"][0]["branch_arm_uid"]
        == test_data_dict["branch_arm2"].branch_arm_uid
    )
    assert (
        res["arm_connected_branch_arms"][0]["name"]
        == test_data_dict["branch_arm2"].name
    )
    assert (
        res["arm_connected_branch_arms"][0]["short_name"]
        == test_data_dict["branch_arm2"].short_name
    )
    assert (
        res["arm_connected_branch_arms"][0]["code"]
        == test_data_dict["branch_arm2"].code
    )
    assert (
        res["arm_connected_branch_arms"][0]["description"]
        == test_data_dict["branch_arm2"].description
    )
    assert (
        res["arm_connected_branch_arms"][0]["randomization_group"]
        == test_data_dict["branch_arm2"].randomization_group
    )
    assert (
        res["arm_connected_branch_arms"][0]["number_of_subjects"]
        == test_data_dict["branch_arm2"].number_of_subjects
    )
    assert res["arm_connected_branch_arms"][0]["start_date"]
    assert (
        res["arm_connected_branch_arms"][0]["author_username"]
        == test_data_dict["branch_arm2"].author_username
    )
    assert res["arm_connected_branch_arms"][0]["end_date"] is None
    assert res["arm_connected_branch_arms"][0]["status"] is None
    assert res["arm_connected_branch_arms"][0]["change_type"] is None
    assert res["arm_connected_branch_arms"][0]["accepted_version"] is False
    assert res["arm_connected_branch_arms"][1]["study_uid"] == "study_root"
    assert res["arm_connected_branch_arms"][1]["order"] == 2
    assert (
        res["arm_connected_branch_arms"][1]["branch_arm_uid"]
        == test_data_dict["branch_arm3"].branch_arm_uid
    )
    assert (
        res["arm_connected_branch_arms"][1]["name"]
        == test_data_dict["branch_arm3"].name
    )
    assert (
        res["arm_connected_branch_arms"][1]["short_name"]
        == test_data_dict["branch_arm3"].short_name
    )
    assert (
        res["arm_connected_branch_arms"][1]["code"]
        == test_data_dict["branch_arm3"].code
    )
    assert (
        res["arm_connected_branch_arms"][1]["description"]
        == test_data_dict["branch_arm3"].description
    )
    assert (
        res["arm_connected_branch_arms"][1]["randomization_group"]
        == test_data_dict["branch_arm3"].randomization_group
    )
    assert (
        res["arm_connected_branch_arms"][1]["number_of_subjects"]
        == test_data_dict["branch_arm3"].number_of_subjects
    )
    assert res["arm_connected_branch_arms"][1]["start_date"]
    assert (
        res["arm_connected_branch_arms"][1]["author_username"]
        == test_data_dict["branch_arm3"].author_username
    )
    assert res["arm_connected_branch_arms"][1]["end_date"] is None
    assert res["arm_connected_branch_arms"][1]["status"] is None
    assert res["arm_connected_branch_arms"][1]["change_type"] is None
    assert res["arm_connected_branch_arms"][1]["accepted_version"] is False


def test_test_if_the_cascade_delete_on_the_study_arm_works_with_design_cells(
    api_client,
):
    response = api_client.delete("/studies/study_root/study-arms/StudyArm_000002")

    assert_response_status_code(response, 204)


def test_get_audit_trail_for_all_design_cells_should_expect_0005_to_be_switched_to_arm_and_then_deleted_the_0002_and_0001_should_be_just_deleted_not_switched_and_the_00003_to_be_reordered(
    api_client,
):
    response = api_client.get("/studies/study_root/study-design-cells/audit-trail/")

    assert_response_status_code(response, 200)


def test_lock_study_test_to_have_multiple_study_value_relationships_attached10(
    api_client,
):
    data = {
        "change_description": "Lock 1",
        "reason_for_change_uid": reason_for_lock_term_uid,
    }
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached10(
    api_client,
):
    response = api_client.post(
        "/studies/study_root/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": reason_for_unlock_term_uid,
        },
    )

    assert_response_status_code(response, 201)


def test_if_the_cascade_delete_works_with_studyelement(api_client):
    response = api_client.delete(
        "/studies/study_root/study-elements/StudyElement_000003"
    )

    assert_response_status_code(response, 204)


def test_get_audit_trail_for_all_design_cells_should_expect_to_the_study_design_cell_00003_to_be_deleted(
    api_client,
):
    response = api_client.get("/studies/study_root/study-design-cells/audit-trail/")

    assert_response_status_code(response, 200)


def test_adding_designcell_to_have_the_scenario_of_having_many_studybranch(api_client):
    data = {
        "study_arm_uid": "StudyArm_000001",
        "study_epoch_uid": "StudyEpoch_000001",
        "study_element_uid": "StudyElement_000001",
        "transition_rule": "Transition_Rule_4",
    }
    response = api_client.post("/studies/study_root/study-design-cells", json=data)

    assert_response_status_code(response, 201)


def test_lock_study_test_to_have_multiple_study_value_relationships_attached11(
    api_client,
):
    data = {
        "change_description": "Lock 1",
        "reason_for_change_uid": reason_for_lock_term_uid,
    }
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached11(
    api_client,
):
    response = api_client.post(
        "/studies/study_root/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": reason_for_unlock_term_uid,
        },
    )

    assert_response_status_code(response, 201)


def test_if_the_cascade_delete_on_the_study_epochs_works_deleting_studydesigncells_attached_to_it(
    api_client,
):
    response = api_client.delete("/studies/study_root/study-epochs/StudyEpoch_000001")

    assert_response_status_code(response, 204)


def test_the_studyepoch_delete_functionality_actually_deletes_the_studyepoch(
    api_client,
):
    response = api_client.get("/studies/study_root/study-epochs")

    assert_response_status_code(response, 200)

    res = response.json()

    assert len(res["items"]) == 1
    assert res["items"][0]["study_uid"] == test_data_dict["study"].uid
    assert res["items"][0]["uid"] == test_data_dict["study_epoch2"].uid


def test_get_audit_trail_for_all_design_cells_should_expect_to_the_study_design_cell_00004_to_be_deleted_and_the_study_design_cell_000005_to_change_order(
    api_client,
):
    response = api_client.get("/studies/study_root/study-design-cells/audit-trail/")

    assert_response_status_code(response, 200)


def test_the_remained_studydesigncells_should_be_cascade_deleted_after_deleting_the_studyepoch(
    api_client,
):
    response = api_client.get("/studies/study_root/study-design-cells")

    assert_response_status_code(response, 200)


def test_test_if_the_cascade_delete_on_the_study_arm_works_with_cohorts(api_client):
    response = api_client.delete("/studies/study_root/study-arms/StudyArm_000001")

    assert_response_status_code(response, 204)


def test_adding_selection_studybrancharm_to_test_that_the_business_exception_has_to_be_raise_if_a_study_design_cell_is_trying_to_connect_to_an_arm_that_has_brancharms_connected_to_it(
    api_client,
):
    arm_data = {
        "name": "Arm_Name_99",
        "short_name": "Arm_Short_Name_99",
        "code": "Arm_code_99",
        "description": "desc...",
        "randomization_group": "Randomization_Group_99",
        "number_of_subjects": 99,
        "arm_type_uid": "ArmType_0001",
    }
    response = api_client.post("/studies/study_root/study-arms", json=arm_data)
    assert_response_status_code(response, 201)
    arm = response.json()
    data = {
        "name": "BranchArm_Name_15",
        "short_name": "BranchArm_Short_Name_15",
        "code": "BranchArm_code_15",
        "description": "desc...",
        "randomization_group": "Randomization_Group_15",
        "number_of_subjects": 10,
        "arm_uid": arm["arm_uid"],
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    branch = response.json()

    # lock and unlock study to have multiple study value relationships attached
    data = {
        "change_description": "Lock 1",
        "reason_for_change_uid": reason_for_lock_term_uid,
    }
    response = api_client.post("/studies/study_root/locks", json=data)
    assert_response_status_code(response, 201)
    response = api_client.post(
        "/studies/study_root/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": reason_for_unlock_term_uid,
        },
    )
    assert_response_status_code(response, 201)
    # adding designcell to arm that has branch arms connected_to_it_raise_the_business(
    data = {
        "study_arm_uid": arm["arm_uid"],
        "study_branch_arm_uid": branch["branch_arm_uid"],
        "study_epoch_uid": "StudyEpoch_000002",
        "study_element_uid": "StudyElement_000002",
        "transition_rule": "Transition_Rule_4",
    }
    response = api_client.post("/studies/study_root/study-design-cells", json=data)

    assert_response_status_code(response, 400)
    res = response.json()
    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == f"The Study Arm with UID '{arm['arm_uid']}' cannot be assigned to a Study Design Cell because it has Study Branch Arms assigned to it"
    )
