# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

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
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_arm,
    create_study_branch_arm,
    create_study_cohort,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

STUDY_ARM_1_UID: str
STUDY_ARM_2_UID: str
STUDY_BRANCH_ARM_1_UID: str


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.tests.study.selection.cohorts.negative")
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
    # db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)

    catalogue_name = "SDTM CT"
    library_name = "Sponsor"
    study_uid = "study_root"

    # Create a study element
    element_subtype_codelist = create_codelist(
        "Element Sub Type",
        "CTCodelist_ElementType",
        catalogue_name,
        library_name,
        submission_value="ELEMSTP",
    )
    create_ct_term(
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
    create_ct_term(
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

    codelist = create_codelist(
        name="Arm Type",
        uid="CTCodelist_00004",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="ARMTTP",
    )
    arm_type_1 = create_ct_term(
        name="Arm Type",
        uid="ArmType_0001",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "Arm Type",
            }
        ],
    )
    arm_type_2 = create_ct_term(
        name="Arm Type 2",
        uid="ArmType_0002",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 2,
                "submission_value": "Arm Type 2",
            }
        ],
    )

    arm1 = create_study_arm(
        study_uid=study_uid,
        name="StudyArm_000001",
        short_name="StudyArm_000001",
        code="Arm_code_1",
        description="desc...",
        randomization_group="Arm_randomizationGroup",
        number_of_subjects=100,
        arm_type_uid=arm_type_1.uid,
    )
    global STUDY_ARM_1_UID
    STUDY_ARM_1_UID = arm1.arm_uid

    arm2 = create_study_arm(
        study_uid=study_uid,
        name="StudyArm_000002",
        short_name="StudyArm_000002",
        code="Arm_code_2",
        description="desc...",
        randomization_group="Arm_randomizationGroup_2",
        number_of_subjects=100,
        arm_type_uid=arm_type_2.uid,
    )
    global STUDY_ARM_2_UID
    STUDY_ARM_2_UID = arm2.arm_uid

    _branch_arm = create_study_branch_arm(
        study_uid=study_uid,
        name="Branch_Arm_Name_1",
        short_name="Branch_Arm_Short_Name_1",
        code="Branch_Arm_code_1",
        description="desc...",
        randomization_group="Branch_Arm_randomizationGroup",
        number_of_subjects=100,
        arm_uid=arm1.arm_uid,
    )
    branch_arm = create_study_branch_arm(
        study_uid=study_uid,
        name="Branch_Arm_Name_2",
        short_name="Branch_Arm_Short_Name_2",
        code="Branch_Arm_code_2",
        description="desc...",
        randomization_group="Branch_Arm_randomizationGroup2",
        number_of_subjects=20,
        arm_uid=arm1.arm_uid,
    )
    global STUDY_BRANCH_ARM_1_UID
    STUDY_BRANCH_ARM_1_UID = branch_arm.branch_arm_uid
    _cohorts = [
        create_study_cohort(
            study_uid=study_uid,
            name="Cohort_Name_1",
            short_name="Cohort_Short_Name_1",
            code="Cohort_code_1",
            description="desc...",
            number_of_subjects=100,
            arm_uids=[arm1.arm_uid],
        ),
        create_study_cohort(
            study_uid=study_uid,
            name="Cohort_Name_2",
            short_name="Cohort_Short_Name_2",
            code="Cohort_code_2",
            description="desc...",
            number_of_subjects=100,
            arm_uids=[arm1.arm_uid],
        ),
    ]
    yield

    drop_db("old.json.tests.study.selection.cohorts.negative")


