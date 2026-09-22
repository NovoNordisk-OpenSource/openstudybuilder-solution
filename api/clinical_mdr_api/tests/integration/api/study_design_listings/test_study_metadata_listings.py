# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models import study_selections
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import inject_base_data
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_some_visits,
    create_study_arm,
    create_study_branch_arm,
    create_study_cohort,
    create_study_design_cell,
    create_study_element,
    create_study_epoch_codelists_ret_cat_and_lib,
    get_catalogue_name_library_name,
    input_metadata_in_study,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

study_uid: str
study_number: str
project_id: str
study: Study
test_data_dict: dict[str, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("StudyListingTestAPI")
    TestUtils.create_library(name="UCUM", is_editable=True)
    global study, test_data_dict
    study, test_data_dict = inject_base_data()
    TestUtils.create_ct_codelist()
    TestUtils.create_study_ct_data_map(codelist_uid=None)

    global study_uid
    study_uid = study.uid
    global study_number
    study_number = study.current_metadata.identification_metadata.study_number
    global project_id
    project_id = study.current_metadata.identification_metadata.project_number
    # Inject study metadata
    input_metadata_in_study(study_uid)
    # Create study epochs
    create_study_epoch_codelists_ret_cat_and_lib(use_test_utils=True)
    catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    study_epoch = TestUtils.create_study_epoch(
        study_uid=study_uid, epoch_subtype="EpochSubType_0001"
    )
    study_epoch2 = TestUtils.create_study_epoch(
        study_uid=study_uid, epoch_subtype="EpochSubType_0002"
    )
    # Create study elements
    element_type_codelist = create_codelist(
        "Element Type",
        "CTCodelist_ElementType",
        catalogue_name,
        library_name,
        submission_value="ELEMTP",
    )
    create_ct_term(
        "Element Type",
        "ElementType_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": element_type_codelist.codelist_uid,
                "order": 1,
                "submission_value": "ElementType1",
            }
        ],
    )

    element_subtype_codelist = create_codelist(
        "Element Sub Type",
        "CTCodelist_ElementSubType",
        catalogue_name,
        library_name,
        submission_value="ELEMSTP",
    )
    element_subtype_term = create_ct_term(
        "Element Sub Type",
        "ElementSubType_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": element_subtype_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Element Sub Type",
            }
        ],
    )
    element_subtype_term_2 = create_ct_term(
        "Element Sub Type 2",
        "ElementSubType_0002",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": element_subtype_codelist.codelist_uid,
                "order": 2,
                "submission_value": "Element Sub Type 2",
            }
        ],
    )
    study_elements = [
        create_study_element(element_subtype_term.uid, study_uid),
        create_study_element(element_subtype_term_2.uid, study_uid),
    ]

    # Create study arms
    codelist = create_codelist(
        name="Arm Type",
        uid="CTCodelist_00019",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="ARMTTP",
    )
    arm_type = create_ct_term(
        name="Arm Type",
        uid="ArmType_0001",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "Arm Type",
            },
        ],
    )

    create_study_arm(
        study_uid=study_uid,
        name="Arm_Name_1",
        short_name="Arm_Short_Name_1",
        code="Arm_code_1",
        description="desc...",
        randomization_group="Arm_randomizationGroup",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )
    create_study_arm(
        study_uid=study_uid,
        name="Arm_Name_2",
        short_name="Arm_Short_Name_2",
        code="Arm_code_2",
        description="desc...",
        randomization_group="Arm_randomizationGroup2",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )
    create_study_arm(
        study_uid=study_uid,
        name="Arm_Name_3",
        short_name="Arm_Short_Name_3",
        code="Arm_code_3",
        description="desc...",
        randomization_group="Arm_randomizationGroup3",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )

    create_study_arm(
        study_uid=study_uid,
        name="Arm_Name_9",
        short_name="Arm_Short_Name_9",
        code="Arm_code_9",
        description="desc...",
        randomization_group="Arm_randomizationGroup9",
        number_of_subjects=100,
        arm_type_uid=arm_type.uid,
    )

    # Create study design cells
    create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch.uid,
        study_arm_uid="StudyArm_000002",
        study_uid=study_uid,
    )
    create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid="StudyArm_000002",
        study_uid=study_uid,
    )

    create_study_design_cell(
        study_element_uid=study_elements[1].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid="StudyArm_000001",
        study_uid=study_uid,
    )

    create_study_design_cell(
        study_element_uid=study_elements[0].element_uid,
        study_epoch_uid=study_epoch2.uid,
        study_arm_uid="StudyArm_000003",
        study_uid=study_uid,
    )

    # Create study branch arms
    create_study_branch_arm(
        study_uid=study_uid,
        name="Branch_Arm_Name_1",
        short_name="Branch_Arm_Short_Name_1",
        code="Branch_Arm_code_1",
        description="desc...",
        randomization_group="Branch_Arm_randomizationGroup",
        number_of_subjects=100,
        arm_uid="StudyArm_000002",
    )

    # Create study cohort
    create_study_cohort(
        study_uid=study_uid,
        name="Cohort_Name_1",
        short_name="Cohort_Short_Name_1",
        code="Cohort_code_1",
        description="desc...",
        number_of_subjects=100,
        arm_uids=["StudyArm_000001"],
    )

    # Create study visit
    create_some_visits(
        use_test_utils=True,
        create_epoch_codelist=False,
        study_uid=study_uid,
        epoch1=study_epoch,
        epoch2=study_epoch2,
    )

    type_codelist = TestUtils.create_ct_codelist(
        name="Criteria Type",
        submission_value="CRITRTP",
        extensible=True,
        approve=True,
    )

    # Create CT Terms
    ct_term_inclusion_criteria = TestUtils.create_ct_term(
        sponsor_preferred_name="INCLUSION CRITERIA",
        codelist_uid=type_codelist.codelist_uid,
    )
    ct_term_exclusion_criteria = TestUtils.create_ct_term(
        sponsor_preferred_name="EXCLUSION CRITERIA",
        codelist_uid=type_codelist.codelist_uid,
    )

    # Create templates
    incl_criteria_template_1 = TestUtils.create_criteria_template(
        type_uid=ct_term_inclusion_criteria.term_uid
    )
    excl_criteria_template_1 = TestUtils.create_criteria_template(
        type_uid=ct_term_exclusion_criteria.term_uid
    )

    # Create study criterias
    TestUtils.create_study_criteria(
        study_uid=study_uid,
        criteria_template_uid=incl_criteria_template_1.uid,
        library_name=incl_criteria_template_1.library.name,
        parameter_terms=[],
    )

    TestUtils.create_study_criteria(
        study_uid=study_uid,
        criteria_template_uid=excl_criteria_template_1.uid,
        library_name=excl_criteria_template_1.library.name,
        parameter_terms=[],
    )

    # Create objective template
    objective_template = TestUtils.create_objective_template()
    TestUtils.create_study_objective(
        study_uid=study_uid,
        objective_template_uid=objective_template.uid,
        parameter_terms=[],
    )

    # Create study objectives
    study_objective = TestUtils.create_study_objective(
        study_uid=study_uid,
        objective_template_uid=objective_template.uid,
        library_name=objective_template.library.name,
        parameter_terms=[],
    )

    # Create endpoint templates
    TestUtils.create_template_parameter(settings.study_endpoint_tp_name)
    endpoint_template = TestUtils.create_endpoint_template()

    unit_definitions = [
        TestUtils.create_unit_definition(name="unit1"),
        TestUtils.create_unit_definition(name="unit2"),
    ]
    unit_separator = "and"
    timeframe_template = TestUtils.create_timeframe_template()
    timeframe = TestUtils.create_timeframe(
        timeframe_template_uid=timeframe_template.uid
    )

    # Create study endpoints
    TestUtils.create_study_endpoint(
        study_uid=study_uid,
        endpoint_template_uid=endpoint_template.uid,
        endpoint_units=study_selections.study_selection.EndpointUnitsInput(
            units=[u.uid for u in unit_definitions], separator=unit_separator
        ),
        timeframe_uid=timeframe.uid,
        library_name=endpoint_template.library.name,
    )

    TestUtils.create_study_endpoint(
        study_uid=study_uid,
        endpoint_template_uid=endpoint_template.uid,
        library_name=endpoint_template.library.name,
        timeframe_uid=timeframe.uid,
        study_objective_uid=study_objective.study_objective_uid,
    )

    # lock study
    study_service = StudyService()
    study_service.lock(
        uid=study_uid,
        change_description="locking it",
        reason_for_lock_term_uid=test_data_dict["reason_for_lock_terms"][0].term_uid,
    )
    study_service.unlock(
        uid=study_uid,
        reason_for_unlock_term_uid=test_data_dict["reason_for_unlock_terms"][
            0
        ].term_uid,
    )


