# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_STUDY_ARM_CYPHER,
    STARTUP_STUDY_BRANCH_ARM_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.selection.branch.arms.negative")
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
    db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)

    yield

    drop_db("old.json.test.study.selection.branch.arms.negative")


def test_adding_selection_1st(api_client):
    data = {
        "name": "BranchArm_Name_1",
        "short_name": "BranchArm_Short_Name_1",
        "code": "BranchArm_code_1",
        "description": "desc...",
        "colour_code": "desc...",
        "randomization_group": "Randomization_Group_1",
        "number_of_subjects": 1,
        "arm_uid": "StudyArm_000001",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

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
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["name"] == "StudyArm_000001"
    assert res["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"] is None
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_selection_2nd(api_client):
    data = {
        "name": "BranchArm_Name_2",
        "short_name": "BranchArm_Short_Name_2",
        "code": "BranchArm_code_2",
        "description": "desc...",
        "colour_code": "desc...",
        "randomization_group": "Randomization_Group_2",
        "number_of_subjects": 2,
        "arm_uid": "StudyArm_000001",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000003"
    assert res["order"] == 2
    assert res["name"] == "BranchArm_Name_2"
    assert res["short_name"] == "BranchArm_Short_Name_2"
    assert res["code"] == "BranchArm_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["name"] == "StudyArm_000001"
    assert res["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"] is None
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 2
    assert res["randomization_group"] == "Randomization_Group_2"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_selection4(api_client):
    data = {
        "name": "BranchArm_Name_1",
        "short_name": "BranchArm_Short_Name_9",
        "code": "BranchArm_code_9",
        "description": "desc...",
        "colour_code": "desc...",
        "randomization_group": "Randomization_Group_9",
        "number_of_subjects": 1,
        "arm_uid": "StudyArm_000001",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 422)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Value 'BranchArm_Name_1' in field Branch Arm Name is not unique for the study."
    )


def test_patch_specific_everything_to_a_new_randomization_group_name(api_client):
    data = {
        "name": "BranchArm_Name_4",
        "short_name": "BranchArm_Short_Name_4",
        "code": "BranchArm_code_4",
        "description": "desc...",
        "colour_code": "desc...",
        "randomization_group": "Randomization_Group_4",
    }
    response = api_client.patch(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res["order"] == 1
    assert res["name"] == "BranchArm_Name_4"
    assert res["short_name"] == "BranchArm_Short_Name_4"
    assert res["code"] == "BranchArm_code_4"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["name"] == "StudyArm_000001"
    assert res["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"] is None
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_4"
    assert res["author_username"] == "unknown-user@example.com"


def test_all_history_of_specific_selection4(api_client):
    response = api_client.get(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000001/audit-trail/"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 1
    assert res[0]["project_number"] is None
    assert res[0]["project_name"] is None
    assert res[0]["study_version"] is None
    assert res[0]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res[0]["name"] == "BranchArm_Name_4"
    assert res[0]["short_name"] == "BranchArm_Short_Name_4"
    assert res[0]["code"] == "BranchArm_code_4"
    assert res[0]["description"] == "desc..."
    assert res[0]["colour_code"] == "desc..."
    assert res[0]["randomization_group"] == "Randomization_Group_4"
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert res[0]["arm_root_uid"] == "StudyArm_000001"
    assert res[0]["changes"] == {
        "name": True,
        "short_name": True,
        "code": True,
        "randomization_group": True,
        "start_date": True,
        "end_date": True,
        "change_type": True,
    }
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["order"] == 1
    assert res[1]["project_number"] is None
    assert res[1]["project_name"] is None
    assert res[1]["study_version"] is None
    assert res[1]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res[1]["name"] == "BranchArm_Name_1"
    assert res[1]["short_name"] == "BranchArm_Short_Name_1"
    assert res[1]["code"] == "BranchArm_code_1"
    assert res[1]["description"] == "desc..."
    assert res[1]["colour_code"] == "desc..."
    assert res[1]["randomization_group"] == "Randomization_Group_1"
    assert res[1]["number_of_subjects"] == 1
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"]
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False
    assert res[1]["arm_root_uid"] == "StudyArm_000001"
    assert res[1]["changes"] == {}


def test_patch_specific_patch_a_randomization_group_name_that_is_in_history_not_actual(
    api_client,
):
    data = {
        "name": "BranchArm_Name_5",
        "short_name": "BranchArm_Short_Name_5",
        "code": "BranchArm_code_5",
        "description": "desc...",
        "colour_code": "desc...",
        "randomization_group": "Randomization_Group_1",
    }
    response = api_client.patch(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 1
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res["name"] == "BranchArm_Name_5"
    assert res["short_name"] == "BranchArm_Short_Name_5"
    assert res["code"] == "BranchArm_code_5"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["number_of_subjects"] == 1
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["arm_root"]["name"] == "StudyArm_000001"
    assert res["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["arm_colour"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"] is None
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False


def test_patch_specific_patch_some_randomization_group_that_is_already_used_on_another_branch1(
    api_client,
):
    data = {
        "name": "BranchArm_Name_8",
        "short_name": "BranchArm_Short_Name_8",
        "code": "BranchArm_code_8",
        "description": "desc...",
        "colour_code": "desc...",
        "randomization_group": "Randomization_Group_2",
    }
    response = api_client.patch(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000001", json=data
    )

    assert_response_status_code(response, 422)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Value 'Randomization_Group_2' in field Branch Arm Randomization code is not unique for the study."
    )
