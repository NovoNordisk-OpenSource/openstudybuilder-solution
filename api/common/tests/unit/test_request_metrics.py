import sys

import pytest
from starlette_context import request_cycle_context

from common.concurrency import RequestContextThreadPoolExecutor
from common.config import settings
from common.telemetry.request_metrics import RequestMetrics, cypher_tracing


@pytest.fixture(name="metrics")
def fixture_metrics():
    metrics = RequestMetrics()  # type: ignore[call-arg]
    with request_cycle_context({"request_metrics": metrics}):
        yield metrics


@pytest.fixture(name="frequent_thread_switches")
def fixture_frequent_thread_switches():
    """Makes updates lost between threads likely, instead of rare"""

    interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)
    yield
    sys.setswitchinterval(interval)


def run_queries(count: int) -> None:
    for _ in range(count):
        with cypher_tracing("RETURN 1", {}):
            pass


@pytest.mark.usefixtures("frequent_thread_switches")
def test_queries_of_worker_threads_are_all_counted(metrics):
    with RequestContextThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(run_queries, 2_000) for _ in range(8)]
        for future in futures:
            future.result()

    assert metrics.cypher_count == 8 * 2_000


def test_failed_query_is_counted(metrics):
    with pytest.raises(RuntimeError):
        with cypher_tracing("RETURN 1", {}):
            raise RuntimeError("query failed")

    assert metrics.cypher_count == 1


def test_slowest_query_is_recorded_above_threshold(metrics):
    threshold = settings.slow_query_duration

    metrics.record_cypher_query("FAST", threshold / 2)
    metrics.record_cypher_query("SLOW", threshold * 2)
    metrics.record_cypher_query("FASTER", threshold / 4)

    assert metrics.cypher_count == 3
    assert metrics.cypher_times == pytest.approx(threshold * 2.75)
    assert metrics.cypher_slowest_time == threshold * 2
    assert metrics.cypher_slowest_query == "SLOW"


def test_slowest_query_below_threshold_is_timed_but_not_recorded(metrics):
    metrics.record_cypher_query("FAST", settings.slow_query_duration / 2)

    assert metrics.cypher_slowest_time == settings.slow_query_duration / 2
    assert metrics.cypher_slowest_query is None