def test_adding_selection8(api_client):
    data = {"name": "Cohort_Name_1", "short_name": "Cohort_Short_Name_1"}
    response = api_client.post("/studies/study_root/study-cohorts", json=data)
    assert_response_status_code(response, 400)
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
    }
    response = api_client.patch(
        "/studies/study_root/study-cohorts/StudyCohort_000001", json=data
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"] is not None
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
    assert res["arm_roots"][0]["arm_uid"] == STUDY_ARM_1_UID
    assert res["arm_roots"][0]["name"] == "StudyArm_000001"
    assert res["arm_roots"][0]["short_name"] == "StudyArm_000001"
    assert res["arm_roots"][0]["code"] == "Arm_code_1"
    assert res["arm_roots"][0]["description"] == "desc..."
    assert res["arm_roots"][0]["randomization_group"] == "Arm_randomizationGroup"
    assert res["arm_roots"][0]["number_of_subjects"] == 100
    assert res["arm_roots"][0]["arm_type"]["term_uid"] == "ArmType_0001"
    assert res["arm_roots"][0]["arm_type"]["term_name"] == "Arm Type"
    assert res["arm_roots"][0]["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res["arm_roots"][0]["arm_type"]["codelist_name"] == "Arm Type"
    assert res["arm_roots"][0]["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res["arm_roots"][0]["arm_type"]["order"] == 1
    assert res["arm_roots"][0]["arm_type"]["submission_value"] == "Arm Type"
    assert res["arm_roots"][0]["arm_type"]["queried_effective_date"] is None
    assert res["arm_roots"][0]["arm_type"]["date_conflict"] is False
    assert res["arm_roots"][0]["start_date"] is not None
    assert res["arm_roots"][0]["author_username"] == "unknown-user@example.com"
    assert res["arm_roots"][0]["end_date"] is None
    assert res["arm_roots"][0]["status"] is None
    assert res["arm_roots"][0]["change_type"] is None
    assert res["arm_roots"][0]["accepted_version"] is False
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 100
    assert res["author_username"] == "unknown-user@example.com"


def test_all_history_of_specific_selection6(api_client):
    response = api_client.get(
        "/studies/study_root/study-cohorts/StudyCohort_000001/audit-trail/"
    )

    res = response.json()

    assert response.status_code == 200
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
    assert res[0]["number_of_subjects"] == 100
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert res[0]["branch_arm_roots_uids"] is None
    assert res[0]["arm_roots_uids"] == ["StudyArm_000001"]
    assert set(res[0]["changes"]) == set(
        [
            "name",
            "short_name",
            "code",
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
    assert res[1]["cohort_uid"] == "StudyCohort_000001"
    assert res[1]["name"] == "Cohort_Name_1"
    assert res[1]["short_name"] == "Cohort_Short_Name_1"
    assert res[1]["code"] == "Cohort_code_1"
    assert res[1]["description"] == "desc..."
    assert res[1]["number_of_subjects"] == 100
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"] is not None
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False
    assert res[1]["branch_arm_roots_uids"] is None
    assert res[1]["arm_roots_uids"] == ["StudyArm_000001"]
    assert res[1]["changes"] == []


def test_patch_specific_patch_a_name_that_is_in_history_not_actual(api_client):
    data = {
        "name": "Cohort_Name_1",
        "short_name": "Cohort_Short_Name_5",
        "code": "Cohort_code_5",
        "description": "desc...",
    }
    response = api_client.patch(
        "/studies/study_root/study-cohorts/StudyCohort_000001", json=data
    )

    res = response.json()

    assert response.status_code == 200
    assert res["study_uid"] == "study_root"
    assert res["order"] == 1
    assert res["study_version"] is not None
    assert res["cohort_uid"] == "StudyCohort_000001"
    assert res["name"] == "Cohort_Name_1"
    assert res["short_name"] == "Cohort_Short_Name_5"
    assert res["code"] == "Cohort_code_5"
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 100
    assert res["branch_arm_roots"] is None
    assert res["arm_roots"][0]["study_uid"] == "study_root"
    assert res["arm_roots"][0]["order"] == 1
    assert res["arm_roots"][0]["arm_uid"] == STUDY_ARM_1_UID
    assert res["arm_roots"][0]["name"] == "StudyArm_000001"
    assert res["arm_roots"][0]["short_name"] == "StudyArm_000001"
    assert res["arm_roots"][0]["code"] == "Arm_code_1"
    assert res["arm_roots"][0]["description"] == "desc..."
    assert res["arm_roots"][0]["randomization_group"] == "Arm_randomizationGroup"
    assert res["arm_roots"][0]["number_of_subjects"] == 100
    assert res["arm_roots"][0]["arm_type"]["term_uid"] == "ArmType_0001"
    assert res["arm_roots"][0]["arm_type"]["term_name"] == "Arm Type"
    assert res["arm_roots"][0]["arm_type"]["codelist_uid"] == "CTCodelist_00004"
    assert res["arm_roots"][0]["arm_type"]["codelist_name"] == "Arm Type"
    assert res["arm_roots"][0]["arm_type"]["codelist_submission_value"] == "ARMTTP"
    assert res["arm_roots"][0]["arm_type"]["order"] == 1
    assert res["arm_roots"][0]["arm_type"]["submission_value"] == "Arm Type"
    assert res["arm_roots"][0]["arm_type"]["queried_effective_date"] is None
    assert res["arm_roots"][0]["arm_type"]["date_conflict"] is False
    assert res["arm_roots"][0]["start_date"] is not None
    assert res["arm_roots"][0]["author_username"] == "unknown-user@example.com"
    assert res["arm_roots"][0]["end_date"] is None
    assert res["arm_roots"][0]["status"] is None
    assert res["arm_roots"][0]["change_type"] is None
    assert res["arm_roots"][0]["accepted_version"] is False
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
    }
    response = api_client.patch(
        "/studies/study_root/study-cohorts/StudyCohort_000001", json=data
    )

    res = response.json()

    assert response.status_code == 400
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
    }
    response = api_client.patch(
        "/studies/study_root/study-cohorts/StudyCohort_000001", json=data
    )

    res = response.json()

    assert response.status_code == 400
    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Value 'Cohort_code_2' in field Cohort code is not unique for the study."
    )
