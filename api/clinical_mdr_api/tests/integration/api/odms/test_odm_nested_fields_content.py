# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

# Tests for the `?fields=` query parameter with every nested relationship field
# on every ODM endpoint (both single-entity and list variants).
#
# Each test:
#   1. Requests only the nested field via `?fields=<field>`
#   2. Asserts that the response contains *only* `uid` + the requested field
#   3. Asserts that the nested field has the correct sub-structure and content

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
    inject_and_clear_db("odm.nested.fields.param")
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

    client = TestClient(app)

    # ---- Vendor infrastructure ----
    vendor_namespace = TestUtils.create_odm_vendor_namespace(
        name="TestNamespace",
        prefix="tns",
        url="http://tns.example.com",
        approve=True,
    )
    vendor_element = TestUtils.create_odm_vendor_element(
        name="TestElement",
        vendor_namespace_uid=vendor_namespace.uid,
        compatible_types=["FormDef", "ItemGroupDef", "ItemDef"],
        approve=True,
    )
    vendor_attr_ns = TestUtils.create_odm_vendor_attribute(
        name="nsAttribute",
        compatible_types=["FormDef", "ItemGroupDef", "ItemDef"],
        data_type="string",
        vendor_namespace_uid=vendor_namespace.uid,
        approve=True,
    )
    vendor_attr_elem = TestUtils.create_odm_vendor_attribute(
        name="elemAttribute",
        compatible_types=[],
        data_type="string",
        vendor_element_uid=vendor_element.uid,
        approve=True,
    )

    # ---- Condition ----
    condition = TestUtils.create_odm_condition(
        name="TestCondition",
        oid="COND.NESTED.001",
        formal_expressions=[
            OdmFormalExpressionModel(context="Python", expression="x > 0"),
        ],
        translated_texts=[
            OdmTranslatedTextModel(
                text_type=OdmTranslatedTextTypeEnum.DESCRIPTION,
                language="eng",
                text="Condition description",
            ),
        ],
        aliases=[OdmAliasModel(context="condctx", name="cond_alias")],
        approve=True,
    )

    # ---- Method ----
    method = TestUtils.create_odm_method(
        name="TestMethod",
        oid="METHOD.NESTED.001",
        method_type="Computation",
        formal_expressions=[
            OdmFormalExpressionModel(context="Python", expression="sum(x)"),
        ],
        translated_texts=[
            OdmTranslatedTextModel(
                text_type=OdmTranslatedTextTypeEnum.DESCRIPTION,
                language="eng",
                text="Method description",
            ),
        ],
        aliases=[OdmAliasModel(context="methctx", name="method_alias")],
        approve=True,
    )

    # ---- Item (with vendor data) ----
    item_resp = client.post(
        "/odms/items",
        json={
            "library_name": "Sponsor",
            "name": "TestItem",
            "oid": "ITEM.NESTED.001",
            "datatype_uid": "text_uid",
            "length": 200,
            "translated_texts": [
                {
                    "text_type": "Question",
                    "language": "eng",
                    "text": "What is the value?",
                },
            ],
            "aliases": [{"context": "itemctx", "name": "item_alias"}],
            "vendor_elements": [
                {"uid": vendor_element.uid, "value": "item_ve_val"},
            ],
            "vendor_attributes": [
                {"uid": vendor_attr_ns.uid, "value": "item_va_val"},
            ],
            "vendor_element_attributes": [
                {"uid": vendor_attr_elem.uid, "value": "item_vea_val"},
            ],
        },
    )
    assert_response_status_code(item_resp, 201)
    item_uid = item_resp.json()["uid"]
    client.post(f"/odms/items/{item_uid}/approvals")

    # ---- Item Group (with vendor data + item) ----
    ig_resp = client.post(
        "/odms/item-groups",
        json={
            "library_name": "Sponsor",
            "name": "TestItemGroup",
            "oid": "IG.NESTED.001",
            "repeating": "Yes",
            "sdtm_domain_uids": [],
            "translated_texts": [
                {
                    "text_type": "Description",
                    "language": "eng",
                    "text": "IG description",
                },
            ],
            "aliases": [{"context": "igctx", "name": "ig_alias"}],
            "vendor_elements": [
                {"uid": vendor_element.uid, "value": "ig_ve_val"},
            ],
            "vendor_attributes": [
                {"uid": vendor_attr_ns.uid, "value": "ig_va_val"},
            ],
            "vendor_element_attributes": [
                {"uid": vendor_attr_elem.uid, "value": "ig_vea_val"},
            ],
        },
    )
    assert_response_status_code(ig_resp, 201)
    ig_uid = ig_resp.json()["uid"]

    add_item = client.post(
        f"/odms/item-groups/{ig_uid}/items",
        json=[
            {
                "uid": item_uid,
                "order_number": 1,
                "mandatory": "Yes",
                "collection_exception_condition_oid": None,
                "vendor": {"attributes": []},
            }
        ],
    )
    assert_response_status_code(add_item, 201)
    client.post(f"/odms/item-groups/{ig_uid}/approvals")

    # ---- Form (with vendor data + item group) ----
    form_resp = client.post(
        "/odms/forms",
        json={
            "library_name": "Sponsor",
            "name": "TestForm",
            "oid": "FORM.NESTED.001",
            "repeating": "Yes",
            "translated_texts": [
                {
                    "text_type": "Description",
                    "language": "eng",
                    "text": "Form description",
                },
            ],
            "aliases": [{"context": "formctx", "name": "form_alias"}],
            "vendor_elements": [
                {"uid": vendor_element.uid, "value": "form_ve_val"},
            ],
            "vendor_attributes": [
                {"uid": vendor_attr_ns.uid, "value": "form_va_val"},
            ],
            "vendor_element_attributes": [
                {"uid": vendor_attr_elem.uid, "value": "form_vea_val"},
            ],
        },
    )
    assert_response_status_code(form_resp, 201)
    form_uid = form_resp.json()["uid"]

    add_ig = client.post(
        f"/odms/forms/{form_uid}/item-groups",
        json=[
            {
                "uid": ig_uid,
                "order_number": 1,
                "mandatory": "Yes",
                "collection_exception_condition_oid": None,
                "vendor": {"attributes": []},
            }
        ],
    )
    assert_response_status_code(add_ig, 201)
    client.post(f"/odms/forms/{form_uid}/approvals")

    # ---- Study Event (with form) ----
    se_resp = client.post(
        "/odms/study-events",
        json={
            "library_name": "Sponsor",
            "name": "TestStudyEvent",
            "oid": "SE.NESTED.001",
            "display_in_tree": True,
        },
    )
    assert_response_status_code(se_resp, 201)
    se_uid = se_resp.json()["uid"]

    add_form = client.post(
        f"/odms/study-events/{se_uid}/forms",
        json=[
            {
                "uid": form_uid,
                "order_number": 1,
                "mandatory": "Yes",
                "locked": "No",
                "collection_exception_condition_oid": None,
            }
        ],
    )
    assert_response_status_code(add_form, 201)
    client.post(f"/odms/study-events/{se_uid}/approvals")

    yield {
        "vendor_namespace_uid": vendor_namespace.uid,
        "vendor_element_uid": vendor_element.uid,
        "vendor_attr_ns_uid": vendor_attr_ns.uid,
        "vendor_attr_elem_uid": vendor_attr_elem.uid,
        "condition_uid": condition.uid,
        "method_uid": method.uid,
        "item_uid": item_uid,
        "ig_uid": ig_uid,
        "form_uid": form_uid,
        "se_uid": se_uid,
    }

    drop_db("odm.nested.fields.param")


