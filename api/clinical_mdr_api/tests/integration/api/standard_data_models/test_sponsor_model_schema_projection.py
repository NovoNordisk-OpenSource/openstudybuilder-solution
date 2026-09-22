"""
Tests that sponsor-defined (extensible) fields flow through the API in both
directions, driven by the Sponsor Model's schema version.
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

import logging

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.standard_data_models.data_model import DataModel
from clinical_mdr_api.models.standard_data_models.data_model_ig import DataModelIG
from clinical_mdr_api.models.standard_data_models.dataset import (
    Dataset as DatasetAPIModel,
)
from clinical_mdr_api.models.standard_data_models.dataset_class import (
    DatasetClass as DatasetClassAPIModel,
)
from clinical_mdr_api.models.standard_data_models.dataset_variable import (
    DatasetVariable as DatasetVariableAPIModel,
)
from clinical_mdr_api.models.standard_data_models.variable_class import (
    VariableClass as VariableClassAPIModel,
)
from clinical_mdr_api.services.standard_data_models.sponsor_model_schema_interpreter import (
    _INTERPRETER_CACHE,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import (
    SPONSOR_LIBRARY_NAME,
    TestUtils,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Schema version 2 declares an extensible dataset field `foo` and variable field `bar`.
SCHEMA_V2 = """
entities:
  sponsor_model:
    extensible:
      - api_field: sm_foo
        type: string
  dataset:
    structural:
      - api_field: is_basic_std
        type: boolean
    extensible:
      - api_field: foo
        type: string
  dataset_variable:
    structural:
      - api_field: is_basic_std
        type: boolean
    extensible:
      - api_field: bar
        type: string
"""

# Version 3 declares a DIFFERENT extensible dataset field (`baz`, not `foo`).
SCHEMA_V3 = """
entities:
  dataset:
    extensible:
      - api_field: baz
        type: string
