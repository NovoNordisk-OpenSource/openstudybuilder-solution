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
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_study_branch_arm,
    create_study_cohort,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.selection.cohorts.negative")
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
    db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)

    study_uid = "study_root"
    arm_uid1 = "StudyArm_000001"

    create_study_cohort(
        study_uid=study_uid,
        name="Cohort_Name_1",
        short_name="Cohort_Short_Name_1",
        code="Cohort_code_1",
        description="desc...",
        colour_code="desc...",
        number_of_subjects=100,
        arm_uids=[arm_uid1],
    )
    create_study_cohort(
        study_uid=study_uid,
        name="Cohort_Name_2",
        short_name="Cohort_Short_Name_2",
        code="Cohort_code_2",
        description="desc...",
        colour_code="desc...",
        number_of_subjects=100,
        arm_uids=[arm_uid1],
    )
    create_study_branch_arm(
        study_uid=study_uid,
        name="Branch_Arm_Name_1",
        short_name="Branch_Arm_Short_Name_1",
        code="Branch_Arm_code_1",
        description="desc...",
        colour_code="colour...",
        randomization_group="Branch_Arm_randomizationGroup",
        number_of_subjects=100,
        arm_uid=arm_uid1,
    )

    yield

    drop_db("old.json.test.study.selection.cohorts.negative")


def test_adding_selection8(api_client):
    data = {"name": "Cohort_Name_1"}
    response = api_client.post("/studies/study_root/study-cohorts", json=data)

    assert_response_status_code(response, 422)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Value 'Cohort_Name_1' in field Cohort Name is not unique for the study."
    )


def test_patch_specific_everything_to_a_new_name(api_client):
    data = {
        "name": "Cohort_Name_77",
        "short_name": "Cohort_Short_Name_4",
        "code": "Cohort_code_4",
        "description": "desc...",
        "colour_code": "desc...",
    }
    response = api_client.patch(
        "/studies/study_root/study-cohorts/StudyCohort_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["cohort_uid"] == "StudyCohort_000001"
    assert res["order"] == 1
    assert res["name"] == "Cohort_Name_77"
    assert res["short_name"] == "Cohort_Short_Name_4"
    assert res["code"] == "Cohort_code_4"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["branch_arm_roots"] is None
    assert res["arm_roots"][0]["study_uid"] == "study_root"
    assert res["arm_roots"][0]["order"] == 1
    assert res["arm_roots"][0]["arm_uid"] == "StudyArm_000001"
    assert res["arm_roots"][0]["name"] == "StudyArm_000001"
    assert res["arm_roots"][0]["short_name"] == "StudyArm_000001"
    assert res["arm_roots"][0]["code"] is None
    assert res["arm_roots"][0]["description"] is None
    assert res["arm_roots"][0]["arm_colour"] is None
    assert res["arm_roots"][0]["randomization_group"] is None
    assert res["arm_roots"][0]["number_of_subjects"] is None
    assert res["arm_roots"][0]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_roots"][0]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_roots"][0]["arm_type"]["codelists"]) == 1
    assert (
        res["arm_roots"][0]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    )
    assert res["arm_roots"][0]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_roots"][0]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert (
        res["arm_roots"][0]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    )
    assert (
        res["arm_roots"][0]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_roots"][0]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_roots"][0]["arm_type"]["start_date"]
    assert res["arm_roots"][0]["arm_type"]["end_date"] is None
    assert res["arm_roots"][0]["arm_type"]["status"] == "Final"
    assert res["arm_roots"][0]["arm_type"]["version"] == "1.0"
    assert res["arm_roots"][0]["arm_type"]["change_description"] == "Approved version"
    assert (
        res["arm_roots"][0]["arm_type"]["author_username"] == "unknown-user@example.com"
    )
    assert res["arm_roots"][0]["arm_type"]["queried_effective_date"] is None
    assert res["arm_roots"][0]["arm_type"]["date_conflict"] is False
    assert res["arm_roots"][0]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_roots"][0]["start_date"]
    assert res["arm_roots"][0]["author_username"] == "unknown-user@example.com"
    assert res["arm_roots"][0]["end_date"] is None
    assert res["arm_roots"][0]["status"] is None
    assert res["arm_roots"][0]["change_type"] is None
    assert res["arm_roots"][0]["accepted_version"] is None
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 100
    assert res["author_username"] == "unknown-user@example.com"


