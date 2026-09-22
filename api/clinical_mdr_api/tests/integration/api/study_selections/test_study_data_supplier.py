"""
Tests for /studies/{study_uid}/study-data-suppliers endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import CTCodelist
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.data_suppliers.data_supplier import DataSupplier
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study: Study
test_data_dict: dict[str, Any]
data_suppliers: list[DataSupplier]
supplier_type: CTTerm
supplier_type2: CTTerm
origin_source: CTTerm
origin_type: CTTerm
supplier_type_codelist: CTCodelist
origin_source_codelist: CTCodelist
origin_type_codelist: CTCodelist


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data(api_client):
    """Initialize test data"""
    db_name = "studydatasupplier"
    inject_and_clear_db(db_name)

    global study, test_data_dict
    study, test_data_dict = inject_base_data()

    response = api_client.patch(
        f"studies/{study.uid}",
        json={
            "current_metadata": {
                "study_description": {
                    "study_title": "title",
                    "study_short_title": "short title",
                }
            }
        },
    )

    study = Study(**response.json())

    global data_suppliers
    global supplier_type
    global supplier_type2
    global origin_source
    global origin_type
    global supplier_type_codelist
    global origin_source_codelist
    global origin_type_codelist

    supplier_type_codelist = TestUtils.create_ct_codelist(
        name="Data Supplier Type",
        sponsor_preferred_name="Data Supplier Type",
        extensible=True,
        approve=True,
        submission_value="DATA_SUPPLIER_TYPE",
        catalogue_name=settings.sdtm_ct_catalogue_name,
    )
    supplier_type = TestUtils.create_ct_term(
        codelist_uid=supplier_type_codelist.codelist_uid,
        sponsor_preferred_name_sentence_case="type",
        sponsor_preferred_name="Type",
        order=1,
        catalogue_name=settings.sdtm_ct_catalogue_name,
        effective_date=datetime(2020, 3, 25, tzinfo=timezone.utc),
        approve=True,
    )
    supplier_type2 = TestUtils.create_ct_term(
        codelist_uid=supplier_type_codelist.codelist_uid,
        sponsor_preferred_name_sentence_case="type2",
        sponsor_preferred_name="Type2",
        order=2,
        catalogue_name=settings.sdtm_ct_catalogue_name,
        effective_date=datetime(2020, 3, 25, tzinfo=timezone.utc),
        approve=True,
    )

    origin_source_codelist = TestUtils.create_ct_codelist(
        name="Origin Source",
        sponsor_preferred_name="Origin Source",
        extensible=True,
        approve=True,
        submission_value="ORIGINS",
        catalogue_name=settings.sdtm_ct_catalogue_name,
        codelist_uid="C170450",
    )
    origin_source = TestUtils.create_ct_term(
        codelist_uid=origin_source_codelist.codelist_uid,
        sponsor_preferred_name="Origin Source",
    )
    origin_type_codelist = TestUtils.create_ct_codelist(
        name="Origin Type",
        sponsor_preferred_name="Origin Type",
        extensible=True,
        approve=True,
        submission_value="ORIGINT",
        catalogue_name=settings.sdtm_ct_catalogue_name,
        codelist_uid="C170449",
    )
    origin_type = TestUtils.create_ct_term(
        codelist_uid=origin_type_codelist.codelist_uid,
        sponsor_preferred_name="Origin Type",
    )

    data_suppliers = []
    data_suppliers.append(
        TestUtils.create_data_supplier(
            name="name A",
            order=1,
            description="Description A",
            api_base_url="api_base_url",
            ui_base_url="ui_base_url",
            supplier_type_uid=supplier_type.term_uid,
            origin_source_uid=origin_source.term_uid,
            origin_type_uid=origin_type.term_uid,
        )
    )
    data_suppliers.append(
        TestUtils.create_data_supplier(
            name="name B",
            order=2,
            description="Description B",
            api_base_url="api_base_url",
            ui_base_url="ui_base_url",
            supplier_type_uid=supplier_type.term_uid,
            origin_source_uid=origin_source.term_uid,
            origin_type_uid=origin_type.term_uid,
        )
    )

    params = {
        "uid": supplier_type.term_uid,
        "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
    }
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTTermNameRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        n.uid =$uid AND EXISTS((ct_name)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )

    params = {
        "uid": supplier_type_codelist.codelist_uid,
        "date": datetime(2020, 3, 26, tzinfo=timezone.utc),
    }
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_NAME_ROOT]-(ct_name:CTCodelistNameRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        n.uid =$uid AND EXISTS((ct_name)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )
    db.cypher_query(
        """
                    MATCH (n)-[:HAS_ATTRIBUTES_ROOT]-(ct_attrs:CTCodelistAttributesRoot)-[has_version:HAS_VERSION]-(val) 
                    where 
                        n.uid =$uid AND EXISTS((ct_attrs)-[:LATEST]-(val)) 
                        AND has_version.status ='Final' 
                    SET has_version.start_date = $date
                """,
        params=params,
    )
    yield


@pytest.mark.order("last")
def test_integrity_checks_for_all_studies(api_client):
    """
    Test integrity checks for all available studies in the database.

    This test should always be executed at the END to check the health of the remaining database.
    It validates that all studies in the database pass integrity checks after all other tests have run.
    """
    TestUtils.run_integrity_checks_for_all_studies(api_client)


def test_get_empty_list_of_study_data_suppliers_of_specific_study(api_client):
    """Test getting an empty list of study data suppliers for a study"""
    response = api_client.get(f"studies/{study.uid}/study-data-suppliers")

    assert_response_status_code(response, 200)
    response = response.json()
    assert response["total"] == 0
    assert response["items"] == []


def test_create_data_supplier_of_specific_study(api_client):
    # First sync: add one supplier with explicit type
    response = api_client.put(
        f"studies/{study.uid}/study-data-suppliers/sync",
        json={
            "suppliers": [
                {
                    "data_supplier_uid": data_suppliers[0].uid,
                    "study_data_supplier_type_uid": supplier_type.term_uid,
                },
            ]
        },
    )

    assert_response_status_code(response, 200)
    rs = response.json()
    assert len(rs) == 1
    assert rs[0]["study_uid"] == study.uid
    assert rs[0]["study_version"] is None
    assert rs[0]["study_data_supplier_uid"] == "StudyDataSupplier_000001"
    assert rs[0]["study_data_supplier_order"] == 1
    assert rs[0]["data_supplier_uid"] == data_suppliers[0].uid
    assert rs[0]["name"] == data_suppliers[0].name
    assert rs[0]["description"] == data_suppliers[0].description
    assert rs[0]["order"] == data_suppliers[0].order
    assert rs[0]["api_base_url"] == data_suppliers[0].api_base_url
    assert rs[0]["ui_base_url"] == data_suppliers[0].ui_base_url
    assert rs[0]["study_data_supplier_type"]["term_uid"] == supplier_type.term_uid
    assert rs[0]["start_date"] is not None
    assert rs[0]["author_username"] == "unknown-user"
    assert rs[0]["end_date"] is None
    assert rs[0]["change_type"] == "Create"

    # Second sync: add another supplier with different type (keep existing one)
    response = api_client.put(
        f"studies/{study.uid}/study-data-suppliers/sync",
        json={
            "suppliers": [
                {
                    "data_supplier_uid": data_suppliers[0].uid,
                    "study_data_supplier_type_uid": supplier_type.term_uid,
                },
                {
                    "data_supplier_uid": data_suppliers[0].uid,
                    "study_data_supplier_type_uid": supplier_type2.term_uid,
                },
            ]
        },
    )

    assert_response_status_code(response, 200)
    rs = response.json()
    assert len(rs) == 2
    # Find the newly created item (with supplier_type2)
    new_item = next(
        item
        for item in rs
        if item["study_data_supplier_type"]["term_uid"] == supplier_type2.term_uid
    )
    assert new_item["study_uid"] == study.uid
    assert new_item["study_version"] is None
    assert new_item["study_data_supplier_uid"] == "StudyDataSupplier_000002"
    assert new_item["study_data_supplier_order"] == 2
    assert new_item["data_supplier_uid"] == data_suppliers[0].uid
    assert new_item["name"] == data_suppliers[0].name
    assert new_item["description"] == data_suppliers[0].description
    assert new_item["order"] == data_suppliers[0].order
    assert new_item["api_base_url"] == data_suppliers[0].api_base_url
    assert new_item["ui_base_url"] == data_suppliers[0].ui_base_url
    assert new_item["start_date"] is not None
    assert new_item["author_username"] == "unknown-user"
    assert new_item["end_date"] is None
    assert new_item["change_type"] == "Create"


def test_delete_data_supplier_of_specific_study(api_client):
    # Sync to add a third supplier (keeping existing two)
    response = api_client.put(
        f"studies/{study.uid}/study-data-suppliers/sync",
        json={
            "suppliers": [
                {
                    "data_supplier_uid": data_suppliers[0].uid,
                    "study_data_supplier_type_uid": supplier_type.term_uid,
                },
                {
                    "data_supplier_uid": data_suppliers[0].uid,
                    "study_data_supplier_type_uid": supplier_type2.term_uid,
                },
                {
                    "data_supplier_uid": data_suppliers[1].uid,
                    "study_data_supplier_type_uid": supplier_type.term_uid,
                },
            ]
        },
    )

    assert_response_status_code(response, 200)
    rs = response.json()
    assert len(rs) == 3
    # Find the newly created item (data_suppliers[1])
    new_item = next(
        item for item in rs if item["data_supplier_uid"] == data_suppliers[1].uid
    )
    assert new_item["study_uid"] == study.uid
    assert new_item["study_version"] is None
    assert new_item["study_data_supplier_uid"] == "StudyDataSupplier_000003"
    assert new_item["study_data_supplier_order"] == 3
    assert new_item["data_supplier_uid"] == data_suppliers[1].uid
    assert new_item["name"] == data_suppliers[1].name
    assert new_item["description"] == data_suppliers[1].description
    assert new_item["order"] == data_suppliers[1].order
    assert new_item["api_base_url"] == data_suppliers[1].api_base_url
    assert new_item["ui_base_url"] == data_suppliers[1].ui_base_url
    assert new_item["study_data_supplier_type"]["term_uid"] == supplier_type.term_uid
    assert new_item["start_date"] is not None
    assert new_item["author_username"] == "unknown-user"
    assert new_item["end_date"] is None
    assert new_item["change_type"] == "Create"

    response = api_client.delete(
        f"studies/{study.uid}/study-data-suppliers/StudyDataSupplier_000003"
    )

    assert_response_status_code(response, 204)


def test_get_specific_study_data_supplier_of_specific_study(api_client):
    response = api_client.get(
        f"studies/{study.uid}/study-data-suppliers/StudyDataSupplier_000001"
    )

    assert_response_status_code(response, 200)
    rs = response.json()
    assert rs["study_uid"] == study.uid
    assert rs["study_version"] is None
    assert rs["study_data_supplier_uid"] == "StudyDataSupplier_000001"
    assert rs["study_data_supplier_order"] == 1
    assert rs["data_supplier_uid"] == data_suppliers[0].uid
    assert rs["name"] == data_suppliers[0].name
    assert rs["description"] == data_suppliers[0].description
    assert rs["order"] == data_suppliers[0].order
    assert rs["api_base_url"] == data_suppliers[0].api_base_url
    assert rs["ui_base_url"] == data_suppliers[0].ui_base_url
    assert rs["study_data_supplier_type"]["term_uid"] == supplier_type.term_uid
    assert rs["start_date"] is not None
    assert rs["author_username"] == "unknown-user"
    assert rs["end_date"] is None
    assert rs["change_type"] == "Create"


def test_get_paginated_response_for_study_data_suppliers_of_specific_study(api_client):
    response = api_client.get(
        f"studies/{study.uid}/study-data-suppliers?total_count=true"
    )

    assert_response_status_code(response, 200)
    rs = response.json()
    assert rs["total"] == 2
    assert rs["items"][0]["study_uid"] == study.uid
    assert rs["items"][0]["study_version"] is None
    assert rs["items"][0]["study_data_supplier_uid"] == "StudyDataSupplier_000001"
    assert rs["items"][0]["study_data_supplier_order"] == 1
    assert rs["items"][0]["data_supplier_uid"] == data_suppliers[0].uid
    assert rs["items"][0]["name"] == data_suppliers[0].name
    assert rs["items"][0]["description"] == data_suppliers[0].description
    assert rs["items"][0]["order"] == data_suppliers[0].order
    assert rs["items"][0]["api_base_url"] == data_suppliers[0].api_base_url
    assert rs["items"][0]["ui_base_url"] == data_suppliers[0].ui_base_url
    assert (
        rs["items"][0]["study_data_supplier_type"]["term_uid"] == supplier_type.term_uid
    )
    assert rs["items"][0]["start_date"] is not None
    assert rs["items"][0]["author_username"] == "unknown-user"
    assert rs["items"][0]["end_date"] is None
    assert rs["items"][0]["change_type"] == "Create"


def test_get_audit_trail_of_study_data_suppliers_of_specific_study(api_client):
    response = api_client.get(f"studies/{study.uid}/study-data-suppliers/audit-trail")

    assert_response_status_code(response, 200)
    rs = response.json()
    # StudyDataSupplier_000003 was created with data_suppliers[1] then deleted
    assert rs[0]["study_uid"] == study.uid
    assert rs[0]["study_version"] is None
    assert rs[0]["study_data_supplier_uid"] == "StudyDataSupplier_000003"
    assert rs[0]["study_data_supplier_order"] == 3
    assert rs[0]["data_supplier_uid"] == data_suppliers[1].uid
    assert rs[0]["name"] == data_suppliers[1].name
    assert rs[0]["description"] == data_suppliers[1].description
    assert rs[0]["order"] == data_suppliers[1].order
    assert rs[0]["api_base_url"] == data_suppliers[1].api_base_url
    assert rs[0]["ui_base_url"] == data_suppliers[1].ui_base_url
    assert rs[0]["study_data_supplier_type"]["term_uid"] == supplier_type.term_uid
    assert rs[0]["start_date"] is not None
    assert rs[0]["author_username"] == "unknown-user"
    assert rs[0]["end_date"] is None
    assert rs[0]["change_type"] == "Delete"

    assert rs[1]["study_uid"] == study.uid
    assert rs[1]["study_version"] is None
    assert rs[1]["study_data_supplier_uid"] == "StudyDataSupplier_000003"
    assert rs[1]["study_data_supplier_order"] == 3
    assert rs[1]["data_supplier_uid"] == data_suppliers[1].uid
    assert rs[1]["name"] == data_suppliers[1].name
    assert rs[1]["description"] == data_suppliers[1].description
    assert rs[1]["order"] == data_suppliers[1].order
    assert rs[1]["api_base_url"] == data_suppliers[1].api_base_url
    assert rs[1]["ui_base_url"] == data_suppliers[1].ui_base_url
    assert rs[1]["study_data_supplier_type"]["term_uid"] == supplier_type.term_uid
    assert rs[1]["start_date"] is not None
    assert rs[1]["author_username"] == "unknown-user"
    assert rs[1]["end_date"] is not None
    assert rs[1]["change_type"] == "Create"

    assert rs[2]["study_uid"] == study.uid
    assert rs[2]["study_version"] is None
    assert rs[2]["study_data_supplier_uid"] == "StudyDataSupplier_000002"
    assert rs[2]["study_data_supplier_order"] == 2
    assert rs[2]["data_supplier_uid"] == data_suppliers[0].uid
    assert rs[2]["name"] == data_suppliers[0].name
    assert rs[2]["description"] == data_suppliers[0].description
    assert rs[2]["order"] == data_suppliers[0].order
    assert rs[2]["api_base_url"] == data_suppliers[0].api_base_url
    assert rs[2]["ui_base_url"] == data_suppliers[0].ui_base_url
    assert rs[2]["study_data_supplier_type"]["term_uid"] == supplier_type2.term_uid
    assert rs[2]["start_date"] is not None
    assert rs[2]["author_username"] == "unknown-user"
    assert rs[2]["end_date"] is None
    assert rs[2]["change_type"] == "Create"

    assert rs[3]["study_uid"] == study.uid
    assert rs[3]["study_version"] is None
    assert rs[3]["study_data_supplier_uid"] == "StudyDataSupplier_000001"
    assert rs[3]["study_data_supplier_order"] == 1
    assert rs[3]["data_supplier_uid"] == data_suppliers[0].uid
    assert rs[3]["name"] == data_suppliers[0].name
    assert rs[3]["description"] == data_suppliers[0].description
    assert rs[3]["order"] == data_suppliers[0].order
    assert rs[3]["api_base_url"] == data_suppliers[0].api_base_url
    assert rs[3]["ui_base_url"] == data_suppliers[0].ui_base_url
    assert rs[3]["study_data_supplier_type"]["term_uid"] == supplier_type.term_uid
    assert rs[3]["start_date"] is not None
    assert rs[3]["author_username"] == "unknown-user"
    assert rs[3]["end_date"] is None
    assert rs[3]["change_type"] == "Create"


def test_get_audit_trail_of_specific_study_data_supplier_of_specific_study(api_client):
    response = api_client.get(
        f"studies/{study.uid}/study-data-suppliers/StudyDataSupplier_000001/audit-trail"
    )

    assert_response_status_code(response, 200)
    rs = response.json()
    assert rs[0]["study_uid"] == study.uid
    assert rs[0]["study_version"] is None
    assert rs[0]["study_data_supplier_uid"] == "StudyDataSupplier_000001"
    assert rs[0]["study_data_supplier_order"] == 1
    assert rs[0]["data_supplier_uid"] == data_suppliers[0].uid
    assert rs[0]["name"] == data_suppliers[0].name
    assert rs[0]["description"] == data_suppliers[0].description
    assert rs[0]["order"] == data_suppliers[0].order
    assert rs[0]["api_base_url"] == data_suppliers[0].api_base_url
    assert rs[0]["ui_base_url"] == data_suppliers[0].ui_base_url
    assert rs[0]["study_data_supplier_type"]["term_uid"] == supplier_type.term_uid
    assert rs[0]["start_date"] is not None
    assert rs[0]["author_username"] == "unknown-user"
    assert rs[0]["end_date"] is None
    assert rs[0]["change_type"] == "Create"


def test_update_data_supplier_of_specific_study(api_client):
    response = api_client.put(
        f"studies/{study.uid}/study-data-suppliers/StudyDataSupplier_000001",
        json={
            "data_supplier_uid": data_suppliers[1].uid,
            "study_data_supplier_type_uid": supplier_type2.term_uid,
        },
    )

    assert_response_status_code(response, 200)
    rs = response.json()
    assert rs["study_uid"] == study.uid
    assert rs["study_version"] is None
    assert rs["study_data_supplier_uid"] == "StudyDataSupplier_000001"
    assert rs["study_data_supplier_order"] == 1
    assert rs["data_supplier_uid"] == data_suppliers[1].uid
    assert rs["name"] == data_suppliers[1].name
    assert rs["description"] == data_suppliers[1].description
    assert rs["order"] == data_suppliers[1].order
    assert rs["api_base_url"] == data_suppliers[1].api_base_url
    assert rs["ui_base_url"] == data_suppliers[1].ui_base_url
    assert rs["study_data_supplier_type"]["term_uid"] == supplier_type2.term_uid
    assert rs["start_date"] is not None
    assert rs["author_username"] == "unknown-user"
    assert rs["end_date"] is None
    assert rs["change_type"] == "Edit"


def test_create_data_supplier_with_blinded_flag(api_client):
    """Test that blinded=True is persisted when creating via sync"""
    # Sync a new supplier with blinded=True alongside existing ones
    response = api_client.put(
        f"studies/{study.uid}/study-data-suppliers/sync",
        json={
            "suppliers": [
                {
                    "data_supplier_uid": data_suppliers[0].uid,
                    "study_data_supplier_type_uid": supplier_type2.term_uid,
                    "blinded": False,
                },
                {
                    "data_supplier_uid": data_suppliers[1].uid,
                    "study_data_supplier_type_uid": supplier_type2.term_uid,
                    "blinded": True,
                },
            ]
        },
    )

    assert_response_status_code(response, 200)
    rs = response.json()
    item = next(
        s
        for s in rs
        if s["data_supplier_uid"] == data_suppliers[1].uid
        and s["study_data_supplier_type"]["term_uid"] == supplier_type2.term_uid
    )
    assert item["blinded"] is True

    # Verify GET returns blinded=True
    response = api_client.get(
        f"studies/{study.uid}/study-data-suppliers/{item['study_data_supplier_uid']}"
    )
    assert_response_status_code(response, 200)
    assert response.json()["blinded"] is True


def test_update_blinded_flag_via_put(api_client):
    """Test that blinded flag is saved when updating a supplier via PUT"""
    # First ensure StudyDataSupplier_000001 exists and set blinded=True
    response = api_client.put(
        f"studies/{study.uid}/study-data-suppliers/StudyDataSupplier_000001",
        json={
            "data_supplier_uid": data_suppliers[1].uid,
            "study_data_supplier_type_uid": supplier_type2.term_uid,
            "blinded": True,
        },
    )

    assert_response_status_code(response, 200)
    rs = response.json()
    assert rs["blinded"] is True
    assert rs["change_type"] == "Edit"

    # Now set it back to False
    response = api_client.put(
        f"studies/{study.uid}/study-data-suppliers/StudyDataSupplier_000001",
        json={
            "data_supplier_uid": data_suppliers[1].uid,
            "study_data_supplier_type_uid": supplier_type2.term_uid,
            "blinded": False,
        },
    )

    assert_response_status_code(response, 200)
    assert response.json()["blinded"] is False


def test_update_blinded_flag_via_sync(api_client):
    """Test that toggling blinded on an existing supplier is persisted via sync.
    This exercises the update path in sync_selections (not just create/delete)."""
    # Get current state — grab a supplier uid to work with
    response = api_client.get(
        f"studies/{study.uid}/study-data-suppliers?total_count=true"
    )
    assert_response_status_code(response, 200)
    items = response.json()["items"]
    assert len(items) > 0

    target = items[0]
    assert target["blinded"] is False

    # Sync with blinded=True for the same (data_supplier_uid, type_uid) key
    suppliers_payload = [
        {
            "data_supplier_uid": s["data_supplier_uid"],
            "study_data_supplier_type_uid": (
                s["study_data_supplier_type"]["term_uid"]
                if s["study_data_supplier_type"]
                else None
            ),
            "blinded": (
                True
                if s["study_data_supplier_uid"] == target["study_data_supplier_uid"]
                else s["blinded"]
            ),
        }
        for s in items
    ]

    response = api_client.put(
        f"studies/{study.uid}/study-data-suppliers/sync",
        json={"suppliers": suppliers_payload},
    )

    assert_response_status_code(response, 200)
    rs = response.json()
    updated = next(
        s
        for s in rs
        if s["study_data_supplier_uid"] == target["study_data_supplier_uid"]
    )
    assert updated["blinded"] is True
    # UID and order must be preserved (not a delete+create)
    assert updated["study_data_supplier_uid"] == target["study_data_supplier_uid"]
    assert updated["study_data_supplier_order"] == target["study_data_supplier_order"]

    # Verify via GET
    response = api_client.get(
        f"studies/{study.uid}/study-data-suppliers/{target['study_data_supplier_uid']}"
    )
    assert_response_status_code(response, 200)
    assert response.json()["blinded"] is True


def test_reorder_study_data_supplier_of_specific_study(api_client):
    response = api_client.patch(
        f"studies/{study.uid}/study-data-suppliers/StudyDataSupplier_000001/order",
        json={"new_order": 2},
    )
    assert_response_status_code(response, 200)
    rs = response.json()
    assert rs["study_uid"] == study.uid
    assert rs["study_version"] is None
    assert rs["study_data_supplier_uid"] == "StudyDataSupplier_000001"
    assert rs["study_data_supplier_order"] == 2
    assert rs["data_supplier_uid"] == data_suppliers[1].uid
    assert rs["name"] == data_suppliers[1].name
    assert rs["description"] == data_suppliers[1].description
    assert rs["order"] == data_suppliers[1].order
    assert rs["api_base_url"] == data_suppliers[1].api_base_url
    assert rs["ui_base_url"] == data_suppliers[1].ui_base_url
    assert rs["study_data_supplier_type"]["term_uid"] == supplier_type2.term_uid
    assert rs["start_date"] is not None
    assert rs["author_username"] == "unknown-user"
    assert rs["end_date"] is None
    assert rs["change_type"] == "Edit"

    response = api_client.get(
        f"studies/{study.uid}/study-data-suppliers?total_count=true"
    )
    assert_response_status_code(response, 200)
    rs = response.json()
    assert rs["total"] == 2
    assert rs["items"][0]["study_uid"] == study.uid
    assert rs["items"][0]["study_version"] is None
    assert rs["items"][0]["study_data_supplier_uid"] == "StudyDataSupplier_000002"
    assert rs["items"][0]["study_data_supplier_order"] == 1
    assert rs["items"][0]["data_supplier_uid"] == data_suppliers[0].uid
    assert rs["items"][0]["name"] == data_suppliers[0].name
    assert rs["items"][0]["description"] == data_suppliers[0].description
    assert rs["items"][0]["order"] == data_suppliers[0].order
    assert rs["items"][0]["api_base_url"] == data_suppliers[0].api_base_url
    assert rs["items"][0]["ui_base_url"] == data_suppliers[0].ui_base_url
    assert (
        rs["items"][0]["study_data_supplier_type"]["term_uid"]
        == supplier_type2.term_uid
    )
    assert rs["items"][0]["start_date"] is not None
    assert rs["items"][0]["author_username"] == "unknown-user"
    assert rs["items"][0]["end_date"] is None
    assert rs["items"][0]["change_type"] == "Edit"

    assert rs["items"][1]["study_uid"] == study.uid
    assert rs["items"][1]["study_version"] is None
    assert rs["items"][1]["study_data_supplier_uid"] == "StudyDataSupplier_000001"
    assert rs["items"][1]["study_data_supplier_order"] == 2
    assert rs["items"][1]["data_supplier_uid"] == data_suppliers[1].uid
    assert rs["items"][1]["name"] == data_suppliers[1].name
    assert rs["items"][1]["description"] == data_suppliers[1].description
    assert rs["items"][1]["order"] == data_suppliers[1].order
    assert rs["items"][1]["api_base_url"] == data_suppliers[1].api_base_url
    assert rs["items"][1]["ui_base_url"] == data_suppliers[1].ui_base_url
    assert (
        rs["items"][1]["study_data_supplier_type"]["term_uid"]
        == supplier_type2.term_uid
    )
    assert rs["items"][1]["start_date"] is not None
    assert rs["items"][1]["author_username"] == "unknown-user"
    assert rs["items"][1]["end_date"] is None
    assert rs["items"][1]["change_type"] == "Edit"


@pytest.mark.parametrize(
    "field_name",
    [
        pytest.param("name"),
        pytest.param("description"),
        pytest.param("order"),
        pytest.param("api_base_url"),
        pytest.param("ui_base_url"),
    ],
)
def test_study_data_suppliers_headers_of_specific_study(api_client, field_name):
    response = api_client.get(
        f"/studies/{study.uid}/study-data-suppliers/headers?field_name={field_name}"
    )
    res = response.json()

    assert_response_status_code(response, 200)
    expected_result = []
    for data_supplier in data_suppliers:
        value = getattr(data_supplier, field_name)
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


def test_get_study_data_suppliers_with_study_value_version_filter(api_client):
    before_lock = api_client.get(
        f"studies/{study.uid}/study-data-suppliers?total_count=true"
    )

    response = api_client.post(
        f"studies/{study.uid}/locks",
        json={
            "change_description": "Locked version",
            "reason_for_change_uid": test_data_dict["reason_for_lock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)
    response = api_client.post(
        f"studies/{study.uid}/unlocks",
        json={
            "change_description": "Unlock",
            "reason_for_change_uid": test_data_dict["reason_for_unlock_terms"][
                0
            ].term_uid,
        },
    )
    assert_response_status_code(response, 201)

    response = api_client.get(
        f"studies/{study.uid}/study-data-suppliers?study_value_version=1&total_count=true"
    )
    assert_response_status_code(response, 200)
    rs = response.json()
    assert {
        key: val
        for item in rs["items"]
        for key, val in item.items()
        if key != "study_version"
    } == {
        key: val
        for item in before_lock.json()["items"]
        for key, val in item.items()
        if key != "study_version"
    }
    assert rs["total"] == 2
    assert rs["items"][0]["study_uid"] == study.uid
    assert rs["items"][0]["study_version"] == "1"
    assert rs["items"][0]["study_data_supplier_uid"] == "StudyDataSupplier_000002"
    assert rs["items"][0]["study_data_supplier_order"] == 1
    assert rs["items"][0]["data_supplier_uid"] == data_suppliers[0].uid
    assert rs["items"][0]["name"] == data_suppliers[0].name
    assert rs["items"][0]["description"] == data_suppliers[0].description
    assert rs["items"][0]["order"] == data_suppliers[0].order
    assert rs["items"][0]["api_base_url"] == data_suppliers[0].api_base_url
    assert rs["items"][0]["ui_base_url"] == data_suppliers[0].ui_base_url
    assert (
        rs["items"][0]["study_data_supplier_type"]["term_uid"]
        == supplier_type2.term_uid
    )
    assert rs["items"][0]["start_date"] is not None
    assert rs["items"][0]["author_username"] == "unknown-user"
    assert rs["items"][0]["end_date"] is None
    assert rs["items"][0]["change_type"] == "Edit"


def test_get_paginated_response_of_study_data_suppliers(api_client):
    response = api_client.get("study-data-suppliers?total_count=true")

    assert_response_status_code(response, 200)
    rs = response.json()
    assert rs["total"] == 2
    assert rs["items"][0]["study_uid"] == study.uid
    assert rs["items"][0]["study_version"] is None
    assert rs["items"][0]["study_data_supplier_uid"] == "StudyDataSupplier_000002"
    assert rs["items"][0]["study_data_supplier_order"] == 1
    assert rs["items"][0]["data_supplier_uid"] == data_suppliers[0].uid
    assert rs["items"][0]["name"] == data_suppliers[0].name
    assert rs["items"][0]["description"] == data_suppliers[0].description
    assert rs["items"][0]["order"] == data_suppliers[0].order
    assert rs["items"][0]["api_base_url"] == data_suppliers[0].api_base_url
    assert rs["items"][0]["ui_base_url"] == data_suppliers[0].ui_base_url
    assert (
        rs["items"][0]["study_data_supplier_type"]["term_uid"]
        == supplier_type2.term_uid
    )
    assert rs["items"][0]["start_date"] is not None
    assert rs["items"][0]["author_username"] == "unknown-user"
    assert rs["items"][0]["end_date"] is None
    assert rs["items"][0]["change_type"] == "Edit"


@pytest.mark.parametrize(
    "field_name",
    [
        pytest.param("name"),
        pytest.param("description"),
        pytest.param("order"),
        pytest.param("api_base_url"),
        pytest.param("ui_base_url"),
    ],
)
def test_study_data_supplier_headers(api_client, field_name):
    response = api_client.get(f"/study-data-suppliers/headers?field_name={field_name}")
    res = response.json()

    assert_response_status_code(response, 200)
    expected_result = []
    for data_supplier in data_suppliers:
        value = getattr(data_supplier, field_name)
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


def test_study_data_supplier_type_version_selecting_ct_package(api_client):
    new_ctterm_name = "new ctterm name"
    response = api_client.post(
        f"/ct/terms/{supplier_type.term_uid}/names/versions",
    )
    assert_response_status_code(response, 201)
    api_client.patch(
        f"/ct/terms/{supplier_type.term_uid}/names",
        json={
            "sponsor_preferred_name": new_ctterm_name,
            "sponsor_preferred_name_sentence_case": new_ctterm_name,
            "change_description": "string",
        },
    )
    response = api_client.post(f"/ct/terms/{supplier_type.term_uid}/names/approvals")
    assert_response_status_code(response, 201)

    # Get current suppliers first
    current_response = api_client.get(f"studies/{study.uid}/study-data-suppliers")
    current_suppliers = [
        {
            "data_supplier_uid": item["data_supplier_uid"],
            "study_data_supplier_type_uid": item["study_data_supplier_type"][
                "term_uid"
            ],
        }
        for item in current_response.json()["items"]
    ]
    # Add the new supplier
    current_suppliers.append(
        {
            "data_supplier_uid": data_suppliers[0].uid,
            "study_data_supplier_type_uid": supplier_type.term_uid,
        }
    )
    response = api_client.put(
        f"/studies/{study.uid}/study-data-suppliers/sync",
        json={"suppliers": current_suppliers},
    )
    assert_response_status_code(response, 200)
    res_list = response.json()
    # Find the newly created item (with supplier_type)
    res = next(
        item
        for item in res_list
        if item["study_data_supplier_type"]["term_uid"] == supplier_type.term_uid
        and item["change_type"] == "Create"
    )
    assert res["study_data_supplier_type"]["term_name"] == new_ctterm_name
    study_selection_uid_study_standard_test = res["study_data_supplier_uid"]

    ct_package_uid = TestUtils.create_ct_package(
        name="SDTM CT 2020-03-27",
        approve_elements=False,
        effective_date=datetime(2020, 3, 27, tzinfo=timezone.utc),
    )

    response = api_client.patch(
        f"/studies/{study.uid}/study-standard-versions/StudyStandardVersion_000001",
        json={
            "ct_package_uid": ct_package_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["ct_package"]["uid"] == ct_package_uid

    response = api_client.get(
        f"/studies/{study.uid}/study-data-suppliers/{study_selection_uid_study_standard_test}",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res["study_data_supplier_type"]["term_name"]
        == supplier_type.sponsor_preferred_name
    )

    response = api_client.put(
        f"/studies/{study.uid}/study-data-suppliers/{study_selection_uid_study_standard_test}",
        json={
            "data_supplier_uid": data_suppliers[1].uid,
            "study_data_supplier_type_uid": supplier_type.term_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res["study_data_supplier_type"]["term_name"]
        == supplier_type.sponsor_preferred_name
    )

    response = api_client.get(
        f"/studies/{study.uid}/study-data-suppliers/{study_selection_uid_study_standard_test}/audit-trail",
    )
    print("-------")
    print(response.json())
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[0]["study_data_supplier_type"]["term_name"]
        == supplier_type.sponsor_preferred_name
    )
    assert res[1]["study_data_supplier_type"]["term_name"] == new_ctterm_name

    response = api_client.get(
        f"/studies/{study.uid}/study-data-suppliers/audit-trail/",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res[2]["study_data_supplier_type"]["term_name"]
        == supplier_type.sponsor_preferred_name
    )
    assert res[3]["study_data_supplier_type"]["term_name"] == new_ctterm_name


def test_reordering_after_deleting_data_supplier_of_specific_study(api_client):
    # Get current suppliers first
    current_response = api_client.get(f"studies/{study.uid}/study-data-suppliers")
    current_suppliers = [
        {
            "data_supplier_uid": item["data_supplier_uid"],
            "study_data_supplier_type_uid": item["study_data_supplier_type"][
                "term_uid"
            ],
        }
        for item in current_response.json()["items"]
    ]
    # Add the new supplier
    current_suppliers.append(
        {
            "data_supplier_uid": data_suppliers[0].uid,
            "study_data_supplier_type_uid": None,
        }
    )
    response = api_client.put(
        f"studies/{study.uid}/study-data-suppliers/sync",
        json={"suppliers": current_suppliers},
    )

    assert_response_status_code(response, 200)
    rs_list = response.json()
    # Find the newly created item
    rs = next(item for item in rs_list if item["change_type"] == "Create")
    assert rs["study_uid"] == study.uid
    assert rs["study_version"] is None
    assert rs["study_data_supplier_uid"] == "StudyDataSupplier_000005"
    assert rs["study_data_supplier_order"] == 4
    assert rs["data_supplier_uid"] == data_suppliers[0].uid
    assert rs["name"] == data_suppliers[0].name
    assert rs["description"] == data_suppliers[0].description
    assert rs["order"] == data_suppliers[0].order
    assert rs["api_base_url"] == data_suppliers[0].api_base_url
    assert rs["ui_base_url"] == data_suppliers[0].ui_base_url
    assert rs["study_data_supplier_type"]["term_uid"] == supplier_type.term_uid
    assert rs["start_date"] is not None
    assert rs["author_username"] == "unknown-user"
    assert rs["end_date"] is None
    assert rs["change_type"] == "Create"

    response = api_client.delete(
        f"studies/{study.uid}/study-data-suppliers/StudyDataSupplier_000002"
    )
    assert_response_status_code(response, 204)

    response = api_client.get(f"studies/{study.uid}/study-data-suppliers")
    assert_response_status_code(response, 200)
    rs = response.json()
    assert rs["items"][0]["study_uid"] == study.uid
    assert rs["items"][0]["study_data_supplier_uid"] == "StudyDataSupplier_000001"
    assert rs["items"][0]["study_data_supplier_order"] == 1
    assert rs["items"][0]["change_type"] == "Edit"
    assert rs["items"][1]["study_uid"] == study.uid
    assert rs["items"][1]["study_data_supplier_uid"] == "StudyDataSupplier_000004"
    assert rs["items"][1]["study_data_supplier_order"] == 2
    assert rs["items"][1]["change_type"] == "Edit"
    assert rs["items"][2]["study_uid"] == study.uid
    assert rs["items"][2]["study_data_supplier_uid"] == "StudyDataSupplier_000005"
    assert rs["items"][2]["study_data_supplier_order"] == 3
    assert rs["items"][2]["change_type"] == "Edit"