# ===========================================================================
# Helper
# ===========================================================================


def _only_uid_and(data, field: str) -> None:
    """Assert the dict contains only uid and the requested field."""
    assert set(data.keys()) == {
        "uid",
        field,
    }, f"Expected only {{'uid', '{field}'}}, got {set(data.keys())}"


def _list_items_only_uid_and(items, field: str) -> None:
    """Assert every item in the list contains only uid and the requested field."""
    assert len(items) > 0
    for item in items:
        assert set(item.keys()) == {
            "uid",
            field,
        }, f"Expected only {{'uid', '{field}'}}, got {set(item.keys())}"


# ===========================================================================
# Forms – ?fields= with every nested relationship field
# ===========================================================================


@pytest.mark.parametrize(
    "field",
    [
        "translated_texts",
        "aliases",
        "item_groups",
        "vendor_elements",
        "vendor_attributes",
        "vendor_element_attributes",
        "possible_actions",
    ],
)
def test_form_single_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/forms/{uid}?fields=<field> returns only uid + the requested field."""
    resp = api_client.get(f"/odms/forms/{test_data['form_uid']}?fields={field}")
    assert_response_status_code(resp, 200)
    _only_uid_and(resp.json(), field)


@pytest.mark.parametrize(
    "field",
    [
        "translated_texts",
        "aliases",
        "item_groups",
        "vendor_elements",
        "vendor_attributes",
        "vendor_element_attributes",
        "possible_actions",
    ],
)
def test_form_list_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/forms?fields=<field> returns items containing only uid + the requested field."""
    resp = api_client.get(f"/odms/forms?fields={field}")
    assert_response_status_code(resp, 200)
    _list_items_only_uid_and(resp.json()["items"], field)


def test_form_fields_translated_texts_content(api_client, test_data):
    """?fields=translated_texts returns translated_texts with text_type, language, text."""
    resp = api_client.get(
        f"/odms/forms/{test_data['form_uid']}?fields=translated_texts"
    )
    assert_response_status_code(resp, 200)
    tt_list = resp.json()["translated_texts"]
    assert len(tt_list) > 0
    tt = tt_list[0]
    assert {"text_type", "language", "text"} <= set(tt.keys())
    assert tt["text_type"] == "Description"
    assert tt["language"] == "eng"
    assert tt["text"] == "Form description"


def test_form_fields_aliases_content(api_client, test_data):
    """?fields=aliases returns aliases with context and name."""
    resp = api_client.get(f"/odms/forms/{test_data['form_uid']}?fields=aliases")
    assert_response_status_code(resp, 200)
    alias_list = resp.json()["aliases"]
    assert len(alias_list) > 0
    alias = alias_list[0]
    assert {"context", "name"} <= set(alias.keys())
    assert alias["context"] == "formctx"
    assert alias["name"] == "form_alias"


