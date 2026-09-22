# pylint: disable=unused-wildcard-import,wildcard-import

from clinical_mdr_api.tests.fixtures.app import *
from clinical_mdr_api.tests.fixtures.auth import *
from clinical_mdr_api.tests.fixtures.database import *
from clinical_mdr_api.tests.fixtures.logging import *
from clinical_mdr_api.tests.fixtures.routes import *
from clinical_mdr_api.tests.fixtures.study import *
from clinical_mdr_api.tests.fixtures.tracing import *


def pytest_configure(config):
    """Register custom pytest markers"""
    # Register the order marker so pytest can recognize it
    config.addinivalue_line("markers", "order: mark test to run in a specific order")


def pytest_addoption(parser):
    """add custom command-line options to Pytest"""

    parser.addoption(
        "--keep-db",
        action="store_true",
        default=False,
        help="Do not destroy the test database after test run",
    )
    parser.addoption(
        "--enable-tracing",
        action="store_true",
        default=False,
        help="Enables logging of tracing messages of OpenCensus tracer",
    )
