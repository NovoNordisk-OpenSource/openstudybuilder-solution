# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db
from pydantic import BaseModel

import clinical_mdr_api.models.syntax_templates.objective_template as ot_models
import clinical_mdr_api.services.libraries.libraries as library_service
from clinical_mdr_api.main import app
from clinical_mdr_api.services.syntax_templates.objective_templates import (
    ObjectiveTemplateService,
)
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    CREATE_NA_TEMPLATE_PARAMETER,
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_PARAMETERS_CYPHER,
    STARTUP_STUDY_CYPHER,
    library_data,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.instance.study.context.single")
    db.cypher_query(STARTUP_PARAMETERS_CYPHER)
    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
    db.cypher_query(CREATE_NA_TEMPLATE_PARAMETER)
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_CYPHER)

    library_service.create(**library_data)
    otdata = {
        "name": "To investigate [Indication]",
        "library": library_data,
        "library_name": "Test library",
    }
    objective_template = ot_models.ObjectiveTemplateCreateInput(**otdata)
    objective_template = ObjectiveTemplateService().create(objective_template)
    if isinstance(objective_template, BaseModel):
        objective_template = objective_template.model_dump()
    ObjectiveTemplateService().approve(objective_template["uid"])

    yield

    drop_db("old.json.test.instance.study.context.single")


