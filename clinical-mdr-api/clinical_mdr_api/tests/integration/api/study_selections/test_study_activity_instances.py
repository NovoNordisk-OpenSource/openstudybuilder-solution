"""
Tests for /studies/{study_uid}/study-activity-instances endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.domains.study_selections.study_selection_activity_instance import (
    StudyActivityInstanceState,
)
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
from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.models.study_selections.study import Study
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

log = logging.getLogger(__name__)

study: Study
epoch_uid: str
DAYUID: str
visits_basic_data: str
activity_instruction: str
general_activity_group: ActivityGroup
randomisation_activity_subgroup: ActivitySubGroup
randomized_activity: Activity
body_mes_activity: Activity
body_measurements_activity_subgroup: ActivitySubGroup
weight_activity: Activity
weight_activity_instance: ActivityInstance
weight_activity_instance_class: ActivityInstanceClass
body_mes_activity_instance: ActivityInstance
clinical_programme: ClinicalProgramme
project: Project


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studyactivityinstanceapi"
    inject_and_clear_db(db_name)

    global study
    study = inject_base_data()

    db.cypher_query(STARTUP_ACTIVITY_GROUPS)
    db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
    db.cypher_query(STARTUP_ACTIVITIES)
    db.cypher_query(
        get_codelist_with_term_cypher(
            "EFFICACY", "Flowchart Group", term_uid="term_efficacy_uid"
        )
    )
    db.cypher_query(
        get_codelist_with_term_cypher(
            "SAFETY", "Flowchart Group", term_uid="informed_consent_uid"
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
        is_data_collected=True,
    )
    body_mes_activity = TestUtils.create_activity(
        name="Body Measurement activity",
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
        is_data_collected=True,
    )
    body_mes_activity_instance_class = TestUtils.create_activity_instance_class(
        name="Body measurement activity instance class"
    )
    global body_mes_activity_instance
    body_mes_activity_instance = TestUtils.create_activity_instance(
        name="Body measurement activity instance",
        activity_instance_class_uid=body_mes_activity_instance_class.uid,
        name_sentence_case="body measurement activity instance",
        topic_code="body measurement activity instance topic code",
        is_required_for_activity=True,
        activities=[body_mes_activity.uid],
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        activity_items=[],
    )
    body_measurements_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Body Measurements", activity_groups=[general_activity_group.uid]
    )
    weight_activity = TestUtils.create_activity(
        name="Weight",
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
        is_data_collected=True,
    )
    global weight_activity_instance_class
    weight_activity_instance_class = TestUtils.create_activity_instance_class(
        name="Weight activity instance class"
    )
    global weight_activity_instance
    weight_activity_instance = TestUtils.create_activity_instance(
        name="Weight activity instance",
        activity_instance_class_uid=weight_activity_instance_class.uid,
        name_sentence_case="weight activity instance",
        topic_code="weight activity instance topic code",
        is_required_for_activity=True,
        activities=[weight_activity.uid],
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        activity_items=[],
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
    yield


def test_create_remove_study_activity_instance_when_study_activity_is_created_removed(
    api_client,
):
    test_study = TestUtils.create_study(project_number=project.project_number)

    TestUtils.create_activity_instance(
        name="Draft Activity Instance",
        activity_instance_class_uid=weight_activity_instance_class.uid,
        name_sentence_case="draft activity instance",
        topic_code="draft activity instance topic code",
        is_required_for_activity=True,
        activities=[weight_activity.uid],
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        activity_items=[],
        approve=False,
    )

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": weight_activity.uid,
            "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": "term_efficacy_uid",
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    study_activity_uid = res["study_activity_uid"]

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    study_activity_instances = res["items"]
    assert len(study_activity_instances) == 1
    study_activity_instance_uid = study_activity_instances[0][
        "study_activity_instance_uid"
    ]
    assert study_activity_instances[0]["study_activity_uid"] == study_activity_uid
    assert study_activity_instances[0]["activity"]["uid"] == weight_activity.uid
    assert (
        study_activity_instances[0]["activity_instance"]["name"]
        == weight_activity_instance.name
    )
    assert (
        study_activity_instances[0]["show_activity_instance_in_protocol_flowchart"]
        is False
    )
    assert (
        study_activity_instances[0]["state"]
        == StudyActivityInstanceState.REQUIRED.value
    )
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_activity_instance_uid"] == study_activity_instance_uid
    assert res["study_activity_subgroup"]["study_activity_subgroup_uid"] is not None
    assert (
        res["study_activity_subgroup"]["activity_subgroup_uid"]
        == body_measurements_activity_subgroup.uid
    )
    assert (
        res["study_activity_subgroup"]["activity_subgroup_name"]
        == body_measurements_activity_subgroup.name
    )
    assert res["study_activity_group"]["study_activity_group_uid"] is not None
    assert (
        res["study_activity_group"]["activity_group_uid"] == general_activity_group.uid
    )
    assert (
        res["study_activity_group"]["activity_group_name"]
        == general_activity_group.name
    )
    assert res["study_soa_group"]["study_soa_group_uid"] is not None
    assert res["study_soa_group"]["soa_group_term_uid"] == "term_efficacy_uid"
    assert res["study_soa_group"]["soa_group_term_name"] is not None

    response = api_client.delete(
        f"/studies/{test_study.uid}/study-activities/{study_activity_uid}",
    )
    assert_response_status_code(response, 204)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 404)
    TestUtils.delete_study(test_study.uid)


def test_delete_study_activity_instance(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": randomized_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": "term_efficacy_uid",
        },
    )
    assert_response_status_code(response, 201)
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    study_activity_instance_uid = res[0]["study_activity_instance_uid"]

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_activity_instance_uid"] == study_activity_instance_uid
    assert res["state"] == StudyActivityInstanceState.MISSING_SELECTION.value

    response = api_client.delete(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 204)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 404)
    TestUtils.delete_study(test_study.uid)


def test_create_study_activity_instance(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": weight_activity.uid,
            "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": "term_efficacy_uid",
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    study_activity_uid = res["study_activity_uid"]

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances",
        json={
            "study_activity_uid": study_activity_uid,
            "activity_instance_uid": body_mes_activity_instance.uid,
        },
    )
    assert_response_status_code(response, 400)
    assert (
        response.json()["message"]
        == f"Activity Instance with Name '{body_mes_activity_instance.name}' isn't linked with the Activity with Name '{weight_activity.name}'."
    )

    new_instance_class = TestUtils.create_activity_instance_class(
        name="New instance class"
    )
    # Create preview ActivityInstance that links to Weight Activity
    new_preview_activity_instance_linked_to_weight = TestUtils.create_activity_instance(
        name="New instance linked to weight activity",
        activity_instance_class_uid=new_instance_class.uid,
        name_sentence_case="new instance linked to weight activity",
        topic_code="new instance linked to weight activity",
        is_required_for_activity=True,
        activities=[weight_activity.uid],
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        activity_items=[],
        preview=True,
    )
    # Create new ActivityInstance that links to Weight Activity
    new_activity_instance_linked_to_weight = TestUtils.create_activity_instance(
        name="New instance linked to weight activity",
        activity_instance_class_uid=new_instance_class.uid,
        name_sentence_case="new instance linked to weight activity",
        topic_code="new instance linked to weight activity",
        is_required_for_activity=True,
        activities=[weight_activity.uid],
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        activity_items=[],
    )

    new_preview_activity_instance_linked_to_weight_without_name_specified = (
        TestUtils.create_activity_instance(
            activity_instance_class_uid=new_instance_class.uid,
            is_required_for_activity=True,
            activities=[weight_activity.uid],
            activity_subgroups=[body_measurements_activity_subgroup.uid],
            activity_groups=[general_activity_group.uid],
            activity_items=[],
            preview=True,
        )
    )

    assert (
        new_preview_activity_instance_linked_to_weight_without_name_specified.name
        == "Weight"
    )
    assert (
        new_preview_activity_instance_linked_to_weight_without_name_specified.name_sentence_case
        == "weight"
    )
    assert (
        new_preview_activity_instance_linked_to_weight_without_name_specified.adam_param_code
        == ""
    )
    diffs = (
        new_preview_activity_instance_linked_to_weight.__dict__.items()
        ^ new_activity_instance_linked_to_weight.__dict__.items()
    )
    assert "uid" in {diff[0] for diff in diffs} and "start_date" in {
        diff[0] for diff in diffs
    }
    assert ("uid", "PreviewTemporalUid") in diffs
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances",
        json={
            "study_activity_uid": study_activity_uid,
            "activity_instance_uid": new_activity_instance_linked_to_weight.uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    study_activity_instance_uid = res["study_activity_instance_uid"]
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_activity_uid"] == study_activity_uid
    assert res["activity_instance"]["uid"] == new_activity_instance_linked_to_weight.uid
    assert res["state"] == StudyActivityInstanceState.REQUIRED.value

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances",
        json={
            "study_activity_uid": study_activity_uid,
            "activity_instance_uid": new_activity_instance_linked_to_weight.uid,
        },
    )
    assert_response_status_code(response, 409)
    assert (
        response.json()["message"]
        == f"There is already a Study Activity Instance with UID '{new_activity_instance_linked_to_weight.uid}' linked to the Activity with UID '{weight_activity.uid}'."
    )
    TestUtils.delete_study(test_study.uid)


def test_edit_study_activity_instance(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": randomized_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": "term_efficacy_uid",
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert len(res) == 1
    study_activity_instance_uid = res[0]["study_activity_instance_uid"]
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity_instance"] is None
    assert res["state"] == StudyActivityInstanceState.MISSING_SELECTION.value

    randomized_activity_instance_class = TestUtils.create_activity_instance_class(
        name="Randomized activity instance class"
    )
    randomized_activity_instance = TestUtils.create_activity_instance(
        name="Randomized activity instance",
        activity_instance_class_uid=randomized_activity_instance_class.uid,
        name_sentence_case="randomized activity instance",
        topic_code="randomized activity instance topic code",
        is_required_for_activity=True,
        activities=[randomized_activity.uid],
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        activity_items=[],
    )

    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "activity_instance_uid": randomized_activity_instance.uid,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity_instance"]["uid"] == randomized_activity_instance.uid

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity_instance"]["uid"] == randomized_activity_instance.uid
    assert res["state"] == StudyActivityInstanceState.REQUIRED.value
    TestUtils.delete_study(test_study.uid)


def test_study_activity_instance_header_endpoint(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": randomized_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": "term_efficacy_uid",
        },
    )
    assert_response_status_code(response, 201)
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": body_mes_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": "term_efficacy_uid",
        },
    )
    assert_response_status_code(response, 201)
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": weight_activity.uid,
            "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": "term_efficacy_uid",
        },
    )
    assert_response_status_code(response, 201)
    # get study activity instance headers
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/headers?field_name=activity.name",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res == [
        randomized_activity.name,
        body_mes_activity.name,
        weight_activity.name,
    ]
    TestUtils.delete_study(test_study.uid)


def test_study_activity_instance_audit_trails(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": randomized_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": "term_efficacy_uid",
        },
    )
    assert_response_status_code(response, 201)
    response = api_client.get(f"/studies/{test_study.uid}/study-activity-instances")
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    study_activity_instance_uid = res[0]["study_activity_instance_uid"]

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": body_mes_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": "term_efficacy_uid",
        },
    )
    assert_response_status_code(response, 201)
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "show_activity_instance_in_protocol_flowchart": True,
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/audit-trail"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert len(res) == 3
    assert res[0]["activity"]["name"] == randomized_activity.name
    assert res[0]["activity_instance"]["name"] == "Randomized activity instance"
    assert res[0]["show_activity_instance_in_protocol_flowchart"] is True
    assert res[1]["activity"]["name"] == randomized_activity.name
    assert res[1]["activity_instance"]["name"] == "Randomized activity instance"
    assert res[1]["show_activity_instance_in_protocol_flowchart"] is False
    assert res[2]["activity"]["name"] == body_mes_activity.name
    assert res[2]["activity_instance"]["name"] == body_mes_activity_instance.name
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}/audit-trail"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == 2
    assert res[0]["activity"]["name"] == randomized_activity.name
    assert res[0]["show_activity_instance_in_protocol_flowchart"] is True
    assert res[1]["activity"]["name"] == randomized_activity.name
    assert res[1]["show_activity_instance_in_protocol_flowchart"] is False
    TestUtils.delete_study(test_study.uid)


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
def test_get_study_activity_instances_csv_xml_excel(api_client, export_format):
    test_study = TestUtils.create_study(project_number=project.project_number)
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": randomized_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": "term_efficacy_uid",
        },
    )
    assert_response_status_code(response, 201)
    url = f"/studies/{test_study.uid}/study-activities"
    TestUtils.verify_exported_data_format(api_client, export_format, url)
    TestUtils.delete_study(test_study.uid)


@pytest.mark.parametrize(
    "activity_name, activity_instance_name, is_required, is_defaulted, expected_state, is_data_collected, retired_instance",
    [
        pytest.param(
            "Required activity",
            "Required activity instance",
            True,
            False,
            "Required",
            True,
            False,
        ),
        pytest.param(
            "Defaulted activity",
            "Defaulted activity instance",
            False,
            True,
            "Defaulted",
            True,
            False,
        ),
        pytest.param(
            "Suggestion activity",
            "Suggestion activity instance",
            False,
            False,
            "Suggestion",
            True,
            False,
        ),
        pytest.param(
            "Not collected activity",
            None,
            False,
            False,
            None,
            False,
            False,
        ),
        pytest.param(
            "Activity with retired instance",
            "Retired activity instance",
            False,
            False,
            None,
            True,
            True,
        ),
    ],
)
def test_study_activity_instances_states(
    api_client,
    activity_name,
    activity_instance_name,
    is_required,
    is_defaulted,
    expected_state,
    is_data_collected,
    retired_instance,
):
    test_study = TestUtils.create_study(project_number=project.project_number)
    new_test_activity = TestUtils.create_activity(
        name=activity_name,
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
        is_data_collected=is_data_collected,
    )
    if is_data_collected:
        new_test_activity_instance = TestUtils.create_activity_instance(
            name=activity_instance_name,
            activity_instance_class_uid=weight_activity_instance_class.uid,
            name_sentence_case=activity_instance_name.lower(),
            topic_code=activity_instance_name + " topic code",
            is_required_for_activity=is_required,
            is_default_selected_for_activity=is_defaulted,
            activities=[new_test_activity.uid],
            activity_subgroups=[body_measurements_activity_subgroup.uid],
            activity_groups=[general_activity_group.uid],
            activity_items=[],
            retire_after_approve=retired_instance,
        )
    else:
        new_test_activity_instance = None

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": new_test_activity.uid,
            "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": "term_efficacy_uid",
        },
    )
    assert_response_status_code(response, 201)
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]

    if is_data_collected and not retired_instance:
        assert len(res) == 1
        assert res[0]["activity_instance"]["uid"] == new_test_activity_instance.uid
        assert (
            new_test_activity.uid
            in res[0]["activity_instance"]["activity_groupings"][0]["activity"]["uid"]
        )
        assert res[0]["activity"]["uid"] == new_test_activity.uid
        assert res[0]["state"] == expected_state
    else:
        # We should get a placeholder, with activity_instance set to None
        assert len(res) == 1
        assert res[0]["activity_instance"] is None

    TestUtils.delete_study(test_study.uid)


def test_sync_to_latest_version_activity_instance(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    new_test_activity = TestUtils.create_activity(
        name="New activity for sync test",
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
        is_data_collected=True,
    )

    new_test_activity_instance = TestUtils.create_activity_instance(
        name="New activity instance for sync test",
        activity_instance_class_uid=weight_activity_instance_class.uid,
        name_sentence_case="new activity instance for sync test",
        topic_code="new activity instance topic code for sync test",
        is_required_for_activity=True,
        is_default_selected_for_activity=True,
        activities=[new_test_activity.uid],
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        activity_items=[],
    )
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": new_test_activity.uid,
            "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": "term_efficacy_uid",
        },
    )
    assert_response_status_code(response, 201)
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    study_activity_instances = response.json()["items"]
    assert len(study_activity_instances) == 1
    study_activity_instance_uid = study_activity_instances[0][
        "study_activity_instance_uid"
    ]
    assert study_activity_instances[0]["activity_instance"]["version"] == "1.0"
    assert (
        study_activity_instances[0]["activity_instance"]["uid"]
        == new_test_activity_instance.uid
    )
    assert study_activity_instances[0]["latest_activity_instance"] is None

    response = api_client.post(
        f"/concepts/activities/activity-instances/{new_test_activity_instance.uid}/versions",
    )
    assert_response_status_code(response, 201)
    # PATCH underling activity-instance
    response = api_client.patch(
        f"/concepts/activities/activity-instances/{new_test_activity_instance.uid}",
        json={
            "definition": "new activity instance definition for sync test",
            "change_description": "Sync to latest version test",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.post(
        f"/concepts/activities/activity-instances/{new_test_activity_instance.uid}/approvals",
    )
    assert_response_status_code(response, 201)

    # Fetch StudyActivityInstance after underlying ActivityInstance is edited
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    study_activity_instance = response.json()
    assert study_activity_instance["activity_instance"]["version"] == "1.0"
    assert (
        study_activity_instance["activity_instance"]["uid"]
        == new_test_activity_instance.uid
    )
    assert study_activity_instance["latest_activity_instance"]["version"] == "2.0"
    assert (
        study_activity_instance["latest_activity_instance"]["uid"]
        == new_test_activity_instance.uid
    )

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}/sync-latest-version",
    )
    assert_response_status_code(response, 201)

    # Fetch StudyActivityInstance after underlying ActivityInstance is synced to latest version
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    study_activity_instance = response.json()
    assert study_activity_instance["activity_instance"]["version"] == "2.0"
    assert (
        study_activity_instance["activity_instance"]["uid"]
        == new_test_activity_instance.uid
    )
    assert study_activity_instance["latest_activity_instance"] is None
    TestUtils.delete_study(test_study.uid)


def test_activity_activity_instance_relationship(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    new_test_activity = TestUtils.create_activity(
        name="Activity to test activity-activity instance rel deletion.",
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
        is_data_collected=True,
    )
    new_test_activity_instance = TestUtils.create_activity_instance(
        name="Activity instance to test activity-activity instance rel deletion.",
        activity_instance_class_uid=weight_activity_instance_class.uid,
        name_sentence_case="activity instance to test activity-activity instance rel deletion.",
        topic_code="topic code",
        is_required_for_activity=False,
        is_default_selected_for_activity=False,
        activities=[new_test_activity.uid],
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        activity_items=[],
    )
    study_activity = TestUtils.create_study_activity(
        study_uid=test_study.uid,
        soa_group_term_uid="term_efficacy_uid",
        activity_uid=new_test_activity.uid,
        activity_subgroup_uid=body_measurements_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
    )

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    study_activity_instances = response.json()["items"]
    assert len(study_activity_instances) == 1
    study_activity_instance_uid = study_activity_instances[0][
        "study_activity_instance_uid"
    ]

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    study_activity_instance = response.json()
    assert (
        study_activity_instance["study_activity_uid"]
        == study_activity.study_activity_uid
    )
    assert study_activity_instance["activity"]["uid"] == new_test_activity.uid
    assert study_activity_instance["activity"]["name"] == new_test_activity.name
    assert (
        study_activity_instance["study_activity_subgroup"]["activity_subgroup_uid"]
        == body_measurements_activity_subgroup.uid
    )
    assert (
        study_activity_instance["study_activity_group"]["activity_group_uid"]
        == general_activity_group.uid
    )
    assert (
        study_activity_instance["activity_instance"]["uid"]
        == new_test_activity_instance.uid
    )
    assert (
        study_activity_instance["activity_instance"]["name"]
        == new_test_activity_instance.name
    )
    assert (
        study_activity_instance["state"] == StudyActivityInstanceState.SUGGESTION.value
    )

    # Delete Activity-ActivityInstance relationship
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "activity_instance_uid": None,
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    study_activity_instance = response.json()
    assert (
        study_activity_instance["study_activity_uid"]
        == study_activity.study_activity_uid
    )
    assert study_activity_instance["activity"]["uid"] == new_test_activity.uid
    assert study_activity_instance["activity"]["name"] == new_test_activity.name
    assert (
        study_activity_instance["study_activity_subgroup"]["activity_subgroup_uid"]
        == body_measurements_activity_subgroup.uid
    )
    assert (
        study_activity_instance["study_activity_group"]["activity_group_uid"]
        == general_activity_group.uid
    )
    assert study_activity_instance["activity_instance"] is None
    assert (
        study_activity_instance["state"]
        == StudyActivityInstanceState.MISSING_SELECTION.value
    )
    TestUtils.delete_study(test_study.uid)


def test_study_activity_instances_batch_create(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    new_test_activity = TestUtils.create_activity(
        name="Activity with some ActivityInstances",
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
        is_data_collected=True,
    )
    name = "First required activity instance"
    first_required_activity_instance = TestUtils.create_activity_instance(
        name=name,
        name_sentence_case=name.lower(),
        activity_instance_class_uid=weight_activity_instance_class.uid,
        topic_code="first requrired topic code",
        is_required_for_activity=True,
        is_default_selected_for_activity=False,
        activities=[new_test_activity.uid],
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        activity_items=[],
    )
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": new_test_activity.uid,
            "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": "term_efficacy_uid",
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    study_activity_uid = res["study_activity_uid"]

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    study_activity_instances = response.json()["items"]
    assert len(study_activity_instances) == 1

    assert study_activity_instances[0]["activity_instance"]["version"] == "1.0"
    assert (
        study_activity_instances[0]["activity_instance"]["uid"]
        == first_required_activity_instance.uid
    )
    assert study_activity_instances[0]["latest_activity_instance"] is None

    req_activity_instance_uids = []
    for i in range(5):
        name = f"{i} required activity instance"
        required_activity_instance = TestUtils.create_activity_instance(
            name=name,
            name_sentence_case=name.lower(),
            activity_instance_class_uid=weight_activity_instance_class.uid,
            topic_code=f"{i} first requrired topic code",
            is_required_for_activity=True,
            is_default_selected_for_activity=False,
            activities=[new_test_activity.uid],
            activity_subgroups=[body_measurements_activity_subgroup.uid],
            activity_groups=[general_activity_group.uid],
            activity_items=[],
        )
        req_activity_instance_uids.append(required_activity_instance.uid)
    req_activity_instance_uids.append(first_required_activity_instance.uid)

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances/batch-select",
        json={
            "study_activity_uid": study_activity_uid,
            "activity_instance_uids": req_activity_instance_uids,
        },
    )
    res = response.json()

    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    study_activity_instances = response.json()["items"]
    assert len(study_activity_instances) == 6

    TestUtils.delete_study(test_study.uid)


def test_study_activity_instances_return_proper_activity_instance_versionsing_data(
    api_client,
):
    test_study = TestUtils.create_study(project_number=project.project_number)
    new_test_activity = TestUtils.create_activity(
        name="Activity StudyActivityInstance return proper ActivityInstance versioning data test",
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
        is_data_collected=True,
    )
    activity_instance_name = "Test activity instance"
    activity_instance = TestUtils.create_activity_instance(
        name=activity_instance_name,
        name_sentence_case=activity_instance_name.lower(),
        activity_instance_class_uid=weight_activity_instance_class.uid,
        topic_code="the requrired topic code",
        is_required_for_activity=True,
        is_default_selected_for_activity=False,
        activities=[new_test_activity.uid],
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        activity_items=[],
    )
    response = api_client.post(
        f"/concepts/activities/activity-instances/{activity_instance.uid}/versions",
    )
    assert_response_status_code(response, 201)
    response = api_client.post(
        f"/concepts/activities/activity-instances/{activity_instance.uid}/approvals",
    )
    assert_response_status_code(response, 201)
    # After creating a new draft and immidiately approving it, we'll have two Final (1.0, 2.0) versions linked between single root-value nodes
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": new_test_activity.uid,
            "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": "term_efficacy_uid",
        },
    )
    assert_response_status_code(response, 201)

    # Get StudyActivityInstance created
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    study_activity_instances = response.json()["items"]
    assert len(study_activity_instances) == 1

    assert study_activity_instances[0]["activity_instance"]["version"] == "2.0"
