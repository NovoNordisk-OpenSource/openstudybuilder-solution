import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CODMDT_CODELIST,
    STARTUP_CT_TERM_ATTRIBUTES_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

DESCRIPTION = {"text_type": "Description", "language": "eng", "text": "description"}


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("odm.comment.items")
    db.cypher_query(STARTUP_CT_TERM_ATTRIBUTES_CYPHER)
    db.cypher_query(STARTUP_CODMDT_CODELIST)

    yield

    drop_db("odm.comment.items")


def item_payload(name, **overrides):
    payload = {
        "library_name": "Sponsor",
        "name": name,
        "oid": f"oid_{name}",
        "datatype_uid": None,
        "vendor_attributes": [],
    }
    payload.update(overrides)
    return payload


def assert_comment_rule_violation(response, property_name):
    messages = " ".join(detail["msg"] for detail in response.json()["details"])
    assert f"Remove: {property_name}." in messages


def test_create_comment_item(api_client, test_data):
    response = api_client.post("odms/items", json=item_payload("comment_ok"))

    assert_response_status_code(response, 201)
    res = response.json()
    assert res["datatype"] is None


def test_create_comment_item_with_translations_and_aliases(api_client, test_data):
    response = api_client.post(
        "odms/items",
        json=item_payload(
            "comment_translated",
            translated_texts=[DESCRIPTION],
            aliases=[{"context": "context", "name": "alias"}],
        ),
    )

    assert_response_status_code(response, 201)
    res = response.json()
    assert res["datatype"] is None
    assert len(res["translated_texts"]) == 1
    assert len(res["aliases"]) == 1


@pytest.mark.parametrize(
    "overrides",
    [
        {"prompt": "prompt"},
        {"length": 5},
        {"comment": "comment"},
        {"origin": "origin"},
    ],
)
def test_create_comment_item_with_other_properties_is_rejected(
    api_client, test_data, overrides
):
    name = f"comment_rejected_{next(iter(overrides))}"
    response = api_client.post("odms/items", json=item_payload(name, **overrides))

    assert_response_status_code(response, 400)
    assert_comment_rule_violation(response, next(iter(overrides)))

    # The failed create is rolled back
    listing = api_client.get("odms/items", params={"page_size": 0}).json()
    assert name not in [item["name"] for item in listing["items"]]


def test_create_regular_item_is_not_a_comment(api_client, test_data):
    response = api_client.post(
        "odms/items",
        json=item_payload(
            "regular", datatype_uid="string_uid", length=10, prompt="prompt"
        ),
    )

    assert_response_status_code(response, 201)
    res = response.json()
    assert res["datatype"] is not None
    assert res["datatype"]["uid"] == "string_uid"


def edit_payload(created, **overrides):
    payload = {
        "change_description": "change",
        "name": created["name"],
        "datatype_uid": None,
        "oid": created["oid"],
        "prompt": None,
        "length": None,
        "significant_digits": None,
        "sas_field_name": None,
        "sds_var_name": None,
        "origin": None,
        "comment": None,
        "external_question": None,
        "codelist": None,
        "terms": [],
        "vendor_elements": [],
        "vendor_element_attributes": [],
        "vendor_attributes": [],
    }
    payload.update(overrides)
    return payload


def test_edit_comment_item(api_client, test_data):
    created = api_client.post("odms/items", json=item_payload("comment_edit")).json()

    response = api_client.patch(
        f"odms/items/{created['uid']}",
        json=edit_payload(created, name="comment_edit_renamed"),
    )

    assert_response_status_code(response, 200)
    res = response.json()
    assert res["name"] == "comment_edit_renamed"
    assert res["datatype"] is None


def test_edit_comment_item_with_other_properties_is_rejected(api_client, test_data):
    created = api_client.post(
        "odms/items", json=item_payload("comment_edit_bad")
    ).json()

    response = api_client.patch(
        f"odms/items/{created['uid']}",
        json=edit_payload(created, prompt="prompt"),
    )

    assert_response_status_code(response, 400)
    assert_comment_rule_violation(response, "prompt")

    unchanged = api_client.get(f"odms/items/{created['uid']}").json()
    assert unchanged.get("prompt") is None


def test_edit_regular_item_into_comment_with_other_properties_is_rejected(
    api_client, test_data
):
    created = api_client.post(
        "odms/items",
        json=item_payload("regular_to_comment", datatype_uid="string_uid", length=10),
    ).json()

    response = api_client.patch(
        f"odms/items/{created['uid']}",
        json=edit_payload(created, datatype_uid=None, length=10),
    )

    assert_response_status_code(response, 400)
    assert_comment_rule_violation(response, "length")


def test_crf_report_renders_comment_item_as_banner_without_input(api_client, test_data):
    comment = api_client.post("odms/items", json=item_payload("report_comment")).json()
    regular = api_client.post(
        "odms/items",
        json=item_payload("report_regular", datatype_uid="string_uid", length=10),
    ).json()
    item_group = TestUtils.create_odm_item_group(
        name="report_item_group", oid="oid_report_item_group", approve=False
    )
    response = api_client.post(
        f"odms/item-groups/{item_group.uid}/items",
        json=[
            {
                "uid": item["uid"],
                "order_number": order,
                "mandatory": "Yes",
                "vendor": {"attributes": []},
            }
            for order, item in enumerate([comment, regular], start=1)
        ],
    )
    assert_response_status_code(response, 201)

    response = api_client.post(
        "odms/metadata/report",
        params={"target_type": "item_group", "targets": item_group.uid},
    )

    assert_response_status_code(response, 200)
    html = response.text
    assert "report_comment" in html
    assert "report_regular" in html
    # The comment is a full-width banner row, the regular item gets one input
    assert html.count('colspan="5"') == 1
    assert html.count('<input type="text"') == 1


def test_create_comment_item_with_vendor_extensions(api_client, test_data):
    namespace = TestUtils.create_odm_vendor_namespace(
        name="CommentNamespace", prefix="cns", url="http://comment.example.com"
    )
    other_attribute = TestUtils.create_odm_vendor_attribute(
        name="otherAttribute",
        compatible_types=["ItemDef"],
        data_type="string",
        vendor_namespace_uid=namespace.uid,
        approve=True,
    )
    payload = item_payload(
        "comment_extensions",
        vendor_attributes=[{"uid": other_attribute.uid, "value": "value"}],
    )

    response = api_client.post("odms/items", json=payload)

    assert_response_status_code(response, 201)
    res = response.json()
    assert res["datatype"] is None
    assert [attr["name"] for attr in res["vendor_attributes"]] == ["otherAttribute"]
