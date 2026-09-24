import json
import logging
from asyncio import Lock
from functools import wraps
from typing import Any, Mapping

from asyncache import cached
from authlib.integrations.starlette_client import StarletteOAuth2App
from cachetools import TTLCache
from opencensus.trace import execution_context

from clinical_mdr_api.models.integrations.msgraph import GraphGroup, GraphUser
from common.auth.dependencies import oauth
from common.config import settings
from common.exceptions import BusinessLogicException

CACHE_TIMEOUT_SEC = 60 * 60  # Cache timeout in seconds
FETCH_MAX_PAGES = 0  # Fetches maximum N pages of group members (0 to disable)
FETCH_PAGE_SIZE = 999  # Ms Graph API limits to Max 999 entries per page
GRAPH_API_SCOPE = "https://graph.microsoft.com/.default"  # scope for requesting an access token to graph API
GROUP_CONTEXT = "https://graph.microsoft.com/v1.0/$metadata#groups"
GROUP_ENTRY_CONTEXT = "https://graph.microsoft.com/v1.0/$metadata#groups/$entity"
LIST_GROUPS_URL = "https://graph.microsoft.com/v1.0/groups"
LIST_GROUP_MEMBERS_URL = (
    "https://graph.microsoft.com/v1.0/groups/{id}/members/microsoft.graph.user"
    f"?$top={FETCH_PAGE_SIZE}&$select=id,displayName,givenName,mail,surname&$orderby=displayName+ASC"
)
RETURN_MAX_USERS = 0  # Maximum number of users to return

log = logging.getLogger(__name__)


def serialize(fnc):
    """Decorator to serialize function calls to avoid parallel execution"""
    fnc.lock = Lock()

    @wraps(fnc)
    async def serialized(*args, **kwargs):
        async with fnc.lock:
            return await fnc(*args, **kwargs)

    return serialized


