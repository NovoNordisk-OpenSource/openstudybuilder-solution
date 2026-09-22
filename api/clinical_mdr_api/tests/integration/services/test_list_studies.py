import unittest

from neomodel import db

from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.domain_repositories.models.syntax import (
    EndpointRoot,
    EndpointValue,
    ObjectiveRoot,
    ObjectiveValue,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyActivityInstructionCreateInput,
    StudySelectionActivityCreateInput,
    StudySelectionCriteriaCreateInput,
)
from clinical_mdr_api.models.study_selections.study_soa_footnote import (
    StudySoAFootnoteCreateInput,
)
from clinical_mdr_api.models.syntax_instances.activity_instruction import (
    ActivityInstructionCreateInput,
)
from clinical_mdr_api.models.syntax_instances.criteria import CriteriaCreateInput
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_activity_instruction import (
    StudyActivityInstructionService,
)
from clinical_mdr_api.services.studies.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.studies.study_criteria_selection import (
    StudyCriteriaSelectionService,
)
from clinical_mdr_api.services.studies.study_soa_footnote import StudySoAFootnoteService
from clinical_mdr_api.services.syntax_instances.endpoints import EndpointService
from clinical_mdr_api.services.syntax_instances.objectives import ObjectiveService
from clinical_mdr_api.tests.integration.utils import data_library
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.utils import TestUtils


class TestListStudiesForObjectiveAndEndpoint(unittest.TestCase):
    TPR_LABEL = "ParameterName"

    def setUp(self):
        inject_and_clear_db("liststudiestest")
        db.cypher_query(data_library.STARTUP_STUDY_LIST_CYPHER)

        # Generate UIDs
        StudyRoot.generate_node_uids_if_not_present()
        ObjectiveRoot.generate_node_uids_if_not_present()
        EndpointRoot.generate_node_uids_if_not_present()

    def test__list_objectives_studies(self):
        objective_service: ObjectiveService = ObjectiveService()
        studies = objective_service.get_referencing_studies(
            "Objective_000001", node_type=ObjectiveValue
        )

        assert len(studies) == 1

    def test__list_endpoints_studies(self):
        endpoint_service: EndpointService = EndpointService()
        studies = endpoint_service.get_referencing_studies(
            "Endpoint_000001", node_type=EndpointValue
        )

        assert len(studies) == 1


