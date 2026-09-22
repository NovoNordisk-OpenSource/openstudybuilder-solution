"""
Tests for /studies/{study_uid}/study-arms endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
from datetime import datetime, timezone
from typing import Any
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.models.controlled_terminologies import ct_term
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.api.study_selections.utils import (
    ct_term_retrieval_at_date_test_common,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

study: Study
arm_uid: str
initial_ct_term_study_standard_test: ct_term.CTTerm
investigational_arm: ct_term.CTTerm
test_data_dict: dict[str, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studyarmapi"
    inject_and_clear_db(db_name)

    global study, test_data_dict
    study, test_data_dict = inject_base_data()

    _catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    catalogue_name = "SDTM CT"
    # Create a study selection
    ct_term_codelist = create_codelist(
        "Arm Type",
        "CTCodelist_ArmType",
        catalogue_name,
        library_name,
        submission_value="ARMTTP",
    )

    global initial_ct_term_study_standard_test
    ct_term_name = "Arm Type"
    initial_ct_term_study_standard_test = TestUtils.create_ct_term(
        codelist_uid=ct_term_codelist.codelist_uid,
        submission_value=ct_term_name,
        sponsor_preferred_name=ct_term_name,
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=datetime(2020, 3, 25, tzinfo=timezone.utc),
        approve=True,
    )
    global investigational_arm
    ct_term_name = "Investigational Arm"
    investigational_arm = TestUtils.create_ct_term(
        codelist_uid=ct_term_codelist.codelist_uid,
        submission_value=ct_term_name,
        sponsor_preferred_name=ct_term_name,
        order=2,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=datetime(2020, 3, 25, tzinfo=timezone.utc),
        approve=True,
    )

    # patch the date of the latest HAS_VERSION FINAL relationship so it can be detected by the selected study_standard_Version
    params = {
        "uid": initial_ct_term_study_standard_test.term_uid,
        "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
    }
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTTermNameRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        n.uid =$uid AND EXISTS((ct_name)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )

    params = {
        "uid": ct_term_codelist.codelist_uid,
        "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
    }
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTCodelistNameRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        n.uid =$uid AND EXISTS((ct_name)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_ATTRIBUTES_ROOT]-(ct_attrs:CTCodelistAttributesRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        n.uid =$uid AND EXISTS((ct_attrs)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )
    yield
    # drop_db(db_name)


@pytest.mark.order("last")
def test_integrity_checks_for_all_studies(api_client):
    """
    Test integrity checks for all available studies in the database.

    This test should always be executed at the END to check the health of the remaining database.
    It validates that all studies in the database pass integrity checks after all other tests have run.
    """
    TestUtils.run_integrity_checks_for_all_studies(api_client)


def test_arm_modify_actions_on_locked_study(api_client):
    global arm_uid
    response = api_client.post(
        f"/studies/{study.uid}/study-arms",
        json={
            "name": "Arm_Name_1",
            "short_name": "Arm_Short_Name_1",
            "label": "Arm_Label_1",
            "code": "Arm_code_1",
            "description": "desc...",
            "randomization_group": "Randomization_Group_1",
            "number_of_subjects": 1,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # get all arms
    response = api_client.get(
        f"/studies/{study.uid}/study-arms/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res
    arm_uid = res[0]["arm_uid"]

    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks",
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.post(
        f"/studies/{study.uid}/study-arms",
        json={
            "name": "Arm_Name_2",
            "short_name": "Arm_Short_Name_2",
            "label": "Arm_Label_2",
            "code": "Arm_code_2",
            "description": "desc...",
            "randomization_group": "Randomization_Group_2",
            "number_of_subjects": 2,
        },
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert res["message"] == f"Study with UID '{study.uid}' is locked."
    # edit arm
    response = api_client.patch(
        f"/studies/{study.uid}/study-arms/{arm_uid}",
        json={
            "name": "New_Arm_Name_1",
        },
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-arms/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert old_res == res

    # test cannot delete
    response = api_client.delete(f"/studies/{study.uid}/study-arms/{arm_uid}")
    assert_response_status_code(response, 400)
    assert response.json()["message"] == f"Study with UID '{study.uid}' is locked."


def test_study_arm_previous_study_version(api_client):
    # get specific arm
    response = api_client.get(
        f"/studies/{study.uid}/study-arms/{arm_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock = res

    # Unlock
    response = api_client.post(
        f"/studies/{study.uid}/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": test_data_dict["reason_for_unlock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # edit arm
    response = api_client.patch(
        f"/studies/{study.uid}/study-arms/{arm_uid}",
        json={
            "name": "New_Arm_Name_1",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)

    # get all arm of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-arms?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock["study_version"] = mock.ANY
    assert res["items"][0] == before_unlock


def test_study_arm_type_version_selecting_ct_package(api_client):
    """change the name of a CTTerm, and verify that the study selection is still set to the old name of the CTTerm when the Sponsor Standard version is set"""
    # edit ctterm
    new_ctterm_name = "new ctterm name"
    # change activity name and approve the version
    response = api_client.post(
        f"/ct/terms/{initial_ct_term_study_standard_test.term_uid}/names/versions",
    )
    assert_response_status_code(response, 201)
    response = api_client.patch(
        f"/ct/terms/{initial_ct_term_study_standard_test.term_uid}/names",
        json={
            "sponsor_preferred_name": new_ctterm_name,
            "sponsor_preferred_name_sentence_case": new_ctterm_name,
            "change_description": "string",
        },
    )
    response = api_client.post(
        f"/ct/terms/{initial_ct_term_study_standard_test.term_uid}/names/approvals"
    )
    assert_response_status_code(response, 201)

    # get study selection with ctterm latest
    suffix_txt = "ct_package"
    response = api_client.post(
        f"/studies/{study.uid}/study-arms",
        json={
            "name": "Arm_Name_1" + suffix_txt,
            "short_name": "Arm_Short_Name_1" + suffix_txt,
            "label": "Arm_Label_1" + suffix_txt,
            "code": "Arm_code_1" + suffix_txt,
            "description": "desc..." + suffix_txt,
            "randomization_group": "Randomization_Group_1" + suffix_txt,
            "number_of_subjects": 1,
            "arm_type_uid": initial_ct_term_study_standard_test.term_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["arm_type"]["term_name"] == new_ctterm_name
    study_selection_uid_study_standard_test = res["arm_uid"]

    ct_package_uid = TestUtils.create_ct_package(
        name="SDTM CT 2020-03-27",
        approve_elements=False,
        effective_date=datetime(2020, 3, 27, tzinfo=timezone.utc),
    )

    # Patch study standard version created in inject_base_data
    response = api_client.patch(
        f"/studies/{study.uid}/study-standard-versions/StudyStandardVersion_000001",
        json={
            "ct_package_uid": ct_package_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["ct_package"]["uid"] == ct_package_uid

    # get study selection with previous ctterm
    response = api_client.get(
        f"/studies/{study.uid}/study-arms/{study_selection_uid_study_standard_test}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res["arm_type"]["term_name"]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )

    # edit arm
    response = api_client.patch(
        f"/studies/{study.uid}/study-arms/{study_selection_uid_study_standard_test}",
        json={
            "name": "Patch for checking audit trail",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res["arm_type"]["term_name"]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )

    # get all arms
    response = api_client.get(
        f"/studies/{study.uid}/study-arms/{study_selection_uid_study_standard_test}/audit-trail/",
    )
    print("-------")
    print(response.json())
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[0]["arm_type"]["term_name"]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )
    assert res[1]["arm_type"]["term_name"] == new_ctterm_name

    # get all arms
    response = api_client.get(
        f"/studies/{study.uid}/study-arms/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[2]["arm_type"]["term_name"]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )
    assert res[3]["arm_type"]["term_name"] == new_ctterm_name


def test_study_arm_ct_term_retrieval_at_date(api_client):
    """
    Test that any CT Term name fetched in the context of a study selection either:
    * Matches the date of the Study Standard version when available
    * Or the latest final version is returned
    The study selection return model includes a queried_effective_data property to verify this
    """

    study_for_queried_effective_date = TestUtils.create_study()
    study_selection_breadcrumb = "study-arms"
    study_selection_ctterm_keys = "arm_type"
    study_selection_ctterm_uid_input_key = "arm_type_uid"
    suffix_txt = "retrieval_at_date"

    # Create selection
    response = api_client.post(
        f"/studies/{study_for_queried_effective_date.uid}/{study_selection_breadcrumb}",
        json={
            "name": "Arm_Name_1" + suffix_txt,
            "short_name": "Arm_Short_Name_1" + suffix_txt,
            "label": "Arm_Label_1" + suffix_txt,
            "code": "Arm_code_1" + suffix_txt,
            "description": "desc..." + suffix_txt,
            "randomization_group": "Randomization_Group_1" + suffix_txt,
            "number_of_subjects": 1,
            study_selection_ctterm_uid_input_key: initial_ct_term_study_standard_test.term_uid,
        },
    )
    print("###########")
    print(response.json())
    res = response.json()
    assert_response_status_code(response, 201)
    assert res[study_selection_ctterm_keys]["queried_effective_date"] is None
    # assert res[study_selection_ctterm_keys]["date_conflict"] is False
    study_selection_uid_study_standard_test = res["arm_uid"]

    ct_term_retrieval_at_date_test_common(
        api_client,
        study_selection_breadcrumb=study_selection_breadcrumb,
        study_selection_ctterm_uid_input_key=study_selection_ctterm_uid_input_key,
        study_selection_ctterm_keys=study_selection_ctterm_keys,
        study_for_queried_effective_date=study_for_queried_effective_date,
        initial_ct_term_study_standard_test=initial_ct_term_study_standard_test,
        study_selection_uid_study_standard_test=study_selection_uid_study_standard_test,
    )


@pytest.mark.parametrize(
    "export_format",
    [
        pytest.param("text/csv"),
        pytest.param("text/xml"),
        pytest.param(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    ],
)
def test_get_study_arms_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-arms"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())


def test_batch_operations(api_client):
    test_study = TestUtils.create_study()
    arm_name_1 = "Arm_Name_1"
    arm_label_1 = "Arm_Label_1"
    arm_name_2 = "Arm_Name_2"
    arm_label_2 = "Arm_Label_2"
    response = api_client.post(
        f"/studies/{test_study.uid}/study-arms/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "name": arm_name_1,
                    "short_name": "Arm_Short_Name_1",
                    "label": arm_label_1,
                    "code": "Arm_code_1",
                    "description": "desc...",
                    "randomization_group": "Randomization_Group_1",
                    "number_of_subjects": 1,
                    "merge_branch_for_this_arm_for_sdtm_adam": True,
                },
            },
            {
                "method": "POST",
                "content": {
                    "name": arm_name_2,
                    "short_name": "Arm_Short_Name_2",
                    "code": "Arm_code_2",
                    "label": arm_label_2,
                    "description": "desc...",
                    "randomization_group": "Randomization_Group_2",
                    "number_of_subjects": 2,
                    "merge_branch_for_this_arm_for_sdtm_adam": False,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert res[0]["response_code"] == 201
    assert res[0]["content"]["name"] == arm_name_1
    assert res[0]["content"]["label"] == arm_label_1
    assert res[0]["content"]["merge_branch_for_this_arm_for_sdtm_adam"] is True
    assert res[1]["response_code"] == 201
    assert res[1]["content"]["name"] == arm_name_2
    assert res[1]["content"]["label"] == arm_label_2
    assert res[1]["content"]["merge_branch_for_this_arm_for_sdtm_adam"] is False
    study_arm_1_uid = res[0]["content"]["arm_uid"]
    study_arm_2_uid = res[1]["content"]["arm_uid"]

    response = api_client.get(f"/studies/{test_study.uid}/study-arms")
    assert_response_status_code(response, 200)
    study_arms = response.json()["items"]
    assert len(study_arms) == 2

    assert study_arms[0]["name"] == arm_name_1
    assert study_arms[1]["name"] == arm_name_2

    response = api_client.post(
        f"/studies/{test_study.uid}/study-arms/batch",
        json=[
            {
                "method": "PATCH",
                "content": {
                    "arm_uid": study_arm_1_uid,
                    "name": arm_name_2,
                },
            },
        ],
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == f"Value '{arm_name_2}' in field Arm name is not unique for the study."
    )

    response = api_client.post(
        f"/studies/{test_study.uid}/study-arms/batch",
        json=[
            {
                "method": "PATCH",
                "content": {
                    "arm_uid": study_arm_1_uid,
                    "name": arm_name_2,
                },
            },
            {
                "method": "PATCH",
                "content": {
                    "arm_uid": study_arm_2_uid,
                    "name": arm_name_1,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert res[0]["response_code"] == 200
    assert res[0]["content"]["name"] == arm_name_2
    assert res[1]["response_code"] == 200
    assert res[1]["content"]["name"] == arm_name_1


def test_study_arm_delete_cascade_deletes_study_branch_arms(api_client):
    test_study = TestUtils.create_study()

    study_arm = TestUtils.create_study_arm(
        study_uid=test_study.uid,
        name="test_arm",
        short_name="test_arm",
    )

    TestUtils.create_study_branch_arm(
        study_uid=test_study.uid,
        name="Unique branch arm name1",
        short_name="BranchArm_Short_Name_1",
        code="BranchArm_code_1",
        randomization_group="Randomization_Group_1",
        number_of_subjects=5,
        study_arm_uid=study_arm.arm_uid,
    )
    TestUtils.create_study_branch_arm(
        study_uid=test_study.uid,
        name="Unique branch arm name2",
        short_name="BranchArm_Short_Name_2",
        code="BranchArm_code_2",
        randomization_group="Randomization_Group_2",
        number_of_subjects=10,
        study_arm_uid=study_arm.arm_uid,
    )
    response = api_client.get(f"/studies/{test_study.uid}/study-branch-arms")
    assert_response_status_code(response, 200)
    assert len(response.json()["items"]) == 2

    response = api_client.delete(
        f"/studies/{test_study.uid}/study-arms/{study_arm.arm_uid}"
    )
    assert_response_status_code(response, 204)

    # Verify the StudyArm is deleted
    response = api_client.get(f"/studies/{test_study.uid}/study-arms")
    assert_response_status_code(response, 200)
    assert len(response.json()["items"]) == 0

    # Verify that StudyBranchArms are cascade deleted
    response = api_client.get(f"/studies/{test_study.uid}/study-branch-arms")
    assert_response_status_code(response, 200)
    assert len(response.json()["items"]) == 0


def test_study_arm_is_not_updated_when_same_payload_is_sent(api_client):
    test_study = TestUtils.create_study()

    test_arm = TestUtils.create_study_arm(
        study_uid=test_study.uid,
        arm_type_uid=investigational_arm.term_uid,
        name="Arm 1 name",
        short_name="Arm 1 short name",
        label="Arm 1 label",
        description="Arm 1 description",
    )

    # edit arm
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-arms/{test_arm.arm_uid}",
        json={
            "name": "Arm 1 name",
            "short_name": "Arm 1 short name",
            "label": "Arm 1 label",
            "description": "Arm 1 description",
            "arm_type_uid": investigational_arm.term_uid,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["name"] == "Arm 1 name"
    assert res["short_name"] == "Arm 1 short name"
    assert res["label"] == "Arm 1 label"
    assert res["description"] == "Arm 1 description"
    assert res["arm_type"]["term_uid"] == investigational_arm.term_uid

    # get all arms
    response = api_client.get(
        f"/studies/{test_study.uid}/study-arms/{test_arm.arm_uid}/audit-trail",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == 1
