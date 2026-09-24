# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

from datetime import date

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
    STARTUP_CODMDT_CODELIST,
    STARTUP_ODM_CONDITIONS,
    STARTUP_ODM_FORMS,
    STARTUP_ODM_ITEM_GROUPS,
    STARTUP_ODM_ITEMS,
    STARTUP_ODM_METHODS,
    STARTUP_ODM_STUDY_EVENTS,
    STARTUP_ODM_VENDOR_ATTRIBUTES,
    STARTUP_ODM_VENDOR_ELEMENTS,
    STARTUP_ODM_VENDOR_NAMESPACES,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("odm.fields.parameter")
    db.cypher_query(STARTUP_ODM_FORMS)
    db.cypher_query(STARTUP_ODM_ITEMS)
    db.cypher_query(STARTUP_ODM_ITEM_GROUPS)
    db.cypher_query(STARTUP_ODM_STUDY_EVENTS)
    db.cypher_query(STARTUP_CODMDT_CODELIST)
    db.cypher_query(STARTUP_ODM_CONDITIONS)
    db.cypher_query(STARTUP_ODM_METHODS)
    db.cypher_query(STARTUP_ODM_VENDOR_NAMESPACES)
    db.cypher_query(STARTUP_ODM_VENDOR_ELEMENTS)
    db.cypher_query(STARTUP_ODM_VENDOR_ATTRIBUTES)

    # Create test data
    form = TestUtils.create_odm_form(
        name="Test Form",
        oid="FORM.TEST.001",
        repeating="Yes",
        sdtm_version="1.0",
        translated_texts=[
            OdmTranslatedTextModel(
                text_type=OdmTranslatedTextTypeEnum.DESCRIPTION,
                language="en",
                text="Test Description",
            ),
        ],
        aliases=[OdmAliasModel(context="test", name="test_alias")],
        approve=True,
    )

    item = TestUtils.create_odm_item(
        name="Test Item",
        oid="ITEM.TEST.001",
        datatype_uid="text_uid",
        length=100,
        translated_texts=[
            OdmTranslatedTextModel(
                text_type=OdmTranslatedTextTypeEnum.QUESTION,
                language="en",
                text="Test Question",
            ),
        ],
        aliases=[OdmAliasModel(context="test", name="test_item_alias")],
        approve=True,
    )

    item_group = TestUtils.create_odm_item_group(
        name="Test Item Group",
        oid="IG.TEST.001",
        repeating="No",
        translated_texts=[
            OdmTranslatedTextModel(
                text_type=OdmTranslatedTextTypeEnum.DESCRIPTION,
                language="en",
                text="Test Item Group Description",
            ),
        ],
        approve=True,
    )

    study_event = TestUtils.create_odm_study_event(
        name="Test Study Event",
        oid="SE.TEST.001",
        effective_date=date(2024, 1, 1),
        retired_date=date(2025, 1, 1),
        approve=True,
    )

    condition = TestUtils.create_odm_condition(
        name="Test Condition",
        oid="COND.TEST.001",
        formal_expressions=[
            OdmFormalExpressionModel(
                context="Python",
                expression="x > 0",
            ),
        ],
        approve=True,
    )

    method = TestUtils.create_odm_method(
        name="Test Method",
        oid="METHOD.TEST.001",
        method_type="Computation",
        formal_expressions=[
            OdmFormalExpressionModel(
                context="Python",
                expression="sum(x)",
            ),
        ],
        approve=True,
    )

    vendor_namespace = TestUtils.create_odm_vendor_namespace(
        name="Test Namespace",
        prefix="tns",
        url="http://test.example.com",
        approve=True,
    )

    vendor_element = TestUtils.create_odm_vendor_element(
        name="TestElement",
        vendor_namespace_uid=vendor_namespace.uid,
        compatible_types=["FormDef", "ItemGroupDef", "ItemDef"],
        approve=True,
    )

    vendor_attribute = TestUtils.create_odm_vendor_attribute(
        name="testAttribute",
        compatible_types=["FormDef", "ItemGroupDef", "ItemDef"],
        data_type="string",
        vendor_namespace_uid=vendor_namespace.uid,
        approve=True,
    )

    yield {
        "form": form,
        "item": item,
        "item_group": item_group,
        "study_event": study_event,
        "condition": condition,
        "method": method,
        "vendor_namespace": vendor_namespace,
        "vendor_element": vendor_element,
        "vendor_attribute": vendor_attribute,
    }

    drop_db("odm.fields.parameter")


