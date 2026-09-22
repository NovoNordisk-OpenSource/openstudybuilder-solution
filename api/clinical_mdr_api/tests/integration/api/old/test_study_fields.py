# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.fields")
    clinical_programme = TestUtils.create_clinical_programme(name="CP")
    TestUtils.create_project(
        name="Project ABC",
        project_number="123",
        description="Description ABC",
        clinical_programme_uid=clinical_programme.uid,
    )
    TestUtils.create_project(
        name="Project DEF",
        project_number="456",
        description="Description DEF",
        clinical_programme_uid=clinical_programme.uid,
    )
    # create library
    library = TestUtils.create_library(name="Sponsor", is_editable=True)
    TestUtils.create_library(name="UCUM", is_editable=True)
    # create catalogue
    catalogue_name = TestUtils.create_ct_catalogue()
    _codelist = TestUtils.create_ct_codelist()
    TestUtils.create_study_ct_data_map(codelist_uid=None)

    library_name = library["name"]

    codelist = create_codelist(
        name="Null Flavor",
        catalogue=catalogue_name,
        uid="null_flav_cl_uid",
        library=library_name,
        submission_value=settings.null_flavor_cl_submval,
    )
    create_ct_term(
        name="Not applicable",  # "Hours",
        uid="na_term_001",  # "Hours_001",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "NA",
            }
        ],
    )
    codelist = create_codelist(
        name="time",  # "Hours",
        uid="C66781",  # "CTCodelist_00004-HOUR",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="UNIT",
    )
    hour_term = create_ct_term(
        name="hours",  # "Hours",
        uid="hours001",  # "Hours_001",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": codelist.codelist_uid,
                "order": 1,
                "submission_value": "hours",
            }
        ],
    )
    subset_codelist = create_codelist(
        name="Unit Subset",
        uid="UnitSubsetCuid",
        catalogue=catalogue_name,
        library=library_name,
        submission_value="UNITSUBS",
    )
    study_time_subset = create_ct_term(
        name="Study Time",
        uid="StudyTimeSuid",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {
                "uid": subset_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Study Time",
            }
        ],
    )
    TestUtils.create_unit_definition(
        name="hours",
        library_name="Sponsor",
        ct_units=[hour_term.uid],
        unit_subsets=[study_time_subset.uid],
    )

    # create Unit Definitions
    TestUtils.create_unit_definition(name="day")
    TestUtils.create_unit_definition(name="week")

    yield

    drop_db("old.json.test.study.fields")


