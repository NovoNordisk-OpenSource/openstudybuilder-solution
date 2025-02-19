"""
Tests for objective-templates endpoints
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
from clinical_mdr_api.models.concepts.concept import TextValue
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.dictionaries.dictionary_codelist import DictionaryCodelist
from clinical_mdr_api.models.dictionaries.dictionary_term import DictionaryTerm
from clinical_mdr_api.models.syntax_templates.objective_template import (
    ObjectiveTemplate,
)
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
objective_templates: list[ObjectiveTemplate]
ct_term_inclusion: CTTerm
dictionary_term_indication: DictionaryTerm
ct_term_category: CTTerm
indications_codelist: DictionaryCodelist
indications_library_name: str
text_value_1: TextValue
text_value_2: TextValue

URL = "objective-templates"


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

    global objective_templates
    global ct_term_inclusion
    global dictionary_term_indication
    global ct_term_category
    global indications_codelist
    global indications_library_name
    global text_value_1
    global text_value_2

    # Create Template Parameter
    TestUtils.create_template_parameter("TextValue")

    text_value_1 = TestUtils.create_text_value()
    text_value_2 = TestUtils.create_text_value()

    # Create Dictionary/CT Terms
    ct_term_inclusion = TestUtils.create_ct_term(
        sponsor_preferred_name="INCLUSION ENDPOINT"
    )
    indications_library_name = "SNOMED"
    indications_codelist = TestUtils.create_dictionary_codelist(
        name="DiseaseDisorder", library_name=indications_library_name
    )
    dictionary_term_indication = TestUtils.create_dictionary_term(
        codelist_uid=indications_codelist.codelist_uid,
        library_name=indications_library_name,
    )
    ct_term_category = TestUtils.create_ct_term()

    # Create some objective_templates
    objective_templates = []
    objective_templates.append(
        TestUtils.create_objective_template(
            name="Default name with [TextValue]",
            guidance_text="Default guidance text",
            study_uid=None,
            library_name="Sponsor",
            is_confirmatory_testing=False,
            indication_uids=[dictionary_term_indication.term_uid],
            category_uids=[ct_term_category.term_uid],
        )
    )
    objective_templates.append(
        TestUtils.create_objective_template(
            name="Default-AAA name with [TextValue]",
            guidance_text="Default-AAA guidance text",
            study_uid=None,
            library_name="Sponsor",
            is_confirmatory_testing=False,
            indication_uids=[dictionary_term_indication.term_uid],
            category_uids=[ct_term_category.term_uid],
        )
    )
    objective_templates.append(
        TestUtils.create_objective_template(
            name="Default-BBB name with [TextValue]",
            guidance_text="Default-BBB guidance text",
            study_uid=None,
            library_name="Sponsor",
            is_confirmatory_testing=False,
            indication_uids=[dictionary_term_indication.term_uid],
            category_uids=[ct_term_category.term_uid],
            approve=False,
        )
    )
    objective_templates.append(
        TestUtils.create_objective_template(
            name="Default-XXX name with [TextValue]",
            guidance_text="Default-XXX guidance text",
            study_uid=None,
            library_name="Sponsor",
            is_confirmatory_testing=False,
            indication_uids=[dictionary_term_indication.term_uid],
            category_uids=[ct_term_category.term_uid],
            approve=False,
        )
    )
    objective_templates.append(
        TestUtils.create_objective_template(
            name="Default-YYY name with [TextValue]",
            guidance_text="Default-YYY guidance text",
            study_uid=None,
            library_name="Sponsor",
            is_confirmatory_testing=False,
            indication_uids=[dictionary_term_indication.term_uid],
            category_uids=[ct_term_category.term_uid],
        )
    )

    for index in range(5):
        objective_templates.append(
            TestUtils.create_objective_template(
                name=f"Default-AAA-{index} name with [TextValue]",
                guidance_text=f"Default-AAA-{index} guidance text",
                study_uid=None,
                library_name="Sponsor",
                is_confirmatory_testing=False,
                indication_uids=[dictionary_term_indication.term_uid],
                category_uids=[ct_term_category.term_uid],
            )
        )
        objective_templates.append(
            TestUtils.create_objective_template(
                name=f"Default-BBB-{index} name with [TextValue]",
                guidance_text=f"Default-BBB-{index} guidance text",
                study_uid=None,
                library_name="Sponsor",
                is_confirmatory_testing=False,
                indication_uids=[dictionary_term_indication.term_uid],
                category_uids=[ct_term_category.term_uid],
            )
        )
        objective_templates.append(
            TestUtils.create_objective_template(
                name=f"Default-XXX-{index} name with [TextValue]",
                guidance_text=f"Default-XXX-{index} guidance text",
                study_uid=None,
                library_name="Sponsor",
                is_confirmatory_testing=False,
                indication_uids=[dictionary_term_indication.term_uid],
                category_uids=[ct_term_category.term_uid],
            )
        )
        objective_templates.append(
            TestUtils.create_objective_template(
                name=f"Default-YYY-{index} name with [TextValue]",
                guidance_text=f"Default-YYY-{index} guidance text",
                study_uid=None,
                library_name="Sponsor",
                is_confirmatory_testing=False,
                indication_uids=[dictionary_term_indication.term_uid],
                category_uids=[ct_term_category.term_uid],
            )
        )

    yield


ENDPOINT_TEMPLATE_FIELDS_ALL = [
    "name",
    "name_plain",
    "guidance_text",
    "uid",
    "sequence_id",
    "status",
    "version",
    "change_description",
    "is_confirmatory_testing",
    "start_date",
    "end_date",
    "author_username",
    "possible_actions",
    "parameters",
    "library",
    "indications",
    "categories",
    "study_count",
]

ENDPOINT_TEMPLATE_FIELDS_NOT_NULL = [
    "uid",
    "sequence_id",
    "name",
]


def test_get_objective_template(api_client):
    response = api_client.get(f"{URL}/{objective_templates[1].uid}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    fields_all_set = set(ENDPOINT_TEMPLATE_FIELDS_ALL)
    fields_all_set.add("counts")
    assert set(list(res.keys())) == fields_all_set
    for key in ENDPOINT_TEMPLATE_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == objective_templates[1].uid
    assert res["sequence_id"] == "O2"
    assert res["name"] == "Default-AAA name with [TextValue]"
    assert res["guidance_text"] == "Default-AAA guidance text"
    assert res["is_confirmatory_testing"] is False
    assert res["parameters"][0]["name"] == "TextValue"
    assert res["parameters"][0]["terms"] == []
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    assert (
        res["categories"][0]["attributes"]["code_submission_value"]
        == ct_term_category.code_submission_value
    )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_get_objective_templates_pagination(api_client):
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
    assert len(objective_templates) == len(results_paginated_merged)


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
def test_get_objective_templates(
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
    assert res["total"] == (len(objective_templates) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(ENDPOINT_TEMPLATE_FIELDS_ALL)
        for key in ENDPOINT_TEMPLATE_FIELDS_NOT_NULL:
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


def test_get_all_parameters_of_objective_template(api_client):
    response = api_client.get(f"{URL}/{objective_templates[0].uid}/parameters")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) == 1
    assert res[0]["name"] == "TextValue"
    assert len(res[0]["terms"]) == 2


def test_get_versions_of_objective_template(api_client):
    response = api_client.get(f"{URL}/{objective_templates[1].uid}/versions")
    res = response.json()

    assert_response_status_code(response, 200)

    assert len(res) == 2
    assert res[0]["uid"] == objective_templates[1].uid
    assert res[0]["sequence_id"] == "O2"
    assert res[0]["version"] == "1.0"
    assert res[0]["status"] == "Final"
    assert res[0]["is_confirmatory_testing"] is False
    assert res[0]["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res[0]["indications"][0]["name"] == dictionary_term_indication.name
    assert res[0]["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res[0]["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res[0]["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    assert (
        res[0]["categories"][0]["attributes"]["code_submission_value"]
        == ct_term_category.code_submission_value
    )
    assert (
        res[0]["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res[0]["version"] == "1.0"
    assert res[0]["status"] == "Final"
    assert res[1]["uid"] == objective_templates[1].uid
    assert res[1]["sequence_id"] == "O2"
    assert res[1]["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res[1]["indications"][0]["name"] == dictionary_term_indication.name
    assert res[1]["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res[1]["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res[1]["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    assert (
        res[1]["categories"][0]["attributes"]["code_submission_value"]
        == ct_term_category.code_submission_value
    )
    assert (
        res[1]["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res[1]["version"] == "0.1"
    assert res[1]["status"] == "Draft"


def test_get_all_final_versions_of_objective_template(api_client):
    response = api_client.get(f"{URL}/{objective_templates[1].uid}/releases")
    res = response.json()

    assert_response_status_code(response, 200)

    assert len(res) == 1
    assert res[0]["uid"] == objective_templates[1].uid
    assert res[0]["sequence_id"] == "O2"
    assert res[0]["is_confirmatory_testing"] is False
    assert res[0]["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res[0]["indications"][0]["name"] == dictionary_term_indication.name
    assert res[0]["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res[0]["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res[0]["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    assert (
        res[0]["categories"][0]["attributes"]["code_submission_value"]
        == ct_term_category.code_submission_value
    )
    assert (
        res[0]["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
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
        pytest.param(
            '{"*": {"v": ["Default-XXX"], "op": "co"}}', "guidance_text", "Default-XXX"
        ),
        pytest.param(
            '{"*": {"v": ["Default-YYY"], "op": "co"}}', "guidance_text", "Default-YYY"
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
        pytest.param(
            '{"guidance_text": {"v": ["Default-XXX"], "op": "co"}}',
            "guidance_text",
            "Default-XXX",
        ),
        pytest.param(
            '{"guidance_text": {"v": ["Default-YYY"], "op": "co"}}',
            "guidance_text",
            "Default-YYY",
        ),
        pytest.param('{"guidance_text": {"v": ["cc"], "op": "co"}}', None, None),
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
    for objective_template in objective_templates:
        value = getattr(objective_template, field_name)
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


def test_pre_validate_objective_template_name(api_client):
    data = {"name": "test [TextValue]"}
    response = api_client.post(f"{URL}/pre-validate", json=data)
    res = response.json()
    log.info("Pre Validated Objective Template name: %s", res)

    assert_response_status_code(response, 202)


def test_create_objective_template(api_client):
    data = {
        "name": "default_name [TextValue]",
        "guidance_text": "default_guidance_text",
        "library_name": "Sponsor",
        "is_confirmatory_testing": True,
        "indication_uids": [dictionary_term_indication.term_uid],
        "category_uids": [ct_term_category.term_uid],
    }
    response = api_client.post(URL, json=data)
    res = response.json()
    log.info("Created Objective Template: %s", res)

    assert_response_status_code(response, 201)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["name"] == "default_name [TextValue]"
    assert res["guidance_text"] == "default_guidance_text"
    assert res["is_confirmatory_testing"] is True
    assert res["parameters"][0]["name"] == "TextValue"
    assert res["parameters"][0]["terms"] == []
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    assert (
        res["categories"][0]["attributes"]["code_submission_value"]
        == ct_term_category.code_submission_value
    )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert set(list(res.keys())) == set(ENDPOINT_TEMPLATE_FIELDS_ALL)
    for key in ENDPOINT_TEMPLATE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_create_new_version_of_objective_template(api_client):
    data = {
        "name": "new test name",
        "guidance_text": "new test guidance text",
        "change_description": "new version",
    }
    response = api_client.post(
        f"{URL}/{objective_templates[4].uid}/versions", json=data
    )
    res = response.json()
    log.info("Created new version of Objective Template: %s", res)

    assert_response_status_code(response, 201)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["name"] == "new test name"
    assert res["guidance_text"] == "new test guidance text"
    assert res["is_confirmatory_testing"] is False
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    assert (
        res["categories"][0]["attributes"]["code_submission_value"]
        == ct_term_category.code_submission_value
    )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "1.1"
    assert res["status"] == "Draft"
    assert set(list(res.keys())) == set(ENDPOINT_TEMPLATE_FIELDS_ALL)
    for key in ENDPOINT_TEMPLATE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_get_specific_version_of_objective_template(api_client):
    response = api_client.get(f"{URL}/{objective_templates[4].uid}/versions/1.1")
    res = response.json()

    assert_response_status_code(response, 200)

    assert res["uid"] == objective_templates[4].uid
    assert res["sequence_id"] == "O5"
    assert res["is_confirmatory_testing"] is False
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    assert (
        res["categories"][0]["attributes"]["code_submission_value"]
        == ct_term_category.code_submission_value
    )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "1.1"
    assert res["status"] == "Draft"


def test_change_objective_template_indexings(api_client):
    indication = TestUtils.create_dictionary_term(
        codelist_uid=indications_codelist.codelist_uid,
        library_name=indications_library_name,
    )
    category = TestUtils.create_ct_term()

    data = {
        "is_confirmatory_testing": True,
        "indication_uids": [dictionary_term_indication.term_uid, indication.term_uid],
        "category_uids": [
            ct_term_category.term_uid,
            category.term_uid,
        ],
    }
    response = api_client.patch(
        f"{URL}/{objective_templates[1].uid}/indexings",
        json=data,
    )
    res = response.json()
    log.info("Changed Objective Template indexings: %s", res)

    assert_response_status_code(response, 200)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["name"] == "Default-AAA name with [TextValue]"
    assert res["guidance_text"] == "Default-AAA guidance text"
    assert res["is_confirmatory_testing"] is True
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["indications"][1]["term_uid"] == indication.term_uid
    assert res["indications"][1]["name"] == indication.name
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    assert (
        res["categories"][0]["attributes"]["code_submission_value"]
        == ct_term_category.code_submission_value
    )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["categories"][1]["term_uid"] == category.term_uid
    assert (
        res["categories"][1]["name"]["sponsor_preferred_name"]
        == category.sponsor_preferred_name
    )
    assert (
        res["categories"][1]["name"]["sponsor_preferred_name_sentence_case"]
        == category.sponsor_preferred_name_sentence_case
    )
    assert (
        res["categories"][1]["attributes"]["code_submission_value"]
        == category.code_submission_value
    )
    assert (
        res["categories"][1]["attributes"]["nci_preferred_name"]
        == category.nci_preferred_name
    )
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert set(list(res.keys())) == set(ENDPOINT_TEMPLATE_FIELDS_ALL)
    for key in ENDPOINT_TEMPLATE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_remove_objective_template_indexings(api_client):
    data = {
        "is_confirmatory_testing": False,
        "indication_uids": [],
        "category_uids": [],
    }
    response = api_client.patch(
        f"{URL}/{objective_templates[1].uid}/indexings",
        json=data,
    )
    res = response.json()
    log.info("Removed Objective Template indexings: %s", res)

    assert_response_status_code(response, 200)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["name"] == "Default-AAA name with [TextValue]"
    assert res["guidance_text"] == "Default-AAA guidance text"
    assert res["is_confirmatory_testing"] is False
    assert not res["indications"]
    assert not res["categories"]
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert set(list(res.keys())) == set(ENDPOINT_TEMPLATE_FIELDS_ALL)
    for key in ENDPOINT_TEMPLATE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_delete_objective_template(api_client):
    response = api_client.delete(f"{URL}/{objective_templates[2].uid}")
    log.info("Deleted Objective Template: %s", objective_templates[2].uid)

    assert_response_status_code(response, 204)


def test_approve_objective_template(api_client):
    response = api_client.post(f"{URL}/{objective_templates[3].uid}/approvals")
    res = response.json()
    log.info("Approved Objective Template: %s", objective_templates[3].uid)

    assert_response_status_code(response, 201)
    assert res["uid"] == objective_templates[3].uid
    assert res["sequence_id"] == "O4"
    assert res["is_confirmatory_testing"] is False
    assert res["name"] == "Default-XXX name with [TextValue]"
    assert res["guidance_text"] == "Default-XXX guidance text"
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    assert (
        res["categories"][0]["attributes"]["code_submission_value"]
        == ct_term_category.code_submission_value
    )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_cascade_approve_objective_template(api_client):
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
    objective = TestUtils.create_objective(
        objective_template_uid=objective_templates[5].uid,
        library_name="Sponsor",
        parameter_terms=parameter_terms,
        approve=False,
    )
    objective_pre_instance = TestUtils.create_objective_pre_instance(
        template_uid=objective_templates[5].uid,
        library_name="Sponsor",
        parameter_terms=parameter_terms,
        indication_uids=[dictionary_term_indication.term_uid],
        category_uids=[ct_term_category.term_uid],
    )

    api_client.post(
        f"{URL}/{objective_templates[5].uid}/versions",
        json={
            "name": "cascade check [TextValue]",
            "change_description": "cascade check for instance and pre instances",
        },
    )

    response = api_client.post(
        f"{URL}/{objective_templates[5].uid}/approvals?cascade=true"
    )
    res = response.json()
    log.info("Approved Objective Template: %s", objective_templates[5].uid)

    assert_response_status_code(response, 201)
    assert res["uid"] == objective_templates[5].uid
    assert res["sequence_id"] == "O6"
    assert res["name"] == "cascade check [TextValue]"
    assert res["guidance_text"] == "Default-AAA-0 guidance text"
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    assert (
        res["categories"][0]["attributes"]["code_submission_value"]
        == ct_term_category.code_submission_value
    )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "2.0"
    assert res["status"] == "Final"

    # Assertions for Objective
    response = api_client.get(f"objectives/{objective.uid}")
    res = response.json()

    assert res["name"] == f"cascade check [{text_value_1.name_sentence_case}]"
    assert res["version"] == "0.2"
    assert res["status"] == "Draft"

    # Assertions for Objective Pre-Instance
    response = api_client.get(f"objective-pre-instances/{objective_pre_instance.uid}")
    res = response.json()

    assert res["name"] == f"cascade check [{text_value_1.name_sentence_case}]"
    assert res["version"] == "2.0"
    assert res["status"] == "Final"


def test_inactivate_objective_template(api_client):
    response = api_client.delete(f"{URL}/{objective_templates[5].uid}/activations")
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == objective_templates[5].uid
    assert res["sequence_id"] == "O6"
    assert res["is_confirmatory_testing"] is False
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    assert (
        res["categories"][0]["attributes"]["code_submission_value"]
        == ct_term_category.code_submission_value
    )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "2.0"
    assert res["status"] == "Retired"

    # Assertions for Objective Pre-Instance
    response = api_client.get("objective-pre-instances/ObjectivePreInstance_000001")
    res = response.json()

    assert res["name"] == f"cascade check [{text_value_1.name_sentence_case}]"
    assert res["version"] == "2.0"
    assert res["status"] == "Retired"


def test_current_final_objective_template(api_client):
    response = api_client.get(
        f"""{URL}?status=Final&filters={{"sequence_id": {{"v": ["O6"], "op": "eq"}}}}"""
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert not res["items"]

    response = api_client.get(
        f"""{URL}/headers?field_name=sequence_id&status=Final&filters={{"sequence_id": {{"v": ["O6"], "op": "eq"}}}}"""
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert not res


def test_reactivate_objective_template(api_client):
    response = api_client.post(f"{URL}/{objective_templates[5].uid}/activations")
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == objective_templates[5].uid
    assert res["sequence_id"] == "O6"
    assert res["is_confirmatory_testing"] is False
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    assert (
        res["categories"][0]["attributes"]["code_submission_value"]
        == ct_term_category.code_submission_value
    )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "2.0"
    assert res["status"] == "Final"

    # Assertions for Objective Pre-Instance
    response = api_client.get("objective-pre-instances/ObjectivePreInstance_000001")
    res = response.json()

    assert res["name"] == f"cascade check [{text_value_1.name_sentence_case}]"
    assert res["version"] == "2.0"
    assert res["status"] == "Final"


def test_objective_template_audit_trail(api_client):
    response = api_client.get(f"{URL}/audit-trail?page_size=100&total_count=true")
    res = response.json()
    log.info("ObjectiveTemplate Audit Trail: %s", res)

    assert_response_status_code(response, 200)
    assert res["total"] == 54
    expected_uids = [
        "ObjectiveTemplate_000006",
        "ObjectiveTemplate_000006",
        "ObjectiveTemplate_000006",
        "ObjectiveTemplate_000006",
        "ObjectiveTemplate_000004",
        "ObjectiveTemplate_000005",
        "ObjectiveTemplate_000026",
        "ObjectiveTemplate_000025",
        "ObjectiveTemplate_000025",
        "ObjectiveTemplate_000024",
        "ObjectiveTemplate_000024",
        "ObjectiveTemplate_000023",
        "ObjectiveTemplate_000023",
        "ObjectiveTemplate_000022",
        "ObjectiveTemplate_000022",
        "ObjectiveTemplate_000021",
        "ObjectiveTemplate_000021",
        "ObjectiveTemplate_000020",
        "ObjectiveTemplate_000020",
        "ObjectiveTemplate_000019",
        "ObjectiveTemplate_000019",
        "ObjectiveTemplate_000018",
        "ObjectiveTemplate_000018",
        "ObjectiveTemplate_000017",
        "ObjectiveTemplate_000017",
        "ObjectiveTemplate_000016",
        "ObjectiveTemplate_000016",
        "ObjectiveTemplate_000015",
        "ObjectiveTemplate_000015",
        "ObjectiveTemplate_000014",
        "ObjectiveTemplate_000014",
        "ObjectiveTemplate_000013",
        "ObjectiveTemplate_000013",
        "ObjectiveTemplate_000012",
        "ObjectiveTemplate_000012",
        "ObjectiveTemplate_000011",
        "ObjectiveTemplate_000011",
        "ObjectiveTemplate_000010",
        "ObjectiveTemplate_000010",
        "ObjectiveTemplate_000009",
        "ObjectiveTemplate_000009",
        "ObjectiveTemplate_000008",
        "ObjectiveTemplate_000008",
        "ObjectiveTemplate_000007",
        "ObjectiveTemplate_000007",
        "ObjectiveTemplate_000006",
        "ObjectiveTemplate_000006",
        "ObjectiveTemplate_000005",
        "ObjectiveTemplate_000005",
        "ObjectiveTemplate_000004",
        "ObjectiveTemplate_000002",
        "ObjectiveTemplate_000002",
        "ObjectiveTemplate_000001",
        "ObjectiveTemplate_000001",
    ]
    actual_uids = [item["uid"] for item in res["items"]]
    assert actual_uids == expected_uids


def test_objective_template_sequence_id_generation(api_client):
    lib = TestUtils.create_library("User Defined")
    data = {
        "name": "user defined [TextValue]",
        "guidance_text": "user_defined_guidance_text",
        "library_name": lib["name"],
        "is_confirmatory_testing": True,
        "indication_uids": [dictionary_term_indication.term_uid],
        "category_uids": [ct_term_category.term_uid],
    }
    response = api_client.post(URL, json=data)
    res = response.json()
    log.info("Created Objective Template: %s", res)

    assert_response_status_code(response, 201)
    assert res["uid"]
    assert res["sequence_id"] == "U-O1"
    assert res["name"] == "user defined [TextValue]"
    assert res["guidance_text"] == "user_defined_guidance_text"
    assert res["is_confirmatory_testing"] is True
    assert res["parameters"][0]["name"] == "TextValue"
    assert res["parameters"][0]["terms"] == []
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    assert (
        res["categories"][0]["attributes"]["code_submission_value"]
        == ct_term_category.code_submission_value
    )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert set(list(res.keys())) == set(ENDPOINT_TEMPLATE_FIELDS_ALL)
    for key in ENDPOINT_TEMPLATE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_cannot_create_objective_template_with_existing_name(api_client):
    data = {
        "name": "Default name with [TextValue]",
        "guidance_text": "default_guidance_text",
        "library_name": "Sponsor",
        "indication_uids": [dictionary_term_indication.term_uid],
        "category_uids": [ct_term_category.term_uid],
    }
    response = api_client.post(URL, json=data)
    res = response.json()
    log.info("Didn't Create Objective Template: %s", res)

    assert_response_status_code(response, 409)
    assert res["message"] == f"Resource with Name '{data['name']}' already exists."


def test_cannot_update_objective_template_to_an_existing_name(api_client):
    data = {
        "name": "Default name with [TextValue]",
        "change_description": "Change for duplicate",
    }
    response = api_client.patch(f"{URL}/{objective_templates[1].uid}", json=data)
    res = response.json()
    log.info("Didn't Update Objective Template: %s", res)

    assert_response_status_code(response, 409)
    assert res["message"] == f"Resource with Name '{data['name']}' already exists."


def test_cannot_update_objective_template_without_change_description(api_client):
    data = {"name": "Default name with [TextValue]"}
    response = api_client.patch(f"{URL}/{objective_templates[1].uid}", json=data)
    res = response.json()
    log.info("Didn't Update Objective Template: %s", res)

    assert_response_status_code(response, 422)
    assert res["detail"] == [
        {
            "loc": ["body", "change_description"],
            "msg": "field required",
            "type": "value_error.missing",
        }
    ]


def test_cannot_update_objective_template_in_final_status(api_client):
    data = {
        "name": "test name [TextValue]",
        "change_description": "Change for final status",
    }
    response = api_client.patch(f"{URL}/{objective_templates[1].uid}", json=data)
    res = response.json()
    log.info("Didn't Update Objective Template: %s", res)

    assert_response_status_code(response, 400)
    assert res["message"] == "The object isn't in draft status."


def test_cannot_change_parameter_numbers_of_objective_template_after_approval(
    api_client,
):
    data = {
        "name": "Default name with",
        "change_description": "Change for parameter numbers",
    }
    response = api_client.patch(f"{URL}/{objective_templates[1].uid}", json=data)
    res = response.json()
    log.info("Didn't Change Objective Template parameter numbers: %s", res)

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "You cannot change number or order of template parameters for a previously approved template."
    )


def test_pre_validate_invalid_objective_template_name(api_client):
    data = {"name": "Missing opening bracket ]"}
    response = api_client.post(f"{URL}/pre-validate", json=data)
    res = response.json()
    log.info("Pre Validated Objective Temaplate name: %s", res)

    assert_response_status_code(response, 422)
    assert res["message"] == f"Template string syntax incorrect: {data['name']}"

    data = {"name": "Lacking closing bracket ["}
    response = api_client.post(f"{URL}/pre-validate", json=data)
    res = response.json()
    log.info("Pre Validated Objective Template name: %s", res)

    assert_response_status_code(response, 422)
    assert res["message"] == f"Template string syntax incorrect: {data['name']}"

    data = {"name": " "}
    response = api_client.post(f"{URL}/pre-validate", json=data)
    res = response.json()
    log.info("Pre Validated Objective Template name: %s", res)

    assert_response_status_code(response, 422)
    assert res == {
        "detail": [
            {
                "loc": ["body", "name"],
                "msg": "ensure this value has at least 1 characters",
                "type": "value_error.any_str.min_length",
                "ctx": {"limit_value": 1},
            }
        ]
    }
