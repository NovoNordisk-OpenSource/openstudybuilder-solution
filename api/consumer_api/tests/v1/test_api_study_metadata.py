# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
"""Tests for Consumer API GET /v1/papillons/study-metadata."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameWithConflictFlag,
)
from clinical_mdr_api.models.study_selections.study import (
    HighLevelStudyDesignJsonModel,
    StudyInterventionJsonModel,
    StudyMetadataJsonModel,
    StudyPatchRequestJsonModel,
    StudyPopulationJsonModel,
)
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpochEditInput
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.tests.integration.utils.api import inject_base_data
from clinical_mdr_api.tests.integration.utils.factory_visit import (
    create_study_visit_codelists,
    generate_default_input_data_for_visit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_study_epoch,
    edit_study_epoch,
    input_metadata_in_study,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from common.config import settings
from consumer_api.consumer_api import app
from consumer_api.tests.utils import assert_response_status_code, set_db

BASE_URL = "/v1"

# Test data counts (align with audit trail pattern, no activities)
total_studies: int = 5
total_study_visits_version_1: int = 5

# Top-level keys of StudyMetadataListingModel
STUDY_METADATA_LISTING_TOP_LEVEL_KEYS = [
    "project",
    "study_number",
    "subpart",
    "study",
    "api_version",
    "study_version",
    "fetch_dt",
    "specified_dt",
    "title",
    "reg_id",
    "study_type",
    "study_attributes",
    "study_population",
    "arms",
    "branches",
    "cohorts",
    "epochs",
    "elements",
    "design_matrix",
    "visits",
    "criteria",
    "objectives",
    "endpoints",
]

# StudyArmListingModel keys (for arms in study-metadata response)
STUDY_ARM_LISTING_KEYS = [
    "uid",
    "name",
    "short_name",
    "code",
    "no_subject",
    "desc",
    "order",
    "rand_grp",
    "type",
]

# CT term shape with codelist metadata (CTTermWithCodelistAndConflictFlag-like)
CT_TERM_WITH_CONFLICT_KEYS = [
    "term_uid",
    "sponsor_preferred_name",
    "submission_value",
    "concept_id",
    "codelist_uid",
    "codelist_name",
    "codelist_submission_value",
    "queried_effective_date",
    "date_conflict",
]


def assert_ct_conflict_object(term_value, field_name: str):
    """Assert CT response shape is conflict-aware object."""
    assert isinstance(term_value, dict), f"{field_name} must be an object when present"
    for key in CT_TERM_WITH_CONFLICT_KEYS:
        assert key in term_value, f"{field_name} missing key: {key}"


def _set_sdtm_ct_package_date_to_mismatch(study_uid: str):
    """Force mismatch by setting SDTM CT package date before any test CT term versions."""
    db.cypher_query(
        """
        MATCH (sr:StudyRoot {uid: $study_uid})-[rel:HAS_VERSION {status: "RELEASED"}]->(sv:StudyValue)
        MATCH (sv)-[:HAS_STUDY_STANDARD_VERSION]->(:StudyStandardVersion)-[:HAS_CT_PACKAGE]->(pkg:CTPackage)
        WHERE pkg.uid CONTAINS "SDTM CT"
        SET pkg.effective_date = date("1900-01-01")
        """,
        params={"study_uid": study_uid},
    )


def _get_study_metadata_response(api_client) -> dict[str, Any]:
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    return response.json()


# StudyBranchArmListingModel keys (for branches in study-metadata response)
STUDY_BRANCH_ARM_LISTING_KEYS = [
    "uid",
    "name",
    "short_name",
    "code",
    "no_subject",
    "desc",
    "order",
    "arm_uid",
    "rand_grp",
]

# StudyCohortListingModel keys (for cohorts in study-metadata response)
STUDY_COHORT_LISTING_KEYS = [
    "uid",
    "name",
    "short_name",
    "code",
    "no_subject",
    "desc",
    "arm_uid",
    "branch_uid",
]

# StudyEpochListingModel keys (for epochs in study-metadata response)
STUDY_EPOCH_LISTING_KEYS = [
    "uid",
    "order",
    "name",
    "type",
    "subtype",
    "start_rule",
    "end_rule",
    "description",
    "ae_lag_time",
    "ae_lag_time_unit_uid",
    "ae_lag_time_unit_name",
    "hypo_lag_time",
    "hypo_lag_time_unit_uid",
    "hypo_lag_time_unit_name",
    "ce_lag_time",
    "ce_lag_time_unit_uid",
    "ce_lag_time_unit_name",
]

# StudyVisitListingModel keys (for visits in study-metadata response)
STUDY_VISIT_LISTING_KEYS = [
    "epoch_uid",
    "epoch_name",
    "visit_type",
    "contact_model",
    "visit_no",
    "name",
    "short_name",
    "study_day",
    "window_min",
    "window_max",
    "window_unit",
    "desc",
    "epoch_alloc",
    "start_rule",
    "end_rule",
]

# StudyElementListingModel keys (for elements in study-metadata response)
STUDY_ELEMENT_LISTING_KEYS = [
    "uid",
    "order",
    "name",
    "short_name",
    "type",
    "subtype",
    "start_rule",
    "end_rule",
    "dur",
    "desc",
]

# StudyDesignMatrixListingModel keys (for design_matrix in study-metadata response)
STUDY_DESIGN_MATRIX_LISTING_KEYS = [
    "arm_uid",
    "branch_uid",
    "epoch_uid",
    "element_uid",
    "transition_rule",
]

# StudyEndpointListingModel keys (for endpoints in study-metadata response)
STUDY_ENDPOINT_LISTING_KEYS = [
    "uid",
    "type",
    "subtype",
    "text",
    "objective_uid",
    "timeframe",
    "endpoint_unit",
]

# StudyObjectiveListingModel keys (for objectives in study-metadata response)
STUDY_OBJECTIVE_LISTING_KEYS = [
    "uid",
    "type",
    "text",
]

# StudyCriteriaListingModel keys (for study criteria in study-metadata response)
STUDY_CRITERIA_LISTING_KEYS = [
    "uid",
    "type",
    "text",
]

# RegistryIdentifiersListingModel keys (for reg_id in study-metadata response)
REG_ID_LISTING_KEYS = [
    "ct_gov",
    "eudract",
    "utn",
    "japic",
    "ind",
    "eutn",
    "civ",
    "nctn",
    "jrct",
    "nmpa",
    "esn",
    "ide",
    "eupn",
]

# StudyTypeListingModel keys (for study_type in study-metadata response)
STUDY_TYPE_LISTING_KEYS = [
    "stype",
    "stype_nf",
    "trial_type",
    "trial_type_nf",
    "phase",
    "phase_nf",
    "extension",
    "extension_nf",
    "adaptive",
    "adaptive_nf",
    "stop_rule",
    "stop_rule_nf",
    "confirmed_res_min_dur",
    "confirmed_res_min_dur_nf",
    "post_auth",
    "post_auth_nf",
]

# StudyAttributesListingModel keys (for study_attributes in study-metadata response)
STUDY_ATTRIBUTES_LISTING_KEYS = [
    "intv_type",
    "intv_type_nf",
    "add_on",
    "add_on_nf",
    "control_type",
    "control_type_nf",
    "intv_model",
    "intv_model_nf",
    "randomised",
    "randomised_nf",
    "strata",
    "strata_nf",
    "blinding",
    "blinding_nf",
    "planned_length",
    "planned_length_nf",
    "study_intent",
    "study_intent_nf",
]

# StudyPopulationListingModel keys (for study_population in study-metadata response)
STUDY_POPULATION_LISTING_KEYS = [
    "therapy_area",
    "therapy_area_nf",
    "indication",
    "indication_nf",
    "diag_grp",
    "diag_grp_nf",
    "sex",
    "sex_nf",
    "rare_dis",
    "rare_dis_nf",
    "healthy_subj",
    "healthy_subj_nf",
    "min_age",
    "min_age_nf",
    "max_age",
    "max_age_nf",
    "stable_dis_min_dur",
    "stable_dis_min_dur_nf",
    "pediatric",
    "pediatric_nf",
    "pediatric_postmarket",
    "pediatric_postmarket_nf",
    "pediatric_inv",
    "pediatric_inv_nf",
    "relapse_criteria",
    "relapse_criteria_nf",
    "plan_no_subject",
    "plan_no_subject_nf",
]

# Global variables shared between fixtures and tests
db: Any
study: Any
studies: list[Any]
study_visits: list[Any]
project_id: str
study_number: str
_test_data_dict: dict[str, Any]
null_flavor_study: Any
null_flavor_project_id: str
null_flavor_study_number: str
ae_lag_time_unit_uid: str


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client using the database name set in the `test_data` fixture."""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data(api_client):
    """Initialize test data: same non-activity components as audit trail (limit 5)."""
    db_name = "consumer-api-v1-papillons-study-metadata"
    global db
    db = set_db(db_name)
    global study
    global studies
    global study_visits
    global project_id
    global study_number
    global _test_data_dict
    study, _test_data_dict = inject_base_data()
    create_study_visit_codelists(create_unit_definitions=False, use_test_utils=True)

    studies = [study]  # type: ignore[list-item]
    for _idx in range(1, total_studies):
        rand_str = TestUtils.random_str(4)
        studies.append(
            TestUtils.create_study(acronym=f"ACR-{rand_str}")  # type: ignore[arg-type]
        )

    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=studies[0].uid)
    study_epoch = edit_study_epoch(study_epoch.uid, study_uid=studies[0].uid)

    # Lag time is legacy MMA data. Set AE only, so the test also covers the
    # unset case for hypo and ce. "days" is seeded by inject_base_data; lag
    # time accepts plural units only.
    global ae_lag_time_unit_uid
    ae_lag_time_unit_uid = TestUtils.get_unit_uid_by_name("days")
    study_epoch = StudyEpochService().edit(
        study_uid=studies[0].uid,
        study_epoch_uid=study_epoch.uid,
        study_epoch_input=StudyEpochEditInput(
            study_uid=studies[0].uid,
            change_description="add lag time",
            ae_lag_time=5,
            ae_lag_time_unit_uid=ae_lag_time_unit_uid,
        ),
    )

    visit_to_create = generate_default_input_data_for_visit().copy()
    study_visits = []
    for _idx in range(0, total_study_visits_version_1):
        visit_to_create.update({"time_value": _idx})
        study_visits.append(
            TestUtils.create_study_visit(  # type: ignore[arg-type]
                study_uid=studies[0].uid,
                study_epoch_uid=study_epoch.uid,
                **visit_to_create,
            )
        )

    # Flowchart codelist + EFFICACY term (no activities)
    flowchart_codelist = TestUtils.create_ct_codelist(
        name="Flowchart Group",
        submission_value="FLWCRTGRP",
        sponsor_preferred_name="Flowchart Group",
        nci_preferred_name="Flowchart Group",
        extensible=True,
        approve=True,
    )
    TestUtils.create_ct_term(
        sponsor_preferred_name="EFFICACY",
        submission_value="EFFICACY",
        codelist_uid=flowchart_codelist.codelist_uid,
    )
    objective_level_codelist = TestUtils.create_ct_codelist(
        name=settings.study_objective_level_name,
        sponsor_preferred_name=settings.study_objective_level_name,
        submission_value=settings.study_objective_level_cl_submval,
        extensible=True,
        approve=True,
    )
    objective_level_term = TestUtils.create_ct_term(
        sponsor_preferred_name="Objective Level Conflict",
        submission_value="OBJ-LEVEL-CONFLICT",
        codelist_uid=objective_level_codelist.codelist_uid,
    )
    endpoint_level_codelist = TestUtils.create_ct_codelist(
        name=settings.study_endpoint_level_name,
        sponsor_preferred_name=settings.study_endpoint_level_name,
        submission_value=settings.study_endpoint_level_cl_submval,
        extensible=True,
        approve=True,
    )
    endpoint_level_term = TestUtils.create_ct_term(
        sponsor_preferred_name="Endpoint Level Conflict",
        submission_value="ENDPOINT-LEVEL-CONFLICT",
        codelist_uid=endpoint_level_codelist.codelist_uid,
    )

    yesno_codelist = TestUtils.create_ct_codelist(
        codelist_uid="C66742",
        name="No Yes Response",
        submission_value="NY",
        sponsor_preferred_name="No Yes Response",
        nci_preferred_name="No Yes Response",
        extensible=True,
        approve=True,
    )
    TestUtils.create_ct_term(
        sponsor_preferred_name="Yes",
        submission_value="Y",
        codelist_uid=yesno_codelist.codelist_uid,
        term_uid="C49488",
    )
    TestUtils.create_ct_term(
        sponsor_preferred_name="No",
        submission_value="N",
        codelist_uid=yesno_codelist.codelist_uid,
        term_uid="C49487",
    )

    TestUtils.create_library(name="UCUM", is_editable=True)
    TestUtils.create_study_ct_data_map(codelist_uid=None)
    input_metadata_in_study(studies[0].uid)
    TestUtils.patch_study_core_ct_text_fields_via_api(study_uid=studies[0].uid)

    # Arm type codelist and term for study arms (required by create_study_arm)
    arm_type_codelist = TestUtils.create_ct_codelist(
        name="Arm Type",
        sponsor_preferred_name="arm type",
        submission_value=settings.study_arm_type_cl_submval,
        extensible=True,
        approve=True,
    )
    arm_type_term = TestUtils.create_ct_term(
        sponsor_preferred_name="Investigational Arm",
        sponsor_preferred_name_sentence_case="investigational arm",
        codelist_uid=arm_type_codelist.codelist_uid,
    )
    arm_1 = TestUtils.create_study_arm(
        study_uid=studies[0].uid,
        name="Arm 1",
        short_name="A1",
        code="ARM1",
        description="First arm",
        randomization_group="R1",
        number_of_subjects=50,
        arm_type_uid=arm_type_term.term_uid,
    )
    TestUtils.create_study_arm(
        study_uid=studies[0].uid,
        name="Arm 2",
        short_name="A2",
        code="ARM2",
        description="Second arm",
        randomization_group="R2",
        number_of_subjects=50,
        arm_type_uid=arm_type_term.term_uid,
    )
    # Study branch arms under first arm (before locking)
    branch_1 = TestUtils.create_study_branch_arm(
        study_uid=studies[0].uid,
        name="Branch 1",
        short_name="B1",
        study_arm_uid=arm_1.arm_uid,
        code="BR1",
        randomization_group="RG1",
        number_of_subjects=25,
    )
    branch_2 = TestUtils.create_study_branch_arm(
        study_uid=studies[0].uid,
        name="Branch 2",
        short_name="B2",
        study_arm_uid=arm_1.arm_uid,
        code="BR2",
        randomization_group="RG2",
        number_of_subjects=25,
    )
    # Study cohorts (before locking): one linked to arm, one to branch arms
    TestUtils.create_study_cohort(
        study_uid=studies[0].uid,
        name="Cohort 1",
        short_name="C1",
        code="COH1",
        description="First cohort",
        number_of_subjects=50,
        arm_uids=[arm_1.arm_uid],
    )
    branch_1_uid = branch_1.branch_arm_uid
    branch_2_uid = branch_2.branch_arm_uid
    assert branch_1_uid is not None and branch_2_uid is not None
    TestUtils.create_study_cohort(
        study_uid=studies[0].uid,
        name="Cohort 2",
        short_name="C2",
        code="COH2",
        description="Second cohort",
        number_of_subjects=50,
        branch_arm_uids=[branch_1_uid, branch_2_uid],
    )

    # Element subtype codelist and term for study elements (required by create_study_element)
    element_subtype_codelist = TestUtils.create_ct_codelist(
        name=settings.study_element_subtype_name,
        sponsor_preferred_name=settings.study_element_subtype_name,
        submission_value=settings.study_element_subtype_cl_submval,
        extensible=True,
        approve=True,
    )
    element_subtype_term = TestUtils.create_ct_term(
        sponsor_preferred_name="Element Sub Type 1",
        submission_value="ELEMSTP1",
        codelist_uid=element_subtype_codelist.codelist_uid,
    )
    study_element_1 = TestUtils.create_study_element(
        study_uid=studies[0].uid,
        name="Element 1",
        short_name="E1",
        code="EL1",
        description="First element",
        element_subtype_uid=element_subtype_term.term_uid,
    )
    # Study design cell (epoch + element; branch only — arm with branch arms cannot be assigned)
    element_uid = study_element_1.element_uid
    assert element_uid is not None and branch_1_uid is not None
    TestUtils.create_study_design_cell(
        study_uid=studies[0].uid,
        study_epoch_uid=study_epoch.uid,
        study_element_uid=element_uid,
        study_arm_uid=None,
        study_branch_arm_uid=branch_1_uid,
        transition_rule="Transition to next epoch",
        order=1,
    )

    # CT term for exclusion criteria type (concept_id C25370) — consumer criteria query filters on it
    criteria_type_codelist = TestUtils.create_ct_codelist(
        name="Criteria Type",
        sponsor_preferred_name="Criteria Type",
        submission_value="CRITRTP",
        extensible=True,
        approve=True,
        catalogue_name=settings.sdtm_ct_catalogue_name,
    )
    TestUtils.create_ct_term(
        codelist_uid=criteria_type_codelist.codelist_uid,
        sponsor_preferred_name="Exclusion Criteria",
        sponsor_preferred_name_sentence_case="exclusion criteria",
        nci_preferred_name="Exclusion Criteria",
        definition="Exclusion criteria type for tests",
        submission_value="Exclusion Criteria",
        concept_id="C25370",
        term_uid="C25370",
        catalogue_name=settings.sdtm_ct_catalogue_name,
    )
    exclusion_criteria_template = TestUtils.create_criteria_template(
        name="Papillons exclusion criterion template",
        guidance_text="exclusion criterion guidance",
        study_uid=None,
        type_uid="C25370",
        indication_uids=[],
    )
    TestUtils.create_study_criteria(
        study_uid=studies[0].uid,
        criteria_template_uid=exclusion_criteria_template.uid,
    )
    TestUtils.create_study_objective_and_endpoint_with_ct_levels(
        study_uid=studies[0].uid,
        objective_level_uid=objective_level_term.term_uid,
        endpoint_level_uid=endpoint_level_term.term_uid,
    )
    study_service = StudyService()
    study_service.lock(
        uid=studies[0].uid,
        change_description="locking it",
        reason_for_lock_term_uid=_test_data_dict["reason_for_lock_terms"][0].term_uid,
    )
    study_service.unlock(
        uid=studies[0].uid,
        reason_for_unlock_term_uid=_test_data_dict["reason_for_unlock_terms"][
            0
        ].term_uid,
    )

    # Extra visit for latest version (no activity)
    visit_to_create.update({"time_value": total_study_visits_version_1})
    study_visits.append(
        TestUtils.create_study_visit(  # type: ignore[arg-type]
            study_uid=studies[0].uid,
            study_epoch_uid=study_epoch.uid,
            **visit_to_create,
        )
    )

    study = studies[0]
    project_id = study.current_metadata.identification_metadata.project_number
    study_number = study.current_metadata.identification_metadata.study_number

    global null_flavor_study
    global null_flavor_project_id
    global null_flavor_study_number
    null_flavor_study = TestUtils.create_study(
        acronym=f"MCP-NF-{TestUtils.random_str(4)}"
    )
    TestUtils.set_study_title(
        null_flavor_study.uid, study_title="MCP null flavor metadata study"
    )
    null_flavor_project_id = (
        null_flavor_study.current_metadata.identification_metadata.project_number
    )
    null_flavor_study_number = (
        null_flavor_study.current_metadata.identification_metadata.study_number
    )


