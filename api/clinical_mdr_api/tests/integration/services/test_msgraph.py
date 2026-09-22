import json
import re
import urllib.parse
from typing import Any

import pytest

from clinical_mdr_api.models.integrations.msgraph import GraphGroup, GraphUser
from clinical_mdr_api.services.integrations import msgraph
from common import exceptions

# pylint: disable=redefined-outer-name


GROUP_URL_RE = re.compile("/groups/([0-9a-f-]+)/members")

GROUPS: tuple[dict[str, Any]] = (
    {
        "id": "02bd9fd6-8f93-4758-87c3-1fb73740a315",
        "createdDateTime": "2017-07-31T18:56:16Z",
        "description": "Welcome to the HR Taskforce team.",
        "displayName": "HR Taskforce",
        "groupTypes": ["Unified"],
        "mail": "HRTaskforce@M365x214355.onmicrosoft.com",
        "mailEnabled": True,
        "mailNickname": "HRTaskforce",
    },
    {
        "id": "06f62f70-9827-4e6e-93ef-8e0f2d9b7b23",
        "createdDateTime": "2017-07-31T17:38:15Z",
        "description": "Video Production",
        "displayName": "Video Production",
        "groupTypes": ["Unified"],
        "mail": "VideoProduction@M365x214355.onmicrosoft.com",
        "mailEnabled": True,
        "mailNickname": "VideoProduction",
    },
    {
        "id": "0a53828f-36c9-44c3-be3d-99a7fce977ac",
        "createdDateTime": "2017-09-02T02:54:25Z",
        "description": "Marketing Campaigns",
        "displayName": "Marketing Campaigns",
        "groupTypes": ["Unified"],
        "mail": "marketingcampaigns@M365x214355.onmicrosoft.com",
        "mailEnabled": True,
        "mailNickname": None,
    },
    {
        "id": "5b22aa31-973b-4457-8d41-53c0f06117b9",
        "createdDateTime": "2020-09-24T21:08:42Z",
        "description": None,
        "displayName": "Northwind Traders",
        "groupTypes": [],
        "mail": "Northwind@M365x214355.onmicrosoft.com",
        "mailEnabled": True,
        "mailNickname": "Northwind",
    },
    {
        "id": "1381c058-2ee8-41ce-a005-aae7d91fe086",
        "createdDateTime": "2017-09-15T01:03:59Z",
        "description": "Where we share video ideas.",
        "displayName": "Videas",
        "groupTypes": ["Unified"],
        "mail": None,
        "mailEnabled": False,
        "mailNickname": "Ideas",
    },
    {
        "id": "13be6971-79db-4f33-9d41-b25589ca25af",
        "createdDateTime": "2017-07-31T18:56:22Z",
        "creationOptions": ["ExchangeProvisioningFlags:481"],
        "description": "Welcome to the BizDev team.",
        "displayName": "Business Development",
        "groupTypes": ["Unified"],
        "mail": "BusinessDevelopment@M365x214355.onmicrosoft.com",
        "mailEnabled": True,
        "mailNickname": "BusinessDevelopment",
    },
)

USERS_DICT = {
    "87d349ed": {
        "id": "87d349ed-44d7-43e1-9a83-5f2406dee5bd",
        "displayName": "Adele Vance",
        "givenName": "Adele",
        "mail": "AdeleV@M365x214355.onmicrosoft.com",
        "surname": "Vance",
    },
    "626cbf8c": {
        "id": "626cbf8c-5dde-46b0-8385-9e40d64736fe",
        "displayName": "Johanna Lorenz",
        "givenName": "Johanna",
        "mail": "JohannaL@M365x214355.onmicrosoft.com",
        "surname": "Lorenz",
    },
    "40079818": {
        "id": "40079818-3808-4585-903b-02605f061225",
        "displayName": "Patti Fernandez",
        "givenName": "Patti",
        "mail": "PattiF@M365x214355.onmicrosoft.com",
        "surname": "Fernandez",
    },
    "074e56ea": {
        "id": "074e56ea-0b50-4461-89e5-c67ae14a2c0b",
        "displayName": "Lee Gu",
        "givenName": "Lee",
        "mail": "LeeG@M365x214355.onmicrosoft.com",
        "surname": "Gu",
    },
    "16cfe710": {
        "id": "16cfe710-1625-4806-9990-91b8f0afee35",
        "displayName": "Enrico Cattechriro",
        "givenName": "Enrico",
        "mail": "EnricoC@M365x214355.onmicrosoft.com",
        "surname": "Cattecriso",
    },
    "089a6bb8": {
        "id": "089a6bb8-e8cb-492c-aa41-c078aa0b5120",
        "displayName": "Nestor Wilke",
        "givenName": "Nestor",
        "mail": "NestorW@M365x214355.onmicrosoft.com",
        "surname": "Wilke",
    },
    "2804bc07": {
        "id": "2804bc07-1e1f-4938-9085-ce6d756a32d2",
        "displayName": "Emily Braun",
        "givenName": "Emily",
        "mail": "EmilyB@M365x214355.onmicrosoft.com",
        "surname": "Braun",
    },
    "b66ecf79": {
        "id": "b66ecf79-a093-4d51-86e0-efcc4531f37a",
        "displayName": "Christie Cline",
        "givenName": "Christie",
        "mail": "ChristieC@M365x214355.onmicrosoft.com",
        "surname": "Cline",
    },
    "4782e723": {
        "id": "4782e723-f4f4-4af3-a76e-25e3bab0d896",
        "displayName": "Alex-Christos Wilber",
        "givenName": "Alex",
        "mail": "AlexM@M365x214355.onmicrosoft.com",
        "surname": "Wilber",
    },
    "08fa38e4": {
        "id": "08fa38e4-cbfa-4488-94ed-c834da6539df",
        "displayName": "Miriam Graham",
        "givenName": "Miriam",
        "mail": "MiriamG@M365x214355.onmicrosoft.com",
        "surname": "Grau",
    },
}
USERS = list(USERS_DICT.values())

