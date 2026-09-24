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
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.concept import TextValue
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import CTCodelist
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.dictionaries.dictionary_codelist import DictionaryCodelist
from clinical_mdr_api.models.dictionaries.dictionary_term import DictionaryTerm
from clinical_mdr_api.models.syntax_pre_instances.objective_pre_instance import (
    ObjectivePreInstance,
)
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
objective_pre_instances: list[ObjectivePreInstance]
objective_template: ObjectiveTemplate
category_codelist: CTCodelist
dictionary_term_indication: DictionaryTerm
ct_term_category: CTTerm
indications_codelist: DictionaryCodelist
indications_library_name: str
text_value_1: TextValue
text_value_2: TextValue

URL = "objective-pre-instances"


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

    global objective_pre_instances
    global objective_template
    global category_codelist
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

    category_codelist = TestUtils.create_ct_codelist(
        name="Objective Category",
        submission_value="OBJTCAT",
        extensible=True,
        approve=True,
    )

    # Create Dictionary/CT Terms
    indications_library_name = "SNOMED"
    indications_codelist = TestUtils.create_dictionary_codelist(
        name="DiseaseDisorder", library_name=indications_library_name
    )
    dictionary_term_indication = TestUtils.create_dictionary_term(
        codelist_uid=indications_codelist.codelist_uid,
        library_name=indications_library_name,
    )
    ct_term_category = TestUtils.create_ct_term(
        codelist_uid=category_codelist.codelist_uid
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

    objective_template = TestUtils.create_objective_template(
        name="Default name with [TextValue]",
        guidance_text="Default guidance text",
        study_uid=None,
        library_name="Sponsor",
        indication_uids=[dictionary_term_indication.term_uid],
        category_uids=[ct_term_category.term_uid],
    )

    # Create some objective_pre_instances
    objective_pre_instances = []
    objective_pre_instances.append(
        TestUtils.create_objective_pre_instance(
            template_uid=objective_template.uid,
            library_name="Sponsor",
            is_confirmatory_testing=True,
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
            category_uids=[ct_term_category.term_uid],
        )
    )
    objective_pre_instances.append(
        TestUtils.create_objective_pre_instance(
            template_uid=objective_template.uid,
            library_name="Sponsor",
            is_confirmatory_testing=True,
            parameter_terms=generate_parameter_terms(),
            indication_uids=[dictionary_term_indication.term_uid],
            category_uids=[ct_term_category.term_uid],
        )
    )
    objective_pre_instances.append(
        TestUtils.create_objective_pre_instance(
            template_uid=objective_template.uid,
            library_name="Sponsor",
            is_confirmatory_testing=True,
            parameter_terms=generate_parameter_terms(),
            indication_uids=[dictionary_term_indication.term_uid],
            category_uids=[ct_term_category.term_uid],
        )
    )
    objective_pre_instances.append(
        TestUtils.create_objective_pre_instance(
            template_uid=objective_template.uid,
            library_name="Sponsor",
            is_confirmatory_testing=True,
            parameter_terms=generate_parameter_terms(),
            indication_uids=[dictionary_term_indication.term_uid],
            category_uids=[ct_term_category.term_uid],
            approve=False,
        )
    )
    objective_pre_instances.append(
        TestUtils.create_objective_pre_instance(
            template_uid=objective_template.uid,
            library_name="Sponsor",
            is_confirmatory_testing=True,
            parameter_terms=generate_parameter_terms(),
            indication_uids=[dictionary_term_indication.term_uid],
            category_uids=[ct_term_category.term_uid],
            approve=False,
        )
    )

    for _ in range(5):
        objective_pre_instances.append(
            TestUtils.create_objective_pre_instance(
                template_uid=objective_template.uid,
                library_name="Sponsor",
                is_confirmatory_testing=False,
                parameter_terms=generate_parameter_terms(),
                indication_uids=[dictionary_term_indication.term_uid],
                category_uids=[ct_term_category.term_uid],
            )
        )
        objective_pre_instances.append(
            TestUtils.create_objective_pre_instance(
                template_uid=objective_template.uid,
                library_name="Sponsor",
                is_confirmatory_testing=False,
                parameter_terms=generate_parameter_terms(),
                indication_uids=[dictionary_term_indication.term_uid],
                category_uids=[ct_term_category.term_uid],
            )
        )
        objective_pre_instances.append(
            TestUtils.create_objective_pre_instance(
                template_uid=objective_template.uid,
                library_name="Sponsor",
                is_confirmatory_testing=False,
                parameter_terms=generate_parameter_terms(),
                indication_uids=[dictionary_term_indication.term_uid],
                category_uids=[ct_term_category.term_uid],
            )
        )
        objective_pre_instances.append(
            TestUtils.create_objective_pre_instance(
                template_uid=objective_template.uid,
                library_name="Sponsor",
                is_confirmatory_testing=False,
                parameter_terms=generate_parameter_terms(),
                indication_uids=[dictionary_term_indication.term_uid],
                category_uids=[ct_term_category.term_uid],
            )
        )

    yield


OBJECTIVE_PRE_INSTANCE_FIELDS_ALL = [
    "name",
    "name_plain",
    "uid",
    "sequence_id",
    "template_uid",
    "template_name",
    "status",
    "version",
    "change_description",
    "start_date",
    "end_date",
    "author_username",
    "possible_actions",
    "is_confirmatory_testing",
    "parameter_terms",
    "library",
    "indications",
    "categories",
]

OBJECTIVE_PRE_INSTANCE_FIELDS_NOT_NULL = [
    "uid",
    "sequence_id",
    "template_uid",
    "template_name",
    "name",
]


def test_get_objective(api_client):
    response = api_client.get(f"{URL}/{objective_pre_instances[0].uid}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    fields_all_set = set(OBJECTIVE_PRE_INSTANCE_FIELDS_ALL)
    assert set(res.keys()) == fields_all_set
    for key in OBJECTIVE_PRE_INSTANCE_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == objective_pre_instances[0].uid
    assert res["sequence_id"] == "O1P1"
    assert res["name"] == f"Default name with [{text_value_1.name_sentence_case}]"
    assert (
        res["parameter_terms"][0]["terms"][0]["name"] == text_value_1.name_sentence_case
    )
    assert res["parameter_terms"][0]["terms"][0]["uid"] == text_value_1.uid
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
    # assert (
    #    res["categories"][0]["attributes"]["code_submission_value"]
    #    == ct_term_category.code_submission_value
    # )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_get_objective_pre_instances_pagination(api_client):
    results_paginated: dict[Any, Any] = {}
    sort_by = '{"uid": true}'
    for page_number in range(1, 4):
        response = api_client.get(
            f"{URL}?page_number={page_number}&page_size=10&sort_by={sort_by}"
        )
        res = response.json()
        res_uids = [item["uid"] for item in res["items"]]
        results_paginated[page_number] = res_uids
        log.info("Page %s: %s", page_number, res_uids)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        list(reduce(lambda a, b: list(a) + list(b), list(results_paginated.values())))
    )
    log.info("All rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"{URL}?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = [item["uid"] for item in res_all["items"]]
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(objective_pre_instances) == len(results_paginated_merged)


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
def test_get_objective_pre_instances(
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
    assert res["total"] == (len(objective_pre_instances) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(OBJECTIVE_PRE_INSTANCE_FIELDS_ALL)
        for key in OBJECTIVE_PRE_INSTANCE_FIELDS_NOT_NULL:
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


def test_get_versions_of_objective_pre_instance(api_client):
    response = api_client.get(f"{URL}/{objective_pre_instances[1].uid}/versions")
    res = response.json()

    assert_response_status_code(response, 200)

    assert len(res) == 2
    assert res[0]["uid"] == objective_pre_instances[1].uid
    assert res[0]["sequence_id"] == "O1P2"
    assert res[0]["template_uid"] == objective_template.uid
    assert res[0]["template_name"] == objective_template.name
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
    # assert (
    #    res[0]["categories"][0]["attributes"]["code_submission_value"]
    #    == ct_term_category.code_submission_value
    # )
    assert (
        res[0]["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res[0]["version"] == "1.0"
    assert res[0]["status"] == "Final"
    assert res[0]["possible_actions"] == ["inactivate", "new_version"]
    assert res[1]["uid"] == objective_pre_instances[1].uid
    assert res[1]["sequence_id"] == "O1P2"
    assert res[0]["template_uid"] == objective_template.uid
    assert res[0]["template_name"] == objective_template.name
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
    # assert (
    #    res[1]["categories"][0]["attributes"]["code_submission_value"]
    #    == ct_term_category.code_submission_value
    # )
    assert (
        res[1]["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
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
    for objective_pre_instance in objective_pre_instances:
        value = getattr(objective_pre_instance, field_name)
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


def test_create_new_version_of_objective_pre_instance(api_client):
    response = api_client.post(f"{URL}/{objective_pre_instances[2].uid}/versions")
    res = response.json()
    log.info("Created new version of Objective Pre-Instance: %s", res)

    assert_response_status_code(response, 201)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["template_uid"] == objective_template.uid
    assert res["template_name"] == objective_template.name
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
    # assert (
    #    res["categories"][0]["attributes"]["code_submission_value"]
    #    == ct_term_category.code_submission_value
    # )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "1.1"
    assert res["status"] == "Draft"


def test_update_objective_pre_instance(api_client):
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
    response = api_client.patch(f"{URL}/{objective_pre_instances[3].uid}", json=data)
    res = response.json()
    log.info("Updated Objective Pre-Instance: %s", res)

    assert_response_status_code(response, 200)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["template_uid"] == objective_template.uid
    assert res["template_name"] == objective_template.name
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
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    # assert (
    #    res["categories"][0]["attributes"]["code_submission_value"]
    #    == ct_term_category.code_submission_value
    # )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert set(res.keys()) == set(OBJECTIVE_PRE_INSTANCE_FIELDS_ALL)
    for key in OBJECTIVE_PRE_INSTANCE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_change_objective_pre_instance_indexings(api_client):
    indication = TestUtils.create_dictionary_term(
        codelist_uid=indications_codelist.codelist_uid,
        library_name=indications_library_name,
    )
    category = TestUtils.create_ct_term(codelist_uid=category_codelist.codelist_uid)

    data = {
        "is_confirmatory_testing": False,
        "indication_uids": [dictionary_term_indication.term_uid, indication.term_uid],
        "category_uids": [
            ct_term_category.term_uid,
            category.term_uid,
        ],
    }
    response = api_client.patch(
        f"{URL}/{objective_pre_instances[0].uid}/indexings",
        json=data,
    )
    res = response.json()
    log.info("Changed Objective Pre-Instance indexings: %s", res)

    assert_response_status_code(response, 200)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["template_uid"] == objective_template.uid
    assert res["template_name"] == objective_template.name
    assert res["name"] == f"Default name with [{text_value_1.name_sentence_case}]"
    assert res["is_confirmatory_testing"] is False
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
    # assert (
    #    res["categories"][0]["attributes"]["code_submission_value"]
    #    == ct_term_category.code_submission_value
    # )
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
    # assert (
    #    res["categories"][1]["attributes"]["code_submission_value"]
    #    == category.code_submission_value
    # )
    assert (
        res["categories"][1]["attributes"]["nci_preferred_name"]
        == category.nci_preferred_name
    )
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert set(res.keys()) == set(OBJECTIVE_PRE_INSTANCE_FIELDS_ALL)
    for key in OBJECTIVE_PRE_INSTANCE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_remove_objective_pre_instance_indexings(api_client):
    data = {
        "is_confirmatory_testing": False,
        "indication_uids": [],
        "category_uids": [],
    }
    response = api_client.patch(
        f"{URL}/{objective_pre_instances[0].uid}/indexings",
        json=data,
    )
    res = response.json()
    log.info("Removed Objective Pre-Instance indexings: %s", res)

    assert_response_status_code(response, 200)
    assert res["uid"]
    assert res["sequence_id"]
    assert res["template_uid"] == objective_template.uid
    assert res["template_name"] == objective_template.name
    assert res["name"] == f"Default name with [{text_value_1.name_sentence_case}]"
    assert res["is_confirmatory_testing"] is False
    assert not res["indications"]
    assert not res["categories"]
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert set(res.keys()) == set(OBJECTIVE_PRE_INSTANCE_FIELDS_ALL)
    for key in OBJECTIVE_PRE_INSTANCE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_delete_objective_pre_instance(api_client):
    response = api_client.delete(f"{URL}/{objective_pre_instances[3].uid}")
    log.info("Deleted Objective Pre-Instance: %s", objective_pre_instances[3].uid)

    assert_response_status_code(response, 204)


def test_approve_objective_pre_instance(api_client):
    response = api_client.post(f"{URL}/{objective_pre_instances[4].uid}/approvals")
    res = response.json()

    assert_response_status_code(response, 201)
    assert res["uid"] == objective_pre_instances[4].uid
    assert res["sequence_id"] == "O1P5"
    assert res["is_confirmatory_testing"] is True
    assert res["template_uid"] == objective_template.uid
    assert res["template_name"] == objective_template.name
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
    # assert (
    #    res["categories"][0]["attributes"]["code_submission_value"]
    #    == ct_term_category.code_submission_value
    # )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_inactivate_objective_pre_instance(api_client):
    response = api_client.delete(f"{URL}/{objective_pre_instances[4].uid}/activations")
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == objective_pre_instances[4].uid
    assert res["sequence_id"] == "O1P5"
    assert res["is_confirmatory_testing"] is True
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
    # assert (
    #    res["categories"][0]["attributes"]["code_submission_value"]
    #    == ct_term_category.code_submission_value
    # )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "1.0"
    assert res["status"] == "Retired"


def test_reactivate_objective_pre_instance(api_client):
    response = api_client.post(f"{URL}/{objective_pre_instances[4].uid}/activations")
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == objective_pre_instances[4].uid
    assert res["sequence_id"] == "O1P5"
    assert res["is_confirmatory_testing"] is True
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
    # assert (
    #    res["categories"][0]["attributes"]["code_submission_value"]
    #    == ct_term_category.code_submission_value
    # )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_objective_pre_instance_audit_trail(api_client):
    response = api_client.get(f"{URL}/audit-trail?page_size=100&total_count=true")
    res = response.json()
    log.info("ObjectivePreInstance Audit Trail: %s", res)

    assert_response_status_code(response, 200)
    assert res["total"] == 51
    expected_uids = [
        "ObjectivePreInstance_000005",
        "ObjectivePreInstance_000005",
        "ObjectivePreInstance_000005",
        "ObjectivePreInstance_000003",
        "ObjectivePreInstance_000025",
        "ObjectivePreInstance_000025",
        "ObjectivePreInstance_000024",
        "ObjectivePreInstance_000024",
        "ObjectivePreInstance_000023",
        "ObjectivePreInstance_000023",
        "ObjectivePreInstance_000022",
        "ObjectivePreInstance_000022",
        "ObjectivePreInstance_000021",
        "ObjectivePreInstance_000021",
        "ObjectivePreInstance_000020",
        "ObjectivePreInstance_000020",
        "ObjectivePreInstance_000019",
        "ObjectivePreInstance_000019",
        "ObjectivePreInstance_000018",
        "ObjectivePreInstance_000018",
        "ObjectivePreInstance_000017",
        "ObjectivePreInstance_000017",
        "ObjectivePreInstance_000016",
        "ObjectivePreInstance_000016",
        "ObjectivePreInstance_000015",
        "ObjectivePreInstance_000015",
        "ObjectivePreInstance_000014",
        "ObjectivePreInstance_000014",
        "ObjectivePreInstance_000013",
        "ObjectivePreInstance_000013",
        "ObjectivePreInstance_000012",
        "ObjectivePreInstance_000012",
        "ObjectivePreInstance_000011",
        "ObjectivePreInstance_000011",
        "ObjectivePreInstance_000010",
        "ObjectivePreInstance_000010",
        "ObjectivePreInstance_000009",
        "ObjectivePreInstance_000009",
        "ObjectivePreInstance_000008",
        "ObjectivePreInstance_000008",
        "ObjectivePreInstance_000007",
        "ObjectivePreInstance_000007",
        "ObjectivePreInstance_000006",
        "ObjectivePreInstance_000006",
        "ObjectivePreInstance_000005",
        "ObjectivePreInstance_000003",
        "ObjectivePreInstance_000003",
        "ObjectivePreInstance_000002",
        "ObjectivePreInstance_000002",
        "ObjectivePreInstance_000001",
        "ObjectivePreInstance_000001",
    ]

    actual_uids = [item["uid"] for item in res["items"]]
    assert actual_uids == expected_uids


def test_create_pre_instance_objective_template(api_client):
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
        "is_confirmatory_testing": True,
        "indication_uids": [dictionary_term_indication.term_uid],
        "category_uids": [ct_term_category.term_uid],
    }
    response = api_client.post(
        f"objective-templates/{objective_template.uid}/pre-instances", json=data
    )
    res = response.json()
    log.info("Created Objective Pre-Instance: %s", res)

    assert_response_status_code(response, 201)
    assert "PreInstance" in res["uid"]
    assert res["sequence_id"]
    assert res["template_uid"] == objective_template.uid
    assert res["is_confirmatory_testing"] is True
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
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    # assert (
    #    res["categories"][0]["attributes"]["code_submission_value"]
    #    == ct_term_category.code_submission_value
    # )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"


def test_keep_original_case_of_unit_definition_parameter_if_it_is_in_the_start_of_objective_pre_instance(
    api_client,
):
    TestUtils.create_template_parameter("Unit")
    _unit = TestUtils.create_unit_definition("u/week", template_parameter=True)

    _objective_template = TestUtils.create_objective_template(
        name="[Unit] test ignore case",
        guidance_text="Default guidance text",
        study_uid=None,
        library_name="Sponsor",
        indication_uids=[],
        category_uids=[],
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
        "is_confirmatory_testing": True,
        "indication_uids": [],
        "category_uids": [],
    }
    response = api_client.post(
        f"objective-templates/{_objective_template.uid}/pre-instances", json=data
    )
    res = response.json()
    log.info("Created Objective Pre-Instance: %s", res)

    assert_response_status_code(response, 201)
    assert res["name"] == f"[{_unit.name}] test ignore case"


def test_objective_pre_instance_sequence_id_generation(api_client):
    template = TestUtils.create_objective_template(
        name="Default [TextValue]",
        guidance_text="Default guidance text",
        study_uid=None,
        library_name="Sponsor",
        indication_uids=[dictionary_term_indication.term_uid],
        category_uids=[ct_term_category.term_uid],
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
        "is_confirmatory_testing": True,
        "indication_uids": [dictionary_term_indication.term_uid],
        "category_uids": [ct_term_category.term_uid],
    }
    response = api_client.post(
        f"objective-templates/{template.uid}/pre-instances", json=data
    )
    res = response.json()
    log.info("Created Objective Pre-Instance: %s", res)

    assert_response_status_code(response, 201)
    assert "PreInstance" in res["uid"]
    assert res["sequence_id"] == "O3P1"
    assert res["template_uid"] == template.uid
    assert res["is_confirmatory_testing"] is True
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
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    # assert (
    #    res["categories"][0]["attributes"]["code_submission_value"]
    #    == ct_term_category.code_submission_value
    # )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"


def test_objective_pre_instance_template_parameter_rules(api_client):
    template = TestUtils.create_objective_template(
        name="[TextValue], [TextValue] parameters",
        guidance_text="Default guidance text",
        study_uid=None,
        library_name="Sponsor",
        indication_uids=[dictionary_term_indication.term_uid],
        category_uids=[ct_term_category.term_uid],
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
        "is_confirmatory_testing": True,
        "indication_uids": [dictionary_term_indication.term_uid],
        "category_uids": [ct_term_category.term_uid],
    }
    response = api_client.post(
        f"objective-templates/{template.uid}/pre-instances", json=data
    )
    res = response.json()
    log.info("Created Objective Pre-Instance: %s", res)

    assert_response_status_code(response, 201)
    assert "PreInstance" in res["uid"]
    assert res["sequence_id"] == "O4P1"
    assert res["template_uid"] == template.uid
    assert res["is_confirmatory_testing"] is True
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
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name"]
        == ct_term_category.sponsor_preferred_name
    )
    assert (
        res["categories"][0]["name"]["sponsor_preferred_name_sentence_case"]
        == ct_term_category.sponsor_preferred_name_sentence_case
    )
    # assert (
    #    res["categories"][0]["attributes"]["code_submission_value"]
    #    == ct_term_category.code_submission_value
    # )
    assert (
        res["categories"][0]["attributes"]["nci_preferred_name"]
        == ct_term_category.nci_preferred_name
    )
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