def test_get_study_metadata_returns_200_and_shape(api_client):
    """GET /v1/papillons/study-metadata returns 200 and JSON with StudyMetadataListingModel shape."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res is not None
    for key in STUDY_METADATA_LISTING_TOP_LEVEL_KEYS:
        assert key in res, f"Missing top-level key: {key}"
    assert res["api_version"] == "v1"
    assert res["project"] == project_id
    assert res["study_number"] == study_number
    assert res["study"] == f"{project_id}-{study_number}{res.get('subpart') or ''}"
    assert isinstance(res["study_version"], str) and len(res["study_version"]) > 0
    assert res["specified_dt"] == "2099-12-30T00:00:00Z"
    assert isinstance(res["fetch_dt"], str) and len(res["fetch_dt"]) > 0


def test_get_study_metadata_arms_shape_and_content(api_client):
    """GET /v1/papillons/study-metadata returns arms as list with StudyArmListingModel shape."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert "arms" in res
    arms = res["arms"]
    assert isinstance(arms, list), "arms must be a list"
    assert len(arms) >= 2, "expected at least 2 study arms from test data"
    for arm in arms:
        for key in STUDY_ARM_LISTING_KEYS:
            assert key in arm, f"Arm missing key: {key}"
    # Test data creates "Arm 1" and "Arm 2"
    arm_names = {a["name"] for a in arms}
    assert "Arm 1" in arm_names
    assert "Arm 2" in arm_names
    # Arm type is a conflict-aware object (CTTermWithCodelistAndConflictFlag-like)
    typed_arms = [a for a in arms if a.get("type") is not None]
    assert len(typed_arms) >= 1, "at least one arm should have type object set"
    for arm in typed_arms:
        assert isinstance(arm["type"], dict), "arm.type must be an object when present"
        for key in CT_TERM_WITH_CONFLICT_KEYS:
            assert key in arm["type"], f"arm.type missing key: {key}"
        assert arm["type"]["term_uid"], "arm.type.term_uid must be populated"
        assert (
            arm["type"]["sponsor_preferred_name"] == "Investigational Arm"
        ), f"unexpected arm.type.sponsor_preferred_name: {arm['type']!r}"
        assert (
            arm["type"]["codelist_submission_value"]
            == settings.study_arm_type_cl_submval
        )
        assert arm["type"]["submission_value"] is not None
        # if no exact date match exists, latest should be used and conflict flagged
        if arm["type"]["date_conflict"] is True:
            assert (
                arm["type"]["queried_effective_date"] is None
            ), "queried_effective_date should be null when fallback/latest is used"


