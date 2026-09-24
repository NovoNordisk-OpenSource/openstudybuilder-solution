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

from clinical_mdr_api.domains.enums import ValidationMode
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
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import CTCodelist
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.data_suppliers.data_supplier import DataSupplier
from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.study_selections.study_selection import (
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
    assert_response_status_code,
    parse_json_response,
)
from common.config import settings

log = logging.getLogger(__name__)

study: Study
epoch_uid: str
DAYUID: str
visits_basic_data: str
activity_instruction: str
general_activity_group: ActivityGroup
randomisation_activity_subgroup: ActivitySubGroup
randomized_activity: Activity
randomized_activity_instance: ActivityInstance
second_randomized_activity_instance: ActivityInstance
randomized_activity_instance_class: ActivityInstanceClass
body_mes_activity: Activity
body_measurements_activity_subgroup: ActivitySubGroup
weight_activity: Activity
weight_activity_instance: ActivityInstance
weight_activity_instance_class: ActivityInstanceClass
body_mes_activity_instance: ActivityInstance
clinical_programme: ClinicalProgramme
project: Project
term_efficacy_uid: str
study_visit_1: StudyVisit
study_visit_2: StudyVisit
# Data supplier and origin fields test data
supplier_type_codelist: CTCodelist
supplier_type_term: CTTerm
origin_source_codelist: CTCodelist
origin_source_term: CTTerm
origin_type_codelist: CTCodelist
origin_type_term: CTTerm
data_supplier: DataSupplier


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
    study, _test_data_dict = inject_base_data()

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

    activity_group = TestUtils.create_activity_group(name="test activity group")
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
        is_data_collected=True,
    )
    global randomized_activity_instance_class
    randomized_activity_instance_class = TestUtils.create_activity_instance_class(
        name="Randomized activity instance class"
    )
    global randomized_activity_instance
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
    global second_randomized_activity_instance
    second_randomized_activity_instance = TestUtils.create_activity_instance(
        name="Second Randomized activity instance",
        activity_instance_class_uid=randomized_activity_instance_class.uid,
        name_sentence_case="second randomized activity instance",
        topic_code="second randomized activity instance topic code",
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
        name="Body Measurements"
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

    catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
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

    global clinical_programme
    global project
    clinical_programme = TestUtils.create_clinical_programme(name="SoA CP")
    project = TestUtils.create_project(
        name="Project for SoA",
        project_number="1234",
        description="Base project",
        clinical_programme_uid=clinical_programme.uid,
    )

    # Setup for data supplier and origin fields tests
    global supplier_type_codelist
    global supplier_type_term
    global origin_source_codelist
    global origin_source_term
    global origin_type_codelist
    global origin_type_term
    global data_supplier

    supplier_type_codelist = TestUtils.create_ct_codelist(
        name="Data Supplier Type",
        sponsor_preferred_name="Data Supplier Type",
        extensible=True,
        approve=True,
        submission_value=settings.data_supplier_type_cl_submval,
        catalogue_name=settings.sdtm_ct_catalogue_name,
    )
    supplier_type_term = TestUtils.create_ct_term(
        codelist_uid=supplier_type_codelist.codelist_uid,
        sponsor_preferred_name="Supplier Type",
        sponsor_preferred_name_sentence_case="supplier type",
        catalogue_name=settings.sdtm_ct_catalogue_name,
        approve=True,
    )

    origin_source_codelist = TestUtils.create_ct_codelist(
        name="Origin Source",
        sponsor_preferred_name="Origin Source",
        extensible=True,
        approve=True,
        submission_value=settings.origin_source_cl_submval,
        catalogue_name=settings.sdtm_ct_catalogue_name,
    )
    origin_source_term = TestUtils.create_ct_term(
        codelist_uid=origin_source_codelist.codelist_uid,
        sponsor_preferred_name="Investigator",
        sponsor_preferred_name_sentence_case="investigator",
        catalogue_name=settings.sdtm_ct_catalogue_name,
        approve=True,
    )

    origin_type_codelist = TestUtils.create_ct_codelist(
        name="Origin Type",
        sponsor_preferred_name="Origin Type",
        extensible=True,
        approve=True,
        submission_value=settings.origin_type_cl_submval,
        catalogue_name=settings.sdtm_ct_catalogue_name,
    )
    origin_type_term = TestUtils.create_ct_term(
        codelist_uid=origin_type_codelist.codelist_uid,
        sponsor_preferred_name="Collected",
        sponsor_preferred_name_sentence_case="collected",
        catalogue_name=settings.sdtm_ct_catalogue_name,
        approve=True,
    )

    data_supplier = TestUtils.create_data_supplier(
        name="Test Data Supplier",
        supplier_type_uid=supplier_type_term.term_uid,
        origin_source_uid=origin_source_term.term_uid,
        origin_type_uid=origin_type_term.term_uid,
        description="Test data supplier for SAI tests",
    )
    yield


@pytest.mark.order("last")
def test_integrity_checks_for_all_studies(api_client):
    """
    Test integrity checks for all available studies in the database.

    This test should always be executed at the END to check the health of the remaining database.
    It validates that all studies in the database pass integrity checks after all other tests have run.
    """
    TestUtils.run_integrity_checks_for_all_studies(api_client)


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
            "soa_group_term_uid": term_efficacy_uid,
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
        == StudyActivityInstanceState.REVIEW_NOT_NEEDED.value
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
    assert res["study_soa_group"]["soa_group_term_uid"] == term_efficacy_uid
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
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    study_activity_uid = response.json()["study_activity_uid"]

    # Create the second activity instances pointed to the same Activity - Randomized
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "activity_instance_uid": second_randomized_activity_instance.uid,
                    "study_activity_uid": study_activity_uid,
                },
            }
        ],
    )
    assert_response_status_code(response, 207)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert len(res) == 2
    required_study_activity_instance_uid = res[0]["study_activity_instance_uid"]
    assert res[0]["is_reviewed"] is True
    second_randomized_activity_instance_uid = res[1]["study_activity_instance_uid"]

    # Delete one StudyActivityInstance pointing to the Randomized Activity, the whole StudyActivityInstance object should be removed
    # as there exists another StudyActivityInstance pointing to the same Activity
    response = api_client.delete(
        f"/studies/{test_study.uid}/study-activity-instances/{second_randomized_activity_instance_uid}",
    )
    assert_response_status_code(response, 204)
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{second_randomized_activity_instance_uid}",
    )
    assert_response_status_code(response, 404)

    # Delete the second one StudyActivityInstance pointing to the Randomized Activity, the whole StudyActivityInstance object should NOT be removed
    # as there does not exist another StudyActivityInstance pointing to the same Activity, the ActivityInstance field should be cleared
    response = api_client.delete(
        f"/studies/{test_study.uid}/study-activity-instances/{required_study_activity_instance_uid}",
    )
    assert_response_status_code(response, 204)
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{required_study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_activity_instance_uid"] == required_study_activity_instance_uid
    assert res["activity_instance"] is None
    assert res["is_reviewed"] is False

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert len(res) == 1
    TestUtils.delete_study(test_study.uid)


def test_create_study_activity_instance(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": weight_activity.uid,
            "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
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

    # Test is_important flag and has_baseline rels
    # add activity schedule for parent activity and visit 1
    test_study_epoch = create_study_epoch("EpochSubType_0001", study_uid=test_study.uid)
    inputs = {
        "study_uid": test_study.uid,
        "study_epoch_uid": test_study_epoch.uid,
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
    study_visit_1 = TestUtils.create_study_visit(**datadict)
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-schedules",
        json={
            "study_activity_uid": study_activity_uid,
            "study_visit_uid": study_visit_1.uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances",
        json={
            "study_activity_uid": study_activity_uid,
            "activity_instance_uid": new_activity_instance_linked_to_weight.uid,
            "is_important": True,
            "baseline_visit_uids": [study_visit_1.uid],
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    study_activity_instance_uid = res["study_activity_instance_uid"]
    assert res["is_important"] is True
    assert res["baseline_visits"] == [
        {
            "uid": study_visit_1.uid,
            "visit_name": study_visit_1.visit_name,
            "visit_type_name": study_visit_1.visit_type.sponsor_preferred_name,
        }
    ]

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_activity_uid"] == study_activity_uid
    assert res["activity_instance"]["uid"] == new_activity_instance_linked_to_weight.uid
    assert res["state"] == StudyActivityInstanceState.REVIEW_NOT_NEEDED.value
    assert res["is_important"] is True
    assert res["baseline_visits"] == [
        {
            "uid": study_visit_1.uid,
            "visit_name": study_visit_1.visit_name,
            "visit_type_name": study_visit_1.visit_type.sponsor_preferred_name,
        }
    ]

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
    expected_audit_trail_length = 0
    test_study = TestUtils.create_study(project_number=project.project_number)
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
    res = response.json()
    study_activity_uid = res["study_activity_uid"]

    expected_audit_trail_length += 1
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
    assert res["activity_instance"]["uid"] == randomized_activity_instance.uid
    assert res["state"] == StudyActivityInstanceState.REVIEW_NOT_NEEDED.value

    # add activity schedule for parent activity and both visit 1 & 2
    test_study_epoch = create_study_epoch("EpochSubType_0001", study_uid=test_study.uid)
    inputs = {
        "study_uid": test_study.uid,
        "study_epoch_uid": test_study_epoch.uid,
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
    study_visit_1 = TestUtils.create_study_visit(**datadict)
    inputs["time_value"] = 200
    datadict.update(inputs)
    study_visit_2 = TestUtils.create_study_visit(**datadict)
    inputs["time_value"] = 300
    datadict.update(inputs)
    unscheduled_visit = TestUtils.create_study_visit(**datadict)
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-schedules",
        json={
            "study_activity_uid": study_activity_uid,
            "study_visit_uid": study_visit_1.uid,
        },
    )
    res = response.json()
    study_activity_schedule_1_uid = res["study_activity_schedule_uid"]
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-schedules",
        json={
            "study_activity_uid": study_activity_uid,
            "study_visit_uid": study_visit_2.uid,
        },
    )
    assert_response_status_code(response, 201)

    # Test is_important & baseline visits
    # Test is_important field - initially should be False
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["is_important"] is False
    assert res["baseline_visits"] is None

    # Test setting is_important to True
    # First, ensure the study activity instance is not reviewed or it will fail
    _ = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "is_reviewed": False,
        },
    )
    expected_audit_trail_length += 1

    # Test setting baseline visits
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "is_important": True,
            "baseline_visit_uids": [study_visit_1.uid, study_visit_2.uid],
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["is_important"] is True
    assert len(res["baseline_visits"]) == 2
    assert {
        "uid": study_visit_1.uid,
        "visit_name": study_visit_1.visit_name,
        "visit_type_name": study_visit_1.visit_type.sponsor_preferred_name,
    } in res["baseline_visits"]
    assert {
        "uid": study_visit_2.uid,
        "visit_name": study_visit_2.visit_name,
        "visit_type_name": study_visit_2.visit_type.sponsor_preferred_name,
    } in res["baseline_visits"]
    expected_audit_trail_length += 1

    # Test setting is_important to False
    # Test removing one baseline visit
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "is_important": False,
            "baseline_visit_uids": [study_visit_2.uid],
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["is_important"] is False
    assert len(res["baseline_visits"]) == 1
    assert {
        "uid": study_visit_2.uid,
        "visit_name": study_visit_2.visit_name,
        "visit_type_name": study_visit_2.visit_type.sponsor_preferred_name,
    } in res["baseline_visits"]
    expected_audit_trail_length += 1

    # Test baseline does not change when not specified
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "is_important": True,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["is_important"] is True
    assert len(res["baseline_visits"]) == 1
    assert {
        "uid": study_visit_2.uid,
        "visit_name": study_visit_2.visit_name,
        "visit_type_name": study_visit_2.visit_type.sponsor_preferred_name,
    } in res["baseline_visits"]
    expected_audit_trail_length += 1

    # Test removing all baseline visits - should set baseline_visits to None
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "baseline_visit_uids": [],
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["baseline_visits"] is None
    expected_audit_trail_length += 1
    # Test adding unscheduled visit to baseline visits - should send an exception
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "baseline_visit_uids": [unscheduled_visit.uid],
        },
    )
    assert_response_status_code(response, 400)
    assert (
        response.json()["message"]
        == f"The Study Visit with UID '{unscheduled_visit.uid}' does not correspond to a current StudyActivitySchedule for the parent StudyActivity with UID '{study_activity_uid}'."
    )

    # Test that editing is_important or baseline_visits on a reviewed instance raises error
    # Set is_reviewed to True with baseline visits
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "is_reviewed": True,
            "is_important": False,
            "baseline_visit_uids": [study_visit_1.uid],
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["is_reviewed"] is True
    assert res["is_important"] is False
    assert len(res["baseline_visits"]) == 1
    expected_audit_trail_length += 1

    # Test cascade deletion of baseline rel for Visit / Schedule deletion
    # Delete schedule 1 - should remove visit 1 from baseline visits
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "is_important": True,
            "baseline_visit_uids": [study_visit_1.uid, study_visit_2.uid],
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["baseline_visits"]) == 2
    expected_audit_trail_length += 1
    response = api_client.delete(
        f"/studies/{test_study.uid}/study-activity-schedules/{study_activity_schedule_1_uid}",
    )
    assert_response_status_code(response, 204)
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["baseline_visits"]) == 1
    assert {
        "uid": study_visit_2.uid,
        "visit_name": study_visit_2.visit_name,
        "visit_type_name": study_visit_2.visit_type.sponsor_preferred_name,
    } in res["baseline_visits"]
    expected_audit_trail_length += 1
    # Before deleting visit, check that patching visit does not change baseline visits
    _ = api_client.patch(
        f"/studies/{test_study.uid}/study-visits/{study_visit_2.uid}",
        json={
            "time_value": 400,
        },
    )
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["baseline_visits"]) == 1
    assert {
        "uid": study_visit_2.uid,
        "visit_name": study_visit_2.visit_name,
        "visit_type_name": study_visit_2.visit_type.sponsor_preferred_name,
    } in res["baseline_visits"]

    # Delete Visit 2 - should remove visit 2 from baseline visits
    _ = api_client.delete(
        f"/studies/{test_study.uid}/study-visits/{study_visit_2.uid}",
    )
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["baseline_visits"] is None
    expected_audit_trail_length += 1

    # Finally, test audit trail for baseline visits
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}/audit-trail",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == expected_audit_trail_length
    assert len([x for x in res if x["baseline_visits"] is None]) == 4
    assert (
        len(
            [
                x
                for x in res
                if x["baseline_visits"] is not None and len(x["baseline_visits"]) == 2
            ]
        )
        == 2
    )
    assert (
        len(
            [
                x
                for x in res
                if x["baseline_visits"] is not None and len(x["baseline_visits"]) == 1
            ]
        )
        == expected_audit_trail_length - 6
    )

    # test detaching from activity instance - should set state to MISSING_SELECTION
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "activity_instance_uid": None,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity_instance"] is None

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity_instance"] is None
    assert res["state"] == StudyActivityInstanceState.ADD_INSTANCE.value

    TestUtils.delete_study(test_study.uid)


