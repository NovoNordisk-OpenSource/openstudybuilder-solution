"""
Tests for /studies/{study_uid}/study-auxiliary-devices endpoints
"""

from typing import Any
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

# Global variables shared between fixtures and tests
study: Study
device_terms: list[CTTerm]
other_term: CTTerm
test_data_dict: dict[str, Any]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    inject_and_clear_db("studyauxiliarydeviceapi")
    global test_data_dict
    _, test_data_dict = inject_base_data()

    global study
    global device_terms
    global other_term
    study = TestUtils.create_study()
    TestUtils.set_study_standard_version(study_uid=study.uid)

    codelist = TestUtils.create_ct_codelist(
        name="Device definitions",
        sponsor_preferred_name="Device definitions",
        submission_value="DEVICE_DEF",
        extensible=True,
        approve=True,
    )
    device_terms = [
        TestUtils.create_ct_term(
            codelist_uid=codelist.codelist_uid,
            submission_value=f"DEVICE{i}",
            sponsor_preferred_name=f"Device {i}",
            algorithm=f"DIPARMCD='SERIAL' and DIORRES='{i}'",
        )
        for i in range(1, 4)
    ]
    other_codelist = TestUtils.create_ct_codelist(
        name="Other", sponsor_preferred_name="Other", extensible=True, approve=True
    )
    other_term = TestUtils.create_ct_term(codelist_uid=other_codelist.codelist_uid)
    yield


def url(suffix: str = "") -> str:
    return f"/studies/{study.uid}/study-auxiliary-devices{suffix}"


def names(api_client) -> list[str]:
    return [
        item["auxiliary_device_name"] for item in api_client.get(url()).json()["items"]
    ]


@pytest.mark.order("last")
def test_integrity_checks_for_all_studies(api_client):
    TestUtils.run_integrity_checks_for_all_studies(api_client)


def test_create_list_get(api_client):
    for term in device_terms[:2]:
        response = api_client.post(
            url(), json={"auxiliary_device_term_uid": term.term_uid}
        )
        assert_response_status_code(response, 201)

    res = response.json()
    assert res["order"] == 2
    assert res["auxiliary_device_term_uid"] == device_terms[1].term_uid
    assert res["auxiliary_device_name"] == "Device 2"
    assert res["auxiliary_device_submission_value"] == "DEVICE2"
    assert res["auxiliary_device_algorithm"] == "DIPARMCD='SERIAL' and DIORRES='2'"
    assert res["auxiliary_device_nci_preferred_name"] == (
        device_terms[1].nci_preferred_name
    )
    assert res["auxiliary_device_definition"] == device_terms[1].definition

    response = api_client.get(url(f"/{res['uid']}"))
    assert_response_status_code(response, 200)
    assert response.json() == res | {"study_version": mock.ANY}

    assert names(api_client) == ["Device 1", "Device 2"]

    # insert in front
    response = api_client.post(
        url(), json={"auxiliary_device_term_uid": device_terms[2].term_uid, "order": 1}
    )
    assert_response_status_code(response, 201)
    assert names(api_client) == ["Device 3", "Device 1", "Device 2"]


def test_create_rejects_invalid(api_client):
    response = api_client.post(
        url(), json={"auxiliary_device_term_uid": device_terms[0].term_uid}
    )
    assert_response_status_code(response, 400)
    assert "already selected" in response.json()["message"]

    response = api_client.post(
        url(), json={"auxiliary_device_term_uid": other_term.term_uid}
    )
    assert_response_status_code(response, 400)
    assert "was not found in the codelist" in response.json()["message"]

    response = api_client.post(
        url(), json={"auxiliary_device_term_uid": "NotExistingTerm"}
    )
    assert_response_status_code(response, 404)

    response = api_client.post(
        url(), json={"auxiliary_device_term_uid": "NotExistingTerm", "order": 0}
    )
    assert_response_status_code(response, 400)

    response = api_client.get(url("/NotExisting"))
    assert_response_status_code(response, 404)


def test_headers(api_client):
    response = api_client.get(
        url("/headers"), params={"field_name": "auxiliary_device_name"}
    )
    assert_response_status_code(response, 200)
    assert response.json() == ["Device 1", "Device 2", "Device 3"]

    # headers are scoped to the study
    other_study = TestUtils.create_study()
    response = api_client.get(
        f"/studies/{other_study.uid}/study-auxiliary-devices/headers",
        params={"field_name": "auxiliary_device_name"},
    )
    assert_response_status_code(response, 200)
    assert response.json() == []