def test_name_generation_of_study_objective_with_0_template_parameters_values(
    api_client,
):
    data = {
        "objective_data": {
            "library_name": "Test library",
            "name": "Test objective",
            "objective_template_uid": "ObjectiveTemplate_000001",
            "parameter_terms": [{"position": 1, "conjunction": "and", "terms": []}],
        },
        "objective_level_uid": "term_root_final",
    }
    response = api_client.post(
        "/studies/study_root/study-objectives?create_objective=true", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["order"] == 1
    assert res["project_number"] == "123"
    assert res["project_name"] == "Project ABC"
    assert res["study_objective_uid"] == "StudyObjective_000001"
    assert res["objective_level"]["term_uid"] == "term_root_final"
    assert res["objective_level"]["catalogue_name"] == "SDTM CT"
    assert len(res["objective_level"]["codelists"]) == 1
    assert res["objective_level"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["objective_level"]["codelists"][0]["order"] == 1
    assert res["objective_level"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["objective_level"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["objective_level"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["objective_level"]["library_name"] == "Sponsor"
    assert res["objective_level"]["start_date"]
    assert res["objective_level"]["end_date"] is None
    assert res["objective_level"]["status"] == "Final"
    assert res["objective_level"]["version"] == "1.0"
    assert res["objective_level"]["change_description"] == "Approved version"
    assert res["objective_level"]["author_username"] == "unknown-user@example.com"
    assert res["objective_level"]["queried_effective_date"] is None
    assert res["objective_level"]["date_conflict"] is False
    assert res["objective_level"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["objective"]["uid"] == "Objective_000001"
    assert res["objective"]["name"] == "To investigate"
    assert res["objective"]["name_plain"] == "To investigate"
    assert res["objective"]["start_date"]
    assert res["objective"]["end_date"] is None
    assert res["objective"]["status"] == "Final"
    assert res["objective"]["version"] == "1.0"
    assert res["objective"]["change_description"] == "Approved version"
    assert res["objective"]["author_username"] == "unknown-user@example.com"
    assert res["objective"]["possible_actions"] == ["inactivate"]
    assert res["objective"]["template"]["name"] == "To investigate [Indication]"
    assert res["objective"]["template"]["name_plain"] == "To investigate [Indication]"
    assert res["objective"]["template"]["uid"] == "ObjectiveTemplate_000001"
    assert res["objective"]["template"]["sequence_id"] == "O1"
    assert res["objective"]["template"]["library_name"] == "Test library"
    assert len(res["objective"]["parameter_terms"]) == 1
    assert res["objective"]["parameter_terms"][0]["position"] == 1
    assert res["objective"]["parameter_terms"][0]["conjunction"] == "and"
    assert len(res["objective"]["parameter_terms"][0]["terms"]) == 0
    assert res["objective"]["library"]["name"] == "Test library"
    assert res["objective"]["library"]["is_editable"] is True
    assert res["objective"]["study_count"] == 0
    assert res["author_username"] == "unknown-user@example.com"
    assert res["endpoint_count"] == 0
    assert res["latest_objective"] is None
    assert res["accepted_version"] is False


def test_name_generation_of_study_objective_with_1_template_parameters_value(
    api_client,
):
    data = {
        "objective_data": {
            "library_name": "Test library",
            "name": "To investigate [Indication]",
            "objective_template_uid": "ObjectiveTemplate_000001",
            "parameter_terms": [
                {
                    "position": 1,
                    "conjunction": "and",
                    "terms": [
                        {
                            "index": 1,
                            "type": "Indication",
                            "name": "type 2 diabetes",
                            "uid": "Indication-99991",
                        }
                    ],
                }
            ],
        },
        "objective_level_uid": "term_root_final",
    }
    response = api_client.post(
        "/studies/study_root/study-objectives?create_objective=true", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["order"] == 2
    assert res["project_number"] == "123"
    assert res["project_name"] == "Project ABC"
    assert res["study_objective_uid"] == "StudyObjective_000002"
    assert res["objective_level"]["term_uid"] == "term_root_final"
    assert res["objective_level"]["catalogue_name"] == "SDTM CT"
    assert len(res["objective_level"]["codelists"]) == 1
    assert res["objective_level"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["objective_level"]["codelists"][0]["order"] == 1
    assert res["objective_level"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["objective_level"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["objective_level"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["objective_level"]["library_name"] == "Sponsor"
    assert res["objective_level"]["start_date"]
    assert res["objective_level"]["end_date"] is None
    assert res["objective_level"]["status"] == "Final"
    assert res["objective_level"]["version"] == "1.0"
    assert res["objective_level"]["change_description"] == "Approved version"
    assert res["objective_level"]["author_username"] == "unknown-user@example.com"
    assert res["objective_level"]["queried_effective_date"] is None
    assert res["objective_level"]["date_conflict"] is False
    assert res["objective_level"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["objective"]["uid"] == "Objective_000002"
    assert res["objective"]["name"] == "To investigate [type 2 diabetes]"
    assert res["objective"]["name_plain"] == "To investigate type 2 diabetes"
    assert res["objective"]["start_date"]
    assert res["objective"]["end_date"] is None
    assert res["objective"]["status"] == "Final"
    assert res["objective"]["version"] == "1.0"
    assert res["objective"]["change_description"] == "Approved version"
    assert res["objective"]["author_username"] == "unknown-user@example.com"
    assert res["objective"]["possible_actions"] == ["inactivate"]
    assert res["objective"]["template"]["name"] == "To investigate [Indication]"
    assert res["objective"]["template"]["name_plain"] == "To investigate [Indication]"
    assert res["objective"]["template"]["uid"] == "ObjectiveTemplate_000001"
    assert res["objective"]["template"]["sequence_id"] == "O1"
    assert res["objective"]["template"]["library_name"] == "Test library"
    assert len(res["objective"]["parameter_terms"]) == 1
    assert res["objective"]["parameter_terms"][0]["position"] == 1
    assert res["objective"]["parameter_terms"][0]["conjunction"] == "and"
    assert len(res["objective"]["parameter_terms"][0]["terms"]) == 1
    assert (
        res["objective"]["parameter_terms"][0]["terms"][0]["uid"] == "Indication-99991"
    )
    assert (
        res["objective"]["parameter_terms"][0]["terms"][0]["name"] == "type 2 diabetes"
    )
    assert res["objective"]["parameter_terms"][0]["terms"][0]["type"] == "Indication"
    assert res["objective"]["parameter_terms"][0]["terms"][0]["index"] == 1
    assert res["objective"]["library"]["name"] == "Test library"
    assert res["objective"]["library"]["is_editable"] is True
    assert res["objective"]["study_count"] == 0
    assert res["author_username"] == "unknown-user@example.com"
    assert res["endpoint_count"] == 0
    assert res["latest_objective"] is None
    assert res["accepted_version"] is False


def test_name_generation_of_study_objective_with_2_template_parameters_values(
    api_client,
):
    data = {
        "objective_data": {
            "library_name": "Test library",
            "name": "To investigate [Indication]",
            "objective_template_uid": "ObjectiveTemplate_000001",
            "parameter_terms": [
                {
                    "position": 1,
                    "conjunction": "and",
                    "terms": [
                        {
                            "index": 1,
                            "type": "Indication",
                            "name": "type 2 diabetes",
                            "uid": "Indication-99991",
                        },
                        {
                            "index": 2,
                            "type": "Indication",
                            "name": "coronary heart disease",
                            "uid": "Indication-99992",
                        },
                    ],
                }
            ],
        },
        "objective_level_uid": "term_root_final",
    }
    response = api_client.post(
        "/studies/study_root/study-objectives?create_objective=true", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["order"] == 3
    assert res["project_number"] == "123"
    assert res["project_name"] == "Project ABC"
    assert res["study_objective_uid"] == "StudyObjective_000003"
    assert res["objective_level"]["term_uid"] == "term_root_final"
    assert res["objective_level"]["catalogue_name"] == "SDTM CT"
    assert len(res["objective_level"]["codelists"]) == 1
    assert res["objective_level"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["objective_level"]["codelists"][0]["order"] == 1
    assert res["objective_level"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["objective_level"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["objective_level"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["objective_level"]["library_name"] == "Sponsor"
    assert res["objective_level"]["end_date"] is None
    assert res["objective_level"]["status"] == "Final"
    assert res["objective_level"]["version"] == "1.0"
    assert res["objective_level"]["change_description"] == "Approved version"
    assert res["objective_level"]["author_username"] == "unknown-user@example.com"
    assert res["objective_level"]["queried_effective_date"] is None
    assert res["objective_level"]["date_conflict"] is False
    assert res["objective_level"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["objective"]["uid"] == "Objective_000003"
    assert (
        res["objective"]["name"]
        == "To investigate [type 2 diabetes and coronary heart disease]"
    )
    assert (
        res["objective"]["name_plain"]
        == "To investigate type 2 diabetes and coronary heart disease"
    )
    assert res["objective"]["start_date"]
    assert res["objective"]["end_date"] is None
    assert res["objective"]["status"] == "Final"
    assert res["objective"]["version"] == "1.0"
    assert res["objective"]["change_description"] == "Approved version"
    assert res["objective"]["author_username"] == "unknown-user@example.com"
    assert res["objective"]["possible_actions"] == ["inactivate"]
    assert res["objective"]["template"]["name"] == "To investigate [Indication]"
    assert res["objective"]["template"]["name_plain"] == "To investigate [Indication]"
    assert res["objective"]["template"]["uid"] == "ObjectiveTemplate_000001"
    assert res["objective"]["template"]["sequence_id"] == "O1"
    assert res["objective"]["template"]["library_name"] == "Test library"
    assert len(res["objective"]["parameter_terms"]) == 1
    assert res["objective"]["parameter_terms"][0]["position"] == 1
    assert res["objective"]["parameter_terms"][0]["conjunction"] == "and"
    assert len(res["objective"]["parameter_terms"][0]["terms"]) == 2
    assert res["objective"]["parameter_terms"][0]["terms"][0]["index"] == 1
    assert res["objective"]["parameter_terms"][0]["terms"][0]["type"] == "Indication"
    assert (
        res["objective"]["parameter_terms"][0]["terms"][0]["name"] == "type 2 diabetes"
    )
    assert (
        res["objective"]["parameter_terms"][0]["terms"][0]["uid"] == "Indication-99991"
    )
    assert res["objective"]["parameter_terms"][0]["terms"][1]["index"] == 2
    assert res["objective"]["parameter_terms"][0]["terms"][1]["type"] == "Indication"
    assert (
        res["objective"]["parameter_terms"][0]["terms"][1]["name"]
        == "coronary heart disease"
    )
    assert (
        res["objective"]["parameter_terms"][0]["terms"][1]["uid"] == "Indication-99992"
    )
    assert res["objective"]["library"]["name"] == "Test library"
    assert res["objective"]["library"]["is_editable"] is True
    assert res["objective"]["study_count"] == 0
    assert res["objective"]["author_username"] == "unknown-user@example.com"
    assert res["endpoint_count"] == 0
    assert res["latest_objective"] is None
    assert res["accepted_version"] is False


def test_name_generation_of_study_objective_with_3_template_parameters_values(
    api_client,
):
    data = {
        "objective_data": {
            "library_name": "Test library",
            "name": "To investigate [Indication]",
            "objective_template_uid": "ObjectiveTemplate_000001",
            "parameter_terms": [
                {
                    "position": 1,
                    "conjunction": "and",
                    "terms": [
                        {
                            "index": 1,
                            "type": "Indication",
                            "name": "type 2 diabetes",
                            "uid": "Indication-99991",
                        },
                        {
                            "index": 2,
                            "type": "Indication",
                            "name": "coronary heart disease",
                            "uid": "Indication-99992",
                        },
                        {
                            "index": 3,
                            "type": "Indication",
                            "name": "breathing problems",
                            "uid": "Indication-99993",
                        },
                    ],
                }
            ],
        },
        "objective_level_uid": "term_root_final",
    }
    response = api_client.post(
        "/studies/study_root/study-objectives?create_objective=true", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["order"] == 4
    assert res["project_number"] == "123"
    assert res["project_name"] == "Project ABC"
    assert res["study_objective_uid"] == "StudyObjective_000004"
    assert res["objective_level"]
    assert res["objective_level"]["term_uid"] == "term_root_final"
    assert res["objective_level"]["catalogue_name"] == "SDTM CT"
    assert len(res["objective_level"]["codelists"]) == 1
    assert res["objective_level"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["objective_level"]["codelists"][0]["order"] == 1
    assert res["objective_level"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["objective_level"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["objective_level"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["objective_level"]["library_name"] == "Sponsor"
    assert res["objective_level"]["end_date"] is None
    assert res["objective_level"]["status"] == "Final"
    assert res["objective_level"]["version"] == "1.0"
    assert res["objective_level"]["change_description"] == "Approved version"
    assert res["objective_level"]["author_username"] == "unknown-user@example.com"
    assert res["objective_level"]["queried_effective_date"] is None
    assert res["objective_level"]["date_conflict"] is False
    assert res["objective_level"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["objective"]["uid"] == "Objective_000004"
    assert (
        res["objective"]["name"]
        == "To investigate [type 2 diabetes, coronary heart disease and breathing problems]"
    )
    assert (
        res["objective"]["name_plain"]
        == "To investigate type 2 diabetes, coronary heart disease and breathing problems"
    )
    assert res["objective"]["start_date"]
    assert res["objective"]["end_date"] is None
    assert res["objective"]["status"] == "Final"
    assert res["objective"]["version"] == "1.0"
    assert res["objective"]["change_description"] == "Approved version"
    assert res["objective"]["author_username"] == "unknown-user@example.com"
    assert res["objective"]["possible_actions"] == ["inactivate"]
    assert res["objective"]["template"]["name"] == "To investigate [Indication]"
    assert res["objective"]["template"]["name_plain"] == "To investigate [Indication]"
    assert res["objective"]["template"]["uid"] == "ObjectiveTemplate_000001"
    assert res["objective"]["template"]["sequence_id"] == "O1"
    assert res["objective"]["template"]["library_name"] == "Test library"
    assert len(res["objective"]["parameter_terms"]) == 1
    assert res["objective"]["parameter_terms"][0]["position"] == 1
    assert res["objective"]["parameter_terms"][0]["conjunction"] == "and"
    assert len(res["objective"]["parameter_terms"][0]["terms"]) == 3
    assert res["objective"]["parameter_terms"][0]["terms"][0]["index"] == 1
    assert res["objective"]["parameter_terms"][0]["terms"][0]["type"] == "Indication"
    assert (
        res["objective"]["parameter_terms"][0]["terms"][0]["name"] == "type 2 diabetes"
    )
    assert (
        res["objective"]["parameter_terms"][0]["terms"][0]["uid"] == "Indication-99991"
    )
    assert res["objective"]["parameter_terms"][0]["terms"][1]["index"] == 2
    assert res["objective"]["parameter_terms"][0]["terms"][1]["type"] == "Indication"
    assert (
        res["objective"]["parameter_terms"][0]["terms"][1]["name"]
        == "coronary heart disease"
    )
    assert (
        res["objective"]["parameter_terms"][0]["terms"][1]["uid"] == "Indication-99992"
    )
    assert res["objective"]["parameter_terms"][0]["terms"][2]["index"] == 3
    assert res["objective"]["parameter_terms"][0]["terms"][2]["type"] == "Indication"
    assert (
        res["objective"]["parameter_terms"][0]["terms"][2]["name"]
        == "breathing problems"
    )
    assert (
        res["objective"]["parameter_terms"][0]["terms"][2]["uid"] == "Indication-99993"
    )
    assert res["objective"]["library"]["name"] == "Test library"
    assert res["objective"]["library"]["is_editable"] is True
    assert res["objective"]["study_count"] == 0
    assert res["author_username"] == "unknown-user@example.com"
    assert res["endpoint_count"] == 0
    assert res["latest_objective"] is None
    assert res["accepted_version"] is False
