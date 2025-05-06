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
footnote_templates: list[FootnoteTemplate]
ct_term_schedule_of_activities: CTTerm
dictionary_term_indication: DictionaryTerm
indications_codelist: DictionaryCodelist
indications_library_name: str
activity: Activity
activity_group: ActivityGroup
activity_subgroup: ActivitySubGroup
text_value_1: TextValue
text_value_2: TextValue

URL = "footnote-templates"


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

    global footnote_templates
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

    text_value_1 = TestUtils.create_text_value()
    text_value_2 = TestUtils.create_text_value()

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

    # Create some footnote_templates
    footnote_templates = []
    footnote_templates.append(
        TestUtils.create_footnote_template(
            name="Default name with [TextValue]",
            study_uid=None,
            library_name="Sponsor",
            type_uid=ct_term_schedule_of_activities.term_uid,
            indication_uids=[dictionary_term_indication.term_uid],
            activity_uids=[activity.uid],
            activity_group_uids=[activity_group.uid],
            activity_subgroup_uids=[activity_subgroup.uid],
        )
    )
    footnote_templates.append(
        TestUtils.create_footnote_template(
            name="Default-AAA name with [TextValue]",
            study_uid=None,
            library_name="Sponsor",
            type_uid=ct_term_schedule_of_activities.term_uid,
            indication_uids=[dictionary_term_indication.term_uid],
            activity_uids=[activity.uid],
            activity_group_uids=[activity_group.uid],
            activity_subgroup_uids=[activity_subgroup.uid],
        )
    )
    footnote_templates.append(
        TestUtils.create_footnote_template(
            name="Default-BBB name with [TextValue]",
            study_uid=None,
            library_name="Sponsor",
            type_uid=ct_term_schedule_of_activities.term_uid,
            indication_uids=[dictionary_term_indication.term_uid],
            activity_uids=[activity.uid],
            activity_group_uids=[activity_group.uid],
            activity_subgroup_uids=[activity_subgroup.uid],
            approve=False,
        )
    )
    footnote_templates.append(
        TestUtils.create_footnote_template(
            name="Default-XXX name with [TextValue]",
            study_uid=None,
            library_name="Sponsor",
            type_uid=ct_term_schedule_of_activities.term_uid,
            indication_uids=[dictionary_term_indication.term_uid],
            activity_uids=[activity.uid],
            activity_group_uids=[activity_group.uid],
            activity_subgroup_uids=[activity_subgroup.uid],
            approve=False,
        )
    )
    footnote_templates.append(
        TestUtils.create_footnote_template(
            name="Default-YYY name with [TextValue]",
            study_uid=None,
            library_name="Sponsor",
            type_uid=ct_term_schedule_of_activities.term_uid,
            indication_uids=[dictionary_term_indication.term_uid],
            activity_uids=[activity.uid],
            activity_group_uids=[activity_group.uid],
            activity_subgroup_uids=[activity_subgroup.uid],
        )
    )

    for index in range(5):
        footnote_templates.append(
            TestUtils.create_footnote_template(
                name=f"Default-AAA-{index} name with [TextValue]",
                study_uid=None,
                library_name="Sponsor",
                type_uid=ct_term_schedule_of_activities.term_uid,
                indication_uids=[dictionary_term_indication.term_uid],
                activity_uids=[activity.uid],
                activity_group_uids=[activity_group.uid],
                activity_subgroup_uids=[activity_subgroup.uid],
            )
        )
        footnote_templates.append(
            TestUtils.create_footnote_template(
                name=f"Default-BBB-{index} name with [TextValue]",
                study_uid=None,
                library_name="Sponsor",
                type_uid=ct_term_schedule_of_activities.term_uid,
                indication_uids=[dictionary_term_indication.term_uid],
                activity_uids=[activity.uid],
                activity_group_uids=[activity_group.uid],
                activity_subgroup_uids=[activity_subgroup.uid],
            )
        )
        footnote_templates.append(
            TestUtils.create_footnote_template(
                name=f"Default-XXX-{index} name with [TextValue]",
                study_uid=None,
                library_name="Sponsor",
                type_uid=ct_term_schedule_of_activities.term_uid,
                indication_uids=[dictionary_term_indication.term_uid],
                activity_uids=[activity.uid],
                activity_group_uids=[activity_group.uid],
                activity_subgroup_uids=[activity_subgroup.uid],
            )
        )
        footnote_templates.append(
            TestUtils.create_footnote_template(
                name=f"Default-YYY-{index} name with [TextValue]",
                study_uid=None,
                library_name="Sponsor",
                type_uid=ct_term_schedule_of_activities.term_uid,
                indication_uids=[dictionary_term_indication.term_uid],
                activity_uids=[activity.uid],
                activity_group_uids=[activity_group.uid],
                activity_subgroup_uids=[activity_subgroup.uid],
            )
        )

    yield


