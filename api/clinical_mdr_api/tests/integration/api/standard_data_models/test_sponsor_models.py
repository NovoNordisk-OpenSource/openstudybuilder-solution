"""
Tests for /standards/sponsor-models endpoints
"""

import json
import logging

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
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
from clinical_mdr_api.tests.integration.utils.utils import CT_CODELIST_UIDS, TestUtils
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
term: CTTermRoot


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
    global term

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
    term = TestUtils.create_ct_term()
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
        "is_cdisc_std": True,
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


def test_post_sponsor_dataset_with_unknown_class_is_created_without_class_link(
    api_client,
):
    """DC-SEM-011: a sponsor dataset whose implemented dataset class is not found
    for its sponsor model (the class does not exist, or is not part of that
    sponsor model's IG) is still created (201) with no IMPLEMENTS_DATASET_CLASS
    link. The API logs a warning instead of refusing (not asserted here).
    This test covers the class-does-not-exist case."""
    url = "/standards/sponsor-models/datasets"
    sponsor_model = TestUtils.create_sponsor_model(
        ig_uid=data_model_ig.uid,
        ig_version_number=data_model_ig.version_number,
        version_number="1",
    )
    params = {
        "target_data_model_catalogue": data_model_catalogue_name,
        "dataset_uid": "DatasetWithNonexistentClass",
        "sponsor_model_name": sponsor_model.name,
        "sponsor_model_version_number": sponsor_model.version,
        "implemented_dataset_class": "NonexistentDatasetClass",
        "is_basic_std": True,
        "is_cdisc_std": True,
        "enrich_build_order": 10,
    }
    response = api_client.post(
        url,
        json=params,
    )

    assert_response_status_code(response, 201)
    res = response.json()
    assert res["uid"] == params["dataset_uid"]

    no_class_link_count = db.cypher_query(
        """
        MATCH (root:Dataset {uid: $uid})-[:HAS_INSTANCE]->(value:SponsorModelDatasetInstance)
        WHERE NOT (value)-[:IMPLEMENTS_DATASET_CLASS]->()
        RETURN count(value)
        """,
        {"uid": params["dataset_uid"]},
    )[0][0][0]
    assert no_class_link_count >= 1


def test_post_sponsor_dataset_without_class_is_created_without_class_link(
    api_client,
):
    """DC-SEM-002: a sponsor dataset may have no dataset class. When no
    implemented dataset class is given, the dataset is created (201) with no
    IMPLEMENTS_DATASET_CLASS link."""
    url = "/standards/sponsor-models/datasets"
    sponsor_model = TestUtils.create_sponsor_model(
        ig_uid=data_model_ig.uid,
        ig_version_number=data_model_ig.version_number,
        version_number="1",
    )
    params = {
        "target_data_model_catalogue": data_model_catalogue_name,
        "dataset_uid": "DatasetWithoutClass",
        "sponsor_model_name": sponsor_model.name,
        "sponsor_model_version_number": sponsor_model.version,
        "is_basic_std": True,
        "is_cdisc_std": True,
        "enrich_build_order": 10,
    }
    response = api_client.post(
        url,
        json=params,
    )

    assert_response_status_code(response, 201)
    res = response.json()
    assert res["uid"] == params["dataset_uid"]

    no_class_link_count = db.cypher_query(
        """
        MATCH (root:Dataset {uid: $uid})-[:HAS_INSTANCE]->(value:SponsorModelDatasetInstance)
        WHERE NOT (value)-[:IMPLEMENTS_DATASET_CLASS]->()
        RETURN count(value)
        """,
        {"uid": params["dataset_uid"]},
    )[0][0][0]
    assert no_class_link_count == 1


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
        "is_cdisc_std": True,
        "order": 20,
        "references_codelists": [CT_CODELIST_UIDS.default],
        "references_terms": [term.term_uid],
    }

    # Making a POST request to create a dataset variable with the sponsor model
    response = api_client.post(
        url,
        json=common_params,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["uid"] == common_params["dataset_variable_uid"]
    # `order` is structural but exposed via the parent dataset's ordinal.
    assert res["dataset"]["ordinal"] == common_params["order"]

    # The listing reaches referenced terms through the CTTermContext node
    uid_filter = json.dumps({"uid": {"v": [common_params["dataset_variable_uid"]]}})
    response = api_client.get(
        f"{url}?sponsor_model_name={sponsor_model.name}"
        f"&sponsor_model_version={sponsor_model.version}&filters={uid_filter}"
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["referenced_terms"] == [
        {"uid": term.term_uid, "submission_value": term.codelists[0].submission_value}
    ]

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

    # It should have been created, with an inconsistency flag
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

    # POST request to create a dataset variable with a codelist which doesn't exist in the database
    params7 = common_params.copy()
    params7["dataset_variable_uid"] = "DatasetVariableWithNonexistentCodelist"
    params7["references_codelists"] = ["ThisCTCodelistDoesNotExist"]
    response = api_client.post(
        url,
        json=params7,
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == "Could not find codelist with uid 'ThisCTCodelistDoesNotExist'."
    )

    # POST request to create a dataset variable with a term which doesn't exist in the database
    params8 = common_params.copy()
    params8["dataset_variable_uid"] = "DatasetVariableWithNonexistentTerm"
    params8["references_terms"] = ["ThisCTTermDoesNotExist"]
    response = api_client.post(
        url,
        json=params8,
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == "Could not find term with uid 'ThisCTTermDoesNotExist'."
