# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.tests.integration.utils.api import inject_base_data
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from consumer_api.consumer_api import app
from consumer_api.tests.utils import assert_response_status_code, set_db
from consumer_api.v2 import models

pytestmark = pytest.mark.skip("Skip until we have a v2 version of the API")

BASE_URL = "/v2"


STUDY_FIELDS_ALL = [
    "uid",
    "acronym",
    "id_prefix",
    "number",
]

STUDY_FIELDS_NOT_NULL = [
    "uid",
    "id_prefix",
]

# Global variables shared between fixtures and tests
rand: str
studies: list[models.Study]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "consumer-api-v2"
    set_db(db_name)
    study = inject_base_data()

    global rand
    global studies

    studies = [study]
    for _idx in range(1, 5):
        rand = TestUtils.random_str(4)
        studies.append(TestUtils.create_study(number=rand, acronym=f"ACR-{rand}"))


def test_get_studies(api_client):
    response = api_client.get(f"{BASE_URL}/studies")
    assert_response_status_code(response, 200)
    res = response.json()

    assert res.keys() == {"self", "prev", "next", "items"}

    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, STUDY_FIELDS_ALL, STUDY_FIELDS_NOT_NULL
        )

    for study in studies:
        assert any(
            item["uid"] == study.uid for item in res["items"]
        ), f"Study {study.uid} not found in response"