# ==================== List Endpoint Tests ====================


@pytest.mark.parametrize(
    "endpoint,fields,expected_fields",
    [
        ("odms/forms", "name,oid", {"uid", "name", "oid"}),
        ("odms/forms", "name,status,version", {"uid", "name", "status", "version"}),
        ("odms/items", "name,oid,datatype", {"uid", "name", "oid", "datatype"}),
        ("odms/item-groups", "name,oid,repeating", {"uid", "name", "oid", "repeating"}),
        (
            "odms/study-events",
            "name,oid",
            {"uid", "name", "oid"},
        ),
        ("odms/conditions", "name,oid", {"uid", "name", "oid"}),
        ("odms/methods", "name,oid,method_type", {"uid", "name", "oid", "method_type"}),
        ("odms/vendor-namespaces", "name,prefix,url", {"uid", "name", "prefix", "url"}),
        ("odms/vendor-elements", "name", {"uid", "name"}),
        ("odms/vendor-attributes", "name", {"uid", "name"}),
    ],
)
def test_list_endpoint_with_fields_parameter(
    api_client, endpoint, fields, expected_fields
):
    """Test that list endpoints return only requested fields"""
    response = api_client.get(f"/{endpoint}?fields={fields}")
    assert_response_status_code(response, 200)

    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0

    for item in data["items"]:
        # Check that only expected fields are present
        assert set(item.keys()) == expected_fields


@pytest.mark.parametrize(
    "endpoint",
    [
        "odms/forms",
        "odms/items",
        "odms/item-groups",
        "odms/study-events",
        "odms/conditions",
        "odms/methods",
        "odms/vendor-namespaces",
        "odms/vendor-elements",
        "odms/vendor-attributes",
    ],
)
def test_list_endpoint_without_fields_returns_full_objects(api_client, endpoint):
    """Test that list endpoints without fields parameter return full objects"""
    response = api_client.get(f"/{endpoint}")
    assert_response_status_code(response, 200)

    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0

    # Full objects should have many fields including uid, name, status, version, etc.
    first_item = data["items"][0]
    assert "uid" in first_item
    assert "name" in first_item
    assert "status" in first_item
    assert "version" in first_item
    assert "start_date" in first_item
    assert "author_username" in first_item


def test_list_endpoint_with_complex_fields(api_client):
    """Test that list endpoints can request complex/computed fields"""
    response = api_client.get("/odms/forms?fields=name,translated_texts,aliases")
    assert_response_status_code(response, 200)

    data = response.json()
    assert len(data["items"]) > 0

    first_item = data["items"][0]
    assert set(first_item.keys()) == {"uid", "name", "translated_texts", "aliases"}
    assert isinstance(first_item["translated_texts"], list)
    assert isinstance(first_item["aliases"], list)


def test_list_endpoint_fields_with_pagination(api_client):
    """Test fields parameter works with pagination"""
    response = api_client.get("/odms/forms?fields=name,oid&page_number=1&page_size=5")
    assert_response_status_code(response, 200)

    data = response.json()
    assert "items" in data
    assert data["page"] == 1
    assert data["size"] == 5

    for item in data["items"]:
        assert set(item.keys()) == {"uid", "name", "oid"}


# ==================== Single-Entity Endpoint Tests ====================


@pytest.mark.parametrize(
    "endpoint_template,uid_key,fields,expected_fields",
    [
        ("odms/forms/{uid}", "form", "name,oid", {"uid", "name", "oid"}),
        (
            "odms/forms/{uid}",
            "form",
            "name,status,version,repeating",
            {"uid", "name", "status", "version", "repeating"},
        ),
        (
            "odms/items/{uid}",
            "item",
            "name,oid,datatype",
            {"uid", "name", "oid", "datatype"},
        ),
        (
            "odms/item-groups/{uid}",
            "item_group",
            "name,oid,repeating",
            {"uid", "name", "oid", "repeating"},
        ),
        (
            "odms/study-events/{uid}",
            "study_event",
            "name,oid",
            {"uid", "name", "oid"},
        ),
        ("odms/conditions/{uid}", "condition", "name,oid", {"uid", "name", "oid"}),
        (
            "odms/methods/{uid}",
            "method",
            "name,oid,method_type",
            {"uid", "name", "oid", "method_type"},
        ),
        (
            "odms/vendor-namespaces/{uid}",
            "vendor_namespace",
            "name,prefix,url",
            {"uid", "name", "prefix", "url"},
        ),
        ("odms/vendor-elements/{uid}", "vendor_element", "name", {"uid", "name"}),
        ("odms/vendor-attributes/{uid}", "vendor_attribute", "name", {"uid", "name"}),
    ],
)
def test_single_entity_endpoint_with_fields_parameter(
    api_client, test_data, endpoint_template, uid_key, fields, expected_fields
):
    """Test that single-entity endpoints return only requested fields"""
    uid = test_data[uid_key].uid
    endpoint = endpoint_template.format(uid=uid)

    response = api_client.get(f"/{endpoint}?fields={fields}")
    assert_response_status_code(response, 200)

    data = response.json()
    # Check that only expected fields are present
    assert set(data.keys()) == expected_fields


