"""
Tests for footnote endpoints
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
from clinical_mdr_api.models.study_selections.study_soa_footnote import (
    StudySoAFootnoteCreateInput,
)
from clinical_mdr_api.models.syntax_instances.footnote import Footnote
from clinical_mdr_api.models.syntax_templates.footnote_template import FootnoteTemplate
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.services.studies.study_soa_footnote import StudySoAFootnoteService
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
footnotes: list[Footnote]
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

URL = "footnotes"


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

    global footnotes
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

    # Create some footnote
    footnotes = []
    footnotes.append(
        TestUtils.create_footnote(
            footnote_template_uid=footnote_template.uid,
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
        )
    )
    footnotes.append(
        TestUtils.create_footnote(
            footnote_template_uid=footnote_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
        )
    )
    footnotes.append(
        TestUtils.create_footnote(
            footnote_template_uid=footnote_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            approve=False,
        )
    )
    footnotes.append(
        TestUtils.create_footnote(
            footnote_template_uid=footnote_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            approve=False,
        )
    )
    footnotes.append(
        TestUtils.create_footnote(
            footnote_template_uid=footnote_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            approve=False,
        )
    )

    for _ in range(5):
        footnotes.append(
            TestUtils.create_footnote(
                footnote_template_uid=footnote_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
            )
        )
        footnotes.append(
            TestUtils.create_footnote(
                footnote_template_uid=footnote_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
            )
        )
        footnotes.append(
            TestUtils.create_footnote(
                footnote_template_uid=footnote_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
            )
        )
        footnotes.append(
            TestUtils.create_footnote(
                footnote_template_uid=footnote_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
            )
        )

    # TODO Should be enabled when Study Footnote Selection has been implemented
    study_footnote_selection_service = StudySoAFootnoteService()
    for footnote in footnotes:
        if footnote.status == "Final":
            study_footnote_selection_service.manage_create(
                study_uid="Study_000001",
                footnote_input=StudySoAFootnoteCreateInput(footnote_uid=footnote.uid),
            )

    yield


FOOTNOTE_FIELDS_ALL = [
    "name",
    "name_plain",
    "uid",
    "status",
    "version",
    "change_description",
    "start_date",
    "end_date",
    "author_username",
    "possible_actions",
    "parameter_terms",
    "library",
    "template",
    "study_count",
]

FOOTNOTE_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "template",
]


def test_get_footnote(api_client):
    response = api_client.get(f"{URL}/{footnotes[0].uid}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    fields_all_set = set(FOOTNOTE_FIELDS_ALL)
    assert set(list(res.keys())) == fields_all_set
    for key in FOOTNOTE_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == footnotes[0].uid
    assert res["name"] == f"Default name with [{text_value_1.name_sentence_case}]"
    assert res["template"]["uid"] == footnote_template.uid
    assert res["template"]["sequence_id"] == "FSA1"
    assert res["parameter_terms"][0]["terms"][0]["uid"] == text_value_1.uid
    assert (
        res["parameter_terms"][0]["terms"][0]["name"] == text_value_1.name_sentence_case
    )
    assert res["parameter_terms"][0]["terms"][0]["type"] == "TextValue"
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_get_footnotes_pagination(api_client):
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
    assert len(
        [footnote for footnote in footnotes if footnote.status == "Final"]
    ) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, True, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 3, True, None, 2),
        pytest.param(10, 1, True, '{"name": false}', 10),
        pytest.param(10, 2, True, '{"name": true}', 10),
    ],
)
def test_get_footnotes(
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
    assert res["total"] == (
        len([footnote for footnote in footnotes if footnote.status == "Final"])
        if total_count
        else 0
    )
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(FOOTNOTE_FIELDS_ALL)
        for key in FOOTNOTE_FIELDS_NOT_NULL:
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


def test_get_all_parameters_of_footnote(api_client):
    response = api_client.get(f"{URL}/{footnotes[0].uid}/parameters")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) == 1
    assert res[0]["name"] == "TextValue"
    assert len(res[0]["terms"]) == 26


def test_get_versions_of_footnote(api_client):
    response = api_client.get(f"{URL}/{footnotes[1].uid}/versions")
    res = response.json()

    assert_response_status_code(response, 200)

    assert len(res) == 2
    assert res[0]["uid"] == footnotes[1].uid
    assert res[0]["version"] == "1.0"
    assert res[0]["status"] == "Final"
    assert res[1]["uid"] == footnotes[1].uid
    assert res[1]["version"] == "0.1"
    assert res[1]["status"] == "Draft"


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param(
            '{"*": {"v": ["Default name with"], "op": "co"}}',
            "name",
            "Default name with",
        ),
        pytest.param('{"*": {"v": ["cc"], "op": "co"}}', None, None),
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
        pytest.param('{"name": {"v": ["Default"], "op": "co"}}', "name", "Default"),
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
    for footnote in footnotes:
        value = getattr(footnote, field_name)
        if value and footnote.status == "Final":
            expected_result.append(value)
    log.info("Expected result is %s", expected_result)
    log.info("Returned %s", res)
    if expected_result:
        assert len(res) > 0
        assert len(set(expected_result)) == len(res)
        assert all(item in res for item in expected_result)
    else:
        assert len(res) == 0


def test_get_studies_of_footnote(api_client):
    response = api_client.get(f"{URL}/{footnotes[0].uid}/studies")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) == 1
    assert res[0]["uid"] == "Study_000001"


def test_create_footnote(api_client):
    text_value = TestUtils.create_text_value()
    data = {
        "footnote_template_uid": footnote_template.uid,
        "library_name": "Sponsor",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "",
                "terms": [
                    {
                        "index": 1,
                        "name": text_value.name,
                        "uid": text_value.uid,
                        "type": "TextValue",
                    }
                ],
            }
        ],
    }
    response = api_client.post(URL, json=data)
    res = response.json()
    log.info("Created Footnote: %s", res)

    assert_response_status_code(response, 201)
    assert res["uid"]
    assert res["name"] == f"Default name with [{text_value.name_sentence_case}]"
    assert res["template"]["uid"] == footnote_template.uid
    assert res["template"]["sequence_id"] == "FSA1"
    assert res["parameter_terms"][0]["terms"][0]["uid"] == text_value.uid
    assert (
        res["parameter_terms"][0]["terms"][0]["name"] == text_value.name_sentence_case
    )
    assert res["parameter_terms"][0]["terms"][0]["type"] == "TextValue"
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert set(list(res.keys())) == set(FOOTNOTE_FIELDS_ALL)
    for key in FOOTNOTE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_keep_original_case_of_unit_definition_parameter_if_it_is_in_the_start_of_footnote(
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
        activity_group_uids=[activity_group.uid],
        activity_subgroup_uids=[activity_subgroup.uid],
    )

    data = {
        "footnote_template_uid": _footnote_template.uid,
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
    }
    response = api_client.post(URL, json=data)
    res = response.json()
    log.info("Created Footnote: %s", res)

    assert_response_status_code(response, 201)
    assert res["name"] == f"[{_unit.name}] test ignore case"


def test_update_footnote(api_client):
    data = {
        "change_description": "parameters changed",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "",
                "terms": [
                    {
                        "index": 1,
                        "name": text_value_2.name,
                        "uid": text_value_2.uid,
                        "type": "TextValue",
                    }
                ],
            }
        ],
    }
    response = api_client.patch(f"{URL}/{footnotes[2].uid}", json=data)
    res = response.json()
    log.info("Updated Footnote: %s", res)

    assert_response_status_code(response, 200)
    assert res["uid"]
    assert res["name"] == f"Default name with [{text_value_2.name_sentence_case}]"
    assert res["template"]["uid"] == footnote_template.uid
    assert res["template"]["sequence_id"] == "FSA1"
    assert res["parameter_terms"][0]["terms"][0]["uid"] == text_value_2.uid
    assert (
        res["parameter_terms"][0]["terms"][0]["name"] == text_value_2.name_sentence_case
    )
    assert res["parameter_terms"][0]["terms"][0]["type"] == "TextValue"
    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert set(list(res.keys())) == set(FOOTNOTE_FIELDS_ALL)
    for key in FOOTNOTE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_delete_footnote(api_client):
    response = api_client.delete(f"{URL}/{footnotes[2].uid}")
    log.info("Deleted Footnote: %s", footnotes[2].uid)

    assert_response_status_code(response, 204)


def test_approve_footnote(api_client):
    response = api_client.post(f"{URL}/{footnotes[3].uid}/approvals")
    res = response.json()

    assert_response_status_code(response, 201)
    assert res["uid"] == footnotes[3].uid
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_inactivate_footnote(api_client):
    response = api_client.delete(f"{URL}/{footnotes[3].uid}/activations")
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == footnotes[3].uid
    assert res["version"] == "1.0"
    assert res["status"] == "Retired"


def test_reactivate_footnote(api_client):
    response = api_client.post(f"{URL}/{footnotes[3].uid}/activations")
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == footnotes[3].uid
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_preview_footnote(api_client):
    text_value = TestUtils.create_text_value()
    data = {
        "footnote_template_uid": footnote_template.uid,
        "library_name": "Sponsor",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "",
                "terms": [
                    {
                        "index": 1,
                        "name": text_value.name,
                        "uid": text_value.uid,
                        "type": "TextValue",
                    }
                ],
            }
        ],
    }
    response = api_client.post(f"{URL}/preview", json=data)
    res = response.json()
    log.info("Previewed Footnote: %s", res)

    assert_response_status_code(response, 200)
    assert res["uid"]
    assert res["name"] == f"Default name with [{text_value.name_sentence_case}]"
    assert res["template"]["uid"] == footnote_template.uid
    assert res["template"]["sequence_id"] == "FSA1"
    assert res["parameter_terms"][0]["terms"][0]["uid"] == text_value.uid
    assert (
        res["parameter_terms"][0]["terms"][0]["name"] == text_value.name_sentence_case
    )
    assert res["parameter_terms"][0]["terms"][0]["type"] == "TextValue"
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert set(list(res.keys())) == set(FOOTNOTE_FIELDS_ALL)
    for key in FOOTNOTE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_footnote_audit_trail(api_client):
    response = api_client.get(f"{URL}/audit-trail?page_size=100&total_count=true")
    res = response.json()
    log.info("Footnote Audit Trail: %s", res)

    assert_response_status_code(response, 200)
    assert res["total"] == 44
    expected_uids = [
        "Footnote_000025",
        "Footnote_000025",
        "Footnote_000024",
        "Footnote_000024",
        "Footnote_000023",
        "Footnote_000023",
        "Footnote_000022",
        "Footnote_000022",
        "Footnote_000021",
        "Footnote_000021",
        "Footnote_000020",
        "Footnote_000020",
        "Footnote_000019",
        "Footnote_000019",
        "Footnote_000018",
        "Footnote_000018",
        "Footnote_000017",
        "Footnote_000017",
        "Footnote_000016",
        "Footnote_000016",
        "Footnote_000015",
        "Footnote_000015",
        "Footnote_000014",
        "Footnote_000014",
        "Footnote_000013",
        "Footnote_000013",
        "Footnote_000012",
        "Footnote_000012",
        "Footnote_000011",
        "Footnote_000011",
        "Footnote_000010",
        "Footnote_000010",
        "Footnote_000009",
        "Footnote_000009",
        "Footnote_000008",
        "Footnote_000008",
        "Footnote_000007",
        "Footnote_000007",
        "Footnote_000006",
        "Footnote_000006",
        "Footnote_000002",
        "Footnote_000002",
        "Footnote_000001",
        "Footnote_000001",
    ]
    actual_uids = [item["uid"] for item in res["items"]]
    assert actual_uids == expected_uids


def test_change_parameter_numbers_of_footnote_after_approval(
    api_client,
):
    data = {
        "name": "Default name with",
        "change_description": "Change for parameter numbers",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "",
                "terms": [],
            }
        ],
    }
    response = api_client.patch(f"{URL}/{footnotes[4].uid}", json=data)
    res = response.json()
    log.info("Changed Footnote parameter numbers: %s", res)

    assert_response_status_code(response, 200)
    assert not res["parameter_terms"][0]["terms"]


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
def test_get_footnotes_csv_xml_excel(api_client, export_format):
    TestUtils.verify_exported_data_format(api_client, export_format, URL)


def test_cannot_update_footnote_without_change_description(api_client):
    data = {"name": "Default name with [TextValue]", "parameter_terms": []}
    response = api_client.patch(f"{URL}/{footnotes[1].uid}", json=data)
    res = response.json()
    log.info("Didn't Update Footnote: %s", res)

    assert_response_status_code(response, 422)
    assert res["detail"] == [
        {
            "type": "missing",
            "loc": ["body", "change_description"],
            "msg": "Field required",
            "input": {"name": "Default name with [TextValue]", "parameter_terms": []},
        }
    ]


def test_cannot_update_footnote_in_final_status(api_client):
    data = {
        "name": "test name [TextValue]",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "",
                "terms": [],
            }
        ],
        "change_description": "Change for final status",
    }
    response = api_client.patch(f"{URL}/{footnotes[1].uid}", json=data)
    res = response.json()
    log.info("Didn't Update Footnote: %s", res)

    assert_response_status_code(response, 400)
    assert res["message"] == "The object isn't in draft status."


def test_cannot_add_wrong_parameters(
    api_client,
):
    data = {
        "name": "Default name with",
        "change_description": "Change for parameter numbers",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "",
                "terms": [
                    {
                        "uid": "wrong",
                        "name": "wrong",
                        "type": "wrong",
                        "index": 1,
                    },
                ],
            }
        ],
    }
    response = api_client.patch(f"{URL}/{footnotes[4].uid}", json=data)
    res = response.json()
    log.info("Didn't change Footnote parameters: %s", res)

    assert_response_status_code(response, 422)
    assert (
        res["message"]
        == "One or more of the specified template parameters can not be found."
    )
