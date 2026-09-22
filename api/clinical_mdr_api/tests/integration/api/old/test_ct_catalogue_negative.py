# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.ct.catalogue.negative")
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)

    yield

    drop_db("old.json.test.ct.catalogue.negative")


def test_get_catalogue_changes_end_datetime_older_than_start_datetime(api_client):
    response = api_client.get(
        "/ct/catalogues/changes?catalogue_name=catalogue&comparison_type=attributes&start_datetime=2020-06-26T00:00:00&end_datetime=2020-03-27T00:00:00"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "End datetime '2020-03-27 00:00:00' can't be older than start datetime '2020-06-26 00:00:00'."
    )


def test_get_catalogue_changes_non_existent_catalogue_passed(api_client):
    response = api_client.get(
        "/ct/catalogues/changes?catalogue_name=non_existent_catalogue&comparison_type=attributes&start_datetime=2020-03-27T00:00:00&end_datetime=2020-06-26T00:00:00"
    )

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"] == "Catalogue with Name 'non_existent_catalogue' doesn't exist."
    )


def test_get_catalogue_changes_not_valid_comparison_type_passed(api_client):
    response = api_client.get(
        "/ct/catalogues/changes?catalogue_name=catalogue&comparison_type=invalid_type&start_datetime=2020-03-27T00:00:00&end_datetime=2020-06-26T00:00:00"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "The following type 'invalid_type' isn't valid catalogue comparison type."
    )