def test_form_fields_item_groups_content(api_client, test_data):
    """?fields=item_groups returns item_groups with uid, name, order_number, mandatory, vendor."""
    resp = api_client.get(f"/odms/forms/{test_data['form_uid']}?fields=item_groups")
    assert_response_status_code(resp, 200)
    ig_list = resp.json()["item_groups"]
    assert len(ig_list) > 0
    ig = ig_list[0]
    assert {"uid", "name", "order_number", "mandatory", "vendor"} <= set(ig.keys())
    assert ig["uid"] == test_data["ig_uid"]
    assert ig["order_number"] == 1
    assert ig["mandatory"] == "Yes"
    assert "attributes" in ig["vendor"]


def test_form_fields_vendor_elements_content(api_client, test_data):
    """?fields=vendor_elements returns vendor_elements with uid, name, value."""
    resp = api_client.get(f"/odms/forms/{test_data['form_uid']}?fields=vendor_elements")
    assert_response_status_code(resp, 200)
    ve_list = resp.json()["vendor_elements"]
    assert len(ve_list) > 0
    ve = ve_list[0]
    assert {"uid", "name", "value"} <= set(ve.keys())
    assert ve["uid"] == test_data["vendor_element_uid"]
    assert ve["value"] == "form_ve_val"


def test_form_fields_vendor_attributes_content(api_client, test_data):
    """?fields=vendor_attributes returns vendor_attributes with uid, name, value."""
    resp = api_client.get(
        f"/odms/forms/{test_data['form_uid']}?fields=vendor_attributes"
    )
    assert_response_status_code(resp, 200)
    va_list = resp.json()["vendor_attributes"]
    assert len(va_list) > 0
    va = va_list[0]
    assert {"uid", "name", "value"} <= set(va.keys())
    assert va["uid"] == test_data["vendor_attr_ns_uid"]
    assert va["value"] == "form_va_val"


def test_form_fields_vendor_element_attributes_content(api_client, test_data):
    """?fields=vendor_element_attributes returns vendor_element_attributes with uid, name, value."""
    resp = api_client.get(
        f"/odms/forms/{test_data['form_uid']}?fields=vendor_element_attributes"
    )
    assert_response_status_code(resp, 200)
    vea_list = resp.json()["vendor_element_attributes"]
    assert len(vea_list) > 0
    vea = vea_list[0]
    assert {"uid", "name", "value"} <= set(vea.keys())
    assert vea["uid"] == test_data["vendor_attr_elem_uid"]
    assert vea["value"] == "form_vea_val"


def test_form_fields_possible_actions_content(api_client, test_data):
    """?fields=possible_actions returns possible_actions as a list of strings."""
    resp = api_client.get(
        f"/odms/forms/{test_data['form_uid']}?fields=possible_actions"
    )
    assert_response_status_code(resp, 200)
    actions = resp.json()["possible_actions"]
    assert isinstance(actions, list)
    assert len(actions) > 0
    assert all(isinstance(a, str) for a in actions)


# ===========================================================================
# Items – ?fields= with every nested relationship field
# ===========================================================================


@pytest.mark.parametrize(
    "field",
    [
        "translated_texts",
        "aliases",
        "terms",
        "unit_definitions",
        "codelist",
        "vendor_elements",
        "vendor_attributes",
        "vendor_element_attributes",
        "possible_actions",
    ],
)
def test_item_single_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/items/{uid}?fields=<field> returns only uid + the requested field."""
    resp = api_client.get(f"/odms/items/{test_data['item_uid']}?fields={field}")
    assert_response_status_code(resp, 200)
    _only_uid_and(resp.json(), field)


@pytest.mark.parametrize(
    "field",
    [
        "translated_texts",
        "aliases",
        "terms",
        "unit_definitions",
        "codelist",
        "vendor_elements",
        "vendor_attributes",
        "vendor_element_attributes",
        "possible_actions",
    ],
)
def test_item_list_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/items?fields=<field> returns items containing only uid + the requested field."""
    resp = api_client.get(f"/odms/items?fields={field}")
    assert_response_status_code(resp, 200)
    _list_items_only_uid_and(resp.json()["items"], field)


def test_item_fields_translated_texts_content(api_client, test_data):
    """?fields=translated_texts returns translated_texts with text_type, language, text."""
    resp = api_client.get(
        f"/odms/items/{test_data['item_uid']}?fields=translated_texts"
    )
    assert_response_status_code(resp, 200)
    tt_list = resp.json()["translated_texts"]
    assert len(tt_list) > 0
    tt = tt_list[0]
    assert {"text_type", "language", "text"} <= set(tt.keys())
    assert tt["text_type"] == "Question"
    assert tt["language"] == "eng"
    assert tt["text"] == "What is the value?"


def test_item_fields_aliases_content(api_client, test_data):
    """?fields=aliases returns aliases with context and name."""
    resp = api_client.get(f"/odms/items/{test_data['item_uid']}?fields=aliases")
    assert_response_status_code(resp, 200)
    alias_list = resp.json()["aliases"]
    assert len(alias_list) > 0
    alias = alias_list[0]
    assert {"context", "name"} <= set(alias.keys())
    assert alias["context"] == "itemctx"
    assert alias["name"] == "item_alias"


def test_item_fields_terms_is_list(api_client, test_data):
    """?fields=terms returns terms as a list."""
    resp = api_client.get(f"/odms/items/{test_data['item_uid']}?fields=terms")
    assert_response_status_code(resp, 200)
    assert isinstance(resp.json()["terms"], list)


def test_item_fields_unit_definitions_is_list(api_client, test_data):
    """?fields=unit_definitions returns unit_definitions as a list."""
    resp = api_client.get(
        f"/odms/items/{test_data['item_uid']}?fields=unit_definitions"
    )
    assert_response_status_code(resp, 200)
    assert isinstance(resp.json()["unit_definitions"], list)


