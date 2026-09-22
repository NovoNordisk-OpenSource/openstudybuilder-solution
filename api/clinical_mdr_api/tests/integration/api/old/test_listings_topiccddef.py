# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_INSTANCES_TOPICCDDEF,
    STARTUP_ACTIVITY_SUB_GROUPS,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.listings.topiccddef")
    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
    db.cypher_query(STARTUP_ACTIVITY_GROUPS)
    db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
    db.cypher_query(STARTUP_ACTIVITIES)
    db.cypher_query(STARTUP_ACTIVITY_INSTANCES_TOPICCDDEF)

    yield

    drop_db("old.json.test.listings.topiccddef")


def test_no_datetime_specified(api_client):
    response = api_client.get("/listings/libraries/all/gcmd/topic-cd-def")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["lb"] == "name2"
    assert res["items"][0]["topic_cd"] == "topic_code2"
    assert res["items"][0]["short_topic_cd"] == "adam_param_code2"
    assert res["items"][0]["description"] == "legacy_description2"
    assert res["items"][0]["molecular_weight"] is None
    assert res["items"][0]["sas_display_format"] is None
    assert res["items"][0]["general_domain_class"] == "Interventions"
    assert res["items"][0]["sub_domain_class"] == "CompoundDosing"
    assert res["items"][0]["sub_domain_type"] == "Other"
    assert res["items"][1]["lb"] == "new_name1"
    assert res["items"][1]["topic_cd"] == "topic_code1"
    assert res["items"][1]["short_topic_cd"] == "adam_param_code1"
    assert res["items"][1]["description"] == "legacy_description1"
    assert res["items"][1]["molecular_weight"] == 1.0
    assert res["items"][1]["sas_display_format"] == "string"
    assert res["items"][1]["general_domain_class"] == "Findings"
    assert res["items"][1]["sub_domain_class"] == "NumericFinding"
    assert res["items"][1]["sub_domain_type"] == "Other"


def test_datetime_specified(api_client):
    response = api_client.get(
        "/listings/libraries/all/gcmd/topic-cd-def?at_specified_date_time=2021-10-02T10%3A00%3A00Z"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["lb"] == "name1"
    assert res["items"][0]["topic_cd"] == "topic_code1"
    assert res["items"][0]["short_topic_cd"] == "adam_param_code1"
    assert res["items"][0]["description"] == "legacy_description1"
    assert res["items"][0]["molecular_weight"] == 0.0
    assert res["items"][0]["sas_display_format"] == "string"
    assert res["items"][0]["general_domain_class"] == "Findings"
    assert res["items"][0]["sub_domain_class"] == "NumericFinding"
    assert res["items"][0]["sub_domain_type"] == "Other"
