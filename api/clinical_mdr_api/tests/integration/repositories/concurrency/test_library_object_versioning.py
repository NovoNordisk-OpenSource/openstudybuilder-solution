import unittest

from neomodel import db

from clinical_mdr_api.domains.libraries.object import (
    ParameterTermEntryVO,
    ParametrizedTemplateVO,
)
from clinical_mdr_api.domains.syntax_instances.objective import ObjectiveAR
from clinical_mdr_api.domains.syntax_templates.objective_template import (
    ObjectiveTemplateAR,
)
from clinical_mdr_api.domains.syntax_templates.template import TemplateVO
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.tests.integration.repositories.concurrency.tools.optimistic_locking_validator import (
    OptimisticLockingValidator,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.utils import strip_html
from common.exceptions import BusinessLogicException, NotFoundException


class ObjectiveRepositoryConcurrencyTest(unittest.TestCase):
    """
    Tests whether concurrency checks are in place when library objects change state.
    It checks that performing two versioning operations at the same time ensures that no invalid
    operations take place, given the object state.

    Note: these tests are only performed for objectives, as endpoints and timeframes use the same repository implementation.
    """

    _repos = MetaRepository()

    library_name = "Sponsor"
    author_id = "TEST"
    template_name = "Example Template"
    parameter_terms: list[ParameterTermEntryVO] = []

    # These are set as part of the test for [Objective, Endpoint, Timeframe]
    template_uid = None
    object_uid = None
    object_ar = None
    template_repository = None
    object_repository = None

    parameterized_template_vo_to_edit: ParametrizedTemplateVO

    INIT_TEST_DATA = """
    CREATE (l:Library{name: 'Sponsor', is_editable: true});
    """

    @classmethod
    def setUpClass(cls) -> None:
        inject_and_clear_db("concurrency.versioning")

    def set_up_base_graph_for_objectives(self):
        db.cypher_query("MATCH (n) DETACH DELETE n")
        db.cypher_query(self.INIT_TEST_DATA)
        self.template_uid = "ObjectiveTemplate_000002"
        self.object_uid = "Objective_000001"
        self.template_repository = self._repos.objective_template_repository
        self.object_repository = self._repos.objective_repository
        # Set up the base data
        template_vo = TemplateVO.from_repository_values(
            template_name=self.template_name,
            template_name_plain=strip_html(self.template_name),
        )
        library_vo = LibraryVO.from_input_values_2(
            library_name="Sponsor", is_library_editable_callback=lambda _: True
        )
        objective_template_ar = ObjectiveTemplateAR.from_input_values(
            author_id=self.author_id,
            template=template_vo,
            library=library_vo,
            generate_uid_callback=lambda: self.template_uid,
        )
        # Create template
        with db.transaction:
            self.template_repository.save(objective_template_ar)
        # Approve template
        with db.transaction:
            objective_template_ar = self.template_repository.find_by_uid(
                self.template_uid, for_update=True
            )
            objective_template_ar.approve(author_id=self.author_id)
            self.template_repository.save(objective_template_ar)
        parameterized_template_vo = (
            ParametrizedTemplateVO.from_name_and_parameter_terms(
                name=self.template_name,
                template_uid=self.template_uid,
                parameter_terms=self.parameter_terms,
                library_name=objective_template_ar.library.name,
            )
        )
        self.parameterized_template_vo_to_edit = (
            ParametrizedTemplateVO.from_name_and_parameter_terms(
                name=f"{self.template_name} to edit",
                template_uid=self.template_uid,
                parameter_terms=self.parameter_terms,
                library_name=objective_template_ar.library.name,
            )
        )
        library_vo = LibraryVO.from_input_values_2(
            library_name="Sponsor", is_library_editable_callback=lambda _: True
        )
        self.object_ar = ObjectiveAR.from_input_values(
            author_id=self.author_id,
            template=parameterized_template_vo,
            library=library_vo,
        )
        self.object_repository.save(self.object_ar)

    def test_soft_delete_objective_aborted_on_approval(self):
        self.set_up_base_graph_for_objectives()
        with self.assertRaises(BusinessLogicException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.approve_object_without_save,
                concurrent_operation=self.soft_delete_object_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual("Object has been accepted", message.exception.msg)

    def test_approve_objective_aborted_on_soft_delete(self):
        self.set_up_base_graph_for_objectives()
        with self.assertRaises(NotFoundException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.soft_delete_object_with_save,
                concurrent_operation=self.approve_object_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual(
            "Resource doesn't exist - it was likely deleted in a concurrent transaction.",
            message.exception.msg,
        )

    def test_edit_objective_aborted_on_approval(self):
        self.set_up_base_graph_for_objectives()
        with self.assertRaises(BusinessLogicException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.approve_object_without_save,
                concurrent_operation=self.edit_object_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual("The object isn't in draft status.", message.exception.msg)

    def test_edit_objective_aborted_on_soft_delete(self):
        self.set_up_base_graph_for_objectives()
        with self.assertRaises(NotFoundException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.soft_delete_object_with_save,
                concurrent_operation=self.edit_object_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual(
            "Resource doesn't exist - it was likely deleted in a concurrent transaction.",
            message.exception.msg,
        )

    def test_inactivate_aborted_on_new_version(self):
        self.set_up_base_graph_for_objectives()
        with db.transaction:
            self.approve_object_with_save()
        with self.assertRaises(BusinessLogicException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.new_version_without_save,
                concurrent_operation=self.inactivate_object_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual("Cannot retire draft version.", message.exception.msg)

    def test_new_version_aborted_on_inactivate(self):
        self.set_up_base_graph_for_objectives()
        with db.transaction:
            self.approve_object_with_save()
        with self.assertRaises(BusinessLogicException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.inactivate_object_without_save,
                concurrent_operation=self.new_version_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual(
            "New draft version can be created only for FINAL versions.",
            message.exception.msg,
        )

    def test_new_version_aborted_on_reactivate(self):
        self.set_up_base_graph_for_objectives()
        with db.transaction:
            self.approve_object_with_save()
        with db.transaction:
            self.inactivate_object_with_save()
        with self.assertRaises(BusinessLogicException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.reactivate_object_without_save,
                concurrent_operation=self.new_version_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual(
            "Only RETIRED version can be reactivated.", message.exception.msg
        )

    def test_reactivate_aborted_on_new_version(self):
        self.set_up_base_graph_for_objectives()
        with db.transaction:
            self.approve_object_with_save()
        with db.transaction:
            self.inactivate_object_with_save()
        with self.assertRaises(BusinessLogicException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.new_version_without_save,
                concurrent_operation=self.reactivate_object_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual(
            "Only RETIRED version can be reactivated.", message.exception.msg
        )

    # Helper functions to be used by the locking validator:

    def approve_object_without_save(self):
        object_ar = self.object_repository.find_by_uid(self.object_uid, for_update=True)
        object_ar.approve(author_id=self.author_id, change_description="APPROVED!")
        self.object_ar = object_ar

    def approve_object_with_save(self):
        object_ar = self.object_repository.find_by_uid(self.object_uid, for_update=True)
        object_ar.approve(author_id=self.author_id, change_description="APPROVED!")
        self.object_repository.save(object_ar)

    def soft_delete_object_with_save(self):
        object_ar = self.object_repository.find_by_uid(self.object_uid, for_update=True)
        object_ar.soft_delete()
        self.object_repository.save(object_ar)

    def edit_object_with_save(self):
        object_ar = self.object_repository.find_by_uid(self.object_uid, for_update=True)
        object_ar.edit_draft(
            author_id=self.author_id,
            change_description="Edited",
            template=self.parameterized_template_vo_to_edit,
        )
        self.object_repository.save(self.object_ar)

    def inactivate_object_without_save(self):
        object_ar = self.object_repository.find_by_uid(self.object_uid, for_update=True)
        object_ar.inactivate(author_id=self.author_id, change_description="Inactivated")
        self.object_ar = object_ar

    def inactivate_object_with_save(self):
        object_ar = self.object_repository.find_by_uid(self.object_uid, for_update=True)
        object_ar.inactivate(author_id=self.author_id, change_description="Inactivated")
        self.object_repository.save(self.object_ar)

    def new_version_without_save(self):
        object_ar = self.object_repository.find_by_uid(self.object_uid, for_update=True)
        object_ar._create_new_version(
            author_id=self.author_id, change_description="New Draft"
        )
        self.object_ar = object_ar

    def new_version_with_save(self):
        object_ar = self.object_repository.find_by_uid(self.object_uid, for_update=True)
        object_ar._create_new_version(
            author_id=self.author_id, change_description="New Draft"
        )
        self.object_repository.save(self.object_ar)

    def reactivate_object_without_save(self):
        object_ar = self.object_repository.find_by_uid(self.object_uid, for_update=True)
        object_ar.reactivate(author_id=self.author_id, change_description="Reactivated")
        self.object_ar = object_ar

    def reactivate_object_with_save(self):
        object_ar = self.object_repository.find_by_uid(self.object_uid, for_update=True)
        object_ar.reactivate(author_id=self.author_id, change_description="Reactivated")
        self.object_repository.save(self.object_ar)

    def save_object(self):
        self.object_repository.save(self.object_ar)
