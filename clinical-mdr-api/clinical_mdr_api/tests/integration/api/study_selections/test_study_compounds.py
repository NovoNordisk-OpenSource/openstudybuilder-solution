"""
Tests for /studies/{study_uid}/study-compounds endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import copy
import json
import logging
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.compound import Compound
from clinical_mdr_api.models.concepts.compound_alias import CompoundAlias
from clinical_mdr_api.models.concepts.concept import LagTime, NumericValueWithUnit
from clinical_mdr_api.models.concepts.medicinal_product import MedicinalProduct
from clinical_mdr_api.models.concepts.pharmaceutical_product import (
    PharmaceuticalProduct,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySelectionCompound,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

HEADERS = {"content-type": "application/json"}
BASE_URL = "/studies/{study_uid}/study-compounds"

rand: str
CREATE_STUDY_COMPOUND_PAYLOAD_OK: dict
study: Study
ct_term_dosage: CTTerm
ct_term_delivery_device: CTTerm
ct_term_dose_frequency: CTTerm
ct_term_dispenser: CTTerm
ct_term_roa: CTTerm
strength_value: NumericValueWithUnit
dose_value: NumericValueWithUnit
lag_time: LagTime
half_life: NumericValueWithUnit
compound: Compound
compound2: Compound
compound_alias: CompoundAlias
compound_alias1a: CompoundAlias
compound_alias2: CompoundAlias
compound_alias2a: CompoundAlias
pharmaceutical_product1: PharmaceuticalProduct
medicinal_product: MedicinalProduct
medicinal_product1: MedicinalProduct
medicinal_product2: MedicinalProduct
medicinal_products_all: list[MedicinalProduct]
study_compounds_all: list[StudySelectionCompound]


initialize_ct_data_map = {
    "TypeOfTreatment": [("CTTerm_000001", "CTTerm_000001")],
    "RouteOfAdministration": [("CTTerm_000002", "CTTerm_000002")],
    "DosageForm": [("CTTerm_000003", "CTTerm_000003")],
    "DispensedIn": [("CTTerm_000004", "CTTerm_000004")],
    "Device": [("CTTerm_000005", "CTTerm_000005")],
    "Formulation": [("CTTerm_000006", "CTTerm_000006")],
    "ReasonForMissingNullValue": [("CTTerm_000007", "CTTerm_000007")],
}


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studycompounds.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global BASE_URL
    global rand
    global study
    global CREATE_STUDY_COMPOUND_PAYLOAD_OK
    global ct_term_dosage
    global ct_term_delivery_device
    global ct_term_dose_frequency
    global ct_term_dispenser
    global ct_term_roa
    global dose_value
    global compound
    global compound2
    global compound_alias
    global compound_alias1a
    global compound_alias2
    global compound_alias2a
    global pharmaceutical_product1
    global medicinal_product
    global medicinal_product1
    global medicinal_product2
    global medicinal_products_all
    global study_compounds_all

    rand = TestUtils.random_str(10)

    # Create CT Terms
    ct_term_dosage = TestUtils.create_ct_term(sponsor_preferred_name="dosage_form_1")
    ct_term_delivery_device = TestUtils.create_ct_term(
        sponsor_preferred_name="delivery_device_1"
    )
    ct_term_dose_frequency = TestUtils.create_ct_term(
        sponsor_preferred_name="dose_frequency_1"
    )
    ct_term_dispenser = TestUtils.create_ct_term(sponsor_preferred_name="dispenser_1")
    ct_term_roa = TestUtils.create_ct_term(
        sponsor_preferred_name="route_of_administration_1"
    )

    # Create Numeric values with unit
    dose_value = TestUtils.create_numeric_value_with_unit(value=10, unit="mg")

    study = TestUtils.create_study()
    BASE_URL = BASE_URL.replace("{study_uid}", study.uid)

    catalogue = "SDTM CT"
    cdisc_package_name = "SDTM CT 2020-03-27"

    standards_ct_package_uid = TestUtils.create_ct_package(
        catalogue=catalogue, name=cdisc_package_name, approve_elements=False
    )
    TestUtils.create_study_standard_version(
        study_uid=study.uid, ct_package_uid=standards_ct_package_uid
    )

    compound = TestUtils.create_compound(name="name-AAA", approve=True)
    compound2 = TestUtils.create_compound(name="name-BBB", approve=True)

    compound_alias = TestUtils.create_compound_alias(
        name="compAlias-AAA", compound_uid=compound.uid, approve=True
    )
    compound_alias1a = TestUtils.create_compound_alias(
        name="compAlias-AAA-1a", compound_uid=compound.uid, approve=True
    )
    compound_alias2 = TestUtils.create_compound_alias(
        name="compAlias-BBB", compound_uid=compound2.uid, approve=True
    )
    compound_alias2a = TestUtils.create_compound_alias(
        name="compAlias-BBB-1a", compound_uid=compound2.uid, approve=True
    )

    pharmaceutical_product1 = TestUtils.create_pharmaceutical_product(
        external_id="external_id1",
        dosage_form_uids=[ct_term_dosage.term_uid],
        route_of_administration_uids=[ct_term_roa.term_uid],
        formulations=[],
        approve=True,
    )
    medicinal_product1 = TestUtils.create_medicinal_product(
        name="medicinal_product1",
        external_id="external_id1",
        dose_value_uids=[dose_value.uid],
        dose_frequency_uid=ct_term_dose_frequency.term_uid,
        delivery_device_uid=ct_term_delivery_device.term_uid,
        dispenser_uid=ct_term_dispenser.term_uid,
        pharmaceutical_product_uids=[pharmaceutical_product1.uid],
        compound_uid=compound.uid,
        approve=True,
    )
    medicinal_product2 = TestUtils.create_medicinal_product(
        name="medicinal_product2",
        external_id="external_id2",
        dose_value_uids=[dose_value.uid],
        dose_frequency_uid=ct_term_dose_frequency.term_uid,
        delivery_device_uid=ct_term_delivery_device.term_uid,
        dispenser_uid=ct_term_dispenser.term_uid,
        pharmaceutical_product_uids=[pharmaceutical_product1.uid],
        compound_uid=compound2.uid,
        approve=True,
    )

    medicinal_products_all = []
    for idx in range(0, 5):
        pharmaceutical_product = TestUtils.create_pharmaceutical_product(
            external_id=f"external_id_{rand}_{idx}",
            dosage_form_uids=[ct_term_dosage.term_uid],
            route_of_administration_uids=[ct_term_roa.term_uid],
            formulations=[],
            approve=True,
        )
        medicinal_product = TestUtils.create_medicinal_product(
            name=f"medicinal_product_{rand}_{idx}",
            external_id=f"external_id_{rand}_{idx}",
            dose_value_uids=[dose_value.uid],
            dose_frequency_uid=ct_term_dose_frequency.term_uid,
            delivery_device_uid=ct_term_delivery_device.term_uid,
            dispenser_uid=ct_term_dispenser.term_uid,
            pharmaceutical_product_uids=[pharmaceutical_product.uid],
            compound_uid=compound.uid,
            approve=True,
        )
        medicinal_products_all.append(medicinal_product)

    study_compounds_all = []
    for idx in range(0, 5):
        study_compound = TestUtils.create_study_compound(
            study_uid=study.uid,
            compound_alias_uid=compound_alias.uid,
            medicinal_product_uid=medicinal_products_all[idx].uid,
            type_of_treatment_uid="CTTerm_000001",
            dispenser_uid=ct_term_dispenser.term_uid,
            dose_value_uid=dose_value.uid,
            dose_frequency_uid=ct_term_dose_frequency.term_uid,
            delivery_device_uid=ct_term_delivery_device.term_uid,
            other_info=f"other_info_{rand}_{idx}",
        )
        study_compounds_all.append(study_compound)

    CREATE_STUDY_COMPOUND_PAYLOAD_OK = {
        "compound_alias_uid": compound_alias.uid,
        "medicinal_product_uid": medicinal_product.uid,
        "type_of_treatment_uid": "CTTerm_000001",
        "other_info": f"other_info_{rand}",
        "reason_for_missing_null_value_uid": None,
    }

    yield


STUDY_COMPOUND_FIELDS_ALL = [
    "study_uid",
    "study_compound_uid",
    "compound",
    "compound_alias",
    "medicinal_product",
    "type_of_treatment",
    "start_date",
    "author_username",
    "order",
    "study_version",
    "project_number",
    "project_name",
    "dispenser",
    "dose_frequency",
    "delivery_device",
    "other_info",
    "reason_for_missing_null_value",
    "study_compound_dosing_count",
]

STUDY_COMPOUND_FIELDS_NOT_NULL = [
    "study_uid",
    "study_compound_uid",
    "compound",
    "compound_alias",
    "medicinal_product",
    "start_date",
    "order",
    "study_version",
]

STUDY_COMPOUND_FIELDS_AUDIT_TRAIL_ALL = [
    "study_uid",
    "study_compound_uid",
    "compound",
    "compound_alias",
    "medicinal_product",
    "type_of_treatment",
    "start_date",
    "end_date",
    "author_username",
    "order",
    "dispenser",
    "dose_frequency",
    "delivery_device",
    "other_info",
    "reason_for_missing_null_value",
    "status",
    "change_type",
]

STUDY_COMPOUND_FIELDS_AUDIT_TRAIL_NOT_NULL = [
    "study_uid",
    "study_compound_uid",
    "compound",
    "compound_alias",
    "medicinal_product",
    "start_date",
    "author_username",
    "order",
    "change_type",
]


def test_get_study_compounds(api_client):
    response = api_client.get(f"{BASE_URL}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, STUDY_COMPOUND_FIELDS_ALL, STUDY_COMPOUND_FIELDS_NOT_NULL
        )


def test_get_study_compound_by_id(api_client):
    response = api_client.get(f"{BASE_URL}/{study_compounds_all[0].study_compound_uid}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    TestUtils.assert_response_shape_ok(
        res, STUDY_COMPOUND_FIELDS_ALL, STUDY_COMPOUND_FIELDS_NOT_NULL
    )

    assert res["study_compound_uid"] == study_compounds_all[0].study_compound_uid
    assert res["study_uid"] == study.uid
    assert res["order"] == study_compounds_all[0].order
    assert res["project_number"] == study_compounds_all[0].project_number
    assert res["project_name"] == study_compounds_all[0].project_name
    assert res["dispenser"]["term_uid"] == ct_term_dispenser.term_uid
    assert res["dispenser"]["name"] == ct_term_dispenser.sponsor_preferred_name
    assert res["dose_frequency"]["term_uid"] == ct_term_dose_frequency.term_uid
    assert (
        res["dose_frequency"]["name"] == ct_term_dose_frequency.sponsor_preferred_name
    )
    assert res["delivery_device"]["term_uid"] == ct_term_delivery_device.term_uid
    assert (
        res["delivery_device"]["name"] == ct_term_delivery_device.sponsor_preferred_name
    )
    assert res["other_info"] == study_compounds_all[0].other_info
    assert (
        res["study_compound_dosing_count"]
        == study_compounds_all[0].study_compound_dosing_count
    )


def test_create_and_remove_study_compound_selection(api_client):
    response = api_client.post(
        f"{BASE_URL}",
        json={
            "compound_alias_uid": compound_alias.uid,
            "medicinal_product_uid": medicinal_product1.uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # Check fields included in the response
    TestUtils.assert_response_shape_ok(
        res, STUDY_COMPOUND_FIELDS_ALL, STUDY_COMPOUND_FIELDS_NOT_NULL
    )

    response = api_client.get(f"{BASE_URL}/{res['study_compound_uid']}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Delete the created study compound
    response = api_client.delete(f"{BASE_URL}/{res['study_compound_uid']}")
    assert_response_status_code(response, 204)

    # Check that the study compound has been deleted
    response = api_client.get(f"{BASE_URL}/{res['study_compound_uid']}")
    assert_response_status_code(response, 404)


def test_get_study_compounds_for_all_studies(api_client):
    response = api_client.get("/study-compounds?total_count=true&page_size=100")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert len(res["items"]) == len(study_compounds_all)
    assert res["total"] == len(study_compounds_all)
    assert res["page"] == 1
    assert res["size"] == 100

    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, STUDY_COMPOUND_FIELDS_ALL, STUDY_COMPOUND_FIELDS_NOT_NULL
        )


@pytest.mark.parametrize(
    "field_name, expected_returned_values",
    [
        pytest.param("study_uid", ["{study_id}"]),
        pytest.param("dispenser", ["{dispenser}"]),
        pytest.param("dose_frequency", ["{dose_frequency}"]),
        pytest.param("delivery_device", ["{delivery_device}"]),
    ],
)
def test_get_study_compounds_headers(api_client, field_name, expected_returned_values):
    url = f"{BASE_URL}/headers?field_name={field_name}&page_size=100"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) >= len(expected_returned_values)

    for val in expected_returned_values:
        val = val.replace("{study_id}", study.uid)
        val = val.replace("{dispenser}", ct_term_dispenser.sponsor_preferred_name)
        val = val.replace(
            "{dose_frequency}", ct_term_dose_frequency.sponsor_preferred_name
        )
        val = val.replace(
            "{delivery_device}", ct_term_delivery_device.sponsor_preferred_name
        )
        assert val in res


@pytest.mark.parametrize(
    "field_name, expected_returned_values",
    [
        pytest.param("study_uid", ["{study_id}"]),
        pytest.param("dispenser", ["{dispenser}"]),
        pytest.param("dose_frequency", ["{dose_frequency}"]),
        pytest.param("delivery_device", ["{delivery_device}"]),
    ],
)
def test_get_study_compounds_headers_for_all_studies(
    api_client, field_name, expected_returned_values
):
    url = f"/study-compounds/headers?field_name={field_name}&page_size=100"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) >= len(expected_returned_values)

    for val in expected_returned_values:
        val = val.replace("{study_id}", study.uid)
        val = val.replace("{dispenser}", ct_term_dispenser.sponsor_preferred_name)
        val = val.replace(
            "{dose_frequency}", ct_term_dose_frequency.sponsor_preferred_name
        )
        val = val.replace(
            "{delivery_device}", ct_term_delivery_device.sponsor_preferred_name
        )
        assert val in res


def test_change_order_of_study_compound(api_client):
    url = f"{BASE_URL}/{study_compounds_all[0].study_compound_uid}/order"
    response = api_client.patch(url, json={"new_order": 2})
    res = response.json()
    assert_response_status_code(response, 200)

    assert res["order"] == 2
    assert res["study_compound_uid"] == study_compounds_all[0].study_compound_uid

    # Get all study compounds
    url = BASE_URL
    response = api_client.get(url)
    res = response.json()
    assert_response_status_code(response, 200)

    # Check that the order has been changed
    assert res["items"][0]["order"] == 1
    assert (
        res["items"][0]["study_compound_uid"]
        == study_compounds_all[1].study_compound_uid
    )

    assert res["items"][1]["order"] == 2
    assert (
        res["items"][1]["study_compound_uid"]
        == study_compounds_all[0].study_compound_uid
    )

    assert res["items"][2]["order"] == 3
    assert (
        res["items"][2]["study_compound_uid"]
        == study_compounds_all[2].study_compound_uid
    )

    assert res["items"][3]["order"] == 4
    assert (
        res["items"][3]["study_compound_uid"]
        == study_compounds_all[3].study_compound_uid
    )

    assert res["items"][4]["order"] == 5
    assert (
        res["items"][4]["study_compound_uid"]
        == study_compounds_all[4].study_compound_uid
    )


def test_change_order_of_study_compound_minus_one(api_client):
    url = f"{BASE_URL}/{study_compounds_all[0].study_compound_uid}/order"

    # Try to set order to -1 => Order will be set to 1
    response = api_client.patch(url, json={"new_order": -1})
    res = response.json()
    assert_response_status_code(response, 200)

    assert res["order"] == 1
    assert res["study_compound_uid"] == study_compounds_all[0].study_compound_uid

    # Get all study compounds
    url = BASE_URL
    response = api_client.get(url)
    res = response.json()
    assert_response_status_code(response, 200)

    # Check that the order has been changed
    assert res["items"][0]["order"] == 1
    assert (
        res["items"][0]["study_compound_uid"]
        == study_compounds_all[0].study_compound_uid
    )

    assert res["items"][1]["order"] == 2
    assert (
        res["items"][1]["study_compound_uid"]
        == study_compounds_all[1].study_compound_uid
    )

    assert res["items"][2]["order"] == 3
    assert (
        res["items"][2]["study_compound_uid"]
        == study_compounds_all[2].study_compound_uid
    )

    assert res["items"][3]["order"] == 4
    assert (
        res["items"][3]["study_compound_uid"]
        == study_compounds_all[3].study_compound_uid
    )

    assert res["items"][4]["order"] == 5
    assert (
        res["items"][4]["study_compound_uid"]
        == study_compounds_all[4].study_compound_uid
    )


def test_change_order_of_study_compound_100(api_client):
    url = f"{BASE_URL}/{study_compounds_all[0].study_compound_uid}/order"

    # Try to set order to 100 => Order will be set to 5 (i.e. to the total number of study compounds)
    response = api_client.patch(url, json={"new_order": 100})
    res = response.json()
    assert_response_status_code(response, 200)

    assert res["order"] == len(study_compounds_all)
    assert res["study_compound_uid"] == study_compounds_all[0].study_compound_uid

    # Get all study compounds
    url = BASE_URL
    response = api_client.get(url)
    res = response.json()
    assert_response_status_code(response, 200)

    # Check that the order has been changed
    assert res["items"][0]["order"] == 1
    assert (
        res["items"][0]["study_compound_uid"]
        == study_compounds_all[1].study_compound_uid
    )

    assert res["items"][1]["order"] == 2
    assert (
        res["items"][1]["study_compound_uid"]
        == study_compounds_all[2].study_compound_uid
    )

    assert res["items"][2]["order"] == 3
    assert (
        res["items"][2]["study_compound_uid"]
        == study_compounds_all[3].study_compound_uid
    )

    assert res["items"][3]["order"] == 4
    assert (
        res["items"][3]["study_compound_uid"]
        == study_compounds_all[4].study_compound_uid
    )

    assert res["items"][4]["order"] == 5
    assert (
        res["items"][4]["study_compound_uid"]
        == study_compounds_all[0].study_compound_uid
    )


def test_patch_study_compounds_medicinal_product(api_client):
    # Create a new study compound first
    response = api_client.post(
        f"{BASE_URL}",
        json={
            "compound_alias_uid": compound_alias.uid,
            "medicinal_product_uid": medicinal_product1.uid,
            "dose_frequency_uid": ct_term_dose_frequency.term_uid,
            "delivery_device_uid": ct_term_delivery_device.term_uid,
            "dispenser_uid": ct_term_dispenser.term_uid,
        },
    )
    initial_study_compound = response.json()
    assert_response_status_code(response, 201)

    # Modify the medicinal product of the just-created study compound
    url = f"{BASE_URL}/{initial_study_compound['study_compound_uid']}"
    response = api_client.patch(
        url, json={"medicinal_product_uid": medicinal_products_all[1].uid}
    )

    res = response.json()
    assert_response_status_code(response, 200)

    assert res["medicinal_product"]["uid"] == medicinal_products_all[1].uid
    assert res["study_compound_uid"] == initial_study_compound["study_compound_uid"]

    # Get the updated study compound and assert that only the medicinal product has been changed
    response = api_client.get(url)
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["medicinal_product"]["uid"] == medicinal_products_all[1].uid
    assert res["compound"] == initial_study_compound["compound"]
    assert res["compound_alias"] == initial_study_compound["compound_alias"]
    assert res["study_compound_uid"] == initial_study_compound["study_compound_uid"]
    assert res["project_number"] == initial_study_compound["project_number"]
    assert res["project_name"] == initial_study_compound["project_name"]
    assert res["dispenser"]["term_uid"] == ct_term_dispenser.term_uid
    assert res["dispenser"]["name"] == ct_term_dispenser.sponsor_preferred_name
    assert res["dose_frequency"]["term_uid"] == ct_term_dose_frequency.term_uid
    assert (
        res["dose_frequency"]["name"] == ct_term_dose_frequency.sponsor_preferred_name
    )
    assert res["delivery_device"]["term_uid"] == ct_term_delivery_device.term_uid
    assert (
        res["delivery_device"]["name"] == ct_term_delivery_device.sponsor_preferred_name
    )
    assert res["other_info"] == initial_study_compound["other_info"]
    assert (
        res["study_compound_dosing_count"]
        == initial_study_compound["study_compound_dosing_count"]
    )


def test_patch_study_compounds_compound_alias(api_client):
    # Create a new study compound first
    response = api_client.post(
        f"{BASE_URL}",
        json={
            "compound_alias_uid": compound_alias.uid,
            "medicinal_product_uid": medicinal_product1.uid,
            "dose_frequency_uid": ct_term_dose_frequency.term_uid,
            "delivery_device_uid": ct_term_delivery_device.term_uid,
            "dispenser_uid": ct_term_dispenser.term_uid,
        },
    )
    initial_study_compound = response.json()
    assert_response_status_code(response, 201)

    # Modify the compound alias of the just-created study compound
    url = f"{BASE_URL}/{initial_study_compound['study_compound_uid']}"
    response = api_client.patch(url, json={"compound_alias_uid": compound_alias1a.uid})

    res = response.json()
    assert_response_status_code(response, 200)

    assert res["compound_alias"]["uid"] == compound_alias1a.uid
    assert res["study_compound_uid"] == initial_study_compound["study_compound_uid"]

    # Get the updated study compound and assert that only the compound/compound alias have been changed
    response = api_client.get(url)
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["medicinal_product"] == initial_study_compound["medicinal_product"]
    assert res["compound"]["uid"] == compound.uid
    assert res["compound_alias"]["uid"] == compound_alias1a.uid
    assert res["study_compound_uid"] == initial_study_compound["study_compound_uid"]
    assert res["project_number"] == initial_study_compound["project_number"]
    assert res["project_name"] == initial_study_compound["project_name"]
    assert res["dispenser"]["term_uid"] == ct_term_dispenser.term_uid
    assert res["dispenser"]["name"] == ct_term_dispenser.sponsor_preferred_name
    assert res["dose_frequency"]["term_uid"] == ct_term_dose_frequency.term_uid
    assert (
        res["dose_frequency"]["name"] == ct_term_dose_frequency.sponsor_preferred_name
    )
    assert res["delivery_device"]["term_uid"] == ct_term_delivery_device.term_uid
    assert (
        res["delivery_device"]["name"] == ct_term_delivery_device.sponsor_preferred_name
    )
    assert res["other_info"] == initial_study_compound["other_info"]
    assert (
        res["study_compound_dosing_count"]
        == initial_study_compound["study_compound_dosing_count"]
    )


def test_get_study_compounds_audit_trail(api_client):
    # Get audit trail for single study compound
    response = api_client.get(
        f"{BASE_URL}/{study_compounds_all[0].study_compound_uid}/audit-trail",
    )
    res = response.json()
    assert_response_status_code(response, 200)

    # Check fields included in the response
    for item in res:
        TestUtils.assert_response_shape_ok(
            item,
            STUDY_COMPOUND_FIELDS_AUDIT_TRAIL_ALL,
            STUDY_COMPOUND_FIELDS_AUDIT_TRAIL_NOT_NULL,
        )
    assert len(res) >= 1

    # Get audit trail for all study compounds
    response = api_client.get(
        f"{BASE_URL}/audit-trail",
    )
    res = response.json()
    assert_response_status_code(response, 200)

    # Check fields included in the response
    for item in res:
        TestUtils.assert_response_shape_ok(
            item,
            STUDY_COMPOUND_FIELDS_AUDIT_TRAIL_ALL,
            STUDY_COMPOUND_FIELDS_AUDIT_TRAIL_NOT_NULL,
        )
    assert len(res) >= 4


def test_compound_modify_actions_on_locked_study(api_client):
    response = api_client.post(
        f"{BASE_URL}",
        json={
            "compound_alias_uid": compound_alias.uid,
            "medicinal_product_uid": medicinal_product1.uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # get audit trail
    response = api_client.get(f"{BASE_URL}/audit-trail/")
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res
    compound_uid = res[0]["study_compound_uid"]

    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert_response_status_code(response, 200)

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks",
        json={"change_description": "Lock 1"},
    )
    assert_response_status_code(response, 201)

    response = api_client.post(
        f"{BASE_URL}",
        json={
            "compound_alias_uid": compound_alias.uid,
            "medicinal_product_uid": medicinal_product1.uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."
    # edit compound
    response = api_client.patch(
        f"{BASE_URL}/{compound_uid}",
        json={"type_of_treatment_uid": "CTTerm_000001"},
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(f"{BASE_URL}/audit-trail/")
    assert_response_status_code(response, 200)
    res = response.json()
    assert old_res == res

    # test cannot delete
    response = api_client.delete(f"{BASE_URL}/{compound_uid}")
    assert_response_status_code(response, 400)
    assert response.json()["message"] == f"Study with UID '{study.uid}' is locked."


def test_get_compounds_data_for_specific_study_version(api_client):
    """
    This test checks the study versioning on study compounds
    """
    # get compound data for first lock
    response = api_client.get(f"{BASE_URL}/")
    res = response.json()
    assert_response_status_code(response, 200)
    res_old = res

    # Unlock
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert_response_status_code(response, 200)

    response = api_client.post(
        f"{BASE_URL}",
        json={
            "compound_alias_uid": compound_alias2.uid,
            "medicinal_product_uid": medicinal_product2.uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # check the study compounds for version 1 is same as first locked
    res_new = api_client.get(
        f"{BASE_URL}",
    ).json()
    res_v1 = api_client.get(
        f"{BASE_URL}?study_value_version=1",
    ).json()
    for i, _ in enumerate(res_old["items"]):
        res_old["items"][i]["study_version"] = mock.ANY
    assert res_v1 == res_old
    assert res_v1 != res_new


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
def test_get_study_compounds_csv_xml_excel(api_client, export_format):
    url = BASE_URL
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        headers = [
            "uid",
            "compound",
            "pharma_class",
            "substance_names",
            "unii_codes",
            "type_of_treatment",
            "dose_frequency",
            "dose_value",
            "dispenser",
            "delivery_device",
            "other",
            "reason_for_missing",
            "study_uid",
            "study_version",
        ]
        for header in headers:
            assert header in str(exported_data.read())
        # assert "LATEST" in str(exported_data.read())


def test_negative_create_medicinal_product_wrong_links(api_client):
    # Try to create study compound with non-existing compound alias
    payload = copy.deepcopy(CREATE_STUDY_COMPOUND_PAYLOAD_OK)
    payload["compound_alias_uid"] = "NON_EXISTING_UID"
    response = api_client.post(BASE_URL, data=json.dumps(payload), headers=HEADERS)
    assert_response_status_code(response, 400)

    res = response.json()
    assert (
        res["message"]
        == "There is no approved Compound Alias with UID 'NON_EXISTING_UID'."
    )

    # Try to create study compound with non-existing medicinal product
    payload = copy.deepcopy(CREATE_STUDY_COMPOUND_PAYLOAD_OK)
    payload["medicinal_product_uid"] = "NON_EXISTING_UID"
    response = api_client.post(BASE_URL, data=json.dumps(payload), headers=HEADERS)
    assert_response_status_code(response, 400)

    res = response.json()
    assert (
        res["message"]
        == "There is no approved Medicinal Product with UID 'NON_EXISTING_UID'."
    )

    # Try to create study compound with missing compound alias uid
    payload = copy.deepcopy(CREATE_STUDY_COMPOUND_PAYLOAD_OK)
    del payload["compound_alias_uid"]
    response = api_client.post(BASE_URL, data=json.dumps(payload), headers=HEADERS)

    assert_response_status_code(response, 422)
    res = response.json()
    assert res["detail"][0]["type"] == "missing"
    assert res["detail"][0]["loc"] == ["body", "compound_alias_uid"]
    assert res["detail"][0]["msg"] == "Field required"
    # Try to create study compound with missing medicinal product uid
    payload = copy.deepcopy(CREATE_STUDY_COMPOUND_PAYLOAD_OK)
    del payload["medicinal_product_uid"]
    response = api_client.post(BASE_URL, data=json.dumps(payload), headers=HEADERS)

    assert_response_status_code(response, 422)
    res = response.json()
    assert res["detail"][0]["type"] == "missing"
    assert res["detail"][0]["loc"] == ["body", "medicinal_product_uid"]
    assert res["detail"][0]["msg"] == "Field required"
