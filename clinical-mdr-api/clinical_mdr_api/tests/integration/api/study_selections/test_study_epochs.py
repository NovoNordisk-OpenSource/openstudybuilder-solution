"""
Tests for /studies/{study_uid}/study-epochs endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

from datetime import datetime, timezone
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api import main
from clinical_mdr_api.models.controlled_terminologies import ct_term
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_study_epoch_codelists_ret_cat_and_lib,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common import config as settings

# Global variables shared between fixtures and tests
study: Study
study_epoch_uid: str
epoch_subtype_uid: str
epoch_subtype2_uid: str

initial_ct_term_study_standard_test: ct_term.CTTerm
epoch_epoch: ct_term.CTTerm


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(main.app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studyepochapi"
    inject_and_clear_db(db_name)
    inject_base_data()
    global epoch_subtype_uid
    global epoch_subtype2_uid
    global study
    study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=study.uid)

    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    create_study_epoch_codelists_ret_cat_and_lib()

    epoch_subtype_uid = "EpochSubType_0001"
    epoch_subtype2_uid = "EpochSubType_0002"

    catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    # Create a study selection
    ct_term_codelist_name = settings.STUDY_EPOCH_SUBTYPE_NAME
    ct_term_name = ct_term_codelist_name + " Name For StudyStandardVersioning test"
    ct_term_start_date = datetime(2020, 3, 25, tzinfo=timezone.utc)

    epoch_type_term_name = "Epoch Type for StudyStandardVersion"
    epoch_type_standard_version = TestUtils.create_ct_term(
        codelist_uid="CTCodelist_00002",
        name_submission_value=epoch_type_term_name,
        sponsor_preferred_name=epoch_type_term_name,
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=ct_term_start_date,
        approve=True,
    )

    global initial_ct_term_study_standard_test
    initial_ct_term_study_standard_test = TestUtils.create_ct_term(
        codelist_uid="CTCodelist_00003",  # ct_term_codelist.codelist_uid,
        name_submission_value=ct_term_name,
        sponsor_preferred_name=ct_term_name,
        order=2,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=ct_term_start_date,
        approve=True,
    )

    TestUtils.add_ct_term_parent(
        term=initial_ct_term_study_standard_test,
        parent_uid=epoch_type_standard_version.term_uid,
        relationship_type="type",
    )

    epoch_term_name = "Epoch Epoch for StudyStandardVersion"
    global epoch_epoch
    epoch_epoch = TestUtils.create_ct_term(
        codelist_uid="C99079",
        name_submission_value=epoch_term_name,
        sponsor_preferred_name=epoch_term_name,
        order=3,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=ct_term_start_date,
        approve=True,
    )
    TestUtils.add_ct_term_parent(
        term=epoch_epoch,
        parent_uid=initial_ct_term_study_standard_test.term_uid,
        relationship_type="subtype",
    )

    # patch the date of the latest HAS_VERSION FINAL relationship so it can be detected by the selected study_standard_Version
    params = {
        "uids": [
            initial_ct_term_study_standard_test.term_uid,
            epoch_epoch.term_uid,
            epoch_type_standard_version.term_uid,
        ],
        "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
    }
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTTermNameRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        n.uid IN $uids AND EXISTS((ct_name)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )

    yield


def test_epoch_modify_actions_on_locked_study(api_client):
    global study_epoch_uid
    response = api_client.post(
        f"/studies/{study.uid}/study-epochs",
        json={
            "study_uid": study.uid,
            "epoch_subtype": epoch_subtype_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # get all epochs
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res
    study_epoch_uid = res[0]["uid"]

    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks",
        json={"change_description": "Lock 1"},
    )
    assert_response_status_code(response, 201)

    response = api_client.post(
        f"/studies/{study.uid}/study-epochs",
        json={
            "study_uid": study.uid,
            "epoch_subtype": epoch_subtype2_uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # edit epoch
    response = api_client.patch(
        f"/studies/{study.uid}/study-epochs/{study_epoch_uid}",
        json={
            "study_uid": study.uid,
            "name": "New_epoch_Name_1",
            "change_description": "this is a changing test",
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/audit-trail/",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    for i, _ in enumerate(old_res):
        old_res[i]["study_version"] = mock.ANY
    assert old_res == res

    # test cannot delete
    response = api_client.delete(f"/studies/{study.uid}/study-epochs/{study_epoch_uid}")
    assert_response_status_code(response, 400)
    assert response.json()["message"] == f"Study with UID '{study.uid}' is locked."


def test_study_epoch_with_study_epoch_subtype_relationship(api_client):
    # get specific study epoch
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/{study_epoch_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["epoch_subtype_ctterm"]["term_uid"] == epoch_subtype_uid
    before_unlock = res

    # get study epoch headers
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/headers?field_name=epoch_subtype_ctterm.term_uid",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == [epoch_subtype_uid]

    # Unlock -- Study remain unlocked
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert_response_status_code(response, 200)

    # edit study epoch
    response = api_client.patch(
        f"/studies/{study.uid}/study-epochs/{study_epoch_uid}",
        json={
            "study_uid": study.uid,
            "epoch_subtype": epoch_subtype2_uid,
            "change_description": "new epoch subtype",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["epoch_subtype_ctterm"]["term_uid"] == epoch_subtype2_uid

    # get all study epochs of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock["study_version"] = mock.ANY
    assert res["items"][0] == before_unlock

    # get specific study epoch of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/{study_epoch_uid}?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == before_unlock

    # get study epoch headers of specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/headers?field_name=epoch_subtype_ctterm.term_uid&study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == [epoch_subtype_uid]

    # get all study epochs
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["items"][0]["epoch_subtype_ctterm"]["term_uid"] == epoch_subtype2_uid

    # get specific study epoch
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/{study_epoch_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["epoch_subtype_ctterm"]["term_uid"] == epoch_subtype2_uid

    # get study epochs headers
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/headers?field_name=epoch_subtype_ctterm.term_uid",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == [epoch_subtype2_uid]


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
def test_get_study_epochs_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-epochs"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())


def test_study_epoch_order_when_epoch_get_deleted_or_modified(api_client):
    study_for_tests = TestUtils.create_study()
    response = api_client.post(
        f"/studies/{study_for_tests.uid}/study-epochs",
        json={
            "study_uid": study_for_tests.uid,
            "epoch_subtype": epoch_subtype_uid,
        },
    )
    epoch_subtype_1 = response.json()
    assert_response_status_code(response, 201)
    assert epoch_subtype_1["order"] == 1
    assert epoch_subtype_1["epoch_ctterm"]["sponsor_preferred_name"] == "Epoch Subtype"

    response = api_client.post(
        f"/studies/{study_for_tests.uid}/study-epochs",
        json={
            "study_uid": study_for_tests.uid,
            "epoch_subtype": epoch_subtype_uid,
        },
    )
    epoch_subtype_2 = response.json()
    assert_response_status_code(response, 201)
    assert epoch_subtype_2["order"] == 2
    assert (
        epoch_subtype_2["epoch_ctterm"]["sponsor_preferred_name"] == "Epoch Subtype 2"
    )

    # Deleting an Epoch from the same Subtype
    response = api_client.delete(
        f"/studies/{study_for_tests.uid}/study-epochs/{epoch_subtype_1['uid']}",
    )
    assert_response_status_code(response, 204)
    response = api_client.get(
        f"/studies/{study_for_tests.uid}/study-epochs/{epoch_subtype_2['uid']}",
    )
    old_subtype_2_new_subtype_1 = response.json()
    assert_response_status_code(response, 200)
    assert old_subtype_2_new_subtype_1["order"] == 1
    assert (
        old_subtype_2_new_subtype_1["epoch_ctterm"]["sponsor_preferred_name"]
        == "Epoch Subtype"
    )

    response = api_client.post(
        f"/studies/{study_for_tests.uid}/study-epochs",
        json={
            "study_uid": study_for_tests.uid,
            "epoch_subtype": epoch_subtype2_uid,
        },
    )
    epoch_subtype_2_1 = response.json()
    assert_response_status_code(response, 201)
    assert epoch_subtype_2_1["order"] == 2
    assert (
        epoch_subtype_2_1["epoch_ctterm"]["sponsor_preferred_name"] == "Epoch Subtype1"
    )

    response = api_client.delete(
        f"/studies/{study_for_tests.uid}/study-epochs/{old_subtype_2_new_subtype_1['uid']}",
    )
    assert_response_status_code(response, 204)

    response = api_client.get(
        f"/studies/{study_for_tests.uid}/study-epochs/{epoch_subtype_2_1['uid']}",
    )
    assert_response_status_code(response, 200)
    epoch_subtype_2_1 = response.json()
    assert epoch_subtype_2_1["order"] == 1
    assert (
        epoch_subtype_2_1["epoch_ctterm"]["sponsor_preferred_name"] == "Epoch Subtype1"
    )

    response = api_client.get(
        f"/studies/{study_for_tests.uid}/study-epochs",
    )
    assert_response_status_code(response, 200)
    all_epochs = response.json()["items"]
    assert len(all_epochs) == 1

    response = api_client.post(
        f"/studies/{study_for_tests.uid}/study-epochs",
        json={
            "study_uid": study_for_tests.uid,
            "epoch_subtype": epoch_subtype2_uid,
        },
    )
    epoch_subtype_2_2 = response.json()
    assert_response_status_code(response, 201)
    assert epoch_subtype_2_2["order"] == 2
    assert (
        epoch_subtype_2_2["epoch_ctterm"]["sponsor_preferred_name"]
        == "Epoch Subtype1 2"
    )

    response = api_client.get(
        f"/studies/{study_for_tests.uid}/study-epochs/{epoch_subtype_2_1['uid']}",
    )
    assert_response_status_code(response, 200)
    epoch_subtype_2_1 = response.json()
    assert epoch_subtype_2_1["order"] == 1
    assert (
        epoch_subtype_2_1["epoch_ctterm"]["sponsor_preferred_name"]
        == "Epoch Subtype1 1"
    )

    response = api_client.post(
        f"/studies/{study_for_tests.uid}/study-epochs",
        json={
            "study_uid": study_for_tests.uid,
            "epoch_subtype": epoch_subtype2_uid,
        },
    )
    epoch_subtype_2_3 = response.json()
    assert_response_status_code(response, 201)
    assert epoch_subtype_2_3["order"] == 3
    assert (
        epoch_subtype_2_3["epoch_ctterm"]["sponsor_preferred_name"]
        == "Epoch Subtype1 3"
    )

    response = api_client.patch(
        f"/studies/{study_for_tests.uid}/study-epochs/{epoch_subtype_2_1['uid']}/order/2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["order"] == 3

    response = api_client.get(
        f"/studies/{study_for_tests.uid}/study-epochs",
    )
    assert_response_status_code(response, 200)
    all_epochs = response.json()["items"]
    assert len(all_epochs) == 3
    assert all_epochs[0]["uid"] == epoch_subtype_2_2["uid"]
    assert all_epochs[0]["order"] == 1
    assert all_epochs[1]["uid"] == epoch_subtype_2_3["uid"]
    assert all_epochs[1]["order"] == 2
    assert all_epochs[2]["uid"] == epoch_subtype_2_1["uid"]
    assert all_epochs[2]["order"] == 3


def test_study_epoch_version_selecting_ct_package(api_client):
    """change the name of a CTTerm, and verify that the study selection is still set to the old name of the CTTerm when the Sponsor Standard version is set"""
    study_selection_breadcrumb = "study-epochs"
    study_selection_ctterm_uid_input_key = "epoch_subtype"
    study_selection_ctterm_keys = "epoch_subtype_ctterm"
    # study_selection_ctterm_uid_key =
    study_selection_ctterm_name_key = "sponsor_preferred_name"
    study_for_ctterm_versioning = TestUtils.create_study()
    response = api_client.post(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}",
        json={
            "study_uid": study_for_ctterm_versioning.uid,
            study_selection_ctterm_uid_input_key: epoch_subtype_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    study_selection_uid_study_standard_test = res["uid"]
    assert res["order"] == 1
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_name_key]
        == "Epoch Subtype"
    )

    # edit ctterm
    new_ctterm_name = "new ctterm name"
    ctterm_uid = initial_ct_term_study_standard_test.term_uid
    # change ctterm name and approve the version
    response = api_client.post(
        f"/ct/terms/{ctterm_uid}/names/versions",
    )
    assert_response_status_code(response, 201)
    response = api_client.patch(
        f"/ct/terms/{ctterm_uid}/names",
        json={
            "sponsor_preferred_name": new_ctterm_name,
            "sponsor_preferred_name_sentence_case": new_ctterm_name,
            "change_description": "string",
        },
    )
    response = api_client.post(f"/ct/terms/{ctterm_uid}/names/approvals")
    assert_response_status_code(response, 201)

    # get study selection with ctterm latest
    response = api_client.patch(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
        json={
            "study_uid": study_for_ctterm_versioning.uid,
            "change_description": "this is a changing test",
            study_selection_ctterm_uid_input_key: ctterm_uid,
            "epoch": epoch_epoch.term_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    # assert res[study_selection_ctterm_name_key] == ctterm_uid
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_name_key]
        == new_ctterm_name
    )

    TestUtils.set_study_standard_version(
        study_uid=study_for_ctterm_versioning.uid,
        package_name="SDTM CT 2020-03-27",
        effective_date=datetime(2020, 3, 27, tzinfo=timezone.utc),
    )

    # get study selection with previous ctterm
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    # assert res[study_selection_ctterm_uid_key] == ctterm_uid
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_name_key]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )

    # edit epoch
    response = api_client.patch(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
        json={
            "study_uid": study_for_ctterm_versioning.uid,
            "name": "New_epoch_Name_1",
            "change_description": "this is a changing test",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_name_key]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )

    # get versions of objective
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[0][study_selection_ctterm_keys][study_selection_ctterm_name_key]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )
    assert (
        res[1][study_selection_ctterm_keys][study_selection_ctterm_name_key]
        == new_ctterm_name
    )

    # get all objectives
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[0][study_selection_ctterm_keys][study_selection_ctterm_name_key]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )
    assert (
        res[1][study_selection_ctterm_keys][study_selection_ctterm_name_key]
        == new_ctterm_name
    )


def test_study_epoch_audit_trail(api_client):
    # get specific study epoch audit trail
    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/{study_epoch_uid}/audit-trail",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res) == 4
