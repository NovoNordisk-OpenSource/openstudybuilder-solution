import logging

import pytest

__all__ = ["silence_neo4j_notifications"]

log = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def silence_neo4j_notifications(request: pytest.FixtureRequest):
    verbosity = request.config.option.verbose
    if verbosity < 3:
        log.info(
            "%s fixture: silencing logger neo4j.notifications", request.fixturename
        )
        logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)
