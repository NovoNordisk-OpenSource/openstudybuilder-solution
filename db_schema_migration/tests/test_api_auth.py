"""Which auth the environment selects, and that it reaches the wire.

Selecting the wrong branch, or building the right object and not attaching it
to the client, looks identical from inside the process until the first request
comes back 401.

Needs no database: only migrations.utils.utils is imported.
"""

import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx_auth
import pytest

# utils reads these at import time; poe sets them from .env, a bare pytest does not
os.environ.setdefault("DATABASE_NAME", "unused")
os.environ.setdefault("DATABASE_URL", "bolt://unused:unused@localhost:7687")

from migrations.utils import utils  # noqa: E402  pylint: disable=wrong-import-position

AUTH_VARS = [
    "STUDYBUILDER_API_TOKEN",
    "CLIENT_ID",
    "CLIENT_SECRET",
    "TOKEN_ENDPOINT",
    "AUTH_ENDPOINT",
    "SCOPE",
]


@pytest.fixture(name="clean_env")
def clean_env_fixture(monkeypatch):
    """No auth configured, and no auth object or client cached yet.

    poe loads .env before pytest runs, so whatever the developer has
    configured locally would otherwise decide which branch these tests take.
    """
    for name in AUTH_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(utils, "_api_auth", None)
    monkeypatch.setattr(utils, "_api_auth_built", False)
    monkeypatch.setattr(utils, "_api_client", None)
    return monkeypatch


def test_no_configuration_means_no_auth(clean_env):
    """The local unauthenticated API is what CI runs against."""
    assert utils._build_api_auth() is None
    assert utils.get_token() is None


def test_static_token_is_selected(clean_env):
    clean_env.setenv("STUDYBUILDER_API_TOKEN", "a-token")
    assert isinstance(utils._build_api_auth(), httpx_auth.HeaderApiKey)


def test_static_token_wins_over_client_id(clean_env):
    clean_env.setenv("STUDYBUILDER_API_TOKEN", "a-token")
    clean_env.setenv("CLIENT_ID", "an-id")
    clean_env.setenv("CLIENT_SECRET", "a-secret")
    clean_env.setenv("TOKEN_ENDPOINT", "https://example.invalid/token")
    clean_env.setenv("SCOPE", "a-scope")
    assert isinstance(utils._build_api_auth(), httpx_auth.HeaderApiKey)


def test_client_id_with_secret_selects_client_credentials(clean_env):
    clean_env.setenv("CLIENT_ID", "an-id")
    clean_env.setenv("CLIENT_SECRET", "a-secret")
    clean_env.setenv("TOKEN_ENDPOINT", "https://example.invalid/token")
    clean_env.setenv("SCOPE", "a-scope")
    assert isinstance(utils._build_api_auth(), httpx_auth.OAuth2ClientCredentials)


def test_client_id_without_secret_selects_interactive_pkce(clean_env):
    clean_env.setenv("CLIENT_ID", "an-id")
    clean_env.setenv("TOKEN_ENDPOINT", "https://example.invalid/token")
    clean_env.setenv("AUTH_ENDPOINT", "https://example.invalid/authorize")
    clean_env.setenv("SCOPE", "a-scope")
    assert isinstance(utils._build_api_auth(), httpx_auth.OAuth2AuthorizationCodePKCE)


def test_building_auth_and_client_makes_no_network_call(clean_env):
    """Constructing must stay lazy, or importing a migration would log in."""
    clean_env.setenv("CLIENT_ID", "an-id")
    clean_env.setenv("TOKEN_ENDPOINT", "https://token.invalid/token")
    clean_env.setenv("AUTH_ENDPOINT", "https://auth.invalid/authorize")
    clean_env.setenv("SCOPE", "a-scope")
    # Unresolvable hosts: anything that actually talked to them would raise.
    assert utils.get_api_client().auth is not None


def test_static_token_is_returned_by_get_token(clean_env):
    """`poe token` prints this, so it must be the bare token."""
    clean_env.setenv("STUDYBUILDER_API_TOKEN", "a-token")
    assert utils.get_token() == "a-token"


# ---------------------------------------------------------------
# End to end, through api_get
# ---------------------------------------------------------------
#
class _RecordingHandler(BaseHTTPRequestHandler):
    seen: list[dict] = []

    def do_GET(self):  # noqa: N802  pylint: disable=invalid-name
        self.seen.append(dict(self.headers))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"[]")

    def log_message(self, *_args):
        pass


@pytest.fixture(name="stub_api")
def stub_api_fixture(clean_env):
    _RecordingHandler.seen = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _RecordingHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    clean_env.setattr(utils, "API_BASE_URL", f"http://127.0.0.1:{server.server_port}")
    yield _RecordingHandler.seen
    server.shutdown()
    server.server_close()


def test_static_token_reaches_the_server(clean_env, stub_api):
    clean_env.setenv("STUDYBUILDER_API_TOKEN", "a-token")
    utils.api_get("/libraries")
    assert stub_api, "stub recorded no traffic"
    assert stub_api[0].get("Authorization") == "Bearer a-token"
    assert stub_api[0].get("User-Agent") == "Data-Migrator"


def test_no_auth_sends_no_authorization_header(stub_api):
    utils.api_get("/libraries")
    assert stub_api, "stub recorded no traffic"
    assert "Authorization" not in stub_api[0]