USERS_BY_PATTERN = {
    "microSOFT": USERS,
    "ha": [USERS_DICT["626cbf8c"], USERS_DICT["08fa38e4"]],
    "Chri": [USERS_DICT["b66ecf79"], USERS_DICT["4782e723"], USERS_DICT["16cfe710"]],
    "emil": [USERS_DICT["2804bc07"]],
    "gra": [USERS_DICT["08fa38e4"]],
    "mi.*a[uh]": [],
}

USERS_BY_GROUP = {
    "02bd9fd6-8f93-4758-87c3-1fb73740a315": USERS[0:3],  # 3 members
    "06f62f70-9827-4e6e-93ef-8e0f2d9b7b23": USERS[3:7],  # 4 members
    "0a53828f-36c9-44c3-be3d-99a7fce977ac": USERS[4:10],  # 6 members
    "1381c058-2ee8-41ce-a005-aae7d91fe086": (
        USERS[2],
        USERS[9],
        USERS[0],
        USERS[4],
        USERS[1],
    ),  # 5 members
    "13be6971-79db-4f33-9d41-b25589ca25af": [USERS[1]],  # 1 member
    "5b22aa31-973b-4457-8d41-53c0f06117b9": [],  # 0 members
}


class MockRequest:
    def __init__(self, url):
        self.url = url


class MockResponse:
    def __init__(
        self,
        status_code: int = 200,
        reason: str = "OK",
        url: str = "/hello+world",
        text: str = "Hello world!",
        payload: Any = None,
    ):
        self.status_code = status_code
        self.reason_phrase = reason
        self.text = text
        self.payload = payload
        self.request = MockRequest(url=url)

    def json(self) -> Any:
        return self.payload


class MockMsGraphApiClient:
    _page_limit = 3

    @staticmethod
    # pylint: disable=unused-argument
    async def request(
        method: str, url: str, token: dict[Any, Any], **kwargs
    ) -> MockResponse:
        if not (token and token.get("expires_at")):
            return MockResponse(
                status_code=403,
                url=url,
                reason="Forbidden",
                text="There was no token argument to the request() call, or no expires_at property.",
            )

        uri = urllib.parse.urlparse(url)

        if match := GROUP_URL_RE.search(uri.path):
            gid = match.group(1)
            return MockMsGraphApiClient._members_list(
                url, gid, offset=int(uri.params or 0)
            )

        if "/groups" in uri.path:
            return MockMsGraphApiClient._groups_list(url)

        if "/non-json-payload" in uri.path:
            return MockMsGraphApiClient._non_json(url)

        return MockResponse(
            status_code=400,
            url=url,
            reason="Not Implemented",
            text=f"The requested url {url} is not mocked.",
        )

    @staticmethod
    def _non_json(url: str) -> MockResponse:
        response = MockResponse(url=url, text="Non-JSON payload")

        def raise_exc():
            raise json.JSONDecodeError(
                msg="Testing JSONDecodeError exception handling",
                doc=response.text,
                pos=0,
            )

        setattr(response, "json", raise_exc)
        return response

    @staticmethod
    def _groups_list(url: str) -> MockResponse:
        payload = {
            "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#groups",
            "value": list(GROUPS),
        }
        return MockResponse(url=url, payload=payload)

    @staticmethod
    def _members_list(url: str, gid: str, offset: int = 0) -> MockResponse:
        limit = 3

        if gid not in USERS_BY_GROUP:
            return MockResponse(
                status_code=404,
                url=url,
                reason="Not Found",
                text=f"Group id {gid} is not in USERS_BY_GROUPS",
            )
        users = USERS_BY_GROUP[gid]

        if offset and offset >= len(users) or offset < 0:
            return MockResponse(
                status_code=400,
                url=url,
                reason="Out-of-range error",
                text="Requested pager offset/limit is out of range",
            )

        payload = {
            "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users(id,displayName,givenName,mail,surname)",
            "@odata.nextLink": f"/groups/{gid}/members;{offset + limit}",
            "value": list(users[offset : offset + limit]),
        }
        if offset + limit >= len(users):
            del payload["@odata.nextLink"]
        return MockResponse(url=url, payload=payload)


