# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db
from pydantic import BaseModel

import clinical_mdr_api.models.syntax_templates.objective_template as ct_models
import clinical_mdr_api.services.libraries.libraries as library_service
from clinical_mdr_api.main import app
from clinical_mdr_api.services.syntax_templates.objective_templates import (
    ObjectiveTemplateService,
)
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_PARAMETERS_CYPHER,
    library_data,
    template_data,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.instance.multiple.separated")
    db.cypher_query(STARTUP_PARAMETERS_CYPHER)
    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)

    library_service.create(**library_data)
    otdata = template_data.copy()
    otdata["name"] = "To investigate [Indication] and [Intervention]"
    objective_template = ct_models.ObjectiveTemplateCreateInput(**otdata)
    objective_template = ObjectiveTemplateService().create(objective_template)
    if isinstance(objective_template, BaseModel):
        objective_template = objective_template.model_dump()
    ObjectiveTemplateService().approve(objective_template["uid"])

    yield

    drop_db("old.json.test.instance.multiple.separated")


def test_name_generation_of_objective_with_0_values_for_both_template_parameters1(
    api_client,
):
    data = {
        "library_name": "Test library",
        "name": "Test objective",
        "objective_template_uid": "ObjectiveTemplate_000001",
        "parameter_terms": [
            {"position": 1, "conjunction": "and", "terms": []},
            {"position": 2, "conjunction": "and", "terms": []},
        ],
    }
    response = api_client.post("/objectives", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Objective_000001"
    assert res["name"] == "To investigate"
    assert res["name_plain"] == "To investigate"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["study_count"] == 0
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["template"] == {
        "name": "To investigate [Indication] and [Intervention]",
        "name_plain": "To investigate [Indication] and [Intervention]",
        "guidance_text": None,
        "uid": "ObjectiveTemplate_000001",
        "sequence_id": "O1",
        "library_name": "Test library",
    }
    assert res["parameter_terms"] == [
        {"position": 1, "conjunction": "and", "terms": []},
        {"position": 2, "conjunction": "and", "terms": []},
    ]
    assert res["library"] == {"name": "Test library", "is_editable": True}


def test_name_generation_of_objective_with_1_template_parameter_term_0_template_parameter_terms1(
    api_client,
):
    data = {
        "library_name": "Test library",
        "name": "Test objective",
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
            },
            {"position": 2, "conjunction": "and", "terms": []},
        ],
    }
    response = api_client.post("/objectives", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Objective_000002"
    assert res["name"] == "To investigate [type 2 diabetes]"
    assert res["name_plain"] == "To investigate type 2 diabetes"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["study_count"] == 0
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["template"] == {
        "name": "To investigate [Indication] and [Intervention]",
        "name_plain": "To investigate [Indication] and [Intervention]",
        "guidance_text": None,
        "uid": "ObjectiveTemplate_000001",
        "sequence_id": "O1",
        "library_name": "Test library",
    }
    assert res["parameter_terms"] == [
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
        },
        {"position": 2, "conjunction": "and", "terms": []},
    ]
    assert res["library"] == {"name": "Test library", "is_editable": True}


def test_name_generation_of_objective_with_2_template_parameters_terms_0_template_parameter_terms1(
    api_client,
):
    data = {
        "library_name": "Test library",
        "name": "Test objective",
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
            },
            {"position": 2, "conjunction": "and", "terms": []},
        ],
    }
    response = api_client.post("/objectives", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Objective_000003"
    assert res["name"] == "To investigate [type 2 diabetes and coronary heart disease]"
    assert (
        res["name_plain"] == "To investigate type 2 diabetes and coronary heart disease"
    )
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["study_count"] == 0
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["template"] == {
        "name": "To investigate [Indication] and [Intervention]",
        "name_plain": "To investigate [Indication] and [Intervention]",
        "guidance_text": None,
        "uid": "ObjectiveTemplate_000001",
        "sequence_id": "O1",
        "library_name": "Test library",
    }
    assert res["parameter_terms"] == [
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
        },
        {"position": 2, "conjunction": "and", "terms": []},
    ]
    assert res["library"] == {"name": "Test library", "is_editable": True}


def test_name_generation_of_objective_with_3_template_parameters_terms_0_template_parameter_terms1(
    api_client,
):
    data = {
        "library_name": "Test library",
        "name": "Test objective",
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
            },
            {"position": 2, "conjunction": "and", "terms": []},
        ],
    }
    response = api_client.post("/objectives", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Objective_000004"
    assert (
        res["name"]
        == "To investigate [type 2 diabetes, coronary heart disease and breathing problems]"
    )
    assert (
        res["name_plain"]
        == "To investigate type 2 diabetes, coronary heart disease and breathing problems"
    )
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["study_count"] == 0
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["template"] == {
        "name": "To investigate [Indication] and [Intervention]",
        "name_plain": "To investigate [Indication] and [Intervention]",
        "guidance_text": None,
        "uid": "ObjectiveTemplate_000001",
        "sequence_id": "O1",
        "library_name": "Test library",
    }
    assert res["parameter_terms"] == [
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
        },
        {"position": 2, "conjunction": "and", "terms": []},
    ]
    assert res["library"] == {"name": "Test library", "is_editable": True}


