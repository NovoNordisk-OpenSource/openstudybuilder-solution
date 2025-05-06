import unittest

from neomodel import db

from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.models.study_selections.study_disease_milestone import (
    StudyDiseaseMilestone,
    StudyDiseaseMilestoneCreateInput,
    StudyDiseaseMilestoneEditInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services.studies.study_disease_milestone import (
    StudyDiseaseMilestoneService,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    fix_study_preferred_time_unit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_study_disease_milestone,
    create_study_disease_milestone_codelists_ret_cat_and_lib,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from common import exceptions
from common.config import SDTM_CT_CATALOGUE_NAME


class TestStudyDiseaseMilestoneManagement(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("studiesdiseasemilestonestest")
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)

        # Generate UIDs
        StudyRoot.generate_node_uids_if_not_present()
        self.study = StudyRoot.nodes.all()[0]
        TestUtils.create_ct_catalogue(catalogue_name=SDTM_CT_CATALOGUE_NAME)
        TestUtils.set_study_standard_version(
            study_uid=self.study.uid, create_codelists_and_terms_for_package=False
        )

        create_study_disease_milestone_codelists_ret_cat_and_lib()

        fix_study_preferred_time_unit("study_root")

    def test__list_disease_milestone_studies(self):
        disease_milestone_service = StudyDiseaseMilestoneService()
        disease_milestones = disease_milestone_service.get_all_disease_milestones(
            self.study.uid
        ).items

        assert len(disease_milestones) == 0

    def test__create_study_disease_milestone(self):
        disease_milestone_service = StudyDiseaseMilestoneService()
        study_disease_milestone_create_input = StudyDiseaseMilestoneCreateInput(
            study_uid="study_root",
            description="test_description",
            disease_milestone_type="Disease_Milestone_Type_0001",
            order="1",
            repetition_indicator=True,
        )
        StudyDiseaseMilestoneService().create(
            "study_root",
            study_disease_milestone_input=study_disease_milestone_create_input,
        )
        disease_milestones = disease_milestone_service.get_all_disease_milestones(
            self.study.uid
        ).items

        assert len(disease_milestones) == 1

    def test__reorder_disease_milestones(self):
        disease_milestone_service = StudyDiseaseMilestoneService()
        dm1: StudyDiseaseMilestone = create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0001"
        )
        dm2 = create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0002"
        )
        dm3 = create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0003"
        )

        dm1 = disease_milestone_service.find_by_uid(dm1.uid)
        dm2 = disease_milestone_service.find_by_uid(dm2.uid)
        dm3 = disease_milestone_service.find_by_uid(dm3.uid)

        self.assertEqual(dm1.order, 1)
        self.assertEqual(dm2.order, 2)
        self.assertEqual(dm3.order, 3)

        with self.assertRaises(exceptions.BusinessLogicException):
            disease_milestone_service.reorder(dm3.uid, 0)

        with self.assertRaises(exceptions.BusinessLogicException):
            disease_milestone_service.reorder(dm3.uid, 4)

        disease_milestone_service.reorder(dm3.uid, 1)

        dm_after1 = disease_milestone_service.find_by_uid(dm1.uid)
        dm_after2 = disease_milestone_service.find_by_uid(dm2.uid)
        dm_after3 = disease_milestone_service.find_by_uid(dm3.uid)

        self.assertEqual(dm_after1.order, 2)
        self.assertEqual(dm_after2.order, 3)
        self.assertEqual(dm_after3.order, 1)

        disease_milestone_service.reorder(dm1.uid, 3)

        dm_after1 = disease_milestone_service.find_by_uid(dm1.uid)
        dm_after2 = disease_milestone_service.find_by_uid(dm2.uid)
        dm_after3 = disease_milestone_service.find_by_uid(dm3.uid)

        self.assertEqual(dm_after1.order, 3)
        self.assertEqual(dm_after2.order, 2)
        self.assertEqual(dm_after3.order, 1)

        disease_milestone_subtype_2 = create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0004"
        )
        disease_milestone_subtype_3 = create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0005"
        )
        dm4 = disease_milestone_service.find_by_uid(disease_milestone_subtype_2.uid)
        self.assertEqual(dm4.order, 4)
        dm5 = disease_milestone_service.find_by_uid(disease_milestone_subtype_3.uid)
        self.assertEqual(dm5.order, 5)
        disease_milestone_service.reorder(dm5.uid, 4)
        dm4 = disease_milestone_service.find_by_uid(disease_milestone_subtype_2.uid)
        self.assertEqual(dm4.order, 5)
        dm5 = disease_milestone_service.find_by_uid(disease_milestone_subtype_3.uid)
        self.assertEqual(dm5.order, 4)

        header = disease_milestone_service.get_distinct_values_for_header(
            field_name="disease_milestone_type",
            search_string="",
            filter_by="",
            filter_operator=FilterOperator.from_str("and"),
            page_size=10,
        )
        self.assertEqual(header[-1], "Disease_Milestone_Type_0005")

    def test__create_study_disease_milestone_with_not_unique_disease_milestone_type(
        self,
    ):
        disease_milestone_service = StudyDiseaseMilestoneService()
        create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0001"
        )
        disease_milestones = disease_milestone_service.get_all_disease_milestones(
            self.study.uid
        ).items
        self.assertEqual(len(disease_milestones), 1)

        study_disease_milestone_create_input = StudyDiseaseMilestoneCreateInput(
            study_uid="study_root",
            description="test_description",
            disease_milestone_type="Disease_Milestone_Type_0002",
            order="1",
            repetition_indicator=True,
        )
        StudyDiseaseMilestoneService().create(
            "study_root",
            study_disease_milestone_input=study_disease_milestone_create_input,
        )
        create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0003"
        )
        create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0004"
        )

        disease_milestones = disease_milestone_service.get_all_disease_milestones(
            self.study.uid
        ).items
        self.assertEqual(len(disease_milestones), 4)
        self.assertEqual(disease_milestones[0].uid, "StudyDiseaseMilestone_000001")

    def test__edit_disease_milestone(self):
        disease_milestone: StudyDiseaseMilestone = create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0002"
        )

        disease_milestone_service = StudyDiseaseMilestoneService()

        disease_milestone = disease_milestone_service.find_by_uid(disease_milestone.uid)
        disease_milestone_type = "Disease_Milestone_Type_0003"
        repetition_indicator = False
        edit_input = StudyDiseaseMilestoneEditInput(
            study_uid=disease_milestone.study_uid,
            disease_milestone_type=disease_milestone_type,
            change_description="rules change",
            repetition_indicator=repetition_indicator,
        )
        # locking and unlocking to create multiple study value relationships on the existent StudySelections
        TestUtils.create_study_fields_configuration()
        TestUtils.lock_and_unlock_study(study_uid="study_root")
        edited_disease_milestone = disease_milestone_service.edit(
            study_disease_milestone_uid=disease_milestone.uid,
            study_disease_milestone_input=edit_input,
        )
        edited_disease_milestone = disease_milestone_service.find_by_uid(
            edited_disease_milestone.uid
        )
        self.assertEqual(
            edited_disease_milestone.disease_milestone_type,
            disease_milestone_type,
        )
        self.assertEqual(
            edited_disease_milestone.repetition_indicator, repetition_indicator
        )
        self.assertEqual(edited_disease_milestone.order, disease_milestone.order)
        self.assertEqual(edited_disease_milestone.uid, disease_milestone.uid)

    def test__get_versions(self):
        disease_milestone: StudyDiseaseMilestone = create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0001"
        )
        disease_milestone_service = StudyDiseaseMilestoneService()
        disease_milestone = disease_milestone_service.find_by_uid(disease_milestone.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyDiseaseMilestoneEditInput(
            study_uid=disease_milestone.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change and type",
            disease_milestone_type="Disease_Milestone_Type_0002",
        )
        disease_milestone_service.edit(
            study_disease_milestone_uid=disease_milestone.uid,
            study_disease_milestone_input=edit_input,
        )
        disease_milestone_versions = disease_milestone_service.audit_trail(
            disease_milestone_uid=disease_milestone.uid,
            study_uid=disease_milestone.study_uid,
        )
        previous_disease_milestone = disease_milestone_versions[1]
        self.assertEqual(previous_disease_milestone.changes, [])

        # test all versions
        disease_milestone: StudyDiseaseMilestone = create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0003"
        )
        disease_milestone_service = StudyDiseaseMilestoneService()
        disease_milestone = disease_milestone_service.find_by_uid(disease_milestone.uid)
        edit_input = StudyDiseaseMilestoneEditInput(
            study_uid=disease_milestone.study_uid,
            change_description="rules change",
        )
        disease_milestone_service.edit(
            study_disease_milestone_uid=disease_milestone.uid,
            study_disease_milestone_input=edit_input,
        )
        disease_milestone_versions = (
            disease_milestone_service.audit_trail_all_disease_milestones(
                study_uid=disease_milestone.study_uid,
            )
        )

        previous_disease_milestone = disease_milestone_versions[1]
        previous_disease_milestone_2 = disease_milestone_versions[3]
        self.assertEqual(previous_disease_milestone.changes, [])
        self.assertEqual(previous_disease_milestone_2.changes, [])

    def test__delete_study_disease_milestone(self):
        disease_milestone_service = StudyDiseaseMilestoneService()

        create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0001"
        )
        disease_milestones = disease_milestone_service.get_all_disease_milestones(
            self.study.uid
        ).items
        self.assertEqual(len(disease_milestones), 1)
        self.assertEqual(disease_milestones[0].order, 1)
        disease_milestone1 = create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0002"
        )
        disease_milestone2 = create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0003"
        )
        disease_milestone3 = create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0004"
        )

        dm1 = disease_milestone_service.find_by_uid(disease_milestone1.uid)
        dm2 = disease_milestone_service.find_by_uid(disease_milestone2.uid)
        dm3 = disease_milestone_service.find_by_uid(disease_milestone3.uid)

        self.assertEqual(dm1.order, 2)
        self.assertEqual(dm2.order, 3)
        self.assertEqual(dm3.order, 4)

        # locking and unlocking to create multiple study value relationships on the existent StudySelections
        TestUtils.create_study_fields_configuration()
        TestUtils.lock_and_unlock_study(study_uid="study_root")

        disease_milestone_service.delete(study_disease_milestone_uid=dm1.uid)

        dm1 = disease_milestone_service.find_by_uid(disease_milestone2.uid)
        dm2 = disease_milestone_service.find_by_uid(disease_milestone3.uid)

        self.assertEqual(dm1.order, 2)
        self.assertEqual(dm2.order, 3)

        disease_milestone_service.delete(study_disease_milestone_uid=dm1.uid)
        dm1 = disease_milestone_service.find_by_uid(dm2.uid)
        self.assertEqual(dm1.order, 2)

        disease_milestone_recreate = create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0002"
        )
        dm_recreate = disease_milestone_service.find_by_uid(
            disease_milestone_recreate.uid
        )
        self.assertEqual(dm_recreate.order, 3)

    def test__duplicated_supplemental_disease_milestone_created__value_error_is_raised(
        self,
    ):
        create_study_disease_milestone(
            disease_milestone_type="Disease_Milestone_Type_0001"
        )

        with self.assertRaises(exceptions.BusinessLogicException):
            create_study_disease_milestone(
                disease_milestone_type="Disease_Milestone_Type_0001"
            )


class TestDiseaseMilestoneService(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("studiesdiseasemilestonestestnewtesting")
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)

        # Generate UIDs
        StudyRoot.generate_node_uids_if_not_present()
        self.study = StudyRoot.nodes.all()[0]
        create_study_disease_milestone_codelists_ret_cat_and_lib()

        super().setUp()

    def test_filtering_exact(self):
        disease_milestone_type = "Disease_Milestone_Type_0001"
        TestUtils.create_disease_milestone(
            study_uid="study_root",
            disease_milestone_type=disease_milestone_type,
            repetition_indicator=True,
        )

        service = StudyDiseaseMilestoneService()
        results: GenericFilteringReturn = service.get_all_disease_milestones(
            study_uid=self.study.uid,
            sort_by={"order": True},
            page_size=1,
            filter_by={"disease_milestone_type": {"v": [disease_milestone_type]}},
            page_number=1,
            filter_operator=FilterOperator.from_str("and"),
            total_count=True,
        )

        if results:
            assert len(results.items) > 0
