import unittest

from neomodel import db

from clinical_mdr_api.domains.libraries.object import (
    ParameterTermEntryVO,
    ParametrizedTemplateVO,
)
from clinical_mdr_api.domains.syntax_instances.endpoint import EndpointAR
from clinical_mdr_api.domains.syntax_instances.objective import ObjectiveAR
from clinical_mdr_api.domains.syntax_instances.timeframe import TimeframeAR
from clinical_mdr_api.domains.syntax_templates.endpoint_template import (
    EndpointTemplateAR,
)
from clinical_mdr_api.domains.syntax_templates.objective_template import (
    ObjectiveTemplateAR,
)
from clinical_mdr_api.domains.syntax_templates.template import TemplateVO
from clinical_mdr_api.domains.syntax_templates.timeframe_template import (
    TimeframeTemplateAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.tests.integration.repositories.concurrency.tools.optimistic_locking_validator import (
    OptimisticLockingValidator,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db


class ObjectiveRepositoryConcurrencyTest(unittest.TestCase):
    """
    Tests whether template instantiations are aborted when the template is concurrently retired.
    The OptimisticLockingValidator is used to do this for library elements (objectives, endpoints, timeframes)
    """

    _repos = MetaRepository()
    graph = None

    library_name = "Sponsor"
    author_id = "TEST"
    template_name = "Example Template"
    parameter_terms: list[ParameterTermEntryVO] = []

    # These are set as part of the test for [Objective, Endpoint, Timeframe]
    template_uid = None
    template_ar = None
    object_uid = None
    object_ar = None
    template_repository = None
    object_repository = None

    INIT_TEST_DATA = """
    CREATE (l:Library{name: 'Sponsor', is_editable: true});
    """

    def setUp(self):
        inject_and_clear_db("concurrency.templates")
        db.cypher_query(self.INIT_TEST_DATA)

    def test_create_objective_aborted_on_inactivate_template(self):
        self.template_uid = "ObjectiveTemplate_000002"
        self.object_uid = "Objective_000001"
        self.template_repository = self._repos.objective_template_repository
        self.object_repository = self._repos.objective_repository
        # Set up the base data
        template_vo = TemplateVO.from_repository_values(
            template_name=self.template_name, template_name_plain=self.template_name
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
        library_vo = LibraryVO.from_input_values_2(
            library_name="Sponsor", is_library_editable_callback=lambda _: True
        )
        self.object_ar = ObjectiveAR.from_input_values(
            author_id=self.author_id,
            template=parameterized_template_vo,
            library=library_vo,
        )

        self.validate_concurrency_check_for_template_instantiation()

    def test_create_endpoint_aborted_on_inactivate_template(self):
        self.template_uid = "EndpointTemplate_000002"
        self.object_uid = "Endpoint_000001"
        self.template_repository = self._repos.endpoint_template_repository
        self.object_repository = self._repos.endpoint_repository
        # Set up the base data
        template_vo = TemplateVO.from_repository_values(
            template_name=self.template_name, template_name_plain=self.template_name
        )
        library_vo = LibraryVO.from_input_values_2(
            library_name="Sponsor", is_library_editable_callback=lambda _: True
        )
        endpoint_template_ar = EndpointTemplateAR.from_input_values(
            author_id=self.author_id,
            template=template_vo,
            library=library_vo,
            generate_uid_callback=lambda: self.template_uid,
        )
        # Create template
        with db.transaction:
            self.template_repository.save(endpoint_template_ar)

        # Approve template
        with db.transaction:
            endpoint_template_ar = self.template_repository.find_by_uid(
                self.template_uid, for_update=True
            )
            endpoint_template_ar.approve(author_id=self.author_id)
            self.template_repository.save(endpoint_template_ar)
        parameterized_template_vo = (
            ParametrizedTemplateVO.from_name_and_parameter_terms(
                name=self.template_name,
                template_uid=self.template_uid,
                parameter_terms=self.parameter_terms,
                library_name=endpoint_template_ar.library.name,
            )
        )
        library_vo = LibraryVO.from_input_values_2(
            library_name="Sponsor", is_library_editable_callback=lambda _: True
        )
        self.object_ar = EndpointAR.from_input_values(
            author_id=self.author_id,
            template=parameterized_template_vo,
            library=library_vo,
        )

        self.validate_concurrency_check_for_template_instantiation()

    def test_create_timeframe_aborted_on_inactivate_template(self):
        self.template_uid = "TimeframeTemplate_000002"
        self.object_uid = "Timeframe_000001"
        self.template_repository = self._repos.timeframe_template_repository
        self.object_repository = self._repos.timeframe_repository
        # Set up the base data
        template_vo = TemplateVO.from_repository_values(
            template_name=self.template_name, template_name_plain=self.template_name
        )
        library_vo = LibraryVO.from_input_values_2(
            library_name="Sponsor", is_library_editable_callback=lambda _: True
        )
        timeframe_template_ar = TimeframeTemplateAR.from_input_values(
            author_id=self.author_id,
            template=template_vo,
            library=library_vo,
            generate_uid_callback=lambda: self.template_uid,
        )
        # Create template
        with db.transaction:
            self.template_repository.save(timeframe_template_ar)

        # Approve template
        with db.transaction:
            timeframe_template_ar = self.template_repository.find_by_uid(
                self.template_uid, for_update=True
            )
            timeframe_template_ar.approve(author_id=self.author_id)
            self.template_repository.save(timeframe_template_ar)
        parameterized_template_vo = (
            ParametrizedTemplateVO.from_name_and_parameter_terms(
                name=self.template_name,
                template_uid=self.template_uid,
                parameter_terms=self.parameter_terms,
                library_name=timeframe_template_ar.library.name,
            )
        )
        library_vo = LibraryVO.from_input_values_2(
            library_name="Sponsor", is_library_editable_callback=lambda _: True
        )
        self.object_ar = TimeframeAR.from_input_values(
            author_id=self.author_id,
            template=parameterized_template_vo,
            library=library_vo,
        )

        self.validate_concurrency_check_for_template_instantiation()

    def validate_concurrency_check_for_template_instantiation(self):
        # TODO - Neo4j 4.3 produces a transient error in this case.
        # This is a known bug, which will be resolved in 4.4. We should revisit this when we upgrade to 4.4.
        with self.assertRaises(Exception) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.get_and_inactivate_template,
                concurrent_operation=self.create_object_from_template,
                main_operation_after=self.save_inactivated_template,
            )
        self.assertEqual("TransientError", str(message.exception.__class__.__name__))

        # with self.assertRaises(ValueError) as message:
        #     OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
        #         main_operation_before=self.get_and_inactivate_template,
        #         concurrent_operation=self.create_object_from_template,
        #         main_operation_after=self.save_inactivated_template
        #     )
        # self.assertEqual(
        #     self.object_uid + " cannot be added to " + self.template_uid + ", as it is retired.",
        #     str(message.exception))

    def get_and_inactivate_template(self):
        template_ar = self.template_repository.find_by_uid(
            self.template_uid, for_update=True
        )
        template_ar.inactivate(author_id=self.author_id)
        # Store the new template so that we can later save it
        self.template_ar = template_ar

    def create_object_from_template(self):
        self.object_repository.save(self.object_ar)

    def save_inactivated_template(self):
        self.template_repository.save(self.template_ar)
