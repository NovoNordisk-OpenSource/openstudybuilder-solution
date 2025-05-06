# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_SUB_GROUPS,
    STARTUP_STUDY_ACTIVITY_CYPHER,
    get_codelist_with_term_cypher,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.selection.activities")
    db.cypher_query(STARTUP_ACTIVITY_GROUPS)
    db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
    db.cypher_query(STARTUP_ACTIVITIES)
    db.cypher_query(
        get_codelist_with_term_cypher(
            "EFFICACY", "Flowchart Group", term_uid="term_efficacy_uid"
        )
    )
    db.cypher_query(STARTUP_STUDY_ACTIVITY_CYPHER)

    yield

    drop_db("old.json.test.study.selection.activities")


def test_getting_empty_list(api_client):
    response = api_client.get("/studies/study_root/study-activities")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_getting_empty_list_for_all_studies(api_client):
    response = api_client.get("/study-activities")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res == {"items": [], "page": 1, "size": 10, "total": 0}


def test_adding_selection(api_client):
    data = {
        "activity_uid": "activity_root1",
        "activity_subgroup_uid": "activity_subgroup_root1",
        "activity_group_uid": "activity_group_root1",
        "soa_group_term_uid": "term_efficacy_uid",
    }
    response = api_client.post("/studies/study_root/study-activities", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 1
    assert res["study_version"]
    assert res["study_activity_uid"] == "StudyActivity_000001"
    assert res["study_activity_subgroup"] == {
        "study_activity_subgroup_uid": "StudyActivitySubGroup_000001",
        "activity_subgroup_uid": "activity_subgroup_root1",
        "activity_subgroup_name": "name1",
        "order": 1,
    }
    assert res["study_activity_group"] == {
        "study_activity_group_uid": "StudyActivityGroup_000001",
        "activity_group_uid": "activity_group_root1",
        "activity_group_name": "name1",
        "order": 1,
    }
    assert res["study_soa_group"] == {
        "study_soa_group_uid": "StudySoAGroup_000001",
        "soa_group_term_uid": "term_efficacy_uid",
        "soa_group_term_name": "EFFICACY",
        "order": 1,
    }
    assert res["show_activity_group_in_protocol_flowchart"] is True
    assert res["show_activity_subgroup_in_protocol_flowchart"] is True
    assert res["show_activity_in_protocol_flowchart"] is False
    assert res["show_soa_group_in_protocol_flowchart"] is False
    assert res["activity"]["uid"] == "activity_root1"
    assert res["activity"]["name"] == "name1"
    assert res["activity"]["name_sentence_case"] == "name1"
    assert res["activity"]["nci_concept_id"] is None
    assert res["activity"]["nci_concept_name"] is None
    assert res["activity"]["synonyms"] == []
    assert res["activity"]["definition"] == "definition1"
    assert res["activity"]["abbreviation"] == "abbv"
    assert res["activity"]["library_name"] == "Sponsor"
    assert res["activity"]["start_date"]
    assert res["activity"]["end_date"] is None
    assert res["activity"]["status"] == "Final"
    assert res["activity"]["version"] == "1.0"
    assert res["activity"]["change_description"] == "Approved version"
    assert res["activity"]["author_username"] == "unknown-user@example.com"
    assert res["activity"]["possible_actions"] == ["inactivate", "new_version"]
    assert len(res["activity"]["activity_groupings"]) == 1
    assert (
        res["activity"]["activity_groupings"][0]["activity_subgroup_uid"]
        == "activity_subgroup_root1"
    )
    assert res["activity"]["activity_groupings"][0]["activity_subgroup_name"] == "name1"
    assert (
        res["activity"]["activity_groupings"][0]["activity_group_uid"]
        == "activity_group_root1"
    )
    assert res["activity"]["activity_groupings"][0]["activity_group_name"] == "name1"
    assert res["activity"]["request_rationale"] is None
    assert res["activity"]["is_request_final"] is False
    assert res["activity"]["is_request_rejected"] is False
    assert res["activity"]["contact_person"] is None
    assert res["activity"]["reason_for_rejecting"] is None
    assert res["activity"]["requester_study_id"] is None
    assert res["activity"]["is_data_collected"] is False
    assert res["activity"]["is_multiple_selection_allowed"] is True
    assert res["activity"]["is_finalized"] is False
    assert res["activity"]["is_used_by_legacy_instances"] is False
    assert res["activity"]["replaced_by_activity"] is None
    assert res["author_username"] == "unknown-user@example.com"
    assert res["latest_activity"] is None
    assert res["accepted_version"] is False


def test_get_all_list_non_empty(api_client):
    response = api_client.get("/studies/study_root/study-activities")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["study_version"]
    assert res["items"][0]["study_activity_uid"] == "StudyActivity_000001"
    assert res["items"][0]["study_activity_subgroup"] == {
        "study_activity_subgroup_uid": "StudyActivitySubGroup_000001",
        "activity_subgroup_uid": "activity_subgroup_root1",
        "activity_subgroup_name": "name1",
        "order": 1,
    }
    assert res["items"][0]["study_activity_group"] == {
        "study_activity_group_uid": "StudyActivityGroup_000001",
        "activity_group_uid": "activity_group_root1",
        "activity_group_name": "name1",
        "order": 1,
    }
    assert res["items"][0]["study_soa_group"] == {
        "study_soa_group_uid": "StudySoAGroup_000001",
        "soa_group_term_uid": "term_efficacy_uid",
        "soa_group_term_name": "EFFICACY",
        "order": 1,
    }
    assert res["items"][0]["show_activity_group_in_protocol_flowchart"] is True
    assert res["items"][0]["show_activity_subgroup_in_protocol_flowchart"] is True
    assert res["items"][0]["show_activity_in_protocol_flowchart"] is False
    assert res["items"][0]["show_soa_group_in_protocol_flowchart"] is False
    assert res["items"][0]["activity"]["uid"] == "activity_root1"
    assert res["items"][0]["activity"]["name"] == "name1"
    assert res["items"][0]["activity"]["name_sentence_case"] == "name1"
    assert res["items"][0]["activity"]["nci_concept_id"] is None
    assert res["items"][0]["activity"]["nci_concept_name"] is None
    assert res["items"][0]["activity"]["synonyms"] == []
    assert res["items"][0]["activity"]["definition"] == "definition1"
    assert res["items"][0]["activity"]["abbreviation"] == "abbv"
    assert res["items"][0]["activity"]["library_name"] == "Sponsor"
    assert res["items"][0]["activity"]["start_date"]
    assert res["items"][0]["activity"]["end_date"] is None
    assert res["items"][0]["activity"]["status"] == "Final"
    assert res["items"][0]["activity"]["version"] == "1.0"
    assert res["items"][0]["activity"]["change_description"] == "Approved version"
    assert res["items"][0]["activity"]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["activity"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert len(res["items"][0]["activity"]["activity_groupings"]) == 1
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_subgroup_uid"]
        == "activity_subgroup_root1"
    )
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_subgroup_name"]
        == "name1"
    )
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_group_uid"]
        == "activity_group_root1"
    )
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_group_name"]
        == "name1"
    )
    assert res["items"][0]["activity"]["request_rationale"] is None
    assert res["items"][0]["activity"]["is_request_final"] is False
    assert res["items"][0]["activity"]["is_request_rejected"] is False
    assert res["items"][0]["activity"]["contact_person"] is None
    assert res["items"][0]["activity"]["reason_for_rejecting"] is None
    assert res["items"][0]["activity"]["requester_study_id"] is None
    assert res["items"][0]["activity"]["is_data_collected"] is False
    assert res["items"][0]["activity"]["is_multiple_selection_allowed"] is True
    assert res["items"][0]["activity"]["is_finalized"] is False
    assert res["items"][0]["activity"]["is_used_by_legacy_instances"] is False
    assert res["items"][0]["activity"]["replaced_by_activity"] is None
    assert res["items"][0]["activity"]
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["latest_activity"] is None
    assert res["items"][0]["accepted_version"] is False


