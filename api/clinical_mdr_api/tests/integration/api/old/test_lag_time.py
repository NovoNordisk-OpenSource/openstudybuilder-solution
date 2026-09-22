# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

import clinical_mdr_api.services.libraries.libraries as library_service
from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_ACTIVITY_INSTANCES_CT_INIT,
    STARTUP_CT_TERM,
    STARTUP_UNIT_DEFINITIONS,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.lag.time")
    library_service.create(name="Sponsor", is_editable=True)
    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
    db.cypher_query(STARTUP_UNIT_DEFINITIONS)
    db.cypher_query(STARTUP_CT_TERM)
    db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
    catalogue_name = "SDTM CT"
    library_name = "Sponsor"
    codelist = create_codelist(
        name="SDTM Domain Abbreviation",
        uid="C66734",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="DOMAIN",
    )
    create_ct_term(
        name="domain",
        uid="domain001",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "XX",
            }
        ],
    )

    yield

    drop_db("old.json.test.lag.time")


def test_post_lag_time(api_client):
    data = {
        "value": 7.5,
        "unit_definition_uid": "unit_definition_root1",
        "sdtm_domain_uid": "domain001",
        "definition": "lag_time_definition1",
        "abbreviation": "abbv",
        "template_parameter": True,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/lag-times", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "LagTime_000001"
    assert res["name"] == "7.5 [unit_definition_root1] for SDTM domain [domain001]"
    assert res["value"] == 7.5
    assert res["unit_definition_uid"] == "unit_definition_root1"
    assert res["unit_label"] == "name1"
    assert res["sdtm_domain_uid"] == "domain001"
    assert res["name_sentence_case"] == "7.5"
    assert res["definition"] == "lag_time_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["template_parameter"] is True
    assert res["library_name"] == "Sponsor"
    assert res["status"] is None
    assert res["version"] is None
    assert res["change_description"] is None
    assert res["author_username"] is None
    assert res["end_date"] is None


def test_post_lag_time_existing_lag_time_is_returned(api_client):
    data = {
        "value": 7.5,
        "unit_definition_uid": "unit_definition_root1",
        "sdtm_domain_uid": "domain001",
        "definition": "lag_time_definition1",
        "abbreviation": "abbv",
        "template_parameter": True,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/lag-times", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "LagTime_000001"
    assert res["name"] == "7.5 [unit_definition_root1] for SDTM domain [domain001]"
    assert res["value"] == 7.5
    assert res["unit_definition_uid"] == "unit_definition_root1"
    assert res["unit_label"] == "name1"
    assert res["sdtm_domain_uid"] == "domain001"
    assert res["name_sentence_case"] == "7.5"
    assert res["definition"] == "lag_time_definition1"
    assert res["abbreviation"] == "abbv"
    assert res["template_parameter"] is True
    assert res["library_name"] == "Sponsor"
    assert res["status"] is None
    assert res["version"] is None
    assert res["change_description"] is None
    assert res["author_username"] is None
    assert res["end_date"] is None


def test_post_lag_time1(api_client):
    data = {
        "value": 9.12,
        "unit_definition_uid": "unit_definition_root1",
        "sdtm_domain_uid": "domain001",
        "definition": "lag_time_definition2",
        "abbreviation": "abbv",
        "template_parameter": True,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/lag-times", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "LagTime_000002"
    assert res["name"] == "9.12 [unit_definition_root1] for SDTM domain [domain001]"
    assert res["value"] == 9.12
    assert res["unit_definition_uid"] == "unit_definition_root1"
    assert res["unit_label"] == "name1"
    assert res["sdtm_domain_uid"] == "domain001"
    assert res["name_sentence_case"] == "9.12"
    assert res["definition"] == "lag_time_definition2"
    assert res["abbreviation"] == "abbv"
    assert res["template_parameter"] is True
    assert res["library_name"] == "Sponsor"
    assert res["status"] is None
    assert res["version"] is None
    assert res["change_description"] is None
    assert res["author_username"] is None
    assert res["end_date"] is None


def test_get_all_lag_times(api_client):
    response = api_client.get("/concepts/lag-times?total_count=true")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "LagTime_000001"
    assert res["items"][0]["name"] == "7.5"
    assert res["items"][0]["value"] == 7.5
    assert res["items"][0]["unit_definition_uid"] == "unit_definition_root1"
    assert res["items"][0]["unit_label"] == "name1"
    assert res["items"][0]["sdtm_domain_uid"] == "domain001"
    assert res["items"][0]["name_sentence_case"] == "7.5"
    assert res["items"][0]["definition"] == "lag_time_definition1"
    assert res["items"][0]["abbreviation"] == "abbv"
    assert res["items"][0]["template_parameter"] is True
    assert res["items"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["status"] is None
    assert res["items"][0]["version"] is None
    assert res["items"][0]["change_description"] is None
    assert res["items"][0]["author_username"] is None
    assert res["items"][0]["end_date"] is None
    assert res["items"][1]["uid"] == "LagTime_000002"
    assert res["items"][1]["name"] == "9.12"
    assert res["items"][1]["value"] == 9.12
    assert res["items"][1]["unit_definition_uid"] == "unit_definition_root1"
    assert res["items"][1]["unit_label"] == "name1"
    assert res["items"][1]["sdtm_domain_uid"] == "domain001"
    assert res["items"][1]["name_sentence_case"] == "9.12"
    assert res["items"][1]["definition"] == "lag_time_definition2"
    assert res["items"][1]["abbreviation"] == "abbv"
    assert res["items"][1]["template_parameter"] is True
    assert res["items"][1]["library_name"] == "Sponsor"
    assert res["items"][1]["status"] is None
    assert res["items"][1]["version"] is None
    assert res["items"][1]["change_description"] is None
    assert res["items"][1]["author_username"] is None
    assert res["items"][1]["end_date"] is None


def test_post_lag_time_specifying_a_non_existent_unit(api_client):
    data = {
        "value": 8.43,
        "unit_definition_uid": "non-existent-uid",
        "sdtm_domain_uid": "domain001",
        "definition": "lag_time_definition2",
        "abbreviation": "abbv",
        "template_parameter": False,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/lag-times", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "LagTimeVO tried to connect to non-existent Unit Definition with UID 'non-existent-uid'."
    )


def test_post_lag_time_specifying_a_non_existent_sdtm_domain(api_client):
    data = {
        "value": 8.43,
        "unit_definition_uid": "unit_definition_root1",
        "sdtm_domain_uid": "non-existent-uid",
        "definition": "lag_time_definition2",
        "abbreviation": "abbv",
        "template_parameter": False,
        "library_name": "Sponsor",
    }
    response = api_client.post("/concepts/lag-times", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "LagTimeVO tried to connect to non-existent SDTM Domain with UID 'non-existent-uid'."
    )
