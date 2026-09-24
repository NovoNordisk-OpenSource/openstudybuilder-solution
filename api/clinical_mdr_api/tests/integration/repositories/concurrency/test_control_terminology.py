import unittest

from neomodel import db

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_name_repository import (
    CTCodelistNameRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_attributes_repository import (
    CTTermAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_name_repository import (
    CTTermNameRepository,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
    CTCodelistAttributesVO,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameAR,
    CTCodelistNameVO,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.tests.integration.repositories.concurrency.tools.optimistic_locking_validator import (
    OptimisticLockingValidator,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM_NAME_CYPHER,
)
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID
from common.exceptions import BusinessLogicException


class ControlTerminologyConcurrencyTest(unittest.TestCase):
    """
    Tests for the following two cases:
    - addition of a CT Term is cancelled when the codelist is modified/deleted concurrently.
    - removal of a CT Term is cancelled when the codelist is modified/deleted concurrently.
    """

    _repos = MetaRepository()
    author_id = AUTHOR_ID
    codelist_uid = "new_cr"
    library_name = "Sponsor"
    ct_term_attributes_repository: CTTermAttributesRepository
    ct_term_names_repository: CTTermNameRepository
    ct_codelist_attributes_repository: CTCodelistAttributesRepository
    ct_codelist_names_repository: CTCodelistNameRepository
    ct_codelist_name_ar: CTCodelistNameAR
    ct_codelist_attributes_ar: CTCodelistNameAR

    @classmethod
    def setUpClass(cls):
        inject_and_clear_db("concurrency.ct")

    def set_up_base_graph_for_control_terminology(self):
        db.cypher_query("MATCH (n) DETACH DELETE n")
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)

        self.ct_term_attributes_repository = self._repos.ct_term_attributes_repository
        self.ct_term_names_repository = self._repos.ct_term_name_repository
        self.ct_codelist_attributes_repository = (
            self._repos.ct_codelist_attribute_repository
        )
        self.ct_codelist_names_repository = self._repos.ct_codelist_name_repository

        library_name = "Sponsor"
        library_vo = LibraryVO.from_repository_values(
            library_name=library_name, is_editable=True
        )

        # Create new codelist

        with db.transaction:
            ct_codelist_attributes_vo = CTCodelistAttributesVO.from_repository_values(
                name="Codelist attributes",
                catalogue_names=["SDTM CT"],
                parent_codelist_uid=None,
                child_codelist_uids=[],
                submission_value="Submission Value",
                preferred_term="Preferred Term",
                definition="Definition",
                extensible=True,
            )

            ct_codelist_attributes_ar = CTCodelistAttributesAR.from_input_values(
                generate_uid_callback=lambda: self.codelist_uid,
                ct_codelist_attributes_vo=ct_codelist_attributes_vo,
                library=library_vo,
                author_id=self.author_id,
            )
            self.ct_codelist_attributes_repository.save(ct_codelist_attributes_ar)

        with db.transaction:
            ct_codelist_name_vo = CTCodelistNameVO.from_repository_values(
                catalogue_names=["SDTM CT"], name="name", is_template_parameter=False
            )
            ct_codelist_name_ar = CTCodelistNameAR.from_input_values(
                generate_uid_callback=lambda: self.codelist_uid,
                ct_codelist_name_vo=ct_codelist_name_vo,
                library=library_vo,
                author_id=self.author_id,
            )
            self.ct_codelist_names_repository.save(ct_codelist_name_ar)

        # upversion codelist
        with db.transaction:
            ct_codelist_attributes_ar = (
                self.ct_codelist_attributes_repository.find_by_uid(
                    codelist_uid=self.codelist_uid, for_update=True
                )
            )
            ct_codelist_attributes_ar.approve(
                author_id=self.author_id, change_description="changed"
            )
            self.ct_codelist_attributes_repository.save(ct_codelist_attributes_ar)

            ct_codelist_name_ar = self.ct_codelist_names_repository.find_by_uid(
                codelist_uid=self.codelist_uid, for_update=True
            )
            ct_codelist_name_ar.approve(
                author_id=self.author_id, change_description="changed"
            )
            self.ct_codelist_names_repository.save(ct_codelist_name_ar)

    def test_add_term_aborted_on_codelist_unfinalized(self):
        self.set_up_base_graph_for_control_terminology()

        with self.assertRaises(BusinessLogicException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.upversion_codelist_without_save,
                concurrent_operation=self.add_term_with_save,
                main_operation_after=self.save_codelist,
            )
        self.assertEqual(
            "Term with UID 'new_ct_term_root_2' cannot be added to Codelist with UID 'new_cr' as the codelist is in a draft state.",
            message.exception.msg,
        )

    def test_remove_term_aborted_on_codelist_unfinalized(self):
        self.set_up_base_graph_for_control_terminology()

        with db.transaction:
            self.add_term_with_save()

        with self.assertRaises(BusinessLogicException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.upversion_codelist_without_save,
                concurrent_operation=self.remove_term_with_save,
                main_operation_after=self.save_codelist,
            )
        self.assertEqual(
            "Term with UID 'new_ct_term_root_2' cannot be removed from Codelist with UID 'new_cr' as the codelist is in a draft state.",
            message.exception.msg,
        )

    def add_term_with_save(self):
        library_name = "Sponsor"
        library_vo = LibraryVO.from_repository_values(
            library_name=library_name, is_editable=True
        )

        ct_term_attributes_vo = CTTermAttributesVO.from_repository_values(
            catalogue_names=["SDTM CT"],
            concept_id=None,
            preferred_term="preferred_term",
            definition="definition",
        )

        ct_term_attributes_ar = CTTermAttributesAR.from_input_values(
            generate_uid_callback=lambda: "new_ct_term_root_2",
            ct_term_attributes_vo=ct_term_attributes_vo,
            library=library_vo,
            author_id=self.author_id,
        )

        ct_term_name_vo = CTTermNameVO.from_repository_values(
            catalogue_names=["SDTM CT"],
            name="term XYZ",
            name_sentence_case="term XYZ",
        )

        ct_term_name_ar = CTTermNameAR.from_input_values(
            generate_uid_callback=lambda: "new_ct_term_root_2",
            ct_term_name_vo=ct_term_name_vo,
            library=library_vo,
            author_id=self.author_id,
        )

        self.ct_term_attributes_repository.save(ct_term_attributes_ar)
        self.ct_term_names_repository.save(ct_term_name_ar)
        self.ct_codelist_attributes_repository.add_term(
            codelist_uid=self.codelist_uid,
            term_uid=ct_term_attributes_ar.uid,
            author_id=AUTHOR_ID,
            order=1,
            submission_value=ct_term_attributes_ar.name,
        )

    def remove_term_with_save(self):
        self.ct_codelist_attributes_repository.remove_term(
            codelist_uid=self.codelist_uid,
            term_uid="new_ct_term_root_2",
            author_id=self.author_id,
        )

    def upversion_codelist_without_save(self):
        # create a new draft version of codelist
        ct_codelist_name_ar = self.ct_codelist_names_repository.find_by_uid(
            codelist_uid=self.codelist_uid, for_update=True
        )
        ct_codelist_attributes_ar = self.ct_codelist_attributes_repository.find_by_uid(
            codelist_uid=self.codelist_uid, for_update=True
        )
        ct_codelist_name_ar.create_new_version(author_id=self.author_id)
        ct_codelist_attributes_ar.create_new_version(author_id=self.author_id)
        self.ct_codelist_name_ar = ct_codelist_name_ar
        self.ct_codelist_attributes_ar = ct_codelist_attributes_ar

    def save_codelist(self):
        self.ct_codelist_names_repository.save(self.ct_codelist_name_ar)
        self.ct_codelist_attributes_repository.save(self.ct_codelist_attributes_ar)
