# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.domain_repositories.models.syntax import (
    ObjectiveRoot,
    ObjectiveTemplateRoot,
)
from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_STUDY_OBJECTIVE_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

STUDY_OBJECTIVE_UID = None
test_data_dict = {}


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.testsstudy.selection.objectives")
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_OBJECTIVE_CYPHER)
    ObjectiveTemplateRoot.generate_node_uids_if_not_present()
    ObjectiveRoot.generate_node_uids_if_not_present()

    _catalogue_name, library_name = get_catalogue_name_library_name()
    catalogue_name = "SDTM CT"
    # Create a objective level codelist
    objective_level_codelist = create_codelist(
        "Objective Level",
        "CTCodelist_ObjectiveLevel",
        catalogue_name,
        library_name,
        submission_value=settings.study_objective_level_cl_submval,
    )
    test_data_dict["objective_type_codelist"] = objective_level_codelist
    objective_level_term = create_ct_term(
        "Objective Level 1",
        "ObjectiveLevel_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": objective_level_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Objective level 1 submval",
            }
        ],
    )
    test_data_dict["objective_level_term"] = objective_level_term
    yield

    drop_db("old.json.testsstudy.selection.objectives")


def test_getting_empty_list3(api_client):
    response = api_client.get("/studies/study_root/study-objectives")
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["items"] == []
    assert res["total"] == 0


def test_getting_empty_list_for_all_studies1(api_client):
    response = api_client.get("/study-objectives")
    assert_response_status_code(response, 200)


def test_adding_selection6(api_client):
    data = {
        "objective_uid": "Objective_000001",
        "objective_level_uid": "ObjectiveLevel_0001",
    }
    response = api_client.post("/studies/study_root/study-objectives", json=data)
    assert_response_status_code(response, 201)
    res = response.json()

    assert res["study_version"] is not None
    assert res["study_objective_uid"] == "StudyObjective_000001"
    assert res["order"] == 1
    assert res["project_number"] == "123"
    assert res["project_name"] == "Project ABC"
    assert res["accepted_version"] is False
    assert res["study_uid"] == "study_root"
    assert res["objective_level"]["term_uid"] == "ObjectiveLevel_0001"
    assert res["objective_level"]["term_name"] == "Objective Level 1"
    assert res["objective_level"]["codelist_uid"] == "CTCodelist_ObjectiveLevel"
    assert res["objective_level"]["codelist_name"] == "Objective Level"
    assert res["objective_level"]["codelist_submission_value"] == "OBJTLEVL"
    assert res["objective_level"]["order"] == 1
    assert res["objective_level"]["submission_value"] == "Objective level 1 submval"
    assert res["objective_level"]["queried_effective_date"] is None
    assert res["objective_level"]["date_conflict"] is False
    assert res["latest_objective"] is None
    assert res["objective"]["uid"] == "Objective_000001"
    assert res["objective"]["name"] == "objective_1"
    assert res["objective"]["name_plain"] == "objective_1"
    assert res["objective"]["start_date"] is not None
    assert res["objective"]["end_date"] is None
    assert res["objective"]["study_count"] == 0
    assert res["objective"]["status"] == "Final"
    assert res["objective"]["version"] == "1.0"
    assert res["objective"]["change_description"] == "Approved version"
    assert res["objective"]["author_username"] == "unknown-user@example.com"
    assert res["objective"]["possible_actions"] == ["inactivate"]
    assert res["objective"]["template"]["name"] == "objective_1"
    assert res["objective"]["template"]["name_plain"] == "objective_1"
    assert res["objective"]["template"]["uid"] == "ObjectiveTemplate_000001"
    assert res["objective"]["template"]["sequence_id"] == "O1"
    assert res["objective"]["template"]["library_name"] == "Sponsor"
    assert res["objective"]["parameter_terms"] == []
    assert res["objective"]["library"]["name"] == "Sponsor"
    assert res["objective"]["library"]["is_editable"] is True
    assert res["author_username"] == "unknown-user@example.com"
    assert res["endpoint_count"] == 0


def test_get_all_list_non_empty3(api_client):
    response = api_client.get("/studies/study_root/study-objectives")
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["items"][0]["study_version"] is not None
    assert res["items"][0]["study_objective_uid"] == "StudyObjective_000001"
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["project_number"] == "123"
    assert res["items"][0]["project_name"] == "Project ABC"
    assert res["items"][0]["accepted_version"] is False
    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["objective_level"]["term_uid"] == "ObjectiveLevel_0001"
    assert res["items"][0]["objective_level"]["term_name"] == "Objective Level 1"
    assert (
        res["items"][0]["objective_level"]["codelist_uid"]
        == "CTCodelist_ObjectiveLevel"
    )
    assert res["items"][0]["objective_level"]["codelist_name"] == "Objective Level"
    assert res["items"][0]["objective_level"]["codelist_submission_value"] == "OBJTLEVL"
    assert res["items"][0]["objective_level"]["order"] == 1
    assert (
        res["items"][0]["objective_level"]["submission_value"]
        == "Objective level 1 submval"
    )
    assert res["items"][0]["objective_level"]["queried_effective_date"] is None
    assert res["items"][0]["objective_level"]["date_conflict"] is False
    assert res["items"][0]["start_date"] is not None
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["objective"]["uid"] == "Objective_000001"
    assert res["items"][0]["objective"]["name"] == "objective_1"
    assert res["items"][0]["objective"]["name_plain"] == "objective_1"
    assert res["items"][0]["objective"]["start_date"] is not None
    assert res["items"][0]["objective"]["study_count"] == 0
    assert res["items"][0]["objective"]["end_date"] is None
    assert res["items"][0]["objective"]["status"] == "Final"
    assert res["items"][0]["objective"]["version"] == "1.0"
    assert res["items"][0]["objective"]["change_description"] == "Approved version"
    assert res["items"][0]["objective"]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["objective"]["possible_actions"] == ["inactivate"]
    assert res["items"][0]["objective"]["template"]["name"] == "objective_1"
    assert res["items"][0]["objective"]["template"]["name_plain"] == "objective_1"
    assert res["items"][0]["objective"]["template"]["uid"] == "ObjectiveTemplate_000001"
    assert res["items"][0]["objective"]["template"]["sequence_id"] == "O1"
    assert res["items"][0]["objective"]["template"]["library_name"] == "Sponsor"
    assert res["items"][0]["objective"]["parameter_terms"] == []
    assert res["items"][0]["objective"]["library"]["name"] == "Sponsor"
    assert res["items"][0]["objective"]["library"]["is_editable"] is True
    assert res["items"][0]["latest_objective"] is None
    assert res["items"][0]["endpoint_count"] == 0
    assert res["total"] == 0


