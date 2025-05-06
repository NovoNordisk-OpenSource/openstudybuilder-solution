import unittest

from neomodel import db

from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.models.study_selections.study_epoch import (
    StudyEpoch,
    StudyEpochCreateInput,
    StudyEpochEditInput,
)
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    fix_study_preferred_time_unit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from common import exceptions
from common.config import SDTM_CT_CATALOGUE_NAME


class TestStudyEpochManagement(unittest.TestCase):
    TPR_LABEL = "ParameterName"

    def setUp(self):
        inject_and_clear_db("studiesepochstest")
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)

        # Generate UIDs
        StudyRoot.generate_node_uids_if_not_present()
        self.study = StudyRoot.nodes.all()[0]
        TestUtils.create_ct_catalogue(catalogue_name=SDTM_CT_CATALOGUE_NAME)
        TestUtils.set_study_standard_version(
            study_uid=self.study.uid, create_codelists_and_terms_for_package=False
        )
        create_study_epoch_codelists_ret_cat_and_lib()

        fix_study_preferred_time_unit(self.study.uid)

    def test__list_epoch_studies(self):
        epoch_service = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items

        assert len(epochs) == 0

    def test__create_study_epoch(self):
        epoch_service = StudyEpochService()
        study_epoch_create_input = StudyEpochCreateInput(
            study_uid="study_root",
            start_rule="start_rule",
            end_rule="end_rule",
            description="test_description",
            epoch_subtype="EpochSubType_0001",
            duration=0,
            duration_unit="duration_unit",
            order="1",
            color_hash="#1100FF",
        )
        StudyEpochService().create(
            "study_root", study_epoch_input=study_epoch_create_input
        )
        epochs = epoch_service.get_all_epochs(self.study.uid).items

        assert len(epochs) == 1

    def test__create_study_epoch_with_not_unique_epoch_subtype__not_raises_forbidden_error(
        self,
    ):
        epoch_subtype_uid = "EpochSubType_0001"
        create_study_epoch(epoch_subtype_uid=epoch_subtype_uid)
        create_study_epoch(epoch_subtype_uid=epoch_subtype_uid)

        epoch_service = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 2)

    def test__create_study_epoch_with_not_unique_epoch_subtype__epoch_names_are_properly_assigned(
        self,
    ):
        epoch_service = StudyEpochService()

        first_epoch_subtype_name = "Epoch Subtype1"
        first_epoch_subtype_uid = "EpochSubType_0002"

        create_study_epoch(epoch_subtype_uid=first_epoch_subtype_uid)
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 1)
        self.assertEqual(
            epochs[0].epoch_ctterm.sponsor_preferred_name, first_epoch_subtype_name
        )
        self.assertEqual(epochs[0].order, 1)

        epoch_subtype_uid = "EpochSubType_0001"
        epoch_subtype_name = "Epoch Subtype"

        create_study_epoch(epoch_subtype_uid=epoch_subtype_uid)
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 2)
        self.assertEqual(
            epochs[0].epoch_ctterm.sponsor_preferred_name, first_epoch_subtype_name
        )
        self.assertEqual(epochs[0].order, 1)
        self.assertEqual(
            epochs[1].epoch_ctterm.sponsor_preferred_name, epoch_subtype_name
        )
        self.assertEqual(epochs[1].order, 2)

        create_study_epoch(epoch_subtype_uid=epoch_subtype_uid)

        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        self.assertEqual(
            epochs[0].epoch_ctterm.sponsor_preferred_name, first_epoch_subtype_name
        )
        self.assertEqual(epochs[0].order, 1)
        self.assertEqual(
            epochs[1].epoch_ctterm.sponsor_preferred_name, epoch_subtype_name + " 1"
        )
        self.assertEqual(epochs[1].order, 2)
        self.assertEqual(
            epochs[2].epoch_ctterm.sponsor_preferred_name, epoch_subtype_name + " 2"
        )
        self.assertEqual(epochs[2].order, 3)

    def test__create_study_epoch_no_unit__created(self):
        epoch_service = StudyEpochService()
        study_epoch_create_input = StudyEpochCreateInput(
            study_uid="study_root",
            start_rule="start_rule",
            end_rule="end_rule",
            description="test_description",
            epoch_subtype="EpochSubType_0001",
            duration=0,
            color_hash="#1100FF",
        )
        StudyEpochService().create(
            "study_root", study_epoch_input=study_epoch_create_input
        )
        epochs = epoch_service.get_all_epochs(self.study.uid).items

        assert len(epochs) == 1

    def test__reorder_epochs(self):
        epoch_service = StudyEpochService()
        ep_epoch_subtype_uid = "EpochSubType_0001"
        ep_epoch_subtype_name = "Epoch Subtype"
        ep1: StudyEpoch = create_study_epoch(ep_epoch_subtype_uid)
        ep2 = create_study_epoch(ep_epoch_subtype_uid)
        ep3 = create_study_epoch(ep_epoch_subtype_uid)

        ep1 = epoch_service.find_by_uid(ep1.uid, study_uid=ep1.study_uid)
        ep2 = epoch_service.find_by_uid(ep2.uid, study_uid=ep2.study_uid)
        ep3 = epoch_service.find_by_uid(ep3.uid, study_uid=ep3.study_uid)

        self.assertEqual(ep1.order, 1)
        self.assertEqual(
            ep1.epoch_ctterm.sponsor_preferred_name, ep_epoch_subtype_name + " 1"
        )
        self.assertEqual(ep2.order, 2)
        self.assertEqual(
            ep2.epoch_ctterm.sponsor_preferred_name, ep_epoch_subtype_name + " 2"
        )
        self.assertEqual(ep3.order, 3)
        self.assertEqual(
            ep3.epoch_ctterm.sponsor_preferred_name, ep_epoch_subtype_name + " 3"
        )

        epoch_service.reorder(ep3.uid, study_uid=ep3.study_uid, new_order=1)

        ep_after1 = epoch_service.find_by_uid(ep1.uid, study_uid=ep1.study_uid)
        ep_after2 = epoch_service.find_by_uid(ep2.uid, study_uid=ep2.study_uid)
        ep_after3 = epoch_service.find_by_uid(ep3.uid, study_uid=ep3.study_uid)

        self.assertEqual(ep_after1.order, 2)
        self.assertEqual(
            ep_after1.epoch_ctterm.sponsor_preferred_name, ep_epoch_subtype_name + " 2"
        )
        self.assertEqual(ep_after2.order, 3)
        self.assertEqual(
            ep_after2.epoch_ctterm.sponsor_preferred_name, ep_epoch_subtype_name + " 3"
        )
        self.assertEqual(ep_after3.order, 1)
        self.assertEqual(
            ep_after3.epoch_ctterm.sponsor_preferred_name, ep_epoch_subtype_name + " 1"
        )

        epoch_service.reorder(ep1.uid, study_uid=ep1.study_uid, new_order=3)

        ep_after1 = epoch_service.find_by_uid(ep1.uid, study_uid=ep1.study_uid)
        ep_after2 = epoch_service.find_by_uid(ep2.uid, study_uid=ep2.study_uid)
        ep_after3 = epoch_service.find_by_uid(ep3.uid, study_uid=ep3.study_uid)

        self.assertEqual(ep_after1.order, 3)
        self.assertEqual(
            ep_after1.epoch_ctterm.sponsor_preferred_name, ep_epoch_subtype_name + " 3"
        )
        self.assertEqual(ep_after2.order, 2)
        self.assertEqual(
            ep_after2.epoch_ctterm.sponsor_preferred_name, ep_epoch_subtype_name + " 2"
        )
        self.assertEqual(ep_after3.order, 1)
        self.assertEqual(
            ep_after3.epoch_ctterm.sponsor_preferred_name, ep_epoch_subtype_name + " 1"
        )

        epoch_subtype_uid2 = "EpochSubType_0002"
        epoch_subtype_name2 = "Epoch Subtype1"
        epoch_subtype_uid3 = "EpochSubType_0003"
        epoch_subtype_name3 = "Epoch Subtype2"
        epoch_subtype_2 = create_study_epoch(epoch_subtype_uid2)
        epoch_subtype_3 = create_study_epoch(epoch_subtype_uid3)
        ep2 = epoch_service.find_by_uid(
            epoch_subtype_2.uid, study_uid=epoch_subtype_2.study_uid
        )
        self.assertEqual(ep2.order, 4)
        self.assertEqual(ep2.epoch_ctterm.sponsor_preferred_name, epoch_subtype_name2)
        ep3 = epoch_service.find_by_uid(
            epoch_subtype_3.uid, study_uid=epoch_subtype_3.study_uid
        )
        self.assertEqual(ep3.order, 5)
        self.assertEqual(ep3.epoch_ctterm.sponsor_preferred_name, epoch_subtype_name3)
        epoch_service.reorder(ep3.uid, study_uid=ep3.study_uid, new_order=4)
        ep2 = epoch_service.find_by_uid(
            epoch_subtype_2.uid, study_uid=epoch_subtype_2.study_uid
        )
        self.assertEqual(ep2.order, 5)
        self.assertEqual(ep2.epoch_ctterm.sponsor_preferred_name, epoch_subtype_name2)
        ep3 = epoch_service.find_by_uid(
            epoch_subtype_3.uid, study_uid=epoch_subtype_3.study_uid
        )
        self.assertEqual(ep3.order, 4)
        self.assertEqual(ep3.epoch_ctterm.sponsor_preferred_name, epoch_subtype_name3)

    def test__create_study_epoch_with_not_unique_epoch_subtype__new_epoch_is_being_created(
        self,
    ):
        epoch_service = StudyEpochService()

        epoch_subtype_uid = "EpochSubType_0001"
        epoch_subtype_name = "Epoch Subtype"
        create_study_epoch(epoch_subtype_uid=epoch_subtype_uid)
        epochs = epoch_service.get_all_epochs(self.study.uid).items

        self.assertEqual(len(epochs), 1)
        self.assertEqual(
            epochs[0].epoch_ctterm.sponsor_preferred_name, epoch_subtype_name
        )

        create_study_epoch(epoch_subtype_uid=epoch_subtype_uid)
        create_study_epoch(epoch_subtype_uid=epoch_subtype_uid)
        create_study_epoch(epoch_subtype_uid=epoch_subtype_uid)
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 4)
        self.assertEqual(
            epochs[0].epoch_ctterm.sponsor_preferred_name, epoch_subtype_name + " 1"
        )
        self.assertEqual(
            epochs[1].epoch_ctterm.sponsor_preferred_name, epoch_subtype_name + " 2"
        )
        self.assertEqual(
            epochs[2].epoch_ctterm.sponsor_preferred_name, epoch_subtype_name + " 3"
        )
        self.assertEqual(
            epochs[3].epoch_ctterm.sponsor_preferred_name, epoch_subtype_name + " 4"
        )

    def test__preview_study_epoch_should_not_bump_epoch_counter(
        self,
    ):
        epoch_service = StudyEpochService()

        epoch_subtype_uid = "EpochSubType_0001"
        epoch_subtype_name = "Epoch Subtype"
        create_study_epoch(epoch_subtype_uid=epoch_subtype_uid)
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 1)
        self.assertEqual(
            epochs[0].epoch_ctterm.sponsor_preferred_name, epoch_subtype_name
        )

        preview_input = StudyEpochCreateInput(
            study_uid="study_root",
            start_rule="start_rule",
            end_rule="end_rule",
            description="test_description",
            epoch_subtype=epoch_subtype_uid,
            color_hash="#1100FF",
        )
        epoch_service.preview(study_uid=self.study.uid, study_epoch_input=preview_input)

        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 1)
        self.assertEqual(
            epochs[0].epoch_ctterm.sponsor_preferred_name, epoch_subtype_name
        )

    def test__edit_epoch_color(self):
        epoch: StudyEpoch = create_study_epoch("EpochSubType_0001")

        epoch_service = StudyEpochService()

        epoch = epoch_service.find_by_uid(epoch.uid, study_uid=epoch.study_uid)
        # locking and unlocking to create multiple study value relationships on the existent StudySelections
        TestUtils.create_study_fields_configuration()
        TestUtils.lock_and_unlock_study(study_uid="study_root")
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            start_rule=start_rule,
            end_rule=end_rule,
            change_description="rules change",
        )
        edited_epoch = epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        edited_epoch = epoch_service.find_by_uid(
            edited_epoch.uid, study_uid=edited_epoch.study_uid
        )
        self.assertEqual(edited_epoch.start_rule, start_rule)
        self.assertEqual(edited_epoch.end_rule, end_rule)
        # verify that properties not sent in the payload were not overridden
        self.assertEqual(
            edited_epoch.epoch_subtype_ctterm.sponsor_preferred_name,
            epoch.epoch_subtype_ctterm.sponsor_preferred_name,
        )
        self.assertEqual(
            edited_epoch.epoch_type_ctterm.sponsor_preferred_name,
            epoch.epoch_type_ctterm.sponsor_preferred_name,
        )
        self.assertEqual(edited_epoch.duration, epoch.duration)
        self.assertEqual(edited_epoch.color_hash, epoch.color_hash)
        self.assertEqual(edited_epoch.order, epoch.order)
        self.assertEqual(edited_epoch.uid, epoch.uid)

        edit_input = StudyEpochEditInput(
            study_uid=epoch.study_uid,
            color_hash="#FFFFFF",
            change_description="color change",
        )
        edited_epoch = epoch_service.edit(
            study_uid=epoch.study_uid,
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        epoch = epoch_service.find_by_uid(
            edited_epoch.uid, study_uid=edited_epoch.study_uid
        )
        self.assertEqual(epoch.color_hash, "#FFFFFF")

    def test__get_versions(self):
        epoch: StudyEpoch = create_study_epoch(epoch_subtype_uid="EpochSubType_0001")
        epoch_service = StudyEpochService()
        epoch = epoch_service.find_by_uid(epoch.uid, study_uid=epoch.study_uid)
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
        epoch_versions = epoch_service.audit_trail(
            epoch_uid=epoch.uid, study_uid=epoch.study_uid
        )

        current_epoch = epoch_versions[0]
        previous_epoch = epoch_versions[1]
        self.assertEqual(
            set(current_epoch.changes),
            set(
                [
                    "start_rule",
                    "study_version",
                    "start_date",
                    "end_date",
                    "end_rule",
                    "change_type",
                ]
            ),
        )
        self.assertEqual(current_epoch.start_rule, start_rule)
        self.assertEqual(current_epoch.end_rule, end_rule)
        self.assertEqual(previous_epoch.changes, [])
        self.assertEqual(previous_epoch.change_type, "Create")
        self.assertEqual(current_epoch.change_type, "Edit")
        self.assertIsNotNone(previous_epoch.end_date)
        self.assertGreater(current_epoch.start_date, previous_epoch.start_date)
        # test all versions
        epoch: StudyEpoch = create_study_epoch(epoch_subtype_uid="EpochSubType_0002")
        epoch_service = StudyEpochService()
        epoch = epoch_service.find_by_uid(uid=epoch.uid, study_uid=epoch.study_uid)
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
        epoch_versions = epoch_service.audit_trail_all_epochs(
            study_uid=epoch.study_uid,
        )

        current_epoch = epoch_versions[0]
        previous_epoch = epoch_versions[1]
        current_epoch_2 = epoch_versions[2]
        previous_epoch_2 = epoch_versions[3]
        self.assertEqual(
            set(current_epoch.changes),
            set(
                [
                    "start_rule",
                    "study_version",
                    "start_date",
                    "end_date",
                    "end_rule",
                    "change_type",
                ]
            ),
        )
        self.assertEqual(current_epoch.start_rule, start_rule)
        self.assertEqual(current_epoch.end_rule, end_rule)
        self.assertEqual(previous_epoch.changes, [])

        self.assertEqual(
            set(current_epoch_2.changes),
            set(
                [
                    "start_rule",
                    "study_version",
                    "start_date",
                    "end_date",
                    "end_rule",
                    "change_type",
                ]
            ),
        )
        self.assertEqual(current_epoch_2.start_rule, start_rule)
        self.assertEqual(current_epoch_2.end_rule, end_rule)
        self.assertEqual(previous_epoch_2.changes, [])

    def test__delete_study_epoch__epochs_are_recalculated(self):
        epoch_service = StudyEpochService()

        first_epoch_subtype_name = "Epoch Subtype1"
        first_epoch_subtype_uid = "EpochSubType_0002"

        create_study_epoch(epoch_subtype_uid=first_epoch_subtype_uid)
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 1)
        self.assertEqual(
            epochs[0].epoch_ctterm.sponsor_preferred_name, first_epoch_subtype_name
        )
        self.assertEqual(epochs[0].order, 1)

        epoch_subtype_uid = "EpochSubType_0001"
        epoch_subtype_name = "Epoch Subtype"
        epoch1 = create_study_epoch(epoch_subtype_uid=epoch_subtype_uid)
        epoch2 = create_study_epoch(epoch_subtype_uid=epoch_subtype_uid)
        epoch3 = create_study_epoch(epoch_subtype_uid=epoch_subtype_uid)

        ep1 = epoch_service.find_by_uid(epoch1.uid, study_uid=epoch1.study_uid)
        ep2 = epoch_service.find_by_uid(epoch2.uid, study_uid=epoch2.study_uid)
        ep3 = epoch_service.find_by_uid(epoch3.uid, study_uid=epoch3.study_uid)

        self.assertEqual(
            ep1.epoch_ctterm.sponsor_preferred_name, epoch_subtype_name + " 1"
        )
        self.assertEqual(ep1.order, 2)
        self.assertEqual(
            ep2.epoch_ctterm.sponsor_preferred_name, epoch_subtype_name + " 2"
        )
        self.assertEqual(ep2.order, 3)
        self.assertEqual(
            ep3.epoch_ctterm.sponsor_preferred_name, epoch_subtype_name + " 3"
        )
        self.assertEqual(ep3.order, 4)

        # locking and unlocking to create multiple study value relationships on the existent StudySelections
        TestUtils.create_study_fields_configuration()
        TestUtils.lock_and_unlock_study(study_uid="study_root")

        epoch_service.delete(study_uid=ep1.study_uid, study_epoch_uid=ep1.uid)

        ep1 = epoch_service.find_by_uid(epoch2.uid, study_uid=epoch2.study_uid)
        ep2 = epoch_service.find_by_uid(epoch3.uid, study_uid=epoch3.study_uid)

        self.assertEqual(
            ep1.epoch_ctterm.sponsor_preferred_name, epoch_subtype_name + " 1"
        )
        self.assertEqual(ep1.order, 2)
        self.assertEqual(
            ep2.epoch_ctterm.sponsor_preferred_name, epoch_subtype_name + " 2"
        )
        self.assertEqual(ep2.order, 3)

        epoch_service.delete(study_uid=ep1.study_uid, study_epoch_uid=ep1.uid)
        ep1 = epoch_service.find_by_uid(ep2.uid, study_uid=ep2.study_uid)
        self.assertEqual(ep1.epoch_ctterm.sponsor_preferred_name, epoch_subtype_name)
        self.assertEqual(ep1.order, 2)

    def test__duplicated_supplemental_epoch_created__value_error_is_raised(self):
        epoch_subtype_uid = "Basic_uid"
        create_study_epoch(epoch_subtype_uid=epoch_subtype_uid)

        with self.assertRaises(exceptions.ValidationException):
            create_study_epoch(epoch_subtype_uid=epoch_subtype_uid)
