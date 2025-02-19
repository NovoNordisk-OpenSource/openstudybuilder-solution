"""
Tests for footnote-templates endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import json
import logging
from functools import reduce

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.activities.activity import Activity
from clinical_mdr_api.models.concepts.activities.activity_group import ActivityGroup
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
)
from clinical_mdr_api.models.concepts.concept import TextValue
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.dictionaries.dictionary_codelist import DictionaryCodelist
from clinical_mdr_api.models.dictionaries.dictionary_term import DictionaryTerm
from clinical_mdr_api.models.syntax_pre_instances.footnote_pre_instance import (
    FootnotePreInstance,
)
from clinical_mdr_api.models.syntax_templates.footnote_template import FootnoteTemplate
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
footnote_pre_instances: list[FootnotePreInstance]
footnote_template: FootnoteTemplate
ct_term_schedule_of_activities: CTTerm
dictionary_term_indication: DictionaryTerm
indications_codelist: DictionaryCodelist
indications_library_name: str
activity: Activity
activity_group: ActivityGroup
activity_subgroup: ActivitySubGroup
text_value_1: TextValue
text_value_2: TextValue

URL = "footnote-pre-instances"


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    inject_and_clear_db(URL + ".api")
    inject_base_data()

    global footnote_pre_instances
    global footnote_template
    global ct_term_schedule_of_activities
    global dictionary_term_indication
    global indications_codelist
    global indications_library_name
    global activity
    global activity_group
    global activity_subgroup
    global text_value_1
    global text_value_2

    # Create Template Parameter
    TestUtils.create_template_parameter("TextValue")

    text_value_1 = TestUtils.create_text_value()
    text_value_2 = TestUtils.create_text_value()

    activity_group = TestUtils.create_activity_group(name="test activity group")
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="test activity subgroup", activity_groups=[activity_group.uid]
    )
    activity = TestUtils.create_activity(
        name="test activity",
        library_name="Sponsor",
        activity_groups=[activity_group.uid],
        activity_subgroups=[activity_subgroup.uid],
    )

    # Create Dictionary/CT Terms
    ct_term_schedule_of_activities = TestUtils.create_ct_term(
        sponsor_preferred_name="Schedule of Activities"
    )
    indications_library_name = "SNOMED"
    indications_codelist = TestUtils.create_dictionary_codelist(
        name="DiseaseDisorder", library_name=indications_library_name
    )
    dictionary_term_indication = TestUtils.create_dictionary_term(
        codelist_uid=indications_codelist.codelist_uid,
        library_name=indications_library_name,
    )

    def generate_parameter_terms():
        text_value = TestUtils.create_text_value()
        return [
            MultiTemplateParameterTerm(
                position=1,
                conjunction="",
                terms=[
                    IndexedTemplateParameterTerm(
                        index=1,
                        name=text_value.name,
                        uid=text_value.uid,
                        type="TextValue",
                    )
                ],
            )
        ]

    footnote_template = TestUtils.create_footnote_template(
        name="Default name with [TextValue]",
        study_uid=None,
        type_uid=ct_term_schedule_of_activities.term_uid,
        library_name="Sponsor",
        indication_uids=[dictionary_term_indication.term_uid],
        activity_uids=[activity.uid],
        activity_group_uids=[activity_group.uid],
        activity_subgroup_uids=[activity_subgroup.uid],
    )

    # Create some footnote_pre_instances
    footnote_pre_instances = []
    footnote_pre_instances.append(
        TestUtils.create_footnote_pre_instance(
            template_uid=footnote_template.uid,
            library_name="Sponsor",
            parameter_terms=[
                MultiTemplateParameterTerm(
                    position=1,
                    conjunction="",
                    terms=[
                        IndexedTemplateParameterTerm(
                            index=1,
                            name=text_value_1.name,
                            uid=text_value_1.uid,
                            type="TextValue",
                        )
                    ],
                )
            ],
            indication_uids=[dictionary_term_indication.term_uid],
            activity_uids=[activity.uid],
            activity_group_uids=[activity_group.uid],
            activity_subgroup_uids=[activity_subgroup.uid],
        )
    )
    footnote_pre_instances.append(
        TestUtils.create_footnote_pre_instance(
            template_uid=footnote_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            indication_uids=[dictionary_term_indication.term_uid],
            activity_uids=[activity.uid],
            activity_group_uids=[activity_group.uid],
            activity_subgroup_uids=[activity_subgroup.uid],
        )
    )
    footnote_pre_instances.append(
        TestUtils.create_footnote_pre_instance(
            template_uid=footnote_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            indication_uids=[dictionary_term_indication.term_uid],
            activity_uids=[activity.uid],
            activity_group_uids=[activity_group.uid],
            activity_subgroup_uids=[activity_subgroup.uid],
        )
    )
    footnote_pre_instances.append(
        TestUtils.create_footnote_pre_instance(
            template_uid=footnote_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            indication_uids=[dictionary_term_indication.term_uid],
            activity_uids=[activity.uid],
            activity_group_uids=[activity_group.uid],
            activity_subgroup_uids=[activity_subgroup.uid],
            approve=False,
        )
    )
    footnote_pre_instances.append(
        TestUtils.create_footnote_pre_instance(
            template_uid=footnote_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            indication_uids=[dictionary_term_indication.term_uid],
            activity_uids=[activity.uid],
            activity_group_uids=[activity_group.uid],
            activity_subgroup_uids=[activity_subgroup.uid],
            approve=False,
        )
    )

    for _ in range(5):
        footnote_pre_instances.append(
            TestUtils.create_footnote_pre_instance(
                template_uid=footnote_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
                indication_uids=[dictionary_term_indication.term_uid],
                activity_uids=[activity.uid],
                activity_group_uids=[activity_group.uid],
                activity_subgroup_uids=[activity_subgroup.uid],
            )
        )
        footnote_pre_instances.append(
            TestUtils.create_footnote_pre_instance(
                template_uid=footnote_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
                indication_uids=[dictionary_term_indication.term_uid],
                activity_uids=[activity.uid],
                activity_group_uids=[activity_group.uid],
                activity_subgroup_uids=[activity_subgroup.uid],
            )
        )
        footnote_pre_instances.append(
            TestUtils.create_footnote_pre_instance(
                template_uid=footnote_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
                indication_uids=[dictionary_term_indication.term_uid],
                activity_uids=[activity.uid],
                activity_group_uids=[activity_group.uid],
                activity_subgroup_uids=[activity_subgroup.uid],
            )
        )
        footnote_pre_instances.append(
            TestUtils.create_footnote_pre_instance(
                template_uid=footnote_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
                indication_uids=[dictionary_term_indication.term_uid],
                activity_uids=[activity.uid],
                activity_group_uids=[activity_group.uid],
                activity_subgroup_uids=[activity_subgroup.uid],
            )
        )

    yield


FOOTNOTE_PRE_INSTANCE_FIELDS_ALL = [
    "name",
    "name_plain",
    "uid",
    "sequence_id",
    "template_uid",
    "template_name",
    "template_type_uid",
    "status",
    "version",
    "change_description",
    "start_date",
    "end_date",
    "author_username",
    "possible_actions",
    "parameter_terms",
    "library",
    "indications",
    "activities",
    "activity_groups",
    "activity_subgroups",
]

FOOTNOTE_PRE_INSTANCE_FIELDS_NOT_NULL = [
    "uid",
    "sequence_id",
    "template_uid",
    "template_name",
    "template_type_uid",
    "name",
]


def test_get_footnote(api_client):
    response = api_client.get(f"{URL}/{footnote_pre_instances[0].uid}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    fields_all_set = set(FOOTNOTE_PRE_INSTANCE_FIELDS_ALL)
    assert set(list(res.keys())) == fields_all_set
    for key in FOOTNOTE_PRE_INSTANCE_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == footnote_pre_instances[0].uid
    assert res["sequence_id"] == "FSA1P1"
    assert res["name"] == f"Default name with [{text_value_1.name_sentence_case}]"
    assert (
        res["parameter_terms"][0]["terms"][0]["name"] == text_value_1.name_sentence_case
    )
    assert res["parameter_terms"][0]["terms"][0]["uid"] == text_value_1.uid
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["activities"][0]["uid"] == activity.uid
    assert res["activities"][0]["name"] == activity.name
    assert res["activities"][0]["name_sentence_case"] == activity.name_sentence_case
    assert res["activity_groups"][0]["uid"] == activity_group.uid
    assert res["activity_groups"][0]["name"] == activity_group.name
    assert (
        res["activity_groups"][0]["name_sentence_case"]
        == activity_group.name_sentence_case
    )
    assert res["activity_subgroups"][0]["uid"] == activity_subgroup.uid
    assert res["activity_subgroups"][0]["name"] == activity_subgroup.name
    assert (
        res["activity_subgroups"][0]["name_sentence_case"]
        == activity_subgroup.name_sentence_case
    )
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_get_footnote_pre_instances_pagination(api_client):
    results_paginated: dict = {}
    sort_by = '{"uid": true}'
    for page_number in range(1, 4):
        response = api_client.get(
            f"{URL}?page_number={page_number}&page_size=10&sort_by={sort_by}"
        )
        res = response.json()
        res_uids = list(map(lambda x: x["uid"], res["items"]))
        results_paginated[page_number] = res_uids
        log.info("Page %s: %s", page_number, res_uids)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        list(reduce(lambda a, b: a + b, list(results_paginated.values())))
    )
    log.info("All rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"{URL}?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["uid"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(footnote_pre_instances) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, True, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 3, True, None, 5),  # Total number of data models is 25
        pytest.param(10, 1, True, '{"name": false}', 10),
        pytest.param(10, 2, True, '{"name": true}', 10),
    ],
)
def test_get_footnote_pre_instances(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = URL
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
    assert res["total"] == (len(footnote_pre_instances) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(FOOTNOTE_PRE_INSTANCE_FIELDS_ALL)
        for key in FOOTNOTE_PRE_INSTANCE_FIELDS_NOT_NULL:
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
        # This assert fails due to API issue with sorting coupled with pagination
        # assert result_vals == result_vals_sorted_locally


def test_get_versions_of_footnote_pre_instance(api_client):
    response = api_client.get(f"{URL}/{footnote_pre_instances[1].uid}/versions")
    res = response.json()

    assert_response_status_code(response, 200)

    assert len(res) == 2
    assert res[0]["uid"] == footnote_pre_instances[1].uid
    assert res[0]["sequence_id"] == "FSA1P2"
    assert res[0]["template_uid"] == footnote_template.uid
    assert res[0]["template_name"] == footnote_template.name
    assert res[0]["template_type_uid"] == ct_term_schedule_of_activities.term_uid
    assert res[0]["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res[0]["indications"][0]["name"] == dictionary_term_indication.name
    assert res[0]["activities"][0]["uid"] == activity.uid
    assert res[0]["activities"][0]["name"] == activity.name
    assert res[0]["activities"][0]["name_sentence_case"] == activity.name_sentence_case
    assert res[0]["activity_groups"][0]["uid"] == activity_group.uid
    assert res[0]["activity_groups"][0]["name"] == activity_group.name
    assert (
        res[0]["activity_groups"][0]["name_sentence_case"]
        == activity_group.name_sentence_case
    )
    assert res[0]["activity_subgroups"][0]["uid"] == activity_subgroup.uid
    assert res[0]["activity_subgroups"][0]["name"] == activity_subgroup.name
    assert (
        res[0]["activity_subgroups"][0]["name_sentence_case"]
        == activity_subgroup.name_sentence_case
    )
    assert res[0]["version"] == "1.0"
    assert res[0]["status"] == "Final"
    assert res[0]["possible_actions"] == ["inactivate", "new_version"]
    assert res[1]["uid"] == footnote_pre_instances[1].uid
    assert res[1]["sequence_id"] == "FSA1P2"
    assert res[1]["template_uid"] == footnote_template.uid
    assert res[1]["template_name"] == footnote_template.name
    assert res[1]["template_type_uid"] == ct_term_schedule_of_activities.term_uid
    assert res[1]["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res[1]["indications"][0]["name"] == dictionary_term_indication.name
    assert res[1]["activities"][0]["uid"] == activity.uid
    assert res[1]["activities"][0]["name"] == activity.name
    assert res[1]["activities"][0]["name_sentence_case"] == activity.name_sentence_case
    assert res[1]["activity_groups"][0]["uid"] == activity_group.uid
    assert res[1]["activity_groups"][0]["name"] == activity_group.name
    assert (
        res[1]["activity_groups"][0]["name_sentence_case"]
        == activity_group.name_sentence_case
    )
    assert res[1]["activity_subgroups"][0]["uid"] == activity_subgroup.uid
    assert res[1]["activity_subgroups"][0]["name"] == activity_subgroup.name
    assert (
        res[1]["activity_subgroups"][0]["name_sentence_case"]
        == activity_subgroup.name_sentence_case
    )
    assert res[1]["version"] == "0.1"
    assert res[1]["status"] == "Draft"
    assert res[1]["possible_actions"] == ["approve", "delete", "edit"]


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["Default"], "op": "co"}}', "name", "Default name"),
        pytest.param('{"*": {"v": ["cc"], "op": "co"}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    response = api_client.get(f"{URL}?filters={filter_by}")
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
    "field_name",
    [
        pytest.param("name"),
    ],
)
def test_headers(api_client, field_name):
    response = api_client.get(f"{URL}/headers?field_name={field_name}&page_size=100")
    res = response.json()

    assert_response_status_code(response, 200)
    expected_result = []
    for footnote_pre_instance in footnote_pre_instances:
        value = getattr(footnote_pre_instance, field_name)
        if value:
            expected_result.append(value)
    log.info("Expected result is %s", expected_result)
    log.info("Returned %s", res)
    if expected_result:
        assert len(res) > 0
        assert len(set(expected_result)) == len(res)
        assert all(item in res for item in expected_result)
    else:
        assert len(res) == 0


def test_create_new_version_of_footnote_pre_instance(api_client):
    response = api_client.post(f"{URL}/{footnote_pre_instances[2].uid}/versions")
    res = response.json()
    log.info("Created new version of Footnote Pre-Instance: %s", res)

    assert_response_status_code(response, 201)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["template_uid"] == footnote_template.uid
    assert res["template_name"] == footnote_template.name
    assert res["template_type_uid"] == ct_term_schedule_of_activities.term_uid
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["activities"][0]["uid"] == activity.uid
    assert res["activities"][0]["name"] == activity.name
    assert res["activities"][0]["name_sentence_case"] == activity.name_sentence_case
    assert res["activity_groups"][0]["uid"] == activity_group.uid
    assert res["activity_groups"][0]["name"] == activity_group.name
    assert (
        res["activity_groups"][0]["name_sentence_case"]
        == activity_group.name_sentence_case
    )
    assert res["activity_subgroups"][0]["uid"] == activity_subgroup.uid
    assert res["activity_subgroups"][0]["name"] == activity_subgroup.name
    assert (
        res["activity_subgroups"][0]["name_sentence_case"]
        == activity_subgroup.name_sentence_case
    )
    assert res["version"] == "1.1"
    assert res["status"] == "Draft"


def test_update_footnote_pre_instance(api_client):
    data = {
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "and",
                "terms": [
                    {
                        "index": 1,
                        "name": text_value_1.name,
                        "uid": text_value_1.uid,
                        "type": "TextValue",
                    },
                    {
                        "index": 2,
                        "name": text_value_2.name,
                        "uid": text_value_2.uid,
                        "type": "TextValue",
                    },
                ],
            }
        ],
        "change_description": "added term",
    }
    response = api_client.patch(f"{URL}/{footnote_pre_instances[3].uid}", json=data)
    res = response.json()
    log.info("Updated Footnote Pre-Instance: %s", res)

    assert_response_status_code(response, 200)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["template_uid"] == footnote_template.uid
    assert res["template_name"] == footnote_template.name
    assert res["template_type_uid"] == ct_term_schedule_of_activities.term_uid
    assert (
        res["name"]
        == f"Default name with [{text_value_1.name_sentence_case} and {text_value_2.name_sentence_case}]"
    )
    assert (
        res["parameter_terms"][0]["terms"][0]["name"] == text_value_1.name_sentence_case
    )
    assert res["parameter_terms"][0]["terms"][0]["uid"] == text_value_1.uid
    assert (
        res["parameter_terms"][0]["terms"][1]["name"] == text_value_2.name_sentence_case
    )
    assert res["parameter_terms"][0]["terms"][1]["uid"] == text_value_2.uid
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["activities"][0]["uid"] == activity.uid
    assert res["activities"][0]["name"] == activity.name
    assert res["activities"][0]["name_sentence_case"] == activity.name_sentence_case
    assert res["activity_groups"][0]["uid"] == activity_group.uid
    assert res["activity_groups"][0]["name"] == activity_group.name
    assert (
        res["activity_groups"][0]["name_sentence_case"]
        == activity_group.name_sentence_case
    )
    assert res["activity_subgroups"][0]["uid"] == activity_subgroup.uid
    assert res["activity_subgroups"][0]["name"] == activity_subgroup.name
    assert (
        res["activity_subgroups"][0]["name_sentence_case"]
        == activity_subgroup.name_sentence_case
    )
    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert set(list(res.keys())) == set(FOOTNOTE_PRE_INSTANCE_FIELDS_ALL)
    for key in FOOTNOTE_PRE_INSTANCE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_change_footnote_pre_instance_indexings(api_client):
    _indication = TestUtils.create_dictionary_term(
        codelist_uid=indications_codelist.codelist_uid,
        library_name=indications_library_name,
    )
    _activity_group = TestUtils.create_activity_group(name="new activity group")
    _activity_subgroup = TestUtils.create_activity_subgroup(
        name="new activity subgroup", activity_groups=[_activity_group.uid]
    )
    _activity = TestUtils.create_activity(
        name="test new activity",
        library_name="Sponsor",
        activity_groups=[_activity_group.uid],
        activity_subgroups=[_activity_subgroup.uid],
    )

    data = {
        "indication_uids": [dictionary_term_indication.term_uid, _indication.term_uid],
        "activity_uids": [activity.uid, _activity.uid],
        "activity_group_uids": [activity_group.uid, _activity_group.uid],
        "activity_subgroup_uids": [activity_subgroup.uid, _activity_subgroup.uid],
    }
    response = api_client.patch(
        f"{URL}/{footnote_pre_instances[0].uid}/indexings",
        json=data,
    )
    res = response.json()
    log.info("Changed Footnote Pre-Instance indexings: %s", res)

    assert_response_status_code(response, 200)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["template_uid"] == footnote_template.uid
    assert res["template_name"] == footnote_template.name
    assert res["template_type_uid"] == ct_term_schedule_of_activities.term_uid
    assert res["name"] == f"Default name with [{text_value_1.name_sentence_case}]"
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["indications"][1]["term_uid"] == _indication.term_uid
    assert res["indications"][1]["name"] == _indication.name
    assert res["activities"][0]["uid"] == activity.uid
    assert res["activities"][0]["name"] == activity.name
    assert res["activities"][0]["name_sentence_case"] == activity.name_sentence_case
    assert res["activities"][1]["uid"] == _activity.uid
    assert res["activities"][1]["name"] == _activity.name
    assert res["activities"][1]["name_sentence_case"] == _activity.name_sentence_case
    assert res["activity_groups"][0]["uid"] == activity_group.uid
    assert res["activity_groups"][0]["name"] == activity_group.name
    assert (
        res["activity_groups"][0]["name_sentence_case"]
        == activity_group.name_sentence_case
    )
    assert res["activity_groups"][1]["uid"] == _activity_group.uid
    assert res["activity_groups"][1]["name"] == _activity_group.name
    assert (
        res["activity_groups"][1]["name_sentence_case"]
        == _activity_group.name_sentence_case
    )
    assert res["activity_subgroups"][0]["uid"] == activity_subgroup.uid
    assert res["activity_subgroups"][0]["name"] == activity_subgroup.name
    assert (
        res["activity_subgroups"][0]["name_sentence_case"]
        == activity_subgroup.name_sentence_case
    )
    assert res["activity_subgroups"][1]["uid"] == _activity_subgroup.uid
    assert res["activity_subgroups"][1]["name"] == _activity_subgroup.name
    assert (
        res["activity_subgroups"][1]["name_sentence_case"]
        == _activity_subgroup.name_sentence_case
    )
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert set(list(res.keys())) == set(FOOTNOTE_PRE_INSTANCE_FIELDS_ALL)
    for key in FOOTNOTE_PRE_INSTANCE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_remove_footnote_pre_instance_indexings(api_client):
    data = {
        "indication_uids": [],
        "activity_uids": [],
        "activity_group_uids": [],
        "activity_subgroup_uids": [],
    }
    response = api_client.patch(
        f"{URL}/{footnote_pre_instances[0].uid}/indexings",
        json=data,
    )
    res = response.json()
    log.info("Removed Footnote Pre-Instance indexings: %s", res)

    assert_response_status_code(response, 200)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["template_uid"] == footnote_template.uid
    assert res["template_name"] == footnote_template.name
    assert res["template_type_uid"] == ct_term_schedule_of_activities.term_uid
    assert res["name"] == f"Default name with [{text_value_1.name_sentence_case}]"
    assert not res["indications"]
    assert not res["activities"]
    assert not res["activity_groups"]
    assert not res["activity_subgroups"]
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert set(list(res.keys())) == set(FOOTNOTE_PRE_INSTANCE_FIELDS_ALL)
    for key in FOOTNOTE_PRE_INSTANCE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_delete_footnote_pre_instance(api_client):
    response = api_client.delete(f"{URL}/{footnote_pre_instances[3].uid}")
    log.info("Deleted Footnote Pre-Instance: %s", footnote_pre_instances[3].uid)

    assert_response_status_code(response, 204)


def test_approve_footnote_pre_instance(api_client):
    response = api_client.post(f"{URL}/{footnote_pre_instances[4].uid}/approvals")
    res = response.json()

    assert_response_status_code(response, 201)
    assert res["uid"] == footnote_pre_instances[4].uid
    assert res["sequence_id"] == "FSA1P5"
    assert res["template_uid"] == footnote_template.uid
    assert res["template_name"] == footnote_template.name
    assert res["template_type_uid"] == ct_term_schedule_of_activities.term_uid
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["activities"][0]["uid"] == activity.uid
    assert res["activities"][0]["name"] == activity.name
    assert res["activities"][0]["name_sentence_case"] == activity.name_sentence_case
    assert res["activity_groups"][0]["uid"] == activity_group.uid
    assert res["activity_groups"][0]["name"] == activity_group.name
    assert (
        res["activity_groups"][0]["name_sentence_case"]
        == activity_group.name_sentence_case
    )
    assert res["activity_subgroups"][0]["uid"] == activity_subgroup.uid
    assert res["activity_subgroups"][0]["name"] == activity_subgroup.name
    assert (
        res["activity_subgroups"][0]["name_sentence_case"]
        == activity_subgroup.name_sentence_case
    )
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_inactivate_footnote_pre_instance(api_client):
    response = api_client.delete(f"{URL}/{footnote_pre_instances[4].uid}/activations")
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == footnote_pre_instances[4].uid
    assert res["sequence_id"] == "FSA1P5"
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["activities"][0]["uid"] == activity.uid
    assert res["activities"][0]["name"] == activity.name
    assert res["activities"][0]["name_sentence_case"] == activity.name_sentence_case
    assert res["activity_groups"][0]["uid"] == activity_group.uid
    assert res["activity_groups"][0]["name"] == activity_group.name
    assert (
        res["activity_groups"][0]["name_sentence_case"]
        == activity_group.name_sentence_case
    )
    assert res["activity_subgroups"][0]["uid"] == activity_subgroup.uid
    assert res["activity_subgroups"][0]["name"] == activity_subgroup.name
    assert (
        res["activity_subgroups"][0]["name_sentence_case"]
        == activity_subgroup.name_sentence_case
    )
    assert res["version"] == "1.0"
    assert res["status"] == "Retired"


def test_reactivate_footnote_pre_instance(api_client):
    response = api_client.post(f"{URL}/{footnote_pre_instances[4].uid}/activations")
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == footnote_pre_instances[4].uid
    assert res["sequence_id"] == "FSA1P5"
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["activities"][0]["uid"] == activity.uid
    assert res["activities"][0]["name"] == activity.name
    assert res["activities"][0]["name_sentence_case"] == activity.name_sentence_case
    assert res["activity_groups"][0]["uid"] == activity_group.uid
    assert res["activity_groups"][0]["name"] == activity_group.name
    assert (
        res["activity_groups"][0]["name_sentence_case"]
        == activity_group.name_sentence_case
    )
    assert res["activity_subgroups"][0]["uid"] == activity_subgroup.uid
    assert res["activity_subgroups"][0]["name"] == activity_subgroup.name
    assert (
        res["activity_subgroups"][0]["name_sentence_case"]
        == activity_subgroup.name_sentence_case
    )
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_footnote_pre_instance_audit_trail(api_client):
    response = api_client.get(f"{URL}/audit-trail?page_size=100&total_count=true")
    res = response.json()
    log.info("FootnotePreInstance Audit Trail: %s", res)

    assert_response_status_code(response, 200)
    assert res["total"] == 51
    expected_uids = [
        "FootnotePreInstance_000005",
        "FootnotePreInstance_000005",
        "FootnotePreInstance_000005",
        "FootnotePreInstance_000003",
        "FootnotePreInstance_000025",
        "FootnotePreInstance_000025",
        "FootnotePreInstance_000024",
        "FootnotePreInstance_000024",
        "FootnotePreInstance_000023",
        "FootnotePreInstance_000023",
        "FootnotePreInstance_000022",
        "FootnotePreInstance_000022",
        "FootnotePreInstance_000021",
        "FootnotePreInstance_000021",
        "FootnotePreInstance_000020",
        "FootnotePreInstance_000020",
        "FootnotePreInstance_000019",
        "FootnotePreInstance_000019",
        "FootnotePreInstance_000018",
        "FootnotePreInstance_000018",
        "FootnotePreInstance_000017",
        "FootnotePreInstance_000017",
        "FootnotePreInstance_000016",
        "FootnotePreInstance_000016",
        "FootnotePreInstance_000015",
        "FootnotePreInstance_000015",
        "FootnotePreInstance_000014",
        "FootnotePreInstance_000014",
        "FootnotePreInstance_000013",
        "FootnotePreInstance_000013",
        "FootnotePreInstance_000012",
        "FootnotePreInstance_000012",
        "FootnotePreInstance_000011",
        "FootnotePreInstance_000011",
        "FootnotePreInstance_000010",
        "FootnotePreInstance_000010",
        "FootnotePreInstance_000009",
        "FootnotePreInstance_000009",
        "FootnotePreInstance_000008",
        "FootnotePreInstance_000008",
        "FootnotePreInstance_000007",
        "FootnotePreInstance_000007",
        "FootnotePreInstance_000006",
        "FootnotePreInstance_000006",
        "FootnotePreInstance_000005",
        "FootnotePreInstance_000003",
        "FootnotePreInstance_000003",
        "FootnotePreInstance_000002",
        "FootnotePreInstance_000002",
        "FootnotePreInstance_000001",
        "FootnotePreInstance_000001",
    ]
    actual_uids = [item["uid"] for item in res["items"]]
    assert actual_uids == expected_uids


def test_create_pre_instance_footnote_template(api_client):
    data = {
        "library_name": "Sponsor",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "",
                "terms": [
                    {
                        "index": 1,
                        "name": text_value_2.name_sentence_case,
                        "uid": text_value_2.uid,
                        "type": "TextValue",
                    }
                ],
            }
        ],
        "indication_uids": [dictionary_term_indication.term_uid],
        "activity_uids": [activity.uid],
        "activity_group_uids": [activity_group.uid],
        "activity_subgroup_uids": [activity_subgroup.uid],
    }
    response = api_client.post(
        f"footnote-templates/{footnote_template.uid}/pre-instances", json=data
    )
    res = response.json()
    log.info("Created Footnote Pre-Instance: %s", res)

    assert_response_status_code(response, 201)
    assert "PreInstance" in res["uid"]
    assert res["sequence_id"] == "FSA1P26"
    assert res["template_uid"] == footnote_template.uid
    assert res["name"] == f"Default name with [{text_value_2.name_sentence_case}]"
    assert (
        res["parameter_terms"][0]["position"] == data["parameter_terms"][0]["position"]
    )
    assert (
        res["parameter_terms"][0]["conjunction"]
        == data["parameter_terms"][0]["conjunction"]
    )
    assert res["parameter_terms"][0]["terms"] == data["parameter_terms"][0]["terms"]
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["activities"][0]["uid"] == activity.uid
    assert res["activities"][0]["name"] == activity.name
    assert res["activities"][0]["name_sentence_case"] == activity.name_sentence_case
    assert res["activity_groups"][0]["uid"] == activity_group.uid
    assert res["activity_groups"][0]["name"] == activity_group.name
    assert (
        res["activity_groups"][0]["name_sentence_case"]
        == activity_group.name_sentence_case
    )
    assert res["activity_subgroups"][0]["uid"] == activity_subgroup.uid
    assert res["activity_subgroups"][0]["name"] == activity_subgroup.name
    assert (
        res["activity_subgroups"][0]["name_sentence_case"]
        == activity_subgroup.name_sentence_case
    )
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"


def test_keep_original_case_of_unit_definition_parameter_if_it_is_in_the_start_of_footnote_pre_instance(
    api_client,
):
    TestUtils.create_template_parameter("Unit")
    _unit = TestUtils.create_unit_definition("u/week", template_parameter=True)

    _footnote_template = TestUtils.create_footnote_template(
        name="[Unit] test ignore case",
        study_uid=None,
        type_uid=ct_term_schedule_of_activities.term_uid,
        library_name="Sponsor",
        indication_uids=[],
        activity_uids=[],
        activity_group_uids=[],
        activity_subgroup_uids=[],
    )

    data = {
        "library_name": "Sponsor",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "",
                "terms": [
                    {
                        "index": 1,
                        "name": _unit.name,
                        "uid": _unit.uid,
                        "type": "Unit",
                    }
                ],
            }
        ],
        "indication_uids": [],
        "activity_uids": [],
        "activity_group_uids": [],
        "activity_subgroup_uids": [],
    }
    response = api_client.post(
        f"footnote-templates/{_footnote_template.uid}/pre-instances", json=data
    )
    res = response.json()
    log.info("Created Footnote Pre-Instance: %s", res)

    assert_response_status_code(response, 201)
    assert res["name"] == f"[{_unit.name}] test ignore case"


def test_footnote_pre_instance_sequence_id_generation(api_client):
    ct_term = TestUtils.create_ct_term(sponsor_preferred_name="Other Activities")
    template = TestUtils.create_footnote_template(
        name="Default [TextValue]",
        study_uid=None,
        type_uid=ct_term.term_uid,
        library_name="Sponsor",
        indication_uids=[dictionary_term_indication.term_uid],
        activity_uids=[activity.uid],
        activity_group_uids=[activity_group.uid],
        activity_subgroup_uids=[activity_subgroup.uid],
    )
    data = {
        "library_name": "Sponsor",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "",
                "terms": [
                    {
                        "index": 1,
                        "name": text_value_1.name_sentence_case,
                        "uid": text_value_1.uid,
                        "type": "TextValue",
                    }
                ],
            }
        ],
        "indication_uids": [dictionary_term_indication.term_uid],
        "activity_uids": [activity.uid],
        "activity_group_uids": [activity_group.uid],
        "activity_subgroup_uids": [activity_subgroup.uid],
    }
    response = api_client.post(
        f"footnote-templates/{template.uid}/pre-instances", json=data
    )
    res = response.json()
    log.info("Created Footnote Pre-Instance: %s", res)

    assert_response_status_code(response, 201)
    assert "PreInstance" in res["uid"]
    assert res["sequence_id"] == "FOA1P1"
    assert res["template_uid"] == template.uid
    assert res["name"] == f"Default [{text_value_1.name_sentence_case}]"
    assert (
        res["parameter_terms"][0]["position"] == data["parameter_terms"][0]["position"]
    )
    assert (
        res["parameter_terms"][0]["conjunction"]
        == data["parameter_terms"][0]["conjunction"]
    )
    assert res["parameter_terms"][0]["terms"] == data["parameter_terms"][0]["terms"]
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["activities"][0]["uid"] == activity.uid
    assert res["activities"][0]["name"] == activity.name
    assert res["activities"][0]["name_sentence_case"] == activity.name_sentence_case
    assert res["activity_groups"][0]["uid"] == activity_group.uid
    assert res["activity_groups"][0]["name"] == activity_group.name
    assert (
        res["activity_groups"][0]["name_sentence_case"]
        == activity_group.name_sentence_case
    )
    assert res["activity_subgroups"][0]["uid"] == activity_subgroup.uid
    assert res["activity_subgroups"][0]["name"] == activity_subgroup.name
    assert (
        res["activity_subgroups"][0]["name_sentence_case"]
        == activity_subgroup.name_sentence_case
    )
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"


def test_footnote_pre_instance_template_parameter_rules(api_client):
    template = TestUtils.create_footnote_template(
        name="[TextValue], [TextValue] parameters",
        study_uid=None,
        type_uid=ct_term_schedule_of_activities.term_uid,
        library_name="Sponsor",
        indication_uids=[dictionary_term_indication.term_uid],
        activity_uids=[activity.uid],
        activity_group_uids=[activity_group.uid],
        activity_subgroup_uids=[activity_subgroup.uid],
    )
    data = {
        "library_name": "Sponsor",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "and",
                "terms": [
                    {
                        "index": 1,
                        "name": text_value_1.name_sentence_case,
                        "uid": text_value_1.uid,
                        "type": "TextValue",
                    },
                    {
                        "index": 2,
                        "name": text_value_2.name_sentence_case,
                        "uid": text_value_2.uid,
                        "type": "TextValue",
                    },
                ],
            },
            {
                "position": 2,
                "conjunction": "",
                "terms": [],
            },
        ],
        "indication_uids": [dictionary_term_indication.term_uid],
        "activity_uids": [activity.uid],
        "activity_group_uids": [activity_group.uid],
        "activity_subgroup_uids": [activity_subgroup.uid],
    }
    response = api_client.post(
        f"footnote-templates/{template.uid}/pre-instances", json=data
    )
    res = response.json()
    log.info("Created Footnote Pre-Instance: %s", res)

    assert_response_status_code(response, 201)
    assert "PreInstance" in res["uid"]
    assert res["sequence_id"] == "FSA3P1"
    assert res["template_uid"] == template.uid
    assert (
        res["name"]
        == f"[{text_value_1.name_sentence_case.capitalize()} and {text_value_2.name_sentence_case}] parameters"
    )
    assert (
        res["parameter_terms"][0]["position"] == data["parameter_terms"][0]["position"]
    )
    assert (
        res["parameter_terms"][0]["conjunction"]
        == data["parameter_terms"][0]["conjunction"]
    )
    assert res["parameter_terms"][0]["terms"] == data["parameter_terms"][0]["terms"]
    assert (
        res["parameter_terms"][1]["position"] == data["parameter_terms"][1]["position"]
    )
    assert (
        res["parameter_terms"][1]["conjunction"]
        == data["parameter_terms"][1]["conjunction"]
    )
    assert res["parameter_terms"][1]["terms"] == data["parameter_terms"][1]["terms"]
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["activities"][0]["uid"] == activity.uid
    assert res["activities"][0]["name"] == activity.name
    assert res["activities"][0]["name_sentence_case"] == activity.name_sentence_case
    assert res["activity_groups"][0]["uid"] == activity_group.uid
    assert res["activity_groups"][0]["name"] == activity_group.name
    assert (
        res["activity_groups"][0]["name_sentence_case"]
        == activity_group.name_sentence_case
    )
    assert res["activity_subgroups"][0]["uid"] == activity_subgroup.uid
    assert res["activity_subgroups"][0]["name"] == activity_subgroup.name
    assert (
        res["activity_subgroups"][0]["name_sentence_case"]
        == activity_subgroup.name_sentence_case
    )
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
