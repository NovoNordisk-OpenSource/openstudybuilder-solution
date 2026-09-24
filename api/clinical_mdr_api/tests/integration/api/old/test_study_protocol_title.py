# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_STUDY_PROTOCOL_TITLE_CYPHER,
    get_codelist_with_term_cypher,
    inject_base_data,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.protocol.title")
    inject_base_data()
    db.cypher_query(get_codelist_with_term_cypher("Investigational Product"))
    db.cypher_query(STARTUP_STUDY_PROTOCOL_TITLE_CYPHER)

    yield

    drop_db("old.json.test.study.protocol.title")


def test_get_study_protocol_title_information(api_client):
    response = api_client.get("/studies/study_root/protocol-title")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_title"] is None
    assert res["study_short_title"] == "Study short title"
    assert res["eudract_id"] == "2019-123456-42"
    assert res["universal_trial_number_utn"] is None
    assert res["trial_phase_code"] is None
    assert res["development_stage_code"] is None
    assert res["ind_number"] == "ind-number-777"
    assert res["substance_name"] == "name"
    assert res["protocol_header_version"] is None
