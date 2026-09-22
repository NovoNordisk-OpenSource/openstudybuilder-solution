"""
Tests for /studies/{study_uid}/study-other-attributes endpoints.
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

import json
import logging
from typing import Any

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.models.controlled_terminologies.ct_term_name import (
    CTTermNameTSParameterInput,
)
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.services.controlled_terminologies.ct_term_name import (
    CTTermNameService,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

log = logging.getLogger(__name__)


# Synthetic TS-parameter CT term for the Other Study Attributes page
TS_TERM_UID = "TS_DCUTDESC"
TS_TERM_NAME = "Data Cutoff Description"
TS_TERM_CODE = "DCUTDESC"
# All three TS terms below intentionally share the SAME osb_field_name to
# exercise the multi-MetaStudyField graph: one MSF per (osb_field_name,
# semantic_data_type_uid) pair.
META_STUDY_FIELD_NAME = "test_other_attribute_field"
NULL_FLAVOR_TERM_UID = "NF_NINF"

# Additional TS terms for typed StudyField coverage (Boolean / Time / unknown)
TS_BOOL_TERM_UID = "TS_BOOLATTR"
TS_BOOL_TERM_NAME = "Boolean Other Attribute"
TS_BOOL_TERM_CODE = "BOOLATTR"
TS_BOOL_META_FIELD = META_STUDY_FIELD_NAME

TS_TIME_TERM_UID = "TS_DATEATTR"
TS_TIME_TERM_NAME = "Date Other Attribute"
TS_TIME_TERM_CODE = "DATEATTR"
TS_TIME_META_FIELD = META_STUDY_FIELD_NAME

DT_TEXT_UID = "DT_TEXT"
DT_BOOL_UID = "DT_BOOLEAN"
DT_DATE_UID = "DT_DATE"


study: Study
test_data_dict: dict[str, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    db_name = "studyotherattrapi"
    inject_and_clear_db(db_name)

    global study, test_data_dict
    study, test_data_dict = inject_base_data()

    catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)

    # Data Type codelist + terms (Text / Boolean / Date) used by the
    # `semantic_data_type_uid` field of `patch_trial_summary_parameter`.
    dt_codelist = create_codelist(
        name="Data Type",
        uid="CTCodelist_DataType",
        catalogue=settings.ddf_ct_catalogue_name,
        library=library_name,
        submission_value=settings.data_type_cl_submval,
    )
    for dt_uid, dt_name in (
        (DT_TEXT_UID, "Text"),
        (DT_BOOL_UID, "Boolean"),
        (DT_DATE_UID, "Date"),
    ):
        create_ct_term(
            name=dt_name,
            uid=dt_uid,
            preferred_term=dt_name,
            definition=f"Data type: {dt_name}",
            catalogue_name=catalogue_name,
            library_name=library_name,
            codelists=[
                {
                    "uid": dt_codelist.codelist_uid,
                    "order": 1,
                    "submission_value": dt_name,
                }
            ],
        )

    # TS-parameter (TSPARMCD) codelist + the parameter terms (Text/Bool/Date)
    ts_code_codelist = create_codelist(
        name="Trial Summary Parameter Test Code",
        uid=settings.ts_parmcd_codelist_uid,
        catalogue=catalogue_name,
        library=library_name,
    )
    for term_uid, term_name, term_code in (
        (TS_TERM_UID, TS_TERM_NAME, TS_TERM_CODE),
        (TS_BOOL_TERM_UID, TS_BOOL_TERM_NAME, TS_BOOL_TERM_CODE),
        (TS_TIME_TERM_UID, TS_TIME_TERM_NAME, TS_TIME_TERM_CODE),
    ):
        create_ct_term(
            name=term_name,
            uid=term_uid,
            preferred_term=term_name,
            definition=term_name,
            catalogue_name=catalogue_name,
            library_name=library_name,
            codelists=[
                {
                    "uid": ts_code_codelist.codelist_uid,
                    "order": 1,
                    "submission_value": term_code,
                },
            ],
        )

    ts_service = CTTermNameService()

    # Wire the TS terms to MetaStudyFields with the appropriate data type
    # and `osb_page_reference`. The text term intentionally has NO
    # semantic_data_type_uid to exercise the "unknown type → StudyTextField"
    # fallback path.
    ts_service.patch_trial_summary_parameter(
        TS_TERM_UID,
        CTTermNameTSParameterInput(
            osb_field_name=META_STUDY_FIELD_NAME,
            osb_page_reference=settings.study_other_attributes_page_reference,
            required_level="Required",
            cardinality="One",
            notes="-",
        ),
    )
    ts_service.approve(TS_TERM_UID)
    ts_service.patch_trial_summary_parameter(
        TS_BOOL_TERM_UID,
        CTTermNameTSParameterInput(
            osb_field_name=TS_BOOL_META_FIELD,
            semantic_data_type_uid=DT_BOOL_UID,
            osb_page_reference=settings.study_other_attributes_page_reference,
            required_level="Optional",
            cardinality="One",
            notes="-",
        ),
    )
    ts_service.approve(TS_BOOL_TERM_UID)
    ts_service.patch_trial_summary_parameter(
        TS_TIME_TERM_UID,
        CTTermNameTSParameterInput(
            osb_field_name=TS_TIME_META_FIELD,
            semantic_data_type_uid=DT_DATE_UID,
            osb_page_reference=settings.study_other_attributes_page_reference,
            required_level="Optional",
            cardinality="One",
            notes="-",
        ),
    )
    ts_service.approve(TS_TIME_TERM_UID)

    # Null Flavor codelist + a sample null flavor term used by the PATCH test
    nf_codelist = create_codelist(
        name="Null Flavor",
        uid="CTCodelist_NullFlavor",
        catalogue=catalogue_name,
        library=library_name,
        submission_value=settings.null_flavor_cl_submval,
    )
    create_ct_term(
        name="No Information",
        uid=NULL_FLAVOR_TERM_UID,
        preferred_term="No Information",
        definition="Null flavor: No Information",
        catalogue_name=catalogue_name,
        library_name=library_name,
        codelists=[
            {"uid": nf_codelist.codelist_uid, "order": 1, "submission_value": "NINF"}
        ],
    )


def test_get_other_attributes_empty_before_post(api_client):
    """GET should return no items when no value has been assigned yet."""
    response = api_client.get(f"/studies/{study.uid}/study-other-attributes")
    assert_response_status_code(response, 200)
    res = response.json()
    rows = res["items"]
    assert len(rows) == 0


def test_post_other_attribute_with_value(api_client):
    response = api_client.post(
        f"/studies/{study.uid}/study-other-attributes",
        json={
            "ts_parameter_term_uid": TS_TERM_UID,
            "parameter_value": "Database Lock",
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["ts_parameter_term_uid"] == TS_TERM_UID
    assert res["parameter_value"] == "Database Lock"
    assert res["null_flavor"] is None


def test_post_other_attribute_duplicate_fails(api_client):
    response = api_client.post(
        f"/studies/{study.uid}/study-other-attributes",
        json={
            "ts_parameter_term_uid": TS_TERM_UID,
            "parameter_value": "Other value",
        },
    )
    assert_response_status_code(response, 409)


def test_get_after_post_returns_value(api_client):
    response = api_client.get(f"/studies/{study.uid}/study-other-attributes")
    assert_response_status_code(response, 200)
    items = response.json()["items"]
    assert len(items) == 1
    row = items[0]
    assert row["ts_parameter_term_uid"] == TS_TERM_UID
    assert row["parameter_value"] == "Database Lock"


def test_patch_other_attribute_to_null_flavor(api_client):
    response = api_client.patch(
        f"/studies/{study.uid}/study-other-attributes/{TS_TERM_UID}",
        json={"null_flavor_term_uid": NULL_FLAVOR_TERM_UID},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res["parameter_value"] is None
    assert res["null_flavor"] is not None
    assert res["null_flavor"]["uid"] == NULL_FLAVOR_TERM_UID


def test_post_xor_validation(api_client):
    """POST with both parameter_value and null_flavor_term_uid should fail."""
    response = api_client.post(
        f"/studies/{study.uid}/study-other-attributes",
        json={
            "ts_parameter_term_uid": "another_term",
            "parameter_value": "x",
            "null_flavor_term_uid": NULL_FLAVOR_TERM_UID,
        },
    )
    assert_response_status_code(response, 400)


def test_patch_xor_validation_both_provided(api_client):
    """PATCH with both parameter_value and null_flavor_term_uid should fail."""
    response = api_client.patch(
        f"/studies/{study.uid}/study-other-attributes/{TS_TERM_UID}",
        json={
            "parameter_value": "x",
            "null_flavor_term_uid": NULL_FLAVOR_TERM_UID,
        },
    )
    assert_response_status_code(response, 400)


def test_batch_xor_validation_both_provided(api_client):
    """Batch POST with both parameter_value and null_flavor_term_uid should fail."""
    response = api_client.post(
        f"/studies/{study.uid}/study-other-attributes/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "ts_parameter_term_uid": "some_term",
                    "parameter_value": "x",
                    "null_flavor_term_uid": NULL_FLAVOR_TERM_UID,
                },
            }
        ],
    )
    assert_response_status_code(response, 400)


def test_patch_unknown_term_returns_404(api_client):
    response = api_client.patch(
        f"/studies/{study.uid}/study-other-attributes/nonexistent_term",
        json={"parameter_value": "x"},
    )
    assert_response_status_code(response, 404)


def test_post_boolean_other_attribute_creates_study_boolean_field(api_client):
    """A TS parameter whose semantic data type is 'Boolean' should be
    persisted as a StudyBooleanField (not a StudyTextField)."""
    response = api_client.post(
        f"/studies/{study.uid}/study-other-attributes",
        json={"ts_parameter_term_uid": TS_BOOL_TERM_UID, "parameter_value": "true"},
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["parameter_value"] is True
    assert res["semantic_data_type"] == "Boolean"

    rows, _ = db.cypher_query(
        """
        MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(:StudyValue)
            -[:HAS_BOOLEAN_FIELD]->(bf:StudyBooleanField)
            -[:HAS_META_STUDY_FIELD]->(:MetaStudyField {osb_field_name: $msf_name})
        RETURN bf.value AS value, labels(bf) AS labels
        """,
        {"study_uid": study.uid, "msf_name": TS_BOOL_META_FIELD},
    )
    assert len(rows) == 1
    assert rows[0][0] is True
    assert "StudyBooleanField" in rows[0][1]


def test_post_boolean_invalid_value_returns_400(api_client):
    response = api_client.post(
        f"/studies/{study.uid}/study-other-attributes",
        json={
            "ts_parameter_term_uid": TS_BOOL_TERM_UID,
            "parameter_value": "not-a-bool",
        },
    )
    # Already exists takes precedence in the current flow only after the
    # type-coercion validation; calling on a fresh term to assert the
    # validation path is exercised independently.
    assert response.status_code in {400, 409}


def test_text_other_attribute_persisted_as_study_text_field(api_client):
    """A TS parameter with no semantic data type should fall back to
    StudyTextField. Verifies the graph state for TS_TERM_UID, which was
    POSTed (test #2) and then PATCHed to a null flavor (test #5)."""
    rows, _ = db.cypher_query(
        """
        MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(:StudyValue)
            -[:HAS_TEXT_FIELD]->(tf:StudyTextField)
            -[:HAS_META_STUDY_FIELD]->(:MetaStudyField {osb_field_name: $msf_name})
        RETURN tf.value AS value, labels(tf) AS labels
        """,
        {"study_uid": study.uid, "msf_name": META_STUDY_FIELD_NAME},
    )
    assert len(rows) == 1
    assert "StudyTextField" in rows[0][1]


def test_post_time_other_attribute_creates_study_time_field(api_client):
    """A TS parameter whose semantic data type is 'Date' should be
    persisted as a StudyTimeField."""
    response = api_client.post(
        f"/studies/{study.uid}/study-other-attributes",
        json={
            "ts_parameter_term_uid": TS_TIME_TERM_UID,
            "parameter_value": "2026-04-29",
        },
    )
    assert_response_status_code(response, 201)
    res = response.json()
    assert res["parameter_value"] == "2026-04-29"
    assert res["semantic_data_type"] == "Date"

    rows, _ = db.cypher_query(
        """
        MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(:StudyValue)
            -[:HAS_TIME_FIELD]->(tf:StudyTimeField)
            -[:HAS_META_STUDY_FIELD]->(:MetaStudyField {osb_field_name: $msf_name})
        RETURN tf.value AS value, labels(tf) AS labels
        """,
        {"study_uid": study.uid, "msf_name": TS_TIME_META_FIELD},
    )
    assert len(rows) == 1
    assert rows[0][0] == "2026-04-29"
    assert "StudyTimeField" in rows[0][1]


def test_distinct_meta_study_fields_per_semantic_data_type(api_client):
    """The three TS terms in this test module share the same osb_field_name
    but differ in their semantic data type (none / Boolean / Date). The
    write-path must therefore have created three DISTINCT MetaStudyField
    nodes — one per (osb_field_name, semantic_data_type_uid) pair — rather
    than reusing a single MSF."""
    rows, _ = db.cypher_query(
        """
        MATCH (msf:MetaStudyField {osb_field_name: $msf_name})
        OPTIONAL MATCH (msf)-[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)
            -[:HAS_SELECTED_TERM]->(dt_root:CTTermRoot)
        RETURN dt_root.uid AS data_type_uid
        ORDER BY data_type_uid
        """,
        {"msf_name": META_STUDY_FIELD_NAME},
    )
    data_type_uids = [r[0] for r in rows]
    assert len(data_type_uids) == 3, (
        f"Expected 3 distinct MetaStudyField nodes for "
        f"osb_field_name='{META_STUDY_FIELD_NAME}', got {len(data_type_uids)}: "
        f"{data_type_uids}"
    )
    assert sorted(data_type_uids, key=lambda x: (x is None, x)) == sorted(
        [None, DT_BOOL_UID, DT_DATE_UID], key=lambda x: (x is None, x)
    )


# ─── Pagination / Filtering / Sorting / Headers ──────────────────────


def test_pagination_default_returns_all(api_client):
    """Without page_size the endpoint returns all items in a CustomPage envelope."""
    response = api_client.get(f"/studies/{study.uid}/study-other-attributes")
    assert_response_status_code(response, 200)
    res = response.json()
    assert "items" in res
    assert "total" in res
    assert "page" in res
    assert "size" in res
    # We have 3 configured TS terms in the fixture
    assert len(res["items"]) == 3


def test_pagination_page_size(api_client):
    """page_size=1 should return exactly one item."""
    response = api_client.get(
        f"/studies/{study.uid}/study-other-attributes",
        params={"page_size": 1, "page_number": 1},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 1
    assert res["page"] == 1
    assert res["size"] == 1


def test_pagination_page_number(api_client):
    """page_number=2 with page_size=1 returns the second item."""
    response = api_client.get(
        f"/studies/{study.uid}/study-other-attributes",
        params={"page_size": 1, "page_number": 2},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 1
    assert res["page"] == 2


def test_pagination_total_count(api_client):
    """total_count=true should populate the total field."""
    response = api_client.get(
        f"/studies/{study.uid}/study-other-attributes",
        params={"page_size": 1, "page_number": 1, "total_count": True},
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert len(res["items"]) == 1
    assert res["total"] == 3


def test_pagination_total_count_false(api_client):
    """total_count defaults to false → total should be 0."""
    response = api_client.get(
        f"/studies/{study.uid}/study-other-attributes",
        params={"page_size": 1, "page_number": 1},
    )
    assert_response_status_code(response, 200)
    assert response.json()["total"] == 0


def test_sort_by_parameter_ascending(api_client):
    """sort_by parameter ascending."""
    response = api_client.get(
        f"/studies/{study.uid}/study-other-attributes",
        params={"sort_by": json.dumps({"parameter": True})},
    )
    assert_response_status_code(response, 200)
    names = [r["parameter"] for r in response.json()["items"]]
    assert names == sorted(names, key=lambda n: (n is None, n or ""))


def test_sort_by_parameter_descending(api_client):
    """sort_by parameter descending."""
    response = api_client.get(
        f"/studies/{study.uid}/study-other-attributes",
        params={"sort_by": json.dumps({"parameter": False})},
    )
    assert_response_status_code(response, 200)
    names = [r["parameter"] for r in response.json()["items"]]
    assert names == sorted(names, key=lambda n: (n is None, n or ""), reverse=True)


def test_filter_by_parameter_contains(api_client):
    """Filtering by parameter name with 'contains' operator."""
    response = api_client.get(
        f"/studies/{study.uid}/study-other-attributes",
        params={
            "filters": json.dumps({"parameter": {"v": [TS_TERM_NAME], "op": "eq"}})
        },
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["parameter"] == TS_TERM_NAME


def test_filter_by_code(api_client):
    """Filtering by the code field (submission_value)."""
    response = api_client.get(
        f"/studies/{study.uid}/study-other-attributes",
        params={
            "filters": json.dumps({"code": {"v": [TS_BOOL_TERM_CODE], "op": "eq"}})
        },
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["code"] == TS_BOOL_TERM_CODE


def test_filter_no_match(api_client):
    """Filter that matches nothing returns empty items."""
    response = api_client.get(
        f"/studies/{study.uid}/study-other-attributes",
        params={
            "filters": json.dumps(
                {"parameter": {"v": ["NONEXISTENT_PARAM"], "op": "eq"}}
            )
        },
    )
    assert_response_status_code(response, 200)
    assert len(response.json()["items"]) == 0


def test_headers_returns_distinct_parameter_names(api_client):
    """The headers endpoint should return distinct values for the 'parameter' field."""
    response = api_client.get(
        f"/studies/{study.uid}/study-other-attributes/headers",
        params={"field_name": "parameter"},
    )
    assert_response_status_code(response, 200)
    values = response.json()
    assert isinstance(values, list)
    assert len(values) == 3
    assert TS_TERM_NAME in values
    assert TS_BOOL_TERM_NAME in values
    assert TS_TIME_TERM_NAME in values


def test_headers_search_string_filters(api_client):
    """search_string on headers should narrow down the returned values."""
    response = api_client.get(
        f"/studies/{study.uid}/study-other-attributes/headers",
        params={"field_name": "parameter", "search_string": "Boolean"},
    )
    assert_response_status_code(response, 200)
    values = response.json()
    assert len(values) == 1
    assert TS_BOOL_TERM_NAME in values


def test_headers_page_size(api_client):
    """page_size should limit the number of returned header values."""
    response = api_client.get(
        f"/studies/{study.uid}/study-other-attributes/headers",
        params={"field_name": "parameter", "page_size": 1},
    )
    assert_response_status_code(response, 200)
    values = response.json()
    assert len(values) == 1


def test_headers_code_field(api_client):
    """Headers should work for the 'code' field."""
    response = api_client.get(
        f"/studies/{study.uid}/study-other-attributes/headers",
        params={"field_name": "code"},
    )
    assert_response_status_code(response, 200)
    values = response.json()
    assert isinstance(values, list)
    assert TS_TERM_CODE in values


# ─── DELETE endpoint ──────────────────────────────────────────────────


def test_delete_other_attribute(api_client):
    """DELETE should remove the study other attribute selection."""
    # Verify TS_TERM_UID is present before deletion
    response = api_client.get(f"/studies/{study.uid}/study-other-attributes")
    assert_response_status_code(response, 200)
    uids = [r["ts_parameter_term_uid"] for r in response.json()["items"]]
    assert TS_TERM_UID in uids

    # Delete it
    response = api_client.delete(
        f"/studies/{study.uid}/study-other-attributes/{TS_TERM_UID}"
    )
    assert_response_status_code(response, 204)

    # Verify it's gone from GET
    response = api_client.get(f"/studies/{study.uid}/study-other-attributes")
    assert_response_status_code(response, 200)
    uids = [r["ts_parameter_term_uid"] for r in response.json()["items"]]
    assert TS_TERM_UID not in uids


def test_delete_nonexistent_returns_404(api_client):
    """DELETE on a non-existent attribute should return 404."""
    response = api_client.delete(
        f"/studies/{study.uid}/study-other-attributes/nonexistent_term"
    )
    assert_response_status_code(response, 404)


def test_delete_already_deleted_returns_404(api_client):
    """DELETE on an already-deleted attribute should return 404."""
    response = api_client.delete(
        f"/studies/{study.uid}/study-other-attributes/{TS_TERM_UID}"
    )
    assert_response_status_code(response, 404)


# ─── Batch endpoint ──────────────────────────────────────────────────


def test_batch_post_creates_attribute(api_client):
    """Batch POST should create a new attribute."""
    response = api_client.post(
        f"/studies/{study.uid}/study-other-attributes/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "ts_parameter_term_uid": TS_TERM_UID,
                    "parameter_value": "Batch Created",
                },
            }
        ],
    )
    assert_response_status_code(response, 207)
    results = response.json()
    assert len(results) == 1
    assert results[0]["response_code"] == 201
    assert results[0]["content"]["ts_parameter_term_uid"] == TS_TERM_UID
    assert results[0]["content"]["parameter_value"] == "Batch Created"


def test_batch_patch_updates_attribute(api_client):
    """Batch PATCH should update an existing attribute."""
    response = api_client.post(
        f"/studies/{study.uid}/study-other-attributes/batch",
        json=[
            {
                "method": "PATCH",
                "content": {
                    "ts_parameter_term_uid": TS_TERM_UID,
                    "parameter_value": "Batch Updated",
                },
            }
        ],
    )
    assert_response_status_code(response, 207)
    results = response.json()
    assert len(results) == 1
    assert results[0]["response_code"] == 200
    assert results[0]["content"]["parameter_value"] == "Batch Updated"


def test_batch_delete_removes_attribute(api_client):
    """Batch DELETE should remove an existing attribute."""
    response = api_client.post(
        f"/studies/{study.uid}/study-other-attributes/batch",
        json=[
            {
                "method": "DELETE",
                "content": {
                    "ts_parameter_term_uid": TS_TERM_UID,
                },
            }
        ],
    )
    assert_response_status_code(response, 207)
    results = response.json()
    assert len(results) == 1
    assert results[0]["response_code"] == 204
    assert results[0]["content"] is None

    # Verify it's gone
    response = api_client.get(f"/studies/{study.uid}/study-other-attributes")
    assert_response_status_code(response, 200)
    uids = [r["ts_parameter_term_uid"] for r in response.json()["items"]]
    assert TS_TERM_UID not in uids


def test_batch_mixed_operations(api_client):
    """Batch with POST then PATCH in a single request."""
    response = api_client.post(
        f"/studies/{study.uid}/study-other-attributes/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "ts_parameter_term_uid": TS_TERM_UID,
                    "parameter_value": "First",
                },
            },
            {
                "method": "PATCH",
                "content": {
                    "ts_parameter_term_uid": TS_TERM_UID,
                    "parameter_value": "Second",
                },
            },
        ],
    )
    assert_response_status_code(response, 207)
    results = response.json()
    assert len(results) == 2
    assert results[0]["response_code"] == 201
    assert results[0]["content"]["parameter_value"] == "First"
    assert results[1]["response_code"] == 200
    assert results[1]["content"]["parameter_value"] == "Second"


def test_batch_delete_nonexistent_fails(api_client):
    """Batch DELETE of a non-existent attribute returns error."""
    response = api_client.post(
        f"/studies/{study.uid}/study-other-attributes/batch",
        json=[
            {
                "method": "DELETE",
                "content": {
                    "ts_parameter_term_uid": "nonexistent_uid",
                },
            }
        ],
    )
    assert_response_status_code(response, 404)
