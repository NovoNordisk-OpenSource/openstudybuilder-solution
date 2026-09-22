import threading
from typing import Callable

from neomodel import db


class ExceptionCatchingThread(threading.Thread):
    """
    An extension of the Thread class to ensure that exceptions are caught and returned to the main caller.
    """

    exc = None

    def __init__(self, target=None, args=()):
        super().__init__(target=target, args=args)

    def run(self):
        try:
            super().run()
        # pylint: disable=broad-except
        except BaseException as e:
            self.exc = e

    def join(self, **kwargs):
        super().join(**kwargs)
        # Since join() returns in caller thread, we re-raise the caught exception if any was caught
        if self.exc:
            raise self.exc


class OptimisticLockingValidator:
    # Timeout used to validate that the secondary thread is blocked by database locks.
    thread_timeout: int = 2

    def __init__(self, thread_timeout: int | None = 2):
        self.thread_timeout = thread_timeout

    def assert_optimistic_locking_ensures_execution_order(
        self,
        main_operation_before: Callable,
        concurrent_operation: Callable,
        main_operation_after: Callable,
    ) -> None:
        """

        A framework for validating that optimistic locking is in place to prevent concurrent updates.

        As arguments, it takes three methods:
        :param main_operation_before: repository operations that grab a lock on parts of the Neo4j graph.
        :param concurrent_operation: concurrent repository operations that need to wait for locks to become free.
        :param main_operation_after: repository operations after which the locks are released.

        The method sets up two concurrency database transactions:
        - Transaction A, which calls main_operation_before() and main_operation_after()
        - Transaction B, which calls concurrent_operation().
        concurrent_operation() is called in between main_operation_before() and main_operation_after().

        Calling the method tests that:
        - concurrent_operation() waits for the locks to be released by main_operation_before().
        - concurrent_operation() finishes after the locks are released by main_operation_after().
        """
        concurrent_thread = ExceptionCatchingThread(
            target=self._execute_in_other_transaction_context,
            args=[concurrent_operation],
        )
        # Start transaction A.
        with db.transaction:
            # Grab the locks by performing some repository operations.
            main_operation_before()

            # Start the second thread with the concurrent operation.
            concurrent_thread.start()

            # Validate that the thread doesn't finish within a set time (e.g. the locks are still taken)
            concurrent_thread.join(timeout=self.thread_timeout)
            if not concurrent_thread.is_alive():
                raise AssertionError(
                    "The thread for "
                    + concurrent_operation.__name__
                    + " has completed. No shared locks were grabbed by the main transaction, "
                    "and concurrent updates may create an invalid state in the graph."
                )

            # Perform the final work in transaction A, after which the locks are released.
            main_operation_after()

        # Now that the locks from the main transaction are released, the thread should finish.
        concurrent_thread.join(timeout=self.thread_timeout)

        if concurrent_thread.is_alive():
            raise AssertionError(
                "The thread for "
                + concurrent_operation.__name__
                + " is still running. Locks weren't released by main transaction."
            )

    def _execute_in_other_transaction_context(self, concurrent_operation) -> None:
        # Executes an operation within the context of another database transaction.
        with db.transaction:
            concurrent_operation()
