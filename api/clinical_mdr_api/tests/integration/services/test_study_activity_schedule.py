import pytest
from neomodel import db

from clinical_mdr_api.models.study_selections.study_selection import (
    StudyActivityScheduleBatchInput,
    StudyActivityScheduleCreateInput,
    StudyActivityScheduleDeleteInput,
)
from clinical_mdr_api.services.studies.study_activity_schedule import (
    StudyActivityScheduleService,
)
from clinical_mdr_api.tests.integration.utils import data_library
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_library_data,
    create_study_activity,
    create_study_epoch,
    create_study_visit_codelists,
    create_visit_with_update,
    get_unit_uid_by_name,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name


class TestData:
    epoch1: any
    epoch2: any
    epoch3: any
    day_uid: any


test_data = TestData()


@pytest.fixture(scope="function")
def setup_and_teardown_db():
    db_name = "studyactivitiescheduletest.schedule"
    inject_and_clear_db(db_name)
    create_library_data()
    db.cypher_query(data_library.STARTUP_ACTIVITY_GROUPS)
    db.cypher_query(data_library.STARTUP_ACTIVITY_SUB_GROUPS)
    db.cypher_query(data_library.STARTUP_ACTIVITIES)

    db.cypher_query(data_library.STARTUP_CT_CATALOGUE_CYPHER)
    db.cypher_query(data_library.STARTUP_SINGLE_STUDY_CYPHER)
    create_study_visit_codelists()
    test_data.epoch1 = create_study_epoch("EpochSubType_0001")
    test_data.epoch2 = create_study_epoch("EpochSubType_0002")
    test_data.epoch3 = create_study_epoch("EpochSubType_0003")
    test_data.day_uid = get_unit_uid_by_name("day")

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

    yield
    drop_db(db_name)


def test_create_delete_schedule(setup_and_teardown_db):
    baseline = create_visit_with_update(
        study_epoch_uid=test_data.epoch1.uid,
        visit_type={"term_uid": "VisitType_0001"},
        time_reference={"term_uid": "VisitSubType_0001"},
        time_value=0,
        time_unit_uid=test_data.day_uid,
    )
    sa1 = create_study_activity("study_root", soa_group_term_uid="term_efficacy_uid")
    service = StudyActivityScheduleService()
    schedule = service.create(
        "study_root",
        StudyActivityScheduleCreateInput(
            study_activity_uid=sa1.study_activity_uid, study_visit_uid=baseline.uid
        ),
    )
    schedules = service.get_all_schedules("study_root")
    assert len(schedules) == 1

    service.delete("study_root", schedule.study_activity_schedule_uid)
    schedules = service.get_all_schedules("study_root")
    assert len(schedules) == 0


def test_batch_operations(setup_and_teardown_db):
    baseline = create_visit_with_update(
        study_epoch_uid=test_data.epoch1.uid,
        visit_type={"term_uid": "VisitType_0001"},
        time_reference={"term_uid": "VisitSubType_0001"},
        time_value=0,
        time_unit_uid=test_data.day_uid,
    )
    create_visit_with_update(
        study_epoch_uid=test_data.epoch1.uid,
        visit_type={"term_uid": "VisitType_0003"},
        time_reference={"term_uid": "VisitSubType_0001"},
        time_value=4,
        time_unit_uid=test_data.day_uid,
    )
    sa1 = create_study_activity("study_root", soa_group_term_uid="term_efficacy_uid")
    sa2 = create_study_activity(
        "study_root",
        activity_uid="activity_root3",
        activity_subgroup_uid="activity_subgroup_root3",
        activity_group_uid="activity_group_root3",
        soa_group_term_uid="term_efficacy_uid",
    )
    service = StudyActivityScheduleService()
    service.handle_batch_operations(
        "study_root",
        [
            StudyActivityScheduleBatchInput(
                method="POST",
                content=StudyActivityScheduleCreateInput(
                    study_activity_uid=sa1.study_activity_uid,
                    study_visit_uid=baseline.uid,
                ),
            ),
            StudyActivityScheduleBatchInput(
                method="POST",
                content=StudyActivityScheduleCreateInput(
                    study_activity_uid=sa2.study_activity_uid,
                    study_visit_uid=baseline.uid,
                ),
            ),
        ],
    )
    schedules = service.get_all_schedules("study_root")
    assert len(schedules) == 2

    service.handle_batch_operations(
        "study_root",
        [
            StudyActivityScheduleBatchInput(
                method="DELETE",
                content=StudyActivityScheduleDeleteInput(
                    uid=schedules[0].study_activity_schedule_uid
                ),
            ),
            StudyActivityScheduleBatchInput(
                method="DELETE",
                content=StudyActivityScheduleDeleteInput(
                    uid=schedules[1].study_activity_schedule_uid
                ),
            ),
        ],
    )
    schedules = service.get_all_schedules("study_root")
    assert len(schedules) == 0
