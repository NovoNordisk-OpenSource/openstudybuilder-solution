import contextlib
import json
import logging
import time
from functools import wraps
from typing import Mapping

import opencensus.trace
from neomodel.sync_.database import Database as NeomodelDatabase
from pydantic import BaseModel, Field
from starlette.datastructures import MutableHeaders
from starlette.responses import Response
from starlette.types import Message
from starlette_context import context

from common.config import settings
from common.telemetry import trace_block

log = logging.getLogger(__name__)

REQUEST_METRICS_HEADER_NAME = "X-Metrics"


class RequestMetrics(BaseModel):
    """Per-request metrics"""

    cypher_count: int = Field(
        0, alias="cypher.count", description="Number of Cypher queries executed"
    )
    cypher_times: float = Field(
        0,
        alias="cypher.times",
        description="Cumulative walltime (in seconds) of Cypher queries",
    )
    cypher_slowest_time: float = Field(
        0,
        alias="cypher.slowest.time",
        description="Walltime (in seconds) of the slowest Cypher query",
    )
    cypher_slowest_query: str | None = Field(
        None,
        alias="cypher.slowest.query",
        description="The slowest Cypher query (by walltime, truncated to 1000 chars) ",
    )
    cypher_slowest_query_params: dict | None = Field(
        None,
        alias="cypher.slowest.query.params",
        description="Parameters of the slowest Cypher query",
    )


def init_request_metrics():
    """Initialize request metrics object in request context"""

    if context.exists():
        context["request_metrics"] = RequestMetrics()  # type: ignore[call-arg]


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

    metrics = get_request_metrics().model_dump(
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
        span.add_attribute("cypher.query", query[: settings.trace_query_max_len])
        # span.add_attribute("cypher.params", params)

        # run the query (or any wrapped code) as a distinct operation (logical tracing block == Span)
        yield span

    # update cypher query metrics of the request
    if metrics:
        # pylint: disable=possibly-used-before-assignment
        delta_time = time.time() - start_time
        metrics.cypher_times += delta_time

        # find the slowest query of the request
        if delta_time > metrics.cypher_slowest_time:
            metrics.cypher_slowest_time = delta_time

            # also record query text and parameters if slower than the threshold
            if delta_time > settings.slow_query_duration:
                metrics.cypher_slowest_query = query[: settings.trace_query_max_len]
                # metrics.cypher_slowest_query_params = params


def patch_neomodel_database():
    """Monkey-patch neomodel db singleton to trace Cypher queries"""

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
            with cypher_tracing(query, params) as span:
                results, meta = func(
                    self,
                    session=session,
                    query=query,
                    params=params,
                    handle_unique=handle_unique,
                    retry_on_session_expire=retry_on_session_expire,
                    resolve_objects=resolve_objects,
                )
                span.add_attribute("cypher.num_results", len(results) if results else 0)
                return results, meta

        return _run_cypher_query

    log.info("Patching neomodel.sync_.database.Database")

    NeomodelDatabase._run_cypher_query = wrap(NeomodelDatabase._run_cypher_query)  # type: ignore[method-assign]