class TestListStudies(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("liststudiestest2")
        db.cypher_query(data_library.STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(data_library.STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(data_library.STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(data_library.STARTUP_ACTIVITIES)

        db.cypher_query(data_library.STARTUP_CRITERIA)

        # Generate UIDs
        StudyRoot.generate_node_uids_if_not_present()
        ObjectiveRoot.generate_node_uids_if_not_present()
        EndpointRoot.generate_node_uids_if_not_present()

        _type_codelist = TestUtils.create_ct_codelist(
            name="Footnote Type",
            submission_value="FTNTTP",
            extensible=True,
            approve=True,
        )
        footnote = TestUtils.create_footnote()
        fl_grp_codelist = TestUtils.create_ct_codelist(
            name="Flowchart Group",
            submission_value="FLWCRTGRP",
            extensible=True,
            approve=True,
        )
        _efficacy_term = TestUtils.create_ct_term(
            sponsor_preferred_name="Efficacy",
            codelist_uid=fl_grp_codelist.codelist_uid,
            term_uid="term_efficacy_uid",
        )
        # Create a SoA Study Footnote
        StudySoAFootnoteService().create(
            "study_root",
            footnote_input=StudySoAFootnoteCreateInput(footnote_uid=footnote.uid),
            create_footnote=False,
        )

        # Create a study activity
        StudyActivitySelectionService().make_selection(
            "study_root",
            StudySelectionActivityCreateInput(
                soa_group_term_uid="term_efficacy_uid",
                activity_uid="activity_root1",
                activity_subgroup_uid="activity_subgroup_root1",
                activity_group_uid="activity_group_root1",
            ),
        )

        # Create a criteria template
        db.cypher_query("""
            MATCH (incl:CTTermRoot {uid: "C25532"})
            MATCH (library:Library {name: "Sponsor"})
            MERGE (incl)<-[:HAS_SELECTED_TERM]-(:CTTermContext)<-[:HAS_TYPE]-(ctr1:CriteriaTemplateRoot:SyntaxTemplateRoot:SyntaxIndexingTemplateRoot {uid: "incl_criteria_1"})
            -[relt:LATEST_FINAL]->(ctv1:CriteriaTemplateValue:SyntaxTemplateValue:SyntaxIndexingTemplateValue {name : "incl_criteria_1", name_plain : "incl_criteria_1"})
            MERGE (ctr1)-[:LATEST]->(ctv1)
            MERGE (ctr1)-[hv:HAS_VERSION]->(ctv1)
            set hv.change_description="Approved version"
            set hv.start_date= datetime()
            set hv.status = "Final"
            set hv.author_id = "unknown-user"
            set hv.version = "1.0"
            MERGE (library)-[:CONTAINS_SYNTAX_TEMPLATE]->(ctr1)
            """)

        # Create a study criteria
        StudyCriteriaSelectionService().make_selection_create_criteria(
            "study_root",
            StudySelectionCriteriaCreateInput(
                criteria_data=CriteriaCreateInput(
                    criteria_template_uid="incl_criteria_1",
                    library_name="Sponsor",
                    parameter_terms=[],
                )
            ),
        )

        # Create an Activity Instruction Template
        db.cypher_query("""
            MATCH (lib:Library {name: "Sponsor"})
            MERGE (adt:ActivityInstructionTemplateRoot:SyntaxTemplateRoot {uid: "ActivityInstructionTemplate_000001"})
            -[relt:LATEST_FINAL]->(adtv:ActivityInstructionTemplateValue:SyntaxTemplateValue
              {name : "activity_description_1", name_plain : "activity_description_1"})
            MERGE (lib)-[:CONTAINS_SYNTAX_TEMPLATE]->(adt)
            MERGE (adt)-[:LATEST]->(adtv)
            MERGE (adt)-[hv:HAS_VERSION]->(adtv)
            set hv.change_description="Approved version"
            set hv.start_date= datetime()
            set hv.status = "Final"
            set hv.author_id = "unknown-user"
            set hv.version = "1.0"
            """)

        # Create a study activity instruction
        StudyActivityInstructionService().create(
            "study_root",
            StudyActivityInstructionCreateInput(
                activity_instruction_data=ActivityInstructionCreateInput(
                    activity_instruction_template_uid="ActivityInstructionTemplate_000001",
                    parameter_terms=[],
                    library_name="Sponsor",
                ),
                study_activity_uid="StudyActivity_000001",
            ),
        )

        # Let's create an empty study
        db.cypher_query("""
            MERGE (sr:StudyRoot {uid: "study_root2"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id2", study_number:"1"})
            MERGE (sr)-[hv:HAS_VERSION]->(sv)
            MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
            set hv.status = "DRAFT"
            set hv.start_date = datetime()
            set hv.author_id = "AZNG"
            set ld.status = "DRAFT"
            set ld.start_date = datetime()
            set ld.author_id = "AZNG"
            WITH sv
            MATCH (p:Project {uid: "Project_000001"})
            MERGE (p)-[:HAS_FIELD]->(sf:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
            """)

        self.study_service = StudyService()

    def test_filter_by_study_footnote(self):
        result = self.study_service.get_all(has_study_footnote=True)
        self.assertEqual(len(result.items), 1)

    def test_filter_by_study_objective(self):
        result = self.study_service.get_all(has_study_objective=True)
        self.assertEqual(len(result.items), 1)

    def test_filter_by_study_endpoint(self):
        result = self.study_service.get_all(has_study_endpoint=True)
        self.assertEqual(len(result.items), 1)

    def test_filter_by_study_activity(self):
        result = self.study_service.get_all(has_study_activity=True)
        self.assertEqual(len(result.items), 1)

    def test_filter_by_study_criteria(self):
        result = self.study_service.get_all(has_study_criteria=True)
        self.assertEqual(len(result.items), 1)

    def test_filter_by_study_activity_instruction(self):
        result = self.study_service.get_all(has_study_activity_instruction=True)
        self.assertEqual(len(result.items), 1)
