"""
Tests for /studies/{study_uid}/study-activities endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import json
import logging
from datetime import datetime, timezone
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
)
from clinical_mdr_api.models.clinical_programmes.clinical_programme import (
    ClinicalProgramme,
)
from clinical_mdr_api.models.concepts.activities.activity import Activity
from clinical_mdr_api.models.concepts.activities.activity_group import ActivityGroup
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
)
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
)
from clinical_mdr_api.models.controlled_terminologies import ct_term
from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.study_selections.study_visit import StudyVisit
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_SUB_GROUPS,
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    get_codelist_with_term_cypher,
)
from clinical_mdr_api.tests.integration.utils.factory_activity import (
    create_study_activity,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
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
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import REQUESTED_LIBRARY_NAME

log = logging.getLogger(__name__)

study: Study
study_activity_uid: str
epoch_uid: str
DAYUID: str
visits_basic_data: str
activity_instruction: str
general_activity_group: ActivityGroup
randomisation_activity_subgroup: ActivitySubGroup
randomized_activity: Activity
randomized_activity_instance: ActivityInstance
generic_activity_instance_class: ActivityInstanceClass
body_mes_activity: Activity
body_measurements_activity_subgroup: ActivitySubGroup
weight_activity: Activity
clinical_programme: ClinicalProgramme
project: Project
initial_ct_term_study_standard_test: ct_term.CTTerm
generic_study_visit: StudyVisit
term_efficacy_uid: str
informed_consent_uid: str


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studyactivityapi"
    inject_and_clear_db(db_name)
    global study
    study = inject_base_data()

    db.cypher_query(STARTUP_ACTIVITY_GROUPS)
    db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
    db.cypher_query(STARTUP_ACTIVITIES)
    global term_efficacy_uid
    term_efficacy_uid = "term_efficacy_uid"
    db.cypher_query(
        get_codelist_with_term_cypher(
            "EFFICACY", "Flowchart Group", term_uid=term_efficacy_uid
        )
    )
    global informed_consent_uid
    informed_consent_uid = "informed_consent_uid"
    db.cypher_query(
        get_codelist_with_term_cypher(
            "SAFETY", "Flowchart Group", term_uid=informed_consent_uid
        )
    )
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
    create_library_data()
    create_study_visit_codelists(create_unit_definitions=False)
    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=study.uid)
    global epoch_uid
    epoch_uid = study_epoch.uid
    global DAYUID
    DAYUID = get_unit_uid_by_name("day")
    global visits_basic_data
    visits_basic_data = generate_default_input_data_for_visit().copy()

    # Create Template Parameter
    TestUtils.create_template_parameter("TextValue")
    TestUtils.create_template_parameter("StudyActivityInstruction")

    text_value_1 = TestUtils.create_text_value()

    activity_group = TestUtils.create_activity_group(name="test activity group")
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="test activity subgroup", activity_groups=[activity_group.uid]
    )
    activity = TestUtils.create_activity(
        name="test activity",
        library_name="Sponsor",
        activity_groups=[activity_group.uid],
        activity_subgroups=[activity_subgroup.uid],
    )

    indications_library_name = "SNOMED"
    indications_codelist = TestUtils.create_dictionary_codelist(
        name="DiseaseDisorder", library_name=indications_library_name
    )
    dictionary_term_indication = TestUtils.create_dictionary_term(
        codelist_uid=indications_codelist.codelist_uid,
        library_name=indications_library_name,
    )

    activity_instruction_template = TestUtils.create_activity_instruction_template(
        name="Default name with [TextValue]",
        guidance_text="Default guidance text",
        library_name="Sponsor",
        indication_uids=[dictionary_term_indication.term_uid],
        activity_uids=[activity.uid],
        activity_group_uids=[activity_group.uid],
        activity_subgroup_uids=[activity_subgroup.uid],
    )

    # Create some activity_instructions
    global activity_instruction
    activity_instruction = TestUtils.create_activity_instruction(
        activity_instruction_template_uid=activity_instruction_template.uid,
        library_name="Sponsor",
        parameter_terms=[
            MultiTemplateParameterTerm(
                position=1,
                conjunction="",
                terms=[
                    IndexedTemplateParameterTerm(
                        index=1,
                        name=text_value_1.name,
                        uid=text_value_1.uid,
                        type="TextValue",
                    )
                ],
            )
        ],
        approve=True,
    )
    global general_activity_group
    global randomisation_activity_subgroup
    global randomized_activity
    global body_mes_activity
    global body_measurements_activity_subgroup
    global weight_activity

    general_activity_group = TestUtils.create_activity_group(name="General")
    randomisation_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Randomisation", activity_groups=[general_activity_group.uid]
    )
    randomized_activity = TestUtils.create_activity(
        name="Randomized",
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )
    global generic_activity_instance_class
    generic_activity_instance_class = TestUtils.create_activity_instance_class(
        name="Randomized activity instance class"
    )
    global randomized_activity_instance
    randomized_activity_instance = TestUtils.create_activity_instance(
        name="Randomized activity instance",
        activity_instance_class_uid=generic_activity_instance_class.uid,
        name_sentence_case="randomized activity instance",
        topic_code="randomized activity instance topic code",
        adam_param_code="randomized adam_param_code",
        is_required_for_activity=True,
        activities=[randomized_activity.uid],
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        activity_items=[],
    )
    body_mes_activity = TestUtils.create_activity(
        name="Body Measurement activity",
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )
    body_measurements_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Body Measurements", activity_groups=[general_activity_group.uid]
    )
    weight_activity = TestUtils.create_activity(
        name="Weight",
        activity_subgroups=[
            body_measurements_activity_subgroup.uid,
            randomisation_activity_subgroup.uid,
        ],
        activity_groups=[general_activity_group.uid, general_activity_group.uid],
        library_name="Sponsor",
    )
    global clinical_programme
    global project
    clinical_programme = TestUtils.create_clinical_programme(name="SoA CP")
    project = TestUtils.create_project(
        name="Project for SoA",
        project_number="1234",
        description="Base project",
        clinical_programme_uid=clinical_programme.uid,
    )

    catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    # Create a study selection
    ct_term_codelist = create_codelist(
        "Flowchart Group", "CTCodelist_Name", catalogue_name, library_name
    )

    # create visit
    inputs = {
        "study_uid": study.uid,
        "study_epoch_uid": study_epoch.uid,
        "visit_type_uid": "VisitType_0001",
        "show_visit": True,
        "time_reference_uid": "VisitSubType_0005",
        "time_value": 100,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    global generic_study_visit
    generic_study_visit = TestUtils.create_study_visit(**datadict)

    global initial_ct_term_study_standard_test
    ct_term_name = "Flowchart Group Name"
    ct_term_start_date = datetime(2020, 3, 25, tzinfo=timezone.utc)
    initial_ct_term_study_standard_test = TestUtils.create_ct_term(
        codelist_uid=ct_term_codelist.codelist_uid,
        name_submission_value=ct_term_name,
        sponsor_preferred_name=ct_term_name,
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=ct_term_start_date,
        approve=True,
    )

    # patch the date of the latest HAS_VERSION FINAL relationship so it can be detected by the selected study_standard_Version
    params = {
        "uid": initial_ct_term_study_standard_test.term_uid,
        "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
    }
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTTermNameRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        n.uid =$uid AND EXISTS((ct_name)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )

    yield


def test_activity_modify_actions_on_locked_study(api_client):
    global study_activity_uid

    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": "activity_root1",
            "activity_subgroup_uid": "activity_subgroup_root1",
            "activity_group_uid": "activity_group_root1",
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    res = response.json()
    study_activity_uid = res["study_activity_uid"]
    assert_response_status_code(response, 201)

    # get all activities
    response = api_client.get(
        f"/studies/{study.uid}/study-activities/audit-trail/",
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
        json={"change_description": "Lock 1"},
    )
    assert_response_status_code(response, 201)

    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": "activity_root2",
            "activity_subgroup_uid": "activity_subgroup_root2",
            "activity_group_uid": "activity_group_root2",
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert res["message"] == f"Study with UID '{study.uid}' is locked."
    # edit activity
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}",
        json={"soa_group_term_uid": term_efficacy_uid},
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-activities/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert old_res == res


def test_study_activity_with_study_soa_group_relationship(api_client):
    # get specific study activity
    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["study_soa_group"]["soa_group_term_uid"] == term_efficacy_uid
    before_unlock = res

    # get study activity headers
    response = api_client.get(
        f"/studies/{study.uid}/study-activities/headers?field_name=study_soa_group.soa_group_term_uid",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == [term_efficacy_uid]

    # Unlock -- Study remain unlocked
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert_response_status_code(response, 200)

    # edit study activity
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}",
        json={
            "activity_uid": "activity_root2",
            "soa_group_term_uid": informed_consent_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["study_soa_group"]["soa_group_term_uid"] == informed_consent_uid

    # get all activities of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-activities?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock["study_version"] = mock.ANY
    assert res["items"][0] == before_unlock

    # get specific study activity of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == before_unlock

    # get study activity headers of specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-activities/headers?field_name=study_soa_group.soa_group_term_uid&study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == [term_efficacy_uid]

    # get all activities
    response = api_client.get(
        f"/studies/{study.uid}/study-activities",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res["items"][0]["study_soa_group"]["soa_group_term_uid"] == informed_consent_uid
    )

    # get specific study activity
    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["study_soa_group"]["soa_group_term_uid"] == informed_consent_uid

    # get study activity headers
    response = api_client.get(
        f"/studies/{study.uid}/study-activities/headers?field_name=study_soa_group.soa_group_term_uid",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == [informed_consent_uid]


def test_update_library_items_of_relationship_to_value_nodes(api_client):
    """
    Test that the StudyActivity selection remains connected to the specific Value node even if the Value node is not latest anymore.

    StudyActivities connected to value nodes:
    - ActivityValue
    """

    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    library_activity_uid = res["activity"]["uid"]
    library_activity_grouping_subgroup_uid = res["activity"]["activity_groupings"][0][
        "activity_subgroup_uid"
    ]
    library_activity_grouping_group_uid = res["activity"]["activity_groupings"][0][
        "activity_group_uid"
    ]
    initial_activity_name = res["activity"]["name"]

    text_value_2_name = "2ndname"
    # change activity name and approve the version
    response = api_client.post(
        f"/concepts/activities/activities/{library_activity_uid}/versions",
    )
    res = response.json()
    assert_response_status_code(response, 201)
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{library_activity_grouping_subgroup_uid}/versions",
    )
    res = response.json()
    assert_response_status_code(response, 201)

    response = api_client.patch(
        f"/concepts/activities/activities/{library_activity_uid}",
        json={
            "change_description": "Change to have a new version of the activity so we can be sure that the study activity won't have any update",
            "name": text_value_2_name,
            "name_sentence_case": text_value_2_name,
            "guidance_text": "don't know",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)

    response = api_client.patch(
        f"/concepts/activities/activity-sub-groups/{library_activity_grouping_subgroup_uid}",
        json={
            "change_description": "Change to have a new version of the activity so we can be sure that the study activity won't have any update",
            "name": text_value_2_name,
            "name_sentence_case": text_value_2_name,
            "guidance_text": "don't know",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activities/{library_activity_uid}/approvals"
    )
    res = response.json()
    assert_response_status_code(response, 201)

    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{library_activity_grouping_subgroup_uid}/approvals"
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # check that the Library item has been changed
    response = api_client.get(f"/concepts/activities/activities/{library_activity_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["name"] == text_value_2_name
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{library_activity_grouping_subgroup_uid}"
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["name"] == text_value_2_name

    # check that the StudySelection StudyActivity hasn't been updated
    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["activity"]["name"] == initial_activity_name
    assert library_activity_grouping_subgroup_uid in [
        group["activity_subgroup_uid"]
        for group in res["activity"]["activity_groupings"]
    ]
    assert library_activity_grouping_group_uid in [
        group["activity_group_uid"] for group in res["activity"]["activity_groupings"]
    ]

    # change activity name and approve the version
    response = api_client.post(
        f"/concepts/activities/activities/{library_activity_uid}/versions",
    )
    res = response.json()
    assert_response_status_code(response, 201)
    response = api_client.patch(
        f"/concepts/activities/activities/{library_activity_uid}",
        json={
            "change_description": "returning the name to the initial one to continue with tests",
            "name": text_value_2_name,
            "name_sentence_case": text_value_2_name,
            "guidance_text": "don't know",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activities/{library_activity_uid}/approvals"
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # change activity name and approve the version
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{library_activity_grouping_subgroup_uid}/versions",
    )
    res = response.json()
    assert_response_status_code(response, 201)
    response = api_client.patch(
        f"/concepts/activities/activity-sub-groups/{library_activity_grouping_subgroup_uid}",
        json={
            "change_description": "returning the name to the initial one to continue with tests",
            "name": text_value_2_name,
            "name_sentence_case": text_value_2_name,
            "guidance_text": "don't know",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{library_activity_grouping_subgroup_uid}/approvals"
    )
    res = response.json()
    assert_response_status_code(response, 201)


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
def test_get_study_activities_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-activities"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())


def test_delete_study_activity(api_client):
    response = api_client.delete(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}",
    )
    assert_response_status_code(response, 204)


def test_cascade_delete_on_activities_schedules(api_client):
    study_for_cascade = TestUtils.create_study(project_number=project.project_number)
    TestUtils.set_study_standard_version(study_uid=study_for_cascade.uid)
    response = api_client.post(
        f"/studies/{study_for_cascade.uid}/study-activities",
        json={
            "activity_uid": "activity_root1",
            "activity_subgroup_uid": "activity_subgroup_root1",
            "activity_group_uid": "activity_group_root1",
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    study_activity_uid = res["study_activity_uid"]

    response = api_client.get(
        f"/studies/{study_for_cascade.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    study_activity_instances = res["items"]
    assert len(study_activity_instances) == 1
    study_activity_instance_uid = study_activity_instances[0][
        "study_activity_instance_uid"
    ]
    assert study_activity_instances[0]["study_activity_uid"] == study_activity_uid
    assert study_activity_instances[0]["activity"]["uid"] == "activity_root1"
    assert study_activity_instances[0]["activity_instance"] is None
    assert (
        study_activity_instances[0]["show_activity_instance_in_protocol_flowchart"]
        is False
    )

    study_epoch = create_study_epoch(
        "EpochSubType_0001", study_uid=study_for_cascade.uid
    )
    # create visit
    inputs = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type_uid": "VisitType_0001",
        "show_visit": True,
        "time_reference_uid": "VisitSubType_0005",
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{study_for_cascade.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    study_visit_uid = res["uid"]
    assert_response_status_code(response, 201)

    # add activity schedule
    response = api_client.post(
        f"/studies/{study_for_cascade.uid}/study-activity-schedules",
        json={
            "study_activity_uid": study_activity_uid,
            "study_visit_uid": study_visit_uid,
        },
    )
    res = response.json()
    assert res["study_activity_uid"] == study_activity_uid
    assert res["study_activity_uid"] == study_activity_uid
    assert_response_status_code(response, 201)

    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study_for_cascade.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)
    # Lock
    response = api_client.post(
        f"/studies/{study_for_cascade.uid}/locks",
        json={"change_description": "Lock 1"},
    )
    assert_response_status_code(response, 201)
    # Unlock -- Study remain unlocked
    response = api_client.delete(f"/studies/{study_for_cascade.uid}/locks")
    assert_response_status_code(response, 200)
    # delete activity
    response = api_client.delete(
        f"/studies/{study_for_cascade.uid}/study-activities/{study_activity_uid}",
    )
    assert_response_status_code(response, 204)

    # Assert that StudyActivityInstance is removed when StudyActivity is removed
    response = api_client.get(
        f"/studies/{study_for_cascade.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    study_activity_instances = res["items"]
    assert len(study_activity_instances) == 0

    # Assert that StudyActivityInstance is removed when StudyActivity is removed
    response = api_client.get(
        f"/studies/{study_for_cascade.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 404)

    # check if the activities schedules have been deleted
    response = api_client.get(
        f"/studies/{study_for_cascade.uid}/study-activity-schedules/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == []

    # clean visits from test
    response = api_client.delete(
        f"/studies/{study_for_cascade.uid}/study-visits/{study_visit_uid}",
    )
    assert_response_status_code(response, 204)


def test_maintain_outbound_rels(api_client):
    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": "activity_root1",
            "activity_subgroup_uid": "activity_subgroup_root1",
            "activity_group_uid": "activity_group_root1",
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    study_activity_uid = res["study_activity_uid"]

    # create visit
    inputs = {
        "study_epoch_uid": epoch_uid,
        "visit_type_uid": "VisitType_0001",
        "show_visit": True,
        "time_reference_uid": "VisitSubType_0005",
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
    assert_response_status_code(response, 201)
    study_visit_uid = res["uid"]

    # add activity schedule
    response = api_client.post(
        f"/studies/{study.uid}/study-activity-schedules",
        json={
            "study_activity_uid": study_activity_uid,
            "study_visit_uid": study_visit_uid,
        },
    )
    assert_response_status_code(response, 201)

    # add activity instruction
    response = api_client.post(
        f"/studies/{study.uid}/study-activity-instructions/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "activity_instruction_uid": activity_instruction.uid,
                    "study_activity_uid": study_activity_uid,
                },
            }
        ],
    )
    assert_response_status_code(response, 207)

    # patch visits to be sure that the outbound relationship (Visits-->ActivitySchedule) is maintained
    inputs = {
        "uid": study_visit_uid,
        "description": "new description",
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.patch(
        f"/studies/{study.uid}/study-visits/{study_visit_uid}",
        json=datadict,
    )
    assert_response_status_code(response, 200)

    # patch activities to be sure that the outbound relationship (Activity-->ActivitySchedule) is maintained
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}",
        json={
            "note": "new note",
        },
    )
    assert_response_status_code(response, 200)

    # check if the activities schedules maintained the trace to StudyVisits new version
    response = api_client.get(
        f"/studies/{study.uid}/study-activity-schedules/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res[0]["study_visit_uid"] == study_visit_uid
    assert res[0]["study_activity_uid"] == study_activity_uid

    # clean visits from test
    response = api_client.delete(
        f"/studies/{study.uid}/study-visits/{study_visit_uid}",
    )
    assert_response_status_code(response, 204)

    # check if the activities schedules were cascade deleted by StudyVisit deletion
    response = api_client.get(
        f"/studies/{study.uid}/study-activity-schedules/",
    )
    res = response.json()
    assert len(res) == 0

    # clean activities from test
    response = api_client.delete(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}",
    )
    assert_response_status_code(response, 204)

    # check if the activities instructions were cascade deleted by a StudyActivity deletion
    response = api_client.get(
        f"/studies/{study.uid}/study-activity-instructions/",
    )
    res = response.json()
    assert len(res) == 0


def test_versioning_on_activity_activity_instruction_activity_schedule_as_group(
    api_client,
):
    study_for_versioning = TestUtils.create_study(project_number=project.project_number)
    response = api_client.post(
        f"/studies/{study_for_versioning.uid}/study-activities",
        json={
            "activity_uid": "activity_root1",
            "activity_subgroup_uid": "activity_subgroup_root1",
            "activity_group_uid": "activity_group_root1",
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    study_activity_uid = res["study_activity_uid"]

    response = api_client.get(
        f"/studies/{study_for_versioning.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    study_activity_instances = res["items"]
    assert len(study_activity_instances) == 1
    assert study_activity_instances[0]["study_activity_uid"] == study_activity_uid
    assert study_activity_instances[0]["activity"]["uid"] == "activity_root1"
    assert study_activity_instances[0]["activity_instance"] is None
    assert (
        study_activity_instances[0]["show_activity_instance_in_protocol_flowchart"]
        is False
    )

    study_epoch = create_study_epoch(
        "EpochSubType_0001", study_uid=study_for_versioning.uid
    )
    # create visit
    inputs = {
        "study_epoch_uid": study_epoch.uid,
        "visit_type_uid": "VisitType_0001",
        "show_visit": True,
        "time_reference_uid": "VisitSubType_0005",
        "time_value": 0,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": True,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{study_for_versioning.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    study_visit_uid = res["uid"]

    # add activity schedule
    response = api_client.post(
        f"/studies/{study_for_versioning.uid}/study-activity-schedules",
        json={
            "study_activity_uid": study_activity_uid,
            "study_visit_uid": study_visit_uid,
        },
    )
    assert_response_status_code(response, 201)

    # add activity instruction
    response = api_client.post(
        f"/studies/{study_for_versioning.uid}/study-activity-instructions/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "activity_instruction_uid": activity_instruction.uid,
                    "study_activity_uid": study_activity_uid,
                },
            }
        ],
    )
    assert_response_status_code(response, 207)

    before_visits = api_client.get(
        f"/studies/{study_for_versioning.uid}/study-visits"
    ).json()
    before_activities = api_client.get(
        f"/studies/{study_for_versioning.uid}/study-activities"
    ).json()
    before_activity_schedules = api_client.get(
        f"/studies/{study_for_versioning.uid}/study-activity-schedules"
    ).json()
    before_activity_instructions = api_client.get(
        f"/studies/{study_for_versioning.uid}/study-activity-instructions"
    ).json()

    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study_for_versioning.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)
    # Set StudyStandardVersion before locking
    TestUtils.set_study_standard_version(study_uid=study_for_versioning.uid)

    # Lock
    response = api_client.post(
        f"/studies/{study_for_versioning.uid}/locks",
        json={"change_description": "Lock 1"},
    )
    assert_response_status_code(response, 201)

    # test cannot delete
    response = api_client.delete(
        f"/studies/{study_for_versioning.uid}/study-activities/{study_activity_uid}",
    )
    assert_response_status_code(response, 400)
    assert (
        response.json()["message"]
        == f"Study with UID '{study_for_versioning.uid}' is locked."
    )

    # Unlock -- Study remain unlocked
    response = api_client.delete(f"/studies/{study_for_versioning.uid}/locks")
    assert_response_status_code(response, 200)

    # patch visits to be sure that the outbound relationship (Visits-->ActivitySchedule) is maintained
    inputs = {
        "uid": study_visit_uid,
        "description": "new description",
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.patch(
        f"/studies/{study_for_versioning.uid}/study-visits/{study_visit_uid}",
        json=datadict,
    )
    assert_response_status_code(response, 200)

    # patch activities to be sure that the outbound relationship (Activity-->ActivitySchedule) is maintained
    response = api_client.patch(
        f"/studies/{study_for_versioning.uid}/study-activities/{study_activity_uid}",
        json={
            "note": "new note",
        },
    )
    assert_response_status_code(response, 200)

    # check if the activities schedules maintained the trace to StudyVisits new version
    response = api_client.get(
        f"/studies/{study_for_versioning.uid}/study-activity-schedules/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res[0]["study_visit_uid"] == study_visit_uid
    assert res[0]["study_activity_uid"] == study_activity_uid

    # clean visits from test
    response = api_client.delete(
        f"/studies/{study_for_versioning.uid}/study-visits/{study_visit_uid}",
    )
    assert_response_status_code(response, 204)

    # check if the activities schedules were cascade deleted by StudyVisit deletion
    response = api_client.get(
        f"/studies/{study_for_versioning.uid}/study-activity-schedules/",
    )
    res = response.json()
    assert len(res) == 0

    # clean activities from test
    response = api_client.delete(
        f"/studies/{study_for_versioning.uid}/study-activities/{study_activity_uid}",
    )
    assert_response_status_code(response, 204)

    # check if the activities instructions were cascade deleted by a StudyActivity deletion
    response = api_client.get(
        f"/studies/{study_for_versioning.uid}/study-activity-instructions/",
    )
    res = response.json()
    assert len(res) == 0

    # get all
    for i, _ in enumerate(before_visits["items"]):
        before_visits["items"][i]["study_version"] = mock.ANY
        for j in before_visits["items"][i]:
            if isinstance(before_visits["items"][i][j], dict):
                before_visits["items"][i][j]["queried_effective_date"] = mock.ANY
    assert (
        before_visits
        == api_client.get(
            f"/studies/{study_for_versioning.uid}/study-visits?study_value_version=1"
        ).json()
    )
    for i, _ in enumerate(before_activities["items"]):
        before_activities["items"][i]["study_version"] = mock.ANY
        for j in before_visits["items"][i]:
            if isinstance(before_visits["items"][i][j], dict):
                before_visits["items"][i][j]["queried_effective_date"] = mock.ANY
    assert (
        before_activities
        == api_client.get(
            f"/studies/{study_for_versioning.uid}/study-activities?study_value_version=1"
        ).json()
    )
    for i, _ in enumerate(before_activity_schedules):
        before_activity_schedules[i]["study_version"] = mock.ANY
        for j in before_visits["items"][i]:
            if isinstance(before_visits["items"][i][j], dict):
                before_visits["items"][i][j]["queried_effective_date"] = mock.ANY
    assert (
        before_activity_schedules
        == api_client.get(
            f"/studies/{study_for_versioning.uid}/study-activity-schedules?study_value_version=1"
        ).json()
    )
    for i, _ in enumerate(before_activity_instructions):
        before_activity_instructions[i]["study_version"] = mock.ANY
        for j in before_visits["items"][i]:
            if isinstance(before_visits["items"][i][j], dict):
                before_visits["items"][i][j]["queried_effective_date"] = mock.ANY
    assert (
        before_activity_instructions
        == api_client.get(
            f"/studies/{study_for_versioning.uid}/study-activity-instructions?study_value_version=1"
        ).json()
    )


def test_reusing_study_activity_group_study_activity_subgroup_study_soa_group(
    api_client,
):
    activity_group_1 = TestUtils.create_activity_group(name="activity_group_1")
    activity_group_2 = TestUtils.create_activity_group(name="activity_group_2")
    activity_subgroup_1 = TestUtils.create_activity_subgroup(
        name="activity_subgroup_1", activity_groups=[activity_group_1.uid]
    )
    activity_subgroup_2 = TestUtils.create_activity_subgroup(
        name="activity_subgroup_2",
        activity_groups=[activity_group_1.uid, activity_group_2.uid],
    )
    activity_1 = TestUtils.create_activity(
        name="activity_1",
        library_name="Sponsor",
        activity_groups=[activity_group_1.uid],
        activity_subgroups=[activity_subgroup_1.uid],
    )
    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": activity_1.uid,
            "activity_subgroup_uid": activity_subgroup_1.uid,
            "activity_group_uid": activity_group_1.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    study_activity_1_uid = res["study_activity_uid"]

    activity_2 = TestUtils.create_activity(
        name="activity_2",
        library_name="Sponsor",
        activity_groups=[activity_group_1.uid],
        activity_subgroups=[activity_subgroup_1.uid],
    )
    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": activity_2.uid,
            "activity_subgroup_uid": activity_subgroup_1.uid,
            "activity_group_uid": activity_group_1.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    study_activity_2_uid = res["study_activity_uid"]

    # Perform double SoAGroup update to verify if we are successfully reusing nodes after such operation
    previous_soa_group_name = res["study_soa_group"]["soa_group_term_name"]
    new_soa_group_name = "SAFETY"
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{study_activity_2_uid}",
        json={
            "soa_group_term_uid": informed_consent_uid,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_soa_group"]["soa_group_term_name"] == new_soa_group_name
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{study_activity_2_uid}",
        json={
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_soa_group"]["soa_group_term_name"] == previous_soa_group_name

    activity_3 = TestUtils.create_activity(
        name="activity_3",
        library_name="Sponsor",
        activity_groups=[activity_group_1.uid],
        activity_subgroups=[activity_subgroup_2.uid],
    )
    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": activity_3.uid,
            "activity_subgroup_uid": activity_subgroup_2.uid,
            "activity_group_uid": activity_group_1.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    study_activity_3_uid = res["study_activity_uid"]

    activity_4 = TestUtils.create_activity(
        name="activity_4",
        library_name="Sponsor",
        activity_groups=[activity_group_2.uid],
        activity_subgroups=[activity_subgroup_2.uid],
    )
    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": activity_4.uid,
            "activity_subgroup_uid": activity_subgroup_2.uid,
            "activity_group_uid": activity_group_2.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    study_activity_4_uid = res["study_activity_uid"]

    activity_5 = TestUtils.create_activity(
        name="activity_5",
        library_name="Sponsor",
        activity_groups=[activity_group_2.uid],
        activity_subgroups=[activity_subgroup_2.uid],
    )
    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": activity_5.uid,
            "activity_subgroup_uid": activity_subgroup_2.uid,
            "activity_group_uid": activity_group_2.uid,
            "soa_group_term_uid": informed_consent_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    study_activity_5_uid = res["study_activity_uid"]

    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_1_uid}",
    )
    assert_response_status_code(response, 200)
    study_activity_1 = response.json()

    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_2_uid}",
    )
    assert_response_status_code(response, 200)
    study_activity_2 = response.json()

    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_3_uid}",
    )
    assert_response_status_code(response, 200)
    study_activity_3 = response.json()

    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_4_uid}",
    )
    assert_response_status_code(response, 200)
    study_activity_4 = response.json()

    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_5_uid}",
    )
    assert_response_status_code(response, 200)
    study_activity_5 = response.json()

    # Compare SA1 and SA2
    # test reusing groups
    assert (
        study_activity_1["study_activity_group"]
        == study_activity_2["study_activity_group"]
    )
    # test reusing subgroups
    assert (
        study_activity_1["study_activity_subgroup"]
        == study_activity_2["study_activity_subgroup"]
    )
    # test reusing soa_group
    assert study_activity_1["study_soa_group"] == study_activity_2["study_soa_group"]

    # Compare SA2 and SA3
    # test reusing group
    assert (
        study_activity_2["study_activity_group"]
        == study_activity_3["study_activity_group"]
    )
    # test reusing soa_group
    assert study_activity_2["study_soa_group"] == study_activity_3["study_soa_group"]

    # test different subgroups
    assert (
        study_activity_2["study_activity_subgroup"]
        != study_activity_3["study_activity_subgroup"]
    )

    # Compare SA3 and SA4
    # test reuse soa_group
    assert study_activity_3["study_soa_group"] == study_activity_4["study_soa_group"]
    # test different groups
    assert (
        study_activity_3["study_activity_group"]
        != study_activity_4["study_activity_group"]
    )
    # test different subgroups
    assert (
        study_activity_3["study_activity_subgroup"]
        != study_activity_4["study_activity_subgroup"]
    )

    # Compare SA4 and SA5
    # test different soa_group
    assert study_activity_4["study_soa_group"] != study_activity_5["study_soa_group"]
    # test different groups
    assert (
        study_activity_4["study_activity_group"]
        != study_activity_5["study_activity_group"]
    )
    # test different subgroups
    assert (
        study_activity_4["study_activity_subgroup"]
        != study_activity_5["study_activity_subgroup"]
    )

    response = api_client.delete(
        f"/studies/{study.uid}/study-activities/{study_activity_1_uid}",
    )
    assert_response_status_code(response, 204)

    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_2_uid}",
    )
    assert_response_status_code(response, 200)
    study_activity_2 = response.json()
    assert (
        study_activity_2["study_activity_group"]["activity_group_uid"]
        == activity_group_1.uid
    )
    assert (
        study_activity_2["study_activity_subgroup"]["activity_subgroup_uid"]
        == activity_subgroup_1.uid
    )
    response = api_client.patch(
        f"/studies/{study.uid}/study-activity-subgroups/{study_activity_2['study_activity_subgroup']['study_activity_subgroup_uid']}",
        json={
            "show_activity_subgroup_in_protocol_flowchart": False,
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.patch(
        f"/studies/{study.uid}/study-activity-groups/{study_activity_2['study_activity_group']['study_activity_group_uid']}",
        json={
            "show_activity_group_in_protocol_flowchart": False,
        },
    )
    assert_response_status_code(response, 200)

    # check that StudySoAGroup change will also change assigned StudyActivityGroup and StudyActivitySubGroup
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{study_activity_5_uid}",
        json={
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_5_uid}",
    )
    assert_response_status_code(response, 200)
    study_activity_5 = response.json()
    # Compare SA4 and SA5 after patching SA5 SoAGroup it should be the same
    # test different soa_group
    assert study_activity_4["study_soa_group"] == study_activity_5["study_soa_group"]
    # test different groups
    assert (
        study_activity_4["study_activity_group"]
        == study_activity_5["study_activity_group"]
    )
    # test different subgroups
    assert (
        study_activity_4["study_activity_subgroup"]
        == study_activity_5["study_activity_subgroup"]
    )


def test_reusing_study_activity_group_study_activity_subgroup_when_study_soa_group_is_changed(
    api_client,
):
    test_study = TestUtils.create_study(project_number=project.project_number)

    another_randomized_activity = TestUtils.create_activity(
        name="Another randomized",
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": randomized_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    randomized_sa = response.json()

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": another_randomized_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": informed_consent_uid,
        },
    )
    assert_response_status_code(response, 201)
    another_randomized_sa = response.json()

    assert (
        another_randomized_sa["study_soa_group"]["study_soa_group_uid"]
        != randomized_sa["study_soa_group"]["study_soa_group_uid"]
    )
    assert (
        another_randomized_sa["study_activity_group"]["study_activity_group_uid"]
        != randomized_sa["study_activity_group"]["study_activity_group_uid"]
    )
    assert (
        another_randomized_sa["study_activity_subgroup"]["study_activity_subgroup_uid"]
        != randomized_sa["study_activity_subgroup"]["study_activity_subgroup_uid"]
    )

    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activities/{another_randomized_sa['study_activity_uid']}",
        json={
            "soa_group_term_uid": term_efficacy_uid,
            # when patching SoAGroup we send activity_group and activity_subgroup from UI as well
            # and that made the API to not update StudyActivityGroup/StudyActivitySubGroup when changing SoAGroup
            # such case should be also handled by the API
            "activity_group_uid": general_activity_group.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
        },
    )
    assert_response_status_code(response, 200)
    another_randomized_sa = response.json()
    assert (
        another_randomized_sa["study_soa_group"]["study_soa_group_uid"]
        == randomized_sa["study_soa_group"]["study_soa_group_uid"]
    )
    assert (
        another_randomized_sa["study_activity_group"]["study_activity_group_uid"]
        == randomized_sa["study_activity_group"]["study_activity_group_uid"]
    )
    assert (
        another_randomized_sa["study_activity_subgroup"]["study_activity_subgroup_uid"]
        == randomized_sa["study_activity_subgroup"]["study_activity_subgroup_uid"]
    )


def test_modify_visibility_flag_in_protocol_flowchart(
    api_client,
):
    activity_group = TestUtils.create_activity_group(name="AG")
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="AS", activity_groups=[activity_group.uid]
    )
    activity = TestUtils.create_activity(
        name="Act",
        library_name="Sponsor",
        activity_groups=[activity_group.uid],
        activity_subgroups=[activity_subgroup.uid],
    )
    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": activity.uid,
            "activity_subgroup_uid": activity_subgroup.uid,
            "activity_group_uid": activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    study_activity_uid = res["study_activity_uid"]
    study_activity_subgroup_uid = res["study_activity_subgroup"][
        "study_activity_subgroup_uid"
    ]
    study_activity_group_uid = res["study_activity_group"]["study_activity_group_uid"]
    study_soa_group_uid = res["study_soa_group"]["study_soa_group_uid"]
    assert res["show_activity_in_protocol_flowchart"] is False
    assert res["show_activity_subgroup_in_protocol_flowchart"] is True
    assert res["show_activity_group_in_protocol_flowchart"] is True
    assert res["show_soa_group_in_protocol_flowchart"] is False

    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}",
        json={
            "show_activity_in_protocol_flowchart": True,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["show_activity_in_protocol_flowchart"] is True

    response = api_client.patch(
        f"/studies/{study.uid}/study-activity-subgroups/{study_activity_subgroup_uid}",
        json={
            "show_activity_subgroup_in_protocol_flowchart": False,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["show_activity_subgroup_in_protocol_flowchart"] is False

    response = api_client.patch(
        f"/studies/{study.uid}/study-activity-groups/{study_activity_group_uid}",
        json={
            "show_activity_group_in_protocol_flowchart": False,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["show_activity_group_in_protocol_flowchart"] is False

    response = api_client.patch(
        f"/studies/{study.uid}/study-soa-groups/{study_soa_group_uid}",
        json={
            "show_soa_group_in_protocol_flowchart": True,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["show_soa_group_in_protocol_flowchart"] is True

    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["show_activity_in_protocol_flowchart"] is True
    assert res["show_activity_subgroup_in_protocol_flowchart"] is False
    assert res["show_activity_group_in_protocol_flowchart"] is False
    assert res["show_soa_group_in_protocol_flowchart"] is True


def test_detailed_soa_history_page(api_client):
    study_for_soa = TestUtils.create_study(project_number=project.project_number)
    visit_to_create = generate_default_input_data_for_visit().copy()
    visit_to_create.update({"time_value": 10})
    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=study_for_soa.uid)
    first_visit = TestUtils.create_study_visit(
        study_uid=study_for_soa.uid, study_epoch_uid=study_epoch.uid, **visit_to_create
    )
    # Randomized Study Activity
    sa_randomized = create_study_activity(
        study_uid=study_for_soa.uid,
        activity_uid=randomized_activity.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    randomized_sas = TestUtils.create_study_activity_schedule(
        study_uid=study_for_soa.uid,
        study_activity_uid=sa_randomized.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )
    response = api_client.delete(
        f"/studies/{study_for_soa.uid}/study-activity-schedules/{randomized_sas.study_activity_schedule_uid}",
    )
    assert_response_status_code(response, 204)
    response = api_client.patch(
        f"/studies/{study_for_soa.uid}/study-activities/{sa_randomized.study_activity_uid}",
        json={"show_activity_in_protocol_flowchart": True},
    )
    assert_response_status_code(response, 200)
    response = api_client.get(
        f"/studies/{study_for_soa.uid}/detailed-soa-history",
        params={"page_size": 0, "total_count": True},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    total_count = res["total"]
    res = res["items"]
    assert len(res) == 7
    assert total_count == 7
    assert res[0]["object_type"] == "visibility flag"
    assert (
        res[0]["description"]
        == f"EFFICACY/{general_activity_group.name}/{randomisation_activity_subgroup.name}/{randomized_activity.name} true"
    )
    assert res[0]["action"] == "Edit"
    assert res[1]["object_type"] == "schedule"
    assert (
        res[1]["description"]
        == f"{randomized_activity.name} {first_visit.visit_short_name}"
    )
    assert res[1]["action"] == "Delete"
    assert res[2]["object_type"] == "schedule"
    assert (
        res[2]["description"]
        == f"{randomized_activity.name} {first_visit.visit_short_name}"
    )
    assert res[2]["action"] == "Create"
    assert res[3]["object_type"] == "visibility flag"
    assert (
        res[3]["description"]
        == f"EFFICACY/{general_activity_group.name}/{randomisation_activity_subgroup.name}/{randomized_activity.name} false"
    )
    assert res[3]["action"] == "Create"
    assert res[4]["object_type"] == "visibility flag"
    assert res[4]["description"] == f"EFFICACY/{general_activity_group.name} true"
    assert res[4]["action"] == "Create"
    assert res[5]["object_type"] == "visibility flag"
    assert (
        res[5]["description"]
        == f"EFFICACY/{general_activity_group.name}/{randomisation_activity_subgroup.name} true"
    )
    assert res[5]["action"] == "Create"
    assert res[6]["object_type"] == "visibility flag"
    assert res[6]["description"] == "EFFICACY false"
    assert res[6]["action"] == "Create"


def test_detailed_soa_export(api_client):
    study_for_export = TestUtils.create_study(project_number=project.project_number)
    visit_to_create = generate_default_input_data_for_visit().copy()
    visit_to_create.update({"time_value": 10})
    study_epoch = create_study_epoch(
        "EpochSubType_0001", study_uid=study_for_export.uid
    )
    first_visit = TestUtils.create_study_visit(
        study_uid=study_for_export.uid,
        study_epoch_uid=study_epoch.uid,
        **visit_to_create,
    )
    # Randomized Study Activity
    sa_randomized = create_study_activity(
        study_uid=study_for_export.uid,
        activity_uid=randomized_activity.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    TestUtils.create_study_activity_schedule(
        study_uid=study_for_export.uid,
        study_activity_uid=sa_randomized.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )
    sa_body_mes = create_study_activity(
        study_uid=study_for_export.uid,
        activity_uid=body_mes_activity.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    TestUtils.create_study_activity_schedule(
        study_uid=study_for_export.uid,
        study_activity_uid=sa_body_mes.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )
    # Weight Study Activity
    sa_weight = create_study_activity(
        study_uid=study_for_export.uid,
        activity_uid=weight_activity.uid,
        activity_subgroup_uid=body_measurements_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    TestUtils.create_study_activity_schedule(
        study_uid=study_for_export.uid,
        study_activity_uid=sa_weight.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )

    export_url = f"/studies/{study_for_export.uid}/detailed-soa-exports"
    response = api_client.get(export_url)
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == 3
    assert (
        res[0]["study_number"]
        == study_for_export.current_metadata.identification_metadata.study_number
    )
    assert res[0]["visit"] == first_visit.visit_short_name
    assert res[0]["epoch"] == study_epoch.epoch_ctterm.sponsor_preferred_name
    assert res[0]["activity"] == randomized_activity.name
    assert res[0]["activity_subgroup"] == randomisation_activity_subgroup.name
    assert res[0]["activity_group"] == general_activity_group.name
    assert res[0]["soa_group"] == "EFFICACY"
    assert (
        res[1]["study_number"]
        == study_for_export.current_metadata.identification_metadata.study_number
    )
    assert res[1]["visit"] == first_visit.visit_short_name
    assert res[1]["epoch"] == study_epoch.epoch_ctterm.sponsor_preferred_name
    assert res[1]["activity"] == body_mes_activity.name
    assert res[1]["activity_subgroup"] == randomisation_activity_subgroup.name
    assert res[1]["activity_group"] == general_activity_group.name
    assert res[1]["soa_group"] == "EFFICACY"
    assert (
        res[2]["study_number"]
        == study_for_export.current_metadata.identification_metadata.study_number
    )
    assert res[2]["visit"] == first_visit.visit_short_name
    assert res[2]["epoch"] == study_epoch.epoch_ctterm.sponsor_preferred_name
    assert res[2]["activity"] == weight_activity.name
    assert res[2]["activity_subgroup"] == body_measurements_activity_subgroup.name
    assert res[2]["activity_group"] == general_activity_group.name
    assert res[2]["soa_group"] == "EFFICACY"

    for export_format in [
        "text/csv",
        "text/xml",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]:
        exported_data = TestUtils.verify_exported_data_format(
            api_client, export_format, export_url
        )
        if export_format == "text/csv":
            assert "study_version" in str(exported_data.read())
            assert "LATEST" in str(exported_data.read())


def test_protocol_soa_html_with_time_units_and_study_versioning(api_client):
    study_for_export = TestUtils.create_study(project_number=project.project_number)
    visit_to_create = generate_default_input_data_for_visit().copy()
    visit_to_create.update({"time_value": 10})
    study_epoch = create_study_epoch(
        "EpochSubType_0001", study_uid=study_for_export.uid
    )
    first_visit = TestUtils.create_study_visit(
        study_uid=study_for_export.uid,
        study_epoch_uid=study_epoch.uid,
        **visit_to_create,
    )
    # Randomized Study Activity
    sa_randomized = create_study_activity(
        study_uid=study_for_export.uid,
        activity_uid=randomized_activity.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    TestUtils.create_study_activity_schedule(
        study_uid=study_for_export.uid,
        study_activity_uid=sa_randomized.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )
    sa_body_mes = create_study_activity(
        study_uid=study_for_export.uid,
        activity_uid=body_mes_activity.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    TestUtils.create_study_activity_schedule(
        study_uid=study_for_export.uid,
        study_activity_uid=sa_body_mes.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )
    # Weight Study Activity
    sa_weight = create_study_activity(
        study_uid=study_for_export.uid,
        activity_uid=weight_activity.uid,
        activity_subgroup_uid=body_measurements_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    TestUtils.create_study_activity_schedule(
        study_uid=study_for_export.uid,
        study_activity_uid=sa_weight.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )
    day_unit_definition = TestUtils.get_unit_by_uid(
        unit_uid=TestUtils.get_unit_uid_by_name(unit_name="day")
    )

    export_format = "text/html"
    export_url = f"/studies/{study_for_export.uid}/flowchart.html"
    previous_locked_exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, export_url
    ).text
    assert "Study week" in str(previous_locked_exported_data)

    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study_for_export.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)
    # Set StudyStandardVersion before locking
    TestUtils.set_study_standard_version(study_uid=study_for_export.uid)

    # Lock
    response = api_client.post(
        f"/studies/{study_for_export.uid}/locks",
        json={"change_description": "Lock 1"},
    )
    assert_response_status_code(response, 201)
    # Unlock -- Study remain unlocked
    response = api_client.delete(f"/studies/{study_for_export.uid}/locks")
    assert_response_status_code(response, 200)

    response = api_client.patch(
        f"/studies/{study_for_export.uid}/time-units?for_protocol_soa=true",
        json={"unit_definition_uid": day_unit_definition.uid},
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["time_unit_name"] == "day"

    export_format = "text/html"
    export_url = f"/studies/{study_for_export.uid}/flowchart.html"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, export_url
    ).text
    assert "Study day" in exported_data

    export_format = "text/html"
    export_url = f"/studies/{study_for_export.uid}/flowchart.html?study_value_version=1"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, export_url
    ).text
    assert exported_data == previous_locked_exported_data


def test_protocol_soa_export(api_client):
    study_for_export = TestUtils.create_study(project_number=project.project_number)
    visit_to_create = generate_default_input_data_for_visit().copy()
    visit_to_create.update({"time_value": 10})
    study_epoch = create_study_epoch(
        "EpochSubType_0001", study_uid=study_for_export.uid
    )
    first_visit = TestUtils.create_study_visit(
        study_uid=study_for_export.uid,
        study_epoch_uid=study_epoch.uid,
        **visit_to_create,
    )
    # Randomized Study Activity
    sa_randomized = create_study_activity(
        study_uid=study_for_export.uid,
        activity_uid=randomized_activity.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    response = api_client.patch(
        f"/studies/{study_for_export.uid}/study-activities/{sa_randomized.study_activity_uid}",
        json={"show_activity_in_protocol_flowchart": True},
    )
    assert_response_status_code(response, 200)
    TestUtils.create_study_activity_schedule(
        study_uid=study_for_export.uid,
        study_activity_uid=sa_randomized.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )
    sa_body_mes = create_study_activity(
        study_uid=study_for_export.uid,
        activity_uid=body_mes_activity.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    TestUtils.create_study_activity_schedule(
        study_uid=study_for_export.uid,
        study_activity_uid=sa_body_mes.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )
    # Weight Study Activity
    sa_weight = create_study_activity(
        study_uid=study_for_export.uid,
        activity_uid=weight_activity.uid,
        activity_subgroup_uid=body_measurements_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    response = api_client.patch(
        f"/studies/{study_for_export.uid}/study-activities/{sa_weight.study_activity_uid}",
        json={"show_activity_in_protocol_flowchart": True},
    )
    assert_response_status_code(response, 200)
    TestUtils.create_study_activity_schedule(
        study_uid=study_for_export.uid,
        study_activity_uid=sa_weight.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )

    export_url = f"/studies/{study_for_export.uid}/protocol-soa-exports"
    response = api_client.get(export_url)
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == 2
    assert (
        res[0]["study_number"]
        == study_for_export.current_metadata.identification_metadata.study_number
    )
    assert res[0]["visit"] == first_visit.visit_short_name
    assert res[0]["epoch"] == study_epoch.epoch_ctterm.sponsor_preferred_name
    assert res[0]["activity"] == randomized_activity.name
    assert res[0]["activity_subgroup"] == randomisation_activity_subgroup.name
    assert res[0]["activity_group"] == general_activity_group.name
    assert res[0]["soa_group"] == "EFFICACY"
    assert (
        res[1]["study_number"]
        == study_for_export.current_metadata.identification_metadata.study_number
    )
    assert (
        res[1]["study_number"]
        == study_for_export.current_metadata.identification_metadata.study_number
    )
    assert res[1]["visit"] == first_visit.visit_short_name
    assert res[1]["epoch"] == study_epoch.epoch_ctterm.sponsor_preferred_name
    assert res[1]["activity"] == weight_activity.name
    assert res[1]["activity_subgroup"] == body_measurements_activity_subgroup.name
    assert res[1]["activity_group"] == general_activity_group.name
    assert res[1]["soa_group"] == "EFFICACY"

    for export_format in [
        "text/csv",
        "text/xml",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]:
        exported_data = TestUtils.verify_exported_data_format(
            api_client, export_format, export_url
        )
        if export_format == "text/csv":
            assert "study_version" in str(exported_data.read())
            assert "LATEST" in str(exported_data.read())


def test_operational_soa_export(api_client):
    study_for_export = TestUtils.create_study(project_number=project.project_number)
    visit_to_create = generate_default_input_data_for_visit().copy()
    visit_to_create.update({"time_value": 10})
    study_epoch = create_study_epoch(
        "EpochSubType_0001", study_uid=study_for_export.uid
    )
    first_visit = TestUtils.create_study_visit(
        study_uid=study_for_export.uid,
        study_epoch_uid=study_epoch.uid,
        **visit_to_create,
    )

    TestUtils.create_activity_instance(
        name="Randomized activity instance 2",
        activity_instance_class_uid=generic_activity_instance_class.uid,
        name_sentence_case="randomized activity instance 2",
        topic_code="randomized activity instance topic code",
        adam_param_code="randomized adam_param_code",
        is_required_for_activity=True,
        activities=["Activity_000001"],
        activity_subgroups=["ActivitySubGroup_000001"],
        activity_groups=["ActivityGroup_000001"],
        activity_items=[],
    )

    # Create StudyActivities
    sa_randomized = create_study_activity(
        study_uid=study_for_export.uid,
        activity_uid=randomized_activity.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    sa_body_mes = create_study_activity(
        study_uid=study_for_export.uid,
        activity_uid=body_mes_activity.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    # Weight Study Activity
    sa_weight = create_study_activity(
        study_uid=study_for_export.uid,
        activity_uid=weight_activity.uid,
        activity_subgroup_uid=body_measurements_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    response = api_client.get(
        f"/studies/{study_for_export.uid}/study-activity-instances"
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert len(res) == 3
    assert res[0]["activity"]["uid"] == randomized_activity.uid
    assert res[1]["activity"]["uid"] == body_mes_activity.uid
    assert res[2]["activity"]["uid"] == weight_activity.uid

    # Create schedules
    TestUtils.create_study_activity_schedule(
        study_uid=study_for_export.uid,
        study_activity_uid=sa_randomized.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )
    TestUtils.create_study_activity_schedule(
        study_uid=study_for_export.uid,
        study_activity_uid=sa_body_mes.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )
    TestUtils.create_study_activity_schedule(
        study_uid=study_for_export.uid,
        study_activity_uid=sa_weight.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )

    export_url = f"/studies/{study_for_export.uid}/operational-soa-exports"
    response = api_client.get(export_url)
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == 3
    assert (
        res[0]["study_number"]
        == study_for_export.current_metadata.identification_metadata.study_number
    )
    assert res[0]["visit"] == first_visit.visit_short_name
    assert res[0]["epoch"] == study_epoch.epoch_ctterm.sponsor_preferred_name
    assert res[0]["activity_instance"] == randomized_activity_instance.name
    assert res[0]["topic_code"] == randomized_activity_instance.topic_code
    assert res[0]["param_code"] == randomized_activity_instance.adam_param_code
    assert res[0]["activity"] == sa_randomized.activity.name
    assert (
        res[0]["activity_subgroup"]
        == sa_randomized.study_activity_subgroup.activity_subgroup_name
    )
    assert (
        res[0]["activity_group"]
        == sa_randomized.study_activity_group.activity_group_name
    )
    assert res[0]["soa_group"] == sa_randomized.study_soa_group.soa_group_term_name
    assert (
        res[1]["study_number"]
        == study_for_export.current_metadata.identification_metadata.study_number
    )
    assert res[1]["visit"] == first_visit.visit_short_name
    assert res[1]["epoch"] == study_epoch.epoch_ctterm.sponsor_preferred_name
    assert res[1]["activity"] == sa_body_mes.activity.name
    assert res[1]["activity_instance"] is None
    assert res[1]["topic_code"] is None
    assert res[1]["param_code"] is None
    assert (
        res[1]["activity_subgroup"]
        == sa_body_mes.study_activity_subgroup.activity_subgroup_name
    )
    assert (
        res[1]["activity_group"] == sa_body_mes.study_activity_group.activity_group_name
    )
    assert res[1]["soa_group"] == sa_body_mes.study_soa_group.soa_group_term_name
    assert (
        res[2]["study_number"]
        == study_for_export.current_metadata.identification_metadata.study_number
    )
    assert res[2]["visit"] == first_visit.visit_short_name
    assert res[2]["epoch"] == study_epoch.epoch_ctterm.sponsor_preferred_name
    assert res[2]["activity"] == sa_weight.activity.name
    assert res[2]["activity_instance"] is None
    assert res[2]["topic_code"] is None
    assert res[2]["param_code"] is None
    assert (
        res[2]["activity_subgroup"]
        == sa_weight.study_activity_subgroup.activity_subgroup_name
    )
    assert (
        res[2]["activity_group"] == sa_weight.study_activity_group.activity_group_name
    )
    assert res[2]["soa_group"] == sa_weight.study_soa_group.soa_group_term_name

    for export_format in [
        "text/csv",
        "text/xml",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]:
        exported_data = TestUtils.verify_exported_data_format(
            api_client, export_format, export_url
        )
        if export_format == "text/csv":
            assert "study_version" in str(exported_data.read())
            assert "LATEST" in str(exported_data.read())


def test_only_placeholder_study_activity_can_have_subgroup_and_group_not_specified(
    api_client,
):
    activity_request = TestUtils.create_activity(
        name="activity request for study activity purpose"
    )
    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": activity_request.uid,
            "activity_subgroup_uid": None,
            "activity_group_uid": None,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 400)
    assert (
        response.json()["message"]
        == "Only StudyActivity placeholder can link to None ActivitySubGroup or None ActivityGroup"
    )


def test_delete_activity_placeholder_with_not_finalized_request_retires_the_request(
    api_client,
):
    activity_request = TestUtils.create_activity(
        name="Activity request for placeholder deletion",
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        is_request_final=True,
        library_name=REQUESTED_LIBRARY_NAME,
    )
    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": activity_request.uid,
            "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    activity_placeholder_uid = res["study_activity_uid"]

    response = api_client.delete(
        f"/studies/{study.uid}/study-activities/{activity_placeholder_uid}",
    )
    assert_response_status_code(response, 204)

    response = api_client.get(
        f"/concepts/activities/activities/{activity_request.uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["status"] == "Retired"


def test_study_activity_delete_underlying_objects(
    api_client,
):
    study_for_sa_delete = TestUtils.create_study(project_number=project.project_number)
    second_weight_activity = TestUtils.create_activity(
        name="Second weight",
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )
    response = api_client.post(
        f"/studies/{study_for_sa_delete.uid}/study-activities",
        json={
            "activity_uid": weight_activity.uid,
            "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    weight_sa = response.json()

    response = api_client.post(
        f"/studies/{study_for_sa_delete.uid}/study-activities",
        json={
            "activity_uid": second_weight_activity.uid,
            "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    second_weight_sa = response.json()

    response = api_client.delete(
        f"/studies/{study_for_sa_delete.uid}/study-activities/{weight_sa['study_activity_uid']}",
    )
    assert_response_status_code(response, 204)
    response = api_client.get(
        f"/studies/{study_for_sa_delete.uid}/study-activities/{weight_sa['study_activity_uid']}",
    )
    assert_response_status_code(response, 404)

    response = api_client.patch(
        f"/studies/{study_for_sa_delete.uid}/study-activity-groups/{weight_sa['study_activity_group']['study_activity_group_uid']}",
        json={
            "show_activity_group_in_protocol_flowchart": False,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["show_activity_group_in_protocol_flowchart"] is False

    response = api_client.patch(
        f"/studies/{study_for_sa_delete.uid}/study-activity-subgroups/{weight_sa['study_activity_subgroup']['study_activity_subgroup_uid']}",
        json={
            "show_activity_subgroup_in_protocol_flowchart": False,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["show_activity_subgroup_in_protocol_flowchart"] is False

    response = api_client.get(
        f"/studies/{study_for_sa_delete.uid}/study-activities/{second_weight_sa['study_activity_uid']}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["show_activity_group_in_protocol_flowchart"] is False
    assert res["show_activity_subgroup_in_protocol_flowchart"] is False

    response = api_client.patch(
        f"/studies/{study_for_sa_delete.uid}/study-activity-groups/{weight_sa['study_activity_group']['study_activity_group_uid']}",
        json={
            "show_activity_group_in_protocol_flowchart": True,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["show_activity_group_in_protocol_flowchart"] is True

    response = api_client.patch(
        f"/studies/{study_for_sa_delete.uid}/study-activity-subgroups/{weight_sa['study_activity_subgroup']['study_activity_subgroup_uid']}",
        json={
            "show_activity_subgroup_in_protocol_flowchart": True,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["show_activity_subgroup_in_protocol_flowchart"] is True

    response = api_client.get(
        f"/studies/{study_for_sa_delete.uid}/study-activities/{second_weight_sa['study_activity_uid']}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["show_activity_group_in_protocol_flowchart"] is True
    assert res["show_activity_subgroup_in_protocol_flowchart"] is True

    response = api_client.delete(
        f"/studies/{study_for_sa_delete.uid}/study-activities/{second_weight_sa['study_activity_uid']}",
    )
    assert_response_status_code(response, 204)
    response = api_client.get(
        f"/studies/{study_for_sa_delete.uid}/study-activities/{second_weight_sa['study_activity_uid']}",
    )
    assert_response_status_code(response, 404)

    response = api_client.patch(
        f"/studies/{study_for_sa_delete.uid}/study-activity-subgroups/{second_weight_sa['study_activity_subgroup']['study_activity_subgroup_uid']}",
        json={
            "show_activity_subgroup_in_protocol_flowchart": True,
        },
    )
    assert_response_status_code(response, 404)


def test_get_study_activity_by_uid(api_client):
    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": weight_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    study_activity_uid = res["study_activity_uid"]

    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["study_activity_subgroup"]["activity_subgroup_uid"]
        == randomisation_activity_subgroup.uid
    )
    assert (
        res["study_activity_group"]["activity_group_uid"] == general_activity_group.uid
    )
    assert res["study_soa_group"]["soa_group_term_uid"] == term_efficacy_uid
    assert res["activity"]["uid"] == weight_activity.uid
    assert len(res["activity"]["activity_groupings"]) == 2
    assert (
        res["activity"]["activity_groupings"][0]["activity_subgroup_uid"]
        == body_measurements_activity_subgroup.uid
    )
    assert (
        res["activity"]["activity_groupings"][0]["activity_group_uid"]
        == general_activity_group.uid
    )
    assert (
        res["activity"]["activity_groupings"][1]["activity_subgroup_uid"]
        == randomisation_activity_subgroup.uid
    )
    assert (
        res["activity"]["activity_groupings"][1]["activity_group_uid"]
        == general_activity_group.uid
    )


def test_study_activity_version_selecting_ct_package(api_client):
    """change the name of a CTTerm, and verify that the study selection is still set to the old name of the CTTerm when the Sponsor Standard version is set"""
    study_selection_breadcrumb = "study-activities"
    study_selection_ctterm_keys = "study_soa_group"
    study_selection_ctterm_uid_key = "soa_group_term_uid"
    study_selection_ctterm_name_key = "soa_group_term_name"
    study_for_ctterm_versioning = TestUtils.create_study(
        project_number=project.project_number
    )
    response = api_client.post(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}",
        json={
            "activity_uid": "activity_root1",
            "activity_subgroup_uid": "activity_subgroup_root1",
            "activity_group_uid": "activity_group_root1",
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    study_selection_uid_study_standard_test = res["study_activity_uid"]

    # edit ctterm
    new_ctterm_name = "new ctterm name"
    ctterm_uid = initial_ct_term_study_standard_test.term_uid
    # change ctterm name and approve the version
    response = api_client.post(
        f"/ct/terms/{ctterm_uid}/names/versions",
    )
    assert_response_status_code(response, 201)
    response = api_client.patch(
        f"/ct/terms/{ctterm_uid}/names",
        json={
            "sponsor_preferred_name": new_ctterm_name,
            "sponsor_preferred_name_sentence_case": new_ctterm_name,
            "change_description": "string",
        },
    )
    response = api_client.post(f"/ct/terms/{ctterm_uid}/names/approvals")
    assert_response_status_code(response, 201)

    # get study selection with ctterm latest
    response = api_client.patch(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
        json={"soa_group_term_uid": ctterm_uid},
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_uid_key] == ctterm_uid
    )
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_name_key]
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
        res[study_selection_ctterm_keys][study_selection_ctterm_uid_key]
        == initial_ct_term_study_standard_test.term_uid
    )
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_name_key]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )

    # edit objective
    response = api_client.patch(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}",
        json={
            "show_activity_group_in_protocol_flowchart": False,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[study_selection_ctterm_keys][study_selection_ctterm_name_key]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )

    # get versions of objective
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/{study_selection_uid_study_standard_test}/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[0][study_selection_ctterm_keys][study_selection_ctterm_name_key]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )
    assert (
        res[1][study_selection_ctterm_keys][study_selection_ctterm_name_key]
        == new_ctterm_name
    )

    # get all objectives
    response = api_client.get(
        f"/studies/{study_for_ctterm_versioning.uid}/{study_selection_breadcrumb}/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[0][study_selection_ctterm_keys][study_selection_ctterm_name_key]
        == initial_ct_term_study_standard_test.sponsor_preferred_name
    )
    assert (
        res[1][study_selection_ctterm_keys][study_selection_ctterm_name_key]
        == new_ctterm_name
    )


def test_edit_study_activity_groupings(api_client):
    # ===== create study activity groupings =====
    # create activity group
    lab_assessment_activity_group = TestUtils.create_activity_group(
        name="Lab Assessment"
    )
    vital_signs_activity_group = TestUtils.create_activity_group(name="Vital Signs")
    incorrect_activity_group = TestUtils.create_activity_group(name="Incorrect Group")
    # create activity subgroup
    blood_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Blood", activity_groups=[lab_assessment_activity_group.uid]
    )
    blood_secondary_activity_subgroup = TestUtils.create_activity_subgroup(
        name="BloodTwo",
        activity_groups=[
            vital_signs_activity_group.uid,
            lab_assessment_activity_group.uid,
        ],
    )
    blood_incorrect_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Blood Incorrect", activity_groups=[incorrect_activity_group.uid]
    )
    blood_tertiary_activity_subgroup = TestUtils.create_activity_subgroup(
        name="BloodThree", activity_groups=[vital_signs_activity_group.uid]
    )

    # create activity
    blood_pressure_activity = TestUtils.create_activity(
        name="Blood Pressure",
        activity_subgroups=[
            blood_activity_subgroup.uid,
            blood_secondary_activity_subgroup.uid,
            blood_secondary_activity_subgroup.uid,
            blood_tertiary_activity_subgroup.uid,
        ],
        activity_groups=[
            lab_assessment_activity_group.uid,
            lab_assessment_activity_group.uid,
            vital_signs_activity_group.uid,
            vital_signs_activity_group.uid,
        ],
    )
    # create study activity
    blood_pressure_study_activity = TestUtils.create_study_activity(
        study_uid=study.uid,
        activity_uid=blood_pressure_activity.uid,
        activity_group_uid=vital_signs_activity_group.uid,
        activity_subgroup_uid=blood_secondary_activity_subgroup.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    # validate study activity exists
    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{blood_pressure_study_activity.study_activity_uid}"
    )
    assert_response_status_code(response, 200)
    # test change of activity group and subgroup
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{blood_pressure_study_activity.study_activity_uid}",
        json={
            "activity_group_uid": vital_signs_activity_group.uid,
            "activity_subgroup_uid": blood_tertiary_activity_subgroup.uid,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["study_activity_group"]["activity_group_uid"]
        == vital_signs_activity_group.uid
    )
    assert (
        res["study_activity_subgroup"]["activity_subgroup_uid"]
        == blood_tertiary_activity_subgroup.uid
    )
    # test change of incorrect activity group and subgroup
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{blood_pressure_study_activity.study_activity_uid}",
        json={
            "activity_group_uid": incorrect_activity_group.uid,
            "activity_subgroup_uid": blood_incorrect_activity_subgroup.uid,
        },
    )
    assert_response_status_code(response, 422)
    assert (
        response.json()["message"]
        == f"Provided Activity Group is not included in '{blood_pressure_activity.uid}' Activity Groupings."
    )
    # test change of just activity group
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{blood_pressure_study_activity.study_activity_uid}",
        json={"activity_group_uid": lab_assessment_activity_group.uid},
    )
    assert_response_status_code(response, 422)
    res = response.json()
    assert res["message"] == "An activity subgroup is required for the selection"
    # test change of just activity subgroup
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{blood_pressure_study_activity.study_activity_uid}",
        json={"activity_subgroup_uid": blood_activity_subgroup.uid},
    )
    assert_response_status_code(response, 422)
    res = response.json()
    assert res["message"] == "An activity group is required for the selection"
    # test change of activity group and subgroup to the same values
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{blood_pressure_study_activity.study_activity_uid}",
        json={
            "activity_group_uid": vital_signs_activity_group.uid,
            "activity_subgroup_uid": blood_tertiary_activity_subgroup.uid,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["study_activity_subgroup"]["activity_subgroup_uid"]
        == blood_tertiary_activity_subgroup.uid
    )
    assert (
        res["study_activity_group"]["activity_group_uid"]
        == vital_signs_activity_group.uid
    )
    # test change of activity group and subgroup to non existent values
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{blood_pressure_study_activity.study_activity_uid}",
        json={
            "activity_group_uid": "non_existent",
            "activity_subgroup_uid": "non_existent",
        },
    )
    assert_response_status_code(response, 422)
    # test change if non existent activity subgroup
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{blood_pressure_study_activity.study_activity_uid}",
        json={
            "activity_group_uid": vital_signs_activity_group.uid,
            "activity_subgroup_uid": "non_existent",
        },
    )
    assert_response_status_code(response, 422)


def test_sync_study_activity_to_latest_version_of_activity(api_client):
    # create activity
    activity_name_before_change = "Activity V1"
    activity_to_change = TestUtils.create_activity(
        name=activity_name_before_change,
        activity_subgroups=[
            randomisation_activity_subgroup.uid,
        ],
        activity_groups=[
            general_activity_group.uid,
        ],
    )
    # create study activity
    study_activity_v1 = TestUtils.create_study_activity(
        study_uid=study.uid,
        activity_uid=activity_to_change.uid,
        activity_group_uid=general_activity_group.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_v1.study_activity_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["latest_activity"] is None
    assert res["activity"]["uid"] == activity_to_change.uid
    assert res["activity"]["name"] == activity_name_before_change

    # create new draft version for activity
    response = api_client.post(
        f"/concepts/activities/activities/{activity_to_change.uid}/versions"
    )
    assert_response_status_code(response, 201)

    # patch library activity
    activity_name_after_change = "Activity V2"
    response = api_client.patch(
        f"/concepts/activities/activities/{activity_to_change.uid}",
        json={
            "name": activity_name_after_change,
            "name_sentence_case": activity_name_after_change.lower(),
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activities/{activity_to_change.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # check if study activity sees that change was made on library level
    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity_v1.study_activity_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["latest_activity"]["uid"] == activity_to_change.uid
    assert res["latest_activity"]["name"] == activity_name_after_change
    assert res["activity"]["uid"] == activity_to_change.uid
    assert res["activity"]["name"] == activity_name_before_change

    # sync to latest version of activity
    response = api_client.post(
        f"/studies/{study.uid}/study-activities/{study_activity_v1.study_activity_uid}/sync-latest-version",
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["latest_activity"] is None
    assert res["activity"]["uid"] == activity_to_change.uid
    assert res["activity"]["name"] == activity_name_after_change


def test_study_activity_replacement_with_different_activities(api_client):
    study_visit_uid = generic_study_visit.uid

    # create study activity
    study_activity = TestUtils.create_study_activity(
        study_uid=study.uid,
        activity_uid=randomized_activity.uid,
        activity_group_uid=general_activity_group.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        soa_group_term_uid=term_efficacy_uid,
    )

    # create schedule
    response = api_client.post(
        f"/studies/{study.uid}/study-activity-schedules",
        json={
            "study_activity_uid": study_activity.study_activity_uid,
            "study_visit_uid": study_visit_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    study_activity_schedule_uid = res["study_activity_schedule_uid"]

    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity.study_activity_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["latest_activity"] is None
    assert res["activity"]["uid"] == randomized_activity.uid
    assert (
        res["study_activity_group"]["activity_group_uid"] == general_activity_group.uid
    )
    assert (
        res["study_activity_subgroup"]["activity_subgroup_uid"]
        == randomisation_activity_subgroup.uid
    )
    assert res["study_soa_group"]["soa_group_term_uid"] == term_efficacy_uid

    # check for study activity instances before replacement
    response = api_client.get(
        f"/studies/{study.uid}/study-activity-instances",
        params={
            "filters": json.dumps(
                {
                    "study_activity_uid": {
                        "v": [f"{study_activity.study_activity_uid}"],
                        "op": "eq",
                    }
                }
            ),
            "page_size": 0,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    study_activity_instances = res["items"]
    assert len(study_activity_instances) == 1
    assert (
        study_activity_instances[0]["study_activity_uid"]
        == study_activity.study_activity_uid
    )
    assert study_activity_instances[0]["activity"]["uid"] == randomized_activity.uid
    assert (
        study_activity_instances[0]["activity_instance"]["uid"]
        == randomized_activity_instance.uid
    )

    some_new_activity_in_same_groupings = TestUtils.create_activity(
        name="Second randomized",
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )
    activity_instance_to_replace_name = "Activity instance to replace"
    activity_instance_for_activity_in_same_groupings = (
        TestUtils.create_activity_instance(
            name=activity_instance_to_replace_name,
            activity_instance_class_uid=generic_activity_instance_class.uid,
            name_sentence_case=activity_instance_to_replace_name.lower(),
            topic_code=f"{activity_instance_to_replace_name} topic code",
            adam_param_code=f"{activity_instance_to_replace_name} adam_param_code",
            is_required_for_activity=True,
            activities=[some_new_activity_in_same_groupings.uid],
            activity_subgroups=[randomisation_activity_subgroup.uid],
            activity_groups=[general_activity_group.uid],
            activity_items=[],
        )
    )
    # replace selected activity
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{study_activity.study_activity_uid}/activity-replacements",
        json={
            "activity_uid": some_new_activity_in_same_groupings.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity"]["uid"] == some_new_activity_in_same_groupings.uid
    assert (
        res["study_activity_group"]["activity_group_uid"] == general_activity_group.uid
    )
    assert (
        res["study_activity_subgroup"]["activity_subgroup_uid"]
        == randomisation_activity_subgroup.uid
    )
    assert res["study_soa_group"]["soa_group_term_uid"] == term_efficacy_uid

    # get study activity after replacement
    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity.study_activity_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity"]["uid"] == some_new_activity_in_same_groupings.uid
    assert (
        res["study_activity_group"]["activity_group_uid"] == general_activity_group.uid
    )
    assert (
        res["study_activity_subgroup"]["activity_subgroup_uid"]
        == randomisation_activity_subgroup.uid
    )
    assert res["study_soa_group"]["soa_group_term_uid"] == term_efficacy_uid
    assert (
        res["show_soa_group_in_protocol_flowchart"]
        == study_activity.show_soa_group_in_protocol_flowchart
    )
    assert (
        res["show_activity_group_in_protocol_flowchart"]
        == study_activity.show_activity_group_in_protocol_flowchart
    )
    assert (
        res["show_activity_subgroup_in_protocol_flowchart"]
        == study_activity.show_activity_subgroup_in_protocol_flowchart
    )
    assert (
        res["show_activity_in_protocol_flowchart"]
        == study_activity.show_activity_in_protocol_flowchart
    )

    # Check if schedule still exists after replacement
    response = api_client.get(f"/studies/{study.uid}/study-activity-schedules")
    assert_response_status_code(response, 200)
    res = response.json()
    assert study_activity_schedule_uid in [
        schedule["study_activity_schedule_uid"] for schedule in res
    ], "Schedule created for StudyActivity before replacement should still exist"
    for schedule in res:
        if schedule["study_activity_schedule_uid"] == study_activity_schedule_uid:
            assert schedule["study_activity_uid"] == study_activity.study_activity_uid
            assert schedule["study_visit_uid"] == study_visit_uid

    # check for study activity instances after first replacement
    response = api_client.get(
        f"/studies/{study.uid}/study-activity-instances",
        params={
            "filters": json.dumps(
                {
                    "study_activity_uid": {
                        "v": [f"{study_activity.study_activity_uid}"],
                        "op": "eq",
                    }
                }
            ),
            "page_size": 0,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    study_activity_instances = res["items"]
    assert len(study_activity_instances) == 1
    assert (
        study_activity_instances[0]["study_activity_uid"]
        == study_activity.study_activity_uid
    )
    assert (
        study_activity_instances[0]["activity"]["uid"]
        == some_new_activity_in_same_groupings.uid
    )
    assert (
        study_activity_instances[0]["activity_instance"]["uid"]
        == activity_instance_for_activity_in_same_groupings.uid
    )

    new_activity_group = TestUtils.create_activity_group(name="new activity group")
    new_activity_subgroup = TestUtils.create_activity_subgroup(
        name="new activity subgroup", activity_groups=[new_activity_group.uid]
    )
    some_new_activity_in_different_groupings = TestUtils.create_activity(
        name="new activity in different grouping",
        activity_subgroups=[new_activity_subgroup.uid],
        activity_groups=[new_activity_group.uid],
        library_name="Sponsor",
    )
    activity_instance_to_replace_with_diff_groupings_name = (
        "Activity instance to replace with different groupings"
    )
    activity_instance_for_activity_in_diff_groupings = TestUtils.create_activity_instance(
        name=activity_instance_to_replace_with_diff_groupings_name,
        activity_instance_class_uid=generic_activity_instance_class.uid,
        name_sentence_case=activity_instance_to_replace_with_diff_groupings_name.lower(),
        topic_code=f"{activity_instance_to_replace_with_diff_groupings_name} topic code",
        adam_param_code=f"{activity_instance_to_replace_with_diff_groupings_name} adam_param_code",
        is_required_for_activity=True,
        activities=[some_new_activity_in_different_groupings.uid],
        activity_subgroups=[new_activity_subgroup.uid],
        activity_groups=[new_activity_group.uid],
        activity_items=[],
    )
    # replace selected activity
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{study_activity.study_activity_uid}/activity-replacements",
        json={
            "activity_uid": some_new_activity_in_different_groupings.uid,
            "activity_subgroup_uid": new_activity_subgroup.uid,
            "activity_group_uid": new_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity"]["uid"] == some_new_activity_in_different_groupings.uid
    assert res["study_activity_group"]["activity_group_uid"] == new_activity_group.uid
    assert (
        res["study_activity_subgroup"]["activity_subgroup_uid"]
        == new_activity_subgroup.uid
    )
    assert res["study_soa_group"]["soa_group_term_uid"] == term_efficacy_uid

    # get study activity after replacement
    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{study_activity.study_activity_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity"]["uid"] == some_new_activity_in_different_groupings.uid
    assert res["study_activity_group"]["activity_group_uid"] == new_activity_group.uid
    assert (
        res["study_activity_subgroup"]["activity_subgroup_uid"]
        == new_activity_subgroup.uid
    )
    assert res["study_soa_group"]["soa_group_term_uid"] == term_efficacy_uid
    assert (
        res["show_soa_group_in_protocol_flowchart"]
        == study_activity.show_soa_group_in_protocol_flowchart
    )
    assert (
        res["show_activity_group_in_protocol_flowchart"]
        == study_activity.show_activity_group_in_protocol_flowchart
    )
    assert (
        res["show_activity_subgroup_in_protocol_flowchart"]
        == study_activity.show_activity_subgroup_in_protocol_flowchart
    )
    assert (
        res["show_activity_in_protocol_flowchart"]
        == study_activity.show_activity_in_protocol_flowchart
    )

    # Check if schedule still exists after second replacement
    response = api_client.get(f"/studies/{study.uid}/study-activity-schedules")
    assert_response_status_code(response, 200)
    res = response.json()
    assert study_activity_schedule_uid in [
        schedule["study_activity_schedule_uid"] for schedule in res
    ], "Schedule created for StudyActivity before replacement should still exist"
    for schedule in res:
        if schedule["study_activity_schedule_uid"] == study_activity_schedule_uid:
            assert schedule["study_activity_uid"] == study_activity.study_activity_uid
            assert schedule["study_visit_uid"] == study_visit_uid
    # check for study activity instances after second replacement
    response = api_client.get(
        f"/studies/{study.uid}/study-activity-instances",
        params={
            "filters": json.dumps(
                {
                    "study_activity_uid": {
                        "v": [f"{study_activity.study_activity_uid}"],
                        "op": "eq",
                    }
                }
            ),
            "page_size": 0,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    study_activity_instances = res["items"]
    assert len(study_activity_instances) == 1
    assert (
        study_activity_instances[0]["study_activity_uid"]
        == study_activity.study_activity_uid
    )
    assert (
        study_activity_instances[0]["activity"]["uid"]
        == some_new_activity_in_different_groupings.uid
    )
    assert (
        study_activity_instances[0]["activity_instance"]["uid"]
        == activity_instance_for_activity_in_diff_groupings.uid
    )

    # delete study activity after a few replacements
    response = api_client.delete(
        f"/studies/{study.uid}/study-activities/{study_activity.study_activity_uid}"
    )
    assert_response_status_code(response, 204)


def test_study_activity_create_in_soa_with_reorder(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    # create study activity
    for i in range(10):
        unique_activity = TestUtils.create_activity(
            name=f"Unique Activity {i}",
            activity_subgroups=[randomisation_activity_subgroup.uid],
            activity_groups=[general_activity_group.uid],
            library_name="Sponsor",
        )
        TestUtils.create_study_activity(
            study_uid=test_study.uid,
            activity_uid=unique_activity.uid,
            activity_group_uid=general_activity_group.uid,
            activity_subgroup_uid=randomisation_activity_subgroup.uid,
            soa_group_term_uid=term_efficacy_uid,
        )

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 10

    # Create StudyActivity in a specific place in SoA, reorder other StudyActivities
    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": randomized_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
            "order": 1,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["order"] == 1
    assert res["activity"]["uid"] == randomized_activity.uid


def test_create_duplicated_study_activitiy(api_client):
    custom_activity = TestUtils.create_activity(
        name="custom_activity",
        activity_subgroups=[
            randomisation_activity_subgroup.uid,
        ],
        activity_groups=[general_activity_group.uid],
    )
    TestUtils.create_study_activity(
        study_uid=study.uid,
        activity_uid=custom_activity.uid,
        activity_group_uid=general_activity_group.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": custom_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 409)
    res = response.json()
    assert (
        res["message"]
        == f"There is already a Study Selection to the activity with Name '{custom_activity.name}' with the same groupings."
    )


def test_batch_operations(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    api_client.post(
        f"/studies/{test_study.uid}/study-activities/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "soa_group_term_uid": term_efficacy_uid,
                    "activity_uid": weight_activity.uid,
                    "activity_subgroup_uid": randomisation_activity_subgroup.uid,
                    "activity_group_uid": general_activity_group.uid,
                },
            },
            {
                "method": "POST",
                "content": {
                    "soa_group_term_uid": term_efficacy_uid,
                    "activity_uid": weight_activity.uid,
                    "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
                    "activity_group_uid": general_activity_group.uid,
                },
            },
        ],
    )

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 2
    randomisation_sactivity = study_activities[0]["study_activity_uid"]
    body_measurements_sactivity = study_activities[1]["study_activity_uid"]

    api_client.post(
        f"/studies/{test_study.uid}/study-activities/batch",
        json=[
            {
                "method": "PATCH",
                "content": {
                    "study_activity_uid": randomisation_sactivity,
                    "content": {"show_activity_in_protocol_flowchart": True},
                },
            },
            {
                "method": "DELETE",
                "content": {
                    "study_activity_uid": body_measurements_sactivity,
                },
            },
        ],
    )

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 1
    assert study_activities[0]["show_activity_in_protocol_flowchart"] is True


def test_batch_operations_for_combined_study_activity_and_activity_schedules(
    api_client,
):
    test_study = TestUtils.create_study(project_number=project.project_number)

    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=test_study.uid)
    inputs = {
        "study_uid": test_study.uid,
        "study_epoch_uid": study_epoch.uid,
        "visit_type_uid": "VisitType_0001",
        "show_visit": True,
        "time_reference_uid": "VisitSubType_0005",
        "time_value": 100,
        "time_unit_uid": DAYUID,
        "visit_class": "SINGLE_VISIT",
        "visit_subclass": "SINGLE_VISIT",
        "is_global_anchor_visit": False,
    }
    datadict = visits_basic_data
    datadict.update(inputs)
    response = api_client.post(
        f"/studies/{test_study.uid}/study-visits",
        json=datadict,
    )
    res = response.json()
    assert_response_status_code(response, 201)
    study_visit_uid = res["uid"]

    response = api_client.post(
        f"/studies/{test_study.uid}/soa-edits/batch",
        json=[
            {
                "method": "POST",
                "object": "StudyActivity",
                "content": {
                    "soa_group_term_uid": term_efficacy_uid,
                    "activity_uid": weight_activity.uid,
                    "activity_subgroup_uid": randomisation_activity_subgroup.uid,
                    "activity_group_uid": general_activity_group.uid,
                },
            },
            {
                "method": "POST",
                "object": "StudyActivity",
                "content": {
                    "soa_group_term_uid": term_efficacy_uid,
                    "activity_uid": weight_activity.uid,
                    "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
                    "activity_group_uid": general_activity_group.uid,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 2
    randomisation_sactivity = study_activities[0]["study_activity_uid"]
    body_measurements_sactivity = study_activities[1]["study_activity_uid"]

    response = api_client.post(
        f"/studies/{test_study.uid}/soa-edits/batch",
        json=[
            {
                "method": "PATCH",
                "object": "StudyActivity",
                "content": {
                    "study_activity_uid": randomisation_sactivity,
                    "content": {"show_activity_in_protocol_flowchart": True},
                },
            },
            {
                "method": "POST",
                "object": "StudyActivitySchedule",
                "content": {
                    "study_visit_uid": study_visit_uid,
                    "study_activity_uid": randomisation_sactivity,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 2
    assert study_activities[0]["show_activity_in_protocol_flowchart"] is True

    response = api_client.get(f"/studies/{test_study.uid}/study-activity-schedules")
    assert_response_status_code(response, 200)
    study_activity_schedules = response.json()
    assert len(study_activity_schedules) == 1
    schedule_uid = study_activity_schedules[0]["study_activity_schedule_uid"]

    response = api_client.post(
        f"/studies/{test_study.uid}/soa-edits/batch",
        json=[
            {
                "method": "DELETE",
                "object": "StudyActivity",
                "content": {
                    "study_activity_uid": body_measurements_sactivity,
                },
            },
            {
                "method": "DELETE",
                "object": "StudyActivitySchedule",
                "content": {
                    "uid": schedule_uid,
                },
            },
        ],
    )
    assert response.status_code == 207

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 1
    assert study_activities[0]["show_activity_in_protocol_flowchart"] is True

    response = api_client.get(f"/studies/{test_study.uid}/study-activity-schedules")
    assert_response_status_code(response, 200)
    study_activity_schedules = response.json()
    assert len(study_activity_schedules) == 0
