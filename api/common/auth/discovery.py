import logging

from common.auth.dependencies import oauth_scheme, oidc_client

log = logging.getLogger(__name__)


async def reconfigure_with_openid_discovery():
    log.info("Reconfiguring Swagger UI settings with OpenID Connect discovery.")

    metadata = await oidc_client.load_server_metadata()

    if authorization_endpoint := metadata.get("authorization_endpoint"):
        oauth_scheme.model.flows.authorizationCode.authorizationUrl = (
            authorization_endpoint
        )

    if token_endpoint := metadata.get("token_endpoint"):
        oauth_scheme.model.flows.authorizationCode.tokenUrl = token_endpoint
