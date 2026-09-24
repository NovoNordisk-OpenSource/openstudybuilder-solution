"""
Tests for /studies/{study_uid}/study-compound-dosings endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging
from typing import Any, Sequence
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.compound import Compound
from clinical_mdr_api.models.concepts.compound_alias import CompoundAlias
from clinical_mdr_api.models.concepts.concept import NumericValueWithUnit
from clinical_mdr_api.models.concepts.medicinal_product import MedicinalProduct
from clinical_mdr_api.models.concepts.pharmaceutical_product import (
    PharmaceuticalProduct,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTerm
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySelectionCompound,
    StudySelectionElement,
)
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_element,
    create_study_epoch_codelists_ret_cat_and_lib,
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.utils import CT_CODELIST_UIDS, TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings

log = logging.getLogger(__name__)

HEADERS = {"content-type": "application/json"}
BASE_URL = "/studies/{study_uid}/study-compound-dosings"

study: Study
compound: Compound
compound_alias: CompoundAlias
study_compound: StudySelectionCompound
study_compound2: StudySelectionCompound
study_elements: Sequence[StudySelectionElement]
pharmaceutical_product1: PharmaceuticalProduct
medicinal_product1: MedicinalProduct
dose_value: NumericValueWithUnit
ct_term_dose_frequency: CTTerm
ct_term_dose_frequency_2: CTTerm
ct_term_dose_frequency_unrelated: CTTerm
test_data_dict: dict[str, Any]

initialize_ct_data_map = {
    "TypeOfTreatment": [("CTTerm_000001", "CTTerm_000001")],
    "RouteOfAdministration": [("CTTerm_000002", "CTTerm_000002")],
    "DosageForm": [("CTTerm_000003", "CTTerm_000003")],
    "DispensedIn": [("CTTerm_000004", "CTTerm_000004")],
    "Device": [("CTTerm_000005", "CTTerm_000005")],
    "Formulation": [("CTTerm_000006", "CTTerm_000006")],
    "ReasonForMissingNullValue": [("CTTerm_000007", "CTTerm_000007")],
}

STUDY_COMPOUND_DOSING_FIELDS_ALL = [
    "study_uid",
    "study_version",
    "order",
    "study_element",
    "study_compound_dosing_uid",
    "study_compound",
    "dose_value",
    "dose_frequency",
    "composition",
    "start_date",
    "author_username",
]

STUDY_COMPOUND_DOSING_FIELDS_NOT_NULL = [
    "study_uid",
    "study_version",
    "order",
    "study_element",
    "study_compound_dosing_uid",
    "study_compound",
    "start_date",
]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studycompounddosings.api"
    inject_and_clear_db(db_name)
    TestUtils.create_library(name="UCUM", is_editable=True)
    global test_data_dict
    _, test_data_dict = inject_base_data()

    codelist = TestUtils.create_ct_codelist()
    TestUtils.create_study_ct_data_map(codelist_uid=codelist.codelist_uid)

    global BASE_URL
    global study
    global compound
    global compound_alias
    global study_compound
    global study_compound2
    global study_elements
    global pharmaceutical_product1
    global medicinal_product1
    global dose_value
    global ct_term_dose_frequency
    global ct_term_dose_frequency_2
    global ct_term_dose_frequency_unrelated

    _catalogue_name, library_name = get_catalogue_name_library_name(use_test_utils=True)
    catalogue_name = "SDTM CT"
    # Create CT Terms

    ct_term_dosage = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.dosage_form,
        submission_value="dosage_form_1",
        sponsor_preferred_name="dosage_form_1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        approve=True,
    )

    ct_term_roa = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.roa,
        submission_value="route_of_administration_1",
        sponsor_preferred_name="route_of_administration_1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        approve=True,
    )

    ct_term_delivery_device = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.delivery_device,
        submission_value="delivery_device_1",
        sponsor_preferred_name="delivery_device_1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        approve=True,
    )

    ct_term_dose_frequency = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.frequency,
        submission_value="dose_frequency_1",
        sponsor_preferred_name="dose_frequency_1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        approve=True,
    )

    ct_term_dose_frequency_2 = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.frequency,
        submission_value="dose_frequency_2",
        sponsor_preferred_name="dose_frequency_2",
        order=2,
        catalogue_name=catalogue_name,
        library_name=library_name,
        approve=True,
    )

    ct_term_dose_frequency_unrelated = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.frequency,
        submission_value="dose_frequency_3",
        sponsor_preferred_name="dose_frequency_3",
        order=3,
        catalogue_name=catalogue_name,
        library_name=library_name,
        approve=True,
    )

    ct_term_dispenser = TestUtils.create_ct_term(
        codelist_uid=CT_CODELIST_UIDS.dispenser,
        submission_value="dispenser_1",
        sponsor_preferred_name="dispenser_1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        approve=True,
    )

    ttype_codelist = create_codelist(
        "Type of Treatment",
        "CTCodelist_TType",
        catalogue_name,
        library_name,
        submission_value=settings.type_of_treatment_cl_submval,
    )

    TestUtils.create_ct_term(
        codelist_uid=ttype_codelist.codelist_uid,
        submission_value="treatment_type_1",
        sponsor_preferred_name="treatment_type_1",
        order=1,
        catalogue_name=catalogue_name,
        library_name=library_name,
        approve=True,
    )

    # Create Numeric values with unit
    dose_value = TestUtils.create_numeric_value_with_unit(value=10, unit="mg")

    compound = TestUtils.create_compound(name="name-AAA", approve=True)
    compound2 = TestUtils.create_compound(name="name-BBB", approve=True)

    compound_alias = TestUtils.create_compound_alias(
        name="compAlias-AAA", compound_uid=compound.uid, approve=True
    )
    compound_alias2 = TestUtils.create_compound_alias(
        name="compAlias-BBB", compound_uid=compound2.uid, approve=True
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
        dose_frequency_uids=[
            ct_term_dose_frequency.term_uid,
            ct_term_dose_frequency_2.term_uid,
        ],
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
        dose_frequency_uids=[ct_term_dose_frequency.term_uid],
        delivery_device_uid=ct_term_delivery_device.term_uid,
        dispenser_uid=ct_term_dispenser.term_uid,
        pharmaceutical_product_uids=[pharmaceutical_product1.uid],
        compound_uid=compound2.uid,
        approve=True,
    )

    # Create study
    study = TestUtils.create_study()
    TestUtils.set_study_standard_version(
        study_uid=study.uid,
    )
    BASE_URL = BASE_URL.replace("{study_uid}", study.uid)

    # Create study compounds
    study_compound = TestUtils.create_study_compound(
        study_uid=study.uid,
        compound_alias_uid=compound_alias.uid,
        medicinal_product_uid=medicinal_product1.uid,
        other_info="some info",
    )

    study_compound2 = TestUtils.create_study_compound(
        study_uid=study.uid,
        compound_alias_uid=compound_alias2.uid,
        medicinal_product_uid=medicinal_product2.uid,
        other_info="some info 2",
    )

    # Create study element
    create_study_epoch_codelists_ret_cat_and_lib(use_test_utils=True)

    element_subtype_codelist = create_codelist(
        "Element Type",
        "CTCodelist_ElementType",
        catalogue_name,
        library_name,
        submission_value="ELEMSTP",
    )
    element_subtype_term = create_ct_term(
        "Element Type",
        "ElementType_0001",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": element_subtype_codelist.codelist_uid,
                "order": 1,
                "submission_value": "Element Type",
            }
        ],
    )
    element_subtype_term_2 = create_ct_term(
        "Element Type 2",
        "ElementType_0002",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": element_subtype_codelist.codelist_uid,
                "order": 2,
                "submission_value": "Element Type 2",
            }
        ],
    )
    study_elements = [
        create_study_element(element_subtype_term.uid, study.uid),
        create_study_element(element_subtype_term_2.uid, study.uid),
    ]

    yield


@pytest.mark.order("last")
def test_integrity_checks_for_all_studies(api_client):
    """
    Test integrity checks for all available studies in the database.

    This test should always be executed at the END to check the health of the remaining database.
    It validates that all studies in the database pass integrity checks after all other tests have run.
    """
    TestUtils.run_integrity_checks_for_all_studies(api_client)


def test_create_and_remove_study_compound_dosing_selection(api_client):
    response = api_client.post(
        f"{BASE_URL}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": medicinal_product1.dose_values[0].uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # Check fields included in the response
    TestUtils.assert_response_shape_ok(
        res, STUDY_COMPOUND_DOSING_FIELDS_ALL, STUDY_COMPOUND_DOSING_FIELDS_NOT_NULL
    )

    response = api_client.get(BASE_URL)
    res = response.json()

    assert_response_status_code(response, 200)
    assert len(res["items"]) == 1

    # Delete the created study compound
    response = api_client.delete(
        f"{BASE_URL}/{res['items'][0]['study_compound_dosing_uid']}"
    )
    assert_response_status_code(response, 204)

    # Check that the study compound has been deleted
    response = api_client.get(BASE_URL)
    assert_response_status_code(response, 200)
    assert len(response.json()["items"]) == 0


def test_create_study_compound_dosing_selection_with_dose_frequency(api_client):
    """
    SCENARIO: Select one of the medicinal product's dose frequencies on a compound dosing
    GIVEN a medicinal product carrying two dose frequencies
    WHEN POST /studies/{uid}/study-compound-dosings is called with one of them
    THEN 201 is returned and the chosen frequency round-trips in the response, the listing and the audit trail
    """
    response = api_client.post(
        f"{BASE_URL}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": medicinal_product1.dose_values[0].uid,
            "dose_frequency_uid": ct_term_dose_frequency_2.term_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)

    TestUtils.assert_response_shape_ok(
        res, STUDY_COMPOUND_DOSING_FIELDS_ALL, STUDY_COMPOUND_DOSING_FIELDS_NOT_NULL
    )
    assert res["dose_frequency"]["term_uid"] == ct_term_dose_frequency_2.term_uid
    assert (
        res["dose_frequency"]["term_name"]
        == ct_term_dose_frequency_2.sponsor_preferred_name
    )

    study_compound_dosing_uid = res["study_compound_dosing_uid"]

    # The chosen value survives the round trip through the repository
    response = api_client.get(BASE_URL)
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res["items"]) == 1
    assert (
        res["items"][0]["dose_frequency"]["term_uid"]
        == ct_term_dose_frequency_2.term_uid
    )

    # ... and shows up in the audit trail
    response = api_client.get(
        f"{BASE_URL}/{study_compound_dosing_uid}/audit-trail",
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res[0]["dose_frequency"]["term_uid"] == ct_term_dose_frequency_2.term_uid

    # Switch to the other frequency defined on the medicinal product
    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": medicinal_product1.dose_values[0].uid,
            "dose_frequency_uid": ct_term_dose_frequency.term_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["dose_frequency"]["term_uid"] == ct_term_dose_frequency.term_uid

    # A PATCH that omits dose_frequency_uid preserves the stored value
    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": medicinal_product1.dose_values[0].uid,
            "composition": "composition without frequency change",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["dose_frequency"]["term_uid"] == ct_term_dose_frequency.term_uid

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_create_study_compound_dosing_selection_without_dose_frequency(api_client):
    """
    SCENARIO: Omit the dose frequency on a compound dosing
    GIVEN a medicinal product carrying two dose frequencies
    WHEN POST /studies/{uid}/study-compound-dosings is called without dose_frequency_uid
    THEN 201 is returned and dose_frequency is null
    """
    response = api_client.post(
        f"{BASE_URL}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": medicinal_product1.dose_values[0].uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert res["dose_frequency"] is None

    response = api_client.delete(f"{BASE_URL}/{res['study_compound_dosing_uid']}")
    assert_response_status_code(response, 204)


def test_negative_create_study_compound_dosing_with_foreign_dose_frequency(api_client):
    """
    SCENARIO: Reject a dose frequency that is not defined on the medicinal product
    GIVEN a dose frequency term that the medicinal product does not link to
    WHEN POST /studies/{uid}/study-compound-dosings is called with it
    THEN 400 is returned with a message naming the medicinal product
    """
    response = api_client.post(
        f"{BASE_URL}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": medicinal_product1.dose_values[0].uid,
            "dose_frequency_uid": ct_term_dose_frequency_unrelated.term_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 400)
    assert (
        res["message"]
        == f"Selected dose frequency is not valid for medicinal product '{medicinal_product1.name}'."
    )

    # Nothing was created
    response = api_client.get(BASE_URL)
    assert_response_status_code(response, 200)
    assert len(response.json()["items"]) == 0


def test_compound_dosing_modify_actions_on_locked_study(api_client):
    response = api_client.post(
        f"/studies/{study.uid}/study-compound-dosings",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": dose_value.uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # get all compounds
    response = api_client.get(
        f"/studies/{study.uid}/study-compound-dosings/audit-trail/"
    )
    res = response.json()
    assert_response_status_code(response, 200)
    old_res = res
    study_compound_dosing_uid = res[0]["study_compound_dosing_uid"]

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
    res = response.json()

    # add another compound dosing
    response = api_client.post(
        f"/studies/{study.uid}/study-compound-dosings",
        json={
            "study_compound_uid": study_compound2.study_compound_uid,
            "study_element_uid": study_elements[1].element_uid,
            "dose_value_uid": dose_value.uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # edit compound dosing
    response = api_client.patch(
        f"/studies/{study.uid}/study-compound-dosings/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound2.study_compound_uid,
            "study_element_uid": study_elements[1].element_uid,
            "dose_value_uid": dose_value.uid,
        },
    )
    assert_response_status_code(response, 400)
    res = response.json()
    assert res["message"] == f"Study with UID '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-compound-dosings/audit-trail/"
    )
    res = response.json()
    assert_response_status_code(response, 200)
    for i, _ in enumerate(old_res):
        old_res[i]["study_compound"]["study_version"] = mock.ANY
        old_res[i]["study_element"]["study_version"] = mock.ANY
    assert old_res == res

    # test cannot delete
    response = api_client.delete(
        f"/studies/{study.uid}/study-compound-dosings/{study_compound_dosing_uid}"
    )
    assert_response_status_code(response, 400)
    assert response.json()["message"] == f"Study with UID '{study.uid}' is locked."


def test_get_compound_doings_data_for_specific_study_version(api_client):
    # get compound data for first lock
    response = api_client.get(f"/studies/{study.uid}/study-compound-dosings/")
    res = response.json()
    assert_response_status_code(response, 200)
    res_old = res

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

    # edit study compound connected
    response = api_client.patch(
        f"/studies/{study.uid}/study-compounds/{study_compound.study_compound_uid}",
        json={"other_info": "some info, updated"},
    )
    res = response.json()
    assert_response_status_code(response, 200)

    res_patch_comp_dosing = api_client.patch(
        f"/studies/{study.uid}/study-compound-dosings/{res_old['items'][0]['study_compound_dosing_uid']}",
        json={
            "composition": "composition updated",
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": dose_value.uid,
        },
    ).json()
    assert res_patch_comp_dosing["composition"] == "composition updated"

    res_get = api_client.get(
        f"/studies/{study.uid}/study-compound-dosings",
    ).json()
    assert res_get["items"][0]["composition"] == "composition updated"

    # edit study element connected
    response = api_client.patch(
        f"/studies/{study.uid}/study-elements/{study_elements[0].element_uid}",
        json={
            "name": "New_Element_Name_1, updated",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)

    # add another compound dosing
    response = api_client.post(
        f"/studies/{study.uid}/study-compound-dosings",
        json={
            "study_compound_uid": study_compound2.study_compound_uid,
            "study_element_uid": study_elements[1].element_uid,
            "dose_value_uid": dose_value.uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)

    # check the study compound dosings for version 1 is same as first locked
    res_new = api_client.get(
        f"/studies/{study.uid}/study-compound-dosings",
    ).json()
    res_v1 = api_client.get(
        f"/studies/{study.uid}/study-compound-dosings?study_value_version=1",
    ).json()
    for i, _ in enumerate(res_old["items"]):
        res_old["items"][i]["study_version"] = mock.ANY
        res_old["items"][i]["study_element"]["study_version"] = mock.ANY
        res_old["items"][i]["study_compound"]["study_version"] = mock.ANY
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
def test_get_study_compound_dosings_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-compound-dosings"
    exported_data = TestUtils.verify_exported_data_format(
        api_client, export_format, url
    )
    if export_format == "text/csv":
        assert "study_version" in str(exported_data.read())
        assert "LATEST" in str(exported_data.read())