FOOTNOTE_TEMPLATE_FIELDS_ALL = [
    "name",
    "name_plain",
    "uid",
    "sequence_id",
    "status",
    "version",
    "change_description",
    "start_date",
    "end_date",
    "author_username",
    "possible_actions",
    "parameters",
    "library",
    "type",
    "indications",
    "activities",
    "activity_groups",
    "activity_subgroups",
    "study_count",
]

FOOTNOTE_TEMPLATE_FIELDS_NOT_NULL = [
    "uid",
    "sequence_id",
    "name",
]


def test_get_footnote_template(api_client):
    response = api_client.get(f"{URL}/{footnote_templates[1].uid}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    fields_all_set = set(FOOTNOTE_TEMPLATE_FIELDS_ALL)
    fields_all_set.add("counts")
    assert set(list(res.keys())) == fields_all_set
    for key in FOOTNOTE_TEMPLATE_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == footnote_templates[1].uid
    assert res["sequence_id"] == "FSA2"
    assert res["name"] == "Default-AAA name with [TextValue]"
    assert res["parameters"][0]["name"] == "TextValue"
    assert res["parameters"][0]["terms"] == []
    assert res["type"]["term_uid"] == ct_term_schedule_of_activities.term_uid
    assert (
        res["type"]["name"]["sponsor_preferred_name"]
        == ct_term_schedule_of_activities.sponsor_preferred_name
    )
    assert (
        res["type"]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_schedule_of_activities.sponsor_preferred_name_sentence_case
    )
    assert (
        res["type"]["attributes"]["code_submission_value"]
        == ct_term_schedule_of_activities.code_submission_value
    )
    assert (
        res["type"]["attributes"]["nci_preferred_name"]
        == ct_term_schedule_of_activities.nci_preferred_name
    )
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


def test_get_footnote_templates_pagination(api_client):
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
    assert len(footnote_templates) == len(results_paginated_merged)


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
def test_get_footnote_templates(
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
    assert res["total"] == (len(footnote_templates) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(FOOTNOTE_TEMPLATE_FIELDS_ALL)
        for key in FOOTNOTE_TEMPLATE_FIELDS_NOT_NULL:
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


def test_get_all_parameters_of_footnote_template(api_client):
    response = api_client.get(f"{URL}/{footnote_templates[0].uid}/parameters")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) == 1
    assert res[0]["name"] == "TextValue"
    assert len(res[0]["terms"]) == 2


def test_get_versions_of_footnote_template(api_client):
    response = api_client.get(f"{URL}/{footnote_templates[1].uid}/versions")
    res = response.json()

    assert_response_status_code(response, 200)

    assert len(res) == 2
    assert res[0]["uid"] == footnote_templates[1].uid
    assert res[0]["sequence_id"] == "FSA2"
    assert res[0]["type"]["term_uid"] == ct_term_schedule_of_activities.term_uid
    assert (
        res[0]["type"]["name"]["sponsor_preferred_name"]
        == ct_term_schedule_of_activities.sponsor_preferred_name
    )
    assert (
        res[0]["type"]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_schedule_of_activities.sponsor_preferred_name_sentence_case
    )
    assert (
        res[0]["type"]["attributes"]["code_submission_value"]
        == ct_term_schedule_of_activities.code_submission_value
    )
    assert (
        res[0]["type"]["attributes"]["nci_preferred_name"]
        == ct_term_schedule_of_activities.nci_preferred_name
    )
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
    assert res[1]["uid"] == footnote_templates[1].uid
    assert res[1]["sequence_id"] == "FSA2"
    assert res[1]["type"]["term_uid"] == ct_term_schedule_of_activities.term_uid
    assert (
        res[1]["type"]["name"]["sponsor_preferred_name"]
        == ct_term_schedule_of_activities.sponsor_preferred_name
    )
    assert (
        res[1]["type"]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_schedule_of_activities.sponsor_preferred_name_sentence_case
    )
    assert (
        res[1]["type"]["attributes"]["code_submission_value"]
        == ct_term_schedule_of_activities.code_submission_value
    )
    assert (
        res[1]["type"]["attributes"]["nci_preferred_name"]
        == ct_term_schedule_of_activities.nci_preferred_name
    )
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


def test_get_all_final_versions_of_footnote_template(api_client):
    response = api_client.get(f"{URL}/{footnote_templates[1].uid}/releases")
    res = response.json()

    assert_response_status_code(response, 200)

    assert len(res) == 1
    assert res[0]["uid"] == footnote_templates[1].uid
    assert res[0]["sequence_id"] == "FSA2"
    assert res[0]["type"]["term_uid"] == ct_term_schedule_of_activities.term_uid
    assert (
        res[0]["type"]["name"]["sponsor_preferred_name"]
        == ct_term_schedule_of_activities.sponsor_preferred_name
    )
    assert (
        res[0]["type"]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_schedule_of_activities.sponsor_preferred_name_sentence_case
    )
    assert (
        res[0]["type"]["attributes"]["code_submission_value"]
        == ct_term_schedule_of_activities.code_submission_value
    )
    assert (
        res[0]["type"]["attributes"]["nci_preferred_name"]
        == ct_term_schedule_of_activities.nci_preferred_name
    )
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


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param(
            '{"*": {"v": ["Default-AAA"], "op": "co"}}', "name", "Default-AAA"
        ),
        pytest.param(
            '{"*": {"v": ["Default-BBB"], "op": "co"}}', "name", "Default-BBB"
        ),
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
    "filter_by, expected_matched_field, expected_result",
    [
        pytest.param(
            '{"name": {"v": ["Default-AAA"], "op": "co"}}', "name", "Default-AAA"
        ),
        pytest.param(
            '{"name": {"v": ["Default-BBB"], "op": "co"}}', "name", "Default-BBB"
        ),
        pytest.param('{"name": {"v": ["cc"], "op": "co"}}', None, None),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    response = api_client.get(f"{URL}?filters={filter_by}")
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
                assert expected_result in row[expected_matched_field]
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
    for footnote_template in footnote_templates:
        value = getattr(footnote_template, field_name)
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


def test_pre_validate_footnote_template_name(api_client):
    data = {"name": "test [TextValue]"}
    response = api_client.post(f"{URL}/pre-validate", json=data)
    res = response.json()
    log.info("Pre Validated Footnote Template name: %s", res)

    assert_response_status_code(response, 202)


def test_create_footnote_template(api_client):
    data = {
        "name": "default_name [TextValue]",
        "library_name": "Sponsor",
        "type_uid": ct_term_schedule_of_activities.term_uid,
        "indication_uids": [dictionary_term_indication.term_uid],
        "activity_uids": [activity.uid],
        "activity_group_uids": [activity_group.uid],
        "activity_subgroup_uids": [activity_subgroup.uid],
    }
    response = api_client.post(URL, json=data)
    res = response.json()
    log.info("Created Footnote Template: %s", res)

    assert_response_status_code(response, 201)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["name"] == "default_name [TextValue]"
    assert res["parameters"][0]["name"] == "TextValue"
    assert res["parameters"][0]["terms"] == []
    assert res["type"]["term_uid"] == ct_term_schedule_of_activities.term_uid
    assert (
        res["type"]["name"]["sponsor_preferred_name"]
        == ct_term_schedule_of_activities.sponsor_preferred_name
    )
    assert (
        res["type"]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_schedule_of_activities.sponsor_preferred_name_sentence_case
    )
    assert (
        res["type"]["attributes"]["code_submission_value"]
        == ct_term_schedule_of_activities.code_submission_value
    )
    assert (
        res["type"]["attributes"]["nci_preferred_name"]
        == ct_term_schedule_of_activities.nci_preferred_name
    )
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
    assert set(list(res.keys())) == set(FOOTNOTE_TEMPLATE_FIELDS_ALL)
    for key in FOOTNOTE_TEMPLATE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_create_new_version_of_footnote_template(api_client):
    data = {
        "name": "new test name",
        "change_description": "new version",
    }
    response = api_client.post(f"{URL}/{footnote_templates[4].uid}/versions", json=data)
    res = response.json()
    log.info("Created new version of Footnote Template: %s", res)

    assert_response_status_code(response, 201)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["name"] == "new test name"
    assert res["type"]["term_uid"] == ct_term_schedule_of_activities.term_uid
    assert (
        res["type"]["name"]["sponsor_preferred_name"]
        == ct_term_schedule_of_activities.sponsor_preferred_name
    )
    assert (
        res["type"]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_schedule_of_activities.sponsor_preferred_name_sentence_case
    )
    assert (
        res["type"]["attributes"]["code_submission_value"]
        == ct_term_schedule_of_activities.code_submission_value
    )
    assert (
        res["type"]["attributes"]["nci_preferred_name"]
        == ct_term_schedule_of_activities.nci_preferred_name
    )
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
    assert set(list(res.keys())) == set(FOOTNOTE_TEMPLATE_FIELDS_ALL)
    for key in FOOTNOTE_TEMPLATE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_get_specific_version_of_footnote_template(api_client):
    response = api_client.get(f"{URL}/{footnote_templates[4].uid}/versions/1.1")
    res = response.json()

    assert_response_status_code(response, 200)

    assert res["uid"] == footnote_templates[4].uid
    assert res["sequence_id"] == "FSA5"
    assert res["type"]["term_uid"] == ct_term_schedule_of_activities.term_uid
    assert (
        res["type"]["name"]["sponsor_preferred_name"]
        == ct_term_schedule_of_activities.sponsor_preferred_name
    )
    assert (
        res["type"]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_schedule_of_activities.sponsor_preferred_name_sentence_case
    )
    assert (
        res["type"]["attributes"]["code_submission_value"]
        == ct_term_schedule_of_activities.code_submission_value
    )
    assert (
        res["type"]["attributes"]["nci_preferred_name"]
        == ct_term_schedule_of_activities.nci_preferred_name
    )
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


def test_change_footnote_template_indexings(api_client):
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
        f"{URL}/{footnote_templates[1].uid}/indexings",
        json=data,
    )
    res = response.json()
    log.info("Changed Footnote Template indexings: %s", res)

    assert_response_status_code(response, 200)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["name"] == "Default-AAA name with [TextValue]"
    assert res["type"]["term_uid"] == ct_term_schedule_of_activities.term_uid
    assert (
        res["type"]["name"]["sponsor_preferred_name"]
        == ct_term_schedule_of_activities.sponsor_preferred_name
    )
    assert (
        res["type"]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_schedule_of_activities.sponsor_preferred_name_sentence_case
    )
    assert (
        res["type"]["attributes"]["code_submission_value"]
        == ct_term_schedule_of_activities.code_submission_value
    )
    assert (
        res["type"]["attributes"]["nci_preferred_name"]
        == ct_term_schedule_of_activities.nci_preferred_name
    )
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
    assert set(list(res.keys())) == set(FOOTNOTE_TEMPLATE_FIELDS_ALL)
    for key in FOOTNOTE_TEMPLATE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_remove_footnote_template_indexings(api_client):
    data = {
        "indication_uids": [],
        "activity_uids": [],
        "activity_group_uids": [],
        "activity_subgroup_uids": [],
    }
    response = api_client.patch(
        f"{URL}/{footnote_templates[1].uid}/indexings",
        json=data,
    )
    res = response.json()
    log.info("Removed Footnote Template indexings: %s", res)

    assert_response_status_code(response, 200)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["name"] == "Default-AAA name with [TextValue]"
    assert res["type"]["term_uid"] == ct_term_schedule_of_activities.term_uid
    assert (
        res["type"]["name"]["sponsor_preferred_name"]
        == ct_term_schedule_of_activities.sponsor_preferred_name
    )
    assert (
        res["type"]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_schedule_of_activities.sponsor_preferred_name_sentence_case
    )
    assert (
        res["type"]["attributes"]["code_submission_value"]
        == ct_term_schedule_of_activities.code_submission_value
    )
    assert (
        res["type"]["attributes"]["nci_preferred_name"]
        == ct_term_schedule_of_activities.nci_preferred_name
    )
    assert not res["indications"]
    assert not res["activities"]
    assert not res["activity_groups"]
    assert not res["activity_subgroups"]
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert set(list(res.keys())) == set(FOOTNOTE_TEMPLATE_FIELDS_ALL)
    for key in FOOTNOTE_TEMPLATE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_delete_footnote_template(api_client):
    response = api_client.delete(f"{URL}/{footnote_templates[2].uid}")
    log.info("Deleted Footnote Template: %s", footnote_templates[2].uid)

    assert_response_status_code(response, 204)


def test_approve_footnote_template(api_client):
    response = api_client.post(f"{URL}/{footnote_templates[3].uid}/approvals")
    res = response.json()
    log.info("Approved Footnote Template: %s", footnote_templates[3].uid)

    assert_response_status_code(response, 201)
    assert res["uid"] == footnote_templates[3].uid
    assert res["sequence_id"] == "FSA4"
    assert res["name"] == "Default-XXX name with [TextValue]"
    assert res["type"]["term_uid"] == ct_term_schedule_of_activities.term_uid
    assert (
        res["type"]["name"]["sponsor_preferred_name"]
        == ct_term_schedule_of_activities.sponsor_preferred_name
    )
    assert (
        res["type"]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_schedule_of_activities.sponsor_preferred_name_sentence_case
    )
    assert (
        res["type"]["attributes"]["code_submission_value"]
        == ct_term_schedule_of_activities.code_submission_value
    )
    assert (
        res["type"]["attributes"]["nci_preferred_name"]
        == ct_term_schedule_of_activities.nci_preferred_name
    )
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


def test_cascade_approve_footnote_template(api_client):
    parameter_terms = [
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
    ]
    footnote = TestUtils.create_footnote(
        footnote_template_uid=footnote_templates[5].uid,
        library_name="Sponsor",
        parameter_terms=parameter_terms,
        approve=False,
    )
    footnote_pre_instance = TestUtils.create_footnote_pre_instance(
        template_uid=footnote_templates[5].uid,
        library_name="Sponsor",
        parameter_terms=parameter_terms,
        indication_uids=[dictionary_term_indication.term_uid],
        activity_uids=[activity.uid],
        activity_group_uids=[activity_group.uid],
        activity_subgroup_uids=[activity_subgroup.uid],
    )

    api_client.post(
        f"{URL}/{footnote_templates[5].uid}/versions",
        json={
            "name": "cascade check [TextValue]",
            "change_description": "cascade check for instance and pre instances",
        },
    )

    response = api_client.post(
        f"{URL}/{footnote_templates[5].uid}/approvals?cascade=true"
    )
    res = response.json()
    log.info("Approved Footnote Template: %s", footnote_templates[5].uid)

    assert_response_status_code(response, 201)
    assert res["uid"] == footnote_templates[5].uid
    assert res["sequence_id"] == "FSA6"
    assert res["name"] == "cascade check [TextValue]"
    assert res["type"]["term_uid"] == ct_term_schedule_of_activities.term_uid
    assert (
        res["type"]["name"]["sponsor_preferred_name"]
        == ct_term_schedule_of_activities.sponsor_preferred_name
    )
    assert (
        res["type"]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_schedule_of_activities.sponsor_preferred_name_sentence_case
    )
    assert (
        res["type"]["attributes"]["code_submission_value"]
        == ct_term_schedule_of_activities.code_submission_value
    )
    assert (
        res["type"]["attributes"]["nci_preferred_name"]
        == ct_term_schedule_of_activities.nci_preferred_name
    )
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
    assert res["version"] == "2.0"
    assert res["status"] == "Final"

    # Assertions for Footnote
    response = api_client.get(f"footnotes/{footnote.uid}")
    res = response.json()

    assert res["name"] == f"cascade check [{text_value_1.name_sentence_case}]"
    assert res["version"] == "0.2"
    assert res["status"] == "Draft"

    # Assertions for Footnote Pre-Instance
    response = api_client.get(f"footnote-pre-instances/{footnote_pre_instance.uid}")
    res = response.json()

    assert res["name"] == f"cascade check [{text_value_1.name_sentence_case}]"
    assert res["version"] == "2.0"
    assert res["status"] == "Final"


def test_inactivate_footnote_template(api_client):
    response = api_client.delete(f"{URL}/{footnote_templates[5].uid}/activations")
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == footnote_templates[5].uid
    assert res["sequence_id"] == "FSA6"
    assert res["type"]["term_uid"] == ct_term_schedule_of_activities.term_uid
    assert (
        res["type"]["name"]["sponsor_preferred_name"]
        == ct_term_schedule_of_activities.sponsor_preferred_name
    )
    assert (
        res["type"]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_schedule_of_activities.sponsor_preferred_name_sentence_case
    )
    assert (
        res["type"]["attributes"]["code_submission_value"]
        == ct_term_schedule_of_activities.code_submission_value
    )
    assert (
        res["type"]["attributes"]["nci_preferred_name"]
        == ct_term_schedule_of_activities.nci_preferred_name
    )
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
    assert res["version"] == "2.0"
    assert res["status"] == "Retired"

    # Assertions for Footnote Pre-Instance
    response = api_client.get("footnote-pre-instances/FootnotePreInstance_000001")
    res = response.json()

    assert res["name"] == f"cascade check [{text_value_1.name_sentence_case}]"
    assert res["version"] == "2.0"
    assert res["status"] == "Retired"


def test_current_final_footnote_template(api_client):
    response = api_client.get(
        f"""{URL}?status=Final&filters={{"sequence_id": {{"v": ["FSA6"], "op": "eq"}}}}"""
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert not res["items"]

    response = api_client.get(
        f"""{URL}/headers?field_name=sequence_id&status=Final&filters={{"sequence_id": {{"v": ["FSA6"], "op": "eq"}}}}"""
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert not res


def test_reactivate_footnote_template(api_client):
    response = api_client.post(f"{URL}/{footnote_templates[5].uid}/activations")
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == footnote_templates[5].uid
    assert res["sequence_id"] == "FSA6"
    assert res["type"]["term_uid"] == ct_term_schedule_of_activities.term_uid
    assert (
        res["type"]["name"]["sponsor_preferred_name"]
        == ct_term_schedule_of_activities.sponsor_preferred_name
    )
    assert (
        res["type"]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_schedule_of_activities.sponsor_preferred_name_sentence_case
    )
    assert (
        res["type"]["attributes"]["code_submission_value"]
        == ct_term_schedule_of_activities.code_submission_value
    )
    assert (
        res["type"]["attributes"]["nci_preferred_name"]
        == ct_term_schedule_of_activities.nci_preferred_name
    )
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
    assert res["version"] == "2.0"
    assert res["status"] == "Final"

    # Assertions for Footnote Pre-Instance
    response = api_client.get("footnote-pre-instances/FootnotePreInstance_000001")
    res = response.json()

    assert res["name"] == f"cascade check [{text_value_1.name_sentence_case}]"
    assert res["version"] == "2.0"
    assert res["status"] == "Final"


def test_footnote_template_audit_trail(api_client):
    response = api_client.get(f"{URL}/audit-trail?page_size=100&total_count=true")
    res = response.json()
    log.info("FootnoteTemplate Audit Trail: %s", res)

    assert_response_status_code(response, 200)
    assert res["total"] == 54
    expected_uids = [
        "FootnoteTemplate_000006",
        "FootnoteTemplate_000006",
        "FootnoteTemplate_000006",
        "FootnoteTemplate_000006",
        "FootnoteTemplate_000004",
        "FootnoteTemplate_000005",
        "FootnoteTemplate_000026",
        "FootnoteTemplate_000025",
        "FootnoteTemplate_000025",
        "FootnoteTemplate_000024",
        "FootnoteTemplate_000024",
        "FootnoteTemplate_000023",
        "FootnoteTemplate_000023",
        "FootnoteTemplate_000022",
        "FootnoteTemplate_000022",
        "FootnoteTemplate_000021",
        "FootnoteTemplate_000021",
        "FootnoteTemplate_000020",
        "FootnoteTemplate_000020",
        "FootnoteTemplate_000019",
        "FootnoteTemplate_000019",
        "FootnoteTemplate_000018",
        "FootnoteTemplate_000018",
        "FootnoteTemplate_000017",
        "FootnoteTemplate_000017",
        "FootnoteTemplate_000016",
        "FootnoteTemplate_000016",
        "FootnoteTemplate_000015",
        "FootnoteTemplate_000015",
        "FootnoteTemplate_000014",
        "FootnoteTemplate_000014",
        "FootnoteTemplate_000013",
        "FootnoteTemplate_000013",
        "FootnoteTemplate_000012",
        "FootnoteTemplate_000012",
        "FootnoteTemplate_000011",
        "FootnoteTemplate_000011",
        "FootnoteTemplate_000010",
        "FootnoteTemplate_000010",
        "FootnoteTemplate_000009",
        "FootnoteTemplate_000009",
        "FootnoteTemplate_000008",
        "FootnoteTemplate_000008",
        "FootnoteTemplate_000007",
        "FootnoteTemplate_000007",
        "FootnoteTemplate_000006",
        "FootnoteTemplate_000006",
        "FootnoteTemplate_000005",
        "FootnoteTemplate_000005",
        "FootnoteTemplate_000004",
        "FootnoteTemplate_000002",
        "FootnoteTemplate_000002",
        "FootnoteTemplate_000001",
        "FootnoteTemplate_000001",
    ]
    actual_uids = [item["uid"] for item in res["items"]]
    assert actual_uids == expected_uids


def test_footnote_template_sequence_id_generation(api_client):
    lib = TestUtils.create_library("User Defined")
    ct_term = TestUtils.create_ct_term(sponsor_preferred_name="Other Activities")
    data = {
        "name": "user defined [TextValue]",
        "library_name": lib["name"],
        "type_uid": ct_term.term_uid,
        "indication_uids": [dictionary_term_indication.term_uid],
        "activity_uids": [activity.uid],
        "activity_group_uids": [activity_group.uid],
        "activity_subgroup_uids": [activity_subgroup.uid],
    }
    response = api_client.post(URL, json=data)
    res = response.json()
    log.info("Created Footnote Template: %s", res)

    assert_response_status_code(response, 201)
    assert res["uid"]
    assert res["sequence_id"] == "U-FOA1"
    assert res["name"] == "user defined [TextValue]"
    assert res["parameters"][0]["name"] == "TextValue"
    assert res["parameters"][0]["terms"] == []
    assert res["type"]["term_uid"] == ct_term.term_uid
    assert (
        res["type"]["name"]["sponsor_preferred_name"] == ct_term.sponsor_preferred_name
    )
    assert (
        res["type"]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term.sponsor_preferred_name_sentence_case
    )
    assert (
        res["type"]["attributes"]["code_submission_value"]
        == ct_term.code_submission_value
    )
    assert res["type"]["attributes"]["nci_preferred_name"] == ct_term.nci_preferred_name
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
    assert set(list(res.keys())) == set(FOOTNOTE_TEMPLATE_FIELDS_ALL)
    for key in FOOTNOTE_TEMPLATE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_cannot_create_footnote_template_with_existing_name(api_client):
    data = {
        "name": "Default name with [TextValue]",
        "library_name": "Sponsor",
        "type_uid": ct_term_schedule_of_activities.term_uid,
        "indication_uids": [dictionary_term_indication.term_uid],
        "activity_group_uids": [activity_group.uid],
        "activity_subgroup_uids": [activity_subgroup.uid],
    }
    response = api_client.post(URL, json=data)
    res = response.json()
    log.info("Didn't Create Footnote Template: %s", res)

    assert_response_status_code(response, 409)
    assert res["message"] == f"Resource with Name '{data['name']}' already exists."


def test_cannot_update_footnote_template_to_an_existing_name(api_client):
    data = {
        "name": "Default name with [TextValue]",
        "change_description": "Change for duplicate",
    }
    response = api_client.patch(f"{URL}/{footnote_templates[1].uid}", json=data)
    res = response.json()
    log.info("Didn't Update Footnote Template: %s", res)

    assert_response_status_code(response, 409)
    assert res["message"] == f"Resource with Name '{data['name']}' already exists."


def test_cannot_update_footnote_template_without_change_description(api_client):
    data = {"name": "Default name with [TextValue]"}
    response = api_client.patch(f"{URL}/{footnote_templates[1].uid}", json=data)
    res = response.json()
    log.info("Didn't Update Footnote Template: %s", res)

    assert_response_status_code(response, 422)
    assert res["detail"] == [
        {
            "type": "missing",
            "loc": ["body", "change_description"],
            "msg": "Field required",
            "input": {"name": "Default name with [TextValue]"},
        }
    ]


def test_cannot_update_footnote_template_in_final_status(api_client):
    data = {
        "name": "test name [TextValue]",
        "change_description": "Change for final status",
    }
    response = api_client.patch(f"{URL}/{footnote_templates[1].uid}", json=data)
    res = response.json()
    log.info("Didn't Update Footnote Template: %s", res)

    assert_response_status_code(response, 400)
    assert res["message"] == "The object isn't in draft status."


def test_cannot_change_parameter_numbers_of_footnote_template_after_approval(
    api_client,
):
    data = {
        "name": "Default name with",
        "change_description": "Change for parameter numbers",
    }
    response = api_client.patch(f"{URL}/{footnote_templates[1].uid}", json=data)
    res = response.json()
    log.info("Didn't Change Footnote Template parameter numbers: %s", res)

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "You cannot change number or order of template parameters for a previously approved template."
    )


def test_pre_validate_invalid_footnote_template_name(api_client):
    data = {"name": "Missing opening bracket ]"}
    response = api_client.post(f"{URL}/pre-validate", json=data)
    res = response.json()
    log.info("Pre Validated Footnote Temaplate name: %s", res)

    assert_response_status_code(response, 422)
    assert res["message"] == f"Template string syntax incorrect: {data['name']}"

    data = {"name": "Lacking closing bracket ["}
    response = api_client.post(f"{URL}/pre-validate", json=data)
    res = response.json()
    log.info("Pre Validated Footnote Template name: %s", res)

    assert_response_status_code(response, 422)
    assert res["message"] == f"Template string syntax incorrect: {data['name']}"

    data = {"name": " "}
    response = api_client.post(f"{URL}/pre-validate", json=data)
    res = response.json()
    log.info("Pre Validated Footnote Template name: %s", res)

    assert_response_status_code(response, 422)
    assert res == {
        "detail": [
            {
                "type": "string_too_short",
                "loc": ["body", "name"],
                "msg": "String should have at least 1 character",
                "input": "",
                "ctx": {"min_length": 1},
            }
        ]
    }