def test_get_all_for_all_studies(api_client):
    response = api_client.get("/study-activities")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["study_version"]
    assert res["items"][0]["study_activity_uid"] == "StudyActivity_000001"
    assert res["items"][0]["study_activity_subgroup"] == {
        "study_activity_subgroup_uid": "StudyActivitySubGroup_000001",
        "activity_subgroup_uid": "activity_subgroup_root1",
        "activity_subgroup_name": "name1",
        "order": 1,
    }
    assert res["items"][0]["study_activity_group"] == {
        "study_activity_group_uid": "StudyActivityGroup_000001",
        "activity_group_uid": "activity_group_root1",
        "activity_group_name": "name1",
        "order": 1,
    }
    assert res["items"][0]["study_soa_group"] == {
        "study_soa_group_uid": "StudySoAGroup_000001",
        "soa_group_term_uid": "term_efficacy_uid",
        "soa_group_term_name": "EFFICACY",
        "order": 1,
    }
    assert res["items"][0]["show_activity_group_in_protocol_flowchart"] is True
    assert res["items"][0]["show_activity_subgroup_in_protocol_flowchart"] is True
    assert res["items"][0]["show_activity_in_protocol_flowchart"] is False
    assert res["items"][0]["show_soa_group_in_protocol_flowchart"] is False
    assert res["items"][0]["activity"]["uid"] == "activity_root1"
    assert res["items"][0]["activity"]["name"] == "name1"
    assert res["items"][0]["activity"]["name_sentence_case"] == "name1"
    assert res["items"][0]["activity"]["nci_concept_id"] is None
    assert res["items"][0]["activity"]["nci_concept_name"] is None
    assert res["items"][0]["activity"]["synonyms"] == []
    assert res["items"][0]["activity"]["definition"] == "definition1"
    assert res["items"][0]["activity"]["abbreviation"] == "abbv"
    assert res["items"][0]["activity"]["library_name"] == "Sponsor"
    assert res["items"][0]["activity"]["start_date"]
    assert res["items"][0]["activity"]["end_date"] is None
    assert res["items"][0]["activity"]["status"] == "Final"
    assert res["items"][0]["activity"]["version"] == "1.0"
    assert res["items"][0]["activity"]["change_description"] == "Approved version"
    assert res["items"][0]["activity"]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["activity"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert len(res["items"][0]["activity"]["activity_groupings"]) == 1
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_subgroup_uid"]
        == "activity_subgroup_root1"
    )
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_subgroup_name"]
        == "name1"
    )
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_group_uid"]
        == "activity_group_root1"
    )
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_group_name"]
        == "name1"
    )
    assert res["items"][0]["activity"]["request_rationale"] is None
    assert res["items"][0]["activity"]["is_request_final"] is False
    assert res["items"][0]["activity"]["is_request_rejected"] is False
    assert res["items"][0]["activity"]["contact_person"] is None
    assert res["items"][0]["activity"]["reason_for_rejecting"] is None
    assert res["items"][0]["activity"]["requester_study_id"] is None
    assert res["items"][0]["activity"]["is_data_collected"] is False
    assert res["items"][0]["activity"]["is_multiple_selection_allowed"] is True
    assert res["items"][0]["activity"]["is_finalized"] is False
    assert res["items"][0]["activity"]["is_used_by_legacy_instances"] is False
    assert res["items"][0]["activity"]["replaced_by_activity"] is None
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["latest_activity"] is None
    assert res["items"][0]["accepted_version"] is False


