# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityInstanceClassRelInput,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.tests.integration.utils.api import inject_base_data
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from common.config import settings
from consumer_api.consumer_api import app
from consumer_api.tests.utils import assert_response_status_code, set_db
from consumer_api.v1 import models

BASE_URL = "/v1"


LIBRARY_ACTIVITY_FIELDS_ALL = [
    "uid",
    "name",
    "groupings",
    "library",
    "definition",
    "nci_concept_id",
    "nci_concept_name",
    "is_data_collected",
    "status",
    "version",
]

LIBRARY_ACTIVITY_FIELDS_NOT_NULL = [
    "uid",
    "library",
    "status",
    "version",
    "name",
    "groupings",
    "is_data_collected",
]

LIBRARY_ACTIVITY_INSTANCE_FIELDS_ALL = [
    "uid",
    "name",
    "groupings",
    "library",
    "definition",
    "nci_concept_id",
    "nci_concept_name",
    "topic_code",
    "param_code",
    "status",
    "version",
    "groupings_status",
    "groupings_version",
    "activity_instance_class",
    "activity_items",
]

LIBRARY_ACTIVITY_INSTANCE_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "groupings",
    "library",
    "topic_code",
    "param_code",
    "status",
    "version",
    "groupings_status",
    "groupings_version",
    "activity_instance_class",
    "activity_items",
]


