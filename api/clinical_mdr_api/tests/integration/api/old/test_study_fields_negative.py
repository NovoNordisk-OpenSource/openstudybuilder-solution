# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.fields.negative")
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
    TestUtils.create_library(name="Sponsor", is_editable=True)
    TestUtils.create_library(name="UCUM", is_editable=True)
    TestUtils.create_ct_catalogue()
    TestUtils.create_unit_definition(name="day")
    TestUtils.create_unit_definition(name="week")
    codelist = TestUtils.create_ct_codelist()
    TestUtils.create_study_ct_data_map(codelist_uid=codelist.codelist_uid)

    yield

    drop_db("old.json.test.study.fields.negative")


def test_get_audit_trail_for_study_fields_of_non_existent_study(api_client):
    response = api_client.get("/studies/___NON_EXISTENT_STUDY___/fields-audit-trail")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert res["message"] == "Study with UID '___NON_EXISTENT_STUDY___' doesn't exist."


def test_adding_study1(api_client):
    data = {
        "study_number": "007",
        "study_acronym": "Study-007",
        "project_number": "123",
        "description": "desc123",
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
    assert (
        res["current_metadata"]["identification_metadata"]["description"] == "desc123"
    )
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
    assert res["current_metadata"]["study_description"]["study_title"] is None
    assert res["current_metadata"]["study_description"]["study_short_title"] is None


def test_create_study_with_duplicated_study_number(api_client):
    data = {"study_number": "007", "project_number": "123"}
    response = api_client.post("/studies", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == "Study with Study Number '007' already exists."
