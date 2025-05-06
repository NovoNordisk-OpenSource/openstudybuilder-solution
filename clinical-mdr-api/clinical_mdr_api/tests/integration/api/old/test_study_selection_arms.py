# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_STUDY_ARM_CYPHER,
    fix_study_preferred_time_unit,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.selection.arms")
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
    TestUtils.set_study_standard_version(
        study_uid="study_root", create_codelists_and_terms_for_package=False
    )

    # locking and unlocking to create multiple study value relationships on the existent StudySelections
    TestUtils.create_study_fields_configuration()
    fix_study_preferred_time_unit("study_root")

    yield

    drop_db("old.json.test.study.selection.arms")


def test_getting_empty_list1(api_client):
    response = api_client.get("/studies/study_root/study-arms")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_getting_empty_list_for_all_studies1(api_client):
    response = api_client.get("/study-arms")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_adding_selection1(api_client):
    data = {
        "name": "Arm_Name_1",
        "short_name": "Arm_Short_Name_1",
        "code": "Arm_code_1",
        "description": "desc...",
        "arm_colour": "arm_colour...",
        "randomization_group": "Randomization_Group_1",
        "number_of_subjects": 1,
        "arm_type_uid": "term_root_final",
    }
    response = api_client.post("/studies/study_root/study-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["arm_uid"] == "StudyArm_000001"
    assert res["order"] == 1
    assert res["name"] == "Arm_Name_1"
    assert res["short_name"] == "Arm_Short_Name_1"
    assert res["code"] == "Arm_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_type"]["codelists"]) == 1
    assert res["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_type"]["start_date"]
    assert res["arm_type"]["end_date"] is None
    assert res["arm_type"]["status"] == "Final"
    assert res["arm_type"]["version"] == "1.0"
    assert res["arm_type"]["change_description"] == "Approved version"
    assert res["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_type"]["queried_effective_date"]
    assert res["arm_type"]["date_conflict"] is False
    assert res["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["description"] == "desc..."
    assert res["arm_colour"] == "arm_colour..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_get_all_list_non_empty1(api_client):
    response = api_client.get("/studies/study_root/study-arms")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["study_version"]
    assert res["items"][0]["arm_uid"] == "StudyArm_000001"
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["name"] == "Arm_Name_1"
    assert res["items"][0]["short_name"] == "Arm_Short_Name_1"
    assert res["items"][0]["code"] == "Arm_code_1"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] is None
    assert res["items"][0]["change_type"] is None
    assert res["items"][0]["accepted_version"] is False
    assert res["items"][0]["arm_type"]["term_uid"] == "term_root_final"
    assert res["items"][0]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["items"][0]["arm_type"]["codelists"]) == 1
    assert res["items"][0]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["items"][0]["arm_type"]["codelists"][0]["order"] == 1
    assert res["items"][0]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["items"][0]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["items"][0]["arm_type"]["library_name"] == "Sponsor"
    assert res["items"][0]["arm_type"]["start_date"]
    assert res["items"][0]["arm_type"]["end_date"] is None
    assert res["items"][0]["arm_type"]["status"] == "Final"
    assert res["items"][0]["arm_type"]["version"] == "1.0"
    assert res["items"][0]["arm_type"]["change_description"] == "Approved version"
    assert res["items"][0]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["arm_type"]["queried_effective_date"]
    assert res["items"][0]["arm_type"]["date_conflict"] is False
    assert res["items"][0]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["items"][0]["arm_connected_branch_arms"] is None
    assert res["items"][0]["description"] == "desc..."
    assert res["items"][0]["arm_colour"] == "arm_colour..."
    assert res["items"][0]["number_of_subjects"] == 1
    assert res["items"][0]["randomization_group"] == "Randomization_Group_1"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"


