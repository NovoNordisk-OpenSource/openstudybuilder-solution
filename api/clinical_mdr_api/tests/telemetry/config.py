import os

import pytest

LOG_CONFIG = os.environ.get("UVICORN_LOG_CONFIG")

if_logging_configured = pytest.mark.skipif(
    not LOG_CONFIG,
    reason="No logging configuration file was set, UVICORN_LOG_CONFIG environment variable was empty.",
)