def test_get_study_metadata_arms_date_conflict_true_on_ct_package_mismatch(api_client):
    """GET /v1/papillons/study-metadata sets arm.type.date_conflict=true when CT package date is before term versions."""
    _set_sdtm_ct_package_date_to_mismatch(studies[0].uid)
    arms = _get_study_metadata_response(api_client)["arms"]
    typed_arms = [a for a in arms if a.get("type") is not None]
    assert typed_arms, "expected at least one arm with CT-backed type object"
    assert any(
        arm["type"]["date_conflict"] is True for arm in typed_arms
    ), "expected date_conflict=True when ct_package date predates any term version"


def test_get_study_metadata_epochs_date_conflict_true_on_ct_package_mismatch(
    api_client,
):
    _set_sdtm_ct_package_date_to_mismatch(studies[0].uid)
    epochs = _get_study_metadata_response(api_client)["epochs"]
    epoch_terms = [
        t
        for epoch in epochs
        for t in (epoch.get("type"), epoch.get("subtype"))
        if t is not None
    ]
    assert epoch_terms, "expected at least one CT-backed epoch term"
    assert any(
        term["date_conflict"] is True for term in epoch_terms
    ), "expected date_conflict=True in epochs when CT package date mismatches"


def test_get_study_metadata_visits_date_conflict_true_on_ct_package_mismatch(
    api_client,
):
    _set_sdtm_ct_package_date_to_mismatch(studies[0].uid)
    visits = _get_study_metadata_response(api_client)["visits"]
    visit_terms = [
        t
        for visit in visits
        for t in (
            visit.get("visit_type"),
            visit.get("contact_model"),
            visit.get("epoch_alloc"),
        )
        if t is not None
    ]
    assert visit_terms, "expected at least one CT-backed visit term"
    assert any(
        term["date_conflict"] is True for term in visit_terms
    ), "expected date_conflict=True in visits when CT package date mismatches"


