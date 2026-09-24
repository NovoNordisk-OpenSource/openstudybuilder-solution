# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.domains.enums import OdmTranslatedTextTypeEnum
from clinical_mdr_api.main import app
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmFormalExpressionModel,
    OdmTranslatedTextModel,
)
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_ODM_CONDITIONS,
    STARTUP_ODM_FORMS,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("odm.metadata")
    db.cypher_query(STARTUP_ODM_FORMS)
    db.cypher_query(STARTUP_ODM_CONDITIONS)

    TestUtils.create_odm_form(
        translated_texts=[
            OdmTranslatedTextModel(
                text_type=OdmTranslatedTextTypeEnum.QUESTION,
                language="da",
                text="QuestionDA",
            ),
            OdmTranslatedTextModel(
                text_type=OdmTranslatedTextTypeEnum.OSB_DESIGN_NOTES,
                language="da",
                text="Design NotesDA",
            ),
            OdmTranslatedTextModel(
                text_type=OdmTranslatedTextTypeEnum.OSB_DISPLAY_TEXT,
                language="da",
                text="Display TextDA",
            ),
        ],
        aliases=[
            OdmAliasModel(context="context", name="name1"),
            OdmAliasModel(context="context", name="name2"),
            OdmAliasModel(context="new context", name="name3"),
        ],
        approve=False,
    )

    TestUtils.create_odm_condition(
        formal_expressions=[
            OdmFormalExpressionModel(context="context", expression="expression1"),
            OdmFormalExpressionModel(context="context", expression="expression2"),
            OdmFormalExpressionModel(context="new context", expression="expression3"),
        ],
        approve=False,
    )

    yield

    drop_db("odm.metadata")


@pytest.mark.parametrize(
    "value, expected_result_prefix, rs_length",
    [
        pytest.param("nAme1", {"name": "name1"}, 2),
        pytest.param("mE1", {"name": "name1"}, 2),
        pytest.param("cOntext1", {"context": "context1"}, 1),
        pytest.param("eXt1", {"context": "context1"}, 1),
        pytest.param("wrong", {}, 0),
    ],
)
def test_get_aliases(
    api_client, value: str, expected_result_prefix: dict[str, str], rs_length: int
):
    response = api_client.get(f"/odms/metadata/aliases?search={value}")
    data = response.json()

    assert_response_status_code(response, 200)

    assert len(data["items"]) == rs_length
    assert data["total"] == rs_length

    for item in data["items"]:
        for key, val in expected_result_prefix.items():
            assert item[key].startswith(val)


@pytest.mark.parametrize(
    "value, expected_order",
    [
        pytest.param(
            "name",
            {"name": ["name1", "name1", "name2", "name3"]},
        ),
        pytest.param(
            "-name",
            {"name": ["name3", "name2", "name1", "name1"]},
        ),
        pytest.param(
            "name,context",
            {
                "name": ["name1", "name1", "name2", "name3"],
                "context": [
                    "context",
                    "context1",
                    "context",
                    "new context",
                ],
            },
        ),
        pytest.param(
            "name,-context",
            {
                "name": ["name1", "name1", "name2", "name3"],
                "context": [
                    "context1",
                    "context",
                    "context",
                    "new context",
                ],
            },
        ),
        pytest.param(
            "-name,context",
            {
                "name": ["name3", "name2", "name1", "name1"],
                "context": [
                    "new context",
                    "context",
                    "context",
                    "context1",
                ],
            },
        ),
        pytest.param(
            "-name,-context",
            {
                "name": ["name3", "name2", "name1", "name1"],
                "context": [
                    "new context",
                    "context",
                    "context1",
                    "context",
                ],
            },
        ),
    ],
)
def test_get_aliases_in_order(
    api_client, value: str, expected_order: dict[str, list[str]]
):
    response = api_client.get(f"/odms/metadata/aliases?sort_by={value}")
    data = response.json()

    assert_response_status_code(response, 200)

    assert len(data["items"]) == 4
    assert data["total"] == 4

    for idx, item in enumerate(data["items"]):
        for field in expected_order.keys():
            assert item[field] == expected_order[field][idx]


@pytest.mark.parametrize(
    "value, expected_result_prefix, rs_length",
    [
        pytest.param("tIOn1", {"text": "Description"}, 1),
        pytest.param("eN", {"language": "en"}, 4),
        pytest.param(" noTes1", {"text": "Design Notes1"}, 1),
        pytest.param(" instrUctions1", {"text": "Completion Instructions1"}, 1),
        pytest.param("wrong", {}, 0),
    ],
)
def test_get_translated_texts(
    api_client, value: str, expected_result_prefix: dict[str, str], rs_length: int
):
    response = api_client.get(f"/odms/metadata/translated-texts?search={value}")
    data = response.json()

    assert_response_status_code(response, 200)

    assert len(data["items"]) == rs_length
    assert data["total"] == rs_length

    for item in data["items"]:
        for key, val in expected_result_prefix.items():
            assert item[key].startswith(val)


