import unittest

from neomodel import db

from clinical_mdr_api.domains.study_selections.study_epoch import (
    StudyEpochVO,
    TimelineAR,
)
from clinical_mdr_api.domains.study_selections.study_visit import StudyVisitVO
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpochEditInput
from clinical_mdr_api.models.study_selections.study_visit import (
    StudyVisit,
    StudyVisitCreateInput,
    StudyVisitEditInput,
)
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.services.studies.study_visit import StudyVisitService
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    fix_study_preferred_time_unit,
)
from clinical_mdr_api.tests.integration.utils.factory_activity import (
    create_study_activity,
)
from clinical_mdr_api.tests.integration.utils.factory_visit import (
    generate_default_input_data_for_visit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_library_data,
    create_study_epoch,
    create_study_visit_codelists,
    create_visit_with_update,
    generate_study_root,
    get_unit_uid_by_name,
    preview_visit_with_update,
    update_visit_with_update,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from common.config import NON_VISIT_NUMBER, SDTM_CT_CATALOGUE_NAME
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    NotFoundException,
    ValidationException,
    VisitsAreNotEqualException,
)


class TestStudyVisitManagement(unittest.TestCase):
    TPR_LABEL = "ParameterName"

    def setUp(self):
        inject_and_clear_db("studiesvisitstest")
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)

        create_library_data()

        self.study = generate_study_root()
        TestUtils.create_ct_catalogue(catalogue_name=SDTM_CT_CATALOGUE_NAME)
        TestUtils.set_study_standard_version(
            study_uid=self.study.uid, create_codelists_and_terms_for_package=False
        )
        create_study_visit_codelists()
        TestUtils.create_study_fields_configuration()

        self.epoch1 = create_study_epoch("EpochSubType_0001")
        self.epoch2 = create_study_epoch("EpochSubType_0002")
        self.epoch3 = create_study_epoch("EpochSubType_0003")
        self.day_uid = get_unit_uid_by_name("day")
        self.flowchart_group_codelist = TestUtils.create_ct_codelist(
            sponsor_preferred_name="Flowchart Group",
            extensible=True,
            approve=True,
            catalogue_name="catalogue",
            library_name="Sponsor",
        )
        self.flowchart_group = TestUtils.create_ct_term(
            sponsor_preferred_name="Subject Information",
            codelist_uid=self.flowchart_group_codelist.codelist_uid,
            catalogue_name="catalogue",
            library_name="Sponsor",
        )
        fix_study_preferred_time_unit(self.study.uid)

    def test__list__visits_studies(self):
        inputs = {
            "study_epoch_uid": self.epoch1.uid,
            "visit_type_uid": "VisitType_0001",
            "time_reference_uid": "VisitSubType_0005",
            "time_value": 0,
            "time_unit_uid": self.day_uid,
            "is_global_anchor_visit": True,
            "visit_class": "SINGLE_VISIT",
            "visit_subclass": "SINGLE_VISIT",
        }
        preview = preview_visit_with_update(self.study.uid, **inputs)
        print("PREVIEW", preview)
        self.assertEqual(preview.order, 1)
        self.assertEqual(preview.visit_number, 1)
        self.assertEqual(preview.unique_visit_number, 100)
        self.assertEqual(preview.study_duration_weeks_label, "0 weeks")
        self.assertEqual(preview.week_in_study_label, "Week 0")

        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0005",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=True,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0003",
            time_reference_uid="VisitSubType_0005",
            time_value=12,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0003",
            time_reference_uid="VisitSubType_0005",
            time_value=10,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        inputs = {
            "study_epoch_uid": self.epoch1.uid,
            "visit_type_uid": "VisitType_0004",
            "time_reference_uid": "VisitSubType_0005",
            "time_value": 20,
            "time_unit_uid": self.day_uid,
            "is_global_anchor_visit": False,
            "visit_class": "SINGLE_VISIT",
            "visit_subclass": "SINGLE_VISIT",
        }
        preview = preview_visit_with_update(self.study.uid, **inputs)
        print("PREVIEW", preview)
        self.assertEqual(preview.order, 4)
        self.assertEqual(preview.visit_number, 4)
        self.assertEqual(preview.unique_visit_number, 400)
        self.assertEqual(preview.study_duration_weeks_label, "2 weeks")
        self.assertEqual(preview.week_in_study_label, "Week 2")

        version3 = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0004",
            time_reference_uid="VisitSubType_0005",
            time_value=20,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        self.assertEqual(version3.unique_visit_number, preview.unique_visit_number)
        self.assertEqual(version3.study_duration_weeks_label, "2 weeks")
        self.assertEqual(version3.week_in_study_label, "Week 2")
        version4 = create_visit_with_update(
            study_epoch_uid=self.epoch2.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=30,
            time_unit_uid=self.day_uid,
            visit_sublabel_reference=None,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="ANCHOR_VISIT_IN_GROUP_OF_SUBV",
        )
        version5 = create_visit_with_update(
            study_epoch_uid=self.epoch2.uid,
            visit_type_uid="VisitType_0003",
            time_reference_uid="VisitSubType_0002",
            time_value=31,
            time_unit_uid=self.day_uid,
            visit_sublabel_reference=version4.uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV",
        )
        visit_service: StudyVisitService = StudyVisitService(study_uid=self.study.uid)
        visits = visit_service.get_all_visits(self.study.uid)
        self.assertEqual(len(visits.items), 6)

        v3new: StudyVisit = visit_service.find_by_uid(
            study_uid=self.study.uid, uid=version3.uid
        )
        self.assertEqual(v3new.order, 4)
        self.assertEqual(v3new.visit_number, 4)
        self.assertEqual(v3new.unique_visit_number, 400)

        self.assertEqual(v3new.study_day_number, 21)
        self.assertEqual(v3new.min_visit_window_value, -1)
        self.assertEqual(v3new.max_visit_window_value, 1)

        self.assertEqual(v3new.study_duration_weeks_label, "2 weeks")
        self.assertEqual(v3new.week_in_study_label, "Week 2")

        v5new: StudyVisit = visit_service.find_by_uid(
            study_uid=self.study.uid, uid=version4.uid
        )
        self.assertEqual(v5new.order, 5)
        self.assertEqual(v5new.visit_number, 5)
        print("V%sub", v5new)
        self.assertEqual(v5new.unique_visit_number, 500)

        self.assertEqual(v5new.study_duration_weeks_label, "4 weeks")
        self.assertEqual(v5new.week_in_study_label, "Week 4")

        v6new: StudyVisit = visit_service.find_by_uid(
            study_uid=self.study.uid, uid=version5.uid
        )
        self.assertEqual(v6new.order, 6)
        self.assertEqual(v5new.visit_number, 5)
        print("V%sub", v6new)
        self.assertEqual(v6new.unique_visit_number, 510)

        references = visit_service.get_all_references(self.study.uid)
        self.assertEqual(len(references), 2)
        visit: StudyVisit = references[0]
        self.assertEqual(visit.visit_type.sponsor_preferred_name, "BASELINE")
        self.assertEqual(visit.study_duration_weeks_label, "0 weeks")
        self.assertEqual(visit.week_in_study_label, "Week 0")

        visit: StudyVisit = references[1]
        self.assertEqual(visit.visit_type.sponsor_preferred_name, "BASELINE2")
        self.assertEqual(visit.study_duration_weeks_label, "4 weeks")
        self.assertEqual(visit.week_in_study_label, "Week 4")

        inputs = {
            "study_epoch_uid": self.epoch2.uid,
            "visit_type_uid": "VisitType_0003",
            "time_reference_uid": "VisitSubType_0002",
            "time_value": 40,
            "time_unit_uid": self.day_uid,
            "visit_sublabel_reference": version4.uid,
            "is_global_anchor_visit": False,
            "visit_class": "SINGLE_VISIT",
            "visit_subclass": "ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV",
        }
        preview = preview_visit_with_update(self.study.uid, **inputs)
        print("PREVIEW", preview)
        self.assertEqual(preview.unique_visit_number, 520)
        self.assertEqual(preview.study_duration_weeks_label, "10 weeks")
        self.assertEqual(preview.week_in_study_label, "Week 10")

        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch1 = epochs[0]
        epoch2 = epochs[1]
        study_epochs = epoch_service.repo.find_all_epochs_by_study(self.study.uid)

        epoch = epoch_service.find_by_uid(epoch1.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )

        visit_repo = epoch_service._repos.study_visit_repository
        study_visits = visit_repo.find_all_visits_by_study_uid(self.study.uid)
        self.assertEqual(len(study_visits), 6)
        timeline = TimelineAR(self.study.uid, _visits=study_visits)
        epochs = timeline.collect_visits_to_epochs(study_epochs)
        visit_vo: StudyVisitVO
        epoch_vo: StudyEpochVO
        for visit_vo in timeline.ordered_study_visits:
            print(
                "VIS",
                visit_vo.uid,
                visit_vo.study_day_number,
                visit_vo.get_unified_window(),
            )
            self.assertEqual(
                visit_vo.get_unified_window(),
                (visit_vo.study_day_number - 1, visit_vo.study_day_number + 1),
            )

        for study_visit in study_visits:
            if study_visit.uid == version3.uid:
                visit3_vo: StudyVisitVO = study_visit
                self.assertEqual(visit3_vo.study_day_number, 21)
                self.assertEqual(visit3_vo.study_week_number, 3)
        for epoch_vo in study_epochs:
            print(
                "EPOCH", epoch_vo.uid, epoch_vo.get_start_day(), epoch_vo.get_end_day()
            )
        print("EPOCH 1", epoch1)
        print("EPOCH 2", epoch2)
        self.assertEqual(epoch1.start_day, 1)
        self.assertEqual(epoch1.end_day, 31)
        self.assertEqual(epoch2.start_day, epoch1.end_day)
        self.assertEqual(epoch2.end_day, 62)

        v3update = update_visit_with_update(
            v3new.uid,
            uid=v3new.uid,
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0004",
            time_reference_uid="VisitSubType_0001",
            time_value=25,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        self.assertEqual(v3update.study_day_number, 26)

    def test__create__props_are_correctly_saved(self):
        visit_service = StudyVisitService(study_uid=self.study.uid)

        input_values = {
            "study_epoch_uid": self.epoch1.uid,
            "visit_type_uid": "VisitType_0001",
            "time_reference_uid": "VisitSubType_0001",
            "time_value": 0,
            "time_unit_uid": self.day_uid,
            "visit_contact_mode_uid": "VisitContactMode_0002",
            "max_visit_window_value": 10,
            "min_visit_window_value": 0,
            "show_visit": True,
            "is_global_anchor_visit": False,
            "visit_class": "SINGLE_VISIT",
            "visit_subclass": "SINGLE_VISIT",
            "epoch_allocation_uid": "EpochAllocation_0002",
        }
        visit = create_visit_with_update(**input_values)
        visit_after_create = visit_service.find_by_uid(
            study_uid=self.study.uid, uid=visit.uid
        )
        self.assertEqual(
            visit_after_create.visit_contact_mode_uid,
            input_values["visit_contact_mode_uid"],
        )
        self.assertEqual(
            visit_after_create.max_visit_window_value,
            input_values["max_visit_window_value"],
        )
        self.assertEqual(
            visit_after_create.min_visit_window_value,
            input_values["min_visit_window_value"],
        )
        self.assertEqual(
            visit_after_create.time_unit_uid, input_values["time_unit_uid"]
        )
        self.assertEqual(visit_after_create.time_value, input_values["time_value"])
        self.assertEqual(visit_after_create.show_visit, input_values["show_visit"])
        self.assertEqual(
            visit_after_create.time_reference_uid, input_values["time_reference_uid"]
        )
        self.assertEqual(
            visit_after_create.visit_type_uid, input_values["visit_type_uid"]
        )
        self.assertEqual(
            visit_after_create.epoch_allocation_uid,
            input_values["epoch_allocation_uid"],
        )
        self.assertEqual(visit_after_create.study_duration_weeks_label, "0 weeks")
        self.assertEqual(visit_after_create.week_in_study_label, "Week 0")

    def test__edit_visit_successfully_handled(self):
        visit_service = StudyVisitService(study_uid=self.study.uid)
        visit = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0005",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=True,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
            epoch_allocation_uid="EpochAllocation_0001",
        )
        self.assertEqual(
            visit.is_soa_milestone,
            False,
        )
        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch1 = epochs[0]

        epoch = epoch_service.find_by_uid(epoch1.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        # locking and unlocking to create multiple study value relationships on the existent StudySelections
        TestUtils.create_study_fields_configuration()
        TestUtils.lock_and_unlock_study(study_uid=self.study.uid)

        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )

        edit_input = {
            "uid": visit.uid,
            "study_epoch_uid": visit.study_epoch_uid,
            "visit_type_uid": "VisitType_0001",
            "time_reference_uid": "VisitSubType_0005",
            "time_value": 7,
            "time_unit_uid": self.day_uid,
            "visit_contact_mode_uid": "VisitContactMode_0002",
            "max_visit_window_value": 10,
            "min_visit_window_value": 0,
            "visit_window_unit_uid": visit.visit_window_unit_uid,
            "show_visit": True,
            "is_global_anchor_visit": False,
            "is_soa_milestone": True,
            "visit_class": "SINGLE_VISIT",
            "visit_subclass": "SINGLE_VISIT",
            "epoch_allocation_uid": "EpochAllocation_0002",
        }
        visit_service.edit(
            study_uid=visit.study_uid,
            study_visit_uid=visit.uid,
            study_visit_input=StudyVisitEditInput(**edit_input),
        )
        visit_after_update = visit_service.find_by_uid(
            study_uid=self.study.uid, uid=visit.uid
        )
        self.assertEqual(
            visit_after_update.is_soa_milestone,
            True,
        )
        self.assertEqual(
            visit_after_update.visit_contact_mode_uid,
            edit_input["visit_contact_mode_uid"],
        )
        self.assertEqual(
            visit_after_update.max_visit_window_value,
            edit_input["max_visit_window_value"],
        )
        self.assertEqual(
            visit_after_update.min_visit_window_value,
            edit_input["min_visit_window_value"],
        )
        self.assertEqual(visit_after_update.time_unit_uid, edit_input["time_unit_uid"])
        self.assertEqual(visit_after_update.time_value, edit_input["time_value"])
        self.assertEqual(visit_after_update.show_visit, edit_input["show_visit"])
        self.assertEqual(
            visit_after_update.time_reference_uid, edit_input["time_reference_uid"]
        )
        self.assertEqual(
            visit_after_update.visit_type_uid, edit_input["visit_type_uid"]
        )
        self.assertEqual(
            visit_after_update.epoch_allocation_uid, edit_input["epoch_allocation_uid"]
        )
        self.assertEqual(visit_after_update.study_duration_weeks_label, "1 weeks")
        self.assertEqual(visit_after_update.week_in_study_label, "Week 1")

    def test__version_visits(self):
        visit_service = StudyVisitService(study_uid=self.study.uid)
        first_visit = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0005",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=True,
            is_soa_milestone=True,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
            epoch_allocation_uid="EpochAllocation_0001",
        )
        self.assertEqual(first_visit.is_soa_milestone, True)

        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch1 = epochs[0]

        epoch = epoch_service.find_by_uid(epoch1.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )

        edit_input = {
            "uid": first_visit.uid,
            "study_epoch_uid": first_visit.study_epoch_uid,
            "visit_type_uid": "VisitType_0001",
            "time_reference_uid": "VisitSubType_0005",
            "time_value": 7,
            "time_unit_uid": self.day_uid,
            "visit_contact_mode_uid": "VisitContactMode_0002",
            "max_visit_window_value": 10,
            "min_visit_window_value": 0,
            "visit_window_unit_uid": first_visit.visit_window_unit_uid,
            "show_visit": True,
            "is_global_anchor_visit": False,
            "is_soa_milestone": False,
            "visit_class": "SINGLE_VISIT",
            "visit_subclass": "SINGLE_VISIT",
            "epoch_allocation_uid": "EpochAllocation_0002",
        }
        visit_service.edit(
            study_uid=first_visit.study_uid,
            study_visit_uid=first_visit.uid,
            study_visit_input=StudyVisitEditInput(**edit_input),
        )
        visit_after_update = visit_service.find_by_uid(
            study_uid=self.study.uid, uid=first_visit.uid
        )

        self.assertEqual(visit_after_update.is_soa_milestone, False)
        self.assertEqual(
            visit_after_update.visit_contact_mode_uid,
            edit_input["visit_contact_mode_uid"],
        )
        self.assertEqual(
            visit_after_update.max_visit_window_value,
            edit_input["max_visit_window_value"],
        )
        self.assertEqual(
            visit_after_update.min_visit_window_value,
            edit_input["min_visit_window_value"],
        )
        self.assertEqual(visit_after_update.time_unit_uid, edit_input["time_unit_uid"])
        self.assertEqual(visit_after_update.time_value, edit_input["time_value"])
        self.assertEqual(visit_after_update.show_visit, edit_input["show_visit"])
        self.assertEqual(
            visit_after_update.time_reference_uid, edit_input["time_reference_uid"]
        )
        self.assertEqual(
            visit_after_update.visit_type_uid, edit_input["visit_type_uid"]
        )
        self.assertEqual(
            visit_after_update.epoch_allocation_uid, edit_input["epoch_allocation_uid"]
        )
        self.assertEqual(visit_after_update.study_duration_weeks_label, "1 weeks")
        self.assertEqual(visit_after_update.week_in_study_label, "Week 1")

        # Verify specific StudyVisit audit-trail
        visits_versions = visit_service.audit_trail(
            visit_uid=first_visit.uid,
            study_uid=first_visit.study_uid,
        )
        first_visit_after_edit = visits_versions[0]
        first_visit_after_create = visits_versions[1]
        self.assertEqual(first_visit_after_edit.uid, first_visit.uid)
        self.assertEqual(
            first_visit_after_edit.visit_contact_mode_uid,
            edit_input["visit_contact_mode_uid"],
        )
        self.assertEqual(
            first_visit_after_edit.max_visit_window_value,
            edit_input["max_visit_window_value"],
        )
        self.assertEqual(
            first_visit_after_edit.min_visit_window_value,
            edit_input["min_visit_window_value"],
        )
        self.assertEqual(first_visit_after_edit.time_value, edit_input["time_value"])

        self.assertEqual(
            first_visit_after_edit.epoch_allocation_uid,
            edit_input["epoch_allocation_uid"],
        )
        self.assertGreater(
            first_visit_after_edit.start_date, first_visit_after_create.start_date
        )
        self.assertEqual(first_visit_after_edit.study_duration_weeks_label, "1 weeks")
        self.assertEqual(first_visit_after_edit.week_in_study_label, "Week 1")
        self.assertEqual(first_visit_after_edit.change_type, "Edit")
        self.assertEqual(
            first_visit_after_create.end_date, first_visit_after_edit.start_date
        )
        self.assertEqual(first_visit_after_create.change_type, "Create")
        self.assertEqual(first_visit_after_create.changes, {})
        self.assertEqual(first_visit_after_create.study_duration_weeks_label, "0 weeks")
        self.assertEqual(first_visit_after_create.week_in_study_label, "Week 0")

        time_value = 30
        second_visit = create_visit_with_update(
            study_epoch_uid=self.epoch2.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=time_value,
            time_unit_uid=self.day_uid,
            visit_sublabel_reference=None,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="ANCHOR_VISIT_IN_GROUP_OF_SUBV",
        )
        # Verify all StudyVisits in a Study audit-trail
        all_visits_versions = visit_service.audit_trail_all_visits(
            study_uid=first_visit.study_uid,
        )

        first_visit_after_edit = all_visits_versions[0]
        first_visit_after_create = all_visits_versions[1]
        second_visit_history = all_visits_versions[2]
        self.assertEqual(first_visit_after_edit.uid, first_visit.uid)
        self.assertEqual(
            first_visit_after_edit.visit_contact_mode_uid,
            edit_input["visit_contact_mode_uid"],
        )
        self.assertEqual(
            first_visit_after_edit.max_visit_window_value,
            edit_input["max_visit_window_value"],
        )
        self.assertEqual(
            first_visit_after_edit.min_visit_window_value,
            edit_input["min_visit_window_value"],
        )
        self.assertEqual(
            first_visit_after_edit.time_unit_uid, edit_input["time_unit_uid"]
        )
        self.assertEqual(first_visit_after_edit.time_value, edit_input["time_value"])
        self.assertEqual(first_visit_after_edit.show_visit, edit_input["show_visit"])
        self.assertEqual(
            first_visit_after_edit.time_reference_uid, edit_input["time_reference_uid"]
        )
        self.assertEqual(
            first_visit_after_edit.visit_type_uid, edit_input["visit_type_uid"]
        )
        self.assertEqual(
            first_visit_after_edit.epoch_allocation_uid,
            edit_input["epoch_allocation_uid"],
        )
        self.assertEqual(first_visit_after_edit.uid, first_visit_after_create.uid)
        self.assertGreater(
            first_visit_after_edit.start_date, first_visit_after_create.start_date
        )
        self.assertEqual(
            first_visit_after_create.end_date, first_visit_after_edit.start_date
        )
        self.assertEqual(first_visit_after_edit.study_duration_weeks_label, "1 weeks")
        self.assertEqual(first_visit_after_edit.week_in_study_label, "Week 1")
        self.assertEqual(first_visit_after_edit.change_type, "Edit")
        self.assertEqual(first_visit_after_create.change_type, "Create")
        self.assertEqual(first_visit_after_create.changes, {})
        self.assertEqual(first_visit_after_create.study_duration_weeks_label, "0 weeks")
        self.assertEqual(first_visit_after_create.week_in_study_label, "Week 0")
        self.assertEqual(second_visit_history.changes, {})
        self.assertEqual(second_visit_history.uid, second_visit.uid)

    def test__create_subvisits_uvn__reordered_successfully(self):
        visit_service = StudyVisitService(study_uid=self.study.uid)
        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0005",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=True,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        time_value = 30
        first_visit_in_seq_of_subvisits = create_visit_with_update(
            study_epoch_uid=self.epoch2.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=time_value,
            time_unit_uid=self.day_uid,
            visit_sublabel_reference=None,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="ANCHOR_VISIT_IN_GROUP_OF_SUBV",
        )
        sub_visit_uvn = 200
        # we add so many subvists as there is a logic of
        # recalculating subvists unique-visit-numbers when we exceed allowed limits
        for i in range(1, 21):
            create_visit_with_update(
                study_epoch_uid=self.epoch2.uid,
                visit_type_uid="VisitType_0003",
                time_reference_uid="VisitSubType_0005",
                time_value=time_value + i,
                time_unit_uid=self.day_uid,
                visit_sublabel_reference=first_visit_in_seq_of_subvisits.uid,
                is_global_anchor_visit=False,
                visit_class="SINGLE_VISIT",
                visit_subclass="ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV",
            )
            # check unique visit numbers before recalculation
            if i == 9:
                all_visits = visit_service.get_all_visits(
                    study_uid=self.study.uid
                ).items
                for sub_idx, sub_visit in enumerate(all_visits[1:]):
                    if (
                        sub_visit.visit_subclass
                        == "ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV"
                    ):
                        self.assertEqual(
                            sub_visit.study_day_number - 1,
                            time_value + time_value + sub_idx,
                        )
                    self.assertEqual(
                        sub_visit.unique_visit_number, sub_visit_uvn + sub_idx * 10
                    )
            # check unique visit numbers after first recalculation
            if i == 10:
                all_visits = visit_service.get_all_visits(
                    study_uid=self.study.uid
                ).items
                for sub_idx, sub_visit in enumerate(all_visits[1:]):
                    if (
                        sub_visit.visit_subclass
                        == "ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV"
                    ):
                        self.assertEqual(
                            sub_visit.study_day_number - 1,
                            time_value + time_value + sub_idx,
                        )
                    self.assertEqual(
                        sub_visit.unique_visit_number, sub_visit_uvn + sub_idx * 5
                    )
            # check unique visit numbers after second recalculation
            if i == 20:
                all_visits = visit_service.get_all_visits(
                    study_uid=self.study.uid
                ).items
                for sub_idx, sub_visit in enumerate(all_visits[1:]):
                    if (
                        sub_visit.visit_subclass
                        == "ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV"
                    ):
                        self.assertEqual(
                            sub_visit.study_day_number - 1,
                            time_value + time_value + sub_idx,
                        )
                    self.assertEqual(
                        sub_visit.unique_visit_number, sub_visit_uvn + sub_idx * 1
                    )
        create_visit_with_update(
            study_epoch_uid=self.epoch2.uid,
            visit_type_uid="VisitType_0003",
            time_reference_uid="VisitSubType_0005",
            time_value=-1,
            time_unit_uid=self.day_uid,
            visit_sublabel_reference=first_visit_in_seq_of_subvisits.uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV",
        )
        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch2 = epochs[1]

        epoch = epoch_service.find_by_uid(epoch2.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )

        all_visits = visit_service.get_all_visits(study_uid=self.study.uid).items
        self.assertEqual(len(all_visits), 23)

        all_visits = [visit for visit in all_visits if visit.visit_number == 2]

        self.assertEqual(all_visits[0].unique_visit_number, sub_visit_uvn)
        self.assertEqual(all_visits[0].study_day_number - 1, time_value - 1)
        self.assertEqual(all_visits[1].unique_visit_number, sub_visit_uvn + 1)
        self.assertEqual(all_visits[1].study_day_number - 1, time_value)

    def test__get_global_anchor_visit(self):
        visit_service = StudyVisitService(study_uid=self.study.uid)

        with self.assertRaises(NotFoundException):
            visit_service.get_global_anchor_visit(study_uid=self.study.uid)

        vis = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0005",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=True,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch1 = epochs[0]

        epoch = epoch_service.find_by_uid(epoch1.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        global_anchor_visit = visit_service.get_global_anchor_visit(
            study_uid=self.study.uid
        )
        self.assertEqual(global_anchor_visit.uid, vis.uid)
        self.assertEqual(global_anchor_visit.visit_name, vis.visit_name)
        self.assertEqual(
            global_anchor_visit.visit_type_name, vis.visit_type.sponsor_preferred_name
        )

    def test__get_anchor_visits_in_a_group_of_subvisits(self):
        visit_service = StudyVisitService(study_uid=self.study.uid)

        anchor_visits = visit_service.get_anchor_visits_in_a_group_of_subvisits(
            study_uid=self.study.uid
        )
        self.assertEqual(anchor_visits, [])

        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0005",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=True,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        anchor_visit = create_visit_with_update(
            study_epoch_uid=self.epoch2.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=30,
            time_unit_uid=self.day_uid,
            visit_sublabel_reference=None,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="ANCHOR_VISIT_IN_GROUP_OF_SUBV",
        )
        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch2 = epochs[1]

        epoch = epoch_service.find_by_uid(epoch2.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        anchor_visits = visit_service.get_anchor_visits_in_a_group_of_subvisits(
            study_uid=self.study.uid
        )
        self.assertEqual(len(anchor_visits), 1)
        self.assertEqual(anchor_visit.uid, anchor_visits[0].uid)
        self.assertEqual(anchor_visit.visit_name, anchor_visits[0].visit_name)
        self.assertEqual(
            anchor_visit.visit_type.sponsor_preferred_name,
            anchor_visits[0].visit_type_name,
        )

    def test__epochs_durations_are_calculated_properly_when_having_empty_epoch(self):
        epoch_service = StudyEpochService()

        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0005",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=True,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            study_epoch_uid=self.epoch3.uid,
            visit_type_uid="VisitType_0003",
            time_reference_uid="VisitSubType_0001",
            time_value=10,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            study_epoch_uid=self.epoch3.uid,
            visit_type_uid="VisitType_0003",
            time_reference_uid="VisitSubType_0001",
            time_value=30,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch3 = epochs[2]

        epoch = epoch_service.find_by_uid(epoch3.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )

        study_epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(study_epochs), 3)
        self.assertEqual(study_epochs[0].start_day, 1)
        self.assertEqual(study_epochs[0].duration, 0)
        self.assertEqual(study_epochs[0].end_day, 1)
        self.assertEqual(study_epochs[1].start_day, 1)
        self.assertEqual(study_epochs[1].duration, 10)
        self.assertEqual(study_epochs[1].end_day, 11)
        self.assertEqual(study_epochs[2].start_day, 11)
        self.assertEqual(study_epochs[2].duration, 20)
        self.assertEqual(study_epochs[2].end_day, 31)

    def test__epochs_durations_are_calculated_properly_when_having_last_epoch_with_one_visit(
        self,
    ):
        epoch_service = StudyEpochService()

        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0001",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0003",
            time_reference_uid="VisitSubType_0001",
            time_value=10,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            study_epoch_uid=self.epoch2.uid,
            visit_type_uid="VisitType_0003",
            time_reference_uid="VisitSubType_0001",
            time_value=30,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            study_epoch_uid=self.epoch2.uid,
            visit_type_uid="VisitType_0003",
            time_reference_uid="VisitSubType_0001",
            time_value=40,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            study_epoch_uid=self.epoch3.uid,
            visit_type_uid="VisitType_0003",
            time_reference_uid="VisitSubType_0001",
            time_value=50,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch1 = epochs[0]
        epoch2 = epochs[1]
        epoch3 = epochs[2]
        epoch = epoch_service.find_by_uid(epoch1.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        epoch = epoch_service.find_by_uid(epoch2.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        epoch = epoch_service.find_by_uid(epoch3.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        study_epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(study_epochs), 3)
        self.assertEqual(study_epochs[0].start_day, 1)
        self.assertEqual(study_epochs[0].duration, 30)
        self.assertEqual(study_epochs[0].end_day, 31)
        self.assertEqual(study_epochs[1].start_day, 31)
        self.assertEqual(study_epochs[1].duration, 20)
        self.assertEqual(study_epochs[1].end_day, 51)
        self.assertEqual(study_epochs[2].start_day, 51)
        self.assertEqual(study_epochs[2].duration, 7)
        self.assertEqual(study_epochs[2].end_day, 58)

    def test__create_visit_with_duplicated_timing__error_raised(self):
        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0005",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=True,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch1 = epochs[0]

        epoch = epoch_service.find_by_uid(epoch1.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        with self.assertRaises(ValidationException):
            create_visit_with_update(
                study_epoch_uid=self.epoch1.uid,
                visit_type_uid="VisitType_0001",
                time_reference_uid="VisitSubType_0005",
                time_value=0,
                time_unit_uid=self.day_uid,
                is_global_anchor_visit=True,
                visit_class="SINGLE_VISIT",
                visit_subclass="SINGLE_VISIT",
            )

    def test__create_unscheduled_visit_without_time_data__no_error_is_raised(self):
        visit_service: StudyVisitService = StudyVisitService(study_uid=self.study.uid)
        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0005",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=True,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=10,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        non_visit_input = {
            "study_epoch_uid": self.epoch1.uid,
            "consecutive_visit_group": None,
            "show_visit": True,
            "description": "description",
            "start_rule": "start_rule",
            "end_rule": "end_rule",
            "visit_contact_mode_uid": "VisitContactMode_0001",
            "visit_type_uid": "VisitType_0003",
            "is_global_anchor_visit": False,
            "visit_class": "NON_VISIT",
        }
        visit_input = StudyVisitCreateInput(**non_visit_input)
        visit_service.create(study_uid=self.study.uid, study_visit_input=visit_input)
        with self.assertRaises(ValidationException):
            visit_service.create(
                study_uid=self.study.uid, study_visit_input=visit_input
            )
        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch1 = epochs[0]

        epoch = epoch_service.find_by_uid(epoch1.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )

        all_visits = visit_service.get_all_visits(study_uid=self.study.uid).items

        self.assertEqual(len(all_visits), 3)
        self.assertEqual(all_visits[0].time_value, 0)
        self.assertEqual(all_visits[1].time_value, 10)
        self.assertEqual(all_visits[2].time_value, None)
        self.assertEqual(all_visits[2].time_reference_uid, None)
        self.assertEqual(all_visits[2].time_reference, None)
        self.assertEqual(all_visits[2].visit_number, NON_VISIT_NUMBER)
        self.assertEqual(all_visits[2].min_visit_window_value, -9999)
        self.assertEqual(all_visits[2].max_visit_window_value, 9999)

    def test__create_special_visit(self):
        visit_service: StudyVisitService = StudyVisitService(study_uid=self.study.uid)
        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0005",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=True,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        special_visit_anchor = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=10,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0003",
            time_reference_uid="VisitSubType_0005",
            time_value=15,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch1 = epochs[0]

        epoch = epoch_service.find_by_uid(epoch1.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        special_visit_input = {
            "study_epoch_uid": self.epoch1.uid,
            "consecutive_visit_group": None,
            "show_visit": True,
            "description": "description",
            "start_rule": "start_rule",
            "end_rule": "end_rule",
            "visit_contact_mode_uid": "VisitContactMode_0001",
            "visit_type_uid": "VisitType_0003",
            "is_global_anchor_visit": False,
            "visit_class": "SPECIAL_VISIT",
            "visit_sublabel_reference": special_visit_anchor.uid,
        }
        visit_input = StudyVisitCreateInput(**special_visit_input)
        special_visit = visit_service.create(
            study_uid=self.study.uid, study_visit_input=visit_input
        )
        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch1 = epochs[0]

        epoch = epoch_service.find_by_uid(epoch1.uid, study_uid=self.study.uid)
        start_rule = "New start rule2"
        end_rule = "New end rule2"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )

        all_visits = visit_service.get_all_visits(study_uid=self.study.uid).items

        self.assertEqual(len(all_visits), 4)
        self.assertEqual(all_visits[0].time_value, 0)
        self.assertEqual(all_visits[1].time_value, 10)
        self.assertEqual(all_visits[2].time_value, None)
        self.assertEqual(all_visits[2].time_reference_uid, None)
        self.assertEqual(all_visits[2].time_reference, None)
        self.assertEqual(all_visits[2].visit_number, special_visit_anchor.visit_number)
        self.assertEqual(
            all_visits[2].visit_short_name, special_visit_anchor.visit_short_name + "A"
        )
        self.assertEqual(all_visits[3].time_value, 15)

        with self.assertRaises(AlreadyExistsException):
            visit_service.create(
                study_uid=self.study.uid, study_visit_input=visit_input
            )
        with self.assertRaises(BusinessLogicException) as message:
            visit_service.delete(
                study_uid=self.study.uid, study_visit_uid=special_visit_anchor.uid
            )
            self.assertEqual(
                f"The Visit can't be deleted as other visits ([{special_visit.uid}]) are referencing this Visit",
                message.exception.msg,
            )
        visit_service.delete(
            study_uid=self.study.uid, study_visit_uid=special_visit.uid
        )
        visit_service.delete(
            study_uid=self.study.uid, study_visit_uid=special_visit_anchor.uid
        )

    def test__group_subsequent_visits_in_consecutive_group(self):
        visit_service: StudyVisitService = StudyVisitService(study_uid=self.study.uid)
        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0005",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=True,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        second_vis = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=10,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        third_visit = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=15,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        fourth_visit = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=20,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch1 = epochs[0]

        epoch = epoch_service.find_by_uid(epoch1.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        consecutive_visit_group = (
            f"{second_vis.visit_short_name}-{third_visit.visit_short_name}"
        )
        with self.assertRaises(BusinessLogicException) as message:
            visit_service.assign_visit_consecutive_group(
                study_uid=self.study.uid,
                visits_to_assign=[second_vis.uid, fourth_visit.uid],
                overwrite_visit_from_template=None,
            )
            self.assertEqual(
                f"The {fourth_visit.uid} that is trying to be assigned to {consecutive_visit_group} "
                f"consecutive visit group is not subsequent with other visits",
                message.exception.msg,
            )

        visit_service.assign_visit_consecutive_group(
            study_uid=self.study.uid,
            visits_to_assign=[second_vis.uid, third_visit.uid],
            overwrite_visit_from_template=None,
        )
        all_visits = visit_service.get_all_visits(study_uid=self.study.uid).items

        self.assertEqual(len(all_visits), 4)
        self.assertEqual(all_visits[1].consecutive_visit_group, consecutive_visit_group)
        self.assertEqual(all_visits[2].consecutive_visit_group, consecutive_visit_group)

    def test__group_visits_in_consecutive_group__visits_are_not_equal(self):
        visit_service: StudyVisitService = StudyVisitService(study_uid=self.study.uid)
        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0005",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=True,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        second_visit = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=10,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch1 = epochs[0]

        epoch = epoch_service.find_by_uid(epoch1.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        # assign some study activity schedule
        activity_group = TestUtils.create_activity_group(name="activity_group")
        activity_subgroup = TestUtils.create_activity_subgroup(
            name="activity_subgroup", activity_groups=[activity_group.uid]
        )
        ar1 = TestUtils.create_activity(
            name="ar1",
            library_name="Sponsor",
            activity_groups=[activity_group.uid],
            activity_subgroups=[activity_subgroup.uid],
        )
        ar2 = TestUtils.create_activity(
            name="ar2",
            library_name="Sponsor",
            activity_groups=[activity_group.uid],
            activity_subgroups=[activity_subgroup.uid],
        )
        ar3 = TestUtils.create_activity(
            name="ar3",
            library_name="Sponsor",
            activity_groups=[activity_group.uid],
            activity_subgroups=[activity_subgroup.uid],
        )
        sa1 = create_study_activity(
            study_uid=self.study.uid,
            activity_uid=ar1.uid,
            activity_subgroup_uid=activity_subgroup.uid,
            activity_group_uid=activity_group.uid,
            soa_group_term_uid=self.flowchart_group.term_uid,
        )
        sas1 = TestUtils.create_study_activity_schedule(
            study_uid=self.study.uid,
            study_activity_uid=sa1.study_activity_uid,
            study_visit_uid=second_visit.uid,
        )
        # get all study activity schedules for second visit
        schedule_service = StudyActivityScheduleService()
        sec_vis_all_schedules = schedule_service.get_all_schedules_for_specific_visit(
            study_uid=self.study.uid, study_visit_uid=second_visit.uid
        )
        self.assertEqual(len(sec_vis_all_schedules), 1)
        self.assertEqual(
            sas1.study_activity_schedule_uid,
            sec_vis_all_schedules[0].study_activity_schedule_uid,
        )

        third_visit = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0003",
            time_reference_uid="VisitSubType_0005",
            time_value=15,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
            visit_contact_mode_uid="VisitContactMode_0002",
            max_visit_window_value=10,
            min_visit_window_value=-10,
        )
        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch1 = epochs[0]

        epoch = epoch_service.find_by_uid(epoch1.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        sa2 = create_study_activity(
            study_uid=self.study.uid,
            activity_uid=ar2.uid,
            activity_subgroup_uid=activity_subgroup.uid,
            activity_group_uid=activity_group.uid,
            soa_group_term_uid=self.flowchart_group.term_uid,
        )
        sas2 = TestUtils.create_study_activity_schedule(
            study_uid=self.study.uid,
            study_activity_uid=sa2.study_activity_uid,
            study_visit_uid=third_visit.uid,
        )
        sa3 = create_study_activity(
            study_uid=self.study.uid,
            activity_uid=ar3.uid,
            activity_subgroup_uid=activity_subgroup.uid,
            activity_group_uid=activity_group.uid,
            soa_group_term_uid=self.flowchart_group.term_uid,
        )
        sas3 = TestUtils.create_study_activity_schedule(
            study_uid=self.study.uid,
            study_activity_uid=sa3.study_activity_uid,
            study_visit_uid=third_visit.uid,
        )

        # get all study activity schedules for third visit
        third_vis_all_schedules = schedule_service.get_all_schedules_for_specific_visit(
            study_uid=self.study.uid, study_visit_uid=third_visit.uid
        )
        self.assertEqual(len(third_vis_all_schedules), 2)
        self.assertEqual(
            sas2.study_activity_schedule_uid,
            third_vis_all_schedules[0].study_activity_schedule_uid,
        )
        self.assertEqual(
            sas3.study_activity_schedule_uid,
            third_vis_all_schedules[1].study_activity_schedule_uid,
        )
        # BusinessLogicException is raised as StudyVisits have different:
        # VisitType, VisitContactMode, VisitWindowMin/Max values
        with self.assertRaises(BusinessLogicException) as message:
            visit_service.assign_visit_consecutive_group(
                study_uid=self.study.uid,
                visits_to_assign=[second_visit.uid, third_visit.uid],
                overwrite_visit_from_template=None,
            )
            self.assertEqual(
                f"The following visit {second_visit.visit_name} is not the same as {third_visit.visit_name}",
                message.exception.msg,
            )
        edit_input = {
            "uid": third_visit.uid,
            "study_epoch_uid": third_visit.study_epoch_uid,
            "visit_type_uid": "VisitType_0002",
            "visit_contact_mode_uid": "VisitContactMode_0001",
            "max_visit_window_value": 1,
            "min_visit_window_value": -1,
            "time_reference_uid": third_visit.time_reference_uid,
            "time_value": third_visit.time_value,
            "time_unit_uid": third_visit.time_unit_uid,
            "is_global_anchor_visit": third_visit.is_global_anchor_visit,
            "visit_class": third_visit.visit_class,
            "visit_subclass": third_visit.visit_subclass,
            "show_visit": third_visit.show_visit,
        }

        visit_service.edit(
            study_uid=third_visit.study_uid,
            study_visit_uid=third_visit.uid,
            study_visit_input=StudyVisitEditInput(**edit_input),
        )

        # VisitsAreNotEqual is raised as StudyVisits have same properties but diffent schedules assigned
        with self.assertRaises(VisitsAreNotEqualException) as message:
            visit_service.assign_visit_consecutive_group(
                study_uid=self.study.uid,
                visits_to_assign=[second_visit.uid, third_visit.uid],
                overwrite_visit_from_template=None,
            )
            self.assertEqual(
                f"The following visit {second_visit.visit_name} has different schedules assigned than {third_visit.visit_name}",
                message.exception.msg,
            )
        visit_service.assign_visit_consecutive_group(
            study_uid=self.study.uid,
            visits_to_assign=[second_visit.uid, third_visit.uid],
            overwrite_visit_from_template=third_visit.uid,
        )
        sec_vis_all_schedules = schedule_service.get_all_schedules_for_specific_visit(
            study_uid=self.study.uid, study_visit_uid=second_visit.uid
        )
        self.assertEqual(len(sec_vis_all_schedules), 2)
        self.assertEqual(
            sas2.study_activity_uid,
            sec_vis_all_schedules[0].study_activity_uid,
        )
        self.assertEqual(
            sas3.study_activity_uid,
            sec_vis_all_schedules[1].study_activity_uid,
        )
        # the third visit activities should be overwritten from the second study
        third_vis_all_schedules = schedule_service.get_all_schedules_for_specific_visit(
            study_uid=self.study.uid, study_visit_uid=third_visit.uid
        )
        self.assertEqual(len(third_vis_all_schedules), 2)
        self.assertEqual(
            sas2.study_activity_uid,
            third_vis_all_schedules[0].study_activity_uid,
        )
        self.assertEqual(
            sas3.study_activity_uid,
            third_vis_all_schedules[1].study_activity_uid,
        )
        all_visits = visit_service.get_all_visits(study_uid=self.study.uid).items

        self.assertEqual(len(all_visits), 3)
        self.assertEqual(
            all_visits[2].consecutive_visit_group, all_visits[1].consecutive_visit_group
        )
        self.assertEqual(
            all_visits[2].min_visit_window_value, all_visits[1].min_visit_window_value
        )
        self.assertEqual(
            all_visits[2].max_visit_window_value, all_visits[1].max_visit_window_value
        )
        self.assertEqual(
            all_visits[2].visit_contact_mode_uid, all_visits[1].visit_contact_mode_uid
        )
        self.assertEqual(
            all_visits[2].visit_contact_mode.sponsor_preferred_name,
            all_visits[1].visit_contact_mode.sponsor_preferred_name,
        )

    def test__group_visits_in_consecutive_group__visits_are_already_in_consecutive_groups(
        self,
    ):
        visit_service: StudyVisitService = StudyVisitService(study_uid=self.study.uid)
        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0005",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=True,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        second_visit = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=10,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        third_visit = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=11,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch1 = epochs[0]

        epoch = epoch_service.find_by_uid(epoch1.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        cons_visit_group = (
            f"{second_visit.visit_short_name}-{third_visit.visit_short_name}"
        )
        visit_service.assign_visit_consecutive_group(
            study_uid=self.study.uid,
            visits_to_assign=[second_visit.uid, third_visit.uid],
            overwrite_visit_from_template=None,
        )

        second_vis = visit_service.find_by_uid(
            study_uid=self.study.uid, uid=second_visit.uid
        )
        self.assertEqual(second_vis.consecutive_visit_group, cons_visit_group)

        fourth_visit = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=15,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )

        with self.assertRaises(BusinessLogicException) as message:
            visit_service.assign_visit_consecutive_group(
                study_uid=self.study.uid,
                visits_to_assign=[second_visit.uid, third_visit.uid, fourth_visit.uid],
                overwrite_visit_from_template=None,
            )
            self.assertEqual(
                f"The following visit {second_visit.uid} already has consecutive group {cons_visit_group}",
                message.exception.msg,
            )

        all_available_consecutive_groups = visit_service.get_consecutive_groups(
            study_uid=self.study.uid
        )
        self.assertEqual(all_available_consecutive_groups, {cons_visit_group})

        consecutive_visit_group = (
            f"{second_visit.visit_short_name}-{fourth_visit.visit_short_name}"
        )
        visit_service.assign_visit_consecutive_group(
            study_uid=self.study.uid,
            visits_to_assign=[second_visit.uid, third_visit.uid, fourth_visit.uid],
            overwrite_visit_from_template=third_visit.uid,
        )
        all_visits = visit_service.get_all_visits(study_uid=self.study.uid).items

        self.assertEqual(len(all_visits), 4)
        self.assertEqual(
            all_visits[3].consecutive_visit_group, all_visits[1].consecutive_visit_group
        )

        all_available_consecutive_groups = visit_service.get_consecutive_groups(
            study_uid=self.study.uid
        )
        self.assertEqual(all_available_consecutive_groups, {consecutive_visit_group})

    def test__consecutive_visits_should_be_subsequent(
        self,
    ):
        visit_service: StudyVisitService = StudyVisitService(study_uid=self.study.uid)
        first_visit = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0005",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=True,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        second_visit = create_visit_with_update(
            study_epoch_uid=self.epoch2.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=10,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        third_visit = create_visit_with_update(
            study_epoch_uid=self.epoch2.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=11,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="ANCHOR_VISIT_IN_GROUP_OF_SUBV",
        )
        first_subv = create_visit_with_update(
            study_epoch_uid=self.epoch2.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=12,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_sublabel_reference=third_visit.uid,
            visit_class="SINGLE_VISIT",
            visit_subclass="ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV",
        )
        second_subv = create_visit_with_update(
            study_epoch_uid=self.epoch2.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=13,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_sublabel_reference=third_visit.uid,
            visit_class="SINGLE_VISIT",
            visit_subclass="ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV",
        )

        with self.assertRaises(BusinessLogicException) as message:
            visit_service.assign_visit_consecutive_group(
                study_uid=self.study.uid,
                visits_to_assign=[first_visit.uid, second_visit.uid],
                overwrite_visit_from_template=None,
            )
            self.assertEqual(
                f"Given Visits can't be collapsed as they exist in different Epochs [{first_visit.study_epoch.sponsor_preferred_name, second_visit.study_epoch.sponsor_preferred_name}]",
                message.exception.msg,
            )

        with self.assertRaises(BusinessLogicException) as message:
            visit_service.assign_visit_consecutive_group(
                study_uid=self.study.uid,
                visits_to_assign=[first_visit.uid, third_visit.uid],
                overwrite_visit_from_template=None,
            )
            self.assertEqual(
                "To create visits group please select consecutive visits.",
                message.exception.msg,
            )

        first_consecutive_visit_group = (
            f"{second_visit.visit_short_name}-{third_visit.visit_short_name}"
        )
        visit_service.assign_visit_consecutive_group(
            study_uid=self.study.uid,
            visits_to_assign=[second_visit.uid, third_visit.uid],
            overwrite_visit_from_template=None,
        )

        all_visits = visit_service.get_all_visits(study_uid=self.study.uid).items
        self.assertEqual(len(all_visits), 5)
        self.assertEqual(
            all_visits[1].consecutive_visit_group, all_visits[2].consecutive_visit_group
        )

        all_available_consecutive_groups = visit_service.get_consecutive_groups(
            study_uid=self.study.uid
        )
        self.assertEqual(
            all_available_consecutive_groups, {first_consecutive_visit_group}
        )

        second_consecutive_visit_group = (
            f"{first_subv.visit_short_name}-{second_subv.visit_short_name}"
        )
        visit_service.assign_visit_consecutive_group(
            study_uid=self.study.uid,
            visits_to_assign=[first_subv.uid, second_subv.uid],
            overwrite_visit_from_template=None,
        )

        all_visits = visit_service.get_all_visits(study_uid=self.study.uid).items
        self.assertEqual(len(all_visits), 5)
        self.assertEqual(
            all_visits[3].consecutive_visit_group, all_visits[4].consecutive_visit_group
        )

        all_available_consecutive_groups = visit_service.get_consecutive_groups(
            study_uid=self.study.uid
        )
        self.assertEqual(
            sorted(all_available_consecutive_groups),
            [first_consecutive_visit_group, second_consecutive_visit_group],
        )

    def test__remove_consecutive_visit_group(self):
        visit_service: StudyVisitService = StudyVisitService(study_uid=self.study.uid)
        create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0001",
            time_reference_uid="VisitSubType_0005",
            time_value=0,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=True,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        second_visit = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=10,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        third_visit = create_visit_with_update(
            study_epoch_uid=self.epoch1.uid,
            visit_type_uid="VisitType_0002",
            time_reference_uid="VisitSubType_0005",
            time_value=15,
            time_unit_uid=self.day_uid,
            is_global_anchor_visit=False,
            visit_class="SINGLE_VISIT",
            visit_subclass="SINGLE_VISIT",
        )
        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch1 = epochs[0]

        epoch = epoch_service.find_by_uid(epoch1.uid, study_uid=self.study.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        consecutive_visit_group = (
            f"{second_visit.visit_short_name}-{third_visit.visit_short_name}"
        )
        visit_service.assign_visit_consecutive_group(
            study_uid=self.study.uid,
            visits_to_assign=[second_visit.uid, third_visit.uid],
            overwrite_visit_from_template=None,
        )
        all_visits = visit_service.get_all_visits(study_uid=self.study.uid).items

        self.assertEqual(len(all_visits), 3)
        self.assertEqual(all_visits[1].consecutive_visit_group, consecutive_visit_group)
        self.assertEqual(all_visits[2].consecutive_visit_group, consecutive_visit_group)

        all_available_consecutive_groups = visit_service.get_consecutive_groups(
            study_uid=self.study.uid
        )
        self.assertEqual(all_available_consecutive_groups, {consecutive_visit_group})

        # locking and unlocking to create multiple study value relationships on the existent StudySelections
        TestUtils.create_study_fields_configuration()
        TestUtils.lock_and_unlock_study(study_uid=self.study.uid)

        visit_service.remove_visit_consecutive_group(
            study_uid=self.study.uid, consecutive_visit_group=consecutive_visit_group
        )
        all_visits = visit_service.get_all_visits(study_uid=self.study.uid).items
        self.assertEqual(len(all_visits), 3)
        self.assertEqual(all_visits[1].consecutive_visit_group, None)
        self.assertEqual(all_visits[2].consecutive_visit_group, None)

        all_available_consecutive_groups = visit_service.get_consecutive_groups(
            study_uid=self.study.uid
        )
        self.assertEqual(all_available_consecutive_groups, set())

    def test_get_anchor_visit_for_special_visit(self):
        visit_service: StudyVisitService = StudyVisitService(study_uid=self.study.uid)
        # create 5 visits in epoch 1
        for idx in range(0, 5):
            is_global_anchor_visit = bool(idx == 0)
            create_visit_with_update(
                study_epoch_uid=self.epoch1.uid,
                visit_type_uid="VisitType_0002",
                time_reference_uid="VisitSubType_0005",
                time_value=idx,
                time_unit_uid=self.day_uid,
                is_global_anchor_visit=is_global_anchor_visit,
                visit_class="SINGLE_VISIT",
                visit_subclass="SINGLE_VISIT",
            )
        # create 5 visits in epoch 2
        for idx in range(5, 10):
            create_visit_with_update(
                study_epoch_uid=self.epoch2.uid,
                visit_type_uid="VisitType_0002",
                time_reference_uid="VisitSubType_0005",
                time_value=idx,
                time_unit_uid=self.day_uid,
                is_global_anchor_visit=False,
                visit_class="SINGLE_VISIT",
                visit_subclass="SINGLE_VISIT",
            )
        all_anchor_visits_for_special_visit = (
            visit_service.get_anchor_for_special_visit(
                study_uid=self.study.uid, study_epoch_uid=self.epoch2.uid
            )
        )
        assert len(all_anchor_visits_for_special_visit) == 5
        # enumerating from 6 because Visit names are being assigned from 1,
        # so the first batch in epoch1 will be (1,2,3,4,5)
        # and second batch in epoch2 will be (6,7,8,9,10)
        for idx, anchor_visit in enumerate(all_anchor_visits_for_special_visit, 6):
            assert anchor_visit.visit_name == f"Visit {idx}"

    def test_consecutive_visit_group_name(self):
        """Test name of consecutive_visit_group_name when merging visit < 10 with visit >= 10"""

        study = TestUtils.create_study()
        visit_service: StudyVisitService = StudyVisitService(study_uid=study.uid)

        study_epoch = TestUtils.create_study_epoch(
            study_uid=study.uid, epoch_subtype="EpochSubType_0001"
        )

        study_visits = []
        for idx in range(0, 12):
            visit_input = generate_default_input_data_for_visit()
            visit_input.update(time_value=idx, time_unit_uid=self.day_uid)
            study_visits.append(
                TestUtils.create_study_visit(
                    study_uid=study.uid, study_epoch_uid=study_epoch.uid, **visit_input
                )
            )

        visit_service.assign_visit_consecutive_group(
            study_uid=study.uid,
            visits_to_assign=[
                study_visits[-2].uid,
                study_visits[-5].uid,
                study_visits[-4].uid,
                study_visits[-3].uid,
            ],
            overwrite_visit_from_template=None,
        )

        visits_grouped = visit_service.get_all_visits(study_uid=study.uid).items

        assert (
            visits_grouped[-2].consecutive_visit_group
            == f"{study_visits[-5].visit_short_name}-{study_visits[-2].visit_short_name}"
        )