def test_get_all_for_all_studies1(api_client):
    response = api_client.get("/study-objectives")
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["items"][0]["study_version"] is not None
    assert res["items"][0]["study_objective_uid"] == "StudyObjective_000001"
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["project_number"] == "123"
    assert res["items"][0]["project_name"] == "Project ABC"
    assert res["items"][0]["accepted_version"] is False
    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["objective_level"]["term_uid"] == "ObjectiveLevel_0001"
    assert res["items"][0]["objective_level"]["term_name"] == "Objective Level 1"
    assert (
        res["items"][0]["objective_level"]["codelist_uid"]
        == "CTCodelist_ObjectiveLevel"
    )
    assert res["items"][0]["objective_level"]["codelist_name"] == "Objective Level"
    assert res["items"][0]["objective_level"]["codelist_submission_value"] == "OBJTLEVL"
    assert res["items"][0]["objective_level"]["order"] == 1
    assert (
        res["items"][0]["objective_level"]["submission_value"]
        == "Objective level 1 submval"
    )
    assert res["items"][0]["objective_level"]["queried_effective_date"] is None
    assert res["items"][0]["objective_level"]["date_conflict"] is False
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["objective"]["uid"] == "Objective_000001"
    assert res["items"][0]["objective"]["name"] == "objective_1"
    assert res["items"][0]["objective"]["name_plain"] == "objective_1"
    assert res["items"][0]["objective"]["start_date"] is not None
    assert res["items"][0]["objective"]["study_count"] == 0
    assert res["items"][0]["objective"]["end_date"] is None
    assert res["items"][0]["objective"]["status"] == "Final"
    assert res["items"][0]["objective"]["version"] == "1.0"
    assert res["items"][0]["objective"]["change_description"] == "Approved version"
    assert res["items"][0]["objective"]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["objective"]["possible_actions"] == ["inactivate"]
    assert res["items"][0]["objective"]["template"]["name"] == "objective_1"
    assert res["items"][0]["objective"]["template"]["name_plain"] == "objective_1"
    assert res["items"][0]["objective"]["template"]["uid"] == "ObjectiveTemplate_000001"
    assert res["items"][0]["objective"]["template"]["sequence_id"] == "O1"
    assert res["items"][0]["objective"]["template"]["library_name"] == "Sponsor"
    assert res["items"][0]["objective"]["parameter_terms"] == []
    assert res["items"][0]["objective"]["library"]["name"] == "Sponsor"
    assert res["items"][0]["objective"]["library"]["is_editable"] is True
    assert res["items"][0]["latest_objective"] is None
    assert res["items"][0]["endpoint_count"] == 0


def test_add_selection_2_no_objective_level_set(api_client):
    data = {"objective_uid": "Objective_000002"}
    response = api_client.post("/studies/study_root/study-objectives", json=data)
    assert_response_status_code(response, 201)
    res = response.json()

    global STUDY_OBJECTIVE_UID
    STUDY_OBJECTIVE_UID = res["study_objective_uid"]
    assert res["study_version"] is not None
    assert res["study_objective_uid"] == "StudyObjective_000002"
    assert res["order"] == 2
    assert res["project_number"] == "123"
    assert res["project_name"] == "Project ABC"
    assert res["accepted_version"] is False
    assert res["study_uid"] == "study_root"
    assert res["objective_level"] is None
    assert res["latest_objective"] is None
    assert res["objective"]["uid"] == "Objective_000002"
    assert res["objective"]["name"] == "objective_2"
    assert res["objective"]["name_plain"] == "objective_2"
    assert res["objective"]["start_date"] is not None
    assert res["objective"]["end_date"] is None
    assert res["objective"]["status"] == "Final"
    assert res["objective"]["study_count"] == 0
    assert res["objective"]["version"] == "1.0"
    assert res["objective"]["change_description"] == "Approved version"
    assert res["objective"]["author_username"] == "unknown-user@example.com"
    assert res["objective"]["possible_actions"] == ["inactivate"]
    assert res["objective"]["template"]["name"] == "objective_2"
    assert res["objective"]["template"]["name_plain"] == "objective_2"
    assert res["objective"]["template"]["uid"] == "ObjectiveTemplate_0000022"
    assert res["objective"]["template"]["sequence_id"] == "O22"
    assert res["objective"]["template"]["library_name"] == "Sponsor"
    assert res["objective"]["parameter_terms"] == []
    assert res["objective"]["library"]["name"] == "Sponsor"
    assert res["objective"]["library"]["is_editable"] is True
    assert res["author_username"] == "unknown-user@example.com"
    assert res["endpoint_count"] == 0


