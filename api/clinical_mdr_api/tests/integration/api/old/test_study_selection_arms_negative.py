# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

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


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.selection.arms.negative")
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
    StudyRoot.generate_node_uids_if_not_present()
    study = StudyRoot.nodes.all()[0]
    TestUtils.set_study_standard_version(
        study_uid="study_root", create_codelists_and_terms_for_package=False
    )
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

    yield

    drop_db("old.json.test.study.selection.arms.negative")


def test_adding_selection9(api_client):
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


def test_adding_2nd_selection(api_client):
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
    assert res["arm_uid"] == "StudyArm_000002"
    assert res["order"] == 2
    assert res["name"] == "Arm_Name_2"
    assert res["code"] == "Arm_code_2"
    assert res["short_name"] == "Arm_Short_Name_2"
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


def test_adding_selection_with_non_unique_name_short_name_randomization(api_client):
    data = {"name": "Arm_Name_1"}
    response = api_client.post("/studies/study_root/study-arms", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Value 'Arm_Name_1' in field Arm name is not unique for the study."
    )


def test_patch_specific_set_name6(api_client):
    data = {
        "name": "New_Arm_Name_1",
        "short_name": "Arm_Short_Name_1",
        "arm_type_uid": "ArmType_0002",
    }
    response = api_client.patch(
        "/studies/study_root/study-arms/StudyArm_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["arm_uid"] == "StudyArm_000001"
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
    assert res["arm_connected_branch_arms"] is None
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_all_history_of_specific_selection7(api_client):
    response = api_client.get(
        "/studies/study_root/study-arms/StudyArm_000001/audit-trail/"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 1
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
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["order"] == 1
    assert res[1]["arm_uid"] == "StudyArm_000001"
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


def test_patch_specific_patch_a_randomization_group_name_that_is_in_history_not_latest(
    api_client,
):
    data = {"name": "Arm_Name_1"}
    response = api_client.patch(
        "/studies/study_root/study-arms/StudyArm_000002", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 2
    assert res["arm_uid"] == "StudyArm_000002"
    assert res["name"] == "Arm_Name_1"
    assert res["short_name"] == "Arm_Short_Name_2"
    assert res["code"] == "Arm_code_2"
    assert res["description"] == "desc..."
    assert res["randomization_group"] == "Randomization_Group_2"
    assert res["number_of_subjects"] == 1
    assert res["arm_type"]["term_uid"] == "ArmType_0001"
    assert res["arm_type"]["term_name"] == "Arm Type"
    assert res["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res["arm_type"]["codelist_name"] == "Arm Type"
    assert res["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res["arm_type"]["order"] == 1
    assert res["arm_type"]["submission_value"] == "Arm Type"
    assert res["arm_type"]["queried_effective_date"] is not None
    assert res["arm_type"]["date_conflict"] is False
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_connected_branch_arms"] is None


def test_patch_specific_patch_some_randomization_group_that_is_already_used_on_another_branch1(
    api_client,
):
    data = {"randomization_group": "Randomization_Group_2"}
    response = api_client.patch(
        "/studies/study_root/study-arms/StudyArm_000001", json=data
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Value 'Randomization_Group_2' in field Arm Randomization code is not unique for the study."
    )