def test_get_all_for_all_studies_with_filter_on_activity_name(api_client):
    response = api_client.get("/study-activities?activity_names=name1")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["study_version"]
    assert res["items"][0]["study_activity_uid"] == "StudyActivity_000001"
    assert res["items"][0]["study_activity_subgroup"] == {
        "study_activity_subgroup_uid": "StudyActivitySubGroup_000001",
        "activity_subgroup_uid": "activity_subgroup_root1",
        "activity_subgroup_name": "name1",
        "order": 1,
    }
    assert res["items"][0]["study_activity_group"] == {
        "study_activity_group_uid": "StudyActivityGroup_000001",
        "activity_group_uid": "activity_group_root1",
        "activity_group_name": "name1",
        "order": 1,
    }
    assert res["items"][0]["study_soa_group"] == {
        "study_soa_group_uid": "StudySoAGroup_000001",
        "soa_group_term_uid": "term_efficacy_uid",
        "soa_group_term_name": "EFFICACY",
        "order": 1,
    }
    assert res["items"][0]["show_activity_group_in_protocol_flowchart"] is True
    assert res["items"][0]["show_activity_subgroup_in_protocol_flowchart"] is True
    assert res["items"][0]["show_activity_in_protocol_flowchart"] is False
    assert res["items"][0]["show_soa_group_in_protocol_flowchart"] is False
    assert res["items"][0]["activity"]["uid"] == "activity_root1"
    assert res["items"][0]["activity"]["name"] == "name1"
    assert res["items"][0]["activity"]["name_sentence_case"] == "name1"
    assert res["items"][0]["activity"]["nci_concept_id"] is None
    assert res["items"][0]["activity"]["nci_concept_name"] is None
    assert res["items"][0]["activity"]["synonyms"] == []
    assert res["items"][0]["activity"]["definition"] == "definition1"
    assert res["items"][0]["activity"]["abbreviation"] == "abbv"
    assert res["items"][0]["activity"]["library_name"] == "Sponsor"
    assert res["items"][0]["activity"]["start_date"]
    assert res["items"][0]["activity"]["end_date"] is None
    assert res["items"][0]["activity"]["status"] == "Final"
    assert res["items"][0]["activity"]["version"] == "1.0"
    assert res["items"][0]["activity"]["change_description"] == "Approved version"
    assert res["items"][0]["activity"]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["activity"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert len(res["items"][0]["activity"]["activity_groupings"]) == 1
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_subgroup_uid"]
        == "activity_subgroup_root1"
    )
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_subgroup_name"]
        == "name1"
    )
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_group_uid"]
        == "activity_group_root1"
    )
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_group_name"]
        == "name1"
    )
    assert res["items"][0]["activity"]["request_rationale"] is None
    assert res["items"][0]["activity"]["is_request_final"] is False
    assert res["items"][0]["activity"]["is_request_rejected"] is False
    assert res["items"][0]["activity"]["contact_person"] is None
    assert res["items"][0]["activity"]["reason_for_rejecting"] is None
    assert res["items"][0]["activity"]["requester_study_id"] is None
    assert res["items"][0]["activity"]["is_data_collected"] is False
    assert res["items"][0]["activity"]["is_multiple_selection_allowed"] is True
    assert res["items"][0]["activity"]["is_finalized"] is False
    assert res["items"][0]["activity"]["is_used_by_legacy_instances"] is False
    assert res["items"][0]["activity"]["replaced_by_activity"] is None
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["latest_activity"] is None
    assert res["items"][0]["accepted_version"] is False