def test_check_list_has_two(api_client):
    response = api_client.get("/studies/study_root/study-objectives")
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["items"][0]["study_version"] is not None
    assert res["items"][0]["study_objective_uid"] == "StudyObjective_000001"
    assert res["items"][0]["order"] == 1
    assert res["items"][0]["project_number"] == "123"
    assert res["items"][0]["project_name"] == "Project ABC"
    assert res["items"][0]["accepted_version"] is False
    assert res["items"][0]["study_uid"] == "study_root"
    assert res["items"][0]["objective_level"]["term_uid"] == "ObjectiveLevel_0001"
    assert res["items"][0]["objective_level"]["term_name"] == "Objective Level 1"
    assert (
        res["items"][0]["objective_level"]["codelist_uid"]
        == "CTCodelist_ObjectiveLevel"
    )
    assert res["items"][0]["objective_level"]["codelist_name"] == "Objective Level"
    assert res["items"][0]["objective_level"]["codelist_submission_value"] == "OBJTLEVL"
    assert res["items"][0]["objective_level"]["order"] == 1
    assert (
        res["items"][0]["objective_level"]["submission_value"]
        == "Objective level 1 submval"
    )
    assert res["items"][0]["objective_level"]["queried_effective_date"] is None
    assert res["items"][0]["objective_level"]["date_conflict"] is False
    assert res["items"][0]["objective"]["uid"] == "Objective_000001"
    assert res["items"][0]["objective"]["name"] == "objective_1"
    assert res["items"][0]["objective"]["name_plain"] == "objective_1"
    assert res["items"][0]["objective"]["start_date"] is not None
    assert res["items"][0]["objective"]["end_date"] is None
    assert res["items"][0]["objective"]["status"] == "Final"
    assert res["items"][0]["objective"]["study_count"] == 0
    assert res["items"][0]["objective"]["version"] == "1.0"
    assert res["items"][0]["objective"]["change_description"] == "Approved version"
    assert res["items"][0]["objective"]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["objective"]["possible_actions"] == ["inactivate"]
    assert res["items"][0]["objective"]["template"]["name"] == "objective_1"
    assert res["items"][0]["objective"]["template"]["name_plain"] == "objective_1"
    assert res["items"][0]["objective"]["template"]["uid"] == "ObjectiveTemplate_000001"
    assert res["items"][0]["objective"]["template"]["sequence_id"] == "O1"
    assert res["items"][0]["objective"]["template"]["library_name"] == "Sponsor"
    assert res["items"][0]["objective"]["parameter_terms"] == []
    assert res["items"][0]["objective"]["library"]["name"] == "Sponsor"
    assert res["items"][0]["objective"]["library"]["is_editable"] is True
    assert res["items"][0]["start_date"] is not None
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["latest_objective"] is None
    assert res["items"][0]["endpoint_count"] == 0
    assert res["items"][1]["study_version"] is not None
    assert res["items"][1]["study_objective_uid"] == "StudyObjective_000002"
    assert res["items"][1]["order"] == 2
    assert res["items"][1]["project_number"] == "123"
    assert res["items"][1]["project_name"] == "Project ABC"
    assert res["items"][1]["accepted_version"] is False
    assert res["items"][1]["study_uid"] == "study_root"
    assert res["items"][1]["objective_level"] is None
    assert res["items"][1]["latest_objective"] is None
    assert res["items"][1]["objective"]["uid"] == "Objective_000002"
    assert res["items"][1]["objective"]["name"] == "objective_2"
    assert res["items"][1]["objective"]["name_plain"] == "objective_2"
    assert res["items"][1]["objective"]["start_date"] is not None
    assert res["items"][1]["objective"]["end_date"] is None
    assert res["items"][1]["objective"]["status"] == "Final"
    assert res["items"][1]["objective"]["study_count"] == 0
    assert res["items"][1]["objective"]["version"] == "1.0"
    assert res["items"][1]["objective"]["change_description"] == "Approved version"
    assert res["items"][1]["objective"]["author_username"] == "unknown-user@example.com"
    assert res["items"][1]["objective"]["possible_actions"] == ["inactivate"]
    assert (
        res["items"][1]["objective"]["template"]["uid"] == "ObjectiveTemplate_0000022"
    )
    assert res["items"][1]["objective"]["template"]["name_plain"] == "objective_2"
    assert res["items"][1]["objective"]["template"]["name"] == "objective_2"
    assert res["items"][1]["objective"]["template"]["sequence_id"] == "O22"
    assert res["items"][1]["objective"]["template"]["library_name"] == "Sponsor"
    assert res["items"][1]["objective"]["parameter_terms"] == []
    assert res["items"][1]["objective"]["library"]["name"] == "Sponsor"
    assert res["items"][1]["objective"]["library"]["is_editable"] is True
    assert res["items"][1]["start_date"] is not None
    assert res["items"][1]["author_username"] == "unknown-user@example.com"
    assert res["items"][1]["endpoint_count"] == 0
    assert res["total"] == 0


