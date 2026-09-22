"""
Tests for /studies/{study_uid}/study-visits endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable, Mapping
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api import main
from clinical_mdr_api.domains.enums import ValidationMode
from clinical_mdr_api.models.clinical_programmes.clinical_programme import (
    ClinicalProgramme,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import CTTermName
from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.study_selections.study_visit import StudyVisitLite
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.factory_visit import (
    generate_default_input_data_for_visit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_library_data,
    create_study_epoch,
    create_study_visit_codelists,
    get_unit_uid_by_name,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import (
    assert_response_status_code,
    parse_json_response,
)
from common.config import settings
from common.utils import VisitClass

STUDY_VISIT_LITE_KEYS = set(StudyVisitLite.model_fields.keys())


# Global variables shared between fixtures and tests
study: Study
study_visit_uid: str
epoch_uid: str
DAYUID: str
WEEKUID: str
visits_basic_data: dict[Any, Any]
clinical_programme: ClinicalProgramme
project: Project
initial_ct_term_study_standard_test: CTTermName
initial_ct_term_study_standard_test_uid: str
test_data_dict: dict[str, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(main.app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studyvisitapi"
    inject_and_clear_db(db_name)
    global test_data_dict
    _, test_data_dict = inject_base_data()

    global study
    study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=study.uid)
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    create_library_data()
    create_study_visit_codelists(create_unit_definitions=False)
    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=study.uid)
    global epoch_uid
    epoch_uid = study_epoch.uid
    global DAYUID
    DAYUID = get_unit_uid_by_name("day")
    global WEEKUID
    WEEKUID = get_unit_uid_by_name("week")
    global visits_basic_data
    visits_basic_data = generate_default_input_data_for_visit().copy()
    global clinical_programme
    global project
    clinical_programme = TestUtils.create_clinical_programme(name="SoA CP")
    project = TestUtils.create_project(
        name="Project for StudyVisit test",
        project_number="1234",
        description="Base project",
        clinical_programme_uid=clinical_programme.uid,
    )

    catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    # Create a study selection
    ct_term_codelist_name = "VisitType"
    ct_term_name = ct_term_codelist_name + " Name For StudyStandardVersioning test"
    ct_term_start_date = datetime(2020, 3, 25, tzinfo=timezone.utc)

    global initial_ct_term_study_standard_test_uid
    initial_ct_term_study_standard_test_uid = "VisitType_0000"
    global initial_ct_term_study_standard_test
    initial_ct_term_study_standard_test = TestUtils.create_ct_term(
        codelist_uid="CTCodelist_00004",
        submission_value=ct_term_name,
        sponsor_preferred_name=ct_term_name,
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=ct_term_start_date,
        approve=True,
    )

    # patch the date of the latest HAS_VERSION FINAL relationship so it can be detected by the selected study_standard_Version
    params = {
        "uids": [initial_ct_term_study_standard_test_uid],
        "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
    }
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTTermNameRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        EXISTS((ct_name)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )

    yield


@pytest.mark.order("last")
def test_integrity_checks_for_all_studies(api_client):
    """
    Test integrity checks for all available studies in the database.

    This test should always be executed at the END to check the health of the remaining database.
    It validates that all studies in the database pass integrity checks after all other tests have run.
    """
    TestUtils.run_integrity_checks_for_all_studies(
        api_client, mode=ValidationMode.STRICT
    )  # needs to be warning for now as it's leaving broken data


def test_visit_modify_actions_on_locked_study(api_client):
    global study_visit_uid

    inputs = {
        "study_epoch_uid": epoch_uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{study.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    study_visit_uid = res["uid"]
    assert_response_status_code(response, 201)

    # get all visits
    response = api_client.get(
        f"/studies/{study.uid}/study-visits/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res

    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks",
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    inputs = {
        "study_epoch_uid": epoch_uid,
        "visit_type": {"term_uid": "VisitType_0003"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0001"},
        "time_value": 12,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # edit visit
    inputs = {
        "uid": study_visit_uid,
        "study_uid": study.uid,
        "description": "new description",
        "study_epoch_uid": epoch_uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.patch(
        f"/studies/{study.uid}/study-visits/{study_visit_uid}",
        json=datadict,
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-visits/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    for i, _ in enumerate(old_res):
        old_res[i]["study_version"] = mock.ANY
    assert old_res == res

    # test cannot delete
    response = api_client.delete(f"/studies/{study.uid}/study-visits/{study_visit_uid}")
    assert_response_status_code(response, 400)
    assert response.json()["message"] == f"Study with UID '{study.uid}' is locked."


def test_study_visit_versioning(api_client):
    _study_epoch = create_study_epoch("EpochSubType_0003", study_uid=study.uid)

    # get specific study visit
    response = api_client.get(
        f"/studies/{study.uid}/study-visits/{study_visit_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["study_epoch_uid"] == epoch_uid
    before_unlock = res

    # get study visit headers
    response = api_client.get(
        f"/studies/{study.uid}/study-visits/headers?field_name=study_epoch_uid",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == [epoch_uid]

    # Unlock -- Study remain unlocked
    response = api_client.post(
        f"/studies/{study.uid}/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": test_data_dict["reason_for_unlock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # edit study visit
    response = api_client.patch(
        f"/studies/{study.uid}/study-visits/{study_visit_uid}",
        json={
            "show_visit": True,
            "time_unit_uid": "UnitDefinition_000001",
            "time_value": 0,
            "visit_contact_mode": {"term_uid": "VisitContactMode_0001"},
            "visit_type": {"term_uid": "VisitType_0001"},
            "time_reference": {"term_uid": "VisitSubType_0005"},
            "is_global_anchor_visit": True,
            "visit_class": "SINGLE_VISIT",
            "study_epoch_uid": _study_epoch.uid,
            "uid": "StudyVisit_000001",
            "study_uid": "Study_000002",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["study_epoch_uid"] == _study_epoch.uid

    # delete epoch
    response = api_client.delete(f"/studies/{study.uid}/study-epochs/{epoch_uid}")
    assert_response_status_code(response, 204)

    # get all study visits of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-visits?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock["study_version"] = mock.ANY
    assert res["items"][0] == before_unlock

    # get specific study visit of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-visits/{study_visit_uid}?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == before_unlock

    # get study visit headers of specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-visits/headers?field_name=study_epoch_uid&study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == [epoch_uid]

    # get all study visits
    response = api_client.get(
        f"/studies/{study.uid}/study-visits",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["items"][0]["study_epoch_uid"] == _study_epoch.uid

    assert_get_all_visits_lite_compares(res["items"], api_client, study.uid)

    # get specific study visit
    response = api_client.get(
        f"/studies/{study.uid}/study-visits/{study_visit_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["study_epoch_uid"] == _study_epoch.uid
    # get study visits headers
    response = api_client.get(
        f"/studies/{study.uid}/study-visits/headers?field_name=study_epoch_uid",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == [_study_epoch.uid]


@pytest.mark.parametrize(
    "export_format",
    [
        pytest.param("text/csv"),
        pytest.param("text/xml"),
        pytest.param(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    ],
)
def test_get_study_visits_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-visits"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())


def test_manually_defined_visit(api_client):
    study_for_i_visit = TestUtils.create_study(project_number=project.project_number)
    study_epoch = create_study_epoch(
        "EpochSubType_0001", study_uid=study_for_i_visit.uid
    )
    # Create 10 Visits with a timing set in 10 days interval
    for visit_timing in range(0, 100, 10):
        inputs = {
            "study_epoch_uid": study_epoch.uid,
            "visit_type": {"term_uid": "VisitType_0002"},
            "time_reference": {"term_uid": "VisitSubType_0005"},
            "time_value": visit_timing,
            "time_unit_uid": DAYUID,
            "visit_class": "SINGLE_VISIT",
            "visit_subclass": "SINGLE_VISIT",
            "is_global_anchor_visit": False,
        }
        datadict = visits_basic_data.copy()
        datadict.update(inputs)
        response = api_client.post(
            f"/studies/{study_for_i_visit.uid}/study-visits",
            json=datadict,
        )
        assert_response_status_code(response, 201)
        res = response.json()
        assert res["time_value"] == visit_timing

    # create SpecialVisit after ScheduledVisits
    response = api_client.get(
        f"/studies/{study_for_i_visit.uid}/study-visits",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    last_scheduled_visit_uid = res["items"][5]["uid"]
    special_visit_input = {
        "visit_sublabel_reference": last_scheduled_visit_uid,
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_unit_uid": DAYUID,
        "visit_class": "SPECIAL_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data.copy()
    datadict.update(special_visit_input)
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)

    # Given Study Visits is defined as a "Manually defined visit"
    # Create Manually defined Visit
    manually_defined_name = "Visit 5"
    manually_defined_short_name = "Manually defined visit short name"
    manually_defined_number = 777
    manually_defined_unique_number = 7777

    inputs = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 55,
        "time_unit_uid": DAYUID,
        "visit_class": "MANUALLY_DEFINED_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
        "visit_name": manually_defined_name,
        "visit_short_name": manually_defined_short_name,
        "visit_number": manually_defined_number,
        "unique_visit_number": manually_defined_unique_number,
    }
    datadict = visits_basic_data.copy()
    datadict.update(inputs)

    # failed post on the chronological check
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "Values 777.0 in field visit number and 7777 in field unique visit number are not defined in chronological order by study visit timing"
    )

    # failed post on the uniqueness check
    manually_defined_number = 11
    manually_defined_unique_number = 1100
    visit_timing = 110
    datadict.update(
        {
            "time_value": visit_timing,
            "visit_number": manually_defined_number,
            "unique_visit_number": manually_defined_unique_number,
        }
    )
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert res["message"] == "Field visit name - Visit 5 is not unique for the Study"

    # successful post on the uniqueness check for visit name, visit short name, visit number and unique visit number
    # When The visit is created or updated
    manually_defined_name = "Manually defined visit name"
    datadict.update({"visit_name": manually_defined_name})
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )

    # Then The visit number must be assigned manually by user input
    # And The unique visit number must be assigned manually by user input
    # And The visit name must be assigned manually by user input
    # And The SDTM visit name as the upper case version of visit name
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["time_value"] == visit_timing
    assert res["visit_name"] == manually_defined_name
    assert res["visit_short_name"] == manually_defined_short_name
    assert res["visit_number"] == manually_defined_number
    assert res["unique_visit_number"] == manually_defined_unique_number
    manual_visit_uid = res["uid"]

    # failed post on the uniqueness check for visit name, visit short name, visit number and unique visit number
    # And The <study visit field> is defined with a test value that already exist for the study
    datadict.update(
        {
            "visit_name": "Manually defined visit name",
            "visit_short_name": "Manually defined visit short name",
            "visit_number": "11",
            "unique_visit_number": "1100",
            "time_value": 105,
        }
    )
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    # Then The system displays the message "Value \"test value\" in field "<study visit field>" is not unique for the study"
    res = response.json()
    assert_response_status_code(response, 400)
    error_msg = "Fields visit number - 11.0 and unique visit number - 1100 and visit name - Manually defined visit name"
    error_msg += " and visit short name - Manually defined visit short name are not unique for the Study"
    assert res["message"] == error_msg

    # failed edit on uniqueness check for visit name, visit short name, visit number and unique visit number
    # When A study visit is created or updated
    # And The study visit is defined as a "Manually defined visit"
    # And The <study visit field> is defined with a test value that already exist for the study
    datadict.update(
        {
            "time_value": 15,
            "visit_name": "Visit 2",
            "visit_short_name": "V2",
            "visit_number": "2",
            "unique_visit_number": "200",
        }
    )
    response = api_client.patch(
        f"/studies/{study_for_i_visit.uid}/study-visits/{manual_visit_uid}",
        json=datadict,
    )

    # Then The system displays the message "Value \"test value\" in field "<study visit field>" is not unique for the study"
    res = response.json()
    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "Fields visit number - 2.0 and unique visit number - 200 and visit name - Visit 2 and visit short name - V2 are not unique for the Study"
    )

    # successful edit on uniqueness check for visit name, visit short name, visit number and unique visit number
    datadict.update(
        {
            "time_value": 55,
            "visit_name": "Manually defined visit name",
            "visit_short_name": "Manually defined visit short name",
            "visit_number": 6.5,
            "unique_visit_number": 650,
        }
    )
    response = api_client.patch(
        f"/studies/{study_for_i_visit.uid}/study-visits/{manual_visit_uid}",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 200)

    # Support Decimal number as Manually defined visit_number
    # Given Study Visits is defined as a "Manually defined visit"
    # When The visit number is defined or updated
    # When The unique visit number is defined or updated
    decimal_manually_defined_name = "Decimal manually defined visit name"
    decimal_manually_defined_short_name = "Decimal manually defined visit short name"
    decimal_manually_defined_number = 6.8
    decimal_manually_defined_unique_number = 680
    datadict.update(
        {
            "time_value": 57,
            "visit_name": decimal_manually_defined_name,
            "visit_short_name": decimal_manually_defined_short_name,
            "visit_number": decimal_manually_defined_number,
            "unique_visit_number": decimal_manually_defined_unique_number,
        }
    )
    # successful post
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )

    # Then The visit number must support a decimal number "float" data type
    # Then the unique visit number must support an integer data type
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["time_value"] == 57
    assert res["visit_name"] == decimal_manually_defined_name
    assert res["visit_short_name"] == decimal_manually_defined_short_name
    assert res["visit_number"] == decimal_manually_defined_number
    assert res["unique_visit_number"] == decimal_manually_defined_unique_number

    response = api_client.get(f"/studies/{study_for_i_visit.uid}/study-visits")
    assert_response_status_code(response, 200)
    study_visits = response.json()["items"]
    for idx, study_visit in enumerate(study_visits[1:], 1):
        two_consecutive_visit_classes = [
            study_visit["visit_class"],
            study_visits[idx - 1]["visit_class"],
        ]
        # SpecialVisit doesn't contain timing
        if VisitClass.SPECIAL_VISIT.name not in two_consecutive_visit_classes:
            assert study_visit["time_value"] > study_visits[idx - 1]["time_value"]
        if (
            VisitClass.MANUALLY_DEFINED_VISIT.name not in two_consecutive_visit_classes
            and VisitClass.SPECIAL_VISIT.name not in two_consecutive_visit_classes
        ):
            assert study_visit["visit_number"] > study_visits[idx - 1]["visit_number"]


def test_non_manually_defined_visit(api_client):
    study_for_i_visit = TestUtils.create_study(project_number=project.project_number)
    study_epoch = create_study_epoch(
        "EpochSubType_0001", study_uid=study_for_i_visit.uid
    )

    # Create 1 study visit
    inputs_visit = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 20,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }

    datadict = visits_basic_data.copy()
    datadict.update(inputs_visit)
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)

    # Create Manually defined Visit
    manually_defined_name = "Visit 2"
    manually_defined_short_name = "V2"
    manually_defined_number = 2
    manually_defined_unique_number = 200
    vis_input = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 25,
        "time_unit_uid": DAYUID,
        "visit_class": "MANUALLY_DEFINED_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
        "visit_name": manually_defined_name,
        "visit_short_name": manually_defined_short_name,
        "visit_number": manually_defined_number,
        "unique_visit_number": manually_defined_unique_number,
    }
    datadict = visits_basic_data.copy()
    datadict.update(vis_input)
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["time_value"] == 25
    assert res["visit_name"] == manually_defined_name
    assert res["visit_short_name"] == manually_defined_short_name
    assert res["visit_number"] == manually_defined_number
    assert res["unique_visit_number"] == manually_defined_unique_number
    manual_visit_uid = res["uid"]

    response = api_client.get(
        f"/studies/{study_for_i_visit.uid}/study-visits/{manual_visit_uid}/audit-trail/",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == 1

    # failed post on the uniqueness check for non_manually defined visit

    # Create a non_manually (ANCHOR_VISIT_IN_GROUP_OF_SUBV) defined study visit with existed visit number, unique visit number, visit name and visit short name
    # When A study visit is created or updated
    # And The study visit is not defined as a "Manually defined visit"
    # And The <study visit field> is defined with a derived or preset test value that already exist for a manually defined study visit
    inputs_visit = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 22,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "ANCHOR_VISIT_IN_GROUP_OF_SUBV",
        "is_global_anchor_visit": False,
    }

    datadict = visits_basic_data.copy()
    datadict.update(inputs_visit)
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )

    # Then The system displays the message "Value \"test value\" in field "<study visit field>" is not unique for the study
    # as a manually defined value exist. Change the manually defined value before this visit can be defined."
    assert_response_status_code(response, 400)
    res = response.json()
    error_msg = "Fields visit number - 2 and unique visit number - 200 and visit name - Visit 2 are not unique"
    error_msg += " for the Study as a manually defined value exists. Change the manually defined value before this visit can be defined."
    assert res["message"] == error_msg

    # Create a non_manually defined study visit with existed visit number, unique visit number, visit name and visit short name
    # When A study visit is created or updated
    # And The study visit is not defined as a "Manually defined visit"
    # And The <study visit field> is defined with a derived or preset test value that already exist for a manually defined study visit
    inputs_visit = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 22,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }

    datadict = visits_basic_data.copy()
    datadict.update(inputs_visit)
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )

    # Then The system displays the message "Value \"test value\" in field "<study visit field>" is not unique for the study
    # as a manually defined value exist. Change the manually defined value before this visit can be defined."
    assert_response_status_code(response, 400)
    res = response.json()
    error_msg = "Fields visit number - 2 and unique visit number - 200 and visit name - Visit 2 and visit short name - V2 are not unique"
    error_msg += " for the Study as a manually defined value exists. Change the manually defined value before this visit can be defined."
    assert res["message"] == error_msg

    # successful post on the uniqueness check for visit name of non_manually defined visit
    # Update manually defined study visit
    manually_defined_name = "Manually defined visit name test"
    manually_defined_short_name = "Manually defined visit short name test"
    manually_defined_number = 88
    manually_defined_unique_number = 888
    datadict.update(
        {
            "time_value": 58,
            "visit_name": manually_defined_name,
            "visit_short_name": manually_defined_short_name,
            "visit_number": manually_defined_number,
            "unique_visit_number": manually_defined_unique_number,
            "visit_class": "MANUALLY_DEFINED_VISIT",
            "uid": manual_visit_uid,
        }
    )

    response = api_client.patch(
        f"/studies/{study_for_i_visit.uid}/study-visits/{manual_visit_uid}",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 200)

    # Create a non_manually defined study visit with non-existed visit name, visit short name, visit number and unique visit number
    inputs = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 57,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }

    datadict = visits_basic_data.copy()
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 201)


def test_manually_defined_visit_in_chronological_order_by_visit_timing(api_client):
    study_for_i_visit = TestUtils.create_study(project_number=project.project_number)
    study_epoch = create_study_epoch(
        "EpochSubType_0001", study_uid=study_for_i_visit.uid
    )
    # Create 5 visits with a timing set in 20 days interval
    time = 0
    number = 1
    unique_number = 100
    for visit_timing in range(0, 100, 20):
        inputs = {
            "study_epoch_uid": study_epoch.uid,
            "visit_type": {"term_uid": "VisitType_0002"},
            "time_reference": {"term_uid": "VisitSubType_0005"},
            "time_value": visit_timing,
            "time_unit_uid": DAYUID,
            "visit_class": "SINGLE_VISIT",
            "visit_subclass": "SINGLE_VISIT",
            "is_global_anchor_visit": False,
        }
        datadict = visits_basic_data.copy()
        datadict.update(inputs)
        response = api_client.post(
            f"/studies/{study_for_i_visit.uid}/study-visits",
            json=datadict,
        )
        assert_response_status_code(response, 201)
        res = response.json()
        assert res["time_value"] == visit_timing
        assert res["time_value"] == time
        assert res["visit_number"] == number
        assert res["unique_visit_number"] == unique_number
        time = time + 20
        number = number + 1
        unique_number = unique_number + 100

    assert visit_timing == 80
    assert res["visit_number"] == 5
    assert res["unique_visit_number"] == 500

    # When A study visit is created and defined as a "Manually defined visit"
    # And The test visit number is not defined in chronological order by study visit timing
    input1 = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 30,
        "time_unit_uid": DAYUID,
        "visit_class": "MANUALLY_DEFINED_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
        "visit_name": "Manually defined visit name6",
        "visit_short_name": "Manually defined visit short name6",
        "visit_number": 11,
        "unique_visit_number": 250,
    }
    datadict = visits_basic_data.copy()
    datadict.update(input1)
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    # Then The system displays the message "Value \"test visit number\" in field visit number
    #  is not defined in chronological order by study visit timing"
    res = response.json()
    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "Value 11.0 in field visit number is not defined in chronological order by study visit timing"
    )

    input2 = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 30,
        "time_unit_uid": DAYUID,
        "visit_class": "MANUALLY_DEFINED_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
        "visit_name": "Manually defined visit name6",
        "visit_short_name": "Manually defined visit short name6",
        "visit_number": 1.5,
        "unique_visit_number": 250,
    }
    datadict = visits_basic_data.copy()
    datadict.update(input2)
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    # Then The system displays the message "Value \"test visit number\" in field visit number
    #  is not defined in chronological order by study visit timing"
    res = response.json()
    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "Value 1.5 in field visit number is not defined in chronological order by study visit timing"
    )

    # Successfully post a manually defined visit with correct visit number and unique visit number in chronological order by visit timing
    input3 = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 30,
        "time_unit_uid": DAYUID,
        "visit_class": "MANUALLY_DEFINED_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
        "visit_name": "Manually defined visit name6",
        "visit_short_name": "Manually defined visit short name6",
        "visit_number": 2.5,
        "unique_visit_number": 250,
    }
    datadict = visits_basic_data.copy()
    datadict.update(input3)
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # When A study visit is created and defined as a "Manually defined visit"
    # And The test unique visit number is not defined in chronological order by study visit timing
    input4 = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 35,
        "time_unit_uid": DAYUID,
        "visit_class": "MANUALLY_DEFINED_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
        "visit_name": "Manually defined visit name6",
        "visit_short_name": "Manually defined visit short name6",
        "visit_number": 2.5,
        "unique_visit_number": 600,
    }
    datadict = visits_basic_data.copy()
    datadict.update(input4)
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    # Then The system displays the message "Value \"test visit number\" in field unique visit number
    #  is not defined in chronological order by study visit timing"
    res = response.json()
    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "Value 600 in field unique visit number is not defined in chronological order by study visit timing"
    )

    input5 = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 35,
        "time_unit_uid": DAYUID,
        "visit_class": "MANUALLY_DEFINED_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
        "visit_name": "Manually defined visit name6",
        "visit_short_name": "Manually defined visit short name6",
        "visit_number": 2.5,
        "unique_visit_number": 150,
    }
    datadict = visits_basic_data.copy()
    datadict.update(input5)
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    # Then The system displays the message "Value \"test visit number\" in field unique visit number
    #  is not defined in chronological order by study visit timing"
    res = response.json()
    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "Value 150 in field unique visit number is not defined in chronological order by study visit timing"
    )


def test_study_visit_timings(api_client):
    study_for_i_visit = TestUtils.create_study(project_number=project.project_number)
    study_epoch = create_study_epoch(
        "EpochSubType_0001", study_uid=study_for_i_visit.uid
    )
    # timing -14
    inputs = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": -14,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data.copy()
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)

    # timing -1
    datadict.update({"time_value": -1})
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)

    # timing 0
    datadict.update({"time_value": 0})
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)

    # timing 1
    datadict.update({"time_value": 1})
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)

    # timing 14
    datadict.update({"time_value": 14})
    response = api_client.post(
        f"/studies/{study_for_i_visit.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)

    response = api_client.get(f"/studies/{study_for_i_visit.uid}/study-visits")
    assert_response_status_code(response, 200)
    visits = response.json()["items"]
    # timing -14
    assert visits[0]["study_day_number"] == -14
    assert visits[0]["study_duration_days_label"] == "-14 days"
    assert visits[0]["study_week_number"] == -2
    assert visits[0]["study_duration_weeks"] == -2
    assert visits[0]["study_duration_weeks_label"] == "-2 weeks"
    assert visits[0]["week_in_study_label"] == "Week -2"
    # timing -1
    assert visits[1]["study_day_number"] == -1
    assert visits[1]["study_duration_days_label"] == "-1 days"
    assert visits[1]["study_week_number"] == -1
    assert visits[1]["study_duration_weeks"] == 0
    assert visits[1]["study_duration_weeks_label"] == "0 weeks"
    assert visits[1]["week_in_study_label"] == "Week 0"
    # timing 0
    assert visits[2]["study_day_number"] == 1
    assert visits[2]["study_duration_days_label"] == "0 days"
    assert visits[2]["study_week_number"] == 1
    assert visits[2]["study_duration_weeks"] == 0
    assert visits[2]["study_duration_weeks_label"] == "0 weeks"
    assert visits[2]["week_in_study_label"] == "Week 0"
    # timing 1
    assert visits[3]["study_day_number"] == 2
    assert visits[3]["study_duration_days_label"] == "1 days"
    assert visits[3]["study_week_number"] == 1
    assert visits[3]["study_duration_weeks"] == 0
    assert visits[3]["study_duration_weeks_label"] == "0 weeks"
    assert visits[3]["week_in_study_label"] == "Week 0"
    # timing 14
    assert visits[4]["study_day_number"] == 15
    assert visits[4]["study_duration_days_label"] == "14 days"
    assert visits[4]["study_week_number"] == 3
    assert visits[4]["study_duration_weeks"] == 2
    assert visits[4]["study_duration_weeks_label"] == "2 weeks"
    assert visits[4]["week_in_study_label"] == "Week 2"


def test_create_repeating_visit(api_client):
    _term = TestUtils.create_ct_term(
        codelist_uid="CTCodelist_Repeating_Visit_Frequency"
    )
    _study = TestUtils.create_study()
    _study_epoch = create_study_epoch("EpochSubType_0001", study_uid=_study.uid)

    inputs = {
        "study_epoch_uid": _study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "REPEATING_VISIT",
        "is_global_anchor_visit": True,
        "repeating_frequency_uid": _term.term_uid,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["repeating_frequency"]["term_uid"] == _term.term_uid
    assert (
        res["repeating_frequency"]["sponsor_preferred_name"]
        == _term.sponsor_preferred_name
    )
    assert res["visit_name"] == "Visit 1.n"
    assert res["visit_subname"] == "Visit 1.n"
    assert res["visit_short_name"] == "V1.n"
    assert res["visit_subclass"] == "REPEATING_VISIT"

    response = api_client.get(f"/studies/{_study.uid}/study-visits/{res['uid']}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["repeating_frequency"]["term_uid"] == _term.term_uid
    assert (
        res["repeating_frequency"]["sponsor_preferred_name"]
        == _term.sponsor_preferred_name
    )
    assert res["visit_name"] == "Visit 1.n"
    assert res["visit_subname"] == "Visit 1.n"
    assert res["visit_short_name"] == "V1.n"
    assert res["visit_subclass"] == "REPEATING_VISIT"

    # When A new repeating visit is created
    inputs = {
        "study_epoch_uid": _study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": -2,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "REPEATING_VISIT",
        "is_global_anchor_visit": False,
        "repeating_frequency_uid": _term.term_uid,
    }
    datadict = visits_basic_data.copy()
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["repeating_frequency"]["term_uid"] == _term.term_uid
    assert (
        res["repeating_frequency"]["sponsor_preferred_name"]
        == _term.sponsor_preferred_name
    )
    assert res["visit_name"] == "Visit 1.n"
    assert res["visit_number"] == 1.0
    assert res["visit_short_name"] == "V1.n"
    assert res["visit_subclass"] == "REPEATING_VISIT"

    # Then The visit number should be chronological
    # And The visit name and visit short name should follow visit naming rules
    response = api_client.get(f"/studies/{_study.uid}/study-visits/{res['uid']}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["repeating_frequency"]["term_uid"] == _term.term_uid
    assert (
        res["repeating_frequency"]["sponsor_preferred_name"]
        == _term.sponsor_preferred_name
    )
    assert res["visit_name"] == "Visit 1.n"
    assert res["visit_number"] == 1.0
    assert res["visit_short_name"] == "V1.n"
    assert res["visit_subclass"] == "REPEATING_VISIT"


def test_create_visit_0(api_client):
    _study = TestUtils.create_study()
    study_epoch1 = create_study_epoch(
        "information_epoch_subtype_uid", study_uid=_study.uid
    )
    study_epoch2 = create_study_epoch("Basic_uid", study_uid=_study.uid)

    inputs = {
        "study_epoch_uid": study_epoch1.uid,
        "visit_type": {"term_uid": "VisitType_0000"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": -1,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["visit_name"] == "Visit 0"
    assert res["visit_subname"] == "Visit 0"
    assert res["visit_short_name"] == "V0"
    assert res["visit_subclass"] == "SINGLE_VISIT"
    study_visit0_uid = res["uid"]

    response = api_client.get(f"/studies/{_study.uid}/study-visits/{study_visit0_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["visit_name"] == "Visit 0"
    assert res["visit_subname"] == "Visit 0"
    assert res["visit_short_name"] == "V0"
    assert res["visit_subclass"] == "SINGLE_VISIT"

    inputs = {
        "study_epoch_uid": study_epoch2.uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["visit_name"] == "Visit 1"
    assert res["visit_subname"] == "Visit 1"
    assert res["visit_short_name"] == "V1"
    assert res["visit_subclass"] == "SINGLE_VISIT"

    study_visit1_uid = res["uid"]

    # Verify the information visit 0 can be removed successfully
    response = api_client.delete(
        f"/studies/{_study.uid}/study-visits/{study_visit0_uid}"
    )
    assert_response_status_code(response, 204)

    # Verify that the original visit was not re-ordered
    response = api_client.get(f"/studies/{_study.uid}/study-visits/{study_visit1_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["visit_name"] == "Visit 1"
    assert res["visit_number"] == 1.0
    assert res["visit_short_name"] == "V1"


def test_visit_0_created_chronologically(api_client):
    _study = TestUtils.create_study()
    study_epoch1 = create_study_epoch(
        "information_epoch_subtype_uid", study_uid=_study.uid
    )
    study_epoch2 = create_study_epoch("Basic_uid", study_uid=_study.uid)

    # Test pre-conditions: create two normal visits with different time value
    input1 = {
        "study_epoch_uid": study_epoch2.uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 10,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(input1)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["visit_name"] == "Visit 1"
    assert res["visit_number"] == 1.0
    assert res["visit_short_name"] == "V1"

    input2 = {
        "study_epoch_uid": study_epoch2.uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 20,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(input2)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["visit_name"] == "Visit 2"
    assert res["visit_number"] == 2.0
    assert res["visit_short_name"] == "V2"

    study_visit2_uid = res["uid"]

    # Scenario: User must be able to create an information visit without visit 0 if the time value is not the lowest
    # Create an information visit with non-first timing
    inputs = {
        "study_epoch_uid": study_epoch1.uid,
        "visit_type": {"term_uid": "VisitType_0000"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 15,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # The name and number of the newly created information visit should follow the regular naming and numbering rules
    assert res["visit_name"] == "Visit 2"
    assert res["visit_number"] == 2.0
    assert res["visit_short_name"] == "V2"

    study_visit0_uid = res["uid"]

    # The original Visit 2 should be re-named and re-numbered
    response = api_client.get(f"/studies/{_study.uid}/study-visits/{study_visit2_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["visit_name"] == "Visit 3"
    assert res["visit_number"] == 3.0
    assert res["visit_short_name"] == "V3"

    # Scenario: User must be able to delete the study information visit without visit 0
    # Delete the information visit without 0
    response = api_client.delete(
        f"/studies/{_study.uid}/study-visits/{study_visit0_uid}"
    )
    assert_response_status_code(response, 204)

    # Then The reordering of other visits will occur
    response = api_client.get(f"/studies/{_study.uid}/study-visits/{study_visit2_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["visit_name"] == "Visit 2"
    assert res["visit_number"] == 2.0
    assert res["visit_short_name"] == "V2"

    # Scenario: User must be able to create an information visit with visit 0 if the time value is the lowest
    # Create an information visit with first timing
    inputs = {
        "study_epoch_uid": study_epoch1.uid,
        "visit_type": {"term_uid": "VisitType_0000"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 5,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    # Verify that newly created information visit should be Visit 0
    assert res["visit_name"] == "Visit 0"
    assert res["visit_number"] == 0.0
    assert res["visit_short_name"] == "V0"

    study_visit0_uid = res["uid"]

    # The previous Visit 3 should not be changed
    response = api_client.get(f"/studies/{_study.uid}/study-visits/{study_visit2_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["visit_name"] == "Visit 2"
    assert res["visit_number"] == 2.0
    assert res["visit_short_name"] == "V2"

    # Scenario: User must be able to indirectly edit the existing information visit 0 when a new visit is added with a lower time value
    # When create a new non-information visit with first timing
    input3 = {
        "study_epoch_uid": study_epoch2.uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 3,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(input3)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["visit_name"] == "Visit 1"
    assert res["visit_number"] == 1.0
    assert res["visit_short_name"] == "V1"

    # The existing visit 0 was re-named and re-numbered
    response = api_client.get(f"/studies/{_study.uid}/study-visits/{study_visit0_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["visit_name"] == "Visit 2"
    assert res["visit_number"] == 2.0
    assert res["visit_short_name"] == "V2"

    # The previous Visit 3 should be changed as well
    response = api_client.get(f"/studies/{_study.uid}/study-visits/{study_visit2_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["visit_name"] == "Visit 4"
    assert res["visit_number"] == 4.0
    assert res["visit_short_name"] == "V4"


def test_visit_0_edited_chronologically(api_client):
    # Scenario: User must be able to edit the study information visit with visit 0 to same visit type
    _study = TestUtils.create_study()
    study_epoch1 = create_study_epoch(
        "information_epoch_subtype_uid", study_uid=_study.uid
    )
    study_epoch2 = create_study_epoch("Basic_uid", study_uid=_study.uid)
    # Create a normal visit
    input1 = {
        "study_epoch_uid": study_epoch2.uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 10,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(input1)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["visit_name"] == "Visit 1"
    assert res["visit_number"] == 1.0
    assert res["visit_short_name"] == "V1"
    study_visit1_uid = res["uid"]

    # Create an information visit with first timing
    inputs = {
        "study_epoch_uid": study_epoch1.uid,
        "visit_type": {"term_uid": "VisitType_0000"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 2,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
        "description": "test",
    }
    datadict = visits_basic_data.copy()
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    res = response.json()

    assert_response_status_code(response, 201)
    # Verify that newly created information visit should be Visit 0
    assert res["visit_name"] == "Visit 0"
    assert res["visit_number"] == 0.0
    assert res["visit_short_name"] == "V0"
    study_visit0_uid = res["uid"]

    # When This study information visit is edited to the same visit type
    response = api_client.patch(
        f"/studies/{_study.uid}/study-visits/{study_visit0_uid}",
        json={
            "show_visit": True,
            "time_unit_uid": "UnitDefinition_000001",
            "time_value": 2,
            "visit_contact_mode": {"term_uid": "VisitContactMode_0001"},
            "visit_type": {"term_uid": "VisitType_0000"},
            "time_reference": {"term_uid": "VisitSubType_0005"},
            "is_global_anchor_visit": True,
            "visit_class": "SINGLE_VISIT",
            "study_epoch_uid": study_epoch1.uid,
            "uid": study_visit0_uid,
            "study_uid": _study.uid,
            "description": "Visit 0 update",
        },
    )
    assert_response_status_code(response, 200)

    # Then This visit should be given the visit number of 0
    response = api_client.get(f"/studies/{_study.uid}/study-visits/{study_visit0_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["visit_name"] == "Visit 0"
    assert res["visit_number"] == 0.0
    assert res["visit_short_name"] == "V0"

    # When This visit is edited to higher visit timing compare to the Global Anchor time reference
    response = api_client.patch(
        f"/studies/{_study.uid}/study-visits/{study_visit0_uid}",
        json={
            "show_visit": True,
            "time_unit_uid": "UnitDefinition_000001",
            "time_value": 14,
            "visit_contact_mode": {"term_uid": "VisitContactMode_0001"},
            "visit_type": {"term_uid": "VisitType_0000"},
            "time_reference": {"term_uid": "VisitSubType_0005"},
            "is_global_anchor_visit": True,
            "visit_class": "SINGLE_VISIT",
            "study_epoch_uid": study_epoch1.uid,
            "uid": study_visit0_uid,
            "study_uid": _study.uid,
        },
    )
    assert_response_status_code(response, 200)

    # Then This information visit should Not be given the visit number of 0
    response = api_client.get(f"/studies/{_study.uid}/study-visits/{study_visit0_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["visit_name"] == "Visit 2"
    assert res["visit_number"] == 2.0
    assert res["visit_short_name"] == "V2"

    # Scenario: User must be able to edit the study information visit with visit 0 to other visit type
    # Given A study information visit with visit 0 is created
    inputs = {
        "study_epoch_uid": study_epoch1.uid,
        "visit_type": {"term_uid": "VisitType_0000"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 2,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    # Verify that newly created information visit should be Visit 0
    assert res["visit_name"] == "Visit 0"
    assert res["visit_number"] == 0.0
    assert res["visit_short_name"] == "V0"
    study_visit0_uid = res["uid"]

    # When This study information visit is edited to be a different visit type
    response = api_client.patch(
        f"/studies/{_study.uid}/study-visits/{study_visit0_uid}",
        json={
            "show_visit": True,
            "time_unit_uid": "UnitDefinition_000001",
            "time_value": 2,
            "visit_contact_mode": {"term_uid": "VisitContactMode_0001"},
            "visit_type": {"term_uid": "VisitType_0001"},
            "time_reference": {"term_uid": "VisitSubType_0005"},
            "is_global_anchor_visit": False,
            "visit_class": "SINGLE_VISIT",
            "study_epoch_uid": study_epoch1.uid,
            "uid": study_visit0_uid,
            "study_uid": _study.uid,
        },
    )
    assert_response_status_code(response, 200)

    # Then This visit can no longer be Visit 0
    response = api_client.get(f"/studies/{_study.uid}/study-visits/{study_visit0_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["visit_name"] == "Visit 1"
    assert res["visit_number"] == 1.0
    assert res["visit_short_name"] == "V1"

    # And Reordering of other visits will occur
    response = api_client.get(f"/studies/{_study.uid}/study-visits/{study_visit1_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["visit_name"] == "Visit 2"
    assert res["visit_number"] == 2.0
    assert res["visit_short_name"] == "V2"


def test_study_visist_version_selecting_ct_package(api_client):
    """change the name of a CTTerm, and verify that the study selection is still set to the old name of the CTTerm when the Sponsor Standard version is set"""
    # patch the date of the latest HAS_VERSION FINAL relationship so it can be detected by the selected study_standard_Version
    params = {
        "uids": [initial_ct_term_study_standard_test_uid],
        "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
    }
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTTermNameRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        EXISTS((ct_name)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )
    study_selection_breadcrumb = "study-visits"
    study_selection_ctterm_uid_input_key = "visit_type"
    study_selection_ctterm_key = "visit_type"
    study_selection_ctterm_name_key = "sponsor_preferred_name"
    study_for_ctterm_versioning = TestUtils.create_study()

    study_epoch1 = create_study_epoch(
        "information_epoch_subtype_uid", study_uid=study_for_ctterm_versioning.uid
    )

    inputs = {
        "study_epoch_uid": study_epoch1.uid,
        study_selection_ctterm_uid_input_key: {
            "term_uid": initial_ct_term_study_standard_test.term_uid
        },
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}",
        json=datadict,
    )

    res = response.json()
    assert_response_status_code(response, 201)
    study_selection_uid_study_standard_test = res["uid"]
    assert res["order"] == 1
    assert (
        res[study_selection_ctterm_key][study_selection_ctterm_name_key]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )

    # edit ctterm
    new_ctterm_name = "new ctterm name"
    ctterm_uid = initial_ct_term_study_standard_test.term_uid
    response = api_client.post(
        f"/ct/terms/{ctterm_uid}/names/versions",
    )
    assert_response_status_code(response, 201)
    api_client.patch(
        f"/ct/terms/{ctterm_uid}/names",
        json={
            "sponsor_preferred_name": new_ctterm_name,
            "sponsor_preferred_name_sentence_case": new_ctterm_name,
            "change_description": "string",
        },
    )
    response = api_client.post(f"/ct/terms/{ctterm_uid}/names/approvals")
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}"
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[study_selection_ctterm_key][study_selection_ctterm_name_key]
        == new_ctterm_name
    )

    TestUtils.set_study_standard_version(
        study_uid=study_for_ctterm_versioning.uid,
        package_name="SDTM CT 2020-03-27",
        effective_date=datetime(2020, 3, 27, tzinfo=timezone.utc),
    )

    # get study selection with previous ctterm
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[study_selection_ctterm_key][study_selection_ctterm_name_key]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )

    # edit selection
    datadict.update(
        {"description": "New_Visit", "uid": study_selection_uid_study_standard_test}
    )
    response = api_client.patch(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[study_selection_ctterm_key][study_selection_ctterm_name_key]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )

    # get versions of selection
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[0][study_selection_ctterm_key][study_selection_ctterm_name_key]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )
    assert (
        res[1][study_selection_ctterm_key][study_selection_ctterm_name_key]
        == new_ctterm_name
    )

    # get all versions
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[0][study_selection_ctterm_key][study_selection_ctterm_name_key]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )
    assert (
        res[1][study_selection_ctterm_key][study_selection_ctterm_name_key]
        == new_ctterm_name
    )


def test_study_visit_circular_time_reference_cant_be_created(api_client):
    _study = TestUtils.create_study()
    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=_study.uid)
    baseline_visit_type_time_reference = "BASELINE"
    baseline2_visit_type_time_reference = "BASELINE2"

    # Global Anchor Visit
    visit_input = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
    }
    datadict = visits_basic_data
    datadict.update(visit_input)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)

    visit_input = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0001"},
        "time_value": -10,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(visit_input)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)

    visit_input = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0002"},
        "time_value": 20,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(visit_input)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == f"""Circular Visit time reference detected: The visit which is being created, refers to ({baseline2_visit_type_time_reference})
                    Visit which refers by time reference to Visit Type ({baseline_visit_type_time_reference}) of the Visit which is being created"""
    )

    datadict = visits_basic_data
    datadict.update({"visit_type": {"term_uid": "VisitType_0003"}})
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)
    res = response.json()
    visit_uid = res["uid"]

    datadict.update(
        {
            "visit_type": {"term_uid": "VisitType_0001"},
            "uid": visit_uid,
            "study_uid": _study.uid,
        }
    )
    response = api_client.patch(
        f"/studies/{_study.uid}/study-visits/{visit_uid}",
        json=datadict,
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == f"""Circular Visit time reference detected: The visit which is being created, refers to ({baseline2_visit_type_time_reference})
                    Visit which refers by time reference to Visit Type ({baseline_visit_type_time_reference}) of the Visit which is being created"""
    )


def test_global_anchor_visit_time_reference(api_client):
    _study = TestUtils.create_study()
    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=_study.uid)
    visit_input = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0002"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
    }
    datadict = visits_basic_data
    datadict.update(visit_input)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == "The global anchor visit must take place at day 0 and time reference has to be set to 'Global anchor Visit' or be an Information Visit"
    )

    # Assigning 'Global anchor visit' as time reference
    datadict.update({"time_reference": {"term_uid": "VisitSubType_0005"}})
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)
    visit_uid = response.json()["uid"]

    datadict.update({"time_reference": {"term_uid": "VisitSubType_0002"}})
    response = api_client.patch(
        f"/studies/{_study.uid}/study-visits/{visit_uid}",
        json=datadict,
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == "The global anchor visit must take place at day 0 and time reference has to be set to 'Global anchor Visit' or be an Information Visit"
    )


def test_study_visit_editing_study_epoch(api_client):
    _study = TestUtils.create_study()
    study_epoch_1 = create_study_epoch("EpochSubType_0001", study_uid=_study.uid)
    study_epoch_2 = create_study_epoch("EpochSubType_0002", study_uid=_study.uid)

    # Global Anchor Visit
    visit_input = {
        "study_epoch_uid": study_epoch_1.uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
    }
    datadict = visits_basic_data
    datadict.update(visit_input)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)

    # Create a visit in epoch 1
    visit_input = {
        "study_epoch_uid": study_epoch_1.uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 1,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(visit_input)
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)
    visit_uid = response.json()["uid"]

    # Move the visit to a different epoch - should succeed without epoch ordering restrictions
    datadict.update(
        {
            "study_epoch_uid": study_epoch_2.uid,
            "uid": visit_uid,
            "study_uid": _study.uid,
            "time_value": 1,
        }
    )
    response = api_client.patch(
        f"/studies/{_study.uid}/study-visits/{visit_uid}",
        json=datadict,
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_epoch_uid"] == study_epoch_2.uid

    response = api_client.get(
        f"/studies/{_study.uid}/study-visits/{visit_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_epoch_uid"] == study_epoch_2.uid


def test_creating_special_visit(api_client):
    study = TestUtils.create_study(project_number=project.project_number)
    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=study.uid)

    # Global Anchor Visit
    inputs = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
    }
    global_anchor_datadict = visits_basic_data.copy()
    global_anchor_datadict.update(inputs)
    response = api_client.post(
        f"/studies/{study.uid}/study-visits",
        json=global_anchor_datadict,
    )
    assert_response_status_code(response, 201)
    global_anchor_visit_before_update = response.json()
    global_anchor_visit = global_anchor_visit_before_update["uid"]
    assert global_anchor_visit_before_update["is_soa_milestone"] is False

    # Special Visit
    special_visit_input = {
        "visit_sublabel_reference": global_anchor_visit,
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_unit_uid": DAYUID,
        "visit_class": "SPECIAL_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(special_visit_input)
    response = api_client.post(
        f"/studies/{study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)
    special_visit_v2a = response.json()
    assert special_visit_v2a["visit_short_name"] == "V1A"

    # edit global anchor visit
    global_anchor_edit_datadict = {"uid": global_anchor_visit, "is_soa_milestone": True}
    global_anchor_datadict.update(global_anchor_edit_datadict)
    response = api_client.patch(
        f"/studies/{study.uid}/study-visits/{global_anchor_visit}",
        json=global_anchor_datadict,
    )
    assert_response_status_code(response, 200)
    global_anchor_visit_after_update = response.json()
    assert global_anchor_visit_after_update["is_soa_milestone"] is True

    # Try to create another SpecialVisit which is not Discontinuation Visit
    response = api_client.post(
        f"/studies/{study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)
    special_visit_v2b = response.json()
    assert special_visit_v2b["visit_short_name"] == "V1B"

    # Create early discontinuation special visit anchored to a visit that already has other special visits
    # assert that ordering for early discontinuation will start from 'X'
    datadict.update({"visit_type": {"term_uid": "VisitType_0005"}})
    response = api_client.post(
        f"/studies/{study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["visit_short_name"] == "V1X"

    second_study_epoch = create_study_epoch("EpochSubType_0002", study_uid=study.uid)
    # Visit Day 10
    inputs = {
        "study_epoch_uid": second_study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 10,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)
    visit_day_10 = response.json()["uid"]

    # Special Visit
    special_visit_input = {
        "visit_sublabel_reference": visit_day_10,
        "study_epoch_uid": second_study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0005"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_unit_uid": DAYUID,
        "visit_class": "SPECIAL_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(special_visit_input)
    response = api_client.post(
        f"/studies/{study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["visit_short_name"] == "V2X"

    response = api_client.post(
        f"/studies/{study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["visit_short_name"] == "V2Y"


def test_editing_special_visit(api_client):
    study = TestUtils.create_study(project_number=project.project_number)
    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=study.uid)

    # Global Anchor Visit
    inputs = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)

    # Visit Day 10
    inputs = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 10,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)
    visit_day_10 = response.json()["uid"]

    # Special Visit
    special_visit_input = {
        "visit_sublabel_reference": visit_day_10,
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_unit_uid": DAYUID,
        "visit_class": "SPECIAL_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(special_visit_input)
    response = api_client.post(
        f"/studies/{study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)
    special_visit_uid = response.json()["uid"]

    # edit SpecialVisit
    special_visit_input = {
        "uid": special_visit_uid,
        "visit_sublabel_reference": visit_day_10,
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_unit_uid": DAYUID,
        "visit_class": "SPECIAL_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
        "show_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(special_visit_input)
    response = api_client.patch(
        f"/studies/{study.uid}/study-visits/{special_visit_uid}",
        json=datadict,
    )
    assert_response_status_code(response, 200)
    special_visit_after_update = response.json()
    assert special_visit_after_update["show_visit"] is False


@pytest.mark.parametrize(
    ("study_uid", "study_value_version"),
    [
        ("Study_000492", "57"),
        ("Study_000787", None),
        (
            None,
            "99",
        ),  # None as study_uid will get replaced with study.uid provided by test_data fixture
    ],
)
def test_get_all_visits_invalid_study_uid_or_version(
    api_client, test_data, study_uid: str, study_value_version: str
):
    if study_uid is None:
        # study global was not available at parametrizing time
        study_uid = study.uid
        response = api_client.get(f"/studies/{study_uid}/study-visits")
        assert_response_status_code(response, 200)

    if study_value_version is not None:
        params = {"study_value_version": study_value_version}
    else:
        params = {}

    response = api_client.get(f"/studies/{study_uid}/study-visits", params=params)
    assert_response_status_code(response, 404)

    params["lite"] = "TRUE"
    response = api_client.get(f"/studies/{study_uid}/study-visits", params=params)
    assert_response_status_code(response, 404)


def test_assert_uvn_is_changed_when_group_of_visits_is_modified(api_client):
    study = TestUtils.create_study(project_number=project.project_number)
    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=study.uid)

    # Global Anchor Visit
    anchor_inputs = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "ANCHOR_VISIT_IN_GROUP_OF_SUBV",
        "is_global_anchor_visit": True,
    }
    datadict = visits_basic_data
    datadict.update(anchor_inputs)
    response = api_client.post(
        f"/studies/{study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)
    anchor_visit = response.json()
    anchor_visit_uid = anchor_visit["uid"]
    assert anchor_visit["unique_visit_number"] == 100

    inputs = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0003"},
        "time_reference": {"term_uid": "VisitSubType_0002"},
        "time_value": -10,
        "time_unit_uid": DAYUID,
        "visit_sublabel_reference": anchor_visit_uid,
        "is_global_anchor_visit": False,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV",
    }
    datadict = visits_basic_data
    datadict.update(inputs)

    response = api_client.post(
        f"/studies/{study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)
    subvisit = response.json()
    subvisit_uid = subvisit["uid"]
    assert subvisit["unique_visit_number"] == 100

    response = api_client.get(
        f"/studies/{study.uid}/study-visits/{anchor_visit_uid}/audit-trail",
    )
    assert_response_status_code(response, 200)
    audit_trail = response.json()
    assert len(audit_trail) == 2
    assert audit_trail[0]["unique_visit_number"] == 110
    assert audit_trail[1]["unique_visit_number"] == 100

    datadict.update({"time_value": 10, "uid": subvisit_uid})
    response = api_client.patch(
        f"/studies/{study.uid}/study-visits/{subvisit_uid}",
        json=datadict,
    )
    assert_response_status_code(response, 200)
    assert response.json()["unique_visit_number"] == 110

    response = api_client.get(
        f"/studies/{study.uid}/study-visits/{subvisit_uid}/audit-trail",
    )
    assert_response_status_code(response, 200)
    audit_trail = response.json()
    assert len(audit_trail) == 2
    assert audit_trail[0]["unique_visit_number"] == 110
    assert audit_trail[1]["unique_visit_number"] == 100

    response = api_client.get(
        f"/studies/{study.uid}/study-visits/{anchor_visit_uid}/audit-trail",
    )
    assert_response_status_code(response, 200)
    audit_trail = response.json()
    assert len(audit_trail) == 3
    print(audit_trail[2]["unique_visit_number"])
    assert audit_trail[0]["unique_visit_number"] == 100
    assert audit_trail[1]["unique_visit_number"] == 110
    assert audit_trail[2]["unique_visit_number"] == 100

    new_visit_description = "Edited Anchor Visit"
    anchor_inputs.update(
        {"description": new_visit_description, "uid": anchor_visit_uid}
    )
    datadict = visits_basic_data
    datadict.update(anchor_inputs)
    response = api_client.patch(
        f"/studies/{study.uid}/study-visits/{anchor_visit_uid}",
        json=datadict,
    )
    assert_response_status_code(response, 200)
    assert response.json()["description"] == new_visit_description

    response = api_client.get(
        f"/studies/{study.uid}/study-visits",
    )
    assert_response_status_code(response, 200)
    study_visits = response.json()["items"]
    assert len(study_visits) == 2
    assert study_visits[0]["uid"] == anchor_visit_uid
    assert study_visits[0]["visit_short_name"] == "V1D1"
    assert study_visits[0]["visit_name"] == "Visit 1"
    assert study_visits[0]["unique_visit_number"] == 100
    assert study_visits[1]["uid"] == subvisit_uid
    assert study_visits[1]["visit_short_name"] == "V1D11"
    assert study_visits[1]["visit_name"] == "Visit 1"
    assert study_visits[1]["unique_visit_number"] == 110

    assert_get_all_visits_lite_compares(study_visits, api_client, study.uid)

    # Call for StudyVisits but derive properties based on visit_number instead of returning them straight from DB
    response = api_client.get(
        f"/studies/{study.uid}/study-visits",
        params={"derive_props_based_on_timeline": True},
    )
    assert_response_status_code(response, 200)
    study_visits = response.json()["items"]
    assert len(study_visits) == 2
    assert study_visits[0]["uid"] == anchor_visit_uid
    assert study_visits[0]["visit_short_name"] == "V1D1"
    assert study_visits[0]["visit_name"] == "Visit 1"
    assert study_visits[0]["unique_visit_number"] == 100
    assert study_visits[1]["uid"] == subvisit_uid
    assert study_visits[1]["visit_short_name"] == "V1D11"
    assert study_visits[1]["visit_name"] == "Visit 1"
    assert study_visits[1]["unique_visit_number"] == 110

    assert_get_all_visits_lite_compares(study_visits, api_client, study.uid)

    response = api_client.get(
        f"/studies/{study.uid}/study-visits/{anchor_visit_uid}",
    )
    assert_response_status_code(response, 200)
    study_visit = response.json()
    assert study_visit["uid"] == anchor_visit_uid
    assert study_visit["visit_short_name"] == "V1D1"
    assert study_visit["visit_name"] == "Visit 1"
    assert study_visit["unique_visit_number"] == 100
    response = api_client.get(
        f"/studies/{study.uid}/study-visits/{subvisit_uid}",
    )
    assert_response_status_code(response, 200)
    study_visit = response.json()
    assert study_visit["uid"] == subvisit_uid
    assert study_visit["visit_short_name"] == "V1D11"
    assert study_visit["visit_name"] == "Visit 1"
    assert study_visit["unique_visit_number"] == 110

    # Call for StudyVisits but derive properties based on visit_number instead of returning them straight from DB
    response = api_client.get(
        f"/studies/{study.uid}/study-visits/{anchor_visit_uid}",
        params={"derive_props_based_on_timeline": True},
    )
    assert_response_status_code(response, 200)
    study_visit = response.json()
    assert study_visit["uid"] == anchor_visit_uid
    assert study_visit["visit_short_name"] == "V1D1"
    assert study_visit["visit_name"] == "Visit 1"
    assert study_visit["unique_visit_number"] == 100
    response = api_client.get(
        f"/studies/{study.uid}/study-visits/{subvisit_uid}",
        params={"derive_props_based_on_timeline": True},
    )
    assert_response_status_code(response, 200)
    study_visit = response.json()
    assert study_visit["uid"] == subvisit_uid
    assert study_visit["visit_short_name"] == "V1D11"
    assert study_visit["visit_name"] == "Visit 1"
    assert study_visit["unique_visit_number"] == 110


def test_unique_visit_numbers_resync_when_subvisit_count_crosses_threshold(api_client):
    """
    Regression test for the SoA chronological-order bug.

    The increment step used to space `unique_visit_number` values inside a
    group of sub-visits depends on the total number of additional sub-visits
    in that group:
        < 10 sub-visits -> step 10
        10..19          -> step 5
        >= 20           -> step 1

    Adding (or removing) a sub-visit can therefore cross a threshold and
    invalidate the stored `unique_visit_number` of every other sibling and
    of the anchor itself. Before the fix, only the visit being mutated was
    re-saved, leaving the rest with stale values. The Schedule of
    Activities orders columns by `unique_visit_number`, so stale values
    produced columns out of chronological order.

    This test:
      1. Creates an anchor + 9 additional sub-visits (count = 9, step = 10),
         expecting unique numbers 100, 110, 120, ..., 190.
      2. Adds a 10th additional sub-visit, crossing the 10-sub-visit
         threshold (step becomes 5). After the fix, every sibling - and
         the anchor - must be re-spaced to 100, 105, 110, ..., 150 and the
         GET /study-visits response must already be in strict ascending
         order of `unique_visit_number`.
      3. Deletes one sub-visit, dropping the count back to 9 (step 10
         again). All remaining unique numbers must snap back to
         100, 110, 120, ..., 190.
    """
    study = TestUtils.create_study(project_number=project.project_number)
    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=study.uid)

    # Anchor visit at day 0
    anchor_inputs = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "ANCHOR_VISIT_IN_GROUP_OF_SUBV",
        "is_global_anchor_visit": True,
    }
    datadict = visits_basic_data.copy()
    datadict.update(anchor_inputs)
    response = api_client.post(f"/studies/{study.uid}/study-visits", json=datadict)
    assert_response_status_code(response, 201)
    anchor_uid = response.json()["uid"]
    assert response.json()["unique_visit_number"] == 100

    def _create_subvisit(day: int) -> str:
        sub_inputs = {
            "study_epoch_uid": study_epoch.uid,
            "visit_type": {"term_uid": "VisitType_0003"},
            "time_reference": {"term_uid": "VisitSubType_0002"},
            "time_value": day,
            "time_unit_uid": DAYUID,
            "visit_sublabel_reference": anchor_uid,
            "is_global_anchor_visit": False,
            "visit_class": "SINGLE_VISIT",
            "visit_subclass": "ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV",
        }
        sub_data = visits_basic_data.copy()
        sub_data.update(sub_inputs)
        sub_response = api_client.post(
            f"/studies/{study.uid}/study-visits", json=sub_data
        )
        assert_response_status_code(sub_response, 201)
        return sub_response.json()["uid"]

    # Step 1: create 9 additional sub-visits at days 1..9 (count = 9, step = 10)
    subvisit_uids = [_create_subvisit(day) for day in range(1, 10)]

    response = api_client.get(
        f"/studies/{study.uid}/study-visits", params={"page_size": 0}
    )
    assert_response_status_code(response, 200)
    visits_by_uid = {v["uid"]: v for v in response.json()["items"]}
    assert visits_by_uid[anchor_uid]["unique_visit_number"] == 100
    expected_below_threshold = [110, 120, 130, 140, 150, 160, 170, 180, 190]
    assert [
        visits_by_uid[uid]["unique_visit_number"] for uid in subvisit_uids
    ] == expected_below_threshold

    # Step 2: add a 10th sub-visit, crossing the threshold (count = 10, step = 5).
    # Without the reconciliation fix, only the new sub-visit would be saved
    # with the new spacing while the existing 9 + anchor would keep the
    # old step-10 values, producing an out-of-order SoA.
    subvisit_uids.append(_create_subvisit(10))

    response = api_client.get(
        f"/studies/{study.uid}/study-visits", params={"page_size": 0}
    )
    assert_response_status_code(response, 200)
    visits_by_uid = {v["uid"]: v for v in response.json()["items"]}
    assert visits_by_uid[anchor_uid]["unique_visit_number"] == 100
    expected_at_threshold = [105, 110, 115, 120, 125, 130, 135, 140, 145, 150]
    assert [
        visits_by_uid[uid]["unique_visit_number"] for uid in subvisit_uids
    ] == expected_at_threshold

    # The SoA orders columns by stored unique_visit_number, so the listing
    # must already be strictly ascending - which is the user-visible
    # symptom the bug caused.
    listed_unique_numbers = [v["unique_visit_number"] for v in response.json()["items"]]
    assert listed_unique_numbers == sorted(listed_unique_numbers)

    # Step 3: delete one sub-visit, dropping back below the threshold
    # (count = 9, step = 10). All remaining numbers must snap back.
    removed_uid = subvisit_uids.pop()
    response = api_client.delete(f"/studies/{study.uid}/study-visits/{removed_uid}")
    assert_response_status_code(response, 204)

    response = api_client.get(
        f"/studies/{study.uid}/study-visits", params={"page_size": 0}
    )
    assert_response_status_code(response, 200)
    visits_by_uid = {v["uid"]: v for v in response.json()["items"]}
    assert visits_by_uid[anchor_uid]["unique_visit_number"] == 100
    assert [
        visits_by_uid[uid]["unique_visit_number"] for uid in subvisit_uids
    ] == expected_below_threshold

    listed_unique_numbers = [v["unique_visit_number"] for v in response.json()["items"]]
    assert listed_unique_numbers == sorted(listed_unique_numbers)


def test_it_is_possible_create_many_study_visits_with_the_same_timing(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=test_study.uid)

    study_visits_dict = {}
    for idx_number in range(1, 5):
        inputs = {
            "study_epoch_uid": study_epoch.uid,
            "visit_type": {"term_uid": "VisitType_0002"},
            "time_reference": {"term_uid": "VisitSubType_0005"},
            "time_value": 10,
            "time_unit_uid": DAYUID,
            "visit_class": "SINGLE_VISIT",
            "visit_subclass": "SINGLE_VISIT",
            "is_global_anchor_visit": False,
        }
        datadict = visits_basic_data.copy()
        datadict.update(inputs)
        response = api_client.post(
            f"/studies/{test_study.uid}/study-visits",
            json=datadict,
        )
        assert_response_status_code(response, 201)
        res = response.json()
        assert res["time_value"] == 10
        assert res["visit_number"] == idx_number
        assert res["visit_short_name"] == f"V{idx_number}"
        assert res["unique_visit_number"] == idx_number * 100
        study_visits_dict[res["uid"]] = res

    response = api_client.get(
        f"/studies/{test_study.uid}/study-visits",
    )
    assert_response_status_code(response, 200)
    study_visits = response.json()["items"]

    assert_get_all_visits_lite_compares(study_visits, api_client, test_study.uid)

    first_visit_uid = study_visits[0]["uid"]
    # Edit first StudyVisit with same timing and make sure it's still the first one in schedule
    new_description = "Edited Visit"
    datadict.update({"uid": first_visit_uid, "description": new_description})
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-visits/{first_visit_uid}",
        json=datadict,
    )
    assert_response_status_code(response, 200)
    edited_study_visit = response.json()
    assert edited_study_visit["time_value"] == 10
    assert edited_study_visit["visit_number"] == 1
    assert edited_study_visit["visit_short_name"] == "V1"
    assert edited_study_visit["unique_visit_number"] == 100
    assert edited_study_visit["description"] == new_description

    # Make sure all study visits are returned in the order they were created
    response = api_client.get(
        f"/studies/{test_study.uid}/study-visits",
    )
    assert_response_status_code(response, 200)
    study_visits = response.json()["items"]
    for study_visit in study_visits:
        assert study_visit["uid"] in study_visits_dict
        created_study_visit = study_visits_dict[study_visit["uid"]]
        assert study_visit["visit_number"] == created_study_visit["visit_number"]
        assert (
            study_visit["visit_short_name"] == created_study_visit["visit_short_name"]
        )
        assert (
            study_visit["unique_visit_number"]
            == created_study_visit["unique_visit_number"]
        )

    assert_get_all_visits_lite_compares(study_visits, api_client, test_study.uid)

    # Although it is possible to create 2 visits with the same timing, it should not be possible 2 visits with timing set to 0
    inputs = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0002"},
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
    }
    datadict = visits_basic_data.copy()
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{test_study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 201)
    anchor_visit = response.json()
    assert anchor_visit["time_value"] == 0

    datadict.update({"is_global_anchor_visit": False})
    response = api_client.post(
        f"/studies/{test_study.uid}/study-visits",
        json=datadict,
    )
    assert_response_status_code(response, 409)
    res = response.json()
    assert res["message"] == "There already exists a visit with timing set to 0"

    last_study_visit = study_visits[-1]
    datadict.update(
        {
            "uid": last_study_visit["uid"],
        }
    )
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-visits/{last_study_visit['uid']}",
        json=datadict,
    )
    assert_response_status_code(response, 409)
    res = response.json()
    assert res["message"] == "There already exists a visit with timing set to 0"


def assert_get_all_visits_lite_compares(
    expected_items: Iterable[Mapping],
    api_client,
    study_uid: str,
    study_value_version: str | None = None,
):
    expected_visits = []
    for item in expected_items:
        item_dict = {k: v.value if isinstance(v, Enum) else v for k, v in item.items()}
        expected_visits.append(visit := StudyVisitLite(**item_dict))

        # Lite endpoint returns None for study_day/week_numbers for special visits
        if visit.visit_class == VisitClass.SPECIAL_VISIT:
            visit.study_day_number = None
            visit.study_week_number = None

    # get all visits lite version
    params = {"lite": "true"}
    if study_value_version:
        params["study_value_version"] = study_value_version
    response = api_client.get(f"/studies/{study_uid}/study-visits", params=params)
    results = parse_json_response(response, assert_status=200)
    visits = [StudyVisitLite(**item) for item in results["items"]]
    assert visits == expected_visits


def test__delete_visit_blocked_after_final_protocol_lock(api_client):
    """
    Verify that a visit created before a Final Protocol lock cannot be deleted,
    but a visit created after the lock can still be deleted.
    Also verify that a non-Final-Protocol lock does not block deletion.
    """
    _study = TestUtils.create_study(project_number=project.project_number)
    _study_epoch = create_study_epoch("EpochSubType_0001", study_uid=_study.uid)

    reason_for_lock_term_uid = test_data_dict["reason_for_lock_terms"][0].term_uid
    reason_for_unlock_term_uid = test_data_dict["reason_for_unlock_terms"][0].term_uid

    # Create a visit before any lock
    visit_input = {
        "study_epoch_uid": _study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
    }
    datadict = visits_basic_data.copy()
    datadict.update(visit_input)
    response = api_client.post(f"/studies/{_study.uid}/study-visits", json=datadict)
    assert_response_status_code(response, 201)
    visit_before_lock_uid = response.json()["uid"]

    # Lock with non-Final-Protocol reason ("Port Approval"), then unlock
    TestUtils.lock_and_unlock_study(
        study_uid=_study.uid,
        reason_for_lock_term_uid=reason_for_lock_term_uid,
        reason_for_unlock_term_uid=reason_for_unlock_term_uid,
    )

    # Visit created before a non-Final-Protocol lock should still be deletable
    response = api_client.delete(
        f"/studies/{_study.uid}/study-visits/{visit_before_lock_uid}"
    )
    assert_response_status_code(response, 204)

    # Re-create a visit for the Final Protocol test
    datadict = visits_basic_data.copy()
    datadict.update(visit_input)
    response = api_client.post(f"/studies/{_study.uid}/study-visits", json=datadict)
    assert_response_status_code(response, 201)
    visit_before_fp_lock_uid = response.json()["uid"]

    # Create a "Final Protocol" reason-for-lock term on the existing codelist
    reason_for_lock_cl = test_data_dict["reason_for_lock_cl"]
    final_protocol_term = TestUtils.create_ct_term(
        codelist_uid=reason_for_lock_cl.codelist_uid,
        sponsor_preferred_name="Final Protocol",
        submission_value=settings.final_protocol_term_submval,
    )

    # Lock with Final Protocol reason (requires protocol_header_major_version), then unlock
    response = api_client.post(
        f"/studies/{_study.uid}/locks",
        json={
            "change_description": "Final Protocol Lock",
            "reason_for_change_uid": final_protocol_term.term_uid,
            "protocol_header_major_version": 1,
            "protocol_header_minor_version": 0,
        },
    )
    assert_response_status_code(response, 201)
    response = api_client.post(
        f"/studies/{_study.uid}/unlocks",
        json={
            "change_description": "Unlock after Final Protocol",
            "reason_for_change_uid": reason_for_unlock_term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # Create a visit AFTER the Final Protocol lock
    visit_after_input = {
        "study_epoch_uid": _study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 10,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data.copy()
    datadict.update(visit_after_input)
    response = api_client.post(f"/studies/{_study.uid}/study-visits", json=datadict)
    assert_response_status_code(response, 201)
    visit_after_fp_lock_uid = response.json()["uid"]

    # Visit created BEFORE Final Protocol lock should NOT be deletable
    response = api_client.delete(
        f"/studies/{_study.uid}/study-visits/{visit_before_fp_lock_uid}"
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert "Final Protocol" in res["message"]
    assert "hidden" in res["message"] and "SoA" in res["message"]

    # Visit created AFTER Final Protocol lock should still be deletable
    response = api_client.delete(
        f"/studies/{_study.uid}/study-visits/{visit_after_fp_lock_uid}"
    )
    assert_response_status_code(response, 204)


def test_create_visit_without_epoch(api_client):
    """Creating a visit without study_epoch_uid should succeed with epoch fields as None."""
    inputs = {
        "study_epoch_uid": None,
        "visit_type": {"term_uid": "VisitType_0003"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 200,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data.copy()
    datadict.update(inputs)
    response = api_client.post(f"/studies/{study.uid}/study-visits", json=datadict)
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["study_epoch_uid"] is None
    assert res["study_epoch"] is None
    assert res["uid"] is not None


def test_create_visit_without_epoch_coexists_with_epoch_visits(api_client):
    """Visits without epoch coexist with visits that have an epoch in get_all."""
    _study = TestUtils.create_study(project_number=project.project_number)
    _epoch = create_study_epoch("EpochSubType_0001", study_uid=_study.uid)

    # Anchor visit required for relative time references
    anchor_inputs = {
        "study_epoch_uid": _epoch.uid,
        "visit_sublabel_reference": None,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
        "visit_contact_mode": {"term_uid": "VisitContactMode_0001"},
    }
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits", json=anchor_inputs
    )
    assert_response_status_code(response, 201)

    # Create a visit with epoch
    inputs_with = {
        "study_epoch_uid": _epoch.uid,
        "visit_sublabel_reference": None,
        "visit_type": {"term_uid": "VisitType_0003"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 10,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
        "visit_contact_mode": {"term_uid": "VisitContactMode_0001"},
    }
    response = api_client.post(f"/studies/{_study.uid}/study-visits", json=inputs_with)
    assert_response_status_code(response, 201)
    assert response.json()["study_epoch_uid"] == _epoch.uid

    # Create a visit without epoch
    inputs_without = {
        "study_epoch_uid": None,
        "visit_sublabel_reference": None,
        "visit_type": {"term_uid": "VisitType_0004"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 20,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
        "visit_contact_mode": {"term_uid": "VisitContactMode_0001"},
    }
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits", json=inputs_without
    )
    assert_response_status_code(response, 201)
    assert response.json()["study_epoch_uid"] is None

    # Verify both types coexist in listing
    response = api_client.get(f"/studies/{_study.uid}/study-visits")
    assert_response_status_code(response, 200)
    items = response.json()["items"]
    visits_with_epoch = [v for v in items if v["study_epoch_uid"] is not None]
    visits_without_epoch = [v for v in items if v["study_epoch_uid"] is None]
    assert len(visits_with_epoch) >= 1
    assert len(visits_without_epoch) >= 1
    for v in visits_without_epoch:
        assert v["study_epoch"] is None


def test_edit_visit_to_remove_epoch(api_client):
    """Editing a visit to set study_epoch_uid=None removes the epoch."""
    _study = TestUtils.create_study(project_number=project.project_number)
    _epoch = create_study_epoch("EpochSubType_0001", study_uid=_study.uid)

    # Anchor visit required for relative time references
    anchor_inputs = {
        "study_epoch_uid": _epoch.uid,
        "visit_sublabel_reference": None,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
        "visit_contact_mode": {"term_uid": "VisitContactMode_0001"},
    }
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits", json=anchor_inputs
    )
    assert_response_status_code(response, 201)

    # Create a visit with epoch
    inputs = {
        "study_epoch_uid": _epoch.uid,
        "visit_sublabel_reference": None,
        "visit_type": {"term_uid": "VisitType_0003"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 10,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
        "visit_contact_mode": {"term_uid": "VisitContactMode_0001"},
    }
    response = api_client.post(f"/studies/{_study.uid}/study-visits", json=inputs)
    assert_response_status_code(response, 201)
    visit_uid = response.json()["uid"]
    assert response.json()["study_epoch_uid"] == _epoch.uid

    # Edit to remove epoch
    edit_inputs = {
        "uid": visit_uid,
        "study_epoch_uid": None,
        "visit_sublabel_reference": None,
        "visit_type": {"term_uid": "VisitType_0003"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 10,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
        "visit_contact_mode": {"term_uid": "VisitContactMode_0001"},
    }
    response = api_client.patch(
        f"/studies/{_study.uid}/study-visits/{visit_uid}", json=edit_inputs
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_epoch_uid"] is None
    assert res["study_epoch"] is None


def test_edit_visit_to_add_epoch(api_client):
    """Editing a visit without epoch to add one should work."""
    _study = TestUtils.create_study(project_number=project.project_number)
    _epoch = create_study_epoch("EpochSubType_0001", study_uid=_study.uid)

    # Anchor visit required for relative time references
    anchor_inputs = {
        "study_epoch_uid": _epoch.uid,
        "visit_sublabel_reference": None,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
        "visit_contact_mode": {"term_uid": "VisitContactMode_0001"},
    }
    response = api_client.post(
        f"/studies/{_study.uid}/study-visits", json=anchor_inputs
    )
    assert_response_status_code(response, 201)

    # Create a visit without epoch
    inputs = {
        "study_epoch_uid": None,
        "visit_sublabel_reference": None,
        "visit_type": {"term_uid": "VisitType_0003"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 10,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
        "visit_contact_mode": {"term_uid": "VisitContactMode_0001"},
    }
    response = api_client.post(f"/studies/{_study.uid}/study-visits", json=inputs)
    assert_response_status_code(response, 201)
    visit_uid = response.json()["uid"]
    assert response.json()["study_epoch_uid"] is None

    # Edit to add epoch
    edit_inputs = {
        "uid": visit_uid,
        "study_epoch_uid": _epoch.uid,
        "visit_sublabel_reference": None,
        "visit_type": {"term_uid": "VisitType_0003"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 10,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
        "visit_contact_mode": {"term_uid": "VisitContactMode_0001"},
    }
    response = api_client.patch(
        f"/studies/{_study.uid}/study-visits/{visit_uid}", json=edit_inputs
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_epoch_uid"] == _epoch.uid
    assert res["study_epoch"] is not None


def test_visit_without_epoch_included_in_soa(api_client):
    """A visit without epoch should still appear in all SoA layouts."""
    # Create a visit without epoch
    inputs = {
        "study_epoch_uid": None,
        "visit_type": {"term_uid": "VisitType_0003"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
        "time_value": 230,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data.copy()
    datadict.update(inputs)
    response = api_client.post(f"/studies/{study.uid}/study-visits", json=datadict)
    assert_response_status_code(response, 201)
    visit_without_epoch_uid = response.json()["uid"]

    # Check Protocol SoA - visit without epoch should be present
    response = api_client.get(
        f"/studies/{study.uid}/flowchart", params={"layout": "protocol"}
    )
    assert_response_status_code(response, 200)
    soa_json = response.json()
    all_uids = _extract_visit_uids_from_soa(soa_json)
    assert visit_without_epoch_uid in all_uids

    # Check Detailed SoA
    response = api_client.get(
        f"/studies/{study.uid}/flowchart", params={"layout": "detailed"}
    )
    assert_response_status_code(response, 200)
    soa_json = response.json()
    all_uids = _extract_visit_uids_from_soa(soa_json)
    assert visit_without_epoch_uid in all_uids

    # Check Operational SoA
    response = api_client.get(
        f"/studies/{study.uid}/flowchart", params={"layout": "operational"}
    )
    assert_response_status_code(response, 200)
    soa_json = response.json()
    all_uids = _extract_visit_uids_from_soa(soa_json)
    assert visit_without_epoch_uid in all_uids


def _extract_visit_uids_from_soa(soa_json: dict[str, Any]) -> set[str]:
    """Extract all visit UIDs referenced in SoA table rows."""
    uids = set()
    for row in soa_json.get("rows", []):
        for cell in row.get("cells", []):
            for ref in cell.get("refs", []):
                if ref.get("type") == "StudyVisit":
                    uids.add(ref["uid"])
    return uids
