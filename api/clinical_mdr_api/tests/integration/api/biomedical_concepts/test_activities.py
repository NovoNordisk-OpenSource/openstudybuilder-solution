"""
Tests for /concepts/activities/activities endpoints
"""

import logging
from functools import reduce
from operator import itemgetter
from typing import Any
from unittest import mock

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
    ActivityCreateInput,
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
from clinical_mdr_api.tests.integration.utils.utils import (
    SPONSOR_LIBRARY_NAME,
    TestUtils,
)
from clinical_mdr_api.tests.utils.checks import (
    assert_response_content_type,
    assert_response_status_code,
    parse_json_response,
)
from common.config import settings

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
activity_with_multiple_groupings: Activity
activity_instances_all: list[ActivityInstance]
activity_instance_classes: list[ActivityInstanceClass]
activity_items: list[ActivityItem]
activity_item_classes: list[ActivityItemClass]
ct_terms: list[CTTerm]
role_term: CTTerm
data_type_term: CTTerm
archived_activities: list[Activity]
archived_activity_group: ActivityGroup
archived_activity_subgroup: ActivitySubGroup
activity_with_archived_groupings: Activity


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """
    Initializes a clean database with test data

    Creates multiple ActivityGroup, ActivitySubGroup, Activity, and ActivityInstance entities
    in a clean database, some with multiple groupings and multiple versions,
    and some archived activities.
    """

    db_name = "activities.api"
    inject_and_clear_db(db_name)
    inject_base_data(inject_unit_dimension=True)

    global activity_group
    activity_group = TestUtils.create_activity_group(name="activity_group")

    global different_activity_group
    different_activity_group = TestUtils.create_activity_group(
        name="different activity_group"
    )

    global archived_activity_group
    archived_activity_group = TestUtils.create_activity_group(
        name="Archive #ActivityGroup"
    )

    global activity_subgroup
    activity_subgroup = TestUtils.create_activity_subgroup(name="activity_subgroup")

    global different_activity_subgroup
    different_activity_subgroup = TestUtils.create_activity_subgroup(
        name="different activity_subgroup"
    )

    global archived_activity_subgroup
    archived_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Archive #ActivitySubGroup"
    )

    global activity_with_multiple_groupings
    activity_with_multiple_groupings = TestUtils.create_activity(
        name="Activity with multiple groupings",
        activity_subgroups=[activity_subgroup.uid, different_activity_subgroup.uid],
        activity_groups=[activity_group.uid, different_activity_group.uid],
    )

    global activities_all
    activities_all = [
        TestUtils.create_activity(
            name="name-AAA",
            synonyms=["name1", "AAA"],
            definition="def-AAA",
            abbreviation="abbr-AAA",
            nci_concept_id="nci-id-AAA",
            nci_concept_name="nci-name-AAA",
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
        ),
        TestUtils.create_activity(
            name="name-BBB",
            synonyms=["name2", "BBB"],
            definition="def-BBB",
            abbreviation="abbr-BBB",
            nci_concept_id="nci-id-BBB",
            nci_concept_name="nci-name-BBB",
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
        ),
        TestUtils.create_activity(
            name="name-CCC",
            synonyms=["name3", "CCC"],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            definition="def-CCC",
            abbreviation="abbr-CCC",
            nci_concept_id="nci-id-CCC",
            nci_concept_name="nci-name-CCC",
            is_data_collected=True,
        ),
        activity_with_multiple_groupings,
    ]

    global archived_activities
    archived_activities = [
        TestUtils.create_activity(
            name="Older Activity #A",
            definition="1st activity to archive #A",
            abbreviation="arch-ACT#A",
            activity_subgroups=[different_activity_subgroup.uid],
            activity_groups=[different_activity_group.uid],
            library_name=settings.requested_library_name,
            request_rationale="testing archiving of activities #A",
            nci_concept_name="nci-#Act",
        ),
        TestUtils.create_activity(
            name="Old #A3 Activity",
            definition="3nd #A activity to archive",
            abbreviation="arch-#ACT3",
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            synonyms=[
                "Old3 #Activity",
            ],
            approve=False,
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

    archived_activities.append(
        TestUtils.create_activity(
            name="Old #A Activity",
            definition="2nd #A activity to archive",
            abbreviation="arch-#ACT2",
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            synonyms=[
                "Stara #Activity",
                "#Activity Viejo",
            ],
        ),
    )
    archived_activities.append(
        TestUtils.create_activity(
            name="another archived Activity #A",
            definition="to archive #A",
            abbreviation="arch-ACT1#A",
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[different_activity_group.uid],
            library_name=settings.requested_library_name,
            nci_concept_name="nci-#Act",
            approve=False,
        )
    )

    global activity_with_archived_groupings
    activities_all.append(
        activity_with_archived_groupings := TestUtils.create_activity(
            name="Activity with archived groupings",
            activity_groups=[activity_group.uid, archived_activity_group.uid],
            activity_subgroups=[archived_activity_subgroup.uid, activity_subgroup.uid],
            approve=False,
        )
    )
    TestUtils.archive_activity_subgroup(archived_activity_subgroup.uid)
    TestUtils.archive_activity_group(archived_activity_group.uid)

    global activity_instance_classes
    activity_instance_classes = [
        TestUtils.create_activity_instance_class(name="Activity instance class 1"),
        TestUtils.create_activity_instance_class(name="Activity instance class 2"),
        TestUtils.create_activity_instance_class(name="Activity instance class 3"),
    ]
    global activity_item_classes
    global data_type_term
    global role_term
    data_type_codelist = TestUtils.create_ct_codelist(
        name="DATATYPE", submission_value="DATATYPE", extensible=True, approve=True
    )
    data_type_term = TestUtils.create_ct_term(
        nci_preferred_name="Data type",
        sponsor_preferred_name="Data type",
        codelist_uid=data_type_codelist.codelist_uid,
    )
    role_codelist = TestUtils.create_ct_codelist(
        name="ROLE", submission_value="ROLE", extensible=True, approve=True
    )
    role_term = TestUtils.create_ct_term(
        sponsor_preferred_name="Role", codelist_uid=role_codelist.codelist_uid
    )
    activity_item_classes = [
        TestUtils.create_activity_item_class(
            name="Activity Item Class name1",
            order=1,
            activity_instance_classes=[
                {
                    "uid": activity_instance_classes[0].uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": True,
                    "is_additional_optional": False,
                    "is_default_linked": False,
                }
            ],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
        TestUtils.create_activity_item_class(
            name="Activity Item Class name2",
            order=2,
            activity_instance_classes=[
                {
                    "uid": activity_instance_classes[1].uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": True,
                    "is_additional_optional": False,
                    "is_default_linked": False,
                }
            ],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
        TestUtils.create_activity_item_class(
            name="Activity Item Class name3",
            order=3,
            activity_instance_classes=[
                {
                    "uid": activity_instance_classes[2].uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": True,
                    "is_additional_optional": False,
                    "is_default_linked": False,
                }
            ],
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
            "ct_terms": [
                {
                    "term_uid": ct_terms[0].term_uid,
                    "codelist_uid": codelist.codelist_uid,
                }
            ],
            "unit_definition_uids": [],
            "is_adam_param_specific": False,
            "odm_form_uid": None,
            "odm_item_group_uid": None,
            "odm_item_uid": None,
        },
        {
            "activity_item_class_uid": activity_item_classes[1].uid,
            "ct_terms": [
                {
                    "term_uid": ct_terms[1].term_uid,
                    "codelist_uid": codelist.codelist_uid,
                }
            ],
            "unit_definition_uids": [],
            "is_adam_param_specific": False,
            "odm_form_uid": None,
            "odm_item_group_uid": None,
            "odm_item_uid": None,
        },
        {
            "activity_item_class_uid": activity_item_classes[2].uid,
            "ct_terms": [
                {
                    "term_uid": ct_terms[0].term_uid,
                    "codelist_uid": codelist.codelist_uid,
                },
                {
                    "term_uid": ct_terms[1].term_uid,
                    "codelist_uid": codelist.codelist_uid,
                },
            ],
            "unit_definition_uids": [],
            "is_adam_param_specific": False,
            "odm_form_uid": None,
            "odm_item_group_uid": None,
            "odm_item_uid": None,
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
        TestUtils.create_activity_instance(
            name="name multiple 1",
            activity_instance_class_uid=activity_instance_classes[0].uid,
            name_sentence_case="name multiple 1",
            topic_code="topic code multiple 1",
            is_required_for_activity=True,
            activities=[activity_with_multiple_groupings.uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[activity_items[0], activity_items[1], activity_items[2]],
        ),
        TestUtils.create_activity_instance(
            name="name multiple 2",
            activity_instance_class_uid=activity_instance_classes[0].uid,
            name_sentence_case="name multiple 2",
            topic_code="topic code multiple 2",
            is_required_for_activity=True,
            activities=[activity_with_multiple_groupings.uid],
            activity_subgroups=[different_activity_subgroup.uid],
            activity_groups=[different_activity_group.uid],
            activity_items=[activity_items[0], activity_items[1], activity_items[2]],
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

    for activity in archived_activities:
        TestUtils.archive_activity(activity.uid)


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
    "activity_instances",
    "request_rationale",
    "is_request_final",
    "is_request_rejected",
    "contact_person",
    "reason_for_rejecting",
    "used_by_studies",
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
    """
    SCENARIO: getting a single Activity by uid
    GIVEN: an existing Activity with all fields filled in the database
    WHEN: GET /concepts/activities/activities/{uid}
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing all the fields of the Activity with correct values.
    """

    response = api_client.get(
        f"/concepts/activities/activities/{activities_all[0].uid}"
    )
    res = parse_json_response(response, assert_status=200)

    # Check fields included in the response
    assert set(res.keys()) == set(ACTIVITY_FIELDS_ALL)
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
    assert len(res["activity_instances"]) == 5
    assert res["activity_instances"][0]["uid"] == activity_instances_all[0].uid
    assert res["activity_instances"][0]["name"] == activity_instances_all[0].name
    assert res["activity_instances"][1]["uid"] == activity_instances_all[3].uid
    assert res["activity_instances"][1]["name"] == activity_instances_all[3].name
    assert res["activity_instances"][2]["uid"] == activity_instances_all[4].uid
    assert res["activity_instances"][2]["name"] == activity_instances_all[4].name
    assert res["activity_instances"][3]["uid"] == activity_instances_all[1].uid
    assert res["activity_instances"][3]["name"] == activity_instances_all[1].name
    assert res["activity_instances"][4]["uid"] == activity_instances_all[2].uid
    assert res["activity_instances"][4]["name"] == activity_instances_all[2].name

    assert res["library_name"] == SPONSOR_LIBRARY_NAME
    assert res["definition"] == "def-AAA"
    assert res["abbreviation"] == "abbr-AAA"
    assert res["is_multiple_selection_allowed"] is True
    assert res["is_finalized"] is False
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert res["possible_actions"] == ["inactivate", "new_version"]


@pytest.mark.parametrize("page_size", [0, 1000, 100, 33, None, 14, 7])
def test_get_activities(api_client, page_size: int | None, archived: bool = False):
    """
    SCENARIO: listing Activities with various page_size values
    GIVEN: multiple Activities in the database, some archived
    WHEN: GET /concepts/activities/activities?page_size={page_size}
    THEN: should respond with 200 HTTP status code and a paginated JSON payload,
          containing up to page_size items (or default_page_size when page_size is None),
          each item having all expected fields with obligatory fields non-nullable,
          and only Activities from the requested library (non-archived by default).
    """

    params = {}
    if archived:
        params["library_name"] = settings.archived_library_name
    if page_size is not None:
        params["page_size"] = page_size

    expected_num_items = len(archived_activities) if archived else len(activities_all)
    expected_num_items = min(
        page_size or settings.default_page_size, expected_num_items
    )
    expected_uids = {
        activity.uid
        for activity in (archived_activities if archived else activities_all)
    }

    response = api_client.get("/concepts/activities/activities", params=params)
    payload = parse_json_response(response)

    # Check CustomPage fields are included
    assert set(payload.keys()) == {"items", "total", "page", "size"}
    assert payload["total"] == 0
    assert payload["page"] == 1
    assert payload["size"] == (
        settings.default_page_size if page_size is None else page_size
    )
    assert payload["items"]

    # Check number of items
    assert len(payload["items"]) == expected_num_items

    # Check each item
    for item in payload["items"]:
        # Check all expected fields are included
        assert set(list(item.keys())) == set(ACTIVITY_FIELDS_ALL)
        # Check obligatory fields are non-nullable
        for key in ACTIVITY_FIELDS_NOT_NULL:
            assert item[key] is not None
        # Check that Activity is in the expected set
        assert item["uid"] in expected_uids


@pytest.mark.parametrize("page_size", [1, None, 7])
def test_get_archived_activities(api_client, page_size: int | None):
    """
    SCENARIO: getting archived Activities without pagination
    GIVEN: multiple Activities in the database, some archived
    WHEN: GET /concepts/activities/activities?library=Archived&page_size={page_size}
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing Archived Activities only,
          with all fields of each Activity included and obligatory fields non-nullable.
    """
    test_get_activities(api_client, page_size, archived=True)


def test_get_activity_pagination(api_client):
    """
    SCENARIO: getting Activities with pagination and sorting
    GIVEN: multiple existing Activities in the database
    WHEN: GET /concepts/activities/activities?page_number={page_number}&page_size={page_size}&sort_by={sort_by}
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the correct page of results sorted by specified field in correct order,
          and the total number of results,
          excluding archived activities.
    """

    results_paginated: dict[Any, Any] = {}
    sort_by = '{"name": true}'
    page_size = 3
    num_pages = (len(activities_all) + page_size - 1) // page_size
    for page_number in range(1, num_pages + 1):
        url = f"/concepts/activities/activities?page_number={page_number}&page_size={page_size}&sort_by={sort_by}"
        res = parse_json_response(api_client.get(url), assert_status=200)
        res_names = [item["name"] for item in res["items"]]
        results_paginated[page_number] = res_names
        log.info("Page %s: %s", page_number, res_names)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        reduce(lambda a, b: list(a) + list(b), list(results_paginated.values()))
    )

    log.info("All rows returned by pagination: %s", results_paginated_merged)

    res_all = parse_json_response(
        api_client.get(
            f"/concepts/activities/activities?page_number=1&page_size=100&sort_by={sort_by}"
        ),
        assert_status=200,
    )
    results_all_in_one_page = list(map(lambda x: x["name"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(activities_all) == len(results_paginated_merged)
    assert results_all_in_one_page == sorted(results_all_in_one_page)

    # Ascending order applied to ActivityGroup name
    sort_by = '{"activity_groupings[0].activity_group_name":true}'
    res_all = parse_json_response(
        api_client.get(
            f"/concepts/activities/activities?page_number=1&page_size=100&sort_by={sort_by}"
        ),
        assert_status=200,
    )
    all_results = [
        item["activity_groupings"][0]["activity_group_name"]
        for item in res_all["items"]
    ]
    assert all_results == sorted(
        all_results
    ), "Results should be returned by ActivityGroup name ascending order"

    # Descending order applied to ActivityGroup name
    sort_by = '{"activity_groupings[0].activity_group_name":false}'
    res_all = parse_json_response(
        api_client.get(
            f"/concepts/activities/activities?page_number=1&page_size=100&sort_by={sort_by}"
        ),
        assert_status=200,
    )
    all_results = [
        item["activity_groupings"][0]["activity_group_name"]
        for item in res_all["items"]
    ]
    assert all_results == sorted(
        all_results, reverse=True
    ), "Results should be returned by ActivityGroup name descending order"

    # Ascending order applied to ActivitySubGroup name
    sort_by = '{"activity_groupings[0].activity_subgroup_name":true}'
    res_all = parse_json_response(
        api_client.get(
            f"/concepts/activities/activities?page_number=1&page_size=100&sort_by={sort_by}"
        ),
        assert_status=200,
    )
    all_results = [
        item["activity_groupings"][0]["activity_subgroup_name"]
        for item in res_all["items"]
    ]
    assert all_results == sorted(
        all_results
    ), "Results should be returned by ActivitySubGroup name ascending order"

    # Descending order applied to ActivitySubGroup name
    sort_by = '{"activity_groupings[0].activity_subgroup_name":false}'
    res_all = parse_json_response(
        api_client.get(
            f"/concepts/activities/activities?page_number=1&page_size=100&sort_by={sort_by}"
        ),
        assert_status=200,
    )
    all_results = [
        item["activity_groupings"][0]["activity_subgroup_name"]
        for item in res_all["items"]
    ]
    assert all_results == sorted(
        all_results, reverse=True
    ), "Results should be returned by ActivitySubGroup name descending order"


def test_get_activity_versions(api_client):
    """
    SCENARIO: getting all versions of all Activities
    GIVEN: multiple existing Activities in the database, some of them having multiple versions
    WHEN: GET /concepts/activities/activities/versions?page_size={page_size}
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing all versions of all Activities sorted by start_date descending,
          excluding archived Activities,
          with all fields of each version included and obligatory fields non-nullable.
    """
    # Create a new version of an activity
    response = api_client.post(
        f"/concepts/activities/activities/{activities_all[0].uid}/versions"
    )
    assert_response_status_code(response, 201)

    # Get all versions of all activities
    response = api_client.get("/concepts/activities/activities/versions?page_size=100")
    res = parse_json_response(response, assert_status=200)

    # Check fields included in the response
    assert set(res.keys()) == set(["items", "total", "page", "size"])

    assert len(res["items"]) == len(activities_all) * 2
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
    ],
)
def test_filtering_versions_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    """
    SCENARIO: filtering versions of Activities by a value contained in any of the fields
    GIVEN: multiple existing Activities in the database, some with multiple versions
    WHEN: GET /concepts/activities/activities/versions?filters={filter_by}
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing only versions of Activities where at least one field's value
          contains the filter value as a substring, case-insensitively,
          with the field that matched the filter value being the expected_matched_field,
          and the value of that field starting with the expected_result_prefix.
          If expected_result_prefix is None, then no versions should be returned.
    """

    url = f"/concepts/activities/activities/versions?filters={filter_by}"
    response = api_client.get(url)
    res = parse_json_response(response, assert_status=200)

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
    """
    SCENARIO: filtering versions of Activities by a value contained in a specific field
    GIVEN: multiple existing Activities in the database, some with multiple versions
    WHEN: GET /concepts/activities/activities/versions?filters={filter_by}
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing only versions of Activities where the value of the expected_matched_field
          is equal to the filter value, with the value of that field being the expected_result.
          If expected_result is None, then no versions should be returned.
    """

    url = f"/concepts/activities/activities/versions?filters={filter_by}"
    response = api_client.get(url)
    res = parse_json_response(response, assert_status=200)

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


def test_explicit_filtering_by_activity_subgroup_and_group_uid(api_client):
    url = "/concepts/activities/activities"
    response = api_client.get(
        url,
        params={
            "activity_subgroup_uid": different_activity_subgroup.uid,
            "activity_group_uid": activity_group.uid,
        },
    )
    res = parse_json_response(response, assert_status=200)["items"]
    assert len(res) == 0

    response = api_client.get(
        url,
        params={
            "activity_subgroup_uid": different_activity_subgroup.uid,
            "activity_group_uid": different_activity_group.uid,
        },
    )
    res = parse_json_response(response, assert_status=200)["items"]
    assert len(res) == 6
    assert res[0]["uid"] == activity_with_multiple_groupings.uid

    assert (
        res[0]["activity_groupings"][0]["activity_subgroup_uid"]
        == activity_subgroup.uid
    )
    assert res[0]["activity_groupings"][0]["activity_group_uid"] == activity_group.uid
    assert (
        res[0]["activity_groupings"][1]["activity_subgroup_uid"]
        == different_activity_subgroup.uid
    )
    assert (
        res[0]["activity_groupings"][1]["activity_group_uid"]
        == different_activity_group.uid
    )

    response = api_client.get(
        url,
        params={
            "activity_subgroup_uid": activity_subgroup.uid,
            "activity_group_uid": different_activity_group.uid,
        },
    )
    res = parse_json_response(response, assert_status=200)["items"]
    assert len(res) == 0


def test_grouped_groupings_payload_flag(api_client):
    """
    SCENARIO: getting Activities with group_by_groupings flag set to true or false
    GIVEN: multiple existing Activities in the database,
           some of them having multiple groupings and multiple instances
    WHEN: GET /concepts/activities/activities?group_by_groupings={group_by_groupings}
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the same set of Activities and the same total number of activity instances,
          but with different structure of activity_groupings and activity_instances fields,
          depending on the value of group_by_groupings flag.
          If group_by_groupings=True, then each activity should be returned once
          for each combination of groupings it has, with only the instances linked to
          that specific combination of groupings included in the activity_instances field,
          and the activity_groupings field containing only that specific combination of groupings.
          If group_by_groupings=False, then each activity should be returned only once,
          with all instances linked to it included in the activity_instances field,
          and the activity_groupings field containing all groupings linked to the activity.
    """

    url = "/concepts/activities/activities"

    # ====== Test preconditions ======

    # Get activities with group_by_groupings=True
    response = api_client.get(
        url,
        params={
            "group_by_groupings": True,
            "page_size": 0,
        },
    )
    items = parse_json_response(response, assert_status=200)["items"]

    assert any(
        len(activity["activity_groupings"]) > 1 for activity in items
    ), "Test precondition failed: At least one activity should have multiple groupings"
    assert any(
        len(activity["activity_instances"]) > 1 for activity in items
    ), "Test precondition failed: At least one activity should have multiple instances"

    # Check that the activity with multiple groupings is present and has two instances linked to it
    assert any(
        activity["uid"] == activity_with_multiple_groupings.uid for activity in items
    ), "Test precondition failed: The activity with multiple groupings is not present in the response"

    # Collect groupings and number of instances for later comparison
    grouped_groupings = set()
    nbr_instances_grouped = 0
    for activity in items:
        if activity["uid"] == activity_with_multiple_groupings.uid:
            assert (
                len(activity["activity_instances"]) == 2
            ), "Test precondition failed: The activity with multiple groupings should have two instances linked to it"
            assert (
                len(activity["activity_groupings"]) == 2
            ), "Test precondition failed: The activity with multiple groupings should have two groupings"
        nbr_instances_grouped += len(activity["activity_instances"])
        for grouping in activity["activity_groupings"]:
            grouped_groupings.add(
                (
                    activity["uid"],
                    grouping["activity_group_uid"],
                    grouping["activity_subgroup_uid"],
                )
            )

    # ===== Test the group_by_groupings=False behavior ======

    response = api_client.get(
        url,
        params={
            "group_by_groupings": False,
            "page_size": 0,
        },
    )
    items = parse_json_response(response, assert_status=200)["items"]

    ungrouped_groupings = set()
    nbr_instances_ungrouped = 0
    for activity in items:
        nbr_instances_ungrouped += len(activity["activity_instances"])
        if activity["uid"] == activity_with_multiple_groupings.uid:
            assert (
                len(activity["activity_instances"]) == 1
            ), "In ungrouped mode, the activity with multiple groupings should have one instance linked to it"
        assert (
            len(activity["activity_groupings"]) <= 1
        ), "When group_by_groupings=False, each activity should have at most one grouping"
        for grouping in activity["activity_groupings"]:
            ungrouped_groupings.add(
                (
                    activity["uid"],
                    grouping["activity_group_uid"],
                    grouping["activity_subgroup_uid"],
                )
            )
    assert grouped_groupings == ungrouped_groupings, (
        "The set of activity-grouping combinations should be the same "
        "regardless of the group_by_groupings flag"
    )
    assert nbr_instances_grouped == nbr_instances_ungrouped, (
        "The total number of activity instances should be the same "
        "regardless of the group_by_groupings flag"
    )


def test_activity_overview(api_client):
    """
    SCENARIO: getting an overview of an Activity
    GIVEN: multiple Activities in the database, some archived
    WHEN: GET /concepts/activities/activities/{uid}/overview
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the overview of the Activity.
    """

    for activity in activities_all + archived_activities:
        print(activity)
        response = api_client.get(
            f"/concepts/activities/activities/{activity.uid}/overview"
        )
        res = parse_json_response(response, assert_status=200)
        assert res["activity"]["name"] == activity.name


def test_activity_cosmos_overview(api_client):
    """
    SCENARIO: getting an overview of an Activity in Cosmos format
    GIVEN: multiple Activities in the database, some archived
    WHEN: GET /concepts/activities/activities/{uid}/overview.cosmos
    THEN: should respond with 200 HTTP status code and YAML payload,
          containing the overview of the Activity in Cosmos format with correct values.
    """

    for activity in activities_all + archived_activities:
        response = api_client.get(
            f"/concepts/activities/activities/{activity.uid}/overview.cosmos"
        )

        assert_response_status_code(response, 200)
        assert_response_content_type(response, "application/x-yaml")

        res = yaml.load(response.text, Loader=yaml.SafeLoader)

        assert res["shortName"] == activity.name
        if activity is activities_all[1]:
            assert (
                res["dataElementConcepts"][0]["shortName"]
                == "Activity Item Class name2"
            )
            assert res["dataElementConcepts"][0]["dataType"] == "Data type"


def test_create_activity_unique_name_validation(api_client):
    """
    SCENARIO: creating an Activity with a name that already exists in the same Library
    GIVEN: an existing Activity with a specific name in the database
    WHEN: POST /concepts/activities/activities with the same name and library_name in the request body
    THEN: should respond with 409 HTTP status code and JSON payload,
          containing the error message that an Activity with the same name already exists.
    WHEN: creating an Activity with the same name but in a different Library,
    THEN: it should be created successfully with 201 HTTP status code
          and JSON payload containing the created Activity's details.
    """

    activity_name = TestUtils.random_str(20, "ActivityName-")
    activity_name2 = TestUtils.random_str(20, "ActivityName-")
    TestUtils.create_activity(
        name=activity_name,
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        approve=False,
        library_name=settings.requested_library_name,
    )
    TestUtils.create_activity(
        name=activity_name2,
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        approve=True,
        library_name=settings.requested_library_name,
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
            "library_name": settings.requested_library_name,
        },
    )
    res = parse_json_response(response, assert_status=409)
    assert res["message"] == f"Activity with Name '{activity_name}' already exists."

    # Create activity with the same name as the first one but in different Library
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
            "library_name": SPONSOR_LIBRARY_NAME,
        },
    )
    res = parse_json_response(response, assert_status=201)
    assert res["name"] == activity_name
    assert res["library_name"] == SPONSOR_LIBRARY_NAME

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
            "library_name": settings.requested_library_name,
        },
    )
    res = parse_json_response(response, assert_status=409)
    assert res["message"] == f"Activity with Name '{activity_name2}' already exists."


def test_update_activity_to_new_grouping(api_client):
    """
    SCENARIO: updating an Activity to link it to a new version of an Activity Subgroup and its corresponding Activity Group
    GIVEN: an existing Activity linked to a specific version of an Activity Subgroup and Activity Group
    WHEN: updating the Activity to link it to a new version of the same Activity Subgroup and its corresponding Activity Group
    THEN: should respond with 200 HTTP status code and JSON payload,
          the Activity should be updated to link to the new version of the Activity Subgroup and its
          corresponding Activity Group, and the version and status of the Activity should be updated to reflect the change.
    WHEN: getting the updated Activity,
    THEN: it should show the new version of the Activity Subgroup
          and its corresponding Activity Group in the activity_groupings field.
    """

    group_name = "original group name"
    original_subgroup_name = "original subgroup name"
    edited_subgroup_name = "edited subgroup name"
    activity_name = "original activity name"

    # ==== Create group, subgroup, activity and activity instance ====
    group = TestUtils.create_activity_group(name=group_name)

    subgroup = TestUtils.create_activity_subgroup(name=original_subgroup_name)
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
    assert_response_status_code(response, 201)

    # Update the subgroup
    response = api_client.put(
        f"/concepts/activities/activity-sub-groups/{subgroup.uid}",
        json={
            "name": edited_subgroup_name,
            "name_sentence_case": edited_subgroup_name,
            "library_name": subgroup.library_name,
            "change_description": "update group",
        },
    )
    assert_response_status_code(response, 200)

    # Approve the subgroup
    response = api_client.post(
        f"/concepts/activities/activity-sub-groups/{subgroup.uid}/approvals"
    )

    # === Assert that the subgroup was updated as expected ===
    response = api_client.get(
        f"/concepts/activities/activity-sub-groups/{subgroup.uid}"
    )

    res = parse_json_response(response, assert_status=200)

    assert res["name"] == edited_subgroup_name

    assert res["version"] == "2.0"
    assert res["status"] == "Final"

    # ==== Update activity ====

    # Create new version of activity
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/versions",
        json={},
    )
    assert_response_status_code(response, 201)

    # Update the activity, no change but groupings should be updated to latest version
    response = api_client.put(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "name": activity.name,
            "name_sentence_case": activity.name_sentence_case,
            "activity_groupings": [
                {"activity_group_uid": group.uid, "activity_subgroup_uid": subgroup.uid}
            ],
            "library_name": activity.library_name,
            "change_description": "update activity",
        },
    )
    assert_response_status_code(response, 200)

    # Approve the activity
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # Get the activity by uid and assert that it was updated to the new subgroup version
    response = api_client.get(f"/concepts/activities/activities/{activity.uid}")
    res = parse_json_response(response, assert_status=200)

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
    """
    SCENARIO: updating an Activity's synonyms and groupings
    GIVEN: an existing approved Activity in the database
    WHEN: PUT /concepts/activities/activities/{uid} with updated synonyms and an additional grouping
    THEN: should respond with 200 HTTP status code and JSON payload,
          the Activity should be in Draft status at version 1.2,
          with the updated synonyms and two groupings (original + new) reflected in the response.
    """

    # Create a new version of an activity
    activity = activities_all[2]
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/versions"
    )
    assert_response_status_code(response, 201)

    response = api_client.put(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "name": activity.name,
            "name_sentence_case": activity.name_sentence_case,
            "synonyms": ["new name", "CCC"],
            "activity_groupings": [
                activity.activity_groupings[0].model_dump(),
                ActivityGrouping(
                    activity_group_uid=different_activity_group.uid,
                    activity_subgroup_uid=different_activity_subgroup.uid,
                ).model_dump(),
            ],
            "change_description": "Updated synonyms and groupings",
        },
    )
    res = parse_json_response(response, assert_status=200)

    assert res["uid"] == activity.uid
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

    assert res["library_name"] == SPONSOR_LIBRARY_NAME
    assert res["definition"] is None
    assert res["is_multiple_selection_allowed"] is True
    assert res["is_finalized"] is False
    assert res["version"] == "1.2"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "edit"]