@pytest.mark.parametrize(
    "value, expected_order",
    [
        pytest.param(
            "language",
            {"language": ["da", "da", "da", "en", "en", "en", "en"]},
        ),
        pytest.param(
            "-language",
            {"language": ["en", "en", "en", "en", "da", "da", "da"]},
        ),
        pytest.param(
            "language,text_type",
            {
                "language": ["da", "da", "da", "en", "en", "en", "en"],
                "text_type": [
                    "osb:DesignNotes",
                    "osb:DisplayText",
                    "Question",
                    "Description",
                    "osb:CompletionInstructions",
                    "osb:DesignNotes",
                    "osb:DisplayText",
                ],
            },
        ),
        pytest.param(
            "language,-text_type",
            {
                "language": ["da", "da", "da", "en", "en", "en", "en"],
                "text_type": [
                    "Question",
                    "osb:DisplayText",
                    "osb:DesignNotes",
                    "osb:DisplayText",
                    "osb:DesignNotes",
                    "osb:CompletionInstructions",
                    "Description",
                ],
            },
        ),
        pytest.param(
            "-language,text_type",
            {
                "language": ["en", "en", "en", "en", "da", "da", "da"],
                "text_type": [
                    "Description",
                    "osb:CompletionInstructions",
                    "osb:DesignNotes",
                    "osb:DisplayText",
                    "osb:DesignNotes",
                    "osb:DisplayText",
                    "Question",
                ],
            },
        ),
        pytest.param(
            "-language,-text_type",
            {
                "language": ["en", "en", "en", "en", "da", "da", "da"],
                "text_type": [
                    "osb:DisplayText",
                    "osb:DesignNotes",
                    "osb:CompletionInstructions",
                    "Description",
                    "Question",
                    "osb:DisplayText",
                    "osb:DesignNotes",
                ],
            },
        ),
    ],
)
def test_get_translated_texts_in_order(
    api_client, value: str, expected_order: dict[str, list[str]]
):
    response = api_client.get(f"/odms/metadata/translated-texts?sort_by={value}")
    data = response.json()

    assert_response_status_code(response, 200)

    assert len(data["items"]) == 7
    assert data["total"] == 7

    for idx, item in enumerate(data["items"]):
        for field in expected_order.keys():
            assert item[field] == expected_order[field][idx]


@pytest.mark.parametrize(
    "value, expected_result_prefix, rs_length",
    [
        pytest.param("cOntext1", {"context": "context1"}, 1),
        pytest.param("eXt1", {"context": "context1"}, 1),
        pytest.param("expreSsion1", {"expression": "expression1"}, 2),
        pytest.param("sIon1", {"expression": "expression1"}, 2),
        pytest.param("wrong", {}, 0),
    ],
)
def test_get_formal_expressions(
    api_client, value: str, expected_result_prefix: dict[str, str], rs_length: int
):
    response = api_client.get(f"/odms/metadata/formal-expressions?search={value}")
    data = response.json()

    assert_response_status_code(response, 200)

    assert len(data["items"]) == rs_length
    assert data["total"] == rs_length

    for item in data["items"]:
        for key, val in expected_result_prefix.items():
            assert item[key].startswith(val)


@pytest.mark.parametrize(
    "value, expected_order",
    [
        pytest.param(
            "context",
            {"context": ["context", "context", "context1", "new context"]},
        ),
        pytest.param(
            "-context",
            {"context": ["new context", "context1", "context", "context"]},
        ),
        pytest.param(
            "context,expression",
            {
                "context": ["context", "context", "context1", "new context"],
                "expression": [
                    "expression1",
                    "expression2",
                    "expression1",
                    "expression3",
                ],
            },
        ),
        pytest.param(
            "context,-expression",
            {
                "context": ["context", "context", "context1", "new context"],
                "expression": [
                    "expression2",
                    "expression1",
                    "expression1",
                    "expression3",
                ],
            },
        ),
        pytest.param(
            "-context,expression",
            {
                "context": ["new context", "context1", "context", "context"],
                "expression": [
                    "expression3",
                    "expression1",
                    "expression1",
                    "expression2",
                ],
            },
        ),
        pytest.param(
            "-context,-expression",
            {
                "context": ["new context", "context1", "context", "context"],
                "expression": [
                    "expression3",
                    "expression1",
                    "expression2",
                    "expression1",
                ],
            },
        ),
    ],
)
def test_get_formal_expressions_in_order(
    api_client, value: str, expected_order: dict[str, list[str]]
):
    response = api_client.get(f"/odms/metadata/formal-expressions?sort_by={value}")
    data = response.json()

    assert_response_status_code(response, 200)

    assert len(data["items"]) == 4
    assert data["total"] == 4

    for idx, item in enumerate(data["items"]):
        for field in expected_order.keys():
            assert item[field] == expected_order[field][idx]