class MsGraphClientService:
    def __init__(self, server_metadata_url: str, client_id: str, client_secret: str):
        self.client: StarletteOAuth2App = oauth.register(
            name="ms-graph",
            server_metadata_url=server_metadata_url,
            client_id=client_id,
            client_secret=client_secret,
            token_endpoint_auth_method="client_secret_post",
            grant_type="client_credentials",
            client_kwargs={"scope": GRAPH_API_SCOPE},
            api_base_url="https://graph.microsoft.com/v1.0/",
            update_token=self.set_token,
        )

        # Dummy expired token to trigger OAuth client to do an authentication flow at first API request
        self.token: Mapping[str, Any] = {"expires_at": 1, "access_token": None}

    # pylint: disable=unused-argument
    async def set_token(
        self, token: Mapping, refresh_token: Any = None, access_token: Any = None
    ):
        """
        set token callback for OAuth client

        OAuth client can initiate authentication flow and also refresh the token, if expired,
        but the token has to be stored elsewhere, and also passed as an argument each request() call,
        so it's stored on the service for simplicity.
        """
        self.token = token

    async def request(self, method: str, url: str, **kwargs) -> dict[Any, Any]:
        """Do an API request with access token, expect a 200 response and parse JSON payload"""

        tracer = execution_context.get_opencensus_tracer()
        with tracer.span("MsGraphClientService.request") as span:
            span.add_attribute("http.url", url)
            resp = await self.client.request(
                method=method, url=url, token=self.token, **kwargs
            )

        BusinessLogicException.raise_if(
            resp.status_code != 200,
            msg=f"Graph request failed: {resp.status_code} {resp.reason_phrase} {resp.request.url} {resp.text[:1024]}",
        )

        try:
            payload = resp.json()
        except json.JSONDecodeError as exc:
            raise BusinessLogicException(
                msg=f"Can't decode response: {exc.msg}"
            ) from exc

        return payload

    async def fetch_groups(self) -> list[GraphGroup]:
        """Fetch groups matching the configured filter query ms_graph_groups_query (or all groups if query is empty)"""

        query = settings.ms_graph_groups_query or None

        payload = await self.request("GET", LIST_GROUPS_URL, params=query)

        if (odata_context := payload.get("@odata.context")) == GROUP_CONTEXT:
            return [GraphGroup(**v) for v in payload["value"]]

        if odata_context == GROUP_ENTRY_CONTEXT:
            return [GraphGroup(**payload)]

        raise BusinessLogicException(msg=f"Unknown OData Context {odata_context}")

    async def fetch_group_direct_member_users(self, group_id: str) -> list[GraphUser]:
        """
        Fetch direct user members of a group

        FETCH_PAGE_SIZE constant sets the page size for pagination in Ms-Graph API
        FETCH_MAX_PAGES limits the number of pages fetched
        """

        next_page_url: str | None = LIST_GROUP_MEMBERS_URL.format(id=group_id)
        results = []

        i = 1
        while next_page_url:
            payload = await self.request("GET", next_page_url)

            for item in payload["value"]:
                results.append(GraphUser(**item))

            next_page_url = payload.get("@odata.nextLink", None)
            if not next_page_url:
                break

            if FETCH_MAX_PAGES and i >= FETCH_MAX_PAGES:
                log.error(
                    "MS Graph API integration is limited to fetch maximum %d pages, but there is more. "
                    "Fetched %d results so far.",
                    FETCH_MAX_PAGES,
                    len(results),
                )
                break
            i += 1

        return results

    @serialize
    @cached(TTLCache(maxsize=1, ttl=CACHE_TIMEOUT_SEC), lock=Lock())
    async def fetch_all_group_direct_member_users(self) -> list[GraphUser]:
        """
        Fetches user members of all groups matching the configured query.

        Returns unique users sorted by display_name.

        This method is expected to complete slowly, and it's results are cached for a longer period,
        so it's execution is serialized. The first call will trigger the fetching, while subsequent calls
        have to wait until the results are available from cache, which was populated by the first call.
        """
        groups = await self.fetch_groups()

        users = {}
        for group in groups:
            members = await self.fetch_group_direct_member_users(group.id)

            for user in members:
                users[user.id] = user

        return sorted(users.values(), key=lambda u: u.display_name or "~")

    async def search_all_group_direct_member_users(
        self, pattern: str | None
    ) -> list[GraphUser]:
        """
        Searches within all user members of all groups matching the configured query.

        Returns maximum RETURN_MAX_USERS unique users matching the optional search `pattern`.

        pattern  :: optional text pattern for searching in user .display_name, .given_name, .surname, .mail
                    If omitted, returns all users without filtering.
        """
        search_pattern = pattern.casefold() if pattern else None

        users = []
        for user in await self.fetch_all_group_direct_member_users():
            if search_pattern:
                for search_query in (
                    user.display_name,
                    user.given_name,
                    user.surname,
                    user.email,
                ):
                    if search_query and search_pattern in search_query.casefold():
                        users.append(user)
                        break

            else:
                users.append(user)

            if RETURN_MAX_USERS and len(users) >= RETURN_MAX_USERS:
                break

        return users


# Singleton service for reusing the OIDC metadata and recycling access/refresh tokens for further requests
service = None  # pylint: disable=invalid-name
if not settings.ms_graph_integration_enabled:
    log.info(
        "MS Graph API integration is disabled. ms_graph_integration_enabled=%r",
        settings.ms_graph_integration_enabled,
    )
elif not (
    settings.oauth_metadata_url
    and settings.oauth_api_app_id
    and settings.oauth_api_app_secret.get_secret_value()
):
    log.warning(
        "MS Graph API integration is not properly configured"
        " (check env. vars OAUTH_API_APP_ID, OAUTH_API_APP_SECRET, OAUTH_METADATA_URL and opt. ms_graph_groups_query)"
    )
else:
    service = MsGraphClientService(
        server_metadata_url=settings.oauth_metadata_url,
        client_id=settings.oauth_api_app_id,
        client_secret=settings.oauth_api_app_secret.get_secret_value(),
    )
