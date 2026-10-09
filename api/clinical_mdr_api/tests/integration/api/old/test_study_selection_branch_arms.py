import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.api.old.utils import assert_study_arm
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    create_reason_for_lock_unlock_terms,
    fix_study_preferred_time_unit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_arm,
    create_study_design_cell,
    create_study_element,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    edit_study_element,
    edit_study_epoch,
    get_catalogue_name_library_name,
    patch_order_study_design_cell,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

test_data_dict = {}
branch_arm_uids = []
reason_for_lock_term_uid = None
reason_for_unlock_term_uid = None

_NOT_NONE = object()
_BRANCH_ARM_AUDIT_DEFAULTS = {
    "study_uid": "study_root",
    "project_number": None,
    "project_name": None,
    "study_version": None,
    "author_username": "unknown-user@example.com",
    "status": None,
    "accepted_version": False,
}


def _assert_branch_arm_audit_entry(entry, expected):
    for field, value in (_BRANCH_ARM_AUDIT_DEFAULTS | expected).items():
        if field == "changes_unordered":
            assert set(entry["changes"]) == set(value)
        elif value is _NOT_NONE:
            assert entry[field] is not None
        else:
            assert entry[field] == value


def _assert_branch_arm_audit_entries(entries, expected_entries):
    assert len(entries) == len(expected_entries)
    for entry, expected in zip(entries, expected_entries):
        _assert_branch_arm_audit_entry(entry, expected)


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.selection.branch.arms")
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    StudyRoot.generate_node_uids_if_not_present()
    study = StudyRoot.nodes.all()[0]
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
    study_epoch2 = create_study_epoch("EpochSubType_0001")
    study_epoch = edit_study_epoch(
        epoch_uid=study_epoch.uid, study_uid=study_epoch.study_uid
    )
    study_epoch2 = edit_study_epoch(
        epoch_uid=study_epoch2.uid, study_uid=study_epoch2.study_uid
    )
    # Create a study element
    element_subtype_codelist = create_codelist(
        "Element Sub Type",
        "CTCodelist_ElementType",
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
    study_elements = [
        create_study_element(element_type_term.uid, study.uid),
        create_study_element(element_type_term_2.uid, study.uid),
    ]
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
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)

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
    # db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)
    create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch.uid,
        study_arm_uid="StudyArm_000003",
        study_uid=study.uid,
    )
    design_cell = create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid="StudyArm_000003",
        study_uid=study.uid,
    )
    # all the tests should work with a study design cell that has been edited
    design_cell = patch_order_study_design_cell(
        study_design_cell_uid=design_cell.design_cell_uid,
        study_uid=study.uid,
    )
    # locking and unlocking to create multiple study value relationships on the existent StudySelections
    fix_study_preferred_time_unit(study.uid)

    yield

    drop_db("old.json.test.study.selection.branch.arms")


def test_getting_empty_list2(api_client):
    response = api_client.get("/studies/study_root/study-branch-arms")

    assert_response_status_code(response, 200)

    res = response.json()["items"]

    assert res == []


