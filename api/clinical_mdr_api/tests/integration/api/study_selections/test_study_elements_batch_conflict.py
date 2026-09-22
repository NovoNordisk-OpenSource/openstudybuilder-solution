"""
Tests for study element batch POST skip deduplication and copy-from-study endpoint.
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

import logging
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.models.controlled_terminologies import ct_term
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

log = logging.getLogger(__name__)

run_in_subtype: ct_term.CTTerm
treatment_subtype: ct_term.CTTerm


@pytest.fixture(scope="module")
def api_client():
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    db_name = "studyelementbatchconflictapi"
    inject_and_clear_db(db_name)

    global run_in_subtype, treatment_subtype
    inject_base_data()

    _catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    catalogue_name = "SDTM CT"
    ct_term_codelist = create_codelist(
        settings.study_element_subtype_name,
        "CTCodelist_ElementSubType_BatchConflict",
        catalogue_name,
        library_name,
        submission_value=settings.study_element_subtype_cl_submval,
    )

    run_in_subtype = TestUtils.create_ct_term(
        codelist_uid=ct_term_codelist.codelist_uid,
        submission_value="Run-in Period",
        sponsor_preferred_name="Run-in Period",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=datetime(2020, 3, 25, tzinfo=timezone.utc),
        approve=True,
    )
    treatment_subtype = TestUtils.create_ct_term(
        codelist_uid=ct_term_codelist.codelist_uid,
        submission_value="Treatment Period",
        sponsor_preferred_name="Treatment Period",
        order=2,
        catalogue_name=catalogue_name,
        library_name=library_name,
        effective_date=datetime(2020, 3, 25, tzinfo=timezone.utc),
        approve=True,
    )

    for term in (run_in_subtype, treatment_subtype):
        db.cypher_query(
            """
            MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTTermNameRoot)-[has_version:HAS_VERSION]-(val)
            WHERE n.uid = $uid AND EXISTS((ct_name)-[:LATEST]-(val))
              AND has_version.status = 'Final'
            SET has_version.start_date = $date
            """,
            params={
                "uid": term.term_uid,
                "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
            },
        )

    db.cypher_query(
        """
        MATCH (n)-[:HAS_ATTRIBUTES_ROOT]-(attr:CTCodelistAttributesRoot)-[has_version:HAS_VERSION]-(val)
        WHERE n.uid = $uid AND EXISTS((attr)-[:LATEST]-(val))
          AND has_version.status = 'Final'
        SET has_version.start_date = $date
        """,
        params={
            "uid": ct_term_codelist.codelist_uid,
            "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
        },
    )


@pytest.fixture(scope="module")
def element_subtypes(test_data):
    yield {
        "run_in": run_in_subtype,
        "treatment": treatment_subtype,
    }


def _post_batch(api_client, study_uid: str, payload: list[dict[str, Any]]):
    return api_client.post(f"/studies/{study_uid}/study-elements/batch", json=payload)


def test_batch_post_creates_three_unique_elements(api_client, element_subtypes):
    target_study = TestUtils.create_study()
    subtype_uid = element_subtypes["run_in"].term_uid

    response = _post_batch(
        api_client,
        target_study.uid,
        [
            {
                "method": "POST",
                "content": {
                    "name": "MCPElemBatch1",
                    "short_name": "MCPBE1",
                    "element_subtype_uid": subtype_uid,
                },
            },
            {
                "method": "POST",
                "content": {
                    "name": "MCPElemBatch2",
                    "short_name": "MCPBE2",
                    "element_subtype_uid": subtype_uid,
                },
            },
            {
                "method": "POST",
                "content": {
                    "name": "MCPElemBatch3",
                    "short_name": "MCPBE3",
                    "element_subtype_uid": subtype_uid,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert len(res) == 3
    assert all(item["response_code"] == 201 for item in res)


def test_batch_post_skip_by_name_and_element_subtype(api_client, element_subtypes):
    target_study = TestUtils.create_study()
    subtype_uid = element_subtypes["run_in"].term_uid
    TestUtils.create_study_element(
        study_uid=target_study.uid,
        name="MCPElemSkipName",
        short_name="MCPESN1",
        element_subtype_uid=subtype_uid,
    )

    response = _post_batch(
        api_client,
        target_study.uid,
        [
            {
                "method": "POST",
                "content": {
                    "name": "MCPElemSkipName",
                    "short_name": "MCPESN2",
                    "element_subtype_uid": subtype_uid,
                },
            }
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert res[0]["response_code"] == 200
    assert "creation skipped" in res[0]["notification"]
    assert res[0]["content"]["name"] == "MCPElemSkipName"


def test_batch_post_skip_by_short_name_and_element_subtype(
    api_client, element_subtypes
):
    target_study = TestUtils.create_study()
    subtype_uid = element_subtypes["run_in"].term_uid
    TestUtils.create_study_element(
        study_uid=target_study.uid,
        name="MCPElemSkipShort1",
        short_name="MCPESS",
        element_subtype_uid=subtype_uid,
    )

    response = _post_batch(
        api_client,
        target_study.uid,
        [
            {
                "method": "POST",
                "content": {
                    "name": "MCPElemSkipShort2",
                    "short_name": "MCPESS",
                    "element_subtype_uid": subtype_uid,
                },
            }
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert res[0]["response_code"] == 200
    assert "creation skipped" in res[0]["notification"]
    assert res[0]["content"]["short_name"] == "MCPESS"


def test_batch_post_same_name_different_subtype_creates(api_client, element_subtypes):
    target_study = TestUtils.create_study()
    TestUtils.create_study_element(
        study_uid=target_study.uid,
        name="MCPElemSharedName",
        short_name="MCPESM1",
        element_subtype_uid=element_subtypes["run_in"].term_uid,
    )

    response = _post_batch(
        api_client,
        target_study.uid,
        [
            {
                "method": "POST",
                "content": {
                    "name": "MCPElemSharedName",
                    "short_name": "MCPESM2",
                    "element_subtype_uid": element_subtypes["treatment"].term_uid,
                },
            }
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert res[0]["response_code"] == 201
    assert res[0]["content"]["name"] == "MCPElemSharedName"
    assert res[0].get("notification") is None


def test_batch_post_duplicate_code_creates(api_client, element_subtypes):
    target_study = TestUtils.create_study()
    subtype_uid = element_subtypes["run_in"].term_uid
    TestUtils.create_study_element(
        study_uid=target_study.uid,
        name="MCPElemCode1",
        short_name="MCPEC1",
        code="MCP_ELEM_CODE",
        element_subtype_uid=subtype_uid,
    )

    response = _post_batch(
        api_client,
        target_study.uid,
        [
            {
                "method": "POST",
                "content": {
                    "name": "MCPElemCode2",
                    "short_name": "MCPEC2",
                    "code": "MCP_ELEM_CODE",
                    "element_subtype_uid": subtype_uid,
                },
            }
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert res[0]["response_code"] == 201
    assert res[0]["content"]["code"] == "MCP_ELEM_CODE"


def test_copy_from_study_creates_all_elements(api_client, element_subtypes):
    source_study = TestUtils.create_study()
    target_study = TestUtils.create_study()
    subtype_uid = element_subtypes["run_in"].term_uid
    TestUtils.create_study_element(
        study_uid=source_study.uid,
        name="MCPSourceElem1",
        short_name="MCPS1",
        code="MCPSC1",
        element_subtype_uid=subtype_uid,
    )
    TestUtils.create_study_element(
        study_uid=source_study.uid,
        name="MCPSourceElem2",
        short_name="MCPS2",
        code="MCPSC2",
        element_subtype_uid=subtype_uid,
    )

    response = api_client.post(
        f"/studies/{target_study.uid}/study-elements/copy-from-study/{source_study.uid}"
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert len(res) == 2
    assert all(item["response_code"] == 201 for item in res)

    list_response = api_client.get(f"/studies/{target_study.uid}/study-elements")
    assert_response_status_code(list_response, 200)
    names = [item["name"] for item in list_response.json()["items"]]
    assert "MCPSourceElem1" in names
    assert "MCPSourceElem2" in names


def test_copy_from_study_skips_conflicting_element_on_target(
    api_client, element_subtypes
):
    source_study = TestUtils.create_study()
    target_study = TestUtils.create_study()
    subtype_uid = element_subtypes["run_in"].term_uid
    TestUtils.create_study_element(
        study_uid=source_study.uid,
        name="MCPCopyConflictElem",
        short_name="MCPCCE1",
        code="MCPCCEC1",
        element_subtype_uid=subtype_uid,
    )
    TestUtils.create_study_element(
        study_uid=source_study.uid,
        name="MCPCopyUniqueElem",
        short_name="MCPCCE2",
        code="MCPCCEC2",
        element_subtype_uid=subtype_uid,
    )
    TestUtils.create_study_element(
        study_uid=target_study.uid,
        name="MCPCopyConflictElem",
        short_name="MCPCCET1",
        code="MCPCCETC1",
        element_subtype_uid=subtype_uid,
    )

    response = api_client.post(
        f"/studies/{target_study.uid}/study-elements/copy-from-study/{source_study.uid}"
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert len(res) == 2
    assert res[0]["response_code"] == 200
    assert "creation skipped" in res[0]["notification"]
    assert res[0]["content"]["name"] == "MCPCopyConflictElem"
    assert res[1]["response_code"] == 201
    assert res[1]["content"]["name"] == "MCPCopyUniqueElem"

    list_response = api_client.get(f"/studies/{target_study.uid}/study-elements")
    assert_response_status_code(list_response, 200)
    assert len(list_response.json()["items"]) == 2


def test_copy_from_study_target_not_found(api_client, element_subtypes):
    source_study = TestUtils.create_study()
    response = api_client.post(
        f"/studies/Study_DoesNotExist/study-elements/copy-from-study/{source_study.uid}"
    )
    assert_response_status_code(response, 404)


def test_batch_mixed_patch_and_post(api_client, element_subtypes):
    target_study = TestUtils.create_study()
    subtype_uid = element_subtypes["run_in"].term_uid
    existing_element = TestUtils.create_study_element(
        study_uid=target_study.uid,
        name="MCPMixedPatchElem",
        short_name="MCPMPE1",
        description="Original description",
        element_subtype_uid=subtype_uid,
    )

    response = _post_batch(
        api_client,
        target_study.uid,
        [
            {
                "method": "PATCH",
                "content": {
                    "element_uid": existing_element.element_uid,
                    "description": "Updated description",
                },
            },
            {
                "method": "POST",
                "content": {
                    "name": "MCPMixedPostElem",
                    "short_name": "MCPMPE2",
                    "element_subtype_uid": subtype_uid,
                },
            },
        ],
    )
    assert_response_status_code(response, 207)
    res = response.json()
    assert len(res) == 2
    assert res[0]["response_code"] == 200
    assert res[0]["content"]["description"] == "Updated description"
    assert res[1]["response_code"] == 201
    assert res[1]["content"]["name"] == "MCPMixedPostElem"

    list_response = api_client.get(f"/studies/{target_study.uid}/study-elements")
    assert_response_status_code(list_response, 200)
    assert len(list_response.json()["items"]) == 2


def test_copy_from_study_rejects_same_study(api_client):
    target_study = TestUtils.create_study()
    response = api_client.post(
        f"/studies/{target_study.uid}/study-elements/copy-from-study/{target_study.uid}"
    )
    assert_response_status_code(response, 400)
    assert "must differ" in response.json()["message"]


def test_copy_from_study_not_found(api_client):
    target_study = TestUtils.create_study()
    response = api_client.post(
        f"/studies/{target_study.uid}/study-elements/copy-from-study/Study_DoesNotExist"
    )
    assert_response_status_code(response, 404)


def test_copy_from_study_empty_source(api_client):
    source_study = TestUtils.create_study()
    target_study = TestUtils.create_study()
    response = api_client.post(
        f"/studies/{target_study.uid}/study-elements/copy-from-study/{source_study.uid}"
    )
    assert_response_status_code(response, 207)
    assert response.json() == []
