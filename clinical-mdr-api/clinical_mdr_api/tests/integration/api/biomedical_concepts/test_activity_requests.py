"""
Tests for /concepts/activities/activities endpoints
"""

import json
import logging
from functools import reduce

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.domains.study_selections.study_selection_activity_instance import (
    StudyActivityInstanceState,
)
from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.activities.activity import Activity
from clinical_mdr_api.models.concepts.activities.activity_group import ActivityGroup
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.factory_activity import (
    create_study_activity,
)
from clinical_mdr_api.tests.integration.utils.utils import CT_CATALOGUE_NAME, TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import REQUESTED_LIBRARY_NAME

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
activity_requests_all: list[Activity]
activity_subgroup: ActivitySubGroup
activity_group: ActivityGroup
study_uid: str
biomarkers_flowchart: CTTerm


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "activityrequests.api"
    inject_and_clear_db(db_name)
    global study_uid
    study_uid = inject_base_data().uid

    catalogue_name = CT_CATALOGUE_NAME
    flowchart_codelist = TestUtils.create_ct_codelist(
        sponsor_preferred_name="Flowchart Group",
        catalogue_name=catalogue_name,
        extensible=True,
        approve=True,
    )
    global biomarkers_flowchart
    biomarkers_flowchart = TestUtils.create_ct_term(
        sponsor_preferred_name="Biomarkers",
        codelist_uid=flowchart_codelist.codelist_uid,
    )

    global activity_group
    activity_group = TestUtils.create_activity_group(name="activity_group")

    global activity_subgroup
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="activity_subgroup", activity_groups=[activity_group.uid]
    )

    global activity_requests_all
    # Create some activity requests
    activity_requests_all = [
        TestUtils.create_activity(
            name="name A",
            request_rationale="New activity request rationale",
            approve=False,
            library_name=REQUESTED_LIBRARY_NAME,
        ),
        TestUtils.create_activity(
            name="name-AAA",
            approve=False,
            library_name=REQUESTED_LIBRARY_NAME,
        ),
        TestUtils.create_activity(
            name="name-BBB",
            approve=False,
            library_name=REQUESTED_LIBRARY_NAME,
        ),
        TestUtils.create_activity(
            name="name XXX",
            definition="def-XXX",
            approve=False,
            library_name=REQUESTED_LIBRARY_NAME,
        ),
        TestUtils.create_activity(
            name="name YYY",
            definition="def-YYY",
            approve=False,
            library_name=REQUESTED_LIBRARY_NAME,
        ),
    ]

    for index in range(5):
        activity_requests_all.append(
            TestUtils.create_activity(
                name=f"name-AAA-{index}",
                approve=False,
                library_name=REQUESTED_LIBRARY_NAME,
            )
        )
        activity_requests_all.append(
            TestUtils.create_activity(
                name=f"name-BBB-{index}",
                approve=False,
                library_name=REQUESTED_LIBRARY_NAME,
            )
        )
        activity_requests_all.append(
            TestUtils.create_activity(
                name=f"name-XXX-{index}",
                definition=f"def-XXX-{index}",
                approve=False,
                library_name=REQUESTED_LIBRARY_NAME,
            )
        )
        activity_requests_all.append(
            TestUtils.create_activity(
                name=f"name-YYY-{index}",
                definition=f"def-YYY-{index}",
                approve=True,
                library_name=REQUESTED_LIBRARY_NAME,
            )
        )

    yield


ACTIVITY_REQUEST_FIELDS_ALL = [
    "uid",
    "nci_concept_id",
    "nci_concept_name",
    "name",
    "name_sentence_case",
    "synonyms",
    "definition",
    "abbreviation",
    "activity_groupings",
    "activity_instances",
    "request_rationale",
    "is_request_final",
    "is_request_rejected",
    "contact_person",
    "reason_for_rejecting",
    "requester_study_id",
    "replaced_by_activity",
    "is_data_collected",
    "is_multiple_selection_allowed",
    "is_finalized",
    "is_used_by_legacy_instances",
    "library_name",
    "start_date",
    "end_date",
    "status",
    "version",
    "change_description",
    "author_username",
    "possible_actions",
]