def test_get_all_for_all_studies_with_filter_on_activity_sub_group_name(api_client):
    response = api_client.get("/study-activities?activity_subgroup_names=name1")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["study_version"]
    assert res["items"][0]["study_activity_uid"] == "StudyActivity_000001"
    assert res["items"][0]["study_activity_subgroup"] == {
        "study_activity_subgroup_uid": "StudyActivitySubGroup_000001",
        "activity_subgroup_uid": "activity_subgroup_root1",
        "activity_subgroup_name": "name1",
        "order": 1,
    }
    assert res["items"][0]["study_activity_group"] == {
        "study_activity_group_uid": "StudyActivityGroup_000001",
        "activity_group_uid": "activity_group_root1",
        "activity_group_name": "name1",
        "order": 1,
    }
    assert res["items"][0]["study_soa_group"] == {
        "study_soa_group_uid": "StudySoAGroup_000001",
        "soa_group_term_uid": "term_efficacy_uid",
        "soa_group_term_name": "EFFICACY",
        "order": 1,
    }
    assert res["items"][0]["show_activity_group_in_protocol_flowchart"] is True
    assert res["items"][0]["show_activity_subgroup_in_protocol_flowchart"] is True
    assert res["items"][0]["show_activity_in_protocol_flowchart"] is False
    assert res["items"][0]["show_soa_group_in_protocol_flowchart"] is False
    assert res["items"][0]["activity"]["uid"] == "activity_root1"
    assert res["items"][0]["activity"]["name"] == "name1"
    assert res["items"][0]["activity"]["name_sentence_case"] == "name1"
    assert res["items"][0]["activity"]["nci_concept_id"] is None
    assert res["items"][0]["activity"]["nci_concept_name"] is None
    assert res["items"][0]["activity"]["synonyms"] == []
    assert res["items"][0]["activity"]["definition"] == "definition1"
    assert res["items"][0]["activity"]["abbreviation"] == "abbv"
    assert res["items"][0]["activity"]["library_name"] == "Sponsor"
    assert res["items"][0]["activity"]["start_date"]
    assert res["items"][0]["activity"]["end_date"] is None
    assert res["items"][0]["activity"]["status"] == "Final"
    assert res["items"][0]["activity"]["version"] == "1.0"
    assert res["items"][0]["activity"]["change_description"] == "Approved version"
    assert res["items"][0]["activity"]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["activity"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert len(res["items"][0]["activity"]["activity_groupings"]) == 1
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_subgroup_uid"]
        == "activity_subgroup_root1"
    )
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_subgroup_name"]
        == "name1"
    )
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_group_uid"]
        == "activity_group_root1"
    )
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_group_name"]
        == "name1"
    )
    assert res["items"][0]["activity"]["request_rationale"] is None
    assert res["items"][0]["activity"]["is_request_final"] is False
    assert res["items"][0]["activity"]["is_request_rejected"] is False
    assert res["items"][0]["activity"]["contact_person"] is None
    assert res["items"][0]["activity"]["reason_for_rejecting"] is None
    assert res["items"][0]["activity"]["requester_study_id"] is None
    assert res["items"][0]["activity"]["is_data_collected"] is False
    assert res["items"][0]["activity"]["is_multiple_selection_allowed"] is True
    assert res["items"][0]["activity"]["is_finalized"] is False
    assert res["items"][0]["activity"]["is_used_by_legacy_instances"] is False
    assert res["items"][0]["activity"]["replaced_by_activity"] is None
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["latest_activity"] is None
    assert res["items"][0]["accepted_version"] is False