def test_study_activity_instance_header_endpoint(api_client):
    # create test Study
    test_study = TestUtils.create_study(project_number=project.project_number)

    # create Study Activities
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

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": body_mes_activity.uid,
            "activity_subgroup_uid": randomisation_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": weight_activity.uid,
            "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)

    # crate Activity Placeholder
    response = api_client.post(
        "/concepts/activities/activities",
        json={
            "name": "Hello activity",
            "is_data_collected": False,
            "is_request_final": False,
            "library_name": "Requested",
            "name_sentence_case": "hello activity",
            "request_rationale": "tst",
            "flowchart_group": {"term_uid": term_efficacy_uid},
        },
    )
    res = parse_json_response(response, assert_status=201)

    response = api_client.post(
        f"/concepts/activities/activities/{res['uid']}/approvals"
    )
    res = parse_json_response(response, assert_status=201)
    hello_activity = Activity(**res)

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": res["uid"],
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)

    # get Study Activity Instance name values
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/headers?field_name=activity.name",
    )
    res = parse_json_response(response, assert_status=200)
    assert res == [
        randomized_activity.name,
        body_mes_activity.name,
        weight_activity.name,
        hello_activity.name,
    ]

    # get Study Activity Instance library_name values
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/headers?field_name=activity.library_name",
    )
    res = parse_json_response(response, assert_status=200)
    assert set(res) == {randomized_activity.library_name, hello_activity.library_name}

    # delete Test Study
    TestUtils.delete_study(test_study.uid)