def test_item_fields_codelist_is_nullable(api_client, test_data):
    """?fields=codelist returns codelist field (null when not set)."""
    resp = api_client.get(f"/odms/items/{test_data['item_uid']}?fields=codelist")
    assert_response_status_code(resp, 200)
    assert "codelist" in resp.json()


def test_item_fields_vendor_elements_content(api_client, test_data):
    """?fields=vendor_elements returns vendor_elements with uid, name, value."""
    resp = api_client.get(f"/odms/items/{test_data['item_uid']}?fields=vendor_elements")
    assert_response_status_code(resp, 200)
    ve_list = resp.json()["vendor_elements"]
    assert len(ve_list) > 0
    ve = ve_list[0]
    assert {"uid", "name", "value"} <= set(ve.keys())
    assert ve["uid"] == test_data["vendor_element_uid"]
    assert ve["value"] == "item_ve_val"


def test_item_fields_vendor_attributes_content(api_client, test_data):
    """?fields=vendor_attributes returns vendor_attributes with uid, name, value."""
    resp = api_client.get(
        f"/odms/items/{test_data['item_uid']}?fields=vendor_attributes"
    )
    assert_response_status_code(resp, 200)
    va_list = resp.json()["vendor_attributes"]
    assert len(va_list) > 0
    va = va_list[0]
    assert {"uid", "name", "value"} <= set(va.keys())
    assert va["uid"] == test_data["vendor_attr_ns_uid"]
    assert va["value"] == "item_va_val"


def test_item_fields_vendor_element_attributes_content(api_client, test_data):
    """?fields=vendor_element_attributes returns vendor_element_attributes with uid, name, value."""
    resp = api_client.get(
        f"/odms/items/{test_data['item_uid']}?fields=vendor_element_attributes"
    )
    assert_response_status_code(resp, 200)
    vea_list = resp.json()["vendor_element_attributes"]
    assert len(vea_list) > 0
    vea = vea_list[0]
    assert {"uid", "name", "value"} <= set(vea.keys())
    assert vea["uid"] == test_data["vendor_attr_elem_uid"]
    assert vea["value"] == "item_vea_val"


def test_item_fields_possible_actions_content(api_client, test_data):
    """?fields=possible_actions returns possible_actions as a list of strings."""
    resp = api_client.get(
        f"/odms/items/{test_data['item_uid']}?fields=possible_actions"
    )
    assert_response_status_code(resp, 200)
    actions = resp.json()["possible_actions"]
    assert isinstance(actions, list)
    assert len(actions) > 0
    assert all(isinstance(a, str) for a in actions)


# ===========================================================================
# Item Groups – ?fields= with every nested relationship field
# ===========================================================================


@pytest.mark.parametrize(
    "field",
    [
        "translated_texts",
        "aliases",
        "sdtm_domains",
        "items",
        "vendor_elements",
        "vendor_attributes",
        "vendor_element_attributes",
        "possible_actions",
    ],
)
def test_item_group_single_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/item-groups/{uid}?fields=<field> returns only uid + the requested field."""
    resp = api_client.get(f"/odms/item-groups/{test_data['ig_uid']}?fields={field}")
    assert_response_status_code(resp, 200)
    _only_uid_and(resp.json(), field)


@pytest.mark.parametrize(
    "field",
    [
        "translated_texts",
        "aliases",
        "sdtm_domains",
        "items",
        "vendor_elements",
        "vendor_attributes",
        "vendor_element_attributes",
        "possible_actions",
    ],
)
def test_item_group_list_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/item-groups?fields=<field> returns items containing only uid + field."""
    resp = api_client.get(f"/odms/item-groups?fields={field}")
    assert_response_status_code(resp, 200)
    _list_items_only_uid_and(resp.json()["items"], field)


def test_item_group_fields_translated_texts_content(api_client, test_data):
    """?fields=translated_texts returns translated_texts with text_type, language, text."""
    resp = api_client.get(
        f"/odms/item-groups/{test_data['ig_uid']}?fields=translated_texts"
    )
    assert_response_status_code(resp, 200)
    tt_list = resp.json()["translated_texts"]
    assert len(tt_list) > 0
    tt = tt_list[0]
    assert {"text_type", "language", "text"} <= set(tt.keys())
    assert tt["text_type"] == "Description"
    assert tt["language"] == "eng"
    assert tt["text"] == "IG description"


def test_item_group_fields_aliases_content(api_client, test_data):
    """?fields=aliases returns aliases with context and name."""
    resp = api_client.get(f"/odms/item-groups/{test_data['ig_uid']}?fields=aliases")
    assert_response_status_code(resp, 200)
    alias_list = resp.json()["aliases"]
    assert len(alias_list) > 0
    alias = alias_list[0]
    assert {"context", "name"} <= set(alias.keys())
    assert alias["context"] == "igctx"
    assert alias["name"] == "ig_alias"


def test_item_group_fields_items_content(api_client, test_data):
    """?fields=items returns items with uid, name, order_number, mandatory, vendor."""
    resp = api_client.get(f"/odms/item-groups/{test_data['ig_uid']}?fields=items")
    assert_response_status_code(resp, 200)
    item_list = resp.json()["items"]
    assert len(item_list) > 0
    item_ref = item_list[0]
    assert {"uid", "name", "order_number", "mandatory", "vendor"} <= set(
        item_ref.keys()
    )
    assert item_ref["uid"] == test_data["item_uid"]
    assert item_ref["order_number"] == 1
    assert item_ref["mandatory"] == "Yes"
    assert "attributes" in item_ref["vendor"]