def test_get_study_metadata_elements_date_conflict_true_on_ct_package_mismatch(
    api_client,
):
    _set_sdtm_ct_package_date_to_mismatch(studies[0].uid)
    elements = _get_study_metadata_response(api_client)["elements"]
    element_terms = [
        t
        for element in elements
        for t in (element.get("type"), element.get("subtype"))
        if t is not None
    ]
    assert element_terms, "expected at least one CT-backed element term"
    assert any(
        term["date_conflict"] is True for term in element_terms
    ), "expected date_conflict=True in elements when CT package date mismatches"


def test_get_study_metadata_endpoints_date_conflict_true_on_ct_package_mismatch(
    api_client,
):
    _set_sdtm_ct_package_date_to_mismatch(studies[0].uid)
    endpoints = _get_study_metadata_response(api_client)["endpoints"]
    endpoint_terms = [
        t
        for endpoint in endpoints
        for t in (endpoint.get("type"), endpoint.get("subtype"))
        if t is not None
    ]
    assert endpoint_terms, "expected at least one CT-backed endpoint term"
    assert any(
        term["date_conflict"] is True for term in endpoint_terms
    ), "expected date_conflict=True in endpoints when CT package date mismatches"


def test_get_study_metadata_objectives_date_conflict_true_on_ct_package_mismatch(
    api_client,
):
    _set_sdtm_ct_package_date_to_mismatch(studies[0].uid)
    objectives = _get_study_metadata_response(api_client)["objectives"]
    objective_terms = [obj["type"] for obj in objectives if obj.get("type") is not None]
    assert objective_terms, "expected at least one CT-backed objective term"
    assert any(
        term["date_conflict"] is True for term in objective_terms
    ), "expected date_conflict=True in objectives when CT package date mismatches"


def test_get_study_metadata_criteria_date_conflict_true_on_ct_package_mismatch(
    api_client,
):
    _set_sdtm_ct_package_date_to_mismatch(studies[0].uid)
    criteria = _get_study_metadata_response(api_client)["criteria"]
    criteria_terms = [
        criterion["type"] for criterion in criteria if criterion.get("type")
    ]
    assert criteria_terms, "expected at least one CT-backed criteria term"
    assert any(
        term["date_conflict"] is True for term in criteria_terms
    ), "expected date_conflict=True in criteria when CT package date mismatches"


