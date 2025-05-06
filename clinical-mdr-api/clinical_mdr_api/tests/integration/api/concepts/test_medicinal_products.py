"""
Tests for /concepts/medicinal-products endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

import copy

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments
import json
import logging
from functools import reduce

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.active_substance import ActiveSubstance
from clinical_mdr_api.models.concepts.compound import Compound
from clinical_mdr_api.models.concepts.concept import LagTime, NumericValueWithUnit
from clinical_mdr_api.models.concepts.medicinal_product import MedicinalProduct
from clinical_mdr_api.models.concepts.pharmaceutical_product import (
    PharmaceuticalProduct,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.dictionaries.dictionary_codelist import DictionaryCodelist
from clinical_mdr_api.models.dictionaries.dictionary_term import DictionaryTerm
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import CT_CODELIST_NAMES, TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code

log = logging.getLogger(__name__)

HEADERS = {"content-type": "application/json"}
BASE_URL = "/concepts/medicinal-products"

# Global variables shared between fixtures and tests
rand: str
CREATE_MEDICINAL_PRODUCT_PAYLOAD_OK: dict
medicinal_products_all: list[MedicinalProduct]
pharmaceutical_products_all: list[PharmaceuticalProduct]
compound: Compound
ct_term_roa: CTTerm
ct_term_dose_form: CTTerm
active_substances_all: list[ActiveSubstance]
dictionary_term_unii: DictionaryTerm
unii_codelist: DictionaryCodelist
strength: NumericValueWithUnit
lag_time: LagTime
half_life: NumericValueWithUnit
formulation_1: dict
dose_value: NumericValueWithUnit
ct_term_delivery_device: CTTerm
ct_term_dose_frequency: CTTerm
ct_term_dispenser: CTTerm


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "medicinal-products.api"
    inject_and_clear_db(db_name)
    inject_base_data()

    global rand
    global CREATE_MEDICINAL_PRODUCT_PAYLOAD_OK
    global medicinal_products_all
    global pharmaceutical_products_all
    global compound
    global ct_term_dose_form
    global ct_term_roa
    global active_substances_all
    global dictionary_term_unii
    global unii_codelist
    global strength
    global lag_time
    global half_life
    global formulation_1
    global dose_value
    global ct_term_delivery_device
    global ct_term_dose_frequency
    global ct_term_dispenser

    rand = TestUtils.random_str(10)

    # Get codelist UIDs
    relevant_codelists = [
        CT_CODELIST_NAMES.delivery_device,
        CT_CODELIST_NAMES.dosage_form,
        CT_CODELIST_NAMES.frequency,
        CT_CODELIST_NAMES.roa,
        CT_CODELIST_NAMES.dispenser,
        CT_CODELIST_NAMES.adverse_events,
    ]
    codelists = TestUtils.get_codelists_by_names(relevant_codelists)

    # Create CT Terms
    ct_term_dose_form = TestUtils.create_ct_term(
        sponsor_preferred_name="dosage_form_1",
        codelist_uid=TestUtils.get_codelist_uid_by_name(
            codelists, CT_CODELIST_NAMES.dosage_form
        ),
    )
    ct_term_roa = TestUtils.create_ct_term(
        sponsor_preferred_name="route_of_administration_1",
        codelist_uid=TestUtils.get_codelist_uid_by_name(
            codelists, CT_CODELIST_NAMES.roa
        ),
    )

    ct_term_delivery_device = TestUtils.create_ct_term(
        sponsor_preferred_name="delivery_device_1",
        codelist_uid=TestUtils.get_codelist_uid_by_name(
            codelists, CT_CODELIST_NAMES.delivery_device
        ),
    )
    ct_term_dose_frequency = TestUtils.create_ct_term(
        sponsor_preferred_name="dose_frequency_1",
        codelist_uid=TestUtils.get_codelist_uid_by_name(
            codelists, CT_CODELIST_NAMES.frequency
        ),
    )
    ct_term_dispenser = TestUtils.create_ct_term(
        sponsor_preferred_name="dispenser_1",
        codelist_uid=TestUtils.get_codelist_uid_by_name(
            codelists, CT_CODELIST_NAMES.dispenser
        ),
    )

    TestUtils.create_library("UNII")
    unii_codelist = TestUtils.create_dictionary_codelist(
        name="UNII", library_name="UNII"
    )
    dictionary_term_unii = TestUtils.create_dictionary_term(
        codelist_uid=unii_codelist.codelist_uid,
        library_name=unii_codelist.library_name,
        dictionary_id="P7YU3ED05N",
        name="INSULIN ICODEC",
    )

    strength = TestUtils.create_numeric_value_with_unit(value=5, unit="mg/mL")
    half_life = TestUtils.create_numeric_value_with_unit(value=8, unit="hours")
    lag_time = TestUtils.create_lag_time(value=7, unit="days")
    dose_value = TestUtils.create_numeric_value_with_unit(value=10, unit="mg")

    # Create a compound
    compound = TestUtils.create_compound(
        name=f"Compound A-{rand}",
    )

    # Create some active substances
    active_substances_all = []
    active_substances_all.append(
        TestUtils.create_active_substance(
            unii_term_uid=dictionary_term_unii.term_uid,
            external_id=f"external_id_a-{rand}",
            analyte_number=f"analyte A-{rand}",
            short_number=f"short number A-{rand}",
            long_number=f"long number A-{rand}",
            inn=f"inn A-{rand}",
        )
    )

    active_substances_all.append(
        TestUtils.create_active_substance(analyte_number=f"analyte_number-AAA-{rand}")
    )
    active_substances_all.append(
        TestUtils.create_active_substance(analyte_number=f"analyte_number-BBB-{rand}")
    )

    # Create some pharmaceutical products
    ingredient_1 = {
        "external_id": f"ingredient-prodex-id-a-{rand}",
        "formulation_name": "formulation-name-a",
        "active_substance_uid": active_substances_all[0].uid,
        "strength_uid": strength.uid,
        "half_life_uid": half_life.uid,
        "lag_time_uids": [lag_time.uid],
    }
    ingredient_2 = {
        "external_id": f"ingredient-prodex-id-b-{rand}",
        "formulation_name": "formulation-name-b",
        "active_substance_uid": active_substances_all[1].uid,
        "strength_uid": strength.uid,
        "half_life_uid": half_life.uid,
        "lag_time_uids": [lag_time.uid],
    }

    formulation_1 = {
        "external_id": f"formulation-prodex-id-a-{rand}",
        "ingredients": [ingredient_1, ingredient_2],
    }

    pharmaceutical_products_all = []
    pharmaceutical_products_all.append(
        TestUtils.create_pharmaceutical_product(
            external_id=f"external_id_a-{rand}",
            dosage_form_uids=[ct_term_dose_form.term_uid],
            route_of_administration_uids=[ct_term_roa.term_uid],
            formulations=[formulation_1],
        )
    )
    pharmaceutical_products_all.append(
        TestUtils.create_pharmaceutical_product(
            external_id=f"external_id_b-{rand}",
            dosage_form_uids=[ct_term_dose_form.term_uid],
            route_of_administration_uids=[ct_term_roa.term_uid],
            formulations=[formulation_1],
        )
    )

    # Create some medicinal products
    medicinal_products_all = []
    medicinal_products_all.append(
        TestUtils.create_medicinal_product(
            compound_uid=compound.uid,
            external_id=f"external_id_a-{rand}",
            name=f"name_A-{rand}",
            name_sentence_case=f"name_a-{rand}",
            pharmaceutical_product_uids=[x.uid for x in pharmaceutical_products_all],
            dose_value_uids=[dose_value.uid],
            dose_frequency_uid=ct_term_dose_frequency.term_uid,
            delivery_device_uid=ct_term_delivery_device.term_uid,
            dispenser_uid=ct_term_dispenser.term_uid,
        )
    )
    medicinal_products_all.append(
        TestUtils.create_medicinal_product(
            compound_uid=compound.uid,
            external_id=f"external_id_b-{rand}",
            name=f"name_B-{rand}",
            name_sentence_case=f"name_b-{rand}",
            pharmaceutical_product_uids=[x.uid for x in pharmaceutical_products_all],
            dose_value_uids=[dose_value.uid],
            dose_frequency_uid=ct_term_dose_frequency.term_uid,
            delivery_device_uid=ct_term_delivery_device.term_uid,
            dispenser_uid=ct_term_dispenser.term_uid,
        )
    )

    for index in range(5):
        medicinal_product_a = TestUtils.create_medicinal_product(
            compound_uid=compound.uid,
            external_id=f"external_id_AAA-{rand}_{index}",
            name=f"name_AAA-{rand}_{index}",
            name_sentence_case=f"name_aaa-{rand}_{index}",
            pharmaceutical_product_uids=[x.uid for x in pharmaceutical_products_all],
            dose_value_uids=[dose_value.uid],
            dose_frequency_uid=ct_term_dose_frequency.term_uid,
            delivery_device_uid=ct_term_delivery_device.term_uid,
            dispenser_uid=ct_term_dispenser.term_uid,
        )
        medicinal_products_all.append(medicinal_product_a)

        medicinal_product_b = TestUtils.create_medicinal_product(
            compound_uid=compound.uid,
            external_id=f"external_id_BBB-{rand}_{index}",
            name=f"name_BBB-{rand}_{index}",
            name_sentence_case=f"name_bbb-{rand}_{index}",
            pharmaceutical_product_uids=[x.uid for x in pharmaceutical_products_all],
            dose_value_uids=[dose_value.uid],
            dose_frequency_uid=ct_term_dose_frequency.term_uid,
            delivery_device_uid=ct_term_delivery_device.term_uid,
            dispenser_uid=ct_term_dispenser.term_uid,
        )
        medicinal_products_all.append(medicinal_product_b)

        medicinal_product_c = TestUtils.create_medicinal_product(
            compound_uid=compound.uid,
            external_id=f"external_id_XXX-{rand}_{index}",
            name=f"name_XXX-{rand}_{index}",
            name_sentence_case=f"name_xxx-{rand}_{index}",
        )
        medicinal_products_all.append(medicinal_product_c)

        medicinal_product_d = TestUtils.create_medicinal_product(
            compound_uid=compound.uid,
            external_id=f"external_id_YYY-{rand}_{index}",
            name=f"name_YYY-{rand}_{index}",
            name_sentence_case=f"name_yyy-{rand}_{index}",
        )
        medicinal_products_all.append(medicinal_product_d)

    CREATE_MEDICINAL_PRODUCT_PAYLOAD_OK = {
        "library_name": "Sponsor",
        "external_id": f"external_id-NEW-{rand}",
        "name": f"name-NEW-{rand}",
        "name_sentence_case": f"name-new-{rand}",
        "compound_uid": compound.uid,
        "pharmaceutical_product_uids": [pharmaceutical_products_all[0].uid],
        "dose_frequency_uid": ct_term_dose_frequency.term_uid,
        "delivery_device_uid": ct_term_delivery_device.term_uid,
        "dose_value_uids": [dose_value.uid],
        "dispenser_uid": ct_term_dispenser.term_uid,
    }

    yield


MEDICINAL_PRODUCT_FIELDS_ALL = [
    "uid",
    "library_name",
    "start_date",
    "end_date",
    "status",
    "version",
    "change_description",
    "author_username",
    "possible_actions",
    "external_id",
    "name",
    "name_sentence_case",
    "pharmaceutical_products",
    "compound",
    "dose_values",
    "dose_frequency",
    "delivery_device",
    "dispenser",
]

MEDICINAL_PRODUCT_FIELDS_NOT_NULL = [
    "uid",
    "start_date",
    "library_name",
    "status",
    "version",
    "possible_actions",
    "dose_values",
    "compound",
    "pharmaceutical_products",
    "name",
    "name_sentence_case",
]


def test_get_medicinal_product(api_client):
    response = api_client.get(f"{BASE_URL}/{medicinal_products_all[0].uid}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(list(res.keys())) == set(MEDICINAL_PRODUCT_FIELDS_ALL)
    for key in MEDICINAL_PRODUCT_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == medicinal_products_all[0].uid
    assert res["external_id"] == f"external_id_a-{rand}"
    assert res["name"] == f"name_A-{rand}"
    assert res["name_sentence_case"] == f"name_a-{rand}"
    assert res["library_name"] == "Sponsor"

    assert res["compound"]["uid"] == compound.uid
    assert res["compound"]["name"] == compound.name

    assert (
        res["pharmaceutical_products"][0]["external_id"]
        == pharmaceutical_products_all[0].external_id
    )
    assert (
        res["pharmaceutical_products"][0]["uid"] == pharmaceutical_products_all[0].uid
    )
    assert (
        res["pharmaceutical_products"][1]["external_id"]
        == pharmaceutical_products_all[1].external_id
    )
    assert (
        res["pharmaceutical_products"][1]["uid"] == pharmaceutical_products_all[1].uid
    )

    assert res["dose_values"][0]["uid"] == dose_value.uid
    assert res["dose_values"][0]["value"] == dose_value.value
    assert res["dose_values"][0]["unit_label"] == dose_value.unit_label

    assert res["dose_frequency"]["term_uid"] == ct_term_dose_frequency.term_uid
    assert (
        res["dose_frequency"]["name"] == ct_term_dose_frequency.sponsor_preferred_name
    )

    assert res["delivery_device"]["term_uid"] == ct_term_delivery_device.term_uid
    assert (
        res["delivery_device"]["name"] == ct_term_delivery_device.sponsor_preferred_name
    )
    assert res["dose_frequency"]["term_uid"] == ct_term_dose_frequency.term_uid
    assert (
        res["dose_frequency"]["name"] == ct_term_dose_frequency.sponsor_preferred_name
    )

    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)


def test_get_medicinal_products_versions(api_client):
    response = api_client.get("/concepts/medicinal-products/versions?total_count=true")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res["items"]) == 10
    assert res["total"] >= len(medicinal_products_all)

    for item in res["items"]:
        assert set(list(item.keys())) == set(MEDICINAL_PRODUCT_FIELDS_ALL)
        for key in MEDICINAL_PRODUCT_FIELDS_NOT_NULL:
            assert item[key] is not None
        TestUtils.assert_timestamp_is_in_utc_zone(item["start_date"])
        TestUtils.assert_timestamp_is_newer_than(item["start_date"], 60)


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
def test_get_medicinal_products_versions_csv_xml_excel(api_client, export_format):
    url = "/concepts/medicinal-products/versions"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


def test_update_medicinal_product_property(api_client):
    # First try a dummy patch with no new property values in the payload
    payload = {
        "change_description": "dummy update",
        "dose_frequency_uid": ct_term_dose_frequency.term_uid,
        "delivery_device_uid": ct_term_delivery_device.term_uid,
        "formulations": [formulation_1],
    }
    response = api_client.patch(
        f"{BASE_URL}/{medicinal_products_all[0].uid}",
        data=json.dumps(payload),
        headers=HEADERS,
    )
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == medicinal_products_all[0].uid
    assert res["external_id"] == medicinal_products_all[0].external_id
    assert res["delivery_device"]["term_uid"] == ct_term_delivery_device.term_uid
    assert (
        res["delivery_device"]["name"] == ct_term_delivery_device.sponsor_preferred_name
    )
    assert res["dose_frequency"]["term_uid"] == ct_term_dose_frequency.term_uid
    assert (
        res["dose_frequency"]["name"] == ct_term_dose_frequency.sponsor_preferred_name
    )

    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    # Another dummy patch with no new property values in the payload
    payload = {
        "change_description": "dummy update",
    }
    response = api_client.patch(
        f"{BASE_URL}/{medicinal_products_all[0].uid}",
        data=json.dumps(payload),
        headers=HEADERS,
    )
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["uid"] == medicinal_products_all[0].uid
    assert res["external_id"] == medicinal_products_all[0].external_id
    assert res["delivery_device"]["term_uid"] == ct_term_delivery_device.term_uid
    assert (
        res["delivery_device"]["name"] == ct_term_delivery_device.sponsor_preferred_name
    )
    assert res["dose_frequency"]["term_uid"] == ct_term_dose_frequency.term_uid
    assert (
        res["dose_frequency"]["name"] == ct_term_dose_frequency.sponsor_preferred_name
    )

    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    # Update external_id
    external_id_new = f"{medicinal_products_all[0].external_id}-updated"
    payload = {
        "external_id": external_id_new,
        "dose_frequency_uid": ct_term_dose_frequency.term_uid,
        "delivery_device_uid": ct_term_delivery_device.term_uid,
        "formulations": [formulation_1],
        "change_description": "external_id updated",
    }
    response = api_client.patch(
        f"{BASE_URL}/{medicinal_products_all[0].uid}",
        data=json.dumps(payload),
        headers=HEADERS,
    )
    res = response.json()

    assert_response_status_code(response, 200)

    assert res["uid"] == medicinal_products_all[0].uid
    assert res["external_id"] == external_id_new
    assert res["delivery_device"]["term_uid"] == ct_term_delivery_device.term_uid
    assert (
        res["delivery_device"]["name"] == ct_term_delivery_device.sponsor_preferred_name
    )
    assert res["dose_frequency"]["term_uid"] == ct_term_dose_frequency.term_uid
    assert (
        res["dose_frequency"]["name"] == ct_term_dose_frequency.sponsor_preferred_name
    )

    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)

    # Nullify external_id
    payload = {
        "external_id": None,
        "change_description": "external_id set to null",
    }
    response = api_client.patch(
        f"{BASE_URL}/{medicinal_products_all[0].uid}",
        data=json.dumps(payload),
        headers=HEADERS,
    )
    res = response.json()

    assert_response_status_code(response, 200)

    assert res["uid"] == medicinal_products_all[0].uid
    assert res["external_id"] is None
    assert res["delivery_device"]["term_uid"] == ct_term_delivery_device.term_uid
    assert (
        res["delivery_device"]["name"] == ct_term_delivery_device.sponsor_preferred_name
    )
    assert res["dose_frequency"]["term_uid"] == ct_term_dose_frequency.term_uid
    assert (
        res["dose_frequency"]["name"] == ct_term_dose_frequency.sponsor_preferred_name
    )

    assert res["version"] == "0.3"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)


def test_update_medicinal_product_delivery_device(api_client):
    ct_term_delivery_device_new = TestUtils.create_ct_term(
        sponsor_preferred_name="delivery_device_2"
    )

    # Change delivery device
    payload = {
        "delivery_device_uid": ct_term_delivery_device_new.term_uid,
        "dose_frequency_uid": ct_term_dose_frequency.term_uid,
        "change_description": "delivery_device updated",
    }
    response = api_client.patch(
        f"{BASE_URL}/{medicinal_products_all[1].uid}",
        data=json.dumps(payload),
        headers=HEADERS,
    )
    res = response.json()

    assert_response_status_code(response, 200)

    assert res["uid"] == medicinal_products_all[1].uid
    assert res["external_id"] == f"external_id_b-{rand}"
    assert res["delivery_device"]["term_uid"] == ct_term_delivery_device_new.term_uid
    assert (
        res["delivery_device"]["name"]
        == ct_term_delivery_device_new.sponsor_preferred_name
    )
    assert res["dose_frequency"]["term_uid"] == ct_term_dose_frequency.term_uid
    assert (
        res["dose_frequency"]["name"] == ct_term_dose_frequency.sponsor_preferred_name
    )

    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)

    # Nullify delivery device and dose frequency values
    payload = {
        "delivery_device_uid": None,
        "dose_frequency_uid": None,
        "change_description": "delivery device and dose frequency updated",
    }
    response = api_client.patch(
        f"{BASE_URL}/{medicinal_products_all[1].uid}",
        data=json.dumps(payload),
        headers=HEADERS,
    )
    res = response.json()

    assert_response_status_code(response, 200)

    assert res["uid"] == medicinal_products_all[1].uid
    assert res["delivery_device"] is None
    assert res["dose_frequency"] is None

    assert res["version"] == "0.3"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]


def test_get_medicinal_product_versioning(api_client):
    uid = medicinal_products_all[2].uid

    response = api_client.get(f"{BASE_URL}/{uid}/versions")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    for item in res:
        assert set(list(item.keys())) == set(MEDICINAL_PRODUCT_FIELDS_ALL)
        for key in MEDICINAL_PRODUCT_FIELDS_NOT_NULL:
            assert item[key] is not None

        assert item["uid"] == uid

    # Approve draft version
    response = api_client.post(f"{BASE_URL}/{uid}/approvals")
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["version"] == "1.0"
    assert res["status"] == "Final"

    # Create new version
    response = api_client.post(f"{BASE_URL}/{uid}/versions")
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["version"] == "1.1"
    assert res["status"] == "Draft"
    assert res["possible_actions"] == ["approve", "edit"]

    # Approve draft version
    response = api_client.post(f"{BASE_URL}/{uid}/approvals")
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["version"] == "2.0"
    assert res["status"] == "Final"
    assert res["possible_actions"] == ["inactivate", "new_version"]

    # Inactivate final version
    response = api_client.delete(f"{BASE_URL}/{uid}/activations")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["version"] == "2.0"
    assert res["status"] == "Retired"
    assert res["possible_actions"] == ["reactivate"]

    # Reactivate retired version
    response = api_client.post(f"{BASE_URL}/{uid}/activations")
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["version"] == "2.0"
    assert res["status"] == "Final"
    assert res["possible_actions"] == ["inactivate", "new_version"]

    # Get all versions, assert they are sorted by version number (newest on top)
    response = api_client.get(f"/concepts/medicinal-products/{uid}/versions")
    res = response.json()
    assert_response_status_code(response, 200)

    assert len(res) == 6

    assert res[0]["version"] == "2.0"
    assert res[0]["status"] == "Final"
    assert res[0]["possible_actions"] == ["inactivate", "new_version"]

    assert res[1]["version"] == "2.0"
    assert res[1]["status"] == "Retired"
    assert res[1]["possible_actions"] == ["reactivate"]

    assert res[2]["version"] == "2.0"
    assert res[2]["status"] == "Final"
    assert res[2]["possible_actions"] == ["inactivate", "new_version"]

    assert res[3]["version"] == "1.1"
    assert res[3]["status"] == "Draft"
    assert res[3]["possible_actions"] == ["approve", "edit"]

    assert res[4]["version"] == "1.0"
    assert res[4]["status"] == "Final"
    assert res[4]["possible_actions"] == ["inactivate", "new_version"]

    assert res[5]["version"] == "0.1"
    assert res[5]["status"] == "Draft"
    assert res[5]["possible_actions"] == ["approve", "delete", "edit"]


def test_get_medicinal_products_pagination(api_client):
    results_paginated: dict = {}
    sort_by = '{"external_id": true}'
    for page_number in range(1, 4):
        url = f"{BASE_URL}?page_number={page_number}&page_size=10&sort_by={sort_by}"
        response = api_client.get(url)
        res = response.json()
        res_external_ids = list(map(lambda x: x["external_id"], res["items"]))
        results_paginated[page_number] = res_external_ids
        log.info("Page %s: %s", page_number, res_external_ids)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        set(list(reduce(lambda a, b: a + b, list(results_paginated.values()))))
    )
    log.info("All unique rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"{BASE_URL}?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["external_id"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(medicinal_products_all) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(
            10, 3, True, None, 2
        ),  # Total number of medicinal products is 22, so the last page should have 2 items
        pytest.param(10, 1, True, '{"external_id": false}', 10),
        pytest.param(10, 2, True, '{"external_id": true}', 10),
    ],
)
def test_get_medicinal_products(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = BASE_URL
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
    assert res["total"] == (len(medicinal_products_all) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(MEDICINAL_PRODUCT_FIELDS_ALL)
        for key in MEDICINAL_PRODUCT_FIELDS_NOT_NULL:
            assert item[key] is not None
        TestUtils.assert_timestamp_is_in_utc_zone(item["start_date"])
        TestUtils.assert_timestamp_is_newer_than(item["start_date"], 60)

    if sort_by:
        # sort_by is JSON string in the form: {"sort_field_name": is_ascending_order}
        sort_by_dict = json.loads(sort_by)
        sort_field: str = list(sort_by_dict.keys())[0]
        sort_order_ascending: bool = list(sort_by_dict.values())[0]

        # extract list of values of 'sort_field_name' field from the returned result
        result_vals = list(map(lambda x: x[sort_field], res["items"]))
        result_vals_sorted_locally = result_vals.copy()
        result_vals_sorted_locally = sorted(
            result_vals_sorted_locally,
            key=lambda x: (x is None, x),
            reverse=not sort_order_ascending,
        )
        assert result_vals == result_vals_sorted_locally


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
def test_get_medicinal_products_csv_xml_excel(api_client, export_format):
    TestUtils.verify_exported_data_format(api_client, export_format, BASE_URL)


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "external_id", "external_id_AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "external_id", "external_id_BBB"),
        pytest.param(
            '{"*": {"v": ["unknown-user"], "op": "co"}}',
            "author_username",
            "unknown-user@example.com",
        ),
        pytest.param('{"*": {"v": ["Draft"]}}', "status", "Draft"),
        pytest.param('{"*": {"v": ["0.1"]}}', "version", "0.1"),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"{BASE_URL}?filters={filter_by}"
    response = api_client.get(url)
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
            '{"external_id": {"v": ["external_id_AAA-{rand}_0"]}}',
            "external_id",
            "external_id_AAA-{rand}_0",
        ),
        pytest.param(
            '{"external_id": {"v": ["external_id_BBB-{rand}_2"]}}',
            "external_id",
            "external_id_BBB-{rand}_2",
        ),
        pytest.param('{"external_id": {"v": ["cc"]}}', None, None),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    filter_by = filter_by.replace("{rand}", rand)
    url = f"{BASE_URL}?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    if expected_result:
        assert len(res["items"]) > 0
        # Each returned row has a field whose value is equal to the specified filter value
        for row in res["items"]:
            assert row[expected_matched_field] == expected_result.replace(
                "{rand}", rand
            )
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "field_name, expected_returned_values",
    [
        pytest.param(
            "external_id",
            ["external_id_AAA-{rand}_0", "external_id_BBB-{rand}_0"],
        ),
    ],
)
def test_get_medicinal_products_headers(
    api_client, field_name, expected_returned_values
):
    url = f"{BASE_URL}/headers?field_name={field_name}&page_size=100"
    response = api_client.get(url)
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res) >= len(expected_returned_values)
    expected_returned_values = [
        x.replace("{rand}", rand) for x in expected_returned_values
    ]
    for val in expected_returned_values:
        assert val in res


def test_create_and_delete_medicinal_product(api_client):
    # Create new medicinal product
    payload = {
        "library_name": "Sponsor",
        "external_id": "external_id-NEW",
        "name": "name-NEW",
        "name_sentence_case": "name-new",
        "compound_uid": compound.uid,
        "pharmaceutical_product_uids": [pharmaceutical_products_all[0].uid],
        "dose_frequency_uid": ct_term_dose_frequency.term_uid,
        "delivery_device_uid": ct_term_delivery_device.term_uid,
        "dose_value_uids": [dose_value.uid],
        "dispenser_uid": ct_term_dispenser.term_uid,
    }
    response = api_client.post(BASE_URL, data=json.dumps(payload), headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 201)
    assert res["external_id"] == "external_id-NEW"
    assert res["delivery_device"]["term_uid"] == ct_term_delivery_device.term_uid
    assert (
        res["delivery_device"]["name"] == ct_term_delivery_device.sponsor_preferred_name
    )
    assert res["dose_frequency"]["term_uid"] == ct_term_dose_frequency.term_uid
    assert (
        res["dose_frequency"]["name"] == ct_term_dose_frequency.sponsor_preferred_name
    )

    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)

    # Delete medicinal product
    response = api_client.delete(f"{BASE_URL}/{res['uid']}")
    assert_response_status_code(response, 204)

    # Check that the medicinal product is deleted
    response = api_client.get(f"{BASE_URL}/{res['uid']}")
    assert_response_status_code(response, 404)


def test_create_and_delete_medicinal_product_with_missing_values(api_client):
    # Create new medicinal product
    payload = copy.deepcopy(CREATE_MEDICINAL_PRODUCT_PAYLOAD_OK)
    del payload["pharmaceutical_product_uids"]
    del payload["dose_frequency_uid"]
    del payload["delivery_device_uid"]
    del payload["dose_value_uids"]
    del payload["dispenser_uid"]

    response = api_client.post(BASE_URL, data=json.dumps(payload), headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 201)
    assert res["external_id"] == f"external_id-NEW-{rand}"
    assert res["delivery_device"] is None
    assert res["dose_frequency"] is None
    assert res["dose_values"] == []
    assert res["dispenser"] is None
    assert res["pharmaceutical_products"] == []

    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)

    # Delete medicinal product
    response = api_client.delete(f"{BASE_URL}/{res['uid']}")
    assert_response_status_code(response, 204)

    # Check that the medicinal product is deleted
    response = api_client.get(f"{BASE_URL}/{res['uid']}")
    assert_response_status_code(response, 404)


def test_negative_create_medicinal_product_wrong_links(api_client):
    # Try to create new medicinal product with non-existing dose frequency
    payload = copy.deepcopy(CREATE_MEDICINAL_PRODUCT_PAYLOAD_OK)
    payload["dose_frequency_uid"] = "NON_EXISTING_UID"
    response = api_client.post(BASE_URL, data=json.dumps(payload), headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "MedicinalProductVO tried to connect to non-existent Dose Frequency with UID 'NON_EXISTING_UID'."
    )

    # Try to create new medicinal product with non-existing dose value
    payload = copy.deepcopy(CREATE_MEDICINAL_PRODUCT_PAYLOAD_OK)
    payload["dose_value_uids"] = ["NON_EXISTING_UID"]
    response = api_client.post(BASE_URL, data=json.dumps(payload), headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "MedicinalProductVO tried to connect to non-existent Dose Value with UID 'NON_EXISTING_UID'."
    )

    # Try to create new medicinal product with non-existing dispenser
    payload = copy.deepcopy(CREATE_MEDICINAL_PRODUCT_PAYLOAD_OK)
    payload["dispenser_uid"] = "NON_EXISTING_UID"
    response = api_client.post(BASE_URL, data=json.dumps(payload), headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "MedicinalProductVO tried to connect to non-existent Dispenser with UID 'NON_EXISTING_UID'."
    )

    # Try to create new medicinal product with non-existing delivery device
    payload = copy.deepcopy(CREATE_MEDICINAL_PRODUCT_PAYLOAD_OK)
    payload["delivery_device_uid"] = "NON_EXISTING_UID"
    response = api_client.post(BASE_URL, data=json.dumps(payload), headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "MedicinalProductVO tried to connect to non-existent Delivery Device with UID 'NON_EXISTING_UID'."
    )

    # Try to create new medicinal product with non-existing compound
    payload = copy.deepcopy(CREATE_MEDICINAL_PRODUCT_PAYLOAD_OK)
    payload["compound_uid"] = "NON_EXISTING_UID"
    response = api_client.post(BASE_URL, data=json.dumps(payload), headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "MedicinalProductVO tried to connect to non-existent Compound with UID 'NON_EXISTING_UID'."
    )

    # Try to create new medicinal product with missing compound uid
    payload = copy.deepcopy(CREATE_MEDICINAL_PRODUCT_PAYLOAD_OK)
    del payload["compound_uid"]
    response = api_client.post(BASE_URL, data=json.dumps(payload), headers=HEADERS)

    assert_response_status_code(response, 422)
    res = response.json()
    assert res["detail"][0]["type"] == "missing"
    assert res["detail"][0]["loc"] == ["body", "compound_uid"]
    assert res["detail"][0]["msg"] == "Field required"

    # Try to create new medicinal product with non-existing pharmaceutical product
    payload = copy.deepcopy(CREATE_MEDICINAL_PRODUCT_PAYLOAD_OK)
    payload["pharmaceutical_product_uids"] = ["NON_EXISTING_UID"]
    response = api_client.post(BASE_URL, data=json.dumps(payload), headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "MedicinalProductVO tried to connect to non-existent Pharmaceutical Product with UID 'NON_EXISTING_UID'."
    )


def test_negative_delete_approved_medicinal_product(api_client):
    item = TestUtils.create_medicinal_product(compound_uid=compound.uid, approve=True)

    # Try to delete approved medicinal product
    response = api_client.delete(f"{BASE_URL}/{item.uid}")
    assert_response_status_code(response, 400)
    assert response.json()["message"] == "Object has been accepted"

    # Check that the medicinal product is not deleted
    response = api_client.get(f"{BASE_URL}/{item.uid}")
    assert_response_status_code(response, 200)
