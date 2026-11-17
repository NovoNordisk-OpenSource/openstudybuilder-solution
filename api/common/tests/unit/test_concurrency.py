import contextvars
from unittest.mock import MagicMock

import pytest
from neo4j import Driver, Session, Transaction
from neomodel import db
from opencensus.trace import execution_context
from starlette_context import context, request_cycle_context

from common.concurrency import RequestContextThreadPoolExecutor


def run_outside_request(fn):
    """Runs fn in an empty context, i.e. outside any request a fixture may have set up"""

    return contextvars.Context().run(fn)


def test_task_runs_with_submitters_request_context():
    with request_cycle_context({"auth": "some-auth"}):
        with RequestContextThreadPoolExecutor() as executor:
            assert executor.submit(context.get, "auth").result() == "some-auth"


def test_task_submitted_outside_request_runs_outside_request():
    def submit():
        with RequestContextThreadPoolExecutor() as executor:
            return executor.submit(context.exists).result()

    assert run_outside_request(submit) is False


def test_task_receives_arguments_and_returns_result():
    def task(fn, /, request_context, *, b):
        return fn, request_context, b

    with request_cycle_context({}):
        with RequestContextThreadPoolExecutor() as executor:
            future = executor.submit(task, 1, request_context=2, b=3)
            assert future.result() == (1, 2, 3)


def test_task_runs_with_submitters_tracer():
    tracer = object()  # stands in for the request's OpenCensus tracer

    def submit():
        execution_context.set_opencensus_tracer(tracer)
        with RequestContextThreadPoolExecutor() as executor:
            return executor.submit(execution_context.get_opencensus_tracer).result()

    assert run_outside_request(submit) is tracer


def test_task_does_not_inherit_submitters_neomodel_transaction():
    transaction = MagicMock(spec=Transaction)

    def submit_inside_transaction():
        db._session = MagicMock(spec=Session)
        db._active_transaction = transaction
        with RequestContextThreadPoolExecutor() as executor:
            in_task = executor.submit(lambda: (db._active_transaction, db._session))
            return in_task.result(), db._active_transaction

    in_task, in_submitter = run_outside_request(submit_inside_transaction)
    assert in_task == (None, None)
    assert in_submitter is transaction


def test_task_reuses_submitters_neomodel_connection():
    driver = MagicMock(spec=Driver)

    def submit_while_connected():
        db.driver = driver
        with RequestContextThreadPoolExecutor() as executor:
            return executor.submit(lambda: db.driver).result()

    # neomodel reconnects, with an extra query, only when the context has no driver
    assert run_outside_request(submit_while_connected) is driver


def test_task_request_context_does_not_leak_to_next_task_on_same_thread():
    def fail():
        raise RuntimeError("task failed")

    with RequestContextThreadPoolExecutor(max_workers=1) as executor:
        with request_cycle_context({"auth": "some-auth"}):
            with pytest.raises(RuntimeError):
                executor.submit(fail).result()

        next_task = run_outside_request(lambda: executor.submit(context.exists))
        assert next_task.result() is False