def test_get_all_for_all_studies_with_filter_on_activity_group_name(api_client):
    response = api_client.get("/study-activities?activity_group_names=name1")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["study_version"]
    assert res["items"][0]["study_activity_uid"] == "StudyActivity_000001"
    assert res["items"][0]["study_activity_subgroup"] == {
        "study_activity_subgroup_uid": "StudyActivitySubGroup_000001",
        "activity_subgroup_uid": "activity_subgroup_root1",
        "activity_subgroup_name": "name1",
        "order": 1,
    }
    assert res["items"][0]["study_activity_group"] == {
        "study_activity_group_uid": "StudyActivityGroup_000001",
        "activity_group_uid": "activity_group_root1",
        "activity_group_name": "name1",
        "order": 1,
    }
    assert res["items"][0]["study_soa_group"] == {
        "study_soa_group_uid": "StudySoAGroup_000001",
        "soa_group_term_uid": "term_efficacy_uid",
        "soa_group_term_name": "EFFICACY",
        "order": 1,
    }
    assert res["items"][0]["show_activity_group_in_protocol_flowchart"] is True
    assert res["items"][0]["show_activity_subgroup_in_protocol_flowchart"] is True
    assert res["items"][0]["show_activity_in_protocol_flowchart"] is False
    assert res["items"][0]["show_soa_group_in_protocol_flowchart"] is False
    assert res["items"][0]["activity"]["uid"] == "activity_root1"
    assert res["items"][0]["activity"]["name"] == "name1"
    assert res["items"][0]["activity"]["name_sentence_case"] == "name1"
    assert res["items"][0]["activity"]["nci_concept_id"] is None
    assert res["items"][0]["activity"]["nci_concept_name"] is None
    assert res["items"][0]["activity"]["synonyms"] == []
    assert res["items"][0]["activity"]["definition"] == "definition1"
    assert res["items"][0]["activity"]["abbreviation"] == "abbv"
    assert res["items"][0]["activity"]["library_name"] == "Sponsor"
    assert res["items"][0]["activity"]["start_date"]
    assert res["items"][0]["activity"]["end_date"] is None
    assert res["items"][0]["activity"]["status"] == "Final"
    assert res["items"][0]["activity"]["version"] == "1.0"
    assert res["items"][0]["activity"]["change_description"] == "Approved version"
    assert res["items"][0]["activity"]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["activity"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert len(res["items"][0]["activity"]["activity_groupings"]) == 1
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_subgroup_uid"]
        == "activity_subgroup_root1"
    )
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_subgroup_name"]
        == "name1"
    )
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_group_uid"]
        == "activity_group_root1"
    )
    assert (
        res["items"][0]["activity"]["activity_groupings"][0]["activity_group_name"]
        == "name1"
    )
    assert res["items"][0]["activity"]["request_rationale"] is None
    assert res["items"][0]["activity"]["is_request_final"] is False
    assert res["items"][0]["activity"]["is_request_rejected"] is False
    assert res["items"][0]["activity"]["contact_person"] is None
    assert res["items"][0]["activity"]["reason_for_rejecting"] is None
    assert res["items"][0]["activity"]["requester_study_id"] is None
    assert res["items"][0]["activity"]["is_data_collected"] is False
    assert res["items"][0]["activity"]["is_multiple_selection_allowed"] is True
    assert res["items"][0]["activity"]["is_finalized"] is False
    assert res["items"][0]["activity"]["is_used_by_legacy_instances"] is False
    assert res["items"][0]["activity"]["replaced_by_activity"] is None
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["latest_activity"] is None
    assert res["items"][0]["accepted_version"] is False


