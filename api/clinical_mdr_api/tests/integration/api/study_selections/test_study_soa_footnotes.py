"""
Tests for /studies/{study_uid}/study-soa-footnotes endpoints
"""

import copy
import json
import logging
from functools import reduce
from typing import Any
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.domains.enums import ValidationMode
from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
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
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpoch
from clinical_mdr_api.models.study_selections.study_selection import (
    ReferencedItem,
    StudyActivitySchedule,
    StudySelectionActivity,
)
from clinical_mdr_api.models.study_selections.study_soa_footnote import StudySoAFootnote
from clinical_mdr_api.models.study_selections.study_visit import StudyVisit
from clinical_mdr_api.models.syntax_instances.footnote import Footnote
from clinical_mdr_api.models.syntax_templates.footnote_template import FootnoteTemplate
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.factory_activity import (
    create_study_activity,
)
from clinical_mdr_api.tests.integration.utils.factory_epoch import create_study_epoch
from clinical_mdr_api.tests.integration.utils.factory_visit import (
    create_study_visit_codelists,
    generate_default_input_data_for_visit,
)
from clinical_mdr_api.tests.integration.utils.utils import PROJECT_NUMBER, TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study: Study
second_study: Study
footnotes: list[Footnote]
footnote_templates: list[FootnoteTemplate]
soa_footnotes: list[StudySoAFootnote]
ct_term_schedule_of_activities: CTTerm
dictionary_term_indication: DictionaryTerm
indications_codelist: DictionaryCodelist
indications_library_name: str
activity: Activity
activity_group: ActivityGroup
activity_subgroup: ActivitySubGroup
text_value_1: TextValue
text_value_2: TextValue
sa_randomized: StudySelectionActivity
randomized_sas: StudyActivitySchedule
sa_body_mes: StudySelectionActivity
body_mes_sas: StudyActivitySchedule
sa_weight: StudySelectionActivity
weight_sas: StudyActivitySchedule
study_epoch: StudyEpoch
first_visit: StudyVisit
second_visit: StudyVisit
new_soa_footnote_uid: str
test_data_dict: dict[str, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studysoafootnotesapi"
    inject_and_clear_db(db_name)
    global second_study, test_data_dict
    second_study, test_data_dict = inject_base_data()
    global study
    study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=study.uid)
    global footnotes
    global footnote_templates
    global soa_footnotes
    global ct_term_schedule_of_activities
    global dictionary_term_indication
    global indications_codelist
    global indications_library_name
    global activity
    global activity_group
    global activity_subgroup
    global text_value_1
    global text_value_2
    global sa_randomized
    global randomized_sas
    global sa_body_mes
    global body_mes_sas
    global sa_weight
    global weight_sas
    global study_epoch
    global first_visit
    global second_visit
    global sa_weight

    # Create Template Parameter
    TestUtils.create_template_parameter("TextValue")

    activity_group = TestUtils.create_activity_group(name="test activity group")
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="test activity subgroup"
    )
    activity = TestUtils.create_activity(
        name="test activity",
        library_name="Sponsor",
        activity_groups=[activity_group.uid],
        activity_subgroups=[activity_subgroup.uid],
    )

    text_value_1 = TestUtils.create_text_value()
    text_value_2 = TestUtils.create_text_value()

    type_codelist = TestUtils.create_ct_codelist(
        name="Footnote Type",
        submission_value="FTNTTP",
        extensible=True,
        approve=True,
    )

    # Create Dictionary/CT Terms
    ct_term_schedule_of_activities = TestUtils.create_ct_term(
        sponsor_preferred_name="Schedule of Activities",
        codelist_uid=type_codelist.codelist_uid,
    )
    flowchart_group_codelist = TestUtils.create_ct_codelist(
        sponsor_preferred_name="Flowchart Group",
        extensible=True,
        approve=True,
        submission_value="FLWCRTGRP",
    )
    flowchart_group = TestUtils.create_ct_term(
        sponsor_preferred_name="Subject Information",
        codelist_uid=flowchart_group_codelist.codelist_uid,
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

    footnote_templates = []
    footnote_templates.append(
        TestUtils.create_footnote_template(
            name="Default name with [TextValue]",
            study_uid=None,
            type_uid=ct_term_schedule_of_activities.term_uid,
            library_name="Sponsor",
            indication_uids=[dictionary_term_indication.term_uid],
            activity_uids=[activity.uid],
            activity_group_uids=[activity_group.uid],
            activity_subgroup_uids=[activity_subgroup.uid],
        )
    )
    footnote_templates.append(
        TestUtils.create_footnote_template(
            name="Another name with [TextValue]",
            study_uid=None,
            type_uid=ct_term_schedule_of_activities.term_uid,
            library_name="Sponsor",
            indication_uids=[dictionary_term_indication.term_uid],
            activity_uids=[activity.uid],
            activity_group_uids=[activity_group.uid],
            activity_subgroup_uids=[activity_subgroup.uid],
        )
    )
    # Create some footnote
    footnotes = []
    footnotes.append(
        TestUtils.create_footnote(
            footnote_template_uid=footnote_templates[0].uid,
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
            footnote_template_uid=footnote_templates[1].uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
        )
    )
    footnotes.append(
        TestUtils.create_footnote(
            footnote_template_uid=footnote_templates[1].uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            approve=False,
        )
    )
    TestUtils.create_ct_catalogue()
    # create epoch and visits
    create_study_visit_codelists(use_test_utils=True, create_unit_definitions=False)
    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=study.uid)
    visits_basic_data = generate_default_input_data_for_visit().copy()
    anchor_visit = visits_basic_data.copy()
    anchor_visit.update({"is_global_anchor_visit": True, "time_value": 0})
    first_visit = TestUtils.create_study_visit(
        study_uid=study.uid, study_epoch_uid=study_epoch.uid, **anchor_visit
    )
    second_visit = TestUtils.create_study_visit(
        study_uid=study.uid, study_epoch_uid=study_epoch.uid, **visits_basic_data
    )

    # create activities
    general_activity_group = TestUtils.create_activity_group(name="General")
    randomisation_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Randomisation"
    )
    randomized_activity = TestUtils.create_activity(
        name="Randomized",
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )

    # Randomized Study Activity
    sa_randomized = create_study_activity(
        study_uid=study.uid,
        activity_uid=randomized_activity.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=flowchart_group.term_uid,
    )
    randomized_sas = TestUtils.create_study_activity_schedule(
        study_uid=study.uid,
        study_activity_uid=sa_randomized.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )
    soa_footnotes = []
    randomized_sas_footnote = TestUtils.create_study_soa_footnote(
        study_uid=study.uid,
        footnote_template_uid=footnote_templates[0].uid,
        referenced_items=[
            ReferencedItem(
                item_uid=randomized_sas.study_activity_schedule_uid,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            )
        ],
    )
    soa_footnotes.append(randomized_sas_footnote)
    body_mes_activity = TestUtils.create_activity(
        name="Body Measurement activity",
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )
    sa_body_mes = create_study_activity(
        study_uid=study.uid,
        activity_uid=body_mes_activity.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=flowchart_group.term_uid,
    )
    body_mes_sas = TestUtils.create_study_activity_schedule(
        study_uid=study.uid,
        study_activity_uid=sa_body_mes.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )

    body_measurements_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Body Measurements"
    )
    weight_activity = TestUtils.create_activity(
        name="Weight",
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )

    # Weight Study Activity
    sa_weight = create_study_activity(
        study_uid=study.uid,
        activity_uid=weight_activity.uid,
        activity_subgroup_uid=body_measurements_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        soa_group_term_uid=flowchart_group.term_uid,
    )
    weight_sas = TestUtils.create_study_activity_schedule(
        study_uid=study.uid,
        study_activity_uid=sa_weight.study_activity_uid,
        study_visit_uid=second_visit.uid,
    )
    weight_sas_footnote = TestUtils.create_study_soa_footnote(
        study_uid=study.uid,
        footnote_template_uid=footnote_templates[1].uid,
        referenced_items=[
            ReferencedItem(
                item_uid=weight_sas.study_activity_schedule_uid,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            )
        ],
    )
    soa_footnotes.append(weight_sas_footnote)
    soa_footnote_to_delete = TestUtils.create_study_soa_footnote(
        study_uid=study.uid,
        footnote_template_uid=footnote_templates[1].uid,
        referenced_items=[
            ReferencedItem(
                item_uid=weight_sas.study_activity_schedule_uid,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            )
        ],
    )
    soa_footnotes.append(soa_footnote_to_delete)
    yield