def test_get_specific5(api_client):
    response = api_client.get(
        f"/studies/study_root/study-objectives/{STUDY_OBJECTIVE_UID}"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["study_version"] is not None
    assert res["study_objective_uid"] == "StudyObjective_000002"
    assert res["order"] == 2
    assert res["project_number"] == "123"
    assert res["project_name"] == "Project ABC"
    assert res["accepted_version"] is False
    assert res["study_uid"] == "study_root"
    assert res["objective_level"] is None
    assert res["latest_objective"] is None
    assert res["objective"]["uid"] == "Objective_000002"
    assert res["objective"]["name"] == "objective_2"
    assert res["objective"]["name_plain"] == "objective_2"
    assert res["objective"]["start_date"] is not None
    assert res["objective"]["end_date"] is None
    assert res["objective"]["status"] == "Final"
    assert res["objective"]["study_count"] == 0
    assert res["objective"]["version"] == "1.0"
    assert res["objective"]["change_description"] == "Approved version"
    assert res["objective"]["author_username"] == "unknown-user@example.com"
    assert res["objective"]["possible_actions"] == ["inactivate"]
    assert res["objective"]["template"]["name"] == "objective_2"
    assert res["objective"]["template"]["name_plain"] == "objective_2"
    assert res["objective"]["template"]["uid"] == "ObjectiveTemplate_0000022"
    assert res["objective"]["template"]["sequence_id"] == "O22"
    assert res["objective"]["template"]["library_name"] == "Sponsor"
    assert res["objective"]["parameter_terms"] == []
    assert res["objective"]["library"]["name"] == "Sponsor"
    assert res["objective"]["library"]["is_editable"] is True
    assert res["author_username"] == "unknown-user@example.com"
    assert res["endpoint_count"] == 0


def test_reorder_specific4(api_client):
    data = {"new_order": 1}
    response = api_client.patch(
        f"/studies/study_root/study-objectives/{STUDY_OBJECTIVE_UID}/order", json=data
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["study_version"] is not None
    assert res["study_objective_uid"] == "StudyObjective_000002"
    assert res["order"] == 1
    assert res["project_number"] == "123"
    assert res["project_name"] == "Project ABC"
    assert res["accepted_version"] is False
    assert res["study_uid"] == "study_root"
    assert res["objective_level"] is None
    assert res["objective"]["uid"] == "Objective_000002"
    assert res["objective"]["name"] == "objective_2"
    assert res["objective"]["name_plain"] == "objective_2"
    assert res["objective"]["start_date"] is not None
    assert res["objective"]["end_date"] is None
    assert res["objective"]["status"] == "Final"
    assert res["objective"]["study_count"] == 0
    assert res["objective"]["version"] == "1.0"
    assert res["objective"]["change_description"] == "Approved version"
    assert res["objective"]["author_username"] == "unknown-user@example.com"
    assert res["objective"]["possible_actions"] == ["inactivate"]
    assert res["objective"]["template"]["name"] == "objective_2"
    assert res["objective"]["template"]["name_plain"] == "objective_2"
    assert res["objective"]["template"]["uid"] == "ObjectiveTemplate_0000022"
    assert res["objective"]["template"]["sequence_id"] == "O22"
    assert res["objective"]["template"]["library_name"] == "Sponsor"
    assert res["objective"]["parameter_terms"] == []
    assert res["objective"]["library"]["name"] == "Sponsor"
    assert res["objective"]["library"]["is_editable"] is True
    assert res["author_username"] == "unknown-user@example.com"
    assert res["latest_objective"] is None
    assert res["endpoint_count"] == 0


def test_patch_specific(api_client):
    data = {"objective_level": None}
    response = api_client.patch(
        f"/studies/study_root/study-objectives/{STUDY_OBJECTIVE_UID}", json=data
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["study_version"] is not None
    assert res["study_objective_uid"] == "StudyObjective_000002"
    assert res["order"] == 2
    assert res["project_number"] == "123"
    assert res["project_name"] == "Project ABC"
    assert res["accepted_version"] is False
    assert res["study_uid"] == "study_root"
    assert res["objective_level"] is None
    assert res["latest_objective"] is None
    assert res["objective"]["uid"] == "Objective_000002"
    assert res["objective"]["name"] == "objective_2"
    assert res["objective"]["name_plain"] == "objective_2"
    assert res["objective"]["start_date"] is not None
    assert res["objective"]["end_date"] is None
    assert res["objective"]["status"] == "Final"
    assert res["objective"]["study_count"] == 0
    assert res["objective"]["version"] == "1.0"
    assert res["objective"]["change_description"] == "Approved version"
    assert res["objective"]["author_username"] == "unknown-user@example.com"
    assert res["objective"]["possible_actions"] == ["inactivate"]
    assert res["objective"]["template"]["name"] == "objective_2"
    assert res["objective"]["template"]["name_plain"] == "objective_2"
    assert res["objective"]["template"]["uid"] == "ObjectiveTemplate_0000022"
    assert res["objective"]["template"]["sequence_id"] == "O22"
    assert res["objective"]["template"]["library_name"] == "Sponsor"
    assert res["objective"]["parameter_terms"] == []
    assert res["objective"]["library"]["name"] == "Sponsor"
    assert res["objective"]["library"]["is_editable"] is True
    assert res["author_username"] == "unknown-user@example.com"
    assert res["endpoint_count"] == 0


def test_get_history_of_all_selections1(
    api_client,
):  # pylint:disable=too-many-statements
    response = api_client.get("/studies/study_root/study-objectives/audit-trail")
    assert_response_status_code(response, 200)
    res = response.json()

    assert res[0]["order"] == 2
    assert res[0]["study_uid"] == "study_root"
    assert res[0]["study_objective_uid"] == "StudyObjective_000001"
    assert res[0]["objective_level"]["term_uid"] == "ObjectiveLevel_0001"
    assert res[0]["objective_level"]["term_name"] == "Objective Level 1"
    assert res[0]["objective_level"]["codelist_uid"] == "CTCodelist_ObjectiveLevel"
    assert res[0]["objective_level"]["codelist_name"] == "Objective Level"
    assert res[0]["objective_level"]["codelist_submission_value"] == "OBJTLEVL"
    assert res[0]["objective_level"]["order"] == 1
    assert res[0]["objective_level"]["submission_value"] == "Objective level 1 submval"
    assert res[0]["objective_level"]["queried_effective_date"] is None
    assert res[0]["objective_level"]["date_conflict"] is False
    assert res[0]["objective"]["uid"] == "Objective_000001"
    assert res[0]["objective"]["name"] == "objective_1"
    assert res[0]["objective"]["name_plain"] == "objective_1"
    assert res[0]["objective"]["start_date"] is not None
    assert res[0]["objective"]["end_date"] is None
    assert res[0]["objective"]["status"] == "Final"
    assert res[0]["objective"]["study_count"] == 0
    assert res[0]["objective"]["version"] == "1.0"
    assert res[0]["objective"]["change_description"] == "Approved version"
    assert res[0]["objective"]["author_username"] == "unknown-user@example.com"
    assert res[0]["objective"]["possible_actions"] == ["inactivate"]
    assert res[0]["objective"]["template"]["name"] == "objective_1"
    assert res[0]["objective"]["template"]["name_plain"] == "objective_1"
    assert res[0]["objective"]["template"]["uid"] == "ObjectiveTemplate_000001"
    assert res[0]["objective"]["template"]["sequence_id"] == "O1"
    assert res[0]["objective"]["template"]["library_name"] == "Sponsor"
    assert res[0]["objective"]["parameter_terms"] == []
    assert res[0]["objective"]["library"]["name"] == "Sponsor"
    assert res[0]["objective"]["library"]["is_editable"] is True
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[1]["order"] == 1
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["study_objective_uid"] == "StudyObjective_000001"
    assert res[1]["objective_level"]["term_uid"] == "ObjectiveLevel_0001"
    assert res[1]["objective_level"]["term_name"] == "Objective Level 1"
    assert res[1]["objective_level"]["codelist_uid"] == "CTCodelist_ObjectiveLevel"
    assert res[1]["objective_level"]["codelist_name"] == "Objective Level"
    assert res[1]["objective_level"]["codelist_submission_value"] == "OBJTLEVL"
    assert res[1]["objective_level"]["order"] == 1
    assert res[1]["objective_level"]["submission_value"] == "Objective level 1 submval"
    assert res[1]["objective_level"]["queried_effective_date"] is None
    assert res[1]["objective_level"]["date_conflict"] is False
    assert res[1]["objective"]["uid"] == "Objective_000001"
    assert res[1]["objective"]["name"] == "objective_1"
    assert res[1]["objective"]["name_plain"] == "objective_1"
    assert res[1]["objective"]["start_date"] is not None
    assert res[1]["objective"]["end_date"] is None
    assert res[1]["objective"]["status"] == "Final"
    assert res[1]["objective"]["study_count"] == 0
    assert res[1]["objective"]["version"] == "1.0"
    assert res[1]["objective"]["change_description"] == "Approved version"
    assert res[1]["objective"]["author_username"] == "unknown-user@example.com"
    assert res[1]["objective"]["possible_actions"] == ["inactivate"]
    assert res[1]["objective"]["template"]["name"] == "objective_1"
    assert res[1]["objective"]["template"]["name_plain"] == "objective_1"
    assert res[1]["objective"]["template"]["uid"] == "ObjectiveTemplate_000001"
    assert res[1]["objective"]["template"]["sequence_id"] == "O1"
    assert res[1]["objective"]["template"]["library_name"] == "Sponsor"
    assert res[1]["objective"]["parameter_terms"] == []
    assert res[1]["objective"]["library"]["name"] == "Sponsor"
    assert res[1]["objective"]["library"]["is_editable"] is True
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"] is not None
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[2]["order"] == 2
    assert res[2]["study_uid"] == "study_root"
    assert res[2]["study_objective_uid"] == "StudyObjective_000002"
    assert res[2]["objective_level"] is None
    assert res[2]["objective"]["uid"] == "Objective_000002"
    assert res[2]["objective"]["name"] == "objective_2"
    assert res[2]["objective"]["name_plain"] == "objective_2"
    assert res[2]["objective"]["start_date"] is not None
    assert res[2]["objective"]["end_date"] is None
    assert res[2]["objective"]["status"] == "Final"
    assert res[2]["objective"]["study_count"] == 0
    assert res[2]["objective"]["version"] == "1.0"
    assert res[2]["objective"]["change_description"] == "Approved version"
    assert res[2]["objective"]["author_username"] == "unknown-user@example.com"
    assert res[2]["objective"]["possible_actions"] == ["inactivate"]
    assert res[2]["objective"]["template"]["name"] == "objective_2"
    assert res[2]["objective"]["template"]["name_plain"] == "objective_2"
    assert res[2]["objective"]["template"]["uid"] == "ObjectiveTemplate_0000022"
    assert res[2]["objective"]["template"]["sequence_id"] == "O22"
    assert res[2]["objective"]["template"]["library_name"] == "Sponsor"
    assert res[2]["objective"]["parameter_terms"] == []
    assert res[2]["objective"]["library"]["name"] == "Sponsor"
    assert res[2]["objective"]["library"]["is_editable"] is True
    assert res[2]["author_username"] == "unknown-user@example.com"
    assert res[2]["end_date"] is None
    assert res[2]["status"] is None
    assert res[2]["change_type"] == "Edit"
    assert res[3]["order"] == 1
    assert res[3]["study_uid"] == "study_root"
    assert res[3]["study_objective_uid"] == "StudyObjective_000002"
    assert res[3]["objective_level"] is None
    assert res[3]["objective"]["uid"] == "Objective_000002"
    assert res[3]["objective"]["name"] == "objective_2"
    assert res[3]["objective"]["name_plain"] == "objective_2"
    assert res[3]["objective"]["start_date"] is not None
    assert res[3]["objective"]["end_date"] is None
    assert res[3]["objective"]["status"] == "Final"
    assert res[3]["objective"]["study_count"] == 0
    assert res[3]["objective"]["version"] == "1.0"
    assert res[3]["objective"]["change_description"] == "Approved version"
    assert res[3]["objective"]["author_username"] == "unknown-user@example.com"
    assert res[3]["objective"]["possible_actions"] == ["inactivate"]
    assert res[3]["objective"]["template"]["name"] == "objective_2"
    assert res[3]["objective"]["template"]["name_plain"] == "objective_2"
    assert res[3]["objective"]["template"]["uid"] == "ObjectiveTemplate_0000022"
    assert res[3]["objective"]["template"]["sequence_id"] == "O22"
    assert res[3]["objective"]["template"]["library_name"] == "Sponsor"
    assert res[3]["objective"]["parameter_terms"] == []
    assert res[3]["objective"]["library"]["name"] == "Sponsor"
    assert res[3]["objective"]["library"]["is_editable"] is True
    assert res[3]["author_username"] == "unknown-user@example.com"
    assert res[3]["end_date"] is not None
    assert res[3]["status"] is None
    assert res[3]["change_type"] == "Edit"
    assert res[4]["order"] == 2
    assert res[4]["study_uid"] == "study_root"
    assert res[4]["study_objective_uid"] == "StudyObjective_000002"
    assert res[4]["objective_level"] is None
    assert res[4]["objective"]["uid"] == "Objective_000002"
    assert res[4]["objective"]["name"] == "objective_2"
    assert res[4]["objective"]["name_plain"] == "objective_2"
    assert res[4]["objective"]["start_date"] is not None
    assert res[4]["objective"]["end_date"] is None
    assert res[4]["objective"]["status"] == "Final"
    assert res[4]["objective"]["study_count"] == 0
    assert res[4]["objective"]["version"] == "1.0"
    assert res[4]["objective"]["change_description"] == "Approved version"
    assert res[4]["objective"]["author_username"] == "unknown-user@example.com"
    assert res[4]["objective"]["possible_actions"] == ["inactivate"]
    assert res[4]["objective"]["template"]["name"] == "objective_2"
    assert res[4]["objective"]["template"]["name_plain"] == "objective_2"
    assert res[4]["objective"]["template"]["uid"] == "ObjectiveTemplate_0000022"
    assert res[4]["objective"]["template"]["sequence_id"] == "O22"
    assert res[4]["objective"]["template"]["library_name"] == "Sponsor"
    assert res[4]["objective"]["parameter_terms"] == []
    assert res[4]["objective"]["library"]["name"] == "Sponsor"
    assert res[4]["objective"]["library"]["is_editable"] is True
    assert res[4]["author_username"] == "unknown-user@example.com"
    assert res[4]["end_date"] is not None
    assert res[4]["status"] is None
    assert res[4]["change_type"] == "Create"


def test_all_history_of_specific_selection4(api_client):
    response = api_client.get(
        f"/studies/study_root/study-objectives/{STUDY_OBJECTIVE_UID}/audit-trail"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert res[0]["order"] == 2
    assert res[0]["study_uid"] == "study_root"
    assert res[0]["study_objective_uid"] == "StudyObjective_000002"
    assert res[0]["objective_level"] is None
    assert res[0]["objective"]["uid"] == "Objective_000002"
    assert res[0]["objective"]["name"] == "objective_2"
    assert res[0]["objective"]["name_plain"] == "objective_2"
    assert res[0]["objective"]["start_date"] is not None
    assert res[0]["objective"]["end_date"] is None
    assert res[0]["objective"]["status"] == "Final"
    assert res[0]["objective"]["study_count"] == 0
    assert res[0]["objective"]["version"] == "1.0"
    assert res[0]["objective"]["change_description"] == "Approved version"
    assert res[0]["objective"]["author_username"] == "unknown-user@example.com"
    assert res[0]["objective"]["possible_actions"] == ["inactivate"]
    assert res[0]["objective"]["template"]["name"] == "objective_2"
    assert res[0]["objective"]["template"]["name_plain"] == "objective_2"
    assert res[0]["objective"]["template"]["uid"] == "ObjectiveTemplate_0000022"
    assert res[0]["objective"]["template"]["sequence_id"] == "O22"
    assert res[0]["objective"]["template"]["library_name"] == "Sponsor"
    assert res[0]["objective"]["parameter_terms"] == []
    assert res[0]["objective"]["library"]["name"] == "Sponsor"
    assert res[0]["objective"]["library"]["is_editable"] is True
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[1]["order"] == 1
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["study_objective_uid"] == "StudyObjective_000002"
    assert res[1]["objective_level"] is None
    assert res[1]["objective"]["uid"] == "Objective_000002"
    assert res[1]["objective"]["name"] == "objective_2"
    assert res[1]["objective"]["name_plain"] == "objective_2"
    assert res[1]["objective"]["start_date"] is not None
    assert res[1]["objective"]["end_date"] is None
    assert res[1]["objective"]["status"] == "Final"
    assert res[1]["objective"]["study_count"] == 0
    assert res[1]["objective"]["version"] == "1.0"
    assert res[1]["objective"]["change_description"] == "Approved version"
    assert res[1]["objective"]["author_username"] == "unknown-user@example.com"
    assert res[1]["objective"]["possible_actions"] == ["inactivate"]
    assert res[1]["objective"]["template"]["name"] == "objective_2"
    assert res[1]["objective"]["template"]["name_plain"] == "objective_2"
    assert res[1]["objective"]["template"]["uid"] == "ObjectiveTemplate_0000022"
    assert res[1]["objective"]["template"]["sequence_id"] == "O22"
    assert res[1]["objective"]["template"]["library_name"] == "Sponsor"
    assert res[1]["objective"]["parameter_terms"] == []
    assert res[1]["objective"]["library"]["name"] == "Sponsor"
    assert res[1]["objective"]["library"]["is_editable"] is True
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"] is not None
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Edit"
    assert res[2]["order"] == 2
    assert res[2]["study_uid"] == "study_root"
    assert res[2]["study_objective_uid"] == "StudyObjective_000002"
    assert res[2]["objective_level"] is None
    assert res[2]["objective"]["uid"] == "Objective_000002"
    assert res[2]["objective"]["name"] == "objective_2"
    assert res[2]["objective"]["name_plain"] == "objective_2"
    assert res[2]["objective"]["start_date"] is not None
    assert res[2]["objective"]["end_date"] is None
    assert res[2]["objective"]["status"] == "Final"
    assert res[2]["objective"]["study_count"] == 0
    assert res[2]["objective"]["version"] == "1.0"
    assert res[2]["objective"]["change_description"] == "Approved version"
    assert res[2]["objective"]["author_username"] == "unknown-user@example.com"
    assert res[2]["objective"]["possible_actions"] == ["inactivate"]
    assert res[2]["objective"]["template"]["name"] == "objective_2"
    assert res[2]["objective"]["template"]["name_plain"] == "objective_2"
    assert res[2]["objective"]["template"]["uid"] == "ObjectiveTemplate_0000022"
    assert res[2]["objective"]["template"]["sequence_id"] == "O22"
    assert res[2]["objective"]["template"]["library_name"] == "Sponsor"
    assert res[2]["objective"]["parameter_terms"] == []
    assert res[2]["objective"]["library"]["name"] == "Sponsor"
    assert res[2]["objective"]["library"]["is_editable"] is True
    assert res[2]["author_username"] == "unknown-user@example.com"
    assert res[2]["end_date"] is not None
    assert res[2]["status"] is None
    assert res[2]["change_type"] == "Create"


def test_patch_specific_replace(api_client):
    data = {"objective_uid": "Objective_000003"}
    response = api_client.patch(
        f"/studies/study_root/study-objectives/{STUDY_OBJECTIVE_UID}", json=data
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["study_version"] is not None
    assert res["study_objective_uid"] == "StudyObjective_000002"
    assert res["accepted_version"] is False
    assert res["order"] == 2
    assert res["project_number"] == "123"
    assert res["project_name"] == "Project ABC"
    assert res["study_uid"] == "study_root"
    assert res["objective_level"] is None
    assert res["author_username"] == "unknown-user@example.com"
    assert res["latest_objective"] is None
    assert res["objective"]["uid"] == "Objective_000003"
    assert res["objective"]["name"] == "objective_3"
    assert res["objective"]["name_plain"] == "objective_3"
    assert res["objective"]["start_date"] is not None
    assert res["objective"]["end_date"] is None
    assert res["objective"]["status"] == "Final"
    assert res["objective"]["study_count"] == 0
    assert res["objective"]["version"] == "1.0"
    assert res["objective"]["change_description"] == "Approved version"
    assert res["objective"]["author_username"] == "unknown-user@example.com"
    assert res["objective"]["possible_actions"] == ["inactivate"]
    assert res["objective"]["template"]["name"] == "objective_3"
    assert res["objective"]["template"]["name_plain"] == "objective_3"
    assert res["objective"]["template"]["uid"] == "ObjectiveTemplate_000003"
    assert res["objective"]["template"]["sequence_id"] == "O3"
    assert res["objective"]["template"]["library_name"] == "Sponsor"
    assert res["objective"]["parameter_terms"] == []
    assert res["objective"]["library"]["name"] == "Sponsor"
    assert res["objective"]["library"]["is_editable"] is True
    assert res["endpoint_count"] == 0


def test_previewing_selection_create1(api_client):
    data = {
        "objective_data": {
            "library_name": "Sponsor",
            "name": "objective_4",
            "objective_template_uid": "ObjectiveTemplate_000004",
            "parameter_terms": [],
        },
        "objective_level_uid": "ObjectiveLevel_0001",
    }
    response = api_client.post(
        "/studies/study_root/study-objectives/preview", json=data
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["study_version"] is not None
    assert res["study_objective_uid"] == "preview"
    assert res["accepted_version"] is False
    assert res["order"] == 3
    assert res["project_number"] == "123"
    assert res["project_name"] == "Project ABC"
    assert res["study_uid"] == "study_root"
    assert res["objective_level"] is not None
    assert res["author_username"] == "unknown-user@example.com"
    assert res["latest_objective"] is None
    assert res["objective"]["uid"] == "preview"
    assert res["objective"]["name"] == "objective_4"
    assert res["objective"]["name_plain"] == "objective_4"
    assert res["objective"]["start_date"] is not None
    assert res["objective"]["end_date"] is None
    assert res["objective"]["status"] == "Final"
    assert res["objective"]["study_count"] == 0
    assert res["objective"]["version"] == "1.0"
    assert res["objective"]["change_description"] == "Approved version"
    assert res["objective"]["author_username"] == "unknown-user@example.com"
    assert res["objective"]["possible_actions"] == ["inactivate"]
    assert res["objective"]["template"]["name"] == "objective_4"
    assert res["objective"]["template"]["name_plain"] == "objective_4"
    assert res["objective"]["template"]["uid"] == "ObjectiveTemplate_000004"
    assert res["objective"]["template"]["sequence_id"] == "O4"
    assert res["objective"]["template"]["library_name"] == "Sponsor"
    assert res["objective"]["parameter_terms"] == []
    assert res["objective"]["library"]["name"] == "Sponsor"
    assert res["objective"]["library"]["is_editable"] is True
    assert res["endpoint_count"] == 0


def test_adding_selection_create1(api_client):
    data = {
        "objective_data": {
            "library_name": "Sponsor",
            "name": "objective_4",
            "objective_template_uid": "ObjectiveTemplate_000004",
            "parameter_terms": [],
        },
        "objective_level_uid": "ObjectiveLevel_0001",
    }
    response = api_client.post(
        "/studies/study_root/study-objectives?create_objective=true", json=data
    )
    assert_response_status_code(response, 201)
    res = response.json()

    assert res["study_version"] is not None
    assert res["study_objective_uid"] == "StudyObjective_000003"
    assert res["accepted_version"] is False
    assert res["order"] == 3
    assert res["project_number"] == "123"
    assert res["project_name"] == "Project ABC"
    assert res["study_uid"] == "study_root"
    assert res["objective_level"]["term_uid"] == "ObjectiveLevel_0001"
    assert res["objective_level"]["term_name"] == "Objective Level 1"
    assert res["objective_level"]["codelist_uid"] == "CTCodelist_ObjectiveLevel"
    assert res["objective_level"]["codelist_name"] == "Objective Level"
    assert res["objective_level"]["codelist_submission_value"] == "OBJTLEVL"
    assert res["objective_level"]["order"] == 1
    assert res["objective_level"]["submission_value"] == "Objective level 1 submval"
    assert res["objective_level"]["queried_effective_date"] is None
    assert res["objective_level"]["date_conflict"] is False
    assert res["author_username"] == "unknown-user@example.com"
    assert res["latest_objective"] is None
    assert res["objective"]["uid"] == "Objective_000006"
    assert res["objective"]["name"] == "objective_4"
    assert res["objective"]["name_plain"] == "objective_4"
    assert res["objective"]["start_date"] is not None
    assert res["objective"]["end_date"] is None
    assert res["objective"]["status"] == "Final"
    assert res["objective"]["study_count"] == 0
    assert res["objective"]["version"] == "1.0"
    assert res["objective"]["change_description"] == "Approved version"
    assert res["objective"]["author_username"] == "unknown-user@example.com"
    assert res["objective"]["possible_actions"] == ["inactivate"]
    assert res["objective"]["template"]["name"] == "objective_4"
    assert res["objective"]["template"]["name_plain"] == "objective_4"
    assert res["objective"]["template"]["uid"] == "ObjectiveTemplate_000004"
    assert res["objective"]["template"]["sequence_id"] == "O4"
    assert res["objective"]["template"]["library_name"] == "Sponsor"
    assert res["objective"]["parameter_terms"] == []
    assert res["objective"]["library"]["name"] == "Sponsor"
    assert res["objective"]["library"]["is_editable"] is True
    assert res["endpoint_count"] == 0


def test_get_all_objectives_with_proper_study_count(api_client):
    response = api_client.get("/objectives?total_count=True")
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["items"][0]["uid"] == "Objective_000006"
    assert res["items"][0]["name"] == "objective_4"
    assert res["items"][0]["name_plain"] == "objective_4"
    assert res["items"][0]["end_date"] is None
    assert res["items"][0]["status"] == "Final"
    assert res["items"][0]["version"] == "1.0"
    assert res["items"][0]["change_description"] == "Approved version"
    assert res["items"][0]["author_username"] == "unknown-user@example.com"
    assert res["items"][0]["possible_actions"] == ["inactivate"]
    assert res["items"][0]["template"]["name"] == "objective_4"
    assert res["items"][0]["template"]["name_plain"] == "objective_4"
    assert res["items"][0]["template"]["guidance_text"] is None
    assert res["items"][0]["template"]["uid"] == "ObjectiveTemplate_000004"
    assert res["items"][0]["template"]["sequence_id"] == "O4"
    assert res["items"][0]["template"]["library_name"] == "Sponsor"
    assert res["items"][0]["parameter_terms"] == []
    assert res["items"][0]["library"]["name"] == "Sponsor"
    assert res["items"][0]["library"]["is_editable"] is True
    assert res["items"][0]["study_count"] == 1
    assert res["items"][1]["uid"] == "Objective_000003"
    assert res["items"][1]["name"] == "objective_3"
    assert res["items"][1]["name_plain"] == "objective_3"
    assert res["items"][1]["end_date"] is None
    assert res["items"][1]["status"] == "Final"
    assert res["items"][1]["version"] == "1.0"
    assert res["items"][1]["change_description"] == "Approved version"
    assert res["items"][1]["author_username"] == "unknown-user@example.com"
    assert res["items"][1]["possible_actions"] == ["inactivate"]
    assert res["items"][1]["template"]["name"] == "objective_3"
    assert res["items"][1]["template"]["name_plain"] == "objective_3"
    assert res["items"][1]["template"]["guidance_text"] is None
    assert res["items"][1]["template"]["uid"] == "ObjectiveTemplate_000003"
    assert res["items"][1]["template"]["sequence_id"] == "O3"
    assert res["items"][1]["template"]["library_name"] == "Sponsor"
    assert res["items"][1]["parameter_terms"] == []
    assert res["items"][1]["library"]["name"] == "Sponsor"
    assert res["items"][1]["library"]["is_editable"] is True
    assert res["items"][1]["study_count"] == 1
    assert res["items"][2]["uid"] == "Objective_000001"
    assert res["items"][2]["name"] == "objective_1"
    assert res["items"][2]["name_plain"] == "objective_1"
    assert res["items"][2]["end_date"] is None
    assert res["items"][2]["status"] == "Final"
    assert res["items"][2]["version"] == "1.0"
    assert res["items"][2]["change_description"] == "Approved version"
    assert res["items"][2]["author_username"] == "unknown-user@example.com"
    assert res["items"][2]["possible_actions"] == ["inactivate"]
    assert res["items"][2]["template"]["name"] == "objective_1"
    assert res["items"][2]["template"]["name_plain"] == "objective_1"
    assert res["items"][2]["template"]["guidance_text"] is None
    assert res["items"][2]["template"]["uid"] == "ObjectiveTemplate_000001"
    assert res["items"][2]["template"]["sequence_id"] == "O1"
    assert res["items"][2]["template"]["library_name"] == "Sponsor"
    assert res["items"][2]["parameter_terms"] == []
    assert res["items"][2]["library"]["name"] == "Sponsor"
    assert res["items"][2]["library"]["is_editable"] is True
    assert res["items"][2]["study_count"] == 1


def test_delete3(api_client):
    respose = api_client.delete(
        f"/studies/study_root/study-objectives/{STUDY_OBJECTIVE_UID}"
    )
    assert_response_status_code(respose, 204)