def test_reorder_and_delete(api_client):
    items = api_client.get(url()).json()["items"]
    response = api_client.patch(url(f"/{items[0]['uid']}/order"), json={"new_order": 3})
    assert_response_status_code(response, 200)
    assert response.json()["order"] == 3
    assert response.json() == api_client.get(url(f"/{items[0]['uid']}")).json() | {
        "study_version": mock.ANY
    }
    assert names(api_client) == ["Device 1", "Device 2", "Device 3"]

    response = api_client.patch(url(f"/{items[0]['uid']}/order"), json={"new_order": 4})
    assert_response_status_code(response, 400)

    response = api_client.delete(url(f"/{items[1]['uid']}"))
    assert_response_status_code(response, 204)
    items = api_client.get(url()).json()["items"]
    assert [(i["order"], i["auxiliary_device_name"]) for i in items] == [
        (1, "Device 2"),
        (2, "Device 3"),
    ]


def test_audit_trails(api_client):
    response = api_client.get(url("/audit-trail"))
    assert_response_status_code(response, 200)
    change_types = [item["change_type"] for item in response.json()]
    assert change_types.count("Create") == 3
    assert change_types.count("Delete") == 1
    assert all(item["auxiliary_device_name"] for item in response.json())

    uid = api_client.get(url()).json()["items"][1]["uid"]
    response = api_client.get(url(f"/{uid}/audit-trail"))
    assert_response_status_code(response, 200)
    res = response.json()
    assert [item["change_type"] for item in res] == ["Edit", "Edit", "Create"]
    assert "order" in res[0]["changes"]
    assert all(item["auxiliary_device_algorithm"] for item in res)


def test_locked_study_and_study_value_version(api_client):
    res_v1 = api_client.get(url()).json()
    audit_v1 = api_client.get(url("/audit-trail")).json()

    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)
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

    # selections survive the lock
    assert len(api_client.get(url()).json()["items"]) == 2

    uid = res_v1["items"][0]["uid"]
    locked_message = f"Study with UID '{study.uid}' is locked."
    for response in (
        api_client.post(
            url(), json={"auxiliary_device_term_uid": device_terms[0].term_uid}
        ),
        api_client.patch(url(f"/{uid}/order"), json={"new_order": 2}),
        api_client.delete(url(f"/{uid}")),
    ):
        assert_response_status_code(response, 400)
        assert response.json()["message"] == locked_message

    for item in audit_v1:
        item["study_version"] = mock.ANY
    assert api_client.get(url("/audit-trail")).json() == audit_v1

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
    response = api_client.post(
        url(), json={"auxiliary_device_term_uid": device_terms[0].term_uid}
    )
    assert_response_status_code(response, 201)

    res_new = api_client.get(url()).json()
    res_locked = api_client.get(url(), params={"study_value_version": "1"}).json()
    for item in res_v1["items"]:
        item["study_version"] = mock.ANY
    assert res_locked == res_v1
    assert len(res_new["items"]) == 3

    headers_locked = api_client.get(
        url("/headers"),
        params={"field_name": "auxiliary_device_name", "study_value_version": "1"},
    ).json()
    assert headers_locked == ["Device 2", "Device 3"]


def test_error_paths(api_client):
    # own study so the shared one keeps its expected state
    study_uid = TestUtils.create_study().uid
    TestUtils.set_study_standard_version(study_uid=study_uid)
    base = f"/studies/{study_uid}/study-auxiliary-devices"
    codelist_uid = device_terms[0].codelists[0].codelist_uid

    response = api_client.post(
        base, json={"auxiliary_device_term_uid": device_terms[0].term_uid, "order": 2}
    )
    assert_response_status_code(response, 400)
    assert response.json()["message"] == "Order is too big."

    removable = TestUtils.create_ct_term(codelist_uid=codelist_uid)
    uids = [
        api_client.post(base, json={"auxiliary_device_term_uid": term_uid}).json()[
            "uid"
        ]
        for term_uid in (device_terms[0].term_uid, removable.term_uid)
    ]

    response = api_client.patch(f"{base}/{uids[0]}/order", json={"new_order": 1})
    assert_response_status_code(response, 200)
    assert response.json()["order"] == 1

    for response in (
        api_client.patch(f"{base}/NotExisting/order", json={"new_order": 1}),
        api_client.delete(f"{base}/NotExisting"),
    ):
        assert_response_status_code(response, 404)

    # selection keeps working after its term leaves the codelist
    response = api_client.delete(
        f"/ct/codelists/{codelist_uid}/terms/{removable.term_uid}"
    )
    assert_response_status_code(response, 200)
    response = api_client.patch(f"{base}/{uids[1]}/order", json={"new_order": 1})
    assert_response_status_code(response, 200)
    assert_response_status_code(api_client.delete(f"{base}/{uids[1]}"), 204)

    for response in (
        api_client.patch(f"{base}/{uids[1]}/order", json={"new_order": 1}),
        api_client.delete(f"{base}/{uids[1]}"),
    ):
        assert_response_status_code(response, 404)

    draft = TestUtils.create_ct_term(codelist_uid=codelist_uid, approve=False)
    response = api_client.post(base, json={"auxiliary_device_term_uid": draft.term_uid})
    assert_response_status_code(response, 400)
    assert "has no approved version" in response.json()["message"]
    assert [item["uid"] for item in api_client.get(base).json()["items"]] == [uids[0]]