def test_cannot_create_activity_with_non_unique_synonyms(api_client):
    """
    SCENARIO: creating an Activity with synonyms that already exist for another Activity
    GIVEN: an existing Activity with specific synonyms in the database
    WHEN: POST /concepts/activities/activities with the same synonyms in the request body
    THEN: should respond with 409 HTTP status code and JSON payload,
          containing the error message that the provided synonyms are
          not unique and the list of Activities that already have those synonyms.
    """

    # Create an activity with the same synonyms as an activity created in the test data
    response = api_client.post(
        "/concepts/activities/activities",
        json={
            "name": "cannot create",
            "name_sentence_case": "cannot create",
            "synonyms": ["name2", "XXX"],
            "library_name": SPONSOR_LIBRARY_NAME,
        },
    )
    assert_response_status_code(response, 409)
    res = parse_json_response(response, assert_status=409)

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "Following Activities already have the provided synonyms: {'Activity_000003': ['name2']}"
    )


def test_cannot_update_activity_with_non_unique_synonyms(api_client):
    """
    SCENARIO: updating an Activity with synonyms that already exist for another Activity
    GIVEN: an existing Activity with specific synonyms in the database,
           and another existing Activity with different synonyms in the database
    WHEN: updating the first Activity to have the same synonyms as the second Activity
    THEN: should respond with 409 HTTP status code and JSON payload,
          containing the error message that the provided synonyms are not unique
          and the list of Activities that already have those synonyms.
    """

    new_activity1 = TestUtils.create_activity(
        name="test1",
        synonyms=["XYZ1", "non_unique1"],
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
    )
    new_activity2 = TestUtils.create_activity(
        name="test2",
        synonyms=["XYZ2", "non_unique2"],
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
    )

    activity = activities_all[0]
    response = api_client.put(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "name": activity.name,
            "name_sentence_case": activity.name_sentence_case,
            "synonyms": ["non_unique1", "non_unique2"],
            "change_description": "Updated synonyms",
        },
    )
    assert_response_status_code(response, 409)
    res = parse_json_response(response, assert_status=409)

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == f"Following Activities already have the provided synonyms: {{'{new_activity1.uid}': ['non_unique1'], '{new_activity2.uid}': ['non_unique2']}}"
    )