def test_item_group_fields_sdtm_domains_is_list(api_client, test_data):
    """?fields=sdtm_domains returns sdtm_domains as a list."""
    resp = api_client.get(
        f"/odms/item-groups/{test_data['ig_uid']}?fields=sdtm_domains"
    )
    assert_response_status_code(resp, 200)
    assert isinstance(resp.json()["sdtm_domains"], list)


def test_item_group_fields_vendor_elements_content(api_client, test_data):
    """?fields=vendor_elements returns vendor_elements with uid, name, value."""
    resp = api_client.get(
        f"/odms/item-groups/{test_data['ig_uid']}?fields=vendor_elements"
    )
    assert_response_status_code(resp, 200)
    ve_list = resp.json()["vendor_elements"]
    assert len(ve_list) > 0
    ve = ve_list[0]
    assert {"uid", "name", "value"} <= set(ve.keys())
    assert ve["uid"] == test_data["vendor_element_uid"]
    assert ve["value"] == "ig_ve_val"


def test_item_group_fields_vendor_attributes_content(api_client, test_data):
    """?fields=vendor_attributes returns vendor_attributes with uid, name, value."""
    resp = api_client.get(
        f"/odms/item-groups/{test_data['ig_uid']}?fields=vendor_attributes"
    )
    assert_response_status_code(resp, 200)
    va_list = resp.json()["vendor_attributes"]
    assert len(va_list) > 0
    va = va_list[0]
    assert {"uid", "name", "value"} <= set(va.keys())
    assert va["uid"] == test_data["vendor_attr_ns_uid"]
    assert va["value"] == "ig_va_val"


def test_item_group_fields_vendor_element_attributes_content(api_client, test_data):
    """?fields=vendor_element_attributes returns vendor_element_attributes with uid, name, value."""
    resp = api_client.get(
        f"/odms/item-groups/{test_data['ig_uid']}?fields=vendor_element_attributes"
    )
    assert_response_status_code(resp, 200)
    vea_list = resp.json()["vendor_element_attributes"]
    assert len(vea_list) > 0
    vea = vea_list[0]
    assert {"uid", "name", "value"} <= set(vea.keys())
    assert vea["uid"] == test_data["vendor_attr_elem_uid"]
    assert vea["value"] == "ig_vea_val"


def test_item_group_fields_possible_actions_content(api_client, test_data):
    """?fields=possible_actions returns possible_actions as a list of strings."""
    resp = api_client.get(
        f"/odms/item-groups/{test_data['ig_uid']}?fields=possible_actions"
    )
    assert_response_status_code(resp, 200)
    actions = resp.json()["possible_actions"]
    assert isinstance(actions, list)
    assert len(actions) > 0
    assert all(isinstance(a, str) for a in actions)


# ===========================================================================
# Study Events – ?fields= with every nested relationship field
# ===========================================================================


@pytest.mark.parametrize("field", ["forms", "possible_actions"])
def test_study_event_single_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/study-events/{uid}?fields=<field> returns only uid + the requested field."""
    resp = api_client.get(f"/odms/study-events/{test_data['se_uid']}?fields={field}")
    assert_response_status_code(resp, 200)
    _only_uid_and(resp.json(), field)


@pytest.mark.parametrize("field", ["forms", "possible_actions"])
def test_study_event_list_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/study-events?fields=<field> returns items containing only uid + field."""
    resp = api_client.get(f"/odms/study-events?fields={field}")
    assert_response_status_code(resp, 200)
    _list_items_only_uid_and(resp.json()["items"], field)


def test_study_event_fields_forms_content(api_client, test_data):
    """?fields=forms returns forms with uid, name, order_number, mandatory, locked,
    collection_exception_condition_oid."""
    resp = api_client.get(f"/odms/study-events/{test_data['se_uid']}?fields=forms")
    assert_response_status_code(resp, 200)
    form_list = resp.json()["forms"]
    assert len(form_list) > 0
    form_ref = form_list[0]
    assert {
        "uid",
        "name",
        "order_number",
        "mandatory",
        "locked",
        "collection_exception_condition_oid",
    } <= set(form_ref.keys())
    assert form_ref["uid"] == test_data["form_uid"]
    assert form_ref["order_number"] == 1
    assert form_ref["mandatory"] == "Yes"
    assert form_ref["locked"] == "No"


def test_study_event_fields_possible_actions_content(api_client, test_data):
    """?fields=possible_actions returns possible_actions as a list of strings."""
    resp = api_client.get(
        f"/odms/study-events/{test_data['se_uid']}?fields=possible_actions"
    )
    assert_response_status_code(resp, 200)
    actions = resp.json()["possible_actions"]
    assert isinstance(actions, list)
    assert len(actions) > 0
    assert all(isinstance(a, str) for a in actions)


# ===========================================================================
# Conditions – ?fields= with every nested relationship field
# ===========================================================================