@pytest.mark.parametrize(
    "endpoint_template,uid_key",
    [
        ("odms/forms/{uid}", "form"),
        ("odms/items/{uid}", "item"),
        ("odms/item-groups/{uid}", "item_group"),
        ("odms/study-events/{uid}", "study_event"),
        ("odms/conditions/{uid}", "condition"),
        ("odms/methods/{uid}", "method"),
        ("odms/vendor-namespaces/{uid}", "vendor_namespace"),
        ("odms/vendor-elements/{uid}", "vendor_element"),
        ("odms/vendor-attributes/{uid}", "vendor_attribute"),
    ],
)
def test_single_entity_endpoint_without_fields_returns_full_object(
    api_client, test_data, endpoint_template, uid_key
):
    """Test that single-entity endpoints without fields parameter return full objects"""
    uid = test_data[uid_key].uid
    endpoint = endpoint_template.format(uid=uid)

    response = api_client.get(f"/{endpoint}")
    assert_response_status_code(response, 200)

    data = response.json()
    # Full objects should have many fields
    assert "uid" in data
    assert "name" in data
    assert "status" in data
    assert "version" in data
    assert "start_date" in data
    assert "author_username" in data


def test_single_entity_endpoint_with_complex_fields(api_client, test_data):
    """Test that single-entity endpoints can request complex/computed fields"""
    uid = test_data["form"].uid

    response = api_client.get(f"/odms/forms/{uid}?fields=name,translated_texts,aliases")
    assert_response_status_code(response, 200)

    data = response.json()
    assert set(data.keys()) == {"uid", "name", "translated_texts", "aliases"}
    assert isinstance(data["translated_texts"], list)
    assert isinstance(data["aliases"], list)


def test_single_entity_endpoint_fields_with_version(api_client, test_data):
    """Test fields parameter works with version parameter"""
    uid = test_data["form"].uid

    response = api_client.get(f"/odms/forms/{uid}?fields=name,oid&version=1.0")
    assert_response_status_code(response, 200)

    data = response.json()
    assert set(data.keys()) == {"uid", "name", "oid"}


# ==================== Relationship Fields Tests ====================


def test_list_endpoint_with_relationship_fields(api_client):
    """Test that list endpoints can request relationship fields"""
    response = api_client.get("/odms/forms?fields=name,item_groups")
    assert_response_status_code(response, 200)

    data = response.json()
    first_item = data["items"][0]
    assert set(first_item.keys()) == {"uid", "name", "item_groups"}
    assert isinstance(first_item["item_groups"], list)


def test_single_entity_endpoint_with_relationship_fields(api_client, test_data):
    """Test that single-entity endpoints can request relationship fields"""
    uid = test_data["form"].uid

    response = api_client.get(f"/odms/forms/{uid}?fields=name,item_groups")
    assert_response_status_code(response, 200)

    data = response.json()
    assert set(data.keys()) == {"uid", "name", "item_groups"}
    assert isinstance(data["item_groups"], list)


# ==================== Edge Cases ====================


def test_fields_parameter_with_single_field(api_client):
    """Test fields parameter with single field"""
    response = api_client.get("/odms/forms?fields=name")
    assert_response_status_code(response, 200)

    data = response.json()
    first_item = data["items"][0]
    assert set(first_item.keys()) == {"uid", "name"}


def test_fields_parameter_with_whitespace(api_client):
    """Test fields parameter handles whitespace correctly"""
    response = api_client.get("/odms/forms?fields=name, oid, status")
    assert_response_status_code(response, 200)

    data = response.json()
    first_item = data["items"][0]
    assert set(first_item.keys()) == {"uid", "name", "oid", "status"}