def test_adding_selection3(api_client):
    data = {
        "name": "BranchArm_Name_1",
        "short_name": "BranchArm_Short_Name_1",
        "code": "BranchArm_code_1",
        "description": "desc...",
        "randomization_group": "Randomization_Group_1",
        "number_of_subjects": 1,
        "arm_uid": test_data_dict["arm1"].arm_uid,
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000001"
    branch_arm_uids.append(res["branch_arm_uid"])
    assert res["order"] == 1
    assert res["name"] == "BranchArm_Name_1"
    assert res["short_name"] == "BranchArm_Short_Name_1"
    assert res["code"] == "BranchArm_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert_study_arm(res["arm_root"], test_data_dict["arm1"])
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_get_all_within_a_arm_list_non_empty(api_client):
    response = api_client.get(
        "/studies/study_root/study-branch-arms/arm/StudyArm_000001"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["study_version"]
    assert res[0]["branch_arm_uid"] == branch_arm_uids[0]
    assert res[0]["order"] == 1
    assert res[0]["name"] == "BranchArm_Name_1"
    assert res[0]["short_name"] == "BranchArm_Short_Name_1"
    assert res[0]["code"] == "BranchArm_code_1"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] is None
    assert res[0]["accepted_version"] is False
    assert_study_arm(res[0]["arm_root"], test_data_dict["arm1"])
    assert res[0]["description"] == "desc..."
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["randomization_group"] == "Randomization_Group_1"
    assert res[0]["author_username"] == "unknown-user@example.com"


def test_get_all_list_non_empty2(api_client):
    response = api_client.get("/studies/study_root/study-branch-arms")

    assert_response_status_code(response, 200)

    res = response.json()["items"]

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["study_version"]
    assert res[0]["branch_arm_uid"] == branch_arm_uids[0]
    assert res[0]["order"] == 1
    assert res[0]["name"] == "BranchArm_Name_1"
    assert res[0]["short_name"] == "BranchArm_Short_Name_1"
    assert res[0]["code"] == "BranchArm_code_1"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] is None
    assert res[0]["accepted_version"] is False
    assert_study_arm(res[0]["arm_root"], test_data_dict["arm1"])
    assert res[0]["description"] == "desc..."
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["randomization_group"] == "Randomization_Group_1"
    assert res[0]["author_username"] == "unknown-user@example.com"