@pytest.mark.parametrize(
    "field",
    [
        "formal_expressions",
        "translated_texts",
        "aliases",
        "possible_actions",
    ],
)
def test_condition_single_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/conditions/{uid}?fields=<field> returns only uid + the requested field."""
    resp = api_client.get(
        f"/odms/conditions/{test_data['condition_uid']}?fields={field}"
    )
    assert_response_status_code(resp, 200)
    _only_uid_and(resp.json(), field)


@pytest.mark.parametrize(
    "field",
    [
        "formal_expressions",
        "translated_texts",
        "aliases",
        "possible_actions",
    ],
)
def test_condition_list_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/conditions?fields=<field> returns items containing only uid + field."""
    resp = api_client.get(f"/odms/conditions?fields={field}")
    assert_response_status_code(resp, 200)
    _list_items_only_uid_and(resp.json()["items"], field)


def test_condition_fields_formal_expressions_content(api_client, test_data):
    """?fields=formal_expressions returns formal_expressions with context and expression."""
    resp = api_client.get(
        f"/odms/conditions/{test_data['condition_uid']}?fields=formal_expressions"
    )
    assert_response_status_code(resp, 200)
    fe_list = resp.json()["formal_expressions"]
    assert len(fe_list) > 0
    fe = fe_list[0]
    assert {"context", "expression"} <= set(fe.keys())
    assert fe["context"] == "Python"
    assert fe["expression"] == "x > 0"


def test_condition_fields_translated_texts_content(api_client, test_data):
    """?fields=translated_texts returns translated_texts with text_type, language, text."""
    resp = api_client.get(
        f"/odms/conditions/{test_data['condition_uid']}?fields=translated_texts"
    )
    assert_response_status_code(resp, 200)
    tt_list = resp.json()["translated_texts"]
    assert len(tt_list) > 0
    tt = tt_list[0]
    assert {"text_type", "language", "text"} <= set(tt.keys())
    assert tt["text_type"] == "Description"
    assert tt["language"] == "eng"
    assert tt["text"] == "Condition description"


def test_condition_fields_aliases_content(api_client, test_data):
    """?fields=aliases returns aliases with context and name."""
    resp = api_client.get(
        f"/odms/conditions/{test_data['condition_uid']}?fields=aliases"
    )
    assert_response_status_code(resp, 200)
    alias_list = resp.json()["aliases"]
    assert len(alias_list) > 0
    alias = alias_list[0]
    assert {"context", "name"} <= set(alias.keys())
    assert alias["context"] == "condctx"
    assert alias["name"] == "cond_alias"


def test_condition_fields_possible_actions_content(api_client, test_data):
    """?fields=possible_actions returns possible_actions as a list of strings."""
    resp = api_client.get(
        f"/odms/conditions/{test_data['condition_uid']}?fields=possible_actions"
    )
    assert_response_status_code(resp, 200)
    actions = resp.json()["possible_actions"]
    assert isinstance(actions, list)
    assert len(actions) > 0
    assert all(isinstance(a, str) for a in actions)


# ===========================================================================
# Methods – ?fields= with every nested relationship field
# ===========================================================================


@pytest.mark.parametrize(
    "field",
    [
        "formal_expressions",
        "translated_texts",
        "aliases",
        "possible_actions",
    ],
)
def test_method_single_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/methods/{uid}?fields=<field> returns only uid + the requested field."""
    resp = api_client.get(f"/odms/methods/{test_data['method_uid']}?fields={field}")
    assert_response_status_code(resp, 200)
    _only_uid_and(resp.json(), field)


@pytest.mark.parametrize(
    "field",
    [
        "formal_expressions",
        "translated_texts",
        "aliases",
        "possible_actions",
    ],
)
def test_method_list_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/methods?fields=<field> returns items containing only uid + field."""
    resp = api_client.get(f"/odms/methods?fields={field}")
    assert_response_status_code(resp, 200)
    _list_items_only_uid_and(resp.json()["items"], field)


def test_method_fields_formal_expressions_content(api_client, test_data):
    """?fields=formal_expressions returns formal_expressions with context and expression."""
    resp = api_client.get(
        f"/odms/methods/{test_data['method_uid']}?fields=formal_expressions"
    )
    assert_response_status_code(resp, 200)
    fe_list = resp.json()["formal_expressions"]
    assert len(fe_list) > 0
    fe = fe_list[0]
    assert {"context", "expression"} <= set(fe.keys())
    assert fe["context"] == "Python"
    assert fe["expression"] == "sum(x)"


def test_method_fields_translated_texts_content(api_client, test_data):
    """?fields=translated_texts returns translated_texts with text_type, language, text."""
    resp = api_client.get(
        f"/odms/methods/{test_data['method_uid']}?fields=translated_texts"
    )
    assert_response_status_code(resp, 200)
    tt_list = resp.json()["translated_texts"]
    assert len(tt_list) > 0
    tt = tt_list[0]
    assert {"text_type", "language", "text"} <= set(tt.keys())
    assert tt["text_type"] == "Description"
    assert tt["language"] == "eng"
    assert tt["text"] == "Method description"


def test_method_fields_aliases_content(api_client, test_data):
    """?fields=aliases returns aliases with context and name."""
    resp = api_client.get(f"/odms/methods/{test_data['method_uid']}?fields=aliases")
    assert_response_status_code(resp, 200)
    alias_list = resp.json()["aliases"]
    assert len(alias_list) > 0
    alias = alias_list[0]
    assert {"context", "name"} <= set(alias.keys())
    assert alias["context"] == "methctx"
    assert alias["name"] == "method_alias"