# Global variables shared between fixtures and tests
activities: list[models.LibraryActivity]
total_activities: int = 25
activity_group: Any
activity_subgroup: Any
activity_instances: list[models.LibraryActivityInstance]
activity_instance_with_items: Any
activity_item_class: Any
activity_item_class_ct_term: Any
activity_item_class_ct_codelist: Any
activity_item_class_text: Any
activity_item_codelist: Any
activity_item_ct_terms: list[CTTerm]
activity_item_unit_definition_uid: str


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data(api_client):
    """Initialize test data"""
    db_name = "consumer-api-v1-library"
    set_db(db_name)
    inject_base_data(inject_unit_dimension=True)
    global activities
    global activity_group
    global activity_subgroup
    global activity_instances

    activity_instance_class = TestUtils.create_activity_instance_class(
        name="Randomized activity instance class"
    )

    activities = []
    activity_instances = []

    activity_group = TestUtils.create_activity_group("Activity Group")
    activity_subgroup = TestUtils.create_activity_subgroup("Activity Sub Group")

    # Create activity item class prerequisites
    global activity_item_class
    global activity_item_class_ct_term
    global activity_item_class_ct_codelist
    global activity_item_class_text
    global activity_instance_with_items
    global activity_item_codelist
    global activity_item_ct_terms
    global activity_item_unit_definition_uid

    data_type_codelist = TestUtils.create_ct_codelist(
        name="DATATYPE", submission_value="DATATYPE", extensible=True, approve=True
    )
    data_type_term = TestUtils.create_ct_term(
        sponsor_preferred_name="Data type", codelist_uid=data_type_codelist.codelist_uid
    )
    role_codelist = TestUtils.create_ct_codelist(
        name="ROLE", submission_value="ROLE", extensible=True, approve=True
    )
    role_term = TestUtils.create_ct_term(
        sponsor_preferred_name="Role", codelist_uid=role_codelist.codelist_uid
    )

    aic_rel = ActivityInstanceClassRelInput(
        uid=activity_instance_class.uid,  # type: ignore[arg-type]
        mandatory=True,
        is_adam_param_specific_enabled=True,
        is_additional_optional=False,
        is_default_linked=False,
    )

    # Activity item class for unit definition type
    activity_item_class = TestUtils.create_activity_item_class(
        name="Test Activity Item Class",
        order=1,
        activity_instance_classes=[aic_rel],
        role_uid=role_term.term_uid,
        data_type_uid=data_type_term.term_uid,
    )

    # Activity item class for ct_term type
    activity_item_class_ct_term = TestUtils.create_activity_item_class(
        name="CT Term Item Class",
        order=2,
        activity_instance_classes=[aic_rel],
        role_uid=role_term.term_uid,
        data_type_uid=data_type_term.term_uid,
    )

    # Activity item class for ct_codelist type
    activity_item_class_ct_codelist = TestUtils.create_activity_item_class(
        name="CT Codelist Item Class",
        order=3,
        activity_instance_classes=[aic_rel],
        role_uid=role_term.term_uid,
        data_type_uid=data_type_term.term_uid,
    )

    # Activity item class for text type
    activity_item_class_text = TestUtils.create_activity_item_class(
        name="Text Item Class",
        order=4,
        activity_instance_classes=[aic_rel],
        role_uid=role_term.term_uid,
        data_type_uid=data_type_term.term_uid,
    )

    # Create a codelist and terms for activity items
    activity_item_codelist = TestUtils.create_ct_codelist(
        name="AI Codelist",
        submission_value="AI_CODELIST",
        extensible=True,
        approve=True,
    )
    activity_item_ct_terms = [
        TestUtils.create_ct_term(
            codelist_uid=activity_item_codelist.codelist_uid,
            sponsor_preferred_name="AI Term 1",
        ),
        TestUtils.create_ct_term(
            codelist_uid=activity_item_codelist.codelist_uid,
            sponsor_preferred_name="AI Term 2",
        ),
    ]

    # Use the "day" unit definition created by inject_base_data
    activity_item_unit_definition_uid = TestUtils.get_unit_uid_by_name("day")

    for idx in range(0, total_activities):
        # Create Final Activity
        activity = TestUtils.create_activity(
            f"Activity {str(idx + 1).zfill(2)}",
            activity_groups=[activity_group.uid],
            activity_subgroups=[activity_subgroup.uid],
            approve=True,
        )
        activities.append(activity)  # type: ignore[arg-type]

        activity_instance = TestUtils.create_activity_instance(
            name=f"Activity instance {idx} - Final",
            activity_instance_class_uid=activity_instance_class.uid,  # type: ignore[arg-type]
            name_sentence_case=f"activity instance {idx} - final",
            topic_code=f"TC {idx} final",
            adam_param_code=f"randomized adam_param_code {idx} final",
            is_required_for_activity=True,
            activities=[activity.uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[],
            approve=True,
        )
        activity_instances.append(activity_instance)  # type: ignore[arg-type]

        # Create Draft Activity Instance
        # (This is to ensure that we have both Final and Draft activities)
        activity_instance = TestUtils.create_activity_instance(
            name=f"Activity instance {idx} - Draft",
            activity_instance_class_uid=activity_instance_class.uid,  # type: ignore[arg-type]
            name_sentence_case=f"activity instance {idx} - draft",
            topic_code=f"TC {idx} draft",
            adam_param_code=f"randomized adam_param_code {idx} draft",
            is_required_for_activity=True,
            activities=[activity.uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[],
            approve=False,
        )
        activity_instances.append(activity_instance)  # type: ignore[arg-type]

        # Create Draft Activity
        activity_draft = TestUtils.create_activity(
            f"Activity Draft {str(idx + 1).zfill(2)}",
            activity_groups=[activity_group.uid],
            activity_subgroups=[activity_subgroup.uid],
            approve=False,
        )
        activities.append(activity_draft)  # type: ignore[arg-type]

    # Create one activity instance with all types of activity items
    ai_activity = TestUtils.create_activity(
        "Activity With Items",
        activity_groups=[activity_group.uid],
        activity_subgroups=[activity_subgroup.uid],
        approve=True,
    )
    activities.append(ai_activity)  # type: ignore[arg-type]
    activity_instance_with_items = TestUtils.create_activity_instance(
        name="Activity instance with items",
        activity_instance_class_uid=activity_instance_class.uid,  # type: ignore[arg-type]
        name_sentence_case="activity instance with items",
        topic_code="TC with items",
        adam_param_code="adam_param_with_items",
        is_required_for_activity=True,
        activities=[ai_activity.uid],
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        activity_items=[
            # Unit definition type
            {
                "activity_item_class_uid": activity_item_class.uid,
                "ct_terms": [],
                "unit_definition_uids": [activity_item_unit_definition_uid],
                "is_adam_param_specific": True,
            },
            # CT term type
            {
                "activity_item_class_uid": activity_item_class_ct_term.uid,
                "ct_terms": [
                    {
                        "term_uid": activity_item_ct_terms[0].term_uid,
                        "codelist_uid": activity_item_codelist.codelist_uid,
                    },
                    {
                        "term_uid": activity_item_ct_terms[1].term_uid,
                        "codelist_uid": activity_item_codelist.codelist_uid,
                    },
                ],
                "unit_definition_uids": [],
                "is_adam_param_specific": False,
            },
            # CT codelist type
            {
                "activity_item_class_uid": activity_item_class_ct_codelist.uid,
                "ct_terms": [],
                "ct_codelist_uid": activity_item_codelist.codelist_uid,
                "unit_definition_uids": [],
                "is_adam_param_specific": False,
            },
            # Text type
            {
                "activity_item_class_uid": activity_item_class_text.uid,
                "ct_terms": [],
                "unit_definition_uids": [],
                "is_adam_param_specific": False,
                "text_value": "Sample text value",
            },
        ],
        approve=True,
    )
    activity_instances.append(activity_instance_with_items)  # type: ignore[arg-type]

    # sort activities by name
    activities.sort(key=lambda x: x.name)


def test_get_library_activities(api_client):
    response = api_client.get(f"{BASE_URL}/library/activities")
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res, False)

    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, LIBRARY_ACTIVITY_FIELDS_ALL, LIBRARY_ACTIVITY_FIELDS_NOT_NULL
        )

        assert item["library"] in ["Sponsor", "Requested"]
        assert item["status"] in ["Final", "Draft", "Retired"]
        assert item["groupings"][0]["activity_group_name"] == activity_group.name
        assert item["groupings"][0]["activity_subgroup_name"] == activity_subgroup.name