def test_get_all_for_all_studies1(api_client):
    response = api_client.get("/study-arms")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["study_version"]
    assert res["items"][0]["arm_uid"] == "StudyArm_000001"
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["name"] == "Arm_Name_1"
    assert res["items"][0]["short_name"] == "Arm_Short_Name_1"
    assert res["items"][0]["code"] == "Arm_code_1"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] is None
    assert res["items"][0]["change_type"] is None
    assert res["items"][0]["accepted_version"] is False
    assert res["items"][0]["arm_type"]["term_uid"] == "term_root_final"
    assert res["items"][0]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["items"][0]["arm_type"]["codelists"]) == 1
    assert res["items"][0]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["items"][0]["arm_type"]["codelists"][0]["order"] == 1
    assert res["items"][0]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["items"][0]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["items"][0]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["items"][0]["arm_type"]["library_name"] == "Sponsor"
    assert res["items"][0]["arm_type"]["start_date"]
    assert res["items"][0]["arm_type"]["end_date"] is None
    assert res["items"][0]["arm_type"]["status"] == "Final"
    assert res["items"][0]["arm_type"]["version"] == "1.0"
    assert res["items"][0]["arm_type"]["change_description"] == "Approved version"
    assert res["items"][0]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["arm_type"]["queried_effective_date"]
    assert res["items"][0]["arm_type"]["date_conflict"] is False
    assert res["items"][0]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["items"][0]["arm_connected_branch_arms"] is None
    assert res["items"][0]["description"] == "desc..."
    assert res["items"][0]["arm_colour"] == "arm_colour..."
    assert res["items"][0]["number_of_subjects"] == 1
    assert res["items"][0]["randomization_group"] == "Randomization_Group_1"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"