def test_submission_value_from_selected_codelist(api_client):
    study_uid = TestUtils.create_study().uid
    TestUtils.set_study_standard_version(study_uid=study_uid)
    base = f"/studies/{study_uid}/study-auxiliary-devices"
    codelist_uid = device_terms[0].codelists[0].codelist_uid
    term = TestUtils.create_ct_term(
        codelist_uid=codelist_uid, submission_value="OLD_DEVICE"
    )
    response = api_client.post(base, json={"auxiliary_device_term_uid": term.term_uid})
    assert_response_status_code(response, 201)
    uid = response.json()["uid"]

    # both leave an extra CTCodelistTerm linked to the term
    response = api_client.patch(
        f"/ct/terms/{term.term_uid}/codelists",
        json={
            "codelist_uid": codelist_uid,
            "order": 1,
            "submission_value": "NEW_DEVICE",
        },
    )
    assert_response_status_code(response, 200)
    response = api_client.post(
        f"/ct/codelists/{other_term.codelists[0].codelist_uid}/terms",
        json={"term_uid": term.term_uid, "submission_value": "OLD_DEVICE"},
    )
    assert_response_status_code(response, 201)

    response = api_client.get(f"{base}/{uid}")
    assert_response_status_code(response, 200)
    assert response.json()["auxiliary_device_submission_value"] == "NEW_DEVICE"
    response = api_client.get(base)
    assert_response_status_code(response, 200)
    assert [
        item["auxiliary_device_submission_value"] for item in response.json()["items"]
    ] == ["NEW_DEVICE"]

    # still resolved once the term has left the codelist
    response = api_client.delete(f"/ct/codelists/{codelist_uid}/terms/{term.term_uid}")
    assert_response_status_code(response, 200)
    response = api_client.patch(f"{base}/{uid}/order", json={"new_order": 1})
    assert_response_status_code(response, 200)
    assert response.json()["auxiliary_device_submission_value"] == "NEW_DEVICE"


def test_paging_with_changed_submission_value(api_client):
    study_uid = TestUtils.create_study().uid
    TestUtils.set_study_standard_version(study_uid=study_uid)
    base = f"/studies/{study_uid}/study-auxiliary-devices"
    codelist_uid = device_terms[0].codelists[0].codelist_uid
    term = TestUtils.create_ct_term(
        codelist_uid=codelist_uid, submission_value="PAGED_DEVICE"
    )
    # a changed submission value leaves a second CTCodelistTerm, doubling the rows
    response = api_client.patch(
        f"/ct/terms/{term.term_uid}/codelists",
        json={"codelist_uid": codelist_uid, "order": 1, "submission_value": "PAGED_2"},
    )
    assert_response_status_code(response, 200)
    for term_uid in (term.term_uid, device_terms[0].term_uid):
        response = api_client.post(base, json={"auxiliary_device_term_uid": term_uid})
        assert_response_status_code(response, 201)

    pages = [
        api_client.get(
            base, params={"page_size": 1, "page_number": page, "total_count": True}
        ).json()
        for page in (1, 2)
    ]
    assert [len(page["items"]) for page in pages] == [1, 1]
    assert {page["items"][0]["auxiliary_device_term_uid"] for page in pages} == {
        term.term_uid,
        device_terms[0].term_uid,
    }
    assert pages[0]["total"] == 2

    # the extra rows must not duplicate audit trail entries either
    assert len(api_client.get(f"{base}/audit-trail").json()) == 2
    uid = pages[0]["items"][0]["uid"]
    assert len(api_client.get(f"{base}/{uid}/audit-trail").json()) == 1
    response = api_client.get(
        f"{base}/headers", params={"field_name": "auxiliary_device_name"}
    )
    assert len(response.json()) == 2

    response = api_client.get(
        base,
        params={
            "filters": '{"auxiliary_device_submission_value": {"v": ["PAGED_2"]}}',
            "total_count": True,
        },
    )
    assert (len(response.json()["items"]), response.json()["total"]) == (1, 1)

    # sorting by submission value needs the has_term_root traversal
    for ascending, expected in (
        (True, ["DEVICE1", "PAGED_2"]),
        (False, ["PAGED_2", "DEVICE1"]),
    ):
        response = api_client.get(
            base,
            params={
                "sort_by": f'{{"auxiliary_device_submission_value": {str(ascending).lower()}}}'
            },
        )
        assert [
            item["auxiliary_device_submission_value"]
            for item in response.json()["items"]
        ] == expected


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
def test_export(api_client, export_format):
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url()
    )
    if export_format == "text/csv":
        assert "auxiliary_device_algorithm" in str(exported_data.read())
