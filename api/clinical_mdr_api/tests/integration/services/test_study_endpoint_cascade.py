import unittest

from neomodel import db

from clinical_mdr_api.domain_repositories.models.generic import Library
from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.domain_repositories.models.syntax import (
    EndpointRoot,
    EndpointTemplateRoot,
    ObjectiveRoot,
    ObjectiveTemplateRoot,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameter,
    TemplateParameterTermRoot,
    TemplateParameterTermValue,
)
from clinical_mdr_api.domain_repositories.syntax_templates.endpoint_template_repository import (
    EndpointTemplateRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.objective_template_repository import (
    ObjectiveTemplateRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.timeframe_template_repository import (
    TimeframeTemplateRepository,
)
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
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySelectionEndpoint,
    StudySelectionEndpointInput,
    StudySelectionObjective,
    StudySelectionObjectiveInput,
)
from clinical_mdr_api.models.syntax_instances.endpoint import EndpointCreateInput
from clinical_mdr_api.models.syntax_instances.objective import ObjectiveCreateInput
from clinical_mdr_api.models.syntax_instances.timeframe import TimeframeCreateInput
from clinical_mdr_api.models.syntax_templates.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.services.studies.study_endpoint_selection import (
    StudyEndpointSelectionService,
)
from clinical_mdr_api.services.studies.study_objective_selection import (
    StudyObjectiveSelectionService,
)
from clinical_mdr_api.services.syntax_instances.endpoints import EndpointService
from clinical_mdr_api.services.syntax_instances.objectives import ObjectiveService
from clinical_mdr_api.services.syntax_instances.timeframes import TimeframeService
from clinical_mdr_api.services.syntax_templates.endpoint_templates import (
    EndpointTemplateService,
)
from clinical_mdr_api.services.syntax_templates.objective_templates import (
    ObjectiveTemplateService,
)
from clinical_mdr_api.services.syntax_templates.timeframe_templates import (
    TimeframeTemplateService,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_PARAMETERS_CYPHER,
    STARTUP_STUDY_ENDPOINT_CYPHER,
)


class TestStudyEndpointUpversion(unittest.TestCase):
    TPR_LABEL = "ParameterName"
    default_template_name = f"Test [{TPR_LABEL}]"
    default_template_name_plain = f"Test {TPR_LABEL}"
    changed_template_name = f"Changed Test [{TPR_LABEL}]"
    changed_template_name_plain = f"Changed Test {TPR_LABEL}"
    lib: Library

    def setUp(self):
        inject_and_clear_db("studyendpointupversion")
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(STARTUP_STUDY_ENDPOINT_CYPHER)

        # Generate UIDs
        StudyRoot.generate_node_uids_if_not_present()
        ObjectiveRoot.generate_node_uids_if_not_present()
        ObjectiveTemplateRoot.generate_node_uids_if_not_present()
        EndpointRoot.generate_node_uids_if_not_present()
        EndpointTemplateRoot.generate_node_uids_if_not_present()

        self.lib = Library(name="LibraryName", is_editable=True)
        self.lib.save()
        self.tpr = TemplateParameter(name=self.TPR_LABEL)
        self.tpr.save()
        self.ttr = TimeframeTemplateRepository()
        self.etr = EndpointTemplateRepository()
        self.otr = ObjectiveTemplateRepository()
        self.objective_service: ObjectiveService = ObjectiveService()
        self.endpoint_service: EndpointService = EndpointService()
        self.timeframe_service: TimeframeService = TimeframeService()
        self.objective_template_service = ObjectiveTemplateService()
        self.timeframe_template_service = TimeframeTemplateService()
        self.endpoint_template_service = EndpointTemplateService()

        self.library = LibraryVO(name="LibraryName", is_editable=True)
        self.template_vo = TemplateVO(
            name=self.default_template_name,
            name_plain=self.default_template_name_plain,
        )
        self.item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id="Test"
        )
        self.ot_ar = ObjectiveTemplateAR(
            _uid=self.otr.root_class.get_next_free_uid_and_increment_counter(),
            _sequence_id="some sequence id",
            _template=self.template_vo,
            _library=self.library,
            _item_metadata=self.item_metadata,
        )
        self.otr.save(self.ot_ar)

        self.ot_ar = self.otr.find_by_uid(self.ot_ar.uid, for_update=True)
        self.ot_ar.approve(author_id="TEST")
        self.otr.save(self.ot_ar)

        self.ot_ar = self.otr.find_by_uid(self.ot_ar.uid, for_update=True)
        self.ot_ar.create_new_version(
            author_id="TEST", change_description="Change", template=self.template_vo
        )
        self.otr.save(self.ot_ar)

        self.ot_ar = self.otr.find_by_uid(self.ot_ar.uid, for_update=True)
        self.ntv = TemplateVO(
            name=self.changed_template_name,
            name_plain=self.changed_template_name_plain,
        )
        self.ot_ar.edit_draft(
            author_id="TEST", change_description="Change", template=self.ntv
        )
        self.ot_ar.approve(author_id="TEST")
        self.otr.save(self.ot_ar)

        self.et_ar = EndpointTemplateAR(
            _uid=self.etr.root_class.get_next_free_uid_and_increment_counter(),
            _sequence_id="some sequence id",
            _template=self.template_vo,
            _library=self.library,
            _item_metadata=self.item_metadata,
        )
        self.etr.save(self.et_ar)

        self.et_ar = self.etr.find_by_uid(self.et_ar.uid, for_update=True)
        self.et_ar.approve(author_id="TEST")
        self.etr.save(self.et_ar)

        self.et_ar = self.etr.find_by_uid(self.et_ar.uid, for_update=True)
        self.et_ar.create_new_version(
            author_id="TEST", change_description="Change", template=self.template_vo
        )
        self.et_ar.approve(author_id="TEST")
        self.etr.save(self.et_ar)

        self.tt_ar = TimeframeTemplateAR(
            _uid=self.ttr.root_class.get_next_free_uid_and_increment_counter(),
            _sequence_id="some sequence id",
            _template=self.template_vo,
            _library=self.library,
            _item_metadata=self.item_metadata,
        )
        self.ttr.save(self.tt_ar)

        self.tt_ar = self.ttr.find_by_uid(self.tt_ar.uid, for_update=True)
        self.tt_ar.approve(author_id="TEST")
        self.ttr.save(self.tt_ar)

        self.tt_ar = self.ttr.find_by_uid(self.tt_ar.uid, for_update=True)
        self.tt_ar.create_new_version(
            author_id="TEST", change_description="Change", template=self.template_vo
        )
        self.ttr.save(self.tt_ar)

        self.tt_ar.approve(author_id="TEST")
        self.ttr.save(self.tt_ar)

        self.create_template_parameters(count=14)
        self.create_objectives(count=10, approved=True)
        self.create_endpoints(count=10, approved=True)
        self.create_timeframes(count=10, approved=True)
        study_service = StudyObjectiveSelectionService()
        study_selection_objective_input = StudySelectionObjectiveInput(
            objective_uid="Objective_000010"
        )
        self.selection: StudySelectionObjective = study_service.make_selection(
            "study_root", study_selection_objective_input
        )

    def modify_endpoint_template(self):
        self.et_ar = self.etr.find_by_uid(self.et_ar.uid, for_update=True)
        self.et_ar.create_new_version(
            author_id="TEST", change_description="Change", template=self.ntv
        )
        self.etr.save(self.et_ar)

    def modify_timeframe_template(self):
        self.tt_ar = self.ttr.find_by_uid(self.tt_ar.uid, for_update=True)
        self.tt_ar.create_new_version(
            author_id="TEST", change_description="Change", template=self.ntv
        )
        self.ttr.save(self.tt_ar)

    def create_template_parameters(self, label=TPR_LABEL, count=10):
        self.term_roots = []
        self.term_values = []
        for i in range(count):
            template_parameter_term_root = TemplateParameterTermRoot(
                uid=label + "uid__" + str(i)
            )
            template_parameter_term_root.save()
            template_parameter_term_value = TemplateParameterTermValue(
                name=label + "__" + str(i)
            )
            template_parameter_term_value.save()
            template_parameter_term_root.has_parameter_term.connect(self.tpr)
            template_parameter_term_root.has_library.connect(self.lib)
            template_parameter_term_root.latest_final.connect(
                template_parameter_term_value
            )
        for template_parameter_term_root in self.tpr.has_parameter_term.all():
            self.term_roots.append(template_parameter_term_root)
            template_parameter_term_value = (
                template_parameter_term_root.latest_final.single()
            )
            self.term_values.append(template_parameter_term_value)

    def create_objectives(self, count=10, approved=False, retired=False):
        for i in range(count):
            template_parameter = TemplateParameterMultiSelectInput(
                template_parameter=self.TPR_LABEL,
                conjunction="",
                terms=[
                    {
                        "position": 1,
                        "index": 1,
                        "name": self.term_values[i].name,
                        "type": self.TPR_LABEL,
                        "uid": self.term_roots[i].uid,
                    }
                ],
            )
            template = ObjectiveCreateInput(
                objective_template_uid=self.ot_ar.uid,
                library_name="LibraryName",
                parameter_terms=[template_parameter],
            )

            print("CREATE", template_parameter)
            item = self.objective_service.create(template)
            if approved:
                self.objective_service.approve(item.uid)
            if retired:
                self.objective_service.inactivate_final(item.uid)

    def create_timeframes(self, count=10, approved=False, retired=False):
        for i in range(count):
            template_parameter = TemplateParameterMultiSelectInput(
                template_parameter=self.TPR_LABEL,
                conjunction="",
                terms=[
                    {
                        "position": 1,
                        "index": 1,
                        "name": self.term_values[i].name,
                        "type": self.TPR_LABEL,
                        "uid": self.term_roots[i].uid,
                    }
                ],
            )
            template = TimeframeCreateInput(
                timeframe_template_uid=self.tt_ar.uid,
                library_name="LibraryName",
                parameter_terms=[template_parameter],
            )

            item = self.timeframe_service.create(template)
            if approved:
                self.timeframe_service.approve(item.uid)
            if retired:
                self.timeframe_service.inactivate_final(item.uid)

    def create_endpoints(self, count=10, approved=False, retired=False):
        for i in range(count):
            template_parameter = TemplateParameterMultiSelectInput(
                template_parameter=self.TPR_LABEL,
                conjunction="",
                terms=[
                    {
                        "position": 1,
                        "index": 1,
                        "name": self.term_values[i].name,
                        "type": self.TPR_LABEL,
                        "uid": self.term_roots[i].uid,
                    }
                ],
            )
            template = EndpointCreateInput(
                endpoint_template_uid=self.et_ar.uid,
                library_name="LibraryName",
                parameter_terms=[template_parameter],
            )
            item = self.endpoint_service.create(template)
            if approved:
                self.endpoint_service.approve(item.uid)
            if retired:
                self.endpoint_service.inactivate_final(item.uid)

    def test__endpoint_upversion__update(self):
        # given

        endpoint_data = {
            "endpoint_level": None,
            "endpoint_uid": "Endpoint_000005",
            "endpoint_units": {"separator": "string", "units": ["unit 1", "unit 2"]},
            "study_objective_uid": self.selection.study_objective_uid,
            "timeframe_uid": "Timeframe_000005",
        }
        endpoint_service = StudyEndpointSelectionService()
        endpoint_selection_input: StudySelectionEndpointInput = (
            StudySelectionEndpointInput(**endpoint_data)
        )
        endpoint_selection: StudySelectionEndpoint = endpoint_service.make_selection(
            "study_root", endpoint_selection_input
        )

        self.assertIsNone(endpoint_selection.latest_timeframe)
        self.assertIsNone(endpoint_selection.latest_endpoint)

        self.modify_endpoint_template()
        self.endpoint_template_service.approve_cascade(self.et_ar.uid)

        selection: StudySelectionEndpoint = endpoint_service.get_specific_selection(
            study_uid="study_root",
            study_selection_uid=endpoint_selection.study_endpoint_uid,
        )

        self.assertNotEqual(
            selection.endpoint.version, selection.latest_endpoint.version
        )

        # when

        response = endpoint_service.update_selection_to_latest_version_of_endpoint(
            "study_root", selection.study_endpoint_uid
        )

        self.assertIsNone(response.latest_endpoint)
        # then
        selection = endpoint_service.get_specific_selection(
            study_uid="study_root", study_selection_uid=selection.study_endpoint_uid
        )
        self.assertIsNone(selection.latest_endpoint)
        self.assertIsNone(selection.latest_timeframe)

    def test__timeframe_upversion__update(self):
        # given
        endpoint_data = {
            "endpoint_level": None,
            "endpoint_uid": "Endpoint_000005",
            "endpoint_units": {"separator": "string", "units": ["unit 1", "unit 2"]},
            "study_objective_uid": self.selection.study_objective_uid,
            "timeframe_uid": "Timeframe_000005",
        }
        endpoint_service = StudyEndpointSelectionService()
        endpoint_selection_input: StudySelectionEndpointInput = (
            StudySelectionEndpointInput(**endpoint_data)
        )
        endpoint_selection: StudySelectionEndpoint = endpoint_service.make_selection(
            "study_root", endpoint_selection_input
        )

        self.assertIsNone(endpoint_selection.latest_timeframe)
        self.assertIsNone(endpoint_selection.latest_endpoint)
        self.modify_timeframe_template()
        self.timeframe_template_service.approve_cascade(self.tt_ar.uid)

        selection: StudySelectionEndpoint = endpoint_service.get_specific_selection(
            study_uid="study_root",
            study_selection_uid=endpoint_selection.study_endpoint_uid,
        )

        self.assertNotEqual(
            selection.timeframe.version, selection.latest_timeframe.version
        )

        # when
        response = endpoint_service.update_selection_to_latest_version_of_timeframe(
            "study_root", selection.study_endpoint_uid
        )

        self.assertIsNone(response.latest_timeframe)
        # then
        selection = endpoint_service.get_specific_selection(
            study_uid="study_root", study_selection_uid=selection.study_endpoint_uid
        )
        self.assertIsNone(selection.latest_timeframe)
        self.assertIsNone(selection.latest_endpoint)

    def test__timeframe_and_endpoint_upversion__update(self):
        # given
        endpoint_data = {
            "endpoint_level": None,
            "endpoint_uid": "Endpoint_000005",
            "endpoint_units": {"separator": "string", "units": ["unit 1", "unit 2"]},
            "study_objective_uid": self.selection.study_objective_uid,
            "timeframe_uid": "Timeframe_000005",
        }
        endpoint_service = StudyEndpointSelectionService()
        endpoint_selection_input: StudySelectionEndpointInput = (
            StudySelectionEndpointInput(**endpoint_data)
        )
        endpoint_selection: StudySelectionEndpoint = endpoint_service.make_selection(
            "study_root", endpoint_selection_input
        )

        self.assertIsNone(endpoint_selection.latest_timeframe)
        self.assertIsNone(endpoint_selection.latest_endpoint)
        self.modify_timeframe_template()
        self.timeframe_template_service.approve_cascade(self.tt_ar.uid)
        self.modify_endpoint_template()
        self.endpoint_template_service.approve_cascade(self.et_ar.uid)

        selection: StudySelectionEndpoint = endpoint_service.get_specific_selection(
            study_uid="study_root",
            study_selection_uid=endpoint_selection.study_endpoint_uid,
        )

        self.assertNotEqual(
            selection.timeframe.version, selection.latest_timeframe.version
        )
        self.assertNotEqual(
            selection.endpoint.version, selection.latest_endpoint.version
        )

        # when
        response = endpoint_service.update_selection_to_latest_version_of_timeframe(
            "study_root", selection.study_endpoint_uid
        )

        self.assertIsNone(response.latest_timeframe)
        # then
        selection = endpoint_service.get_specific_selection(
            study_uid="study_root", study_selection_uid=selection.study_endpoint_uid
        )
        self.assertIsNone(selection.latest_timeframe)
        self.assertIsNotNone(selection.latest_endpoint)