def test_name_generation_of_objective_with_0_template_parameter_terms_1_template_parameter_term1(
    api_client,
):
    data = {
        "library_name": "Test library",
        "name": "Test objective",
        "objective_template_uid": "ObjectiveTemplate_000001",
        "parameter_terms": [
            {"position": 1, "conjunction": "and", "terms": []},
            {
                "position": 2,
                "conjunction": "and",
                "terms": [
                    {
                        "index": 1,
                        "type": "Intervention",
                        "name": "Metformin",
                        "uid": "Intervention-99992",
                    }
                ],
            },
        ],
    }
    response = api_client.post("/objectives", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Objective_000005"
    assert res["name"] == "To investigate [Metformin]"
    assert res["name_plain"] == "To investigate Metformin"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["study_count"] == 0
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["template"] == {
        "name": "To investigate [Indication] and [Intervention]",
        "name_plain": "To investigate [Indication] and [Intervention]",
        "guidance_text": None,
        "uid": "ObjectiveTemplate_000001",
        "sequence_id": "O1",
        "library_name": "Test library",
    }
    assert res["parameter_terms"] == [
        {"position": 1, "conjunction": "and", "terms": []},
        {
            "position": 2,
            "conjunction": "and",
            "terms": [
                {
                    "index": 1,
                    "type": "Intervention",
                    "name": "Metformin",
                    "uid": "Intervention-99992",
                }
            ],
        },
    ]
    assert res["library"] == {"name": "Test library", "is_editable": True}


def test_name_generation_of_objective_with_1_template_parameter_term_1_template_parameter_term1(
    api_client,
):
    data = {
        "library_name": "Test library",
        "name": "Test objective",
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
            },
            {
                "position": 2,
                "conjunction": "and",
                "terms": [
                    {
                        "index": 1,
                        "type": "Intervention",
                        "name": "Metformin",
                        "uid": "Intervention-99992",
                    }
                ],
            },
        ],
    }
    response = api_client.post("/objectives", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Objective_000006"
    assert res["name"] == "To investigate [type 2 diabetes] and [Metformin]"
    assert res["name_plain"] == "To investigate type 2 diabetes and Metformin"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["study_count"] == 0
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["template"] == {
        "name": "To investigate [Indication] and [Intervention]",
        "name_plain": "To investigate [Indication] and [Intervention]",
        "guidance_text": None,
        "uid": "ObjectiveTemplate_000001",
        "sequence_id": "O1",
        "library_name": "Test library",
    }
    assert res["parameter_terms"] == [
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
        },
        {
            "position": 2,
            "conjunction": "and",
            "terms": [
                {
                    "index": 1,
                    "type": "Intervention",
                    "name": "Metformin",
                    "uid": "Intervention-99992",
                }
            ],
        },
    ]
    assert res["library"] == {"name": "Test library", "is_editable": True}


def test_name_generation_of_objective_with_2_template_parameters_terms_1_template_parameter_term1(
    api_client,
):
    data = {
        "library_name": "Test library",
        "name": "Test objective",
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
            },
            {
                "position": 2,
                "conjunction": "and",
                "terms": [
                    {
                        "index": 1,
                        "type": "Intervention",
                        "name": "Metformin",
                        "uid": "Intervention-99992",
                    }
                ],
            },
        ],
    }
    response = api_client.post("/objectives", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Objective_000007"
    assert (
        res["name"]
        == "To investigate [type 2 diabetes, coronary heart disease] and [Metformin]"
    )
    assert (
        res["name_plain"]
        == "To investigate type 2 diabetes, coronary heart disease and Metformin"
    )
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["study_count"] == 0
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["template"] == {
        "name": "To investigate [Indication] and [Intervention]",
        "name_plain": "To investigate [Indication] and [Intervention]",
        "guidance_text": None,
        "uid": "ObjectiveTemplate_000001",
        "sequence_id": "O1",
        "library_name": "Test library",
    }
    assert res["parameter_terms"] == [
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
        },
        {
            "position": 2,
            "conjunction": "and",
            "terms": [
                {
                    "index": 1,
                    "type": "Intervention",
                    "name": "Metformin",
                    "uid": "Intervention-99992",
                }
            ],
        },
    ]
    assert res["library"] == {"name": "Test library", "is_editable": True}


def test_name_generation_of_objective_with_3_template_parameters_terms_1_template_parameter_term1(
    api_client,
):
    data = {
        "library_name": "Test library",
        "name": "Test objective",
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
            },
            {
                "position": 2,
                "conjunction": "and",
                "terms": [
                    {
                        "index": 1,
                        "type": "Intervention",
                        "name": "Metformin",
                        "uid": "Intervention-99992",
                    }
                ],
            },
        ],
    }
    response = api_client.post("/objectives", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Objective_000008"
    assert (
        res["name"]
        == "To investigate [type 2 diabetes, coronary heart disease, breathing problems] and [Metformin]"
    )
    assert (
        res["name_plain"]
        == "To investigate type 2 diabetes, coronary heart disease, breathing problems and Metformin"
    )
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["study_count"] == 0
    assert res["version"] == "0.1"
    assert res["change_description"] == "Initial version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["template"] == {
        "name": "To investigate [Indication] and [Intervention]",
        "name_plain": "To investigate [Indication] and [Intervention]",
        "guidance_text": None,
        "uid": "ObjectiveTemplate_000001",
        "sequence_id": "O1",
        "library_name": "Test library",
    }
    assert res["parameter_terms"] == [
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
        },
        {
            "position": 2,
            "conjunction": "and",
            "terms": [
                {
                    "index": 1,
                    "type": "Intervention",
                    "name": "Metformin",
                    "uid": "Intervention-99992",
                }
            ],
        },
    ]
    assert res["library"] == {"name": "Test library", "is_editable": True}
