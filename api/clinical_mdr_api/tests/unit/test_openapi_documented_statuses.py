"""The generated spec must declare every status the routes actually return.

Reads the committed `openapi.json` rather than building the app, so the test
needs no database and no running API.
"""

import json
from pathlib import Path

import pytest

OPENAPI_PATH = Path(__file__).parents[3] / "openapi.json"
OPENAPI = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))

# Create routes that raise AlreadyExistsException on a uniqueness conflict.
ROUTES_DECLARING_409 = [
    ("/activity-instance-classes", "post"),
    ("/concepts/activities/activity-groups", "post"),
    ("/concepts/activities/activity-sub-groups", "post"),
    ("/ct/paired-codelists", "post"),
]


@pytest.mark.parametrize("path,method", ROUTES_DECLARING_409)
def test_conflict_status_is_documented(path: str, method: str):
    responses = OPENAPI["paths"][path][method]["responses"]
    assert (
        "409" in responses
    ), f"{method.upper()} {path} returns 409 but does not document it"