def test_get_study_metadata_study_type_date_conflict_true_on_ct_package_mismatch(
    api_client,
):
    _set_sdtm_ct_package_date_to_mismatch(studies[0].uid)
    study_type = _get_study_metadata_response(api_client)["study_type"]
    assert study_type is not None
    assert study_type.get("stype") is not None, "expected stype CT object"
    assert (
        study_type["stype"]["date_conflict"] is True
    ), "expected date_conflict=True for study_type.stype"


def test_get_study_metadata_study_attributes_date_conflict_true_on_ct_package_mismatch(
    api_client,
):
    _set_sdtm_ct_package_date_to_mismatch(studies[0].uid)
    study_attributes = _get_study_metadata_response(api_client)["study_attributes"]
    assert study_attributes is not None
    assert study_attributes.get("intv_type") is not None, "expected intv_type CT object"
    assert (
        study_attributes["intv_type"]["date_conflict"] is True
    ), "expected date_conflict=True for study_attributes.intv_type"


def test_get_study_metadata_study_population_date_conflict_true_on_ct_package_mismatch(
    api_client,
):
    _set_sdtm_ct_package_date_to_mismatch(studies[0].uid)
    study_population = _get_study_metadata_response(api_client)["study_population"]
    assert study_population is not None
    assert study_population.get("sex") is not None, "expected sex CT object"
    assert (
        study_population["sex"]["date_conflict"] is True
    ), "expected date_conflict=True for study_population.sex"


def test_get_study_metadata_branches_shape_and_content(api_client):
    """GET /v1/papillons/study-metadata returns branches as list with StudyBranchArmListingModel shape."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert "branches" in res
    branches = res["branches"]
    assert isinstance(branches, list), "branches must be a list"
    assert len(branches) >= 2, "expected at least 2 study branch arms from test data"
    for branch in branches:
        for key in STUDY_BRANCH_ARM_LISTING_KEYS:
            assert key in branch, f"Branch missing key: {key}"
    # Test data creates "Branch 1" and "Branch 2"
    branch_names = {b["name"] for b in branches}
    assert "Branch 1" in branch_names
    assert "Branch 2" in branch_names
    # Each branch should have arm_uid set (parent arm)
    for branch in branches:
        assert branch.get("arm_uid"), "each branch should have arm_uid set"


def test_get_study_metadata_cohorts_shape_and_content(api_client):
    """GET /v1/papillons/study-metadata returns cohorts as list with StudyCohortListingModel shape."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert "cohorts" in res
    cohorts = res["cohorts"]
    assert isinstance(cohorts, list), "cohorts must be a list"
    assert len(cohorts) >= 2, "expected at least 2 study cohorts from test data"
    for cohort in cohorts:
        for key in STUDY_COHORT_LISTING_KEYS:
            assert key in cohort, f"Cohort missing key: {key}"
        assert isinstance(cohort["arm_uid"], list), "arm_uid must be a list"
        assert isinstance(cohort["branch_uid"], list), "branch_uid must be a list"
    # Test data creates "Cohort 1" and "Cohort 2"
    cohort_names = {c["name"] for c in cohorts}
    assert "Cohort 1" in cohort_names
    assert "Cohort 2" in cohort_names
    # Cohort 1 is linked to arm; Cohort 2 to branch arms
    c1 = next(c for c in cohorts if c["name"] == "Cohort 1")
    c2 = next(c for c in cohorts if c["name"] == "Cohort 2")
    assert len(c1["arm_uid"]) >= 1, "Cohort 1 should have at least one arm_uid"
    assert len(c2["branch_uid"]) >= 1, "Cohort 2 should have at least one branch_uid"


def test_get_study_metadata_epochs_shape_and_content(api_client):
    """GET /v1/papillons/study-metadata returns epochs as list with StudyEpochListingModel shape."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert "epochs" in res
    epochs = res["epochs"]
    assert isinstance(epochs, list), "epochs must be a list"
    assert len(epochs) >= 1, "expected at least 1 study epoch from test data"
    for epoch in epochs:
        for key in STUDY_EPOCH_LISTING_KEYS:
            assert key in epoch, f"Epoch missing key: {key}"
        if epoch.get("type") is not None:
            assert_ct_conflict_object(epoch["type"], "epochs[].type")
        if epoch.get("subtype") is not None:
            assert_ct_conflict_object(epoch["subtype"], "epochs[].subtype")
    # Test data creates one epoch via create_study_epoch; it should have uid and order
    assert all(e.get("uid") for e in epochs), "each epoch should have uid"
    # At least one epoch should have non-empty name or subtype (from EpochSubType)
    has_name_or_subtype = any(e.get("name") or e.get("subtype") for e in epochs)
    assert has_name_or_subtype, "at least one epoch should have name or subtype set"


def test_get_study_metadata_epochs_lag_time(api_client):
    """Lag time only carries data migrated from MMA, so unset slots stay null."""
    res = _get_study_metadata_response(api_client)
    epochs = res["epochs"]
    lag_epochs = [e for e in epochs if e["ae_lag_time"] is not None]
    assert len(lag_epochs) == 1, "test data sets AE lag time on exactly one epoch"
    epoch = lag_epochs[0]

    assert epoch["ae_lag_time"] == 5
    assert epoch["ae_lag_time_unit_uid"] == ae_lag_time_unit_uid
    assert epoch["ae_lag_time_unit_name"] == "days"

    # hypo and ce were never set, so value and unit must both come back null
    assert epoch["hypo_lag_time"] is None
    assert epoch["hypo_lag_time_unit_uid"] is None
    assert epoch["hypo_lag_time_unit_name"] is None
    assert epoch["ce_lag_time"] is None
    assert epoch["ce_lag_time_unit_uid"] is None
    assert epoch["ce_lag_time_unit_name"] is None


def test_get_study_metadata_visits_shape_and_content(api_client):
    """GET /v1/papillons/study-metadata returns visits as list with StudyVisitListingModel shape."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert "visits" in res
    visits = res["visits"]
    assert isinstance(visits, list), "visits must be a list"
    assert len(visits) >= 1, "expected at least 1 study visit from test data"
    for visit in visits:
        for key in STUDY_VISIT_LISTING_KEYS:
            assert key in visit, f"Visit missing key: {key}"
        if visit.get("visit_type") is not None:
            assert_ct_conflict_object(visit["visit_type"], "visits[].visit_type")
        if visit.get("contact_model") is not None:
            assert_ct_conflict_object(visit["contact_model"], "visits[].contact_model")
        if visit.get("epoch_alloc") is not None:
            assert_ct_conflict_object(visit["epoch_alloc"], "visits[].epoch_alloc")
    # Test data creates multiple visits (total_study_visits_version_1 + 1); each should have epoch_uid and visit_no
    assert all(v.get("epoch_uid") for v in visits), "each visit should have epoch_uid"
    assert all(
        v.get("visit_no") is not None and str(v.get("visit_no")) != "" for v in visits
    ), "each visit should have visit_no"
    # At least one visit should have non-empty name or short_name
    has_name = any(v.get("name") or v.get("short_name") for v in visits)
    assert has_name, "at least one visit should have name or short_name set"