def test_fields_parameter_with_invalid_field_names(api_client):
    """Test fields parameter with invalid field names (should not break, just omit invalid fields)"""
    response = api_client.get("/odms/forms?fields=name,invalid_field_xyz")
    assert_response_status_code(response, 200)

    data = response.json()
    # Should still work, just won't include invalid fields
    assert "items" in data


def test_fields_parameter_returns_json_serializable_dates(api_client):
    """Test that datetime fields are properly converted to JSON-serializable format"""
    response = api_client.get("/odms/forms?fields=name,start_date")
    assert_response_status_code(response, 200)

    data = response.json()
    first_item = data["items"][0]
    assert "start_date" in first_item
    # Should be a string in ISO format, not a Neo4j DateTime object
    assert isinstance(first_item["start_date"], str)


# ==================== Vendor Extension Fields Tests ====================


def test_list_endpoint_with_vendor_fields(api_client):
    """Test that list endpoints can request vendor extension fields"""
    response = api_client.get(
        "/odms/forms?fields=name,vendor_elements,vendor_attributes"
    )
    assert_response_status_code(response, 200)

    data = response.json()
    first_item = data["items"][0]
    assert set(first_item.keys()) == {
        "uid",
        "name",
        "vendor_elements",
        "vendor_attributes",
    }
    assert isinstance(first_item["vendor_elements"], list)
    assert isinstance(first_item["vendor_attributes"], list)


def test_single_entity_endpoint_with_vendor_fields(api_client, test_data):
    """Test that single-entity endpoints can request vendor extension fields"""
    uid = test_data["form"].uid

    response = api_client.get(
        f"/odms/forms/{uid}?fields=name,vendor_elements,vendor_attributes"
    )
    assert_response_status_code(response, 200)

    data = response.json()
    assert set(data.keys()) == {"uid", "name", "vendor_elements", "vendor_attributes"}


def test_vendor_namespace_fields_include_related_counts(api_client, test_data):
    """Test vendor namespace fields include vendor element/attribute UIDs"""
    uid = test_data["vendor_namespace"].uid

    response = api_client.get(
        f"/odms/vendor-namespaces/{uid}?fields=name,vendor_elements,vendor_attributes"
    )
    assert_response_status_code(response, 200)

    data = response.json()
    assert set(data.keys()) == {
        "uid",
        "name",
        "vendor_elements",
        "vendor_attributes",
    }
    assert isinstance(data["vendor_elements"], list)
    assert isinstance(data["vendor_attributes"], list)


# ==================== Conditions and Methods Specific Tests ====================


def test_condition_with_formal_expressions_field(api_client, test_data):
    """Test condition endpoints can request formal_expressions field"""
    uid = test_data["condition"].uid

    response = api_client.get(f"/odms/conditions/{uid}?fields=name,formal_expressions")
    assert_response_status_code(response, 200)

    data = response.json()
    assert set(data.keys()) == {"uid", "name", "formal_expressions"}
    assert isinstance(data["formal_expressions"], list)
    assert len(data["formal_expressions"]) > 0
    assert "context" in data["formal_expressions"][0]
    assert "expression" in data["formal_expressions"][0]


def test_method_with_formal_expressions_field(api_client, test_data):
    """Test method endpoints can request formal_expressions field"""
    uid = test_data["method"].uid

    response = api_client.get(
        f"/odms/methods/{uid}?fields=name,method_type,formal_expressions"
    )
    assert_response_status_code(response, 200)

    data = response.json()
    assert set(data.keys()) == {"uid", "name", "method_type", "formal_expressions"}
    assert isinstance(data["formal_expressions"], list)
    assert len(data["formal_expressions"]) > 0


def test_conditions_list_with_fields(api_client):
    """Test conditions list endpoint with fields parameter"""
    response = api_client.get("/odms/conditions?fields=name,oid,formal_expressions")
    assert_response_status_code(response, 200)

    data = response.json()
    assert len(data["items"]) > 0
    first_item = data["items"][0]
    assert set(first_item.keys()) == {"uid", "name", "oid", "formal_expressions"}


def test_methods_list_with_fields(api_client):
    """Test methods list endpoint with fields parameter"""
    response = api_client.get("/odms/methods?fields=name,oid,method_type")
    assert_response_status_code(response, 200)

    data = response.json()
    assert len(data["items"]) > 0
    first_item = data["items"][0]
    assert set(first_item.keys()) == {"uid", "name", "oid", "method_type"}


# ==================== possible_actions Field Tests ====================


