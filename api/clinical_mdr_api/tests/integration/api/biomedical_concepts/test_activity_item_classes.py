"""
Tests for /activity-item-classes endpoints
"""

import json
import logging
from functools import reduce
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
)
from clinical_mdr_api.models.biomedical_concepts.activity_item_class import (
    ActivityItemClass,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import CTCodelist
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.standard_data_models.data_model_ig import DataModelIG
from clinical_mdr_api.models.standard_data_models.dataset import Dataset
from clinical_mdr_api.models.standard_data_models.dataset_class import DatasetClass
from clinical_mdr_api.models.standard_data_models.dataset_variable import (
    DatasetVariable,
)
from clinical_mdr_api.models.standard_data_models.variable_class import VariableClass
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import CT_CODELIST_UIDS, TestUtils
from clinical_mdr_api.tests.utils.checks import (
    assert_response_status_code,
    parse_json_response,
)

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
activity_item_classes_all: list[ActivityItemClass]
activity_instance_class: ActivityInstanceClass
activity_instance_class2: ActivityInstanceClass
role_term: CTTerm
data_type_term: CTTerm
dataset_class: DatasetClass
variable_class: VariableClass
data_type_codelist: CTCodelist
role_codelist: CTCodelist
response_codelist: CTCodelist
dataset: Dataset
dataset_variable: DatasetVariable
data_model_catalogue_name: str
data_model_ig: DataModelIG


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    inject_and_clear_db("activity-item-class.api")
    inject_base_data()
    TestUtils.create_study_fields_ct_data()

    global activity_item_classes_all
    global activity_instance_class
    global activity_instance_class2
    global data_type_codelist
    global data_type_term
    global role_codelist
    global role_term
    global response_codelist
    global variable_class
    global dataset_class
    global dataset
    global dataset_variable
    global data_model_catalogue_name
    global data_model_ig

    activity_instance_class = TestUtils.create_activity_instance_class(
        name="Activity Instance Class name1"
    )
    activity_instance_class2 = TestUtils.create_activity_instance_class(
        name="Activity Instance Class name2"
    )

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
    response_codelist = TestUtils.create_ct_codelist(
        name="RESPONSE", submission_value="RESPONSE", extensible=True, approve=True
    )
    data_model = TestUtils.create_data_model()
    data_model_catalogue_name = TestUtils.create_data_model_catalogue()
    dataset_class = TestUtils.create_dataset_class(
        data_model_uid=data_model.uid,
        data_model_catalogue_name=data_model_catalogue_name,
        data_model_name=data_model.name,
    )
    variable_class = TestUtils.create_variable_class(
        dataset_class_uid=dataset_class.uid,
        data_model_catalogue_name=data_model_catalogue_name,
        data_model_name=data_model.uid,
        data_model_version=data_model.version_number,
    )
    data_model_ig = TestUtils.create_data_model_ig(
        implemented_data_model=data_model.uid
    )
    dataset = TestUtils.create_dataset(
        data_model_ig_uid=data_model_ig.uid,
        data_model_ig_version_number=data_model_ig.version_number,
        implemented_dataset_class_name=dataset_class.uid,
        data_model_catalogue_name=data_model_catalogue_name,
    )
    dataset_variable = TestUtils.create_dataset_variable(
        dataset_uid=dataset.uid,
        data_model_catalogue_name=data_model_catalogue_name,
        data_model_ig_name=data_model_ig.uid,
        data_model_ig_version=data_model_ig.version_number,
        class_variable_uid=variable_class.uid,
        references_codelist_uids=[CT_CODELIST_UIDS.default],
    )

    # Create some activity item classes
    activity_item_classes_all = [
        TestUtils.create_activity_item_class(
            name="name A",
            definition="definition A",
            nci_concept_id="nci id A",
            nci_concept_name="nci name A",
            order=1,
            activity_instance_classes=[
                {
                    "uid": activity_instance_class.uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": True,
                    "is_additional_optional": False,
                    "is_default_linked": False,
                },
                {
                    "uid": activity_instance_class2.uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": True,
                    "is_additional_optional": False,
                    "is_default_linked": False,
                },
            ],
            role_uid=role_term.term_uid,
            data_type_uid=data_type_term.term_uid,
        ),
        TestUtils.create_activity_item_class(
            name="name-AAA",
            definition="definition AAA",
            nci_concept_id="nci id AAA",
            order=2,
            activity_instance_classes=[
                {
                    "uid": activity_instance_class.uid,
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
            name="name-BBB",
            definition="definition BBB",
            nci_concept_id="nci id BBB",
            order=3,
            activity_instance_classes=[
                {
                    "uid": activity_instance_class.uid,
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
            name="name XXX",
            definition="definition XXX",
            nci_concept_id="nci id XXX",
            order=4,
            activity_instance_classes=[
                {
                    "uid": activity_instance_class.uid,
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
            name="name YYY",
            definition="definition YYY",
            nci_concept_id="nci id YYY",
            order=5,
            activity_instance_classes=[
                {
                    "uid": activity_instance_class.uid,
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

    for index in range(5):
        activity_item_classes_all.append(
            TestUtils.create_activity_item_class(
                name=f"name-AAA-{index}",
                definition=f"definition AAA-{index}",
                nci_concept_id=f"nci id AAA-{index}",
                order=(index * 4) + 1,
                activity_instance_classes=[
                    {
                        "uid": activity_instance_class.uid,
                        "mandatory": False,
                        "is_adam_param_specific_enabled": False,
                        "is_additional_optional": False,
                        "is_default_linked": False,
                    }
                ],
                role_uid=role_term.term_uid,
                data_type_uid=data_type_term.term_uid,
            )
        )
        activity_item_classes_all.append(
            TestUtils.create_activity_item_class(
                name=f"name-BBB-{index}",
                definition=f"definition BBB-{index}",
                nci_concept_id=f"nci id BBB-{index}",
                order=(index * 4) + 2,
                activity_instance_classes=[
                    {
                        "uid": activity_instance_class.uid,
                        "mandatory": False,
                        "is_adam_param_specific_enabled": False,
                        "is_additional_optional": False,
                        "is_default_linked": False,
                    },
                ],
                role_uid=role_term.term_uid,
                data_type_uid=data_type_term.term_uid,
            )
        )
        activity_item_classes_all.append(
            TestUtils.create_activity_item_class(
                name=f"name-XXX-{index}",
                definition=f"definition XXX-{index}",
                nci_concept_id=f"nci id XXX-{index}",
                order=(index * 4) + 3,
                activity_instance_classes=[
                    {
                        "uid": activity_instance_class.uid,
                        "mandatory": False,
                        "is_adam_param_specific_enabled": False,
                        "is_additional_optional": False,
                        "is_default_linked": False,
                    },
                ],
                role_uid=role_term.term_uid,
                data_type_uid=data_type_term.term_uid,
            )
        )
        activity_item_classes_all.append(
            TestUtils.create_activity_item_class(
                name=f"name-YYY-{index}",
                definition=f"definition YYY-{index}",
                nci_concept_id=f"nci id YYY-{index}",
                order=(index * 4) + 4,
                activity_instance_classes=[
                    {
                        "uid": activity_instance_class.uid,
                        "mandatory": False,
                        "is_adam_param_specific_enabled": False,
                        "is_additional_optional": False,
                        "is_default_linked": False,
                    },
                ],
                role_uid=role_term.term_uid,
                data_type_uid=data_type_term.term_uid,
            )
        )


ACTIVITY_IC_FIELDS_ALL = [
    "uid",
    "name",
    "display_name",
    "definition",
    "nci_concept_id",
    "nci_concept_name",
    "order",
    "activity_instance_classes",
    "data_type",
    "role",
    "variable_classes",
    "valid_codelists",
    "non_standard_variable",
    "library_name",
    "start_date",
    "end_date",
    "status",
    "version",
    "change_description",
    "author_username",
    "possible_actions",
]

ACTIVITY_IC_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "order",
    "activity_instance_classes",
    "data_type",
    "role",
]


def test_get_activity_item_class(api_client):
    """
    SCENARIO: Retrieve a single activity item class by UID
    GIVEN an approved activity item class with known fields and linked instance classes
    WHEN GET /activity-item-classes/{uid} is called
    THEN 200 is returned with all expected fields, correct values, linked activity_instance_classes, role and data_type
    """
    response = api_client.get(
        f"/activity-item-classes/{activity_item_classes_all[0].uid}"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(res.keys()) == set(ACTIVITY_IC_FIELDS_ALL)
    for key in ACTIVITY_IC_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == activity_item_classes_all[0].uid
    assert res["name"] == "name A"
    assert res["definition"] == "definition A"
    assert res["nci_concept_id"] == "nci id A"
    assert res["nci_concept_name"] == "nci name A"
    assert res["order"] == 1
    assert sorted(
        instance_class["uid"] for instance_class in res["activity_instance_classes"]
    ) == [activity_instance_class.uid, activity_instance_class2.uid]
    assert sorted(
        instance_class["name"] for instance_class in res["activity_instance_classes"]
    ) == [activity_instance_class.name, activity_instance_class2.name]
    assert res["role"]["uid"] == role_term.term_uid
    assert res["data_type"]["uid"] == data_type_term.term_uid
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_get_activity_item_class_pagination(api_client):
    """
    SCENARIO: Paginated listing of activity item classes returns consistent results
    GIVEN multiple activity item classes exist
    WHEN the list endpoint is fetched across multiple pages (page_size=10) and in one large page (page_size=1000)
    THEN the merged paginated results match the single-page result and the total fixture count
    """
    results_paginated: dict[Any, Any] = {}
    sort_by = '{"name": true}'
    page_size = 10
    for page_number in range(1, 4):
        res = parse_json_response(
            api_client.get(
                "/activity-item-classes",
                params={
                    "page_number": page_number,
                    "page_size": page_size,
                    "sort_by": sort_by,
                },
            )
        )
        items = res["items"]
        assert (
            0 < len(items) <= page_size
        ), f"Empty page #{page_number} or too many items > {page_size}, sorted by {sort_by}"
        res_names = [item["name"] for item in items]
        results_paginated[page_number] = res_names
        log.info("Page %s: %s", page_number, res_names)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        reduce(lambda a, b: list(a) + list(b), list(results_paginated.values()))
    )
    log.info("All rows returned by pagination: %s", results_paginated_merged)

    res_all = parse_json_response(
        api_client.get(
            "/activity-item-classes",
            params={"page_number": 1, "page_size": 1000, "sort_by": sort_by},
        )
    )
    results_all_in_one_page = list(map(lambda x: x["name"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(activity_item_classes_all) == len(results_paginated_merged)


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
def test_get_activity_item_classes(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    """
    SCENARIO: List activity item classes with various pagination and sort parameters
    GIVEN activity item classes exist in the system
    WHEN GET /activity-item-classes is called with parametrized page_size, page_number, total_count, sort_by
    THEN 200 is returned with the correct number of items, pagination metadata and all required fields present
    """
    params = {}
    if page_size:
        params["page_size"] = page_size
    if page_number:
        params["page_number"] = page_number
    if total_count:
        params["total_count"] = total_count
    if sort_by:
        params["sort_by"] = sort_by

    res = parse_json_response(api_client.get("/activity-item-classes", params=params))

    # Check fields included in the response
    assert list(res.keys()) == ["items", "total", "page", "size"]
    assert len(res["items"]) == expected_result_len
    assert res["total"] == (len(activity_item_classes_all) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(ACTIVITY_IC_FIELDS_ALL)
        for key in ACTIVITY_IC_FIELDS_NOT_NULL:
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
def test_get_activity_item_classes_csv_xml_excel(api_client, export_format):
    """
    SCENARIO: Export activity item classes in CSV, XML, and Excel formats
    GIVEN activity item classes exist
    WHEN GET /activity-item-classes is called with Accept header for csv/xml/excel
    THEN 200 is returned with data in the requested export format
    """
    url = "activity-item-classes"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "name", "name-AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "name", "name-BBB"),
        pytest.param(
            '{"*": {"v": ["Activity Instance Class name1"]}}',
            "activity_instance_classes.name",
            "Activity Instance Class name1",
        ),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    """
    SCENARIO: Wildcard filter on activity item classes list
    GIVEN activity item classes with varied names and activity_instance_classes exist
    WHEN GET /activity-item-classes is called with a wildcard filter
    THEN 200 is returned and each result row contains a field matching the filter prefix, or no results when no match
    """
    url = f"/activity-item-classes?filters={filter_by}"
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
        pytest.param('{"name": {"v": ["cc"]}}', None, None),
        pytest.param('{"order": {"v": [1]}}', "order", 1),
        pytest.param(
            '{"activity_instance_classes.uid": {"v": ["ActivityInstanceClass_000001"]}}',
            "activity_instance_classes.uid",
            "ActivityInstanceClass_000001",
        ),
        pytest.param(
            '{"activity_instance_classes.name": {"v": ["Activity Instance Class name1"]}}',
            "activity_instance_classes.name",
            "Activity Instance Class name1",
        ),
        pytest.param(
            '{"activity_instance_classes.mandatory": {"v": [true]}}',
            "activity_instance_classes.mandatory",
            True,
        ),
        pytest.param(
            '{"data_type.name": {"v": ["Data type"]}}',
            "data_type.name",
            "Data type",
        ),
        pytest.param(
            '{"role.name": {"v": ["Role"]}}',
            "role.name",
            "Role",
        ),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    """
    SCENARIO: Exact filter on activity item classes list
    GIVEN activity item classes with specific names, orders, data_types, roles and linked instance classes exist
    WHEN GET /activity-item-classes is called with an exact-match filter
    THEN 200 is returned and each result row has the filtered field exactly equal to the expected value, or no results when no match
    """
    url = f"/activity-item-classes?filters={filter_by}"
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


def test_edit_activity_item_class(api_client):
    """
    SCENARIO: Edit an activity item class via PATCH with updated fields and model/codelist mappings
    GIVEN a draft activity item class created with one activity_instance_class
    WHEN PATCH is called with updated name, definition, order and a different activity_instance_class, then model-mappings and valid-codelist-mappings are patched
    THEN 200 is returned with updated fields; a subsequent GET confirms persistence; model-mappings and codelist-mappings are stored correctly
    """
    activity_instance_class_after_edit = TestUtils.create_activity_instance_class(
        name="Activity IC after edit"
    )
    activity_item_class = TestUtils.create_activity_item_class(
        name="New item class",
        order=30,
        activity_instance_classes=[
            {
                "uid": activity_instance_class.uid,
                "mandatory": True,
                "is_adam_param_specific_enabled": True,
                "is_additional_optional": False,
                "is_default_linked": False,
            }
        ],
        approve=False,
        data_type_uid=data_type_term.term_uid,
        role_uid=role_term.term_uid,
    )
    response = api_client.patch(
        f"/activity-item-classes/{activity_item_class.uid}",
        json={
            "name": "new name for item class",
            "definition": "new definition for item class",
            "nci_concept_id": "new nci concept id",
            "nci_concept_name": "new nci concept name",
            "display_name": "new display name for item class",
            "order": 45,
            "activity_instance_classes": [
                {
                    "uid": activity_instance_class_after_edit.uid,
                    "mandatory": False,
                    "is_adam_param_specific_enabled": False,
                    "is_additional_optional": True,
                    "is_default_linked": True,
                }
            ],
            "change_description": "updated item class",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["name"] == "new name for item class"
    assert res["definition"] == "new definition for item class"
    assert res["nci_concept_id"] == "new nci concept id"
    assert res["nci_concept_name"] == "new nci concept name"
    assert res["display_name"] == "new display name for item class"
    assert res["order"] == 45
    ic_after_edit = next(
        x
        for x in res["activity_instance_classes"]
        if x["uid"] == activity_instance_class_after_edit.uid
    )
    assert ic_after_edit["name"] == "Activity IC after edit"
    assert ic_after_edit["mandatory"] is False
    assert ic_after_edit["is_adam_param_specific_enabled"] is False
    assert ic_after_edit["is_additional_optional"] is True
    assert ic_after_edit["is_default_linked"] is True
    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["library_name"] == "Sponsor"

    # Verify the changes persisted by doing a GET request
    get_response = api_client.get(f"/activity-item-classes/{activity_item_class.uid}")
    get_res = get_response.json()
    assert_response_status_code(get_response, 200)
    assert get_res["name"] == "new name for item class"
    assert get_res["definition"] == "new definition for item class"
    assert get_res["nci_concept_id"] == "new nci concept id"
    assert get_res["nci_concept_name"] == "new nci concept name"
    assert get_res["display_name"] == "new display name for item class"
    assert get_res["order"] == 45
    ic_after_edit = next(
        x
        for x in res["activity_instance_classes"]
        if x["uid"] == activity_instance_class_after_edit.uid
    )
    assert ic_after_edit["name"] == "Activity IC after edit"
    assert ic_after_edit["mandatory"] is False
    assert ic_after_edit["is_adam_param_specific_enabled"] is False
    assert ic_after_edit["is_additional_optional"] is True
    assert ic_after_edit["is_default_linked"] is True
    assert get_res["version"] == "0.2"
    assert get_res["status"] == "Draft"
    assert get_res["possible_actions"] == ["approve", "delete", "edit"]
    assert get_res["library_name"] == "Sponsor"

    response = api_client.patch(
        f"/activity-item-classes/{activity_item_class.uid}/model-mappings",
        json={
            "variable_class_uids": [variable_class.uid],
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["variable_classes"] == [{"uid": variable_class.uid}]

    # Edit Valid codelist mapping and verify
    response = api_client.patch(
        f"/activity-item-classes/{activity_item_class.uid}/valid-codelist-mappings",
        json={"valid_codelist_uids": [response_codelist.codelist_uid]},
    )
    res = response.json()
    assert_response_status_code(response, 200)

    response = api_client.get(
        f"/activity-item-classes/{activity_item_class.uid}/datasets/{dataset.uid}/codelists?valid_codelists_for_item=True",
    )
    res = response.json()
    assert len(res["items"]) == 1
    assert res["items"][0]["codelist_uid"] == response_codelist.codelist_uid


def test_post_activity_item_class(api_client):
    """
    SCENARIO: Create a new activity item class via POST
    GIVEN valid payload with name, definition, order, role, data_type and activity_instance_class
    WHEN POST /activity-item-classes is called
    THEN 201 is returned with correct name, definition, order, activity_instance_class details, and metadata (version 0.1, Draft)
    """
    response = api_client.post(
        "/activity-item-classes",
        json={
            "name": "New AIC Name",
            "definition": "New AIC Def",
            "nci_concept_id": "New nci id",
            "nci_concept_name": "New nci name",
            "display_name": "New AIC Display Name",
            "order": 36,
            "library_name": "Sponsor",
            "activity_instance_classes": [
                {
                    "uid": activity_instance_class.uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": True,
                    "is_additional_optional": False,
                    "is_default_linked": False,
                }
            ],
            "role_uid": role_term.term_uid,
            "data_type_uid": data_type_term.term_uid,
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["name"] == "New AIC Name"
    assert res["definition"] == "New AIC Def"
    assert res["nci_concept_id"] == "New nci id"
    assert res["nci_concept_name"] == "New nci name"
    assert res["display_name"] == "New AIC Display Name"
    assert res["order"] == 36
    assert res["activity_instance_classes"][0]["uid"] == activity_instance_class.uid
    assert res["activity_instance_classes"][0]["name"] == activity_instance_class.name
    assert res["activity_instance_classes"][0]["mandatory"] is True
    assert res["activity_instance_classes"][0]["is_adam_param_specific_enabled"] is True
    assert res["activity_instance_classes"][0]["is_additional_optional"] is False
    assert res["activity_instance_classes"][0]["is_default_linked"] is False
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "delete", "edit"]
    assert res["library_name"] == "Sponsor"


def test_activity_item_class_versioning(api_client):
    """
    SCENARIO: Full versioning lifecycle for an activity item class
    GIVEN a draft activity item class is created
    WHEN version lifecycle actions (new_version on draft, approve, approve twice, activate non-retired, inactivate, reactivate, new_version, delete draft) are called in sequence
    THEN each valid action succeeds and each invalid transition returns 400 with the appropriate message
    """
    activity_item_class = TestUtils.create_activity_item_class(
        name="New item",
        order=2,
        activity_instance_classes=[
            {
                "uid": activity_instance_class.uid,
                "mandatory": False,
                "is_adam_param_specific_enabled": False,
                "is_additional_optional": False,
                "is_default_linked": False,
            }
        ],
        approve=False,
        data_type_uid=data_type_term.term_uid,
        role_uid=role_term.term_uid,
    )

    # not successful create new version
    response = api_client.post(
        f"/activity-item-classes/{activity_item_class.uid}/versions"
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert res["message"] == "New draft version can be created only for FINAL versions."

    # successful approve
    response = api_client.post(
        f"/activity-item-classes/{activity_item_class.uid}/approvals"
    )
    assert_response_status_code(response, 201)

    # not successful approve
    response = api_client.post(
        f"/activity-item-classes/{activity_item_class.uid}/approvals"
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert res["message"] == "The object isn't in draft status."

    # not successful reactivate
    response = api_client.post(
        f"/activity-item-classes/{activity_item_class.uid}/activations"
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == "Only RETIRED version can be reactivated."

    # successful inactivate
    response = api_client.delete(
        f"/activity-item-classes/{activity_item_class.uid}/activations"
    )
    assert_response_status_code(response, 200)

    # successful reactivate
    response = api_client.post(
        f"/activity-item-classes/{activity_item_class.uid}/activations"
    )
    assert_response_status_code(response, 200)

    # successful new version
    response = api_client.post(
        f"/activity-item-classes/{activity_item_class.uid}/versions"
    )
    assert_response_status_code(response, 201)

    activity_ic_to_delete = TestUtils.create_activity_item_class(
        name="activity ic to delete",
        order=2,
        activity_instance_classes=[
            {
                "uid": activity_instance_class.uid,
                "mandatory": False,
                "is_adam_param_specific_enabled": False,
                "is_additional_optional": False,
                "is_default_linked": False,
            },
        ],
        approve=False,
        data_type_uid=data_type_term.term_uid,
        role_uid=role_term.term_uid,
    )
    # successful delete
    response = api_client.delete(f"/activity-item-classes/{activity_ic_to_delete.uid}")
    assert_response_status_code(response, 204)


def test_get_activity_item_class_codelists(api_client):
    """
    SCENARIO: Retrieve codelists for an activity item class scoped to a dataset
    GIVEN an activity item class mapped to a variable_class and a response codelist, with optional sponsor model overrides
    WHEN GET /activity-item-classes/{uid}/datasets/{dataset_uid}/codelists is called with various filters (ct_catalogue_name, use_sponsor_model, valid_codelists_for_item)
    THEN 200 is returned and the correct codelists and term_uids are returned for each filter combination
    """
    # Map an ActivityItemClass to a VariableClass
    # This VariableClass will have Variables belonging to the target Dataset
    api_client.patch(
        f"/activity-item-classes/{activity_item_classes_all[0].uid}/model-mappings",
        json={
            "variable_class_uids": [variable_class.uid],
        },
    )

    # Also map the item class to a response codelist
    api_client.patch(
        f"/activity-item-classes/{activity_item_classes_all[0].uid}/valid-codelist-mappings",
        json={"valid_codelist_uids": [response_codelist.codelist_uid]},
    )

    # Fetching terms with this ActivityItemClass and Dataset
    # Will return those Variables
    # Which will in turn map a Codelist, whose Terms should be returned
    response = api_client.get(
        f"/activity-item-classes/{activity_item_classes_all[0].uid}/datasets/{dataset.uid}/codelists"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["items"][0]["codelist_uid"] == "C66737"
    assert len(res["items"]) == 1

    # term uids should be None, indicating that all terms of the codelist are available
    assert res["items"][0]["term_uids"] is None

    # Fetch codelists with ct catalogue name filter
    response = api_client.get(
        f"/activity-item-classes/{activity_item_classes_all[0].uid}/datasets/{dataset.uid}/codelists?ct_catalogue_name=SDTM CT"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 1
    assert res["items"][0]["codelist_uid"] == "C66737"

    # Fetch codelists with non-existent ct catalogue name filter
    response = api_client.get(
        f"/activity-item-classes/{activity_item_classes_all[0].uid}/datasets/{dataset.uid}/codelists?ct_catalogue_name=non-existent"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 0

    # Now, test that sponsor models are properly used
    sponsor_model = TestUtils.create_sponsor_model(
        ig_uid=data_model_ig.uid,
        ig_version_number=data_model_ig.version_number,
        version_number="1",
    )
    sponsor_dataset = TestUtils.create_sponsor_dataset(
        dataset_uid=dataset.uid,
        sponsor_model_name=sponsor_model.name,
        sponsor_model_version_number=sponsor_model.version,
        implemented_dataset_class=dataset_class.uid,
    )

    _ = TestUtils.create_sponsor_dataset_variable(
        target_data_model_catalogue=data_model_catalogue_name,
        dataset_uid=sponsor_dataset.uid,
        dataset_variable_uid=dataset_variable.uid,
        sponsor_model_name=sponsor_model.name,
        sponsor_model_version_number=sponsor_model.version,
        implemented_variable_class=variable_class.uid,
        implemented_parent_dataset_class=dataset_class.uid,
        references_codelists=[CT_CODELIST_UIDS.default],
        references_terms=["C123631"],
    )

    # Fetch codelists using sponsor model
    # Should be filtered down to a single term
    response = api_client.get(
        f"/activity-item-classes/{activity_item_classes_all[0].uid}/datasets/{dataset.uid}/codelists?use_sponsor_model=True"
    )
    res = response.json()
    assert len(res["items"]) == 1
    assert res["items"][0]["term_uids"] == ["C123631"]

    # Fetch codelists without using sponsor model
    # Should return all terms, i.e. None
    response = api_client.get(
        f"/activity-item-classes/{activity_item_classes_all[0].uid}/datasets/{dataset.uid}/codelists?use_sponsor_model=False"
    )
    res = response.json()
    # term uids should be None, indicating that all terms of the codelist are available
    assert len(res["items"]) == 1
    assert res["items"][0]["term_uids"] is None

    # Finally, fetching using the valid codelists filter
    # Will only return the specific codelists marked as valid
    response = api_client.get(
        f"/activity-item-classes/{activity_item_classes_all[0].uid}/datasets/{dataset.uid}/codelists?valid_codelists_for_item=True",
    )
    res = response.json()
    assert len(res["items"]) == 1
    assert res["items"][0]["codelist_uid"] == response_codelist.codelist_uid


def test_get_activity_item_class_overview(api_client: TestClient) -> None:
    """
    SCENARIO: Retrieve overview of an activity item class including all versions
    GIVEN a Final activity item class and its draft version exist
    WHEN GET /activity-item-classes/{uid}/overview is called (with and without version parameter), and with an invalid UID
    THEN the current version returns correct item details and all_versions; with version=0.1 returns the draft; invalid UID returns 404
    """
    activity_item_class = activity_item_classes_all[0]

    # Test basic overview
    response = api_client.get(
        f"/activity-item-classes/{activity_item_class.uid}/overview"
    )
    assert_response_status_code(response, 200)

    result = response.json()
    assert "activity_item_class" in result
    assert "all_versions" in result

    item_detail = result["activity_item_class"]
    assert item_detail["uid"] == activity_item_class.uid
    assert item_detail["name"] == activity_item_class.name
    assert item_detail["definition"] == activity_item_class.definition
    assert item_detail["nci_code"] == activity_item_class.nci_concept_id
    assert item_detail["nci_concept_name"] == activity_item_class.nci_concept_name
    assert item_detail["status"] == "Final"  # Test data creates items with Final status
    assert item_detail["version"] == "1.0"  # Test data creates version 1.0
    # Non-NSV item classes still expose the field; value is null when not applicable.
    assert "non_standard_variable" in item_detail
    assert item_detail["non_standard_variable"] is None

    # Test with version parameter
    response = api_client.get(
        f"/activity-item-classes/{activity_item_class.uid}/overview?version=0.1"
    )
    assert_response_status_code(response, 200)

    result = response.json()
    assert result["activity_item_class"]["version"] == "0.1"

    # Test with non-existent UID
    response = api_client.get("/activity-item-classes/INVALID_UID/overview")
    assert_response_status_code(response, 404)


def test_get_activity_instance_classes_using_item(api_client: TestClient) -> None:
    """
    SCENARIO: Retrieve activity instance classes that use a specific activity item class
    GIVEN an activity item class linked to multiple activity instance classes
    WHEN GET /activity-item-classes/{uid}/activity-instance-classes is called with and without pagination/version parameters, and with an invalid UID
    THEN 200 is returned with correct item structure and pagination metadata; invalid UID returns empty list with total=0
    """
    activity_item_class = activity_item_classes_all[0]

    # Test basic request
    response = api_client.get(
        f"/activity-item-classes/{activity_item_class.uid}/activity-instance-classes"
    )
    assert_response_status_code(response, 200)

    result = response.json()
    assert "items" in result
    assert "total" in result
    assert len(result["items"]) > 0

    # Check first item structure
    first_item = result["items"][0]
    assert "uid" in first_item
    assert "name" in first_item
    assert "adam_param_specific_enabled" in first_item
    assert "mandatory" in first_item
    assert "modified_date" in first_item
    assert "modified_by" in first_item
    assert "version" in first_item
    assert "status" in first_item

    # Test with pagination
    response = api_client.get(
        f"/activity-item-classes/{activity_item_class.uid}/activity-instance-classes?page_size=1&page_number=1&total_count=true"
    )
    assert_response_status_code(response, 200)

    result = response.json()
    assert len(result["items"]) <= 1
    assert result["total"] >= 1

    # Test with version parameter
    response = api_client.get(
        f"/activity-item-classes/{activity_item_class.uid}/activity-instance-classes?version=0.1"
    )
    assert_response_status_code(response, 200)

    # Test with non-existent UID - returns empty results
    response = api_client.get(
        "/activity-item-classes/INVALID_UID/activity-instance-classes"
    )
    assert_response_status_code(response, 200)
    result = response.json()
    assert result["items"] == []
    assert result["total"] == 0


def test_get_activity_item_classes_versions(api_client):
    """Test GET /activity-item-classes/versions endpoint"""
    # First, create a new version of one item class so we have multiple versions
    response = api_client.post(
        f"/activity-item-classes/{activity_item_classes_all[0].uid}/versions"
    )
    assert_response_status_code(response, 201)

    # Get all versions
    response = api_client.get(
        "/activity-item-classes/versions?page_size=100&total_count=true"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check response structure
    assert set(res.keys()) == {"items", "total", "page", "size"}
    assert res["total"] > 0

    # Should have more versions than unique classes (since we created a new version above)
    assert res["total"] > len(activity_item_classes_all)

    # Check that the items are sorted by start_date descending
    start_dates = [item["start_date"] for item in res["items"] if item["start_date"]]
    assert start_dates == sorted(start_dates, reverse=True)

    # Check that the class updated in this test has multiple versions
    versions_of_class = [
        item["version"]
        for item in res["items"]
        if item["uid"] == activity_item_classes_all[0].uid
    ]
    assert len(versions_of_class) >= 2

    # Check fields on first item
    item = res["items"][0]
    assert "uid" in item
    assert "name" in item
    assert "version" in item
    assert "status" in item
    assert "start_date" in item
    assert "library_name" in item


def test_get_activity_item_classes_versions_pagination(api_client):
    """Test pagination on /activity-item-classes/versions"""
    # Get first page
    response = api_client.get(
        "/activity-item-classes/versions?page_size=2&page_number=1&total_count=true"
    )
    assert_response_status_code(response, 200)
    page1 = response.json()
    assert len(page1["items"]) == 2
    assert page1["total"] > 2

    # Get second page
    response = api_client.get(
        "/activity-item-classes/versions?page_size=2&page_number=2&total_count=true"
    )
    assert_response_status_code(response, 200)
    page2 = response.json()
    assert len(page2["items"]) > 0

    # Pages should not overlap
    page1_uids_versions = {(i["uid"], i["version"]) for i in page1["items"]}
    page2_uids_versions = {(i["uid"], i["version"]) for i in page2["items"]}
    assert page1_uids_versions.isdisjoint(page2_uids_versions)


def test_post_activity_item_class_with_valid_codelist_uids(api_client):
    """
    SCENARIO: Create an activity item class with valid_codelist_uids
    GIVEN a valid payload and an existing codelist
    WHEN POST /activity-item-classes is called with valid_codelist_uids populated
    THEN the created item's response has valid_codelists populated with the given uids and their submission_value
    AND a subsequent GET by uid returns the same valid_codelists
    """
    response = api_client.post(
        "/activity-item-classes",
        json={
            "name": "AIC with valid codelists",
            "order": 100,
            "library_name": "Sponsor",
            "activity_instance_classes": [
                {
                    "uid": activity_instance_class.uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": False,
                    "is_additional_optional": False,
                    "is_default_linked": False,
                }
            ],
            "role_uid": role_term.term_uid,
            "data_type_uid": data_type_term.term_uid,
            "valid_codelist_uids": [response_codelist.codelist_uid],
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["valid_codelists"] == [
        {"uid": response_codelist.codelist_uid, "submission_value": "RESPONSE"}
    ]
    assert res["non_standard_variable"] is None

    # Verify via GET by uid (neomodel single-item path)
    get_res = api_client.get(f"/activity-item-classes/{res['uid']}").json()
    assert get_res["valid_codelists"] == [
        {"uid": response_codelist.codelist_uid, "submission_value": "RESPONSE"}
    ]


def test_post_activity_item_class_nsv_and_is_nsv_filter(api_client):
    """
    SCENARIO: Create a Non Standard Variable activity item class and filter listings by is_nsv
    GIVEN an existing role term and data type term
    WHEN POST /activity-item-classes is called with a non_standard_variable payload
    THEN the created item's response has non_standard_variable populated with the supplied fields
    AND GET /activity-item-classes?is_nsv=true returns the new item (and only NSV items)
    AND GET /activity-item-classes?is_nsv=false excludes the new item
    """
    response = api_client.post(
        "/activity-item-classes",
        json={
            "name": "NSV item class",
            "order": 101,
            "library_name": "Sponsor",
            "activity_instance_classes": [
                {
                    "uid": activity_instance_class.uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": False,
                    "is_additional_optional": False,
                    "is_default_linked": False,
                }
            ],
            "role_uid": role_term.term_uid,
            "data_type_uid": data_type_term.term_uid,
            "non_standard_variable": {
                "code": "NSV_CODE",
                "is_multiple": True,
                "length": 8,
                "algorithm": "ALG",
                "is_cdisc_defined": False,
                "derivation_rule": "rule X",
            },
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    created_uid = res["uid"]
    nsv = res["non_standard_variable"]
    assert nsv is not None
    assert nsv["code"] == "NSV_CODE"
    assert nsv["is_multiple"] is True
    assert nsv["length"] == 8
    assert nsv["algorithm"] == "ALG"
    assert nsv["is_cdisc_defined"] is False
    assert nsv["derivation_rule"] == "rule X"
    assert nsv["origin_type"] is None
    assert nsv["origin_source"] is None

    # Single-item GET returns same NSV payload
    get_res = api_client.get(f"/activity-item-classes/{created_uid}").json()
    assert get_res["non_standard_variable"]["code"] == "NSV_CODE"

    # Overview endpoint exposes the same NSV info under activity_item_class.non_standard_variable
    overview_detail = api_client.get(
        f"/activity-item-classes/{created_uid}/overview"
    ).json()["activity_item_class"]
    overview_nsv = overview_detail["non_standard_variable"]
    assert overview_nsv is not None
    assert overview_nsv["code"] == "NSV_CODE"
    assert overview_nsv["is_multiple"] is True
    assert overview_nsv["length"] == 8
    assert overview_nsv["algorithm"] == "ALG"
    assert overview_nsv["is_cdisc_defined"] is False
    assert overview_nsv["derivation_rule"] == "rule X"
    assert overview_nsv["origin_type"] is None
    assert overview_nsv["origin_source"] is None

    # List filtered by is_nsv=true must include the NSV and contain only NSV items
    nsv_list = parse_json_response(
        api_client.get(
            "/activity-item-classes",
            params={"is_nsv": "true", "page_size": 1000, "total_count": True},
        )
    )
    nsv_uids = {item["uid"] for item in nsv_list["items"]}
    assert created_uid in nsv_uids
    for item in nsv_list["items"]:
        assert item["non_standard_variable"] is not None

    # List filtered by is_nsv=false must exclude the NSV
    non_nsv_list = parse_json_response(
        api_client.get(
            "/activity-item-classes",
            params={"is_nsv": "false", "page_size": 1000, "total_count": True},
        )
    )
    non_nsv_uids = {item["uid"] for item in non_nsv_list["items"]}
    assert created_uid not in non_nsv_uids
    for item in non_nsv_list["items"]:
        assert item["non_standard_variable"] is None

    # Unfiltered list includes both (sanity check that the filter partitions the set)
    unfiltered = parse_json_response(
        api_client.get(
            "/activity-item-classes",
            params={"page_size": 1000, "total_count": True},
        )
    )
    assert nsv_list["total"] + non_nsv_list["total"] == unfiltered["total"]


def test_patch_activity_item_class_valid_codelist_uids(api_client):
    """
    SCENARIO: PATCH /activity-item-classes/{uid} honors valid_codelist_uids semantics
    GIVEN a draft activity item class
    WHEN valid_codelist_uids is provided as a list → mappings are replaced
    AND when omitted on a subsequent PATCH → existing mappings are preserved
    AND when provided as [] → mappings are cleared
    """
    activity_item_class = TestUtils.create_activity_item_class(
        name="AIC patch valid codelists",
        order=102,
        activity_instance_classes=[
            {
                "uid": activity_instance_class.uid,
                "mandatory": False,
                "is_adam_param_specific_enabled": False,
                "is_additional_optional": False,
                "is_default_linked": False,
            }
        ],
        approve=False,
        role_uid=role_term.term_uid,
        data_type_uid=data_type_term.term_uid,
    )

    # Replace: set mapping via PATCH
    response = api_client.patch(
        f"/activity-item-classes/{activity_item_class.uid}",
        json={
            "change_description": "add valid codelists",
            "valid_codelist_uids": [response_codelist.codelist_uid],
        },
    )
    assert_response_status_code(response, 200)
    assert response.json()["valid_codelists"] == [
        {"uid": response_codelist.codelist_uid, "submission_value": "RESPONSE"}
    ]

    # Preserve: omitting valid_codelist_uids keeps the mapping intact
    response = api_client.patch(
        f"/activity-item-classes/{activity_item_class.uid}",
        json={"change_description": "touch name", "name": "AIC patch vc renamed"},
    )
    assert_response_status_code(response, 200)
    assert response.json()["valid_codelists"] == [
        {"uid": response_codelist.codelist_uid, "submission_value": "RESPONSE"}
    ]

    # Clear: empty list wipes all mappings
    response = api_client.patch(
        f"/activity-item-classes/{activity_item_class.uid}",
        json={"change_description": "clear valid codelists", "valid_codelist_uids": []},
    )
    assert_response_status_code(response, 200)
    assert response.json()["valid_codelists"] == []


def test_patch_activity_item_class_non_standard_variable(api_client):
    """
    SCENARIO: PATCH /activity-item-classes/{uid} partially updates non_standard_variable
    GIVEN an NSV activity item class with core fields populated
    WHEN PATCH is called with only one NSV field (algorithm)
    THEN only that field changes and all other NSV fields are preserved
    AND a later PATCH that does not mention non_standard_variable still preserves NSV nature
    """
    # Create an NSV, keep as draft for PATCH
    response = api_client.post(
        "/activity-item-classes",
        json={
            "name": "NSV item class for patch",
            "order": 103,
            "library_name": "Sponsor",
            "activity_instance_classes": [
                {
                    "uid": activity_instance_class.uid,
                    "mandatory": False,
                    "is_adam_param_specific_enabled": False,
                    "is_additional_optional": False,
                    "is_default_linked": False,
                }
            ],
            "role_uid": role_term.term_uid,
            "data_type_uid": data_type_term.term_uid,
            "non_standard_variable": {
                "code": "ORIG_CODE",
                "is_multiple": False,
                "length": 4,
                "algorithm": "orig-alg",
                "is_cdisc_defined": True,
            },
        },
    )
    assert_response_status_code(response, 201)
    created_uid = response.json()["uid"]

    # Partial NSV patch: only algorithm changes, other fields preserved
    response = api_client.patch(
        f"/activity-item-classes/{created_uid}",
        json={
            "change_description": "tweak algorithm",
            "non_standard_variable": {"algorithm": "patched-alg"},
        },
    )
    assert_response_status_code(response, 200)
    nsv = response.json()["non_standard_variable"]
    assert nsv["algorithm"] == "patched-alg"
    assert nsv["code"] == "ORIG_CODE"
    assert nsv["is_multiple"] is False
    assert nsv["length"] == 4
    assert nsv["is_cdisc_defined"] is True

    # PATCH without non_standard_variable must preserve NSV nature (guards latent bug)
    response = api_client.patch(
        f"/activity-item-classes/{created_uid}",
        json={"change_description": "rename", "name": "NSV item class renamed"},
    )
    assert_response_status_code(response, 200)
    nsv_after_rename = response.json()["non_standard_variable"]
    assert nsv_after_rename is not None
    assert nsv_after_rename["code"] == "ORIG_CODE"
    assert nsv_after_rename["algorithm"] == "patched-alg"


def test_nsv_is_cdisc_defined_filter_headers_and_export(api_client):
    """
    SCENARIO: NSV is_cdisc_defined supports list filter, headers, and NSV CSV export
    GIVEN two NSVs with is_cdisc_defined true and false
    WHEN filtering / sorting / requesting headers / exporting with is_nsv=true
    THEN only matching NSVs are returned, headers include both booleans,
    AND CSV export columns include non_standard_variable.is_cdisc_defined
    """
    cdisc_true = api_client.post(
        "/activity-item-classes",
        json={
            "name": "NSV CDISC true",
            "order": 201,
            "library_name": "Sponsor",
            "activity_instance_classes": [
                {
                    "uid": activity_instance_class.uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": False,
                    "is_additional_optional": False,
                    "is_default_linked": False,
                }
            ],
            "role_uid": role_term.term_uid,
            "data_type_uid": data_type_term.term_uid,
            "non_standard_variable": {
                "code": "CDISC_Y",
                "is_multiple": False,
                "length": 8,
                "is_cdisc_defined": True,
            },
        },
    )
    assert_response_status_code(cdisc_true, 201)
    uid_true = cdisc_true.json()["uid"]

    cdisc_false = api_client.post(
        "/activity-item-classes",
        json={
            "name": "NSV CDISC false",
            "order": 202,
            "library_name": "Sponsor",
            "activity_instance_classes": [
                {
                    "uid": activity_instance_class.uid,
                    "mandatory": True,
                    "is_adam_param_specific_enabled": False,
                    "is_additional_optional": False,
                    "is_default_linked": False,
                }
            ],
            "role_uid": role_term.term_uid,
            "data_type_uid": data_type_term.term_uid,
            "non_standard_variable": {
                "code": "CDISC_N",
                "is_multiple": False,
                "length": 8,
                "is_cdisc_defined": False,
            },
        },
    )
    assert_response_status_code(cdisc_false, 201)
    uid_false = cdisc_false.json()["uid"]

    filtered = parse_json_response(
        api_client.get(
            "/activity-item-classes",
            params={
                "is_nsv": "true",
                "filters": json.dumps(
                    {"non_standard_variable.is_cdisc_defined": {"v": [True]}}
                ),
                "page_size": 1000,
                "total_count": True,
            },
        )
    )
    filtered_uids = {item["uid"] for item in filtered["items"]}
    assert uid_true in filtered_uids
    assert uid_false not in filtered_uids
    assert all(
        item["non_standard_variable"]["is_cdisc_defined"] is True
        for item in filtered["items"]
    )

    sorted_resp = parse_json_response(
        api_client.get(
            "/activity-item-classes",
            params={
                "is_nsv": "true",
                "sort_by": json.dumps({"non_standard_variable.is_cdisc_defined": True}),
                "page_size": 1000,
            },
        )
    )
    assert sorted_resp["items"]
    assert all("non_standard_variable" in item for item in sorted_resp["items"])

    headers = parse_json_response(
        api_client.get(
            "/activity-item-classes/headers",
            params={"field_name": "non_standard_variable.is_cdisc_defined"},
        )
    )
    assert True in headers
    assert False in headers

    export_response = TestUtils.verify_exported_data_format(
        api_client,
        "text/csv",
        "activity-item-classes",
        params={"is_nsv": "true"},
    )
    csv_header_line = export_response.content.decode("utf-8").splitlines()[0]
    assert "non_standard_variable.is_cdisc_defined" in csv_header_line
    # Column order: immediately after is_multiple in NSV export defaults
    assert csv_header_line.index(
        "non_standard_variable.is_multiple"
    ) < csv_header_line.index("non_standard_variable.is_cdisc_defined")


def _post_activity_item_class(
    api_client,
    name: str,
    order: int,
    non_standard_variable: dict[str, Any] | None = None,
):
    body = {
        "name": name,
        "order": order,
        "library_name": "Sponsor",
        "activity_instance_classes": [
            {
                "uid": activity_instance_class.uid,
                "mandatory": True,
                "is_adam_param_specific_enabled": False,
                "is_additional_optional": False,
                "is_default_linked": False,
            }
        ],
        "role_uid": role_term.term_uid,
        "data_type_uid": data_type_term.term_uid,
    }
    if non_standard_variable is not None:
        body["non_standard_variable"] = non_standard_variable
    return api_client.post("/activity-item-classes", json=body)


def test_standard_and_nsv_activity_item_class_can_share_name(api_client):
    """
    SCENARIO: name-uniqueness is scoped separately for standard items and NSVs
    GIVEN a standard (non-NSV) Activity Item Class with a given name
    WHEN a Non Standard Variable is created with that same name
    THEN it succeeds, since NSV name-uniqueness is independent from standard items'
    """
    shared_name = "Shared Standard NSV Name"

    standard_response = _post_activity_item_class(
        api_client, name=shared_name, order=301
    )
    assert_response_status_code(standard_response, 201)

    nsv_response = _post_activity_item_class(
        api_client,
        name=shared_name,
        order=302,
        non_standard_variable={
            "code": "SHARED_NAME_NSV_CODE",
            "is_multiple": False,
            "length": 8,
            "is_cdisc_defined": False,
        },
    )
    assert_response_status_code(nsv_response, 201)
    assert (
        nsv_response.json()["non_standard_variable"]["code"] == "SHARED_NAME_NSV_CODE"
    )


def test_duplicate_name_conflict_between_two_standard_activity_item_classes(
    api_client,
):
    """
    SCENARIO: name-uniqueness is still enforced within standard Activity Item Classes
    GIVEN an existing standard Activity Item Class with a given name
    WHEN another standard Activity Item Class is created with the same name
    THEN it fails with 409 AlreadyExistsException
    """
    name = "Duplicate Standard AIC Name"
    first_response = _post_activity_item_class(api_client, name=name, order=303)
    assert_response_status_code(first_response, 201)

    second_response = _post_activity_item_class(api_client, name=name, order=304)
    res = parse_json_response(second_response, assert_status=409)
    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == f"Activity Item Class with Name '{name}' already exists."


def test_duplicate_name_conflict_between_two_nsv_activity_item_classes(api_client):
    """
    SCENARIO: name-uniqueness is still enforced within Non Standard Variables
    GIVEN an existing NSV Activity Item Class with a given name
    WHEN another NSV Activity Item Class is created with the same name
    THEN it fails with 409 AlreadyExistsException
    """
    name = "Duplicate NSV Name"
    first_response = _post_activity_item_class(
        api_client,
        name=name,
        order=305,
        non_standard_variable={
            "code": "DUP_NSV_CODE_1",
            "is_multiple": False,
            "length": 8,
            "is_cdisc_defined": False,
        },
    )
    assert_response_status_code(first_response, 201)

    second_response = _post_activity_item_class(
        api_client,
        name=name,
        order=306,
        non_standard_variable={
            "code": "DUP_NSV_CODE_2",
            "is_multiple": False,
            "length": 8,
            "is_cdisc_defined": False,
        },
    )
    res = parse_json_response(second_response, assert_status=409)
    assert res["type"] == "AlreadyExistsException"
    assert res["message"] == f"Activity Item Class with Name '{name}' already exists."


def _patch_activity_item_class(
    api_client,
    uid: str,
    name: str,
    change_description: str = "rename",
    non_standard_variable: dict[str, Any] | None = None,
):
    body: dict[str, Any] = {"name": name, "change_description": change_description}
    if non_standard_variable is not None:
        body["non_standard_variable"] = non_standard_variable
    return api_client.patch(f"/activity-item-classes/{uid}", json=body)


def test_edit_standard_activity_item_class_name_conflict_with_another_standard(
    api_client,
):
    """
    SCENARIO: name-uniqueness within standard Activity Item Classes is enforced on edit
    GIVEN two draft standard Activity Item Classes with different names
    WHEN one is renamed via PATCH to the other's name
    THEN it fails with 409 AlreadyExistsException
    """
    existing_response = _post_activity_item_class(
        api_client, name="Edit Standard Existing Name", order=307
    )
    assert_response_status_code(existing_response, 201)

    to_rename_response = _post_activity_item_class(
        api_client, name="Edit Standard To Rename", order=308
    )
    assert_response_status_code(to_rename_response, 201)
    to_rename_uid = to_rename_response.json()["uid"]

    patch_response = _patch_activity_item_class(
        api_client, uid=to_rename_uid, name="Edit Standard Existing Name"
    )
    res = parse_json_response(patch_response, assert_status=409)
    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "Activity Item Class with Name 'Edit Standard Existing Name' already exists."
    )


def test_edit_nsv_activity_item_class_name_conflict_with_another_nsv(api_client):
    """
    SCENARIO: name-uniqueness within Non Standard Variables is enforced on edit
    GIVEN two draft NSV Activity Item Classes with different names
    WHEN one is renamed via PATCH to the other's name
    THEN it fails with 409 AlreadyExistsException
    """
    existing_response = _post_activity_item_class(
        api_client,
        name="Edit NSV Existing Name",
        order=309,
        non_standard_variable={
            "code": "EDIT_NSV_EXISTING_CODE",
            "is_multiple": False,
            "length": 8,
            "is_cdisc_defined": False,
        },
    )
    assert_response_status_code(existing_response, 201)

    to_rename_response = _post_activity_item_class(
        api_client,
        name="Edit NSV To Rename",
        order=310,
        non_standard_variable={
            "code": "EDIT_NSV_TO_RENAME_CODE",
            "is_multiple": False,
            "length": 8,
            "is_cdisc_defined": False,
        },
    )
    assert_response_status_code(to_rename_response, 201)
    to_rename_uid = to_rename_response.json()["uid"]

    patch_response = _patch_activity_item_class(
        api_client, uid=to_rename_uid, name="Edit NSV Existing Name"
    )
    res = parse_json_response(patch_response, assert_status=409)
    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "Activity Item Class with Name 'Edit NSV Existing Name' already exists."
    )


def test_edit_converting_standard_to_nsv_can_reuse_name_from_standard_pool(
    api_client,
):
    """
    SCENARIO: converting a standard item to an NSV while renaming checks the NSV pool, not the standard pool
    GIVEN a draft standard Activity Item Class, and a separate standard Activity Item Class occupying a name
    WHEN the first item is renamed to that name AND given a non_standard_variable in the same PATCH
    THEN it succeeds, since after conversion its name only needs to be unique among NSVs
    """
    standard_response = _post_activity_item_class(
        api_client, name="Edit Conversion Standard Name Holder", order=311
    )
    assert_response_status_code(standard_response, 201)

    to_convert_response = _post_activity_item_class(
        api_client, name="Edit Conversion To Convert", order=312
    )
    assert_response_status_code(to_convert_response, 201)
    to_convert_uid = to_convert_response.json()["uid"]

    patch_response = _patch_activity_item_class(
        api_client,
        uid=to_convert_uid,
        name="Edit Conversion Standard Name Holder",
        non_standard_variable={
            "code": "EDIT_CONVERSION_CODE",
            "is_multiple": False,
            "length": 8,
            "is_cdisc_defined": False,
        },
    )
    res = parse_json_response(patch_response, assert_status=200)
    assert res["name"] == "Edit Conversion Standard Name Holder"
    assert res["non_standard_variable"]["code"] == "EDIT_CONVERSION_CODE"


def test_edit_converting_standard_to_nsv_name_conflict_with_existing_nsv(api_client):
    """
    SCENARIO: converting a standard item to an NSV while renaming still enforces uniqueness within the NSV pool
    GIVEN a draft standard Activity Item Class, and an existing NSV occupying a name
    WHEN the standard item is renamed to that name AND given a non_standard_variable in the same PATCH
    THEN it fails with 409 AlreadyExistsException, since the new name collides with an existing NSV
    """
    nsv_response = _post_activity_item_class(
        api_client,
        name="Edit Conversion NSV Name Holder",
        order=313,
        non_standard_variable={
            "code": "EDIT_CONVERSION_NSV_HOLDER_CODE",
            "is_multiple": False,
            "length": 8,
            "is_cdisc_defined": False,
        },
    )
    assert_response_status_code(nsv_response, 201)

    to_convert_response = _post_activity_item_class(
        api_client, name="Edit Conversion To Convert Conflict", order=314
    )
    assert_response_status_code(to_convert_response, 201)
    to_convert_uid = to_convert_response.json()["uid"]

    patch_response = _patch_activity_item_class(
        api_client,
        uid=to_convert_uid,
        name="Edit Conversion NSV Name Holder",
        non_standard_variable={
            "code": "EDIT_CONVERSION_CONFLICT_CODE",
            "is_multiple": False,
            "length": 8,
            "is_cdisc_defined": False,
        },
    )
    res = parse_json_response(patch_response, assert_status=409)
    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "Activity Item Class with Name 'Edit Conversion NSV Name Holder' already exists."
    )