def test_get_study_metadata_elements_shape_and_content(api_client):
    """GET study-metadata returns elements list with StudyElementListingModel shape and content."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert "elements" in res
    elements = res["elements"]
    assert isinstance(elements, list), "elements must be a list"
    assert len(elements) >= 1, "expected at least 1 study element from test data"
    for elem in elements:
        for key in STUDY_ELEMENT_LISTING_KEYS:
            assert key in elem, f"Element missing key: {key}"
        if elem.get("type") is not None:
            assert_ct_conflict_object(elem["type"], "elements[].type")
        if elem.get("subtype") is not None:
            assert_ct_conflict_object(elem["subtype"], "elements[].subtype")
    # At least one element should have non-empty name or type
    has_content = any(
        elem.get("name") or elem.get("type") or elem.get("subtype") for elem in elements
    )
    assert has_content, "at least one element should have name, type, or subtype set"


def test_get_study_metadata_design_matrix_shape_and_content(api_client):
    """GET study-metadata returns design_matrix list with transition_rule and shape."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert "design_matrix" in res
    design_matrix = res["design_matrix"]
    assert isinstance(design_matrix, list), "design_matrix must be a list"
    assert len(design_matrix) >= 1, "expected at least 1 design cell from test data"
    for cell in design_matrix:
        for key in STUDY_DESIGN_MATRIX_LISTING_KEYS:
            assert key in cell, f"Design cell missing key: {key}"
    # transition_rule is included; at least one cell should have non-empty transition_rule or epoch_uid
    has_content = any(
        cell.get("transition_rule") or cell.get("epoch_uid") or cell.get("element_uid")
        for cell in design_matrix
    )
    assert (
        has_content
    ), "at least one design cell should have transition_rule, epoch_uid, or element_uid set"


def test_get_study_metadata_endpoints_shape_and_content(api_client):
    """GET study-metadata returns endpoints list with StudyEndpointListingModel shape."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert "endpoints" in res
    endpoints = res["endpoints"]
    assert isinstance(endpoints, list), "endpoints must be a list"
    for ep in endpoints:
        for key in STUDY_ENDPOINT_LISTING_KEYS:
            assert key in ep, f"Endpoint missing key: {key}"
        if ep.get("type") is not None:
            assert_ct_conflict_object(ep["type"], "endpoints[].type")
        if ep.get("subtype") is not None:
            assert_ct_conflict_object(ep["subtype"], "endpoints[].subtype")
    if len(endpoints) >= 1:
        has_content = any(
            ep.get("text") or ep.get("type") or ep.get("objective_uid")
            for ep in endpoints
        )
        assert (
            has_content
        ), "at least one endpoint should have text, type, or objective_uid set"


def test_get_study_metadata_objectives_shape_and_content(api_client):
    """GET study-metadata returns objectives list with StudyObjectiveListingModel shape."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert "objectives" in res
    objectives = res["objectives"]
    assert isinstance(objectives, list), "objectives must be a list"
    for obj in objectives:
        for key in STUDY_OBJECTIVE_LISTING_KEYS:
            assert key in obj, f"Objective missing key: {key}"
        if obj.get("type") is not None:
            assert_ct_conflict_object(obj["type"], "objectives[].type")
    if len(objectives) >= 1:
        has_content = any(obj.get("text") or obj.get("type") for obj in objectives)
        assert has_content, "at least one objective should have text or type set"


def test_get_study_metadata_criteria_shape_and_content(api_client):
    """GET study-metadata returns criteria list with StudyCriteriaListingModel shape."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert "criteria" in res
    criteria = res["criteria"]
    assert isinstance(criteria, list), "criteria must be a list"
    for c in criteria:
        for key in STUDY_CRITERIA_LISTING_KEYS:
            assert key in c, f"Criteria missing key: {key}"
        if c.get("type") is not None:
            assert_ct_conflict_object(c["type"], "criteria[].type")
    if len(criteria) >= 1:
        has_content = any(c.get("text") or c.get("type") for c in criteria)
        assert has_content, "at least one criterion should have text or type set"


def test_get_study_metadata_criteria_unique_uids(api_client):
    """Each study criterion must appear at most once (no duplicate rows per StudyCriteria)."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    criteria = response.json()["criteria"]
    uids = [c["uid"] for c in criteria if c.get("uid")]
    assert len(uids) == len(
        set(uids)
    ), f"criteria uids must be unique, got {len(uids)} entries / {len(set(uids))} distinct uids"


def test_get_study_metadata_exclusion_criteria_single_entry(api_client):
    """Exclusion criteria (C25370 / template) must appear exactly once in the criteria list."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    criteria = response.json()["criteria"]
    # Match the fixture template name (instance text / name_plain), not CT display string
    exclusion = [
        c for c in criteria if c.get("text") and "Papillons exclusion" in c["text"]
    ]
    assert len(exclusion) == 1, (
        "expected exactly one exclusion criterion from test data, "
        f"got {len(exclusion)}; criteria={criteria!r}"
    )
    assert exclusion[0].get("uid"), "criterion should have uid"
    assert exclusion[0].get("type"), "criterion should have type from CT attributes"
    criterion_type = exclusion[0]["type"]
    for key in CT_TERM_WITH_CONFLICT_KEYS:
        assert key in criterion_type, f"criterion.type missing key: {key}"
    assert criterion_type["concept_id"] == "C25370"
    assert criterion_type["submission_value"] == "Exclusion Criteria"
    assert criterion_type["codelist_submission_value"] == "CRITRTP"
    type_name = criterion_type["sponsor_preferred_name"] or ""
    assert (
        "exclusion" in type_name.lower()
    ), f"type should reflect exclusion CT term, got {criterion_type!r}"


def test_get_study_metadata_reg_id_shape_and_content(api_client):
    """GET study-metadata returns reg_id with RegistryIdentifiersListingModel shape."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert "reg_id" in res
    reg_id = res["reg_id"]
    assert reg_id is not None, "reg_id must be a dict (not null)"
    assert isinstance(reg_id, dict), "reg_id must be a dict"
    for key in REG_ID_LISTING_KEYS:
        assert key in reg_id, f"reg_id missing key: {key}"
        assert isinstance(reg_id[key], str), f"reg_id[{key!r}] must be a string"


