import pytest
from neomodel import db

from clinical_mdr_api.services._utils import ensure_transaction
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db


class TestEnsureTransaction:
    """tests @ensure_transaction decorator and intrinsically AggregatedTransactionProxy"""

    def setup_class(self):
        inject_and_clear_db("service.utils")

    @staticmethod
    def assert_transaction_started():
        """asserts a db transaction is started"""

        # pylint: disable=unused-variable
        __tracebackhide__ = True

        with pytest.raises(SystemError, match="Transaction in progress"):
            db.begin()

    @classmethod
    def query(cls):
        cls.assert_transaction_started()

        results, _ = db.cypher_query("RETURN 'hello' AS msg")
        assert results[0][0] == "hello"

    @db.transaction
    def always_starts_transaction(self):
        self.query()

    @ensure_transaction(db)
    def conditionally_starts_transaction(self):
        self.query()

    @db.transaction
    def test_embed_transaction_fail(self):
        self.query()
        with pytest.raises(SystemError, match="Transaction in progress"):
            self.always_starts_transaction()

    @ensure_transaction(db)
    def test_embed_transaction_fail_2(self):
        self.query()
        with pytest.raises(SystemError, match="Transaction in progress"):
            self.always_starts_transaction()

    @db.transaction
    def test_embed_ensure_transaction_1(self):
        self.query()
        self.conditionally_starts_transaction()

    @ensure_transaction(db)
    def test_embed_ensure_transaction_2(self):
        self.query()
        self.conditionally_starts_transaction()