def test_all_history_of_specific_selection6(api_client):
    response = api_client.get(
        "/studies/study_root/study-cohorts/StudyCohort_000001/audit-trail/"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 1
    assert res[0]["project_number"] is None
    assert res[0]["project_name"] is None
    assert res[0]["study_version"] is None
    assert res[0]["cohort_uid"] == "StudyCohort_000001"
    assert res[0]["name"] == "Cohort_Name_77"
    assert res[0]["short_name"] == "Cohort_Short_Name_4"
    assert res[0]["code"] == "Cohort_code_4"
    assert res[0]["description"] == "desc..."
    assert res[0]["colour_code"] == "desc..."
    assert res[0]["number_of_subjects"] == 100
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert res[0]["branch_arm_roots_uids"] is None
    assert res[0]["arm_roots_uids"] == ["StudyArm_000001"]
    assert res[0]["changes"] == {
        "name": True,
        "short_name": True,
        "code": True,
        "start_date": True,
        "end_date": True,
        "change_type": True,
    }
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["order"] == 1
    assert res[1]["project_number"] is None
    assert res[1]["project_name"] is None
    assert res[1]["study_version"] is None
    assert res[1]["cohort_uid"] == "StudyCohort_000001"
    assert res[1]["name"] == "Cohort_Name_1"
    assert res[1]["short_name"] == "Cohort_Short_Name_1"
    assert res[1]["code"] == "Cohort_code_1"
    assert res[1]["description"] == "desc..."
    assert res[1]["colour_code"] == "desc..."
    assert res[1]["number_of_subjects"] == 100
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"]
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False
    assert res[1]["branch_arm_roots_uids"] is None
    assert res[1]["arm_roots_uids"] == ["StudyArm_000001"]
    assert res[1]["changes"] == {}


def test_patch_specific_patch_a_name_that_is_in_history_not_actual(api_client):
    data = {
        "name": "Cohort_Name_1",
        "short_name": "Cohort_Short_Name_5",
        "code": "Cohort_code_5",
        "description": "desc...",
        "colour_code": "desc...",
    }
    response = api_client.patch(
        "/studies/study_root/study-cohorts/StudyCohort_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 1
    assert res["study_version"]
    assert res["cohort_uid"] == "StudyCohort_000001"
    assert res["name"] == "Cohort_Name_1"
    assert res["short_name"] == "Cohort_Short_Name_5"
    assert res["code"] == "Cohort_code_5"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "desc..."
    assert res["number_of_subjects"] == 100
    assert res["branch_arm_roots"] is None
    assert res["arm_roots"][0]["study_uid"] == "study_root"
    assert res["arm_roots"][0]["order"] == 1
    assert res["arm_roots"][0]["arm_uid"] == "StudyArm_000001"
    assert res["arm_roots"][0]["name"] == "StudyArm_000001"
    assert res["arm_roots"][0]["short_name"] == "StudyArm_000001"
    assert res["arm_roots"][0]["code"] is None
    assert res["arm_roots"][0]["description"] is None
    assert res["arm_roots"][0]["arm_colour"] is None
    assert res["arm_roots"][0]["randomization_group"] is None
    assert res["arm_roots"][0]["number_of_subjects"] is None
    assert res["arm_roots"][0]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_roots"][0]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_roots"][0]["arm_type"]["codelists"]) == 1
    assert (
        res["arm_roots"][0]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    )
    assert res["arm_roots"][0]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_roots"][0]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert (
        res["arm_roots"][0]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    )
    assert (
        res["arm_roots"][0]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_roots"][0]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_roots"][0]["arm_type"]["start_date"]
    assert res["arm_roots"][0]["arm_type"]["end_date"] is None
    assert res["arm_roots"][0]["arm_type"]["status"] == "Final"
    assert res["arm_roots"][0]["arm_type"]["version"] == "1.0"
    assert res["arm_roots"][0]["arm_type"]["change_description"] == "Approved version"
    assert (
        res["arm_roots"][0]["arm_type"]["author_username"] == "unknown-user@example.com"
    )
    assert res["arm_roots"][0]["arm_type"]["queried_effective_date"] is None
    assert res["arm_roots"][0]["arm_type"]["date_conflict"] is False
    assert res["arm_roots"][0]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_roots"][0]["start_date"]
    assert res["arm_roots"][0]["author_username"] == "unknown-user@example.com"
    assert res["arm_roots"][0]["end_date"] is None
    assert res["arm_roots"][0]["status"] is None
    assert res["arm_roots"][0]["change_type"] is None
    assert res["arm_roots"][0]["accepted_version"] is None
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False


def test_patch_specific_patch_some_name_that_is_already_used_on_another_cohort(
    api_client,
):
    data = {
        "name": "Cohort_Name_2",
        "short_name": "Cohort_Short_Name_8",
        "code": "Cohort_code_8",
        "description": "desc...",
        "colour_code": "desc...",
    }
    response = api_client.patch(
        "/studies/study_root/study-cohorts/StudyCohort_000001", json=data
    )

    assert_response_status_code(response, 422)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Value 'Cohort_Name_2' in field Cohort Name is not unique for the study."
    )


def test_patch_specific_patch_some_name_that_is_already_used_on_another_cohort1(
    api_client,
):
    data = {
        "name": "Cohort_Name_8",
        "short_name": "Cohort_Short_Name_8",
        "code": "Cohort_code_2",
        "description": "desc...",
        "colour_code": "desc...",
    }
    response = api_client.patch(
        "/studies/study_root/study-cohorts/StudyCohort_000001", json=data
    )

    assert_response_status_code(response, 422)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Value 'Cohort_code_2' in field Cohort code is not unique for the study."
    )