@pytest.mark.parametrize(
    "field_name, search_string",
    [
        ("name", "name-CCC"),
        ("name_sentence_case", "name-CCC"),
        # ("synonyms", "CCC"),
        ("library_name", SPONSOR_LIBRARY_NAME),
        ("definition", "def"),
        ("abbreviation", "ab"),
        ("nci_concept_id", "nci"),
        ("nci_concept_name", "nci"),
        ("is_data_collected", "t"),
        ("is_used_by_legacy_instances", "f"),
        ("start_date", "20"),
        ("version", "1.0"),
        ("status", "Final"),
        ("author_username", "unknown-user"),
    ],
)
def test_get_activities_headers(api_client, field_name, search_string):
    """
    SCENARIO: getting headers of Activities filtered by a search string in a specific field
    GIVEN: multiple existing Activities in the database, some of which are archived (with '#a' in name)
    WHEN: GET /concepts/activities/activities/headers?field_name={field_name}&search_string={search_string}&lite={lite}
    THEN: should respond with 200 HTTP status code and a list payload,
          with at least 1 result whose value contains the search string case-insensitively,
          and archived Activity names (containing '#a') excluded from all results.
    """

    for lite in [True, False]:
        query_params = {
            "field_name": field_name,
            "search_string": search_string,
            "lite": lite,
        }
        response = api_client.get(
            "/concepts/activities/activities/headers", params=query_params
        )
        payload = parse_json_response(response, assert_status=200)
        assert isinstance(payload, list)
        assert len(payload) >= 1

        expected = str(search_string).lower()
        for res in payload:
            lower = str(res).lower()
            assert expected in lower
            assert "#a" not in lower


