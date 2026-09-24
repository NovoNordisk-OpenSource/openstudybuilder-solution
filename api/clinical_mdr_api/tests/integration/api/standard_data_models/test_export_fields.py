"""
Tests for export_fields query parameter functionality
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

import csv
import io
import logging

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import (
    assert_response_content_type,
    assert_response_status_code,
)

log = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "export-fields.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    # Create a data model with some datasets and variables
    data_model_catalogue_name = TestUtils.create_data_model_catalogue()
    data_model = TestUtils.create_data_model()
    data_model_ig = TestUtils.create_data_model_ig(
        implemented_data_model=data_model.uid,
    )
    dataset_class = TestUtils.create_dataset_class(
        data_model_uid=data_model.uid,
        data_model_name=data_model.name,
        data_model_catalogue_name=data_model_catalogue_name,
    )
    dataset = TestUtils.create_dataset(
        data_model_ig_uid=data_model_ig.uid,
        data_model_ig_version_number=data_model_ig.version_number,
        implemented_dataset_class_name=dataset_class.uid,
        data_model_catalogue_name=data_model_catalogue_name,
    )
    variable_class = TestUtils.create_variable_class(
        dataset_class_uid=dataset_class.uid,
        data_model_catalogue_name=data_model_catalogue_name,
        data_model_name=data_model.uid,
        data_model_version=data_model.version_number,
    )
    dataset_variable = TestUtils.create_dataset_variable(
        dataset_uid=dataset.uid,
        data_model_catalogue_name=data_model_catalogue_name,
        data_model_ig_name=data_model_ig.uid,
        data_model_ig_version=data_model_ig.version_number,
        class_variable_uid=variable_class.uid,
    )

    # Create sponsor model
    sponsor_model = TestUtils.create_sponsor_model(
        ig_uid=data_model_ig.uid,
        ig_version_number=data_model_ig.version_number,
        version_number="1",
    )
    sponsor_dataset = TestUtils.create_sponsor_dataset(
        dataset_uid=dataset.uid,
        sponsor_model_name=sponsor_model.name,
        sponsor_model_version_number=sponsor_model.version,
        implemented_dataset_class=dataset_class.uid,
    )
    sponsor_variable = TestUtils.create_sponsor_dataset_variable(
        dataset_uid=sponsor_dataset.uid,
        dataset_variable_uid=dataset_variable.uid,
        sponsor_model_name=sponsor_model.name,
        sponsor_model_version_number=sponsor_model.version,
    )

    yield {
        "data_model_catalogue_name": data_model_catalogue_name,
        "data_model": data_model,
        "data_model_ig": data_model_ig,
        "dataset_class": dataset_class,
        "dataset": dataset,
        "variable_class": variable_class,
        "dataset_variable": dataset_variable,
        "sponsor_model": sponsor_model,
        "sponsor_dataset": sponsor_dataset,
        "sponsor_variable": sponsor_variable,
    }


def test_export_with_default_fields(api_client, test_data):
    """Test CSV export with default fields (no export_fields parameter)"""
    url = "/standards/sponsor-models/dataset-variables"
    params = {"sponsor_model_name": test_data["sponsor_model"].name}
    headers = {"Accept": "text/csv"}

    response = api_client.get(url, params=params, headers=headers)

    assert_response_status_code(response, 200)
    assert_response_content_type(response, "text/csv")

    # Parse CSV to check default fields
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    assert len(rows) > 0
    # Default fields are ["uid", "dataset.uid"]
    assert "uid" in rows[0]
    assert "dataset.uid" in rows[0]


def test_export_with_custom_fields_csv(api_client, test_data):
    """Test CSV export with custom fields via export_fields parameter"""
    url = "/standards/sponsor-models/dataset-variables"
    params = {
        "sponsor_model_name": test_data["sponsor_model"].name,
        "export_fields": "uid,name,label",
    }
    headers = {"Accept": "text/csv"}

    response = api_client.get(url, params=params, headers=headers)

    assert_response_status_code(response, 200)
    assert_response_content_type(response, "text/csv")

    # Parse CSV to check custom fields
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    assert len(rows) > 0
    # Only the specified fields should be present
    assert "uid" in rows[0]
    assert "name" in rows[0]
    assert "label" in rows[0]
    # Default fields should not be present if not specified
    assert len(rows[0].keys()) == 3


def test_export_with_nested_fields(api_client, test_data):
    """Test export with nested field notation (e.g., dataset.uid)"""
    url = "/standards/sponsor-models/dataset-variables"
    params = {
        "sponsor_model_name": test_data["sponsor_model"].name,
        "export_fields": "uid,name,dataset.uid,dataset.name",
    }
    headers = {"Accept": "text/csv"}

    response = api_client.get(url, params=params, headers=headers)

    assert_response_status_code(response, 200)
    assert_response_content_type(response, "text/csv")

    # Parse CSV to check nested fields
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    assert len(rows) > 0
    assert "uid" in rows[0]
    assert "name" in rows[0]
    assert "dataset.uid" in rows[0]
    assert "dataset.name" in rows[0]


def test_export_with_custom_fields_excel(api_client, test_data):
    """Test Excel export with custom fields"""
    url = "/standards/sponsor-models/dataset-variables"
    params = {
        "sponsor_model_name": test_data["sponsor_model"].name,
        "export_fields": "uid,name",
    }
    headers = {
        "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }

    response = api_client.get(url, params=params, headers=headers)

    assert_response_status_code(response, 200)
    assert_response_content_type(
        response,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    # Just verify it returns valid Excel data
    TestUtils.assert_valid_excel(response.content)


def test_export_with_custom_fields_xml(api_client, test_data):
    """Test XML export with custom fields"""
    url = "/standards/sponsor-models/dataset-variables"
    params = {
        "sponsor_model_name": test_data["sponsor_model"].name,
        "export_fields": "uid,name,status",
    }
    headers = {"Accept": "text/xml"}

    response = api_client.get(url, params=params, headers=headers)

    assert_response_status_code(response, 200)
    assert_response_content_type(response, "text/xml")
    # Just verify it returns valid XML data
    TestUtils.assert_valid_xml(response.content.decode("utf-8"))


def test_export_fields_whitespace_handling(api_client, test_data):
    """Test that export_fields parameter handles whitespace correctly"""
    url = "/standards/sponsor-models/dataset-variables"
    params = {
        "sponsor_model_name": test_data["sponsor_model"].name,
        "export_fields": "uid, name , label ",  # Note the extra spaces
    }
    headers = {"Accept": "text/csv"}

    response = api_client.get(url, params=params, headers=headers)

    assert_response_status_code(response, 200)

    # Parse CSV to verify fields are correctly parsed despite whitespace
    csv_content = response.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    assert len(rows) > 0
    assert "uid" in rows[0]
    assert "name" in rows[0]
    assert "label" in rows[0]


def test_json_response_not_affected_by_export_fields(api_client, test_data):
    """Test that export_fields does not affect JSON responses (only exports)"""
    url = "/standards/sponsor-models/dataset-variables"
    params = {
        "sponsor_model_name": test_data["sponsor_model"].name,
        "export_fields": "uid,name",  # Should be ignored for JSON
    }
    # No Accept header, defaults to JSON

    response = api_client.get(url, params=params)

    assert_response_status_code(response, 200)
    assert_response_content_type(response, "application/json")

    # JSON response should include all fields, not just export_fields
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0
    # Should have more than just uid and name
    assert "uid" in data["items"][0]
    # Other fields should also be present
    assert len(data["items"][0].keys()) > 2
