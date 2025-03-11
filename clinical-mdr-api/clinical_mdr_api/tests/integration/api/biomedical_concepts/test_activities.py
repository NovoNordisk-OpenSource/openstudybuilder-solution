"""
Tests for /concepts/activities/activities endpoints
"""

import logging
from functools import reduce
from operator import itemgetter

import pytest
import yaml
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
)
from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityItemClass,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    Activity,
    ActivityGrouping,
)
from clinical_mdr_api.models.concepts.activities.activity_group import ActivityGroup
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
)
from clinical_mdr_api.models.concepts.activities.activity_item import ActivityItem
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
activity_group: ActivityGroup
different_activity_group: ActivityGroup
activity_subgroup: ActivitySubGroup
different_activity_subgroup: ActivitySubGroup
activities_all: list[Activity]
activity_instances_all: list[ActivityInstance]
activity_instance_classes: list[ActivityInstanceClass]
activity_items: list[ActivityItem]
activity_item_classes: list[ActivityItemClass]
ct_terms: list[CTTerm]
role_term: CTTerm
data_type_term: CTTerm


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "activities.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global activity_group
    activity_group = TestUtils.create_activity_group(name="activity_group")

    global activity_subgroup
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="activity_subgroup", activity_groups=[activity_group.uid]
    )

    global different_activity_group
    different_activity_group = TestUtils.create_activity_group(
        name="different activity_group"
    )
    global different_activity_subgroup
    different_activity_subgroup = TestUtils.create_activity_subgroup(
        name="different activity_subgroup",
        activity_groups=[different_activity_group.uid],
    )

    global activities_all
    activities_all = [
        TestUtils.create_activity(
            name="name-AAA",
            synonyms=["name1", "AAA"],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
        ),
        TestUtils.create_activity(
            name="name-BBB",
            synonyms=["name2", "BBB"],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
        ),
        TestUtils.create_activity(
            name="name-CCC",
            synonyms=["name3", "CCC"],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
        ),
    ]

    for index in range(5):
        activities_all.append(
            TestUtils.create_activity(
                name=f"Activity-{index}",
                synonyms=[f"Activity{index}"],
                activity_subgroups=[different_activity_subgroup.uid],
                activity_groups=[different_activity_group.uid],
            )
        )

    global activity_instance_classes
    activity_instance_classes = [
        TestUtils.create_activity_instance_class(name="Activity instance class 1"),
        TestUtils.create_activity_instance_class(name="Activity instance class 2"),
        TestUtils.create_activity_instance_class(name="Activity instance class 3"),
    ]
    global activity_item_classes
    global data_type_term
    global role_term
    data_type_term = TestUtils.create_ct_term(
        nci_preferred_name="Data type", sponsor_preferred_name="Data type"
    )
    role_term = TestUtils.create_ct_term(sponsor_preferred_name="Role")
    activity_item_classes = [
        TestUtils.create_activity_item_class(
            name="Activity Item Class name1",
            order=1,
            mandatory=True,
            activity_instance_class_uids=[activity_instance_classes[0].uid],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
        TestUtils.create_activity_item_class(
            name="Activity Item Class name2",
            order=2,
            mandatory=True,
            activity_instance_class_uids=[activity_instance_classes[1].uid],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
        TestUtils.create_activity_item_class(
            name="Activity Item Class name3",
            order=3,
            mandatory=True,
            activity_instance_class_uids=[activity_instance_classes[2].uid],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
    ]
    global ct_terms

    codelist = TestUtils.create_ct_codelist(extensible=True, approve=True)
    ct_terms = [
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="Activity item term",
        ),
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            sponsor_preferred_name="Activity item term2",
        ),
    ]
    global activity_items
    activity_items = [
        {
            "activity_item_class_uid": activity_item_classes[0].uid,
            "ct_term_uids": [ct_terms[0].term_uid],
            "unit_definition_uids": [],
        },
        {
            "activity_item_class_uid": activity_item_classes[1].uid,
            "ct_term_uids": [ct_terms[1].term_uid],
            "unit_definition_uids": [],
        },
        {
            "activity_item_class_uid": activity_item_classes[2].uid,
            "ct_term_uids": [ct_terms[0].term_uid, ct_terms[1].term_uid],
            "unit_definition_uids": [],
        },
    ]
    global activity_instances_all
    # Create some activity instances
    activity_instances_all = [
        TestUtils.create_activity_instance(
            name="name A",
            activity_instance_class_uid=activity_instance_classes[0].uid,
            name_sentence_case="name A",
            topic_code="topic code A",
            is_required_for_activity=True,
            activities=[activities_all[0].uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[activity_items[0]],
        ),
        TestUtils.create_activity_instance(
            name="name-AAA",
            activity_instance_class_uid=activity_instance_classes[0].uid,
            name_sentence_case="name-AAA",
            topic_code="topic code-AAA",
            is_required_for_activity=True,
            activities=[activities_all[0].uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[activity_items[0]],
        ),
        TestUtils.create_activity_instance(
            name="name-BBB",
            activity_instance_class_uid=activity_instance_classes[0].uid,
            name_sentence_case="name-BBB",
            topic_code="topic code-BBB",
            is_required_for_activity=True,
            activities=[activities_all[0].uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[activity_items[0]],
        ),
        TestUtils.create_activity_instance(
            name="name XXX",
            activity_instance_class_uid=activity_instance_classes[0].uid,
            name_sentence_case="name XXX",
            topic_code="topic code XXX",
            is_required_for_activity=True,
            activities=[activities_all[0].uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[activity_items[0], activity_items[1], activity_items[2]],
        ),
        TestUtils.create_activity_instance(
            name="name YYY",
            activity_instance_class_uid=activity_instance_classes[0].uid,
            name_sentence_case="name YYY",
            topic_code="topic code YYY",
            is_required_for_activity=True,
            activities=[activities_all[0].uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[activity_items[0], activity_items[1]],
        ),
    ]

    for index in range(5):
        activity_instances_all.append(
            TestUtils.create_activity_instance(
                name=f"name-AAA-{index}",
                activity_instance_class_uid=activity_instance_classes[1].uid,
                name_sentence_case=f"name-AAA-{index}",
                topic_code=f"topic code-AAA-{index}",
                is_required_for_activity=True,
                activities=[activities_all[1].uid],
                activity_subgroups=[activity_subgroup.uid],
                activity_groups=[activity_group.uid],
                activity_items=[activity_items[1]],
            )
        )
        activity_instances_all.append(
            TestUtils.create_activity_instance(
                name=f"name-BBB-{index}",
                activity_instance_class_uid=activity_instance_classes[1].uid,
                name_sentence_case=f"name-BBB-{index}",
                topic_code=f"topic code-BBB-{index}",
                is_required_for_activity=True,
                activities=[activities_all[1].uid],
                activity_subgroups=[activity_subgroup.uid],
                activity_groups=[activity_group.uid],
                activity_items=[activity_items[1]],
            )
        )
        activity_instances_all.append(
            TestUtils.create_activity_instance(
                name=f"name-XXX-{index}",
                activity_instance_class_uid=activity_instance_classes[1].uid,
                name_sentence_case=f"name-XXX-{index}",
                topic_code=f"topic code-XXX-{index}",
                is_required_for_activity=True,
                activities=[activities_all[1].uid],
                activity_subgroups=[activity_subgroup.uid],
                activity_groups=[activity_group.uid],
                activity_items=[activity_items[1]],
            )
        )
        activity_instances_all.append(
            TestUtils.create_activity_instance(
                name=f"name-YYY-{index}",
                activity_instance_class_uid=activity_instance_classes[1].uid,
                name_sentence_case=f"name-YYY-{index}",
                topic_code=f"topic code-YYY-{index}",
                is_required_for_activity=True,
                activities=[activities_all[1].uid],
                activity_subgroups=[activity_subgroup.uid],
                activity_groups=[activity_group.uid],
                activity_items=[activity_items[1]],
            )
        )

    yield


ACTIVITY_FIELDS_ALL = [
    "uid",
    "nci_concept_id",
    "nci_concept_name",
    "name",
    "synonyms",
    "name_sentence_case",
    "definition",
    "abbreviation",
    "activity_groupings",
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

ACTIVITY_FIELDS_NOT_NULL = ["uid", "name", "activity_groupings", "start_date"]


def test_get_activity(api_client):
    response = api_client.get(
        f"/concepts/activities/activities/{activities_all[0].uid}"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(list(res.keys())) == set(ACTIVITY_FIELDS_ALL)
    for key in ACTIVITY_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == activities_all[0].uid
    assert res["name"] == "name-AAA"
    assert res["name_sentence_case"] == "name-AAA"
    assert res["synonyms"] == ["name1", "AAA"]
    assert len(res["activity_groupings"]) == 1
    assert res["activity_groupings"][0]["activity_group_uid"] == activity_group.uid
    assert res["activity_groupings"][0]["activity_group_name"] == activity_group.name
    assert (
        res["activity_groupings"][0]["activity_subgroup_uid"] == activity_subgroup.uid
    )
    assert (
        res["activity_groupings"][0]["activity_subgroup_name"] == activity_subgroup.name
    )

    assert res["library_name"] == "Sponsor"
    assert res["definition"] is None
    assert res["is_multiple_selection_allowed"] is True
    assert res["is_finalized"] is False
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_get_activity_pagination(api_client):
    results_paginated: dict = {}
    sort_by = '{"name": true}'
    for page_number in range(1, 4):
        url = f"/concepts/activities/activities?page_number={page_number}&page_size=3&sort_by={sort_by}"
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
    assert len(activities_all) == len(results_paginated_merged)
    assert results_all_in_one_page == sorted(results_all_in_one_page)

    # Assert sorting by ActivityGroup works fine
    sort_by = '{"activity_groupings[0].activity_group_name":true}'
    res_all = api_client.get(
        f"/concepts/activities/activities?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    all_results = list(
        map(
            lambda x: x["activity_groupings"][0]["activity_group_name"],
            res_all["items"],
        )
    )
    assert all_results == sorted(
        all_results
    ), "Results should be returned by ActivityGroup name ascending order"
    sort_by = '{"activity_groupings[0].activity_group_name":false}'
    res_all = api_client.get(
        f"/concepts/activities/activities?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    all_results = list(
        map(
            lambda x: x["activity_groupings"][0]["activity_group_name"],
            res_all["items"],
        )
    )
    assert all_results == sorted(
        all_results, reverse=True
    ), "Results should be returned by ActivityGroup name descending order"

    # Assert sorting by ActivitySubGroup works fine
    sort_by = '{"activity_groupings[0].activity_subgroup_name":true}'
    res_all = api_client.get(
        f"/concepts/activities/activities?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    all_results = list(
        map(
            lambda x: x["activity_groupings"][0]["activity_subgroup_name"],
            res_all["items"],
        )
    )
    assert all_results == sorted(
        all_results
    ), "Results should be returned by ActivitySubGroup name ascending order"
    sort_by = '{"activity_groupings[0].activity_subgroup_name":false}'
    res_all = api_client.get(
        f"/concepts/activities/activities?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    all_results = list(
        map(
            lambda x: x["activity_groupings"][0]["activity_subgroup_name"],
            res_all["items"],
        )
    )
    assert all_results == sorted(
        all_results, reverse=True
    ), "Results should be returned by ActivitySubGroup name descending order"


def test_get_activity_versions(api_client):
    # Create a new version of an activity
    response = api_client.post(
        f"/concepts/activities/activities/{activities_all[0].uid}/versions"
    )
    assert_response_status_code(response, 201)

    # Get all versions of all activities
    response = api_client.get("/concepts/activities/activities/versions?page_size=100")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(list(res.keys())) == set(["items", "total", "page", "size"])

    assert len(res["items"]) == len(activities_all) * 2 + 1
    for item in res["items"]:
        assert set(list(item.keys())) == set(ACTIVITY_FIELDS_ALL)
        for key in ACTIVITY_FIELDS_NOT_NULL:
            assert item[key] is not None

    # Check that the items are sorted by start_date descending
    sorted_items = sorted(res["items"], key=itemgetter("start_date"), reverse=True)
    assert sorted_items == res["items"]


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "name", "name-AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "name", "name-BBB"),
        pytest.param('{"*": {"v": ["zzzz"]}}', None, None),
        pytest.param('{"*": {"v": ["Final"]}}', "status", "Final"),
        pytest.param('{"*": {"v": ["1.0"]}}', "version", "1.0"),
        pytest.param(
            '{"*": {"v": ["activity_group"]}}',
            "activity_groupings.activity_group_name",
            "activity_group",
        ),
        pytest.param(
            '{"*": {"v": ["activity_subgroup"]}}',
            "activity_groupings.activity_subgroup_name",
            "activity_subgroup",
        ),
    ],
)
def test_filtering_versions_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"/concepts/activities/activities/versions?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result_prefix:
        assert len(res["items"]) > 0
        nested_path = None

        # if we expect a nested property to be equal to specified value
        if isinstance(expected_matched_field, str) and "." in expected_matched_field:
            nested_path = expected_matched_field.split(".")
            expected_matched_field = nested_path[-1]
            nested_path = nested_path[:-1]

        # Each returned row has a field that starts with the specified filter value
        for row in res["items"]:
            if nested_path:
                for prop in nested_path:
                    row = row[prop]
            if isinstance(row, list):
                any(
                    item[expected_matched_field].startswith(expected_result_prefix)
                    for item in row
                )
            else:
                assert row[expected_matched_field].startswith(expected_result_prefix)
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result",
    [
        pytest.param('{"name": {"v": ["name-AAA"]}}', "name", "name-AAA"),
        pytest.param('{"name": {"v": ["name-BBB"]}}', "name", "name-BBB"),
        pytest.param('{"name": {"v": ["zzzz"]}}', None, None),
        pytest.param(
            '{"name_sentence_case": {"v": ["name-AAA"]}}',
            "name_sentence_case",
            "name-AAA",
        ),
        pytest.param(
            '{"name_sentence_case": {"v": ["name-BBB"]}}',
            "name_sentence_case",
            "name-BBB",
        ),
        pytest.param('{"name_sentence_case": {"v": ["zzzz"]}}', None, None),
    ],
)
def test_filtering_versions_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    url = f"/concepts/activities/activities/versions?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result:
        assert len(res["items"]) > 0

        # if we expect a nested property to be equal to specified value
        nested_path = None
        if isinstance(expected_matched_field, str) and "." in expected_matched_field:
            nested_path = expected_matched_field.split(".")
            expected_matched_field = nested_path[-1]
            nested_path = nested_path[:-1]

        # Each returned row has a field whose value is equal to the specified filter value
        for row in res["items"]:
            if nested_path:
                for prop in nested_path:
                    row = row[prop]
            if isinstance(expected_result, list):
                assert all(
                    item in row[expected_matched_field] for item in expected_result
                )
            else:
                if isinstance(row, list):
                    all(item[expected_matched_field] == expected_result for item in row)
                else:
                    assert row[expected_matched_field] == expected_result
    else:
        assert len(res["items"]) == 0


def test_activity_cosmos_overview(api_client):
    url = f"/concepts/activities/activities/{activities_all[1].uid}/overview.cosmos"
    response = api_client.get(url)

    assert_response_status_code(response, 200)
    assert "application/x-yaml" in response.headers["content-type"]

    res = yaml.load(response.text, Loader=yaml.SafeLoader)

    assert res["shortName"] == "name-BBB"
    assert res["dataElementConcepts"][0]["shortName"] == "Activity Item Class name2"
    assert res["dataElementConcepts"][0]["dataType"] == "Data type"


def test_create_activity_unique_name_validation(api_client):
    activity_name = TestUtils.random_str(20, "ActivityName-")
    activity_name2 = TestUtils.random_str(20, "ActivityName-")
    TestUtils.create_activity(
        name=activity_name,
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        approve=False,
    )
    TestUtils.create_activity(
        name=activity_name2,
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        approve=True,
    )

    # Create activity with the same name as the first one
    response = api_client.post(
        "/concepts/activities/activities",
        json={
            "name": activity_name,
            "name_sentence_case": activity_name,
            "activity_groupings": [
                {
                    "activity_subgroup_uid": activity_subgroup.uid,
                    "activity_group_uid": activity_group.uid,
                }
            ],
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 409)
    assert (
        response.json()["message"]
        == f"Activity with Name '{activity_name}' already exists."
    )

    # Create activity with the same name as the second one
    response = api_client.post(
        "/concepts/activities/activities",
        json={
            "name": activity_name2,
            "name_sentence_case": activity_name2,
            "activity_groupings": [
                {
                    "activity_subgroup_uid": activity_subgroup.uid,
                    "activity_group_uid": activity_group.uid,
                }
            ],
            "library_name": "Sponsor",
        },
    )
    assert_response_status_code(response, 409)
    assert (
        response.json()["message"]
        == f"Activity with Name '{activity_name2}' already exists."
    )


def test_update_activity_to_new_grouping(api_client):
    group_name = "original group name"
    original_subgroup_name = "original subgroup name"
    edited_subgroup_name = "edited subgroup name"
    activity_name = "original activity name"

    # ==== Create group, subgroup, activity and activity instance ====
    group = TestUtils.create_activity_group(name=group_name)

    subgroup = TestUtils.create_activity_subgroup(
        name=original_subgroup_name, activity_groups=[group.uid]
    )
    activity = TestUtils.create_activity(
        name=activity_name,
        activity_subgroups=[subgroup.uid],
        activity_groups=[group.uid],
        approve=True,
    )

    # ==== Update subgroup ====
    # Create new version of subgroup
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{subgroup.uid}/versions",
        json={},
    )
    assert response.status_code == 201

    # Patch the subgroup
    response = api_client.patch(
        f"/concepts/activities/activity-sub-groups/{subgroup.uid}",
        json={
            "name": edited_subgroup_name,
            "name_sentence_case": edited_subgroup_name,
            "change_description": "patch group",
        },
    )
    assert response.status_code == 200

    # Approve the subgroup
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{subgroup.uid}/approvals"
    )

    # === Assert that the subgroup was updated as expected ===
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{subgroup.uid}"
    )

    assert response.status_code == 200
    res = response.json()

    assert res["name"] == edited_subgroup_name
    assert len(res["activity_groups"]) == 1
    assert res["activity_groups"][0]["uid"] == group.uid

    assert res["activity_groups"][0]["name"] == group_name

    assert res["version"] == "2.0"
    assert res["status"] == "Final"

    # ==== Update activity ====

    # Create new version of activity
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/versions",
        json={},
    )
    assert response.status_code == 201

    # Patch the activity, no changes
    response = api_client.patch(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "change_description": "patch activity",
        },
    )
    assert response.status_code == 200

    # Approve the activity
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/approvals"
    )
    assert response.status_code == 201

    # Get the activity by uid and assert that it was updated to the new subgroup version
    response = api_client.get(f"/concepts/activities/activities/{activity.uid}")
    assert response.status_code == 200
    res = response.json()

    assert res["version"] == "2.0"
    assert res["status"] == "Final"

    assert res["name"] == activity_name
    assert len(res["activity_groupings"]) == 1

    assert res["activity_groupings"][0]["activity_subgroup_uid"] == subgroup.uid
    assert (
        res["activity_groupings"][0]["activity_subgroup_name"] == edited_subgroup_name
    )
    assert res["activity_groupings"][0]["activity_group_uid"] == group.uid
    assert res["activity_groupings"][0]["activity_group_name"] == group_name