def test_add_study_title_test_to_have_multiple_study_value_relationships_attached2(
    api_client,
):
    data = {"current_metadata": {"study_description": {"study_title": "new title"}}}
    response = api_client.patch("/studies/study_root", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "study_root"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "0"
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
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "some_id-0"
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
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["study_description"] == {
        "study_title": "new title",
        "study_short_title": None,
    }


def test_lock_study_test_to_have_multiple_study_value_relationships_attached5(
    api_client,
):
    data = {"change_description": "Lock 1"}
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached5(
    api_client,
):
    response = api_client.delete("/studies/study_root/locks")

    assert_response_status_code(response, 200)


def test_patch_specific_set_name1(api_client):
    data = {"name": "New_Arm_Name_1", "arm_type_uid": "term_root_final_non_edit"}
    response = api_client.patch(
        "/studies/study_root/study-arms/StudyArm_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["arm_uid"] == "StudyArm_000001"
    assert res["order"] == 1
    assert res["name"] == "New_Arm_Name_1"
    assert res["short_name"] == "Arm_Short_Name_1"
    assert res["code"] == "Arm_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_type"]["codelists"]) == 1
    assert res["arm_type"]["codelists"][0]["codelist_uid"] == "non_editable_cr"
    assert res["arm_type"]["codelists"][0]["order"] == 3
    assert res["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert res["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    assert (
        res["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_type"]["library_name"] == "CDISC"
    assert res["arm_type"]["start_date"]
    assert res["arm_type"]["end_date"] is None
    assert res["arm_type"]["status"] == "Final"
    assert res["arm_type"]["version"] == "1.0"
    assert res["arm_type"]["change_description"] == "Approved version"
    assert res["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_type"]["queried_effective_date"]
    assert res["arm_type"]["date_conflict"] is False
    assert res["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["arm_connected_branch_arms"] is None
    assert res["description"] == "desc..."
    assert res["arm_colour"] == "arm_colour..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_all_history_of_specific_selection1(api_client):
    response = api_client.get(
        "/studies/study_root/study-arms/StudyArm_000001/audit-trail/"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 1
    assert res[0]["project_number"] is None
    assert res[0]["project_name"] is None
    assert res[0]["study_version"] is None
    assert res[0]["arm_uid"] == "StudyArm_000001"
    assert res[0]["name"] == "New_Arm_Name_1"
    assert res[0]["short_name"] == "Arm_Short_Name_1"
    assert res[0]["code"] == "Arm_code_1"
    assert res[0]["description"] == "desc..."
    assert res[0]["arm_colour"] == "arm_colour..."
    assert res[0]["randomization_group"] == "Randomization_Group_1"
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res[0]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res[0]["arm_type"]["codelists"]) == 1
    assert res[0]["arm_type"]["codelists"][0]["codelist_uid"] == "non_editable_cr"
    assert res[0]["arm_type"]["codelists"][0]["order"] == 3
    assert res[0]["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert res[0]["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    assert (
        res[0]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[0]["arm_type"]["library_name"] == "CDISC"
    assert res[0]["arm_type"]["start_date"]
    assert res[0]["arm_type"]["end_date"] is None
    assert res[0]["arm_type"]["status"] == "Final"
    assert res[0]["arm_type"]["version"] == "1.0"
    assert res[0]["arm_type"]["change_description"] == "Approved version"
    assert res[0]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res[0]["arm_type"]["queried_effective_date"]
    assert res[0]["arm_type"]["date_conflict"] is False
    assert res[0]["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert set(res[0]["changes"]) == set(
        [
            "name",
            "arm_type",
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["order"] == 1
    assert res[1]["project_number"] is None
    assert res[1]["project_name"] is None
    assert res[1]["study_version"] is None
    assert res[1]["arm_uid"] == "StudyArm_000001"
    assert res[1]["name"] == "Arm_Name_1"
    assert res[1]["short_name"] == "Arm_Short_Name_1"
    assert res[1]["code"] == "Arm_code_1"
    assert res[1]["description"] == "desc..."
    assert res[1]["arm_colour"] == "arm_colour..."
    assert res[1]["randomization_group"] == "Randomization_Group_1"
    assert res[1]["number_of_subjects"] == 1
    assert res[1]["arm_type"]["term_uid"] == "term_root_final"
    assert res[1]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res[1]["arm_type"]["codelists"]) == 1
    assert res[1]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res[1]["arm_type"]["codelists"][0]["order"] == 1
    assert res[1]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res[1]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res[1]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[1]["arm_type"]["library_name"] == "Sponsor"
    assert res[1]["arm_type"]["start_date"]
    assert res[1]["arm_type"]["end_date"] is None
    assert res[1]["arm_type"]["status"] == "Final"
    assert res[1]["arm_type"]["version"] == "1.0"
    assert res[1]["arm_type"]["change_description"] == "Approved version"
    assert res[1]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res[1]["arm_type"]["queried_effective_date"]
    assert res[1]["arm_type"]["date_conflict"] is False
    assert res[1]["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"]
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False
    assert res[1]["changes"] == []


def test_adding_selection_21(api_client):
    data = {
        "name": "Arm_Name_2",
        "short_name": "Arm_Short_Name_2",
        "code": "Arm_code_2",
        "description": "desc...",
        "arm_colour": "arm_colour...",
        "randomization_group": "Randomization_Group_2",
        "number_of_subjects": 1,
        "arm_type_uid": "term_root_final",
    }
    response = api_client.post("/studies/study_root/study-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["arm_uid"] == "StudyArm_000004"
    assert res["order"] == 2
    assert res["name"] == "Arm_Name_2"
    assert res["short_name"] == "Arm_Short_Name_2"
    assert res["code"] == "Arm_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_type"]["codelists"]) == 1
    assert res["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_type"]["start_date"]
    assert res["arm_type"]["end_date"] is None
    assert res["arm_type"]["status"] == "Final"
    assert res["arm_type"]["version"] == "1.0"
    assert res["arm_type"]["change_description"] == "Approved version"
    assert res["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_type"]["queried_effective_date"]
    assert res["arm_type"]["date_conflict"] is False
    assert res["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["description"] == "desc..."
    assert res["arm_colour"] == "arm_colour..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_2"
    assert res["author_username"] == "unknown-user@example.com"


def test_get_specific1(api_client):
    response = api_client.get("/studies/study_root/study-arms/StudyArm_000004")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["arm_uid"] == "StudyArm_000004"
    assert res["order"] == 2
    assert res["name"] == "Arm_Name_2"
    assert res["short_name"] == "Arm_Short_Name_2"
    assert res["code"] == "Arm_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_type"]["codelists"]) == 1
    assert res["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_type"]["start_date"]
    assert res["arm_type"]["end_date"] is None
    assert res["arm_type"]["status"] == "Final"
    assert res["arm_type"]["version"] == "1.0"
    assert res["arm_type"]["change_description"] == "Approved version"
    assert res["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_type"]["queried_effective_date"]
    assert res["arm_type"]["date_conflict"] is False
    assert res["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["arm_connected_branch_arms"] is None
    assert res["description"] == "desc..."
    assert res["arm_colour"] == "arm_colour..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_2"
    assert res["author_username"] == "unknown-user@example.com"


def test_reorder_specific1(api_client):
    data = {"new_order": 2}
    response = api_client.patch(
        "/studies/study_root/study-arms/StudyArm_000004/order", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["arm_uid"] == "StudyArm_000004"
    assert res["order"] == 2
    assert res["name"] == "Arm_Name_2"
    assert res["short_name"] == "Arm_Short_Name_2"
    assert res["code"] == "Arm_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_type"]["codelists"]) == 1
    assert res["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_type"]["start_date"]
    assert res["arm_type"]["end_date"] is None
    assert res["arm_type"]["status"] == "Final"
    assert res["arm_type"]["version"] == "1.0"
    assert res["arm_type"]["change_description"] == "Approved version"
    assert res["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_type"]["queried_effective_date"]
    assert res["arm_type"]["date_conflict"] is False
    assert res["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["arm_connected_branch_arms"] is None
    assert res["description"] == "desc..."
    assert res["arm_colour"] == "arm_colour..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_2"
    assert res["author_username"] == "unknown-user@example.com"


def test_lock_study_test_to_have_multiple_study_value_relationships_attached6(
    api_client,
):
    data = {"change_description": "Lock 1"}
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached6(
    api_client,
):
    response = api_client.delete("/studies/study_root/locks")

    assert_response_status_code(response, 200)


def test_delete3(api_client):
    response = api_client.delete("/studies/study_root/study-arms/StudyArm_000004")

    assert_response_status_code(response, 204)


def test_adding_selection_to_check_if_the_type_can_be_optional(api_client):
    data = {
        "name": "Arm_Name_3",
        "short_name": "Arm_Short_Name_3",
        "code": "Arm_code_3",
        "description": "desc...",
        "arm_colour": "arm_colour...",
        "randomization_group": "Randomization_Group_3",
        "number_of_subjects": 1,
    }
    response = api_client.post("/studies/study_root/study-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["arm_uid"] == "StudyArm_000007"
    assert res["order"] == 2
    assert res["name"] == "Arm_Name_3"
    assert res["short_name"] == "Arm_Short_Name_3"
    assert res["code"] == "Arm_code_3"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"] is None
    assert res["description"] == "desc..."
    assert res["arm_colour"] == "arm_colour..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_3"
    assert res["author_username"] == "unknown-user@example.com"


def test_patch_specific_set_arm_type_uid_to_check_after_not_being_specified(api_client):
    data = {"name": "New_Arm_Name_3", "arm_type_uid": "term_root_final_non_edit"}
    response = api_client.patch(
        "/studies/study_root/study-arms/StudyArm_000007", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["arm_uid"] == "StudyArm_000007"
    assert res["order"] == 2
    assert res["name"] == "New_Arm_Name_3"
    assert res["short_name"] == "Arm_Short_Name_3"
    assert res["code"] == "Arm_code_3"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_type"]["codelists"]) == 1
    assert res["arm_type"]["codelists"][0]["codelist_uid"] == "non_editable_cr"
    assert res["arm_type"]["codelists"][0]["order"] == 3
    assert res["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert res["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    assert (
        res["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_type"]["library_name"] == "CDISC"
    assert res["arm_type"]["start_date"]
    assert res["arm_type"]["end_date"] is None
    assert res["arm_type"]["status"] == "Final"
    assert res["arm_type"]["version"] == "1.0"
    assert res["arm_type"]["change_description"] == "Approved version"
    assert res["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_type"]["queried_effective_date"]
    assert res["arm_type"]["date_conflict"] is False
    assert res["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["arm_connected_branch_arms"] is None
    assert res["description"] == "desc..."
    assert res["arm_colour"] == "arm_colour..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_3"
    assert res["author_username"] == "unknown-user@example.com"


def test_all_history_of_specific_selection_to_test_if_the_armtype_optional_is_being_manage_even_if_the_history_schema_is_applied(
    api_client,
):
    response = api_client.get(
        "/studies/study_root/study-arms/StudyArm_000007/audit-trail/"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 2
    assert res[0]["project_number"] is None
    assert res[0]["project_name"] is None
    assert res[0]["study_version"] is None
    assert res[0]["arm_uid"] == "StudyArm_000007"
    assert res[0]["name"] == "New_Arm_Name_3"
    assert res[0]["short_name"] == "Arm_Short_Name_3"
    assert res[0]["code"] == "Arm_code_3"
    assert res[0]["description"] == "desc..."
    assert res[0]["arm_colour"] == "arm_colour..."
    assert res[0]["randomization_group"] == "Randomization_Group_3"
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res[0]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res[0]["arm_type"]["codelists"]) == 1
    assert res[0]["arm_type"]["codelists"][0]["codelist_uid"] == "non_editable_cr"
    assert res[0]["arm_type"]["codelists"][0]["order"] == 3
    assert res[0]["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert res[0]["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    assert (
        res[0]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[0]["arm_type"]["library_name"] == "CDISC"
    assert res[0]["arm_type"]["start_date"]
    assert res[0]["arm_type"]["end_date"] is None
    assert res[0]["arm_type"]["status"] == "Final"
    assert res[0]["arm_type"]["version"] == "1.0"
    assert res[0]["arm_type"]["change_description"] == "Approved version"
    assert res[0]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res[0]["arm_type"]["queried_effective_date"]
    assert res[0]["arm_type"]["date_conflict"] is False
    assert res[0]["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert set(res[0]["changes"]) == set(
        [
            "name",
            "arm_type",
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["order"] == 2
    assert res[1]["project_number"] is None
    assert res[1]["project_name"] is None
    assert res[1]["study_version"] is None
    assert res[1]["arm_uid"] == "StudyArm_000007"
    assert res[1]["name"] == "Arm_Name_3"
    assert res[1]["short_name"] == "Arm_Short_Name_3"
    assert res[1]["code"] == "Arm_code_3"
    assert res[1]["description"] == "desc..."
    assert res[1]["arm_colour"] == "arm_colour..."
    assert res[1]["randomization_group"] == "Randomization_Group_3"
    assert res[1]["number_of_subjects"] == 1
    assert res[1]["arm_type"] is None
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"]
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False
    assert res[1]["changes"] == []


def test_patch_specific_set_arm_type_uid_to_null1(api_client):
    data = {"arm_type_uid": None}
    response = api_client.patch(
        "/studies/study_root/study-arms/StudyArm_000007", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["arm_uid"] == "StudyArm_000007"
    assert res["order"] == 2
    assert res["name"] == "New_Arm_Name_3"
    assert res["short_name"] == "Arm_Short_Name_3"
    assert res["code"] == "Arm_code_3"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"] is None
    assert res["arm_connected_branch_arms"] is None
    assert res["description"] == "desc..."
    assert res["arm_colour"] == "arm_colour..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_3"
    assert res["author_username"] == "unknown-user@example.com"


def test_all_history_of_all_selection_study_arms(api_client):
    response = api_client.get("/studies/study_root/study-arms/audit-trail/")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 1
    assert res[0]["project_number"] is None
    assert res[0]["project_name"] is None
    assert res[0]["study_version"] is None
    assert res[0]["arm_uid"] == "StudyArm_000001"
    assert res[0]["name"] == "New_Arm_Name_1"
    assert res[0]["short_name"] == "Arm_Short_Name_1"
    assert res[0]["code"] == "Arm_code_1"
    assert res[0]["description"] == "desc..."
    assert res[0]["arm_colour"] == "arm_colour..."
    assert res[0]["randomization_group"] == "Randomization_Group_1"
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res[0]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res[0]["arm_type"]["codelists"]) == 1
    assert res[0]["arm_type"]["codelists"][0]["codelist_uid"] == "non_editable_cr"
    assert res[0]["arm_type"]["codelists"][0]["order"] == 3
    assert res[0]["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert res[0]["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    assert (
        res[0]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[0]["arm_type"]["library_name"] == "CDISC"
    assert res[0]["arm_type"]["start_date"]
    assert res[0]["arm_type"]["end_date"] is None
    assert res[0]["arm_type"]["status"] == "Final"
    assert res[0]["arm_type"]["version"] == "1.0"
    assert res[0]["arm_type"]["change_description"] == "Approved version"
    assert res[0]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res[0]["arm_type"]["queried_effective_date"]
    assert res[0]["arm_type"]["date_conflict"] is False
    assert res[0]["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert set(res[0]["changes"]) == set(
        [
            "name",
            "arm_type",
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["order"] == 1
    assert res[1]["project_number"] is None
    assert res[1]["project_name"] is None
    assert res[1]["study_version"] is None
    assert res[1]["arm_uid"] == "StudyArm_000001"
    assert res[1]["name"] == "Arm_Name_1"
    assert res[1]["short_name"] == "Arm_Short_Name_1"
    assert res[1]["code"] == "Arm_code_1"
    assert res[1]["description"] == "desc..."
    assert res[1]["arm_colour"] == "arm_colour..."
    assert res[1]["randomization_group"] == "Randomization_Group_1"
    assert res[1]["number_of_subjects"] == 1
    assert res[1]["arm_type"]["term_uid"] == "term_root_final"
    assert res[1]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res[1]["arm_type"]["codelists"]) == 1
    assert res[1]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res[1]["arm_type"]["codelists"][0]["order"] == 1
    assert res[1]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res[1]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res[1]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[1]["arm_type"]["library_name"] == "Sponsor"
    assert res[1]["arm_type"]["start_date"]
    assert res[1]["arm_type"]["end_date"] is None
    assert res[1]["arm_type"]["status"] == "Final"
    assert res[1]["arm_type"]["version"] == "1.0"
    assert res[1]["arm_type"]["change_description"] == "Approved version"
    assert res[1]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res[1]["arm_type"]["queried_effective_date"]
    assert res[1]["arm_type"]["date_conflict"] is False
    assert res[1]["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"]
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False
    assert res[1]["changes"] == []
    assert res[2]["study_uid"] == "study_root"
    assert res[2]["order"] == 2
    assert res[2]["project_number"] is None
    assert res[2]["project_name"] is None
    assert res[2]["study_version"] is None
    assert res[2]["arm_uid"] == "StudyArm_000004"
    assert res[2]["name"] == "Arm_Name_2"
    assert res[2]["short_name"] == "Arm_Short_Name_2"
    assert res[2]["code"] == "Arm_code_2"
    assert res[2]["description"] == "desc..."
    assert res[2]["arm_colour"] == "arm_colour..."
    assert res[2]["randomization_group"] == "Randomization_Group_2"
    assert res[2]["number_of_subjects"] == 1
    assert res[2]["arm_type"]["term_uid"] == "term_root_final"
    assert res[2]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res[2]["arm_type"]["codelists"]) == 1
    assert res[2]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res[2]["arm_type"]["codelists"][0]["order"] == 1
    assert res[2]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res[2]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res[2]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[2]["arm_type"]["library_name"] == "Sponsor"
    assert res[2]["arm_type"]["start_date"]
    assert res[2]["arm_type"]["end_date"] is None
    assert res[2]["arm_type"]["status"] == "Final"
    assert res[2]["arm_type"]["version"] == "1.0"
    assert res[2]["arm_type"]["change_description"] == "Approved version"
    assert res[2]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res[2]["arm_type"]["queried_effective_date"]
    assert res[2]["arm_type"]["date_conflict"] is False
    assert res[2]["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res[2]["author_username"] == "unknown-user@example.com"
    assert res[2]["end_date"] is None
    assert res[2]["status"] is None
    assert res[2]["change_type"] == "Delete"
    assert res[2]["accepted_version"] is False
    assert set(res[2]["changes"]) == set(
        [
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[3]["study_uid"] == "study_root"
    assert res[3]["order"] == 2
    assert res[3]["project_number"] is None
    assert res[3]["project_name"] is None
    assert res[3]["study_version"] is None
    assert res[3]["arm_uid"] == "StudyArm_000004"
    assert res[3]["name"] == "Arm_Name_2"
    assert res[3]["short_name"] == "Arm_Short_Name_2"
    assert res[3]["code"] == "Arm_code_2"
    assert res[3]["description"] == "desc..."
    assert res[3]["arm_colour"] == "arm_colour..."
    assert res[3]["randomization_group"] == "Randomization_Group_2"
    assert res[3]["number_of_subjects"] == 1
    assert res[3]["arm_type"]["term_uid"] == "term_root_final"
    assert res[3]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res[3]["arm_type"]["codelists"]) == 1
    assert res[3]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res[3]["arm_type"]["codelists"][0]["order"] == 1
    assert res[3]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res[3]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res[3]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[3]["arm_type"]["library_name"] == "Sponsor"
    assert res[3]["arm_type"]["start_date"]
    assert res[3]["arm_type"]["end_date"] is None
    assert res[3]["arm_type"]["status"] == "Final"
    assert res[3]["arm_type"]["version"] == "1.0"
    assert res[3]["arm_type"]["change_description"] == "Approved version"
    assert res[3]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res[3]["arm_type"]["queried_effective_date"]
    assert res[3]["arm_type"]["date_conflict"] is False
    assert res[3]["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res[3]["author_username"] == "unknown-user@example.com"
    assert res[3]["end_date"]
    assert res[3]["status"] is None
    assert res[3]["change_type"] == "Create"
    assert res[3]["accepted_version"] is False
    assert res[3]["changes"] == []
    assert res[4]["study_uid"] == "study_root"
    assert res[4]["order"] == 2
    assert res[4]["project_number"] is None
    assert res[4]["project_name"] is None
    assert res[4]["study_version"] is None
    assert res[4]["arm_uid"] == "StudyArm_000007"
    assert res[4]["name"] == "New_Arm_Name_3"
    assert res[4]["short_name"] == "Arm_Short_Name_3"
    assert res[4]["code"] == "Arm_code_3"
    assert res[4]["description"] == "desc..."
    assert res[4]["arm_colour"] == "arm_colour..."
    assert res[4]["randomization_group"] == "Randomization_Group_3"
    assert res[4]["number_of_subjects"] == 1
    assert res[4]["arm_type"] is None
    assert res[4]["author_username"] == "unknown-user@example.com"
    assert res[4]["end_date"] is None
    assert res[4]["status"] is None
    assert res[4]["change_type"] == "Edit"
    assert res[4]["accepted_version"] is False
    assert set(res[4]["changes"]) == set(
        [
            "arm_type",
            "start_date",
            "end_date",
        ]
    )
    assert res[5]["study_uid"] == "study_root"
    assert res[5]["order"] == 2
    assert res[5]["project_number"] is None
    assert res[5]["project_name"] is None
    assert res[5]["study_version"] is None
    assert res[5]["arm_uid"] == "StudyArm_000007"
    assert res[5]["name"] == "New_Arm_Name_3"
    assert res[5]["short_name"] == "Arm_Short_Name_3"
    assert res[5]["code"] == "Arm_code_3"
    assert res[5]["description"] == "desc..."
    assert res[5]["arm_colour"] == "arm_colour..."
    assert res[5]["randomization_group"] == "Randomization_Group_3"
    assert res[5]["number_of_subjects"] == 1
    assert res[5]["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res[5]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res[5]["arm_type"]["codelists"]) == 1
    assert res[5]["arm_type"]["codelists"][0]["codelist_uid"] == "non_editable_cr"
    assert res[5]["arm_type"]["codelists"][0]["order"] == 3
    assert res[5]["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert res[5]["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    assert (
        res[5]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[5]["arm_type"]["library_name"] == "CDISC"
    assert res[5]["arm_type"]["start_date"]
    assert res[5]["arm_type"]["end_date"] is None
    assert res[5]["arm_type"]["status"] == "Final"
    assert res[5]["arm_type"]["version"] == "1.0"
    assert res[5]["arm_type"]["change_description"] == "Approved version"
    assert res[5]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res[5]["arm_type"]["queried_effective_date"]
    assert res[5]["arm_type"]["date_conflict"] is False
    assert res[5]["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res[5]["author_username"] == "unknown-user@example.com"
    assert res[5]["end_date"]
    assert res[5]["status"] is None
    assert res[5]["change_type"] == "Edit"
    assert res[5]["accepted_version"] is False
    assert set(res[5]["changes"]) == set(
        [
            "name",
            "arm_type",
            "start_date",
            "end_date",
            "change_type",
        ]
    )
    assert res[6]["study_uid"] == "study_root"
    assert res[6]["order"] == 2
    assert res[6]["project_number"] is None
    assert res[6]["project_name"] is None
    assert res[6]["study_version"] is None
    assert res[6]["arm_uid"] == "StudyArm_000007"
    assert res[6]["name"] == "Arm_Name_3"
    assert res[6]["short_name"] == "Arm_Short_Name_3"
    assert res[6]["code"] == "Arm_code_3"
    assert res[6]["description"] == "desc..."
    assert res[6]["arm_colour"] == "arm_colour..."
    assert res[6]["randomization_group"] == "Randomization_Group_3"
    assert res[6]["number_of_subjects"] == 1
    assert res[6]["arm_type"] is None
    assert res[6]["author_username"] == "unknown-user@example.com"
    assert res[6]["end_date"]
    assert res[6]["status"] is None
    assert res[6]["change_type"] == "Create"
    assert res[6]["accepted_version"] is False
    assert res[6]["changes"] == []
