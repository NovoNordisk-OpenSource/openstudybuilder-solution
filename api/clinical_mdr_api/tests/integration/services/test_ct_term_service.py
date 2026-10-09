import unittest

from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTermCodelistInput,
    CTTermCreateInput,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import inject_base_data
from common.exceptions import BusinessLogicException


class TestCTTermNonexistentCodelist(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("cttermservicetest")
        inject_base_data()

    def test_nonexistent_codelist_uid_raises_bad_request(self):
        # A codelist_uid that exists in the payload but resolves to no graph
        # node must be treated as invalid create input (400).
        with self.assertRaises(BusinessLogicException):
            CTTermService().create(
                CTTermCreateInput(
                    catalogue_names=["SDTM CT"],
                    codelists=[
                        CTTermCodelistInput(
                            codelist_uid="nonexistent_codelist_uid",
                            submission_value="SUB",
                        )
                    ],
                    definition="Test definition",
                    sponsor_preferred_name="Test term",
                    sponsor_preferred_name_sentence_case="test term",
                    library_name="Sponsor",
                )
            )
