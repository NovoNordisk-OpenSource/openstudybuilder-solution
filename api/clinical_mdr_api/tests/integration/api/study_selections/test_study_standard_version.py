"""
Tests for /studies/{study_uid}/study-standard-versions endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
from typing import Any
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study: Study
standard_version_uid: str
standard_version_type_term: CTTerm
standard_version_type_term2: CTTerm
ct_package_uid: str
ct_package_uid_2: str
ct_package_uid_3: str
test_data_dict: dict[str, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studystandardversionapi"
    inject_and_clear_db(db_name)

    global study
    global test_data_dict
    _, test_data_dict = inject_base_data()

    study = TestUtils.create_study()
    catalogue = "SDTM CT"
    cdisc_package_name = "SDTM CT 2020-03-27"
    cdisc_package_name_2 = "SDTM CT 2020-03-28"
    catalogue_3 = "ADAM CT"
    cdisc_package_name_3 = "ADAM CT 2020-03-27"

    global ct_package_uid
    global ct_package_uid_2
    global ct_package_uid_3

    ct_package_uid = TestUtils.create_ct_package(
        catalogue=catalogue, name=cdisc_package_name, approve_elements=False
    )
    ct_package_uid_2 = TestUtils.create_ct_package(
        catalogue=catalogue, name=cdisc_package_name_2, approve_elements=False
    )
    ct_package_uid_3 = TestUtils.create_ct_package(
        catalogue=catalogue_3, name=cdisc_package_name_3, approve_elements=False
    )
    yield


@pytest.mark.order("last")
def test_integrity_checks_for_all_studies(api_client):
    """
    Test integrity checks for all available studies in the database.

    This test should always be executed at the END to check the health of the remaining database.
    It validates that all studies in the database pass integrity checks after all other tests have run.
    """
    TestUtils.run_integrity_checks_for_all_studies(api_client)


def test_study_standard_version_crud_operations(api_client):
    # get all standard versions
    response = api_client.get(
        "/ct/packages",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert ct_package_uid == res[2]["uid"]
    assert ct_package_uid_2 == res[3]["uid"]
    assert ct_package_uid_3 == res[0]["uid"]
    description = "My description"
    description2 = "Other description"
    description3 = "ADAM description"

    global standard_version_uid
    response = api_client.post(
        f"/studies/{study.uid}/study-standard-versions",
        json={"ct_package_uid": ct_package_uid, "description": description},
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["ct_package"]["uid"] == ct_package_uid
    assert res["description"] == description
    standard_version_uid = res["uid"]

    # CHECK THAT CANNOT CREATE A STUDY STANDARD VERSION FOR THE SAME CATALOGUE
    response = api_client.post(
        f"/studies/{study.uid}/study-standard-versions",
        json={"ct_package_uid": ct_package_uid_2, "description": description2},
    )
    res = response.json()
    assert_response_status_code(response, 409)
    assert (
        res["message"]
        == "Standard Version ('StudyStandardVersion_000002', 'SDTM CT 2020-03-27') already exists for Catalogue with Name 'SDTM CT'."
    )

    response = api_client.post(
        f"/studies/{study.uid}/study-standard-versions",
        json={"ct_package_uid": ct_package_uid_3, "description": description3},
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["ct_package"]["uid"] == ct_package_uid_3
    assert res["description"] == description3

    # get all standard versions
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res) == 2
    assert res[0]["uid"] == standard_version_uid
    assert res[0]["description"] == description

    # # get specific standard versions audit trail
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions/{standard_version_uid}/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)

    # Test patch ct package uid
    # And description not removed - patch and not put
    response = api_client.patch(
        f"/studies/{study.uid}/study-standard-versions/{standard_version_uid}",
        json={
            "ct_package_uid": ct_package_uid_2,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["ct_package"]["uid"] == ct_package_uid_2
    assert res["description"] == description

    # Test patch description
    # And ct package uid not removed - patch and not put
    response = api_client.patch(
        f"/studies/{study.uid}/study-standard-versions/{standard_version_uid}",
        json={
            "description": description2,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["ct_package"]["uid"] == ct_package_uid_2
    assert res["description"] == description2

    # test delete
    response = api_client.delete(
        f"/studies/{study.uid}/study-standard-versions/{standard_version_uid}"
    )
    assert_response_status_code(response, 204)

    # get all standard versions
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions/{standard_version_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == f"The StudyStandardVersion with UID '{standard_version_uid}' doesn't exist."
    )


def test_standard_version_modify_actions_on_locked_study(api_client):
    global standard_version_uid
    response = api_client.post(
        f"/studies/{study.uid}/study-standard-versions",
        json={
            "ct_package_uid": ct_package_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    standard_version_uid = res["uid"]

    # get all standard versions
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res

    # # get all standard versions
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res

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
        f"/studies/{study.uid}/study-standard-versions",
        json={
            "ct_package_uid": ct_package_uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    response = api_client.patch(
        f"/studies/{study.uid}/study-standard-versions/{standard_version_uid}",
        json={
            "ct_package_uid": ct_package_uid_2,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    for i, _ in enumerate(old_res):
        old_res[i]["study_version"] = mock.ANY
    assert old_res == res

    # test cannot delete
    response = api_client.delete(
        f"/studies/{study.uid}/study-standard-versions/{standard_version_uid}"
    )
    assert_response_status_code(response, 400)
    assert response.json()["message"] == f"Study with UID '{study.uid}' is locked."

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

    # test delete
    response = api_client.delete(
        f"/studies/{study.uid}/study-standard-versions/{standard_version_uid}"
    )
    # assert_response_status_code(response, 400)

    # Lock and check automatically creation
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

    # get all the study standard_versions, check the SDTM automatically created
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions",
    )
    assert_response_status_code(response, 200)
    res_old = response.json()
    assert res_old[1]["automatically_created"] is True
    assert "SDTM CT" in res_old[1]["ct_package"]["uid"]


def test_get_standard_version_data_for_specific_study_version(api_client):
    # get the study standard_version for 1st locked: version 1, used for compare later
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions",
    )
    assert_response_status_code(response, 200)
    res_old = response.json()

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

    response = api_client.patch(
        f"/studies/{study.uid}/study-standard-versions/{res_old[0]['uid']}",
        json={
            "ct_package_uid": ct_package_uid_2,
        },
    )
    assert_response_status_code(response, 200)

    # check the study standard_version for version 1 is same as first locked
    res_new = api_client.get(
        f"/studies/{study.uid}/study-standard-versions",
    ).json()
    res_v1 = api_client.get(
        f"/studies/{study.uid}/study-standard-versions?study_value_version=2",
    ).json()
    for i, _ in enumerate(res_old):
        res_old[i]["study_version"] = mock.ANY
    assert res_v1 == res_old
    assert res_v1 != res_new
    response = api_client.get(
        f"/studies/{study.uid}/study-standard-versions?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res[0]["ct_package"]["uid"] == res_v1[0]["ct_package"]["uid"]


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
def test_get_standard_versions_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-standard-versions"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())
