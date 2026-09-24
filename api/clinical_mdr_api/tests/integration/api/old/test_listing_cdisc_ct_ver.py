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
    inject_and_clear_db("old.json.test.listing.cdisc.ct.ver")
    db.cypher_query(STARTUP_CT_PACKAGE_CYPHER_CDISC_CT)

    yield

    drop_db("old.json.test.listing.cdisc.ct.ver")


def test_no_date_specified_sorting_by_ct_scope_and_ct_ver(api_client):
    response = api_client.get(
        "/listings/libraries/all/gcmd/cdisc-ct-ver?sort_by=%7B%22ct_scope%22%3Atrue%2C%22ct_ver%22%3Atrue%7D&page_number=1&page_size=0&total_count=false"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["ct_scope"] == "catalogue"
    assert res["items"][0]["ct_ver"] == "2020-03-27"
    assert res["items"][0]["pkg_nm"] == "old_package"
    assert res["items"][1]["ct_scope"] == "catalogue"
    assert res["items"][1]["ct_ver"] == "2020-06-26"
    assert res["items"][1]["pkg_nm"] == "new_package"
    assert res["items"][2]["ct_scope"] == "catalogue2"
    assert res["items"][2]["ct_ver"] == "2020-06-26"
    assert res["items"][2]["pkg_nm"] == "package1"
    assert res["items"][3]["ct_scope"] == "catalogue3"
    assert res["items"][3]["ct_ver"] == "2020-06-26"
    assert res["items"][3]["pkg_nm"] == "package2"


def test_date_specified_filtering_on_catalogue3(api_client):
    response = api_client.get(
        "/listings/libraries/all/gcmd/cdisc-ct-ver?catalogue_name=catalogue,catalogue2&sort_by=%7B%22ct_scope%22%3Atrue%7D&after_specified_date=2020-06-20"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["ct_scope"] == "catalogue"
    assert res["items"][0]["ct_ver"] == "2020-06-26"
    assert res["items"][0]["pkg_nm"] == "new_package"
    assert res["items"][1]["ct_scope"] == "catalogue2"
    assert res["items"][1]["ct_ver"] == "2020-06-26"
    assert res["items"][1]["pkg_nm"] == "package1"
