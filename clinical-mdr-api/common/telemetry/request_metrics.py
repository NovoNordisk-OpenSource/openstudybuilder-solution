import contextlib
import json
import logging
import time
from functools import wraps
from typing import Annotated, Mapping

import neomodel
import opencensus.trace
from pydantic import BaseModel, Field
from starlette.datastructures import MutableHeaders
from starlette.responses import Response
from starlette.types import Message
from starlette_context import context

from common import config
from common.telemetry import trace_block

log = logging.getLogger(__name__)

REQUEST_METRICS_HEADER_NAME = "X-Metrics"


class RequestMetrics(BaseModel):
    """Per-request metrics"""

    cypher_count: Annotated[
        int, Field(alias="cypher.count", title="Number of Cypher queries executed")
    ] = 0
    cypher_times: Annotated[
        float,
        Field(
            alias="cypher.times",
            title="Cumulative walltime (in seconds) of Cypher queries",
        ),
    ] = 0
    cypher_slowest_time: Annotated[
        float,
        Field(
            alias="cypher.slowest.time",
            title="Walltime (in seconds) of the slowest Cypher query",
        ),
    ] = 0
    cypher_slowest_query: Annotated[
        str | None,
        Field(
            alias="cypher.slowest.query",
            title="The slowest Cypher query (by walltime, truncated to 1000 chars) ",
        ),
    ] = None
    cypher_slowest_query_params: Annotated[
        dict | None,
        Field(
            alias="cypher.slowest.query.params",
            title="Parameters of the slowest Cypher query",
        ),
    ] = None


def init_request_metrics():
    """Initialize request metrics object in request context"""

    if context.exists():
        context["request_metrics"] = RequestMetrics()


def include_request_metrics(span: opencensus.trace.Span):
    """Adds request metrics to tracing Span"""

    if metrics := get_request_metrics():
        for key, val in metrics.dict(by_alias=True, exclude_none=True).items():
            span.add_attribute(key, val)


def get_request_metrics() -> RequestMetrics | None:
    """Gets request metrics object from request context"""

    if context.exists():
        return context.get("request_metrics")

    return None


def add_request_metrics_header(
    response: Response | Message,
    expose_header: bool = False,
) -> None:
    """Adds custom response header with request metrics"""

    metrics = get_request_metrics()
    metrics = metrics.dict(
        by_alias=True, include={"cypher_count", "cypher_times", "cypher_slowest_time"}
    )
    metrics = {
        k: (round(v, 4) if isinstance(v, float) else v) for k, v in metrics.items()
    }
    value = json.dumps(metrics)

    if isinstance(response, Response):
        headers = response.headers
    else:
        headers = MutableHeaders(scope=response)

    headers.append(REQUEST_METRICS_HEADER_NAME, value)
    if expose_header:
        headers.setdefault("Access-Control-Expose-Headers", REQUEST_METRICS_HEADER_NAME)


@contextlib.contextmanager
# pylint: disable=unused-argument
def cypher_tracing(query: str, params: Mapping):
    """cypher query tracing and metrics to Opencensus"""
    # update request metrics
    if metrics := get_request_metrics():
        metrics.cypher_count += 1
        start_time = time.time()

    with trace_block("neomodel.query") as span:
        span.add_attribute("cypher.query", query[: config.TRACE_QUERY_MAX_LEN])
        # span.add_attribute("cypher.params", params)

        # run the query (or any wrapped code) as a distinct operation (logical tracing block == Span)
        yield

    # update cypher query metrics of the request
    if metrics:
        # pylint: disable=possibly-used-before-assignment
        delta_time = time.time() - start_time
        metrics.cypher_times += delta_time

        # find the slowest query of the request
        if delta_time > metrics.cypher_slowest_time:
            metrics.cypher_slowest_time = delta_time

            # also record query text and parameters if slower than the threshold
            if delta_time > config.SLOW_QUERY_TIME_SECS:
                metrics.cypher_slowest_query = query[: config.TRACE_QUERY_MAX_LEN]
                # metrics.cypher_slowest_query_params = params


def patch_neomodel_database():
    """Monkey-patch neomodel.core.db singleton to trace Cypher queries"""

    def wrap(func):
        @wraps(func)
        def _run_cypher_query(
            self,
            session,
            query,
            params,
            handle_unique,
            retry_on_session_expire,
            resolve_objects,
        ):
            with cypher_tracing(query, params):
                return func(
                    self,
                    session=session,
                    query=query,
                    params=params,
                    handle_unique=handle_unique,
                    retry_on_session_expire=retry_on_session_expire,
                    resolve_objects=resolve_objects,
                )

        return _run_cypher_query

    log.info("Patching neomodel.util.Database")

    neomodel.sync_.core.Database._run_cypher_query = wrap(
        neomodel.sync_.core.Database._run_cypher_query
    )
