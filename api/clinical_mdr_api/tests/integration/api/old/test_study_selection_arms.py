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
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_STUDY_ARM_CYPHER,
    create_reason_for_lock_unlock_terms,
    fix_study_preferred_time_unit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_element,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

test_data_dict = {}
reason_for_lock_term_uid = None
reason_for_unlock_term_uid = None


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.selection.arms")
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
    StudyRoot.generate_node_uids_if_not_present()
    study = StudyRoot.nodes.all()[0]
    TestUtils.set_study_standard_version(
        study_uid="study_root", create_codelists_and_terms_for_package=False
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
    arm_type2 = create_ct_term(
        name="Arm Type 2",
        uid="ArmType_0002",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": arm_type_codelist.codelist_uid,
                "order": 2,
                "submission_value": "Arm Type 2",
            }
        ],
    )
    test_data_dict["arm_type2"] = arm_type2

    # locking and unlocking to create multiple study value relationships on the existent StudySelections
    fix_study_preferred_time_unit("study_root")

    yield

    drop_db("old.json.test.study.selection.arms")


def test_getting_empty_list4(api_client):
    response = api_client.get("/studies/study_root/study-arms")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_getting_empty_list_for_all_studies2(api_client):
    response = api_client.get("/study-arms")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_adding_selection7(api_client):
    data = {
        "name": "Arm_Name_1",
        "short_name": "Arm_Short_Name_1",
        "code": "Arm_code_1",
        "description": "desc...",
        "randomization_group": "Randomization_Group_1",
        "number_of_subjects": 1,
        "arm_type_uid": "ArmType_0001",
    }
    response = api_client.post("/studies/study_root/study-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["arm_uid"] == "StudyArm_000001"
    test_data_dict["first_arm_uid"] = res["arm_uid"]
    assert res["order"] == 1
    assert res["name"] == "Arm_Name_1"
    assert res["short_name"] == "Arm_Short_Name_1"
    assert res["code"] == "Arm_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"]["term_uid"] == "ArmType_0001"
    assert res["arm_type"]["term_name"] == "Arm Type"
    assert res["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res["arm_type"]["codelist_name"] == "Arm Type"
    assert res["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res["arm_type"]["order"] == 1
    assert res["arm_type"]["submission_value"] == "Arm Type"
    assert res["arm_type"]["queried_effective_date"] is not None
    assert res["arm_type"]["date_conflict"] is False
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_get_all_list_non_empty4(api_client):
    response = api_client.get("/studies/study_root/study-arms")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["study_version"]
    assert res["items"][0]["arm_uid"] == "StudyArm_000001"
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["name"] == "Arm_Name_1"
    assert res["items"][0]["short_name"] == "Arm_Short_Name_1"
    assert res["items"][0]["code"] == "Arm_code_1"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] is None
    assert res["items"][0]["change_type"] is None
    assert res["items"][0]["accepted_version"] is False
    assert res["items"][0]["arm_type"]["term_uid"] == "ArmType_0001"
    assert res["items"][0]["arm_type"]["term_name"] == "Arm Type"
    assert res["items"][0]["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res["items"][0]["arm_type"]["codelist_name"] == "Arm Type"
    assert res["items"][0]["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res["items"][0]["arm_type"]["order"] == 1
    assert res["items"][0]["arm_type"]["submission_value"] == "Arm Type"
    assert res["items"][0]["arm_type"]["queried_effective_date"] is not None
    assert res["items"][0]["arm_type"]["date_conflict"] is False
    assert res["items"][0]["arm_connected_branch_arms"] is None
    assert res["items"][0]["description"] == "desc..."
    assert res["items"][0]["number_of_subjects"] == 1
    assert res["items"][0]["randomization_group"] == "Randomization_Group_1"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"


def test_get_all_for_all_studies2(api_client):
    response = api_client.get("/study-arms")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["study_version"]
    assert res["items"][0]["arm_uid"] == "StudyArm_000001"
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["name"] == "Arm_Name_1"
    assert res["items"][0]["short_name"] == "Arm_Short_Name_1"
    assert res["items"][0]["code"] == "Arm_code_1"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] is None
    assert res["items"][0]["change_type"] is None
    assert res["items"][0]["accepted_version"] is False
    assert res["items"][0]["arm_type"]["term_uid"] == "ArmType_0001"
    assert res["items"][0]["arm_type"]["term_name"] == "Arm Type"
    assert res["items"][0]["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res["items"][0]["arm_type"]["codelist_name"] == "Arm Type"
    assert res["items"][0]["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res["items"][0]["arm_type"]["order"] == 1
    assert res["items"][0]["arm_type"]["submission_value"] == "Arm Type"
    assert res["items"][0]["arm_type"]["queried_effective_date"] is not None
    assert res["items"][0]["arm_type"]["date_conflict"] is False
    assert res["items"][0]["arm_connected_branch_arms"] is None
    assert res["items"][0]["description"] == "desc..."
    assert res["items"][0]["number_of_subjects"] == 1
    assert res["items"][0]["randomization_group"] == "Randomization_Group_1"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"


def test_add_study_title_test_to_have_multiple_study_value_relationships_attached3(
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


def test_lock_study_test_to_have_multiple_study_value_relationships_attached6(
    api_client,
):
    data = {
        "change_description": "Lock 1",
        "reason_for_change_uid": reason_for_lock_term_uid,
    }
    response = api_client.post("/studies/study_root/locks", json=data)

    assert response.status_code == 201


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached6(
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


def test_patch_specific_set_name4(api_client):
    data = {"name": "New_Arm_Name_1", "arm_type_uid": "ArmType_0002"}
    response = api_client.patch(
        f"/studies/study_root/study-arms/{test_data_dict['first_arm_uid']}", json=data
    )

    assert_response_status_code(response, 200)
    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["arm_uid"] == test_data_dict["first_arm_uid"]
    assert res["order"] == 1
    assert res["name"] == "New_Arm_Name_1"
    assert res["short_name"] == "Arm_Short_Name_1"
    assert res["code"] == "Arm_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"]["term_uid"] == "ArmType_0002"
    assert res["arm_type"]["term_name"] == "Arm Type 2"
    assert res["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res["arm_type"]["codelist_name"] == "Arm Type"
    assert res["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res["arm_type"]["order"] == 2
    assert res["arm_type"]["submission_value"] == "Arm Type 2"
    assert res["arm_type"]["queried_effective_date"] is not None
    assert res["arm_type"]["date_conflict"] is False
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_all_history_of_specific_selection5(api_client):
    response = api_client.get(
        f"/studies/study_root/study-arms/{test_data_dict['first_arm_uid']}/audit-trail/"
    )

    res = response.json()

    assert response.status_code == 200
    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 1
    assert res[0]["project_number"] is None
    assert res[0]["project_name"] is None
    assert res[0]["study_version"] is None
    assert res[0]["arm_uid"] == test_data_dict["first_arm_uid"]
    assert res[0]["name"] == "New_Arm_Name_1"
    assert res[0]["short_name"] == "Arm_Short_Name_1"
    assert res[0]["code"] == "Arm_code_1"
    assert res[0]["description"] == "desc..."
    assert res[0]["randomization_group"] == "Randomization_Group_1"
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["arm_type"]["term_uid"] == "ArmType_0002"
    assert res[0]["arm_type"]["term_name"] == "Arm Type 2"
    assert res[0]["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res[0]["arm_type"]["codelist_name"] == "Arm Type"
    assert res[0]["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res[0]["arm_type"]["order"] == 2
    assert res[0]["arm_type"]["submission_value"] == "Arm Type 2"
    assert res[0]["arm_type"]["queried_effective_date"] is not None
    assert res[0]["arm_type"]["date_conflict"] is False
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert set(res[0]["changes"]) == set(
        [
            "name",
            "arm_type",
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["order"] == 1
    assert res[1]["project_number"] is None
    assert res[1]["project_name"] is None
    assert res[1]["study_version"] is None
    assert res[1]["arm_uid"] == test_data_dict["first_arm_uid"]
    assert res[1]["name"] == "Arm_Name_1"
    assert res[1]["short_name"] == "Arm_Short_Name_1"
    assert res[1]["code"] == "Arm_code_1"
    assert res[1]["description"] == "desc..."
    assert res[1]["randomization_group"] == "Randomization_Group_1"
    assert res[1]["number_of_subjects"] == 1
    assert res[1]["arm_type"]["term_uid"] == "ArmType_0001"
    assert res[1]["arm_type"]["term_name"] == "Arm Type"
    assert res[1]["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res[1]["arm_type"]["codelist_name"] == "Arm Type"
    assert res[1]["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res[1]["arm_type"]["order"] == 1
    assert res[1]["arm_type"]["submission_value"] == "Arm Type"
    assert res[1]["arm_type"]["queried_effective_date"] is not None
    assert res[1]["arm_type"]["date_conflict"] is False
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"] is not None
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False
    assert res[1]["changes"] == []


def test_adding_selection_22(api_client):
    data = {
        "name": "Arm_Name_2",
        "short_name": "Arm_Short_Name_2",
        "code": "Arm_code_2",
        "description": "desc...",
        "randomization_group": "Randomization_Group_2",
        "number_of_subjects": 1,
        "arm_type_uid": "ArmType_0001",
    }
    response = api_client.post("/studies/study_root/study-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["arm_uid"].startswith("StudyArm_")
    test_data_dict["second_arm_uid"] = res["arm_uid"]
    assert res["order"] == 2
    assert res["name"] == "Arm_Name_2"
    assert res["short_name"] == "Arm_Short_Name_2"
    assert res["code"] == "Arm_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"]["term_uid"] == "ArmType_0001"
    assert res["arm_type"]["term_name"] == "Arm Type"
    assert res["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res["arm_type"]["codelist_name"] == "Arm Type"
    assert res["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res["arm_type"]["order"] == 1
    assert res["arm_type"]["submission_value"] == "Arm Type"
    assert res["arm_type"]["queried_effective_date"] is not None
    assert res["arm_type"]["date_conflict"] is False
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_2"
    assert res["author_username"] == "unknown-user@example.com"


def test_get_specific6(api_client):
    response = api_client.get(
        f"/studies/study_root/study-arms/{test_data_dict['second_arm_uid']}"
    )

    assert_response_status_code(response, 200)
    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["arm_uid"] == test_data_dict["second_arm_uid"]
    assert res["order"] == 2
    assert res["name"] == "Arm_Name_2"
    assert res["short_name"] == "Arm_Short_Name_2"
    assert res["code"] == "Arm_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"]["term_uid"] == "ArmType_0001"
    assert res["arm_type"]["term_name"] == "Arm Type"
    assert res["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res["arm_type"]["codelist_name"] == "Arm Type"
    assert res["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res["arm_type"]["order"] == 1
    assert res["arm_type"]["submission_value"] == "Arm Type"
    assert res["arm_type"]["queried_effective_date"] is not None
    assert res["arm_type"]["date_conflict"] is False
    assert res["arm_connected_branch_arms"] is None
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_2"
    assert res["author_username"] == "unknown-user@example.com"


def test_reorder_specific5(api_client):
    data = {"new_order": 1}
    response = api_client.patch(
        f"/studies/study_root/study-arms/{test_data_dict['second_arm_uid']}/order",
        json=data,
    )

    assert_response_status_code(response, 200)
    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["arm_uid"] == test_data_dict["second_arm_uid"]
    assert res["order"] == 1
    assert res["name"] == "Arm_Name_2"
    assert res["short_name"] == "Arm_Short_Name_2"
    assert res["code"] == "Arm_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"]["term_uid"] == "ArmType_0001"
    assert res["arm_type"]["term_name"] == "Arm Type"
    assert res["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res["arm_type"]["codelist_name"] == "Arm Type"
    assert res["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res["arm_type"]["order"] == 1
    assert res["arm_type"]["submission_value"] == "Arm Type"
    assert res["arm_type"]["queried_effective_date"] is not None
    assert res["arm_type"]["date_conflict"] is False
    assert res["arm_connected_branch_arms"] is None
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_2"
    assert res["author_username"] == "unknown-user@example.com"


def test_lock_study_test_to_have_multiple_study_value_relationships_attached7(
    api_client,
):
    data = {
        "change_description": "Lock 1",
        "reason_for_change_uid": reason_for_lock_term_uid,
    }
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached7(
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


def test_adding_selection_to_check_if_the_type_can_be_optional(api_client):
    data = {
        "name": "Arm_Name_3",
        "short_name": "Arm_Short_Name_3",
        "code": "Arm_code_3",
        "description": "desc...",
        "randomization_group": "Randomization_Group_3",
        "number_of_subjects": 1,
    }
    response = api_client.post("/studies/study_root/study-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["arm_uid"].startswith("StudyArm_")

    test_data_dict["new_arm_uid"] = res["arm_uid"]
    assert res["order"] == 3
    assert res["name"] == "Arm_Name_3"
    assert res["short_name"] == "Arm_Short_Name_3"
    assert res["code"] == "Arm_code_3"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"] is None
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_3"
    assert res["author_username"] == "unknown-user@example.com"


def test_patch_specific_set_arm_type_uid_to_check_after_not_being_specified(api_client):
    data = {"name": "New_Arm_Name_3", "arm_type_uid": "ArmType_0002"}
    response = api_client.patch(
        f"/studies/study_root/study-arms/{test_data_dict['new_arm_uid']}", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["arm_uid"] == test_data_dict["new_arm_uid"]
    assert res["order"] == 3
    assert res["name"] == "New_Arm_Name_3"
    assert res["short_name"] == "Arm_Short_Name_3"
    assert res["code"] == "Arm_code_3"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"]["term_uid"] == "ArmType_0002"
    assert res["arm_type"]["term_name"] == "Arm Type 2"
    assert res["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res["arm_type"]["codelist_name"] == "Arm Type"
    assert res["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res["arm_type"]["order"] == 2
    assert res["arm_type"]["submission_value"] == "Arm Type 2"
    assert res["arm_type"]["queried_effective_date"] is not None
    assert res["arm_type"]["date_conflict"] is False
    assert res["arm_connected_branch_arms"] is None
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_3"
    assert res["author_username"] == "unknown-user@example.com"


def test_all_history_of_specific_selection_to_test_if_the_armtype_optional_is_being_manage_even_if_the_history_schema_is_applied(
    api_client,
):
    response = api_client.get(
        f"/studies/study_root/study-arms/{test_data_dict['new_arm_uid']}/audit-trail/"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 3
    assert res[0]["project_number"] is None
    assert res[0]["project_name"] is None
    # assert res[0]["study_version"]
    assert res[0]["arm_uid"] == test_data_dict["new_arm_uid"]
    assert res[0]["name"] == "New_Arm_Name_3"
    assert res[0]["short_name"] == "Arm_Short_Name_3"
    assert res[0]["code"] == "Arm_code_3"
    assert res[0]["description"] == "desc..."
    assert res[0]["randomization_group"] == "Randomization_Group_3"
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["arm_type"]["term_uid"] == "ArmType_0002"
    assert res[0]["arm_type"]["term_name"] == "Arm Type 2"
    assert res[0]["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res[0]["arm_type"]["codelist_name"] == "Arm Type"
    assert res[0]["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res[0]["arm_type"]["order"] == 2
    assert res[0]["arm_type"]["submission_value"] == "Arm Type 2"
    assert res[0]["arm_type"]["queried_effective_date"] is not None
    assert res[0]["arm_type"]["date_conflict"] is False
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert set(res[0]["changes"]) == set(
        [
            "name",
            "arm_type",
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["order"] == 3
    assert res[1]["project_number"] is None
    assert res[1]["project_name"] is None
    assert res[1]["study_version"] is None
    assert res[1]["arm_uid"] == test_data_dict["new_arm_uid"]
    assert res[1]["name"] == "Arm_Name_3"
    assert res[1]["short_name"] == "Arm_Short_Name_3"
    assert res[1]["code"] == "Arm_code_3"
    assert res[1]["description"] == "desc..."
    assert res[1]["randomization_group"] == "Randomization_Group_3"
    assert res[1]["number_of_subjects"] == 1
    assert res[1]["arm_type"] is None
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"]
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False
    assert res[1]["changes"] == []


def test_patch_specific_set_arm_type_uid_to_null(api_client):
    data = {"arm_type_uid": ""}
    response = api_client.patch(
        f"/studies/study_root/study-arms/{test_data_dict['new_arm_uid']}", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["arm_uid"] == test_data_dict["new_arm_uid"]
    assert res["order"] == 3
    assert res["name"] == "New_Arm_Name_3"
    assert res["short_name"] == "Arm_Short_Name_3"
    assert res["code"] == "Arm_code_3"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"] is None
    assert res["arm_connected_branch_arms"] is None
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_3"
    assert res["author_username"] == "unknown-user@example.com"


def test_all_history_of_all_selection_study_arms(
    api_client,
):  # pylint:disable=too-many-statements
    response = api_client.get("/studies/study_root/study-arms/audit-trail/")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 2
    assert res[0]["project_number"] is None
    assert res[0]["project_name"] is None
    assert res[0]["study_version"] is None
    assert res[0]["arm_uid"] == "StudyArm_000001"
    assert res[0]["name"] == "New_Arm_Name_1"
    assert res[0]["short_name"] == "Arm_Short_Name_1"
    assert res[0]["code"] == "Arm_code_1"
    assert res[0]["description"] == "desc..."
    assert res[0]["randomization_group"] == "Randomization_Group_1"
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["arm_type"]["term_uid"] == "ArmType_0002"
    assert res[0]["arm_type"]["term_name"] == "Arm Type 2"
    assert res[0]["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res[0]["arm_type"]["codelist_name"] == "Arm Type"
    assert res[0]["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res[0]["arm_type"]["order"] == 2
    assert res[0]["arm_type"]["submission_value"] == "Arm Type 2"
    assert res[0]["arm_type"]["queried_effective_date"] is not None
    assert res[0]["arm_type"]["date_conflict"] is False
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert set(res[0]["changes"]) == set(
        [
            "order",
            "start_date",
            "end_date",
        ]
    )
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["order"] == 1
    assert res[1]["project_number"] is None
    assert res[1]["project_name"] is None
    assert res[1]["study_version"] is None
    assert res[1]["arm_uid"] == "StudyArm_000001"
    assert res[1]["name"] == "New_Arm_Name_1"
    assert res[1]["short_name"] == "Arm_Short_Name_1"
    assert res[1]["code"] == "Arm_code_1"
    assert res[1]["description"] == "desc..."
    assert res[1]["randomization_group"] == "Randomization_Group_1"
    assert res[1]["number_of_subjects"] == 1
    assert res[1]["arm_type"]["term_uid"] == "ArmType_0002"
    assert res[1]["arm_type"]["term_name"] == "Arm Type 2"
    assert res[1]["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res[1]["arm_type"]["codelist_name"] == "Arm Type"
    assert res[1]["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res[1]["arm_type"]["order"] == 2
    assert res[1]["arm_type"]["submission_value"] == "Arm Type 2"
    assert res[1]["arm_type"]["queried_effective_date"] is not None
    assert res[1]["arm_type"]["date_conflict"] is False
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"] is not None
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Edit"
    assert res[1]["accepted_version"] is False
    assert set(res[1]["changes"]) == set(
        [
            "name",
            "arm_type",
            "start_date",
            "end_date",
            "change_type",
        ]
    )

    assert res[2]["study_uid"] == "study_root"
    assert res[2]["order"] == 1
    assert res[2]["project_number"] is None
    assert res[2]["project_name"] is None
    assert res[2]["study_version"] is None
    assert res[2]["arm_uid"] == "StudyArm_000001"
    assert res[2]["name"] == "Arm_Name_1"
    assert res[2]["short_name"] == "Arm_Short_Name_1"
    assert res[2]["code"] == "Arm_code_1"
    assert res[2]["description"] == "desc..."
    assert res[2]["randomization_group"] == "Randomization_Group_1"
    assert res[2]["number_of_subjects"] == 1
    assert res[2]["arm_type"]["term_uid"] == "ArmType_0001"
    assert res[2]["arm_type"]["term_name"] == "Arm Type"
    assert res[2]["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res[2]["arm_type"]["codelist_name"] == "Arm Type"
    assert res[2]["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res[2]["arm_type"]["order"] == 1
    assert res[2]["arm_type"]["submission_value"] == "Arm Type"
    assert res[2]["arm_type"]["queried_effective_date"] is not None
    assert res[2]["arm_type"]["date_conflict"] is False
    assert res[2]["author_username"] == "unknown-user@example.com"
    assert res[2]["end_date"] is not None
    assert res[2]["status"] is None
    assert res[2]["change_type"] == "Create"
    assert res[2]["accepted_version"] is False
    assert res[2]["changes"] == []

    assert res[3]["study_uid"] == "study_root"
    assert res[3]["order"] == 1
    assert res[3]["project_number"] is None
    assert res[3]["project_name"] is None
    assert res[3]["study_version"] is None
    assert res[3]["arm_uid"] == "StudyArm_000002"
    assert res[3]["name"] == "Arm_Name_2"
    assert res[3]["short_name"] == "Arm_Short_Name_2"
    assert res[3]["code"] == "Arm_code_2"
    assert res[3]["description"] == "desc..."
    assert res[3]["randomization_group"] == "Randomization_Group_2"
    assert res[3]["number_of_subjects"] == 1
    assert res[3]["arm_type"]["term_uid"] == "ArmType_0001"
    assert res[3]["arm_type"]["term_name"] == "Arm Type"
    assert res[3]["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res[3]["arm_type"]["codelist_name"] == "Arm Type"
    assert res[3]["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res[3]["arm_type"]["order"] == 1
    assert res[3]["arm_type"]["submission_value"] == "Arm Type"
    assert res[3]["arm_type"]["queried_effective_date"] is not None
    assert res[3]["arm_type"]["date_conflict"] is False
    assert res[3]["author_username"] == "unknown-user@example.com"
    assert res[3]["end_date"] is None
    assert res[3]["status"] is None
    assert res[3]["change_type"] == "Edit"
    assert res[3]["accepted_version"] is False
    assert set(res[3]["changes"]) == set(
        [
            "order",
            "start_date",
            "end_date",
            "change_type",
        ]
    )

    assert res[4]["study_uid"] == "study_root"
    assert res[4]["order"] == 2
    assert res[4]["project_number"] is None
    assert res[4]["project_name"] is None
    assert res[4]["study_version"] is None
    assert res[4]["arm_uid"] == "StudyArm_000002"
    assert res[4]["name"] == "Arm_Name_2"
    assert res[4]["short_name"] == "Arm_Short_Name_2"
    assert res[4]["code"] == "Arm_code_2"
    assert res[4]["description"] == "desc..."
    assert res[4]["randomization_group"] == "Randomization_Group_2"
    assert res[4]["number_of_subjects"] == 1
    assert res[4]["arm_type"]["term_uid"] == "ArmType_0001"
    assert res[4]["arm_type"]["term_name"] == "Arm Type"
    assert res[4]["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res[4]["arm_type"]["codelist_name"] == "Arm Type"
    assert res[4]["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res[4]["arm_type"]["order"] == 1
    assert res[4]["arm_type"]["submission_value"] == "Arm Type"
    assert res[4]["arm_type"]["queried_effective_date"] is not None
    assert res[4]["arm_type"]["date_conflict"] is False
    assert res[4]["author_username"] == "unknown-user@example.com"
    assert res[4]["end_date"] is not None
    assert res[4]["status"] is None
    assert res[4]["change_type"] == "Create"
    assert res[4]["accepted_version"] is False
    assert res[4]["changes"] == []

    assert res[5]["study_uid"] == "study_root"
    assert res[5]["order"] == 3
    assert res[5]["project_number"] is None
    assert res[5]["project_name"] is None
    assert res[5]["study_version"] is None
    assert res[5]["arm_uid"] == test_data_dict["new_arm_uid"]
    assert res[5]["name"] == "New_Arm_Name_3"
    assert res[5]["short_name"] == "Arm_Short_Name_3"
    assert res[5]["code"] == "Arm_code_3"
    assert res[5]["description"] == "desc..."
    assert res[5]["randomization_group"] == "Randomization_Group_3"
    assert res[5]["number_of_subjects"] == 1
    assert res[5]["arm_type"] is None
    assert res[5]["author_username"] == "unknown-user@example.com"
    assert res[5]["end_date"] is None
    assert res[5]["status"] is None
    assert res[5]["change_type"] == "Edit"
    assert res[5]["accepted_version"] is False
    assert set(res[5]["changes"]) == set(
        [
            "arm_type",
            "start_date",
            "end_date",
        ]
    )

    assert res[6]["study_uid"] == "study_root"
    assert res[6]["order"] == 3
    assert res[6]["project_number"] is None
    assert res[6]["project_name"] is None
    assert res[6]["study_version"] is None
    assert res[6]["arm_uid"] == test_data_dict["new_arm_uid"]
    assert res[6]["name"] == "New_Arm_Name_3"
    assert res[6]["short_name"] == "Arm_Short_Name_3"
    assert res[6]["code"] == "Arm_code_3"
    assert res[6]["description"] == "desc..."
    assert res[6]["randomization_group"] == "Randomization_Group_3"
    assert res[6]["number_of_subjects"] == 1
    assert res[6]["arm_type"]["term_uid"] == "ArmType_0002"
    assert res[6]["arm_type"]["term_name"] == "Arm Type 2"
    assert res[6]["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res[6]["arm_type"]["codelist_name"] == "Arm Type"
    assert res[6]["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res[6]["arm_type"]["order"] == 2
    assert res[6]["arm_type"]["submission_value"] == "Arm Type 2"
    assert res[6]["arm_type"]["queried_effective_date"] is not None
    assert res[6]["arm_type"]["date_conflict"] is False
    assert res[6]["author_username"] == "unknown-user@example.com"
    assert res[6]["end_date"] is not None
    assert res[6]["status"] is None
    assert res[6]["change_type"] == "Edit"
    assert res[6]["accepted_version"] is False
    assert set(res[6]["changes"]) == set(
        [
            "name",
            "arm_type",
            "start_date",
            "end_date",
            "change_type",
        ]
    )

    assert res[7]["study_uid"] == "study_root"
    assert res[7]["order"] == 3
    assert res[7]["project_number"] is None
    assert res[7]["project_name"] is None
    assert res[7]["study_version"] is None
    assert res[7]["arm_uid"] == test_data_dict["new_arm_uid"]
    assert res[7]["name"] == "Arm_Name_3"
    assert res[7]["short_name"] == "Arm_Short_Name_3"
    assert res[7]["code"] == "Arm_code_3"
    assert res[7]["description"] == "desc..."
    assert res[7]["randomization_group"] == "Randomization_Group_3"
    assert res[7]["number_of_subjects"] == 1
    assert res[7]["arm_type"] is None
    assert res[7]["author_username"] == "unknown-user@example.com"
    assert res[7]["end_date"]
    assert res[7]["status"] is None
    assert res[7]["change_type"] == "Create"
    assert res[7]["accepted_version"] is False
    assert res[7]["changes"] == []


def test_delete(api_client):
    response = api_client.delete(
        f"/studies/study_root/study-arms/{test_data_dict['new_arm_uid']}"
    )

    assert_response_status_code(response, 204)
