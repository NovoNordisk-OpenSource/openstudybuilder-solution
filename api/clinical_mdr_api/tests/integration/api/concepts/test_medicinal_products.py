"""
Tests for /concepts/medicinal-products endpoints
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
from clinical_mdr_api.models.concepts.active_substance import ActiveSubstance
from clinical_mdr_api.models.concepts.compound import Compound
from clinical_mdr_api.models.concepts.concept import LagTime, NumericValueWithUnit
from clinical_mdr_api.models.concepts.medicinal_product import (
    MedicinalProduct,
    MedicinalProductCreateInput,
)
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
from clinical_mdr_api.tests.integration.utils.utils import (
    CT_CODELIST_NAMES,
    CT_CODELIST_UIDS,
    SPONSOR_LIBRARY_NAME,
    TestUtils,
)
from clinical_mdr_api.tests.utils.checks import (
    assert_response_status_code,
    parse_json_response,
)
from common.config import settings

log = logging.getLogger(__name__)

HEADERS = {"content-type": "application/json"}
BASE_URL = "/concepts/medicinal-products"

# Global variables shared between fixtures and tests
rand: str
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
formulation_1: dict[Any, Any]
dose_value: NumericValueWithUnit
ct_term_delivery_device: CTTerm
ct_term_dose_frequency: CTTerm
ct_term_dose_frequency_2: CTTerm
ct_term_dispenser: CTTerm
archived_medicinal_products: list[MedicinalProduct]


def create_medicinal_product_payload() -> dict[str, str | list[str]]:
    """Return a fresh payload dict for creating a medicinal product."""
    name = TestUtils.random_str(prefix="name-")
    return {
        "library_name": SPONSOR_LIBRARY_NAME,
        "external_id": TestUtils.random_str(prefix="rand-"),
        "name": name,
        "name_sentence_case": name.lower(),
        "compound_uid": compound.uid,
        "pharmaceutical_product_uids": [pharmaceutical_products_all[0].uid],
        "dose_frequency_uids": [ct_term_dose_frequency.term_uid],
        "delivery_device_uid": ct_term_delivery_device.term_uid,
        "dose_value_uids": [dose_value.uid],
        "dispenser_uid": ct_term_dispenser.term_uid,
    }


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
    global ct_term_dose_frequency_2
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
    _codelists = TestUtils.get_codelists_by_names(relevant_codelists)

    # Create CT Terms
    catalogue_name = "SDTM CT"

    ct_term_dose_form = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.dosage_form,
        submission_value="dosage_form_1",
        sponsor_preferred_name="dosage_form_1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=SPONSOR_LIBRARY_NAME,
        approve=True,
    )
    ct_term_roa = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.roa,
        submission_value="route_of_administration_1",
        sponsor_preferred_name="route_of_administration_1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=SPONSOR_LIBRARY_NAME,
        approve=True,
    )
    ct_term_delivery_device = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.delivery_device,
        submission_value="delivery_device_1a",
        sponsor_preferred_name="delivery_device_1a",
        order=1,
        catalogue_name=catalogue_name,
        library_name=SPONSOR_LIBRARY_NAME,
        approve=True,
    )

    ct_term_dose_frequency = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.frequency,
        submission_value="dose_frequency_1",
        sponsor_preferred_name="dose_frequency_1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=SPONSOR_LIBRARY_NAME,
        approve=True,
    )

    ct_term_dose_frequency_2 = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.frequency,
        submission_value="dose_frequency_2",
        sponsor_preferred_name="dose_frequency_2",
        order=2,
        catalogue_name=catalogue_name,
        library_name=SPONSOR_LIBRARY_NAME,
        approve=True,
    )

    ct_term_dispenser = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.dispenser,
        submission_value="dispenser_1",
        sponsor_preferred_name="dispenser_1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=SPONSOR_LIBRARY_NAME,
        approve=True,
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
            dose_frequency_uids=[ct_term_dose_frequency.term_uid],
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
            dose_frequency_uids=[ct_term_dose_frequency.term_uid],
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
            dose_frequency_uids=[ct_term_dose_frequency.term_uid],
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
            dose_frequency_uids=[ct_term_dose_frequency.term_uid],
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

    global archived_medicinal_products
    archived_medicinal_products = [
        TestUtils.create_medicinal_product(**create_medicinal_product_payload()),
        TestUtils.create_medicinal_product(**create_medicinal_product_payload()),
    ]
    for mp in archived_medicinal_products:
        TestUtils.archive_medicinal_product(mp.uid)

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
    "dose_frequencies",
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

PHARMACEUTICAL_PRODUCT_FIELDS_ALL = [
    "uid",
    "external_id",
]

PHARMACEUTICAL_PRODUCT_FIELDS_NOT_NULL = [
    "uid",
]


def test_get_medicinal_product(api_client):
    """
    SCENARIO: Retrieve a single medicinal product by UID
    GIVEN a medicinal product with compound, pharmaceutical products, dose values, dose frequency, and delivery device exists
    WHEN GET /concepts/medicinal-products/{uid} is called
    THEN 200 is returned with all expected fields, correct linked entities, version 0.1, status Draft, and a valid UTC start_date
    """
    response = api_client.get(f"{BASE_URL}/{medicinal_products_all[0].uid}")
    res = response.json()

    assert_response_status_code(response, 200)

    # Check fields included in the response
    assert set(res.keys()) == set(MEDICINAL_PRODUCT_FIELDS_ALL)
    for key in MEDICINAL_PRODUCT_FIELDS_NOT_NULL:
        assert res[key] is not None

    for item in res["pharmaceutical_products"]:
        assert set(item.keys()) == set(PHARMACEUTICAL_PRODUCT_FIELDS_ALL)
        for key_pp in PHARMACEUTICAL_PRODUCT_FIELDS_NOT_NULL:
            assert item[key_pp] is not None

    assert res["uid"] == medicinal_products_all[0].uid
    assert res["external_id"] == f"external_id_a-{rand}"
    assert res["name"] == f"name_A-{rand}"
    assert res["name_sentence_case"] == f"name_a-{rand}"
    assert res["library_name"] == SPONSOR_LIBRARY_NAME

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

    assert res["dose_frequencies"] == [
        {
            "term_uid": ct_term_dose_frequency.term_uid,
            "name": ct_term_dose_frequency.sponsor_preferred_name,
        }
    ]

    assert res["delivery_device"]["term_uid"] == ct_term_delivery_device.term_uid
    assert (
        res["delivery_device"]["name"] == ct_term_delivery_device.sponsor_preferred_name
    )
    assert res["dose_frequencies"] == [
        {
            "term_uid": ct_term_dose_frequency.term_uid,
            "name": ct_term_dose_frequency.sponsor_preferred_name,
        }
    ]

    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)


def test_get_medicinal_products_versions(api_client):
    """
    SCENARIO: Retrieve all medicinal product versions
    GIVEN medicinal products exist
    WHEN GET /concepts/medicinal-products/versions?total_count=true is called
    THEN 200 is returned with 10 items per page, total at least equal to fixture count, and all required fields are present
    """
    response = api_client.get("/concepts/medicinal-products/versions?total_count=true")
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res["items"]) == 10
    assert res["total"] >= len(medicinal_products_all)

    for item in res["items"]:
        assert set(list(item.keys())) == set(MEDICINAL_PRODUCT_FIELDS_ALL)
        for key in MEDICINAL_PRODUCT_FIELDS_NOT_NULL:
            assert item[key] is not None

        for pp in item["pharmaceutical_products"]:
            assert set(pp.keys()) == set(PHARMACEUTICAL_PRODUCT_FIELDS_ALL)
            for key_pp in PHARMACEUTICAL_PRODUCT_FIELDS_NOT_NULL:
                assert pp[key_pp] is not None

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
    """
    SCENARIO: Export medicinal product versions in CSV, XML, and Excel formats
    GIVEN medicinal products exist
    WHEN GET /concepts/medicinal-products/versions is called with Accept header for csv/xml/excel
    THEN 200 is returned with data in the requested export format
    """
    url = "/concepts/medicinal-products/versions"
    TestUtils.verify_exported_data_format(api_client, export_format, url)


def test_update_medicinal_product_property(api_client):
    """
    SCENARIO: Update properties of a medicinal product
    GIVEN a draft medicinal product exists
    WHEN PATCH /concepts/medicinal-products/{uid} is called with various payloads (dummy, external_id update, nullify external_id)
    THEN 200 is returned each time with the updated fields reflected, version incremented appropriately, and UTC start_date present
    """
    # First try a dummy patch with no new property values in the payload
    payload: dict[Any, Any]
    payload = {
        "change_description": "dummy update",
        "dose_frequency_uids": [ct_term_dose_frequency.term_uid],
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
    assert res["dose_frequencies"] == [
        {
            "term_uid": ct_term_dose_frequency.term_uid,
            "name": ct_term_dose_frequency.sponsor_preferred_name,
        }
    ]

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
    assert res["dose_frequencies"] == [
        {
            "term_uid": ct_term_dose_frequency.term_uid,
            "name": ct_term_dose_frequency.sponsor_preferred_name,
        }
    ]

    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    # Update external_id
    external_id_new = f"{medicinal_products_all[0].external_id}-updated"
    payload = {
        "external_id": external_id_new,
        "dose_frequency_uids": [ct_term_dose_frequency.term_uid],
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
    assert res["dose_frequencies"] == [
        {
            "term_uid": ct_term_dose_frequency.term_uid,
            "name": ct_term_dose_frequency.sponsor_preferred_name,
        }
    ]

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
    assert res["dose_frequencies"] == [
        {
            "term_uid": ct_term_dose_frequency.term_uid,
            "name": ct_term_dose_frequency.sponsor_preferred_name,
        }
    ]

    assert res["version"] == "0.3"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)


def test_update_medicinal_product_delivery_device(api_client):
    """
    SCENARIO: Update and nullify delivery device on a medicinal product
    GIVEN a draft medicinal product exists
    WHEN PATCH /concepts/medicinal-products/{uid} is called to change delivery device, then again to nullify it and dose frequency
    THEN 200 is returned with updated device reflected; after nullify, delivery_device is null and dose_frequencies is empty
    """
    ct_term_delivery_device_new = TestUtils.create_ct_term(
        sponsor_preferred_name="delivery_device_2",
        codelist_uid=CT_CODELIST_UIDS.delivery_device,
        order=2,
    )

    payload: dict[Any, Any]
    # Change delivery device
    payload = {
        "delivery_device_uid": ct_term_delivery_device_new.term_uid,
        "dose_frequency_uids": [ct_term_dose_frequency.term_uid],
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
    assert res["dose_frequencies"] == [
        {
            "term_uid": ct_term_dose_frequency.term_uid,
            "name": ct_term_dose_frequency.sponsor_preferred_name,
        }
    ]

    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]

    TestUtils.assert_timestamp_is_in_utc_zone(res["start_date"])
    TestUtils.assert_timestamp_is_newer_than(res["start_date"], 60)

    # Nullify delivery device and dose frequency values
    payload = {
        "delivery_device_uid": None,
        "dose_frequency_uids": [],
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
    assert res["dose_frequencies"] == []

    assert res["version"] == "0.3"
    assert res["status"] == "Draft"
    assert list(res["possible_actions"]) == ["approve", "delete", "edit"]


def test_get_medicinal_product_versioning(api_client):
    """
    SCENARIO: Full versioning lifecycle of a medicinal product
    GIVEN a draft medicinal product exists
    WHEN approve, new_version, approve again, inactivate, reactivate, and list versions are called in sequence
    THEN each action returns the correct status and version, and the final version list is ordered newest first
    """
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
    """
    SCENARIO: Paginate through all medicinal products
    GIVEN multiple medicinal products exist
    WHEN GET /concepts/medicinal-products is called across multiple pages with a consistent sort order
    THEN each page returns distinct results, and combined unique results match the full single-page listing
    """
    results_paginated: dict[Any, Any] = {}
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
        set(
            list(
                reduce(lambda a, b: list(a) + list(b), list(results_paginated.values()))
            )
        )
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
    """
    SCENARIO: List medicinal products with pagination and sorting
    GIVEN medicinal products exist
    WHEN GET /concepts/medicinal-products is called with various page_size, page_number, total_count, and sort_by combinations
    THEN 200 is returned with the correct item count, pagination metadata, all required fields, and correct sort order
    """
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

        for pp in item["pharmaceutical_products"]:
            assert set(pp.keys()) == set(PHARMACEUTICAL_PRODUCT_FIELDS_ALL)
            for key_pp in PHARMACEUTICAL_PRODUCT_FIELDS_NOT_NULL:
                assert pp[key_pp] is not None

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
    """
    SCENARIO: Export medicinal products in CSV, XML, and Excel formats
    GIVEN medicinal products exist
    WHEN GET /concepts/medicinal-products is called with Accept header for csv/xml/excel
    THEN 200 is returned with data in the requested export format
    """
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
    """
    SCENARIO: Filter medicinal products with wildcard search
    GIVEN medicinal products with various field values exist
    WHEN GET /concepts/medicinal-products?filters=<wildcard_filter> is called
    THEN 200 is returned; matching items have the expected field starting with the filter prefix, or no items if no match
    """
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
    """
    SCENARIO: Filter medicinal products with exact-match search
    GIVEN medicinal products with known field values exist
    WHEN GET /concepts/medicinal-products?filters=<exact_filter> is called
    THEN 200 is returned; matching items have the specified field equal to the exact filter value, or no items if no match
    """
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
    """
    SCENARIO: Retrieve distinct header values for a medicinal product field
    GIVEN medicinal products with known field values exist
    WHEN GET /concepts/medicinal-products/headers?field_name={field_name} is called
    THEN 200 is returned and the response list contains all expected values
    """
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
    """
    SCENARIO: Create and delete a medicinal product
    GIVEN valid compound, pharmaceutical product, dose values, frequency, delivery device, and dispenser exist
    WHEN POST /concepts/medicinal-products is called then DELETE /concepts/medicinal-products/{uid}
    THEN 201 is returned with correct linked entities and status Draft; subsequent GET returns 404
    """
    # Create new medicinal product
    payload = {
        "library_name": SPONSOR_LIBRARY_NAME,
        "external_id": "external_id-NEW",
        "name": "name-NEW",
        "name_sentence_case": "name-new",
        "compound_uid": compound.uid,
        "pharmaceutical_product_uids": [pharmaceutical_products_all[0].uid],
        "dose_frequency_uids": [ct_term_dose_frequency.term_uid],
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
    assert res["dose_frequencies"] == [
        {
            "term_uid": ct_term_dose_frequency.term_uid,
            "name": ct_term_dose_frequency.sponsor_preferred_name,
        }
    ]

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


def test_create_and_update_medicinal_product_with_multiple_dose_frequencies(api_client):
    """
    SCENARIO: Create a medicinal product carrying two dose frequencies, then reduce it to one
    GIVEN two approved dose frequency terms exist
    WHEN POST /concepts/medicinal-products is called with both term UIDs, then PATCH with only one
    THEN 201 returns both frequencies sorted by name, and the PATCH returns only the remaining one
    """
    payload = create_medicinal_product_payload()
    payload["dose_frequency_uids"] = [
        ct_term_dose_frequency_2.term_uid,
        ct_term_dose_frequency.term_uid,
    ]

    response = api_client.post(BASE_URL, data=json.dumps(payload), headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 201)
    # Sorted by name, so dose_frequency_1 comes before dose_frequency_2
    assert res["dose_frequencies"] == [
        {
            "term_uid": ct_term_dose_frequency.term_uid,
            "name": ct_term_dose_frequency.sponsor_preferred_name,
        },
        {
            "term_uid": ct_term_dose_frequency_2.term_uid,
            "name": ct_term_dose_frequency_2.sponsor_preferred_name,
        },
    ]
    assert res["version"] == "0.1"

    uid = res["uid"]

    # Reduce to a single dose frequency
    patch_payload = {
        "dose_frequency_uids": [ct_term_dose_frequency_2.term_uid],
        "change_description": "dose frequencies reduced to one",
    }
    response = api_client.patch(
        f"{BASE_URL}/{uid}", data=json.dumps(patch_payload), headers=HEADERS
    )
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["dose_frequencies"] == [
        {
            "term_uid": ct_term_dose_frequency_2.term_uid,
            "name": ct_term_dose_frequency_2.sponsor_preferred_name,
        }
    ]
    assert res["version"] == "0.2"

    # A PATCH that omits dose_frequency_uids preserves the stored value
    patch_payload = {"change_description": "unrelated update"}
    response = api_client.patch(
        f"{BASE_URL}/{uid}", data=json.dumps(patch_payload), headers=HEADERS
    )
    res = response.json()

    assert_response_status_code(response, 200)
    assert res["dose_frequencies"] == [
        {
            "term_uid": ct_term_dose_frequency_2.term_uid,
            "name": ct_term_dose_frequency_2.sponsor_preferred_name,
        }
    ]

    response = api_client.delete(f"{BASE_URL}/{uid}")
    assert_response_status_code(response, 204)


def test_create_and_delete_medicinal_product_with_missing_values(api_client):
    """
    SCENARIO: Create and delete a medicinal product with only required fields
    GIVEN a valid compound exists
    WHEN POST /concepts/medicinal-products is called with optional fields omitted, then DELETE is called
    THEN 201 is returned with null optional fields; subsequent GET returns 404
    """
    payload = create_medicinal_product_payload()
    del payload["pharmaceutical_product_uids"]
    del payload["dose_frequency_uids"]
    del payload["delivery_device_uid"]
    del payload["dose_value_uids"]
    del payload["dispenser_uid"]

    response = api_client.post(BASE_URL, json=payload, headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 201)
    assert res["external_id"] == payload["external_id"]
    assert res["delivery_device"] is None
    assert res["dose_frequencies"] == []
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
    """
    SCENARIO: Attempt to create a medicinal product with invalid linked UIDs
    GIVEN valid base data exists
    WHEN POST /concepts/medicinal-products is called with non-existing UIDs for dose frequency, dose value, dispenser, delivery device, compound, or pharmaceutical product
    THEN 400 is returned with a message indicating which linked entity could not be found
    """
    # Try to create new medicinal product with non-existing dose frequency
    payload = create_medicinal_product_payload()
    payload["dose_frequency_uids"] = ["NON_EXISTING_UID"]
    response = api_client.post(BASE_URL, json=payload, headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "MedicinalProductVO tried to connect to non-existent Dose Frequency with UID 'NON_EXISTING_UID'."
    )

    # Try to create new medicinal product with non-existing dose value
    payload = create_medicinal_product_payload()
    payload["dose_value_uids"] = ["NON_EXISTING_UID"]
    response = api_client.post(BASE_URL, json=payload, headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "MedicinalProductVO tried to connect to non-existent Dose Value with UID 'NON_EXISTING_UID'."
    )

    # Try to create new medicinal product with non-existing dispenser
    payload = create_medicinal_product_payload()
    payload["dispenser_uid"] = "NON_EXISTING_UID"
    response = api_client.post(BASE_URL, json=payload, headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "MedicinalProductVO tried to connect to non-existent Dispenser with UID 'NON_EXISTING_UID'."
    )

    # Try to create new medicinal product with non-existing delivery device
    payload = create_medicinal_product_payload()
    payload["delivery_device_uid"] = "NON_EXISTING_UID"
    response = api_client.post(BASE_URL, json=payload, headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "MedicinalProductVO tried to connect to non-existent Delivery Device with UID 'NON_EXISTING_UID'."
    )

    # Try to create new medicinal product with non-existing compound
    payload = create_medicinal_product_payload()
    payload["compound_uid"] = "NON_EXISTING_UID"
    response = api_client.post(BASE_URL, json=payload, headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "MedicinalProductVO tried to connect to non-existent Compound with UID 'NON_EXISTING_UID'."
    )

    # Try to create new medicinal product with missing compound uid
    payload = create_medicinal_product_payload()
    del payload["compound_uid"]
    response = api_client.post(BASE_URL, json=payload, headers=HEADERS)

    assert_response_status_code(response, 400)
    res = response.json()
    assert res["details"][0]["error_code"] == "missing"
    assert res["details"][0]["field"] == ["body", "compound_uid"]
    assert res["details"][0]["msg"] == "Field required"

    # Try to create new medicinal product with non-existing pharmaceutical product
    payload = create_medicinal_product_payload()
    payload["pharmaceutical_product_uids"] = ["NON_EXISTING_UID"]
    response = api_client.post(BASE_URL, json=payload, headers=HEADERS)
    res = response.json()

    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == "MedicinalProductVO tried to connect to non-existent Pharmaceutical Product with UID 'NON_EXISTING_UID'."
    )


def test_negative_delete_approved_medicinal_product(api_client):
    """
    SCENARIO: Attempt to delete an approved medicinal product
    GIVEN an approved (Final status) medicinal product exists
    WHEN DELETE /concepts/medicinal-products/{uid} is called
    THEN 400 is returned with message "Object has been accepted", and subsequent GET still returns 200
    """
    item = TestUtils.create_medicinal_product(compound_uid=compound.uid, approve=True)

    # Try to delete approved medicinal product
    response = api_client.delete(f"{BASE_URL}/{item.uid}")
    assert_response_status_code(response, 400)
    assert response.json()["message"] == "Object has been accepted"

    # Check that the medicinal product is not deleted
    response = api_client.get(f"{BASE_URL}/{item.uid}")
    assert_response_status_code(response, 200)


def test_get_medicinal_products_excludes_archived(api_client):
    """
    SCENARIO: listing Medicinal Products excluding archived ones
    GIVEN: multiple Medicinal Products in the database, some archived
    WHEN: GET /concepts/medicinal-products
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing all existing Medicinal Products, excluding archived Medicinal Products.
    """
    response = api_client.get(BASE_URL, params={"page_size": 1000})
    payload = parse_json_response(response, assert_status=200)

    items = payload["items"]
    assert len(items) > 0
    for item in items:
        assert item["library_name"] != settings.archived_library_name


def test_get_archived_medicinal_products(api_client):
    """
    SCENARIO: getting archived Medicinal Products
    GIVEN: multiple Medicinal Products in the database, some archived
    WHEN: GET /concepts/medicinal-products?library_name=Archived
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing only the archived Medicinal Products.
    """
    response = api_client.get(
        BASE_URL,
        params={"library_name": settings.archived_library_name, "page_size": 1000},
    )
    payload = parse_json_response(response, assert_status=200)

    items = payload["items"]
    assert len(items) > 0
    for item in items:
        assert item["library_name"] == settings.archived_library_name


def test_get_medicinal_product_by_uid_returns_archived(api_client):
    """
    SCENARIO: getting a single archived Medicinal Product by UID
    GIVEN: an archived Medicinal Product in the database
    WHEN: GET /concepts/medicinal-products/{uid}
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Medicinal Product with library_name set to 'Archived'.
    """
    archived_mp = archived_medicinal_products[0]
    response = api_client.get(f"{BASE_URL}/{archived_mp.uid}")
    res = parse_json_response(response, assert_status=200)

    assert res["uid"] == archived_mp.uid
    assert res["library_name"] == settings.archived_library_name


def test_archived_medicinal_product_excluded_from_headers(api_client):
    """
    SCENARIO: getting headers of Medicinal Products with archived Medicinal Products in the database
    GIVEN: an existing Medicinal Product in the database, later archived
    WHEN: GET /concepts/medicinal-products/headers?field_name=name
    THEN: should respond with 200 HTTP status code and JSON payload,
          with the archived Medicinal Product excluded from the results.
    """
    # Create a Medicinal Product
    medicinal_product = TestUtils.create_medicinal_product(
        **create_medicinal_product_payload()
    )

    # Get headers — the new product should appear
    response = api_client.get(
        f"{BASE_URL}/headers",
        params={"field_name": "name"},
    )
    payload = parse_json_response(response, assert_status=200)
    assert isinstance(payload, list)
    assert medicinal_product.name in payload

    # Archive the Medicinal Product
    TestUtils.archive_medicinal_product(medicinal_product.uid)

    # Get headers again — the archived product should no longer appear
    response = api_client.get(
        f"{BASE_URL}/headers",
        params={"field_name": "name"},
    )
    payload = parse_json_response(response, assert_status=200)
    assert isinstance(payload, list)
    assert medicinal_product.name not in payload


def test_archiving_medicinal_product_draft(api_client):
    """
    SCENARIO: archiving a Medicinal Product in Draft status
    GIVEN: a Medicinal Product in Draft status
    WHEN: POST /concepts/medicinal-products/{uid}/archive
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Medicinal Product with library_name set to the archived library.
    """
    medicinal_product = TestUtils.create_medicinal_product(
        compound_uid=compound.uid,
        name=f"Draft Product To Archive-{rand}",
        name_sentence_case=f"draft product to archive-{rand}",
        approve=False,
    )

    response = api_client.post(f"{BASE_URL}/{medicinal_product.uid}/archive")
    res = parse_json_response(response, assert_status=200)

    assert res["library_name"] == settings.archived_library_name
    assert res["name"] == medicinal_product.name


def test_archiving_medicinal_product_final(api_client):
    """
    SCENARIO: archiving a Medicinal Product in Final status
    GIVEN: a Medicinal Product in Final (approved) status
    WHEN: POST /concepts/medicinal-products/{uid}/archive
    THEN: should respond with 200 HTTP status code and JSON payload,
          containing the archived Medicinal Product with library_name set to the archived library.
    """
    medicinal_product = TestUtils.create_medicinal_product(
        compound_uid=compound.uid,
        name=f"Final Product To Archive-{rand}",
        name_sentence_case=f"final product to archive-{rand}",
    )

    response = api_client.post(f"{BASE_URL}/{medicinal_product.uid}/archive")
    res = parse_json_response(response, assert_status=200)

    assert res["library_name"] == settings.archived_library_name


def test_can_not_archive_already_archived_medicinal_product(api_client):
    """
    SCENARIO: attempting to archive an already-archived Medicinal Product
    GIVEN: Medicinal Products that are already archived
    WHEN: POST /concepts/medicinal-products/{uid}/archive for each archived product
    THEN: should respond with 400 HTTP status code and an error message indicating the product
          is already in the archived library.
    """
    for medicinal_product in archived_medicinal_products:
        uid = medicinal_product.uid
        response = api_client.post(f"{BASE_URL}/{uid}/archive")
        res = parse_json_response(response, assert_status=400)

        assert (
            res["message"]
            == f"Concept with UID '{uid}' is already in '{settings.archived_library_name}' library."
        )


def test_can_not_create_new_version_of_archived_medicinal_product(api_client):
    """
    SCENARIO: attempting to create a new version of an archived Medicinal Product
    GIVEN: Medicinal Products that are already archived
    WHEN: POST /concepts/medicinal-products/{uid}/versions for each archived product
    THEN: should respond with 400 HTTP status code and an error message indicating the library
          is not editable.
    """
    for medicinal_product in archived_medicinal_products:
        response = api_client.post(f"{BASE_URL}/{medicinal_product.uid}/versions")
        res = parse_json_response(response, assert_status=400)

        assert res["message"] == "Library isn't editable."


def test_can_not_edit_archived_medicinal_product(api_client):
    """
    SCENARIO: attempting to edit an archived Medicinal Product
    GIVEN: Medicinal Products that are already archived
    WHEN: PATCH /concepts/medicinal-products/{uid} for each archived product
    THEN: should respond with 400 HTTP status code and an error message indicating the library
          is not editable.
    """
    for medicinal_product in archived_medicinal_products:
        response = api_client.patch(
            f"{BASE_URL}/{medicinal_product.uid}",
            json={
                "name": f"edited {medicinal_product.name}",
                "name_sentence_case": f"edited {medicinal_product.name_sentence_case}",
                "change_description": "edit attempt on archived",
            },
        )
        res = parse_json_response(response, assert_status=400)

        assert res["message"] == "Library isn't editable."


def test_allow_recreating_archived_medicinal_product(api_client):
    """
    SCENARIO: re-creating a Medicinal Product with the same name as an archived one
    GIVEN: Medicinal Products that are already archived
    WHEN: POST /concepts/medicinal-products with the same name as the archived product
    THEN: should respond with 201 HTTP status code and JSON payload,
          containing the newly created Medicinal Product with the same name.
    """
    for medicinal_product in archived_medicinal_products:
        mp_dict = medicinal_product.model_dump()
        mp_dict["compound_uid"] = medicinal_product.compound.uid
        mp_dict["library_name"] = settings.sponsor_library_name
        input_model = MedicinalProductCreateInput(**mp_dict)

        response = api_client.post(
            BASE_URL,
            json=input_model.model_dump(),
        )
        res = parse_json_response(response, assert_status=201)
        assert res["name"] == medicinal_product.name


def test_delete_draft_medicinal_product(api_client):
    """
    SCENARIO: deleting a draft Medicinal Product
    GIVEN: an existing draft Medicinal Product
    WHEN: DELETE /concepts/medicinal-products/{uid}
    THEN: should respond with 204 HTTP status code
    """

    medicinal_product = TestUtils.create_medicinal_product(
        compound_uid=compound.uid, approve=False
    )

    response = api_client.delete(f"{BASE_URL}/{medicinal_product.uid}")
    assert_response_status_code(response, 204)


def test_delete_archived_medicinal_product_fails(api_client):
    """
    SCENARIO: deleting an archived Medicinal Product
    GIVEN: an existing archived Medicinal Product
    WHEN: DELETE /concepts/medicinal-products/{uid}
    THEN: should respond with 400 HTTP status code and JSON payload,
          with an error message that archived concepts cannot be deleted.
    """

    medicinal_product = TestUtils.create_medicinal_product(
        compound_uid=compound.uid, approve=False
    )
    TestUtils.archive_medicinal_product(medicinal_product.uid)

    response = api_client.delete(f"{BASE_URL}/{medicinal_product.uid}")
    resp = parse_json_response(response, assert_status=400)
    assert "Can't delete Concept" in resp["message"]
