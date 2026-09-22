"""Tests for NSV create payload rules used by the library form."""

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

# pylint: disable=unused-argument,redefined-outer-name


@pytest.fixture(scope="module")
def api_client(test_data):
    """FastAPI client bound to the NSV form test database."""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Seed instance classes, DATATYPE, and role terms for NSV create tests."""
    inject_and_clear_db("nsv-form.api")
    inject_base_data()
    instance_class = TestUtils.create_activity_instance_class(
        name="MCP NSV Instance Class"
    )
    instance_class_2 = TestUtils.create_activity_instance_class(
        name="MCP NSV Instance Class 2"
    )
    data_type_codelist = TestUtils.create_ct_codelist(
        name="DATATYPE",
        submission_value="DATATYPE",
        extensible=True,
        approve=True,
    )
    data_type_term = TestUtils.create_ct_term(
        sponsor_preferred_name="CT Term",
        codelist_uid=data_type_codelist.codelist_uid,
    )
    role_codelist = TestUtils.create_ct_codelist(
        name="ROLE",
        submission_value="ROLE",
        extensible=True,
        approve=True,
    )
    role_term = TestUtils.create_ct_term(
        sponsor_preferred_name="Record Qualifier",
        codelist_uid=role_codelist.codelist_uid,
    )
    return {
        "instance_class": instance_class,
        "instance_class_2": instance_class_2,
        "data_type_term": data_type_term,
        "role_term": role_term,
    }


def _aic_rel(uid):
    return {
        "uid": uid,
        "mandatory": False,
        "is_adam_param_specific_enabled": False,
        "is_additional_optional": False,
        "is_default_linked": False,
    }


def _nsv_payload(test_data, **nsv_overrides):
    nsv = {
        "code": "MCPNSV1",
        "is_multiple": False,
        "length": 8,
        "is_cdisc_defined": False,
    }
    nsv.update(nsv_overrides)
    return {
        "name": "mcp nsv form payload",
        "order": 201,
        "library_name": "Sponsor",
        "activity_instance_classes": [_aic_rel(test_data["instance_class"].uid)],
        "role_uid": test_data["role_term"].term_uid,
        "data_type_uid": test_data["data_type_term"].term_uid,
        "non_standard_variable": nsv,
    }


def test_post_nsv_without_is_cdisc_defined_returns_400(api_client, test_data):
    """Omitting is_cdisc_defined on NSV create is rejected with HTTP 400."""
    payload = _nsv_payload(test_data)
    del payload["non_standard_variable"]["is_cdisc_defined"]
    payload["name"] = "mcp nsv missing cdisc defined"
    response = api_client.post("/activity-item-classes", json=payload)
    assert_response_status_code(response, 400)
    assert "is_cdisc_defined" in response.text


def test_post_nsv_with_multiple_activity_instance_classes(api_client, test_data):
    """NSV create with is_multiple can attach more than one instance class."""
    payload = _nsv_payload(test_data, is_multiple=True, code="MCPNSVM", length=7)
    payload["name"] = "mcp nsv multiple aic"
    payload["activity_instance_classes"] = [
        _aic_rel(test_data["instance_class"].uid),
        _aic_rel(test_data["instance_class_2"].uid),
    ]
    response = api_client.post("/activity-item-classes", json=payload)
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["non_standard_variable"]["is_multiple"] is True
    returned_uids = {item["uid"] for item in res["activity_instance_classes"]}
    assert test_data["instance_class"].uid in returned_uids
    assert test_data["instance_class_2"].uid in returned_uids