def test_update_activity(api_client):
    # Create a new version of an activity
    response = api_client.post(
        f"/concepts/activities/activities/{activities_all[2].uid}/versions"
    )
    assert_response_status_code(response, 201)

    response = api_client.patch(
        f"/concepts/activities/activities/{activities_all[2].uid}",
        json={
            "synonyms": ["new name", "CCC"],
            "activity_groupings": [
                activities_all[2].activity_groupings[0].dict(),
                ActivityGrouping(
                    activity_group_uid=different_activity_group.uid,
                    activity_subgroup_uid=different_activity_subgroup.uid,
                ).dict(),
            ],
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["uid"] == activities_all[2].uid
    assert res["name"] == "name-CCC"
    assert res["name_sentence_case"] == "name-CCC"
    assert res["synonyms"] == ["new name", "CCC"]
    assert len(res["activity_groupings"]) == 2
    assert res["activity_groupings"][0]["activity_group_uid"] == activity_group.uid
    assert res["activity_groupings"][0]["activity_group_name"] == activity_group.name
    assert (
        res["activity_groupings"][0]["activity_subgroup_uid"] == activity_subgroup.uid
    )
    assert (
        res["activity_groupings"][0]["activity_subgroup_name"] == activity_subgroup.name
    )
    assert (
        res["activity_groupings"][1]["activity_group_uid"]
        == different_activity_group.uid
    )
    assert (
        res["activity_groupings"][1]["activity_group_name"]
        == different_activity_group.name
    )
    assert (
        res["activity_groupings"][1]["activity_subgroup_uid"]
        == different_activity_subgroup.uid
    )
    assert (
        res["activity_groupings"][1]["activity_subgroup_name"]
        == different_activity_subgroup.name
    )

    assert res["library_name"] == "Sponsor"
    assert res["definition"] is None
    assert res["is_multiple_selection_allowed"] is True
    assert res["is_finalized"] is False
    assert res["version"] == "1.2"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "edit"]


def test_cannot_create_activity_with_non_unique_synonyms(api_client):
    # Create an activity with the same synonyms as an activity created in the test data
    response = api_client.post(
        "/concepts/activities/activities",
        json={
            "name": "cannot create",
            "name_sentence_case": "cannot create",
            "synonyms": ["name2", "XXX"],
            "library_name": "Sponsor",
        },
    )
    assert response.status_code == 409
    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "Following Activities already have the provided synonyms: {'Activity_000002': ['name2']}"
    )


def test_cannot_update_activity_with_non_unique_synonyms(api_client):
    new_activity1 = TestUtils.create_activity(
        name="test1", synonyms=["XYZ1", "non_unique1"]
    )
    new_activity2 = TestUtils.create_activity(
        name="test2", synonyms=["XYZ2", "non_unique2"]
    )

    response = api_client.patch(
        f"/concepts/activities/activities/{activities_all[0].uid}",
        json={
            "synonyms": ["non_unique1", "non_unique2"],
        },
    )
    assert response.status_code == 409
    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == f"Following Activities already have the provided synonyms: {{'{new_activity1.uid}': ['non_unique1'], '{new_activity2.uid}': ['non_unique2']}}"
    )
