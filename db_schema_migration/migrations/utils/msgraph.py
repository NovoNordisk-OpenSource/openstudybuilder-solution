# pylint: disable=broad-exception-raised
import json
import logging
from os import environ
from typing import Any, Mapping

from api.clinical_mdr_api.models.integrations.msgraph import GraphUser
from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from opencensus.trace import execution_context

OAUTH_API_APP_ID = environ.get("OAUTH_API_APP_ID")
OAUTH_API_APP_SECRET = environ.get("OAUTH_API_APP_SECRET")
OAUTH_METADATA_URL = environ.get("OAUTH_METADATA_URL")

GRAPH_API_SCOPE = "https://graph.microsoft.com/.default"  # scope for requesting an access token to graph API
LIST_USERS_URL = "https://graph.microsoft.com/v1.0/users"

log = logging.getLogger(__name__)


oauth = OAuth()


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
        self.token: dict = {"expires_at": 1, "access_token": None}

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

    async def request(self, method: str, url: str, **kwargs) -> dict:
        """Do an API request with access token, expect a 200 response and parse JSON payload"""

        tracer = execution_context.get_opencensus_tracer()
        with tracer.span("MsGraphClientService.request") as span:
            span.add_attribute("http.url", url)
            resp = await self.client.request(
                method=method, url=url, token=self.token, **kwargs
            )

        if resp.status_code != 200:
            raise Exception(
                msg=f"Graph request failed: {resp.status_code} {resp.reason_phrase} {resp.request.url} {resp.text[:1024]}",
            )

        try:
            payload = resp.json()
        except json.JSONDecodeError as exc:
            raise Exception(msg=f"Can't decode response: {exc.msg}") from exc

        return payload

    async def get_user_by_email(self, email: str) -> GraphUser:
        response = await self.request(
            "GET", LIST_USERS_URL, params=f"$filter=mail eq '{email}'"
        )
        if len(response["value"]):
            user = response["value"][0]
            return GraphUser(**user)
        return None


# Singleton service for reusing the OIDC metadata and recycling access/refresh tokens for further requests
service = None  # pylint: disable=invalid-name
if not (OAUTH_METADATA_URL and OAUTH_API_APP_ID and OAUTH_API_APP_SECRET):
    log.warning(
        "MS Graph API integration is not properly configured"
        " (Set env. vars OAUTH_API_APP_ID, OAUTH_API_APP_SECRET, OAUTH_METADATA_URL)"
    )
else:
    service = MsGraphClientService(
        server_metadata_url=OAUTH_METADATA_URL,
        client_id=OAUTH_API_APP_ID,
        client_secret=OAUTH_API_APP_SECRET,
    )