def test_get_study_metadata_study_type_shape_and_content(api_client):
    """GET study-metadata returns study_type with StudyTypeListingModel shape."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert "study_type" in res
    study_type = res["study_type"]
    # study_type can be null if no high-level design; when present it must match shape
    if study_type is not None:
        assert isinstance(study_type, dict), "study_type must be a dict when present"
        for key in STUDY_TYPE_LISTING_KEYS:
            assert key in study_type, f"study_type missing key: {key}"
        for ct_key in (
            "stype",
            "stype_nf",
            "trial_type_nf",
            "phase",
            "phase_nf",
            "extension_nf",
            "adaptive_nf",
            "stop_rule_nf",
            "confirmed_res_min_dur_nf",
            "post_auth_nf",
        ):
            if study_type.get(ct_key) is not None:
                assert_ct_conflict_object(study_type[ct_key], f"study_type.{ct_key}")
        assert isinstance(
            study_type["trial_type"], list
        ), "study_type.trial_type must be a list"
        for item in study_type["trial_type"]:
            assert isinstance(item, dict), "trial_type items must be dicts"
            assert_ct_conflict_object(item, "study_type.trial_type[]")


def test_get_study_metadata_study_attributes_shape_and_content(api_client):
    """GET study-metadata returns study_attributes with StudyAttributesListingModel shape."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert "study_attributes" in res
    study_attributes = res["study_attributes"]
    if study_attributes is not None:
        assert isinstance(
            study_attributes, dict
        ), "study_attributes must be a dict when present"
        for key in STUDY_ATTRIBUTES_LISTING_KEYS:
            assert key in study_attributes, f"study_attributes missing key: {key}"
        for ct_key in (
            "intv_type",
            "intv_type_nf",
            "add_on_nf",
            "control_type",
            "control_type_nf",
            "intv_model",
            "intv_model_nf",
            "randomised_nf",
            "strata_nf",
            "blinding",
            "blinding_nf",
            "planned_length_nf",
            "study_intent_nf",
        ):
            if study_attributes.get(ct_key) is not None:
                assert_ct_conflict_object(
                    study_attributes[ct_key], f"study_attributes.{ct_key}"
                )
        assert isinstance(
            study_attributes["study_intent"], list
        ), "study_attributes.study_intent must be a list"
        for item in study_attributes["study_intent"]:
            assert isinstance(item, dict), "study_intent items must be dicts"
            assert_ct_conflict_object(item, "study_attributes.study_intent[]")


def test_get_study_metadata_study_population_shape_and_content(api_client):
    """GET study-metadata returns study_population with StudyPopulationListingModel shape."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert "study_population" in res
    study_population = res["study_population"]
    if study_population is not None:
        assert isinstance(
            study_population, dict
        ), "study_population must be a dict when present"
        for key in STUDY_POPULATION_LISTING_KEYS:
            assert key in study_population, f"study_population missing key: {key}"
        for ct_key in (
            "therapy_area_nf",
            "indication_nf",
            "diag_grp_nf",
            "sex",
            "sex_nf",
            "rare_dis_nf",
            "healthy_subj_nf",
            "min_age_nf",
            "max_age_nf",
            "stable_dis_min_dur_nf",
            "pediatric_nf",
            "pediatric_postmarket_nf",
            "pediatric_inv_nf",
            "relapse_criteria_nf",
            "plan_no_subject_nf",
        ):
            if study_population.get(ct_key) is not None:
                assert_ct_conflict_object(
                    study_population[ct_key], f"study_population.{ct_key}"
                )
        for list_key in ("therapy_area", "indication", "diag_grp"):
            assert isinstance(
                study_population[list_key], list
            ), f"study_population.{list_key} must be a list"
            for item in study_population[list_key]:
                assert isinstance(item, dict), f"{list_key} items must be dicts"
                assert_ct_conflict_object(item, f"study_population.{list_key}[]")
        plan_no_subject = study_population.get("plan_no_subject")
        assert plan_no_subject is None or isinstance(
            plan_no_subject, int
        ), "plan_no_subject must be int or null"


def test_get_study_metadata_400_when_both_version_and_datetime(api_client):
    """GET /v1/papillons/study-metadata returns 400 when both study_value_version and datetime are provided."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "study_value_version": "1",
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 400)


def test_get_study_metadata_200_latest_when_neither_version_nor_datetime(
    api_client,
):
    """GET /v1/papillons/study-metadata without version/datetime uses latest released (same as far-future datetime)."""
    latest_via_dt = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(latest_via_dt, 200)
    implicit_latest = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": project_id,
            "study_number": study_number,
        },
    )
    assert_response_status_code(implicit_latest, 200)
    assert (
        implicit_latest.json()["study_version"] == latest_via_dt.json()["study_version"]
    ), "omitting version/datetime should match latest released (2099 datetime)"


def test_get_study_metadata_404_unknown_study(api_client):
    """GET /v1/papillons/study-metadata returns 404 for unknown project_id/study_number."""
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": "UNKNOWN_PROJECT",
            "study_number": "99999999",
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 404)


def _null_flavor_term(term_uid: str) -> SimpleCTTermNameWithConflictFlag:
    return SimpleCTTermNameWithConflictFlag(term_uid=term_uid)


def _assert_null_flavor(
    section: dict[str, Any] | None,
    field_key: str,
    *,
    null_term_uid: str,
    null_name: str,
) -> None:
    assert section is not None
    nf = section.get(field_key)
    assert nf is not None, f"expected {field_key} when null flavor is set"
    assert_ct_conflict_object(nf, field_key)
    assert nf["term_uid"] == null_term_uid
    assert nf["sponsor_preferred_name"] == null_name


def _patch_study_null_flavor(
    study_uid: str,
    *,
    high_level_study_design: HighLevelStudyDesignJsonModel | None = None,
    study_intervention: StudyInterventionJsonModel | None = None,
    study_population: StudyPopulationJsonModel | None = None,
) -> None:
    study_service = StudyService()
    study = study_service.get_by_uid(uid=study_uid)
    if study.current_metadata.version_metadata.study_status != StudyStatus.DRAFT.value:
        study_service.unlock(
            uid=study_uid,
            reason_for_unlock_term_uid=_test_data_dict["reason_for_unlock_terms"][
                0
            ].term_uid,
        )
    study_service.patch(
        uid=study_uid,
        dry=False,
        study_patch_request=StudyPatchRequestJsonModel(
            current_metadata=StudyMetadataJsonModel(
                high_level_study_design=high_level_study_design,
                study_intervention=study_intervention,
                study_population=study_population,
            )
        ),
    )
    study_service.lock(
        uid=study_uid,
        change_description="lock after null flavor patch",
        reason_for_lock_term_uid=_test_data_dict["reason_for_lock_terms"][0].term_uid,
    )


def _get_null_flavor_study_metadata_response(api_client) -> dict[str, Any]:
    response = api_client.get(
        f"{BASE_URL}/papillons/study-metadata",
        params={
            "project_id": null_flavor_project_id,
            "study_number": null_flavor_study_number,
            "datetime": "2099-12-30T00:00:00Z",
        },
    )
    assert_response_status_code(response, 200)
    return response.json()