def test_method_fields_possible_actions_content(api_client, test_data):
    """?fields=possible_actions returns possible_actions as a list of strings."""
    resp = api_client.get(
        f"/odms/methods/{test_data['method_uid']}?fields=possible_actions"
    )
    assert_response_status_code(resp, 200)
    actions = resp.json()["possible_actions"]
    assert isinstance(actions, list)
    assert len(actions) > 0
    assert all(isinstance(a, str) for a in actions)


# ===========================================================================
# Vendor Namespaces – ?fields= with every nested relationship field
# ===========================================================================


@pytest.mark.parametrize(
    "field", ["vendor_elements", "vendor_attributes", "possible_actions"]
)
def test_vendor_namespace_single_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/vendor-namespaces/{uid}?fields=<field> returns only uid + the requested field."""
    resp = api_client.get(
        f"/odms/vendor-namespaces/{test_data['vendor_namespace_uid']}?fields={field}"
    )
    assert_response_status_code(resp, 200)
    _only_uid_and(resp.json(), field)


@pytest.mark.parametrize(
    "field", ["vendor_elements", "vendor_attributes", "possible_actions"]
)
def test_vendor_namespace_list_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/vendor-namespaces?fields=<field> returns items containing only uid + field."""
    resp = api_client.get(f"/odms/vendor-namespaces?fields={field}")
    assert_response_status_code(resp, 200)
    _list_items_only_uid_and(resp.json()["items"], field)


def test_vendor_namespace_fields_vendor_elements_content(api_client, test_data):
    """?fields=vendor_elements returns vendor_elements with uid, name, compatible_types."""
    resp = api_client.get(
        f"/odms/vendor-namespaces/{test_data['vendor_namespace_uid']}?fields=vendor_elements"
    )
    assert_response_status_code(resp, 200)
    ve_list = resp.json()["vendor_elements"]
    assert len(ve_list) > 0
    ve = ve_list[0]
    assert {"uid", "name", "compatible_types"} <= set(ve.keys())
    assert ve["uid"] == test_data["vendor_element_uid"]
    assert isinstance(ve["compatible_types"], list)


def test_vendor_namespace_fields_vendor_attributes_content(api_client, test_data):
    """?fields=vendor_attributes returns vendor_attributes with uid, name, compatible_types."""
    resp = api_client.get(
        f"/odms/vendor-namespaces/{test_data['vendor_namespace_uid']}?fields=vendor_attributes"
    )
    assert_response_status_code(resp, 200)
    va_list = resp.json()["vendor_attributes"]
    assert len(va_list) > 0
    va = va_list[0]
    assert {"uid", "name", "compatible_types"} <= set(va.keys())
    assert va["uid"] == test_data["vendor_attr_ns_uid"]
    assert isinstance(va["compatible_types"], list)


def test_vendor_namespace_fields_possible_actions_content(api_client, test_data):
    """?fields=possible_actions returns possible_actions as a list of strings."""
    resp = api_client.get(
        f"/odms/vendor-namespaces/{test_data['vendor_namespace_uid']}?fields=possible_actions"
    )
    assert_response_status_code(resp, 200)
    actions = resp.json()["possible_actions"]
    assert isinstance(actions, list)
    assert len(actions) > 0
    assert all(isinstance(a, str) for a in actions)


# ===========================================================================
# Vendor Elements – ?fields= with every nested relationship field
# ===========================================================================


@pytest.mark.parametrize(
    "field",
    [
        "compatible_types",
        "vendor_namespace",
        "vendor_attributes",
        "possible_actions",
    ],
)
def test_vendor_element_single_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/vendor-elements/{uid}?fields=<field> returns only uid + the requested field."""
    resp = api_client.get(
        f"/odms/vendor-elements/{test_data['vendor_element_uid']}?fields={field}"
    )
    assert_response_status_code(resp, 200)
    _only_uid_and(resp.json(), field)


@pytest.mark.parametrize(
    "field",
    [
        "compatible_types",
        "vendor_namespace",
        "vendor_attributes",
        "possible_actions",
    ],
)
def test_vendor_element_list_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/vendor-elements?fields=<field> returns items containing only uid + field."""
    resp = api_client.get(f"/odms/vendor-elements?fields={field}")
    assert_response_status_code(resp, 200)
    _list_items_only_uid_and(resp.json()["items"], field)


def test_vendor_element_fields_compatible_types_content(api_client, test_data):
    """?fields=compatible_types returns compatible_types as a list of strings."""
    resp = api_client.get(
        f"/odms/vendor-elements/{test_data['vendor_element_uid']}?fields=compatible_types"
    )
    assert_response_status_code(resp, 200)
    ct = resp.json()["compatible_types"]
    assert isinstance(ct, list)
    assert len(ct) > 0
    assert all(isinstance(t, str) for t in ct)
    assert "FormDef" in ct


def test_vendor_element_fields_vendor_namespace_content(api_client, test_data):
    """?fields=vendor_namespace returns vendor_namespace with uid, name, prefix, url."""
    resp = api_client.get(
        f"/odms/vendor-elements/{test_data['vendor_element_uid']}?fields=vendor_namespace"
    )
    assert_response_status_code(resp, 200)
    vns = resp.json()["vendor_namespace"]
    assert vns is not None
    assert {"uid", "name", "prefix", "url"} <= set(vns.keys())
    assert vns["uid"] == test_data["vendor_namespace_uid"]
    assert vns["prefix"] == "tns"
    assert vns["url"] == "http://tns.example.com"