def test_doesnt_return_aliases_that_are_only_connected_to_deleted_odms(api_client):
    data = {
        "library_name": "Sponsor",
        "name": "to be deleted1",
        "oid": "oid",
        "sdtm_version": "0.1",
        "repeating": "No",
        "translated_texts": [],
        "aliases": [{"context": "connected to be deleted", "name": "deleted"}],
    }
    response = api_client.post("odms/forms", json=data)
    assert_response_status_code(response, 201)
    rs = response.json()

    response = api_client.get("/odms/metadata/aliases?page_size=0")
    assert_response_status_code(response, 200)
    data = response.json()
    assert any(item["context"] == "connected to be deleted" for item in data["items"])
    assert data["total"] == 5
    assert len(data["items"]) == 5

    response = api_client.delete(f"odms/forms/{rs["uid"]}")
    assert_response_status_code(response, 204)

    response = api_client.get("/odms/metadata/aliases?page_size=0")
    assert_response_status_code(response, 200)
    data = response.json()
    assert all(item["context"] != "connected to be deleted" for item in data["items"])
    assert data["total"] == 4
    assert len(data["items"]) == 4


def test_doesnt_return_translated_texts_that_are_only_connected_to_deleted_odms(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "to be deleted2",
        "oid": "oid",
        "sdtm_version": "0.1",
        "repeating": "No",
        "translated_texts": [
            {
                "text_type": "Description",
                "language": "en",
                "text": "Description1",
            },
            {
                "text_type": "osb:CompletionInstructions",
                "language": "en",
                "text": "Completion Instructions1",
            },
            {
                "text_type": "osb:DesignNotes",
                "language": "en",
                "text": "Design Notes1",
            },
            {
                "text_type": "osb:DisplayText",
                "language": "en",
                "text": "connected to be deleted",
            },
        ],
        "aliases": [],
    }
    response = api_client.post("odms/forms", json=data)
    assert_response_status_code(response, 201)
    rs = response.json()

    response = api_client.get("/odms/metadata/translated-texts?page_size=0")
    assert_response_status_code(response, 200)
    data = response.json()
    assert any(item["text"] == "connected to be deleted" for item in data["items"])
    assert data["total"] == 8
    assert len(data["items"]) == 8

    response = api_client.delete(f"odms/forms/{rs["uid"]}")
    assert_response_status_code(response, 204)

    response = api_client.get("/odms/metadata/translated-texts?page_size=0")
    assert_response_status_code(response, 200)
    data = response.json()
    assert all(item["text"] != "connected to be deleted" for item in data["items"])
    assert data["total"] == 7
    assert len(data["items"]) == 7


def test_doesnt_return_formal_expressions_that_are_only_connected_to_deleted_odms(
    api_client,
):
    data = {
        "library_name": "Sponsor",
        "name": "to be deleted1",
        "oid": "oid",
        "formal_expressions": [
            {"context": "connected to be deleted", "expression": "expression"}
        ],
        "translated_texts": [],
        "aliases": [],
    }
    response = api_client.post("odms/conditions", json=data)
    assert_response_status_code(response, 201)
    rs = response.json()

    response = api_client.get("/odms/metadata/formal-expressions?page_size=0")
    assert_response_status_code(response, 200)
    data = response.json()
    assert any(item["context"] == "connected to be deleted" for item in data["items"])
    assert data["total"] == 5
    assert len(data["items"]) == 5

    response = api_client.delete(f"odms/conditions/{rs["uid"]}")
    assert_response_status_code(response, 204)

    response = api_client.get("/odms/metadata/formal-expressions?page_size=0")
    assert_response_status_code(response, 200)
    data = response.json()
    assert all(item["context"] != "connected to be deleted" for item in data["items"])
    assert data["total"] == 4
    assert len(data["items"]) == 4


