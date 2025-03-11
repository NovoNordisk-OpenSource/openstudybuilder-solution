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
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.selection.cohorts")
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
    db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)
    study_uid = "study_root"
    arm_uid1 = "StudyArm_000001"
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
    create_study_branch_arm(
        study_uid=study_uid,
        name="Branch_Arm_Name_2",
        short_name="Branch_Arm_Short_Name_2",
        code="Branch_Arm_code_2",
        description="desc...",
        colour_code="colour...2",
        randomization_group="Branch_Arm_randomizationGroup2",
        number_of_subjects=20,
        arm_uid=arm_uid1,
    )

    yield

    drop_db("old.json.test.study.selection.cohorts")


def test_getting_empty_list3(api_client):
    response = api_client.get("/studies/study_root/study-cohorts")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_adding_selection5(api_client):
    data = {
        "name": "Cohort_Name_1",
        "short_name": "Cohort_Short_Name_1",
        "code": "Cohort_code_1",
        "description": "desc...",
        "colour_code": "colour_code_1",
        "number_of_subjects": 1,
        "arm_uids": ["StudyArm_000001", "StudyArm_000002"],
    }
    response = api_client.post("/studies/study_root/study-cohorts", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["cohort_uid"] == "StudyCohort_000001"
    assert res["order"] == 1
    assert res["name"] == "Cohort_Name_1"
    assert res["short_name"] == "Cohort_Short_Name_1"
    assert res["code"] == "Cohort_code_1"
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
    assert res["arm_roots"][1]["study_uid"] == "study_root"
    assert res["arm_roots"][1]["order"] == 2
    assert res["arm_roots"][1]["arm_uid"] == "StudyArm_000002"
    assert res["arm_roots"][1]["name"] == "StudyArm_000002"
    assert res["arm_roots"][1]["short_name"] == "StudyArm_000002"
    assert res["arm_roots"][1]["code"] is None
    assert res["arm_roots"][1]["description"] is None
    assert res["arm_roots"][1]["arm_colour"] is None
    assert res["arm_roots"][1]["randomization_group"] is None
    assert res["arm_roots"][1]["number_of_subjects"] is None
    assert res["arm_roots"][1]["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res["arm_roots"][1]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_roots"][1]["arm_type"]["codelists"]) == 1
    assert (
        res["arm_roots"][1]["arm_type"]["codelists"][0]["codelist_uid"]
        == "non_editable_cr"
    )
    assert res["arm_roots"][1]["arm_type"]["codelists"][0]["order"] == 3
    assert res["arm_roots"][1]["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert (
        res["arm_roots"][1]["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    )
    assert (
        res["arm_roots"][1]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_roots"][1]["arm_type"]["library_name"] == "CDISC"
    assert res["arm_roots"][1]["arm_type"]["start_date"]
    assert res["arm_roots"][1]["arm_type"]["end_date"] is None
    assert res["arm_roots"][1]["arm_type"]["status"] == "Final"
    assert res["arm_roots"][1]["arm_type"]["version"] == "1.0"
    assert res["arm_roots"][1]["arm_type"]["change_description"] == "Approved version"
    assert (
        res["arm_roots"][1]["arm_type"]["author_username"] == "unknown-user@example.com"
    )
    assert res["arm_roots"][1]["arm_type"]["queried_effective_date"] is None
    assert res["arm_roots"][1]["arm_type"]["date_conflict"] is False
    assert res["arm_roots"][1]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_roots"][1]["start_date"]
    assert res["arm_roots"][1]["author_username"] == "unknown-user@example.com"
    assert res["arm_roots"][1]["end_date"] is None
    assert res["arm_roots"][1]["status"] is None
    assert res["arm_roots"][1]["change_type"] is None
    assert res["arm_roots"][1]["accepted_version"] is None
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["colour_code"] == "colour_code_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_get_all_list_non_empty3(api_client):
    response = api_client.get("/studies/study_root/study-cohorts")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["study_version"]
    assert res["items"][0]["cohort_uid"] == "StudyCohort_000001"
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["name"] == "Cohort_Name_1"
    assert res["items"][0]["short_name"] == "Cohort_Short_Name_1"
    assert res["items"][0]["code"] == "Cohort_code_1"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] is None
    assert res["items"][0]["change_type"] is None
    assert res["items"][0]["accepted_version"] is False
    assert res["items"][0]["branch_arm_roots"] is None
    assert res["items"][0]["arm_roots"][0]["study_uid"] == "study_root"
    assert res["items"][0]["arm_roots"][0]["order"] == 1
    assert res["items"][0]["arm_roots"][0]["arm_uid"] == "StudyArm_000001"
    assert res["items"][0]["arm_roots"][0]["name"] == "StudyArm_000001"
    assert res["items"][0]["arm_roots"][0]["short_name"] == "StudyArm_000001"
    assert res["items"][0]["arm_roots"][0]["code"] is None
    assert res["items"][0]["arm_roots"][0]["description"] is None
    assert res["items"][0]["arm_roots"][0]["arm_colour"] is None
    assert res["items"][0]["arm_roots"][0]["randomization_group"] is None
    assert res["items"][0]["arm_roots"][0]["number_of_subjects"] is None
    assert res["items"][0]["arm_roots"][0]["arm_type"]["term_uid"] == "term_root_final"
    assert res["items"][0]["arm_roots"][0]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["items"][0]["arm_roots"][0]["arm_type"]["codelists"]) == 1
    assert (
        res["items"][0]["arm_roots"][0]["arm_type"]["codelists"][0]["codelist_uid"]
        == "editable_cr"
    )
    assert res["items"][0]["arm_roots"][0]["arm_type"]["codelists"][0]["order"] == 1
    assert (
        res["items"][0]["arm_roots"][0]["arm_type"]["codelists"][0]["library_name"]
        == "Sponsor"
    )
    assert (
        res["items"][0]["arm_roots"][0]["arm_type"]["sponsor_preferred_name"]
        == "term_value_name1"
    )
    assert (
        res["items"][0]["arm_roots"][0]["arm_type"][
            "sponsor_preferred_name_sentence_case"
        ]
        == "term_value_name_sentence_case"
    )
    assert res["items"][0]["arm_roots"][0]["arm_type"]["library_name"] == "Sponsor"
    assert res["items"][0]["arm_roots"][0]["arm_type"]["start_date"]
    assert res["items"][0]["arm_roots"][0]["arm_type"]["end_date"] is None
    assert res["items"][0]["arm_roots"][0]["arm_type"]["status"] == "Final"
    assert res["items"][0]["arm_roots"][0]["arm_type"]["version"] == "1.0"
    assert (
        res["items"][0]["arm_roots"][0]["arm_type"]["change_description"]
        == "Approved version"
    )
    assert (
        res["items"][0]["arm_roots"][0]["arm_type"]["author_username"]
        == "unknown-user@example.com"
    )
    assert res["items"][0]["arm_roots"][0]["arm_type"]["queried_effective_date"] is None
    assert res["items"][0]["arm_roots"][0]["arm_type"]["date_conflict"] is False
    assert res["items"][0]["arm_roots"][0]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["items"][0]["arm_roots"][0]["start_date"]
    assert (
        res["items"][0]["arm_roots"][0]["author_username"] == "unknown-user@example.com"
    )
    assert res["items"][0]["arm_roots"][0]["end_date"] is None
    assert res["items"][0]["arm_roots"][0]["status"] is None
    assert res["items"][0]["arm_roots"][0]["change_type"] is None
    assert res["items"][0]["arm_roots"][0]["accepted_version"] is None
    assert res["items"][0]["arm_roots"][1]["study_uid"] == "study_root"
    assert res["items"][0]["arm_roots"][1]["order"] == 2
    assert res["items"][0]["arm_roots"][1]["arm_uid"] == "StudyArm_000002"
    assert res["items"][0]["arm_roots"][1]["name"] == "StudyArm_000002"
    assert res["items"][0]["arm_roots"][1]["short_name"] == "StudyArm_000002"
    assert res["items"][0]["arm_roots"][1]["code"] is None
    assert res["items"][0]["arm_roots"][1]["description"] is None
    assert res["items"][0]["arm_roots"][1]["arm_colour"] is None
    assert res["items"][0]["arm_roots"][1]["randomization_group"] is None
    assert res["items"][0]["arm_roots"][1]["number_of_subjects"] is None
    assert (
        res["items"][0]["arm_roots"][1]["arm_type"]["term_uid"]
        == "term_root_final_non_edit"
    )
    assert res["items"][0]["arm_roots"][1]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["items"][0]["arm_roots"][1]["arm_type"]["codelists"]) == 1
    assert (
        res["items"][0]["arm_roots"][1]["arm_type"]["codelists"][0]["codelist_uid"]
        == "non_editable_cr"
    )
    assert res["items"][0]["arm_roots"][1]["arm_type"]["codelists"][0]["order"] == 3
    assert (
        res["items"][0]["arm_roots"][1]["arm_type"]["codelists"][0]["library_name"]
        == "CDISC"
    )
    assert (
        res["items"][0]["arm_roots"][1]["arm_type"]["sponsor_preferred_name"]
        == "term_value_name3"
    )
    assert (
        res["items"][0]["arm_roots"][1]["arm_type"][
            "sponsor_preferred_name_sentence_case"
        ]
        == "term_value_name_sentence_case"
    )
    assert res["items"][0]["arm_roots"][1]["arm_type"]["library_name"] == "CDISC"
    assert res["items"][0]["arm_roots"][1]["arm_type"]["start_date"]
    assert res["items"][0]["arm_roots"][1]["arm_type"]["end_date"] is None
    assert res["items"][0]["arm_roots"][1]["arm_type"]["status"] == "Final"
    assert res["items"][0]["arm_roots"][1]["arm_type"]["version"] == "1.0"
    assert (
        res["items"][0]["arm_roots"][1]["arm_type"]["change_description"]
        == "Approved version"
    )
    assert (
        res["items"][0]["arm_roots"][1]["arm_type"]["author_username"]
        == "unknown-user@example.com"
    )
    assert res["items"][0]["arm_roots"][1]["arm_type"]["queried_effective_date"] is None
    assert res["items"][0]["arm_roots"][1]["arm_type"]["date_conflict"] is False
    assert res["items"][0]["arm_roots"][1]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["items"][0]["arm_roots"][1]["start_date"]
    assert (
        res["items"][0]["arm_roots"][1]["author_username"] == "unknown-user@example.com"
    )
    assert res["items"][0]["arm_roots"][1]["end_date"] is None
    assert res["items"][0]["arm_roots"][1]["status"] is None
    assert res["items"][0]["arm_roots"][1]["change_type"] is None
    assert res["items"][0]["arm_roots"][1]["accepted_version"] is None
    assert res["items"][0]["description"] == "desc..."
    assert res["items"][0]["number_of_subjects"] == 1
    assert res["items"][0]["colour_code"] == "colour_code_1"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"