@pytest.mark.order("last")
def test_integrity_checks_for_all_studies(api_client):
    """
    Test integrity checks for all available studies in the database.

    This test should always be executed at the END to check the health of the remaining database.
    It validates that all studies in the database pass integrity checks after all other tests have run.
    """
    TestUtils.run_integrity_checks_for_all_studies(
        api_client, mode=ValidationMode.WARNING
    )  # needs to be warning for now as it's leaving broken data


STUDY_FOOTNOTE_FIELDS_ALL = [
    "uid",
    "study_uid",
    "order",
    "footnote",
    "template",
    "referenced_items",
    "modified",
    "study_version",
    "accepted_version",
    "latest_footnote",
    "author_username",
    "layout",
]

STUDY_FOOTNOTE_FIELDS_NOT_NULL = [
    "uid",
    "study_uid",
    "order",
    "referenced_items",
    "modified",
    "accepted_version",
]

STUDY_FOOTNOTE_FIELDS_ALL_MINIMAL_RESPONSE = [
    "uid",
    "study_uid",
    "order",
    "referenced_items",
    "footnote",
    "template",
    "layout",
]

STUDY_FOOTNOTE_FIELDS_NOT_NULL_MINIMAL_RESPONSE = [
    "uid",
    "study_uid",
    "order",
    "referenced_items",
]


def test_get_study_soa_footnote(api_client):
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[0].uid}"
    )
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    fields_all_set = set(STUDY_FOOTNOTE_FIELDS_ALL)
    assert set(res.keys()) == fields_all_set
    for key in STUDY_FOOTNOTE_FIELDS_NOT_NULL:
        assert res[key] is not None
    assert res["uid"] == soa_footnotes[0].uid
    assert res["study_uid"] == study.uid
    assert res["order"] == 1
    assert len(res["referenced_items"]) == 1
    assert (
        res["referenced_items"][0]["item_uid"]
        == randomized_sas.study_activity_schedule_uid
    )
    assert (
        res["referenced_items"][0]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
    )
    assert res["template"]["uid"] == footnote_templates[0].uid


def test_get_study_soa_footnotes_minimal_response(api_client):
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes", params={"minimal_response": True}
    )
    assert_response_status_code(response, 200)

    study_soa_footnotes = response.json()["items"]
    for order, study_soa_footnote in enumerate(study_soa_footnotes, start=1):
        # Check fields included in the response
        fields_all_set = set(STUDY_FOOTNOTE_FIELDS_ALL_MINIMAL_RESPONSE)
        assert set(study_soa_footnote.keys()) == fields_all_set
        for key in STUDY_FOOTNOTE_FIELDS_NOT_NULL_MINIMAL_RESPONSE:
            assert study_soa_footnote[key] is not None
        assert study_soa_footnote["uid"] is not None
        assert study_soa_footnote["study_uid"] == study.uid
        assert study_soa_footnote["order"] == order
        for ref_item in study_soa_footnote["referenced_items"]:
            assert ref_item["item_uid"] is not None
            assert ref_item["item_type"] is not None
            assert "item_name" not in ref_item
            assert "visible_in_protocol_soa" not in ref_item

        assert study_soa_footnote["template"]["uid"] is not None
        assert study_soa_footnote["template"]["name"] is not None
        assert study_soa_footnote["template"]["name_plain"] is not None
        assert "library_name" not in study_soa_footnote["template"]
        assert "version" not in study_soa_footnote["template"]
        assert "parameters" not in study_soa_footnote["template"]

        assert "version" not in study_soa_footnote["template"]
        assert "library_name" not in study_soa_footnote["template"]
        assert "parameters" not in study_soa_footnote["template"]
        assert study_soa_footnote["footnote"] is None
        assert "latest_footnote" not in study_soa_footnote
        assert "modified" not in study_soa_footnote
        assert "accepted_version" not in study_soa_footnote
        assert "author_username" not in study_soa_footnote
        assert "study_version" not in study_soa_footnote


