# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_PACKAGE_CYPHER_CDISC_CT,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.listing.cdisc.ct.val")
    db.cypher_query(STARTUP_CT_PACKAGE_CYPHER_CDISC_CT)

    yield

    drop_db("old.json.test.listing.cdisc.ct.val")


def test_no_date_specified_sorting_by_ct_scope_ct_ver_pkg_nm_ct_cd_list_submval_ct_cd(
    api_client,
):
    response = api_client.get(
        "/listings/libraries/all/gcmd/cdisc-ct-val?sort_by=%7B%22ct_scope%22%3Atrue%2C%20%22ct_ver%22%3Atrue%2C%20%22pkg_nm%22%3Atrue%2C%20%22ct_cd_list_submval%22%3Atrue%2C%20%22ct_cd%22%3Atrue%7D"
    )

    assert_response_status_code(response, 200)

    res = response.json()
    import json

    print(json.dumps(res, indent=2))

    assert res["items"][0]["ct_cd"] == "concept_id1"
    assert res["items"][0]["ct_cd_list_submval"] == "old_submission_value1"
    assert res["items"][0]["ct_scope"] == "catalogue"
    assert res["items"][0]["ct_submval"] == "submission_value1"
    assert res["items"][0]["ct_ver"] == "2020-03-27"
    assert res["items"][0]["definition"] == "definition1"
    assert res["items"][0]["nci_pref_term"] == "pref_term1"
    assert res["items"][0]["pkg_nm"] == "old_package"
    assert res["items"][0]["synonyms"] == "syn1;syn2"
    assert res["items"][1]["ct_cd"] == "concept_id2"
    assert res["items"][1]["ct_cd_list_submval"] == "old_submission_value2"
    assert res["items"][1]["ct_scope"] == "catalogue"
    assert res["items"][1]["ct_submval"] == "submission_value2"
    assert res["items"][1]["ct_ver"] == "2020-03-27"
    assert res["items"][1]["definition"] == "definition2"
    assert res["items"][1]["nci_pref_term"] == "pref_term2"
    assert res["items"][1]["pkg_nm"] == "old_package"
    assert res["items"][1]["synonyms"] == "syn"
    assert res["items"][2]["ct_cd"] == "concept_id3"
    assert res["items"][2]["ct_cd_list_submval"] == "new_submission_value"
    assert res["items"][2]["ct_scope"] == "catalogue"
    assert res["items"][2]["ct_submval"] == "submission_value3"
    assert res["items"][2]["ct_ver"] == "2020-06-26"
    assert res["items"][2]["definition"] == "definition3"
    assert res["items"][2]["nci_pref_term"] == "pref_term3"
    assert res["items"][2]["pkg_nm"] == "new_package"
    assert res["items"][2]["synonyms"] is None
    assert res["items"][3]["ct_cd"] == "concept_id4"
    assert res["items"][3]["ct_cd_list_submval"] == "new_submission_value"
    assert res["items"][3]["ct_scope"] == "catalogue"
    assert res["items"][3]["ct_submval"] == "submission_value4"
    assert res["items"][3]["ct_ver"] == "2020-06-26"
    assert res["items"][3]["definition"] == "definition4"
    assert res["items"][3]["nci_pref_term"] == "pref_term4"
    assert res["items"][3]["pkg_nm"] == "new_package"
    assert res["items"][3]["synonyms"] == "syn1;syn2;syn3"
    assert res["items"][4]["ct_cd"] == "concept_id"
    assert res["items"][4]["ct_cd_list_submval"] == "submission_value1"
    assert res["items"][4]["ct_scope"] == "catalogue2"
    assert res["items"][4]["ct_submval"] == "submission_value"
    assert res["items"][4]["ct_ver"] == "2020-06-26"
    assert res["items"][4]["definition"] == "definition"
    assert res["items"][4]["nci_pref_term"] == "pref_term"
    assert res["items"][4]["pkg_nm"] == "package1"
    assert res["items"][4]["synonyms"] == "syn1;syn2"
    assert res["items"][5]["ct_cd"] == "concept_id2"
    assert res["items"][5]["ct_cd_list_submval"] == "submission_value2"
    assert res["items"][5]["ct_scope"] == "catalogue3"
    assert res["items"][5]["ct_submval"] == "submission_value2"
    assert res["items"][5]["ct_ver"] == "2020-06-26"
    assert res["items"][5]["definition"] == "definition2"
    assert res["items"][5]["nci_pref_term"] == "pref_term2"
    assert res["items"][5]["pkg_nm"] == "package2"
    assert res["items"][5]["synonyms"] == "syn1;syn2"


