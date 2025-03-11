# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db
from pydantic import BaseModel

import clinical_mdr_api.models.syntax_templates.criteria_template as ct_models
import clinical_mdr_api.services.libraries.libraries as library_service
from clinical_mdr_api.main import app
from clinical_mdr_api.services.syntax_templates.criteria_templates import (
    CriteriaTemplateService,
)
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_CRITERIA,
    STARTUP_PARAMETERS_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.data_library import (
    criteria_template_data as template_data,
)
from clinical_mdr_api.tests.integration.utils.data_library import (
    inject_base_data,
    library_data,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.criteria")
    db.cypher_query(STARTUP_PARAMETERS_CYPHER)
    db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
    inject_base_data()
    db.cypher_query(STARTUP_CRITERIA)

    library_service.create(**library_data)
    templatedata = template_data.copy()
    criteria_template = ct_models.CriteriaTemplateCreateInput(**templatedata)
    criteria_template = CriteriaTemplateService().create(criteria_template)
    if isinstance(criteria_template, BaseModel):
        criteria_template = criteria_template.dict()
    CriteriaTemplateService().approve(criteria_template["uid"])

    yield

    drop_db("old.json.test.criteria")


def test_empty_list(api_client):
    response = api_client.get("/criteria?total_count=true")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_adding_criteria(api_client):
    data = {
        "criteria_data": {
            "criteria_template_uid": "CriteriaTemplate_000001",
            "library_name": "Test library",
            "parameter_terms": [],
        }
    }
    response = api_client.post(
        "/studies/Study_000001/study-criteria?create_criteria=true", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "Study_000001"
    assert res["study_version"]
    assert res["key_criteria"] is False
    assert res["order"] == 1
    assert res["project_number"] == "123"
    assert res["project_name"] == "Project ABC"
    assert res["study_criteria_uid"] == "StudyCriteria_000001"
    assert res["criteria_type"]["term_uid"] == "C25532"
    assert res["criteria_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["criteria_type"]["codelists"]) == 1
    assert res["criteria_type"]["codelists"][0]["codelist_uid"] == "CTCodelist_000001"
    assert res["criteria_type"]["codelists"][0]["order"] is None
    assert res["criteria_type"]["codelists"][0]["library_name"] == "CDISC"
    assert res["criteria_type"]["sponsor_preferred_name"] == "INCLUSION CRITERIA"
    assert (
        res["criteria_type"]["sponsor_preferred_name_sentence_case"]
        == "Inclusion Criteria"
    )
    assert res["criteria_type"]["library_name"] == "CDISC"
    assert res["criteria_type"]["start_date"]
    assert res["criteria_type"]["end_date"] is None
    assert res["criteria_type"]["status"] == "Final"
    assert res["criteria_type"]["version"] == "1.0"
    assert res["criteria_type"]["change_description"] == "Approved version"
    assert res["criteria_type"]["author_username"] == "unknown-user@example.com"
    assert res["criteria_type"]["queried_effective_date"]
    assert res["criteria_type"]["date_conflict"] is False
    assert res["criteria_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["criteria"]["uid"] == "Criteria_000001"
    assert res["criteria"]["name"] == "Test_Name_Template"
    assert res["criteria"]["name_plain"] == "Test_Name_Template"
    assert res["criteria"]["end_date"] is None
    assert res["criteria"]["status"] == "Final"
    assert res["criteria"]["version"] == "1.0"
    assert res["criteria"]["change_description"] == "Approved version"
    assert res["criteria"]["author_username"] == "unknown-user@example.com"
    assert res["criteria"]["possible_actions"] == ["inactivate"]
    assert res["criteria"]["template"]["name"] == "Test_Name_Template"
    assert res["criteria"]["template"]["name_plain"] == "Test_Name_Template"
    assert res["criteria"]["template"]["uid"] == "CriteriaTemplate_000001"
    assert res["criteria"]["template"]["sequence_id"] == "CI1"
    assert res["criteria"]["template"]["guidance_text"] is None
    assert res["criteria"]["template"]["library_name"] == "Test library"
    assert res["criteria"]["parameter_terms"] == []
    assert res["criteria"]["library"]["name"] == "Test library"
    assert res["criteria"]["library"]["is_editable"] is True
    assert res["criteria"]["study_count"] == 0
    assert res["author_username"] == "unknown-user@example.com"
    assert res["latest_criteria"] is None
    assert res["accepted_version"] is False


def test_get_all(api_client):
    response = api_client.get("/criteria?total_count=true")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "Criteria_000001"
    assert res["items"][0]["name"] == "Test_Name_Template"
    assert res["items"][0]["name_plain"] == "Test_Name_Template"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Final"
    assert res["items"][0]["version"] == "1.0"
    assert res["items"][0]["change_description"] == "Approved version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["possible_actions"] == ["inactivate"]
    assert res["items"][0]["template"] == {
        "name": "Test_Name_Template",
        "name_plain": "Test_Name_Template",
        "uid": "CriteriaTemplate_000001",
        "sequence_id": "CI1",
        "guidance_text": None,
        "library_name": "Test library",
        "type": {
            "term_uid": "C25532",
            "name": {
                "sponsor_preferred_name": "INCLUSION CRITERIA",
                "sponsor_preferred_name_sentence_case": "Inclusion Criteria",
            },
            "attributes": {
                "code_submission_value": "Inclusion Criteria",
                "nci_preferred_name": "Inclusion Criteria",
            },
        },
    }
    assert res["items"][0]["parameter_terms"] == []
    assert res["items"][0]["library"] == {"name": "Test library", "is_editable": True}
    assert res["items"][0]["study_count"] == 1


def test_creating_the_same_criteria_creates_a_new_selection_of_same_criteria(
    api_client,
):
    data = {
        "criteria_data": {
            "criteria_template_uid": "CriteriaTemplate_000001",
            "library_name": "Test library",
            "parameter_terms": [],
        }
    }
    response = api_client.post(
        "/studies/Study_000001/study-criteria?create_criteria=true", json=data
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "Study_000001"
    assert res["study_version"]
    assert res["key_criteria"] is False
    assert res["order"] == 2
    assert res["project_number"] == "123"
    assert res["project_name"] == "Project ABC"
    assert res["study_criteria_uid"] == "StudyCriteria_000002"
    assert res["criteria_type"]["term_uid"] == "C25532"
    assert res["criteria_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["criteria_type"]["codelists"]) == 1
    assert res["criteria_type"]["codelists"][0]["codelist_uid"] == "CTCodelist_000001"
    assert res["criteria_type"]["codelists"][0]["order"] is None
    assert res["criteria_type"]["codelists"][0]["library_name"] == "CDISC"
    assert res["criteria_type"]["sponsor_preferred_name"] == "INCLUSION CRITERIA"
    assert (
        res["criteria_type"]["sponsor_preferred_name_sentence_case"]
        == "Inclusion Criteria"
    )
    assert res["criteria_type"]["library_name"] == "CDISC"
    assert res["criteria_type"]["start_date"]
    assert res["criteria_type"]["end_date"] is None
    assert res["criteria_type"]["status"] == "Final"
    assert res["criteria_type"]["version"] == "1.0"
    assert res["criteria_type"]["change_description"] == "Approved version"
    assert res["criteria_type"]["author_username"] == "unknown-user@example.com"
    assert res["criteria_type"]["queried_effective_date"]
    assert res["criteria_type"]["date_conflict"] is False
    assert res["criteria_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["criteria"]["uid"] == "Criteria_000001"
    assert res["criteria"]["name"] == "Test_Name_Template"
    assert res["criteria"]["name_plain"] == "Test_Name_Template"
    assert res["criteria"]["end_date"] is None
    assert res["criteria"]["status"] == "Final"
    assert res["criteria"]["version"] == "1.0"
    assert res["criteria"]["change_description"] == "Approved version"
    assert res["criteria"]["author_username"] == "unknown-user@example.com"
    assert res["criteria"]["possible_actions"] == ["inactivate"]
    assert res["criteria"]["template"]["name"] == "Test_Name_Template"
    assert res["criteria"]["template"]["name_plain"] == "Test_Name_Template"
    assert res["criteria"]["template"]["uid"] == "CriteriaTemplate_000001"
    assert res["criteria"]["template"]["sequence_id"] == "CI1"
    assert res["criteria"]["template"]["guidance_text"] is None
    assert res["criteria"]["template"]["library_name"] == "Test library"
    assert res["criteria"]["parameter_terms"] == []
    assert res["criteria"]["library"]["name"] == "Test library"
    assert res["criteria"]["library"]["is_editable"] is True
    assert res["criteria"]["study_count"] == 0
    assert res["author_username"] == "unknown-user@example.com"
    assert res["latest_criteria"] is None
    assert res["accepted_version"] is False


def test_get_all_still_returns_a_single_entry(api_client):
    response = api_client.get("/criteria?total_count=true")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["uid"] == "Criteria_000001"
    assert res["items"][0]["name"] == "Test_Name_Template"
    assert res["items"][0]["name_plain"] == "Test_Name_Template"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Final"
    assert res["items"][0]["version"] == "1.0"
    assert res["items"][0]["change_description"] == "Approved version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["possible_actions"] == ["inactivate"]
    assert res["items"][0]["template"] == {
        "name": "Test_Name_Template",
        "name_plain": "Test_Name_Template",
        "uid": "CriteriaTemplate_000001",
        "sequence_id": "CI1",
        "guidance_text": None,
        "library_name": "Test library",
        "type": {
            "term_uid": "C25532",
            "name": {
                "sponsor_preferred_name": "INCLUSION CRITERIA",
                "sponsor_preferred_name_sentence_case": "Inclusion Criteria",
            },
            "attributes": {
                "code_submission_value": "Inclusion Criteria",
                "nci_preferred_name": "Inclusion Criteria",
            },
        },
    }
    assert res["items"][0]["parameter_terms"] == []
    assert res["items"][0]["library"] == {"name": "Test library", "is_editable": True}
    assert res["items"][0]["study_count"] == 1


def test_get_by_uid(api_client):
    response = api_client.get("/criteria/Criteria_000001")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "Criteria_000001"
    assert res["name"] == "Test_Name_Template"
    assert res["name_plain"] == "Test_Name_Template"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["change_description"] == "Approved version"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["inactivate"]
    assert res["template"] == {
        "name": "Test_Name_Template",
        "name_plain": "Test_Name_Template",
        "uid": "CriteriaTemplate_000001",
        "sequence_id": "CI1",
        "guidance_text": None,
        "library_name": "Test library",
        "type": {
            "term_uid": "C25532",
            "name": {
                "sponsor_preferred_name": "INCLUSION CRITERIA",
                "sponsor_preferred_name_sentence_case": "Inclusion Criteria",
            },
            "attributes": {
                "code_submission_value": "Inclusion Criteria",
                "nci_preferred_name": "Inclusion Criteria",
            },
        },
    }
    assert res["parameter_terms"] == []
    assert res["library"] == {"name": "Test library", "is_editable": True}
    assert res["study_count"] == 1


def test_get_versions(api_client):
    response = api_client.get("/criteria/Criteria_000001/versions")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["uid"] == "Criteria_000001"
    assert res[0]["name"] == "Test_Name_Template"
    assert res[0]["name_plain"] == "Test_Name_Template"
    assert res[0]["end_date"] is None
    assert res[0]["status"] == "Final"
    assert res[0]["version"] == "1.0"
    assert res[0]["change_description"] == "Approved version"
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["possible_actions"] == ["inactivate"]
    assert res[0]["template"] == {
        "name": "Test_Name_Template",
        "name_plain": "Test_Name_Template",
        "uid": "CriteriaTemplate_000001",
        "sequence_id": "CI1",
        "guidance_text": None,
        "library_name": "Test library",
        "type": {
            "term_uid": "C25532",
            "name": {
                "sponsor_preferred_name": "INCLUSION CRITERIA",
                "sponsor_preferred_name_sentence_case": "Inclusion Criteria",
            },
            "attributes": {
                "code_submission_value": "Inclusion Criteria",
                "nci_preferred_name": "Inclusion Criteria",
            },
        },
    }
    assert res[0]["parameter_terms"] == []
    assert res[0]["library"] == {"name": "Test library", "is_editable": True}
    assert res[0]["study_count"] == 1
    assert res[0]["changes"] == {
        "start_date": True,
        "end_date": True,
        "status": True,
        "version": True,
        "change_description": True,
        "possible_actions": True,
    }
    assert res[1]["uid"] == "Criteria_000001"
    assert res[1]["name"] == "Test_Name_Template"
    assert res[1]["name_plain"] == "Test_Name_Template"
    assert res[1]["end_date"]
    assert res[1]["status"] == "Draft"
    assert res[1]["version"] == "0.1"
    assert res[1]["change_description"] == "Initial version"
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["possible_actions"] == ["approve", "delete", "edit"]
    assert res[1]["template"] == {
        "name": "Test_Name_Template",
        "name_plain": "Test_Name_Template",
        "uid": "CriteriaTemplate_000001",
        "sequence_id": "CI1",
        "guidance_text": None,
        "library_name": "Test library",
        "type": {
            "term_uid": "C25532",
            "name": {
                "sponsor_preferred_name": "INCLUSION CRITERIA",
                "sponsor_preferred_name_sentence_case": "Inclusion Criteria",
            },
            "attributes": {
                "code_submission_value": "Inclusion Criteria",
                "nci_preferred_name": "Inclusion Criteria",
            },
        },
    }
    assert res[1]["parameter_terms"] == []
    assert res[1]["library"] == {"name": "Test library", "is_editable": True}
    assert res[1]["study_count"] == 1
    assert res[1]["changes"] == {}


def test_get_studies(api_client):
    response = api_client.get("/criteria/Criteria_000001/studies")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["uid"] == "Study_000001"
    assert res[0]["possible_actions"] == ["delete", "lock", "release"]
    assert res[0]["study_parent_part"] is None
    assert res[0]["study_subpart_uids"] == []
    assert (
        res[0]["current_metadata"]["identification_metadata"]["study_number"] == "123"
    )
    assert res[0]["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert (
        res[0]["current_metadata"]["identification_metadata"]["study_acronym"]
        == "study_root"
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["project_number"] == "123"
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["project_name"]
        == "Project ABC"
    )
    assert res[0]["current_metadata"]["identification_metadata"]["description"]
    assert (
        res[0]["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "CP"
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["study_id"] == "123-123"
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res[0]["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert res[0]["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res[0]["current_metadata"]["version_metadata"]["version_number"] is None
    assert res[0]["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res[0]["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res[0]["current_metadata"]["version_metadata"]["version_description"] is None
    assert res[0]["current_metadata"]["high_level_study_design"] is None
    assert res[0]["current_metadata"]["study_population"] is None
    assert res[0]["current_metadata"]["study_intervention"] is None
    assert res[0]["current_metadata"]["study_description"] == {
        "study_title": None,
        "study_short_title": None,
    }


def test_get_parameters(api_client):
    response = api_client.get("/criteria/Criteria_000001/parameters")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == []


def test_delete(api_client):
    response = api_client.delete("/criteria/Criteria_000001")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Object has been accepted"
