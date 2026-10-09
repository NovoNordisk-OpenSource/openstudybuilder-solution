"""
Tests for /studies/{study_uid}/study-compound-dosings endpoints
"""

import json
import logging
from collections.abc import Sequence
from typing import Any
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.concepts.activities.activity import Activity
from clinical_mdr_api.models.concepts.activities.activity_group import ActivityGroup
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
)
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
)
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
FREE_TEXT_DOSE_VALUE_1 = "5 mL"
FREE_TEXT_DOSE_VALUE_2 = "10 mL"
FREE_TEXT_DOSE_FREQUENCY_1 = "Every other Tuesday"
FREE_TEXT_DOSE_FREQUENCY_2 = "Twice per menstrual cycle"

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
# A term from a different codelist, used to prove a non-frequency uid is rejected
ct_term_dosage: CTTerm
test_data_dict: dict[str, Any]

# Activity data backing the optional dose collection study activity instance link
soa_group_term_uid: str
activity_group: ActivityGroup
activity_subgroup: ActivitySubGroup
weight_activity: Activity
weight_activity_instance: ActivityInstance
height_activity: Activity
height_activity_instance: ActivityInstance
siblings_activity: Activity
siblings_activity_instance: ActivityInstance
siblings_activity_instance_2: ActivityInstance
placeholder_activity: Activity
placeholder_activity_instance: ActivityInstance
cascade_activity: Activity
cascade_activity_instance: ActivityInstance
study_activity_weight_uid: str
study_activity_height_uid: str
study_activity_instance_weight_uid: str
study_activity_instance_height_uid: str

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
    "free_text_dose_value",
    "dose_value_label",
    "dose_frequency",
    "free_text_dose_frequency",
    "dose_frequency_label",
    "composition",
    "study_activity_instance",
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
    global ct_term_dosage
    global soa_group_term_uid
    global activity_group
    global activity_subgroup
    global weight_activity
    global weight_activity_instance
    global height_activity
    global height_activity_instance
    global siblings_activity
    global siblings_activity_instance
    global siblings_activity_instance_2
    global placeholder_activity
    global placeholder_activity_instance
    global cascade_activity
    global cascade_activity_instance
    global study_activity_weight_uid
    global study_activity_height_uid

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

    # Activity library data backing the dose collection study activity instance link.
    # A study activity auto-creates one study activity instance per required
    # activity instance of the selected activity, which is what the link targets.
    flowchart_group_codelist = create_codelist(
        "Flowchart Group",
        "CTCodelist_FlowchartGroup",
        catalogue_name,
        library_name,
        submission_value=settings.flowchart_group_cl_submval,
    )
    soa_group_term = create_ct_term(
        "EFFICACY",
        "term_efficacy_uid",
        catalogue_name,
        library_name,
        codelists=[
            {
                "uid": flowchart_group_codelist.codelist_uid,
                "order": 1,
                "submission_value": "EFFICACY",
            }
        ],
    )
    soa_group_term_uid = soa_group_term.uid

    activity_group = TestUtils.create_activity_group(name="General")
    activity_subgroup = TestUtils.create_activity_subgroup(name="Body Measurements")
    activity_instance_class = TestUtils.create_activity_instance_class(
        name="Dose collection activity instance class"
    )

    def _create_activity_with_instances(
        activity_name: str, instance_names: list[str]
    ) -> tuple[Activity, list[ActivityInstance]]:
        created_activity = TestUtils.create_activity(
            name=activity_name,
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            library_name="Sponsor",
            is_data_collected=True,
        )
        created_instances = [
            TestUtils.create_activity_instance(
                name=instance_name,
                activity_instance_class_uid=activity_instance_class.uid,
                name_sentence_case=instance_name.lower(),
                topic_code=f"{instance_name} topic code",
                # Only the first instance is auto-selected when the study
                # activity is created; further ones are added on demand.
                is_required_for_activity=index == 0,
                activities=[created_activity.uid],
                activity_subgroups=[activity_subgroup.uid],
                activity_groups=[activity_group.uid],
                activity_items=[],
            )
            for index, instance_name in enumerate(instance_names)
        ]
        return created_activity, created_instances

    weight_activity, (weight_activity_instance,) = _create_activity_with_instances(
        "Weight", ["Weight activity instance"]
    )
    height_activity, (height_activity_instance,) = _create_activity_with_instances(
        "Height", ["Height activity instance"]
    )
    (
        siblings_activity,
        (siblings_activity_instance, siblings_activity_instance_2),
    ) = _create_activity_with_instances(
        "Siblings", ["Siblings activity instance", "Second siblings activity instance"]
    )
    (
        placeholder_activity,
        (placeholder_activity_instance,),
    ) = _create_activity_with_instances(
        "Placeholder", ["Placeholder activity instance"]
    )
    cascade_activity, (cascade_activity_instance,) = _create_activity_with_instances(
        "Cascade", ["Cascade activity instance"]
    )

    # The two study activities shared by the linking tests
    study_activity_weight_uid = TestUtils.create_study_activity(
        study_uid=study.uid,
        soa_group_term_uid=soa_group_term_uid,
        activity_uid=weight_activity.uid,
        activity_subgroup_uid=activity_subgroup.uid,
        activity_group_uid=activity_group.uid,
    ).study_activity_uid
    study_activity_height_uid = TestUtils.create_study_activity(
        study_uid=study.uid,
        soa_group_term_uid=soa_group_term_uid,
        activity_uid=height_activity.uid,
        activity_subgroup_uid=activity_subgroup.uid,
        activity_group_uid=activity_group.uid,
    ).study_activity_uid

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