def test_get_library_activities_pagination_sorting(api_client):

    # Default page size
    response = api_client.get(f"{BASE_URL}/library/activities")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == len(activities)
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default page size
    response = api_client.get(f"{BASE_URL}/library/activities?page_size=2")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 2
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default page size
    response = api_client.get(f"{BASE_URL}/library/activities?page_size=100")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == len(activities)
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default page number and page size
    response = api_client.get(
        f"{BASE_URL}/library/activities?page_size=3&page_number=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 3
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default sort_by
    response = api_client.get(f"{BASE_URL}/library/activities?page_size=10&sort_by=uid")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)
    assert len(res["items"]) == 10
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default sort_by and sort_order
    response = api_client.get(
        f"{BASE_URL}/library/activities?sort_order=desc&sort_by=uid&page_size=15"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 15
    TestUtils.assert_sort_order(res["items"], "uid", True)


@pytest.mark.parametrize("page_size", [8, 20, 100])
def test_get_library_activities_all(api_client, page_size):
    all_fetched_activities = []

    response = api_client.get(f"{BASE_URL}/library/activities?page_size={page_size}")
    all_fetched_activities.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_activities.extend(response.json()["items"])

    assert len(all_fetched_activities) == len(activities)
    assert {activity["name"] for activity in all_fetched_activities} == {
        activity.name for activity in activities
    }

    TestUtils.assert_sort_order(all_fetched_activities, "name", False)


def test_get_library_activities_filtering(api_client):
    # Filter by status
    response = api_client.get(f"{BASE_URL}/library/activities?status=Final")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "status=Final&" in res[key]

    assert len(res["items"]) == total_activities + 1  # +1 for ai_activity
    for item in res["items"]:
        assert item["status"] == "Final"

    response = api_client.get(f"{BASE_URL}/library/activities?status=Draft")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "status=Draft&" in res[key]

    assert len(res["items"]) == total_activities
    for item in res["items"]:
        assert item["status"] == "Draft"

    # Filter by library
    response = api_client.get(f"{BASE_URL}/library/activities?library=Sponsor")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "library=Sponsor&" in res[key]

    assert len(res["items"]) == len(activities)
    for item in res["items"]:
        assert item["library"] == "Sponsor"

    response = api_client.get(f"{BASE_URL}/library/activities?library=Requested")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "library=Requested&" in res[key]

    assert len(res["items"]) == 0
    for item in res["items"]:
        assert item["library"] == "Requested"

    # Filter by library and status
    response = api_client.get(
        f"{BASE_URL}/library/activities?library=Sponsor&status=Final"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "library=Sponsor&" in res[key]
        assert "status=Final&" in res[key]

    assert len(res["items"]) == total_activities + 1  # +1 for ai_activity
    for item in res["items"]:
        assert item["library"] == "Sponsor"
        assert item["status"] == "Final"


def test_get_library_activities_invalid_pagination_params(api_client):
    response = api_client.get(f"{BASE_URL}/library/activities?page_size=0")
    assert_response_status_code(response, 400)
    assert (
        response.json()["details"][0]["msg"]
        == "Input should be greater than or equal to 1"
    )

    response = api_client.get(
        f"{BASE_URL}/studies?page_size={settings.max_page_size + 1}"
    )
    assert_response_status_code(response, 400)
    assert (
        response.json()["details"][0]["msg"]
        == "Input should be less than or equal to 1000"
    )

    response = api_client.get(
        f"{BASE_URL}/studies?page_number={settings.max_int_neo4j + 1}&page_size=1"
    )
    assert_response_status_code(response, 400)
    response_data = response.json()
    assert response_data["message"] == "The request failed due to validation errors"
    assert response_data["details"][0]["error_code"] == "less_than_equal"
    assert (
        response_data["details"][0]["msg"]
        == "Input should be less than or equal to 1000000000"
    )


def test_get_library_activity_instances(api_client):
    response = api_client.get(f"{BASE_URL}/library/activity-instances")
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res, False)

    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item,
            LIBRARY_ACTIVITY_INSTANCE_FIELDS_ALL,
            LIBRARY_ACTIVITY_INSTANCE_FIELDS_NOT_NULL,
        )

        assert item["library"] in ["Sponsor", "Requested"]
        assert item["status"] in ["Final", "Draft", "Retired"]
        assert item["groupings"][0]["activity_group_name"] == activity_group.name
        assert item["groupings"][0]["activity_subgroup_name"] == activity_subgroup.name