def test_archived_activity_excluded_from_headers(api_client):
    """
    SCENARIO: getting headers of Activities with archived Activities in the database
    GIVEN: an existing Activity in the database, and the same Activity archived
    WHEN: GET /concepts/activities/activities/headers?field_name=name&search_string=canary&lite={lite}
    THEN: should respond with 200 HTTP status code and JSON payload,
          with the header of the Activity included in the results when it is not archived
          and excluded from the results when it is archived, regardless of the value of lite parameter.
    """

    def get_activity_headers():
        query_params = {
            "field_name": "name",
        }
        if search_string is not None:
            query_params["search_string"] = search_string
        if lite is not None:
            query_params["lite"] = str(lite)
        response = api_client.get(
            "/concepts/activities/activities/headers", params=query_params
        )
        payload = parse_json_response(response, assert_status=200)
        assert isinstance(payload, list)
        return payload

    # create an Activity
    activity = TestUtils.create_activity(
        name="A Canary activity",
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        approve=True,
    )

    # get headers, results should include the activity
    for lite in (True, False, None):
        for search_string in ("act", "canary", None):
            results = get_activity_headers()
            assert len(results) > 0
            assert activity.name in results

    # archive the activity
    TestUtils.archive_activity(activity.uid)

    # get headers, results should exclude the archived activity
    for lite in (True, False, None):
        for search_string in ("act", "canary", None):
            results = get_activity_headers()
            if search_string == "canary":
                assert len(results) == 0
            else:
                assert len(results) > 0
            assert activity.name not in results