def test_create_study_compound_dosing_with_dose_frequency_not_on_medicinal_product(
    api_client,
):
    """
    SCENARIO: Select a dose frequency the medicinal product does not link to
    GIVEN a frequency codelist term that is not among the medicinal product's own
    WHEN POST /studies/{uid}/study-compound-dosings is called with it
    THEN 201 is returned and the term is stored

    A medicinal product lists only a handful of frequencies while studies need the
    rest of the codelist, so membership is checked against the codelist instead.
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
    assert_response_status_code(response, 201)
    assert (
        res["dose_frequency"]["term_uid"] == ct_term_dose_frequency_unrelated.term_uid
    )
    assert res["dose_frequency_label"] == res["dose_frequency"]["term_name"]

    # ... and that is what is stored, not just what is echoed back
    res = _get_compound_dosing(api_client, res["study_compound_dosing_uid"])
    assert (
        res["dose_frequency"]["term_uid"] == ct_term_dose_frequency_unrelated.term_uid
    )

    response = api_client.delete(f"{BASE_URL}/{res['study_compound_dosing_uid']}")
    assert_response_status_code(response, 204)


def test_negative_create_study_compound_dosing_with_non_frequency_term(api_client):
    """
    SCENARIO: Pass a CT term that is not a frequency at all as the dose frequency
    WHEN POST /studies/{uid}/study-compound-dosings is called with it
    THEN 400 is returned naming the offending uid, and nothing is created

    The message must come from the domain layer, not from the persistence layer's
    lower-level "not found in the codelist identified by uid ..." error.
    """
    response = api_client.post(
        f"{BASE_URL}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": medicinal_product1.dose_values[0].uid,
            "dose_frequency_uid": ct_term_dosage.term_uid,
        },
    )
    assert_response_status_code(response, 400)
    message = response.json()["message"]
    assert ct_term_dosage.term_uid in message
    assert "dose frequency codelist" in message

    # Nothing was created
    response = api_client.get(BASE_URL)
    assert_response_status_code(response, 200)
    assert len(response.json()["items"]) == 0


def _get_study_activity_instance_uids(
    api_client, study_uid: str, study_activity_uid: str
) -> list[str]:
    """Return the uids of the study activity instances of one study activity."""
    response = api_client.get(
        f"/studies/{study_uid}/study-activity-instances",
        params={
            "filters": json.dumps(
                {"study_activity_uid": {"v": [study_activity_uid], "op": "eq"}}
            ),
            "page_size": 0,
        },
    )
    assert_response_status_code(response, 200)
    return [item["study_activity_instance_uid"] for item in response.json()["items"]]


def _post_compound_dosing(api_client, **overrides) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "study_compound_uid": study_compound.study_compound_uid,
        "study_element_uid": study_elements[0].element_uid,
        "dose_value_uid": medicinal_product1.dose_values[0].uid,
    }
    payload.update(overrides)
    response = api_client.post(BASE_URL, json=payload)
    assert_response_status_code(response, 201)
    return response.json()


def _get_compound_dosing(api_client, study_compound_dosing_uid: str) -> dict[str, Any]:
    """Read one compound dosing off the listing, asserting it appears exactly once.

    There is no GET for a single compound dosing, and the uniqueness assertion is
    what catches a relationship that accumulated across versions.
    """
    response = api_client.get(BASE_URL)
    assert_response_status_code(response, 200)
    matches = [
        item
        for item in response.json()["items"]
        if item["study_compound_dosing_uid"] == study_compound_dosing_uid
    ]
    assert len(matches) == 1
    return matches[0]


def test_create_study_compound_dosing_with_dose_collection_instance(api_client):
    """
    SCENARIO: Link a compound dosing to the study activity instance collecting its dose
    GIVEN a study activity instance belonging to the same study
    WHEN POST /studies/{uid}/study-compound-dosings carries its uid
    THEN 201 is returned and both the uid and the resolved name round-trip
    """
    instance_uid = _get_study_activity_instance_uids(
        api_client, study.uid, study_activity_weight_uid
    )[0]

    res = _post_compound_dosing(api_client, study_activity_instance_uid=instance_uid)
    TestUtils.assert_response_shape_ok(
        res, STUDY_COMPOUND_DOSING_FIELDS_ALL, STUDY_COMPOUND_DOSING_FIELDS_NOT_NULL
    )
    assert res["study_activity_instance"]["study_activity_instance_uid"] == instance_uid
    assert (
        res["study_activity_instance"]["activity_instance"]["name"]
        == weight_activity_instance.name
    )
    study_compound_dosing_uid = res["study_compound_dosing_uid"]

    # The link survives the round trip through the repository
    response = api_client.get(BASE_URL)
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res["items"]) == 1
    assert (
        res["items"][0]["study_activity_instance"]["study_activity_instance_uid"]
        == instance_uid
    )
    assert (
        res["items"][0]["study_activity_instance"]["activity_instance"]["name"]
        == weight_activity_instance.name
    )

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_create_study_compound_dosing_without_dose_collection_instance(api_client):
    """
    SCENARIO: Omit the dose collection study activity instance
    WHEN POST /studies/{uid}/study-compound-dosings leaves the field out
    THEN 201 is returned and the nested study activity instance is null
    """
    res = _post_compound_dosing(api_client)

    assert res["study_activity_instance"] is None

    response = api_client.delete(f"{BASE_URL}/{res['study_compound_dosing_uid']}")
    assert_response_status_code(response, 204)


def test_negative_create_study_compound_dosing_with_unknown_dose_collection_instance(
    api_client,
):
    """
    SCENARIO: Reject a dose collection instance that this study cannot select
    GIVEN a study activity instance uid that does not exist, and one belonging to another study
    WHEN POST /studies/{uid}/study-compound-dosings is called with either
    THEN 404 is returned and nothing is created
    """
    response = api_client.post(
        BASE_URL,
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": medicinal_product1.dose_values[0].uid,
            "study_activity_instance_uid": "StudyActivityInstance_999999",
        },
    )
    assert_response_status_code(response, 404)
    assert (
        response.json()["message"]
        == "Study Activity Instance with UID 'StudyActivityInstance_999999' doesn't exist."
    )

    # A study activity instance of a different study is equally unusable here
    other_study = TestUtils.create_study()
    other_study_activity = TestUtils.create_study_activity(
        study_uid=other_study.uid,
        soa_group_term_uid=soa_group_term_uid,
        activity_uid=weight_activity.uid,
        activity_subgroup_uid=activity_subgroup.uid,
        activity_group_uid=activity_group.uid,
    )
    foreign_instance_uid = _get_study_activity_instance_uids(
        api_client, other_study.uid, other_study_activity.study_activity_uid
    )[0]

    response = api_client.post(
        BASE_URL,
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": medicinal_product1.dose_values[0].uid,
            "study_activity_instance_uid": foreign_instance_uid,
        },
    )
    assert_response_status_code(response, 404)
    assert (
        response.json()["message"]
        == f"Study Activity Instance with UID '{foreign_instance_uid}' doesn't exist."
    )

    response = api_client.get(BASE_URL)
    assert_response_status_code(response, 200)
    assert len(response.json()["items"]) == 0


def test_patch_study_compound_dosing_sets_dose_collection_instance(api_client):
    """
    SCENARIO: Add the dose collection link to a compound dosing created without one
    WHEN PATCH sends study_activity_instance_uid
    THEN the link is stored and a new audit trail entry is written
    """
    instance_uid = _get_study_activity_instance_uids(
        api_client, study.uid, study_activity_weight_uid
    )[0]
    res = _post_compound_dosing(api_client)
    study_compound_dosing_uid = res["study_compound_dosing_uid"]
    assert res["study_activity_instance"] is None

    response = api_client.get(f"{BASE_URL}/{study_compound_dosing_uid}/audit-trail")
    assert_response_status_code(response, 200)
    audit_trail_length_before = len(response.json())

    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": medicinal_product1.dose_values[0].uid,
            "study_activity_instance_uid": instance_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["study_activity_instance"]["study_activity_instance_uid"] == instance_uid
    assert (
        res["study_activity_instance"]["activity_instance"]["name"]
        == weight_activity_instance.name
    )

    # The change was detected, so a new version was written
    response = api_client.get(f"{BASE_URL}/{study_compound_dosing_uid}/audit-trail")
    assert_response_status_code(response, 200)
    audit_trail = response.json()
    assert len(audit_trail) == audit_trail_length_before + 1
    assert (
        audit_trail[0]["study_activity_instance"]["study_activity_instance_uid"]
        == instance_uid
    )

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_patch_study_compound_dosing_preserves_dose_collection_instance(api_client):
    """
    SCENARIO: Change an unrelated field on a linked compound dosing
    WHEN PATCH sends only composition
    THEN the dose collection link is preserved rather than wiped
    """
    instance_uid = _get_study_activity_instance_uids(
        api_client, study.uid, study_activity_weight_uid
    )[0]
    res = _post_compound_dosing(api_client, study_activity_instance_uid=instance_uid)
    study_compound_dosing_uid = res["study_compound_dosing_uid"]

    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": medicinal_product1.dose_values[0].uid,
            "composition": "composition changed, link untouched",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["composition"] == "composition changed, link untouched"
    assert res["study_activity_instance"]["study_activity_instance_uid"] == instance_uid

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_patch_study_compound_dosing_clears_optional_fields_with_explicit_null(
    api_client,
):
    """
    SCENARIO: Clear optional fields by sending them explicitly as null
    GIVEN a compound dosing carrying a dose value, a dose frequency and a dose collection link
    WHEN PATCH sends null for each of them
    THEN all three are cleared, since an explicitly sent null is not back-filled
    """
    instance_uid = _get_study_activity_instance_uids(
        api_client, study.uid, study_activity_weight_uid
    )[0]
    res = _post_compound_dosing(
        api_client,
        dose_frequency_uid=ct_term_dose_frequency.term_uid,
        study_activity_instance_uid=instance_uid,
    )
    study_compound_dosing_uid = res["study_compound_dosing_uid"]
    assert res["study_activity_instance"]["study_activity_instance_uid"] == instance_uid

    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": None,
            "dose_frequency_uid": None,
            "study_activity_instance_uid": None,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["dose_value"] is None
    assert res["dose_frequency"] is None
    assert res["study_activity_instance"] is None

    # ... and the cleared state is what is stored, not just what is echoed back
    res = _get_compound_dosing(api_client, study_compound_dosing_uid)
    assert res["dose_value"] is None
    assert res["dose_frequency"] is None
    assert res["study_activity_instance"] is None

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_patch_study_compound_dosing_repoints_dose_collection_instance(api_client):
    """
    SCENARIO: Move the dose collection link from one study activity instance to another
    WHEN PATCH sends a different study activity instance uid
    THEN the link is replaced, not added alongside the old one

    The relationship is copied forward onto every new version of the dosing node,
    so a missing exclusion would leave the dosing linked to both instances and
    duplicate the row in the listing.
    """
    weight_instance_uid = _get_study_activity_instance_uids(
        api_client, study.uid, study_activity_weight_uid
    )[0]
    height_instance_uid = _get_study_activity_instance_uids(
        api_client, study.uid, study_activity_height_uid
    )[0]
    assert weight_instance_uid != height_instance_uid

    res = _post_compound_dosing(
        api_client, study_activity_instance_uid=weight_instance_uid
    )
    study_compound_dosing_uid = res["study_compound_dosing_uid"]

    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": medicinal_product1.dose_values[0].uid,
            "study_activity_instance_uid": height_instance_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert (
        res["study_activity_instance"]["study_activity_instance_uid"]
        == height_instance_uid
    )
    assert (
        res["study_activity_instance"]["activity_instance"]["name"]
        == height_activity_instance.name
    )

    response = api_client.get(BASE_URL)
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res["items"]) == 1
    assert (
        res["items"][0]["study_activity_instance"]["study_activity_instance_uid"]
        == height_instance_uid
    )

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_edit_linked_study_activity_instance_keeps_dose_collection_link(api_client):
    """
    SCENARIO: Edit the study activity instance a compound dosing is linked to
    WHEN the instance is patched, which replaces its node with a new one of the same uid
    THEN the dose collection link still resolves, to exactly one row

    Study selections are versioned by node replacement and inbound relationships
    are copied forward, so the link must resolve against the study value rather
    than against whichever node version happens to still carry the edge.
    """
    instance_uid = _get_study_activity_instance_uids(
        api_client, study.uid, study_activity_weight_uid
    )[0]
    res = _post_compound_dosing(api_client, study_activity_instance_uid=instance_uid)
    study_compound_dosing_uid = res["study_compound_dosing_uid"]

    response = api_client.patch(
        f"/studies/{study.uid}/study-activity-instances/{instance_uid}",
        json={"is_important": True},
    )
    assert_response_status_code(response, 200)
    assert response.json()["study_activity_instance_uid"] == instance_uid

    response = api_client.get(BASE_URL)
    res = response.json()
    assert_response_status_code(response, 200)
    assert len(res["items"]) == 1
    assert (
        res["items"][0]["study_activity_instance"]["study_activity_instance_uid"]
        == instance_uid
    )
    assert (
        res["items"][0]["study_activity_instance"]["activity_instance"]["name"]
        == weight_activity_instance.name
    )

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_negative_delete_study_activity_instance_used_for_dose_collection(api_client):
    """
    SCENARIO: Delete a study activity instance that a compound dosing collects its dose from
    GIVEN the instance has a sibling instance, so deleting it removes the row
    WHEN DELETE /studies/{uid}/study-activity-instances/{uid} is called
    THEN 400 is returned and the compound dosing keeps its link
    """
    study_activity_uid = TestUtils.create_study_activity(
        study_uid=study.uid,
        soa_group_term_uid=soa_group_term_uid,
        activity_uid=siblings_activity.uid,
        activity_subgroup_uid=activity_subgroup.uid,
        activity_group_uid=activity_group.uid,
    ).study_activity_uid

    # Add a second instance for the same activity, so that deleting one of them
    # removes the row instead of converting it to a placeholder
    response = api_client.post(
        f"/studies/{study.uid}/study-activity-instances/batch",
        json=[
            {
                "method": "POST",
                "content": {
                    "activity_instance_uid": siblings_activity_instance_2.uid,
                    "study_activity_uid": study_activity_uid,
                },
            }
        ],
    )
    assert_response_status_code(response, 207)

    instance_uids = _get_study_activity_instance_uids(
        api_client, study.uid, study_activity_uid
    )
    assert len(instance_uids) == 2
    linked_instance_uid = instance_uids[1]

    res = _post_compound_dosing(
        api_client,
        study_activity_instance_uid=linked_instance_uid,
    )
    study_compound_dosing_uid = res["study_compound_dosing_uid"]

    response = api_client.delete(
        f"/studies/{study.uid}/study-activity-instances/{linked_instance_uid}"
    )
    assert_response_status_code(response, 400)
    assert study_compound_dosing_uid in response.json()["message"]

    # The instance and the link are both untouched
    assert (
        _get_study_activity_instance_uids(api_client, study.uid, study_activity_uid)
        == instance_uids
    )
    res = _get_compound_dosing(api_client, study_compound_dosing_uid)
    assert (
        res["study_activity_instance"]["study_activity_instance_uid"]
        == linked_instance_uid
    )

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_delete_last_study_activity_instance_keeps_dose_collection_link(api_client):
    """
    SCENARIO: Delete the only study activity instance of an activity
    GIVEN that path converts the instance to a placeholder rather than removing the row
    WHEN DELETE /studies/{uid}/study-activity-instances/{uid} is called
    THEN it succeeds, the link survives and the name falls back to the activity name
    """
    study_activity_uid = TestUtils.create_study_activity(
        study_uid=study.uid,
        soa_group_term_uid=soa_group_term_uid,
        activity_uid=placeholder_activity.uid,
        activity_subgroup_uid=activity_subgroup.uid,
        activity_group_uid=activity_group.uid,
    ).study_activity_uid
    instance_uid = _get_study_activity_instance_uids(
        api_client, study.uid, study_activity_uid
    )[0]

    res = _post_compound_dosing(api_client, study_activity_instance_uid=instance_uid)
    study_compound_dosing_uid = res["study_compound_dosing_uid"]
    assert (
        res["study_activity_instance"]["activity_instance"]["name"]
        == placeholder_activity_instance.name
    )

    response = api_client.delete(
        f"/studies/{study.uid}/study-activity-instances/{instance_uid}"
    )
    assert_response_status_code(response, 204)

    # The row survives with the same uid, so the link survives with it; without a
    # selected activity instance the name falls back to the activity name
    res = _get_compound_dosing(api_client, study_compound_dosing_uid)
    assert res["study_activity_instance"]["study_activity_instance_uid"] == instance_uid
    assert res["study_activity_instance"]["activity_instance"] is None
    assert (
        res["study_activity_instance"]["activity"]["name"] == placeholder_activity.name
    )

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_negative_delete_study_activity_used_for_dose_collection(api_client):
    """
    SCENARIO: Delete a study activity whose instance a compound dosing collects its dose from
    GIVEN deleting a study activity cascades to its study activity instances
    WHEN DELETE /studies/{uid}/study-activities/{uid} is called
    THEN 400 is returned and the compound dosing keeps its link
    """
    study_activity_uid = TestUtils.create_study_activity(
        study_uid=study.uid,
        soa_group_term_uid=soa_group_term_uid,
        activity_uid=cascade_activity.uid,
        activity_subgroup_uid=activity_subgroup.uid,
        activity_group_uid=activity_group.uid,
    ).study_activity_uid
    instance_uid = _get_study_activity_instance_uids(
        api_client, study.uid, study_activity_uid
    )[0]

    res = _post_compound_dosing(api_client, study_activity_instance_uid=instance_uid)
    study_compound_dosing_uid = res["study_compound_dosing_uid"]

    response = api_client.delete(
        f"/studies/{study.uid}/study-activities/{study_activity_uid}"
    )
    assert_response_status_code(response, 400)
    assert study_compound_dosing_uid in response.json()["message"]

    res = _get_compound_dosing(api_client, study_compound_dosing_uid)
    assert res["study_activity_instance"]["study_activity_instance_uid"] == instance_uid

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_study_compound_dosing_audit_trail_reports_dose_collection_instance(api_client):
    """
    SCENARIO: Read the audit trail of a compound dosing whose dose collection link changed
    WHEN GET /studies/{uid}/study-compound-dosings/{uid}/audit-trail is called
    THEN there is one row per version, each carrying the uid linked at that time
    """
    weight_instance_uid = _get_study_activity_instance_uids(
        api_client, study.uid, study_activity_weight_uid
    )[0]
    height_instance_uid = _get_study_activity_instance_uids(
        api_client, study.uid, study_activity_height_uid
    )[0]

    res = _post_compound_dosing(api_client)
    study_compound_dosing_uid = res["study_compound_dosing_uid"]

    for instance_uid in (weight_instance_uid, height_instance_uid):
        response = api_client.patch(
            f"{BASE_URL}/{study_compound_dosing_uid}",
            json={
                "study_compound_uid": study_compound.study_compound_uid,
                "study_element_uid": study_elements[0].element_uid,
                "dose_value_uid": medicinal_product1.dose_values[0].uid,
                "study_activity_instance_uid": instance_uid,
            },
        )
        assert_response_status_code(response, 200)

    response = api_client.get(f"{BASE_URL}/{study_compound_dosing_uid}/audit-trail")
    audit_trail = response.json()
    assert_response_status_code(response, 200)
    # Newest first: linked to height, then to weight, then unlinked at creation
    assert [
        (
            entry["study_activity_instance"]["study_activity_instance_uid"]
            if entry["study_activity_instance"]
            else None
        )
        for entry in audit_trail
    ] == [height_instance_uid, weight_instance_uid, None]

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_create_study_compound_dosing_with_free_text_dose_value(api_client):
    """
    SCENARIO: Define a dose value that does not exist in the library
    WHEN POST /studies/{uid}/study-compound-dosings carries free_text_dose_value only
    THEN 201 is returned, the free text round-trips and no library dose value is linked
    """
    res = _post_compound_dosing(
        api_client, dose_value_uid=None, free_text_dose_value=FREE_TEXT_DOSE_VALUE_1
    )
    TestUtils.assert_response_shape_ok(
        res, STUDY_COMPOUND_DOSING_FIELDS_ALL, STUDY_COMPOUND_DOSING_FIELDS_NOT_NULL
    )
    study_compound_dosing_uid = res["study_compound_dosing_uid"]
    assert res["free_text_dose_value"] == FREE_TEXT_DOSE_VALUE_1
    assert res["dose_value"] is None

    # ... and that is what is stored, not just what is echoed back
    res = _get_compound_dosing(api_client, study_compound_dosing_uid)
    assert res["free_text_dose_value"] == FREE_TEXT_DOSE_VALUE_1
    assert res["dose_value"] is None

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_create_study_compound_dosing_without_free_text_dose_value(api_client):
    """
    SCENARIO: Omit the free text dose value
    WHEN POST /studies/{uid}/study-compound-dosings picks a library dose value instead
    THEN 201 is returned and the free text dose value is null
    """
    res = _post_compound_dosing(api_client)

    assert res["free_text_dose_value"] is None
    assert res["dose_value"] is not None

    response = api_client.delete(f"{BASE_URL}/{res['study_compound_dosing_uid']}")
    assert_response_status_code(response, 204)


def test_negative_create_study_compound_dosing_with_both_dose_values(api_client):
    """
    SCENARIO: Provide both a library dose value and a free text one
    WHEN POST /studies/{uid}/study-compound-dosings carries both
    THEN 400 is returned naming both fields, and nothing is created
    """
    response = api_client.post(
        BASE_URL,
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": medicinal_product1.dose_values[0].uid,
            "free_text_dose_value": FREE_TEXT_DOSE_VALUE_1,
        },
    )
    assert_response_status_code(response, 400)
    message = response.json()["message"]
    assert "dose_value_uid" in message
    assert "free_text_dose_value" in message

    response = api_client.get(BASE_URL)
    assert_response_status_code(response, 200)
    assert len(response.json()["items"]) == 0


def test_create_two_free_text_dosings_on_the_same_compound(api_client):
    """
    SCENARIO: Record two different free text dose values for one study compound
    WHEN two POSTs differ only in free_text_dose_value
    THEN both succeed, since the free text takes part in the uniqueness key

    Repeating the same free text is still rejected as a duplicate.
    """
    first = _post_compound_dosing(
        api_client, dose_value_uid=None, free_text_dose_value=FREE_TEXT_DOSE_VALUE_1
    )
    second = _post_compound_dosing(
        api_client, dose_value_uid=None, free_text_dose_value=FREE_TEXT_DOSE_VALUE_2
    )
    assert (
        first["study_compound_dosing_uid"] != second["study_compound_dosing_uid"]
    ), "the second free text dosing was not created"
    assert first["free_text_dose_value"] == FREE_TEXT_DOSE_VALUE_1
    assert second["free_text_dose_value"] == FREE_TEXT_DOSE_VALUE_2

    response = api_client.post(
        BASE_URL,
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": None,
            "free_text_dose_value": FREE_TEXT_DOSE_VALUE_1,
        },
    )
    assert_response_status_code(response, 409)
    assert "already exists" in response.json()["message"]

    for res in (first, second):
        response = api_client.delete(f"{BASE_URL}/{res['study_compound_dosing_uid']}")
        assert_response_status_code(response, 204)


def test_patch_study_compound_dosing_sets_free_text_dose_value(api_client):
    """
    SCENARIO: Change the free text dose value of a compound dosing
    WHEN PATCH sends a different free_text_dose_value
    THEN the new value is stored and a new audit trail entry is written
    """
    res = _post_compound_dosing(
        api_client, dose_value_uid=None, free_text_dose_value=FREE_TEXT_DOSE_VALUE_1
    )
    study_compound_dosing_uid = res["study_compound_dosing_uid"]

    response = api_client.get(f"{BASE_URL}/{study_compound_dosing_uid}/audit-trail")
    assert_response_status_code(response, 200)
    audit_trail_length_before = len(response.json())

    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "free_text_dose_value": FREE_TEXT_DOSE_VALUE_2,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["free_text_dose_value"] == FREE_TEXT_DOSE_VALUE_2

    # The change was detected, so a new version was written
    response = api_client.get(f"{BASE_URL}/{study_compound_dosing_uid}/audit-trail")
    assert_response_status_code(response, 200)
    audit_trail = response.json()
    assert len(audit_trail) == audit_trail_length_before + 1
    assert audit_trail[0]["free_text_dose_value"] == FREE_TEXT_DOSE_VALUE_2

    res = _get_compound_dosing(api_client, study_compound_dosing_uid)
    assert res["free_text_dose_value"] == FREE_TEXT_DOSE_VALUE_2

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_patch_study_compound_dosing_preserves_free_text_dose_value(api_client):
    """
    SCENARIO: Change an unrelated field on a free text dosing
    WHEN PATCH sends only composition
    THEN the free text dose value is carried onto the new node version
    """
    res = _post_compound_dosing(
        api_client, dose_value_uid=None, free_text_dose_value=FREE_TEXT_DOSE_VALUE_1
    )
    study_compound_dosing_uid = res["study_compound_dosing_uid"]

    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "composition": "composition changed, free text untouched",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["composition"] == "composition changed, free text untouched"
    assert res["free_text_dose_value"] == FREE_TEXT_DOSE_VALUE_1

    res = _get_compound_dosing(api_client, study_compound_dosing_uid)
    assert res["free_text_dose_value"] == FREE_TEXT_DOSE_VALUE_1

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_patch_study_compound_dosing_switches_dose_value_mode(api_client):
    """
    SCENARIO: Toggle a compound dosing between a library dose value and a free text one
    GIVEN omitted fields are filled in from the current state
    WHEN PATCH sends the field being switched away from as explicit null
    THEN the switch succeeds in both directions, while omitting the null is rejected
    """
    res = _post_compound_dosing(api_client)
    study_compound_dosing_uid = res["study_compound_dosing_uid"]
    assert res["dose_value"] is not None

    # Omitting the null back-fills the library dose value, so both end up set
    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "free_text_dose_value": FREE_TEXT_DOSE_VALUE_1,
        },
    )
    assert_response_status_code(response, 400)
    message = response.json()["message"]
    assert "dose_value_uid" in message
    assert "free_text_dose_value" in message

    # Library dose value -> free text
    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": None,
            "free_text_dose_value": FREE_TEXT_DOSE_VALUE_1,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["dose_value"] is None
    assert res["free_text_dose_value"] == FREE_TEXT_DOSE_VALUE_1

    # ... and back again
    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": medicinal_product1.dose_values[0].uid,
            "free_text_dose_value": None,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["free_text_dose_value"] is None
    assert res["dose_value"]["uid"] == medicinal_product1.dose_values[0].uid

    res = _get_compound_dosing(api_client, study_compound_dosing_uid)
    assert res["free_text_dose_value"] is None
    assert res["dose_value"]["uid"] == medicinal_product1.dose_values[0].uid

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_study_compound_dosing_audit_trail_reports_free_text_dose_value(api_client):
    """
    SCENARIO: Read the audit trail of a compound dosing whose dose value mode changed
    WHEN GET /studies/{uid}/study-compound-dosings/{uid}/audit-trail is called
    THEN there is one row per version, each carrying the free text of that version
    """
    res = _post_compound_dosing(api_client)
    study_compound_dosing_uid = res["study_compound_dosing_uid"]

    for free_text_dose_value in (FREE_TEXT_DOSE_VALUE_1, FREE_TEXT_DOSE_VALUE_2):
        response = api_client.patch(
            f"{BASE_URL}/{study_compound_dosing_uid}",
            json={
                "study_compound_uid": study_compound.study_compound_uid,
                "study_element_uid": study_elements[0].element_uid,
                "dose_value_uid": None,
                "free_text_dose_value": free_text_dose_value,
            },
        )
        assert_response_status_code(response, 200)

    response = api_client.get(f"{BASE_URL}/{study_compound_dosing_uid}/audit-trail")
    audit_trail = response.json()
    assert_response_status_code(response, 200)
    # Newest first, and the creation entry carried the library dose value instead
    assert [entry["free_text_dose_value"] for entry in audit_trail] == [
        FREE_TEXT_DOSE_VALUE_2,
        FREE_TEXT_DOSE_VALUE_1,
        None,
    ]

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_create_study_compound_dosing_with_free_text_dose_frequency(api_client):
    """
    SCENARIO: Define a dose frequency that does not exist in the library
    WHEN POST /studies/{uid}/study-compound-dosings carries free_text_dose_frequency only
    THEN 201 is returned, the free text round-trips and no library frequency is linked
    """
    res = _post_compound_dosing(
        api_client, free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1
    )
    TestUtils.assert_response_shape_ok(
        res, STUDY_COMPOUND_DOSING_FIELDS_ALL, STUDY_COMPOUND_DOSING_FIELDS_NOT_NULL
    )
    study_compound_dosing_uid = res["study_compound_dosing_uid"]
    assert res["free_text_dose_frequency"] == FREE_TEXT_DOSE_FREQUENCY_1
    assert res["dose_frequency"] is None
    # The combined label is what the listing displays, sorts and filters on
    assert res["dose_frequency_label"] == FREE_TEXT_DOSE_FREQUENCY_1

    # ... and that is what is stored, not just what is echoed back
    res = _get_compound_dosing(api_client, study_compound_dosing_uid)
    assert res["free_text_dose_frequency"] == FREE_TEXT_DOSE_FREQUENCY_1
    assert res["dose_frequency"] is None
    assert res["dose_frequency_label"] == FREE_TEXT_DOSE_FREQUENCY_1

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_create_study_compound_dosing_without_free_text_dose_frequency(api_client):
    """
    SCENARIO: Omit the free text dose frequency
    WHEN POST /studies/{uid}/study-compound-dosings picks a library frequency instead
    THEN 201 is returned, the free text is null and the label reports the term name
    """
    res = _post_compound_dosing(
        api_client, dose_frequency_uid=ct_term_dose_frequency.term_uid
    )

    assert res["free_text_dose_frequency"] is None
    assert res["dose_frequency"] is not None
    assert res["dose_frequency_label"] == res["dose_frequency"]["term_name"]

    response = api_client.delete(f"{BASE_URL}/{res['study_compound_dosing_uid']}")
    assert_response_status_code(response, 204)


def test_negative_create_study_compound_dosing_with_both_dose_frequencies(api_client):
    """
    SCENARIO: Provide both a library dose frequency and a free text one
    WHEN POST /studies/{uid}/study-compound-dosings carries both
    THEN 400 is returned naming both fields, and nothing is created
    """
    response = api_client.post(
        BASE_URL,
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_frequency_uid": ct_term_dose_frequency.term_uid,
            "free_text_dose_frequency": FREE_TEXT_DOSE_FREQUENCY_1,
        },
    )
    assert_response_status_code(response, 400)
    message = response.json()["message"]
    assert "dose_frequency_uid" in message
    assert "free_text_dose_frequency" in message

    response = api_client.get(BASE_URL)
    assert_response_status_code(response, 200)
    assert len(response.json()["items"]) == 0


def test_create_study_compound_dosing_with_both_fields_as_free_text(api_client):
    """
    SCENARIO: Define both the dose value and the dose frequency as free text
    WHEN POST carries free_text_dose_value and free_text_dose_frequency together
    THEN 201 is returned — the two choices are independent of one another
    """
    res = _post_compound_dosing(
        api_client,
        dose_value_uid=None,
        free_text_dose_value=FREE_TEXT_DOSE_VALUE_1,
        free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1,
    )

    assert res["dose_value"] is None
    assert res["dose_frequency"] is None
    assert res["dose_value_label"] == FREE_TEXT_DOSE_VALUE_1
    assert res["dose_frequency_label"] == FREE_TEXT_DOSE_FREQUENCY_1

    response = api_client.delete(f"{BASE_URL}/{res['study_compound_dosing_uid']}")
    assert_response_status_code(response, 204)


def test_create_two_free_text_frequency_dosings_on_the_same_compound(api_client):
    """
    SCENARIO: Record two different free text dose frequencies for one study compound
    WHEN two POSTs differ only in free_text_dose_frequency
    THEN both succeed, since the free text frequency takes part in the uniqueness key

    This is the regression guard for the uniqueness key: without the free text
    frequency in it, the second POST collides with the first as a duplicate.
    Repeating the same free text is still rejected.
    """
    first = _post_compound_dosing(
        api_client, free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1
    )
    second = _post_compound_dosing(
        api_client, free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_2
    )
    assert (
        first["study_compound_dosing_uid"] != second["study_compound_dosing_uid"]
    ), "the second free text frequency dosing was not created"
    assert first["free_text_dose_frequency"] == FREE_TEXT_DOSE_FREQUENCY_1
    assert second["free_text_dose_frequency"] == FREE_TEXT_DOSE_FREQUENCY_2

    response = api_client.post(
        BASE_URL,
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": medicinal_product1.dose_values[0].uid,
            "free_text_dose_frequency": FREE_TEXT_DOSE_FREQUENCY_1,
        },
    )
    assert_response_status_code(response, 409)
    assert "already exists" in response.json()["message"]

    for res in (first, second):
        response = api_client.delete(f"{BASE_URL}/{res['study_compound_dosing_uid']}")
        assert_response_status_code(response, 204)


def test_patch_study_compound_dosing_sets_free_text_dose_frequency(api_client):
    """
    SCENARIO: Change the free text dose frequency of a compound dosing
    WHEN PATCH sends a different free_text_dose_frequency
    THEN the new value is stored and a new audit trail entry is written
    """
    res = _post_compound_dosing(
        api_client, free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1
    )
    study_compound_dosing_uid = res["study_compound_dosing_uid"]

    response = api_client.get(f"{BASE_URL}/{study_compound_dosing_uid}/audit-trail")
    assert_response_status_code(response, 200)
    audit_trail_length_before = len(response.json())

    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "free_text_dose_frequency": FREE_TEXT_DOSE_FREQUENCY_2,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["free_text_dose_frequency"] == FREE_TEXT_DOSE_FREQUENCY_2

    # The change was detected, so a new version was written
    response = api_client.get(f"{BASE_URL}/{study_compound_dosing_uid}/audit-trail")
    assert_response_status_code(response, 200)
    audit_trail = response.json()
    assert len(audit_trail) == audit_trail_length_before + 1
    assert audit_trail[0]["free_text_dose_frequency"] == FREE_TEXT_DOSE_FREQUENCY_2

    res = _get_compound_dosing(api_client, study_compound_dosing_uid)
    assert res["free_text_dose_frequency"] == FREE_TEXT_DOSE_FREQUENCY_2

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_patch_study_compound_dosing_preserves_free_text_dose_frequency(api_client):
    """
    SCENARIO: Change an unrelated field on a free text frequency dosing
    WHEN PATCH sends only composition
    THEN the free text dose frequency is carried onto the new node version

    Guards the _add_new_selection scalar-loss trap: versioning copies
    relationships, never properties, so an omitted scalar is lost on every edit.
    """
    res = _post_compound_dosing(
        api_client, free_text_dose_frequency=FREE_TEXT_DOSE_FREQUENCY_1
    )
    study_compound_dosing_uid = res["study_compound_dosing_uid"]

    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "composition": "composition changed, free text frequency untouched",
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["composition"] == "composition changed, free text frequency untouched"
    assert res["free_text_dose_frequency"] == FREE_TEXT_DOSE_FREQUENCY_1

    res = _get_compound_dosing(api_client, study_compound_dosing_uid)
    assert res["free_text_dose_frequency"] == FREE_TEXT_DOSE_FREQUENCY_1

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_patch_study_compound_dosing_switches_dose_frequency_mode(api_client):
    """
    SCENARIO: Toggle a compound dosing between a library dose frequency and free text
    GIVEN omitted fields are filled in from the current state
    THEN the switch succeeds in both directions, while omitting the null is rejected

    Switching away from the library must also drop the HAS_DOSE_FREQUENCY
    relationship, not merely set the scalar — asserted through dose_frequency
    coming back null on a fresh read.
    """
    library_frequency_uid = ct_term_dose_frequency.term_uid
    res = _post_compound_dosing(api_client, dose_frequency_uid=library_frequency_uid)
    study_compound_dosing_uid = res["study_compound_dosing_uid"]
    assert res["dose_frequency"] is not None

    # Omitting the null back-fills the library frequency, so both end up set
    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "free_text_dose_frequency": FREE_TEXT_DOSE_FREQUENCY_1,
        },
    )
    assert_response_status_code(response, 400)
    message = response.json()["message"]
    assert "dose_frequency_uid" in message
    assert "free_text_dose_frequency" in message

    # Library dose frequency -> free text
    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_frequency_uid": None,
            "free_text_dose_frequency": FREE_TEXT_DOSE_FREQUENCY_1,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["dose_frequency"] is None
    assert res["free_text_dose_frequency"] == FREE_TEXT_DOSE_FREQUENCY_1

    # The relationship is really gone, not just absent from the echoed response
    res = _get_compound_dosing(api_client, study_compound_dosing_uid)
    assert res["dose_frequency"] is None
    assert res["dose_frequency_label"] == FREE_TEXT_DOSE_FREQUENCY_1

    # ... and back again
    response = api_client.patch(
        f"{BASE_URL}/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_frequency_uid": library_frequency_uid,
            "free_text_dose_frequency": None,
        },
    )
    res = response.json()
    assert_response_status_code(response, 200)
    assert res["free_text_dose_frequency"] is None
    assert res["dose_frequency"]["term_uid"] == library_frequency_uid

    res = _get_compound_dosing(api_client, study_compound_dosing_uid)
    assert res["free_text_dose_frequency"] is None
    assert res["dose_frequency"]["term_uid"] == library_frequency_uid
    assert res["dose_frequency_label"] == res["dose_frequency"]["term_name"]

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_study_compound_dosing_audit_trail_reports_free_text_dose_frequency(api_client):
    """
    SCENARIO: Read the audit trail of a dosing whose dose frequency mode changed
    WHEN GET /studies/{uid}/study-compound-dosings/{uid}/audit-trail is called
    THEN there is one row per version, each carrying the free text of that version
    """
    res = _post_compound_dosing(
        api_client, dose_frequency_uid=ct_term_dose_frequency.term_uid
    )
    study_compound_dosing_uid = res["study_compound_dosing_uid"]

    for free_text_dose_frequency in (
        FREE_TEXT_DOSE_FREQUENCY_1,
        FREE_TEXT_DOSE_FREQUENCY_2,
    ):
        response = api_client.patch(
            f"{BASE_URL}/{study_compound_dosing_uid}",
            json={
                "study_compound_uid": study_compound.study_compound_uid,
                "study_element_uid": study_elements[0].element_uid,
                "dose_frequency_uid": None,
                "free_text_dose_frequency": free_text_dose_frequency,
            },
        )
        assert_response_status_code(response, 200)

    response = api_client.get(f"{BASE_URL}/{study_compound_dosing_uid}/audit-trail")
    audit_trail = response.json()
    assert_response_status_code(response, 200)
    # Newest first, and the creation entry carried the library frequency instead
    assert [entry["free_text_dose_frequency"] for entry in audit_trail] == [
        FREE_TEXT_DOSE_FREQUENCY_2,
        FREE_TEXT_DOSE_FREQUENCY_1,
        None,
    ]

    response = api_client.delete(f"{BASE_URL}/{study_compound_dosing_uid}")
    assert_response_status_code(response, 204)


def test_compound_dosing_modify_actions_on_locked_study(api_client):
    locked_instance_uid = _get_study_activity_instance_uids(
        api_client, study.uid, study_activity_weight_uid
    )[0]

    response = api_client.post(
        f"/studies/{study.uid}/study-compound-dosings",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": dose_value.uid,
            "study_activity_instance_uid": locked_instance_uid,
        },
    )
    res = response.json()
    assert_response_status_code(response, 201)
    assert (
        res["study_activity_instance"]["study_activity_instance_uid"]
        == locked_instance_uid
    )

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

    # edit the dose collection study activity instance link
    response = api_client.patch(
        f"/studies/{study.uid}/study-compound-dosings/{study_compound_dosing_uid}",
        json={
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": dose_value.uid,
            "study_activity_instance_uid": locked_instance_uid,
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

    # Re-point the dose collection link so the locked version has to resolve the
    # study activity instance it carried at the time, not the current one
    locked_instance_uid = res_old["items"][0]["study_activity_instance"][
        "study_activity_instance_uid"
    ]
    assert locked_instance_uid is not None
    new_instance_uid = _get_study_activity_instance_uids(
        api_client, study.uid, study_activity_height_uid
    )[0]
    assert new_instance_uid != locked_instance_uid

    res_patch_comp_dosing = api_client.patch(
        f"/studies/{study.uid}/study-compound-dosings/{res_old['items'][0]['study_compound_dosing_uid']}",
        json={
            "composition": "composition updated",
            "study_compound_uid": study_compound.study_compound_uid,
            "study_element_uid": study_elements[0].element_uid,
            "dose_value_uid": dose_value.uid,
            "study_activity_instance_uid": new_instance_uid,
        },
    ).json()
    assert res_patch_comp_dosing["composition"] == "composition updated"
    assert (
        res_patch_comp_dosing["study_activity_instance"]["study_activity_instance_uid"]
        == new_instance_uid
    )

    res_get = api_client.get(
        f"/studies/{study.uid}/study-compound-dosings",
    ).json()
    assert res_get["items"][0]["composition"] == "composition updated"
    assert (
        res_get["items"][0]["study_activity_instance"]["study_activity_instance_uid"]
        == new_instance_uid
    )

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
        if res_old["items"][i]["study_activity_instance"]:
            res_old["items"][i]["study_activity_instance"]["study_version"] = mock.ANY
    assert res_v1 == res_old
    assert res_v1 != res_new
    # The locked version reports the study activity instance linked at that time
    assert (
        res_v1["items"][0]["study_activity_instance"]["study_activity_instance_uid"]
        == locked_instance_uid
    )
    assert (
        res_new["items"][0]["study_activity_instance"]["study_activity_instance_uid"]
        == new_instance_uid
    )


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
        assert "dose_collection_activity_instance" in str(exported_data.read())
        # Both free text sources and both combined labels are exportable, so the
        # export can reproduce the columns the UI displays and filters on
        assert "free_text_dose_value" in str(exported_data.read())
        assert "dose_value_label" in str(exported_data.read())
        assert "free_text_dose_frequency" in str(exported_data.read())
        assert "dose_frequency_label" in str(exported_data.read())