def test_get_library_activity_instances_pagination_sorting(api_client):

    # Default page size
    response = api_client.get(f"{BASE_URL}/library/activity-instances")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == len(activities)
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default page size
    response = api_client.get(f"{BASE_URL}/library/activity-instances?page_size=2")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 2
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default page size
    response = api_client.get(f"{BASE_URL}/library/activity-instances?page_size=100")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == len(activities)
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default page number and page size
    response = api_client.get(
        f"{BASE_URL}/library/activity-instances?page_size=3&page_number=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 3
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default sort_by
    response = api_client.get(
        f"{BASE_URL}/library/activity-instances?page_size=10&sort_by=uid"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)
    assert len(res["items"]) == 10
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default sort_by and sort_order
    response = api_client.get(
        f"{BASE_URL}/library/activity-instances?sort_order=desc&sort_by=uid&page_size=15"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 15
    TestUtils.assert_sort_order(res["items"], "uid", True)


@pytest.mark.parametrize("page_size", [8, 20, 100])
def test_get_library_activity_instances_all(api_client, page_size):
    all_fetched_activity_instances = []

    response = api_client.get(
        f"{BASE_URL}/library/activity-instances?page_size={page_size}"
    )
    all_fetched_activity_instances.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_activity_instances.extend(response.json()["items"])

    assert len(all_fetched_activity_instances) == len(activity_instances)
    assert {
        activity_inst["name"] for activity_inst in all_fetched_activity_instances
    } == {activity_inst.name for activity_inst in activity_instances}

    TestUtils.assert_sort_order(all_fetched_activity_instances, "name", False)


def test_get_library_activity_instances_filtering(api_client):
    # Filter by status
    response = api_client.get(f"{BASE_URL}/library/activity-instances?status=Final")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "status=Final&" in res[key]

    assert (
        len(res["items"]) == total_activities + 1
    )  # +1 for activity_instance_with_items
    for item in res["items"]:
        assert item["status"] == "Final"

    response = api_client.get(f"{BASE_URL}/library/activity-instances?status=Draft")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "status=Draft&" in res[key]

    assert len(res["items"]) == total_activities
    for item in res["items"]:
        assert item["status"] == "Draft"

    # Filter by library
    response = api_client.get(f"{BASE_URL}/library/activity-instances?library=Sponsor")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "library=Sponsor&" in res[key]

    assert len(res["items"]) == len(activity_instances)
    for item in res["items"]:
        assert item["library"] == "Sponsor"

    response = api_client.get(
        f"{BASE_URL}/library/activity-instances?library=Requested"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "library=Requested&" in res[key]

    assert len(res["items"]) == 0
    for item in res["items"]:
        assert item["library"] == "Requested"

    # Filter by library and status
    response = api_client.get(
        f"{BASE_URL}/library/activity-instances?library=Sponsor&status=Final"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "library=Sponsor&" in res[key]
        assert "status=Final&" in res[key]

    assert (
        len(res["items"]) == total_activities + 1
    )  # +1 for activity_instance_with_items
    for item in res["items"]:
        assert item["library"] == "Sponsor"
        assert item["status"] == "Final"

    # Filter by activity_uid
    activity_uid = activities[0].uid
    response = api_client.get(
        f"{BASE_URL}/library/activity-instances?activity_uid={activity_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert f"activity_uid={activity_uid}&" in res[key]

    assert len(res["items"]) == 2  # One Final and one Draft activity instance
    for item in res["items"]:
        assert item["library"] == "Sponsor"
        assert item["groupings"][0]["activity_uid"] == activity_uid
        assert item["groupings"][0]["activity_group_uid"] == activity_group.uid
        assert item["groupings"][0]["activity_subgroup_uid"] == activity_subgroup.uid


def test_get_library_activity_instances_activity_items(api_client):
    """Test that all types of activity items are properly returned."""
    response = api_client.get(
        f"{BASE_URL}/library/activity-instances?page_size=100&status=Final"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    # Find the activity instance that has activity items
    items_with_activity_items = [
        item for item in res["items"] if len(item.get("activity_items", [])) > 0
    ]
    assert (
        len(items_with_activity_items) > 0
    ), "Expected at least one activity instance with activity items"

    item = items_with_activity_items[0]
    assert item["name"] == "Activity instance with items"
    assert len(item["activity_items"]) == 4

    expected_keys = {
        "activity_item_class",
        "data_type",
        "ct_codelist",
        "ct_terms",
        "unit_definitions",
        "text_value",
        "is_adam_param_specific",
        "is_activity_instance_id_specific",
    }
    for activity_item in item["activity_items"]:
        assert set(activity_item.keys()) == expected_keys

    # Build a lookup by activity_item_class uid for easier assertions
    items_by_class = {
        ai["activity_item_class"]["uid"]: ai for ai in item["activity_items"]
    }

    # --- Unit definition type ---
    unit_item = items_by_class[activity_item_class.uid]
    assert unit_item["activity_item_class"]["name"] == "Test Activity Item Class"
    assert unit_item["data_type"] == "Data type"
    assert len(unit_item["unit_definitions"]) == 1
    assert unit_item["unit_definitions"][0]["uid"] == activity_item_unit_definition_uid
    assert unit_item["ct_terms"] == []
    assert unit_item["ct_codelist"] is None
    assert unit_item["text_value"] is None
    assert unit_item["is_adam_param_specific"] is True

    # --- CT term type ---
    ct_term_item = items_by_class[activity_item_class_ct_term.uid]
    assert ct_term_item["activity_item_class"]["name"] == "CT Term Item Class"
    assert ct_term_item["data_type"] == "Data type"
    assert len(ct_term_item["ct_terms"]) == 2
    ct_term_uids = {t["term_uid"] for t in ct_term_item["ct_terms"]}
    assert ct_term_uids == {
        activity_item_ct_terms[0].term_uid,
        activity_item_ct_terms[1].term_uid,
    }
    for ct_term in ct_term_item["ct_terms"]:
        assert ct_term["codelist_uid"] == activity_item_codelist.codelist_uid
    assert ct_term_item["unit_definitions"] == []
    assert ct_term_item["ct_codelist"] is None
    assert ct_term_item["text_value"] is None
    assert ct_term_item["is_adam_param_specific"] is False

    # --- CT codelist type ---
    codelist_item = items_by_class[activity_item_class_ct_codelist.uid]
    assert codelist_item["activity_item_class"]["name"] == "CT Codelist Item Class"
    assert codelist_item["data_type"] == "Data type"
    assert codelist_item["ct_codelist"] is not None
    assert codelist_item["ct_codelist"]["uid"] == activity_item_codelist.codelist_uid
    assert codelist_item["ct_codelist"]["submission_value"] is not None
    assert codelist_item["ct_terms"] == []
    assert codelist_item["unit_definitions"] == []
    assert codelist_item["text_value"] is None
    assert codelist_item["is_adam_param_specific"] is False

    # --- Text type ---
    text_item = items_by_class[activity_item_class_text.uid]
    assert text_item["activity_item_class"]["name"] == "Text Item Class"
    assert text_item["data_type"] == "Data type"
    assert text_item["text_value"] == "Sample text value"
    assert text_item["ct_terms"] == []
    assert text_item["ct_codelist"] is None
    assert text_item["unit_definitions"] == []
    assert text_item["is_adam_param_specific"] is False

    # Verify activity_instance_class is present on the activity instance
    assert item["activity_instance_class"] is not None
    assert item["activity_instance_class"]["uid"] is not None
    assert (
        item["activity_instance_class"]["name"] == "Randomized activity instance class"
    )

    # Verify activity instances without items have empty list
    items_without_activity_items = [
        item for item in res["items"] if len(item.get("activity_items", [])) == 0
    ]
    assert (
        len(items_without_activity_items) > 0
    ), "Expected some activity instances without activity items"
    for item in items_without_activity_items:
        assert item["activity_items"] == []


def test_get_library_activity_instances_invalid_pagination_params(api_client):
    response = api_client.get(f"{BASE_URL}/library/activity-instances?page_size=0")
    assert_response_status_code(response, 400)
    assert (
        response.json()["details"][0]["msg"]
        == "Input should be greater than or equal to 1"
    )

    response = api_client.get(
        f"{BASE_URL}/studies?page_size={settings.max_page_size + 1}"
    )
    assert_response_status_code(response, 400)
    assert (
        response.json()["details"][0]["msg"]
        == "Input should be less than or equal to 1000"
    )

    response = api_client.get(
        f"{BASE_URL}/studies?page_number={settings.max_int_neo4j + 1}&page_size=1"
    )
    assert_response_status_code(response, 400)
    response_data = response.json()
    assert response_data["message"] == "The request failed due to validation errors"
    assert response_data["details"][0]["error_code"] == "less_than_equal"
    assert (
        response_data["details"][0]["msg"]
        == "Input should be less than or equal to 1000000000"
    )