def test_cascade_edit_activities(api_client):
    """
    SCENARIO: editing an Activity with cascade_edit_and_approve flag
    GIVEN: an existing Activity linked to an Activity Instance in the database
    WHEN: updating the Activity multiple times with cascade_edit_and_approve=True (adding groupings, then removing one)
    THEN: the linked Activity Instance should be bumped to a new Final version after each cascade approval,
          reflecting the Activity's latest groupings, and intermediate draft versions should not persist.
    WHEN: updating the Activity with cascade_edit_and_approve=False
    THEN: the linked Activity Instance should remain at its current version unchanged.
    """

    # ==== Create activity and activity instance ====
    activity = TestUtils.create_activity(
        name="Cascade Activity",
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        approve=True,
    )
    activity_instance = TestUtils.create_activity_instance(
        name="Cascade Activity Instance",
        activity_instance_class_uid=activity_instance_classes[0].uid,
        name_sentence_case="cascade activity instance",
        nci_concept_id="C-1234",
        topic_code="cascade activity instance tc",
        activities=[activity.uid],
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        activity_items=[activity_items[0]],
        approve=True,
    )
    response = api_client.get(
        f"/concepts/activities/activity-instances/{activity_instance.uid}"
    )

    res = parse_json_response(response, assert_status=200)
    assert res["name"] == "Cascade Activity Instance"
    assert len(res["activity_groupings"]) == 1
    assert res["activity_groupings"][0]["activity"]["uid"] == activity.uid
    assert res["activity_groupings"][0]["activity"]["name"] == activity.name
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["uid"]
        == activity_subgroup.uid
    )
    assert (
        res["activity_groupings"][0]["activity_subgroup"]["name"]
        == activity_subgroup.name
    )
    assert res["activity_groupings"][0]["activity_group"]["uid"] == activity_group.uid
    assert res["activity_groupings"][0]["activity_group"]["name"] == activity_group.name

    assert res["version"] == "1.0"
    assert res["status"] == "Final"

    # ==== Update activity with cascade edit&approve, instance groupings should be updated also ====

    # Create new version of activity
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/versions",
        json={},
    )
    assert_response_status_code(response, 201)

    # Update the activity
    activity_group_xyz = TestUtils.create_activity_group(name="activity_group xyz")
    activity_subgroup_xyz = TestUtils.create_activity_subgroup(
        name="activity_subgroup xyz"
    )
    response = api_client.put(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "name": "Edited Cascade Activity 1",
            "name_sentence_case": "edited cascade activity 1",
            "change_description": "test cascade edit",
            "library_name": activity.library_name,
            "is_data_collected": True,
            "activity_groupings": [
                {
                    "activity_group_uid": activity_group.uid,
                    "activity_subgroup_uid": activity_subgroup.uid,
                },
                {
                    "activity_group_uid": activity_group_xyz.uid,
                    "activity_subgroup_uid": activity_subgroup_xyz.uid,
                },
            ],
        },
    )
    assert_response_status_code(response, 200)

    # Approve the activity with cascade_edit_and_approve set to True
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/approvals",
        params={"cascade_edit_and_approve": True},
    )
    assert_response_status_code(response, 201)

    # Assert number of activity groupings in the instance
    response = api_client.get(
        f"/concepts/activities/activity-instances/{activity_instance.uid}"
    )
    res = parse_json_response(response, assert_status=200)
    assert len(res["activity_groupings"]) == 1

    # Update the activity by adding new activity groupings
    api_client.post(f"/concepts/activities/activities/{activity.uid}/versions")
    activity_group_zxy = TestUtils.create_activity_group(name="activity_group zyx")
    activity_subgroup_zxy = TestUtils.create_activity_subgroup(
        name="activity_subgroup zyx"
    )
    response = api_client.put(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "name": "Edited Cascade Activity 2",
            "name_sentence_case": "edited cascade activity 2",
            "change_description": "test cascade edit",
            "library_name": activity.library_name,
            "is_data_collected": True,
            "activity_groupings": [
                {
                    "activity_group_uid": activity_group.uid,
                    "activity_subgroup_uid": activity_subgroup.uid,
                },
                {
                    "activity_group_uid": activity_group_xyz.uid,
                    "activity_subgroup_uid": activity_subgroup_xyz.uid,
                },
                {
                    "activity_group_uid": activity_group_zxy.uid,
                    "activity_subgroup_uid": activity_subgroup_zxy.uid,
                },
            ],
        },
    )
    assert_response_status_code(response, 200)

    # Approve the activity with cascade_edit_and_approve set to True
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/approvals",
        params={"cascade_edit_and_approve": True},
    )
    assert_response_status_code(response, 201)

    # Get the instance and assert that it was updated
    response = api_client.get(
        f"/concepts/activities/activity-instances/{activity_instance.uid}"
    )
    res = parse_json_response(response, assert_status=200)
    assert len(res["activity_groupings"]) == 1
    assert res["groupings_version"] == "3.0"
    assert res["groupings_status"] == "Final"

    # Update the activity by removing activity grouping
    api_client.post(f"/concepts/activities/activities/{activity.uid}/versions")
    response = api_client.put(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "name": "Edited Cascade Activity 3",
            "name_sentence_case": "edited cascade activity 3",
            "change_description": "test cascade edit",
            "library_name": activity.library_name,
            "is_data_collected": True,
            "activity_groupings": [
                {
                    "activity_group_uid": activity_group_xyz.uid,
                    "activity_subgroup_uid": activity_subgroup_xyz.uid,
                },
                {
                    "activity_group_uid": activity_group_zxy.uid,
                    "activity_subgroup_uid": activity_subgroup_zxy.uid,
                },
            ],
        },
    )
    assert_response_status_code(response, 200)

    # Approve the activity with cascade_edit_and_approve set to True
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/approvals",
        params={"cascade_edit_and_approve": True},
    )
    assert_response_status_code(response, 201)

    # Get the instance and assert that it was updated
    response = api_client.get(
        f"/concepts/activities/activity-instances/{activity_instance.uid}"
    )
    res = parse_json_response(response, assert_status=200)
    assert len(res["activity_groupings"]) == 1
    assert res["groupings_version"] == "3.0"
    assert res["groupings_status"] == "Final"

    # Get the instance versions and assert that there is one new version created.
    # There should be a new final version 2.0 that links to activity version 2.0
    response = api_client.get(
        f"/concepts/activities/activity-instances/{activity_instance.uid}/groupings/versions"
    )
    res = parse_json_response(response, assert_status=200)
    unchanged_draft = TestUtils._get_version_from_list(res, "1.1")
    updated_draft = TestUtils._get_version_from_list(res, "1.2")
    new_final = TestUtils._get_version_from_list(res, "2.0")
    latest_new_final = TestUtils._get_version_from_list(res, "3.0")

    assert unchanged_draft is None
    assert updated_draft is None
    assert (
        new_final["activity_groupings"][0]["activity"]["name"]
        == "Edited Cascade Activity 1"
    )
    assert (
        latest_new_final["activity_groupings"][0]["activity"]["name"]
        == "Edited Cascade Activity 2"
    )

    # ==== Update activity without cascade edit&approve, instance should NOT be updated ====

    # Create new version of activity
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/versions",
        json={},
    )
    assert_response_status_code(response, 201)

    # Patch the activity
    response = api_client.put(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "name": "Edited Cascade Activity 4",
            "name_sentence_case": "edited cascade activity 4",
            "change_description": "test cascade edit again",
            "library_name": activity.library_name,
        },
    )
    assert_response_status_code(response, 200)

    # Approve the activity with cascade_edit_and_approve set to False
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/approvals",
        params={"cascade_edit_and_approve": False},
    )
    assert_response_status_code(response, 201)

    # Get the instance and assert that it was not updated
    response = api_client.get(
        f"/concepts/activities/activity-instances/{activity_instance.uid}"
    )
    res = parse_json_response(response, assert_status=200)

    assert res["groupings_version"] == "3.0"
    assert res["groupings_status"] == "Final"


