"""
Tests for /studies/{study_uid}/study-elements endpoints
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
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import CTCodelist
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.api.study_selections.utils import (
    ct_term_retrieval_at_date_test_common,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study: Study
study_element_uid: str
element_subtype: CTTerm
element_subtype_codelist: CTCodelist
initial_ct_term_study_standard_test: ct_term.CTTerm
element_type: CTTerm
test_data_dict: dict[str, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studyelementapi"
    inject_and_clear_db(db_name)
    global test_data_dict
    _, test_data_dict = inject_base_data()
    global element_subtype
    global element_subtype_codelist

    global study
    study = TestUtils.create_study()
    TestUtils.set_study_standard_version(
        study_uid=study.uid,
    )
    ct_term_start_date = datetime(2020, 3, 25, tzinfo=timezone.utc)
    element_subtype_codelist = TestUtils.create_ct_codelist(
        name=settings.study_element_subtype_name,
        sponsor_preferred_name=settings.study_element_subtype_name,
        extensible=True,
        approve=True,
        submission_value=settings.study_element_subtype_cl_submval,
        effective_date=ct_term_start_date,
    )
    element_subtype = TestUtils.create_ct_term(
        codelist_uid=element_subtype_codelist.codelist_uid,
        submission_value=settings.study_element_subtype_name,
        sponsor_preferred_name=settings.study_element_subtype_name,
    )
    global element_type
    element_type_codelist = TestUtils.create_ct_codelist(
        name="Element Type",
        sponsor_preferred_name="Element Type",
        extensible=True,
        approve=True,
        submission_value=settings.study_element_type_cl_submval,
        effective_date=ct_term_start_date,
    )
    element_type = TestUtils.create_ct_term(
        codelist_uid=element_type_codelist.codelist_uid,
        submission_value="Element Type",
        sponsor_preferred_name="Element Type",
    )
    TestUtils.add_ct_term_parent(element_subtype, element_type)

    _catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    catalogue_name = "SDTM CT"
    # Create a study selection
    ct_term_codelist_name = settings.study_element_subtype_name
    ct_term_name = ct_term_codelist_name + " Name"

    global initial_ct_term_study_standard_test
    initial_ct_term_study_standard_test = TestUtils.create_ct_term(
        codelist_uid=element_subtype_codelist.codelist_uid,
        submission_value=ct_term_name,
        sponsor_preferred_name=ct_term_name,
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=ct_term_start_date,
        approve=True,
    )

    # patch the date of the latest HAS_VERSION FINAL relationship so it can be detected by the selected study_standard_Version
    params = {
        "uid": initial_ct_term_study_standard_test.term_uid,
        "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
    }
    # adjust term name start_date of the 1.0 final
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
    # adjust codelist name start and end date
    params["uid"] = element_subtype_codelist.codelist_uid
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
    # adjust codelist attributes start_date of the 1.0 final
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


@pytest.mark.order("last")
def test_integrity_checks_for_all_studies(api_client):
    """
    Test integrity checks for all available studies in the database.

    This test should always be executed at the END to check the health of the remaining database.
    It validates that all studies in the database pass integrity checks after all other tests have run.
    """
    TestUtils.run_integrity_checks_for_all_studies(api_client)


def test_element_modify_actions_on_locked_study(api_client):
    global study_element_uid

    response = api_client.post(
        f"/studies/{study.uid}/study-elements",
        json={
            "name": "Element_Name_1",
            "short_name": "Element_Short_Name_1",
            "element_subtype_uid": element_subtype.term_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["element_type"]["term_uid"] == element_type.term_uid

    # get all elements
    response = api_client.get(
        f"/studies/{study.uid}/study-element/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res
    study_element_uid = res[0]["element_uid"]

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
        f"/studies/{study.uid}/study-elements",
        json={
            "name": "Element_Name_2",
            "short_name": "Element_Short_Name_2",
            "element_subtype_uid": element_subtype.term_uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # edit element
    response = api_client.patch(
        f"/studies/{study.uid}/study-elements/{study_element_uid}",
        json={
            "name": "New_Element_Name_1",
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."
    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-element/audit-trail/",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert old_res == res

    # test cannot delete
    response = api_client.delete(
        f"/studies/{study.uid}/study-elements/{study_element_uid}"
    )
    assert_response_status_code(response, 400)
    assert response.json()["message"] == f"Study with UID '{study.uid}' is locked."


def test_study_element_with_study_element_subtype_relationship(api_client):
    _element_subtype = TestUtils.create_ct_term(
        codelist_uid=element_subtype_codelist.codelist_uid,
        submission_value="test element subtype",
        sponsor_preferred_name="test element subtype",
    )
    TestUtils.add_ct_term_parent(_element_subtype, TestUtils.create_ct_term())

    # get specific study element
    response = api_client.get(
        f"/studies/{study.uid}/study-elements/{study_element_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["element_subtype"]["term_uid"] == element_subtype.term_uid
    before_unlock = res

    # get study element headers
    response = api_client.get(
        f"/studies/{study.uid}/study-elements/headers?field_name=element_subtype.term_uid",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == [element_subtype.term_uid]

    # Unlock -- Study remain unlocked
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

    # edit study element
    response = api_client.patch(
        f"/studies/{study.uid}/study-elements/{study_element_uid}",
        json={"element_subtype_uid": _element_subtype.term_uid},
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["element_subtype"]["term_uid"] == _element_subtype.term_uid

    # get all study elements of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-elements?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock["study_version"] = mock.ANY
    assert res["items"][0] == before_unlock

    # get specific study element of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-elements/{study_element_uid}?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock["study_version"] = mock.ANY
    assert res == before_unlock

    # get study element headers of specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-elements/headers?field_name=element_subtype.term_uid&study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == [element_subtype.term_uid]

    # get all study elements
    response = api_client.get(
        f"/studies/{study.uid}/study-elements",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["items"][0]["element_subtype"]["term_uid"] == _element_subtype.term_uid

    # get specific study element
    response = api_client.get(
        f"/studies/{study.uid}/study-elements/{study_element_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["element_subtype"]["term_uid"] == _element_subtype.term_uid

    # get study elements headers
    response = api_client.get(
        f"/studies/{study.uid}/study-elements/headers?field_name=element_subtype.term_uid",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == [_element_subtype.term_uid]


def test_study_element_version_selecting_ct_package(api_client):
    """change the name of a CTTerm, and verify that the study selection is still set to the old name of the CTTerm when the Sponsor Standard version is set"""
    study_selection_url = "study-elements"
    study_for_ctterm_versioning = TestUtils.create_study()
    response = api_client.post(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_url}",
        json={
            "name": "Element_Name_2",
            "short_name": "Element_Short_Name_2",
            "element_subtype_uid": element_subtype.term_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    study_selection_uid_study_standard_test = res["element_uid"]

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
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_url}/{study_selection_uid_study_standard_test}",
        json={"element_subtype_uid": ctterm_uid},
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["element_subtype"]["term_uid"] == ctterm_uid
    assert res["element_subtype"]["term_name"] == new_ctterm_name

    TestUtils.set_study_standard_version(
        study_uid=study_for_ctterm_versioning.uid,
        package_name="SDTM CT 2020-03-27",
        effective_date=datetime(2020, 3, 27, tzinfo=timezone.utc),
    )

    # get study selection with previous ctterm
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_url}/{study_selection_uid_study_standard_test}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["element_subtype"]["term_uid"] == ctterm_uid
    assert (
        res["element_subtype"]["term_name"]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )

    # edit element
    response = api_client.patch(
        f"/studies/{study_for_ctterm_versioning.uid}/study-elements/{study_selection_uid_study_standard_test}",
        json={
            "name": "New_Element_Name_1",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res["element_subtype"]["term_name"]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )

    # get all elements
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/study-elements/{study_selection_uid_study_standard_test}/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[0]["element_subtype"]["term_name"]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )
    assert res[1]["element_subtype"]["term_name"] == new_ctterm_name

    # get all elements
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/study-element/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[0]["element_subtype"]["term_name"]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )
    assert res[1]["element_subtype"]["term_name"] == new_ctterm_name


def test_study_element_ct_term_retrieval_at_date(api_client):
    """
    Test that any CT Term name fetched in the context of a study selection either:
    * Matches the date of the Study Standard version when available
    * Or the latest final version is returned
    The study selection return model includes a queried_effective_data property to verify this
    """

    study_for_queried_effective_date = TestUtils.create_study()
    study_selection_breadcrumb = "study-elements"
    study_selection_ctterm_keys = "element_subtype"
    study_selection_ctterm_uid_input_key = "element_subtype_uid"

    # Create selection
    response = api_client.post(
        f"/studies/{study_for_queried_effective_date.uid}/{study_selection_breadcrumb}",
        json={
            "name": "Element_Name_2",
            "short_name": "Element_Short_Name_2",
            "element_subtype_uid": element_subtype.term_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res[study_selection_ctterm_keys]["queried_effective_date"] is None
    assert res[study_selection_ctterm_keys]["date_conflict"] is False
    study_selection_uid_study_standard_test = res["element_uid"]

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
def test_get_study_elements_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-elements"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())