def test_study_metadata_listing_api(api_client):
    response = api_client.get(
        f"/listings/studies/study-metadata?project_id={project_id}&study_number={study_number}&datetime=2099-12-30",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res is not None

    expected_output = {
        "api_ver": "TBA",
        "study_id": f"{study.current_metadata.identification_metadata.project_number}-{study.current_metadata.identification_metadata.study_number}",
        "study_ver": 1.0,
        "specified_dt": "2099-12-30",
        "request_dt": "2024-03-18T10:41:58",
        "title": "Some Study Title for Testing",
        "reg_id": {
            "ct_gov": "some ct gov id",
            "eudract": "some eudtact id",
            "utn": "some utn id",
            "japic": "some japic id",
            "ind": "some ind id",
            "eutn": "some etn",
            "civ": "some cisn",
            "nctn": "some nctn",
            "jrct": "some jrct",
            "nmpa": "some nmpa",
            "esn": "some esn",
            "ide": "some ide",
            "eupn": "some eupn",
        },
        "study_type": {
            "stype": "",
            "stype_nf": "",
            "trial_type": [],
            "trial_type_nf": "",
            "phase": "",
            "phase_nf": "",
            "extension": "N",
            "extension_nf": "",
            "adaptive": "N",
            "adaptive_nf": "",
            "stop_rule": "some stop rule",
            "stop_rule_nf": "",
            "confirmed_res_min_dur": "",
            "confirmed_res_min_dur_nf": "",
            "post_auth": "Y",
            "post_auth_nf": "",
        },
        "study_attributes": {
            "intv_type": "",
            "intv_type_nf": "",
            "add_on": "N",
            "add_on_nf": "",
            "control_type": "",
            "control_type_nf": "",
            "intv_model": "",
            "intv_model_nf": "",
            "randomised": "Y",
            "randomised_nf": "",
            "strata": "Some stratification factors",
            "strata_nf": "",
            "blinding": "",
            "blinding_nf": "",
            "planned_length": "",
            "planned_length_nf": "",
            "study_intent": [],
            "study_intent_nf": "",
        },
        "study_population": {
            "therapy_area": [],
            "therapy_area_nf": "",
            "indication": [],
            "indication_nf": "",
            "diag_grp": [],
            "diag_grp_nf": "",
            "sex": "",
            "sex_nf": "",
            "rare_dis": "N",
            "rare_dis_nf": "",
            "healthy_subj": "N",
            "healthy_subj_nf": "",
            "min_age": "",
            "min_age_nf": "",
            "max_age": "",
            "max_age_nf": "",
            "stable_dis_min_dur": "",
            "stable_dis_min_dur_nf": "",
            "pediatric": "N",
            "pediatric_nf": "",
            "pediatric_postmarket": "N",
            "pediatric_postmarket_nf": "",
            "pediatric_inv": "Y",
            "pediatric_inv_nf": "",
            "relapse_criteria": "some criteria",
            "relapse_criteria_nf": "",
            "plan_no_subject": None,
            "plan_no_subject_nf": "",
        },
        "arms": [
            {
                "uid": "StudyArm_000001",
                "name": "Arm_Name_1",
                "short_name": "Arm_Short_Name_1",
                "code": "Arm_code_1",
                "no_subject": 100,
                "desc": "desc...",
                "order": 1,
                "rand_grp": "Arm_randomizationGroup",
                "type": "test",
            },
            {
                "uid": "StudyArm_000002",
                "name": "Arm_Name_2",
                "short_name": "Arm_Short_Name_2",
                "code": "Arm_code_2",
                "no_subject": 100,
                "desc": "desc...",
                "order": 2,
                "rand_grp": "Arm_randomizationGroup2",
                "type": "test",
            },
            {
                "uid": "StudyArm_000003",
                "name": "Arm_Name_3",
                "short_name": "Arm_Short_Name_3",
                "code": "Arm_code_3",
                "no_subject": 100,
                "desc": "desc...",
                "order": 3,
                "rand_grp": "Arm_randomizationGroup3",
                "type": "test",
            },
            {
                "uid": "StudyArm_000004",
                "name": "Arm_Name_9",
                "short_name": "Arm_Short_Name_9",
                "code": "Arm_code_9",
                "no_subject": 100,
                "desc": "desc...",
                "order": 4,
                "rand_grp": "Arm_randomizationGroup9",
                "type": "test",
            },
        ],
        "branches": [
            {
                "uid": "StudyBranchArm_000001",
                "name": "Branch_Arm_Name_1",
                "short_name": "Branch_Arm_Short_Name_1",
                "code": "Branch_Arm_code_1",
                "no_subject": 100,
                "desc": "desc...",
                "order": 1,
                "arm_uid": "StudyArm_000002",
                "rand_grp": "Branch_Arm_randomizationGroup",
            }
        ],
        "cohorts": [
            {
                "uid": "StudyCohort_000001",
                "name": "Cohort_Name_1",
                "short_name": "Cohort_Short_Name_1",
                "code": "Cohort_code_1",
                "no_subject": 100,
                "desc": "desc...",
                "arm_uid": ["StudyArm_000001"],
                "branch_uid": [],
            }
        ],
        "epochs": [
            {
                "uid": "StudyEpoch_000001",
                "order": 1,
                "name": "Epoch Subtype",
                "type": "test",
                "subtype": "test",
                "start_rule": "",
                "end_rule": "",
                "description": "",
            },
            {
                "uid": "StudyEpoch_000002",
                "order": 2,
                "name": "Epoch Subtype1",
                "type": "test",
                "subtype": "test",
                "start_rule": "",
                "end_rule": "",
                "description": "",
            },
        ],
        "elements": [
            {
                "uid": "StudyElement_000001",
                "order": 1,
                "name": "Element_Name_1",
                "short_name": "Element_Short_Name_1",
                "type": "uid: Element_code_1 not found",
                "subtype": "test",
                "start_rule": "",
                "end_rule": "",
                "dur": "",
                "desc": "desc...",
            },
            {
                "uid": "StudyElement_000002",
                "order": 2,
                "name": "Element_Name_1",
                "short_name": "Element_Short_Name_1",
                "type": "uid: Element_code_1 not found",
                "subtype": "test",
                "start_rule": "",
                "end_rule": "",
                "dur": "",
                "desc": "desc...",
            },
        ],
        "design_matrix": [
            {
                "arm_uid": "",
                "branch_uid": "StudyBranchArm_000001",
                "epoch_uid": "StudyEpoch_000001",
                "element_uid": "StudyElement_000001",
            },
            {
                "arm_uid": "",
                "branch_uid": "StudyBranchArm_000001",
                "epoch_uid": "StudyEpoch_000002",
                "element_uid": "StudyElement_000001",
            },
            {
                "arm_uid": "StudyArm_000001",
                "branch_uid": "",
                "epoch_uid": "StudyEpoch_000002",
                "element_uid": "StudyElement_000002",
            },
            {
                "arm_uid": "StudyArm_000003",
                "branch_uid": "",
                "epoch_uid": "StudyEpoch_000002",
                "element_uid": "StudyElement_000001",
            },
        ],
        "visits": [
            {
                "epoch_uid": "StudyEpoch_000001",
                "epoch_name": "Epoch Subtype",
                "visit_type": "BASELINE",
                "contact_model": "On Site Visit",
                "visit_no": "100",
                "name": "Visit 1",
                "short_name": "V1",
                "study_day": 1,
                "window_min": -1,
                "window_max": 1,
                "window_unit": "day",
                "desc": "description",
                "epoch_alloc": "",
                "start_rule": "start_rule",
                "end_rule": "end_rule",
            },
            {
                "epoch_uid": "StudyEpoch_000001",
                "epoch_name": "Epoch Subtype",
                "visit_type": "Visit Type2",
                "contact_model": "On Site Visit",
                "visit_no": "200",
                "name": "Visit 2",
                "short_name": "V2",
                "study_day": 11,
                "window_min": -1,
                "window_max": 1,
                "window_unit": "day",
                "desc": "description",
                "epoch_alloc": "",
                "start_rule": "start_rule",
                "end_rule": "end_rule",
            },
            {
                "epoch_uid": "StudyEpoch_000001",
                "epoch_name": "Epoch Subtype",
                "visit_type": "Visit Type2",
                "contact_model": "On Site Visit",
                "visit_no": "300",
                "name": "Visit 3",
                "short_name": "V3",
                "study_day": 13,
                "window_min": -1,
                "window_max": 1,
                "window_unit": "day",
                "desc": "description",
                "epoch_alloc": "",
                "start_rule": "start_rule",
                "end_rule": "end_rule",
            },
            {
                "epoch_uid": "StudyEpoch_000002",
                "epoch_name": "Epoch Subtype1",
                "visit_type": "BASELINE2",
                "contact_model": "On Site Visit",
                "visit_no": "400",
                "name": "Visit 4",
                "short_name": "V4D1",
                "study_day": 31,
                "window_min": -1,
                "window_max": 1,
                "window_unit": "day",
                "desc": "description",
                "epoch_alloc": "",
                "start_rule": "start_rule",
                "end_rule": "end_rule",
            },
            {
                "epoch_uid": "StudyEpoch_000002",
                "epoch_name": "Epoch Subtype1",
                "visit_type": "Visit Type3",
                "contact_model": "On Site Visit",
                "visit_no": "500",
                "name": "Visit 5",
                "short_name": "V5",
                "study_day": 36,
                "window_min": -1,
                "window_max": 1,
                "window_unit": "day",
                "desc": "description",
                "epoch_alloc": "",
                "start_rule": "start_rule",
                "end_rule": "end_rule",
            },
            {
                "epoch_uid": "StudyEpoch_000002",
                "epoch_name": "Epoch Subtype1",
                "visit_type": "Visit Type2",
                "contact_model": "On Site Visit",
                "visit_no": "410",
                "name": "Visit 4",
                "short_name": "V4D32",
                "study_day": 62,
                "window_min": -1,
                "window_max": 1,
                "window_unit": "day",
                "desc": "description",
                "epoch_alloc": "",
                "start_rule": "start_rule",
                "end_rule": "end_rule",
            },
        ],
        "criteria": [
            {"type": "code_submission_value-938695620", "text": "ct-2909257234"},
            {"type": "code_submission_value-8594230448", "text": "ct-2050518536"},
        ],
        "objectives": [
            {"uid": "StudyObjective_000001", "type": "", "text": "ot-5233975461"},
            {"uid": "StudyObjective_000002", "type": "", "text": "ot-5233975461"},
        ],
        "endpoints": [
            {
                "uid": "StudyEndpoint_000003",
                "type": "",
                "subtype": "",
                "text": "et-1714377337",
                "objective_uid": "StudyObjective_000002",
                "timeframe": "tt-7280569194",
                "endpoint_unit": "",
            },
            {
                "uid": "StudyEndpoint_000001",
                "type": "",
                "subtype": "",
                "text": "et-1714377337",
                "objective_uid": "",
                "timeframe": "tt-7280569194",
                "endpoint_unit": "unit1 and unit2",
            },
        ],
    }

    print("******************")
    print(res)
    print("******************")

    assert res["api_ver"] == expected_output["api_ver"]
    assert res["study_id"] == expected_output["study_id"]
    assert res["study_ver"] == expected_output["study_ver"]
    assert res["specified_dt"] == expected_output["specified_dt"]
    assert res["title"] == expected_output["title"]
    assert res["reg_id"] == expected_output["reg_id"]
    assert res["study_type"] == expected_output["study_type"]
    assert res["study_attributes"] == expected_output["study_attributes"]
    assert res["study_population"] == expected_output["study_population"]
    assert res["arms"] == expected_output["arms"]
    assert res["branches"] == expected_output["branches"]
    assert res["cohorts"] == expected_output["cohorts"]
    assert res["epochs"] == expected_output["epochs"]
    assert res["elements"] == expected_output["elements"]
    assert res["design_matrix"] == expected_output["design_matrix"]
    assert res["visits"] == expected_output["visits"]
    assert len(res["criteria"]) == len(expected_output["criteria"])
    assert len(res["objectives"]) == len(expected_output["objectives"])
    assert len(res["endpoints"]) == len(expected_output["endpoints"])


def test_study_metadata_listing_with_subpart(api_client):
    subpart_acronym = "TEST"
    # create parent study
    parent_study = TestUtils.create_study(project_number=project_id)
    TestUtils.set_study_standard_version(study_uid=parent_study.uid)

    p_study_number = parent_study.current_metadata.identification_metadata.study_number
    # connect study to parent
    response = api_client.patch(
        f"/studies/{study_uid}",
        json={
            "study_parent_part_uid": parent_study.uid,
            "current_metadata": {
                "identification_metadata": {"study_subpart_acronym": subpart_acronym}
            },
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    response = api_client.patch(
        f"/studies/{parent_study.uid}",
        json={
            "current_metadata": {"study_description": {"study_title": "new title"}},
        },
    )
    assert_response_status_code(response, 200)
    # Lock
    response = api_client.post(
        f"/studies/{parent_study.uid}/locks",
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/listings/studies/study-metadata?project_id={project_id}&study_number={p_study_number}&datetime=2099-12-30",
    )
    assert_response_status_code(response, 400)
    assert (
        response.json()["message"]
        == f"Study {project_id}-{p_study_number} is a parent study, please specify study subpart acronym for specific sub study."
    )

    response = api_client.get(
        "/listings/studies/study-metadata?"
        + f"project_id={project_id}&study_number={p_study_number}&subpart_acronym={subpart_acronym}&datetime=2099-12-30",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res is not None

    expected_output = {
        "api_ver": "TBA",
        "study_id": f"123-{p_study_number}{subpart_acronym}",
        "study_ver": 2.0,
        "specified_dt": "2099-12-30",
        "request_dt": "2024-04-05T09:55:55",
        "title": "new title",
        "reg_id": {
            "ct_gov": "",
            "eudract": "",
            "utn": "",
            "japic": "",
            "ind": "",
            "eutn": "",
            "civ": "",
            "nctn": "",
            "jrct": "",
            "nmpa": "",
            "esn": "",
            "ide": "",
            "eupn": "",
        },
        "study_type": {
            "stype": "",
            "stype_nf": "",
            "trial_type": [],
            "trial_type_nf": "",
            "phase": "",
            "phase_nf": "",
            "extension": "N",
            "extension_nf": "",
            "adaptive": "N",
            "adaptive_nf": "",
            "stop_rule": "some stop rule",
            "stop_rule_nf": "",
            "confirmed_res_min_dur": "",
            "confirmed_res_min_dur_nf": "",
            "post_auth": "Y",
            "post_auth_nf": "",
        },
        "study_attributes": {
            "intv_type": "",
            "intv_type_nf": "",
            "add_on": "N",
            "add_on_nf": "",
            "control_type": "",
            "control_type_nf": "",
            "intv_model": "",
            "intv_model_nf": "",
            "randomised": "Y",
            "randomised_nf": "",
            "strata": "Some stratification factors",
            "strata_nf": "",
            "blinding": "",
            "blinding_nf": "",
            "planned_length": "",
            "planned_length_nf": "",
            "study_intent": [],
            "study_intent_nf": "",
        },
        "study_population": {
            "therapy_area": [],
            "therapy_area_nf": "",
            "indication": [],
            "indication_nf": "",
            "diag_grp": [],
            "diag_grp_nf": "",
            "sex": "",
            "sex_nf": "",
            "rare_dis": "N",
            "rare_dis_nf": "",
            "healthy_subj": "N",
            "healthy_subj_nf": "",
            "min_age": "",
            "min_age_nf": "",
            "max_age": "",
            "max_age_nf": "",
            "stable_dis_min_dur": "",
            "stable_dis_min_dur_nf": "",
            "pediatric": "N",
            "pediatric_nf": "",
            "pediatric_postmarket": "N",
            "pediatric_postmarket_nf": "",
            "pediatric_inv": "Y",
            "pediatric_inv_nf": "",
            "relapse_criteria": "some criteria",
            "relapse_criteria_nf": "",
            "plan_no_subject": None,
            "plan_no_subject_nf": "",
        },
        "arms": [
            {
                "uid": "StudyArm_000001",
                "name": "Arm_Name_1",
                "short_name": "Arm_Short_Name_1",
                "code": "Arm_code_1",
                "no_subject": 100,
                "desc": "desc...",
                "order": 1,
                "rand_grp": "Arm_randomizationGroup",
                "type": "test",
            },
            {
                "uid": "StudyArm_000002",
                "name": "Arm_Name_2",
                "short_name": "Arm_Short_Name_2",
                "code": "Arm_code_2",
                "no_subject": 100,
                "desc": "desc...",
                "order": 2,
                "rand_grp": "Arm_randomizationGroup2",
                "type": "test",
            },
            {
                "uid": "StudyArm_000003",
                "name": "Arm_Name_3",
                "short_name": "Arm_Short_Name_3",
                "code": "Arm_code_3",
                "no_subject": 100,
                "desc": "desc...",
                "order": 3,
                "rand_grp": "Arm_randomizationGroup3",
                "type": "test",
            },
            {
                "uid": "StudyArm_000004",
                "name": "Arm_Name_9",
                "short_name": "Arm_Short_Name_9",
                "code": "Arm_code_9",
                "no_subject": 100,
                "desc": "desc...",
                "order": 4,
                "rand_grp": "Arm_randomizationGroup9",
                "type": "test",
            },
        ],
        "branches": [
            {
                "uid": "StudyBranchArm_000001",
                "name": "Branch_Arm_Name_1",
                "short_name": "Branch_Arm_Short_Name_1",
                "code": "Branch_Arm_code_1",
                "no_subject": 100,
                "desc": "desc...",
                "order": 1,
                "arm_uid": "StudyArm_000002",
                "rand_grp": "Branch_Arm_randomizationGroup",
            }
        ],
        "cohorts": [
            {
                "uid": "StudyCohort_000001",
                "name": "Cohort_Name_1",
                "short_name": "Cohort_Short_Name_1",
                "code": "Cohort_code_1",
                "no_subject": 100,
                "desc": "desc...",
                "arm_uid": ["StudyArm_000001"],
                "branch_uid": [],
            }
        ],
        "epochs": [
            {
                "uid": "StudyEpoch_000001",
                "order": 1,
                "name": "Epoch Subtype",
                "type": "test",
                "subtype": "test",
                "start_rule": "",
                "end_rule": "",
                "description": "",
            },
            {
                "uid": "StudyEpoch_000002",
                "order": 2,
                "name": "Epoch Subtype1",
                "type": "test",
                "subtype": "test",
                "start_rule": "",
                "end_rule": "",
                "description": "",
            },
        ],
        "elements": [
            {
                "uid": "StudyElement_000001",
                "order": 1,
                "name": "Element_Name_1",
                "short_name": "Element_Short_Name_1",
                "type": "uid: Element_code_1 not found",
                "subtype": "test",
                "start_rule": "",
                "end_rule": "",
                "dur": "",
                "desc": "desc...",
            },
            {
                "uid": "StudyElement_000002",
                "order": 2,
                "name": "Element_Name_1",
                "short_name": "Element_Short_Name_1",
                "type": "uid: Element_code_1 not found",
                "subtype": "test",
                "start_rule": "",
                "end_rule": "",
                "dur": "",
                "desc": "desc...",
            },
        ],
        "design_matrix": [
            {
                "arm_uid": "",
                "branch_uid": "StudyBranchArm_000001",
                "epoch_uid": "StudyEpoch_000001",
                "element_uid": "StudyElement_000001",
            },
            {
                "arm_uid": "",
                "branch_uid": "StudyBranchArm_000001",
                "epoch_uid": "StudyEpoch_000002",
                "element_uid": "StudyElement_000001",
            },
            {
                "arm_uid": "StudyArm_000001",
                "branch_uid": "",
                "epoch_uid": "StudyEpoch_000002",
                "element_uid": "StudyElement_000002",
            },
            {
                "arm_uid": "StudyArm_000003",
                "branch_uid": "",
                "epoch_uid": "StudyEpoch_000002",
                "element_uid": "StudyElement_000001",
            },
        ],
        "visits": [
            {
                "epoch_uid": "StudyEpoch_000001",
                "epoch_name": "Epoch Subtype",
                "visit_type": "BASELINE",
                "contact_model": "On Site Visit",
                "visit_no": "100",
                "name": "Visit 1",
                "short_name": "V1",
                "study_day": 1,
                "window_min": -1,
                "window_max": 1,
                "window_unit": "day",
                "desc": "description",
                "epoch_alloc": "",
                "start_rule": "start_rule",
                "end_rule": "end_rule",
            },
            {
                "epoch_uid": "StudyEpoch_000001",
                "epoch_name": "Epoch Subtype",
                "visit_type": "Visit Type2",
                "contact_model": "On Site Visit",
                "visit_no": "200",
                "name": "Visit 2",
                "short_name": "V2",
                "study_day": 11,
                "window_min": -1,
                "window_max": 1,
                "window_unit": "day",
                "desc": "description",
                "epoch_alloc": "",
                "start_rule": "start_rule",
                "end_rule": "end_rule",
            },
            {
                "epoch_uid": "StudyEpoch_000001",
                "epoch_name": "Epoch Subtype",
                "visit_type": "Visit Type2",
                "contact_model": "On Site Visit",
                "visit_no": "300",
                "name": "Visit 3",
                "short_name": "V3",
                "study_day": 13,
                "window_min": -1,
                "window_max": 1,
                "window_unit": "day",
                "desc": "description",
                "epoch_alloc": "",
                "start_rule": "start_rule",
                "end_rule": "end_rule",
            },
            {
                "epoch_uid": "StudyEpoch_000002",
                "epoch_name": "Epoch Subtype1",
                "visit_type": "BASELINE2",
                "contact_model": "On Site Visit",
                "visit_no": "400",
                "name": "Visit 4",
                "short_name": "V4D1",
                "study_day": 31,
                "window_min": -1,
                "window_max": 1,
                "window_unit": "day",
                "desc": "description",
                "epoch_alloc": "",
                "start_rule": "start_rule",
                "end_rule": "end_rule",
            },
            {
                "epoch_uid": "StudyEpoch_000002",
                "epoch_name": "Epoch Subtype1",
                "visit_type": "Visit Type3",
                "contact_model": "On Site Visit",
                "visit_no": "500",
                "name": "Visit 5",
                "short_name": "V5",
                "study_day": 36,
                "window_min": -1,
                "window_max": 1,
                "window_unit": "day",
                "desc": "description",
                "epoch_alloc": "",
                "start_rule": "start_rule",
                "end_rule": "end_rule",
            },
            {
                "epoch_uid": "StudyEpoch_000002",
                "epoch_name": "Epoch Subtype1",
                "visit_type": "Visit Type2",
                "contact_model": "On Site Visit",
                "visit_no": "410",
                "name": "Visit 4",
                "short_name": "V4D32",
                "study_day": 62,
                "window_min": -1,
                "window_max": 1,
                "window_unit": "day",
                "desc": "description",
                "epoch_alloc": "",
                "start_rule": "start_rule",
                "end_rule": "end_rule",
            },
        ],
        "criteria": [
            {"type": "code_submission_value-7516643925", "text": "ct-5124433050"},
            {"type": "code_submission_value-1098504529", "text": "ct-8525557584"},
        ],
        "objectives": [
            {"uid": "StudyObjective_000001", "type": "", "text": "ot-3953094314"},
            {"uid": "StudyObjective_000002", "type": "", "text": "ot-3953094314"},
        ],
        "endpoints": [
            {
                "uid": "StudyEndpoint_000003",
                "type": "",
                "subtype": "",
                "text": "et-4088726782",
                "objective_uid": "StudyObjective_000002",
                "timeframe": "tt-1204109695",
                "endpoint_unit": "",
            },
            {
                "uid": "StudyEndpoint_000001",
                "type": "",
                "subtype": "",
                "text": "et-4088726782",
                "objective_uid": "",
                "timeframe": "tt-1204109695",
                "endpoint_unit": "unit1 and unit2",
            },
        ],
    }

    print("******************")
    print(res)
    print("******************")

    assert res["api_ver"] == expected_output["api_ver"]
    assert res["study_id"] == expected_output["study_id"]
    assert res["study_ver"] == expected_output["study_ver"]
    assert res["specified_dt"] == expected_output["specified_dt"]
    assert res["title"] == expected_output["title"]
    assert res["reg_id"] == expected_output["reg_id"]
    assert res["study_type"] == expected_output["study_type"]
    assert res["study_attributes"] == expected_output["study_attributes"]
    assert res["study_population"] == expected_output["study_population"]
    assert res["arms"] == expected_output["arms"]
    assert res["branches"] == expected_output["branches"]
    assert res["cohorts"] == expected_output["cohorts"]
    assert res["epochs"] == expected_output["epochs"]
    assert res["elements"] == expected_output["elements"]
    assert res["design_matrix"] == expected_output["design_matrix"]
    assert res["visits"] == expected_output["visits"]
    assert len(res["criteria"]) == len(expected_output["criteria"])
    assert len(res["objectives"]) == len(expected_output["objectives"])
    assert len(res["endpoints"]) == len(expected_output["endpoints"])
