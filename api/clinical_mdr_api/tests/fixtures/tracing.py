import logging

import pytest
from opencensus.trace.logging_exporter import LoggingExporter
from opencensus.trace.samplers import AlwaysOnSampler
from opencensus.trace.tracer import Tracer

__all__ = ["tracer"]

log = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def tracer(request: pytest.FixtureRequest):
    """Initializes OpenCensus tracer to log tracing messages when Pytest executed with `--enable-tracing` option"""

    if request.config.getoption("--enable-tracing"):
        log.info("%s fixture: initializing tracing", request.fixturename)

        tracy = Tracer(sampler=AlwaysOnSampler(), exporter=LoggingExporter())

        with tracy.span(request.node.name):
            yield

    else:
        log.debug("%s fixture: skipping tracing", request.fixturename)
        yield
