import contextvars
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

from neomodel import db


class RequestContextThreadPoolExecutor(ThreadPoolExecutor):
    """ThreadPoolExecutor whose tasks run in a copy of the submitter's context.

    The copy carries the request context (the authenticated user for Neo4j transaction
    metadata, and the request metrics), the OpenCensus tracer, and neomodel's open
    connection, so a task does not reconnect to Neo4j. Only neomodel's active
    transaction is withheld: a Neo4j transaction must never be shared between threads.
    """

    def submit[T](
        self, fn: Callable[..., T], /, *args: Any, **kwargs: Any
    ) -> Future[T]:
        # A copy per task, so nothing a task sets outlives it or reaches the submitter
        task_context = contextvars.copy_context()
        return super().submit(
            task_context.run, _run_outside_transaction, fn, *args, **kwargs
        )


def _run_outside_transaction[T](
    fn: Callable[..., T], /, *args: Any, **kwargs: Any
) -> T:
    # Detaches only the task's own context copy; the submitter's transaction is untouched
    db._active_transaction = None
    db._session = None
    return fn(*args, **kwargs)