def test_study_activity_instance_audit_trails(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
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
            "soa_group_term_uid": term_efficacy_uid,
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
    assert res[0]["is_important"] is False
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
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    url = f"/studies/{test_study.uid}/study-activities"
    TestUtils.verify_exported_data_format(api_client, export_format, url)
    TestUtils.delete_study(test_study.uid)


@pytest.mark.parametrize(
    "activity_name, activity_instance_name, is_required, is_defaulted, expected_state, is_data_collected, retired_instance, is_multiple_selection_allowed",
    [
        pytest.param(
            "Review not needed activity",
            "Review not needed activity instance",
            True,
            False,
            "Review not needed",
            True,
            False,
            True,
        ),
        pytest.param(
            "Review needed activity",
            "Review needed activity instance",
            False,
            True,
            "Review needed",
            True,
            False,
            True,
        ),
        pytest.param(
            "Review needed activity 2",
            "Review needed activity instance 2",
            False,
            False,
            "Review needed",
            True,
            False,
            True,
        ),
        pytest.param(
            "Not collected activity", None, False, False, None, False, False, True
        ),
        pytest.param(
            "Activity with retired instance",
            "Retired activity instance",
            False,
            False,
            None,
            True,
            True,
            True,
        ),
        pytest.param(
            "Multiple selection not allowed activity",
            "Multiple selection not allowed instance",
            False,
            False,
            "Remove instance",
            True,
            False,
            False,
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
    is_multiple_selection_allowed,
):
    test_study = TestUtils.create_study(project_number=project.project_number)
    new_test_activity = TestUtils.create_activity(
        name=activity_name,
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
        is_data_collected=is_data_collected,
        is_multiple_selection_allowed=is_multiple_selection_allowed,
    )
    new_test_activity_instance = None
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

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": new_test_activity.uid,
            "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    study_activity_uid = response.json()["study_activity_uid"]

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    res = response.json()["items"]

    if is_data_collected and not retired_instance and is_multiple_selection_allowed:
        assert len(res) == 1
        assert res[0]["activity_instance"]["uid"] == new_test_activity_instance.uid
        assert res[0]["activity"]["uid"] == new_test_activity.uid
        assert (
            res[0]["study_activity_subgroup"]["activity_subgroup_uid"]
            == body_measurements_activity_subgroup.uid
        )
        assert (
            res[0]["study_activity_group"]["activity_group_uid"]
            == general_activity_group.uid
        )
        assert res[0]["activity"]["uid"] == new_test_activity.uid
        assert res[0]["state"] == expected_state
    elif not is_multiple_selection_allowed:
        second_instance_name = activity_instance_name + " 2"
        second_instance = TestUtils.create_activity_instance(
            name=second_instance_name,
            activity_instance_class_uid=weight_activity_instance_class.uid,
            name_sentence_case=second_instance_name.lower(),
            topic_code=second_instance_name + " topic code",
            is_required_for_activity=is_required,
            is_default_selected_for_activity=is_defaulted,
            activities=[new_test_activity.uid],
            activity_subgroups=[body_measurements_activity_subgroup.uid],
            activity_groups=[general_activity_group.uid],
            activity_items=[],
            retire_after_approve=retired_instance,
        )
        response = api_client.post(
            f"/studies/{test_study.uid}/study-activity-instances/batch",
            json=[
                {
                    "method": "POST",
                    "content": {
                        "activity_instance_uid": second_instance.uid,
                        "study_activity_uid": study_activity_uid,
                    },
                }
            ],
        )
        assert_response_status_code(response, 207)
        response = api_client.get(
            f"/studies/{test_study.uid}/study-activity-instances",
        )
        assert_response_status_code(response, 200)
        res = response.json()["items"]
        assert len(res) == 2
        for study_activity_instance in res:
            assert study_activity_instance["activity_instance"] is not None
            assert study_activity_instance["activity"]["uid"] == new_test_activity.uid
            assert study_activity_instance["state"] == expected_state
        # Delete SAI to check if REMOVE_INSTANCE state changes to REVIEW_NEEDED
        sai_to_delete = res[0]["study_activity_instance_uid"]
        response = api_client.delete(
            f"/studies/{test_study.uid}/study-activity-instances/{sai_to_delete}",
        )
        assert_response_status_code(response, 204)
        response = api_client.get(
            f"/studies/{test_study.uid}/study-activity-instances",
        )
        assert_response_status_code(response, 200)
        res = response.json()["items"]
        assert len(res) == 1
        for study_activity_instance in res:
            assert study_activity_instance["activity_instance"] is not None
            assert study_activity_instance["activity"]["uid"] == new_test_activity.uid
            assert (
                study_activity_instance["state"]
                == StudyActivityInstanceState.REVIEW_NEEDED.value
            )
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
            "soa_group_term_uid": term_efficacy_uid,
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
    assert study_activity_instances[0]["keep_old_version"] is False

    response = api_client.post(
        f"/concepts/activities/activity-instances/{new_test_activity_instance.uid}/attributes/versions",
    )
    assert_response_status_code(response, 201)
    # PATCH underling activity-instance
    changed_definition = "new activity instance definition for sync test"
    response = api_client.patch(
        f"/concepts/activities/activity-instances/{new_test_activity_instance.uid}/attributes",
        json={
            "definition": changed_definition,
            "change_description": "Sync to latest version test",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.post(
        f"/concepts/activities/activity-instances/{new_test_activity_instance.uid}/attributes/approvals",
    )
    assert_response_status_code(response, 201)

    # Fetch StudyActivityInstance after underlying ActivityInstance is edited
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    study_activity_instance = response.json()

    # The red bell should not be shown if there modified property is not any of (topic code, activity instance class or activity instance name)
    assert study_activity_instance["is_activity_instance_updated"] is False
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
        f"/concepts/activities/activity-instances/{new_test_activity_instance.uid}/attributes/versions",
    )
    assert_response_status_code(response, 201)
    # PATCH underling activity-instance - use a modifiable field instead of activity_instance_class_uid
    # DUE TO THE activity_instance_class_uid is not modifiable after creation
    updated_name = "Updated activity instance name for sync test"
    response = api_client.patch(
        f"/concepts/activities/activity-instances/{new_test_activity_instance.uid}/attributes",
        json={
            "name": updated_name,
            "name_sentence_case": updated_name.lower(),
            "change_description": "Sync to latest version test",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.post(
        f"/concepts/activities/activity-instances/{new_test_activity_instance.uid}/attributes/approvals",
    )
    assert_response_status_code(response, 201)

    # Fetch StudyActivityInstance after underlying ActivityInstance is edited
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    study_activity_instance = response.json()

    assert study_activity_instance["is_activity_instance_updated"] is True
    assert study_activity_instance["activity_instance"]["version"] == "1.0"
    assert (
        study_activity_instance["activity_instance"]["activity_instance_class"]["uid"]
        == weight_activity_instance_class.uid
    )
    assert (
        study_activity_instance["activity_instance"]["uid"]
        == new_test_activity_instance.uid
    )
    assert study_activity_instance["latest_activity_instance"]["version"] == "3.0"
    assert (
        study_activity_instance["latest_activity_instance"]["uid"]
        == new_test_activity_instance.uid
    )
    # Check that the name was updated instead of activity_instance_class
    assert study_activity_instance["latest_activity_instance"]["name"] == updated_name

    # Check the ActivityInstance update, decide to keep old version
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "keep_old_version": True,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["keep_old_version"] is True

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["keep_old_version"] is True

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}/sync-latest-version",
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["keep_old_version"] is False

    # Fetch StudyActivityInstance after underlying ActivityInstance is synced to latest version
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
    )
    assert_response_status_code(response, 200)
    study_activity_instance = response.json()
    assert study_activity_instance["is_activity_instance_updated"] is False
    assert study_activity_instance["activity_instance"]["version"] == "3.0"
    assert (
        study_activity_instance["activity_instance"]["uid"]
        == new_test_activity_instance.uid
    )
    # Check that the name was synced
    assert study_activity_instance["activity_instance"]["name"] == updated_name
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
        soa_group_term_uid=term_efficacy_uid,
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
        study_activity_instance["state"]
        == StudyActivityInstanceState.REVIEW_NEEDED.value
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
        == StudyActivityInstanceState.ADD_INSTANCE.value
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
            "soa_group_term_uid": term_efficacy_uid,
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

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "activity_instance_uid": activity_instance_uid,
                    "study_activity_uid": study_activity_uid,
                },
            }
            for activity_instance_uid in req_activity_instance_uids
        ],
    )
    assert_response_status_code(response, 207)

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
        f"/concepts/activities/activity-instances/{activity_instance.uid}/attributes/versions",
    )
    assert_response_status_code(response, 201)
    response = api_client.post(
        f"/concepts/activities/activity-instances/{activity_instance.uid}/attributes/approvals",
    )
    assert_response_status_code(response, 201)
    # After creating a new draft and immidiately approving it, we'll have two Final (1.0, 2.0) versions linked between single root-value nodes
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": new_test_activity.uid,
            "activity_subgroup_uid": body_measurements_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
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


