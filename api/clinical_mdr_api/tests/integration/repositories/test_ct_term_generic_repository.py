import unittest

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_name_repository import (
    CTTermNameRepository,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db


class TestFindByUidWithCodelistName(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("cttermgenericrepo")
        self.repository = CTTermNameRepository()

    def test_returns_none_when_term_is_not_in_the_codelist(self):
        # Filtering across a relationship makes neomodel return a row, so the
        # lookup subscripts the result. Nothing matches here, so the result is
        # None and subscripting it used to raise TypeError, surfacing as a 500
        # even though every caller checks for None.
        result = self.repository.find_by_uid(
            term_uid="CTTerm_000001", codelist_name="No Such Codelist"
        )

        self.assertIsNone(result)