def test_list_endpoint_with_possible_actions_field(api_client):
    """Test that possible_actions is returned when explicitly selected in fields."""
    response = api_client.get("/odms/forms?fields=possible_actions")
    assert_response_status_code(response, 200)

    data = response.json()
    assert len(data["items"]) > 0

    first_item = data["items"][0]
    # Only uid (always present) and possible_actions should appear - no leaked deps
    assert set(first_item.keys()) == {"uid", "possible_actions"}
    assert isinstance(first_item["possible_actions"], list)
    assert len(first_item["possible_actions"]) > 0


def test_list_endpoint_possible_actions_values_for_final_status(api_client):
    """Test that possible_actions contains the correct values for Final-status items."""
    # All test fixtures are created with approve=True → Final status
    response = api_client.get("/odms/forms?fields=possible_actions,status")
    assert_response_status_code(response, 200)

    data = response.json()
    for item in data["items"]:
        assert item["status"] == "Final"
        assert sorted(item["possible_actions"]) == sorted(["inactivate", "new_version"])


def test_list_endpoint_possible_actions_does_not_leak_injected_deps(api_client):
    """Test that auto-injected status/version deps don't appear unless explicitly requested."""
    response = api_client.get("/odms/forms?fields=name,possible_actions")
    assert_response_status_code(response, 200)

    data = response.json()
    first_item = data["items"][0]
    # status and version were injected internally but must not appear in the response
    assert "status" not in first_item
    assert "version" not in first_item
    assert set(first_item.keys()) == {"uid", "name", "possible_actions"}


def test_list_endpoint_possible_actions_with_explicit_status_and_version(api_client):
    """Test that status/version appear normally when also explicitly requested alongside possible_actions."""
    response = api_client.get("/odms/forms?fields=name,status,version,possible_actions")
    assert_response_status_code(response, 200)

    data = response.json()
    first_item = data["items"][0]
    assert set(first_item.keys()) == {
        "uid",
        "name",
        "status",
        "version",
        "possible_actions",
    }
    assert first_item["status"] == "Final"
    assert sorted(first_item["possible_actions"]) == sorted(
        ["inactivate", "new_version"]
    )


def test_single_entity_endpoint_with_possible_actions_field(api_client, test_data):
    """Test that single-entity endpoint returns possible_actions when requested."""
    uid = test_data["form"].uid

    response = api_client.get(f"/odms/forms/{uid}?fields=name,possible_actions")
    assert_response_status_code(response, 200)

    data = response.json()
    assert set(data.keys()) == {"uid", "name", "possible_actions"}
    assert isinstance(data["possible_actions"], list)
    assert sorted(data["possible_actions"]) == sorted(["inactivate", "new_version"])


@pytest.mark.parametrize(
    "endpoint,uid_key",
    [
        ("odms/forms/{uid}", "form"),
        ("odms/items/{uid}", "item"),
        ("odms/item-groups/{uid}", "item_group"),
        ("odms/study-events/{uid}", "study_event"),
        ("odms/conditions/{uid}", "condition"),
        ("odms/methods/{uid}", "method"),
    ],
)
def test_possible_actions_field_supported_across_odm_types(
    api_client, test_data, endpoint, uid_key
):
    """Test that possible_actions works for all ODM entity types."""
    uid = test_data[uid_key].uid
    url = f"/{endpoint.format(uid=uid)}?fields=possible_actions"

    response = api_client.get(url)
    assert_response_status_code(response, 200)

    data = response.json()
    assert "possible_actions" in data
    assert isinstance(data["possible_actions"], list)
    assert sorted(data["possible_actions"]) == sorted(["inactivate", "new_version"])


# ==================== Wildcard Filtering with Fields Tests ====================


def test_wildcard_filter_with_fields_parameter(api_client):
    """Test that wildcard filtering only searches in fields specified by fields parameter"""
    # When fields parameter is provided, wildcard should only search those fields
    response = api_client.get(
        '/odms/forms?fields=name,oid&filters={"*":{"v":["Test"],"op":"co"}}'
    )
    assert_response_status_code(response, 200)

    data = response.json()
    # Should only return items where "Test" is found in name or oid fields
    # (not in other fields that are not requested)
    assert "items" in data


def test_wildcard_filter_without_fields_parameter(api_client):
    """Test that wildcard filtering searches all fields when fields parameter is not provided"""
    response = api_client.get('/odms/forms?filters={"*":{"v":["Test"],"op":"co"}}')
    assert_response_status_code(response, 200)

    data = response.json()
    # Should return items where "Test" is found in any searchable field
    assert "items" in data