def test_get_study_metadata_null_flavors_returned_for_study_type_fields(api_client):
    """GET study-metadata returns *_nf for study_type text/boolean/array/time fields."""
    null_term_uid, null_name = TestUtils.get_null_value_code()
    nf = _null_flavor_term(null_term_uid)
    _patch_study_null_flavor(
        null_flavor_study.uid,
        high_level_study_design=HighLevelStudyDesignJsonModel(
            study_type_code=None,
            study_type_null_value_code=nf,
            trial_type_codes=None,
            trial_type_null_value_code=nf,
            trial_phase_code=None,
            trial_phase_null_value_code=nf,
            is_extension_trial=None,
            is_extension_trial_null_value_code=nf,
            is_adaptive_design=None,
            is_adaptive_design_null_value_code=nf,
            study_stop_rules=None,
            study_stop_rules_null_value_code=nf,
            confirmed_response_minimum_duration=None,
            confirmed_response_minimum_duration_null_value_code=nf,
            post_auth_indicator=None,
            post_auth_indicator_null_value_code=nf,
        ),
    )
    res = _get_null_flavor_study_metadata_response(api_client)

    study_type = res["study_type"]
    assert study_type.get("stype") is None
    assert study_type.get("extension") in (None, "")
    assert study_type.get("confirmed_res_min_dur") in (None, "")
    for key in (
        "stype_nf",
        "extension_nf",
        "trial_type_nf",
        "phase_nf",
        "stop_rule_nf",
        "adaptive_nf",
        "confirmed_res_min_dur_nf",
        "post_auth_nf",
    ):
        _assert_null_flavor(
            study_type, key, null_term_uid=null_term_uid, null_name=null_name
        )


def test_get_study_metadata_null_flavors_returned_for_study_attributes_fields(
    api_client,
):
    """GET study-metadata returns *_nf for study_attributes text/boolean/array/time fields."""
    null_term_uid, null_name = TestUtils.get_null_value_code()
    nf = _null_flavor_term(null_term_uid)
    _patch_study_null_flavor(
        null_flavor_study.uid,
        study_intervention=StudyInterventionJsonModel(
            intervention_type_code=None,
            intervention_type_null_value_code=nf,
            planned_study_length=None,
            planned_study_length_null_value_code=nf,
            add_on_to_existing_treatments=None,
            add_on_to_existing_treatments_null_value_code=nf,
            control_type_code=None,
            control_type_null_value_code=nf,
            intervention_model_code=None,
            intervention_model_null_value_code=nf,
            is_trial_randomised=None,
            is_trial_randomised_null_value_code=nf,
            stratification_factor=None,
            stratification_factor_null_value_code=nf,
            trial_blinding_schema_code=None,
            trial_blinding_schema_null_value_code=nf,
            trial_intent_types_codes=None,
            trial_intent_types_null_value_code=nf,
        ),
    )
    res = _get_null_flavor_study_metadata_response(api_client)

    study_attributes = res["study_attributes"]
    assert study_attributes.get("intv_type") is None
    assert study_attributes.get("planned_length") in (None, "")
    for key in (
        "intv_type_nf",
        "planned_length_nf",
        "add_on_nf",
        "control_type_nf",
        "intv_model_nf",
        "randomised_nf",
        "strata_nf",
        "blinding_nf",
        "study_intent_nf",
    ):
        _assert_null_flavor(
            study_attributes, key, null_term_uid=null_term_uid, null_name=null_name
        )


def test_get_study_metadata_null_flavors_returned_for_study_population_fields(
    api_client,
):
    """GET study-metadata returns *_nf for study_population text/boolean/array/time/int fields."""
    null_term_uid, null_name = TestUtils.get_null_value_code()
    nf = _null_flavor_term(null_term_uid)
    _patch_study_null_flavor(
        null_flavor_study.uid,
        study_population=StudyPopulationJsonModel(
            therapeutic_area_codes=None,
            therapeutic_area_null_value_code=nf,
            disease_condition_or_indication_codes=None,
            disease_condition_or_indication_null_value_code=nf,
            diagnosis_group_codes=None,
            diagnosis_group_null_value_code=nf,
            sex_of_participants_code=None,
            sex_of_participants_null_value_code=nf,
            rare_disease_indicator=None,
            rare_disease_indicator_null_value_code=nf,
            healthy_subject_indicator=None,
            healthy_subject_indicator_null_value_code=nf,
            planned_minimum_age_of_subjects=None,
            planned_minimum_age_of_subjects_null_value_code=nf,
            planned_maximum_age_of_subjects=None,
            planned_maximum_age_of_subjects_null_value_code=nf,
            stable_disease_minimum_duration=None,
            stable_disease_minimum_duration_null_value_code=nf,
            pediatric_study_indicator=None,
            pediatric_study_indicator_null_value_code=nf,
            pediatric_postmarket_study_indicator=None,
            pediatric_postmarket_study_indicator_null_value_code=nf,
            pediatric_investigation_plan_indicator=None,
            pediatric_investigation_plan_indicator_null_value_code=nf,
            relapse_criteria=None,
            relapse_criteria_null_value_code=nf,
            number_of_expected_subjects=None,
            number_of_expected_subjects_null_value_code=nf,
        ),
    )
    res = _get_null_flavor_study_metadata_response(api_client)

    study_population = res["study_population"]
    assert study_population.get("min_age") in (None, "")
    assert study_population.get("plan_no_subject") is None
    for key in (
        "therapy_area_nf",
        "min_age_nf",
        "plan_no_subject_nf",
        "indication_nf",
        "diag_grp_nf",
        "sex_nf",
        "rare_dis_nf",
        "healthy_subj_nf",
        "max_age_nf",
        "stable_dis_min_dur_nf",
        "pediatric_nf",
        "pediatric_postmarket_nf",
        "pediatric_inv_nf",
        "relapse_criteria_nf",
    ):
        _assert_null_flavor(
            study_population, key, null_term_uid=null_term_uid, null_name=null_name
        )


def test_get_study_metadata_null_flavors_date_conflict_true_on_ct_package_mismatch(
    api_client,
):
    """A null-flavor term is itself CT-backed, so it must also flag date_conflict on CT package mismatch."""
    _set_sdtm_ct_package_date_to_mismatch(null_flavor_study.uid)
    study_type = _get_null_flavor_study_metadata_response(api_client)["study_type"]
    assert study_type is not None
    assert study_type.get("stype_nf") is not None, "expected stype_nf CT object"
    assert (
        study_type["stype_nf"]["date_conflict"] is True
    ), "expected date_conflict=True for study_type.stype_nf"