def test_date_specified_filtering_on_catalogue2(api_client):
    response = api_client.get(
        "/listings/libraries/all/gcmd/cdisc-ct-val?catalogue_name=catalogue2,catalogue3&sort_by=%7B%22ct_scope%22%3Atrue%2C%20%22ct_ver%22%3Atrue%2C%20%22pkg_nm%22%3Atrue%2C%20%22ct_cd_list_submval%22%3Atrue%2C%20%22ct_cd%22%3Atrue%7D"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["ct_cd"] == "concept_id"
    assert res["items"][0]["ct_cd_list_submval"] == "submission_value1"
    assert res["items"][0]["ct_scope"] == "catalogue2"
    assert res["items"][0]["ct_submval"] == "submission_value"
    assert res["items"][0]["ct_ver"] == "2020-06-26"
    assert res["items"][0]["definition"] == "definition"
    assert res["items"][0]["nci_pref_term"] == "pref_term"
    assert res["items"][0]["pkg_nm"] == "package1"
    assert res["items"][0]["synonyms"] == "syn1;syn2"
    assert res["items"][1]["ct_cd"] == "concept_id2"
    assert res["items"][1]["ct_cd_list_submval"] == "submission_value2"
    assert res["items"][1]["ct_scope"] == "catalogue3"
    assert res["items"][1]["ct_submval"] == "submission_value2"
    assert res["items"][1]["ct_ver"] == "2020-06-26"
    assert res["items"][1]["definition"] == "definition2"
    assert res["items"][1]["nci_pref_term"] == "pref_term2"
    assert res["items"][1]["pkg_nm"] == "package2"
    assert res["items"][1]["synonyms"] == "syn1;syn2"


def test_filtering_on_pkg_nm1(api_client):
    response = api_client.get(
        "/listings/libraries/all/gcmd/cdisc-ct-val?package=new_package&sort_by=%7B%22ct_scope%22%3Atrue%2C%20%22ct_ver%22%3Atrue%2C%20%22pkg_nm%22%3Atrue%2C%20%22ct_cd_list_submval%22%3Atrue%2C%20%22ct_cd%22%3Atrue%7D"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["ct_cd"] == "concept_id3"
    assert res["items"][0]["ct_cd_list_submval"] == "new_submission_value"
    assert res["items"][0]["ct_scope"] == "catalogue"
    assert res["items"][0]["ct_submval"] == "submission_value3"
    assert res["items"][0]["ct_ver"] == "2020-06-26"
    assert res["items"][0]["definition"] == "definition3"
    assert res["items"][0]["nci_pref_term"] == "pref_term3"
    assert res["items"][0]["pkg_nm"] == "new_package"
    assert res["items"][0]["synonyms"] is None
    assert res["items"][1]["ct_cd"] == "concept_id4"
    assert res["items"][1]["ct_cd_list_submval"] == "new_submission_value"
    assert res["items"][1]["ct_scope"] == "catalogue"
    assert res["items"][1]["ct_submval"] == "submission_value4"
    assert res["items"][1]["ct_ver"] == "2020-06-26"
    assert res["items"][1]["definition"] == "definition4"
    assert res["items"][1]["nci_pref_term"] == "pref_term4"
    assert res["items"][1]["pkg_nm"] == "new_package"
    assert res["items"][1]["synonyms"] == "syn1;syn2;syn3"