def test_get_specific_activity_version_groupings(api_client):
    """Test that the /groupings endpoint returns activity instances linked to an activity,
    and that updating the activity/instance shows correct data per version."""

    # ==== Setup: create fresh group, subgroup, activity, and instance ====
    grp = TestUtils.create_activity_group(name="groupings_test_group")
    subgrp = TestUtils.create_activity_subgroup(name="groupings_test_subgroup")

    activity = TestUtils.create_activity(
        name="Groupings Test Activity",
        activity_subgroups=[subgrp.uid],
        activity_groups=[grp.uid],
        approve=True,
        is_data_collected=True,
    )

    instance = TestUtils.create_activity_instance(
        name="Groupings Test Instance",
        activity_instance_class_uid=activity_instance_classes[0].uid,
        name_sentence_case="groupings test instance",
        topic_code="groupings_tc",
        activities=[activity.uid],
        activity_subgroups=[subgrp.uid],
        activity_groups=[grp.uid],
        activity_items=[activity_items[0]],
        approve=True,
    )

    # ==== 1: check groupings for the initial approved version ====
    response = api_client.get(
        f"/concepts/activities/activities/{activity.uid}/versions/1.0/groupings",
        params={"total_count": True},
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["total"] >= 1
    items = res["items"]
    assert len(items) >= 1

    grouping = items[0]
    assert grouping["group"]["uid"] == grp.uid
    assert grouping["group"]["name"] == grp.name
    assert grouping["subgroup"]["uid"] == subgrp.uid
    assert grouping["subgroup"]["name"] == subgrp.name

    instance_uids = [inst["uid"] for inst in grouping["activity_instances"]]
    assert instance.uid in instance_uids

    # ==== 2: update the activity with a new name, approve, and check that the groupings endpoint for v2.0 returns the updated data ====
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/versions",
        json={},
    )
    assert_response_status_code(response, 201)
    response = api_client.put(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "name": "Updated Groupings Test Activity",
            "name_sentence_case": "updated groupings test activity",
            "change_description": "test update for v2.0",
            "library_name": activity.library_name,
            "is_data_collected": True,
            "activity_groupings": [
                {"activity_group_uid": grp.uid, "activity_subgroup_uid": subgrp.uid}
            ],
        },
    )
    assert_response_status_code(response, 200)

    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/approvals",
        params={"cascade_edit_and_approve": True},
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/concepts/activities/activities/{activity.uid}/versions/2.0/groupings",
        params={"total_count": True},
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert res["total"] >= 1
    items = res["items"]
    assert len(items) >= 1

    grouping = items[0]
    assert grouping["group"]["uid"] == grp.uid
    assert grouping["group"]["name"] == grp.name
    assert grouping["subgroup"]["uid"] == subgrp.uid
    assert grouping["subgroup"]["name"] == subgrp.name

    assert grouping["activity_instances"][0]["uid"] == instance.uid
    assert grouping["activity_instances"][0]["name"] == "Groupings Test Instance"

    # 3a: Update the instance with a new name, approve
    response = api_client.post(
        f"/concepts/activities/activity-instances/{instance.uid}/attributes/versions",
        json={},
    )
    assert_response_status_code(response, 201)
    response = api_client.patch(
        f"/concepts/activities/activity-instances/{instance.uid}/attributes",
        json={
            "name": "Updated Groupings Test Instance",
            "name_sentence_case": "updated groupings test instance",
            "change_description": "test update for instance",
            "topic_code": instance.topic_code,
            "nci_concept_id": instance.nci_concept_id,
            "library_name": instance.library_name,
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activity-instances/{instance.uid}/attributes/approvals",
    )
    assert_response_status_code(response, 201)

    # 3b: Undate the instance groupings to link it to the new activity version, approve
    response = api_client.post(
        f"/concepts/activities/activity-instances/{instance.uid}/groupings/versions",
        json={},
    )
    assert_response_status_code(response, 201)
    response = api_client.patch(
        f"/concepts/activities/activity-instances/{instance.uid}/groupings",
        json={
            "change_description": "link instance to new activity version",
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activity-instances/{instance.uid}/groupings/approvals",
    )
    assert_response_status_code(response, 201)

    # 4: Get the activity groupings for the activity v2.0 again and assert that the instance data is updated
    response = api_client.get(
        f"/concepts/activities/activities/{activity.uid}/versions/2.0/groupings"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    items = res["items"]
    assert len(items) == 1
    grouping = items[0]
    assert len(grouping["activity_instances"]) == 1
    assert grouping["activity_instances"][0]["uid"] == instance.uid
    assert (
        grouping["activity_instances"][0]["name"] == "Updated Groupings Test Instance"
    )

    # 5: Get the activity groupings for the activity v1.0 and assert that the instance data is NOT updated in the old version
    response = api_client.get(
        f"/concepts/activities/activities/{activity.uid}/versions/1.0/groupings"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    items = res["items"]
    assert len(items) == 1
    grouping = items[0]
    assert len(grouping["activity_instances"]) == 1
    assert grouping["activity_instances"][0]["uid"] == instance.uid
    assert grouping["activity_instances"][0]["name"] == "Groupings Test Instance"


def test_get_instances_for_version(api_client):
    # Create activity and instance
    activity = TestUtils.create_activity(
        name="Linked Instances Test Activity",
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        approve=True,
    )
    instance = TestUtils.create_activity_instance(
        name="Linked Instances Test Instance",
        activity_instance_class_uid=activity_instance_classes[0].uid,
        name_sentence_case="linked instances test instance",
        topic_code="linked_instances_tc",
        activities=[activity.uid],
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        activity_items=[activity_items[0]],
        approve=True,
    )
    # Get instances linked to the activity version
    response = api_client.get(
        f"/concepts/activities/activities/{activity.uid}/versions/1.0/instances"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["total"] == 1
    assert res["items"][0]["uid"] == instance.uid
    assert res["items"][0]["name"] == "Linked Instances Test Instance"
    all_linked_versions = [child["version"] for child in res["items"][0]["children"]]
    all_linked_versions.append(res["items"][0]["version"])
    assert len(all_linked_versions) == 2
    assert "1.0" in all_linked_versions
    assert "0.1" in all_linked_versions

    # Make a new Ativity version
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/versions",
        json={},
    )
    assert_response_status_code(response, 201)
    response = api_client.put(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "name": "Edited Linked Instances Test Activity",
            "name_sentence_case": "edited linked instances test activity",
            "change_description": "test update for new version",
            "library_name": activity.library_name,
            "is_data_collected": True,
            "activity_groupings": [
                {
                    "activity_group_uid": activity_group.uid,
                    "activity_subgroup_uid": activity_subgroup.uid,
                }
            ],
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/approvals",
        params={"cascade_edit_and_approve": True},
    )
    assert_response_status_code(response, 201)

    # Get instances linked to the new activity version
    response = api_client.get(
        f"/concepts/activities/activities/{activity.uid}/versions/2.0/instances"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["total"] == 1
    assert res["items"][0]["uid"] == instance.uid
    assert res["items"][0]["name"] == "Linked Instances Test Instance"
    all_linked_versions = [child["version"] for child in res["items"][0]["children"]]
    all_linked_versions.append(res["items"][0]["version"])
    assert len(all_linked_versions) == 1
    assert "1.0" in all_linked_versions

    # Make a new instance attributes version
    response = api_client.post(
        f"/concepts/activities/activity-instances/{instance.uid}/attributes/versions",
        json={},
    )
    assert_response_status_code(response, 201)
    response = api_client.patch(
        f"/concepts/activities/activity-instances/{instance.uid}/attributes",
        json={
            "name": "Edited Linked Instances Test Instance",
            "name_sentence_case": "edited linked instances test instance",
            "change_description": "test update for instance",
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activity-instances/{instance.uid}/attributes/approvals",
    )
    assert_response_status_code(response, 201)

    # Get instances linked to the new activity version again, should include the new instance version as well
    response = api_client.get(
        f"/concepts/activities/activities/{activity.uid}/versions/2.0/instances"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["total"] == 1
    assert res["items"][0]["uid"] == instance.uid
    assert res["items"][0]["name"] == "Edited Linked Instances Test Instance"
    all_linked_versions = [child["version"] for child in res["items"][0]["children"]]
    all_linked_versions.append(res["items"][0]["version"])
    assert len(all_linked_versions) == 4
    assert "1.0" in all_linked_versions
    assert "1.1" in all_linked_versions
    assert "1.2" in all_linked_versions
    assert "2.0" in all_linked_versions

    # Get the instances linked to the old activity version, should still be linked to the old version
    response = api_client.get(
        f"/concepts/activities/activities/{activity.uid}/versions/1.0/instances"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["total"] == 1
    assert res["items"][0]["uid"] == instance.uid
    assert res["items"][0]["name"] == "Linked Instances Test Instance"
    all_linked_versions = [child["version"] for child in res["items"][0]["children"]]
    all_linked_versions.append(res["items"][0]["version"])
    assert len(all_linked_versions) == 2
    assert "1.0" in all_linked_versions
    assert "0.1" in all_linked_versions


def test_get_all_versions_instances(api_client):
    """Test the /versions/instances endpoint returns compact instance info per activity version,
    and that retired instances are excluded."""

    # ==== Setup: create activity, group, subgroup, and two instances ====
    grp = TestUtils.create_activity_group(name="all_versions_test_group")
    subgrp = TestUtils.create_activity_subgroup(name="all_versions_test_subgroup")

    activity = TestUtils.create_activity(
        name="All Versions Test Activity",
        activity_subgroups=[subgrp.uid],
        activity_groups=[grp.uid],
        approve=True,
        is_data_collected=True,
    )

    instance_a = TestUtils.create_activity_instance(
        name="All Versions Instance A",
        activity_instance_class_uid=activity_instance_classes[0].uid,
        name_sentence_case="all versions instance a",
        topic_code="all_ver_tc_a",
        activities=[activity.uid],
        activity_subgroups=[subgrp.uid],
        activity_groups=[grp.uid],
        activity_items=[activity_items[0]],
        approve=True,
    )

    instance_b = TestUtils.create_activity_instance(
        name="All Versions Instance B",
        activity_instance_class_uid=activity_instance_classes[0].uid,
        name_sentence_case="all versions instance b",
        topic_code="all_ver_tc_b",
        activities=[activity.uid],
        activity_subgroups=[subgrp.uid],
        activity_groups=[grp.uid],
        activity_items=[activity_items[0]],
        approve=True,
    )

    # ==== 1: Get all versions instances for v1.0 ====
    response = api_client.get(
        f"/concepts/activities/activities/{activity.uid}/versions/instances"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert len(res) == 1
    assert res[0]["version"] == "1.0"
    instance_uids = {inst["uid"] for inst in res[0]["instances"]}
    assert instance_a.uid in instance_uids
    assert instance_b.uid in instance_uids

    # Verify compact structure
    for inst in res[0]["instances"]:
        assert "uid" in inst
        assert "name" in inst
        assert "topic_code" in inst
        assert "groupings" in inst
        assert len(inst["groupings"]) >= 1
        grouping = inst["groupings"][0]
        assert grouping["activity_group_uid"] == grp.uid
        assert grouping["activity_group_name"] == grp.name
        assert grouping["activity_subgroup_uid"] == subgrp.uid
        assert grouping["activity_subgroup_name"] == subgrp.name

    # ==== 2: Create a second activity version (v2.0) ====
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/versions",
        json={},
    )
    assert_response_status_code(response, 201)
    response = api_client.put(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "name": "All Versions Test Activity v2",
            "name_sentence_case": "all versions test activity v2",
            "change_description": "create v2.0",
            "library_name": activity.library_name,
            "is_data_collected": True,
            "activity_groupings": [
                {"activity_group_uid": grp.uid, "activity_subgroup_uid": subgrp.uid}
            ],
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/approvals",
        params={"cascade_edit_and_approve": True},
    )
    assert_response_status_code(response, 201)

    # Now there should be 2 versions
    response = api_client.get(
        f"/concepts/activities/activities/{activity.uid}/versions/instances"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    # Both versions should appear, ordered descending
    versions = [v["version"] for v in res]
    assert "2.0" in versions
    assert "1.0" in versions
    assert versions.index("2.0") < versions.index("1.0")

    # ==== 3: Retire instance_b and verify it's excluded ====
    response = api_client.delete(
        f"/concepts/activities/activity-instances/{instance_b.uid}/activations"
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        f"/concepts/activities/activities/{activity.uid}/versions/instances"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    # instance_b should be excluded from all versions since its latest status is Retired
    for version_entry in res:
        instance_uids = {inst["uid"] for inst in version_entry["instances"]}
        assert (
            instance_a.uid in instance_uids
        ), f"Active instance_a should be present in version {version_entry['version']}"
        assert (
            instance_b.uid not in instance_uids
        ), f"Retired instance_b should NOT be present in version {version_entry['version']}"

    # ==== 4: Test 404 for non-existent activity ====
    response = api_client.get(
        "/concepts/activities/activities/nonexistent-uid/versions/instances"
    )
    assert_response_status_code(response, 404)


def test_create_activity_without_groupings_not_allowed(api_client):
    """
    SCENARIO: creating an Activity in Sponsor Library without any groupings
    GIVEN: no specific preconditions
    WHEN: POST /concepts/activities/activities with empty activity_groupings list and library_name set to "Sponsor" in the request body
    THEN: should respond with 400 HTTP status code and JSON payload,
          containing the error message that Sponsor activities must have at least one grouping
    """

    response = api_client.post(
        "/concepts/activities/activities",
        json={
            "name": "Activity without groupings",
            "name_sentence_case": "Activity without groupings",
            "library_name": SPONSOR_LIBRARY_NAME,
            "activity_groupings": [],
        },
    )
    res = parse_json_response(response, assert_status=400)

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Sponsor activities must have at least one grouping."


def test_batch_update_groupings(api_client):
    """Test the batch-update endpoint for activity instance groupings."""

    # ==== Setup: create two activities with different groups, and two instances ====
    grp_a = TestUtils.create_activity_group(name="batch_group_a")
    grp_b = TestUtils.create_activity_group(name="batch_group_b")
    subgrp_a = TestUtils.create_activity_subgroup(name="batch_subgroup_a")
    subgrp_b = TestUtils.create_activity_subgroup(name="batch_subgroup_b")

    activity_a = TestUtils.create_activity(
        name="Batch Test Activity A",
        activity_subgroups=[subgrp_a.uid],
        activity_groups=[grp_a.uid],
        approve=True,
        is_data_collected=True,
    )
    activity_b = TestUtils.create_activity(
        name="Batch Test Activity B",
        activity_subgroups=[subgrp_b.uid],
        activity_groups=[grp_b.uid],
        approve=True,
        is_data_collected=True,
    )

    instance_1 = TestUtils.create_activity_instance(
        name="Batch Instance 1",
        activity_instance_class_uid=activity_instance_classes[0].uid,
        name_sentence_case="batch instance 1",
        topic_code="batch_tc_1",
        activities=[activity_a.uid],
        activity_subgroups=[subgrp_a.uid],
        activity_groups=[grp_a.uid],
        activity_items=[activity_items[0]],
        approve=True,
    )
    instance_2 = TestUtils.create_activity_instance(
        name="Batch Instance 2",
        activity_instance_class_uid=activity_instance_classes[0].uid,
        name_sentence_case="batch instance 2",
        topic_code="batch_tc_2",
        activities=[activity_a.uid],
        activity_subgroups=[subgrp_a.uid],
        activity_groups=[grp_a.uid],
        activity_items=[activity_items[0]],
        approve=True,
    )

    # Verify both instances start with grouping to activity_a / grp_a / subgrp_a
    for inst in [instance_1, instance_2]:
        response = api_client.get(
            f"/concepts/activities/activity-instances/{inst.uid}/groupings"
        )
        assert_response_status_code(response, 200)
        res = response.json()
        assert res["status"] == "Final"
        assert len(res["activity_groupings"]) == 1
        assert res["activity_groupings"][0]["activity"]["uid"] == activity_a.uid

    # ==== 1: Batch update both instances to point to activity_b / grp_b / subgrp_b ====
    response = api_client.post(
        "/concepts/activities/activity-instances/groupings/batch-update",
        json={
            "change_description": "Batch reassign to activity B",
            "items": [
                {
                    "activity_instance_uid": instance_1.uid,
                    "activity_groupings": [
                        {
                            "activity_uid": activity_b.uid,
                            "activity_group_uid": grp_b.uid,
                            "activity_subgroup_uid": subgrp_b.uid,
                        }
                    ],
                },
                {
                    "activity_instance_uid": instance_2.uid,
                    "activity_groupings": [
                        {
                            "activity_uid": activity_b.uid,
                            "activity_group_uid": grp_b.uid,
                            "activity_subgroup_uid": subgrp_b.uid,
                        }
                    ],
                },
            ],
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()

    # Should return a list of 2 approved groupings
    assert len(res) == 2
    for grouping_result in res:
        assert grouping_result["status"] == "Final"

    # ==== 2: Verify both instances now have the updated groupings ====
    for inst in [instance_1, instance_2]:
        response = api_client.get(
            f"/concepts/activities/activity-instances/{inst.uid}/groupings"
        )
        assert_response_status_code(response, 200)
        res = response.json()
        assert res["status"] == "Final"
        assert len(res["activity_groupings"]) == 1
        assert res["activity_groupings"][0]["activity"]["uid"] == activity_b.uid
        assert res["activity_groupings"][0]["activity_group"]["uid"] == grp_b.uid
        assert res["activity_groupings"][0]["activity_subgroup"]["uid"] == subgrp_b.uid

    # ==== 3: Test 404 for non-existent instance in batch ====
    response = api_client.post(
        "/concepts/activities/activity-instances/groupings/batch-update",
        json={
            "change_description": "Should fail",
            "items": [
                {
                    "activity_instance_uid": "nonexistent-uid",
                    "activity_groupings": [
                        {
                            "activity_uid": activity_a.uid,
                            "activity_group_uid": grp_a.uid,
                            "activity_subgroup_uid": subgrp_a.uid,
                        }
                    ],
                },
            ],
        },
    )
    assert_response_status_code(response, 404)

    # ==== 4: Test validation - empty items list ====
    response = api_client.post(
        "/concepts/activities/activity-instances/groupings/batch-update",
        json={
            "change_description": "Empty batch",
            "items": [],
        },
    )
    assert_response_status_code(response, 400)


def test_archiving_activity_draft(api_client):
    """
    SCENARIO: archiving an Activity in Draft status
    GIVEN: an existing Activity in the database (that is Draft and not archived)
    WHEN: POST /concepts/activities/activities/{uid}/archive for the archived Activity
    THEN: should respond with 200 HTTP status code and JSON payload,
          with the Activity moved to the archived library, other details unchanged.
    """

    activity = TestUtils.create_activity(
        name="Draft Activity to Archive",
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        approve=False,
    )

    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/archive"
    )
    res = parse_json_response(response, assert_status=200)

    expected_activity_dict = activity.model_dump()
    expected_activity_dict["library_name"] = settings.archived_library_name
    expected_activity_dict["start_date"] = activity.start_date.isoformat().replace(
        "+00:00", "Z"
    )
    expected_activity_dict["activity_groupings"][0]["activity_group_version"] = mock.ANY
    expected_activity_dict["activity_groupings"][0][
        "activity_subgroup_version"
    ] = mock.ANY
    assert res == expected_activity_dict


def test_archiving_final_activity(api_client):
    """
    SCENARIO: archiving an Activity in Final status
    GIVEN: an existing Activity in the database (that is Final and not archived)
    WHEN: POST /concepts/activities/activities/{uid}/archive for the archived Activity
    THEN: should respond with 200 HTTP status code and JSON payload,
          with the Activity moved to the archived library, other details unchanged.
    """

    activity = TestUtils.create_activity(
        name="Final Activity to Archive",
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        approve=True,
    )

    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/archive"
    )
    res = parse_json_response(response, assert_status=200)

    expected_activity_dict = activity.model_dump()
    expected_activity_dict["library_name"] = settings.archived_library_name
    expected_activity_dict["start_date"] = activity.start_date.isoformat().replace(
        "+00:00", "Z"
    )
    assert res == expected_activity_dict


def test_archiving_activity_request(api_client):
    """
    SCENARIO: archiving an Activity request
    GIVEN: a requested Activity in the database (that is Draft and not archived)
    WHEN: POST /concepts/activities/activities/{uid}/archive for the archived Activity
    THEN: should respond with 200 HTTP status code and JSON payload,
          with the Activity moved to the archived library, other details unchanged.
    """

    activity = TestUtils.create_activity(
        name="Activity request to Archive",
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        approve=False,
    )

    response = api_client.post(
        f"/concepts/activities/activities/{activity.uid}/archive"
    )
    res = parse_json_response(response, assert_status=200)

    assert_activities_match(res, activity)


def assert_activities_match(activity_dict: dict[str, any], expected_activity: Activity):
    expected_activity_dict = expected_activity.model_dump()
    expected_activity_dict["library_name"] = settings.archived_library_name
    expected_activity_dict["start_date"] = (
        expected_activity.start_date.isoformat().replace("+00:00", "Z")
    )
    expected_activity_dict["activity_groupings"][0]["activity_group_version"] = mock.ANY
    expected_activity_dict["activity_groupings"][0][
        "activity_subgroup_version"
    ] = mock.ANY
    assert activity_dict == expected_activity_dict


def test_get_activity_by_uid_returns_archived(api_client):
    """
    SCENARIO: getting an archived Activity by UID
    GIVEN: an existing Activity in the database that is archived
    WHEN: GET /concepts/activities/activities/{uid} for the archived Activity
    THEN: should respond with 200 HTTP status code and JSON payload,
          with the details of the archived Activity returned.
    """

    for activity in archived_activities:
        response = api_client.get(f"/concepts/activities/activities/{activity.uid}")
        res = parse_json_response(response, assert_status=200)

        assert_activities_match(res, activity)


def test_can_not_archive_already_archived_activity(api_client):
    """
    SCENARIO: archiving an already archived Activity
    GIVEN: an existing Activity in the database that is already archived
    WHEN: POST /concepts/activities/activities/{uid}/archive for the archived Activity
    THEN: should respond with 400 HTTP status code and JSON payload,
          containing the error message that the Activity is already archived.
    """

    for activity in archived_activities:
        response = api_client.post(
            f"/concepts/activities/activities/{activity.uid}/archive"
        )
        res = parse_json_response(response, assert_status=400)
        assert (
            res["message"]
            == f"Concept with UID '{activity.uid}' is already in '{settings.archived_library_name}' library."
        )


def test_can_not_create_new_version_of_archived_activity(api_client):
    """
    SCENARIO: creating a new version of an archived Activity
    GIVEN: an existing Activity in the database that is already archived
    WHEN: POST /concepts/activities/activities/{uid}/versions for the archived Activity
    THEN: should respond with 400 HTTP status code and JSON payload, with an error message.
    """

    for activity in archived_activities:
        response = api_client.post(
            f"/concepts/activities/activities/{activity.uid}/versions"
        )
        res = parse_json_response(response, assert_status=400)
        assert res["message"] == "Library isn't editable."


def test_can_not_edit_archived_activity(api_client):
    """
    SCENARIO: editing an archived Activity
    GIVEN: an existing Activity in the database that is already archived
    WHEN: PUT /concepts/activities/activities/{uid} for the archived Activity
    THEN: should respond with 400 HTTP status code and JSON payload, with an error message.
    """

    for activity in archived_activities:
        response = api_client.put(
            f"/concepts/activities/activities/{activity.uid}",
            json={
                "name": "Edited Archived Activity",
                "name_sentence_case": "edited archived activity",
                "change_description": "test edit archived activity",
            },
        )
        res = parse_json_response(response, assert_status=400)
        assert res["message"] == "Library isn't editable."


def test_allow_recreating_archived_activity(api_client):
    """
    SCENARIO: creating a new Activity with the same data as an archived Activity
    GIVEN: an existing Activity in the database that is already archived
    WHEN: POST /concepts/activities/activities with the same data as the archived Activity
    THEN: should respond with 201 HTTP status code and JSON payload, with the created Activity
    """

    for activity in archived_activities:
        activity_dict = activity.model_dump()
        activity_dict["library_name"] = SPONSOR_LIBRARY_NAME
        activity_input = ActivityCreateInput(**activity_dict)

        response = api_client.post(
            "/concepts/activities/activities", json=activity_input.model_dump()
        )
        res = parse_json_response(response, assert_status=201)

        assert res["name"] == activity.name


def test_forbid_creating_activity_in_archived_group(api_client):
    """
    SCENARIO: creating an Activity to link to an archived ActivityGroup
    GIVEN: an archived ActivityGroup in the database
    WHEN: creating a new Activity to link to the archived ActivityGroup
    THEN: should respond with 400 HTTP status code and JSON payload, with an error message.
    """

    response = api_client.post(
        "/concepts/activities/activities",
        json={
            "name": "Linking to archived group",
            "name_sentence_case": "Linking to archived group",
            "library_name": SPONSOR_LIBRARY_NAME,
            "activity_groupings": [
                {
                    "activity_subgroup_uid": activity_subgroup.uid,
                    "activity_group_uid": archived_activity_group.uid,
                }
            ],
        },
    )
    res = parse_json_response(response, assert_status=400)
    expected_msg = f"Activities cannot be connected to Activity Groups in the '{settings.archived_library_name}' library"
    assert expected_msg in res["message"]


def test_forbid_linking_activity_to_archived_group(api_client):
    """
    SCENARIO: updating an existing Activity to link to an archived ActivityGroup
    GIVEN: an existing Activity in the database, and an archived ActivityGroup in the database
    WHEN: updating the existing Activity to link to the archived ActivityGroup
    THEN: should respond with 400 HTTP status code and JSON payload, with an error message
    """

    activity = TestUtils.create_activity(
        name="Activity to link to archived group",
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        approve=True,
    )

    response = api_client.put(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "name": activity.name,
            "name_sentence_case": activity.name_sentence_case,
            "change_description": "test linking to archived group",
            "library_name": activity.library_name,
            "activity_groupings": [
                {
                    "activity_group_uid": archived_activity_group.uid,
                    "activity_subgroup_uid": activity_subgroup.uid,
                }
            ],
        },
    )
    res = parse_json_response(response, assert_status=400)
    expected_msg = f"Activities cannot be connected to Activity Groups in the '{settings.archived_library_name}' library"
    assert expected_msg in res["message"]


def test_forbid_creating_activity_in_archived_subgroup(api_client):
    """
    SCENARIO: creating an Activity to link to an archived ActivitySubGroup
    GIVEN: an archived ActivitySubGroup in the database
    WHEN: creating a new Activity to link to the archived ActivitySubGroup
    THEN: should respond with 400 HTTP status code and JSON payload, with an error message
    """

    response = api_client.post(
        "/concepts/activities/activities",
        json={
            "name": "Linking to archived subgroup",
            "name_sentence_case": "Linking to archived subgroup",
            "library_name": SPONSOR_LIBRARY_NAME,
            "activity_groupings": [
                {
                    "activity_group_uid": activity_group.uid,
                    "activity_subgroup_uid": archived_activity_subgroup.uid,
                }
            ],
        },
    )
    res = parse_json_response(response, assert_status=400)
    expected_msg = f"Activities cannot be connected to Activity Subgroups in the '{settings.archived_library_name}' library"
    assert expected_msg in res["message"]


def test_forbid_linking_activity_to_archived_subgroup(api_client):
    """
    SCENARIO: updating an existing Activity to link to an archived ActivitySubGroup
    GIVEN: an existing Activity in the database, and an archived ActivitySubGroup in the database
    WHEN: updating the existing Activity to link to the archived ActivitySubGroup
    THEN: should respond with 400 HTTP status code and JSON payload, with an error message
    """

    activity = TestUtils.create_activity(
        name="Activity to link archived subgroup",
        activity_subgroups=[activity_subgroup.uid],
        activity_groups=[activity_group.uid],
        approve=True,
    )

    response = api_client.put(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "name": activity.name,
            "name_sentence_case": activity.name_sentence_case,
            "change_description": "test linking to archived subgroup",
            "library_name": activity.library_name,
            "activity_groupings": [
                {
                    "activity_group_uid": activity_group.uid,
                    "activity_subgroup_uid": archived_activity_subgroup.uid,
                }
            ],
        },
    )
    res = parse_json_response(response, assert_status=400)
    expected_msg = f"Activities cannot be connected to Activity Subgroups in the '{settings.archived_library_name}' library"
    assert expected_msg in res["message"]


def test_updating_activity_with_archived_groupings(api_client):
    """
    SCENARIO: updating an existing Activity that is linked to archived groupings
    GIVEN: an existing Activity in the database that is linked to archived ActivityGroup and ActivitySubGroup
    WHEN: updating the existing Activity's name and synonyms
    THEN: should respond with 200 HTTP status code and JSON payload, with the updated Activity details,
          and the archived groupings should still be linked to the Activity.
    """

    activity = activity_with_archived_groupings

    response = api_client.put(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "name": activity.name,
            "name_sentence_case": activity.name_sentence_case,
            "synonyms": ["updated synonym1", "updated synonym2"],
            "change_description": "test updating activity with archived groupings",
        },
    )
    res = parse_json_response(response, assert_status=200)

    assert set(res["synonyms"]) == {"updated synonym1", "updated synonym2"}


def test_extend_groupings_of_activity_with_archived_groupings(api_client):
    """
    SCENARIO: adding more groupings to an Activity that is linked to archived groupings
    GIVEN: an existing Activity in the database that is linked to archived ActivityGroup and ActivitySubGroup
    WHEN: updating the Activity to link to additional ActivityGroup and ActivitySubGroup which are not archived
    THEN: should respond with 200 HTTP status code and JSON payload,
          and the newly added groupings should be included.
    """

    activity = activity_with_archived_groupings

    response = api_client.put(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "name": activity.name,
            "name_sentence_case": activity.name_sentence_case,
            "change_description": "extending groupings of an activity with archived groupings",
            "activity_groupings": [
                ag.model_dump() for ag in activity.activity_groupings
            ]
            + [
                {
                    "activity_group_uid": different_activity_group.uid,
                    "activity_subgroup_uid": different_activity_subgroup.uid,
                }
            ],
        },
    )
    res = parse_json_response(response, assert_status=200)

    groupings = res["activity_groupings"]
    assert len(groupings) == len(activity.activity_groupings) + 1
    assert any(
        g["activity_group_uid"] == different_activity_group.uid
        and g["activity_subgroup_uid"] == different_activity_subgroup.uid
        for g in groupings
    )


def test_unlink_archived_groupings_from_activity(api_client):
    """
    SCENARIO: updating an existing Activity to remove from archived groupings
    GIVEN: an existing Activity in the database that is linked to archived ActivityGroup and ActivitySubGroup
    WHEN: updating the existing Activity to remove from archived groupings
    THEN: should respond with 200 HTTP status code and JSON payload, with the updated Activity details,
          and the archived Activity Groupings replaced.
    """

    activity = activity_with_archived_groupings

    response = api_client.put(
        f"/concepts/activities/activities/{activity.uid}",
        json={
            "name": activity.name,
            "name_sentence_case": activity.name_sentence_case,
            "change_description": "test unlinking archived groupings from activity",
            "activity_groupings": [
                {
                    "activity_group_uid": activity_group.uid,
                    "activity_subgroup_uid": activity_subgroup.uid,
                }
            ],
        },
    )
    res = parse_json_response(response, assert_status=200)

    assert len(res["activity_groupings"]) == 1
    assert res["activity_groupings"][0]["activity_group_uid"] == activity_group.uid
    assert (
        res["activity_groupings"][0]["activity_subgroup_uid"] == activity_subgroup.uid
    )


def test_delete_draft_activity(api_client):
    """
    SCENARIO: deleting a draft activity
    GIVEN: an existing draft activity
    WHEN: deleting the activity
    THEN: should respond with 204 HTTP status code
    """

    activity = TestUtils.create_activity(
        name="Activity to delete",
        activity_groups=[activity_group.uid],
        activity_subgroups=[activity_subgroup.uid],
        approve=False,
    )

    response = api_client.delete(f"/concepts/activities/activities/{activity.uid}")
    assert_response_status_code(response, 204)


def test_delete_archived_activity_fails(api_client):
    """
    SCENARIO: deleting a archived activity
    GIVEN: an existing archived activity
    WHEN: deleting the activity
    THEN: should respond with 204 HTTP status code and JSON payload,
          with an error message that archived concepts cannot be deleted.
    """

    activity = TestUtils.create_activity(
        name="Third activity to delete",
        activity_groups=[activity_group.uid],
        activity_subgroups=[activity_subgroup.uid],
        approve=False,
    )
    TestUtils.archive_activity(activity.uid)

    response = api_client.delete(f"/concepts/activities/activities/{activity.uid}")
    resp = parse_json_response(response, assert_status=400)
    assert "Can't delete Concept" in resp["message"]