def test_getting_empty_study_list(api_client):
    response = api_client.get("/studies")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_adding_study(api_client):
    data = {
        "study_number": "007",
        "study_acronym": "Study-007",
        "project_number": "123",
    }
    response = api_client.post("/studies", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Study_000001"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "007"
    assert res["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["study_acronym"]
        == "Study-007"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert res["current_metadata"]["identification_metadata"]["project_number"] == "123"
    assert res["current_metadata"]["identification_metadata"]["description"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["project_name"]
        == "Project ABC"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "CP"
    )
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "123-007"
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["study_description"] == {
        "study_short_title": None,
        "study_title": None,
    }


def test_patch_study_add_study_title(api_client):
    data = {"current_metadata": {"study_description": {"study_title": "123"}}}
    response = api_client.patch("/studies/Study_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Study_000001"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "007"
    assert res["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["study_acronym"]
        == "Study-007"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert res["current_metadata"]["identification_metadata"]["project_number"] == "123"
    assert res["current_metadata"]["identification_metadata"]["description"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["project_name"]
        == "Project ABC"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "CP"
    )
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "123-007"
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["study_description"] == {
        "study_short_title": None,
        "study_title": "123",
    }


def test_patch_study_change_study_title(api_client):
    data = {"current_metadata": {"study_description": {"study_title": "456"}}}
    response = api_client.patch("/studies/Study_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Study_000001"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "007"
    assert res["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["study_acronym"]
        == "Study-007"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert res["current_metadata"]["identification_metadata"]["project_number"] == "123"
    assert res["current_metadata"]["identification_metadata"]["description"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["project_name"]
        == "Project ABC"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "CP"
    )
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "123-007"
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["study_description"] == {
        "study_short_title": None,
        "study_title": "456",
    }


def test_patch_study_remove_study_title(api_client):
    data = {"current_metadata": {"study_description": {"study_title": None}}}
    response = api_client.patch("/studies/Study_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Study_000001"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "007"
    assert res["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["study_acronym"]
        == "Study-007"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert res["current_metadata"]["identification_metadata"]["project_number"] == "123"
    assert res["current_metadata"]["identification_metadata"]["description"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["project_name"]
        == "Project ABC"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "CP"
    )
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "123-007"
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["study_description"] == {
        "study_short_title": None,
        "study_title": None,
    }


def test_patch_study_add_multiple_boolean_text_and_numeric_fields(api_client):
    data = {
        "current_metadata": {
            "identification_metadata": {"project_number": "456"},
            "high_level_study_design": {
                "study_type_null_value_code": {"term_uid": "A bad reason"},
                "trial_phase_null_value_code": {"term_uid": "A good reason"},
                "is_extension_trial": False,
                "is_adaptive_design": True,
                "study_stop_rules": "study_stop_rules 710",
            },
            "study_intervention": {
                "intervention_type_code": {"term_uid": "C127574"},
                "trial_intent_types_null_value_code": {"term_uid": "A good reason"},
                "planned_study_length": {
                    "duration_value": 50,
                    "duration_unit_code": {"uid": "UnitDefinition_000001"},
                },
            },
        }
    }
    response = api_client.patch("/studies/Study_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Study_000001"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "007"
    assert res["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["study_acronym"]
        == "Study-007"
    )
    assert res["current_metadata"]["identification_metadata"]["project_number"] == "456"
    assert res["current_metadata"]["identification_metadata"]["description"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["project_name"]
        == "Project DEF"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "CP"
    )
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "456-007"
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["study_description"] == {
        "study_short_title": None,
        "study_title": None,
    }


def test_patch_study_update_and_remove_multiple_fields(api_client):
    data = {
        "current_metadata": {
            "high_level_study_design": {
                "study_type_null_value_code": {"term_uid": "A good reason"},
                "trial_phase_null_value_code": {"term_uid": "A bad reason"},
                "is_extension_trial": True,
                "is_adaptive_design": False,
                "study_stop_rules": None,
            },
            "study_intervention": {
                "trial_intent_types_codes": [
                    {"term_uid": "C49654"},
                    {"term_uid": "C49655"},
                    {"term_uid": "C49657"},
                ],
                "trial_intent_types_null_value_code": None,
                "intervention_type_code": {"term_uid": "C127589"},
                "planned_study_length": {
                    "duration_value": 10,
                    "duration_unit_code": {"uid": "UnitDefinition_000001"},
                },
            },
        }
    }
    response = api_client.patch("/studies/Study_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Study_000001"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "007"
    assert res["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["study_acronym"]
        == "Study-007"
    )
    assert res["current_metadata"]["identification_metadata"]["project_number"] == "456"
    assert res["current_metadata"]["identification_metadata"]["description"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["project_name"]
        == "Project DEF"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "CP"
    )
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "456-007"
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["study_description"] == {
        "study_short_title": None,
        "study_title": None,
    }


def test_add_study_title_test_to_have_multiple_study_value_relationships_attached1(
    api_client,
):
    data = {"current_metadata": {"study_description": {"study_title": "new title"}}}
    response = api_client.patch("/studies/Study_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Study_000001"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "007"
    assert res["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["study_acronym"]
        == "Study-007"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert res["current_metadata"]["identification_metadata"]["project_number"] == "456"
    assert res["current_metadata"]["identification_metadata"]["description"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["project_name"]
        == "Project DEF"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "CP"
    )
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "456-007"
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["study_description"] == {
        "study_short_title": None,
        "study_title": "new title",
    }


def test_patch_study_change_study_identifiers(api_client):
    data = {
        "current_metadata": {
            "identification_metadata": {"study_acronym": "new acronym"}
        }
    }
    response = api_client.patch("/studies/Study_000001", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Study_000001"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "007"
    assert res["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["study_acronym"]
        == "new acronym"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert res["current_metadata"]["identification_metadata"]["project_number"] == "456"
    assert res["current_metadata"]["identification_metadata"]["description"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["project_name"]
        == "Project DEF"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "CP"
    )
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "456-007"
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["study_description"] == {
        "study_short_title": None,
        "study_title": "new title",
    }


def test_get_complete_audit_trail_for_study_fields(api_client):
    response = api_client.get("/studies/Study_000001/fields-audit-trail")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "Study_000001"
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["date"]
    assert res[0]["actions"] == [
        {
            "section": "identification_metadata",
            "field": "study_acronym",
            "before_value": {"term_uid": "Study-007", "name": None},
            "after_value": {"term_uid": "new acronym", "name": None},
            "action": "Edit",
        }
    ]
    assert res[1]["study_uid"] == "Study_000001"
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["date"]
    assert res[1]["actions"] == [
        {
            "section": "study_description",
            "field": "study_title",
            "before_value": None,
            "after_value": {"term_uid": "new title", "name": None},
            "action": "Create",
        }
    ]
    assert res[2]["study_uid"] == "Study_000001"
    assert res[2]["author_username"] == "unknown-user@example.com"
    assert res[2]["date"]
    assert res[2]["actions"] == [
        {
            "section": "study_intervention",
            "field": "intervention_type",
            "before_value": {"term_uid": "C127574", "name": "MJDIAEVS"},
            "after_value": {
                "term_uid": "C127589",
                "name": "Pulmonic Valve Regurgitant Jet Width",
            },
            "action": "Edit",
        },
        {
            "section": "high_level_study_design",
            "field": "is_adaptive_design",
            "before_value": {"term_uid": "true", "name": None},
            "after_value": {"term_uid": "false", "name": None},
            "action": "Edit",
        },
        {
            "section": "high_level_study_design",
            "field": "is_extension_trial",
            "before_value": {"term_uid": "false", "name": None},
            "after_value": {"term_uid": "true", "name": None},
            "action": "Edit",
        },
        {
            "section": "study_intervention",
            "field": "planned_study_length",
            "before_value": {"term_uid": "P50H", "name": None},
            "after_value": {"term_uid": "P10H", "name": None},
            "action": "Edit",
        },
        {
            "section": "high_level_study_design",
            "field": "study_stop_rules",
            "before_value": {"term_uid": "study_stop_rules 710", "name": None},
            "after_value": {"name": None, "term_uid": "study_stop_rules 710"},
            "action": "Delete",
        },
        {
            "section": "high_level_study_design",
            "field": "study_type_null_value_code",
            "before_value": {"term_uid": "A bad reason", "name": "NullValue2"},
            "after_value": {"term_uid": "A good reason", "name": "NullValue1"},
            "action": "Edit",
        },
        {
            "section": "study_intervention",
            "field": "trial_intent_type_null_value_code",
            "before_value": {"term_uid": "A good reason", "name": "NullValue1"},
            "after_value": {"name": "NullValue1", "term_uid": "A good reason"},
            "action": "Delete",
        },
        {
            "section": "study_intervention",
            "field": "trial_intent_type",
            "before_value": {"term_uid": "", "name": None},
            "after_value": {"term_uid": "C49654, C49655, C49657", "name": None},
            "action": "Edit",
        },
        {
            "section": "high_level_study_design",
            "field": "trial_phase_null_value_code",
            "before_value": {"term_uid": "A good reason", "name": "NullValue1"},
            "after_value": {"term_uid": "A bad reason", "name": "NullValue2"},
            "action": "Edit",
        },
    ]
    assert res[3]["study_uid"] == "Study_000001"
    assert res[3]["author_username"] == "unknown-user@example.com"
    assert res[3]["date"]
    assert res[3]["actions"] == [
        {
            "section": "study_intervention",
            "field": "intervention_type",
            "before_value": None,
            "after_value": {"term_uid": "C127574", "name": "MJDIAEVS"},
            "action": "Create",
        },
        {
            "section": "high_level_study_design",
            "field": "is_adaptive_design",
            "before_value": None,
            "after_value": {"term_uid": "true", "name": None},
            "action": "Create",
        },
        {
            "section": "high_level_study_design",
            "field": "is_extension_trial",
            "before_value": None,
            "after_value": {"term_uid": "false", "name": None},
            "action": "Create",
        },
        {
            "section": "study_intervention",
            "field": "planned_study_length",
            "before_value": None,
            "after_value": {"term_uid": "P50H", "name": None},
            "action": "Create",
        },
        {
            "section": "identification_metadata",
            "field": "project_number",
            "before_value": {"term_uid": "123", "name": None},
            "after_value": {"term_uid": "456", "name": None},
            "action": "Edit",
        },
        {
            "section": "identification_metadata",
            "field": "study_id",
            "before_value": {"term_uid": "123", "name": None},
            "after_value": {"term_uid": "456", "name": None},
            "action": "Edit",
        },
        {
            "section": "high_level_study_design",
            "field": "study_stop_rules",
            "before_value": None,
            "after_value": {"term_uid": "study_stop_rules 710", "name": None},
            "action": "Create",
        },
        {
            "section": "high_level_study_design",
            "field": "study_type_null_value_code",
            "before_value": None,
            "after_value": {"term_uid": "A bad reason", "name": "NullValue2"},
            "action": "Create",
        },
        {
            "section": "study_intervention",
            "field": "trial_intent_type_null_value_code",
            "before_value": None,
            "after_value": {"term_uid": "A good reason", "name": "NullValue1"},
            "action": "Create",
        },
        {
            "section": "study_intervention",
            "field": "trial_intent_type",
            "before_value": None,
            "after_value": {"term_uid": "", "name": None},
            "action": "Create",
        },
        {
            "section": "high_level_study_design",
            "field": "trial_phase_null_value_code",
            "before_value": None,
            "after_value": {"term_uid": "A good reason", "name": "NullValue1"},
            "action": "Create",
        },
    ]
    assert res[4]["study_uid"] == "Study_000001"
    assert res[4]["author_username"] == "unknown-user@example.com"
    assert res[4]["date"]
    assert res[4]["actions"] == [
        {
            "section": "study_description",
            "field": "study_title",
            "before_value": {"term_uid": "456", "name": None},
            "after_value": {"name": None, "term_uid": "456"},
            "action": "Delete",
        }
    ]
    assert res[5]["study_uid"] == "Study_000001"
    assert res[5]["author_username"] == "unknown-user@example.com"
    assert res[5]["date"]
    assert res[5]["actions"] == [
        {
            "section": "study_description",
            "field": "study_title",
            "before_value": {"term_uid": "123", "name": None},
            "after_value": {"term_uid": "456", "name": None},
            "action": "Edit",
        }
    ]
    assert res[6]["study_uid"] == "Study_000001"
    assert res[6]["author_username"] == "unknown-user@example.com"
    assert res[6]["date"]
    assert res[6]["actions"] == [
        {
            "section": "study_description",
            "field": "study_title",
            "before_value": None,
            "after_value": {"term_uid": "123", "name": None},
            "action": "Create",
        }
    ]
    assert res[7]["study_uid"] == "Study_000001"
    assert res[7]["author_username"] == "unknown-user@example.com"
    assert res[7]["date"]
    assert res[7]["actions"] == [
        {
            "section": "Unknown",
            "field": "soa_show_all_visits_lab_table",
            "before_value": None,
            "after_value": {"term_uid": "true", "name": None},
            "action": "Create",
        }
    ]
    assert res[8]["study_uid"] == "Study_000001"
    assert res[8]["author_username"] == "unknown-user@example.com"
    assert res[8]["date"]
    assert res[8]["actions"] == [
        {
            "section": "Unknown",
            "field": "baseline_as_time_zero",
            "before_value": None,
            "after_value": {"term_uid": "true", "name": None},
            "action": "Create",
        }
    ]
    assert res[9]["study_uid"] == "Study_000001"
    assert res[9]["author_username"] == "unknown-user@example.com"
    assert res[9]["date"]
    assert res[9]["actions"] == [
        {
            "section": "Unknown",
            "field": "soa_show_milestones",
            "before_value": None,
            "after_value": {"term_uid": "false", "name": None},
            "action": "Create",
        }
    ]
    assert res[10]["study_uid"] == "Study_000001"
    assert res[10]["author_username"] == "unknown-user@example.com"
    assert res[10]["date"]
    assert res[10]["actions"] == [
        {
            "section": "Unknown",
            "field": "soa_show_epochs",
            "before_value": None,
            "after_value": {"term_uid": "true", "name": None},
            "action": "Create",
        }
    ]
    assert res[11]["study_uid"] == "Study_000001"
    assert res[11]["author_username"] == "unknown-user@example.com"
    assert res[11]["date"]
    assert res[11]["actions"] == [
        {
            "section": "Unknown",
            "field": "soa_preferred_time_unit",
            "before_value": None,
            "after_value": {"term_uid": "UnitDefinition_000003", "name": None},
            "action": "Create",
        }
    ]
    assert res[12]["study_uid"] == "Study_000001"
    assert res[12]["author_username"] == "unknown-user@example.com"
    assert res[12]["date"]
    assert res[12]["actions"] == [
        {
            "section": "Unknown",
            "field": "preferred_time_unit",
            "before_value": None,
            "after_value": {"term_uid": "UnitDefinition_000002", "name": None},
            "action": "Create",
        }
    ]
    assert res[13]["study_uid"] == "Study_000001"
    assert res[13]["author_username"] == "unknown-user@example.com"
    assert res[13]["date"]
    assert res[13]["actions"] == [
        {
            "section": "identification_metadata",
            "field": "project_number",
            "before_value": None,
            "after_value": {"term_uid": "123", "name": None},
            "action": "Create",
        },
        {
            "section": "identification_metadata",
            "field": "study_acronym",
            "before_value": None,
            "after_value": {"term_uid": "Study-007", "name": None},
            "action": "Create",
        },
        {
            "section": "identification_metadata",
            "field": "study_id",
            "before_value": None,
            "after_value": {"term_uid": "123", "name": None},
            "action": "Create",
        },
        {
            "section": "identification_metadata",
            "field": "study_number",
            "before_value": None,
            "after_value": {"term_uid": "007", "name": None},
            "action": "Create",
        },
    ]


def test_get_filtered_audit_trail_for_study_fields(api_client):
    response = api_client.get(
        "/studies/Study_000001/fields-audit-trail?exclude_sections=identification_metadata&include_sections=high_level_study_design"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "Study_000001"
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["date"]
    assert res[0]["actions"] == [
        {
            "section": "high_level_study_design",
            "field": "is_adaptive_design",
            "before_value": {"term_uid": "true", "name": None},
            "after_value": {"term_uid": "false", "name": None},
            "action": "Edit",
        },
        {
            "section": "high_level_study_design",
            "field": "is_extension_trial",
            "before_value": {"term_uid": "false", "name": None},
            "after_value": {"term_uid": "true", "name": None},
            "action": "Edit",
        },
        {
            "section": "high_level_study_design",
            "field": "study_stop_rules",
            "before_value": {"term_uid": "study_stop_rules 710", "name": None},
            "after_value": {
                "name": None,
                "term_uid": "study_stop_rules 710",
            },
            "action": "Delete",
        },
        {
            "section": "high_level_study_design",
            "field": "study_type_null_value_code",
            "before_value": {"term_uid": "A bad reason", "name": "NullValue2"},
            "after_value": {"term_uid": "A good reason", "name": "NullValue1"},
            "action": "Edit",
        },
        {
            "section": "high_level_study_design",
            "field": "trial_phase_null_value_code",
            "before_value": {"term_uid": "A good reason", "name": "NullValue1"},
            "after_value": {"term_uid": "A bad reason", "name": "NullValue2"},
            "action": "Edit",
        },
    ]
    assert res[1]["study_uid"] == "Study_000001"
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["date"]
    assert res[1]["actions"] == [
        {
            "section": "high_level_study_design",
            "field": "is_adaptive_design",
            "before_value": None,
            "after_value": {"term_uid": "true", "name": None},
            "action": "Create",
        },
        {
            "section": "high_level_study_design",
            "field": "is_extension_trial",
            "before_value": None,
            "after_value": {"term_uid": "false", "name": None},
            "action": "Create",
        },
        {
            "section": "high_level_study_design",
            "field": "study_stop_rules",
            "before_value": None,
            "after_value": {"term_uid": "study_stop_rules 710", "name": None},
            "action": "Create",
        },
        {
            "section": "high_level_study_design",
            "field": "study_type_null_value_code",
            "before_value": None,
            "after_value": {"term_uid": "A bad reason", "name": "NullValue2"},
            "action": "Create",
        },
        {
            "section": "high_level_study_design",
            "field": "trial_phase_null_value_code",
            "before_value": None,
            "after_value": {"term_uid": "A good reason", "name": "NullValue1"},
            "action": "Create",
        },
    ]


def test_adding_second_study(api_client):
    data = {"study_number": "1910", "project_number": "123"}
    response = api_client.post("/studies", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["uid"] == "Study_000002"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "1910"
    assert res["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert res["current_metadata"]["identification_metadata"]["study_acronym"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert res["current_metadata"]["identification_metadata"]["project_number"] == "123"
    assert res["current_metadata"]["identification_metadata"]["description"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["project_name"]
        == "Project ABC"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "CP"
    )
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "123-1910"
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["study_description"] == {
        "study_short_title": None,
        "study_title": None,
    }


def test_copy_study_high_level_design(api_client):
    response = api_client.get(
        "/studies/Study_000002/copy-component?reference_study_uid=Study_000001&component_to_copy=high_level_study_design&overwrite=true",
    )
    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Study_000002"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "1910"
    assert res["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert res["current_metadata"]["identification_metadata"]["study_acronym"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert res["current_metadata"]["identification_metadata"]["project_number"] == "123"
    assert res["current_metadata"]["identification_metadata"]["description"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["project_name"]
        == "Project ABC"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "CP"
    )
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "123-1910"
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["high_level_study_design"]["study_type_code"] is None
    assert (
        res["current_metadata"]["high_level_study_design"][
            "study_type_null_value_code"
        ]["term_uid"]
        == "A good reason"
    )
    assert (
        res["current_metadata"]["high_level_study_design"][
            "study_type_null_value_code"
        ]["sponsor_preferred_name"]
        == "NullValue1"
    )
    assert (
        res["current_metadata"]["high_level_study_design"][
            "study_type_null_value_code"
        ]["queried_effective_date"]
        is None
    )
    assert (
        res["current_metadata"]["high_level_study_design"][
            "study_type_null_value_code"
        ]["date_conflict"]
        is False
    )
    assert res["current_metadata"]["high_level_study_design"]["trial_type_codes"] == []
    assert (
        res["current_metadata"]["high_level_study_design"]["trial_type_null_value_code"]
        is None
    )
    assert (
        res["current_metadata"]["high_level_study_design"]["trial_phase_code"] is None
    )
    assert (
        res["current_metadata"]["high_level_study_design"][
            "trial_phase_null_value_code"
        ]["term_uid"]
        == "A bad reason"
    )
    assert (
        res["current_metadata"]["high_level_study_design"]["development_stage_code"]
        is None
    )
    assert (
        res["current_metadata"]["high_level_study_design"][
            "trial_phase_null_value_code"
        ]["sponsor_preferred_name"]
        == "NullValue2"
    )
    assert (
        res["current_metadata"]["high_level_study_design"][
            "trial_phase_null_value_code"
        ]["queried_effective_date"]
        is None
    )
    assert (
        res["current_metadata"]["high_level_study_design"][
            "trial_phase_null_value_code"
        ]["date_conflict"]
        is False
    )
    assert (
        res["current_metadata"]["high_level_study_design"]["is_extension_trial"] is True
    )
    assert (
        res["current_metadata"]["high_level_study_design"][
            "is_extension_trial_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["high_level_study_design"]["is_adaptive_design"]
        is False
    )
    assert (
        res["current_metadata"]["high_level_study_design"][
            "is_adaptive_design_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["high_level_study_design"]["study_stop_rules"] is None
    )
    assert (
        res["current_metadata"]["high_level_study_design"][
            "study_stop_rules_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["high_level_study_design"][
            "confirmed_response_minimum_duration"
        ]
        is None
    )
    assert (
        res["current_metadata"]["high_level_study_design"][
            "confirmed_response_minimum_duration_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["high_level_study_design"]["post_auth_indicator"]
        is None
    )
    assert (
        res["current_metadata"]["high_level_study_design"][
            "post_auth_indicator_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["study_population"] is None
    assert res["current_metadata"]["study_intervention"] is None
    assert res["current_metadata"]["study_description"] == {
        "study_short_title": None,
        "study_title": None,
    }


def test_copy_study_intervention(api_client):
    response = api_client.get(
        "/studies/Study_000002/copy-component?reference_study_uid=Study_000001&component_to_copy=study_intervention&overwrite=true"
    )
    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Study_000002"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "1910"
    assert res["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert res["current_metadata"]["identification_metadata"]["study_acronym"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert res["current_metadata"]["identification_metadata"]["project_number"] == "123"
    assert res["current_metadata"]["identification_metadata"]["description"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["project_name"]
        == "Project ABC"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "CP"
    )
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "123-1910"
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["high_level_study_design"] is None
    assert res["current_metadata"]["study_population"] is None
    assert (
        res["current_metadata"]["study_intervention"]["intervention_type_code"][
            "term_uid"
        ]
        == "C127589"
    )
    assert (
        res["current_metadata"]["study_intervention"]["intervention_type_code"][
            "sponsor_preferred_name"
        ]
        == "Pulmonic Valve Regurgitant Jet Width"
    )
    assert (
        res["current_metadata"]["study_intervention"]["intervention_type_code"][
            "queried_effective_date"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_intervention"]["intervention_type_code"][
            "date_conflict"
        ]
        is False
    )
    assert (
        res["current_metadata"]["study_intervention"][
            "intervention_type_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_intervention"]["add_on_to_existing_treatments"]
        is None
    )
    assert (
        res["current_metadata"]["study_intervention"][
            "add_on_to_existing_treatments_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["study_intervention"]["control_type_code"] is None
    assert (
        res["current_metadata"]["study_intervention"]["control_type_null_value_code"]
        is None
    )
    assert (
        res["current_metadata"]["study_intervention"]["intervention_model_code"] is None
    )
    assert (
        res["current_metadata"]["study_intervention"][
            "intervention_model_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["study_intervention"]["is_trial_randomised"] is None
    assert (
        res["current_metadata"]["study_intervention"][
            "is_trial_randomised_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_intervention"]["stratification_factor"] is None
    )
    assert (
        res["current_metadata"]["study_intervention"][
            "stratification_factor_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_intervention"]["trial_blinding_schema_code"]
        is None
    )
    assert (
        res["current_metadata"]["study_intervention"][
            "trial_blinding_schema_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_intervention"]["planned_study_length"][
            "duration_value"
        ]
        == 10
    )
    assert (
        res["current_metadata"]["study_intervention"]["planned_study_length"][
            "duration_unit_code"
        ]["uid"]
        == "UnitDefinition_000001"
    )
    assert (
        res["current_metadata"]["study_intervention"]["planned_study_length"][
            "duration_unit_code"
        ]["name"]
        == "hours"
    )
    assert (
        res["current_metadata"]["study_intervention"]["planned_study_length"][
            "duration_unit_code"
        ]["dimension_name"]
        is None
    )
    assert (
        res["current_metadata"]["study_intervention"][
            "planned_study_length_null_value_code"
        ]
        is None
    )
    assert (
        len(res["current_metadata"]["study_intervention"]["trial_intent_types_codes"])
        == 3
    )
    assert (
        res["current_metadata"]["study_intervention"]["trial_intent_types_codes"][0][
            "term_uid"
        ]
        == "C49654"
    )
    assert (
        res["current_metadata"]["study_intervention"]["trial_intent_types_codes"][0][
            "sponsor_preferred_name"
        ]
        == "Cure Study"
    )
    assert (
        res["current_metadata"]["study_intervention"]["trial_intent_types_codes"][0][
            "queried_effective_date"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_intervention"]["trial_intent_types_codes"][0][
            "date_conflict"
        ]
        is False
    )
    assert (
        res["current_metadata"]["study_intervention"]["trial_intent_types_codes"][1][
            "term_uid"
        ]
        == "C49655"
    )
    assert (
        res["current_metadata"]["study_intervention"]["trial_intent_types_codes"][1][
            "sponsor_preferred_name"
        ]
        == "Adverse Effect Mitigation Study"
    )
    assert (
        res["current_metadata"]["study_intervention"]["trial_intent_types_codes"][1][
            "queried_effective_date"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_intervention"]["trial_intent_types_codes"][1][
            "date_conflict"
        ]
        is False
    )
    assert (
        res["current_metadata"]["study_intervention"]["trial_intent_types_codes"][2][
            "term_uid"
        ]
        == "C49657"
    )
    assert (
        res["current_metadata"]["study_intervention"]["trial_intent_types_codes"][2][
            "sponsor_preferred_name"
        ]
        == "Prevention Study"
    )
    assert (
        res["current_metadata"]["study_intervention"]["trial_intent_types_codes"][2][
            "queried_effective_date"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_intervention"]["trial_intent_types_codes"][2][
            "date_conflict"
        ]
        is False
    )
    assert (
        res["current_metadata"]["study_intervention"][
            "trial_intent_types_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["study_description"] == {
        "study_short_title": None,
        "study_title": None,
    }


def test_copy_study_population(api_client):
    response = api_client.get(
        "/studies/Study_000002/copy-component?reference_study_uid=Study_000001&component_to_copy=study_population&overwrite=true"
    )
    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Study_000002"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "1910"
    assert res["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert res["current_metadata"]["identification_metadata"]["study_acronym"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert res["current_metadata"]["identification_metadata"]["project_number"] == "123"
    assert res["current_metadata"]["identification_metadata"]["description"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["project_name"]
        == "Project ABC"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "CP"
    )
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "123-1910"
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_pas_number_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["high_level_study_design"] is None
    assert res["current_metadata"]["study_population"]["therapeutic_area_codes"] == []
    assert (
        res["current_metadata"]["study_population"]["therapeutic_area_null_value_code"]
        is None
    )
    assert (
        res["current_metadata"]["study_population"][
            "disease_condition_or_indication_codes"
        ]
        == []
    )
    assert (
        res["current_metadata"]["study_population"][
            "disease_condition_or_indication_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["study_population"]["diagnosis_group_codes"] == []
    assert (
        res["current_metadata"]["study_population"]["diagnosis_group_null_value_code"]
        is None
    )
    assert (
        res["current_metadata"]["study_population"]["sex_of_participants_code"] is None
    )
    assert (
        res["current_metadata"]["study_population"][
            "sex_of_participants_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["study_population"]["rare_disease_indicator"] is None
    assert (
        res["current_metadata"]["study_population"][
            "rare_disease_indicator_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_population"]["healthy_subject_indicator"] is None
    )
    assert (
        res["current_metadata"]["study_population"][
            "healthy_subject_indicator_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_population"]["planned_minimum_age_of_subjects"]
        is None
    )
    assert (
        res["current_metadata"]["study_population"][
            "planned_minimum_age_of_subjects_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_population"]["planned_maximum_age_of_subjects"]
        is None
    )
    assert (
        res["current_metadata"]["study_population"][
            "planned_maximum_age_of_subjects_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_population"]["stable_disease_minimum_duration"]
        is None
    )
    assert (
        res["current_metadata"]["study_population"][
            "stable_disease_minimum_duration_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_population"]["pediatric_study_indicator"] is None
    )
    assert (
        res["current_metadata"]["study_population"][
            "pediatric_study_indicator_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_population"][
            "pediatric_postmarket_study_indicator"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_population"][
            "pediatric_postmarket_study_indicator_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_population"][
            "pediatric_investigation_plan_indicator"
        ]
        is None
    )
    assert (
        res["current_metadata"]["study_population"][
            "pediatric_investigation_plan_indicator_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["study_population"]["relapse_criteria"] is None
    assert (
        res["current_metadata"]["study_population"]["relapse_criteria_null_value_code"]
        is None
    )
    assert (
        res["current_metadata"]["study_population"]["number_of_expected_subjects"]
        is None
    )
    assert (
        res["current_metadata"]["study_population"][
            "number_of_expected_subjects_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["study_intervention"] is None
    assert res["current_metadata"]["study_description"] == {
        "study_short_title": None,
        "study_title": None,
    }