def test_get_soa_footnotes_pagination(api_client):
    url = f"/studies/{study.uid}/study-soa-footnotes"
    results_paginated: dict[Any, Any] = {}
    sort_by = '{"uid": true}'
    for page_number in range(1, 4):
        response = api_client.get(
            f"{url}?page_number={page_number}&page_size=10&sort_by={sort_by}"
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
        f"{url}?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = [item["uid"] for item in res_all["items"]]
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, True, None, 3),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 0),
        pytest.param(10, 2, True, None, 0),
        pytest.param(10, 3, True, None, 0),
        pytest.param(10, 1, True, '{"uid": false}', 3),
        pytest.param(10, 2, True, '{"uid": true}', 0),
    ],
)
def test_get_study_soa_footnotes(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = f"/studies/{study.uid}/study-soa-footnotes"
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
    assert res["total"] == (len(soa_footnotes) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(STUDY_FOOTNOTE_FIELDS_ALL)
        for key in STUDY_FOOTNOTE_FIELDS_NOT_NULL:
            assert item[key] is not None

    if sort_by:
        # sort_by is JSON string in the form: {"sort_field_name": is_ascending_order}
        sort_by_dict = json.loads(sort_by)
        sort_field: str = next(iter(sort_by_dict.keys()))
        sort_order_ascending: bool = next(iter(sort_by_dict.values()))

        # extract list of values of 'sort_field_name' field from the returned result
        result_vals = list(map(lambda x: x[sort_field], res["items"]))
        result_vals_sorted_locally = result_vals.copy()
        result_vals_sorted_locally.sort(reverse=not sort_order_ascending)
        # This assert fails due to API issue with sorting coupled with pagination
        # assert result_vals == result_vals_sorted_locally


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param(
            '{"*": {"v": ["FootnoteTemplate_000001"]}}',
            "template.uid",
            "FootnoteTemplate_000001",
        ),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"/studies/{study.uid}/study-soa-footnotes?filters={filter_by}"
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
            current_row = row
            if nested_path:
                for prop in nested_path:
                    current_row = current_row[prop]
            if isinstance(current_row, list):
                any(
                    item[expected_matched_field].startswith(expected_result_prefix)
                    for item in current_row
                )
            else:
                assert current_row[expected_matched_field].startswith(
                    expected_result_prefix
                )
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result",
    [
        pytest.param(
            '{"template.uid": {"v": ["FootnoteTemplate_000001"]}}',
            "template.uid",
            "FootnoteTemplate_000001",
        ),
        pytest.param(
            '{"referenced_items.item_uid": {"v": ["StudyActivitySchedule_000001"]}}',
            "referenced_items.item_uid",
            "StudyActivitySchedule_000001",
        ),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    url = f"/studies/{study.uid}/study-soa-footnotes?filters={filter_by}"
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
            current_row = row
            if nested_path:
                for prop in nested_path:
                    current_row = current_row[prop]
            if isinstance(expected_result, list):
                assert all(
                    item in current_row[expected_matched_field]
                    for item in expected_result
                )
            elif isinstance(current_row, list):
                all(
                    item[expected_matched_field] == expected_result
                    for item in current_row
                )
            else:
                assert current_row[expected_matched_field] == expected_result
    else:
        assert len(res["items"]) == 0


def test_footnote_reordering_when_adding_new_footnote(api_client):
    response = api_client.get(f"/studies/{study.uid}/study-soa-footnotes")
    assert_response_status_code(response, 200)
    res = response.json()["items"]

    assert len(res) == 3

    assert (
        res[0]["referenced_items"][0]["item_uid"]
        == randomized_sas.study_activity_schedule_uid
    )
    assert (
        res[0]["referenced_items"][0]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
    )
    assert res[0]["order"] == 1
    assert res[0]["template"]["uid"] == footnote_templates[0].uid

    assert (
        res[1]["referenced_items"][0]["item_uid"]
        == weight_sas.study_activity_schedule_uid
    )
    assert (
        res[1]["referenced_items"][0]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
    )
    assert res[1]["order"] == 2
    assert res[1]["template"]["uid"] == footnote_templates[1].uid

    body_mes_sas_footnote = TestUtils.create_study_soa_footnote(
        study_uid=study.uid,
        footnote_template_uid=footnote_templates[0].uid,
        referenced_items=[
            ReferencedItem(
                item_uid=body_mes_sas.study_activity_schedule_uid,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            )
        ],
    )

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{body_mes_sas_footnote.uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["order"] == 2

    response = api_client.get(f"/studies/{study.uid}/study-soa-footnotes")
    assert_response_status_code(response, 200)
    res = response.json()["items"]

    assert len(res) == 4

    assert (
        res[0]["referenced_items"][0]["item_uid"]
        == randomized_sas.study_activity_schedule_uid
    )
    assert (
        res[0]["referenced_items"][0]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
    )
    assert (
        res[0]["referenced_items"][0]["item_name"]
        == f"{sa_randomized.activity.name} {first_visit.visit_short_name}"
    )
    assert res[0]["template"]["uid"] == footnote_templates[0].uid
    assert res[0]["order"] == 1

    assert (
        res[1]["referenced_items"][0]["item_uid"]
        == body_mes_sas.study_activity_schedule_uid
    )
    assert (
        res[1]["referenced_items"][0]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
    )
    assert (
        res[1]["referenced_items"][0]["item_name"]
        == f"{sa_body_mes.activity.name} {first_visit.visit_short_name}"
    )
    assert res[1]["template"]["uid"] == footnote_templates[0].uid
    assert res[1]["order"] == 2

    assert (
        res[2]["referenced_items"][0]["item_uid"]
        == weight_sas.study_activity_schedule_uid
    )
    assert (
        res[2]["referenced_items"][0]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
    )
    assert (
        res[2]["referenced_items"][0]["item_name"]
        == f"{sa_weight.activity.name} {second_visit.visit_short_name}"
    )
    assert res[2]["template"]["uid"] == footnote_templates[1].uid
    assert res[2]["order"] == 3


def test_edit(api_client):
    response = api_client.patch(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[0].uid}",
        json={"footnote_template_uid": footnote_templates[1].uid},
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[0].uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["template"]["uid"] == footnote_templates[1].uid

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[1].uid}"
    )

    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["referenced_items"][0]["item_uid"] == weight_sas.study_activity_schedule_uid
    )
    assert (
        res["referenced_items"][0]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
    )

    response = api_client.patch(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[1].uid}",
        json={
            "referenced_items": [
                {
                    "item_uid": first_visit.uid,
                    "item_type": SoAItemType.STUDY_VISIT.value,
                }
            ]
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.get(f"/studies/{study.uid}/study-soa-footnotes")
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res[0]["referenced_items"][0]["item_uid"] == first_visit.uid
    assert res[0]["referenced_items"][0]["item_type"] == SoAItemType.STUDY_VISIT.value
    for order, soa_footnote in enumerate(res, start=1):
        assert soa_footnote["order"] == order

    TestUtils.create_study_soa_footnote(
        study_uid=study.uid,
        footnote_template_uid=footnote_templates[0].uid,
        referenced_items=[
            ReferencedItem(
                item_uid=study_epoch.uid,
                item_type=SoAItemType.STUDY_EPOCH,
            )
        ],
    )

    response = api_client.get(f"/studies/{study.uid}/study-soa-footnotes")
    assert_response_status_code(response, 200)
    res = response.json()["items"]
    assert res[0]["referenced_items"][0]["item_uid"] == study_epoch.uid
    assert res[0]["referenced_items"][0]["item_type"] == SoAItemType.STUDY_EPOCH.value
    for order, soa_footnote in enumerate(res, start=1):
        assert soa_footnote["order"] == order


def test_delete(api_client):
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[2].uid}"
    )
    assert_response_status_code(response, 200)

    response = api_client.delete(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[2].uid}"
    )
    assert_response_status_code(response, 204)

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[2].uid}"
    )
    assert_response_status_code(response, 404)

    response = api_client.get(f"/studies/{study.uid}/study-soa-footnotes")
    assert_response_status_code(response, 200)
    res = response.json()["items"]

    # removed the first element make sure that the orders are reassigned
    assert res[0]["order"] == 1