def test_vendor_element_fields_vendor_attributes_content(api_client, test_data):
    """?fields=vendor_attributes returns vendor_attributes with uid, name, compatible_types."""
    resp = api_client.get(
        f"/odms/vendor-elements/{test_data['vendor_element_uid']}?fields=vendor_attributes"
    )
    assert_response_status_code(resp, 200)
    va_list = resp.json()["vendor_attributes"]
    assert len(va_list) > 0
    va = va_list[0]
    assert {"uid", "name", "compatible_types"} <= set(va.keys())
    assert va["uid"] == test_data["vendor_attr_elem_uid"]


def test_vendor_element_fields_possible_actions_content(api_client, test_data):
    """?fields=possible_actions returns possible_actions as a list of strings."""
    resp = api_client.get(
        f"/odms/vendor-elements/{test_data['vendor_element_uid']}?fields=possible_actions"
    )
    assert_response_status_code(resp, 200)
    actions = resp.json()["possible_actions"]
    assert isinstance(actions, list)
    assert len(actions) > 0
    assert all(isinstance(a, str) for a in actions)


# ===========================================================================
# Vendor Attributes – ?fields= with every nested relationship field
# ===========================================================================


@pytest.mark.parametrize(
    "field",
    [
        "compatible_types",
        "vendor_namespace",
        "vendor_element",
        "possible_actions",
    ],
)
def test_vendor_attribute_single_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/vendor-attributes/{uid}?fields=<field> returns only uid + the requested field."""
    resp = api_client.get(
        f"/odms/vendor-attributes/{test_data['vendor_attr_ns_uid']}?fields={field}"
    )
    assert_response_status_code(resp, 200)
    _only_uid_and(resp.json(), field)


@pytest.mark.parametrize(
    "field",
    [
        "compatible_types",
        "vendor_namespace",
        "vendor_element",
        "possible_actions",
    ],
)
def test_vendor_attribute_list_fields_param_returns_only_requested_nested_field(
    api_client, test_data, field
):
    """GET /odms/vendor-attributes?fields=<field> returns items containing only uid + field."""
    resp = api_client.get(f"/odms/vendor-attributes?fields={field}")
    assert_response_status_code(resp, 200)
    _list_items_only_uid_and(resp.json()["items"], field)


def test_vendor_attribute_fields_compatible_types_content(api_client, test_data):
    """?fields=compatible_types returns compatible_types as a list of strings."""
    resp = api_client.get(
        f"/odms/vendor-attributes/{test_data['vendor_attr_ns_uid']}?fields=compatible_types"
    )
    assert_response_status_code(resp, 200)
    ct = resp.json()["compatible_types"]
    assert isinstance(ct, list)
    assert len(ct) > 0
    assert all(isinstance(t, str) for t in ct)


def test_vendor_attribute_ns_level_fields_vendor_namespace_content(
    api_client, test_data
):
    """Namespace-level ?fields=vendor_namespace returns vendor_namespace with uid, name, prefix, url."""
    resp = api_client.get(
        f"/odms/vendor-attributes/{test_data['vendor_attr_ns_uid']}?fields=vendor_namespace"
    )
    assert_response_status_code(resp, 200)
    vns = resp.json()["vendor_namespace"]
    assert vns is not None
    assert {"uid", "name", "prefix", "url"} <= set(vns.keys())
    assert vns["uid"] == test_data["vendor_namespace_uid"]


def test_vendor_attribute_ns_level_fields_vendor_element_is_none(api_client, test_data):
    """Namespace-level ?fields=vendor_element returns null vendor_element."""
    resp = api_client.get(
        f"/odms/vendor-attributes/{test_data['vendor_attr_ns_uid']}?fields=vendor_element"
    )
    assert_response_status_code(resp, 200)
    assert resp.json()["vendor_element"] is None


def test_vendor_attribute_elem_level_fields_vendor_element_content(
    api_client, test_data
):
    """Element-level ?fields=vendor_element returns vendor_element with uid, name, compatible_types."""
    resp = api_client.get(
        f"/odms/vendor-attributes/{test_data['vendor_attr_elem_uid']}?fields=vendor_element"
    )
    assert_response_status_code(resp, 200)
    ve = resp.json()["vendor_element"]
    assert ve is not None
    assert {"uid", "name", "compatible_types"} <= set(ve.keys())
    assert ve["uid"] == test_data["vendor_element_uid"]
    assert isinstance(ve["compatible_types"], list)


def test_vendor_attribute_elem_level_fields_vendor_namespace_is_none(
    api_client, test_data
):
    """Element-level ?fields=vendor_namespace returns null vendor_namespace."""
    resp = api_client.get(
        f"/odms/vendor-attributes/{test_data['vendor_attr_elem_uid']}?fields=vendor_namespace"
    )
    assert_response_status_code(resp, 200)
    assert resp.json()["vendor_namespace"] is None


def test_vendor_attribute_fields_possible_actions_content(api_client, test_data):
    """?fields=possible_actions returns possible_actions as a list of strings."""
    resp = api_client.get(
        f"/odms/vendor-attributes/{test_data['vendor_attr_ns_uid']}?fields=possible_actions"
    )
    assert_response_status_code(resp, 200)
    actions = resp.json()["possible_actions"]
    assert isinstance(actions, list)
    assert len(actions) > 0
    assert all(isinstance(a, str) for a in actions)