def test_get_specific3(api_client):
    response = api_client.get("/studies/study_root/study-cohorts/StudyCohort_000001")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["cohort_uid"] == "StudyCohort_000001"
    assert res["order"] == 1
    assert res["name"] == "Cohort_Name_1"
    assert res["short_name"] == "Cohort_Short_Name_1"
    assert res["code"] == "Cohort_code_1"
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
    assert res["arm_roots"][1]["study_uid"] == "study_root"
    assert res["arm_roots"][1]["order"] == 2
    assert res["arm_roots"][1]["arm_uid"] == "StudyArm_000002"
    assert res["arm_roots"][1]["name"] == "StudyArm_000002"
    assert res["arm_roots"][1]["short_name"] == "StudyArm_000002"
    assert res["arm_roots"][1]["code"] is None
    assert res["arm_roots"][1]["description"] is None
    assert res["arm_roots"][1]["arm_colour"] is None
    assert res["arm_roots"][1]["randomization_group"] is None
    assert res["arm_roots"][1]["number_of_subjects"] is None
    assert res["arm_roots"][1]["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res["arm_roots"][1]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_roots"][1]["arm_type"]["codelists"]) == 1
    assert (
        res["arm_roots"][1]["arm_type"]["codelists"][0]["codelist_uid"]
        == "non_editable_cr"
    )
    assert res["arm_roots"][1]["arm_type"]["codelists"][0]["order"] == 3
    assert res["arm_roots"][1]["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert (
        res["arm_roots"][1]["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    )
    assert (
        res["arm_roots"][1]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_roots"][1]["arm_type"]["library_name"] == "CDISC"
    assert res["arm_roots"][1]["arm_type"]["start_date"]
    assert res["arm_roots"][1]["arm_type"]["end_date"] is None
    assert res["arm_roots"][1]["arm_type"]["status"] == "Final"
    assert res["arm_roots"][1]["arm_type"]["version"] == "1.0"
    assert res["arm_roots"][1]["arm_type"]["change_description"] == "Approved version"
    assert (
        res["arm_roots"][1]["arm_type"]["author_username"] == "unknown-user@example.com"
    )
    assert res["arm_roots"][1]["arm_type"]["queried_effective_date"] is None
    assert res["arm_roots"][1]["arm_type"]["date_conflict"] is False
    assert res["arm_roots"][1]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_roots"][1]["start_date"]
    assert res["arm_roots"][1]["author_username"] == "unknown-user@example.com"
    assert res["arm_roots"][1]["end_date"] is None
    assert res["arm_roots"][1]["status"] is None
    assert res["arm_roots"][1]["change_type"] is None
    assert res["arm_roots"][1]["accepted_version"] is None


def test_patch_specific_set_name4(api_client):
    data = {"name": "New_Cohort_Name_1"}
    response = api_client.patch(
        "/studies/study_root/study-cohorts/StudyCohort_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["cohort_uid"] == "StudyCohort_000001"
    assert res["order"] == 1
    assert res["name"] == "New_Cohort_Name_1"
    assert res["short_name"] == "Cohort_Short_Name_1"
    assert res["code"] == "Cohort_code_1"
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
    assert res["arm_roots"][1]["study_uid"] == "study_root"
    assert res["arm_roots"][1]["order"] == 2
    assert res["arm_roots"][1]["arm_uid"] == "StudyArm_000002"
    assert res["arm_roots"][1]["name"] == "StudyArm_000002"
    assert res["arm_roots"][1]["short_name"] == "StudyArm_000002"
    assert res["arm_roots"][1]["code"] is None
    assert res["arm_roots"][1]["description"] is None
    assert res["arm_roots"][1]["arm_colour"] is None
    assert res["arm_roots"][1]["randomization_group"] is None
    assert res["arm_roots"][1]["number_of_subjects"] is None
    assert res["arm_roots"][1]["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res["arm_roots"][1]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_roots"][1]["arm_type"]["codelists"]) == 1
    assert (
        res["arm_roots"][1]["arm_type"]["codelists"][0]["codelist_uid"]
        == "non_editable_cr"
    )
    assert res["arm_roots"][1]["arm_type"]["codelists"][0]["order"] == 3
    assert res["arm_roots"][1]["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert (
        res["arm_roots"][1]["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    )
    assert (
        res["arm_roots"][1]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_roots"][1]["arm_type"]["library_name"] == "CDISC"
    assert res["arm_roots"][1]["arm_type"]["start_date"]
    assert res["arm_roots"][1]["arm_type"]["end_date"] is None
    assert res["arm_roots"][1]["arm_type"]["status"] == "Final"
    assert res["arm_roots"][1]["arm_type"]["version"] == "1.0"
    assert res["arm_roots"][1]["arm_type"]["change_description"] == "Approved version"
    assert (
        res["arm_roots"][1]["arm_type"]["author_username"] == "unknown-user@example.com"
    )
    assert res["arm_roots"][1]["arm_type"]["queried_effective_date"] is None
    assert res["arm_roots"][1]["arm_type"]["date_conflict"] is False
    assert res["arm_roots"][1]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_roots"][1]["start_date"]
    assert res["arm_roots"][1]["author_username"] == "unknown-user@example.com"
    assert res["arm_roots"][1]["end_date"] is None
    assert res["arm_roots"][1]["status"] is None
    assert res["arm_roots"][1]["change_type"] is None
    assert res["arm_roots"][1]["accepted_version"] is None
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["colour_code"] == "colour_code_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_all_history_of_specific_selection5(api_client):
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
    assert res[0]["name"] == "New_Cohort_Name_1"
    assert res[0]["short_name"] == "Cohort_Short_Name_1"
    assert res[0]["code"] == "Cohort_code_1"
    assert res[0]["description"] == "desc..."
    assert res[0]["colour_code"] == "colour_code_1"
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert res[0]["branch_arm_roots_uids"] is None
    assert res[0]["arm_roots_uids"] == ["StudyArm_000001", "StudyArm_000002"]
    assert res[0]["changes"] == {
        "name": True,
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
    assert res[1]["colour_code"] == "colour_code_1"
    assert res[1]["number_of_subjects"] == 1
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"]
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False
    assert res[1]["branch_arm_roots_uids"] is None
    assert res[1]["arm_roots_uids"] == ["StudyArm_000001", "StudyArm_000002"]
    assert res[1]["changes"] == {}


def test_2nd_adding_selection1(api_client):
    data = {
        "name": "Cohort_Name_2",
        "short_name": "Cohort_Short_Name_2",
        "code": "Cohort_code_2",
        "description": "desc...",
        "colour_code": "colour_code_2",
        "number_of_subjects": 1,
        "arm_uids": ["StudyArm_000001"],
    }
    response = api_client.post("/studies/study_root/study-cohorts", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["cohort_uid"] == "StudyCohort_000002"
    assert res["order"] == 2
    assert res["name"] == "Cohort_Name_2"
    assert res["short_name"] == "Cohort_Short_Name_2"
    assert res["code"] == "Cohort_code_2"
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
    assert res["number_of_subjects"] == 1
    assert res["colour_code"] == "colour_code_2"
    assert res["author_username"] == "unknown-user@example.com"


def test_delete_delete_the_1st_to_test_the_reordering_for_the_2nd_to_be_eq_to_11(
    api_client,
):
    response = api_client.delete("/studies/study_root/study-cohorts/StudyCohort_000001")

    assert_response_status_code(response, 204)


def test_3rd_adding_selection1(api_client):
    data = {
        "name": "Cohort_Name_3",
        "short_name": "Cohort_Short_Name_3",
        "code": "Cohort_code_3",
        "description": "desc...",
        "colour_code": "colour_code_3",
        "number_of_subjects": 3,
        "arm_uids": ["StudyArm_000001"],
    }
    response = api_client.post("/studies/study_root/study-cohorts", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["cohort_uid"] == "StudyCohort_000003"
    assert res["order"] == 2
    assert res["name"] == "Cohort_Name_3"
    assert res["short_name"] == "Cohort_Short_Name_3"
    assert res["code"] == "Cohort_code_3"
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
    assert res["number_of_subjects"] == 3
    assert res["colour_code"] == "colour_code_3"
    assert res["author_username"] == "unknown-user@example.com"


def test_4rd_adding_selection_for_another_arm(api_client):
    data = {
        "name": "Cohort_Name_4",
        "short_name": "Cohort_Short_Name_4",
        "code": "Cohort_code_4",
        "description": "desc...",
        "colour_code": "colour_code_4",
        "number_of_subjects": 4,
        "arm_uids": ["StudyArm_000002"],
    }
    response = api_client.post("/studies/study_root/study-cohorts", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["cohort_uid"] == "StudyCohort_000004"
    assert res["order"] == 3
    assert res["name"] == "Cohort_Name_4"
    assert res["short_name"] == "Cohort_Short_Name_4"
    assert res["code"] == "Cohort_code_4"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["branch_arm_roots"] is None
    assert res["arm_roots"][0]["study_uid"] == "study_root"
    assert res["arm_roots"][0]["order"] == 2
    assert res["arm_roots"][0]["arm_uid"] == "StudyArm_000002"
    assert res["arm_roots"][0]["name"] == "StudyArm_000002"
    assert res["arm_roots"][0]["short_name"] == "StudyArm_000002"
    assert res["arm_roots"][0]["code"] is None
    assert res["arm_roots"][0]["description"] is None
    assert res["arm_roots"][0]["arm_colour"] is None
    assert res["arm_roots"][0]["randomization_group"] is None
    assert res["arm_roots"][0]["number_of_subjects"] is None
    assert res["arm_roots"][0]["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res["arm_roots"][0]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_roots"][0]["arm_type"]["codelists"]) == 1
    assert (
        res["arm_roots"][0]["arm_type"]["codelists"][0]["codelist_uid"]
        == "non_editable_cr"
    )
    assert res["arm_roots"][0]["arm_type"]["codelists"][0]["order"] == 3
    assert res["arm_roots"][0]["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert (
        res["arm_roots"][0]["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    )
    assert (
        res["arm_roots"][0]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_roots"][0]["arm_type"]["library_name"] == "CDISC"
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
    assert res["number_of_subjects"] == 4
    assert res["colour_code"] == "colour_code_4"
    assert res["author_username"] == "unknown-user@example.com"


def test_5th_adding_selection_for_another_arm(api_client):
    data = {
        "name": "Cohort_Name_5",
        "short_name": "Cohort_Short_Name_5",
        "code": "Cohort_code_5",
        "description": "desc...",
        "colour_code": "colour_code_5",
        "number_of_subjects": 5,
        "arm_uids": None,
        "branch_arm_uid": None,
    }
    response = api_client.post("/studies/study_root/study-cohorts", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["cohort_uid"] == "StudyCohort_000005"
    assert res["order"] == 4
    assert res["name"] == "Cohort_Name_5"
    assert res["short_name"] == "Cohort_Short_Name_5"
    assert res["code"] == "Cohort_code_5"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["branch_arm_roots"] is None
    assert res["arm_roots"] is None
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 5
    assert res["colour_code"] == "colour_code_5"
    assert res["author_username"] == "unknown-user@example.com"


def test_reorder_specific3(api_client):
    data = {"new_order": 5}
    response = api_client.patch(
        "/studies/study_root/study-cohorts/StudyCohort_000003/order", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["cohort_uid"] == "StudyCohort_000003"
    assert res["order"] == 4
    assert res["name"] == "Cohort_Name_3"
    assert res["short_name"] == "Cohort_Short_Name_3"
    assert res["code"] == "Cohort_code_3"
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
    assert res["number_of_subjects"] == 3
    assert res["colour_code"] == "colour_code_3"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_selection6(api_client):
    data = {
        "name": "Cohort_Name_6",
        "short_name": "Cohort_Short_Name_6",
        "code": "Cohort_code_6",
        "description": "desc...",
        "colour_code": "colour_code_6",
        "number_of_subjects": 1,
        "arm_uids": ["StudyArm_000002"],
        "branch_arm_uids": ["StudyBranchArm_000001"],
    }
    response = api_client.post("/studies/study_root/study-cohorts", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["cohort_uid"] == "StudyCohort_000006"
    assert res["order"] == 5
    assert res["name"] == "Cohort_Name_6"
    assert res["short_name"] == "Cohort_Short_Name_6"
    assert res["code"] == "Cohort_code_6"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["branch_arm_roots"][0]["study_uid"] == "study_root"
    assert res["branch_arm_roots"][0]["order"] == 1
    assert res["branch_arm_roots"][0]["study_version"]
    assert res["branch_arm_roots"][0]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res["branch_arm_roots"][0]["name"] == "Branch_Arm_Name_1"
    assert res["branch_arm_roots"][0]["short_name"] == "Branch_Arm_Short_Name_1"
    assert res["branch_arm_roots"][0]["code"] == "Branch_Arm_code_1"
    assert res["branch_arm_roots"][0]["description"] == "desc..."
    assert res["branch_arm_roots"][0]["colour_code"] == "colour..."
    assert (
        res["branch_arm_roots"][0]["randomization_group"]
        == "Branch_Arm_randomizationGroup"
    )
    assert res["branch_arm_roots"][0]["number_of_subjects"] == 100
    assert res["branch_arm_roots"][0]["start_date"]
    assert res["branch_arm_roots"][0]["author_username"] == "unknown-user@example.com"
    assert res["branch_arm_roots"][0]["end_date"] is None
    assert res["branch_arm_roots"][0]["status"] is None
    assert res["branch_arm_roots"][0]["change_type"] is None
    assert res["branch_arm_roots"][0]["accepted_version"] is False
    assert res["branch_arm_roots"][0]["arm_root"]["study_uid"] == "study_root"
    assert res["branch_arm_roots"][0]["arm_root"]["order"] == 1
    assert res["branch_arm_roots"][0]["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["branch_arm_roots"][0]["arm_root"]["name"] == "StudyArm_000001"
    assert res["branch_arm_roots"][0]["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["branch_arm_roots"][0]["arm_root"]["code"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["description"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["arm_colour"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["randomization_group"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["number_of_subjects"] is None
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["term_uid"]
        == "term_root_final"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["catalogue_name"]
        == "SDTM CT"
    )
    assert len(res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"][0][
            "codelist_uid"
        ]
        == "editable_cr"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"][0][
            "library_name"
        ]
        == "Sponsor"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["sponsor_preferred_name"]
        == "term_value_name1"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"][
            "sponsor_preferred_name_sentence_case"
        ]
        == "term_value_name_sentence_case"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    )
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["start_date"]
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["end_date"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["status"] == "Final"
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["version"] == "1.0"
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["change_description"]
        == "Approved version"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["author_username"]
        == "unknown-user@example.com"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["queried_effective_date"]
        is None
    )
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["branch_arm_roots"][0]["arm_root"]["start_date"]
    assert (
        res["branch_arm_roots"][0]["arm_root"]["author_username"]
        == "unknown-user@example.com"
    )
    assert res["branch_arm_roots"][0]["arm_root"]["end_date"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["status"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["change_type"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["accepted_version"] is None

    assert res["arm_roots"][0]["study_uid"] == "study_root"
    assert res["arm_roots"][0]["order"] == 2
    assert res["arm_roots"][0]["arm_uid"] == "StudyArm_000002"
    assert res["arm_roots"][0]["name"] == "StudyArm_000002"
    assert res["arm_roots"][0]["short_name"] == "StudyArm_000002"
    assert res["arm_roots"][0]["code"] is None
    assert res["arm_roots"][0]["description"] is None
    assert res["arm_roots"][0]["arm_colour"] is None
    assert res["arm_roots"][0]["randomization_group"] is None
    assert res["arm_roots"][0]["number_of_subjects"] is None
    assert res["arm_roots"][0]["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res["arm_roots"][0]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_roots"][0]["arm_type"]["codelists"]) == 1
    assert (
        res["arm_roots"][0]["arm_type"]["codelists"][0]["codelist_uid"]
        == "non_editable_cr"
    )
    assert res["arm_roots"][0]["arm_type"]["codelists"][0]["order"] == 3
    assert res["arm_roots"][0]["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert (
        res["arm_roots"][0]["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    )
    assert (
        res["arm_roots"][0]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_roots"][0]["arm_type"]["library_name"] == "CDISC"
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
    assert res["number_of_subjects"] == 1
    assert res["colour_code"] == "colour_code_6"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_selection7(api_client):
    data = {
        "name": "Cohort_Name_7",
        "short_name": "Cohort_Short_Name_7",
        "code": "Cohort_code_7",
        "description": "desc...",
        "colour_code": "colour_code_7",
        "number_of_subjects": 1,
        "arm_uids": ["StudyArm_000002"],
        "branch_arm_uids": ["StudyBranchArm_000001", "StudyBranchArm_000003"],
    }
    response = api_client.post("/studies/study_root/study-cohorts", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["cohort_uid"] == "StudyCohort_000007"
    assert res["order"] == 6
    assert res["name"] == "Cohort_Name_7"
    assert res["short_name"] == "Cohort_Short_Name_7"
    assert res["code"] == "Cohort_code_7"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["branch_arm_roots"][0]["study_uid"] == "study_root"
    assert res["branch_arm_roots"][0]["order"] == 1
    assert res["branch_arm_roots"][0]["study_version"]
    assert res["branch_arm_roots"][0]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res["branch_arm_roots"][0]["name"] == "Branch_Arm_Name_1"
    assert res["branch_arm_roots"][0]["short_name"] == "Branch_Arm_Short_Name_1"
    assert res["branch_arm_roots"][0]["code"] == "Branch_Arm_code_1"
    assert res["branch_arm_roots"][0]["description"] == "desc..."
    assert res["branch_arm_roots"][0]["colour_code"] == "colour..."
    assert (
        res["branch_arm_roots"][0]["randomization_group"]
        == "Branch_Arm_randomizationGroup"
    )
    assert res["branch_arm_roots"][0]["number_of_subjects"] == 100
    assert res["branch_arm_roots"][0]["start_date"]
    assert res["branch_arm_roots"][0]["author_username"] == "unknown-user@example.com"
    assert res["branch_arm_roots"][0]["end_date"] is None
    assert res["branch_arm_roots"][0]["status"] is None
    assert res["branch_arm_roots"][0]["change_type"] is None
    assert res["branch_arm_roots"][0]["accepted_version"] is False
    assert res["branch_arm_roots"][0]["arm_root"]["study_uid"] == "study_root"
    assert res["branch_arm_roots"][0]["arm_root"]["order"] == 1
    assert res["branch_arm_roots"][0]["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["branch_arm_roots"][0]["arm_root"]["name"] == "StudyArm_000001"
    assert res["branch_arm_roots"][0]["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["branch_arm_roots"][0]["arm_root"]["code"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["description"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["arm_colour"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["randomization_group"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["number_of_subjects"] is None
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["term_uid"]
        == "term_root_final"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["catalogue_name"]
        == "SDTM CT"
    )
    assert len(res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"][0][
            "codelist_uid"
        ]
        == "editable_cr"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"][0][
            "library_name"
        ]
        == "Sponsor"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["sponsor_preferred_name"]
        == "term_value_name1"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"][
            "sponsor_preferred_name_sentence_case"
        ]
        == "term_value_name_sentence_case"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    )
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["start_date"]
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["end_date"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["status"] == "Final"
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["version"] == "1.0"
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["change_description"]
        == "Approved version"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["author_username"]
        == "unknown-user@example.com"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["queried_effective_date"]
        is None
    )
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["branch_arm_roots"][0]["arm_root"]["start_date"]
    assert (
        res["branch_arm_roots"][0]["arm_root"]["author_username"]
        == "unknown-user@example.com"
    )
    assert res["branch_arm_roots"][0]["arm_root"]["end_date"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["status"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["change_type"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["accepted_version"] is None
    assert res["branch_arm_roots"][1]["study_uid"] == "study_root"
    assert res["branch_arm_roots"][1]["order"] == 2
    assert res["branch_arm_roots"][1]["study_version"]
    assert res["branch_arm_roots"][1]["branch_arm_uid"] == "StudyBranchArm_000003"
    assert res["branch_arm_roots"][1]["name"] == "Branch_Arm_Name_2"
    assert res["branch_arm_roots"][1]["short_name"] == "Branch_Arm_Short_Name_2"
    assert res["branch_arm_roots"][1]["code"] == "Branch_Arm_code_2"
    assert res["branch_arm_roots"][1]["description"] == "desc..."
    assert res["branch_arm_roots"][1]["colour_code"] == "colour...2"
    assert (
        res["branch_arm_roots"][1]["randomization_group"]
        == "Branch_Arm_randomizationGroup2"
    )
    assert res["branch_arm_roots"][1]["number_of_subjects"] == 20
    assert res["branch_arm_roots"][1]["start_date"]
    assert res["branch_arm_roots"][1]["author_username"] == "unknown-user@example.com"
    assert res["branch_arm_roots"][1]["end_date"] is None
    assert res["branch_arm_roots"][1]["status"] is None
    assert res["branch_arm_roots"][1]["change_type"] is None
    assert res["branch_arm_roots"][1]["accepted_version"] is False
    assert res["branch_arm_roots"][1]["arm_root"]["study_uid"] == "study_root"
    assert res["branch_arm_roots"][1]["arm_root"]["order"] == 1
    assert res["branch_arm_roots"][1]["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["branch_arm_roots"][1]["arm_root"]["name"] == "StudyArm_000001"
    assert res["branch_arm_roots"][1]["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["branch_arm_roots"][1]["arm_root"]["code"] is None
    assert res["branch_arm_roots"][1]["arm_root"]["description"] is None
    assert res["branch_arm_roots"][1]["arm_root"]["arm_colour"] is None
    assert res["branch_arm_roots"][1]["arm_root"]["randomization_group"] is None
    assert res["branch_arm_roots"][1]["arm_root"]["number_of_subjects"] is None
    assert (
        res["branch_arm_roots"][1]["arm_root"]["arm_type"]["term_uid"]
        == "term_root_final"
    )
    assert (
        res["branch_arm_roots"][1]["arm_root"]["arm_type"]["catalogue_name"]
        == "SDTM CT"
    )
    assert len(res["branch_arm_roots"][1]["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res["branch_arm_roots"][1]["arm_root"]["arm_type"]["codelists"][0][
            "codelist_uid"
        ]
        == "editable_cr"
    )
    assert (
        res["branch_arm_roots"][1]["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    )
    assert (
        res["branch_arm_roots"][1]["arm_root"]["arm_type"]["codelists"][0][
            "library_name"
        ]
        == "Sponsor"
    )
    assert (
        res["branch_arm_roots"][1]["arm_root"]["arm_type"]["sponsor_preferred_name"]
        == "term_value_name1"
    )
    assert (
        res["branch_arm_roots"][1]["arm_root"]["arm_type"][
            "sponsor_preferred_name_sentence_case"
        ]
        == "term_value_name_sentence_case"
    )
    assert (
        res["branch_arm_roots"][1]["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    )
    assert res["branch_arm_roots"][1]["arm_root"]["arm_type"]["start_date"]
    assert res["branch_arm_roots"][1]["arm_root"]["arm_type"]["end_date"] is None
    assert res["branch_arm_roots"][1]["arm_root"]["arm_type"]["status"] == "Final"
    assert res["branch_arm_roots"][1]["arm_root"]["arm_type"]["version"] == "1.0"
    assert (
        res["branch_arm_roots"][1]["arm_root"]["arm_type"]["change_description"]
        == "Approved version"
    )
    assert (
        res["branch_arm_roots"][1]["arm_root"]["arm_type"]["author_username"]
        == "unknown-user@example.com"
    )
    assert (
        res["branch_arm_roots"][1]["arm_root"]["arm_type"]["queried_effective_date"]
        is None
    )
    assert res["branch_arm_roots"][1]["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["branch_arm_roots"][1]["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["branch_arm_roots"][1]["arm_root"]["start_date"]
    assert (
        res["branch_arm_roots"][1]["arm_root"]["author_username"]
        == "unknown-user@example.com"
    )
    assert res["branch_arm_roots"][1]["arm_root"]["end_date"] is None
    assert res["branch_arm_roots"][1]["arm_root"]["status"] is None
    assert res["branch_arm_roots"][1]["arm_root"]["change_type"] is None
    assert res["branch_arm_roots"][1]["arm_root"]["accepted_version"] is None
    assert res["arm_roots"][0]["study_uid"] == "study_root"
    assert res["arm_roots"][0]["order"] == 2
    assert res["arm_roots"][0]["arm_uid"] == "StudyArm_000002"
    assert res["arm_roots"][0]["name"] == "StudyArm_000002"
    assert res["arm_roots"][0]["short_name"] == "StudyArm_000002"
    assert res["arm_roots"][0]["code"] is None
    assert res["arm_roots"][0]["description"] is None
    assert res["arm_roots"][0]["arm_colour"] is None
    assert res["arm_roots"][0]["randomization_group"] is None
    assert res["arm_roots"][0]["number_of_subjects"] is None
    assert res["arm_roots"][0]["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res["arm_roots"][0]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_roots"][0]["arm_type"]["codelists"]) == 1
    assert (
        res["arm_roots"][0]["arm_type"]["codelists"][0]["codelist_uid"]
        == "non_editable_cr"
    )
    assert res["arm_roots"][0]["arm_type"]["codelists"][0]["order"] == 3
    assert res["arm_roots"][0]["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert (
        res["arm_roots"][0]["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    )
    assert (
        res["arm_roots"][0]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_roots"][0]["arm_type"]["library_name"] == "CDISC"
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
    assert res["number_of_subjects"] == 1
    assert res["colour_code"] == "colour_code_7"
    assert res["author_username"] == "unknown-user@example.com"


def test_studybrancharm_delete_to_ensure_that_the_studybrancharm_cohort_relationship_is_being_updated(
    api_client,
):
    response = api_client.delete(
        "/studies/study_root/study-branch-arms/StudyBranchArm_000003"
    )

    assert_response_status_code(response, 204)


def test_get_specific4(api_client):
    response = api_client.get("/studies/study_root/study-cohorts/StudyCohort_000007")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 6
    assert res["study_version"]
    assert res["cohort_uid"] == "StudyCohort_000007"
    assert res["name"] == "Cohort_Name_7"
    assert res["short_name"] == "Cohort_Short_Name_7"
    assert res["code"] == "Cohort_code_7"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "colour_code_7"
    assert res["number_of_subjects"] == 1
    assert res["branch_arm_roots"][0]["study_uid"] == "study_root"
    assert res["branch_arm_roots"][0]["order"] == 1
    assert res["branch_arm_roots"][0]["study_version"]
    assert res["branch_arm_roots"][0]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res["branch_arm_roots"][0]["name"] == "Branch_Arm_Name_1"
    assert res["branch_arm_roots"][0]["short_name"] == "Branch_Arm_Short_Name_1"
    assert res["branch_arm_roots"][0]["code"] == "Branch_Arm_code_1"
    assert res["branch_arm_roots"][0]["description"] == "desc..."
    assert res["branch_arm_roots"][0]["colour_code"] == "colour..."
    assert (
        res["branch_arm_roots"][0]["randomization_group"]
        == "Branch_Arm_randomizationGroup"
    )
    assert res["branch_arm_roots"][0]["number_of_subjects"] == 100
    assert res["branch_arm_roots"][0]["start_date"]
    assert res["branch_arm_roots"][0]["author_username"] == "unknown-user@example.com"
    assert res["branch_arm_roots"][0]["end_date"] is None
    assert res["branch_arm_roots"][0]["status"] is None
    assert res["branch_arm_roots"][0]["change_type"] is None
    assert res["branch_arm_roots"][0]["accepted_version"] is False
    assert res["branch_arm_roots"][0]["arm_root"]["study_uid"] == "study_root"
    assert res["branch_arm_roots"][0]["arm_root"]["order"] == 1
    assert res["branch_arm_roots"][0]["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["branch_arm_roots"][0]["arm_root"]["name"] == "StudyArm_000001"
    assert res["branch_arm_roots"][0]["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["branch_arm_roots"][0]["arm_root"]["code"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["description"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["arm_colour"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["randomization_group"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["number_of_subjects"] is None
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["term_uid"]
        == "term_root_final"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["catalogue_name"]
        == "SDTM CT"
    )
    assert len(res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"][0][
            "codelist_uid"
        ]
        == "editable_cr"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"][0][
            "library_name"
        ]
        == "Sponsor"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["sponsor_preferred_name"]
        == "term_value_name1"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"][
            "sponsor_preferred_name_sentence_case"
        ]
        == "term_value_name_sentence_case"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    )
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["start_date"]
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["end_date"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["status"] == "Final"
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["version"] == "1.0"
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["change_description"]
        == "Approved version"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["author_username"]
        == "unknown-user@example.com"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["queried_effective_date"]
        is None
    )
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["branch_arm_roots"][0]["arm_root"]["start_date"]
    assert (
        res["branch_arm_roots"][0]["arm_root"]["author_username"]
        == "unknown-user@example.com"
    )
    assert res["branch_arm_roots"][0]["arm_root"]["end_date"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["status"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["change_type"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["accepted_version"] is None
    assert res["arm_roots"][0]["study_uid"] == "study_root"
    assert res["arm_roots"][0]["order"] == 2
    assert res["arm_roots"][0]["arm_uid"] == "StudyArm_000002"
    assert res["arm_roots"][0]["name"] == "StudyArm_000002"
    assert res["arm_roots"][0]["short_name"] == "StudyArm_000002"
    assert res["arm_roots"][0]["code"] is None
    assert res["arm_roots"][0]["description"] is None
    assert res["arm_roots"][0]["arm_colour"] is None
    assert res["arm_roots"][0]["randomization_group"] is None
    assert res["arm_roots"][0]["number_of_subjects"] is None
    assert res["arm_roots"][0]["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res["arm_roots"][0]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_roots"][0]["arm_type"]["codelists"]) == 1
    assert (
        res["arm_roots"][0]["arm_type"]["codelists"][0]["codelist_uid"]
        == "non_editable_cr"
    )
    assert res["arm_roots"][0]["arm_type"]["codelists"][0]["order"] == 3
    assert res["arm_roots"][0]["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert (
        res["arm_roots"][0]["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    )
    assert (
        res["arm_roots"][0]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_roots"][0]["arm_type"]["library_name"] == "CDISC"
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


def test_all_history_of_all_selection_study_cohort(api_client):
    response = api_client.get("/studies/study_root/study-cohort/audit-trail")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 1
    assert res[0]["project_number"] is None
    assert res[0]["project_name"] is None
    assert res[0]["study_version"] is None
    assert res[0]["cohort_uid"] == "StudyCohort_000001"
    assert res[0]["name"] == "New_Cohort_Name_1"
    assert res[0]["short_name"] == "Cohort_Short_Name_1"
    assert res[0]["code"] == "Cohort_code_1"
    assert res[0]["description"] == "desc..."
    assert res[0]["colour_code"] == "colour_code_1"
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Delete"
    assert res[0]["accepted_version"] is False
    assert res[0]["branch_arm_roots_uids"] is None
    assert res[0]["arm_roots_uids"] == ["StudyArm_000001", "StudyArm_000002"]
    assert res[0]["changes"] == {
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
    assert res[1]["name"] == "New_Cohort_Name_1"
    assert res[1]["short_name"] == "Cohort_Short_Name_1"
    assert res[1]["code"] == "Cohort_code_1"
    assert res[1]["description"] == "desc..."
    assert res[1]["colour_code"] == "colour_code_1"
    assert res[1]["number_of_subjects"] == 1
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"]
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Edit"
    assert res[1]["accepted_version"] is False
    assert res[1]["branch_arm_roots_uids"] is None
    assert res[1]["arm_roots_uids"] == ["StudyArm_000001", "StudyArm_000002"]
    assert res[1]["changes"] == {
        "name": True,
        "start_date": True,
        "end_date": True,
        "change_type": True,
    }
    assert res[2]["study_uid"] == "study_root"
    assert res[2]["order"] == 1
    assert res[2]["project_number"] is None
    assert res[2]["project_name"] is None
    assert res[2]["study_version"] is None
    assert res[2]["cohort_uid"] == "StudyCohort_000001"
    assert res[2]["name"] == "Cohort_Name_1"
    assert res[2]["short_name"] == "Cohort_Short_Name_1"
    assert res[2]["code"] == "Cohort_code_1"
    assert res[2]["description"] == "desc..."
    assert res[2]["colour_code"] == "colour_code_1"
    assert res[2]["number_of_subjects"] == 1
    assert res[2]["author_username"] == "unknown-user@example.com"
    assert res[2]["end_date"]
    assert res[2]["status"] is None
    assert res[2]["change_type"] == "Create"
    assert res[2]["accepted_version"] is False
    assert res[2]["branch_arm_roots_uids"] is None
    assert res[2]["arm_roots_uids"] == ["StudyArm_000001", "StudyArm_000002"]
    assert res[2]["changes"] == {}
    assert res[3]["study_uid"] == "study_root"
    assert res[3]["order"] == 1
    assert res[3]["project_number"] is None
    assert res[3]["project_name"] is None
    assert res[3]["study_version"] is None
    assert res[3]["cohort_uid"] == "StudyCohort_000002"
    assert res[3]["name"] == "Cohort_Name_2"
    assert res[3]["short_name"] == "Cohort_Short_Name_2"
    assert res[3]["code"] == "Cohort_code_2"
    assert res[3]["description"] == "desc..."
    assert res[3]["colour_code"] == "colour_code_2"
    assert res[3]["number_of_subjects"] == 1
    assert res[3]["author_username"] == "unknown-user@example.com"
    assert res[3]["end_date"] is None
    assert res[3]["status"] is None
    assert res[3]["change_type"] == "Edit"
    assert res[3]["accepted_version"] is False
    assert res[3]["branch_arm_roots_uids"] is None
    assert res[3]["arm_roots_uids"] == ["StudyArm_000001"]
    assert res[3]["changes"] == {
        "order": True,
        "start_date": True,
        "end_date": True,
        "change_type": True,
    }
    assert res[4]["study_uid"] == "study_root"
    assert res[4]["order"] == 2
    assert res[4]["project_number"] is None
    assert res[4]["project_name"] is None
    assert res[4]["study_version"] is None
    assert res[4]["cohort_uid"] == "StudyCohort_000002"
    assert res[4]["name"] == "Cohort_Name_2"
    assert res[4]["short_name"] == "Cohort_Short_Name_2"
    assert res[4]["code"] == "Cohort_code_2"
    assert res[4]["description"] == "desc..."
    assert res[4]["colour_code"] == "colour_code_2"
    assert res[4]["number_of_subjects"] == 1
    assert res[4]["author_username"] == "unknown-user@example.com"
    assert res[4]["end_date"]
    assert res[4]["status"] is None
    assert res[4]["change_type"] == "Create"
    assert res[4]["accepted_version"] is False
    assert res[4]["branch_arm_roots_uids"] is None
    assert res[4]["arm_roots_uids"] == ["StudyArm_000001"]
    assert res[4]["changes"] == {}
    assert res[5]["study_uid"] == "study_root"
    assert res[5]["order"] == 4
    assert res[5]["project_number"] is None
    assert res[5]["project_name"] is None
    assert res[5]["study_version"] is None
    assert res[5]["cohort_uid"] == "StudyCohort_000003"
    assert res[5]["name"] == "Cohort_Name_3"
    assert res[5]["short_name"] == "Cohort_Short_Name_3"
    assert res[5]["code"] == "Cohort_code_3"
    assert res[5]["description"] == "desc..."
    assert res[5]["colour_code"] == "colour_code_3"
    assert res[5]["number_of_subjects"] == 3
    assert res[5]["author_username"] == "unknown-user@example.com"
    assert res[5]["end_date"] is None
    assert res[5]["status"] is None
    assert res[5]["change_type"] == "Edit"
    assert res[5]["accepted_version"] is False
    assert res[5]["branch_arm_roots_uids"] is None
    assert res[5]["arm_roots_uids"] == ["StudyArm_000001"]
    assert res[5]["changes"] == {
        "order": True,
        "start_date": True,
        "end_date": True,
        "change_type": True,
    }
    assert res[6]["study_uid"] == "study_root"
    assert res[6]["order"] == 2
    assert res[6]["project_number"] is None
    assert res[6]["project_name"] is None
    assert res[6]["study_version"] is None
    assert res[6]["cohort_uid"] == "StudyCohort_000003"
    assert res[6]["name"] == "Cohort_Name_3"
    assert res[6]["short_name"] == "Cohort_Short_Name_3"
    assert res[6]["code"] == "Cohort_code_3"
    assert res[6]["description"] == "desc..."
    assert res[6]["colour_code"] == "colour_code_3"
    assert res[6]["number_of_subjects"] == 3
    assert res[6]["author_username"] == "unknown-user@example.com"
    assert res[6]["end_date"]
    assert res[6]["status"] is None
    assert res[6]["change_type"] == "Create"
    assert res[6]["accepted_version"] is False
    assert res[6]["branch_arm_roots_uids"] is None
    assert res[6]["arm_roots_uids"] == ["StudyArm_000001"]
    assert res[6]["changes"] == {}
    assert res[7]["study_uid"] == "study_root"
    assert res[7]["order"] == 2
    assert res[7]["project_number"] is None
    assert res[7]["project_name"] is None
    assert res[7]["study_version"] is None
    assert res[7]["cohort_uid"] == "StudyCohort_000004"
    assert res[7]["name"] == "Cohort_Name_4"
    assert res[7]["short_name"] == "Cohort_Short_Name_4"
    assert res[7]["code"] == "Cohort_code_4"
    assert res[7]["description"] == "desc..."
    assert res[7]["colour_code"] == "colour_code_4"
    assert res[7]["number_of_subjects"] == 4
    assert res[7]["author_username"] == "unknown-user@example.com"
    assert res[7]["end_date"] is None
    assert res[7]["status"] is None
    assert res[7]["change_type"] == "Edit"
    assert res[7]["accepted_version"] is False
    assert res[7]["branch_arm_roots_uids"] is None
    assert res[7]["arm_roots_uids"] == ["StudyArm_000002"]
    assert res[7]["changes"] == {
        "order": True,
        "start_date": True,
        "end_date": True,
        "change_type": True,
    }
    assert res[8]["study_uid"] == "study_root"
    assert res[8]["order"] == 3
    assert res[8]["project_number"] is None
    assert res[8]["project_name"] is None
    assert res[8]["study_version"] is None
    assert res[8]["cohort_uid"] == "StudyCohort_000004"
    assert res[8]["name"] == "Cohort_Name_4"
    assert res[8]["short_name"] == "Cohort_Short_Name_4"
    assert res[8]["code"] == "Cohort_code_4"
    assert res[8]["description"] == "desc..."
    assert res[8]["colour_code"] == "colour_code_4"
    assert res[8]["number_of_subjects"] == 4
    assert res[8]["author_username"] == "unknown-user@example.com"
    assert res[8]["end_date"]
    assert res[8]["status"] is None
    assert res[8]["change_type"] == "Create"
    assert res[8]["accepted_version"] is False
    assert res[8]["branch_arm_roots_uids"] is None
    assert res[8]["arm_roots_uids"] == ["StudyArm_000002"]
    assert res[8]["changes"] == {}
    assert res[9]["study_uid"] == "study_root"
    assert res[9]["order"] == 3
    assert res[9]["project_number"] is None
    assert res[9]["project_name"] is None
    assert res[9]["study_version"] is None
    assert res[9]["cohort_uid"] == "StudyCohort_000005"
    assert res[9]["name"] == "Cohort_Name_5"
    assert res[9]["short_name"] == "Cohort_Short_Name_5"
    assert res[9]["code"] == "Cohort_code_5"
    assert res[9]["description"] == "desc..."
    assert res[9]["colour_code"] == "colour_code_5"
    assert res[9]["number_of_subjects"] == 5
    assert res[9]["author_username"] == "unknown-user@example.com"
    assert res[9]["end_date"] is None
    assert res[9]["status"] is None
    assert res[9]["change_type"] == "Edit"
    assert res[9]["accepted_version"] is False
    assert res[9]["branch_arm_roots_uids"] is None
    assert res[9]["arm_roots_uids"] is None
    assert res[9]["changes"] == {
        "order": True,
        "start_date": True,
        "end_date": True,
        "change_type": True,
    }
    assert res[10]["study_uid"] == "study_root"
    assert res[10]["order"] == 4
    assert res[10]["project_number"] is None
    assert res[10]["project_name"] is None
    assert res[10]["study_version"] is None
    assert res[10]["cohort_uid"] == "StudyCohort_000005"
    assert res[10]["name"] == "Cohort_Name_5"
    assert res[10]["short_name"] == "Cohort_Short_Name_5"
    assert res[10]["code"] == "Cohort_code_5"
    assert res[10]["description"] == "desc..."
    assert res[10]["colour_code"] == "colour_code_5"
    assert res[10]["number_of_subjects"] == 5
    assert res[10]["author_username"] == "unknown-user@example.com"
    assert res[10]["end_date"]
    assert res[10]["status"] is None
    assert res[10]["change_type"] == "Create"
    assert res[10]["accepted_version"] is False
    assert res[10]["branch_arm_roots_uids"] is None
    assert res[10]["arm_roots_uids"] is None
    assert res[10]["changes"] == {}
    assert res[11]["study_uid"] == "study_root"
    assert res[11]["order"] == 5
    assert res[11]["project_number"] is None
    assert res[11]["project_name"] is None
    assert res[11]["study_version"] is None
    assert res[11]["cohort_uid"] == "StudyCohort_000006"
    assert res[11]["name"] == "Cohort_Name_6"
    assert res[11]["short_name"] == "Cohort_Short_Name_6"
    assert res[11]["code"] == "Cohort_code_6"
    assert res[11]["description"] == "desc..."
    assert res[11]["colour_code"] == "colour_code_6"
    assert res[11]["number_of_subjects"] == 1
    assert res[11]["author_username"] == "unknown-user@example.com"
    assert res[11]["end_date"] is None
    assert res[11]["status"] is None
    assert res[11]["change_type"] == "Create"
    assert res[11]["accepted_version"] is False
    assert res[11]["branch_arm_roots_uids"] == ["StudyBranchArm_000001"]
    assert res[11]["arm_roots_uids"] == ["StudyArm_000002"]
    assert res[11]["changes"] == {}
    assert res[12]["study_uid"] == "study_root"
    assert res[12]["order"] == 6
    assert res[12]["project_number"] is None
    assert res[12]["project_name"] is None
    assert res[12]["study_version"] is None
    assert res[12]["cohort_uid"] == "StudyCohort_000007"
    assert res[12]["name"] == "Cohort_Name_7"
    assert res[12]["short_name"] == "Cohort_Short_Name_7"
    assert res[12]["code"] == "Cohort_code_7"
    assert res[12]["description"] == "desc..."
    assert res[12]["colour_code"] == "colour_code_7"
    assert res[12]["number_of_subjects"] == 1
    assert res[12]["author_username"] == "unknown-user@example.com"
    assert res[12]["end_date"] is None
    assert res[12]["status"] is None
    assert res[12]["change_type"] == "Create"
    assert res[12]["accepted_version"] is False
    assert res[12]["branch_arm_roots_uids"] == [
        "StudyBranchArm_000001",
        "StudyBranchArm_000003",
        "StudyBranchArm_000003",
    ]
    assert res[12]["arm_roots_uids"] == [
        "StudyArm_000002",
        "StudyArm_000002",
        "StudyArm_000002",
    ]
    assert res[12]["changes"] == {}


def test_adding_selection_8_to_ensure_that_the_only_required_fields_are_the_name_and_short_name_fields(
    api_client,
):
    data = {"name": "Cohort_Name_8", "short_name": "Cohort_Short_Name_8"}
    response = api_client.post("/studies/study_root/study-cohorts", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 7
    assert res["study_version"]
    assert res["cohort_uid"] == "StudyCohort_000008"
    assert res["name"] == "Cohort_Name_8"
    assert res["short_name"] == "Cohort_Short_Name_8"
    assert res["code"] is None
    assert res["description"] is None
    assert res["colour_code"] is None
    assert res["number_of_subjects"] is None
    assert res["branch_arm_roots"] is None
    assert res["arm_roots"] is None
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False


def test_patch_number_of_subjects_as_null(api_client):
    data = {"number_of_subjects": None}
    response = api_client.patch(
        "/studies/study_root/study-cohorts/StudyCohort_000007", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 6
    assert res["study_version"]
    assert res["cohort_uid"] == "StudyCohort_000007"
    assert res["name"] == "Cohort_Name_7"
    assert res["short_name"] == "Cohort_Short_Name_7"
    assert res["code"] == "Cohort_code_7"
    assert res["description"] == "desc..."
    assert res["colour_code"] == "colour_code_7"
    assert res["number_of_subjects"] is None
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["branch_arm_roots"][0]["study_uid"] == "study_root"
    assert res["branch_arm_roots"][0]["order"] == 1
    assert res["branch_arm_roots"][0]["study_version"]
    assert res["branch_arm_roots"][0]["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res["branch_arm_roots"][0]["name"] == "Branch_Arm_Name_1"
    assert res["branch_arm_roots"][0]["short_name"] == "Branch_Arm_Short_Name_1"
    assert res["branch_arm_roots"][0]["code"] == "Branch_Arm_code_1"
    assert res["branch_arm_roots"][0]["description"] == "desc..."
    assert res["branch_arm_roots"][0]["colour_code"] == "colour..."
    assert (
        res["branch_arm_roots"][0]["randomization_group"]
        == "Branch_Arm_randomizationGroup"
    )
    assert res["branch_arm_roots"][0]["number_of_subjects"] == 100
    assert res["branch_arm_roots"][0]["start_date"]
    assert res["branch_arm_roots"][0]["author_username"] == "unknown-user@example.com"
    assert res["branch_arm_roots"][0]["end_date"] is None
    assert res["branch_arm_roots"][0]["status"] is None
    assert res["branch_arm_roots"][0]["change_type"] is None
    assert res["branch_arm_roots"][0]["accepted_version"] is False
    assert res["branch_arm_roots"][0]["arm_root"]["study_uid"] == "study_root"
    assert res["branch_arm_roots"][0]["arm_root"]["order"] == 1
    assert res["branch_arm_roots"][0]["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["branch_arm_roots"][0]["arm_root"]["name"] == "StudyArm_000001"
    assert res["branch_arm_roots"][0]["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["branch_arm_roots"][0]["arm_root"]["code"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["description"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["arm_colour"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["randomization_group"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["number_of_subjects"] is None
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["term_uid"]
        == "term_root_final"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["catalogue_name"]
        == "SDTM CT"
    )
    assert len(res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"]) == 1
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"][0][
            "codelist_uid"
        ]
        == "editable_cr"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["codelists"][0][
            "library_name"
        ]
        == "Sponsor"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["sponsor_preferred_name"]
        == "term_value_name1"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"][
            "sponsor_preferred_name_sentence_case"
        ]
        == "term_value_name_sentence_case"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    )
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["start_date"]
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["end_date"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["status"] == "Final"
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["version"] == "1.0"
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["change_description"]
        == "Approved version"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["author_username"]
        == "unknown-user@example.com"
    )
    assert (
        res["branch_arm_roots"][0]["arm_root"]["arm_type"]["queried_effective_date"]
        is None
    )
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["branch_arm_roots"][0]["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["branch_arm_roots"][0]["arm_root"]["start_date"]
    assert (
        res["branch_arm_roots"][0]["arm_root"]["author_username"]
        == "unknown-user@example.com"
    )
    assert res["branch_arm_roots"][0]["arm_root"]["end_date"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["status"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["change_type"] is None
    assert res["branch_arm_roots"][0]["arm_root"]["accepted_version"] is None
    assert res["arm_roots"][0]["study_uid"] == "study_root"
    assert res["arm_roots"][0]["order"] == 2
    assert res["arm_roots"][0]["arm_uid"] == "StudyArm_000002"
    assert res["arm_roots"][0]["name"] == "StudyArm_000002"
    assert res["arm_roots"][0]["short_name"] == "StudyArm_000002"
    assert res["arm_roots"][0]["code"] is None
    assert res["arm_roots"][0]["description"] is None
    assert res["arm_roots"][0]["arm_colour"] is None
    assert res["arm_roots"][0]["randomization_group"] is None
    assert res["arm_roots"][0]["number_of_subjects"] is None
    assert res["arm_roots"][0]["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res["arm_roots"][0]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_roots"][0]["arm_type"]["codelists"]) == 1
    assert (
        res["arm_roots"][0]["arm_type"]["codelists"][0]["codelist_uid"]
        == "non_editable_cr"
    )
    assert res["arm_roots"][0]["arm_type"]["codelists"][0]["order"] == 3
    assert res["arm_roots"][0]["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert (
        res["arm_roots"][0]["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    )
    assert (
        res["arm_roots"][0]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_roots"][0]["arm_type"]["library_name"] == "CDISC"
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
