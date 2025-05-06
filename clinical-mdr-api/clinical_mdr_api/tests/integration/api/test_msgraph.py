# pylint: disable=unused-import,redefined-outer-name,unused-argument

import pytest

from clinical_mdr_api.services.integrations import msgraph
from clinical_mdr_api.tests.integration.services.test_msgraph import (
    USERS,
    USERS_BY_PATTERN,
    mocked_msgraph_service,
)
from clinical_mdr_api.tests.utils.checks import (
    assert_response_content_type,
    assert_response_status_code,
)
from common import config


@pytest.fixture
def mock_msgraph_service_to_none(monkeypatch):
    monkeypatch.setattr(msgraph, "service", None)


# Test purpose is to validate Ms-Graph API integration config, only if Ms-Graph Integration is enabled and configured
@pytest.mark.skipif(
    not config.MS_GRAPH_INTEGRATION_ENABLED,
    reason="Ms-Graph integration is disabled (see MS_GRAPH_INTEGRATION_ENABLED env var)",
)
# run test at least twice because it utilizes caching and singleton class and reusing of access token
@pytest.mark.parametrize(
    "pattern",
    ["test", None, "t.sT", "te.*ser"],
)
def test_get_users(api_client, pattern):
    params = {"search": pattern} if pattern else None
    response = api_client.get("/integrations/ms-graph/users", params=params)

    assert_response_status_code(response, 200)
    assert_response_content_type(response)

    payload = response.json()

    assert isinstance(payload, list)
    assert len(payload)
    user = payload[0]
    assert user.get("id")
    assert user.get(
        "display_name"
    ), f"Missing display_name of user, perhaps User.Read.All Ms-Graph permission not granted to application: {user}"

    assert_users_well_ordered(payload)


@pytest.mark.parametrize(
    "pattern, expected_users",
    [(None, USERS)] + list(USERS_BY_PATTERN.items()),
)
def test_get_users_mocked(api_client, mocked_msgraph_service, pattern, expected_users):
    params = {"search": pattern} if pattern else None
    response = api_client.get("/integrations/ms-graph/users", params=params)
    assert_response_status_code(response, 200)
    assert_response_content_type(response)
    payload = response.json()

    _assert_users_match_expected(payload, expected_users)
    assert_users_well_ordered(payload)


@pytest.mark.parametrize(
    "pattern",
    ["test", None, "t.sT", "w.*Ter"],
)
def test_get_users_when_service_disabled(
    api_client, mock_msgraph_service_to_none, pattern
):
    params = {"search": pattern} if pattern else None
    response = api_client.get("/integrations/ms-graph/users", params=params)
    assert_response_status_code(response, 200)
    assert_response_content_type(response)
    payload = response.json()
    assert payload == []


def _assert_users_match_expected(payload, expected_users):
    # pylint: disable=unused-variable
    __tracebackhide__ = True

    assert isinstance(payload, list)
    assert len(payload) == len(expected_users)

    users = {u.get("id"): u for u in payload}
    assert len(users) == len(expected_users)

    for expected in expected_users:
        user = users.get(expected["id"])
        assert user.get("display_name") == expected.get("displayName")
        assert user.get("given_name") == expected.get("givenName")
        assert user.get("email") == expected.get("mail")
        assert user.get("surname") == expected.get("surname")


def assert_users_well_ordered(payload):
    # pylint: disable=unused-variable
    __tracebackhide__ = True

    display_names = [u.get("display_name") for u in payload]
    expected_order = sorted(display_names)
    assert (
        display_names == expected_order
    ), "Users are not correctly ordered by display_name"


@pytest.mark.parametrize(
    "pattern",
    [
        "8",
        "F",
        "t",
        " ",
        "  ",
        " G ",
        "m  ",
        "C ",
        "?",
        "too-long uGeeyohB2Eiqu sool7neiPh0We Die2iel ooqu ahbooH3Oi6xieP sol7iPh0We uGeeyo ja1"
        * 3,
    ],
)
def test_get_users_invalid_pattern_length(api_client, mocked_msgraph_service, pattern):
    params = {"search": pattern} if pattern else None
    response = api_client.get("/integrations/ms-graph/users", params=params)

    assert_response_status_code(response, 422)
    assert_response_content_type(response)

    payload = response.json()

    assert isinstance(payload, dict)
    assert payload.get("detail")
    assert isinstance(payload["detail"], list)

    detail0 = payload.get("detail")[0]
    assert isinstance(detail0, dict)
    assert detail0.get("type")
    assert isinstance(detail0["type"], str)
    assert detail0["type"].startswith("string_too_")


@pytest.mark.parametrize(
    "pattern",
    [
        "?0",
        r"\1",
        "*foo",
    ],
)
def test_get_users_invalid_pattern_regex(api_client, mocked_msgraph_service, pattern):
    params = {"search": pattern} if pattern else None
    response = api_client.get("/integrations/ms-graph/users", params=params)

    assert_response_status_code(response, 422)
    assert_response_content_type(response)

    payload = response.json()

    assert isinstance(payload, dict)
    assert payload.get("message")
    assert isinstance(payload["message"], str)
    assert "invalid regular expression" in payload["message"].lower()
