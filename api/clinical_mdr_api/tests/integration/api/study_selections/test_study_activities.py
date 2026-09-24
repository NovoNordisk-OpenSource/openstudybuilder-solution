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
from typing import Any
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.domains.enums import ValidationMode
from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
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
from clinical_mdr_api.models.study_selections.study_selection import (
    ReferencedItem,
    StudySelectionReviewAction,
)
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
)
from clinical_mdr_api.tests.integration.utils.factory_activity import (
    create_study_activity,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
    create_ct_term,
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
    assert_json_response,
    assert_response_status_code,
)
from common.config import settings

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
activity_group: ActivityGroup
activity_subgroup: ActivitySubGroup
test_data_dict: dict[str, Any]


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
    global study, test_data_dict
    study, test_data_dict = inject_base_data()

    db.cypher_query(STARTUP_ACTIVITY_GROUPS)
    db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
    db.cypher_query(STARTUP_ACTIVITIES)

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
    global activity_group
    activity_group = TestUtils.create_activity_group(name="test activity group")
    global activity_subgroup
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="test activity subgroup"
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
        name="Randomisation"
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
        name="Body Measurements"
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

    _catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    catalogue_name = "SDTM CT"
    # Create a study selection
    ct_term_codelist = create_codelist(
        "Flowchart Group",
        "CTCodelist_Name",
        catalogue_name,
        library_name,
        submission_value="FLWCRTGRP",
    )
    global term_efficacy_uid
    term_efficacy_uid = "term_efficacy_uid"
    create_ct_term(
        codelists=[
            {
                "uid": ct_term_codelist.codelist_uid,
                "submission_value": "EFFICACY",
                "order": 1,
            },
        ],
        name="EFFICACY",
        catalogue_name=catalogue_name,
        library_name=library_name,
        uid=term_efficacy_uid,
    )
    global informed_consent_uid
    informed_consent_uid = "informed_consent_uid"
    create_ct_term(
        codelists=[
            {
                "uid": ct_term_codelist.codelist_uid,
                "submission_value": "SAFETY",
                "order": 2,
            },
        ],
        name="SAFETY",
        catalogue_name=catalogue_name,
        library_name=library_name,
        uid=informed_consent_uid,
    )

    # create visit
    inputs = {
        "study_uid": study.uid,
        "study_epoch_uid": study_epoch.uid,
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
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
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
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
    initial_activity_groupings = res["activity"]["activity_groupings"]
    initial_activity_name = res["activity"]["name"]

    text_value_2_name = "2ndname"
    # change activity name and approve the version
    response = api_client.post(
        f"/concepts/activities/activities/{library_activity_uid}/versions",
    )
    assert_response_status_code(response, 201)

    response = api_client.put(
        f"/concepts/activities/activities/{library_activity_uid}",
        json={
            "change_description": "Change to have a new version of the activity so we can be sure that the study activity won't have any update",
            "name": text_value_2_name,
            "name_sentence_case": text_value_2_name,
            "guidance_text": "don't know",
            "activity_groupings": initial_activity_groupings,
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{library_activity_grouping_subgroup_uid}/versions",
    )
    assert_response_status_code(response, 201)

    response = api_client.put(
        f"/concepts/activities/activity-sub-groups/{library_activity_grouping_subgroup_uid}",
        json={
            "change_description": "Change to have a new version of the activity so we can be sure that the study activity won't have any update",
            "name": text_value_2_name,
            "name_sentence_case": text_value_2_name,
            "guidance_text": "don't know",
            "library_name": "Sponsor",
            "activity_groups": [library_activity_grouping_group_uid],
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activities/{library_activity_uid}/approvals"
    )
    assert_response_status_code(response, 201)

    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{library_activity_grouping_subgroup_uid}/approvals"
    )
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
    assert_response_status_code(response, 201)
    response = api_client.put(
        f"/concepts/activities/activities/{library_activity_uid}",
        json={
            "change_description": "returning the name to the initial one to continue with tests",
            "name": text_value_2_name,
            "name_sentence_case": text_value_2_name,
            "guidance_text": "don't know",
            "activity_groupings": initial_activity_groupings,
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activities/{library_activity_uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # change activity name and approve the version
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{library_activity_grouping_subgroup_uid}/versions",
    )
    assert_response_status_code(response, 201)
    response = api_client.put(
        f"/concepts/activities/activity-sub-groups/{library_activity_grouping_subgroup_uid}",
        json={
            "change_description": "returning the name to the initial one to continue with tests",
            "name": text_value_2_name,
            "name_sentence_case": text_value_2_name,
            "guidance_text": "don't know",
            "library_name": "Sponsor",
            "activity_groups": [library_activity_grouping_group_uid],
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{library_activity_grouping_subgroup_uid}/approvals"
    )
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
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)
    # Unlock -- Study remain unlocked
    response = api_client.post(
        f"/studies/{study_for_cascade.uid}/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": test_data_dict["reason_for_unlock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)
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


def _normalize_versioned_study_data(
    outer_list: list[dict[str, Any]],
    visits_items: list[dict[str, Any]],
    set_study_version: bool = True,
) -> None:
    for i, item in enumerate(outer_list):
        if set_study_version:
            item["study_version"] = mock.ANY
        for j in visits_items[i]:
            if isinstance(visits_items[i][j], dict):
                visits_items[i][j]["queried_effective_date"] = mock.ANY


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

    # get data of prior version for comparation
    expected_visits = api_client.get(
        f"/studies/{study_for_versioning.uid}/study-visits"
    ).json()
    expected_activities = api_client.get(
        f"/studies/{study_for_versioning.uid}/study-activities"
    ).json()
    expected_activity_schedules = api_client.get(
        f"/studies/{study_for_versioning.uid}/study-activity-schedules"
    ).json()
    expected_activity_instructions = api_client.get(
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
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
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
    response = api_client.post(
        f"/studies/{study_for_versioning.uid}/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": test_data_dict["reason_for_unlock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

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

    # CHECK if data of locked study version was not changed
    visits_items = expected_visits["items"]
    # compare study visits of locked study version
    _normalize_versioned_study_data(expected_visits["items"], visits_items)
    current_visits = api_client.get(
        f"/studies/{study_for_versioning.uid}/study-visits?study_value_version=1"
    ).json()
    assert current_visits == expected_visits

    # compare study activities of locked study version
    _normalize_versioned_study_data(expected_activities["items"], visits_items)
    current_activities = api_client.get(
        f"/studies/{study_for_versioning.uid}/study-activities?study_value_version=1"
    ).json()
    assert current_activities == expected_activities

    # compare study activity schedules of locked study version
    _normalize_versioned_study_data(
        expected_activity_schedules, visits_items, set_study_version=False
    )
    current_activity_schedules = api_client.get(
        f"/studies/{study_for_versioning.uid}/study-activity-schedules?study_value_version=1"
    ).json()
    assert current_activity_schedules == expected_activity_schedules

    # compare study activity instructions of locked study version
    _normalize_versioned_study_data(expected_activity_instructions, visits_items)
    current_activity_instructions = api_client.get(
        f"/studies/{study_for_versioning.uid}/study-activity-instructions?study_value_version=1"
    ).json()
    assert current_activity_instructions == expected_activity_instructions


def test_reusing_study_activity_group_study_activity_subgroup_study_soa_group(
    api_client,
):
    activity_group_1 = TestUtils.create_activity_group(name="activity_group_1")
    activity_group_2 = TestUtils.create_activity_group(name="activity_group_2")
    activity_subgroup_1 = TestUtils.create_activity_subgroup(name="activity_subgroup_1")
    activity_subgroup_2 = TestUtils.create_activity_subgroup(
        name="activity_subgroup_2",
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
    activity_subgroup = TestUtils.create_activity_subgroup(name="AS")
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
    assert (
        res[4]["description"]
        == f"EFFICACY/{general_activity_group.name}/{randomisation_activity_subgroup.name} true"
    )
    assert res[4]["action"] == "Create"
    assert res[5]["object_type"] == "visibility flag"
    assert res[5]["description"] == f"EFFICACY/{general_activity_group.name} true"
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
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)
    # Unlock -- Study remain unlocked
    response = api_client.post(
        f"/studies/{study_for_export.uid}/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": test_data_dict["reason_for_unlock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

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
        topic_code="randomized activity instance topic code 2",
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
    assert_json_response(response)
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
    assert_json_response(response)
    res = response.json()
    # Operational SoA now includes study-activity-instance placeholders (activity_instance=None)
    # In this scenario we have 3 study-activity-instances: 1 real + 2 placeholders
    assert len(res) == 3

    # Find the real activity instance (the one with activity_instance not None)
    real_instances = [r for r in res if r["activity_instance"] is not None]
    placeholder_instances = [r for r in res if r["activity_instance"] is None]
    assert len(real_instances) == 1
    assert len(placeholder_instances) == 2

    # Validate the real activity instance
    assert (
        real_instances[0]["study_number"]
        == study_for_export.current_metadata.identification_metadata.study_number
    )
    assert real_instances[0]["visit"] == first_visit.visit_short_name
    assert real_instances[0]["epoch"] == study_epoch.epoch_ctterm.sponsor_preferred_name
    assert real_instances[0]["activity_instance"] == randomized_activity_instance.name
    assert real_instances[0]["topic_code"] == randomized_activity_instance.topic_code
    assert (
        real_instances[0]["param_code"] == randomized_activity_instance.adam_param_code
    )
    assert real_instances[0]["activity"] == sa_randomized.activity.name
    assert (
        real_instances[0]["activity_subgroup"]
        == sa_randomized.study_activity_subgroup.activity_subgroup_name
    )
    assert (
        real_instances[0]["activity_group"]
        == sa_randomized.study_activity_group.activity_group_name
    )
    assert (
        real_instances[0]["soa_group"]
        == sa_randomized.study_soa_group.soa_group_term_name
    )

    # Validate placeholder instances have null activity_instance fields
    for placeholder in placeholder_instances:
        assert placeholder["topic_code"] is None
        assert placeholder["param_code"] is None

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
        name="activity request for study activity purpose",
        library_name="Sponsor",
        activity_groups=[activity_group.uid],
        activity_subgroups=[activity_subgroup.uid],
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
    assert_response_status_code(response, 200)
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
    blood_activity_subgroup = TestUtils.create_activity_subgroup(name="Blood")
    blood_secondary_activity_subgroup = TestUtils.create_activity_subgroup(
        name="BloodTwo",
    )
    blood_incorrect_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Blood Incorrect"
    )
    blood_tertiary_activity_subgroup = TestUtils.create_activity_subgroup(
        name="BloodThree"
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
    assert_response_status_code(response, 400)
    assert (
        response.json()["message"]
        == f"Provided Activity Group is not included in '{blood_pressure_activity.uid}' Activity Groupings."
    )
    # test change of just activity group
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{blood_pressure_study_activity.study_activity_uid}",
        json={"activity_group_uid": lab_assessment_activity_group.uid},
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == "An activity subgroup is required for the selection"
    # test change of just activity subgroup
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{blood_pressure_study_activity.study_activity_uid}",
        json={"activity_subgroup_uid": blood_activity_subgroup.uid},
    )
    assert_response_status_code(response, 400)
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
    assert_response_status_code(response, 400)
    # test change if non existent activity subgroup
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{blood_pressure_study_activity.study_activity_uid}",
        json={
            "activity_group_uid": vital_signs_activity_group.uid,
            "activity_subgroup_uid": "non_existent",
        },
    )
    assert_response_status_code(response, 400)


def test_sync_study_activity_to_latest_version_of_activity(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
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
    # StudyActivity created for same (SoAGroup, ActivityGroup) but different ActivitySubGroup
    # to validate order numbers after updating activity to newer version
    TestUtils.create_study_activity(
        study_uid=test_study.uid,
        activity_uid=weight_activity.uid,
        activity_group_uid=general_activity_group.uid,
        activity_subgroup_uid=body_measurements_activity_subgroup.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    # create study activity
    study_activity_v1 = TestUtils.create_study_activity(
        study_uid=test_study.uid,
        activity_uid=activity_to_change.uid,
        activity_group_uid=general_activity_group.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activities/{study_activity_v1.study_activity_uid}"
    )
    assert_response_status_code(response, 200)
    sa_before_sync = response.json()
    assert sa_before_sync["is_activity_updated"] is False
    assert sa_before_sync["latest_activity"] is None
    assert sa_before_sync["activity"]["uid"] == activity_to_change.uid
    assert sa_before_sync["activity"]["name"] == activity_name_before_change
    assert sa_before_sync["keep_old_version"] is False

    temporary_ag = TestUtils.create_activity_group(name="Temporary AG")
    # Update ActivitySubGroup to latest ActivityGroup version
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{randomisation_activity_subgroup.uid}/versions"
    )
    assert_response_status_code(response, 201)

    response = api_client.put(
        f"/concepts/activities/activity-sub-groups/{randomisation_activity_subgroup.uid}",
        json={
            "name": randomisation_activity_subgroup.name,
            "name_sentence_case": randomisation_activity_subgroup.name.lower(),
            "library_name": randomisation_activity_subgroup.library_name,
            "activity_groups": [general_activity_group.uid, temporary_ag.uid],
            "change_description": "Pulled ActivityGroup change",
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{randomisation_activity_subgroup.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # create new draft version for activity
    response = api_client.post(
        f"/concepts/activities/activities/{activity_to_change.uid}/versions"
    )
    assert_response_status_code(response, 201)

    # update library activity
    response = api_client.put(
        f"/concepts/activities/activities/{activity_to_change.uid}",
        json={
            "name": activity_to_change.name,
            "name_sentence_case": activity_to_change.name.lower(),
            "activity_groupings": [
                {
                    "activity_group_uid": general_activity_group.uid,
                    "activity_subgroup_uid": randomisation_activity_subgroup.uid,
                },
                {
                    "activity_group_uid": temporary_ag.uid,
                    "activity_subgroup_uid": randomisation_activity_subgroup.uid,
                },
            ],
            "library_name": activity_to_change.library_name,
            "change_description": "Updated name",
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activities/{activity_to_change.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # check if study activity sees that change was made on library level
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activities/{study_activity_v1.study_activity_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["is_activity_updated"] is False
    assert res["latest_activity"]["uid"] == activity_to_change.uid
    assert res["latest_activity"]["name"] == activity_to_change.name
    assert len(res["latest_activity"]["activity_groupings"]) == 2
    assert res["activity"]["uid"] == activity_to_change.uid
    assert res["activity"]["name"] == activity_name_before_change
    assert len(res["activity"]["activity_groupings"]) == 1

    # sync to latest version of activity
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities/{study_activity_v1.study_activity_uid}/sync-latest-version",
        json={
            "activity_group_uid": general_activity_group.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
        },
    )
    assert_response_status_code(response, 201)
    sa_after_sync = response.json()
    # Synced Activity got new pair of ActivityGroupings, so this change does not influence ProtocolSoA so we don't have to change StudyActivityGroup and StudyActivitySubGroup nodes
    assert (
        sa_after_sync["study_activity_group"]["study_activity_group_uid"]
        == sa_before_sync["study_activity_group"]["study_activity_group_uid"]
    )
    assert (
        sa_after_sync["study_activity_subgroup"]["study_activity_subgroup_uid"]
        == sa_before_sync["study_activity_subgroup"]["study_activity_subgroup_uid"]
    )

    # Update ActivityGroup name
    response = api_client.post(
        f"/concepts/activities/activity-groups/{general_activity_group.uid}/versions"
    )
    assert_response_status_code(response, 201)

    general_activity_group_updated_name = general_activity_group.name + " Updated"
    response = api_client.put(
        f"/concepts/activities/activity-groups/{general_activity_group.uid}",
        json={
            "name": general_activity_group_updated_name,
            "name_sentence_case": general_activity_group_updated_name.lower(),
            "library_name": activity_to_change.library_name,
            "change_description": "Updated name",
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activity-groups/{general_activity_group.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # create new draft version for activity
    response = api_client.post(
        f"/concepts/activities/activities/{activity_to_change.uid}/versions"
    )
    assert_response_status_code(response, 201)

    # update library activity
    activity_name_after_change = "Activity V2"
    response = api_client.put(
        f"/concepts/activities/activities/{activity_to_change.uid}",
        json={
            "name": activity_name_after_change,
            "name_sentence_case": activity_name_after_change.lower(),
            "activity_groupings": [
                {
                    "activity_group_uid": general_activity_group.uid,
                    "activity_subgroup_uid": randomisation_activity_subgroup.uid,
                }
            ],
            "library_name": activity_to_change.library_name,
            "change_description": "Updated name",
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activities/{activity_to_change.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # check if study activity sees that change was made on library level
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activities/{study_activity_v1.study_activity_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["is_activity_updated"] is True
    assert res["latest_activity"]["uid"] == activity_to_change.uid
    assert res["latest_activity"]["name"] == activity_name_after_change
    assert (
        res["latest_activity"]["activity_groupings"][0]["activity_group_name"]
        == general_activity_group_updated_name
    )
    assert res["activity"]["uid"] == activity_to_change.uid
    assert res["activity"]["name"] == activity_name_before_change
    assert (
        res["activity"]["activity_groupings"][0]["activity_group_name"]
        == general_activity_group.name
    )

    # sync to latest version of activity
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities/{study_activity_v1.study_activity_uid}/sync-latest-version",
        json={
            "activity_group_uid": general_activity_group.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
        },
    )
    assert_response_status_code(response, 201)
    sa_after_sync = response.json()
    assert (
        sa_after_sync["study_activity_group"]["study_activity_group_uid"]
        != sa_before_sync["study_activity_group"]["study_activity_group_uid"]
    )
    assert sa_after_sync["is_activity_updated"] is False
    assert sa_after_sync["latest_activity"] is None
    assert sa_after_sync["activity"]["uid"] == activity_to_change.uid
    assert sa_after_sync["activity"]["name"] == activity_name_after_change
    assert (
        sa_after_sync["activity"]["activity_groupings"][0]["activity_group_name"]
        == general_activity_group_updated_name
    )

    assert sa_after_sync["order"] == sa_before_sync["order"]
    assert (
        sa_after_sync["study_soa_group"]["order"]
        == sa_before_sync["study_soa_group"]["order"]
    )
    assert sa_after_sync["study_activity_group"]["order"] == 2
    assert sa_after_sync["study_activity_subgroup"]["order"] == 1

    adverse_events_activity_group = TestUtils.create_activity_group(
        name="Adverse Events"
    )
    adverse_events_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Adverse Events"
    )
    # create new draft version for activity with different groupings
    response = api_client.post(
        f"/concepts/activities/activities/{activity_to_change.uid}/versions"
    )
    assert_response_status_code(response, 201)

    # update library activity
    response = api_client.put(
        f"/concepts/activities/activities/{activity_to_change.uid}",
        json={
            "name": activity_name_after_change,
            "name_sentence_case": activity_name_after_change.lower(),
            "activity_groupings": [
                {
                    "activity_group_uid": adverse_events_activity_group.uid,
                    "activity_subgroup_uid": adverse_events_activity_subgroup.uid,
                }
            ],
            "library_name": activity_to_change.library_name,
            "change_description": "Updated activity groupings",
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activities/{activity_to_change.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # check if study activity sees that change was made on library level
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activities/{study_activity_v1.study_activity_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["is_activity_updated"] is True
    assert len(res["latest_activity"]["activity_groupings"]) == 1
    assert res["latest_activity"]["uid"] == activity_to_change.uid
    assert (
        res["latest_activity"]["activity_groupings"][0]["activity_group_uid"]
        == adverse_events_activity_group.uid
    )
    assert (
        res["latest_activity"]["activity_groupings"][0]["activity_subgroup_uid"]
        == adverse_events_activity_subgroup.uid
    )
    assert len(res["activity"]["activity_groupings"]) == 1
    assert res["activity"]["uid"] == activity_to_change.uid
    assert (
        res["activity"]["activity_groupings"][0]["activity_group_uid"]
        == general_activity_group.uid
    )
    assert (
        res["activity"]["activity_groupings"][0]["activity_subgroup_uid"]
        == randomisation_activity_subgroup.uid
    )

    # Check the Activity update, decide to keep old version
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activities/{study_activity_v1.study_activity_uid}",
        json={
            "keep_old_version": True,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["keep_old_version"] is True

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activities/{study_activity_v1.study_activity_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["keep_old_version"] is True

    # sync to latest version of activity
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities/{study_activity_v1.study_activity_uid}/sync-latest-version",
        json={
            "activity_group_uid": adverse_events_activity_group.uid,
            "activity_subgroup_uid": adverse_events_activity_subgroup.uid,
        },
    )
    assert_response_status_code(response, 201)
    sa_after_sync = response.json()
    assert sa_after_sync["is_activity_updated"] is False
    assert sa_after_sync["latest_activity"] is None
    assert (
        sa_after_sync["study_activity_group"]["activity_group_uid"]
        == adverse_events_activity_group.uid
    )
    assert (
        sa_after_sync["study_activity_subgroup"]["activity_subgroup_uid"]
        == adverse_events_activity_subgroup.uid
    )
    assert (
        sa_after_sync["study_activity_group"]["study_activity_group_uid"]
        != sa_before_sync["study_activity_group"]["study_activity_group_uid"]
    )
    assert (
        sa_after_sync["study_activity_subgroup"]["study_activity_subgroup_uid"]
        != sa_before_sync["study_activity_subgroup"]["study_activity_subgroup_uid"]
    )
    assert sa_after_sync["study_activity_group"]["order"] == 2
    assert sa_after_sync["study_activity_subgroup"]["order"] == 1
    assert sa_after_sync["keep_old_version"] is False


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
            "replacements": [
                {
                    "activity_uid": some_new_activity_in_same_groupings.uid,
                    "activity_subgroup_uid": randomisation_activity_subgroup.uid,
                    "activity_group_uid": general_activity_group.uid,
                    "soa_group_term_uid": term_efficacy_uid,
                }
            ]
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert isinstance(res, list)
    assert len(res) == 1
    res = res[0]
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
        name="new activity subgroup"
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
            "replacements": [
                {
                    "activity_uid": some_new_activity_in_different_groupings.uid,
                    "activity_subgroup_uid": new_activity_subgroup.uid,
                    "activity_group_uid": new_activity_group.uid,
                    "soa_group_term_uid": term_efficacy_uid,
                }
            ]
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert isinstance(res, list)
    assert len(res) == 1
    res = res[0]
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


def test_study_activity_placeholder_replacement_with_multiple_activities(api_client):
    """
    Test replacing a placeholder StudyActivity (activity in Requested library) with multiple activities.
    Verifies that:
    - Exactly 2 study activities are created (not more)
    - The data matches the replacement request (activity, activity group, activity subgroup, soa group)
    - All study activities have the same schedules replicated (and not more)
    """
    study_visit_uid = generic_study_visit.uid

    # Create an activity in the Requested library (placeholder)
    placeholder_activity = TestUtils.create_activity(
        name="Placeholder Activity Request",
        library_name=settings.requested_library_name,
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
    )

    # Create a StudyActivity placeholder with the Requested activity
    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": placeholder_activity.uid,
            "activity_subgroup_uid": None,
            "activity_group_uid": None,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    placeholder_study_activity_uid = res["study_activity_uid"]
    assert res["activity"]["uid"] == placeholder_activity.uid
    assert res["activity"]["library_name"] == settings.requested_library_name

    # Create schedules for the placeholder StudyActivity
    response = api_client.post(
        f"/studies/{study.uid}/study-activity-schedules",
        json={
            "study_activity_uid": placeholder_study_activity_uid,
            "study_visit_uid": study_visit_uid,
        },
    )
    assert_response_status_code(response, 201)

    # Create a second visit for additional schedule
    visit_to_create = generate_default_input_data_for_visit().copy()
    visit_to_create.update(
        {
            "visit_type": {"term_uid": generic_study_visit.visit_type.term_uid},
        }
    )
    second_visit = TestUtils.create_study_visit(
        study_uid=study.uid, study_epoch_uid=epoch_uid, **visit_to_create
    )
    response = api_client.post(
        f"/studies/{study.uid}/study-activity-schedules",
        json={
            "study_activity_uid": placeholder_study_activity_uid,
            "study_visit_uid": second_visit.uid,
        },
    )
    assert_response_status_code(response, 201)

    # Verify schedules exist before replacement
    response = api_client.get(
        f"/studies/{study.uid}/study-activity-schedules",
        params={
            "filters": json.dumps(
                {
                    "study_activity_uid": {
                        "v": [placeholder_study_activity_uid],
                        "op": "eq",
                    }
                }
            ),
            "page_size": 0,
        },
    )
    assert_response_status_code(response, 200)
    schedules_response = response.json()
    # Handle both list and dict with items key
    schedules_before = (
        schedules_response["items"]
        if isinstance(schedules_response, dict)
        else schedules_response
    )
    assert len(schedules_before) == 2

    # Create two sponsor activities to replace the placeholder
    replacement_activity_1 = TestUtils.create_activity(
        name="Replacement Activity 1",
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )
    replacement_activity_2 = TestUtils.create_activity(
        name="Replacement Activity 2",
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )

    # Replace placeholder with 2 activities
    response = api_client.patch(
        f"/studies/{study.uid}/study-activities/{placeholder_study_activity_uid}/activity-replacements",
        json={
            "replacements": [
                {
                    "activity_uid": replacement_activity_1.uid,
                    "activity_subgroup_uid": randomisation_activity_subgroup.uid,
                    "activity_group_uid": general_activity_group.uid,
                    "soa_group_term_uid": term_efficacy_uid,
                },
                {
                    "activity_uid": replacement_activity_2.uid,
                    "activity_subgroup_uid": randomisation_activity_subgroup.uid,
                    "activity_group_uid": general_activity_group.uid,
                    "soa_group_term_uid": term_efficacy_uid,
                },
            ]
        },
    )
    assert_response_status_code(response, 200)
    replacement_res = response.json()
    # Handle case where response might be wrapped
    if isinstance(replacement_res, dict) and "items" in replacement_res:
        replacement_res = replacement_res["items"]
    assert isinstance(
        replacement_res, list
    ), f"Expected list, got {type(replacement_res)}: {replacement_res}"
    assert len(replacement_res) == 2, "Exactly 2 study activities should be created"

    # Verify first replacement (replaced the original placeholder)
    replaced_study_activity = replacement_res[0]
    assert replaced_study_activity["activity"]["uid"] == replacement_activity_1.uid
    assert (
        replaced_study_activity["study_activity_group"]["activity_group_uid"]
        == general_activity_group.uid
    )
    assert (
        replaced_study_activity["study_activity_subgroup"]["activity_subgroup_uid"]
        == randomisation_activity_subgroup.uid
    )
    assert (
        replaced_study_activity["study_soa_group"]["soa_group_term_uid"]
        == term_efficacy_uid
    )
    assert (
        replaced_study_activity["study_activity_uid"] == placeholder_study_activity_uid
    ), "First replacement should keep the same study_activity_uid"

    # Verify second replacement (newly created)
    new_study_activity = replacement_res[1]
    assert new_study_activity["activity"]["uid"] == replacement_activity_2.uid
    assert (
        new_study_activity["study_activity_group"]["activity_group_uid"]
        == general_activity_group.uid
    )
    assert (
        new_study_activity["study_activity_subgroup"]["activity_subgroup_uid"]
        == randomisation_activity_subgroup.uid
    )
    assert (
        new_study_activity["study_soa_group"]["soa_group_term_uid"] == term_efficacy_uid
    )
    assert (
        new_study_activity["study_activity_uid"] != placeholder_study_activity_uid
    ), "Second replacement should have a new study_activity_uid"

    # Verify that exactly 2 study activities exist (not more)
    response = api_client.get(
        f"/studies/{study.uid}/study-activities",
        params={
            "filters": json.dumps(
                {
                    "study_soa_group.soa_group_term_uid": {
                        "v": [term_efficacy_uid],
                        "op": "eq",
                    }
                }
            ),
            "page_size": 0,
        },
    )
    assert_response_status_code(response, 200)
    all_study_activities = response.json()["items"]
    # Filter to only the ones we care about (the 2 replacements)
    relevant_activities = [
        sa
        for sa in all_study_activities
        if sa["study_activity_uid"]
        in [
            replaced_study_activity["study_activity_uid"],
            new_study_activity["study_activity_uid"],
        ]
    ]
    assert (
        len(relevant_activities) == 2
    ), "There should be exactly 2 study activities created, not more"

    # Verify schedules are replicated to both study activities
    # Check schedules for the first (replaced) study activity
    response = api_client.get(
        f"/studies/{study.uid}/study-activity-schedules",
        params={
            "filters": json.dumps(
                {
                    "study_activity_uid": {
                        "v": [replaced_study_activity["study_activity_uid"]],
                        "op": "eq",
                    }
                }
            ),
            "page_size": 0,
        },
    )
    assert_response_status_code(response, 200)
    schedules_response = response.json()
    schedules_replaced = (
        schedules_response["items"]
        if isinstance(schedules_response, dict)
        else schedules_response
    )
    # Filter to only schedules for the replaced StudyActivity to avoid any duplicates
    schedules_replaced = [
        s
        for s in schedules_replaced
        if s["study_activity_uid"] == replaced_study_activity["study_activity_uid"]
    ]
    assert (
        len(schedules_replaced) == 2
    ), f"Replaced study activity should have 2 schedules, but found {len(schedules_replaced)}. Schedules: {[s['study_activity_schedule_uid'] for s in schedules_replaced]}"
    schedule_visit_uids_replaced = {
        schedule["study_visit_uid"] for schedule in schedules_replaced
    }
    assert study_visit_uid in schedule_visit_uids_replaced
    assert second_visit.uid in schedule_visit_uids_replaced

    # Check schedules for the second (newly created) study activity
    response = api_client.get(
        f"/studies/{study.uid}/study-activity-schedules",
        params={
            "filters": json.dumps(
                {
                    "study_activity_uid": {
                        "v": [new_study_activity["study_activity_uid"]],
                        "op": "eq",
                    }
                }
            ),
            "page_size": 0,
        },
    )
    assert_response_status_code(response, 200)
    schedules_response = response.json()
    schedules_new = (
        schedules_response["items"]
        if isinstance(schedules_response, dict)
        else schedules_response
    )
    # Filter to only schedules for the new StudyActivity
    schedules_new = [
        s
        for s in schedules_new
        if s["study_activity_uid"] == new_study_activity["study_activity_uid"]
    ]
    assert (
        len(schedules_new) == 2
    ), f"Newly created study activity should have 2 schedules, but found {len(schedules_new)}. Schedules: {[s['study_activity_schedule_uid'] for s in schedules_new]}"
    schedule_visit_uids_new = {
        schedule["study_visit_uid"] for schedule in schedules_new
    }
    assert study_visit_uid in schedule_visit_uids_new
    assert second_visit.uid in schedule_visit_uids_new

    # Verify that no extra schedules were created (total should be 4: 2 for each activity)
    response = api_client.get(
        f"/studies/{study.uid}/study-activity-schedules",
        params={
            "filters": json.dumps(
                {
                    "study_activity_uid": {
                        "v": [
                            replaced_study_activity["study_activity_uid"],
                            new_study_activity["study_activity_uid"],
                        ],
                        "op": "in",
                    }
                }
            ),
            "page_size": 0,
        },
    )
    assert_response_status_code(response, 200)
    schedules_response = response.json()
    all_schedules = (
        schedules_response["items"]
        if isinstance(schedules_response, dict)
        else schedules_response
    )
    assert (
        len(all_schedules) == 4
    ), "Total schedules should be exactly 4 (2 for each of the 2 study activities), not more"

    replaced_by_relations, _ = db.cypher_query(
        """
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(edit_action:Edit)
            -[:AFTER]->(:StudyActivity {uid: $placeholder_study_activity_uid})
        WITH edit_action
        ORDER BY edit_action.date DESC
        LIMIT 1
        MATCH (edit_action)-[:BEFORE]->(old_placeholder:StudyActivity {uid: $placeholder_study_activity_uid})
        MATCH (old_placeholder)-[:REPLACED_BY]->(replacement:StudyActivity)
        RETURN replacement.uid
        ORDER BY replacement.uid
        """,
        {
            "study_uid": study.uid,
            "placeholder_study_activity_uid": placeholder_study_activity_uid,
        },
    )
    assert [row[0] for row in replaced_by_relations] == sorted(
        [
            replaced_study_activity["study_activity_uid"],
            new_study_activity["study_activity_uid"],
        ]
    )


def test_study_activity_placeholder_single_replacement_creates_replaced_by_link(
    api_client,
):
    test_study = TestUtils.create_study(project_number=project.project_number)

    placeholder_activity = TestUtils.create_activity(
        name="MCP Placeholder Single Replacement",
        library_name=settings.requested_library_name,
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
    )
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": placeholder_activity.uid,
            "activity_subgroup_uid": None,
            "activity_group_uid": None,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    placeholder_study_activity_uid = response.json()["study_activity_uid"]

    replacement_activity = TestUtils.create_activity(
        name="MCP Replacement Single Activity",
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activities/{placeholder_study_activity_uid}/activity-replacements",
        json={
            "replacements": [
                {
                    "activity_uid": replacement_activity.uid,
                    "activity_subgroup_uid": randomisation_activity_subgroup.uid,
                    "activity_group_uid": general_activity_group.uid,
                    "soa_group_term_uid": term_efficacy_uid,
                }
            ]
        },
    )
    assert_response_status_code(response, 200)
    replacement_res = response.json()
    assert len(replacement_res) == 1
    assert replacement_res[0]["study_activity_uid"] == placeholder_study_activity_uid
    assert replacement_res[0]["activity"]["uid"] == replacement_activity.uid

    replaced_by_relations, _ = db.cypher_query(
        """
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(edit_action:Edit)
            -[:AFTER]->(:StudyActivity {uid: $placeholder_study_activity_uid})
        WITH edit_action
        ORDER BY edit_action.date DESC
        LIMIT 1
        MATCH (edit_action)-[:BEFORE]->(old_placeholder:StudyActivity {uid: $placeholder_study_activity_uid})
        MATCH (old_placeholder)-[:REPLACED_BY]->(replacement:StudyActivity)
        RETURN replacement.uid
        ORDER BY replacement.uid
        """,
        {
            "study_uid": test_study.uid,
            "placeholder_study_activity_uid": placeholder_study_activity_uid,
        },
    )
    assert [row[0] for row in replaced_by_relations] == [placeholder_study_activity_uid]


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
        f"/studies/{test_study.uid}/study-activities",
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


def test_study_activity_reordering(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    # create study activity
    randomized_sa = TestUtils.create_study_activity(
        study_uid=test_study.uid,
        activity_uid=randomized_activity.uid,
        activity_group_uid=general_activity_group.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    body_measurement_sa = TestUtils.create_study_activity(
        study_uid=test_study.uid,
        activity_uid=body_mes_activity.uid,
        activity_group_uid=general_activity_group.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    weight_sa1 = TestUtils.create_study_activity(
        study_uid=test_study.uid,
        activity_uid=weight_activity.uid,
        activity_group_uid=general_activity_group.uid,
        activity_subgroup_uid=body_measurements_activity_subgroup.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    weight_sa2 = TestUtils.create_study_activity(
        study_uid=test_study.uid,
        activity_uid=weight_activity.uid,
        activity_group_uid=general_activity_group.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        soa_group_term_uid=term_efficacy_uid,
    )

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 4
    assert study_activities[0]["activity"]["uid"] == randomized_sa.activity.uid
    assert study_activities[0]["study_soa_group"]["order"] == 1
    assert study_activities[0]["study_activity_group"]["order"] == 1
    assert study_activities[0]["study_activity_subgroup"]["order"] == 1
    assert study_activities[0]["order"] == 1
    assert study_activities[1]["activity"]["uid"] == body_measurement_sa.activity.uid
    assert study_activities[1]["study_soa_group"]["order"] == 1
    assert study_activities[1]["study_activity_group"]["order"] == 1
    assert study_activities[1]["study_activity_subgroup"]["order"] == 1
    assert study_activities[1]["order"] == 2
    assert study_activities[2]["activity"]["uid"] == weight_sa2.activity.uid
    assert study_activities[2]["study_soa_group"]["order"] == 1
    assert study_activities[2]["study_activity_group"]["order"] == 1
    assert study_activities[2]["study_activity_subgroup"]["order"] == 1
    assert study_activities[2]["order"] == 3
    assert study_activities[3]["activity"]["uid"] == weight_sa1.activity.uid
    assert study_activities[3]["study_soa_group"]["order"] == 1
    assert study_activities[3]["study_activity_group"]["order"] == 1
    assert study_activities[3]["study_activity_subgroup"]["order"] == 2
    assert study_activities[3]["order"] == 1

    # Change SoA of first SA, all other should be reordered
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activities/{randomized_sa.study_activity_uid}",
        json={
            "soa_group_term_uid": informed_consent_uid,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity"]["uid"] == randomized_sa.activity.uid
    assert res["study_soa_group"]["order"] == 2
    assert res["study_activity_group"]["order"] == 1
    assert res["study_activity_subgroup"]["order"] == 1
    assert res["order"] == 1

    # Get all SA after SoA patch
    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]

    assert len(study_activities) == 4
    assert study_activities[0]["activity"]["uid"] == body_measurement_sa.activity.uid
    assert study_activities[0]["study_soa_group"]["order"] == 1
    assert study_activities[0]["study_activity_group"]["order"] == 1
    assert study_activities[0]["study_activity_subgroup"]["order"] == 1
    assert study_activities[0]["order"] == 1
    assert study_activities[1]["activity"]["uid"] == weight_sa2.activity.uid
    assert study_activities[1]["study_soa_group"]["order"] == 1
    assert study_activities[1]["study_activity_group"]["order"] == 1
    assert study_activities[1]["study_activity_subgroup"]["order"] == 1
    assert study_activities[1]["order"] == 2
    assert study_activities[2]["activity"]["uid"] == weight_sa1.activity.uid
    assert study_activities[2]["study_soa_group"]["order"] == 1
    assert study_activities[2]["study_activity_group"]["order"] == 1
    assert study_activities[2]["study_activity_subgroup"]["order"] == 2
    assert study_activities[2]["order"] == 1
    assert study_activities[3]["activity"]["uid"] == randomized_sa.activity.uid
    assert study_activities[3]["study_soa_group"]["order"] == 2
    assert study_activities[3]["study_activity_group"]["order"] == 1
    assert study_activities[3]["study_activity_subgroup"]["order"] == 1
    assert study_activities[3]["order"] == 1

    # Reorder first SA
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activities/{weight_sa2.study_activity_uid}/order",
        json={
            "new_order": 3,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == f"The maximum new order is (2) as there are 2 Study Activities in {randomisation_activity_subgroup.name} subgroup and order (3) was requested"
    )

    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activities/{weight_sa2.study_activity_uid}/order",
        json={
            "new_order": 2,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == f"The order (2) for study activity {weight_sa2.activity.name} was not changed"
    )

    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activities/{weight_sa2.study_activity_uid}/order",
        json={
            "new_order": 1,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity"]["uid"] == weight_sa2.activity.uid
    assert res["study_soa_group"]["order"] == 1
    assert res["study_activity_group"]["order"] == 1
    assert res["study_activity_subgroup"]["order"] == 1
    assert res["order"] == 1

    # Get all SA after SA reorder
    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 4
    assert study_activities[0]["activity"]["uid"] == weight_sa2.activity.uid
    assert study_activities[0]["study_soa_group"]["order"] == 1
    assert study_activities[0]["study_activity_group"]["order"] == 1
    assert study_activities[0]["study_activity_subgroup"]["order"] == 1
    assert study_activities[0]["order"] == 1
    assert study_activities[1]["activity"]["uid"] == body_measurement_sa.activity.uid
    assert study_activities[1]["study_soa_group"]["order"] == 1
    assert study_activities[1]["study_activity_group"]["order"] == 1
    assert study_activities[1]["study_activity_subgroup"]["order"] == 1
    assert study_activities[1]["order"] == 2
    assert study_activities[2]["activity"]["uid"] == weight_sa1.activity.uid
    assert study_activities[2]["study_soa_group"]["order"] == 1
    assert study_activities[2]["study_activity_group"]["order"] == 1
    assert study_activities[2]["study_activity_subgroup"]["order"] == 2
    assert study_activities[2]["order"] == 1
    assert study_activities[3]["activity"]["uid"] == randomized_sa.activity.uid
    assert study_activities[3]["study_soa_group"]["order"] == 2
    assert study_activities[3]["study_activity_group"]["order"] == 1
    assert study_activities[3]["study_activity_subgroup"]["order"] == 1
    assert study_activities[3]["order"] == 1

    # Delete SA and check orders
    response = api_client.delete(
        f"/studies/{test_study.uid}/study-activities/{weight_sa2.study_activity_uid}"
    )
    assert_response_status_code(response, 204)

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 3

    assert study_activities[0]["activity"]["uid"] == body_measurement_sa.activity.uid
    assert study_activities[0]["study_soa_group"]["order"] == 1
    assert study_activities[0]["study_activity_group"]["order"] == 1
    assert study_activities[0]["study_activity_subgroup"]["order"] == 1
    assert study_activities[0]["order"] == 1
    assert study_activities[1]["activity"]["uid"] == weight_sa1.activity.uid
    assert study_activities[1]["study_soa_group"]["order"] == 1
    assert study_activities[1]["study_activity_group"]["order"] == 1
    assert study_activities[1]["study_activity_subgroup"]["order"] == 2
    assert study_activities[1]["order"] == 1
    assert study_activities[2]["activity"]["uid"] == randomized_sa.activity.uid
    assert study_activities[2]["study_soa_group"]["order"] == 2
    assert study_activities[2]["study_activity_group"]["order"] == 1
    assert study_activities[2]["study_activity_subgroup"]["order"] == 1
    assert study_activities[2]["order"] == 1

    # Delete SA from subgroup to see if subgroup gets reordered
    response = api_client.delete(
        f"/studies/{test_study.uid}/study-activities/{body_measurement_sa.study_activity_uid}"
    )
    assert_response_status_code(response, 204)
    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 2
    assert study_activities[0]["activity"]["uid"] == weight_sa1.activity.uid
    assert study_activities[0]["study_soa_group"]["order"] == 1
    assert study_activities[0]["study_activity_group"]["order"] == 1
    assert study_activities[0]["study_activity_subgroup"]["order"] == 1
    assert study_activities[0]["order"] == 1
    assert study_activities[1]["activity"]["uid"] == randomized_sa.activity.uid
    assert study_activities[1]["study_soa_group"]["order"] == 2
    assert study_activities[1]["study_activity_group"]["order"] == 1
    assert study_activities[1]["study_activity_subgroup"]["order"] == 1
    assert study_activities[1]["order"] == 1

    # Delete last SA from SoAGroup to see if SoAGroup gets reordered
    response = api_client.delete(
        f"/studies/{test_study.uid}/study-activities/{weight_sa1.study_activity_uid}"
    )
    assert_response_status_code(response, 204)

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 1
    assert study_activities[0]["activity"]["uid"] == randomized_sa.activity.uid
    assert study_activities[0]["study_soa_group"]["order"] == 1
    assert study_activities[0]["study_activity_group"]["order"] == 1
    assert study_activities[0]["study_activity_subgroup"]["order"] == 1
    assert study_activities[0]["order"] == 1


# pylint: disable=too-many-statements
def test_study_activity_placeholder_reordering(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    # create study activity
    activity_request_1 = TestUtils.create_activity(
        name="Activity request 1",
        library_name=settings.requested_library_name,
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
    )
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": activity_request_1.uid,
            "activity_subgroup_uid": None,
            "activity_group_uid": None,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    activity_placeholder_1_uid = res["study_activity_uid"]

    activity_request_2 = TestUtils.create_activity(
        name="Activity request 2",
        library_name=settings.requested_library_name,
    )
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": activity_request_2.uid,
            "activity_subgroup_uid": None,
            "activity_group_uid": None,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    activity_placeholder_2_uid = res["study_activity_uid"]

    activity_request_3 = TestUtils.create_activity(
        name="Activity request 3",
        library_name=settings.requested_library_name,
    )
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": activity_request_3.uid,
            "activity_subgroup_uid": None,
            "activity_group_uid": None,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    activity_placeholder_3_uid = res["study_activity_uid"]

    randomized_sa = TestUtils.create_study_activity(
        study_uid=test_study.uid,
        activity_uid=randomized_activity.uid,
        activity_group_uid=general_activity_group.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        soa_group_term_uid=term_efficacy_uid,
    )

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 4
    assert study_activities[0]["activity"]["uid"] == activity_request_1.uid
    assert study_activities[0]["study_soa_group"]["order"] == 1
    assert study_activities[0]["study_activity_group"]["order"] is None
    assert study_activities[0]["study_activity_subgroup"]["order"] is None
    assert study_activities[0]["order"] == 1
    assert study_activities[1]["activity"]["uid"] == activity_request_2.uid
    assert study_activities[1]["study_soa_group"]["order"] == 1
    assert study_activities[1]["study_activity_group"]["order"] is None
    assert study_activities[1]["study_activity_subgroup"]["order"] is None
    assert study_activities[1]["order"] == 2
    assert study_activities[2]["activity"]["uid"] == activity_request_3.uid
    assert study_activities[2]["study_soa_group"]["order"] == 1
    assert study_activities[2]["study_activity_group"]["order"] is None
    assert study_activities[2]["study_activity_subgroup"]["order"] is None
    assert study_activities[2]["order"] == 3
    assert study_activities[3]["activity"]["uid"] == randomized_sa.activity.uid
    assert study_activities[3]["study_soa_group"]["order"] == 1
    assert study_activities[3]["study_activity_group"]["order"] == 1
    assert study_activities[3]["study_activity_subgroup"]["order"] == 1
    assert study_activities[3]["order"] == 1

    # Change SoA of first SA, all other should be reordered
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-requests/{activity_placeholder_2_uid}",
        json={
            "soa_group_term_uid": informed_consent_uid,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity"]["uid"] == activity_request_2.uid
    assert res["study_soa_group"]["order"] == 2
    assert res["study_activity_group"]["order"] is None
    assert res["study_activity_subgroup"]["order"] is None
    assert res["order"] == 1

    # Get all SA after SoA patch
    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]

    assert len(study_activities) == 4
    assert study_activities[0]["activity"]["uid"] == activity_request_1.uid
    assert study_activities[0]["study_soa_group"]["order"] == 1
    assert study_activities[0]["study_activity_group"]["order"] is None
    assert study_activities[0]["study_activity_subgroup"]["order"] is None
    assert study_activities[0]["order"] == 1
    assert study_activities[1]["activity"]["uid"] == activity_request_3.uid
    assert study_activities[1]["study_soa_group"]["order"] == 1
    assert study_activities[1]["study_activity_group"]["order"] is None
    assert study_activities[1]["study_activity_subgroup"]["order"] is None
    assert study_activities[1]["order"] == 2
    assert study_activities[2]["activity"]["uid"] == randomized_sa.activity.uid
    assert study_activities[2]["study_soa_group"]["order"] == 1
    assert study_activities[2]["study_activity_group"]["order"] == 1
    assert study_activities[2]["study_activity_subgroup"]["order"] == 1
    assert study_activities[2]["order"] == 1
    assert study_activities[3]["activity"]["uid"] == activity_request_2.uid
    assert study_activities[3]["study_soa_group"]["order"] == 2
    assert study_activities[3]["study_activity_group"]["order"] is None
    assert study_activities[3]["study_activity_subgroup"]["order"] is None
    assert study_activities[3]["order"] == 1

    # Reorder first SA
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activities/{activity_placeholder_1_uid}/order",
        json={
            "new_order": 2,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity"]["uid"] == activity_request_1.uid
    assert res["study_soa_group"]["order"] == 1
    assert res["study_activity_group"]["order"] is None
    assert res["study_activity_subgroup"]["order"] is None
    assert res["order"] == 2

    # Get all SA after SA reorder
    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 4
    assert study_activities[0]["activity"]["uid"] == activity_request_3.uid
    assert study_activities[0]["study_soa_group"]["order"] == 1
    assert study_activities[0]["study_activity_group"]["order"] is None
    assert study_activities[0]["study_activity_subgroup"]["order"] is None
    assert study_activities[0]["order"] == 1
    assert study_activities[1]["activity"]["uid"] == activity_request_1.uid
    assert study_activities[1]["study_soa_group"]["order"] == 1
    assert study_activities[1]["study_activity_group"]["order"] is None
    assert study_activities[1]["study_activity_subgroup"]["order"] is None
    assert study_activities[1]["order"] == 2
    assert study_activities[2]["activity"]["uid"] == randomized_sa.activity.uid
    assert study_activities[2]["study_soa_group"]["order"] == 1
    assert study_activities[2]["study_activity_group"]["order"] == 1
    assert study_activities[2]["study_activity_subgroup"]["order"] == 1
    assert study_activities[2]["order"] == 1
    assert study_activities[3]["activity"]["uid"] == activity_request_2.uid
    assert study_activities[3]["study_soa_group"]["order"] == 2
    assert study_activities[3]["study_activity_group"]["order"] is None
    assert study_activities[3]["study_activity_subgroup"]["order"] is None
    assert study_activities[3]["order"] == 1

    # Delete SA and check orders
    response = api_client.delete(
        f"/studies/{test_study.uid}/study-activities/{activity_placeholder_3_uid}"
    )
    assert_response_status_code(response, 204)

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 3
    assert study_activities[0]["activity"]["uid"] == activity_request_1.uid
    assert study_activities[0]["study_soa_group"]["order"] == 1
    assert study_activities[0]["study_activity_group"]["order"] is None
    assert study_activities[0]["study_activity_subgroup"]["order"] is None
    assert study_activities[0]["order"] == 1
    assert study_activities[1]["activity"]["uid"] == randomized_sa.activity.uid
    assert study_activities[1]["study_soa_group"]["order"] == 1
    assert study_activities[1]["study_activity_group"]["order"] == 1
    assert study_activities[1]["study_activity_subgroup"]["order"] == 1
    assert study_activities[1]["order"] == 1
    assert study_activities[2]["activity"]["uid"] == activity_request_2.uid
    assert study_activities[2]["study_soa_group"]["order"] == 2
    assert study_activities[2]["study_activity_group"]["order"] is None
    assert study_activities[2]["study_activity_subgroup"]["order"] is None
    assert study_activities[2]["order"] == 1

    # Change Groupings of StudyActivity placeholder to verify the orders
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-requests/{activity_placeholder_1_uid}",
        json={
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity"]["uid"] == activity_request_1.uid
    assert res["study_soa_group"]["order"] == 1
    assert res["study_activity_group"]["order"] == 1
    assert res["study_activity_subgroup"]["order"] == 1
    assert res["order"] == 2

    # Change Groupings of StudyActivity placeholder to verify the orders
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-requests/{activity_placeholder_2_uid}",
        json={
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity"]["uid"] == activity_request_2.uid
    assert res["study_soa_group"]["order"] == 1
    assert res["study_activity_group"]["order"] == 1
    assert res["study_activity_subgroup"]["order"] == 1
    assert res["order"] == 3

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 3
    assert study_activities[0]["activity"]["uid"] == randomized_sa.activity.uid
    assert study_activities[0]["study_soa_group"]["order"] == 1
    assert study_activities[0]["study_activity_group"]["order"] == 1
    assert study_activities[0]["study_activity_subgroup"]["order"] == 1
    assert study_activities[0]["order"] == 1
    assert study_activities[1]["activity"]["uid"] == activity_request_1.uid
    assert study_activities[1]["study_soa_group"]["order"] == 1
    assert study_activities[1]["study_activity_group"]["order"] == 1
    assert study_activities[1]["study_activity_subgroup"]["order"] == 1
    assert study_activities[1]["order"] == 2
    assert study_activities[2]["activity"]["uid"] == activity_request_2.uid
    assert study_activities[2]["study_soa_group"]["order"] == 1
    assert study_activities[2]["study_activity_group"]["order"] == 1
    assert study_activities[2]["study_activity_subgroup"]["order"] == 1
    assert study_activities[2]["order"] == 3


def test_only_final_activity_can_be_selected_to_study(api_client):
    # Test only Final Activity can be added to Study
    draft_or_retired_activity = TestUtils.create_activity(
        name="Draft/Retired Activity",
        activity_subgroups=[
            randomisation_activity_subgroup.uid,
        ],
        activity_groups=[general_activity_group.uid],
        approve=False,
    )
    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": draft_or_retired_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == f"There is no approved Activity with name '{draft_or_retired_activity.name}'."
    )

    # Approve
    response = api_client.post(
        f"/concepts/activities/activities/{draft_or_retired_activity.uid}/approvals"
    )
    assert_response_status_code(response, 201)
    # Retire
    response = api_client.delete(
        f"/concepts/activities/activities/{draft_or_retired_activity.uid}/activations"
    )
    assert_response_status_code(response, 200)

    response = api_client.post(
        f"/studies/{study.uid}/study-activities",
        json={
            "activity_uid": draft_or_retired_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == f"There is no approved Activity with name '{draft_or_retired_activity.name}'."
    )


def test_cross_soa_group_duplicate_study_activity_blocked_on_create(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)

    cross_scope_activity = TestUtils.create_activity(
        name="CrossScopeActivity",
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
    )

    # First selection under Efficacy → succeeds
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": cross_scope_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)

    # Second selection under Safety (different SoA group, same activity+groupings) → 409
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": cross_scope_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": informed_consent_uid,
        },
    )
    assert_response_status_code(response, 409)
    res = response.json()
    assert (
        res["message"]
        == f"There is already a Study Selection to the activity with Name '{cross_scope_activity.name}' with the same groupings."
    )


def test_clone_big_study_with_study_activity_flags_enabled(api_client):
    response = api_client.post(
        "/studies/Study_000001/clone",
        json={
            "study_number": "9001",
            "study_acronym": "9001",
            "project_number": project.project_number,
            "description": "Clone with study activity flags enabled",
            "copy_study_arm": True,
            "copy_study_branch_arm": True,
            "copy_study_cohort": True,
            "copy_study_element": True,
            "copy_study_visit": True,
            "copy_study_epoch": True,
            "copy_study_visits_study_footnote": True,
            "copy_study_epochs_study_footnote": True,
            "copy_study_design_matrix": True,
            "copy_study_soa_group": True,
            "copy_study_activity_group": True,
            "copy_study_activity_subgroup": True,
            "copy_study_activity": True,
            "copy_study_activity_instance": True,
            "copy_study_activity_schedule": True,
            "validation_mode": ValidationMode.WARNING.value,
        },
    )
    assert_response_status_code(response, 201)
    study_cloned = response.json()
    assert study_cloned["uid"] != "Study_000001"


def test_clone_copies_soa_footnotes_for_activity_related_selections(api_client):
    source_study = TestUtils.create_study(
        project_number=project.project_number,
        acronym="MCPACTFN",
    )

    source_epoch = create_study_epoch("EpochSubType_0001", study_uid=source_study.uid)
    source_visit = TestUtils.create_study_visit(
        study_uid=source_study.uid,
        study_epoch_uid=source_epoch.uid,
        **generate_default_input_data_for_visit(),
    )

    activity_group = TestUtils.create_activity_group(name="Activity Group")
    activity_subgroup = TestUtils.create_activity_subgroup(name="Activity Subgroup")
    activity = TestUtils.create_activity(
        name="Activity",
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
    )

    source_study_activity = create_study_activity(
        study_uid=source_study.uid,
        activity_uid=activity.uid,
        activity_subgroup_uid=activity_subgroup.uid,
        activity_group_uid=activity_group.uid,
        soa_group_term_uid=term_efficacy_uid,
    )
    source_study_activity_schedule = TestUtils.create_study_activity_schedule(
        study_uid=source_study.uid,
        study_activity_uid=source_study_activity.study_activity_uid,
        study_visit_uid=source_visit.uid,
    )

    catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    ftnttp_codelist = create_codelist(
        name="Footnote Type",
        uid=f"FTNTTP{source_study.uid[-6:]}",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="FTNTTP",
    )
    TestUtils.create_ct_term(
        codelist_uid=ftnttp_codelist.codelist_uid,
        submission_value=f"FT{source_study.uid[-4:]}",
        sponsor_preferred_name="Footnote Type",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        approve=True,
    )

    footnote = TestUtils.create_footnote()
    TestUtils.create_study_soa_footnote(
        study_uid=source_study.uid,
        footnote_uid=footnote.uid,
        referenced_items=[
            ReferencedItem(
                item_uid=source_study_activity.study_soa_group.study_soa_group_uid,
                item_type=SoAItemType.STUDY_SOA_GROUP,
            ),
            ReferencedItem(
                item_uid=source_study_activity.study_activity_group.study_activity_group_uid,
                item_type=SoAItemType.STUDY_ACTIVITY_GROUP,
            ),
            ReferencedItem(
                item_uid=source_study_activity.study_activity_subgroup.study_activity_subgroup_uid,
                item_type=SoAItemType.STUDY_ACTIVITY_SUBGROUP,
            ),
            ReferencedItem(
                item_uid=source_study_activity.study_activity_uid,
                item_type=SoAItemType.STUDY_ACTIVITY,
            ),
            ReferencedItem(
                item_uid=source_study_activity_schedule.study_activity_schedule_uid,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            ),
        ],
    )

    clone_response = api_client.post(
        f"/studies/{source_study.uid}/clone",
        json={
            "study_number": "9909",
            "study_acronym": "MCPACTFNC",
            "project_number": project.project_number,
            "description": "Clone activity footnotes",
            "copy_study_arm": False,
            "copy_study_branch_arm": False,
            "copy_study_cohort": False,
            "copy_study_element": False,
            "copy_study_visit": True,
            "copy_study_epoch": True,
            "copy_study_visits_study_footnote": False,
            "copy_study_epochs_study_footnote": False,
            "copy_study_design_matrix": False,
            "copy_study_soa_group": True,
            "copy_study_activity_group": True,
            "copy_study_activity_subgroup": True,
            "copy_study_activity": True,
            "copy_study_activity_instance": False,
            "copy_study_activity_schedule": True,
            "validation_mode": ValidationMode.WARNING.value,
        },
    )
    assert_response_status_code(clone_response, 201)
    cloned_study_uid = clone_response.json()["uid"]

    cloned_footnote_count, _ = db.cypher_query(
        """
        MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)-[:HAS_STUDY_FOOTNOTE]->(sf:StudySoAFootnote)
        RETURN count(sf)
        """,
        {"study_uid": cloned_study_uid},
    )
    assert cloned_footnote_count[0][0] == 1

    cloned_reference_counts, _ = db.cypher_query(
        """
        MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)-[:HAS_STUDY_FOOTNOTE]->(sf:StudySoAFootnote)
        RETURN
            SIZE([(sf)-[:REFERENCES_STUDY_SOA_GROUP]->(:StudySoAGroup) | 1]) AS soa_group_ref_count,
            SIZE([(sf)-[:REFERENCES_STUDY_ACTIVITY_GROUP]->(:StudyActivityGroup) | 1]) AS activity_group_ref_count,
            SIZE([(sf)-[:REFERENCES_STUDY_ACTIVITY_SUBGROUP]->(:StudyActivitySubGroup) | 1]) AS activity_subgroup_ref_count,
            SIZE([(sf)-[:REFERENCES_STUDY_ACTIVITY]->(:StudyActivity) | 1]) AS activity_ref_count,
            SIZE([(sf)-[:REFERENCES_STUDY_ACTIVITY_SCHEDULE]->(:StudyActivitySchedule) | 1]) AS activity_schedule_ref_count
        """,
        {"study_uid": cloned_study_uid},
    )
    (
        soa_group_ref_count,
        activity_group_ref_count,
        activity_subgroup_ref_count,
        activity_ref_count,
        activity_schedule_ref_count,
    ) = cloned_reference_counts[0]
    assert soa_group_ref_count == 1
    assert activity_group_ref_count == 1
    assert activity_subgroup_ref_count == 1
    assert activity_ref_count == 1
    assert activity_schedule_ref_count == 1


def test_cross_soa_group_duplicate_study_activity_blocked_on_patch(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)

    # Create an activity linked to two subgroups under the same group
    subgroup_a = TestUtils.create_activity_subgroup(name="PatchDupSubgroupA")
    subgroup_b = TestUtils.create_activity_subgroup(name="PatchDupSubgroupB")
    patch_dup_activity = TestUtils.create_activity(
        name="PatchDuplicateActivity",
        activity_subgroups=[subgroup_a.uid, subgroup_b.uid],
        activity_groups=[general_activity_group.uid, general_activity_group.uid],
    )

    # First study activity: subgroup A under Efficacy SoA group
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": patch_dup_activity.uid,
            "activity_subgroup_uid": subgroup_a.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)

    # Second study activity: subgroup B under a *different* SoA group (Safety)
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": patch_dup_activity.uid,
            "activity_subgroup_uid": subgroup_b.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": informed_consent_uid,
        },
    )
    assert_response_status_code(response, 201)
    second_study_activity_uid = response.json()["study_activity_uid"]

    # Patch second: subgroup B → A. Same groupings but different SoA groups → 409
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activities/{second_study_activity_uid}",
        json={
            "activity_subgroup_uid": subgroup_a.uid,
            "activity_group_uid": general_activity_group.uid,
        },
    )
    assert_response_status_code(response, 409)
    res = response.json()
    assert (
        res["message"]
        == f"There is already a Study Selection to the activity with Name '{patch_dup_activity.name}' with the same groupings."
    )


def test_sync_latest_version_blocked_when_target_grouping_already_exists(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)

    sync_subgroup = TestUtils.create_activity_subgroup(name="SyncDupSubgroup")
    group_a = TestUtils.create_activity_group(name="SyncDupGroupA")
    group_b = TestUtils.create_activity_group(name="SyncDupGroupB")
    sync_activity = TestUtils.create_activity(
        name="SyncDuplicateActivity",
        activity_subgroups=[sync_subgroup.uid, sync_subgroup.uid],
        activity_groups=[group_a.uid, group_b.uid],
    )

    # Study activity #1: (subgroup, group_a) under Efficacy
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": sync_activity.uid,
            "activity_subgroup_uid": sync_subgroup.uid,
            "activity_group_uid": group_a.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    first_study_activity_uid = response.json()["study_activity_uid"]

    # Study activity #2: (subgroup, group_b) under the same SoA group (Efficacy)
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": sync_activity.uid,
            "activity_subgroup_uid": sync_subgroup.uid,
            "activity_group_uid": group_b.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)

    # --- Modify the subgroup at library level so its version advances ---
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{sync_subgroup.uid}/versions"
    )
    assert_response_status_code(response, 201)
    response = api_client.put(
        f"/concepts/activities/activity-sub-groups/{sync_subgroup.uid}",
        json={
            "name": sync_subgroup.name,
            "name_sentence_case": sync_subgroup.name.lower(),
            "library_name": sync_subgroup.library_name,
            "activity_groups": [group_a.uid, group_b.uid],
            "change_description": "Version bump to cause sync_latest_version divergence",
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{sync_subgroup.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # --- Update the activity at library level: remove group_a ---
    response = api_client.post(
        f"/concepts/activities/activities/{sync_activity.uid}/versions"
    )
    assert_response_status_code(response, 201)

    response = api_client.put(
        f"/concepts/activities/activities/{sync_activity.uid}",
        json={
            "name": sync_activity.name,
            "name_sentence_case": sync_activity.name.lower(),
            "activity_groupings": [
                {
                    "activity_group_uid": group_b.uid,
                    "activity_subgroup_uid": sync_subgroup.uid,
                },
            ],
            "library_name": sync_activity.library_name,
            "change_description": "Removed group_a, only group_b remains",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.post(
        f"/concepts/activities/activities/{sync_activity.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # Verify first study activity sees a newer version is available
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activities/{first_study_activity_uid}"
    )
    assert_response_status_code(response, 200)
    assert response.json()["latest_activity"] is not None

    # --- Sync first study activity to latest, requesting (subgroup, group_b) ---
    # That grouping is already used by study activity #2 → should be blocked
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities/{first_study_activity_uid}/sync-latest-version",
        json={
            "activity_group_uid": group_b.uid,
            "activity_subgroup_uid": sync_subgroup.uid,
        },
    )
    assert_response_status_code(response, 409)
    res = response.json()
    assert (
        res["message"]
        == f"There is already a Study Selection to the activity with Name '{sync_activity.name}' with the same groupings."
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
        "visit_type": {"term_uid": "VisitType_0001"},
        "show_visit": True,
        "time_reference": {"term_uid": "VisitSubType_0005"},
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
    assert_response_status_code(response, 207)

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    assert len(study_activities) == 1
    assert study_activities[0]["show_activity_in_protocol_flowchart"] is True

    response = api_client.get(f"/studies/{test_study.uid}/study-activity-schedules")
    assert_response_status_code(response, 200)
    study_activity_schedules = response.json()
    assert len(study_activity_schedules) == 0


def test_study_activities_review_changes_batch(api_client):
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

    # Retire Activity
    response = api_client.delete(
        f"/concepts/activities/activities/{weight_activity.uid}/activations"
    )
    assert_response_status_code(response, 200)

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    for sa in study_activities:
        assert sa["latest_activity"] is not None
        assert sa["latest_activity"]["uid"] == weight_activity.uid
        assert sa["latest_activity"]["status"] == "Retired"
        assert sa["activity"]["uid"] == weight_activity.uid
        assert sa["activity"]["status"] == "Final"

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities/changes-review/batch",
        json=[
            {
                "action": StudySelectionReviewAction.DECLINE.value,
                "uid": randomisation_sactivity,
                "content": {
                    "keep_old_version": True,
                },
            },
            {
                "action": StudySelectionReviewAction.DECLINE.value,
                "uid": body_measurements_sactivity,
                "content": {
                    "keep_old_version": True,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)
    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    study_activities = response.json()["items"]
    for sa in study_activities:
        assert sa["keep_old_version"] is True
        assert sa["latest_activity"] is not None
        assert sa["latest_activity"]["uid"] == weight_activity.uid
        assert sa["latest_activity"]["status"] == "Retired"
        assert sa["activity"]["uid"] == weight_activity.uid
        assert sa["activity"]["status"] == "Final"

    # Reactivate Activity
    response = api_client.post(
        f"/concepts/activities/activities/{weight_activity.uid}/activations"
    )
    assert_response_status_code(response, 200)

    # create new draft version for activity
    response = api_client.post(
        f"/concepts/activities/activities/{weight_activity.uid}/versions"
    )
    assert_response_status_code(response, 201)

    # update library activity
    activity_name_after_change = "Activity Weight V2"
    response = api_client.put(
        f"/concepts/activities/activities/{weight_activity.uid}",
        json={
            "name": activity_name_after_change,
            "name_sentence_case": activity_name_after_change.lower(),
            "activity_groupings": [
                {
                    "activity_group_uid": general_activity_group.uid,
                    "activity_subgroup_uid": randomisation_activity_subgroup.uid,
                },
                {
                    "activity_group_uid": general_activity_group.uid,
                    "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
                },
            ],
            "library_name": weight_activity.library_name,
            "change_description": "Updated name",
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activities/{weight_activity.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # Retire Randomisation Subgroup
    response = api_client.delete(
        f"/concepts/activities/activity-sub-groups/{randomisation_activity_subgroup.uid}/activations"
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activities?filter_out_retired_groupings=true"
    )
    assert_response_status_code(response, 200)

    res = response.json()["items"][0]
    # Randomisation subgroups gets Retired so it got filtered out from /study-activities response
    # so it couldn't be used in the StudyActivity version update form
    assert len(res["latest_activity"]["activity_groupings"]) == 1
    assert len(res["activity"]["activity_groupings"]) == 2

    response = api_client.get(f"/concepts/activities/activities/{weight_activity.uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["activity_groupings"]) == 2

    # Reactivate Randomisation Subgroup
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{randomisation_activity_subgroup.uid}/activations"
    )
    assert_response_status_code(response, 200)

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities/changes-review/batch",
        json=[
            {
                "action": StudySelectionReviewAction.ACCEPT.value,
                "uid": randomisation_sactivity,
                "content": {
                    "activity_group_uid": general_activity_group.uid,
                    "activity_subgroup_uid": randomisation_activity_subgroup.uid,
                },
            },
            {
                "action": StudySelectionReviewAction.DECLINE.value,
                "uid": body_measurements_sactivity,
                "content": {
                    "keep_old_version": True,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activities/{randomisation_sactivity}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["latest_activity"] is None
    assert res["activity"]["name"] == activity_name_after_change
    assert res["keep_old_version"] is False

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activities/{body_measurements_sactivity}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["latest_activity"]["name"] == activity_name_after_change
    assert res["activity"]["name"] == weight_activity.name
    assert res["keep_old_version"] is True


def test_study_activity_should_link_subgroup_and_group_version_based_on_the_version_linked_by_activity(
    api_client,
):
    test_study = TestUtils.create_study(project_number=project.project_number)
    response = api_client.post(
        f"/concepts/activities/activity-groups/{general_activity_group.uid}/versions",
    )
    assert_response_status_code(response, 201)
    response = api_client.put(
        f"/concepts/activities/activity-groups/{general_activity_group.uid}",
        json={
            "name": general_activity_group.name + "V2",
            "name_sentence_case": general_activity_group.name_sentence_case + "v2",
            "change_description": "V2",
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activity-groups/{general_activity_group.uid}/approvals",
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/concepts/activities/activities/{randomized_activity.uid}",
    )
    assert_response_status_code(response, 200)
    randomized_activity_after_group_update = response.json()

    assert (
        randomized_activity_after_group_update["activity_groupings"][0][
            "activity_group_uid"
        ]
        == general_activity_group.uid
    )
    group_version_linked_by_activity = randomized_activity_after_group_update[
        "activity_groupings"
    ][0]["activity_group_version"]
    response = api_client.get(
        f"/concepts/activities/activity-groups/{general_activity_group.uid}/versions",
    )
    assert_response_status_code(response, 200)
    group_versions = response.json()
    group_in_specific_version = None
    for group_ver in group_versions:
        if group_ver["version"] == group_version_linked_by_activity:
            group_in_specific_version = group_ver

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": randomized_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert (
        res["study_activity_group"]["activity_group_name"]
        == group_in_specific_version["name"]
    )


def test_study_activity_invalidate_keep_old_version(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    test_activity = TestUtils.create_activity(
        name="Test activity",
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": test_activity.uid,
            "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    study_activity_uid = response.json()["study_activity_uid"]

    response = api_client.delete(
        f"/concepts/activities/activities/{test_activity.uid}/activations"
    )
    assert_response_status_code(response, 200)

    # Known limitation: get by uid returns same activity for latest_activity and activity when activity is retired.
    # It should return Retired one as latest_activity and Final one as activity.
    # As temporary fix calling get all that works fine as for now.
    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    res = response.json()["items"]

    assert res[0]["keep_old_version"] is False
    assert res[0]["activity"]["status"] == "Final"
    assert res[0]["latest_activity"]["status"] == "Retired"

    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activities/{study_activity_uid}",
        json={
            "keep_old_version": True,
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res[0]["keep_old_version"] is True
    assert res[0]["activity"]["status"] == "Final"
    assert res[0]["latest_activity"]["status"] == "Retired"

    response = api_client.post(
        f"/concepts/activities/activities/{test_activity.uid}/activations"
    )
    assert_response_status_code(response, 200)

    response = api_client.post(
        f"/concepts/activities/activities/{test_activity.uid}/versions"
    )
    assert_response_status_code(response, 201)
    activity = response.json()

    updated_name = test_activity.name + " updated"
    response = api_client.put(
        f"/concepts/activities/activities/{test_activity.uid}",
        json={
            "name": updated_name,
            "name_sentence_case": updated_name.lower(),
            "activity_groupings": activity["activity_groupings"],
            "library_name": test_activity.library_name,
            "change_description": "Updated name",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.post(
        f"/concepts/activities/activities/{test_activity.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res[0]["keep_old_version"] is False
    assert res[0]["activity"]["status"] == "Final"
    assert res[0]["latest_activity"]["status"] == "Final"
    assert res[0]["latest_activity"]["name"] == updated_name

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities/{study_activity_uid}/sync-latest-version",
    )
    assert_response_status_code(response, 201)

    response = api_client.get(f"/studies/{test_study.uid}/study-activities")
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res[0]["keep_old_version"] is False
    assert res[0]["activity"]["status"] == "Final"
    assert res[0]["activity"]["name"] == updated_name
    assert res[0]["latest_activity"] is None