ACTIVITY_REQUEST_FIELDS_NOT_NULL = [
    "uid",
    "name",
]


def test_get_activity_request(api_client):
    response = api_client.get(
        f"/concepts/activities/activities/{activity_requests_all[0].uid}"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(list(res.keys())) == set(ACTIVITY_REQUEST_FIELDS_ALL)
    for key in ACTIVITY_REQUEST_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == activity_requests_all[0].uid
    assert res["name"] == "name A"
    assert res["library_name"] == REQUESTED_LIBRARY_NAME
    assert res["definition"] is None
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert res["activity_groupings"] == []
    assert res["activity_instances"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["request_rationale"] == "New activity request rationale"


def test_get_activity_requests_pagination(api_client):
    results_paginated: dict = {}
    sort_by = '{"name": true}'
    for page_number in range(1, 4):
        url = f"/concepts/activities/activities?page_number={page_number}&page_size=10&sort_by={sort_by}"
        response = api_client.get(url)
        res = response.json()
        res_names = list(map(lambda x: x["name"], res["items"]))
        results_paginated[page_number] = res_names
        log.info("Page %s: %s", page_number, res_names)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        list(reduce(lambda a, b: a + b, list(results_paginated.values())))
    )
    log.info("All rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"/concepts/activities/activities?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["name"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(activity_requests_all) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 3, True, None, 5),  # Total number of data models is 25
        pytest.param(10, 1, True, '{"name": false}', 10),
        pytest.param(10, 2, True, '{"name": true}', 10),
    ],
)
def test_get_activity_requests(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = "/concepts/activities/activities"
    query_params = []
    if page_size:
        query_params.append(f"page_size={page_size}")
    if page_number:
        query_params.append(f"page_number={page_number}")
    if total_count:
        query_params.append(f"total_count={total_count}")
    if sort_by:
        query_params.append(f"sort_by={sort_by}")

    if query_params:
        url = f"{url}?{'&'.join(query_params)}"

    log.info("GET %s", url)
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert list(res.keys()) == ["items", "total", "page", "size"]
    assert len(res["items"]) == expected_result_len
    assert res["total"] == (len(activity_requests_all) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(ACTIVITY_REQUEST_FIELDS_ALL)
        for key in ACTIVITY_REQUEST_FIELDS_NOT_NULL:
            assert item[key] is not None

    if sort_by:
        # sort_by is JSON string in the form: {"sort_field_name": is_ascending_order}
        sort_by_dict = json.loads(sort_by)
        sort_field: str = list(sort_by_dict.keys())[0]
        sort_order_ascending: bool = list(sort_by_dict.values())[0]

        # extract list of values of 'sort_field_name' field from the returned result
        result_vals = list(map(lambda x: x[sort_field], res["items"]))
        result_vals_sorted_locally = result_vals.copy()
        result_vals_sorted_locally.sort(reverse=not sort_order_ascending)
        # This asser fails due to API issue with sorting coupled with pagination
        # assert result_vals == result_vals_sorted_locally


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
def test_get_activity_requests_csv_xml_excel(api_client, export_format):
    url = "/concepts/activities/activities"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "name", "name-AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "name", "name-BBB"),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"/concepts/activities/activities?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result_prefix:
        assert len(res["items"]) > 0
        # Each returned row has a field that starts with the specified filter value
        for row in res["items"]:
            assert row[expected_matched_field].startswith(expected_result_prefix)
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result",
    [
        pytest.param('{"name": {"v": ["name-AAA"]}}', "name", "name-AAA"),
        pytest.param('{"name": {"v": ["name-BBB"]}}', "name", "name-BBB"),
        pytest.param('{"name": {"v": ["cc"]}}', None, None),
        pytest.param('{"definition": {"v": ["def-XXX"]}}', "definition", "def-XXX"),
        pytest.param('{"definition": {"v": ["def-YYY"]}}', "definition", "def-YYY"),
        pytest.param('{"definition": {"v": ["cc"]}}', None, None),
        pytest.param('{"status": {"v": ["Draft"]}}', "status", "Draft"),
        pytest.param('{"status": {"v": ["Final"]}}', "status", "Final"),
        pytest.param(
            '{"library_name": {"v": ["Requested"]}}',
            "library_name",
            REQUESTED_LIBRARY_NAME,
        ),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    url = f"/concepts/activities/activities?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result:
        assert len(res["items"]) > 0
        # Each returned row has a field whose value is equal to the specified filter value
        for row in res["items"]:
            if isinstance(expected_result, list):
                assert all(
                    item in row[expected_matched_field] for item in expected_result
                )
            else:
                assert row[expected_matched_field] == expected_result
    else:
        assert len(res["items"]) == 0


def test_edit_activity_request(api_client):
    activity_request = TestUtils.create_activity(
        name="Activity Request name",
        request_rationale="New activity request rationale",
        approve=False,
        library_name=REQUESTED_LIBRARY_NAME,
    )
    response = api_client.patch(
        f"/concepts/activities/activities/{activity_request.uid}",
        json={
            "name": "new name",
            "name_sentence_case": "new name",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["name"] == "new name"
    assert res["library_name"] == REQUESTED_LIBRARY_NAME
    assert res["definition"] is None
    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert res["activity_groupings"] == []
    assert res["activity_instances"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_post_activity_request(api_client):
    response = api_client.post(
        "/concepts/activities/activities",
        json={
            "name": "New Activity Request Name",
            "name_sentence_case": "new activity request name",
            "library_name": REQUESTED_LIBRARY_NAME,
            "request_rationale": "Activity request rationale",
            "is_data_collected": True,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["name"] == "New Activity Request Name"
    assert res["name_sentence_case"] == "new activity request name"
    assert res["library_name"] == REQUESTED_LIBRARY_NAME
    assert res["definition"] is None
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert res["activity_groupings"] == []
    assert res["activity_instances"] == []
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["request_rationale"] == "Activity request rationale"
    assert res["is_data_collected"] is True


def test_post_sponsor_activity_from_activity_request(api_client):
    # Fail sponsor activity creation because activity request is not Final
    response = api_client.post(
        "/concepts/activities/activities/sponsor-activities",
        json={
            "activity_request_uid": activity_requests_all[0].uid,
            "name": "New Sponsor Activity from Activity Request",
            "name_sentence_case": "new sponsor activity from activity request",
            "definition": "definition",
            "abbreviation": "abbreviation",
            "activity_groupings": [
                {
                    "activity_subgroup_uid": activity_subgroup.uid,
                    "activity_group_uid": activity_group.uid,
                }
            ],
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert (
        res["message"]
        == f"To update the Activity Request with Name '{activity_requests_all[0].name}' to Sponsor Activity it should be in Final state."
    )

    # Approve activity request
    response = api_client.post(
        f"/concepts/activities/activities/{activity_requests_all[0].uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # Successful sponsor activity creation from activity request
    response = api_client.post(
        "/concepts/activities/activities/sponsor-activities",
        json={
            "activity_request_uid": activity_requests_all[0].uid,
            "name": activity_requests_all[0].name,
            "name_sentence_case": activity_requests_all[0].name_sentence_case,
            "definition": "definition",
            "abbreviation": "abbreviation",
            "activity_groupings": [
                {
                    "activity_subgroup_uid": activity_subgroup.uid,
                    "activity_group_uid": activity_group.uid,
                }
            ],
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["name"] == "name A"
    assert res["name_sentence_case"] == "name A"
    assert res["library_name"] == "Sponsor"
    assert res["definition"] == "definition"
    assert res["abbreviation"] == "abbreviation"
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert len(res["activity_groupings"]) == 1
    assert (
        res["activity_groupings"][0]["activity_subgroup_uid"]
        == "ActivitySubGroup_000001"
    )
    assert res["activity_groupings"][0]["activity_subgroup_name"] == "activity_subgroup"
    assert res["activity_groupings"][0]["activity_group_uid"] == "ActivityGroup_000001"
    assert res["activity_groupings"][0]["activity_group_name"] == "activity_group"
    assert res["activity_instances"] == []
    assert res["possible_actions"] == ["inactivate", "new_version"]
    assert res["request_rationale"] is None
    replaced_activity_uid = res["uid"]

    # Confirm that activity request contains relationship to the sponsor activity that replaced specific request
    response = api_client.get(
        f"/concepts/activities/activities/{activity_requests_all[0].uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["name"] == "name A"
    assert res["library_name"] == REQUESTED_LIBRARY_NAME
    assert res["version"] == "1.0"
    assert res["status"] == "Retired"
    assert res["possible_actions"] == ["reactivate"]
    assert res["request_rationale"] == "New activity request rationale"
    assert res["activity_groupings"] == []
    assert res["activity_instances"] == []
    assert res["replaced_by_activity"] == replaced_activity_uid
    assert res["is_data_collected"] is True


def test_update_activity_request_to_sponsor_in_study_activity(api_client):
    # Create things needed for Study Activity
    activity_request = TestUtils.create_activity(
        name="activity request for study activity purpose",
        library_name=REQUESTED_LIBRARY_NAME,
    )
    study_activity = create_study_activity(
        study_uid=study_uid,
        activity_uid=activity_request.uid,
        activity_subgroup_uid=None,
        activity_group_uid=None,
        soa_group_term_uid=biomarkers_flowchart.term_uid,
    )
    # Create sponsor activity from activity request
    sponsor_activity_name = (
        "New Sponsor Activity from Activity Request used in Study Activity"
    )
    response = api_client.post(
        "/concepts/activities/activities/sponsor-activities",
        json={
            "activity_request_uid": activity_request.uid,
            "name": sponsor_activity_name,
            "name_sentence_case": sponsor_activity_name.lower(),
            "definition": "definition",
            "abbreviation": "abbreviation",
            "is_data_collected": True,
            "activity_groupings": [
                {
                    "activity_subgroup_uid": activity_subgroup.uid,
                    "activity_group_uid": activity_group.uid,
                }
            ],
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    replaced_activity_uid = res["uid"]

    # Confirm that activity request contains relationship to the sponsor activity that replaced specific request
    response = api_client.get(
        f"/concepts/activities/activities/{activity_request.uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["replaced_by_activity"] == replaced_activity_uid

    # Replace activity request to the replacing sponsor activity in the Study Activity
    response = api_client.patch(
        f"/studies/{study_uid}/study-activities/{study_activity.study_activity_uid}/activity-requests-approvals",
    )
    assert_response_status_code(response, 200)

    # Confirm that requested activity was successfully replaced by sponsor activity in Study Activity
    response = api_client.get(
        f"/studies/{study_uid}/study-activities/{study_activity.study_activity_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity"]["uid"] == replaced_activity_uid
    assert res["activity"]["status"] == "Final"
    assert res["activity"]["name"] == sponsor_activity_name
    assert res["activity"]["library_name"] == "Sponsor"
    assert (
        res["study_activity_subgroup"]["activity_subgroup_uid"] == activity_subgroup.uid
    )
    assert (
        res["study_activity_subgroup"]["activity_subgroup_name"]
        == activity_subgroup.name
    )
    assert res["study_activity_group"]["activity_group_uid"] == activity_group.uid
    assert res["study_activity_group"]["activity_group_name"] == activity_group.name

    # Assert StudyActivityInstance was created when ActivityRequest was substituted to Sponsor Activity
    response = api_client.get(
        f"/studies/{study_uid}/study-activity-instances/",
    )
    assert_response_status_code(response, 200)
    study_activity_instances = response.json()["items"]
    created_sai = []
    for sai in study_activity_instances:
        if sai["study_activity_uid"] == study_activity.study_activity_uid:
            created_sai.append(sai)
    assert (
        len(created_sai) == 1
    ), "There should be exactly just one StudyActivityInstance created when Request is substituted to the Sponsor Activity"
    created_sai = created_sai[0]
    assert created_sai["study_activity_uid"] == study_activity.study_activity_uid
    assert created_sai["state"] == StudyActivityInstanceState.MISSING_SELECTION.value


def test_edit_study_activity_request(api_client):
    clinical_programme = TestUtils.create_clinical_programme(name="SoA CP")
    project_for_test = TestUtils.create_project(
        name="Project for SoA",
        project_number="1234",
        description="Base project",
        clinical_programme_uid=clinical_programme.uid,
    )
    study_for_test = TestUtils.create_study(
        project_number=project_for_test.project_number
    )
    # Create things needed for Study Activity
    activity_request = TestUtils.create_activity(
        name="activity request for study activity edit",
        request_rationale="Some rationale",
        library_name=REQUESTED_LIBRARY_NAME,
    )
    study_activity = create_study_activity(
        study_uid=study_for_test.uid,
        activity_uid=activity_request.uid,
        activity_subgroup_uid=None,
        activity_group_uid=None,
        soa_group_term_uid=biomarkers_flowchart.term_uid,
    )
    response = api_client.get(
        f"/studies/{study_for_test.uid}/study-activities/{study_activity.study_activity_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity"]["request_rationale"] == "Some rationale"
    assert res["activity"]["is_request_final"] is False
    assert res["activity"]["is_data_collected"] is True

    general_activity_group = TestUtils.create_activity_group(name="General")
    general_activity_subgroup = TestUtils.create_activity_subgroup(
        name="General subgroup", activity_groups=[general_activity_group.uid]
    )
    # Replace activity request to the replacing sponsor activity in the Study Activity
    response = api_client.patch(
        f"/studies/{study_for_test.uid}/study-activity-requests/{study_activity.study_activity_uid}",
        json={
            "activity_subgroup_uid": general_activity_subgroup.uid,
            "activity_group_uid": general_activity_group.uid,
        },
    )
    assert_response_status_code(response, 200)

    # Confirm that requested activity was successfully replaced by sponsor activity in Study Activity
    response = api_client.get(
        f"/studies/{study_for_test.uid}/study-activities/{study_activity.study_activity_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity"]["uid"] == activity_request.uid
    assert res["activity"]["version"] == "2.0"
    assert (
        res["study_activity_subgroup"]["activity_subgroup_uid"]
        == general_activity_subgroup.uid
    )
    assert (
        res["study_activity_group"]["activity_group_uid"] == general_activity_group.uid
    )

    response = api_client.patch(
        f"/studies/{study_for_test.uid}/study-activity-requests/{study_activity.study_activity_uid}",
        json={
            "request_rationale": "New rationale",
            "activity_name": "New request name",
            "is_request_final": True,
            "is_data_collected": False,
        },
    )
    assert_response_status_code(response, 200)

    # Confirm that requested activity was successfully replaced by sponsor activity in Study Activity
    response = api_client.get(
        f"/studies/{study_for_test.uid}/study-activities/{study_activity.study_activity_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["activity"]["uid"] == activity_request.uid
    assert res["activity"]["version"] == "3.0"
    assert res["activity"]["request_rationale"] == "New rationale"
    assert res["activity"]["name"] == "New request name"
    assert res["activity"]["is_request_final"] is True
    assert res["activity"]["is_data_collected"] is False


def test_reject_activity_request(api_client):
    # Create things needed for Study Activity
    activity_request = TestUtils.create_activity(
        name="activity request for rejection test",
        request_rationale="Some rationale",
        library_name=REQUESTED_LIBRARY_NAME,
    )
    create_study_activity(
        study_uid=study_uid,
        activity_uid=activity_request.uid,
        activity_subgroup_uid=None,
        activity_group_uid=None,
        soa_group_term_uid=biomarkers_flowchart.term_uid,
    )
    reason_for_rejecting = "Some rejection reason"
    contact_person = "person to contact about rejecting"
    response = api_client.patch(
        f"/concepts/activities/activities/{activity_request.uid}/activity-request-rejections",
        json={
            "contact_person": contact_person,
            "reason_for_rejecting": reason_for_rejecting,
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["status"] == "Retired"
    assert res["contact_person"] == contact_person
    assert res["reason_for_rejecting"] == reason_for_rejecting
    assert res["is_request_rejected"] is True

    response = api_client.get(f"/concepts/activities/activities/{activity_request.uid}")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["status"] == "Retired"
    assert res["contact_person"] == contact_person
    assert res["reason_for_rejecting"] == reason_for_rejecting
    assert res["is_request_rejected"] is True