"""

data_model_catalogue_name: str
data_model: DataModel
data_model_ig: DataModelIG
dataset_classes: list[DatasetClassAPIModel]
variable_classes: list[VariableClassAPIModel]
datasets: list[DatasetAPIModel]
dataset_variables: list[DatasetVariableAPIModel]


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("sponsor-model-schema-projection.api")
    inject_base_data()
    _INTERPRETER_CACHE.clear()

    global data_model_catalogue_name, data_model, data_model_ig
    global dataset_classes, variable_classes, datasets, dataset_variables

    data_model_catalogue_name = TestUtils.create_data_model_catalogue(
        name="DataModelCatalogueA"
    )
    data_model = TestUtils.create_data_model(name="DataModelA")
    data_model_ig = TestUtils.create_data_model_ig(
        name="DataModelIGA", version_number="1", implemented_data_model=data_model.uid
    )
    dataset_classes = [
        TestUtils.create_dataset_class(
            label=f"DatasetClass{i} label",
            data_model_uid=data_model.uid,
            data_model_catalogue_name=data_model_catalogue_name,
            data_model_name=data_model.name,
        )
        for i in range(2)
    ]
    variable_classes = [
        TestUtils.create_variable_class(
            label=f"VariableClass{i} label",
            data_model_catalogue_name=data_model_catalogue_name,
            dataset_class_uid=dataset_classes[i].uid,
            data_model_name=data_model.uid,
            data_model_version=data_model.version_number,
        )
        for i in range(2)
    ]
    datasets = [
        TestUtils.create_dataset(
            label=f"Dataset{i} label",
            data_model_catalogue_name=data_model_catalogue_name,
            data_model_ig_uid=data_model_ig.uid,
            data_model_ig_version_number=data_model_ig.version_number,
            implemented_dataset_class_name=dataset_classes[i].uid,
        )
        for i in range(2)
    ]
    dataset_variables = [
        TestUtils.create_dataset_variable(
            label=f"DatasetVariable{i} label",
            data_model_catalogue_name=data_model_catalogue_name,
            data_model_ig_name=data_model_ig.uid,
            data_model_ig_version=data_model_ig.version_number,
            dataset_uid=datasets[i].uid,
            class_variable_uid=variable_classes[i].uid,
        )
        for i in range(2)
    ]
    yield


def _publish_schema(api_client, version: int, schema: str):
    return api_client.post(
        "/standards/sponsor-models/schema",
        json={"schema_version": version, "schema": schema},
    )


def _create_sponsor_model(api_client, version_number: str, schema_version: int | None):
    body = {
        "ig_uid": data_model_ig.uid,
        "ig_version_number": data_model_ig.version_number,
        "version_number": version_number,
        "library_name": SPONSOR_LIBRARY_NAME,
    }
    if schema_version is not None:
        body["schema_version"] = schema_version
    response = api_client.post("/standards/sponsor-models/models", json=body)
    assert_response_status_code(response, 201)
    return response.json()


def test_extensible_dataset_field_flows_through(api_client):
    assert_response_status_code(_publish_schema(api_client, 2, SCHEMA_V2), 201)
    sponsor_model = _create_sponsor_model(api_client, "1", schema_version=2)

    # Create a dataset carrying the sponsor-defined `foo` field.
    create = api_client.post(
        "/standards/sponsor-models/datasets",
        json={
            "target_data_model_catalogue": data_model_catalogue_name,
            "dataset_uid": datasets[0].uid,
            "sponsor_model_name": sponsor_model["name"],
            "sponsor_model_version_number": sponsor_model["version"],
            "implemented_dataset_class": dataset_classes[0].uid,
            "is_basic_std": True,
            "is_cdisc_std": True,
            "foo": "sponsor-value",
        },
    )
    assert_response_status_code(create, 201)
    # Create response already round-trips the extra.
    assert create.json()["foo"] == "sponsor-value"

    # The regression this task fixes: GET/list must return `foo`, not drop it.
    listing = api_client.get(
        "/standards/sponsor-models/datasets",
        params={"sponsor_model_name": sponsor_model["name"]},
    )
    assert_response_status_code(listing, 200)
    rows = {row["uid"]: row for row in listing.json()["items"]}
    assert datasets[0].uid in rows
    assert rows[datasets[0].uid]["foo"] == "sponsor-value"


def test_extensible_sponsor_model_field_flows_through(api_client):
    # Sponsor model with a sponsor-defined field, following schema v2.
    response = api_client.post(
        "/standards/sponsor-models/models",
        json={
            "ig_uid": data_model_ig.uid,
            "ig_version_number": data_model_ig.version_number,
            "version_number": "5",
            "library_name": SPONSOR_LIBRARY_NAME,
            "schema_version": 2,
            "sm_foo": "sm-value",
        },
    )
    assert_response_status_code(response, 201)
    assert response.json()["sm_foo"] == "sm-value"

    listing = api_client.get("/standards/sponsor-models/models")
    assert_response_status_code(listing, 200)
    match = [row for row in listing.json()["items"] if row.get("sm_foo") == "sm-value"]
    assert match, "sponsor-defined field sm_foo was dropped on read"
    # Structural fields resolved via the versioned traversal must survive the
    # schema-version fetch (regression: a second traverse dropped extends_version,
    # nulling extended_implementation_guide on the /models listing).
    row = match[0]
    assert (
        row["extended_implementation_guide"] == data_model_ig.name
    ), "extended_implementation_guide was dropped on the /models listing"
    assert row["schema_version"] == 2


def test_child_read_reflects_its_own_parent_schema(api_client):
    # Two sponsor models on different schema versions declaring different fields.
    assert_response_status_code(_publish_schema(api_client, 3, SCHEMA_V3), 201)
    sm_v2 = _create_sponsor_model(api_client, "2", schema_version=2)
    sm_v3 = _create_sponsor_model(api_client, "3", schema_version=3)

    for sm in (sm_v2, sm_v3):
        assert_response_status_code(
            api_client.post(
                "/standards/sponsor-models/datasets",
                json={
                    "target_data_model_catalogue": data_model_catalogue_name,
                    "dataset_uid": datasets[1].uid,
                    "sponsor_model_name": sm["name"],
                    "sponsor_model_version_number": sm["version"],
                    "implemented_dataset_class": dataset_classes[1].uid,
                    "is_basic_std": True,
                    "is_cdisc_std": True,
                },
            ),
            201,
        )

    v2_row = api_client.get(
        "/standards/sponsor-models/datasets",
        params={"sponsor_model_name": sm_v2["name"]},
    ).json()["items"][0]
    v3_row = api_client.get(
        "/standards/sponsor-models/datasets",
        params={"sponsor_model_name": sm_v3["name"]},
    ).json()["items"][0]

    # Each row's null-filled declared columns follow ITS OWN parent's schema.
    assert "foo" in v2_row and "baz" not in v2_row
    assert "baz" in v3_row and "foo" not in v3_row


def test_changed_extensible_value_is_not_dropped_on_reimport(api_client):
    # Re-importing a dataset whose ONLY change is an extensible value must not
    # reuse the old value node (which would drop the new value).
    sponsor_model = _create_sponsor_model(api_client, "6", schema_version=2)
    common = {
        "target_data_model_catalogue": data_model_catalogue_name,
        "dataset_uid": datasets[1].uid,
        "sponsor_model_name": sponsor_model["name"],
        "sponsor_model_version_number": sponsor_model["version"],
        "implemented_dataset_class": dataset_classes[1].uid,
        "is_basic_std": True,
        "is_cdisc_std": True,
    }
    assert_response_status_code(
        api_client.post(
            "/standards/sponsor-models/datasets", json={**common, "foo": "v1"}
        ),
        201,
    )
    second = api_client.post(
        "/standards/sponsor-models/datasets", json={**common, "foo": "v2"}
    )
    assert_response_status_code(second, 201)
    assert second.json()["foo"] == "v2"


def test_legacy_sponsor_model_defaults_and_degrades_gracefully(api_client):
    # Sponsor model with no schema_version (legacy) -> children default to v1.
    # v1 is not published here, so reads must degrade (structural + stored extras),
    # never 500.
    sponsor_model = _create_sponsor_model(api_client, "4", schema_version=None)
    create = api_client.post(
        "/standards/sponsor-models/datasets",
        json={
            "target_data_model_catalogue": data_model_catalogue_name,
            "dataset_uid": datasets[0].uid,
            "sponsor_model_name": sponsor_model["name"],
            "sponsor_model_version_number": sponsor_model["version"],
            "implemented_dataset_class": dataset_classes[0].uid,
            # Structurally distinct from other datasets on this root so a fresh
            # instance node is created (instances are shared when structural data
            # is unchanged).
            "is_basic_std": False,
            "is_cdisc_std": False,
            "structure": "legacy-only-structure",
            "legacy_extra": "kept",
        },
    )
    assert_response_status_code(create, 201)

    listing = api_client.get(
        "/standards/sponsor-models/datasets",
        params={"sponsor_model_name": sponsor_model["name"]},
    )
    assert_response_status_code(listing, 200)
    row = {r["uid"]: r for r in listing.json()["items"]}[datasets[0].uid]
    # Stored extras are never lost, even when the schema can't be resolved.
    assert row["legacy_extra"] == "kept"


def test_extensible_field_with_dashes_and_spaces_round_trips(api_client):
    # Neo4j property keys cannot contain spaces or dashes, so the repository
    # sanitizes them to underscores when persisting the node. Sanitization happens
    # on the DB write, so it is the read (list) path that surfaces the sanitized
    # key `my_dashed_field` — recovered from the stored node properties.
    sponsor_model = _create_sponsor_model(api_client, "7", schema_version=2)
    create = api_client.post(
        "/standards/sponsor-models/datasets",
        json={
            "target_data_model_catalogue": data_model_catalogue_name,
            "dataset_uid": datasets[0].uid,
            "sponsor_model_name": sponsor_model["name"],
            "sponsor_model_version_number": sponsor_model["version"],
            "implemented_dataset_class": dataset_classes[0].uid,
            "is_basic_std": True,
            "is_cdisc_std": True,
            "my-dashed field": "sanitized-value",
        },
    )
    assert_response_status_code(create, 201)

    listing = api_client.get(
        "/standards/sponsor-models/datasets",
        params={"sponsor_model_name": sponsor_model["name"]},
    )
    assert_response_status_code(listing, 200)
    row = {r["uid"]: r for r in listing.json()["items"]}[datasets[0].uid]
    # Spaces and dashes are collapsed to underscores in the stored (and read-back) key.
    assert row["my_dashed_field"] == "sanitized-value"
    assert "my-dashed field" not in row


def test_undeclared_extra_under_published_schema_is_stored_and_returned(api_client):
    # Policy: under a published schema, a field the schema does NOT declare is still
    # accepted, stored, and echoed back (permissive extras), alongside the schema's
    # declared/null-filled columns.
    sponsor_model = _create_sponsor_model(api_client, "8", schema_version=2)
    create = api_client.post(
        "/standards/sponsor-models/datasets",
        json={
            "target_data_model_catalogue": data_model_catalogue_name,
            "dataset_uid": datasets[0].uid,
            "sponsor_model_name": sponsor_model["name"],
            "sponsor_model_version_number": sponsor_model["version"],
            "implemented_dataset_class": dataset_classes[0].uid,
            "is_basic_std": True,
            "is_cdisc_std": True,
            "foo": "declared",  # declared by schema v2
            "undeclared_extra": "kept",  # NOT declared by schema v2
        },
    )
    assert_response_status_code(create, 201)
    assert create.json()["undeclared_extra"] == "kept"

    listing = api_client.get(
        "/standards/sponsor-models/datasets",
        params={"sponsor_model_name": sponsor_model["name"]},
    )
    assert_response_status_code(listing, 200)
    row = {r["uid"]: r for r in listing.json()["items"]}[datasets[0].uid]
    # Both the declared field and the undeclared extra are present on read.
    assert row["foo"] == "declared"
    assert row["undeclared_extra"] == "kept"


def test_dataset_listing_requires_sponsor_model_name(api_client):
    # Without a sponsor model name the schema version is unknown, so extensible
    # fields cannot be projected; the parameter is mandatory. A missing required
    # query param is a request-validation failure, which this app maps to 400.
    response = api_client.get("/standards/sponsor-models/datasets")
    assert_response_status_code(response, 400)


def test_dataset_variable_listing_requires_sponsor_model_name(api_client):
    response = api_client.get("/standards/sponsor-models/dataset-variables")
    assert_response_status_code(response, 400)


def test_extensible_variable_field_flows_through(api_client):
    # Reuse the schema v2 / SM published by the dataset test's module-scoped DB.
    sponsor_model = _create_sponsor_model(api_client, "1", schema_version=2)

    # A sponsor dataset to hang the variable off.
    dataset = api_client.post(
        "/standards/sponsor-models/datasets",
        json={
            "target_data_model_catalogue": data_model_catalogue_name,
            "dataset_uid": datasets[0].uid,
            "sponsor_model_name": sponsor_model["name"],
            "sponsor_model_version_number": sponsor_model["version"],
            "implemented_dataset_class": dataset_classes[0].uid,
            "is_basic_std": True,
            "is_cdisc_std": True,
        },
    )
    assert_response_status_code(dataset, 201)

    create = api_client.post(
        "/standards/sponsor-models/dataset-variables",
        json={
            "target_data_model_catalogue": data_model_catalogue_name,
            "dataset_uid": datasets[0].uid,
            "dataset_variable_uid": dataset_variables[0].uid,
            "sponsor_model_name": sponsor_model["name"],
            "sponsor_model_version_number": sponsor_model["version"],
            "is_basic_std": True,
            "is_cdisc_std": True,
            "bar": "variable-value",
        },
    )
    assert_response_status_code(create, 201)
    assert create.json()["bar"] == "variable-value"

    listing = api_client.get(
        "/standards/sponsor-models/dataset-variables",
        params={"sponsor_model_name": sponsor_model["name"]},
    )
    assert_response_status_code(listing, 200)
    rows = {row["uid"]: row for row in listing.json()["items"]}
    assert dataset_variables[0].uid in rows
    assert rows[dataset_variables[0].uid]["bar"] == "variable-value"