@pytest.fixture
def mocked_msgraph_service(monkeypatch):
    service = msgraph.MsGraphClientService(
        server_metadata_url="/metadata",
        client_id="client-id",
        client_secret="client-secret",
    )
    monkeypatch.setattr(service, "client", MockMsGraphApiClient())
    monkeypatch.setattr(msgraph, "service", service)
    return service


@pytest.mark.asyncio
async def test_msgraph_request_error(mocked_msgraph_service):
    with pytest.raises(exceptions.BusinessLogicException) as exc_info:
        await mocked_msgraph_service.request("GET", "/not-implemented")
    assert "request failed" in exc_info.value.msg


@pytest.mark.asyncio
async def test_msgraph_request_non_json(mocked_msgraph_service):
    with pytest.raises(exceptions.BusinessLogicException) as exc_info:
        await mocked_msgraph_service.request("GET", "/non-json-payload")
    assert "Testing JSONDecodeError" in exc_info.value.msg


@pytest.mark.asyncio
async def test_msgraph_request_forbidden(mocked_msgraph_service):
    with pytest.raises(exceptions.BusinessLogicException) as exc_info:
        mocked_msgraph_service.token = {}
        await mocked_msgraph_service.request("GET", "/groups")
    assert "Forbidden" in exc_info.value.msg


@pytest.mark.asyncio
async def test_msgraph_fetch_groups(mocked_msgraph_service):
    payload = await mocked_msgraph_service.fetch_groups()
    _assert_groups_match_expected(payload, GROUPS)


def _assert_groups_match_expected(payload, expected_groups):
    # pylint: disable=unused-variable
    __tracebackhide__ = True

    assert isinstance(payload, list)
    assert len(payload) == len(expected_groups)

    groups: dict[str, GraphGroup] = {g.id: g for g in payload}
    assert len(groups) == len(expected_groups)

    for expected in expected_groups:
        group = groups.get(expected.get("id"))
        assert group.display_name == expected.get("displayName")
        assert group.description == expected.get("description")


@pytest.mark.parametrize(
    "gid",
    [g["id"] for g in GROUPS],
)
@pytest.mark.asyncio
async def test_fetch_group_direct_member_users(mocked_msgraph_service, gid):
    payload = await mocked_msgraph_service.fetch_group_direct_member_users(gid)
    _assert_users_match_expected(payload, USERS_BY_GROUP[gid])


@pytest.mark.asyncio
async def test_fetch_all_group_direct_member_users(mocked_msgraph_service):
    payload = await mocked_msgraph_service.fetch_all_group_direct_member_users()
    _assert_users_match_expected(payload, USERS)
    _assert_users_well_ordered(payload)

    # Test caching: if a new requests were launched, it would fail without token
    # related: test_fetch_all_group_direct_member_users_fails_without_token()
    mocked_msgraph_service.token = {}

    payload = await mocked_msgraph_service.fetch_all_group_direct_member_users()
    _assert_users_match_expected(payload, USERS)
    _assert_users_well_ordered(payload)


@pytest.mark.asyncio
async def test_fetch_all_group_direct_member_users_fails_without_token(
    mocked_msgraph_service,
):
    with pytest.raises(exceptions.BusinessLogicException) as exc_info:
        mocked_msgraph_service.token = {}
        await mocked_msgraph_service.fetch_all_group_direct_member_users()
    assert "Forbidden" in exc_info.value.msg


@pytest.mark.parametrize(
    "pattern, expected_users",
    list(USERS_BY_PATTERN.items()),
)
@pytest.mark.asyncio
async def test_search_all_group_direct_member_users(
    mocked_msgraph_service, pattern, expected_users
):
    payload = await mocked_msgraph_service.search_all_group_direct_member_users(pattern)
    _assert_users_match_expected(payload, expected_users)
    _assert_users_well_ordered(payload)


def _assert_users_match_expected(payload, expected_users):
    # pylint: disable=unused-variable
    __tracebackhide__ = True

    assert isinstance(payload, list)
    assert len(payload) == len(expected_users)

    users: dict[str, GraphUser] = {u.id: u for u in payload}
    assert len(users) == len(expected_users)

    for expected in expected_users:
        user = users.get(expected["id"])
        assert user.display_name == expected.get("displayName")
        assert user.given_name == expected.get("givenName")
        assert user.email == expected.get("mail")
        assert user.surname == expected.get("surname")


def _assert_users_well_ordered(payload):
    # pylint: disable=unused-variable
    __tracebackhide__ = True

    display_names = [u.display_name for u in payload]
    expected_order = sorted(display_names)
    assert (
        display_names == expected_order
    ), "Users are not correctly ordered by display_name"
