import unittest
from unittest.mock import patch

from neomodel import db

from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domains.syntax_templates.objective_template import (
    ObjectiveTemplateAR,
)
from clinical_mdr_api.domains.syntax_templates.template import TemplateVO
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.utils import strip_html


class ForUpdateCacheBypassTest(unittest.TestCase):
    """
    Regression test for the for_update=True cache-bypass fix.

    The class-level TTL cache on find_by_uid_2 / find_by_uid_optimized /
    CTTermGenericRepository.find_by_uid used to include for_update in the
    hashkey but still read/write the same cache — so a second call with
    for_update=True could be served from a cache entry populated by an
    earlier call (in an earlier transaction), skipping the method body
    entirely and therefore skipping _lock_object().

    Neo4j write locks are transaction-scoped and released at commit, so a
    cached aggregate from a prior committed transaction represents no live
    lock in the caller's current transaction. These tests would have
    passed only vacuously before the fix (the spy would have recorded one
    call instead of two).
    """

    _repos = MetaRepository()
    author_id = "TEST"
    library_name = "Sponsor"
    template_name = "Example Template"
    template_uid = "ObjectiveTemplate_bypass_test"

    INIT_TEST_DATA = "CREATE (l:Library{name: 'Sponsor', is_editable: true});"

    @classmethod
    def setUpClass(cls) -> None:
        inject_and_clear_db("concurrency.forupdate-cache-bypass")

    def setUp(self) -> None:
        db.cypher_query("MATCH (n) DETACH DELETE n")
        db.cypher_query(self.INIT_TEST_DATA)
        # Class-level TTL cache is process-wide — clear it so prior tests in
        # this process don't pre-populate the entry for our uid.
        LibraryItemRepositoryImplBase.cache_store_item_by_uid.clear()

        self.template_repository = self._repos.objective_template_repository

        template_vo = TemplateVO.from_repository_values(
            template_name=self.template_name,
            template_name_plain=strip_html(self.template_name),
        )
        library_vo = LibraryVO.from_input_values_2(
            library_name=self.library_name,
            is_library_editable_callback=lambda _: True,
        )
        objective_template_ar = ObjectiveTemplateAR.from_input_values(
            author_id=self.author_id,
            template=template_vo,
            library=library_vo,
            generate_uid_callback=lambda: self.template_uid,
        )
        with db.transaction:
            self.template_repository.save(objective_template_ar)

    def test_for_update_true_always_locks_even_when_cache_is_primed(self) -> None:
        """Two back-to-back for_update=True calls must both call _lock_object,
        even after the cache has been populated by a prior read-only call
        with otherwise-matching arguments."""
        # Prime the cache with a read-only call first. Before the fix, this
        # entry would have been re-used by the subsequent for_update=True
        # calls (because for_update is part of the hashkey but the cache
        # is shared), silently skipping the method body — including the
        # _lock_object call.
        with db.transaction:
            self.template_repository.find_by_uid(self.template_uid)

        with patch.object(
            self.template_repository,
            "_lock_object",
            wraps=self.template_repository._lock_object,
        ) as spy_lock:
            with db.transaction:
                self.template_repository.find_by_uid(self.template_uid, for_update=True)
            with db.transaction:
                self.template_repository.find_by_uid(self.template_uid, for_update=True)

        self.assertEqual(
            spy_lock.call_count,
            2,
            "_lock_object must be called on every for_update=True invocation; "
            f"got {spy_lock.call_count}. The TTL cache is masking the write lock.",
        )

    def test_for_update_false_still_uses_cache(self) -> None:
        """Read-path caching is unchanged: two for_update=False calls with
        the same arguments hit the DB only once."""
        with patch.object(
            self.template_repository,
            "_find_cypher_query_optimized",
            wraps=self.template_repository._find_cypher_query_optimized,
        ) as spy_build_query:
            with db.transaction:
                self.template_repository.find_by_uid(self.template_uid)
            with db.transaction:
                self.template_repository.find_by_uid(self.template_uid)

        self.assertEqual(
            spy_build_query.call_count,
            1,
            "for_update=False reads should be served from the cache on the "
            f"second call; got {spy_build_query.call_count} invocations.",
        )
