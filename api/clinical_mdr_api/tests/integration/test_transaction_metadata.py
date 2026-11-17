"""Every Neo4j transaction carries the identity of the user it runs for"""

from typing import Any

import pytest
from fastapi import BackgroundTasks, FastAPI
from fastapi.testclient import TestClient
from neomodel import db, get_config
from starlette_context import request_cycle_context

from clinical_mdr_api import main, routers
from clinical_mdr_api.models.jobs.job import JobResponse
from clinical_mdr_api.services._background_job import background_job
from common.auth.dependencies import (
    dummy_access_token_claims,
    dummy_auth_object,
    security,
)
from common.auth.user import transaction_metadata
from common.concurrency import RequestContextThreadPoolExecutor
from common.config import settings
from common.database import TxMetadataDriver

USER_METADATA = {"user_id": "tx-metadata-user"}


@pytest.fixture(scope="module")
def tx_metadata_driver(temp_database):
    """Routes neomodel through the transaction metadata driver, as the apps do.

    Set on the global config, not only on the current connection: a context without
    neomodel's connection state (any thread not started through
    RequestContextThreadPoolExecutor, such as the TestClient's) reconnects from it.
    """

    config = get_config()
    plain_driver = config.driver
    config.driver = TxMetadataDriver(plain_driver, transaction_metadata)
    db.set_connection(driver=config.driver)
    yield
    # Only the driver was changed, so restoring it restores temp_database's config
    config.driver = plain_driver
    db.set_connection(driver=plain_driver)


@pytest.fixture
def user_request():
    auth_info = dummy_auth_object(dummy_access_token_claims(user_id="tx-metadata-user"))
    with request_cycle_context({"auth": auth_info}):
        yield


def get_tx_metadata() -> dict[str, Any]:
    rows, _ = db.cypher_query("CALL tx.getMetaData() YIELD metadata RETURN metadata")
    return rows[0][0]


class TxMetadataJobService:
    author_id = settings.dummy_user_id

    @background_job()
    def read_tx_metadata(self) -> dict[str, Any]:
        return get_tx_metadata()


@pytest.fixture
def job_client():
    """Serves a background job that reports its own transaction's metadata.

    Uses the main API's middleware, which decides whether the request context is
    still there when the job runs after the response.
    """

    app = FastAPI(middleware=main.app.user_middleware)
    app.include_router(routers.jobs_router, prefix="/jobs")

    @app.post("/tx-metadata-job", dependencies=[security], status_code=202)
    def start_tx_metadata_job(background_tasks: BackgroundTasks) -> JobResponse:
        return TxMetadataJobService().read_tx_metadata(
            background_tasks=background_tasks
        )

    return TestClient(app)


@pytest.mark.usefixtures("tx_metadata_driver", "user_request")
def test_auto_commit_query_carries_user():
    assert get_tx_metadata() == USER_METADATA


@pytest.mark.usefixtures("tx_metadata_driver", "user_request")
def test_transaction_carries_user():
    with db.transaction:
        assert get_tx_metadata() == USER_METADATA


@pytest.mark.usefixtures("tx_metadata_driver", "user_request")
def test_worker_thread_queries_inside_transaction_carry_user():
    # Mirrors the SoA flowchart, which fetches in parallel from inside a write transaction
    with db.transaction:
        with RequestContextThreadPoolExecutor() as executor:
            futures = [executor.submit(get_tx_metadata) for _ in range(5)]
            assert [future.result() for future in futures] == [USER_METADATA] * 5

        assert get_tx_metadata() == USER_METADATA


@pytest.mark.usefixtures("tx_metadata_driver")
def test_background_job_transaction_carries_user(job_client):
    # TestClient runs background tasks before returning, as the server does after responding
    job_uid = job_client.post("/tx-metadata-job").json()["uid"]

    job = job_client.get(f"/jobs/{job_uid}").json()
    assert job["status"] == "COMPLETED", job["response"]
    assert job["response"] == {"user_id": settings.dummy_user_id}


@pytest.mark.usefixtures("tx_metadata_driver")
def test_unauthenticated_query_carries_no_metadata():
    with request_cycle_context({}):
        assert get_tx_metadata() == {}