def test_batch_create(api_client):
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes?total_count=True"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    amount_of_soa_footnotes = res["total"]

    text_value1 = TestUtils.create_text_value()
    text_value2 = TestUtils.create_text_value()

    batch_input = [
        {
            "footnote_data": {
                "footnote_template_uid": footnote_templates[0].uid,
                "library_name": "Sponsor",
                "parameter_terms": [
                    {
                        "position": 1,
                        "conjunction": "",
                        "terms": [
                            {
                                "index": 1,
                                "name": text_value1.name,
                                "uid": text_value1.uid,
                                "type": "TextValue",
                            }
                        ],
                    }
                ],
            },
            "referenced_items": [],
        },
        {
            "footnote_data": {
                "footnote_template_uid": footnote_templates[1].uid,
                "library_name": "Sponsor",
                "parameter_terms": [
                    {
                        "position": 1,
                        "conjunction": "",
                        "terms": [
                            {
                                "index": 1,
                                "name": text_value2.name,
                                "uid": text_value2.uid,
                                "type": "TextValue",
                            }
                        ],
                    }
                ],
            },
            "referenced_items": [],
        },
    ]
    response = api_client.post(
        f"/studies/{study.uid}/study-soa-footnotes/batch-select",
        json=batch_input,
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes?total_count=True"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["total"] == amount_of_soa_footnotes + len(batch_input)
    for idx, soa_footnote in enumerate(res["items"], start=1):
        assert soa_footnote["order"] == idx


def test_get_all_across_studies(api_client):
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes?total_count=True"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    total_in_first_study = res["total"]

    response = api_client.get(
        f"/studies/{second_study.uid}/study-soa-footnotes?total_count=True"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    total_in_second_study = res["total"]

    response = api_client.get("/study-soa-footnotes?total_count=True")
    assert_response_status_code(response, 200)
    res = response.json()
    total_across_studies = res["total"]
    assert total_across_studies == total_in_second_study + total_in_first_study


def test_preview_study_soa_footnote(api_client):
    text_value1 = TestUtils.create_text_value()
    response = api_client.post(
        f"/studies/{second_study.uid}/study-soa-footnotes/preview",
        json={
            "footnote_data": {
                "footnote_template_uid": footnote_templates[0].uid,
                "library_name": "Sponsor",
                "parameter_terms": [
                    {
                        "position": 1,
                        "conjunction": "",
                        "terms": [
                            {
                                "index": 1,
                                "name": text_value1.name,
                                "uid": text_value1.uid,
                                "type": "TextValue",
                            }
                        ],
                    }
                ],
            },
            "referenced_items": [],
        },
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["footnote"]["template_uid"] == footnote_templates[0].uid
    assert res["footnote"]["name_plain"] == footnote_templates[0].name.replace(
        "[TextValue]", text_value1.name_sentence_case
    )


@pytest.mark.parametrize(
    "field_name",
    [
        pytest.param("order"),
        pytest.param("footnote.uid"),
        pytest.param("template.uid"),
    ],
)
def test_headers(api_client, field_name):
    url = f"/studies/{study.uid}/study-soa-footnotes/headers?field_name={field_name}&page_size=100"
    response = api_client.get(
        url,
    )
    res = response.json()

    assert_response_status_code(response, 200)
    expected_result = []

    nested_path = None
    if isinstance(field_name, str) and "." in field_name:
        nested_path = field_name.split(".")
        expected_matched_field = nested_path[-1]
        nested_path = nested_path[:-1]
    all_soa_footnotes = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes"
    ).json()["items"]
    for study_soa_footnote in all_soa_footnotes:
        current_study_soa_footnote = study_soa_footnote
        if nested_path:
            for prop in nested_path:
                current_study_soa_footnote = current_study_soa_footnote.get(prop)
            if not current_study_soa_footnote:
                continue
            if isinstance(current_study_soa_footnote, list):
                for item in current_study_soa_footnote:
                    value = item.get(expected_matched_field)
                    expected_result.append(value)
            else:
                value = current_study_soa_footnote.get(expected_matched_field)
                expected_result.append(value)

        else:
            value = study_soa_footnote.get(field_name)
            expected_result.append(value)
    expected_result = [result for result in expected_result if result is not None]
    log.info("Expected result is %s", expected_result)
    log.info("Returned %s", res)
    if expected_result:
        assert len(res) > 0
        assert len(set(expected_result)) == len(res)
        assert all(item in res for item in expected_result)
    else:
        assert len(res) == 0


def test_audit_trail_specific_soa_footnote(api_client):
    text_value1 = TestUtils.create_text_value()
    response = api_client.post(
        f"/studies/{study.uid}/study-soa-footnotes",
        params={"create_footnote": True},
        json={
            "footnote_data": {
                "footnote_template_uid": footnote_templates[0].uid,
                "library_name": "Sponsor",
                "parameter_terms": [
                    {
                        "position": 1,
                        "conjunction": "",
                        "terms": [
                            {
                                "index": 1,
                                "name": text_value1.name,
                                "uid": text_value1.uid,
                                "type": "TextValue",
                            }
                        ],
                    }
                ],
            },
            "referenced_items": [],
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    uid = res["uid"]
    global new_soa_footnote_uid
    new_soa_footnote_uid = uid

    response = api_client.patch(
        f"/studies/{study.uid}/study-soa-footnotes/{uid}",
        json={
            "referenced_items": [
                {
                    "item_uid": first_visit.uid,
                    "item_type": SoAItemType.STUDY_VISIT.value,
                }
            ]
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{uid}/audit-trail"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert len(res) == 2
    assert set(res[0]["changes"]) == set(
        ["referenced_items", "change_type", "start_date", "end_date"]
    )
    assert res[1]["changes"] == []


def test_add_footnotes_to_subgroup_and_group(api_client):
    soa_footnote = TestUtils.create_study_soa_footnote(
        study_uid=study.uid,
        footnote_template_uid=footnote_templates[1].uid,
        referenced_items=[
            ReferencedItem(
                item_uid=sa_weight.study_activity_subgroup.study_activity_subgroup_uid,
                item_type=SoAItemType.STUDY_ACTIVITY_SUBGROUP,
            ),
            ReferencedItem(
                item_uid=sa_weight.study_activity_group.study_activity_group_uid,
                item_type=SoAItemType.STUDY_ACTIVITY_GROUP,
            ),
        ],
    )
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnote.uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert (
        res["referenced_items"][0]["item_uid"]
        == sa_weight.study_activity_subgroup.study_activity_subgroup_uid
    )
    assert (
        res["referenced_items"][0]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_SUBGROUP.value
    )
    assert (
        res["referenced_items"][1]["item_uid"]
        == sa_weight.study_activity_group.study_activity_group_uid
    )
    assert (
        res["referenced_items"][1]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_GROUP.value
    )

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes",
    )
    assert_response_status_code(response, 200)


def test_modify_actions_on_locked_study(api_client):
    _study_epoch = create_study_epoch("EpochSubType_0002", study_uid=study.uid)
    text_value_2_name = "test-2ndname"
    # change footnote name and approve the version
    response = api_client.post(
        f"/footnote-templates/{footnote_templates[0].uid}/versions",
        json={
            "change_description": "test change",
            "name": text_value_2_name,
            "guidance_text": "don't know",
        },
    )
    assert_response_status_code(response, 201)
    response = api_client.post(
        f"/footnote-templates/{footnote_templates[0].uid}/approvals?cascade=true"
    )
    assert_response_status_code(response, 201)

    study_soa_footnote_uid = soa_footnotes[0].uid

    response = api_client.patch(
        f"/studies/{study.uid}/study-soa-footnotes/{study_soa_footnote_uid}",
        json={
            "referenced_items": [
                {
                    "item_uid": first_visit.uid,
                    "item_type": SoAItemType.STUDY_VISIT.value,
                },
                {
                    "item_uid": _study_epoch.uid,
                    "item_type": SoAItemType.STUDY_EPOCH.value,
                },
                {
                    "item_uid": sa_randomized.study_activity_uid,
                    "item_type": SoAItemType.STUDY_ACTIVITY.value,
                },
                {
                    "item_uid": weight_sas.study_activity_schedule_uid,
                    "item_type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
                },
            ]
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["referenced_items"] == [
        {
            "item_name": None,
            "item_type": "StudyVisit",
            "item_uid": first_visit.uid,
            "visible_in_protocol_soa": None,
        },
        {
            "item_name": None,
            "item_type": "StudyEpoch",
            "item_uid": _study_epoch.uid,
            "visible_in_protocol_soa": None,
        },
        {
            "item_name": None,
            "item_type": "StudyActivity",
            "item_uid": sa_randomized.study_activity_uid,
            "visible_in_protocol_soa": None,
        },
        {
            "item_name": None,
            "item_type": "StudyActivitySchedule",
            "item_uid": weight_sas.study_activity_schedule_uid,
            "visible_in_protocol_soa": None,
        },
    ]

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{study_soa_footnote_uid}"
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock = res
    assert res["referenced_items"] == [
        {
            "item_name": "Epoch Subtype1",
            "item_type": "StudyEpoch",
            "item_uid": _study_epoch.uid,
            "visible_in_protocol_soa": True,
        },
        {
            "item_name": "Randomized",
            "item_type": "StudyActivity",
            "item_uid": sa_randomized.study_activity_uid,
            "visible_in_protocol_soa": False,
        },
        {
            "item_name": "V1",
            "item_type": "StudyVisit",
            "item_uid": first_visit.uid,
            "visible_in_protocol_soa": True,
        },
        {
            "item_name": "Weight V2",
            "item_type": "StudyActivitySchedule",
            "item_uid": weight_sas.study_activity_schedule_uid,
            "visible_in_protocol_soa": False,
        },
    ]

    response = api_client.get(
        f"/studies/{study.uid}/study-visits/{first_visit.uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock_visit = res

    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/{_study_epoch.uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock_epoch = res

    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{sa_randomized.study_activity_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock_activity = res

    response = api_client.get(
        f"/studies/{study.uid}/study-activity-schedules",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock_activity_schedule = res

    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks",
        json={
            "change_description": "Lock 1",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # test cannot delete
    response = api_client.delete(
        f"/studies/{study.uid}/study-soa-footnotes/{study_soa_footnote_uid}"
    )
    assert_response_status_code(response, 400)
    assert response.json()["message"] == f"Study with UID '{study.uid}' is locked."

    # Unlock
    response = api_client.post(
        f"/studies/{study.uid}/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": test_data_dict["reason_for_unlock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    # edit study soa footnote
    response = api_client.patch(
        f"/studies/{study.uid}/study-soa-footnotes/{study_soa_footnote_uid}",
        json={
            "referenced_items": [
                {
                    "item_uid": second_visit.uid,
                    "item_type": SoAItemType.STUDY_VISIT.value,
                }
            ]
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["referenced_items"] == [
        {
            "item_name": None,
            "item_type": "StudyVisit",
            "item_uid": second_visit.uid,
            "visible_in_protocol_soa": mock.ANY,
        },
    ]

    response = api_client.delete(
        f"/studies/{study.uid}/study-visits/{first_visit.uid}",
    )
    assert_response_status_code(response, 204)

    response = api_client.delete(
        f"/studies/{study.uid}/study-epochs/{_study_epoch.uid}",
    )
    assert_response_status_code(response, 204)

    # deleting a study activity
    response = api_client.delete(
        f"/studies/{study.uid}/study-activities/{sa_randomized.study_activity_uid}",
    )
    assert_response_status_code(response, 204)
    # NOTE: the footnote's referenced_items for the locked version (study_value_version=1)
    # must keep the reference to sa_randomized even after it is deleted here on the
    # draft - referenced-item membership for a historical snapshot is determined by the
    # snapshot's own HAS_STUDY_ACTIVITY edge, not by whether the live draft still has it.

    response = api_client.delete(
        f"/studies/{study.uid}/study-activity-schedules/{weight_sas.study_activity_schedule_uid}",
    )
    assert_response_status_code(response, 204)

    # get all study soa footnotes of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock["study_version"] = mock.ANY

    to_compare = next(
        item for item in res["items"] if item["uid"] == before_unlock["uid"]
    )
    assert to_compare == before_unlock

    # get specific study soa footnote of a specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{study_soa_footnote_uid}?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == before_unlock

    # get study soa footnote headers of specific study version
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/headers?field_name=referenced_items.item_name&study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    header_items = [
        "Epoch Subtype",
        "V1",
        "Epoch Subtype1",
        "Randomized",
        "Weight V2",
        "Body Measurements",
        "General",
        "Body Measurement activity V1",
    ]
    assert set(res) == set(header_items)

    response = api_client.get(
        f"/studies/{study.uid}/study-visits/{first_visit.uid}?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock_visit["study_version"] = mock.ANY
    assert res == before_unlock_visit

    response = api_client.get(
        f"/studies/{study.uid}/study-epochs/{_study_epoch.uid}?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock_epoch["study_version"] = mock.ANY
    assert res == before_unlock_epoch

    response = api_client.get(
        f"/studies/{study.uid}/study-activities/{sa_randomized.study_activity_uid}?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    before_unlock_activity["study_version"] = mock.ANY
    assert res == before_unlock_activity

    response = api_client.get(
        f"/studies/{study.uid}/study-activity-schedules?study_value_version=1",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == before_unlock_activity_schedule

    # get all study soa footnotes
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    to_compare = next(
        item for item in res["items"] if item["uid"] == study_soa_footnote_uid
    )
    assert to_compare["referenced_items"] == [
        {
            "item_name": "V1",
            "item_type": "StudyVisit",
            "item_uid": second_visit.uid,
            "visible_in_protocol_soa": mock.ANY,
        },
    ]

    # get specific study soa footnote
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{study_soa_footnote_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["referenced_items"] == [
        {
            "item_name": "V1",
            "item_type": "StudyVisit",
            "item_uid": second_visit.uid,
            "visible_in_protocol_soa": mock.ANY,
        },
    ]

    # get study soa footnote headers
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/headers?field_name=referenced_items.item_name",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res == ["Epoch Subtype", "V1", "Body Measurements", "General"]


def test_update_footnote_library_items_of_relationship_to_value_nodes(api_client):
    """
    Test that the StudySoAFootnote selection remains connected to the specific Value node even if the Value node is not latest anymore.

    StudySoAFootnote is connected to value nodes:
    - FootnoteTemplate
    """
    study_soa_footnote_uid = new_soa_footnote_uid
    # get specific study soa footnote
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{study_soa_footnote_uid}",
    )
    assert_response_status_code(response, 200)
    res = response.json()
    library_template_footnote_uid = res["footnote"]["template_uid"]
    initial_footnote_name = res["footnote"]["name"]

    text_value_2_name = "3rdname"
    # change footnote name and approve the version
    response = api_client.post(
        f"/footnote-templates/{library_template_footnote_uid}/versions",
        json={
            "change_description": "test change",
            "name": text_value_2_name,
            "guidance_text": "don't know",
        },
    )
    response = api_client.post(
        f"/footnote-templates/{library_template_footnote_uid}/approvals?cascade=true"
    )

    # check that the Library item has been changed
    response = api_client.get(f"/footnote-templates/{library_template_footnote_uid}")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["name"] == text_value_2_name

    # check that the StudySelection StudySoAFootnote hasn't been updated
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{study_soa_footnote_uid}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["footnote"]["name"] == initial_footnote_name
    assert res["template"] is None

    # check that the StudySelection can approve the current version
    response = api_client.post(
        f"/studies/{study.uid}/study-soa-footnotes/{study_soa_footnote_uid}/accept-version",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["accepted_version"] is True

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{study_soa_footnote_uid}/audit-trail"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    counting_before_sync = len(res)

    # check that the StudySelection's Footnote can be updated to the LATEST
    response = api_client.post(
        f"/studies/{study.uid}/study-soa-footnotes/{study_soa_footnote_uid}/sync-latest-version",
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{study_soa_footnote_uid}/audit-trail"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res) == counting_before_sync + 1

    study_cloned = api_client.post(
        f"/studies/{study.uid}/clone",
        json={
            "study_number": "6675",
            "study_acronym": "6675",
            "project_number": PROJECT_NUMBER,
            "description": "6675",
            "copy_study_arm": True,
            "copy_study_branch_arm": True,
            "copy_study_cohort": True,
            "copy_study_element": True,
            "copy_study_visit": False,
            "copy_study_epoch": True,
            "copy_study_visits_study_footnote": False,
            "copy_study_epochs_study_footnote": True,
            "copy_study_design_matrix": True,
            "copy_study_soa_group": True,
            "copy_study_activity_group": False,
            "copy_study_activity_subgroup": False,
            "copy_study_activity": False,
            "copy_study_activity_instance": False,
            "copy_study_activity_schedule": False,
            "validation_mode": ValidationMode.WARNING.value,  # TODO: FIX DELETION, FAILING ON INTEGRITY CHECK
        },
    ).json()
    # get all
    cloned_footnotes = api_client.get(
        f"/studies/{study_cloned['uid']}/study-soa-footnotes"
    ).json()
    cloned_footnotes_any = copy.deepcopy(cloned_footnotes)
    for i, _ in enumerate(cloned_footnotes_any["items"]):
        cloned_footnotes_any["items"][i]["study_version"] = mock.ANY
        cloned_footnotes_any["items"][i]["study_uid"] = mock.ANY
        cloned_footnotes_any["items"][i]["modified"] = mock.ANY
        cloned_footnotes_any["items"][i]["uid"] = mock.ANY
        cloned_footnotes_any["items"][i]["order"] = mock.ANY
        for j, __ in enumerate(cloned_footnotes_any["items"][i]["referenced_items"]):
            cloned_footnotes_any["items"][i]["referenced_items"][j][
                "item_uid"
            ] = mock.ANY
    # Fetch footnotes for the original study
    final_footnotes = api_client.get(f"/studies/{study.uid}/study-soa-footnotes").json()

    # Standardize original footnotes and filter unwanted items
    normalized_footnotes = []
    for footnote in final_footnotes["items"]:
        if footnote["uid"] in ["StudySoAFootnote_000003", "StudySoAFootnote_000004"]:
            continue  # Skip specific footnote
        if [
            True
            for item in footnote["referenced_items"]
            if item["item_type"] in {"StudyActivityGroup", "StudyVisit"}
        ]:
            continue
        footnote.update(
            {
                "study_version": mock.ANY,
                "study_uid": mock.ANY,
                "modified": mock.ANY,
                "uid": mock.ANY,
                "order": mock.ANY,
            }
        )

        footnote["referenced_items"] = [
            {**item, "item_uid": mock.ANY}
            for item in footnote["referenced_items"]
            if item["item_type"] not in {"StudyActivityGroup", "StudyVisit"}
        ]

        normalized_footnotes.append(footnote)

    # Assign filtered list back to final_footnotes
    final_footnotes["items"] = normalized_footnotes

    # Validate that the cloned study matches the original after processing
    for idx, cloned_footnote in enumerate(cloned_footnotes_any["items"]):
        # If original Footnote referenced some items, the order must be same in the cloned Study
        if cloned_footnote["referenced_items"]:
            assert cloned_footnote == final_footnotes["items"][idx]
        # If original Footnote did not referenced any items the order does not have to be reflected in the cloned Study
        # but it must exist in the cloned Study
        else:
            assert cloned_footnote in final_footnotes["items"]

    study_cloned = api_client.post(
        f"/studies/{study.uid}/clone",
        json={
            "study_number": "6676",
            "study_acronym": "6676",
            "project_number": PROJECT_NUMBER,
            "description": "6676",
            "copy_study_arm": True,
            "copy_study_branch_arm": True,
            "copy_study_cohort": True,
            "copy_study_element": True,
            "copy_study_visit": False,
            "copy_study_epoch": False,
            "copy_study_visits_study_footnote": False,
            "copy_study_epochs_study_footnote": False,
            "copy_study_design_matrix": False,
            "copy_study_soa_group": False,
            "copy_study_activity_group": False,
            "copy_study_activity_subgroup": False,
            "copy_study_activity": False,
            "copy_study_activity_instance": False,
            "copy_study_activity_schedule": False,
            "validation_mode": ValidationMode.WARNING.value,  # TODO: FIX DELETION, FAILING ON INTEGRITY CHECK
        },
    ).json()
    # get all
    cloned_footnotes = api_client.get(
        f"/studies/{study_cloned['uid']}/study-soa-footnotes"
    ).json()
    assert cloned_footnotes["items"] == []

    study_cloned = api_client.post(
        f"/studies/{study.uid}/clone",
        json={
            "study_number": "6677",
            "study_acronym": "6677",
            "project_number": PROJECT_NUMBER,
            "description": "6677",
            "copy_study_arm": True,
            "copy_study_branch_arm": True,
            "copy_study_cohort": True,
            "copy_study_element": True,
            "copy_study_visit": True,
            "copy_study_epoch": True,
            "copy_study_visits_study_footnote": True,
            "copy_study_epochs_study_footnote": True,
            "copy_study_design_matrix": True,
            "copy_study_soa_group": True,
            "copy_study_activity_group": True,
            "copy_study_activity_subgroup": True,
            "copy_study_activity": True,
            "copy_study_activity_instance": True,
            "copy_study_activity_schedule": True,
            "validation_mode": ValidationMode.WARNING.value,  # TODO: FIX DELETION, FAILING ON INTEGRITY CHECK
        },
    ).json()
    # get all
    cloned_footnotes = api_client.get(
        f"/studies/{study_cloned['uid']}/study-soa-footnotes"
    ).json()
    _activity_ref_types = {
        "StudyActivityGroup",
        "StudyActivitySubGroup",
        "StudyActivity",
        "StudyActivityInstance",
        "StudyActivitySchedule",
    }
    cloned_footnotes_any = copy.deepcopy(cloned_footnotes)
    for i, _ in enumerate(cloned_footnotes_any["items"]):
        cloned_footnotes_any["items"][i]["study_version"] = mock.ANY
        cloned_footnotes_any["items"][i]["study_uid"] = mock.ANY
        cloned_footnotes_any["items"][i]["modified"] = mock.ANY
        cloned_footnotes_any["items"][i]["uid"] = mock.ANY
        cloned_footnotes_any["items"][i]["order"] = mock.ANY
        cloned_footnotes_any["items"][i]["template"] = mock.ANY
        for j, __ in enumerate(cloned_footnotes_any["items"][i]["referenced_items"]):
            cloned_footnotes_any["items"][i]["referenced_items"][j][
                "item_uid"
            ] = mock.ANY
        cloned_footnotes_any["items"][i]["referenced_items"] = [
            {**item, "item_uid": mock.ANY, "visible_in_protocol_soa": mock.ANY}
            for item in cloned_footnotes_any["items"][i]["referenced_items"]
            if item["item_type"] not in _activity_ref_types
        ]
    # Fetch footnotes for the original study
    final_footnotes = api_client.get(f"/studies/{study.uid}/study-soa-footnotes").json()

    # Standardize original footnotes and filter unwanted items
    normalized_footnotes = []
    for footnote in final_footnotes["items"]:
        if footnote["uid"] in ["StudySoAFootnote_000003", "StudySoAFootnote_000004"]:
            continue  # Skip specific footnote
        if [
            True
            for item in footnote["referenced_items"]
            if item["item_type"] in _activity_ref_types
        ]:
            continue
        footnote.update(
            {
                "study_version": mock.ANY,
                "study_uid": mock.ANY,
                "modified": mock.ANY,
                "uid": mock.ANY,
                "order": mock.ANY,
                "template": mock.ANY,
            }
        )

        footnote["referenced_items"] = [
            {**item, "item_uid": mock.ANY, "visible_in_protocol_soa": mock.ANY}
            for item in footnote["referenced_items"]
            if item["item_type"] not in _activity_ref_types
        ]

        normalized_footnotes.append(footnote)

    # Assign filtered list back to final_footnotes
    final_footnotes["items"] = normalized_footnotes
    # Validate that the cloned study matches the original after processing
    for idx, cloned_footnote in enumerate(cloned_footnotes_any["items"]):
        # If original Footnote referenced some items, the order must be same in the cloned Study
        if cloned_footnote["referenced_items"]:
            assert cloned_footnote == final_footnotes["items"][idx]
        # If original Footnote did not referenced any items the order does not have to be reflected in the cloned Study
        # but it must exist in the cloned Study
        else:
            assert cloned_footnote in final_footnotes["items"]


def _create_layout_footnote(api_client, study_uid, layout=None):
    """Create a template-based Study SoA footnote, optionally connected to a layout."""
    body: dict[str, Any] = {
        "footnote_template_uid": footnote_templates[0].uid,
        "referenced_items": [],
    }
    if layout is not None:
        body["layout"] = layout
    response = api_client.post(
        f"/studies/{study_uid}/study-soa-footnotes",
        params={"create_footnote": False},
        json=body,
    )
    assert_response_status_code(response, 201)
    return response.json()


def test_create_footnote_with_layout(api_client):
    """POST accepts and persists the layout field, GET returns it."""
    layout_study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=layout_study.uid)

    res = _create_layout_footnote(api_client, layout_study.uid, layout="protocol")
    footnote_uid = res["uid"]
    assert res["layout"] == "protocol"

    response = api_client.get(
        f"/studies/{layout_study.uid}/study-soa-footnotes/{footnote_uid}"
    )
    assert_response_status_code(response, 200)
    assert response.json()["layout"] == "protocol"


def test_create_footnote_without_layout_defaults_to_none(api_client):
    """A footnote created without a layout has layout None (applies to all layouts)."""
    layout_study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=layout_study.uid)

    res = _create_layout_footnote(api_client, layout_study.uid, layout=None)
    assert res["layout"] is None


@pytest.mark.parametrize("layout", ["not_a_layout", "", "PROTOCOL"])
def test_create_footnote_with_invalid_layout_is_rejected(api_client, layout):
    """The layout field only accepts the SoALayout enum values."""
    layout_study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=layout_study.uid)

    response = api_client.post(
        f"/studies/{layout_study.uid}/study-soa-footnotes",
        params={"create_footnote": False},
        json={
            "footnote_template_uid": footnote_templates[0].uid,
            "referenced_items": [],
            "layout": layout,
        },
    )
    # The app maps request-body validation errors to HTTP 400 (RequestValidationError handler).
    assert_response_status_code(response, 400)


def test_edit_footnote_layout(api_client):
    """PATCH updates the layout and preserves it when it is not provided."""
    layout_study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=layout_study.uid)

    footnote_uid = _create_layout_footnote(
        api_client, layout_study.uid, layout="detailed"
    )["uid"]

    # Changing the layout is reflected
    response = api_client.patch(
        f"/studies/{layout_study.uid}/study-soa-footnotes/{footnote_uid}",
        json={"layout": "protocol_lab_table"},
    )
    assert_response_status_code(response, 200)
    assert response.json()["layout"] == "protocol_lab_table"

    # Editing another field without passing layout keeps the current layout
    response = api_client.patch(
        f"/studies/{layout_study.uid}/study-soa-footnotes/{footnote_uid}",
        json={"footnote_template_uid": footnote_templates[1].uid},
    )
    assert_response_status_code(response, 200)
    assert response.json()["layout"] == "protocol_lab_table"


def test_create_footnote_with_underlying_footnote_and_layout(api_client):
    """The create_footnote=True path also persists the layout."""
    layout_study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=layout_study.uid)
    text_value = TestUtils.create_text_value()

    response = api_client.post(
        f"/studies/{layout_study.uid}/study-soa-footnotes",
        params={"create_footnote": True},
        json={
            "footnote_data": {
                "footnote_template_uid": footnote_templates[0].uid,
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
            },
            "referenced_items": [],
            "layout": "operational",
        },
    )
    assert_response_status_code(response, 201)
    assert response.json()["layout"] == "operational"


def test_get_footnotes_filtered_by_layout(api_client):
    """The layout query parameter returns matching footnotes plus those with no layout."""
    layout_study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=layout_study.uid)

    uid_protocol = _create_layout_footnote(
        api_client, layout_study.uid, layout="protocol"
    )["uid"]
    uid_lab = _create_layout_footnote(
        api_client, layout_study.uid, layout="protocol_lab_table"
    )["uid"]
    uid_none = _create_layout_footnote(api_client, layout_study.uid, layout=None)["uid"]

    def get_uids(query=""):
        response = api_client.get(
            f"/studies/{layout_study.uid}/study-soa-footnotes{query}"
        )
        assert_response_status_code(response, 200)
        return {item["uid"] for item in response.json()["items"]}

    # layout=protocol -> protocol-specific + no-layout, but not lab-table
    uids = get_uids("?layout=protocol")
    assert uid_protocol in uids
    assert uid_none in uids
    assert uid_lab not in uids

    # layout=protocol_lab_table -> lab-table-specific + no-layout, but not protocol
    uids = get_uids("?layout=protocol_lab_table")
    assert uid_lab in uids
    assert uid_none in uids
    assert uid_protocol not in uids

    # layout=detailed -> only the no-layout footnote (no detailed-specific footnote exists)
    uids = get_uids("?layout=detailed")
    assert uids == {uid_none}

    # no layout parameter -> all footnotes returned
    uids = get_uids()
    assert {uid_protocol, uid_lab, uid_none} == uids


def test_get_footnotes_filtered_by_layout_orders_are_contiguous(api_client):
    """Order numbers stay contiguous (1..N) within a layout-filtered result, no gaps."""
    layout_study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=layout_study.uid)

    # Interleave layouts so the full-list positions of the 'protocol' subset are non-consecutive
    _create_layout_footnote(api_client, layout_study.uid, layout="detailed")
    _create_layout_footnote(api_client, layout_study.uid, layout="protocol")
    _create_layout_footnote(api_client, layout_study.uid, layout="detailed")
    _create_layout_footnote(api_client, layout_study.uid, layout="protocol")
    _create_layout_footnote(api_client, layout_study.uid, layout=None)

    response = api_client.get(
        f"/studies/{layout_study.uid}/study-soa-footnotes?layout=protocol"
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]

    # protocol (2) + no-layout (1) = 3 footnotes, numbered 1, 2, 3 with no gaps
    orders = [item["order"] for item in items]
    assert orders == list(range(1, len(items) + 1))


def test_get_footnotes_filtered_by_layout_total_count(api_client):
    """Pagination total_count reflects the layout-filtered set."""
    layout_study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=layout_study.uid)

    _create_layout_footnote(api_client, layout_study.uid, layout="protocol")
    _create_layout_footnote(api_client, layout_study.uid, layout="detailed")
    _create_layout_footnote(api_client, layout_study.uid, layout=None)

    # protocol + no-layout = 2 of the 3 footnotes
    response = api_client.get(
        f"/studies/{layout_study.uid}/study-soa-footnotes"
        "?layout=protocol&total_count=true"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["total"] == 2
    assert len(res["items"]) == 2
    for item in res["items"]:
        assert item["layout"] in ("protocol", None)


def test_get_footnotes_across_studies_filtered_by_layout(api_client):
    """The all-studies endpoint also applies the layout filter."""
    layout_study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=layout_study.uid)

    _create_layout_footnote(api_client, layout_study.uid, layout="protocol")
    _create_layout_footnote(api_client, layout_study.uid, layout="protocol_lab_table")
    _create_layout_footnote(api_client, layout_study.uid, layout=None)

    response = api_client.get("/study-soa-footnotes?layout=protocol")
    assert_response_status_code(response, 200)
    for item in response.json()["items"]:
        assert item["layout"] in ("protocol", None)


def test_get_footnotes_minimal_response_includes_layout(api_client):
    """The minimal response exposes the layout field and honors the layout filter."""
    layout_study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=layout_study.uid)

    uid_protocol = _create_layout_footnote(
        api_client, layout_study.uid, layout="protocol"
    )["uid"]
    _create_layout_footnote(api_client, layout_study.uid, layout="detailed")

    response = api_client.get(
        f"/studies/{layout_study.uid}/study-soa-footnotes",
        params={"minimal_response": True, "layout": "protocol"},
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]

    # Only the protocol footnote matches (no no-layout footnote exists here)
    assert {item["uid"] for item in items} == {uid_protocol}
    assert all("layout" in item for item in items)
    assert items[0]["layout"] == "protocol"


def _create_footnote_data_payload(text_value, template_uid):
    return {
        "footnote_data": {
            "footnote_template_uid": template_uid,
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
        },
        "referenced_items": [],
    }


def test_batch_select_footnotes_with_layout(api_client):
    """Batch-select persists the layout on each created footnote."""
    layout_study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=layout_study.uid)
    text_value1 = TestUtils.create_text_value()
    text_value2 = TestUtils.create_text_value()

    item_with_layout = _create_footnote_data_payload(
        text_value1, footnote_templates[0].uid
    )
    item_with_layout["layout"] = "protocol"
    item_without_layout = _create_footnote_data_payload(
        text_value2, footnote_templates[1].uid
    )

    response = api_client.post(
        f"/studies/{layout_study.uid}/study-soa-footnotes/batch-select",
        json=[item_with_layout, item_without_layout],
    )
    assert_response_status_code(response, 201)
    created = response.json()

    assert {c["layout"] for c in created} == {"protocol", None}


def test_batch_edit_footnotes_layout(api_client):
    """Batch-edit updates the layout of study SoA footnotes."""
    layout_study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=layout_study.uid)

    uid1 = _create_layout_footnote(api_client, layout_study.uid, layout="protocol")[
        "uid"
    ]
    uid2 = _create_layout_footnote(api_client, layout_study.uid, layout=None)["uid"]

    response = api_client.patch(
        f"/studies/{layout_study.uid}/study-soa-footnotes/batch-edit",
        json=[
            {"study_soa_footnote_uid": uid1, "layout": "detailed"},
            {"study_soa_footnote_uid": uid2, "layout": "operational"},
        ],
    )
    assert_response_status_code(response, 207)
    results = response.json()

    layout_by_uid = {r["content"]["uid"]: r["content"]["layout"] for r in results}
    assert layout_by_uid[uid1] == "detailed"
    assert layout_by_uid[uid2] == "operational"


def test_audit_trail_records_layout_change(api_client):
    """Changing a footnote's layout is captured in its audit trail."""
    layout_study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=layout_study.uid)

    uid = _create_layout_footnote(api_client, layout_study.uid, layout="protocol")[
        "uid"
    ]

    response = api_client.patch(
        f"/studies/{layout_study.uid}/study-soa-footnotes/{uid}",
        json={"layout": "detailed"},
    )
    assert_response_status_code(response, 200)

    response = api_client.get(
        f"/studies/{layout_study.uid}/study-soa-footnotes/{uid}/audit-trail"
    )
    assert_response_status_code(response, 200)
    res = response.json()

    assert len(res) == 2
    # Newest version records the layout change; oldest is the creation baseline
    assert "layout" in res[0]["changes"]
    assert res[0]["layout"] == "detailed"
    assert res[1]["layout"] == "protocol"


def test_create_footnote_with_retired_template_is_rejected(api_client):
    """Selecting a Retired footnote template returns 400 naming the template and its status."""
    retired_study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=retired_study.uid)
    retired_template = TestUtils.create_footnote_template(
        name="Retired template with [TextValue]",
        study_uid=None,
        type_uid=ct_term_schedule_of_activities.term_uid,
        library_name="Sponsor",
        indication_uids=[dictionary_term_indication.term_uid],
    )
    response = api_client.delete(
        f"/footnote-templates/{retired_template.uid}/activations"
    )
    assert_response_status_code(response, 200)
    assert response.json()["status"] == "Retired"

    response = api_client.post(
        f"/studies/{retired_study.uid}/study-soa-footnotes",
        params={"create_footnote": False},
        json={
            "footnote_template_uid": retired_template.uid,
            "referenced_items": [],
        },
    )
    assert_response_status_code(response, 400)
    message = response.json()["message"]
    assert retired_template.uid in message
    assert "Retired" in message


def test_delete_footnote_on_template_with_retirement_history(api_client):
    """A footnote whose template was retired after creation can still be deleted.

    Retiring the template adds a second value node at the same version (1.0),
    which previously raised MultipleNodesReturned and stranded the footnote.
    """
    del_study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=del_study.uid)
    template = TestUtils.create_footnote_template(
        name="Deletable template with [TextValue]",
        study_uid=None,
        type_uid=ct_term_schedule_of_activities.term_uid,
        library_name="Sponsor",
        indication_uids=[dictionary_term_indication.term_uid],
    )
    # Create the study footnote while the template is Final
    response = api_client.post(
        f"/studies/{del_study.uid}/study-soa-footnotes",
        params={"create_footnote": False},
        json={"footnote_template_uid": template.uid, "referenced_items": []},
    )
    assert_response_status_code(response, 201)
    footnote_uid = response.json()["uid"]

    # Retire the template -> adds a second value node at the same version number
    response = api_client.delete(f"/footnote-templates/{template.uid}/activations")
    assert_response_status_code(response, 200)

    response = api_client.delete(
        f"/studies/{del_study.uid}/study-soa-footnotes/{footnote_uid}"
    )
    assert_response_status_code(response, 204)