def test_get_specific2(api_client):
    response = api_client.get(
        f"/studies/study_root/study-branch-arms/{branch_arm_uids[0]}"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res["order"] == 1
    assert res["name"] == "BranchArm_Name_1"
    assert res["short_name"] == "BranchArm_Short_Name_1"
    assert res["code"] == "BranchArm_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert_study_arm(res["arm_root"], test_data_dict["arm1"])
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_add_study_title_test_to_have_multiple_study_value_relationships_attached2(
    api_client,
):
    data = {"current_metadata": {"study_description": {"study_title": "new title"}}}
    response = api_client.patch("/studies/study_root", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "study_root"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["study_description"]["study_title"] == "new title"


def test_lock_study_test_to_have_multiple_study_value_relationships_attached4(
    api_client,
):
    data = {
        "change_description": "Lock 1",
        "reason_for_change_uid": reason_for_lock_term_uid,
    }
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached4(
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


def test_patch_specific_set_name2(api_client):
    data = {"name": "New_BranchArm_Name_1"}
    response = api_client.patch(
        f"/studies/study_root/study-branch-arms/{branch_arm_uids[-1]}", json=data
    )

    res = response.json()

    assert response.status_code == 200
    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == branch_arm_uids[-1]
    assert res["order"] == 1
    assert res["name"] == "New_BranchArm_Name_1"
    assert res["short_name"] == "BranchArm_Short_Name_1"
    assert res["code"] == "BranchArm_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert_study_arm(res["arm_root"], test_data_dict["arm1"])
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_all_history_of_specific_selection2(api_client):
    response = api_client.get(
        f"/studies/study_root/study-branch-arms/{branch_arm_uids[-1]}/audit-trail/"
    )

    res = response.json()

    assert response.status_code == 200
    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 1
    assert res[0]["project_number"] is None
    assert res[0]["project_name"] is None
    # assert res[0]["study_version"]
    assert res[0]["branch_arm_uid"] == branch_arm_uids[-1]
    assert res[0]["name"] == "New_BranchArm_Name_1"
    assert res[0]["short_name"] == "BranchArm_Short_Name_1"
    assert res[0]["code"] == "BranchArm_code_1"
    assert res[0]["description"] == "desc..."
    assert res[0]["randomization_group"] == "Randomization_Group_1"
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert res[0]["arm_root_uid"] == "StudyArm_000001"
    assert set(res[0]["changes"]) == set(
        [
            "name",
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["order"] == 1
    assert res[1]["project_number"] is None
    assert res[1]["project_name"] is None
    # assert res[1]["study_version"]
    assert res[1]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res[1]["name"] == "BranchArm_Name_1"
    assert res[1]["short_name"] == "BranchArm_Short_Name_1"
    assert res[1]["code"] == "BranchArm_code_1"
    assert res[1]["description"] == "desc..."
    assert res[1]["randomization_group"] == "Randomization_Group_1"
    assert res[1]["number_of_subjects"] == 1
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"] is not None
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False
    assert res[1]["arm_root_uid"] == "StudyArm_000001"
    assert res[1]["changes"] == []


def test_2nd_adding_selection(api_client):
    data = {
        "name": "BranchArm_Name_2",
        "short_name": "BranchArm_Short_Name_2",
        "code": "BranchArm_code_2",
        "description": "desc...",
        "randomization_group": "Randomization_Group_2",
        "number_of_subjects": 1,
        "arm_uid": test_data_dict["arm1"].arm_uid,
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"].startswith("StudyBranchArm_")
    branch_arm_uids.append(res["branch_arm_uid"])
    assert res["order"] == 2
    assert res["name"] == "BranchArm_Name_2"
    assert res["short_name"] == "BranchArm_Short_Name_2"
    assert res["code"] == "BranchArm_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert_study_arm(res["arm_root"], test_data_dict["arm1"])
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_2"
    assert res["author_username"] == "unknown-user@example.com"


def test_lock_study_test_to_have_multiple_study_value_relationships_attached5(
    api_client,
):
    data = {
        "change_description": "Lock 1",
        "reason_for_change_uid": reason_for_lock_term_uid,
    }
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached5(
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


def test_delete_delete_the_1st_to_test_the_reordering_for_the_2nd_to_be_eq_to_1(
    api_client,
):
    response = api_client.delete(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000001"
    )

    assert_response_status_code(response, 204)


def test_3rd_adding_selection(api_client):
    data = {
        "name": "BranchArm_Name_3",
        "short_name": "BranchArm_Short_Name_3",
        "code": "BranchArm_code_3",
        "description": "desc...",
        "randomization_group": "Randomization_Group_3",
        "number_of_subjects": 3,
        "arm_uid": "StudyArm_000001",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"].startswith("StudyBranchArm_")
    branch_arm_uids.append(res["branch_arm_uid"])
    assert res["order"] == 2
    assert res["name"] == "BranchArm_Name_3"
    assert res["short_name"] == "BranchArm_Short_Name_3"
    assert res["code"] == "BranchArm_code_3"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert_study_arm(res["arm_root"], test_data_dict["arm1"])
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 3
    assert res["randomization_group"] == "Randomization_Group_3"
    assert res["author_username"] == "unknown-user@example.com"


def test_4rd_adding_selection_for_another_arm_to_check_the_ordering_will_follow_within_a_new_arm(
    api_client,
):
    data = {
        "name": "BranchArm_Name_4",
        "short_name": "BranchArm_Short_Name_4",
        "code": "BranchArm_code_4",
        "description": "desc...",
        "randomization_group": "Randomization_Group_4",
        "number_of_subjects": 4,
        "arm_uid": test_data_dict["arm3"].arm_uid,
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"].startswith("StudyBranchArm_")
    branch_arm_uids.append(res["branch_arm_uid"])
    assert res["order"] == 1
    assert res["name"] == "BranchArm_Name_4"
    assert res["short_name"] == "BranchArm_Short_Name_4"
    assert res["code"] == "BranchArm_code_4"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert_study_arm(res["arm_root"], test_data_dict["arm3"])
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 4
    assert res["randomization_group"] == "Randomization_Group_4"
    assert res["author_username"] == "unknown-user@example.com"


def test_5th_adding_selection_for_the_first_arm_to_check_the_ordering_will_follow_within_an_arm(
    api_client,
):
    data = {
        "name": "BranchArm_Name_5",
        "short_name": "BranchArm_Short_Name_5",
        "code": "BranchArm_code_5",
        "description": "desc...",
        "randomization_group": "Randomization_Group_5",
        "number_of_subjects": 5,
        "arm_uid": "StudyArm_000001",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"].startswith("StudyBranchArm_")
    branch_arm_uids.append(res["branch_arm_uid"])
    assert res["order"] == 3
    assert res["name"] == "BranchArm_Name_5"
    assert res["short_name"] == "BranchArm_Short_Name_5"
    assert res["code"] == "BranchArm_code_5"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert_study_arm(res["arm_root"], test_data_dict["arm1"])
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 5
    assert res["randomization_group"] == "Randomization_Group_5"
    assert res["author_username"] == "unknown-user@example.com"


def test_reorder_specific2(api_client):
    data = {"new_order": 2}
    response = api_client.patch(
        f"/studies/study_root/study-branch-arms/{branch_arm_uids[1]}/order", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == branch_arm_uids[1]
    assert res["order"] == 2
    assert res["name"] == "BranchArm_Name_2"
    assert res["short_name"] == "BranchArm_Short_Name_2"
    assert res["code"] == "BranchArm_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert_study_arm(res["arm_root"], test_data_dict["arm1"])
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_2"
    assert res["author_username"] == "unknown-user@example.com"


def test_get_all_within_an_arm_list_non_empty1(api_client):
    response = api_client.get(
        f"/studies/study_root/study-branch-arms/arm/{test_data_dict["arm1"].arm_uid}"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["study_version"]
    # assert res[0]["branch_arm_uid"] == "StudyBranchArm_000004"
    assert res[0]["order"] == 1
    assert res[0]["name"] == "BranchArm_Name_3"
    assert res[0]["short_name"] == "BranchArm_Short_Name_3"
    assert res[0]["code"] == "BranchArm_code_3"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] is None
    assert res[0]["accepted_version"] is False
    assert_study_arm(res[0]["arm_root"], test_data_dict["arm1"])
    assert res[0]["description"] == "desc..."
    assert res[0]["number_of_subjects"] == 3
    assert res[0]["randomization_group"] == "Randomization_Group_3"
    assert res[0]["author_username"] == "unknown-user@example.com"

    assert res[1]["study_uid"] == "study_root"
    assert res[1]["study_version"]
    # assert res[1]["branch_arm_uid"] == "StudyBranchArm_000012"
    assert res[1]["order"] == 2
    assert res[1]["name"] == "BranchArm_Name_2"
    assert res[1]["short_name"] == "BranchArm_Short_Name_2"
    assert res[1]["code"] == "BranchArm_code_2"
    assert res[1]["end_date"] is None
    assert res[1]["status"] is None
    assert res[1]["change_type"] is None
    assert res[1]["accepted_version"] is False
    assert_study_arm(res[1]["arm_root"], test_data_dict["arm1"])
    assert res[1]["description"] == "desc..."
    assert res[1]["number_of_subjects"] == 1
    assert res[1]["randomization_group"] == "Randomization_Group_2"
    assert res[1]["author_username"] == "unknown-user@example.com"

    assert res[2]["study_uid"] == "study_root"
    assert res[2]["study_version"]
    # assert res[2]["branch_arm_uid"] == "StudyBranchArm_000008"
    assert res[2]["order"] == 3
    assert res[2]["name"] == "BranchArm_Name_5"
    assert res[2]["short_name"] == "BranchArm_Short_Name_5"
    assert res[2]["code"] == "BranchArm_code_5"
    assert res[2]["end_date"] is None
    assert res[2]["status"] is None
    assert res[2]["change_type"] is None
    assert res[2]["accepted_version"] is False
    assert_study_arm(res[2]["arm_root"], test_data_dict["arm1"])
    assert res[2]["description"] == "desc..."
    assert res[2]["number_of_subjects"] == 5
    assert res[2]["randomization_group"] == "Randomization_Group_5"
    assert res[2]["author_username"] == "unknown-user@example.com"


def test_adding_selection_to_extract_designcells_from_arm(api_client):
    data = {
        "name": "BranchArm_Name_6",
        "short_name": "BranchArm_Short_Name_6",
        "code": "BranchArm_code_6",
        "description": "desc...",
        "randomization_group": "Randomization_Group_6",
        "number_of_subjects": 1,
        "arm_uid": test_data_dict["arm3"].arm_uid,
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"].startswith("StudyBranchArm_")
    branch_arm_uids.append(res["branch_arm_uid"])
    assert res["order"] == 2
    assert res["name"] == "BranchArm_Name_6"
    assert res["short_name"] == "BranchArm_Short_Name_6"
    assert res["code"] == "BranchArm_code_6"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert_study_arm(res["arm_root"], test_data_dict["arm3"])
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_6"
    assert res["author_username"] == "unknown-user@example.com"


def test_delete_delete_so_the_designcells_can_turn_back_to_the_study_arm(api_client):
    response = api_client.delete(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000006"
    )

    assert_response_status_code(response, 204)


def test_adding_selection_to_extract_designcells_from_arm_2(api_client):
    data = {
        "name": "BranchArm_Name_8",
        "short_name": "BranchArm_Short_Name_8",
        "code": "BranchArm_code_8",
        "description": "desc...",
        "randomization_group": "Randomization_Group_8",
        "number_of_subjects": 1,
        "arm_uid": test_data_dict["arm3"].arm_uid,
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"].startswith("StudyBranchArm_")
    branch_arm_uids.append(res["branch_arm_uid"])
    assert res["order"] == 2
    assert res["name"] == "BranchArm_Name_8"
    assert res["short_name"] == "BranchArm_Short_Name_8"
    assert res["code"] == "BranchArm_code_8"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert_study_arm(res["arm_root"], test_data_dict["arm3"])
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_8"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_selection_to_prove_that_the_cascade_delete_wont_activate_if_there_are_2_branches(
    api_client,
):
    data = {
        "name": "BranchArm_Name_7",
        "short_name": "BranchArm_Short_Name_7",
        "code": "BranchArm_code_7",
        "description": "desc...",
        "randomization_group": "Randomization_Group_7",
        "number_of_subjects": 1,
        "arm_uid": test_data_dict["arm3"].arm_uid,
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"].startswith("StudyBranchArm_")
    branch_arm_uids.append(res["branch_arm_uid"])
    assert res["order"] == 3
    assert res["name"] == "BranchArm_Name_7"
    assert res["short_name"] == "BranchArm_Short_Name_7"
    assert res["code"] == "BranchArm_code_7"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert_study_arm(res["arm_root"], test_data_dict["arm3"])
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_7"
    assert res["author_username"] == "unknown-user@example.com"


def test_delete_to_be_sure_that_the_cascade_delete_wont_take_effect(api_client):
    response = api_client.delete(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000007"
    )

    assert_response_status_code(response, 204)


def test_all_history_of_all_selection_study_branch_arms(api_client):
    response = api_client.get("/studies/study_root/study-branch-arm/audit-trail")

    assert_response_status_code(response, 200)

    expected_entries = [
        {
            "order": 1,
            "branch_arm_uid": "StudyBranchArm_000001",
            "name": "New_BranchArm_Name_1",
            "short_name": "BranchArm_Short_Name_1",
            "code": "BranchArm_code_1",
            "description": "desc...",
            "randomization_group": "Randomization_Group_1",
            "number_of_subjects": 1,
            "end_date": None,
            "change_type": "Delete",
            "arm_root_uid": "StudyArm_000001",
            "changes_unordered": ["start_date", "end_date", "change_type"],
        },
        {
            "order": 1,
            "branch_arm_uid": "StudyBranchArm_000001",
            "name": "New_BranchArm_Name_1",
            "short_name": "BranchArm_Short_Name_1",
            "code": "BranchArm_code_1",
            "description": "desc...",
            "randomization_group": "Randomization_Group_1",
            "number_of_subjects": 1,
            "end_date": _NOT_NONE,
            "change_type": "Edit",
            "arm_root_uid": "StudyArm_000001",
            "changes_unordered": ["name", "start_date", "end_date", "change_type"],
        },
        {
            "order": 1,
            "branch_arm_uid": "StudyBranchArm_000001",
            "name": "BranchArm_Name_1",
            "short_name": "BranchArm_Short_Name_1",
            "code": "BranchArm_code_1",
            "description": "desc...",
            "randomization_group": "Randomization_Group_1",
            "number_of_subjects": 1,
            "end_date": _NOT_NONE,
            "change_type": "Create",
            "arm_root_uid": "StudyArm_000001",
            "changes": [],
        },
        {
            "order": 2,
            "branch_arm_uid": "StudyBranchArm_000002",
            "name": "BranchArm_Name_2",
            "short_name": "BranchArm_Short_Name_2",
            "code": "BranchArm_code_2",
            "description": "desc...",
            "randomization_group": "Randomization_Group_2",
            "number_of_subjects": 1,
            "end_date": None,
            "change_type": "Edit",
            "arm_root_uid": "StudyArm_000001",
            "changes_unordered": ["order", "start_date", "end_date"],
        },
        {
            "order": 1,
            "branch_arm_uid": "StudyBranchArm_000002",
            "name": "BranchArm_Name_2",
            "short_name": "BranchArm_Short_Name_2",
            "code": "BranchArm_code_2",
            "description": "desc...",
            "randomization_group": "Randomization_Group_2",
            "number_of_subjects": 1,
            "end_date": _NOT_NONE,
            "change_type": "Edit",
            "arm_root_uid": "StudyArm_000001",
            "changes_unordered": ["order", "start_date", "end_date", "change_type"],
        },
        {
            "order": 2,
            "branch_arm_uid": "StudyBranchArm_000002",
            "name": "BranchArm_Name_2",
            "short_name": "BranchArm_Short_Name_2",
            "code": "BranchArm_code_2",
            "description": "desc...",
            "randomization_group": "Randomization_Group_2",
            "number_of_subjects": 1,
            "end_date": _NOT_NONE,
            "change_type": "Create",
            "arm_root_uid": "StudyArm_000001",
            "changes": [],
        },
        {
            "order": 1,
            "branch_arm_uid": "StudyBranchArm_000003",
            "name": "BranchArm_Name_3",
            "short_name": "BranchArm_Short_Name_3",
            "code": "BranchArm_code_3",
            "description": "desc...",
            "randomization_group": "Randomization_Group_3",
            "number_of_subjects": 3,
            "end_date": None,
            "change_type": "Edit",
            "arm_root_uid": "StudyArm_000001",
            "changes_unordered": ["order", "start_date", "end_date", "change_type"],
        },
        {
            "order": 2,
            "branch_arm_uid": "StudyBranchArm_000003",
            "name": "BranchArm_Name_3",
            "short_name": "BranchArm_Short_Name_3",
            "code": "BranchArm_code_3",
            "description": "desc...",
            "randomization_group": "Randomization_Group_3",
            "number_of_subjects": 3,
            "end_date": _NOT_NONE,
            "change_type": "Create",
            "arm_root_uid": "StudyArm_000001",
            "changes": [],
        },
        {
            "order": 1,
            "branch_arm_uid": "StudyBranchArm_000004",
            "name": "BranchArm_Name_4",
            "short_name": "BranchArm_Short_Name_4",
            "code": "BranchArm_code_4",
            "description": "desc...",
            "randomization_group": "Randomization_Group_4",
            "number_of_subjects": 4,
            "end_date": None,
            "change_type": "Create",
            "arm_root_uid": test_data_dict["arm3"].arm_uid,
            "changes": [],
        },
        {
            "order": 3,
            "branch_arm_uid": "StudyBranchArm_000005",
            "name": "BranchArm_Name_5",
            "short_name": "BranchArm_Short_Name_5",
            "code": "BranchArm_code_5",
            "description": "desc...",
            "randomization_group": "Randomization_Group_5",
            "number_of_subjects": 5,
            "end_date": None,
            "change_type": "Create",
            "arm_root_uid": "StudyArm_000001",
            "changes": [],
        },
        {
            "order": 2,
            "branch_arm_uid": "StudyBranchArm_000006",
            "name": "BranchArm_Name_6",
            "short_name": "BranchArm_Short_Name_6",
            "code": "BranchArm_code_6",
            "description": "desc...",
            "randomization_group": "Randomization_Group_6",
            "number_of_subjects": 1,
            "end_date": None,
            "change_type": "Delete",
            "arm_root_uid": test_data_dict["arm3"].arm_uid,
            "changes_unordered": ["start_date", "end_date", "change_type"],
        },
        {
            "order": 2,
            "branch_arm_uid": "StudyBranchArm_000006",
            "name": "BranchArm_Name_6",
            "short_name": "BranchArm_Short_Name_6",
            "code": "BranchArm_code_6",
            "description": "desc...",
            "randomization_group": "Randomization_Group_6",
            "number_of_subjects": 1,
            "end_date": _NOT_NONE,
            "change_type": "Create",
            "arm_root_uid": test_data_dict["arm3"].arm_uid,
            "changes": [],
        },
        {
            "order": 2,
            "branch_arm_uid": "StudyBranchArm_000007",
            "name": "BranchArm_Name_8",
            "short_name": "BranchArm_Short_Name_8",
            "code": "BranchArm_code_8",
            "description": "desc...",
            "randomization_group": "Randomization_Group_8",
            "number_of_subjects": 1,
            "end_date": None,
            "change_type": "Delete",
            "arm_root_uid": test_data_dict["arm3"].arm_uid,
            "changes_unordered": ["start_date", "end_date", "change_type"],
        },
        {
            "order": 2,
            "branch_arm_uid": "StudyBranchArm_000007",
            "name": "BranchArm_Name_8",
            "short_name": "BranchArm_Short_Name_8",
            "code": "BranchArm_code_8",
            "description": "desc...",
            "randomization_group": "Randomization_Group_8",
            "number_of_subjects": 1,
            "end_date": _NOT_NONE,
            "change_type": "Create",
            "arm_root_uid": test_data_dict["arm3"].arm_uid,
            "changes": [],
        },
        {
            "order": 2,
            "branch_arm_uid": "StudyBranchArm_000008",
            "name": "BranchArm_Name_7",
            "short_name": "BranchArm_Short_Name_7",
            "code": "BranchArm_code_7",
            "description": "desc...",
            "randomization_group": "Randomization_Group_7",
            "number_of_subjects": 1,
            "end_date": None,
            "change_type": "Edit",
            "arm_root_uid": test_data_dict["arm3"].arm_uid,
            "changes_unordered": ["order", "start_date", "end_date", "change_type"],
        },
        {
            "order": 3,
            "branch_arm_uid": "StudyBranchArm_000008",
            "name": "BranchArm_Name_7",
            "short_name": "BranchArm_Short_Name_7",
            "code": "BranchArm_code_7",
            "description": "desc...",
            "randomization_group": "Randomization_Group_7",
            "number_of_subjects": 1,
            "end_date": _NOT_NONE,
            "change_type": "Create",
            "arm_root_uid": test_data_dict["arm3"].arm_uid,
            "changes": [],
        },
    ]

    _assert_branch_arm_audit_entries(response.json(), expected_entries)
