# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_PACKAGE_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.ct.package.negative")
    db.cypher_query(STARTUP_CT_PACKAGE_CYPHER)

    yield

    drop_db("old.json.test.ct.package.negative")


def test_get_packages_changes_new_package_older_than_old_package(api_client):
    response = api_client.get(
        "/ct/packages/changes?catalogue_name=catalogue&old_package_date=2020-06-26&new_package_date=2020-03-27"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "New package can't be older than old package"


def test_get_packages_changes_non_existent_catalogue_passed(api_client):
    response = api_client.get(
        "/ct/packages/changes?catalogue_name=non_existent_catalogue&old_package_date=2020-03-27&new_package_date=2020-06-26"
    )

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"] == "Catalogue with Name 'non_existent_catalogue' doesn't exist."
    )


def test_get_packages_changes_non_existent_date_for_given_catalogue(api_client):
    response = api_client.get(
        "/ct/packages/changes?catalogue_name=catalogue&old_package_date=2020-03-27&new_package_date=2020-06-01"
    )

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "There is no Package with Date '2020-06-01' for the Catalogue with Name 'catalogue'."
    )


def test_get_packages_dates_non_existent_catalogue_passed(api_client):
    response = api_client.get(
        "/ct/packages/dates?catalogue_name=non_existent_catalogue"
    )

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"] == "Catalogue with Name 'non_existent_catalogue' doesn't exist."
    )