def test_doesnt_return_aliases_that_are_not_connected_to_latest_odms(api_client):
    response = api_client.post(
        "odms/forms",
        json={
            "library_name": "Sponsor",
            "name": "to be updated1",
            "oid": "oid",
            "sdtm_version": "0.1",
            "repeating": "No",
            "translated_texts": [],
            "aliases": [{"context": "connected to be renamed", "name": "renaming"}],
        },
    )
    assert_response_status_code(response, 201)
    rs = response.json()

    response = api_client.get("/odms/metadata/aliases?page_size=0")
    assert_response_status_code(response, 200)
    data = response.json()
    assert any(item["context"] == "connected to be renamed" for item in data["items"])
    assert data["total"] == 5
    assert len(data["items"]) == 5

    response = api_client.patch(
        f"odms/forms/{rs["uid"]}",
        json={
            "library_name": "Sponsor",
            "name": "to be updated1",
            "oid": "oid",
            "sdtm_version": "0.1",
            "repeating": "No",
            "translated_texts": [],
            "aliases": [{"context": "done", "name": "renamed"}],
            "vendor_elements": [],
            "vendor_element_attributes": [],
            "vendor_attributes": [],
            "change_description": "Updating alias",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get("/odms/metadata/aliases?page_size=0")
    assert_response_status_code(response, 200)
    data = response.json()
    assert all(item["context"] != "connected to be renamed" for item in data["items"])
    assert data["total"] == 5
    assert len(data["items"]) == 5


def test_doesnt_return_translated_texts_that_are_not_connected_to_latest_odms(
    api_client,
):
    response = api_client.post(
        "odms/forms",
        json={
            "library_name": "Sponsor",
            "name": "to be updated2",
            "oid": "translated_texts",
            "sdtm_version": "0.1",
            "repeating": "No",
            "translated_texts": [
                {
                    "text_type": "Description",
                    "language": "en",
                    "text": "Description1",
                },
                {
                    "text_type": "osb:CompletionInstructions",
                    "language": "en",
                    "text": "Completion Instructions1",
                },
                {
                    "text_type": "osb:DesignNotes",
                    "language": "en",
                    "text": "Design Notes1",
                },
                {
                    "text_type": "osb:DisplayText",
                    "language": "en",
                    "text": "connected to be renamed",
                },
            ],
            "aliases": [],
        },
    )
    assert_response_status_code(response, 201)
    rs = response.json()

    response = api_client.get("/odms/metadata/translated-texts?page_size=0")
    assert_response_status_code(response, 200)
    data = response.json()
    assert any(item["text"] == "connected to be renamed" for item in data["items"])
    assert data["total"] == 8
    assert len(data["items"]) == 8

    response = api_client.patch(
        f"odms/forms/{rs["uid"]}",
        json={
            "library_name": "Sponsor",
            "name": "to be updated2",
            "oid": "translated_texts",
            "sdtm_version": "0.1",
            "repeating": "No",
            "translated_texts": [
                {
                    "text_type": "Description",
                    "language": "en",
                    "text": "Description1",
                },
                {
                    "text_type": "osb:CompletionInstructions",
                    "language": "en",
                    "text": "Completion Instructions1",
                },
                {
                    "text_type": "osb:DesignNotes",
                    "language": "en",
                    "text": "Design Notes1",
                },
                {
                    "text_type": "osb:DisplayText",
                    "language": "en",
                    "text": "renamed",
                },
            ],
            "aliases": [],
            "vendor_elements": [],
            "vendor_element_attributes": [],
            "vendor_attributes": [],
            "change_description": "Updating description",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get("/odms/metadata/translated-texts?page_size=0")
    assert_response_status_code(response, 200)
    data = response.json()
    assert all(item["text"] != "connected to be renamed" for item in data["items"])
    assert data["total"] == 8
    assert len(data["items"]) == 8


def test_doesnt_return_formal_expressions_that_are_not_connected_to_latest_odms(
    api_client,
):
    response = api_client.post(
        "odms/conditions",
        json={
            "library_name": "Sponsor",
            "name": "to be renamed1",
            "oid": "oid",
            "formal_expressions": [
                {"context": "connected to be renamed", "expression": "renaming"}
            ],
            "translated_texts": [],
            "aliases": [],
        },
    )
    assert_response_status_code(response, 201)
    rs = response.json()

    response = api_client.get("/odms/metadata/formal-expressions?page_size=0")
    assert_response_status_code(response, 200)
    data = response.json()
    assert any(item["context"] == "connected to be renamed" for item in data["items"])
    assert data["total"] == 5
    assert len(data["items"]) == 5

    response = api_client.patch(
        f"odms/conditions/{rs["uid"]}",
        json={
            "library_name": "Sponsor",
            "name": "to be renamed1",
            "oid": "oid",
            "formal_expressions": [{"context": "renamed", "expression": "done"}],
            "translated_texts": [],
            "aliases": [],
            "change_description": "Updating formal expression",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get("/odms/metadata/formal-expressions?page_size=0")
    assert_response_status_code(response, 200)
    data = response.json()
    assert all(item["context"] != "connected to be renamed" for item in data["items"])
    assert data["total"] == 5
    assert len(data["items"]) == 5
