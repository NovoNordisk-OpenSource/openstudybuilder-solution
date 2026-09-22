import pytest

from common.config import settings

if_oauth_enabled = pytest.mark.skipif(
    not settings.oauth_enabled, reason="Authentication is disabled"
)