def test_batch_operations(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
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
    study_activity_uid = response.json()["study_activity_uid"]

    response = api_client.get(f"/studies/{test_study.uid}/study-activity-instances")
    assert_response_status_code(response, 200)
    study_activity_instances = response.json()["items"]
    assert len(study_activity_instances) == 1
    study_activity_instance_uid = study_activity_instances[0][
        "study_activity_instance_uid"
    ]

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances/batch",
        json=[
            {
                "method": "PATCH",
                "content": {
                    "study_activity_uid": study_activity_uid,
                    "study_activity_instance_uid": study_activity_instance_uid,
                    "activity_instance_uid": None,
                },
            },
            {
                "method": "POST",
                "content": {
                    "study_activity_uid": study_activity_uid,
                    "activity_instance_uid": second_randomized_activity_instance.uid,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)

    response = api_client.get(f"/studies/{test_study.uid}/study-activity-instances")
    assert_response_status_code(response, 200)
    study_activity_instances = response.json()["items"]
    assert len(study_activity_instances) == 2
    assert any(
        item["activity_instance"] is None
        and item["study_activity_instance_uid"] == study_activity_instance_uid
        for item in study_activity_instances
    )
    assert any(
        item.get("activity_instance", {}).get("uid")
        == second_randomized_activity_instance.uid
        for item in study_activity_instances
    )
    assert study_activity_instances[1]["activity_instance"] is None
    assert (
        study_activity_instances[1]["study_activity_instance_uid"]
        == study_activity_instance_uid
    )
    # Assert sorting by activity instance name succeeds when there exists at least one StudyActivityInstance with no linked ActivityInstance
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
        params={"sort_by": '{"activity_instance.name": true}'},
    )
    assert_response_status_code(response, 200)


def test_study_activity_instances_review_changes_batch(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
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
    study_activity_uid = response.json()["study_activity_uid"]

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "study_activity_uid": study_activity_uid,
                    "activity_instance_uid": second_randomized_activity_instance.uid,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)

    response = api_client.get(f"/studies/{test_study.uid}/study-activity-instances")
    assert_response_status_code(response, 200)
    study_activity_instances = response.json()["items"]

    assert len(study_activity_instances) == 2
    randomized_sa_instance = study_activity_instances[0]["study_activity_instance_uid"]
    assert study_activity_instances[0]["is_reviewed"] is True
    assert (
        study_activity_instances[0]["state"]
        == StudyActivityInstanceState.REVIEW_NOT_NEEDED.value
    )
    second_randomized_sa_instance = study_activity_instances[1][
        "study_activity_instance_uid"
    ]
    assert study_activity_instances[1]["is_reviewed"] is False
    assert (
        study_activity_instances[1]["state"]
        == StudyActivityInstanceState.REVIEW_NEEDED.value
    )

    response = api_client.delete(
        f"/concepts/activities/activity-instances/{randomized_activity_instance.uid}/activations"
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{randomized_sa_instance}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["latest_activity_instance"] is not None
    assert res["latest_activity_instance"]["uid"] == randomized_activity_instance.uid
    assert res["latest_activity_instance"]["status"] == "Retired"
    assert res["activity_instance"]["uid"] == randomized_activity_instance.uid
    assert res["activity_instance"]["status"] == "Final"
    assert res["state"] == StudyActivityInstanceState.REVIEW_NEEDED.value

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances/changes-review/batch",
        json=[
            {
                "action": StudySelectionReviewAction.DECLINE.value,
                "uid": randomized_sa_instance,
                "content": {
                    "keep_old_version": True,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)
    assert response.json()[0]["response_code"] == 204

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{randomized_sa_instance}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["keep_old_version"] is True
    assert res["is_reviewed"] is True
    assert res["latest_activity_instance"] is not None
    assert res["latest_activity_instance"]["uid"] == randomized_activity_instance.uid
    assert res["latest_activity_instance"]["status"] == "Retired"
    assert res["activity_instance"]["uid"] == randomized_activity_instance.uid
    assert res["activity_instance"]["status"] == "Final"
    assert res["state"] == StudyActivityInstanceState.REVIEW_NOT_NEEDED.value

    response = api_client.post(
        f"/concepts/activities/activity-instances/{randomized_activity_instance.uid}/activations"
    )
    assert_response_status_code(response, 200)

    # update library activity instance
    response = api_client.post(
        f"/concepts/activities/activity-instances/{randomized_activity_instance.uid}/attributes/versions"
    )
    assert_response_status_code(response, 201)

    randomized_activity_name_after_update = "Randomized activity name after update"
    response = api_client.patch(
        f"/concepts/activities/activity-instances/{randomized_activity_instance.uid}/attributes",
        json={
            "name": randomized_activity_name_after_update,
            "name_sentence_case": randomized_activity_name_after_update.lower(),
            "change_description": "Updated name",
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activity-instances/{randomized_activity_instance.uid}/attributes/approvals"
    )
    assert_response_status_code(response, 201)

    # update library activity
    response = api_client.post(
        f"/concepts/activities/activity-instances/{second_randomized_activity_instance.uid}/attributes/versions"
    )
    assert_response_status_code(response, 201)

    second_randomized_activity_name_after_update = (
        "Second Randomized activity name after update"
    )
    response = api_client.patch(
        f"/concepts/activities/activity-instances/{second_randomized_activity_instance.uid}/attributes",
        json={
            "name": second_randomized_activity_name_after_update,
            "name_sentence_case": second_randomized_activity_name_after_update.lower(),
            "change_description": "Updated name",
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activity-instances/{second_randomized_activity_instance.uid}/attributes/approvals"
    )
    assert_response_status_code(response, 201)

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances/changes-review/batch",
        json=[
            {
                "action": StudySelectionReviewAction.ACCEPT.value,
                "uid": randomized_sa_instance,
                "content": None,
            },
            {
                "action": StudySelectionReviewAction.DECLINE.value,
                "uid": second_randomized_sa_instance,
                "content": {
                    "keep_old_version": True,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)

    response = api_client.get(f"/studies/{test_study.uid}/study-activity-instances")
    assert_response_status_code(response, 200)
    study_activity_instances = response.json()["items"]
    assert len(study_activity_instances) == 2
    assert study_activity_instances[0]["latest_activity_instance"] is None
    assert (
        study_activity_instances[0]["activity_instance"]["name"]
        == randomized_activity_name_after_update
    )
    assert study_activity_instances[0]["keep_old_version"] is False
    assert study_activity_instances[0]["is_reviewed"] is True
    assert (
        study_activity_instances[0]["state"]
        == StudyActivityInstanceState.REVIEW_NOT_NEEDED.value
    )
    assert (
        study_activity_instances[1]["latest_activity_instance"]["name"]
        == second_randomized_activity_name_after_update
    )
    assert (
        study_activity_instances[1]["activity_instance"]["name"]
        == second_randomized_activity_instance.name
    )
    assert study_activity_instances[1]["keep_old_version"] is True
    assert study_activity_instances[1]["is_reviewed"] is True
    assert (
        study_activity_instances[1]["state"]
        == StudyActivityInstanceState.REVIEWED.value
    )


def test_study_activity_instances_invalidate_keep_old_version(api_client):
    test_study = TestUtils.create_study(project_number=project.project_number)
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

    response = api_client.get(f"/studies/{test_study.uid}/study-activity-instances")
    assert_response_status_code(response, 200)
    study_activity_instances = response.json()["items"]
    assert len(study_activity_instances) == 1
    study_activity_instance_uid = study_activity_instances[0][
        "study_activity_instance_uid"
    ]
    assert study_activity_instances[0]["keep_old_version"] is False
    assert study_activity_instances[0]["latest_activity_instance"] is None
    assert study_activity_instances[0]["activity_instance"]["status"] == "Final"

    response = api_client.delete(
        f"/concepts/activities/activity-instances/{randomized_activity_instance.uid}/activations"
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["keep_old_version"] is False
    assert res["activity_instance"]["status"] == "Final"
    assert res["latest_activity_instance"]["status"] == "Retired"

    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "keep_old_version": True,
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["keep_old_version"] is True
    assert res["is_reviewed"] is True
    assert res["state"] == StudyActivityInstanceState.REVIEW_NOT_NEEDED.value
    assert res["activity_instance"]["status"] == "Final"
    assert res["latest_activity_instance"]["status"] == "Retired"

    response = api_client.post(
        f"/concepts/activities/activity-instances/{randomized_activity_instance.uid}/activations"
    )
    assert_response_status_code(response, 200)

    response = api_client.post(
        f"/concepts/activities/activity-instances/{randomized_activity_instance.uid}/attributes/versions"
    )
    assert_response_status_code(response, 201)

    updated_name = randomized_activity_instance.name + " updated"
    response = api_client.patch(
        f"/concepts/activities/activity-instances/{randomized_activity_instance.uid}/attributes",
        json={
            "name": updated_name,
            "name_sentence_case": updated_name.lower(),
            "change_description": "Updated name",
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.post(
        f"/concepts/activities/activity-instances/{randomized_activity_instance.uid}/attributes/approvals"
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["keep_old_version"] is False
    assert res["is_reviewed"] is False
    assert res["state"] == StudyActivityInstanceState.REVIEW_NEEDED.value
    assert res["activity_instance"]["status"] == "Final"
    assert res["latest_activity_instance"]["status"] == "Final"
    assert res["latest_activity_instance"]["name"] == updated_name

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}/sync-latest-version",
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["keep_old_version"] is False
    assert res["is_reviewed"] is True
    assert res["state"] == StudyActivityInstanceState.REVIEW_NOT_NEEDED.value
    assert res["activity_instance"]["status"] == "Final"
    assert res["activity_instance"]["name"] == updated_name
    assert res["latest_activity_instance"] is None


def test_create_study_activity_instance_with_data_supplier_and_origin_fields(
    api_client,
):
    """Test creating a StudyActivityInstance with data supplier and origin fields (L3 SoA)."""
    test_study = TestUtils.create_study(project_number=project.project_number)

    # First sync the data supplier to the study
    response = api_client.put(
        f"/studies/{test_study.uid}/study-data-suppliers/sync",
        json={
            "suppliers": [
                {
                    "data_supplier_uid": data_supplier.uid,
                    "study_data_supplier_type_uid": supplier_type_term.term_uid,
                },
            ]
        },
    )
    assert_response_status_code(response, 200)
    study_data_supplier_uid = response.json()[0]["study_data_supplier_uid"]

    # Create a study activity
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
    study_activity_uid = response.json()["study_activity_uid"]

    # Get the auto-created study activity instance
    response = api_client.get(f"/studies/{test_study.uid}/study-activity-instances")
    assert_response_status_code(response, 200)
    study_activity_instances = response.json()["items"]
    assert len(study_activity_instances) == 1
    # Initially, data supplier and origin fields should be None
    assert study_activity_instances[0]["study_data_supplier_uid"] is None
    assert study_activity_instances[0]["study_data_supplier_name"] is None
    assert study_activity_instances[0]["origin_type"] is None
    assert study_activity_instances[0]["origin_source"] is None

    # Create a new study activity instance with data supplier and origin fields
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances",
        json={
            "study_activity_uid": study_activity_uid,
            "activity_instance_uid": second_randomized_activity_instance.uid,
            "study_data_supplier_uid": study_data_supplier_uid,
            "origin_type_uid": origin_type_term.term_uid,
            "origin_source_uid": origin_source_term.term_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()

    # Verify the data supplier and origin fields are set
    assert res["study_data_supplier_uid"] == study_data_supplier_uid
    assert res["study_data_supplier_name"] == data_supplier.name
    assert res["origin_type"] is not None
    assert res["origin_type"]["term_uid"] == origin_type_term.term_uid
    assert res["origin_type"]["term_name"] == origin_type_term.sponsor_preferred_name
    assert res["origin_source"] is not None
    assert res["origin_source"]["term_uid"] == origin_source_term.term_uid
    assert (
        res["origin_source"]["term_name"] == origin_source_term.sponsor_preferred_name
    )

    # Verify via GET endpoint
    study_activity_instance_uid = res["study_activity_instance_uid"]
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_data_supplier_uid"] == study_data_supplier_uid
    assert res["study_data_supplier_name"] == data_supplier.name
    assert res["origin_type"]["term_uid"] == origin_type_term.term_uid
    assert res["origin_source"]["term_uid"] == origin_source_term.term_uid

    TestUtils.delete_study(test_study.uid)


def test_edit_study_activity_instance_data_supplier_and_origin_fields(api_client):
    """Test editing data supplier and origin fields on a StudyActivityInstance."""
    test_study = TestUtils.create_study(project_number=project.project_number)

    # Sync data supplier to study
    response = api_client.put(
        f"/studies/{test_study.uid}/study-data-suppliers/sync",
        json={
            "suppliers": [
                {
                    "data_supplier_uid": data_supplier.uid,
                    "study_data_supplier_type_uid": supplier_type_term.term_uid,
                },
            ]
        },
    )
    assert_response_status_code(response, 200)
    study_data_supplier_uid = response.json()[0]["study_data_supplier_uid"]

    # Create a study activity
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

    # Get the auto-created study activity instance
    response = api_client.get(f"/studies/{test_study.uid}/study-activity-instances")
    assert_response_status_code(response, 200)
    study_activity_instance_uid = response.json()["items"][0][
        "study_activity_instance_uid"
    ]

    # Initially fields should be None
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_data_supplier_uid"] is None
    assert res["origin_type"] is None
    assert res["origin_source"] is None

    # PATCH to add data supplier and origin fields
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "study_data_supplier_uid": study_data_supplier_uid,
            "origin_type_uid": origin_type_term.term_uid,
            "origin_source_uid": origin_source_term.term_uid,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_data_supplier_uid"] == study_data_supplier_uid
    assert res["study_data_supplier_name"] == data_supplier.name
    assert res["origin_type"]["term_uid"] == origin_type_term.term_uid
    assert res["origin_source"]["term_uid"] == origin_source_term.term_uid

    # Verify via GET
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_data_supplier_uid"] == study_data_supplier_uid
    assert res["origin_type"]["term_uid"] == origin_type_term.term_uid
    assert res["origin_source"]["term_uid"] == origin_source_term.term_uid

    # Note: Clearing these fields via PATCH (setting to None) is not currently supported
    # due to how fill_missing_values_in_base_model_from_reference_base_model handles
    # Pydantic's model_fields_set when the explicit value equals the default value.

    TestUtils.delete_study(test_study.uid)


def test_study_activity_instance_audit_trail_includes_data_supplier_fields(api_client):
    """Test that audit trail captures changes to data supplier and origin fields."""
    test_study = TestUtils.create_study(project_number=project.project_number)

    # Sync data supplier to study
    response = api_client.put(
        f"/studies/{test_study.uid}/study-data-suppliers/sync",
        json={
            "suppliers": [
                {
                    "data_supplier_uid": data_supplier.uid,
                    "study_data_supplier_type_uid": supplier_type_term.term_uid,
                },
            ]
        },
    )
    assert_response_status_code(response, 200)
    study_data_supplier_uid = response.json()[0]["study_data_supplier_uid"]

    # Create a study activity
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

    # Get the auto-created study activity instance
    response = api_client.get(f"/studies/{test_study.uid}/study-activity-instances")
    assert_response_status_code(response, 200)
    study_activity_instance_uid = response.json()["items"][0][
        "study_activity_instance_uid"
    ]

    # PATCH to add data supplier and origin fields (creates an audit trail entry)
    response = api_client.patch(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}",
        json={
            "study_data_supplier_uid": study_data_supplier_uid,
            "origin_type_uid": origin_type_term.term_uid,
            "origin_source_uid": origin_source_term.term_uid,
        },
    )
    assert_response_status_code(response, 200)

    # Check audit trail for this specific study activity instance
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}/audit-trail"
    )
    assert_response_status_code(response, 200)
    audit_trail = response.json()

    # Should have at least 2 entries: initial creation and the PATCH
    assert len(audit_trail) >= 2

    # Most recent entry should have the data supplier and origin fields
    latest_entry = audit_trail[0]
    assert latest_entry["study_data_supplier_uid"] == study_data_supplier_uid
    assert latest_entry["study_data_supplier_name"] == data_supplier.name
    assert latest_entry["origin_type"]["term_uid"] == origin_type_term.term_uid
    assert latest_entry["origin_source"]["term_uid"] == origin_source_term.term_uid

    # Previous entry (initial creation) should have None for these fields
    initial_entry = audit_trail[1]
    assert initial_entry["study_data_supplier_uid"] is None
    assert initial_entry["origin_type"] is None
    assert initial_entry["origin_source"] is None

    TestUtils.delete_study(test_study.uid)


def test_batch_create_study_activity_instance_with_data_supplier_and_origin_fields(
    api_client,
):
    """Test batch creating StudyActivityInstances with data supplier and origin fields."""
    test_study = TestUtils.create_study(project_number=project.project_number)

    # Sync data supplier to study
    response = api_client.put(
        f"/studies/{test_study.uid}/study-data-suppliers/sync",
        json={
            "suppliers": [
                {
                    "data_supplier_uid": data_supplier.uid,
                    "study_data_supplier_type_uid": supplier_type_term.term_uid,
                },
            ]
        },
    )
    assert_response_status_code(response, 200)
    study_data_supplier_uid = response.json()[0]["study_data_supplier_uid"]

    # Create a study activity
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
    study_activity_uid = response.json()["study_activity_uid"]

    # Batch create with data supplier and origin fields
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "study_activity_uid": study_activity_uid,
                    "activity_instance_uid": second_randomized_activity_instance.uid,
                    "study_data_supplier_uid": study_data_supplier_uid,
                    "origin_type_uid": origin_type_term.term_uid,
                    "origin_source_uid": origin_source_term.term_uid,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)

    # Get all study activity instances and find the one we just created
    response = api_client.get(f"/studies/{test_study.uid}/study-activity-instances")
    assert_response_status_code(response, 200)
    items = response.json()["items"]

    # Find the instance with the second_randomized_activity_instance
    created_instance = next(
        (
            item
            for item in items
            if item.get("activity_instance")
            and item["activity_instance"]["uid"]
            == second_randomized_activity_instance.uid
        ),
        None,
    )
    assert created_instance is not None
    assert created_instance["study_data_supplier_uid"] == study_data_supplier_uid
    assert created_instance["origin_type"]["term_uid"] == origin_type_term.term_uid
    assert created_instance["origin_source"]["term_uid"] == origin_source_term.term_uid

    TestUtils.delete_study(test_study.uid)


def test_study_activity_instance_headers_for_data_supplier_name(api_client):
    """Test headers endpoint returns unique study_data_supplier_name values."""
    test_study = TestUtils.create_study(project_number=project.project_number)

    # Sync data supplier to study
    response = api_client.put(
        f"/studies/{test_study.uid}/study-data-suppliers/sync",
        json={
            "suppliers": [
                {
                    "data_supplier_uid": data_supplier.uid,
                    "study_data_supplier_type_uid": supplier_type_term.term_uid,
                },
            ]
        },
    )
    assert_response_status_code(response, 200)
    study_data_supplier_uid = response.json()[0]["study_data_supplier_uid"]

    # Create study activities with different data suppliers
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
    study_activity_uid = response.json()["study_activity_uid"]

    # Create instance with data supplier
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances",
        json={
            "study_activity_uid": study_activity_uid,
            "activity_instance_uid": second_randomized_activity_instance.uid,
            "study_data_supplier_uid": study_data_supplier_uid,
        },
    )
    assert_response_status_code(response, 201)

    # Test headers endpoint for study_data_supplier_name
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/headers?field_name=study_data_supplier_name"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert data_supplier.name in res

    TestUtils.delete_study(test_study.uid)


@pytest.mark.parametrize(
    "export_format",
    [pytest.param("csv"), pytest.param("xml"), pytest.param("excel")],
)
def test_study_activity_instances_export_includes_data_supplier_fields(
    api_client, export_format
):
    """Test that CSV/XML/Excel exports include data supplier and origin fields."""
    test_study = TestUtils.create_study(project_number=project.project_number)

    # Sync data supplier to study
    response = api_client.put(
        f"/studies/{test_study.uid}/study-data-suppliers/sync",
        json={
            "suppliers": [
                {
                    "data_supplier_uid": data_supplier.uid,
                    "study_data_supplier_type_uid": supplier_type_term.term_uid,
                },
            ]
        },
    )
    assert_response_status_code(response, 200)
    study_data_supplier_uid = response.json()[0]["study_data_supplier_uid"]

    # Create a study activity
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
    study_activity_uid = response.json()["study_activity_uid"]

    # Create instance with data supplier and origin fields
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances",
        json={
            "study_activity_uid": study_activity_uid,
            "activity_instance_uid": second_randomized_activity_instance.uid,
            "study_data_supplier_uid": study_data_supplier_uid,
            "origin_type_uid": origin_type_term.term_uid,
            "origin_source_uid": origin_source_term.term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # Export and verify data contains the new fields
    url = f"/studies/{test_study.uid}/study-activity-instances"
    response = api_client.get(f"{url}?export={export_format}")
    assert_response_status_code(response, 200)

    # For CSV, check that the content includes the field values
    if export_format == "csv":
        content = response.text
        assert "study_data_supplier_uid" in content or "Study Data Supplier" in content
        assert study_data_supplier_uid in content or data_supplier.name in content

    TestUtils.delete_study(test_study.uid)


def test_batch_patch_study_activity_instance_data_supplier_and_origin_fields(
    api_client,
):
    """Test batch PATCH operations on data supplier and origin fields."""
    test_study = TestUtils.create_study(project_number=project.project_number)

    # Sync data supplier to study
    response = api_client.put(
        f"/studies/{test_study.uid}/study-data-suppliers/sync",
        json={
            "suppliers": [
                {
                    "data_supplier_uid": data_supplier.uid,
                    "study_data_supplier_type_uid": supplier_type_term.term_uid,
                },
            ]
        },
    )
    assert_response_status_code(response, 200)
    study_data_supplier_uid = response.json()[0]["study_data_supplier_uid"]

    # Create a study activity
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
    study_activity_uid = response.json()["study_activity_uid"]

    # Get the auto-created study activity instance
    response = api_client.get(f"/studies/{test_study.uid}/study-activity-instances")
    assert_response_status_code(response, 200)
    study_activity_instance_uid = response.json()["items"][0][
        "study_activity_instance_uid"
    ]

    # Batch PATCH to add data supplier and origin fields
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances/batch",
        json=[
            {
                "method": "PATCH",
                "content": {
                    "study_activity_instance_uid": study_activity_instance_uid,
                    "study_activity_uid": study_activity_uid,
                    "study_data_supplier_uid": study_data_supplier_uid,
                    "origin_type_uid": origin_type_term.term_uid,
                    "origin_source_uid": origin_source_term.term_uid,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)
    batch_results = response.json()
    assert batch_results[0]["response_code"] == 200

    # Verify the changes
    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances/{study_activity_instance_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["study_data_supplier_uid"] == study_data_supplier_uid
    assert res["study_data_supplier_name"] == data_supplier.name
    assert res["origin_type"]["term_uid"] == origin_type_term.term_uid
    assert res["origin_source"]["term_uid"] == origin_source_term.term_uid

    TestUtils.delete_study(test_study.uid)


@pytest.mark.parametrize(
    "field,invalid_uid,expected_msg",
    [
        (
            "origin_type_uid",
            "InvalidUid_1",
            "Origin Type Term with UID 'InvalidUid_1' doesn't exist.",
        ),
        (
            "origin_source_uid",
            "InvalidUid_2",
            "Origin Source Term with UID 'InvalidUid_2' doesn't exist.",
        ),
    ],
)
def test_study_activity_instance_invalid_origin_uid(
    api_client, field, invalid_uid, expected_msg
):
    """Test that invalid origin UIDs return 400 error."""
    test_study = TestUtils.create_study(project_number=project.project_number)
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
    study_activity_uid = response.json()["study_activity_uid"]

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances",
        json={
            "study_activity_uid": study_activity_uid,
            "activity_instance_uid": second_randomized_activity_instance.uid,
            field: invalid_uid,
        },
    )
    assert_response_status_code(response, 400)
    assert response.json()["message"] == expected_msg
    TestUtils.delete_study(test_study.uid)


def test_study_activity_instance_origin_term_not_in_codelist(api_client):
    """Test that using a term from wrong codelist returns 400 error."""
    test_study = TestUtils.create_study(project_number=project.project_number)
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
    study_activity_uid = response.json()["study_activity_uid"]

    # Use supplier_type_term which exists but is NOT in ORIGINT codelist
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances",
        json={
            "study_activity_uid": study_activity_uid,
            "activity_instance_uid": second_randomized_activity_instance.uid,
            "origin_type_uid": supplier_type_term.term_uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert "was not found in the codelist" in res["message"]
    TestUtils.delete_study(test_study.uid)


# ────────────────────────────────────────────────────────────────────────────
# Tests for StudyActivityInstance state field
# ────────────────────────────────────────────────────────────────────────────


def test_state_not_applicable_for_non_data_collection_activity(api_client):
    """
    Requirement: User must be presented with 'Not applicable' state for every
    non-data collection study activity.
    """
    test_study = TestUtils.create_study(project_number=project.project_number)

    non_dc_activity_group = TestUtils.create_activity_group(name="NonDC Group")
    non_dc_activity_subgroup = TestUtils.create_activity_subgroup(name="NonDC SubGroup")
    non_dc_activity = TestUtils.create_activity(
        name="Non Data Collection Activity",
        activity_subgroups=[non_dc_activity_subgroup.uid],
        activity_groups=[non_dc_activity_group.uid],
        library_name="Sponsor",
        is_data_collected=False,
    )

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": non_dc_activity.uid,
            "activity_subgroup_uid": non_dc_activity_subgroup.uid,
            "activity_group_uid": non_dc_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]
    assert len(items) >= 1
    for item in items:
        assert item["state"] == StudyActivityInstanceState.NOT_APPLICABLE.value

    TestUtils.delete_study(test_study.uid)


def test_state_review_needed_for_default_activity_instance(api_client):
    """
    Requirement: User must be presented with 'Review needed' state when
    activity instance selected for study activity is default (not mandatory).
    """
    test_study = TestUtils.create_study(project_number=project.project_number)

    default_activity_group = TestUtils.create_activity_group(name="Default AI Group")
    default_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Default AI SubGroup"
    )
    default_activity = TestUtils.create_activity(
        name="Activity With Default Instance",
        activity_subgroups=[default_activity_subgroup.uid],
        activity_groups=[default_activity_group.uid],
        library_name="Sponsor",
        is_data_collected=True,
    )
    default_instance_class = TestUtils.create_activity_instance_class(
        name="Default Instance Class"
    )
    TestUtils.create_activity_instance(
        name="Default selected instance",
        activity_instance_class_uid=default_instance_class.uid,
        name_sentence_case="default selected instance",
        topic_code="default_selected_topic",
        is_required_for_activity=False,
        is_default_selected_for_activity=True,
        activities=[default_activity.uid],
        activity_subgroups=[default_activity_subgroup.uid],
        activity_groups=[default_activity_group.uid],
        activity_items=[],
    )

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": default_activity.uid,
            "activity_subgroup_uid": default_activity_subgroup.uid,
            "activity_group_uid": default_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["state"] == StudyActivityInstanceState.REVIEW_NEEDED.value
    assert items[0]["is_reviewed"] is False

    TestUtils.delete_study(test_study.uid)


def test_state_review_not_needed_for_mandatory_activity_instance(api_client):
    """
    Requirement: User must be presented with 'Review not needed' and checked
    Reviewed checkbox when activity instance selected for study activity is mandatory.
    """
    test_study = TestUtils.create_study(project_number=project.project_number)

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

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]
    # The auto-created instance corresponds to randomized_activity_instance which is mandatory
    mandatory_items = [
        item
        for item in items
        if item.get("activity_instance")
        and item["activity_instance"]["is_required_for_activity"]
    ]
    assert len(mandatory_items) >= 1
    for item in mandatory_items:
        assert item["state"] == StudyActivityInstanceState.REVIEW_NOT_NEEDED.value
        assert item["is_reviewed"] is True

    TestUtils.delete_study(test_study.uid)


def test_state_add_instance_when_no_activity_instance_linked(api_client):
    """
    Requirement: User must be presented with 'Add instance' and disabled Reviewed
    checkbox when study activity is not linked to any activity instance.
    """
    test_study = TestUtils.create_study(project_number=project.project_number)

    # Create an activity that has no linked activity instances
    orphan_activity_group = TestUtils.create_activity_group(name="Orphan Group")
    orphan_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Orphan SubGroup"
    )
    orphan_activity = TestUtils.create_activity(
        name="Activity Without Instances",
        activity_subgroups=[orphan_activity_subgroup.uid],
        activity_groups=[orphan_activity_group.uid],
        library_name="Sponsor",
        is_data_collected=True,
    )

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": orphan_activity.uid,
            "activity_subgroup_uid": orphan_activity_subgroup.uid,
            "activity_group_uid": orphan_activity_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["state"] == StudyActivityInstanceState.ADD_INSTANCE.value
    assert items[0]["activity_instance"] is None
    assert items[0]["is_reviewed"] is False

    TestUtils.delete_study(test_study.uid)


def test_state_remove_instance_when_too_many_instances(api_client):
    """
    Requirement: User must be presented with 'Remove instance' and disabled Reviewed
    checkbox when study activity has more linked activity instances than allowed
    for that study activity (is_multiple_selection_allowed=False with >1 instance).
    """
    test_study = TestUtils.create_study(project_number=project.project_number)

    single_select_group = TestUtils.create_activity_group(name="SingleSelect Group")
    single_select_subgroup = TestUtils.create_activity_subgroup(
        name="SingleSelect SubGroup"
    )
    single_select_activity = TestUtils.create_activity(
        name="Single Select Activity",
        activity_subgroups=[single_select_subgroup.uid],
        activity_groups=[single_select_group.uid],
        library_name="Sponsor",
        is_data_collected=True,
        is_multiple_selection_allowed=False,
    )
    single_select_instance_class = TestUtils.create_activity_instance_class(
        name="SingleSelect Instance Class"
    )
    TestUtils.create_activity_instance(
        name="SingleSelect required instance",
        activity_instance_class_uid=single_select_instance_class.uid,
        name_sentence_case="singleselect required instance",
        topic_code="single_select_required_topic",
        is_required_for_activity=True,
        activities=[single_select_activity.uid],
        activity_subgroups=[single_select_subgroup.uid],
        activity_groups=[single_select_group.uid],
        activity_items=[],
    )
    extra_instance = TestUtils.create_activity_instance(
        name="SingleSelect extra instance",
        activity_instance_class_uid=single_select_instance_class.uid,
        name_sentence_case="singleselect extra instance",
        topic_code="single_select_extra_topic",
        is_required_for_activity=False,
        activities=[single_select_activity.uid],
        activity_subgroups=[single_select_subgroup.uid],
        activity_groups=[single_select_group.uid],
        activity_items=[],
    )

    response = api_client.post(
        f"/studies/{test_study.uid}/study-activities",
        json={
            "activity_uid": single_select_activity.uid,
            "activity_subgroup_uid": single_select_subgroup.uid,
            "activity_group_uid": single_select_group.uid,
            "soa_group_term_uid": term_efficacy_uid,
        },
    )
    assert_response_status_code(response, 201)
    study_activity_uid = response.json()["study_activity_uid"]

    # Auto-creation should have created one instance (the required one).
    # Now manually add a second instance to exceed the allowed count.
    response = api_client.post(
        f"/studies/{test_study.uid}/study-activity-instances/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "activity_instance_uid": extra_instance.uid,
                    "study_activity_uid": study_activity_uid,
                },
            }
        ],
    )
    assert_response_status_code(response, 207)

    response = api_client.get(
        f"/studies/{test_study.uid}/study-activity-instances",
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]
    assert len(items) == 2
    for item in items:
        assert item["state"] == StudyActivityInstanceState.REMOVE_INSTANCE.value

    TestUtils.delete_study(test_study.uid)


def test_clone_big_study_with_study_activity_flags_enabled(api_client):
    response = api_client.post(
        "/studies/Study_000001/clone",
        json={
            "study_number": "9002",
            "study_acronym": "9002",
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