def test_patch_specific(api_client):
    data = {"soa_group_term_uid": "term_efficacy_uid"}
    response = api_client.patch(
        "/studies/study_root/study-activities/StudyActivity_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 1
    assert res["study_version"]
    assert res["study_activity_uid"] == "StudyActivity_000001"
    assert res["study_activity_subgroup"] == {
        "study_activity_subgroup_uid": "StudyActivitySubGroup_000001",
        "activity_subgroup_uid": "activity_subgroup_root1",
        "activity_subgroup_name": "name1",
        "order": 1,
    }
    assert res["study_activity_group"] == {
        "study_activity_group_uid": "StudyActivityGroup_000001",
        "activity_group_uid": "activity_group_root1",
        "activity_group_name": "name1",
        "order": 1,
    }
    assert res["study_soa_group"] == {
        "study_soa_group_uid": "StudySoAGroup_000001",
        "soa_group_term_uid": "term_efficacy_uid",
        "soa_group_term_name": "EFFICACY",
        "order": 1,
    }
    assert res["show_activity_group_in_protocol_flowchart"] is True
    assert res["show_activity_subgroup_in_protocol_flowchart"] is True
    assert res["show_activity_in_protocol_flowchart"] is False
    assert res["show_soa_group_in_protocol_flowchart"] is False
    assert res["activity"]["uid"] == "activity_root1"
    assert res["activity"]["name"] == "name1"
    assert res["activity"]["name_sentence_case"] == "name1"
    assert res["activity"]["nci_concept_id"] is None
    assert res["activity"]["nci_concept_name"] is None
    assert res["activity"]["synonyms"] == []
    assert res["activity"]["definition"] == "definition1"
    assert res["activity"]["abbreviation"] == "abbv"
    assert res["activity"]["library_name"] == "Sponsor"
    assert res["activity"]["start_date"]
    assert res["activity"]["end_date"] is None
    assert res["activity"]["status"] == "Final"
    assert res["activity"]["version"] == "1.0"
    assert res["activity"]["change_description"] == "Approved version"
    assert res["activity"]["author_username"] == "unknown-user@example.com"
    assert res["activity"]["possible_actions"] == ["inactivate", "new_version"]
    assert len(res["activity"]["activity_groupings"]) == 1
    assert (
        res["activity"]["activity_groupings"][0]["activity_subgroup_uid"]
        == "activity_subgroup_root1"
    )
    assert res["activity"]["activity_groupings"][0]["activity_subgroup_name"] == "name1"
    assert (
        res["activity"]["activity_groupings"][0]["activity_group_uid"]
        == "activity_group_root1"
    )
    assert res["activity"]["activity_groupings"][0]["activity_group_name"] == "name1"
    assert res["activity"]["request_rationale"] is None
    assert res["activity"]["is_request_final"] is False
    assert res["activity"]["is_request_rejected"] is False
    assert res["activity"]["contact_person"] is None
    assert res["activity"]["reason_for_rejecting"] is None
    assert res["activity"]["requester_study_id"] is None
    assert res["activity"]["is_data_collected"] is False
    assert res["activity"]["is_multiple_selection_allowed"] is True
    assert res["activity"]["is_finalized"] is False
    assert res["activity"]["is_used_by_legacy_instances"] is False
    assert res["activity"]["replaced_by_activity"] is None
    assert res["author_username"] == "unknown-user@example.com"
    assert res["latest_activity"] is None
    assert res["accepted_version"] is False


def test_all_history_of_specific_selection(api_client):
    response = api_client.get(
        "/studies/study_root/study-activities/StudyActivity_000001/audit-trail/"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 1
    assert res[0]["study_activity_uid"] == "StudyActivity_000001"
    assert res[0]["study_activity_subgroup"] == {
        "study_activity_subgroup_uid": "StudyActivitySubGroup_000001",
        "activity_subgroup_uid": "activity_subgroup_root1",
        "activity_subgroup_name": "name1",
        "order": 1,
    }
    assert res[0]["study_activity_group"] == {
        "study_activity_group_uid": "StudyActivityGroup_000001",
        "activity_group_uid": "activity_group_root1",
        "activity_group_name": "name1",
        "order": 1,
    }
    assert res[0]["study_soa_group"] == {
        "study_soa_group_uid": "StudySoAGroup_000001",
        "soa_group_term_uid": "term_efficacy_uid",
        "soa_group_term_name": "EFFICACY",
        "order": 1,
    }
    assert res[0]["activity"]["uid"] == "activity_root1"
    assert res[0]["activity"]["name"] == "name1"
    assert res[0]["activity"]["name_sentence_case"] == "name1"
    assert res[0]["activity"]["nci_concept_id"] is None
    assert res[0]["activity"]["nci_concept_name"] is None
    assert res[0]["activity"]["synonyms"] == []
    assert res[0]["activity"]["definition"] == "definition1"
    assert res[0]["activity"]["abbreviation"] == "abbv"
    assert res[0]["activity"]["library_name"] == "Sponsor"
    assert res[0]["activity"]["start_date"]
    assert res[0]["activity"]["end_date"] is None
    assert res[0]["activity"]["status"] == "Final"
    assert res[0]["activity"]["version"] == "1.0"
    assert res[0]["activity"]["change_description"] == "Approved version"
    assert res[0]["activity"]["author_username"] == "unknown-user@example.com"
    assert res[0]["activity"]["possible_actions"] == ["inactivate", "new_version"]
    assert len(res[0]["activity"]["activity_groupings"]) == 1
    assert (
        res[0]["activity"]["activity_groupings"][0]["activity_subgroup_uid"]
        == "activity_subgroup_root1"
    )
    assert (
        res[0]["activity"]["activity_groupings"][0]["activity_subgroup_name"] == "name1"
    )
    assert (
        res[0]["activity"]["activity_groupings"][0]["activity_group_uid"]
        == "activity_group_root1"
    )
    assert res[0]["activity"]["activity_groupings"][0]["activity_group_name"] == "name1"
    assert res[0]["activity"]["request_rationale"] is None
    assert res[0]["activity"]["is_request_final"] is False
    assert res[0]["activity"]["is_request_rejected"] is False
    assert res[0]["activity"]["contact_person"] is None
    assert res[0]["activity"]["reason_for_rejecting"] is None
    assert res[0]["activity"]["requester_study_id"] is None
    assert res[0]["activity"]["is_data_collected"] is False
    assert res[0]["activity"]["is_multiple_selection_allowed"] is True
    assert res[0]["activity"]["is_finalized"] is False
    assert res[0]["activity"]["is_used_by_legacy_instances"] is False
    assert res[0]["activity"]["replaced_by_activity"] is None
    assert res[0]["show_activity_group_in_protocol_flowchart"] is True
    assert res[0]["show_activity_subgroup_in_protocol_flowchart"] is True
    assert res[0]["show_activity_in_protocol_flowchart"] is False
    assert res[0]["show_soa_group_in_protocol_flowchart"] is False
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["order"] == 1
    assert res[1]["study_activity_uid"] == "StudyActivity_000001"
    assert res[1]["study_activity_subgroup"] == {
        "study_activity_subgroup_uid": "StudyActivitySubGroup_000001",
        "activity_subgroup_uid": "activity_subgroup_root1",
        "activity_subgroup_name": "name1",
        "order": 1,
    }
    assert res[1]["study_activity_group"] == {
        "study_activity_group_uid": "StudyActivityGroup_000001",
        "activity_group_uid": "activity_group_root1",
        "activity_group_name": "name1",
        "order": 1,
    }
    assert res[1]["study_soa_group"] == {
        "study_soa_group_uid": "StudySoAGroup_000001",
        "soa_group_term_uid": "term_efficacy_uid",
        "soa_group_term_name": "EFFICACY",
        "order": 1,
    }
    assert res[1]["activity"]["uid"] == "activity_root1"
    assert res[1]["activity"]["name"] == "name1"
    assert res[1]["activity"]["name_sentence_case"] == "name1"
    assert res[1]["activity"]["nci_concept_id"] is None
    assert res[1]["activity"]["nci_concept_name"] is None
    assert res[1]["activity"]["synonyms"] == []
    assert res[1]["activity"]["definition"] == "definition1"
    assert res[1]["activity"]["abbreviation"] == "abbv"
    assert res[1]["activity"]["library_name"] == "Sponsor"
    assert res[1]["activity"]["start_date"]
    assert res[1]["activity"]["end_date"] is None
    assert res[1]["activity"]["status"] == "Final"
    assert res[1]["activity"]["version"] == "1.0"
    assert res[1]["activity"]["change_description"] == "Approved version"
    assert res[1]["activity"]["author_username"] == "unknown-user@example.com"
    assert res[1]["activity"]["possible_actions"] == ["inactivate", "new_version"]
    assert len(res[1]["activity"]["activity_groupings"]) == 1
    assert (
        res[1]["activity"]["activity_groupings"][0]["activity_subgroup_uid"]
        == "activity_subgroup_root1"
    )
    assert (
        res[1]["activity"]["activity_groupings"][0]["activity_subgroup_name"] == "name1"
    )
    assert (
        res[1]["activity"]["activity_groupings"][0]["activity_group_uid"]
        == "activity_group_root1"
    )
    assert res[1]["activity"]["activity_groupings"][0]["activity_group_name"] == "name1"
    assert res[1]["activity"]["request_rationale"] is None
    assert res[1]["activity"]["is_request_final"] is False
    assert res[1]["activity"]["is_request_rejected"] is False
    assert res[1]["activity"]["contact_person"] is None
    assert res[1]["activity"]["reason_for_rejecting"] is None
    assert res[1]["activity"]["requester_study_id"] is None
    assert res[1]["activity"]["is_data_collected"] is False
    assert res[1]["activity"]["is_multiple_selection_allowed"] is True
    assert res[1]["activity"]["is_finalized"] is False
    assert res[1]["activity"]["is_used_by_legacy_instances"] is False
    assert res[1]["activity"]["replaced_by_activity"] is None
    assert res[1]["show_activity_group_in_protocol_flowchart"] is True
    assert res[1]["show_activity_subgroup_in_protocol_flowchart"] is True
    assert res[1]["show_activity_in_protocol_flowchart"] is False
    assert res[1]["show_soa_group_in_protocol_flowchart"] is False
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"]
    assert res[1]["change_type"] == "Create"


def test_adding_selection_2(api_client):
    data = {
        "activity_uid": "activity_root3",
        "activity_subgroup_uid": "activity_subgroup_root3",
        "activity_group_uid": "activity_group_root3",
        "soa_group_term_uid": "term_efficacy_uid",
    }
    response = api_client.post("/studies/study_root/study-activities", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 1
    assert res["study_version"]
    assert res["study_activity_uid"] == "StudyActivity_000002"
    assert res["study_activity_subgroup"] == {
        "study_activity_subgroup_uid": "StudyActivitySubGroup_000002",
        "activity_subgroup_uid": "activity_subgroup_root3",
        "activity_subgroup_name": "name3",
        "order": 1,
    }
    assert res["study_activity_group"] == {
        "study_activity_group_uid": "StudyActivityGroup_000002",
        "activity_group_uid": "activity_group_root3",
        "activity_group_name": "name3",
        "order": 2,
    }
    assert res["study_soa_group"] == {
        "study_soa_group_uid": "StudySoAGroup_000001",
        "soa_group_term_uid": "term_efficacy_uid",
        "soa_group_term_name": "EFFICACY",
        "order": 1,
    }
    assert res["show_activity_group_in_protocol_flowchart"] is True
    assert res["show_activity_subgroup_in_protocol_flowchart"] is True
    assert res["show_activity_in_protocol_flowchart"] is False
    assert res["show_soa_group_in_protocol_flowchart"] is False
    assert res["activity"]["uid"] == "activity_root3"
    assert res["activity"]["name"] == "name3"
    assert res["activity"]["name_sentence_case"] == "name3"
    assert res["activity"]["nci_concept_id"] is None
    assert res["activity"]["nci_concept_name"] is None
    assert res["activity"]["synonyms"] == []
    assert res["activity"]["definition"] == "definition3"
    assert res["activity"]["abbreviation"] == "abbv"
    assert res["activity"]["library_name"] == "Sponsor"
    assert res["activity"]["start_date"]
    assert res["activity"]["end_date"] is None
    assert res["activity"]["status"] == "Final"
    assert res["activity"]["version"] == "1.0"
    assert res["activity"]["change_description"] == "Approved version"
    assert res["activity"]["author_username"] == "unknown-user@example.com"
    assert res["activity"]["possible_actions"] == ["inactivate", "new_version"]
    assert len(res["activity"]["activity_groupings"]) == 1
    assert (
        res["activity"]["activity_groupings"][0]["activity_subgroup_uid"]
        == "activity_subgroup_root3"
    )
    assert res["activity"]["activity_groupings"][0]["activity_subgroup_name"] == "name3"
    assert (
        res["activity"]["activity_groupings"][0]["activity_group_uid"]
        == "activity_group_root3"
    )
    assert res["activity"]["activity_groupings"][0]["activity_group_name"] == "name3"
    assert res["activity"]["request_rationale"] is None
    assert res["activity"]["is_request_final"] is False
    assert res["activity"]["is_request_rejected"] is False
    assert res["activity"]["contact_person"] is None
    assert res["activity"]["reason_for_rejecting"] is None
    assert res["activity"]["requester_study_id"] is None
    assert res["activity"]["is_data_collected"] is False
    assert res["activity"]["is_multiple_selection_allowed"] is True
    assert res["activity"]["is_finalized"] is False
    assert res["activity"]["is_used_by_legacy_instances"] is False
    assert res["activity"]["replaced_by_activity"] is None
    assert res["author_username"] == "unknown-user@example.com"
    assert res["latest_activity"] is None
    assert res["accepted_version"] is False


def test_get_specific(api_client):
    response = api_client.get(
        "/studies/study_root/study-activities/StudyActivity_000001"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 1
    assert res["study_version"]
    assert res["study_activity_uid"] == "StudyActivity_000001"
    assert res["study_activity_subgroup"] == {
        "study_activity_subgroup_uid": "StudyActivitySubGroup_000001",
        "activity_subgroup_uid": "activity_subgroup_root1",
        "activity_subgroup_name": "name1",
        "order": 1,
    }
    assert res["study_activity_group"] == {
        "study_activity_group_uid": "StudyActivityGroup_000001",
        "activity_group_uid": "activity_group_root1",
        "activity_group_name": "name1",
        "order": 1,
    }
    assert res["study_soa_group"] == {
        "study_soa_group_uid": "StudySoAGroup_000001",
        "soa_group_term_uid": "term_efficacy_uid",
        "soa_group_term_name": "EFFICACY",
        "order": 1,
    }
    assert res["show_activity_group_in_protocol_flowchart"] is True
    assert res["show_activity_subgroup_in_protocol_flowchart"] is True
    assert res["show_activity_in_protocol_flowchart"] is False
    assert res["show_soa_group_in_protocol_flowchart"] is False
    assert res["activity"]["uid"] == "activity_root1"
    assert res["activity"]["name"] == "name1"
    assert res["activity"]["name_sentence_case"] == "name1"
    assert res["activity"]["nci_concept_id"] is None
    assert res["activity"]["nci_concept_name"] is None
    assert res["activity"]["synonyms"] == []
    assert res["activity"]["definition"] == "definition1"
    assert res["activity"]["abbreviation"] == "abbv"
    assert res["activity"]["library_name"] == "Sponsor"
    assert res["activity"]["start_date"]
    assert res["activity"]["end_date"] is None
    assert res["activity"]["status"] == "Final"
    assert res["activity"]["version"] == "1.0"
    assert res["activity"]["change_description"] == "Approved version"
    assert res["activity"]["author_username"] == "unknown-user@example.com"
    assert res["activity"]["possible_actions"] == ["inactivate", "new_version"]
    assert len(res["activity"]["activity_groupings"]) == 1
    assert (
        res["activity"]["activity_groupings"][0]["activity_subgroup_uid"]
        == "activity_subgroup_root1"
    )
    assert res["activity"]["activity_groupings"][0]["activity_subgroup_name"] == "name1"
    assert (
        res["activity"]["activity_groupings"][0]["activity_group_uid"]
        == "activity_group_root1"
    )
    assert res["activity"]["activity_groupings"][0]["activity_group_name"] == "name1"
    assert res["activity"]["request_rationale"] is None
    assert res["activity"]["is_request_final"] is False
    assert res["activity"]["is_request_rejected"] is False
    assert res["activity"]["contact_person"] is None
    assert res["activity"]["reason_for_rejecting"] is None
    assert res["activity"]["requester_study_id"] is None
    assert res["activity"]["is_data_collected"] is False
    assert res["activity"]["is_multiple_selection_allowed"] is True
    assert res["activity"]["is_finalized"] is False
    assert res["activity"]["is_used_by_legacy_instances"] is False
    assert res["activity"]["replaced_by_activity"] is None
    assert res["author_username"] == "unknown-user@example.com"
    assert res["latest_activity"] is None
    assert res["accepted_version"] is False


def test_delete_specific(api_client):
    response = api_client.delete(
        "/studies/study_root/study-activities/StudyActivity_000001"
    )
    assert_response_status_code(response, 204)
