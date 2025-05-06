"""
Tests for /standards/sponsor-models endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.domain_repositories.models.standard_data_model import (
    SponsorModelDatasetVariableInstance,
)
from clinical_mdr_api.main import app
from clinical_mdr_api.models.standard_data_models.data_model import DataModel
from clinical_mdr_api.models.standard_data_models.data_model_ig import DataModelIG
from clinical_mdr_api.models.standard_data_models.dataset import Dataset
from clinical_mdr_api.models.standard_data_models.dataset_class import DatasetClass
from clinical_mdr_api.models.standard_data_models.dataset_variable import (
    DatasetVariable,
)
from clinical_mdr_api.models.standard_data_models.variable_class import VariableClass
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
data_model_catalogue_name: str
data_model: DataModel
data_model_ig: DataModelIG
dataset_classes: list[DatasetClass]
variable_classes: list[VariableClass]
datasets: list[Dataset]
dataset_variables: list[DatasetVariable]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "sponsor-models.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global data_model_catalogue_name
    global data_model
    global data_model_ig
    global dataset_classes
    global variable_classes
    global datasets
    global dataset_variables

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
        )
        for i in range(3)
    ]
    variable_classes = [
        TestUtils.create_variable_class(
            label=f"VariableClass{i} label",
            data_model_catalogue_name=data_model_catalogue_name,
            dataset_class_uid=dataset_classes[i].uid,
            data_model_name=data_model.uid,
            data_model_version=data_model.version_number,
        )
        for i in range(3)
    ]
    datasets = [
        TestUtils.create_dataset(
            label=f"Dataset{i} label",
            data_model_catalogue_name=data_model_catalogue_name,
            data_model_ig_uid=data_model_ig.uid,
            data_model_ig_version_number=data_model_ig.version_number,
            implemented_dataset_class_name=dataset_classes[i].uid,
        )
        for i in range(3)
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
        for i in range(3)
    ]

    yield


def test_post_sponsor_model(api_client):
    response = api_client.post(
        "/standards/sponsor-models/models",
        json={
            "ig_uid": data_model_ig.uid,
            "ig_version_number": data_model_ig.version_number,
            "version_number": "1",
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert (
        res["name"]
        == f"{data_model_ig.uid.lower()}_mastermodel_{data_model_ig.version_number}_NN01"
    )
    assert res["version"] == data_model_ig.version_number


def test_post_dataset(api_client):
    url = "/standards/sponsor-models/datasets"
    sponsor_model = TestUtils.create_sponsor_model(
        ig_uid=data_model_ig.uid,
        ig_version_number=data_model_ig.version_number,
        version_number="1",
    )

    common_params = {
        "target_data_model_catalogue": data_model_catalogue_name,
        "dataset_uid": datasets[0].uid,
        "sponsor_model_name": sponsor_model.name,
        "sponsor_model_version_number": sponsor_model.version,
        "implemented_dataset_class": dataset_classes[0].uid,
        "is_basic_std": True,
        "enrich_build_order": 10,
    }

    # Making a POST request to create a dataset with the sponsor model
    response = api_client.post(
        url,
        json=common_params,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["uid"] == common_params["dataset_uid"]
    assert res["enrich_build_order"] == common_params["enrich_build_order"]

    # POST request to create a dataset with a non-existent sponsor model
    params2 = common_params.copy()
    params2["sponsor_model_name"] = "non_existent_sponsor_model"
    response = api_client.post(
        url,
        json=params2,
    )

    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == "Sponsor Model with Name 'non_existent_sponsor_model' doesn't exist."
    )

    # POST request to create a sponsor dataset instantiating a dataset that doesn't exist in CDISC
    params3 = common_params.copy()
    params3["dataset_uid"] = "NewDataset"
    response = api_client.post(
        url,
        json=params3,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["uid"] == params3["dataset_uid"]

    # POST request to create a dataset implementing a dataset class which doesn't exist in CDISC
    params4 = common_params.copy()
    params4["dataset_uid"] = "DatasetWithNonexistentClass"
    params4["implemented_dataset_class"] = "NonexistentDatasetClass"
    response = api_client.post(
        url,
        json=params4,
    )

    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == "Dataset class with uid 'NonexistentDatasetClass' does not exist."
    )


def test_post_dataset_variable(api_client):
    url = "/standards/sponsor-models/dataset-variables"

    # Create a sponsor model
    sponsor_model = TestUtils.create_sponsor_model(
        ig_uid=data_model_ig.uid,
        ig_version_number=data_model_ig.version_number,
        version_number="1",
    )

    # Create a sponsor dataset
    dataset = TestUtils.create_sponsor_dataset(
        dataset_uid=datasets[0].uid,
        sponsor_model_name=sponsor_model.name,
        sponsor_model_version_number=sponsor_model.version,
        implemented_dataset_class=dataset_classes[0].uid,
    )

    common_params = {
        "target_data_model_catalogue": data_model_catalogue_name,
        "dataset_uid": dataset.uid,
        "dataset_variable_uid": dataset_variables[0].uid,
        "sponsor_model_name": sponsor_model.name,
        "sponsor_model_version_number": sponsor_model.version,
        "implemented_variable_class": variable_classes[0].uid,
        "implemented_parent_dataset_class": dataset_classes[0].uid,
        "is_basic_std": True,
        "order": 20,
    }

    # Making a POST request to create a dataset variable with the sponsor model
    response = api_client.post(
        url,
        json=common_params,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["uid"] == common_params["dataset_variable_uid"]
    assert res["order"] == common_params["order"]

    # POST request to create a dataset variable with a non-existent sponsor model
    params2 = common_params.copy()
    params2["sponsor_model_name"] = "non_existent_sponsor_model"
    response = api_client.post(
        url,
        json=params2,
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == f"Dataset with UID '{common_params['dataset_uid']}' is not instantiated in this version of the sponsor model."
    )

    # POST request to create a dataset variable with a dataset which doesn't exist in CDISC
    params3 = common_params.copy()
    params3["dataset_uid"] = "NonexistentDataset"
    response = api_client.post(
        url,
        json=params3,
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == f"Dataset with UID '{params3['dataset_uid']}' is not instantiated in this version of the sponsor model."
    )

    # POST request to create a sponsor dataset variable instantiating a dataset variable
    # which doesn't exist in CDISC
    params4 = common_params.copy()
    params4["dataset_variable_uid"] = "NonexistentDatasetVariable"
    response = api_client.post(
        url,
        json=params4,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["uid"] == params4["dataset_variable_uid"]

    # POST request to create a dataset variable implementing a variable class
    # which doesn't exist in CDISC
    params5 = common_params.copy()
    params5["dataset_variable_uid"] = "DatasetVariableWithNonexistentClass"
    params5["implemented_parent_dataset_class"] = dataset_classes[0].uid
    params5["implemented_variable_class"] = "NonexistentVariableClass"
    response = api_client.post(
        url,
        json=params5,
    )

    assert_response_status_code(response, 201)
    res = response.json()

    # It should have bee, created, with an inconsistency flag
    created_instance = SponsorModelDatasetVariableInstance.nodes.filter(
        is_instance_of__uid=params5["dataset_variable_uid"]
    ).resolve_subgraph()
    assert created_instance
    assert created_instance[0].implemented_variable_class_inconsistency is True
    assert (
        created_instance[0].implemented_variable_class_uid
        == params5["implemented_variable_class"]
    )
    assert (
        created_instance[0].implemented_parent_dataset_class_uid
        == params5["implemented_parent_dataset_class"]
    )

    # POST request to create a dataset variable implementing an existing variable class
    # But the parent dataset class doesn't exist in CDISC
    params6 = common_params.copy()
    params6["dataset_variable_uid"] = "DatasetVariableWithNonexistentParentClass"
    params6["implemented_parent_dataset_class"] = "NonexistentParentDatasetClass"
    response = api_client.post(
        url,
        json=params6,
    )

    assert_response_status_code(response, 201)
    res = response.json()

    created_instance = SponsorModelDatasetVariableInstance.nodes.filter(
        is_instance_of__uid=params6["dataset_variable_uid"]
    ).resolve_subgraph()
    assert created_instance
    assert created_instance[0].implemented_variable_class_inconsistency is True
    assert (
        created_instance[0].implemented_variable_class_uid
        == params6["implemented_variable_class"]
    )
    assert (
        created_instance[0].implemented_parent_dataset_class_uid
        == params6["implemented_parent_dataset_class"]
    )
